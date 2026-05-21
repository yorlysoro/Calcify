from decimal import Decimal
from uuid import UUID
from sqlalchemy import String, Numeric, Boolean, ForeignKey
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
