from decimal import Decimal

from domain.services.currency_converter import CurrencyConverter
from domain.exceptions import InvalidExchangeRateError


VES_RATE: Decimal = Decimal("548.59")
VES_INVERSE: Decimal = Decimal("1") / VES_RATE
EUR_RATE: Decimal = Decimal("0.92")
EUR_INVERSE: Decimal = Decimal("1") / EUR_RATE


def test_inverse_multiplication_precision() -> None:
    """Verifies that inverse_rate * amount rounds to 4 decimals correctly."""
    result: Decimal = VES_INVERSE * Decimal("100")
    rounded: Decimal = result.quantize(Decimal("0.0001"))
    assert rounded == Decimal("0.1823")


def test_inverse_rate_multiplication_identity() -> None:
    """Verifies that inverse_rate * rate * 100 = 100 (identity check)."""
    result: Decimal = VES_INVERSE * VES_RATE * Decimal("100")
    rounded: Decimal = result.quantize(Decimal("0.0001"))
    assert rounded == Decimal("100.0000")


def test_convert_base_to_target() -> None:
    """
    Base (USD) to Target (VES):
    amount=100, source_inverse=1, target_inverse=VES_INVERSE
    Expected: (100 * 1) / VES_INVERSE = 100 * VES_RATE = 54859.0000
    """
    result: Decimal = CurrencyConverter.convert(
        Decimal("100"), Decimal("1"), VES_INVERSE,
    )
    assert result == Decimal("54859.0000")


def test_convert_target_to_base() -> None:
    """
    Target (VES) to Base (USD):
    amount=54859, source_inverse=VES_INVERSE, target_inverse=1
    Expected: (54859 * VES_INVERSE) / 1 = 100.0000
    """
    result: Decimal = CurrencyConverter.convert(
        Decimal("54859"), VES_INVERSE, Decimal("1"),
    )
    assert result == Decimal("100.0000")


def test_convert_cross_currency() -> None:
    """
    Cross Currency (EUR to VES where Base is USD):
    amount=100, source_inverse=EUR_INVERSE, target_inverse=VES_INVERSE
    Expected: (100 * EUR_INVERSE) / VES_INVERSE = 100 * EUR_INVERSE * VES_RATE = 59629.3478
    """
    result: Decimal = CurrencyConverter.convert(
        Decimal("100"), EUR_INVERSE, VES_INVERSE,
    )
    assert result == Decimal("59629.3478")


def test_convert_zero_source_inverse_raises_error() -> None:
    """Zero source inverse must raise InvalidExchangeRateError."""
    try:
        CurrencyConverter.convert(Decimal("100"), Decimal("0"), VES_INVERSE)
        assert False, "Expected InvalidExchangeRateError"
    except InvalidExchangeRateError:
        pass


def test_convert_zero_target_inverse_raises_error() -> None:
    """Zero target inverse must raise InvalidExchangeRateError."""
    try:
        CurrencyConverter.convert(Decimal("100"), Decimal("1"), Decimal("0"))
        assert False, "Expected InvalidExchangeRateError"
    except InvalidExchangeRateError:
        pass
