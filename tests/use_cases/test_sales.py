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
from sqlalchemy.orm import Session
from sqlalchemy import text

from domain.models import Product, Transaction
from use_cases.sales import RegisterSaleUseCase
from infrastructure.repositories.sqlalchemy_repos import (
    SqlAlchemyProductRepository,
    SqlAlchemyTransactionRepository,
)



def seed_product(db_session: Session, stock: int = 10) -> Product:
    """Helper to create a product with given stock."""
    product = Product(
        id=uuid4(),
        name="Test Product",
        cost_price=Decimal("10.00"),
        cost_currency_code="USD",
        margin_percentage=Decimal("30.00"),
        category="Test",
        stock_quantity=stock,
    )
    repo = SqlAlchemyProductRepository(db_session)
    repo.save(product)
    db_session.commit()
    return product


class TestRegisterSale:
    """Suite for RegisterSaleUseCase."""

    def test_reduces_stock(self, db_session: Session) -> None:
        """Selling 5 of 10 should leave 5 remaining."""
        product = seed_product(db_session, stock=10)
        use_case = RegisterSaleUseCase(
            product_repo=SqlAlchemyProductRepository(db_session),
            transaction_repo=SqlAlchemyTransactionRepository(db_session),
        )

        result = use_case.execute(
            product_id=product.id,
            quantity=5,
            unit_price=Decimal("15.00"),
            currency_code="USD",
        )

        assert result.remaining_stock == 5

        # Verify DB was updated
        updated = SqlAlchemyProductRepository(db_session).get_by_id(product.id)
        assert updated is not None
        assert updated.stock_quantity == 5

    def test_creates_out_transaction(self, db_session: Session) -> None:
        """Selling should create a Transaction with type OUT."""
        product = seed_product(db_session, stock=10)
        use_case = RegisterSaleUseCase(
            product_repo=SqlAlchemyProductRepository(db_session),
            transaction_repo=SqlAlchemyTransactionRepository(db_session),
        )

        result = use_case.execute(
            product_id=product.id,
            quantity=3,
            unit_price=Decimal("12.50"),
            currency_code="EUR",
        )

        assert result.transaction.transaction_type == "OUT"
        assert result.transaction.product_id == product.id
        assert result.transaction.quantity == 3
        assert result.transaction.unit_price == Decimal("12.50")
        assert result.transaction.currency_code == "EUR"

        # Verify it persists
        tx_repo = SqlAlchemyTransactionRepository(db_session)
        found = tx_repo.get_by_id(result.transaction.id)
        assert found is not None
        assert found.transaction_type == "OUT"

    def test_with_comment(self, db_session: Session) -> None:
        """Comment should be persisted on the transaction."""
        product = seed_product(db_session, stock=5)
        use_case = RegisterSaleUseCase(
            product_repo=SqlAlchemyProductRepository(db_session),
            transaction_repo=SqlAlchemyTransactionRepository(db_session),
        )

        result = use_case.execute(
            product_id=product.id,
            quantity=2,
            unit_price=Decimal("20.00"),
            currency_code="USD",
            comment="Venta de prueba",
        )

        assert result.transaction.comment == "Venta de prueba"

        # Verify in DB
        tx_repo = SqlAlchemyTransactionRepository(db_session)
        found = tx_repo.get_by_id(result.transaction.id)
        assert found is not None
        assert found.comment == "Venta de prueba"

    def test_preserves_currency(self, db_session: Session) -> None:
        """Sale in GBP should be recorded with GBP currency."""
        product = seed_product(db_session, stock=10)
        use_case = RegisterSaleUseCase(
            product_repo=SqlAlchemyProductRepository(db_session),
            transaction_repo=SqlAlchemyTransactionRepository(db_session),
        )

        result = use_case.execute(
            product_id=product.id,
            quantity=1,
            unit_price=Decimal("50.00"),
            currency_code="GBP",
        )

        assert result.transaction.currency_code == "GBP"

    def test_raises_error_when_product_not_found(self, db_session: Session) -> None:
        """Non-existent product should raise ValueError."""
        use_case = RegisterSaleUseCase(
            product_repo=SqlAlchemyProductRepository(db_session),
            transaction_repo=SqlAlchemyTransactionRepository(db_session),
        )

        with pytest.raises(ValueError, match="not found"):
            use_case.execute(
                product_id=uuid4(),
                quantity=1,
                unit_price=Decimal("10.00"),
                currency_code="USD",
            )

    def test_raises_error_when_insufficient_stock(self, db_session: Session) -> None:
        """Selling more than available stock should raise ValueError."""
        product = seed_product(db_session, stock=10)
        use_case = RegisterSaleUseCase(
            product_repo=SqlAlchemyProductRepository(db_session),
            transaction_repo=SqlAlchemyTransactionRepository(db_session),
        )

        with pytest.raises(ValueError, match="Insufficient stock"):
            use_case.execute(
                product_id=product.id,
                quantity=20,
                unit_price=Decimal("10.00"),
                currency_code="USD",
            )

    def test_raises_error_when_quantity_is_zero(self, db_session: Session) -> None:
        """Zero quantity should raise ValueError."""
        product = seed_product(db_session, stock=10)
        use_case = RegisterSaleUseCase(
            product_repo=SqlAlchemyProductRepository(db_session),
            transaction_repo=SqlAlchemyTransactionRepository(db_session),
        )

        with pytest.raises(ValueError, match="Quantity must be greater than zero"):
            use_case.execute(
                product_id=product.id,
                quantity=0,
                unit_price=Decimal("10.00"),
                currency_code="USD",
            )

    def test_raises_error_when_quantity_is_negative(self, db_session: Session) -> None:
        """Negative quantity should raise ValueError."""
        product = seed_product(db_session, stock=10)
        use_case = RegisterSaleUseCase(
            product_repo=SqlAlchemyProductRepository(db_session),
            transaction_repo=SqlAlchemyTransactionRepository(db_session),
        )

        with pytest.raises(ValueError, match="Quantity must be greater than zero"):
            use_case.execute(
                product_id=product.id,
                quantity=-1,
                unit_price=Decimal("10.00"),
                currency_code="USD",
            )

    def test_does_not_create_transaction_on_failure(self, db_session: Session) -> None:
        """When stock is insufficient, no transaction should be created."""
        product = seed_product(db_session, stock=10)
        tx_repo = SqlAlchemyTransactionRepository(db_session)
        tx_count_before = len(tx_repo.get_all())

        use_case = RegisterSaleUseCase(
            product_repo=SqlAlchemyProductRepository(db_session),
            transaction_repo=tx_repo,
        )

        with pytest.raises(ValueError, match="Insufficient stock"):
            use_case.execute(
                product_id=product.id,
                quantity=20,
                unit_price=Decimal("10.00"),
                currency_code="USD",
            )

        tx_count_after = len(tx_repo.get_all())
        assert tx_count_after == tx_count_before
