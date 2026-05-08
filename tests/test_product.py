import pytest
from uuid import uuid4, UUID
from decimal import Decimal
from datetime import datetime

# Assuming your imports are structured this way
from domain.models import Product, Currency, ExchangeRate
from domain.services import CurrencyConverter


@pytest.fixture
def converter() -> CurrencyConverter:
    """Fixture providing the stateless domain service."""
    return CurrencyConverter()


@pytest.fixture
def usd() -> Currency:
    return Currency(code="USD", name="US Dollar", symbol="$", is_main=True)


@pytest.fixture
def ves() -> Currency:
    return Currency(code="VES", name="Venezuelan Bolivar", symbol="Bs.", is_main=False)


@pytest.fixture
def rate_usd_ves() -> ExchangeRate:
    return ExchangeRate(
        base_currency_code="USD",
        target_currency_code="VES",
        rate=Decimal("36.50"),
        date=datetime.now(),
    )


@pytest.fixture
def test_product() -> Product:
    """Fixture for a standard product with a 30% margin."""
    return Product(
        id=uuid4(),
        name="Mechanical Keyboard Architect Edition",
        cost_price=Decimal("100.00"),
        cost_currency_code="USD",
        margin_percentage=Decimal("30.00"),
    )


def test_product_calculate_sale_price(test_product: Product) -> None:
    """
    Tests that a 30% margin on a 100.00 cost results in a 130.00 sale price.
    """
    expected_price: Decimal = Decimal("130.00")
    assert test_product.calculate_sale_price() == expected_price


def test_product_calculate_sale_price_rounding() -> None:
    """
    Tests strict financial rounding (ROUND_HALF_UP) for complex margins.
    Cost: 100.00, Margin: 33.33% -> Raw: 133.33.
    """
    product: Product = Product(
        id=uuid4(),
        name="Odd Margin Item",
        cost_price=Decimal("45.55"),
        cost_currency_code="USD",
        margin_percentage=Decimal("15.25"),
    )
    # 45.55 * (1 + 15.25/100) = 45.55 * 1.1525 = 52.496375
    # Round Half Up to 2 decimals -> 52.50
    expected_price: Decimal = Decimal("52.50")
    assert product.calculate_sale_price() == expected_price


def test_product_get_sale_price_in_currency(
    test_product: Product,
    usd: Currency,
    ves: Currency,
    converter: CurrencyConverter,
    rate_usd_ves: ExchangeRate,
) -> None:
    """
    Tests the integration between the Product's sale price logic and
    the CurrencyConverter domain service.
    """
    # Sale price in USD is 130.00. Rate is 36.50.
    # 130.00 * 36.50 = 4745.00
    expected_ves_price: Decimal = Decimal("4745.00")

    result: Decimal = test_product.get_sale_price_in_currency(
        base_currency=usd,
        target_currency=ves,
        converter=converter,
        current_rate=rate_usd_ves,
    )

    assert result == expected_ves_price


def test_product_rejects_invalid_base_currency(
    test_product: Product,
    ves: Currency,
    converter: CurrencyConverter,
    rate_usd_ves: ExchangeRate,
) -> None:
    """
    Tests that injecting a base currency that does not match the product's
    internal cost_currency_code raises a ValueError.
    """
    # Passing VES as base currency when the product is in USD
    # Using a raw string (r"") and wildcard (.*) to handle the dynamic f-string
    # injection inside the ValueError message: "(VES)" and "(USD)".
    # The regex explicitly checks the start and the core of the message
    expected_error_pattern: str = r"Base currency provided \(.*\) does not match"
    with pytest.raises(ValueError, match=expected_error_pattern):
        test_product.get_sale_price_in_currency(
            base_currency=ves,
            target_currency=ves,
            converter=converter,
            current_rate=rate_usd_ves,
        )
