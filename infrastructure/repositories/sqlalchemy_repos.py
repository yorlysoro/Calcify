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

from typing import Optional, List
from uuid import UUID
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import timezone

from domain.models import Currency, Product, Transaction, CurrencyRate
from infrastructure.database.models import (
    CurrencyModel, ProductModel, ConfigModel, TransactionModel, CurrencyRateModel,
)
from infrastructure.repositories.interfaces import (
    ICurrencyRepository, IProductRepository, IConfigRepository, ITransactionRepository,
    ICurrencyRateRepository,
)


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

    def save(self, currency: Currency) -> None:
        """Maps a domain Currency entity to an ORM model and persists it."""
        model: CurrencyModel = CurrencyModel(
            code=currency.code,
            name=currency.name,
            symbol=currency.symbol,
            is_main=currency.is_main,
        )
        self._session.merge(model)

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
            margin_percentage=model.margin_percentage,
            category=model.category
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
            existing_model.category = product.category
        else:
            # Create a new ORM instance mapped from the domain entity
            new_model = ProductModel(
                id=product.id,
                name=product.name,
                cost_price=product.cost_price,
                cost_currency_code=product.cost_currency_code,
                margin_percentage=product.margin_percentage,
                category=product.category
            )
            self._session.add(new_model)
            
        # The flush/commit operation is handled globally by a UnitOfWork, not here.
    
    def get_all(self) -> List[Product]:
        models = self._session.query(ProductModel).all()
        return [
            Product(
                id=m.id, name=m.name, cost_price=m.cost_price,
                cost_currency_code=m.cost_currency_code, margin_percentage=m.margin_percentage
            ) for m in models
        ]
    
    def delete(self, product_id: UUID) -> bool:
        """
        Executes a hard delete on the ORM model. Time Complexity: O(1) via PK index.
        """
        model: Optional[ProductModel] = self._session.query(ProductModel).filter_by(id=product_id).first()
        
        if not model:
            return False
            
        self._session.delete(model)
        # Note: Deliberately omitting self._session.commit() to respect the Unit of Work
        return True

class SqlAlchemyCurrencyRateRepository(ICurrencyRateRepository):
    """
    SQLAlchemy implementation of the currency rate repository interface.
    Handles the boundary mapping between CurrencyRateModel and domain CurrencyRate.
    """

    def __init__(self, session: Session) -> None:
        self._session: Session = session

    def save(self, rate: CurrencyRate) -> None:
        """Maps a domain CurrencyRate to an ORM model and persists it via merge."""
        model: CurrencyRateModel = CurrencyRateModel(
            id=rate.id,
            currency_code=rate.currency_code,
            rate=rate.rate,
            created_at=rate.created_at,
        )
        self._session.merge(model)

    def get_latest_by_code(self, code: str) -> Optional[CurrencyRate]:
        """Returns the most recent CurrencyRate for the given code, or None."""
        model: Optional[CurrencyRateModel] = (
            self._session.query(CurrencyRateModel)
            .filter_by(currency_code=code)
            .order_by(CurrencyRateModel.created_at.desc())
            .first()
        )
        if not model:
            return None
        return CurrencyRate(
            id=model.id,
            currency_code=model.currency_code,
            rate=model.rate,
            created_at=model.created_at,
        )

    def get_all_latest(self) -> List[CurrencyRate]:
        """Returns the most recent CurrencyRate for each currency code."""
        subq = (
            self._session.query(
                CurrencyRateModel.currency_code,
                func.max(CurrencyRateModel.created_at).label("max_created_at"),
            )
            .group_by(CurrencyRateModel.currency_code)
            .subquery()
        )
        models: List[CurrencyRateModel] = (
            self._session.query(CurrencyRateModel)
            .join(
                subq,
                (CurrencyRateModel.currency_code == subq.c.currency_code)
                & (CurrencyRateModel.created_at == subq.c.max_created_at),
            )
            .all()
        )
        return [
            CurrencyRate(
                id=m.id,
                currency_code=m.currency_code,
                rate=m.rate,
                created_at=m.created_at,
            )
            for m in models
        ]

    def delete(self, rate_id: UUID) -> bool:
        """Deletes a CurrencyRate by ID. Returns True if found and removed."""
        model: Optional[CurrencyRateModel] = (
            self._session.query(CurrencyRateModel)
            .filter_by(id=rate_id)
            .first()
        )
        if not model:
            return False
        self._session.delete(model)
        return True


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
    
    def get_all(self) -> List[Transaction]:
        models = self._session.query(TransactionModel).order_by(TransactionModel.created_at.desc()).all()
        return [self._map_to_domain(m) for m in models]
