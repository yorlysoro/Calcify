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

from presentation.api.auth import login_required
import logging
from typing import Optional, Tuple, Dict, Any, List
from uuid import UUID, uuid4
from decimal import Decimal, InvalidOperation

from flask import Blueprint, request, jsonify, g, Response

# Pure Domain Imports
from domain.models import Product, Currency, Transaction

# Infrastructure Imports (Adapters only, NO ORM models)
from infrastructure.repositories.sqlalchemy_repos import (
    SqlAlchemyProductRepository,
    SqlAlchemyCurrencyRepository,
    SqlAlchemyTransactionRepository
)

from datetime import datetime, timezone

# Import the Use Case
from use_cases.export_backup import ExportBackupUseCase

logger: logging.Logger = logging.getLogger(__name__)

# <BP> stands for Blueprint. Groups related routes under a common URL prefix.
api_bp: Blueprint = Blueprint("api", __name__, url_prefix="/api/v1")


@api_bp.route("/currencies", methods=["GET"])
@login_required
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
@login_required
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
        category = str(payload.get("category", "Uncategorized"))

        # 2. Instantiate Pure Domain Entity
        new_product = Product(
            id=product_id,
            name=name,
            cost_price=cost_price,
            cost_currency_code=cost_currency_code,
            margin_percentage=margin_percentage,
            category=category
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
@login_required
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
                        "category": product.category,
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

@api_bp.route("/products", methods=["GET"])
@login_required
def get_products() -> Tuple[Response, int]:
    """
    Retrieves the entire product inventory.
    Protected endpoint: Requires active session.
    
    Returns:
        A JSON list of products with safely serialized financial types.
    """
    repo = SqlAlchemyProductRepository(session=g.db_session)
    
    try:
        # 1. Fetch pure domain entities
        products: List[Product] = repo.get_all()
        
        # 2. Serialize Domain to JSON-friendly structures (O(N) mapping)
        response_data: List[Dict[str, Any]] = [
            {
                "id": str(p.id),
                "name": p.name,
                "cost_price": str(p.cost_price), # Strict Decimal-to-String conversion
                "cost_currency_code": p.cost_currency_code,
                "margin_percentage": str(p.margin_percentage),
                "category": p.category,
            }
            for p in products
        ]
        
        return jsonify({"data": response_data}), 200
        
    except Exception as e:
        logger.error(f"Failed to fetch inventory products: {str(e)}")
        return jsonify({"error": "Internal server error while fetching inventory."}), 500

@api_bp.route("/transactions", methods=["POST"])
@login_required
def create_transaction() -> Tuple[Response, int]:
    """
    Records a new financial movement (IN/OUT) in the system's ledger.
    Protected endpoint: Requires active session.
    """
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "Invalid or missing JSON payload."}), 400

    tx_repo = SqlAlchemyTransactionRepository(session=g.db_session)
    prod_repo = SqlAlchemyProductRepository(session=g.db_session)

    try:
        # Edge Validation & Type Casting
        product_id = UUID(payload["product_id"])
        
        # Referencial Integrity Check (Foreign Key Guard)
        if not prod_repo.get_by_id(product_id):
            return jsonify({"error": f"Product {product_id} does not exist."}), 400
            
        new_tx = Transaction(
            id=uuid4(),
            product_id=product_id,
            transaction_type=str(payload["transaction_type"]),
            quantity=int(payload["quantity"]),
            unit_price=Decimal(str(payload["unit_price"])),
            currency_code=str(payload["currency_code"]),
            created_at=datetime.now(timezone.utc) # Strict timezone awareness
        )

        # Persistence (Unit of Work)
        tx_repo.save(new_tx)
        g.db_session.commit()

        # Serialization Helper (Inline Mapping for O(1) response)
        serialized_tx = {
            "id": str(new_tx.id),
            "product_id": str(new_tx.product_id),
            "transaction_type": new_tx.transaction_type,
            "quantity": new_tx.quantity,
            "unit_price": str(new_tx.unit_price), # Strict String casting
            "currency_code": new_tx.currency_code,
            "created_at": new_tx.created_at.isoformat()
        }

        return jsonify({
            "message": "Transaction recorded successfully.",
            "data": serialized_tx
        }), 201

    except KeyError as e:
        return jsonify({"error": f"Missing required field: {str(e)}"}), 400
    except ValueError as e:
        return jsonify({"error": f"Invalid data format: {str(e)}"}), 400
    except InvalidOperation:
        return jsonify({"error": "Financial values must be valid decimal numbers."}), 400
    except Exception as e:
        g.db_session.rollback()
        logger.error(f"Failed to record transaction: {str(e)}")
        return jsonify({"error": "Failed to process the transaction request."}), 500


@api_bp.route("/transactions", methods=["GET"])
@login_required
def get_transactions() -> Tuple[Response, int]:
    """
    Retrieves the chronological ledger history of all transactions.
    Protected endpoint: Requires active session.
    """
    repo = SqlAlchemyTransactionRepository(session=g.db_session)
    
    try:
        transactions: List[Transaction] = repo.get_all()
        
        # O(N) Serialization block
        response_data: List[Dict[str, Any]] = [
            {
                "id": str(tx.id),
                "product_id": str(tx.product_id),
                "transaction_type": tx.transaction_type,
                "quantity": tx.quantity,
                "unit_price": str(tx.unit_price),
                "currency_code": tx.currency_code,
                "created_at": tx.created_at.isoformat()
            }
            for tx in transactions
        ]
        
        return jsonify({"data": response_data}), 200
        
    except Exception as e:
        logger.error(f"Failed to fetch transaction ledger: {str(e)}")
        return jsonify({"error": "Internal server error while fetching transactions."}), 500

@api_bp.route("/backup/export", methods=["GET"])
@login_required
def export_backup() -> Response:
    """
    Triggers the generation of a full system backup.
    Protected endpoint: Requires active session.
    
    Returns:
        A JSON file forced as a downloadable attachment via HTTP headers.
    """
    # 1. Instantiate Repositories
    prod_repo = SqlAlchemyProductRepository(session=g.db_session)
    curr_repo = SqlAlchemyCurrencyRepository(session=g.db_session)
    tx_repo = SqlAlchemyTransactionRepository(session=g.db_session)
    
    # 2. Inject dependencies into the Use Case
    use_case = ExportBackupUseCase(
        product_repo=prod_repo,
        currency_repo=curr_repo,
        transaction_repo=tx_repo
    )
    
    try:
        # 3. Execute pure domain logic
        backup_data: Dict[str, Any] = use_case.execute()
        
        # 4. Format presentation (Flask Response)
        response: Response = jsonify(backup_data)
        
        # 5. Modify Headers to force file download
        date_str: str = datetime.now().strftime("%Y%m%d")
        filename: str = f"respaldo_calculadora_{date_str}.json"
        
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        
        return response

    except Exception as e:
        logger.error(f"Failed to export system backup: {str(e)}")
        return jsonify({"error": "Failed to generate system backup."}), 500

@api_bp.route("/products/<product_id>", methods=["DELETE"])
@login_required
def delete_product(product_id: str) -> Tuple[Response, int]:
    """
    Executes a Hard Delete on a specific product by its UUID.
    Protected endpoint: Requires active session.
    """
    repo = SqlAlchemyProductRepository(session=g.db_session)

    try:
        parsed_id = UUID(product_id)
        
        # Cross the repository boundary
        deleted: bool = repo.delete(parsed_id)
        
        if not deleted:
            return jsonify({"error": f"Product with ID {product_id} not found."}), 404
            
        # Unit of Work: Commit the transaction
        g.db_session.commit()
        return jsonify({"message": "Product deleted successfully."}), 200

    except ValueError:
        return jsonify({"error": "Invalid product ID format. Must be a valid UUID."}), 400
    except Exception as e:
        g.db_session.rollback()
        logger.error(f"Failed to delete product {product_id}: {str(e)}")
        return jsonify({"error": "Internal server error."}), 500
