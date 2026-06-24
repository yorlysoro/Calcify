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

"""Tests for the CurrencyConverter domain service."""

from decimal import Decimal

from domain.services.currency_converter import CurrencyConverter
from domain.exceptions import InvalidExchangeRateError

# Arbitrary test constants (main = USD)
VES_RATE: Decimal = Decimal("548.59")
VES_INVERSE: Decimal = Decimal("1") / VES_RATE
EUR_RATE: Decimal = Decimal("0.92")
EUR_INVERSE: Decimal = Decimal("1") / EUR_RATE

# Realistic example constants (main = Bs)
#   rate  = how many main currency units per 1 unit of this currency
#   inverse = 1/rate
BS_USD_RATE: Decimal = Decimal("500")
BS_USD_INVERSE: Decimal = Decimal("1") / BS_USD_RATE  # 0.002
BS_EUR_RATE: Decimal = Decimal("600")
BS_EUR_INVERSE: Decimal = Decimal("1") / BS_EUR_RATE  # 0.001666667


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


def test_no_float_type_hints_in_domain_services() -> None:
    """Structural test: domain services must not use float for monetary params."""
    import inspect
    from domain.services import CurrencyConverter

    with_invalid: list[str] = []
    for name, method in inspect.getmembers(CurrencyConverter, predicate=inspect.isfunction):
        sig = inspect.signature(method)
        for pname, param in sig.parameters.items():
            if pname == "self":
                continue
            hint_raw = param.annotation
            if isinstance(hint_raw, str) and hint_raw == "float":
                with_invalid.append(f"{name}.{pname}")
            elif hint_raw is float:
                with_invalid.append(f"{name}.{pname}")
        ret = sig.return_annotation
        if isinstance(ret, str) and ret == "float":
            with_invalid.append(f"{name}.return")
        elif ret is float:
            with_invalid.append(f"{name}.return")

    assert not with_invalid, (
        f"Domain services use float instead of Decimal: {with_invalid}"
    )


def test_main_to_main_identity() -> None:
    """
    Main → Main: both inverses are 1, amount stays unchanged.
    Formula: (amount * 1) / 1 = amount
    """
    result: Decimal = CurrencyConverter.convert(
        Decimal("100"), Decimal("1"), Decimal("1"),
    )
    assert result == Decimal("100.0000")


def test_convert_main_to_non_main() -> None:
    """
    Main (inv=1) → VES (inv=VES_INVERSE):
    Formula: (100 * VES_INVERSE) / 1 = 100 / VES_RATE = 0.1823
    """
    result: Decimal = CurrencyConverter.convert(
        Decimal("100"), Decimal("1"), VES_INVERSE,
    )
    assert result == Decimal("0.1823")


def test_convert_non_main_to_main() -> None:
    """
    VES (inv=VES_INVERSE) → Main (inv=1):
    Formula: (100 * 1) / VES_INVERSE = 100 * VES_RATE = 54859.0000
    """
    result: Decimal = CurrencyConverter.convert(
        Decimal("100"), VES_INVERSE, Decimal("1"),
    )
    assert result == Decimal("54859.0000")


def test_convert_cross_currency() -> None:
    """
    EUR (inv=EUR_INVERSE) → VES (inv=VES_INVERSE):
    Formula: (100 * VES_INVERSE) / EUR_INVERSE = 100 * 0.92 / 548.59 = 0.1677
    """
    result: Decimal = CurrencyConverter.convert(
        Decimal("100"), EUR_INVERSE, VES_INVERSE,
    )
    assert result == Decimal("0.1677")


def test_convert_main_to_non_main_bs_usd() -> None:
    """
    User example: Main (Bs) → USD
    amount=5000 Bs, source_inv=1, target_inv=0.002
    Formula: (5000 * 0.002) / 1 = 10.0000 USD
    """
    result: Decimal = CurrencyConverter.convert(
        Decimal("5000"), Decimal("1"), BS_USD_INVERSE,
    )
    assert result == Decimal("10.0000")


def test_convert_non_main_to_main_usd_bs() -> None:
    """
    User example: USD → Main (Bs)
    amount=10 USD, source_inv=0.002, target_inv=1
    Formula: (10 * 1) / 0.002 = 5000.0000 Bs
    """
    result: Decimal = CurrencyConverter.convert(
        Decimal("10"), BS_USD_INVERSE, Decimal("1"),
    )
    assert result == Decimal("5000.0000")


def test_convert_cross_currency_usd_to_eur() -> None:
    """
    User example: USD → EUR (main=Bs)
    amount=10 USD, source_inv=0.002, target_inv=0.001666667
    Formula: (10 * 0.001666667) / 0.002 = 8.3333
    """
    result: Decimal = CurrencyConverter.convert(
        Decimal("10"), BS_USD_INVERSE, BS_EUR_INVERSE,
    )
    assert result == Decimal("8.3333")


def test_convert_cross_currency_eur_to_usd() -> None:
    """
    User example: EUR → USD (main=Bs)
    amount=10 EUR, source_inv=0.001666667, target_inv=0.002
    Formula: (10 * 0.002) / 0.001666667 = 12.0000
    """
    result: Decimal = CurrencyConverter.convert(
        Decimal("10"), BS_EUR_INVERSE, BS_USD_INVERSE,
    )
    assert result == Decimal("12.0000")


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
