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
SQLAlchemy repository implementations for the Calcify application.

Provides concrete implementations of all repository interfaces using SQLAlchemy 2.0
ORM. Each repository maps between ORM models and pure domain entities through the
_map_to_domain adapter pattern, maintaining strict Clean Architecture boundaries.
"""

from typing import Optional, List
from uuid import UUID
from decimal import Decimal
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
    """SQLAlchemy implementation of the currency repository interface."""

    def __init__(self, session: Session) -> None:
        """Initializes the repository with an active database session.

        Args:
            session: The active SQLAlchemy session for database operations.
        """
        self._session: Session = session

    def _map_to_domain(self, model: CurrencyModel) -> Currency:
        """Maps a CurrencyModel ORM entity to a pure Currency domain entity.

        Args:
            model: The ORM model instance to convert.

        Returns:
            A pure domain Currency entity.
        """
        return Currency(
            code=model.code,
            name=model.name,
            symbol=model.symbol,
            is_main=model.is_main,
        )

    def get_by_code(self, code: str) -> Optional[Currency]:
        """Retrieves a currency by its ISO 4217 code.

        Args:
            code: The ISO 4217 currency code (e.g. 'USD', 'EUR').

        Returns:
            The Currency domain entity if found, None otherwise.
        """
        model: Optional[CurrencyModel] = self._session.query(CurrencyModel).filter_by(code=code).first()
        if not model:
            return None
        return self._map_to_domain(model)

    def save(self, currency: Currency) -> None:
        """Persists a currency entity using merge (upsert) semantics.

        Args:
            currency: The Currency domain entity to save or update.
        """
        model: CurrencyModel = CurrencyModel(
            code=currency.code,
            name=currency.name,
            symbol=currency.symbol,
            is_main=currency.is_main,
        )
        self._session.merge(model)

    def get_all(self) -> List[Currency]:
        """Retrieves all available currencies.

        Returns:
            A list of Currency domain entities.
        """
        models: List[CurrencyModel] = self._session.query(CurrencyModel).all()
        return [self._map_to_domain(m) for m in models]

    def set_main(self, code: str) -> None:
        """Sets a currency as main/base, unsetting all others."""
        self._session.query(CurrencyModel).update(
            {CurrencyModel.is_main: False}
        )
        self._session.query(CurrencyModel).filter_by(code=code).update(
            {CurrencyModel.is_main: True}
        )


class SqlAlchemyProductRepository(IProductRepository):
    """SQLAlchemy implementation of the product repository interface."""

    def __init__(self, session: Session) -> None:
        """Initializes the repository with an active database session.

        Args:
            session: The active SQLAlchemy session for database operations.
        """
        self._session: Session = session

    def _map_to_domain(self, model: ProductModel) -> Product:
        """Maps a ProductModel ORM entity to a pure Product domain entity.

        Applies defensive defaults for legacy rows with NULL values.

        Args:
            model: The ORM model instance to convert.

        Returns:
            A pure domain Product entity.
        """
        return Product(
            id=model.id,
            name=model.name,
            cost_price=model.cost_price,
            cost_currency_code=model.cost_currency_code,
            margin_percentage=model.margin_percentage,
            category=model.category or "Uncategorized",
            stock_quantity=model.stock_quantity or 0,
        )

    def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """Retrieves a product by its UUID.

        Args:
            product_id: The UUID of the product to find.

        Returns:
            The Product domain entity if found, None otherwise.
        """
        model: Optional[ProductModel] = self._session.query(ProductModel).filter_by(id=product_id).first()
        if not model:
            return None
        return self._map_to_domain(model)

    def save(self, product: Product) -> None:
        """Persists a product using lookup-then-update semantics for existing records.

        Creates a new ORM record if no existing product matches the ID.

        Args:
            product: The Product domain entity to save or update.
        """
        existing_model: Optional[ProductModel] = self._session.query(ProductModel).filter_by(id=product.id).first()

        if existing_model:
            existing_model.name = product.name
            existing_model.cost_price = product.cost_price
            existing_model.cost_currency_code = product.cost_currency_code
            existing_model.margin_percentage = product.margin_percentage
            existing_model.category = product.category
            existing_model.stock_quantity = product.stock_quantity
        else:
            new_model = ProductModel(
                id=product.id,
                name=product.name,
                cost_price=product.cost_price,
                cost_currency_code=product.cost_currency_code,
                margin_percentage=product.margin_percentage,
                category=product.category,
                stock_quantity=product.stock_quantity,
            )
            self._session.add(new_model)

    def get_all(self) -> List[Product]:
        """Retrieves all products from the database.

        Returns:
            A list of Product domain entities.
        """
        models = self._session.query(ProductModel).all()
        return [self._map_to_domain(m) for m in models]

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
    """SQLAlchemy implementation of the currency rate repository interface."""

    def __init__(self, session: Session) -> None:
        """Initializes the repository with an active database session.

        Args:
            session: The active SQLAlchemy session for database operations.
        """
        self._session: Session = session

    def _map_to_domain(self, model: CurrencyRateModel) -> CurrencyRate:
        """Maps a CurrencyRateModel ORM entity to a pure CurrencyRate domain entity.

        Defensively corrects SQLite naive datetime to timezone-aware UTC.

        Args:
            model: The ORM model instance to convert.

        Returns:
            A pure domain CurrencyRate entity.
        """
        dt = model.created_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return CurrencyRate(
            id=model.id,
            currency_code=model.currency_code,
            rate=model.rate,
            inverse_rate=model.inverse_rate,
            created_at=dt,
        )

    def save(self, rate: CurrencyRate) -> None:
        """Persists a currency rate using merge (upsert) semantics.

        Pre-calculates the inverse_rate as 1/rate. Rejects zero rates to
        prevent DivisionByZero errors.

        Args:
            rate: The CurrencyRate domain entity to save.

        Raises:
            ValueError: If the rate value is zero.
        """
        if rate.rate == Decimal("0"):
            raise ValueError("Exchange rate cannot be zero.")
        inverse: Decimal = Decimal("1") / rate.rate
        model: CurrencyRateModel = CurrencyRateModel(
            id=rate.id,
            currency_code=rate.currency_code,
            rate=rate.rate,
            inverse_rate=inverse,
            created_at=rate.created_at,
        )
        self._session.merge(model)

    def get_latest_by_code(self, code: str) -> Optional[CurrencyRate]:
        """Retrieves the most recent rate for a given currency code.

        Args:
            code: The ISO 4217 currency code.

        Returns:
            The latest CurrencyRate if found, None otherwise.
        """
        model: Optional[CurrencyRateModel] = (
            self._session.query(CurrencyRateModel)
            .filter_by(currency_code=code)
            .order_by(CurrencyRateModel.created_at.desc())
            .first()
        )
        if not model:
            return None
        return self._map_to_domain(model)

    def get_all_latest(self) -> List[CurrencyRate]:
        """Retrieves the most recent rate for each currency using a grouped subquery.

        Uses SQLAlchemy subquery with func.max to identify the latest rate
        per currency_code in a single query.

        Returns:
            A list of the most recent CurrencyRate per currency code.
        """
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
        return [self._map_to_domain(m) for m in models]

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
        """Initializes the repository with an active database session.

        Args:
            session: The active SQLAlchemy session for database operations.
        """
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
            created_at=dt,
            comment=model.comment or "",
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
            existing_model.comment = transaction.comment
        else:
            new_model = TransactionModel(
                id=transaction.id,
                product_id=transaction.product_id,
                transaction_type=transaction.transaction_type,
                quantity=transaction.quantity,
                unit_price=transaction.unit_price,
                currency_code=transaction.currency_code,
                created_at=transaction.created_at,
                comment=transaction.comment,
            )
            self._session.add(new_model)
    
    def get_all(self) -> List[Transaction]:
        """Retrieves all transactions ordered by creation date descending.

        Returns:
            A list of Transaction domain entities (newest first).
        """
        models = self._session.query(TransactionModel).order_by(TransactionModel.created_at.desc()).all()
        return [self._map_to_domain(m) for m in models]
