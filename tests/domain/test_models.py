import pytest
from uuid import uuid4
from decimal import Decimal
from domain.models import Product

def test_product_entity_includes_category_with_default_value() -> None:
    """
    TDD Red Phase: Verifies that the Product domain entity natively 
    supports a category field with a strict default fallback.
    """
    test_id = uuid4()
    
    # Intentionally omitting 'category' from kwargs
    product = Product(
        id=test_id,
        name="Harina PAN",
        cost_price=Decimal("1.00"),
        cost_currency_code="USD",
        margin_percentage=Decimal("30.00")
    )
    
    assert hasattr(product, 'category'), "Product entity is missing the 'category' attribute."
    assert product.category == "Uncategorized", "Default category fallback failed."
