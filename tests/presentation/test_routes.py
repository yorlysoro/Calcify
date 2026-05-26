import pytest
from decimal import Decimal
from uuid import uuid4
from flask import g
from flask.testing import FlaskClient
from werkzeug.security import generate_password_hash

# Infrastructure Imports (To interact with the in-memory DB during tests)
from domain.models import Product
from infrastructure.repositories.sqlalchemy_repos import SqlAlchemyConfigRepository, SqlAlchemyProductRepository
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

def test_export_backup_success(client: FlaskClient, seed_admin_password: None) -> None:
    """
    Integration test for the Backup Export Use Case.
    Verifies that the endpoint generates the JSON payload, forces a file 
    download via HTTP headers, and correctly serializes pure Domain Entities.
    """
    # 1. Arrange: Authenticate the client
    with client.session_transaction() as session:
        session["authenticated"] = True

    # 2. Arrange: Seed a test product directly into the database
    target_product_id = uuid4()
    with client.application.test_request_context("/"):
        client.application.preprocess_request()
        
        repo = SqlAlchemyProductRepository(g.db_session)
        test_product = Product(
            id=target_product_id,
            name="Backup Integration Test Product",
            cost_price=Decimal("99.99"),
            cost_currency_code="USD",
            margin_percentage=Decimal("15.00")
        )
        repo.save(test_product)
        g.db_session.commit()

    # 3. Act: Trigger the export endpoint (Note the Blueprint URL prefix!)
    response = client.get("/api/v1/backup/export")

    # 4. Assert: Verify HTTP Protocol constraints
    assert response.status_code == 200, "Export endpoint failed to return HTTP 200."
    
    # Verify Content-Disposition header triggers a download with the correct prefix
    assert "Content-Disposition" in response.headers
    assert response.headers["Content-Disposition"].startswith("attachment; filename=respaldo_calculadora_")
    
    # 5. Assert: Verify Domain Serialization Payload
    payload = response.get_json()
    assert payload is not None
    assert payload.get("version") == "1.0.0"
    
    # Verify the nested data structure
    data = payload.get("data", {})
    assert "currencies" in data
    assert "products" in data
    assert "transactions" in data
    
    # Verify the test product was correctly exported and complex types (UUID/Decimal) were converted to strings
    exported_products = data["products"]
    assert len(exported_products) >= 1
    
    # Find our specific seeded product in the backup
    matched_product = next((p for p in exported_products if p["id"] == str(target_product_id)), None)
    
    assert matched_product is not None, "Seeded product was not found in the backup export."
    assert matched_product["name"] == "Backup Integration Test Product"
    # Strict validation: Decimal must have been serialized as a string
    assert matched_product["cost_price"] == "99.99"

def test_get_all_products(client: FlaskClient, seed_admin_password: None) -> None:
    """
    Integration test for the Inventory List endpoint.
    Verifies that multiple products can be fetched and that complex financial 
    types (Decimal, UUID) are safely serialized into JSON strings.
    """
    # 1. Arrange: Forge an authenticated session
    with client.session_transaction() as session:
        session["authenticated"] = True

    # 2. Arrange: Seed multiple products into the isolated test database
    product1_id = uuid4()
    product2_id = uuid4()
    
    with client.application.test_request_context("/"):
        client.application.preprocess_request()
        repo = SqlAlchemyProductRepository(g.db_session)
        
        repo.save(Product(
            id=product1_id, name="Alpha Matrix Hub", 
            cost_price=Decimal("150.75"), cost_currency_code="USD", margin_percentage=Decimal("30.00")
        ))
        repo.save(Product(
            id=product2_id, name="Beta Cyber Deck", 
            cost_price=Decimal("999.99"), cost_currency_code="EUR", margin_percentage=Decimal("15.50")
        ))
        
        g.db_session.commit()

    # 3. Act: Fetch the inventory list
    response = client.get("/api/v1/products")
    payload = response.get_json()

    # 4. Assert: HTTP Protocol and Structure
    assert response.status_code == 200
    assert "data" in payload
    assert isinstance(payload["data"], list)
    
    # Since tests share the memory DB in a session scope (depending on earlier tests), 
    # we assert there are AT LEAST the 2 products we just inserted.
    products_list = payload["data"]
    assert len(products_list) >= 2

    # 5. Assert: Data Integrity and Strict Serialization
    alpha_product = next((p for p in products_list if p["id"] == str(product1_id)), None)
    
    assert alpha_product is not None, "Seeded Alpha product is missing from response."
    assert alpha_product["name"] == "Alpha Matrix Hub"
    # The Decimals MUST arrive as strings to prevent floating point corruption
    assert alpha_product["cost_price"] == "150.75"
    assert alpha_product["margin_percentage"] == "30.00"
    assert alpha_product["cost_currency_code"] == "USD"
