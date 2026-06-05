import os
import shutil
import logging
from pathlib import Path

from alembic.config import Config
from alembic import command
from alembic.util.exc import CommandError

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
    alembic_ini_path: Path = project_root / "alembic.ini"
    migrations_dir: Path = project_root / "migrations"

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

    # 4. Inject database URL dynamically (in memory, not written to file)
    config.set_main_option("script_location", str(migrations_dir))
    config.set_main_option("sqlalchemy.url", db_url)

    # 5. Patch env.py with target_metadata and render_as_batch
    env_py_path: Path = migrations_dir / "env.py"
    if env_py_path.exists():
        content: str = env_py_path.read_text()

        needs_patch: bool = False

        if "target_metadata = None" in content:
            content = content.replace(
                "target_metadata = None",
                "from infrastructure.database.models import Base, CurrencyModel, ProductModel, CurrencyRateModel, TransactionModel, ConfigModel\ntarget_metadata = Base.metadata",
            )
            needs_patch = True

        if "render_as_batch=True" not in content:
            content = content.replace(
                "context.configure(",
                "context.configure(render_as_batch=True, compare_type=True, compare_server_default=True, ",
            )
            needs_patch = True

        if needs_patch:
            logger.info("Patching migrations/env.py with target_metadata and render_as_batch.")
            env_py_path.write_text(content)

    # 6. Auto-generate and apply migration via Alembic's Python API
    try:
        command.revision(config, autogenerate=True, message="auto_schema_update")
        command.upgrade(config, "head")
    except CommandError as e:
        logger.warning(f"No schema changes detected or revision is up to date: {e}")
    except Exception as e:
        logger.warning(f"Alembic migration skipped or failed: {e}")

    # 7. Generate offline SQL trace (DDL dump) for debugging and manual review
    sql_trace_path: Path = project_root / "schema_trace.sql"
    try:
        with open(str(sql_trace_path), "w") as buffer:
            config.output_buffer = buffer
            command.upgrade(config, "base:head", sql=True)
        logger.info(f"Offline SQL trace written to {sql_trace_path}")
    except Exception as e:
        logger.warning(f"Failed to generate offline SQL trace: {e}")

    return True
