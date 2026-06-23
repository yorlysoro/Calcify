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

import pytest
from datetime import datetime, timezone
from decimal import Decimal

# Future imports from our Clean Architecture domain
from domain.models import Currency, ExchangeRate

# The following modules do not exist yet. TDD dictates we import them
# and let the tests fail until we write the implementation.
from domain.services import CurrencyConverter
from domain.exceptions import InvalidExchangeRateError


@pytest.fixture
def converter() -> CurrencyConverter:
    """Fixture providing a fresh instance of the domain service."""
    return CurrencyConverter()


@pytest.fixture
def usd() -> Currency:
    """Fixture for US Dollar domain entity."""
    return Currency(code="USD", name="US Dollar", symbol="$", is_main=True)


@pytest.fixture
def ves() -> Currency:
    """Fixture for Venezuelan Bolivar domain entity."""
    return Currency(code="VES", name="Venezuelan Bolivar", symbol="Bs.", is_main=False)


@pytest.fixture
def usd_to_ves_rate() -> ExchangeRate:
    """Fixture providing a standard 36.50 exchange rate from USD to VES."""
    return ExchangeRate(
        base_currency_code="USD",
        target_currency_code="VES",
        rate=Decimal("36.50"),
        date=datetime.now(timezone.utc),
    )


def test_normal_conversion_direct_multiplication(
    converter: CurrencyConverter,
    usd: Currency,
    ves: Currency,
    usd_to_ves_rate: ExchangeRate,
) -> None:
    """
    Tests standard conversion where the source matches the rate's base currency.
    Operation: amount * rate
    """
    amount: Decimal = Decimal("10.00")
    expected_result: Decimal = Decimal("365.00")

    result: Decimal = converter.convert(amount, usd, ves, usd_to_ves_rate)

    assert result == expected_result


def test_inverse_conversion_division(
    converter: CurrencyConverter,
    usd: Currency,
    ves: Currency,
    usd_to_ves_rate: ExchangeRate,
) -> None:
    """
    Tests mathematical inverse conversion where the source matches the rate's target currency.
    Operation: amount / rate
    """
    amount: Decimal = Decimal("365.00")
    expected_result: Decimal = Decimal("10.00")

    # We pass VES as from_currency and USD as to_currency.
    # The converter must detect the inversion and apply division.
    result: Decimal = converter.convert(amount, ves, usd, usd_to_ves_rate)

    assert result == expected_result


def test_zero_exchange_rate_raises_invalid_rate_error(
    converter: CurrencyConverter, usd: Currency, ves: Currency
) -> None:
    """
    Tests that a 0.00 rate raises a domain-specific exception to prevent ZeroDivisionError.
    """
    zero_rate: ExchangeRate = ExchangeRate(
        base_currency_code="USD",
        target_currency_code="VES",
        rate=Decimal("0.00"),
        date=datetime.now(timezone.utc),
    )

    with pytest.raises(InvalidExchangeRateError):
        converter.convert(Decimal("10.00"), usd, ves, zero_rate)


def test_strict_financial_rounding_to_two_decimals(
    converter: CurrencyConverter,
    usd: Currency,
    ves: Currency,
    usd_to_ves_rate: ExchangeRate,
) -> None:
    """
    Tests that conversion logic strictly applies financial rounding (ROUND_HALF_UP)
    to a maximum of 2 decimal places.
    """
    amount: Decimal = Decimal("10.015")
    # Mathematical calculation: 10.015 * 36.50 = 365.5475
    # Financial rounding (Half Up) to 2 decimals -> 365.55
    expected_result: Decimal = Decimal("365.55")

    result: Decimal = converter.convert(amount, usd, ves, usd_to_ves_rate)

    assert result == expected_result


def test_conversion_with_unrelated_rate_raises_value_error(
    converter: CurrencyConverter, usd: Currency, ves: Currency
) -> None:
    """
    Tests that passing an ExchangeRate object whose base/target currencies
    do not match the requested conversion currencies raises a ValueError.
    """
    # E.g., trying to convert USD to VES using a EUR to VES rate
    eur_to_ves_rate: ExchangeRate = ExchangeRate(
        base_currency_code="EUR",
        target_currency_code="VES",
        rate=Decimal("40.00"),
        date=datetime.now(timezone.utc),
    )

    # regex match for explicit failure context
    with pytest.raises(
        ValueError, match="Exchange rate does not match the provided currencies"
    ):
        converter.convert(Decimal("10.00"), usd, ves, eur_to_ves_rate)
