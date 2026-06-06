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
        self._currency_repo: ICurrencyRepository = currency_repo
        self._rate_repo: ICurrencyRateRepository = rate_repo

    def execute(
        self,
        source_currency_code: str,
        target_currency_code: str,
        amount: Decimal,
    ) -> Dict[str, Union[str, Decimal]]:
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
