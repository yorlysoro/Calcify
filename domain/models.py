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
        """
        Validates data integrity post-instantiation.
        Ensures strict compliance with the financial precision rule.
        """
        if not isinstance(self.rate, Decimal):
            # Enforcing strict typing at runtime just in case someone ignores the Type Hints
            raise TypeError(
                f"ExchangeRate.rate MUST be of type decimal.Decimal, "
                f"got {type(self.rate).__name__} instead."
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

    def __post_init__(self) -> None:
        """Validates that financial attributes are strictly Decimals to prevent float corruption."""
        if not isinstance(self.cost_price, Decimal):
            raise TypeError("Product.cost_price MUST be a decimal.Decimal.")
        if not isinstance(self.margin_percentage, Decimal):
            raise TypeError("Product.margin_percentage MUST be a decimal.Decimal.")

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
