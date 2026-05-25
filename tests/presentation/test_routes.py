import pytest
from uuid import uuid4
from flask import g
from flask.testing import FlaskClient
from werkzeug.security import generate_password_hash

# Infrastructure Imports (To interact with the in-memory DB during tests)
from infrastructure.repositories.sqlalchemy_repos import SqlAlchemyConfigRepository
from infrastructure.database.models import CurrencyModel


@pytest.fixture
def seed_admin_password(client: FlaskClient) -> None:
    """
    Test Fixture: Seeds the in-memory database with a valid admin password hash
    before the test runs. Utilizes Flask's request context to trigger the
    'before_request' middleware and acquire a valid g.db_session.
    """
    with client.application.test_request_context("/"):
        client.application.preprocess_request()  # Triggers @app.before_request -> populates g.db_session

        repo = SqlAlchemyConfigRepository(g.db_session)
        # Using "admin123" as the test PIN
        repo.set_value("admin_password_hash", generate_password_hash("admin123"))

        # Optional: Seed a generic currency to avoid Foreign Key violations
        # when testing Product Creation later.
        usd = CurrencyModel(code="USD", name="US Dollar", symbol="$", is_main=True)
        g.db_session.merge(usd)

        g.db_session.commit()


def test_unauthenticated_access_is_blocked(client: FlaskClient) -> None:
    """
    TDD Red Phase Expected: This test WILL FAIL until you add @login_required
    to the endpoints in presentation/api/routes.py.

    Verifies that an unauthenticated GET request to an API endpoint is intercepted
    by the security middleware and returns an HTTP 401 Unauthorized JSON.
    """
    response = client.get("/api/v1/currencies")

    assert response.status_code == 401, "API failed to block unauthenticated access!"
    assert "error" in response.get_json()
    assert response.get_json()["error"] == "Unauthorized access. Please log in."


def test_failed_login_attempt(client: FlaskClient, seed_admin_password: None) -> None:
    """
    Tests the authentication boundary with an invalid PIN.
    Ensures HTTP 401 is returned and the session remains completely unauthenticated.
    """
    # Act
    response = client.post("/login", json={"pin": "wrong_pin_999"})

    # Assert Http Response
    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid credentials."

    # Assert Session State
    with client.session_transaction() as session:
        assert not session.get(
            "authenticated"
        ), "Session was compromised despite wrong PIN!"


def test_successful_login(client: FlaskClient, seed_admin_password: None) -> None:
    """
    Tests the happy path for authentication.
    Verifies that the correct PIN upgrades the Flask session to permanent and authenticated.
    """
    # Act
    response = client.post("/login", json={"pin": "admin123"})

    # Assert Http Response
    assert response.status_code == 200
    assert response.get_json()["message"] == "Authentication successful."

    # Assert Session State Isolation
    with client.session_transaction() as session:
        assert session.get("authenticated") is True
        assert session.permanent is True


def test_authorized_access_to_api(
    client: FlaskClient, seed_admin_password: None
) -> None:
    """
    Tests that a client with a valid authenticated session can access protected resources.
    """
    # Arrange: Manually forge an authenticated session to isolate the test from the /login route
    with client.session_transaction() as session:
        session["authenticated"] = True

    # Act
    response = client.get("/api/v1/currencies")

    # Assert
    assert response.status_code == 200
    assert "data" in response.get_json()


def test_protected_crud_product_creation(
    client: FlaskClient, seed_admin_password: None
) -> None:
    """
    Integration test spanning the entire architecture:
    Controller (Flask) -> Adapter (Repository) -> Memory Database.
    Ensures that a valid POST payload correctly persists a new Domain Entity.
    """
    # Arrange: Authenticate the client
    with client.session_transaction() as session:
        session["authenticated"] = True

    new_product_id: str = str(uuid4())
    payload = {
        "id": new_product_id,
        "name": "Testing Keyboard",
        "cost_price": "75.50",
        "cost_currency_code": "USD",
        "margin_percentage": "30.00",
    }

    # Act
    response = client.post("/api/v1/products", json=payload)
    response_json = response.get_json()

    # Assert
    assert response.status_code == 201
    assert response_json["message"] == "Product created successfully."
    assert response_json["data"]["id"] == new_product_id
