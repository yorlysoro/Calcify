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

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from domain.models import Currency, Product, Transaction, CurrencyRate

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
    def save(self, currency: Currency) -> None:
        """Persists a pure Currency domain entity to the data store."""
        pass

    @abstractmethod
    def get_all(self) -> List[Currency]:
        """Retrieves all available Currency domain entities."""
        pass

    @abstractmethod
    def set_main(self, code: str) -> None:
        """Sets a currency as the main/base, unsetting all others."""
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
    
    @abstractmethod
    def get_all(self) -> List[Product]:
        pass
    
    @abstractmethod
    def delete(self, product_id: UUID) -> bool:
        """
        Removes a product from the database.
        Returns True if successful, False if the product was not found.
        """
        pass

class ICurrencyRateRepository(ABC):
    """
    Interface defining the required database operations for CurrencyRate entities.
    """

    @abstractmethod
    def save(self, rate: CurrencyRate) -> None:
        """Persists a CurrencyRate domain entity to the data store."""
        pass

    @abstractmethod
    def get_latest_by_code(self, code: str) -> Optional[CurrencyRate]:
        """Retrieves the most recent CurrencyRate for a given currency code."""
        pass

    @abstractmethod
    def get_all_latest(self) -> List[CurrencyRate]:
        """Retrieves the most recent CurrencyRate for each currency code."""
        pass

    @abstractmethod
    def delete(self, rate_id: UUID) -> bool:
        """Removes a CurrencyRate by its ID. Returns True if found and deleted."""
        pass


class IConfigRepository(ABC):
    """
    Interface defining the required operations for the key-value configuration store.
    """

    @abstractmethod
    def get_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieves a configuration value by its unique key.
        
        Args:
            key (str): The configuration identifier.
            default (Optional[str]): Fallback value if the key does not exist.
            
        Returns:
            Optional[str]: The stored value or the provided default.
        """
        pass

    @abstractmethod
    def set_value(self, key: str, value: str) -> None:
        """
        Persists a configuration value, updating it if the key already exists (Upsert).
        
        Args:
            key (str): The configuration identifier.
            value (str): The string value to store.
        """
        pass

class ITransactionRepository(ABC):
    """
    Interface defining the boundaries for transaction ledger persistence.
    """
    
    @abstractmethod
    def save(self, transaction: Transaction) -> None:
        """Persists a new transaction or updates an existing one."""
        pass

    @abstractmethod
    def get_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        """Retrieves a single transaction by its unique ID."""
        pass

    @abstractmethod
    def get_by_product_id(self, product_id: UUID) -> List[Transaction]:
        """Retrieves the chronological transaction history for a specific product."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[Transaction]:
        pass

