from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timezone
from dataclasses import dataclass

from domain.models import Transaction
from infrastructure.repositories.interfaces import IProductRepository, ITransactionRepository


@dataclass(slots=True)
class SaleResult:
    transaction: Transaction
    remaining_stock: int


class RegisterSaleUseCase:
    def __init__(
        self,
        product_repo: IProductRepository,
        transaction_repo: ITransactionRepository,
    ) -> None:
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
