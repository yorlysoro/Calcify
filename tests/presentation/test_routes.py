# BSD 3-Clause License
#
# Copyright (c) 2026, yorlysoro
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timezone
from flask import g
from flask.testing import FlaskClient
from werkzeug.security import generate_password_hash

# Infrastructure Imports (To interact with the in-memory DB during tests)
from domain.models import Product, Transaction, CurrencyRate
from infrastructure.repositories.sqlalchemy_repos import (
    SqlAlchemyConfigRepository,
    SqlAlchemyProductRepository,
    SqlAlchemyCurrencyRateRepository,
)
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

def test_delete_product_returns_404_if_not_found(client: FlaskClient, seed_admin_password: None) -> None:
    """
    TDD Red Phase: Verifies that attempting to delete a non-existent UUID 
    gracefully returns an HTTP 404 instead of causing a 500 Server Error.
    """
    # Forge authenticated session
    with client.session_transaction() as session:
        session["authenticated"] = True

    fake_id = str(uuid4())
    response = client.delete(f"/api/v1/products/{fake_id}")
    
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_delete_product_success(client: FlaskClient, seed_admin_password: None) -> None:
    """
    Tests the successful Hard Delete of an existing product.
    """
    with client.session_transaction() as session:
        session["authenticated"] = True

    # 1. Arrange: Seed a product to delete
    target_id = uuid4()
    with client.application.test_request_context("/"):
        client.application.preprocess_request()
        repo = SqlAlchemyProductRepository(g.db_session)
        repo.save(Product(
            id=target_id, name="Delete Target", category="Test",
            cost_price=Decimal("10.00"), cost_currency_code="USD", margin_percentage=Decimal("0.00")
        ))
        g.db_session.commit()

    # 2. Act: Execute the DELETE request
    response = client.delete(f"/api/v1/products/{target_id}")

    # 3. Assert: Verify the response and database state
    assert response.status_code == 200
    assert response.get_json()["message"] == "Product deleted successfully."
    
    # Verify it's actually gone from the DB
    with client.application.test_request_context("/"):
        client.application.preprocess_request()
        check_repo = SqlAlchemyProductRepository(g.db_session)
        assert check_repo.get_by_id(target_id) is None

def test_create_transaction_serialization_and_persistence(client: FlaskClient, seed_admin_password: None) -> None:
    """
    TDD Red Phase: Verifies that creating a transaction correctly persists 
    the domain entity and strictly serializes Decimals/UUIDs back to the client.
    """
    with client.session_transaction() as session:
        session["authenticated"] = True

    # 1. Arrange: Seed a product to attach the transaction to
    target_product_id = uuid4()
    with client.application.test_request_context("/"):
        client.application.preprocess_request()
        repo = SqlAlchemyProductRepository(g.db_session)
        repo.save(Product(
            id=target_product_id, name="Ledger Product", category="Hardware",
            cost_price=Decimal("10.00"), cost_currency_code="USD", margin_percentage=Decimal("0.00")
        ))
        g.db_session.commit()

    # 2. Act: Execute POST request
    payload = {
        "product_id": str(target_product_id),
        "transaction_type": "IN",
        "quantity": 10,
        "unit_price": "15.50",  # String to avoid JS float corruption
        "currency_code": "USD"
    }
    response = client.post("/api/v1/transactions", json=payload)
    
    # 3. Assert
    assert response.status_code == 201
    response_data = response.get_json()["data"]
    
    assert isinstance(response_data["unit_price"], str)
    assert response_data["unit_price"] == "15.50"
    assert response_data["transaction_type"] == "IN"
    # Verify ISO-8601 formatting presence
    assert "T" in response_data["created_at"]


def test_create_currency_success(client: FlaskClient, seed_admin_password: None) -> None:
    """
    Tests successful creation of a new currency via the API.
    Verifies HTTP 201 with the serialized currency data matching the payload.
    """
    with client.session_transaction() as session:
        session["authenticated"] = True

    payload = {
        "code": "GBP",
        "name": "British Pound",
        "symbol": "\u00a3",
        "is_main": False,
    }
    response = client.post("/api/v1/currencies", json=payload)
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["code"] == "GBP"
    assert data["name"] == "British Pound"
    assert data["symbol"] == "\u00a3"
    assert data["is_main"] is False


def test_create_currency_duplicate(client: FlaskClient, seed_admin_password: None) -> None:
    """
    Tests that attempting to create a duplicate currency returns a graceful error.
    Ensures no 500 crash on unique constraint violation.
    """
    with client.session_transaction() as session:
        session["authenticated"] = True

    with client.application.test_request_context("/"):
        client.application.preprocess_request()
        eur = CurrencyModel(code="EUR", name="Euro", symbol="\u20ac", is_main=False)
        g.db_session.merge(eur)
        g.db_session.commit()

    payload = {"code": "EUR", "name": "Euro", "symbol": "\u20ac", "is_main": False}
    response = client.post("/api/v1/currencies", json=payload)
    assert response.status_code in (400, 409)
    assert "error" in response.get_json()


def test_create_currency_rate(client: FlaskClient, seed_admin_password: None) -> None:
    """
    Tests creating a new exchange rate via POST /api/v1/rates.
    Asserts 201 and strict string serialization of the Decimal rate.
    """
    with client.session_transaction() as session:
        session["authenticated"] = True

    payload = {"currency_code": "EUR", "rate": "1.05"}
    response = client.post("/api/v1/rates", json=payload)
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["currency_code"] == "EUR"
    assert isinstance(data["rate"], str)
    assert data["rate"] == "1.05"
    assert "T" in data["created_at"]


def test_get_latest_currency_rates(client: FlaskClient, seed_admin_password: None) -> None:
    """
    Seeds two CurrencyRate records for the same code and verifies
    GET /api/v1/rates/latest returns only the most recent one.
    """
    with client.session_transaction() as session:
        session["authenticated"] = True

    with client.application.test_request_context("/"):
        client.application.preprocess_request()
        repo = SqlAlchemyCurrencyRateRepository(g.db_session)
        now = datetime.now(timezone.utc)
        repo.save(CurrencyRate(id=uuid4(), currency_code="EUR", rate=Decimal("1.05"), created_at=now))
        repo.save(CurrencyRate(id=uuid4(), currency_code="EUR", rate=Decimal("1.10"), created_at=datetime.now(timezone.utc)))
        g.db_session.commit()

    response = client.get("/api/v1/rates/latest")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) >= 1
    eur_rates = [r for r in data if r["currency_code"] == "EUR"]
    assert len(eur_rates) == 1
    assert eur_rates[0]["rate"] == "1.100000"


def test_get_chronological_transactions(client: FlaskClient, seed_admin_password: None) -> None:
    """
    Verifies that the API returns the ledger history correctly serialized.
    """
    with client.session_transaction() as session:
        session["authenticated"] = True

    # Act
    response = client.get("/api/v1/transactions")
    
    # Assert
    assert response.status_code == 200
    assert "data" in response.get_json()
    assert isinstance(response.get_json()["data"], list)
