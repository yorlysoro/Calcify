import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from domain.models import Currency, Product, Transaction
from infrastructure.repositories.interfaces import (
    ICurrencyRepository,
    IProductRepository,
    ITransactionRepository
)

logger: logging.Logger = logging.getLogger(__name__)

class ExportBackupUseCase:
    """
    Orchestrates the extraction of all domain entities and formats them 
    into a standardized, JSON-serializable dictionary.
    """

    def __init__(
        self,
        product_repo: IProductRepository,
        currency_repo: ICurrencyRepository,
        transaction_repo: ITransactionRepository
    ) -> None:
        """
        Dependency Injection: The use case relies strictly on abstract interfaces,
        making it entirely decoupled from the underlying database technology.
        """
        self._product_repo = product_repo
        self._currency_repo = currency_repo
        self._transaction_repo = transaction_repo

    def execute(self) -> Dict[str, Any]:
        """
        Executes the backup extraction process.
        
        Time Complexity: O(C + P + T) where C, P, and T are the total number 
        of currencies, products, and transactions respectively.
        
        Returns:
            A structured dictionary containing the full system snapshot safely 
            serialized (UUIDs, Decimals, and Datetimes converted to strings).
        """
        logger.info("Initiating full system data backup...")

        # 1. Fetch all raw domain entities
        currencies: List[Currency] = self._currency_repo.get_all()
        products: List[Product] = self._product_repo.get_all()
        transactions: List[Transaction] = self._transaction_repo.get_all()

        # 2. Serialize Data: Explicitly mapping complex types to primitives
        serialized_currencies = [
            {
                "code": c.code,
                "name": c.name,
                "symbol": c.symbol,
                "is_main": c.is_main
            }
            for c in currencies
        ]

        serialized_products = [
            {
                "id": str(p.id),
                "name": p.name,
                "cost_price": str(p.cost_price),  # Decimal to string
                "cost_currency_code": p.cost_currency_code,
                "margin_percentage": str(p.margin_percentage) # Decimal to string
            }
            for p in products
        ]

        serialized_transactions = [
            {
                "id": str(t.id),
                "product_id": str(t.product_id),
                "transaction_type": t.transaction_type,
                "quantity": t.quantity,
                "unit_price": str(t.unit_price),  # Decimal to string
                "currency_code": t.currency_code,
                "created_at": t.created_at.isoformat()  # Datetime to ISO 8601 string
            }
            for t in transactions
        ]

        # 3. Construct the standardized export payload
        export_payload: Dict[str, Any] = {
            "version": "1.0.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "data": {
                "currencies": serialized_currencies,
                "products": serialized_products,
                "transactions": serialized_transactions
            }
        }

        logger.info(f"Backup generated successfully: {len(products)} products, {len(transactions)} transactions exported.")
        
        return export_payload
