from decimal import Decimal, ROUND_HALF_UP
from domain.models import Currency, ExchangeRate


class InvalidExchangeRateError(ValueError):
    """
    Domain-specific exception raised when an exchange rate is mathematically
    or logically invalid for processing (e.g., a rate of 0.00).
    """

    pass


class CurrencyConverter:
    """
    A stateless domain service responsible for securely converting financial
    amounts between different currencies using an established exchange rate.
    """

    def convert(
        self,
        amount: Decimal,
        from_currency: Currency,
        to_currency: Currency,
        exchange_rate: ExchangeRate,
    ) -> Decimal:
        """
        Converts an amount from one currency to another using exact financial math.

        Args:
            amount (Decimal): The monetary value to be converted.
            from_currency (Currency): The source currency entity.
            to_currency (Currency): The target currency entity.
            exchange_rate (ExchangeRate): The rate defining the mathematical relationship.

        Returns:
            Decimal: The converted amount strictly rounded to 2 decimal places using ROUND_HALF_UP.

        Raises:
            InvalidExchangeRateError: If the exchange rate is strictly zero.
            ValueError: If the currencies provided do not match the exchange rate's scope.
        """
        # 1. Validation: Prevent ZeroDivisionError and logical absurdities
        if exchange_rate.rate == Decimal("0.00"):
            raise InvalidExchangeRateError(
                "Exchange rate cannot be mathematically zero."
            )

        # 2. Scope Validation: Evaluate directionality of the conversion
        is_direct: bool = (
            exchange_rate.base_currency_code == from_currency.code
            and exchange_rate.target_currency_code == to_currency.code
        )
        is_inverse: bool = (
            exchange_rate.base_currency_code == to_currency.code
            and exchange_rate.target_currency_code == from_currency.code
        )

        # Fail fast if the rate is totally unrelated to the request
        if not is_direct and not is_inverse:
            raise ValueError("Exchange rate does not match the provided currencies.")

        # 3. Execution: Apply correct mathematical operation based on direction
        if is_direct:
            raw_result: Decimal = amount * exchange_rate.rate
        else:
            raw_result: Decimal = amount / exchange_rate.rate

        # 4. Financial Rounding: Strictly enforce 2 decimal points using banking standard
        # The string "0.01" serves as the quantization pattern for two decimal places.
        return raw_result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
