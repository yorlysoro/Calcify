from decimal import Decimal, ROUND_HALF_UP

from domain.exceptions import InvalidExchangeRateError


class CurrencyConverter:
    """
    A stateless domain service for currency conversion using Decimal math.

    Converts monetary amounts through the main/base currency using pre-calculated
    inverse exchange rates. Formula: (amount * target_inverse) / source_inverse

    This ensures all conversions flow through the main currency:
      1. Convert source to main:  amount / source_inverse = amount * source_rate
      2. Convert main to target:  (amount in main) * target_inverse
      3. Combined: amount * target_inverse / source_inverse
    """

    @staticmethod
    def convert(
        amount: Decimal,
        source_inverse: Decimal,
        target_inverse: Decimal,
    ) -> Decimal:
        """
        Converts an amount using source and target inverse exchange rates.

        Always routes through the main/base currency for precision.

        Formula: (amount * target_inverse) / source_inverse

        Args:
            amount (Decimal): The monetary value to convert.
            source_inverse (Decimal): Inverse rate of the source currency (1/rate).
                                      Pass Decimal("1") if source is the main currency.
            target_inverse (Decimal): Inverse rate of the target currency (1/rate).
                                      Pass Decimal("1") if target is the main currency.

        Returns:
            Decimal: The converted amount rounded to 4 decimal places.

        Raises:
            InvalidExchangeRateError: If either inverse rate is zero.
        """
        src_inv: Decimal = Decimal(str(source_inverse))
        tgt_inv: Decimal = Decimal(str(target_inverse))

        if src_inv == Decimal("0") or tgt_inv == Decimal("0"):
            raise InvalidExchangeRateError("Exchange rate cannot be zero.")

        result: Decimal = (amount * tgt_inv) / src_inv
        return result.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
