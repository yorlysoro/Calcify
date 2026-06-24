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
SQLAlchemy ORM models for the Calcify application.

Defines the database schema using SQLAlchemy 2.0 Declarative mapping with
strict Numeric types for financial precision. Each model maps to a domain
entity while remaining isolated from domain layer imports.
"""

from decimal import Decimal
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import String, Numeric, Boolean, ForeignKey, Integer, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# <ORM> stands for Object-Relational Mapping
class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models using the 2.0 Declarative style.
    """
    pass


class CurrencyModel(Base):
    """
    ORM representation of the Currency database table.
    """
    __tablename__ = "currencies"

    # Using String(3) for ISO 4217 standard (e.g., 'USD', 'VES')
    code: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(5), nullable=False)
    is_main: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ProductModel(Base):
    """
    ORM representation of the Product database table.
    """
    __tablename__ = "products"

    # <UUID> stands for Universally Unique Identifier
    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Financial Precision: Strictly using Numeric to map to Python's decimal.Decimal.
    # 14 digits total, 2 decimal places. No float logic is permitted at the DB schema level.
    cost_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    
    # Foreign key referencing the Currency table
    cost_currency_code: Mapped[str] = mapped_column(
        String(3), ForeignKey("currencies.code"), nullable=False
    )
    
    # Percentage margin strictly defined as Decimal
    margin_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    category: Mapped[str] = mapped_column(String(100), server_default="Uncategorized", nullable=False)


class TransactionModel(Base):
    """
    ORM representation of an inventory or financial Transaction.
    
    Acts as the single source of truth for historical ledger movements (IN/OUT).
    Uses strict numeric typing for financial amounts.
    """
    __tablename__ = "transactions"

    # <UUID> stands for Universally Unique Identifier.
    # Essential for distributed systems and offline-first desktop apps.
    id: Mapped[UUID] = mapped_column(primary_key=True)
    
    # <FK> stands for Foreign Key. Links the transaction to a specific Product.
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"), nullable=False)
    
    # Restricting string length to 3 ('IN' or 'OUT') to save disk space.
    transaction_type: Mapped[str] = mapped_column(String(3), nullable=False)
    
    # Inventory count must be whole numbers.
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Financial precision required: Numeric mapping strictly to decimal.Decimal
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    
    # The currency used at the exact moment of the transaction
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    
    # We pass a callable lambda using timezone-aware UTC datetime. 
    # datetime.utcnow() is deprecated in Python 3.12+.
    comment: Mapped[str] = mapped_column(String(500), server_default="", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

class CurrencyRateModel(Base):
    """
    ORM representation of the currency_rates database table.
    Stores exchange rate snapshots for each currency over time.
    """
    __tablename__ = "currency_rates"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False)
    inverse_rate: Mapped[Decimal] = mapped_column(Numeric(24, 12), server_default="0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class ConfigModel(Base):
    """
    ORM representation of the system's key-value configuration store.
    
    Used to store dynamic application settings (e.g., API keys, feature flags)
    without requiring environment variable reloads.
    """
    __tablename__ = "configurations"

    # The string key acts as the Primary Key for O(1) lookups and upsert logic
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    
    # Text allows for practically unlimited string length (useful for JWTs or JSON)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Tracks both creation and modification time dynamically using UTC
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
