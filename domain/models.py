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
Domain entities for the Calcify application.

Defines the core business objects: Currency, ExchangeRate, Product, CurrencyRate,
and Transaction. All entities use @dataclass(slots=True) for memory efficiency and
enforce strict type validation in __post_init__ to prevent float corruption and
timezone-naive datetime propagation.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

# Required for forward referencing types without causing circular imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # We only import the service during static type checking.
    # At runtime, this block is ignored, preventing the dreaded Circular Import.
    from domain.services import CurrencyConverter


@dataclass(slots=True)
class Currency:
    """
    Represents a currency entity within the domain.

    This is a pure domain entity containing no infrastructure or framework logic.
    Using slots=True optimizes memory allocation and attribute access speed.

    Attributes:
        code (str): The standard ISO 4217 currency code (e.g., 'USD', 'EUR').
        name (str): The full name of the currency (e.g., 'US Dollar').
        symbol (str): The graphical symbol used as a shorthand (e.g., '$', '€').
        is_main (bool): Flag indicating if this is the default/reference currency.
    """

    code: str
    name: str
    symbol: str
    is_main: bool


@dataclass(slots=True)
class ExchangeRate:
    """
    Represents the exchange rate between two currencies at a specific point in time.

    Financial precision is guaranteed by using decimal.Decimal.
    Never use float for the 'rate' attribute.

    Attributes:
        base_currency_code (str): The code of the currency being converted from.
        target_currency_code (str): The code of the currency being converted to.
        rate (Decimal): The exact financial conversion rate.
        date (datetime): The timestamp when this rate was established or retrieved.
    """

    base_currency_code: str
    target_currency_code: str
    rate: Decimal
    date: datetime

    def __post_init__(self) -> None:
        """Validates that rate is a Decimal and date is timezone-aware."""
        if not isinstance(self.rate, Decimal):
            raise TypeError(
                f"ExchangeRate.rate MUST be of type decimal.Decimal, "
                f"got {type(self.rate).__name__} instead."
            )
        if self.date.tzinfo is None:
            raise ValueError(
                "ExchangeRate.date must be timezone-aware. "
                "Use datetime.now(timezone.utc) or similar."
            )


@dataclass(slots=True)
class Product:
    """
    Represents a sellable item within the domain layer.

    Attributes:
        id (UUID): The Universally Unique Identifier for the product.
        name (str): The commercial name of the product.
        cost_price (Decimal): The base acquisition or manufacturing cost.
        cost_currency_code (str): ISO 4217 code representing the currency of the cost.
        margin_percentage (Decimal): The profit margin expressed as a percentage (e.g., 30.00).
    """

    id: UUID
    name: str
    cost_price: Decimal
    cost_currency_code: str
    margin_percentage: Decimal
    category: str = "Uncategorized"
    stock_quantity: int = 0

    def __post_init__(self) -> None:
        """Validates that financial attributes are strictly Decimals to prevent float corruption."""
        if not isinstance(self.cost_price, Decimal):
            raise TypeError("Product.cost_price MUST be a decimal.Decimal.")
        if not isinstance(self.margin_percentage, Decimal):
            raise TypeError("Product.margin_percentage MUST be a decimal.Decimal.")
        if self.stock_quantity < 0:
            raise ValueError(f"Product.stock_quantity cannot be negative, got {self.stock_quantity}.")

    def calculate_sale_price(self) -> Decimal:
        """
        Calculates the final sale price applying the margin percentage over the cost.

        Formula: cost_price * (1 + margin_percentage / 100)

        Returns:
            Decimal: The calculated sale price, strictly rounded to 2 decimal places.
        """
        # <ROI> stands for Return On Investment (conceptually, what the margin builds towards)
        margin_factor: Decimal = Decimal("1.00") + (
            self.margin_percentage / Decimal("100.00")
        )
        raw_price: Decimal = self.cost_price * margin_factor

        return raw_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def get_sale_price_in_currency(
        self,
        base_currency: "Currency",
        target_currency: "Currency",
        converter: "CurrencyConverter",
        current_rate: "ExchangeRate",
    ) -> Decimal:
        """
        Calculates the sale price and converts it to a target currency using an external domain service.

        Notice the architectural decision: We force the caller to inject the 'base_currency'
        object. The Product entity should not be responsible for querying repositories to
        fetch Currency instances.

        Args:
            base_currency (Currency): The entity representing the cost_currency_code.
            target_currency (Currency): The entity representing the desired output currency.
            converter (CurrencyConverter): The stateless domain service handling the conversion logic.
            current_rate (ExchangeRate): The applicable exchange rate.

        Returns:
            Decimal: The converted final sale price.

        Raises:
            ValueError: If the injected base_currency does not match the product's internal currency code.
        """
        if base_currency.code != self.cost_currency_code:
            raise ValueError(
                f"Base currency provided ({base_currency.code}) does not match "
                f"the product's cost currency ({self.cost_currency_code})."
            )

        sale_price: Decimal = self.calculate_sale_price()

        return converter.convert(
            amount=sale_price,
            from_currency=base_currency,
            to_currency=target_currency,
            exchange_rate=current_rate,
        )

@dataclass(slots=True)
class CurrencyRate:
    """
    Represents a financial exchange rate for a specific currency at a point in time.

    Attributes:
        id (UUID): The unique identifier for this rate record.
        currency_code (str): The ISO 4217 currency code this rate applies to.
        rate (Decimal): The exchange rate value relative to the main/base currency.
        inverse_rate (Decimal): The pre-calculated reciprocal of rate (1/rate).
        created_at (datetime): A strict timezone-aware timestamp.
    """

    id: UUID
    currency_code: str
    rate: Decimal
    created_at: datetime
    inverse_rate: Decimal = Decimal("0.0")

    def __post_init__(self) -> None:
        """Validates that rate is a Decimal and created_at is timezone-aware."""
        if not isinstance(self.rate, Decimal):
            raise TypeError(
                f"CurrencyRate.rate MUST be of type decimal.Decimal, "
                f"got {type(self.rate).__name__} instead."
            )
        if self.created_at.tzinfo is None:
            raise ValueError(
                "CurrencyRate.created_at must be timezone-aware. "
                "Use datetime.now(timezone.utc) or similar."
            )


@dataclass(slots=True)
class Transaction:
    """
    Represents a movement of inventory (IN or OUT) coupled with its financial snapshot 
    in the domain layer. Pure Python entity without external dependencies.
    
    Attributes:
        id (UUID): The unique identifier for this ledger entry.
        product_id (UUID): Reference to the product being moved.
        transaction_type (str): Direction of movement ('IN' or 'OUT').
        quantity (int): Number of units moved.
        unit_price (Decimal): The exact financial cost/sale price per unit at the time.
        currency_code (str): The currency used for this specific transaction.
        created_at (datetime): A strict timezone-aware timestamp.
    """
    id: UUID
    product_id: UUID
    transaction_type: str
    quantity: int
    unit_price: Decimal
    currency_code: str
    created_at: datetime
    comment: str = ""

    def __post_init__(self) -> None:
        """
        Validates internal consistency to enforce domain-driven design constraints.
        Prevents corrupt data objects from propagating through the system.
        """
        if not isinstance(self.unit_price, Decimal):
            raise TypeError(f"Transaction.unit_price MUST be a Decimal, got {type(self.unit_price)}.")
        
        if self.transaction_type not in ("IN", "OUT"):
            raise ValueError(f"Invalid transaction_type: '{self.transaction_type}'. Must be 'IN' or 'OUT'.")
        
        # Prevent naive datetimes from entering the domain logic
        if self.created_at.tzinfo is None:
            raise ValueError("Transaction.created_at MUST be a timezone-aware datetime object.")
