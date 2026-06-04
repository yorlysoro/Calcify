import os
import shutil
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, Column, String, Integer

from infrastructure.database.auto_migrate import bootstrap_migrations
from infrastructure.database.models import Base


PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent


def _clean_alembic_artifacts() -> None:
    alembic_ini = PROJECT_ROOT / "alembic.ini"
    migrations = PROJECT_ROOT / "migrations"
    if alembic_ini.exists():
        alembic_ini.unlink()
    if migrations.exists():
        shutil.rmtree(str(migrations), ignore_errors=True)


def _remove_test_col() -> None:
    products_table = Base.metadata.tables["products"]
    if "test_col" in products_table.c:
        col = products_table.c["test_col"]
        products_table._columns.remove(col)


@pytest.fixture(scope="module")
def isolated_env() -> str:
    _clean_alembic_artifacts()
    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        db_url = f"sqlite:///{tmpdir}/test.db"
        yield db_url
        os.chdir(old_cwd)
    _clean_alembic_artifacts()


def test_1_initial_schema(isolated_env: str) -> None:
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


def test_2_add_field(isolated_env: str) -> None:
    db_url: str = isolated_env
    products_table = Base.metadata.tables["products"]
    products_table.append_column(Column("test_col", String))

    assert bootstrap_migrations(db_url, Base.metadata)

    engine = create_engine(db_url)
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns("products")]
    assert "test_col" in columns


def test_3_drop_field(isolated_env: str) -> None:
    db_url: str = isolated_env
    products_table = Base.metadata.tables["products"]
    col = products_table.c["test_col"]
    products_table._columns.remove(col)

    assert bootstrap_migrations(db_url, Base.metadata)

    engine = create_engine(db_url)
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns("products")]
    assert "test_col" not in columns


def test_4_replace_field(isolated_env: str) -> None:
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
