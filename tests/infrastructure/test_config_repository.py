import pytest
from typing import Optional
from sqlalchemy.orm import Session

# Infrastructure imports
from infrastructure.database.models import ConfigModel
from infrastructure.repositories.sqlalchemy_repos import SqlAlchemyConfigRepository

def test_config_repository_saves_and_retrieves_value(db_session: Session) -> None:
    """
    Tests that a key-value pair can be successfully persisted and retrieved.
    Ensures the basic mapping and Unit of Work integration functions correctly.
    """
    # <AAA> stands for Arrange, Act, Assert
    # Arrange
    repo: SqlAlchemyConfigRepository = SqlAlchemyConfigRepository(db_session)
    test_key: str = "test_key"
    test_value: str = "123"

    # Act
    repo.set_value(test_key, test_value)
    # Explicit commit to trigger the SQLAlchemy flush to the in-memory DB
    db_session.commit()

    # Assert
    retrieved_value: Optional[str] = repo.get_value(test_key)
    assert retrieved_value == test_value


def test_config_repository_returns_default_when_key_is_missing(db_session: Session) -> None:
    """
    Tests the fallback mechanism of the repository. 
    If a configuration key does not exist, it MUST return None or the provided default.
    """
    # Arrange
    repo: SqlAlchemyConfigRepository = SqlAlchemyConfigRepository(db_session)
    missing_key: str = "non_existent_config"

    # Act
    result_none: Optional[str] = repo.get_value(missing_key)
    result_default: Optional[str] = repo.get_value(missing_key, default="fallback_value")

    # Assert
    assert result_none is None, "Expected None for a missing key with no default provided."
    assert result_default == "fallback_value", "Expected the custom default value to be returned."


def test_config_repository_upserts_existing_keys_without_duplication(db_session: Session) -> None:
    """
    CRITICAL: Tests the Upsert (Update or Insert) functionality.
    Ensures that saving an existing key updates the value instead of creating a duplicate row.
    """
    # Arrange
    repo: SqlAlchemyConfigRepository = SqlAlchemyConfigRepository(db_session)
    target_key: str = "upsert_key"
    initial_value: str = "123"
    updated_value: str = "456"

    # Insert the initial value
    repo.set_value(target_key, initial_value)
    db_session.commit()

    # Act: Attempt to save the same key with a new value
    repo.set_value(target_key, updated_value)
    db_session.commit()

    # Assert 1: The value must reflect the update
    current_value: Optional[str] = repo.get_value(target_key)
    assert current_value == updated_value, "The repository failed to return the updated value."

    # Assert 2: Strict Database Integrity Check
    # We bypass the repository purely to verify the SQL table row count.
    # If the Upsert failed and inserted a new row, count will be > 1.
    row_count: int = db_session.query(ConfigModel).filter_by(key=target_key).count()
    assert row_count == 1, f"Upsert failed! Expected 1 row for key '{target_key}', but found {row_count}."
