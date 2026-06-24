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

"""
Sales use case for the Calcify application.

Provides the RegisterSaleUseCase that handles product sale transactions,
reducing stock and creating OUT transaction records in the ledger.
"""

from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timezone
from dataclasses import dataclass

from domain.models import Transaction
from infrastructure.repositories.interfaces import IProductRepository, ITransactionRepository


@dataclass(slots=True)
class SaleResult:
    """Represents the outcome of a completed sale operation.

    Attributes:
        transaction (Transaction): The OUT transaction record created for the sale.
        remaining_stock (int): The product stock quantity after the sale.
    """
    transaction: Transaction
    remaining_stock: int


class RegisterSaleUseCase:
    """Use case for registering a product sale.

    Validates stock availability, creates an OUT transaction, and decrements
    the product stock quantity as a single atomic operation.
    """

    def __init__(
        self,
        product_repo: IProductRepository,
        transaction_repo: ITransactionRepository,
    ) -> None:
        """Initializes the use case with required repository dependencies.

        Args:
            product_repo: Repository for product persistence operations.
            transaction_repo: Repository for transaction ledger operations.
        """
        self._product_repo = product_repo
        self._transaction_repo = transaction_repo

    def execute(
        self,
        product_id: UUID,
        quantity: int,
        unit_price: Decimal,
        currency_code: str,
        comment: str = "",
    ) -> SaleResult:
        """Executes a sale transaction.

        Args:
            product_id: The UUID of the product being sold.
            quantity: Number of units sold (must be positive).
            unit_price: Price per unit at the time of sale.
            currency_code: ISO 4217 currency code for the sale price.
            comment: Optional note attached to the transaction.

        Returns:
            A SaleResult containing the created transaction and remaining stock.

        Raises:
            ValueError: If quantity <= 0, product not found, or insufficient stock.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        product = self._product_repo.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found.")

        if product.stock_quantity < quantity:
            raise ValueError(
                f"Insufficient stock. Available: {product.stock_quantity}, requested: {quantity}"
            )

        transaction = Transaction(
            id=uuid4(),
            product_id=product_id,
            transaction_type="OUT",
            quantity=quantity,
            unit_price=unit_price,
            currency_code=currency_code,
            created_at=datetime.now(timezone.utc),
            comment=comment,
        )
        self._transaction_repo.save(transaction)

        from domain.models import Product
        updated_product = Product(
            id=product.id,
            name=product.name,
            cost_price=product.cost_price,
            cost_currency_code=product.cost_currency_code,
            margin_percentage=product.margin_percentage,
            category=product.category,
            stock_quantity=product.stock_quantity - quantity,
        )
        self._product_repo.save(updated_product)

        return SaleResult(
            transaction=transaction,
            remaining_stock=updated_product.stock_quantity,
        )
