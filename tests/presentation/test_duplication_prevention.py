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

"""Tests for preventing duplicate entity creation in API routes."""

from uuid import uuid4
import pytest
from flask.testing import FlaskClient
def test_create_currency_then_product_creates_only_one(
    client: FlaskClient, seed_admin_password: None
) -> None:
    """Simulates ConfigView.create->InventoryView.initModal->product create.

    Regression test for the bug where InventoryView.initModal() registered
    duplicate submit listeners, causing N product POSTs per form submit.
    """
    with client.session_transaction() as session:
        session["authenticated"] = True

    # Step 1: Create a currency (triggers InventoryView.initModal in UI)
    cur_resp = client.post("/api/v1/currencies", json={
        "code": "GBP", "name": "Pound", "symbol": "\u00a3",
    })
    assert cur_resp.status_code == 201

    # Step 2: Create a product (in the bug, this would create 2 due to
    # duplicate submit handlers — same frontend payload, two POSTs)
    prod_id = str(uuid4())
    prod_resp = client.post("/api/v1/products", json={
        "id": prod_id,
        "name": "Single Product",
        "cost_price": "50.00",
        "cost_currency_code": "USD",
        "margin_percentage": "20.00",
        "stock_quantity": 5,
    })
    assert prod_resp.status_code == 201

    # Step 3: Verify only one product exists
    list_resp = client.get("/api/v1/products")
    assert list_resp.status_code == 200
    products = list_resp.get_json()["data"]
    matching = [p for p in products if p["name"] == "Single Product"]
    assert len(matching) == 1, (
        f"Expected 1 product named 'Single Product', got {len(matching)}. "
        f"Duplicate submit handlers would create N>1 copies."
    )


def test_sales_select_refreshes_after_product_create(
    client: FlaskClient, seed_admin_password: None
) -> None:
    """Simulates: create product in Inventory -> Sales select sees it.

    Regression test ensuring that after a product is created, it appears
    in the product list returned to the sales endpoint.
    """
    with client.session_transaction() as session:
        session["authenticated"] = True

    product_id = str(uuid4())
    prod_resp = client.post("/api/v1/products", json={
        "id": product_id,
        "name": "Sales Select Test",
        "cost_price": "30.00",
        "cost_currency_code": "USD",
        "margin_percentage": "25.00",
        "stock_quantity": 10,
    })
    assert prod_resp.status_code == 201

    products_resp = client.get("/api/v1/products")
    assert products_resp.status_code == 200
    names = [p["name"] for p in products_resp.get_json()["data"]]
    assert "Sales Select Test" in names, (
        "Product created should be in the products list for Sales dropdown"
    )


def test_sales_select_refreshes_after_product_delete(
    client: FlaskClient, seed_admin_password: None
) -> None:
    """Simulates: delete product in Inventory -> Sales select sees removal.

    Regression test ensuring that after a product is deleted, it no longer
    appears in the product list returned to the sales endpoint.
    """
    with client.session_transaction() as session:
        session["authenticated"] = True

    product_id = str(uuid4())
    client.post("/api/v1/products", json={
        "id": product_id,
        "name": "To Delete",
        "cost_price": "10.00",
        "cost_currency_code": "USD",
        "margin_percentage": "10.00",
        "stock_quantity": 1,
    })

    del_resp = client.delete(f"/api/v1/products/{product_id}")
    assert del_resp.status_code == 200

    products_resp = client.get("/api/v1/products")
    names = [p["name"] for p in products_resp.get_json()["data"]]
    assert "To Delete" not in names, (
        "Deleted product should not appear in the products list"
    )
