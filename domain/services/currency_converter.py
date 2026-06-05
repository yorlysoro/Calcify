from decimal import Decimal, ROUND_HALF_UP

from domain.exceptions import InvalidExchangeRateError


class CurrencyConverter:
    """
    A stateless domain service for currency conversion using Decimal math.

    Converts monetary amounts using pre-calculated inverse exchange rates
    relative to the base currency. Formula: (amount * source_inverse) / target_inverse
    """

    @staticmethod
    def convert(
        amount: Decimal,
        source_inverse: Decimal,
        target_inverse: Decimal,
    ) -> Decimal:
        """
        Converts an amount using source and target inverse exchange rates.

        Formula: (amount * source_inverse) / target_inverse

        Args:
            amount (Decimal): The monetary value to convert.
            source_inverse (Decimal): Inverse rate of the source currency (1/rate).
            target_inverse (Decimal): Inverse rate of the target currency (1/rate).

        Returns:
            Decimal: The converted amount rounded to 4 decimal places.

        Raises:
            InvalidExchangeRateError: If either inverse rate is zero.
        """
        src_inv: Decimal = Decimal(str(source_inverse))
        tgt_inv: Decimal = Decimal(str(target_inverse))

        if src_inv == Decimal("0") or tgt_inv == Decimal("0"):
            raise InvalidExchangeRateError("Exchange rate cannot be zero.")

        result: Decimal = (amount * src_inv) / tgt_inv
        return result.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
