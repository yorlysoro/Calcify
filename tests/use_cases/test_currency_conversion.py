import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session

from domain.models import Currency, CurrencyRate
from use_cases.currency_conversion import CurrencyConversionUseCase
from infrastructure.repositories.sqlalchemy_repos import (
    SqlAlchemyCurrencyRepository,
    SqlAlchemyCurrencyRateRepository,
)
from infrastructure.database.models import CurrencyModel


def seed_currencies_and_rates(db_session: Session) -> None:
    """Helper to seed Bs (main), USD (rate=500), EUR (rate=600)."""
    db_session.merge(CurrencyModel(code="BS", name="Bolivar", symbol="Bs", is_main=True))
    db_session.merge(CurrencyModel(code="USD", name="US Dollar", symbol="$", is_main=False))
    db_session.merge(CurrencyModel(code="EUR", name="Euro", symbol="\u20ac", is_main=False))
    db_session.commit()

    rate_repo = SqlAlchemyCurrencyRateRepository(db_session)
    now = datetime.now(timezone.utc)
    rate_repo.save(CurrencyRate(id=uuid4(), currency_code="USD", rate=Decimal("500"), created_at=now))
    rate_repo.save(CurrencyRate(id=uuid4(), currency_code="EUR", rate=Decimal("600"), created_at=now))
    db_session.commit()


def test_convert_non_main_to_main_usd_to_bs(db_session: Session) -> None:
    """10 USD → Bs (main): 10 * 1 / 0.002 = 5000.0000"""
    seed_currencies_and_rates(db_session)
    currency_repo = SqlAlchemyCurrencyRepository(db_session)
    rate_repo = SqlAlchemyCurrencyRateRepository(db_session)
    use_case = CurrencyConversionUseCase(
        currency_repo=currency_repo,
        rate_repo=rate_repo,
    )

    result = use_case.execute(
        source_currency_code="USD",
        target_currency_code="BS",
        amount=Decimal("10"),
    )

    assert result["source_currency_code"] == "USD"
    assert result["target_currency_code"] == "BS"
    assert result["amount"] == Decimal("10")
    assert result["result"] == Decimal("5000.0000")


def test_convert_main_to_non_main_bs_to_usd(db_session: Session) -> None:
    """5000 Bs (main) → USD: 5000 * 0.002 / 1 = 10.0000"""
    seed_currencies_and_rates(db_session)
    currency_repo = SqlAlchemyCurrencyRepository(db_session)
    rate_repo = SqlAlchemyCurrencyRateRepository(db_session)
    use_case = CurrencyConversionUseCase(
        currency_repo=currency_repo,
        rate_repo=rate_repo,
    )

    result = use_case.execute(
        source_currency_code="BS",
        target_currency_code="USD",
        amount=Decimal("5000"),
    )

    assert result["result"] == Decimal("10.0000")


def test_convert_cross_currency_usd_to_eur(db_session: Session) -> None:
    """10 USD → EUR: 10 * 0.001666667 / 0.002 = 8.3333"""
    seed_currencies_and_rates(db_session)
    currency_repo = SqlAlchemyCurrencyRepository(db_session)
    rate_repo = SqlAlchemyCurrencyRateRepository(db_session)
    use_case = CurrencyConversionUseCase(
        currency_repo=currency_repo,
        rate_repo=rate_repo,
    )

    result = use_case.execute(
        source_currency_code="USD",
        target_currency_code="EUR",
        amount=Decimal("10"),
    )

    assert result["result"] == Decimal("8.3333")


def test_convert_cross_currency_eur_to_usd(db_session: Session) -> None:
    """10 EUR → USD: 10 * 0.002 / 0.001666667 = 12.0000"""
    seed_currencies_and_rates(db_session)
    currency_repo = SqlAlchemyCurrencyRepository(db_session)
    rate_repo = SqlAlchemyCurrencyRateRepository(db_session)
    use_case = CurrencyConversionUseCase(
        currency_repo=currency_repo,
        rate_repo=rate_repo,
    )

    result = use_case.execute(
        source_currency_code="EUR",
        target_currency_code="USD",
        amount=Decimal("10"),
    )

    assert result["result"] == Decimal("12.0000")


def test_convert_main_to_main(db_session: Session) -> None:
    """Main → Main: amount unchanged."""
    db_session.merge(CurrencyModel(code="GBP", name="Pound", symbol="\u00a3", is_main=True))
    db_session.flush()

    currency_repo = SqlAlchemyCurrencyRepository(db_session)
    rate_repo = SqlAlchemyCurrencyRateRepository(db_session)
    use_case = CurrencyConversionUseCase(
        currency_repo=currency_repo,
        rate_repo=rate_repo,
    )

    result = use_case.execute(
        source_currency_code="GBP",
        target_currency_code="GBP",
        amount=Decimal("100"),
    )

    assert result["result"] == Decimal("100.0000")


def test_raises_error_when_no_main_currency(db_session: Session) -> None:
    """No currency marked as main should raise ValueError."""
    db_session.execute(text("DELETE FROM currencies"))
    db_session.merge(CurrencyModel(code="JPY", name="Yen", symbol="\u00a5", is_main=False))
    db_session.commit()

    currency_repo = SqlAlchemyCurrencyRepository(db_session)
    rate_repo = SqlAlchemyCurrencyRateRepository(db_session)
    use_case = CurrencyConversionUseCase(
        currency_repo=currency_repo,
        rate_repo=rate_repo,
    )

    with pytest.raises(ValueError, match="No main currency configured"):
        use_case.execute("JPY", "JPY", Decimal("10"))


def test_raises_error_when_source_currency_not_found(db_session: Session) -> None:
    """Non-existent source currency should raise ValueError."""
    db_session.execute(text("DELETE FROM currencies"))
    db_session.merge(CurrencyModel(code="CHF", name="Franc", symbol="Fr", is_main=True))
    db_session.commit()

    currency_repo = SqlAlchemyCurrencyRepository(db_session)
    rate_repo = SqlAlchemyCurrencyRateRepository(db_session)
    use_case = CurrencyConversionUseCase(
        currency_repo=currency_repo,
        rate_repo=rate_repo,
    )

    with pytest.raises(ValueError, match="Source currency.*not found"):
        use_case.execute("XYZ", "CHF", Decimal("10"))


def test_raises_error_when_target_currency_not_found(db_session: Session) -> None:
    """Non-existent target currency should raise ValueError."""
    db_session.execute(text("DELETE FROM currencies"))
    db_session.merge(CurrencyModel(code="CAD", name="Dollar", symbol="$", is_main=True))
    db_session.commit()

    currency_repo = SqlAlchemyCurrencyRepository(db_session)
    rate_repo = SqlAlchemyCurrencyRateRepository(db_session)
    use_case = CurrencyConversionUseCase(
        currency_repo=currency_repo,
        rate_repo=rate_repo,
    )

    with pytest.raises(ValueError, match="Target currency.*not found"):
        use_case.execute("CAD", "XYZ", Decimal("10"))


def test_raises_error_when_no_rate_for_source(db_session: Session) -> None:
    """Source currency without a rate (and not main) should raise ValueError."""
    db_session.execute(text("DELETE FROM currencies"))
    db_session.merge(CurrencyModel(code="MXN", name="Mexican Peso", symbol="$", is_main=False))
    db_session.merge(CurrencyModel(code="ARS", name="Argentine Peso", symbol="$", is_main=True))
    db_session.commit()

    currency_repo = SqlAlchemyCurrencyRepository(db_session)
    rate_repo = SqlAlchemyCurrencyRateRepository(db_session)
    use_case = CurrencyConversionUseCase(
        currency_repo=currency_repo,
        rate_repo=rate_repo,
    )

    with pytest.raises(ValueError, match="No exchange rate found for source"):
        use_case.execute("MXN", "ARS", Decimal("10"))


def test_raises_error_when_no_rate_for_target(db_session: Session) -> None:
    """Target currency without a rate (and not main) should raise ValueError."""
    db_session.execute(text("DELETE FROM currencies"))
    db_session.merge(CurrencyModel(code="COP", name="Colombian Peso", symbol="$", is_main=True))
    db_session.merge(CurrencyModel(code="CLP", name="Chilean Peso", symbol="$", is_main=False))
    db_session.commit()

    currency_repo = SqlAlchemyCurrencyRepository(db_session)
    rate_repo = SqlAlchemyCurrencyRateRepository(db_session)
    use_case = CurrencyConversionUseCase(
        currency_repo=currency_repo,
        rate_repo=rate_repo,
    )

    with pytest.raises(ValueError, match="No exchange rate found for target"):
        use_case.execute("COP", "CLP", Decimal("10"))
