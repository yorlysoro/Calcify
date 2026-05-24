import logging
from typing import Optional, Tuple, Dict, Any, List
from uuid import UUID
from decimal import Decimal, InvalidOperation

from flask import Blueprint, request, jsonify, g, Response

# Pure Domain Imports
from domain.models import Product, Currency

# Infrastructure Imports (Adapters only, NO ORM models)
from infrastructure.repositories.sqlalchemy_repos import (
    SqlAlchemyProductRepository,
    SqlAlchemyCurrencyRepository,
)

logger: logging.Logger = logging.getLogger(__name__)

# <BP> stands for Blueprint. Groups related routes under a common URL prefix.
api_bp: Blueprint = Blueprint("api", __name__, url_prefix="/api/v1")


@api_bp.route("/currencies", methods=["GET"])
def get_currencies() -> Tuple[Response, int]:
    """
    Retrieves all available currencies from the domain.
    """
    # 1. Dependency Injection via Flask's global request context 'g'
    repo = SqlAlchemyCurrencyRepository(session=g.db_session)

    try:
        # 2. Fetch Pure Domain Entities
        currencies: List[Currency] = repo.get_all()

        # 3. Serialization: Domain Entities to JSON-serializable dictionaries
        # Using list comprehension for O(N) efficient mapping
        response_data: List[Dict[str, Any]] = [
            {"code": c.code, "name": c.name, "symbol": c.symbol, "is_main": c.is_main}
            for c in currencies
        ]

        return jsonify({"data": response_data}), 200

    except Exception as e:
        logger.error(f"Failed to fetch currencies: {str(e)}")
        return (
            jsonify({"error": "Internal server error while fetching currencies."}),
            500,
        )


@api_bp.route("/products", methods=["POST"])
def create_product() -> Tuple[Response, int]:
    """
    Creates a new Product in the system.
    Expects a JSON payload with id, name, cost_price, cost_currency_code, and margin_percentage.
    """
    payload: Optional[Dict[str, Any]] = request.get_json()
    if not payload:
        return jsonify({"error": "Invalid or missing JSON payload."}), 400

    repo = SqlAlchemyProductRepository(session=g.db_session)

    try:
        # 1. Edge Validation & Type Casting
        # We strictly convert incoming generic types to our Domain constraints.
        product_id = UUID(payload["id"])
        name = str(payload["name"])
        cost_price = Decimal(str(payload["cost_price"]))
        cost_currency_code = str(payload["cost_currency_code"])
        margin_percentage = Decimal(str(payload["margin_percentage"]))

        # 2. Instantiate Pure Domain Entity
        new_product = Product(
            id=product_id,
            name=name,
            cost_price=cost_price,
            cost_currency_code=cost_currency_code,
            margin_percentage=margin_percentage,
        )

        # 3. Persistence (Unit of Work)
        repo.save(new_product)
        g.db_session.commit()

        # 4. Response formatting
        return (
            jsonify(
                {
                    "message": "Product created successfully.",
                    "data": {"id": str(new_product.id)},
                }
            ),
            201,
        )

    except KeyError as e:
        # Catching missing dictionary keys
        return jsonify({"error": f"Missing required field: {str(e)}"}), 400
    except ValueError:
        # Catching invalid UUID formats
        return jsonify({"error": "Invalid UUID format provided for 'id'."}), 400
    except InvalidOperation:
        # Catching invalid decimal formats (e.g., passing letters instead of numbers)
        return (
            jsonify({"error": "Financial values must be valid decimal numbers."}),
            400,
        )
    except Exception as e:
        # Catch-all and rollback for database or unforeseen domain errors
        g.db_session.rollback()
        logger.error(f"Failed to create product: {str(e)}")
        return (
            jsonify({"error": "Failed to process the product creation request."}),
            500,
        )


@api_bp.route("/products/<product_id>", methods=["GET"])
def get_product(product_id: str) -> Tuple[Response, int]:
    """
    Retrieves a single product by its UUID and calculates its sale price dynamically.
    """
    repo = SqlAlchemyProductRepository(session=g.db_session)

    try:
        parsed_id = UUID(product_id)

        # Domain boundary check
        product: Optional[Product] = repo.get_by_id(parsed_id)

        if not product:
            return jsonify({"error": f"Product with ID {product_id} not found."}), 404

        # Execute Domain Logic seamlessly
        calculated_sale_price: Decimal = product.calculate_sale_price()

        return (
            jsonify(
                {
                    "data": {
                        "id": str(product.id),
                        "name": product.name,
                        "cost_price": str(product.cost_price),
                        "cost_currency_code": product.cost_currency_code,
                        "margin_percentage": str(product.margin_percentage),
                        "calculated_sale_price": str(
                            calculated_sale_price
                        ),  # Serialized to string to prevent float precision loss in JSON
                    }
                }
            ),
            200,
        )

    except ValueError:
        return (
            jsonify({"error": "Invalid product ID format. Must be a valid UUID."}),
            400,
        )
    except Exception as e:
        logger.error(f"Failed to fetch product {product_id}: {str(e)}")
        return jsonify({"error": "Internal server error."}), 500
