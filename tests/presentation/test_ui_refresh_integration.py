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

"""Tests for UI data refresh after CRUD operations."""

from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timezone

import pytest
from flask.testing import FlaskClient
from infrastructure.repositories.sqlalchemy_repos import SqlAlchemyProductRepository
from domain.models import Product


def test_create_currency_then_list_includes_it(
    client: FlaskClient, seed_admin_password: None
) -> None:
    """
    Tests that after creating a currency via POST /api/v1/currencies,
    a subsequent GET /api/v1/currencies includes the new currency in its list.

    This validates the UI refresh contract: the frontend fetches currencies
    after creation and expects the new currency to be present.
    """
    with client.session_transaction() as session:
        session["authenticated"] = True

    # Arrange: Create a new currency
    payload = {
        "code": "GBP",
        "name": "British Pound",
        "symbol": "\u00a3",
    }
    create_resp = client.post("/api/v1/currencies", json=payload)
    assert create_resp.status_code == 201

    # Act: Fetch all currencies
    list_resp = client.get("/api/v1/currencies")
    assert list_resp.status_code == 200
    currencies = list_resp.get_json()["data"]

    # Assert: The new currency is in the list
    codes = [c["code"] for c in currencies]
    assert "GBP" in codes
    gbp = next(c for c in currencies if c["code"] == "GBP")
    assert gbp["name"] == "British Pound"
    assert gbp["symbol"] == "\u00a3"


def test_create_sale_then_transactions_include_it(
    client: FlaskClient, seed_admin_password: None
) -> None:
    """
    Tests that after registering a sale via POST /api/v1/sales,
    a subsequent GET /api/v1/transactions?date=<today> includes the new
    OUT transaction.

    This validates the UI refresh contract: the frontend fetches transactions
    after a sale and expects the new transaction to appear in the report.
    """
    with client.session_transaction() as session:
        session["authenticated"] = True

    # Arrange: Seed a product
    target_product_id = uuid4()
    with client.application.test_request_context("/"):
        client.application.preprocess_request()
        import flask
        prod_repo = SqlAlchemyProductRepository(flask.g.db_session)
        prod_repo.save(Product(
            id=target_product_id, name="Integration Test Product",
            cost_price=Decimal("10.00"), cost_currency_code="USD",
            margin_percentage=Decimal("30.00"), stock_quantity=10,
        ))
        flask.g.db_session.commit()

    # Act: Register a sale
    sale_resp = client.post("/api/v1/sales", json={
        "product_id": str(target_product_id),
        "quantity": 2,
        "unit_price": "15.00",
        "currency_code": "USD",
        "comment": "Integration test sale",
    })
    assert sale_resp.status_code == 201

    # Act: Fetch transactions for today
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tx_resp = client.get(f"/api/v1/transactions?date={today_str}")
    assert tx_resp.status_code == 200
    transactions = tx_resp.get_json()["data"]

    # Assert: The new sale transaction is in the list
    sale_tx = [t for t in transactions if t["product_id"] == str(target_product_id)]
    assert len(sale_tx) >= 1
    assert sale_tx[0]["transaction_type"] == "OUT"
    assert sale_tx[0]["quantity"] == 2
    assert sale_tx[0]["unit_price"] == "15.00"
    assert sale_tx[0]["currency_code"] == "USD"


def test_create_product_then_list_includes_it(
    client: FlaskClient, seed_admin_password: None
) -> None:
    """
    Tests that after creating a product via POST /api/v1/products,
    a subsequent GET /api/v1/products includes the new product.

    Validates that inventory UI refresh works after product creation.
    """
    with client.session_transaction() as session:
        session["authenticated"] = True

    product_id = str(uuid4())
    payload = {
        "id": product_id,
        "name": "New UI Refresh Product",
        "category": "Testing",
        "cost_price": "25.00",
        "cost_currency_code": "USD",
        "margin_percentage": "20.00",
        "stock_quantity": 5,
    }
    create_resp = client.post("/api/v1/products", json=payload)
    assert create_resp.status_code == 201

    list_resp = client.get("/api/v1/products")
    assert list_resp.status_code == 200
    products = list_resp.get_json()["data"]
    ids = [p["id"] for p in products]
    assert product_id in ids
    created = next(p for p in products if p["id"] == product_id)
    assert created["name"] == "New UI Refresh Product"


def test_create_rate_then_latest_rates_include_it(
    client: FlaskClient, seed_admin_password: None
) -> None:
    """
    Tests that after creating a rate via POST /api/v1/rates,
    a subsequent GET /api/v1/rates/latest includes the new rate.

    Validates that the rate list in ConfigView refreshes after rate creation.
    """
    with client.session_transaction() as session:
        session["authenticated"] = True

    # Arrange: Create a currency first
    client.post("/api/v1/currencies", json={
        "code": "GBP", "name": "British Pound", "symbol": "\u00a3",
    })

    # Act: Create a rate
    rate_payload = {
        "currency_code": "GBP",
        "rate": "1.250000",
    }
    create_rate_resp = client.post("/api/v1/rates", json=rate_payload)
    assert create_rate_resp.status_code == 201

    # Act: Fetch latest rates
    latest_resp = client.get("/api/v1/rates/latest")
    assert latest_resp.status_code == 200
    rates = latest_resp.get_json()["data"]

    # Assert: GBP rate is in the list
    gbp_rates = [r for r in rates if r["currency_code"] == "GBP"]
    assert len(gbp_rates) >= 1
    assert gbp_rates[0]["rate"] == "1.250000"
