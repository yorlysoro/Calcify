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

"""Tests for domain entity validation and business logic."""

import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timezone
from domain.models import Product, CurrencyRate, Transaction, ExchangeRate


def test_product_entity_includes_category_with_default_value() -> None:
    """
    TDD Red Phase: Verifies that the Product domain entity natively 
    supports a category field with a strict default fallback.
    """
    test_id = uuid4()
    
    product = Product(
        id=test_id,
        name="Harina PAN",
        cost_price=Decimal("1.00"),
        cost_currency_code="USD",
        margin_percentage=Decimal("30.00")
    )
    
    assert hasattr(product, 'category')
    assert product.category == "Uncategorized"


def test_product_rejects_float_for_cost_price() -> None:
    with pytest.raises(TypeError, match="Product.cost_price MUST be a decimal.Decimal."):
        Product(id=uuid4(), name="Test", cost_price=1.0, cost_currency_code="USD", margin_percentage=Decimal("10.00"))


def test_product_rejects_float_for_margin_percentage() -> None:
    with pytest.raises(TypeError, match="Product.margin_percentage MUST be a decimal.Decimal."):
        Product(id=uuid4(), name="Test", cost_price=Decimal("1.00"), cost_currency_code="USD", margin_percentage=10.0)


def test_product_rejects_negative_stock() -> None:
    with pytest.raises(ValueError, match="Product.stock_quantity cannot be negative"):
        Product(id=uuid4(), name="Test", cost_price=Decimal("1.00"), cost_currency_code="USD", margin_percentage=Decimal("10.00"), stock_quantity=-1)


def test_currency_rate_rejects_float_for_rate() -> None:
    with pytest.raises(TypeError, match="CurrencyRate.rate MUST be of type decimal.Decimal"):
        CurrencyRate(id=uuid4(), currency_code="USD", rate=500.0, created_at=datetime.now(timezone.utc))


def test_currency_rate_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="CurrencyRate.created_at must be timezone-aware"):
        CurrencyRate(id=uuid4(), currency_code="USD", rate=Decimal("500"), created_at=datetime.now())


def test_transaction_rejects_float_for_unit_price() -> None:
    with pytest.raises(TypeError, match="Transaction.unit_price MUST be a Decimal"):
        Transaction(id=uuid4(), product_id=uuid4(), transaction_type="OUT", quantity=1, unit_price=10.0, currency_code="USD", created_at=datetime.now(timezone.utc))


def test_transaction_rejects_invalid_type() -> None:
    with pytest.raises(ValueError, match="Invalid transaction_type"):
        Transaction(id=uuid4(), product_id=uuid4(), transaction_type="INVALID", quantity=1, unit_price=Decimal("10.00"), currency_code="USD", created_at=datetime.now(timezone.utc))


def test_transaction_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="Transaction.created_at MUST be a timezone-aware"):
        Transaction(id=uuid4(), product_id=uuid4(), transaction_type="IN", quantity=1, unit_price=Decimal("10.00"), currency_code="USD", created_at=datetime.now())


def test_exchange_rate_rejects_float_for_rate() -> None:
    with pytest.raises(TypeError, match="ExchangeRate.rate MUST be of type decimal.Decimal"):
        ExchangeRate(base_currency_code="USD", target_currency_code="EUR", rate=1.2, date=datetime.now(timezone.utc))


def test_exchange_rate_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="ExchangeRate.date must be timezone-aware"):
        ExchangeRate(base_currency_code="USD", target_currency_code="EUR", rate=Decimal("1.2"), date=datetime.now())
