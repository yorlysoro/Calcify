import pytest
from uuid import uuid4, UUID
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session

# Pure Domain imports
from domain.models import Product, Currency

# Infrastructure imports
from infrastructure.database.models import CurrencyModel
from infrastructure.repositories.sqlalchemy_repos import (
    SqlAlchemyProductRepository,
    SqlAlchemyCurrencyRepository
)


def test_product_repository_save_does_not_raise_error(db_session: Session) -> None:
    """
    Verifies that persisting a valid pure Product domain entity does not raise 
    any database exceptions, confirming the schema mapping is correct.
    """
    # <AAA> stands for Arrange, Act, Assert
    # Arrange
    repo: SqlAlchemyProductRepository = SqlAlchemyProductRepository(db_session)
    new_product: Product = Product(
        id=uuid4(),
        name="Mechanical Keyboard Architect Edition",
        cost_price=Decimal("120.00"),
        cost_currency_code="USD",
        margin_percentage=Decimal("35.00")
    )

    # Act & Assert
    try:
        repo.save(new_product)
        # We explicitly commit to test the actual DB flush constraints.
        # The pytest savepoint fixture prevents this from polluting other tests.
        db_session.commit()
    except Exception as e:
        pytest.fail(f"Saving the product raised an unexpected exception: {e}")


def test_product_repository_retrieves_pure_domain_entity(db_session: Session) -> None:
    """
    Enforces the strict Clean Architecture boundary rule:
    The repository MUST return a pure Python domain entity, NEVER an ORM model.
    """
    # Arrange
    repo: SqlAlchemyProductRepository = SqlAlchemyProductRepository(db_session)
    product_id: UUID = uuid4()
    domain_product: Product = Product(
        id=product_id,
        name="Pythonic Coffee Mug",
        cost_price=Decimal("15.50"),
        cost_currency_code="USD",
        margin_percentage=Decimal("50.00")
    )
    
    repo.save(domain_product)
    db_session.commit()

    # Act
    retrieved_product: Optional[Product] = repo.get_by_id(product_id)

    # Assert
    assert retrieved_product is not None
    # STRICT RULE: Must be a pure domain entity
    assert isinstance(retrieved_product, Product), "Repository leaked an ORM model instead of a pure Domain entity!"
    # Verify data integrity
    assert retrieved_product.id == product_id
    assert retrieved_product.cost_price == Decimal("15.50")


def test_currency_repository_list_and_filter_main_currency(db_session: Session) -> None:
    """
    Tests fetching all currencies and filtering them using domain logic.
    Ensures ORM booleans are correctly mapped to Domain booleans.
    """
    # Arrange: Seed the database directly using ORM models
    # We create three currencies, but only one is main.
    usd_model = CurrencyModel(code="USD", name="US Dollar", symbol="$", is_main=True)
    eur_model = CurrencyModel(code="EUR", name="Euro", symbol="€", is_main=False)
    ves_model = CurrencyModel(code="VES", name="Bolivar", symbol="Bs", is_main=False)
    
    db_session.add_all([usd_model, eur_model, ves_model])
    db_session.commit()

    repo: SqlAlchemyCurrencyRepository = SqlAlchemyCurrencyRepository(db_session)

    # Act: Retrieve all domain entities from the repository
    all_currencies: List[Currency] = repo.get_all()

    # Apply Pythonic filtering using list comprehensions
    main_currencies: List[Currency] = [c for c in all_currencies if c.is_main is True]

    # Assert
    assert len(all_currencies) == 3, "Failed to retrieve all seeded currencies."
    assert len(main_currencies) == 1, "There should be exactly one main currency."
    
    main_currency: Currency = main_currencies[0]
    # Verify pure domain entity boundary
    assert isinstance(main_currency, Currency)
    assert main_currency.code == "USD"
    assert main_currency.is_main is True
