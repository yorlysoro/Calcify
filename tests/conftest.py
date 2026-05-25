import pytest
from typing import Generator
from sqlalchemy import create_engine, Engine, Connection
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import close_all_sessions

# Importing the declarative Base and ALL models.
# This ensures that when Base.metadata.create_all is invoked,
# the SQLAlchemy registry is fully aware of the schemas.
# <ORM> stands for Object-Relational Mapping.
from infrastructure.database.models import (
    Base,
    CurrencyModel,
    ProductModel,
    TransactionModel,
    ConfigModel,
)

from app import create_app


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
        echo=False,  # Set to True if SQL query debugging is needed during tests
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
        bind=connection, join_transaction_mode="create_savepoint"
    )

    yield session

    # Strict Isolation Teardown:
    # 1. Close the ORM session to release memory and tracked objects
    session.close()

    # 2. Rollback the global connection transaction to erase any data created by the test
    transaction.rollback()

    # 3. Return the connection to the StaticPool
    connection.close()


@pytest.fixture(scope="function")
def client() -> Generator[FlaskClient, None, None]:
    """
    Provides a fully configured Flask test client for API integration testing.

    This fixture invokes the Application Factory in 'testing' mode. It completely
    isolates the HTTP request cycle, ensuring that each test interacts with a
    fresh instance of the application and a pristine in-memory database.

    Yields:
        FlaskClient: The simulated web client used to dispatch HTTP requests.
    """
    # 1. Bootstrap: Create the isolated Flask application instance
    # Our app.py logic automatically calls Base.metadata.create_all(engine)
    # when config_name == "testing".
    app: Flask = create_app(config_name="testing")

    # 2. Push the application context to mimic a live server environment
    with app.app_context():
        # 3. Instantiate the test client
        with app.test_client() as testing_client:
            # Yield pauses the fixture execution, handing control to the test function
            yield testing_client

    # 4. Teardown Phase (Runs strictly after the test finishes)
    # Explicitly close any lingering SQLAlchemy sessions to release memory locks.
    # The SQLite :memory: database will be instantly destroyed by the Python GC
    # as the 'app' and its enclosed engine are deallocated.
    close_all_sessions()
