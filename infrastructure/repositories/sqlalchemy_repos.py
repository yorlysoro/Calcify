from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import timezone

from domain.models import Currency, Product, Transaction
from infrastructure.database.models import CurrencyModel, ProductModel, ConfigModel, TransactionModel
from infrastructure.repositories.interfaces import ICurrencyRepository, IProductRepository, IConfigRepository, ITransactionRepository


class SqlAlchemyCurrencyRepository(ICurrencyRepository):
    """
    SQLAlchemy implementation of the currency repository interface.
    Handles the boundary mapping between ORM models and pure Domain models.
    """

    def __init__(self, session: Session) -> None:
        """
        Injects the database session dependency to perform transactions.
        
        Args:
            session (Session): The active SQLAlchemy database session.
        """
        self._session: Session = session

    def get_by_code(self, code: str) -> Optional[Currency]:
        """
        Queries the database for a currency and maps it to a domain entity.
        Time Complexity: O(1) assuming the 'code' primary key is indexed.
        """
        model: Optional[CurrencyModel] = self._session.query(CurrencyModel).filter_by(code=code).first()
        if not model:
            return None
        
        # Domain Mapping: Returning pure entities without DB session attachment
        return Currency(
            code=model.code,
            name=model.name,
            symbol=model.symbol,
            is_main=model.is_main
        )

    def get_all(self) -> List[Currency]:
        """Retrieves all currencies mapped to domain entities."""
        models: List[CurrencyModel] = self._session.query(CurrencyModel).all()
        return [
            Currency(
                code=m.code,
                name=m.name,
                symbol=m.symbol,
                is_main=m.is_main
            )
            for m in models
        ]


class SqlAlchemyProductRepository(IProductRepository):
    """
    SQLAlchemy implementation of the product repository interface.
    Ensures domain isolation by handling all mapping internally.
    """

    def __init__(self, session: Session) -> None:
        self._session: Session = session

    def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """
        Queries the database for a product by UUID and maps it to the domain.
        """
        model: Optional[ProductModel] = self._session.query(ProductModel).filter_by(id=product_id).first()
        if not model:
            return None

        return Product(
            id=model.id,
            name=model.name,
            cost_price=model.cost_price,
            cost_currency_code=model.cost_currency_code,
            margin_percentage=model.margin_percentage
        )

    def save(self, product: Product) -> None:
        """
        Maps a pure domain entity to an ORM model and persists it to the database.
        Note: The caller is responsible for committing the session (Unit of Work pattern).
        """
        # Determine if we are updating an existing entity or inserting a new one
        existing_model: Optional[ProductModel] = self._session.query(ProductModel).filter_by(id=product.id).first()

        if existing_model:
            # Update mapped attributes directly to trigger SQLAlchemy state changes
            existing_model.name = product.name
            existing_model.cost_price = product.cost_price
            existing_model.cost_currency_code = product.cost_currency_code
            existing_model.margin_percentage = product.margin_percentage
        else:
            # Create a new ORM instance mapped from the domain entity
            new_model = ProductModel(
                id=product.id,
                name=product.name,
                cost_price=product.cost_price,
                cost_currency_code=product.cost_currency_code,
                margin_percentage=product.margin_percentage
            )
            self._session.add(new_model)
            
        # The flush/commit operation is handled globally by a UnitOfWork, not here.

class SqlAlchemyConfigRepository(IConfigRepository):
    """
    SQLAlchemy implementation of the configuration repository interface.
    Handles the Key-Value storage mapping and Upsert mechanics.
    """

    def __init__(self, session: Session) -> None:
        """
        Injects the database session dependency.
        
        Args:
            session (Session): The active SQLAlchemy database session.
        """
        self._session: Session = session

    def get_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Queries the database for a configuration key.
        Time Complexity: O(1) due to Primary Key indexing.
        """
        model: Optional[ConfigModel] = self._session.query(ConfigModel).filter_by(key=key).first()
        
        if model is None:
            return default
            
        return model.value

    def set_value(self, key: str, value: str) -> None:
        """
        Executes an Upsert (Update or Insert) using SQLAlchemy's merge operation.
        Note: The transaction must be committed by the caller (UnitOfWork).
        """
        # Create a detached instance representing the desired state
        config_instance = ConfigModel(key=key, value=value)
        
        # session.merge() checks the Primary Key. 
        # If 'key' exists, it updates 'value' and 'updated_at'. 
        # If it doesn't exist, it queues an INSERT.
        self._session.merge(config_instance)

class SqlAlchemyTransactionRepository(ITransactionRepository):
    """
    SQLAlchemy implementation of the transaction ledger.
    Responsible for executing ORM queries and securely mapping data back 
    to strictly typed domain entities.
    """

    def __init__(self, session: Session) -> None:
        self._session: Session = session

    def _map_to_domain(self, model: TransactionModel) -> Transaction:
        """
        Internal helper to map an ORM model to a Pure Domain Entity.
        Complexity: O(1)
        """
        # Defensive Mapping: SQLite sometimes strips timezone info upon retrieval.
        # If the driver returns a naive datetime, we explicitly attach UTC to satisfy 
        # the domain's strict constraint (self.created_at.tzinfo is not None).
        dt = model.created_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return Transaction(
            id=model.id,
            product_id=model.product_id,
            transaction_type=model.transaction_type,
            quantity=model.quantity,
            unit_price=model.unit_price,
            currency_code=model.currency_code,
            created_at=dt
        )

    def get_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        """Fetches a transaction by ID. Time Complexity: O(1) via PK index."""
        model: Optional[TransactionModel] = self._session.query(TransactionModel).filter_by(id=transaction_id).first()
        if not model:
            return None
        return self._map_to_domain(model)

    def get_by_product_id(self, product_id: UUID) -> List[Transaction]:
        """
        Fetches the ledger history for a product.
        Time Complexity: O(N) where N is the number of transactions for the product.
        """
        # Ordering by created_at descending ensures a chronological ledger (newest first)
        models: List[TransactionModel] = (
            self._session.query(TransactionModel)
            .filter_by(product_id=product_id)
            .order_by(TransactionModel.created_at.desc())
            .all()
        )
        return [self._map_to_domain(m) for m in models]

    def save(self, transaction: Transaction) -> None:
        """Upserts a domain transaction entity into the ORM."""
        existing_model: Optional[TransactionModel] = self._session.query(TransactionModel).filter_by(id=transaction.id).first()

        if existing_model:
            existing_model.product_id = transaction.product_id
            existing_model.transaction_type = transaction.transaction_type
            existing_model.quantity = transaction.quantity
            existing_model.unit_price = transaction.unit_price
            existing_model.currency_code = transaction.currency_code
            existing_model.created_at = transaction.created_at
        else:
            new_model = TransactionModel(
                id=transaction.id,
                product_id=transaction.product_id,
                transaction_type=transaction.transaction_type,
                quantity=transaction.quantity,
                unit_price=transaction.unit_price,
                currency_code=transaction.currency_code,
                created_at=transaction.created_at
            )
            self._session.add(new_model)
