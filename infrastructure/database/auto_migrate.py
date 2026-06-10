import os
import shutil
import logging
from pathlib import Path

from alembic.config import Config
from alembic import command
from alembic.util.exc import CommandError

from infrastructure.database.session import get_db_path

logger: logging.Logger = logging.getLogger(__name__)


def bootstrap_migrations(db_url: str, metadata) -> bool:
    """
    Bootstraps Alembic from scratch if no migration infrastructure exists,
    then auto-generates and applies a migration to sync the schema.

    Args:
        db_url (str): The SQLAlchemy database URL to target.
        metadata: The SQLAlchemy Base.metadata to compare against.
    """
    project_root: Path = Path(__file__).resolve().parent.parent.parent
    db_path: Path = get_db_path("Calcify")
    data_dir: Path = db_path.parent
    data_dir.mkdir(parents=True, exist_ok=True)

    alembic_ini_path: Path = data_dir / "alembic.ini"
    migrations_dir: Path = data_dir / "migrations"

    logger.info(f"Data dir (migration artifacts): {data_dir}")
    logger.info(f"Target database: {db_url}")
    logger.info(f"Tables in metadata: {list(metadata.tables.keys())}")

    # 0. Migrate legacy artifacts from project root to data dir
    # This MUST run before the init check so moved files are reused.
    legacy_alembic_ini: Path = project_root / "alembic.ini"
    legacy_migrations: Path = project_root / "migrations"
    legacy_sql_trace: Path = project_root / "schema_trace.sql"

    if not alembic_ini_path.exists() and legacy_alembic_ini.exists():
        logger.info("Migrating legacy alembic.ini from project root to data dir.")
        shutil.move(str(legacy_alembic_ini), str(alembic_ini_path))
    if not migrations_dir.exists() and legacy_migrations.exists():
        logger.info("Migrating legacy migrations/ from project root to data dir.")
        shutil.move(str(legacy_migrations), str(migrations_dir))
    if not (data_dir / "schema_trace.sql").exists() and legacy_sql_trace.exists():
        logger.info("Migrating legacy schema_trace.sql from project root to data dir.")
        shutil.move(str(legacy_sql_trace), str(data_dir / "schema_trace.sql"))

    # 1. Comprehensive initialization: ensure both alembic.ini and migrations/ exist
    config: Config
    if not alembic_ini_path.exists() or not migrations_dir.is_dir():
        logger.info("Alembic infrastructure incomplete. Performing clean initialization.")
        if alembic_ini_path.exists():
            alembic_ini_path.unlink()
        if migrations_dir.exists():
            shutil.rmtree(str(migrations_dir), ignore_errors=True)
        config = Config(str(alembic_ini_path))
        command.init(config, str(migrations_dir))
    else:
        config = Config(str(alembic_ini_path))

    # 2. Inject database URL and script location dynamically (in memory, not written to file)
    config.set_main_option("script_location", str(migrations_dir))
    config.set_main_option("sqlalchemy.url", db_url)

    # 3. Patch env.py with sys.path, target_metadata, and render_as_batch
    env_py_path: Path = migrations_dir / "env.py"
    if env_py_path.exists():
        content: str = env_py_path.read_text()

        needs_patch: bool = False

        if "target_metadata = None" in content:
            project_root_str: str = str(project_root)
            replacement: str = (
                f"import sys\n"
                f"sys.path.insert(0, {project_root_str!r})\n"
                f"from infrastructure.database.models import Base, CurrencyModel, ProductModel, CurrencyRateModel, TransactionModel, ConfigModel\n"
                f"target_metadata = Base.metadata"
            )
            content = content.replace(
                "target_metadata = None",
                replacement,
            )
            needs_patch = True

        if "render_as_batch=True" not in content:
            content = content.replace(
                "context.configure(",
                "context.configure(render_as_batch=True, compare_type=True, compare_server_default=True, ",
            )
            needs_patch = True

        if needs_patch:
            logger.info("Patching migrations/env.py with sys.path, target_metadata, and render_as_batch.")
            env_py_path.write_text(content)

    # 4. Inspect DB state (tables, alembic tracking, fresh/legacy detection)
    from sqlalchemy import create_engine as _ce, inspect as _insp, text as sa_text, String as _SAString, Text as _SAText

    _ck_engine = _ce(db_url)
    _ck_insp = _insp(_ck_engine)
    _db_tables: set = set(_ck_insp.get_table_names())
    _has_av: bool = "alembic_version" in _db_tables

    logger.info(f"alembic_version exists: {_has_av}")
    logger.info(f"DB tables: {sorted(_db_tables)}")

    app_tables: set = set(metadata.tables.keys())
    _tables_exist_no_tracking: bool = (not _has_av) and app_tables.issubset(_db_tables)
    _fresh_db: bool = not _db_tables or _db_tables == {"alembic_version"}

    # 5. ALTER TABLE repair + column metadata extraction.
    # Wrapped in try/finally to guarantee _ck_engine.dispose() even on
    # exception — prevents dangling SQLite file lock on Windows.
    _db_column_info: dict = {}
    try:
        if not _fresh_db:
            for _table_name, _table in metadata.tables.items():
                if _table_name not in _db_tables:
                    continue
                _existing_col_names: set = {c["name"] for c in _ck_insp.get_columns(_table_name)}
                _meta_col_names: set = {c.name for c in _table.c}
                _missing: set = _meta_col_names - _existing_col_names
                if not _missing:
                    continue
                for _col_name in _missing:
                    _col = _table.c[_col_name]
                    _col_type_str: str = str(_col.type)
                    _stmt: str = f"ALTER TABLE {_table_name} ADD COLUMN {_col_name} {_col_type_str}"
                    if _col.server_default is not None:
                        _default_raw: str = str(_col.server_default.arg)
                        if isinstance(_col.type, (_SAString, _SAText)):
                            _stmt += f" DEFAULT '{_default_raw}'"
                        else:
                            _stmt += f" DEFAULT {_default_raw}"
                    if not _col.nullable:
                        _stmt += " NOT NULL"
                    with _ck_engine.begin() as _conn:
                        _conn.execute(sa_text(_stmt))
                    logger.info(f"Added missing column {_table_name}.{_col_name}")

        for _tname in _db_tables - {"alembic_version"}:
            _db_column_info[_tname] = {
                c["name"]: str(c["type"]).upper().replace(" ", "")
                for c in _ck_insp.get_columns(_tname)
            }
    finally:
        _ck_engine.dispose()

    _schema_still_differs: bool = _fresh_db or _tables_exist_no_tracking
    if not _schema_still_differs:
        for _table_name, _table in metadata.tables.items():
            if _table_name not in _db_column_info:
                _schema_still_differs = True
                break
            _db_info: dict = _db_column_info[_table_name]
            _meta_cols: dict = {c.name: c for c in _table.c}
            if set(_db_info.keys()) != set(_meta_cols.keys()):
                _schema_still_differs = True
                break
            for _c_name, _c in _meta_cols.items():
                _meta_norm: str = str(_c.type).upper().replace(" ", "")
                if _meta_norm != _db_info.get(_c_name, ""):
                    _schema_still_differs = True
                    break
            if _schema_still_differs:
                break

    # 7. Apply Alembic migrations / stamp / revision.
    #
    # command.revision(autogenerate=True) is called ONLY for:
    #   - _fresh_db: initial schema on first-ever boot (no hang risk, DB is empty)
    #   - _schema_still_differs: non-additive changes (rare — type change / drop column)
    #
    # For _tables_exist_no_tracking, we use revision() WITHOUT autogenerate to
    # create a baseline migration file, then stamp. No DB comparison = no hang.
    try:
        if _fresh_db:
            logger.info("Fresh database detected. Generating initial schema via Alembic.")
            command.revision(config, autogenerate=True, message="initial_schema")
            command.upgrade(config, "head")
        elif _tables_exist_no_tracking:
            logger.info("Tables exist without Alembic tracking. Creating baseline revision and stamping.")
            command.revision(config, message="initial_schema")
            command.stamp(config, "head")
        elif _schema_still_differs:
            logger.info("Non-additive schema differences detected. Auto-generating migration.")
            command.revision(config, autogenerate=True, message="auto_schema_update")
            command.upgrade(config, "head")
        else:
            command.upgrade(config, "head")
    except CommandError as e:
        msg: str = str(e)
        if "No changes" in msg or "already up to date" in msg.lower() or "already current" in msg.lower():
            logger.info(f"Schema is up to date: {msg}")
        elif "Can't locate revision" in msg:
            logger.warning(f"Stale alembic_version revision detected: {msg}")
            logger.info("Dropping stale alembic_version and creating baseline revision.")
            _recovery_engine = _ce(db_url)
            try:
                with _recovery_engine.begin() as _conn:
                    _conn.execute(sa_text("DROP TABLE IF EXISTS alembic_version"))
            finally:
                _recovery_engine.dispose()
            command.revision(config, message="baseline_recovery")
            command.stamp(config, "head")
        else:
            logger.error(f"Alembic migration error: {msg}")
            raise
    except Exception as e:
        logger.error(f"Alembic migration failed: {e}")
        raise

    # 8. Generate offline SQL trace (DDL dump) for debugging and manual review
    sql_trace_path: Path = data_dir / "schema_trace.sql"
    try:
        with open(str(sql_trace_path), "w") as buffer:
            config.output_buffer = buffer
            command.upgrade(config, "base:head", sql=True)
        logger.info(f"Offline SQL trace written to {sql_trace_path}")
    except Exception as e:
        logger.warning(f"Failed to generate offline SQL trace: {e}")

    return True
