from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from domain.models import Currency, Product

# <ABC> stands for Abstract Base Class
class ICurrencyRepository(ABC):
    """
    Interface defining the required database operations for Currency entities.
    """
    
    @abstractmethod
    def get_by_code(self, code: str) -> Optional[Currency]:
        """Retrieves a pure Currency domain entity by its ISO code."""
        pass

    @abstractmethod
    def get_all(self) -> List[Currency]:
        """Retrieves all available Currency domain entities."""
        pass


class IProductRepository(ABC):
    """
    Interface defining the required database operations for Product entities.
    """
    
    @abstractmethod
    def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """Retrieves a pure Product domain entity by its unique identifier."""
        pass

    @abstractmethod
    def save(self, product: Product) -> None:
        """Persists a pure Product domain entity to the data store."""
        pass
