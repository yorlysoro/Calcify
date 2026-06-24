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
Currency conversion use case for the Calcify application.

Provides the CurrencyConversionUseCase that converts monetary amounts between
currencies through the main/base currency using pre-calculated inverse rates.
"""

from decimal import Decimal
from typing import Dict, Union, Optional

from domain.models import Currency, CurrencyRate
from domain.services.currency_converter import CurrencyConverter
from domain.exceptions import InvalidExchangeRateError
from infrastructure.repositories.interfaces import (
    ICurrencyRepository,
    ICurrencyRateRepository,
)


class CurrencyConversionUseCase:
    """
    Use case that converts an amount from one currency to another,
    always routing through the main/base currency.

    Flow:
      1. Look up the main currency (is_main=True)
      2. Get inverse_rate for source currency (1.0 if main)
      3. Get inverse_rate for target currency (1.0 if main)
      4. Apply the formula: amount * target_inverse / source_inverse
    """

    def __init__(
        self,
        currency_repo: ICurrencyRepository,
        rate_repo: ICurrencyRateRepository,
    ) -> None:
        """Initializes the conversion use case with repository dependencies.

        Args:
            currency_repo: Repository for currency lookup operations.
            rate_repo: Repository for exchange rate retrieval.
        """
        self._currency_repo: ICurrencyRepository = currency_repo
        self._rate_repo: ICurrencyRateRepository = rate_repo

    def execute(
        self,
        source_currency_code: str,
        target_currency_code: str,
        amount: Decimal,
    ) -> Dict[str, Union[str, Decimal]]:
        """Converts an amount from source to target currency via the main currency.

        Args:
            source_currency_code: ISO 4217 code of the source currency.
            target_currency_code: ISO 4217 code of the target currency.
            amount: The monetary amount to convert.

        Returns:
            A dictionary with keys: source_currency_code, target_currency_code,
            amount, result, and rate.

        Raises:
            ValueError: If the main currency is not configured, either currency
                is unknown, or exchange rates are missing.
        """
        source_code: str = source_currency_code.upper()
        target_code: str = target_currency_code.upper()

        # 1. Resolve the main currency
        all_currencies = self._currency_repo.get_all()
        main_currency: Optional[Currency] = next(
            (c for c in all_currencies if c.is_main), None,
        )
        if main_currency is None:
            raise ValueError("No main currency configured in the system.")

        # 2. Validate source currency exists
        source_currency: Optional[Currency] = self._currency_repo.get_by_code(source_code)
        if source_currency is None:
            raise ValueError(f"Source currency '{source_code}' not found.")

        # 3. Validate target currency exists
        target_currency: Optional[Currency] = self._currency_repo.get_by_code(target_code)
        if target_currency is None:
            raise ValueError(f"Target currency '{target_code}' not found.")

        # 4. Determine inverse rates
        source_inverse: Decimal
        if source_currency.is_main:
            source_inverse = Decimal("1")
        else:
            source_rate: Optional[CurrencyRate] = self._rate_repo.get_latest_by_code(source_code)
            if source_rate is None:
                raise ValueError(f"No exchange rate found for source currency '{source_code}'.")
            source_inverse = source_rate.inverse_rate

        target_inverse: Decimal
        if target_currency.is_main:
            target_inverse = Decimal("1")
        else:
            target_rate: Optional[CurrencyRate] = self._rate_repo.get_latest_by_code(target_code)
            if target_rate is None:
                raise ValueError(f"No exchange rate found for target currency '{target_code}'.")
            target_inverse = target_rate.inverse_rate

        # 5. Execute conversion through the domain service
        try:
            result: Decimal = CurrencyConverter.convert(
                amount=amount,
                source_inverse=source_inverse,
                target_inverse=target_inverse,
            )
        except InvalidExchangeRateError as e:
            raise ValueError(str(e)) from e

        # 6. Calculate the effective exchange rate used
        effective_rate: Decimal = target_inverse / source_inverse

        return {
            "source_currency_code": source_code,
            "target_currency_code": target_code,
            "amount": amount,
            "result": result,
            "rate": effective_rate,
        }
