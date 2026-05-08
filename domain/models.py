from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


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
