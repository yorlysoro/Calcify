import pytest
from typing import Generator
from sqlalchemy import create_engine, Engine, Connection
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

# Importing the declarative Base and ALL models.
# This ensures that when Base.metadata.create_all is invoked, 
# the SQLAlchemy registry is fully aware of the schemas.
# <ORM> stands for Object-Relational Mapping.
from infrastructure.database.models import (
    Base,
    CurrencyModel,
    ProductModel,
    TransactionModel,
    ConfigModel
)


@pytest.fixture(scope="session")
def db_engine() -> Generator[Engine, None, None]:
    """
    Creates an in-memory SQLite database engine for the entire test session.
    
    Using StaticPool ensures that all connections interact with the exact same 
    in-memory database instance rather than spawning new blank databases.
    
    Yields:
        Engine: The SQLAlchemy core engine bound to the memory database.
    """
    # <URI> stands for Uniform Resource Identifier
    engine: Engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True if SQL query debugging is needed during tests
    )
    
    # Generates the complete schema inside the RAM
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Teardown: Clean up the schema and dispose the engine pool
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    """
    Provides a pristine, isolated database session for each test function.
    
    Implements the "nested transaction" (SAVEPOINT) pattern. This guarantees 
    that even if the domain logic or repository explicitly calls session.commit(), 
    the changes will NOT persist across tests, maintaining 100% test isolation.
    
    Args:
        db_engine (Engine): The session-scoped SQLite engine.
        
    Yields:
        Session: The active SQLAlchemy ORM session.
    """
    # Establish a foundational connection and start a global transaction
    connection: Connection = db_engine.connect()
    transaction = connection.begin()
    
    # Bind the session directly to the connection, forcing it to use SAVEPOINTS
    # instead of committing fully to the database.
    session: Session = Session(
        bind=connection, 
        join_transaction_mode="create_savepoint"
    )
    
    yield session
    
    # Strict Isolation Teardown:
    # 1. Close the ORM session to release memory and tracked objects
    session.close()
    
    # 2. Rollback the global connection transaction to erase any data created by the test
    transaction.rollback()
    
    # 3. Return the connection to the StaticPool
    connection.close()
