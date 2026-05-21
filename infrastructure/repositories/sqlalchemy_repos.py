from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from domain.models import Currency, Product
from infrastructure.database.models import CurrencyModel, ProductModel
from infrastructure.repositories.interfaces import ICurrencyRepository, IProductRepository

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
