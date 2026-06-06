import os
import shutil
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, Column, String, Integer, Numeric

from infrastructure.database.auto_migrate import bootstrap_migrations
from infrastructure.database.models import Base


PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent


def _clean_alembic_artifacts(root: Path = PROJECT_ROOT) -> None:
    for name in ("alembic.ini", "migrations", "schema_trace.sql"):
        p = root / name
        if p.exists():
            if p.is_dir():
                shutil.rmtree(str(p), ignore_errors=True)
            else:
                p.unlink()


def _remove_test_col() -> None:
    products_table = Base.metadata.tables["products"]
    if "test_col" in products_table.c:
        col = products_table.c["test_col"]
        products_table._columns.remove(col)


@pytest.fixture(scope="module")
def isolated_env() -> str:
    _clean_alembic_artifacts()
    with tempfile.TemporaryDirectory() as tmpdir:
        old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = tmpdir
        db_file = Path(tmpdir) / "Calcify" / "database.sqlite"
        db_url: str = f"sqlite:///{db_file}"
        yield db_url
        if old_xdg is None:
            del os.environ["XDG_CONFIG_HOME"]
        else:
            os.environ["XDG_CONFIG_HOME"] = old_xdg
    _clean_alembic_artifacts()


def test_1_artifacts_in_data_dir(isolated_env: str) -> None:
    """Verify alembic artifacts live alongside the DB, not in project root."""
    db_url: str = isolated_env
    assert bootstrap_migrations(db_url, Base.metadata)

    tmpdir = os.environ["XDG_CONFIG_HOME"]
    data_dir = Path(tmpdir) / "Calcify"

    assert (data_dir / "alembic.ini").exists()
    assert (data_dir / "migrations").exists()
    assert (data_dir / "migrations" / "env.py").exists()
    assert (data_dir / "migrations" / "versions").exists()
    assert not (PROJECT_ROOT / "alembic.ini").exists()
    assert not (PROJECT_ROOT / "migrations").exists()


def test_2_initial_schema(isolated_env: str) -> None:
    db_url: str = isolated_env
    assert bootstrap_migrations(db_url, Base.metadata)

    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "products" in tables
    assert "currencies" in tables
    assert "transactions" in tables
    assert "currency_rates" in tables
    assert "configurations" in tables


def test_3_add_field(isolated_env: str) -> None:
    db_url: str = isolated_env
    products_table = Base.metadata.tables["products"]
    products_table.append_column(Column("test_col", String))

    assert bootstrap_migrations(db_url, Base.metadata)

    engine = create_engine(db_url)
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns("products")]
    assert "test_col" in columns


def test_4_drop_field(isolated_env: str) -> None:
    db_url: str = isolated_env
    products_table = Base.metadata.tables["products"]
    col = products_table.c["test_col"]
    products_table._columns.remove(col)

    assert bootstrap_migrations(db_url, Base.metadata)

    engine = create_engine(db_url)
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns("products")]
    assert "test_col" not in columns


def test_5_replace_field(isolated_env: str) -> None:
    db_url: str = isolated_env
    products_table = Base.metadata.tables["products"]
    products_table.append_column(Column("test_col", String))

    assert bootstrap_migrations(db_url, Base.metadata)

    products_table._columns.remove(products_table.c["test_col"])
    products_table.append_column(Column("test_col", Integer))

    assert bootstrap_migrations(db_url, Base.metadata)

    engine = create_engine(db_url)
    inspector = inspect(engine)
    columns = inspector.get_columns("products")
    col_info = next(c for c in columns if c["name"] == "test_col")
    assert str(col_info["type"]) == "INTEGER"

    _remove_test_col()


def test_6_currency_rates_inverse(isolated_env: str) -> None:
    from sqlalchemy import Table

    db_url: str = isolated_env
    metadata = Base.metadata
    rates_table: Table = metadata.tables["currency_rates"]

    inverse_col = rates_table.c["inverse_rate"]
    rates_table._columns.remove(inverse_col)

    assert bootstrap_migrations(db_url, Base.metadata)

    engine = create_engine(db_url)
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns("currency_rates")]
    assert "inverse_rate" not in columns
    engine.dispose()

    rates_table.append_column(
        Column("inverse_rate", Numeric(24, 12), server_default="0", nullable=False),
    )

    assert bootstrap_migrations(db_url, Base.metadata)

    engine = create_engine(db_url)
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns("currency_rates")]
    assert "inverse_rate" in columns
    engine.dispose()

    rates_table._columns.remove(rates_table.c["inverse_rate"])
    rates_table.append_column(inverse_col)


def test_7_no_alembic_version_stamped(isolated_env: str) -> None:
    """Bug 1 regression: create_all before bootstrap must still produce alembic_version."""
    db_url: str = isolated_env

    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    engine.dispose()

    assert bootstrap_migrations(db_url, Base.metadata)

    engine2 = create_engine(db_url)
    inspector = inspect(engine2)
    assert "alembic_version" in inspector.get_table_names()
    engine2.dispose()

    products_table = Base.metadata.tables["products"]
    products_table.append_column(Column("test_col", String))

    assert bootstrap_migrations(db_url, Base.metadata)

    engine3 = create_engine(db_url)
    inspector3 = inspect(engine3)
    columns = [c["name"] for c in inspector3.get_columns("products")]
    assert "test_col" in columns
    engine3.dispose()

    _remove_test_col()


def test_8_cwd_independent(isolated_env: str) -> None:
    """Bug 2 regression: migration must work when CWD is NOT the project root."""
    db_url: str = isolated_env
    assert bootstrap_migrations(db_url, Base.metadata)

    old_cwd: str = os.getcwd()
    os.chdir("/tmp")
    try:
        products_table = Base.metadata.tables["products"]
        products_table.append_column(Column("test_col", String))

        assert bootstrap_migrations(db_url, Base.metadata)

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = [c["name"] for c in inspector.get_columns("products")]
        assert "test_col" in columns
    finally:
        os.chdir(old_cwd)

    _remove_test_col()


def test_9_legacy_artifacts_migrated(isolated_env: str) -> None:
    """Legacy artifacts in project root are auto-migrated to data dir."""
    db_url: str = isolated_env

    # Step 1: Bootstrap normally (creates matching migration history + stamps DB)
    assert bootstrap_migrations(db_url, Base.metadata)

    # Step 2: Copy proper artifacts to project root (simulate legacy location)
    tmpdir = os.environ["XDG_CONFIG_HOME"]
    data_dir = Path(tmpdir) / "Calcify"

    legacy_ini: Path = PROJECT_ROOT / "alembic.ini"
    legacy_migrations: Path = PROJECT_ROOT / "migrations"
    try:
        shutil.copytree(str(data_dir / "migrations"), str(legacy_migrations))
        shutil.copy(str(data_dir / "alembic.ini"), str(legacy_ini))

        # Step 3: Remove from data_dir so bootstrap detects them as legacy
        shutil.rmtree(str(data_dir / "migrations"))
        (data_dir / "alembic.ini").unlink()

        # Step 4: Bootstrap again — should move artifacts from project root
        assert bootstrap_migrations(db_url, Base.metadata)

        # Step 5: Verify artifacts ended up in data_dir, legacy is gone
        assert (data_dir / "alembic.ini").exists(), f"alembic.ini not in {data_dir}"
        assert not legacy_ini.exists(), f"legacy alembic.ini still at {legacy_ini}"
    finally:
        _clean_alembic_artifacts()
