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
from uuid import uuid4, UUID
from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

# Pure Domain imports (Transaction entity does not exist yet; TDD dictates we import it anyway)
from domain.models import Product, Transaction

# Infrastructure imports
from infrastructure.repositories.sqlalchemy_repos import (
    SqlAlchemyProductRepository,
    SqlAlchemyTransactionRepository
)

@pytest.fixture
def base_product(db_session: Session) -> Product:
    """
    Fixture to create and persist a base product required to satisfy 
    the Foreign Key constraints of the transactions.
    
    Args:
        db_session (Session): The isolated test database session.
        
    Returns:
        Product: The persisted domain entity.
    """
    repo = SqlAlchemyProductRepository(db_session)
    product = Product(
        id=uuid4(),
        name="Test Driven Product",
        cost_price=Decimal("100.00"),
        cost_currency_code="USD",
        margin_percentage=Decimal("20.00")
    )
    repo.save(product)
    db_session.commit()
    return product


def test_transaction_repository_saves_in_and_out_records(
    db_session: Session, 
    base_product: Product
) -> None:
    """
    Verifies that 'IN' (purchase) and 'OUT' (sale) transactions can be persisted
    and retrieved properly mapped to the pure Domain Entity.
    """
    # Arrange
    # <repo> stands for Repository
    tx_repo: SqlAlchemyTransactionRepository = SqlAlchemyTransactionRepository(db_session)
    
    # <UTC> stands for Coordinated Universal Time
    now_utc: datetime = datetime.now(timezone.utc)
    
    tx_in: Transaction = Transaction(
        id=uuid4(),
        product_id=base_product.id,
        transaction_type="IN",
        quantity=50,
        unit_price=Decimal("100.00"),
        currency_code="USD",
        created_at=now_utc
    )
    
    tx_out: Transaction = Transaction(
        id=uuid4(),
        product_id=base_product.id,
        transaction_type="OUT",
        quantity=5,
        unit_price=Decimal("120.00"),  # Sale price
        currency_code="USD",
        created_at=now_utc
    )

    # Act
    tx_repo.save(tx_in)
    tx_repo.save(tx_out)
    db_session.commit()

    # Assert: Retrieve and verify pure domain mapping
    # Assuming get_by_id will be implemented
    retrieved_in: Optional[Transaction] = tx_repo.get_by_id(tx_in.id)
    
    assert retrieved_in is not None
    assert isinstance(retrieved_in, Transaction), "Repository MUST return a pure domain entity."
    assert retrieved_in.transaction_type == "IN"
    assert retrieved_in.quantity == 50


def test_transaction_repository_filters_history_by_product_id(
    db_session: Session, 
    base_product: Product
) -> None:
    """
    Tests that the repository correctly fetches a list of historical transactions 
    isolated to a specific product identifier.
    """
    # Arrange
    tx_repo: SqlAlchemyTransactionRepository = SqlAlchemyTransactionRepository(db_session)
    product_repo: SqlAlchemyProductRepository = SqlAlchemyProductRepository(db_session)
    
    # Create a secondary product to ensure transactions don't mix
    other_product: Product = Product(
        id=uuid4(), name="Other", cost_price=Decimal("10"), 
        cost_currency_code="USD", margin_percentage=Decimal("10")
    )
    product_repo.save(other_product)
    db_session.commit()
    
    now_utc: datetime = datetime.now(timezone.utc)
    
    # Save 2 transactions for base_product, 1 for other_product
    tx_repo.save(Transaction(id=uuid4(), product_id=base_product.id, transaction_type="IN", quantity=10, unit_price=Decimal("100"), currency_code="USD", created_at=now_utc))
    tx_repo.save(Transaction(id=uuid4(), product_id=base_product.id, transaction_type="OUT", quantity=2, unit_price=Decimal("120"), currency_code="USD", created_at=now_utc))
    tx_repo.save(Transaction(id=uuid4(), product_id=other_product.id, transaction_type="IN", quantity=5, unit_price=Decimal("10"), currency_code="USD", created_at=now_utc))
    db_session.commit()

    # Act
    history: List[Transaction] = tx_repo.get_by_product_id(base_product.id)

    # Assert
    assert len(history) == 2, "Should only retrieve transactions for the specified product."
    assert all(isinstance(tx, Transaction) for tx in history)
    assert all(tx.product_id == base_product.id for tx in history)


def test_transaction_repository_preserves_timezone_awareness(
    db_session: Session, 
    base_product: Product
) -> None:
    """
    Strictly verifies that datetime objects are saved and retrieved without 
    losing their timezone awareness. Crucial for financial auditing.
    """
    # Arrange
    tx_repo: SqlAlchemyTransactionRepository = SqlAlchemyTransactionRepository(db_session)
    original_datetime: datetime = datetime.now(timezone.utc)
    
    tx: Transaction = Transaction(
        id=uuid4(),
        product_id=base_product.id,
        transaction_type="IN",
        quantity=10,
        unit_price=Decimal("100.00"),
        currency_code="USD",
        created_at=original_datetime
    )
    
    tx_repo.save(tx)
    db_session.commit()

    # Act
    retrieved_tx: Optional[Transaction] = tx_repo.get_by_id(tx.id)

    # Assert
    assert retrieved_tx is not None
    # Verify tzinfo is NOT None (Naive datetime rejection)
    assert retrieved_tx.created_at.tzinfo is not None, "Datetime lost its timezone awareness!"
    # Compare timestamps (SQLite might truncate microseconds, so we compare timestamps or exact strings if configured)
    assert retrieved_tx.created_at == original_datetime
