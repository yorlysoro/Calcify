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

import traceback
from presentation.api.auth import login_required
import logging
from typing import Optional, Tuple, Dict, Any, List, Union
from uuid import UUID, uuid4
from decimal import Decimal, InvalidOperation

from flask import Blueprint, request, jsonify, g, Response
from flask_babel import _

# Pure Domain Imports
from domain.models import Product, Currency, Transaction, CurrencyRate

# Infrastructure Imports (Adapters only, NO ORM models)
from infrastructure.repositories.sqlalchemy_repos import (
    SqlAlchemyProductRepository,
    SqlAlchemyCurrencyRepository,
    SqlAlchemyTransactionRepository,
    SqlAlchemyCurrencyRateRepository,
)

from datetime import datetime, timezone

# Import the Use Cases
from use_cases.export_backup import ExportBackupUseCase
from use_cases.currency_conversion import CurrencyConversionUseCase
from use_cases.sales import RegisterSaleUseCase

logger: logging.Logger = logging.getLogger(__name__)

# <BP> stands for Blueprint. Groups related routes under a common URL prefix.
api_bp: Blueprint = Blueprint("api", __name__, url_prefix="/api/v1")


@api_bp.errorhandler(Exception)
def handle_unhandled_error(error: Exception) -> Tuple[Response, int]:
    """Global exception handler for all unhandled API errors."""
    traceback.print_exc()
    logger.error("Unhandled exception:\n%s", traceback.format_exc())
    return jsonify({"error": _("Internal Server Error"), "message": str(error)}), 500


@api_bp.route("/currencies", methods=["GET"])
@login_required
def get_currencies() -> Tuple[Response, int]:
    """
    Retrieves all available currencies from the domain.
    """
    repo = SqlAlchemyCurrencyRepository(session=g.db_session)

    try:
        currencies: List[Currency] = repo.get_all()

        response_data: List[Dict[str, Any]] = [
            {"code": c.code, "name": c.name, "symbol": c.symbol, "is_main": c.is_main}
            for c in currencies
        ]

        return jsonify({"data": response_data}), 200

    except Exception as e:
        logger.error(f"Failed to fetch currencies: {str(e)}")
        return (
            jsonify({"error": _("Internal server error while fetching currencies.")}),
            500,
        )


@api_bp.route("/currencies", methods=["POST"])
@login_required
def create_currency() -> Tuple[Response, int]:
    """
    Creates a new currency in the system.
    Expects a JSON payload with code, name, symbol, and optional is_main.
    """
    payload: Optional[Dict[str, Any]] = request.get_json()
    if not payload:
        return jsonify({"error": _("Invalid or missing JSON payload.")}), 400

    repo = SqlAlchemyCurrencyRepository(session=g.db_session)

    try:
        code: str = str(payload["code"]).upper()
        name: str = str(payload["name"])
        symbol: str = str(payload["symbol"])
        is_main: bool = bool(payload.get("is_main", False))

        existing: Optional[Currency] = repo.get_by_code(code)
        if existing is not None:
            return jsonify({"error": _("Currency %(code)s already exists.", code=code)}), 409

        new_currency: Currency = Currency(
            code=code, name=name, symbol=symbol, is_main=is_main
        )

        repo.save(new_currency)
        g.db_session.commit()

        return (
            jsonify({
                "message": _("Currency created successfully."),
                "data": {
                    "code": new_currency.code,
                    "name": new_currency.name,
                    "symbol": new_currency.symbol,
                    "is_main": new_currency.is_main,
                },
            }),
            201,
        )

    except KeyError as e:
        return jsonify({"error": _("Missing required field: %(field)s", field=str(e))}), 400
    except Exception as e:
        g.db_session.rollback()
        logger.error(f"Failed to create currency: {str(e)}")
        return (
            jsonify({"error": _("Failed to process the currency creation request.")}),
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
        return jsonify({"error": _("Invalid or missing JSON payload.")}), 400

    repo = SqlAlchemyProductRepository(session=g.db_session)

    try:
        product_id = UUID(payload["id"])
        name = str(payload["name"])
        cost_price = Decimal(str(payload["cost_price"]))
        cost_currency_code = str(payload["cost_currency_code"])
        margin_percentage = Decimal(str(payload["margin_percentage"]))
        category = str(payload.get("category", "Uncategorized"))
        stock_quantity = int(payload.get("stock_quantity", 0))

        new_product = Product(
            id=product_id,
            name=name,
            cost_price=cost_price,
            cost_currency_code=cost_currency_code,
            margin_percentage=margin_percentage,
            category=category,
            stock_quantity=stock_quantity,
        )

        repo.save(new_product)
        g.db_session.commit()

        return (
            jsonify(
                {
                    "message": _("Product created successfully."),
                    "data": {"id": str(new_product.id)},
                }
            ),
            201,
        )

    except KeyError as e:
        return jsonify({"error": _("Missing required field: %(field)s", field=str(e))}), 400
    except ValueError:
        return jsonify({"error": _("Invalid UUID format provided for 'id'.")}), 400
    except InvalidOperation:
        return (
            jsonify({"error": _("Financial values must be valid decimal numbers.")}),
            400,
        )
    except Exception as e:
        g.db_session.rollback()
        logger.error(f"Failed to create product: {str(e)}")
        return (
            jsonify({"error": _("Failed to process the product creation request.")}),
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

        product: Optional[Product] = repo.get_by_id(parsed_id)

        if not product:
            return jsonify({"error": _("Product with ID %(id)s not found.", id=product_id)}), 404

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
                        ),
                        "category": product.category,
                        "stock_quantity": product.stock_quantity,
                    }
                }
            ),
            200,
        )

    except ValueError:
        return (
            jsonify({"error": _("Invalid product ID format. Must be a valid UUID.")}),
            400,
        )
    except Exception as e:
        logger.error(f"Failed to fetch product {product_id}: {str(e)}")
        return jsonify({"error": _("Internal server error.")}), 500


@api_bp.route("/products/<product_id>", methods=["PUT"])
@login_required
def update_product(product_id: str) -> Tuple[Response, int]:
    """
    Updates an existing product's fields.
    Expects a JSON payload with any subset of updatable fields.
    Protected endpoint: Requires active session.
    """
    repo = SqlAlchemyProductRepository(session=g.db_session)

    try:
        parsed_id = UUID(product_id)
        product: Optional[Product] = repo.get_by_id(parsed_id)
        if not product:
            return jsonify({"error": _("Product with ID %(id)s not found.", id=product_id)}), 404

        payload: Optional[Dict[str, Any]] = request.get_json()
        if not payload:
            return jsonify({"error": _("Invalid or missing JSON payload.")}), 400

        if "name" in payload:
            product.name = str(payload["name"])
        if "category" in payload:
            product.category = str(payload.get("category", "Uncategorized"))
        if "cost_price" in payload:
            product.cost_price = Decimal(str(payload["cost_price"]))
        if "cost_currency_code" in payload:
            product.cost_currency_code = str(payload["cost_currency_code"])
        if "margin_percentage" in payload:
            product.margin_percentage = Decimal(str(payload["margin_percentage"]))
        if "stock_quantity" in payload:
            product.stock_quantity = int(payload["stock_quantity"])

        repo.save(product)
        g.db_session.commit()

        return jsonify({
            "message": _("Product updated successfully."),
            "data": {
                "id": str(product.id),
                "name": product.name,
                "category": product.category,
                "cost_price": str(product.cost_price),
                "cost_currency_code": product.cost_currency_code,
                "margin_percentage": str(product.margin_percentage),
                "stock_quantity": product.stock_quantity,
            },
        }), 200

    except ValueError:
        return jsonify({"error": _("Invalid product ID format. Must be a valid UUID.")}), 400
    except InvalidOperation:
        return jsonify({"error": _("Financial values must be valid decimal numbers.")}), 400
    except Exception as e:
        g.db_session.rollback()
        logger.error(f"Failed to update product {product_id}: {str(e)}")
        return jsonify({"error": _("Internal server error.")}), 500


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
        products: List[Product] = repo.get_all()

        response_data: List[Dict[str, Any]] = [
            {
                "id": str(p.id),
                "name": p.name,
                "cost_price": str(p.cost_price),
                "cost_currency_code": p.cost_currency_code,
                "margin_percentage": str(p.margin_percentage),
                "category": p.category,
                "stock_quantity": p.stock_quantity,
            }
            for p in products
        ]

        return jsonify({"data": response_data}), 200

    except Exception:
        logger.error("Failed to fetch inventory products.")
        return jsonify({"error": _("Internal server error while fetching products.")}), 500


@api_bp.route("/transactions", methods=["POST"])
@login_required
def create_transaction() -> Tuple[Response, int]:
    """
    Records a new financial movement (IN/OUT) in the system's ledger.
    Protected endpoint: Requires active session.
    """
    payload = request.get_json()
    if not payload:
        return jsonify({"error": _("Invalid or missing JSON payload.")}), 400

    tx_repo = SqlAlchemyTransactionRepository(session=g.db_session)
    prod_repo = SqlAlchemyProductRepository(session=g.db_session)

    try:
        product_id = UUID(payload["product_id"])

        if not prod_repo.get_by_id(product_id):
            return jsonify({"error": _("Product %(id)s does not exist.", id=product_id)}), 400

        new_tx = Transaction(
            id=uuid4(),
            product_id=product_id,
            transaction_type=str(payload["transaction_type"]),
            quantity=int(payload["quantity"]),
            unit_price=Decimal(str(payload["unit_price"])),
            currency_code=str(payload["currency_code"]),
            created_at=datetime.now(timezone.utc)
        )

        tx_repo.save(new_tx)
        g.db_session.commit()

        serialized_tx = {
            "id": str(new_tx.id),
            "product_id": str(new_tx.product_id),
            "transaction_type": new_tx.transaction_type,
            "quantity": new_tx.quantity,
            "unit_price": str(new_tx.unit_price),
            "currency_code": new_tx.currency_code,
            "created_at": new_tx.created_at.isoformat()
        }

        return jsonify({
            "message": _("Transaction recorded successfully."),
            "data": serialized_tx
        }), 201

    except KeyError as e:
        return jsonify({"error": _("Missing required field: %(field)s", field=str(e))}), 400
    except ValueError as e:
        return jsonify({"error": _("Invalid data format: %(msg)s", msg=str(e))}), 400
    except InvalidOperation:
        return jsonify({"error": _("Financial values must be valid decimal numbers.")}), 400
    except Exception as e:
        g.db_session.rollback()
        logger.error(f"Failed to record transaction: {str(e)}")
        return jsonify({"error": _("Failed to process the transaction request.")}), 500


@api_bp.route("/transactions", methods=["GET"])
@login_required
def get_transactions() -> Tuple[Response, int]:
    """
    Retrieves the chronological ledger history of all transactions.
    Supports optional ?date=YYYY-MM-DD query parameter for server-side filtering.
    Protected endpoint: Requires active session.
    """
    repo = SqlAlchemyTransactionRepository(session=g.db_session)

    try:
        date_str: Optional[str] = request.args.get("date")
        transactions: List[Transaction] = repo.get_all()

        if date_str:
            try:
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                transactions = [
                    tx for tx in transactions
                    if tx.created_at.date() == parsed_date
                ]
            except ValueError:
                return jsonify({"error": _("Invalid date format. Use YYYY-MM-DD.")}), 400

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
        return jsonify({"error": _("Internal server error while fetching transactions.")}), 500


@api_bp.route("/rates", methods=["POST"])
@login_required
def create_currency_rate() -> Tuple[Response, int]:
    """
    Creates a new exchange rate entry for a currency.
    Expects JSON with currency_code and rate.
    """
    payload: Optional[Dict[str, Any]] = request.get_json()
    if not payload:
        return jsonify({"error": _("Invalid or missing JSON payload.")}), 400

    repo = SqlAlchemyCurrencyRateRepository(session=g.db_session)

    try:
        currency_code: str = str(payload["currency_code"]).upper()
        rate: Decimal = Decimal(str(payload["rate"]))
        inverse_rate: Decimal = Decimal("1.0") / rate

        new_rate: CurrencyRate = CurrencyRate(
            id=uuid4(),
            currency_code=currency_code,
            rate=rate,
            inverse_rate=inverse_rate,
            created_at=datetime.now(timezone.utc),
        )

        repo.save(new_rate)
        g.db_session.commit()

        return (
            jsonify({
                "message": _("Rate created successfully."),
                "data": {
                    "id": str(new_rate.id),
                    "currency_code": new_rate.currency_code,
                    "rate": str(new_rate.rate),
                    "inverse_rate": str(new_rate.inverse_rate),
                    "created_at": new_rate.created_at.isoformat(),
                },
            }),
            201,
        )

    except KeyError as e:
        return jsonify({"error": _("Missing required field: %(field)s", field=str(e))}), 400
    except InvalidOperation:
        return jsonify({"error": _("Rate must be a valid decimal number.")}), 400
    except Exception as e:
        g.db_session.rollback()
        logger.error(f"Failed to create rate: {str(e)}")
        return jsonify({"error": _("Failed to process rate creation.")}), 500


@api_bp.route("/rates/latest", methods=["GET"])
@login_required
def get_latest_currency_rates() -> Tuple[Response, int]:
    """
    Retrieves the most recent exchange rate for each currency.
    """
    repo = SqlAlchemyCurrencyRateRepository(session=g.db_session)

    try:
        rates: List[CurrencyRate] = repo.get_all_latest()
        response_data: List[Dict[str, Any]] = [
            {
                "id": str(r.id),
                "currency_code": r.currency_code,
                "rate": str(r.rate),
                "inverse_rate": str(r.inverse_rate),
                "created_at": r.created_at.isoformat(),
            }
            for r in rates
        ]
        return jsonify({"data": response_data}), 200

    except Exception as e:
        traceback.print_exc()
        logger.error(f"Failed to fetch latest rates: {str(e)}")
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@api_bp.route("/convert", methods=["POST"])
@login_required
def convert_currency() -> Tuple[Response, int]:
    """
    Converts a monetary amount from one currency to another,
    always routing through the main/base currency for precision.

    Expects JSON payload:
        source_currency_code (str): ISO code of the source currency.
        target_currency_code (str): ISO code of the target currency.
        amount (str): Decimal amount as string to preserve precision.

    Returns:
        JSON with source_currency_code, target_currency_code, amount,
        result, and effective rate. All Decimals serialized as strings.
    """
    payload: Optional[Dict[str, Any]] = request.get_json()
    if not payload:
        return jsonify({"error": _("Invalid or missing JSON payload.")}), 400

    try:
        source_code: str = str(payload["source_currency_code"])
        target_code: str = str(payload["target_currency_code"])
        amount: Decimal = Decimal(str(payload["amount"]))

        currency_repo = SqlAlchemyCurrencyRepository(session=g.db_session)
        rate_repo = SqlAlchemyCurrencyRateRepository(session=g.db_session)
        use_case = CurrencyConversionUseCase(
            currency_repo=currency_repo,
            rate_repo=rate_repo,
        )

        result_data: Dict[str, Union[str, Decimal]] = use_case.execute(
            source_currency_code=source_code,
            target_currency_code=target_code,
            amount=amount,
        )

        return jsonify({
            "data": {
                "source_currency_code": result_data["source_currency_code"],
                "target_currency_code": result_data["target_currency_code"],
                "amount": str(result_data["amount"]),
                "result": str(result_data["result"]),
                "rate": str(result_data["rate"]),
            },
        }), 200

    except KeyError as e:
        return jsonify({"error": _("Missing required field: %(field)s", field=str(e))}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except InvalidOperation:
        return jsonify({"error": _("Amount must be a valid decimal number.")}), 400
    except Exception as e:
        logger.error(f"Failed to convert currency: {str(e)}")
        return jsonify({"error": _("Failed to process currency conversion.")}), 500


@api_bp.route("/rates/<rate_id>", methods=["DELETE"])
@login_required
def delete_currency_rate(rate_id: str) -> Tuple[Response, int]:
    """
    Deletes a specific currency rate record by its UUID.
    """
    repo = SqlAlchemyCurrencyRateRepository(session=g.db_session)

    try:
        parsed_id: UUID = UUID(rate_id)
        deleted: bool = repo.delete(parsed_id)

        if not deleted:
            return jsonify({"error": _("Rate with ID %(id)s not found.", id=rate_id)}), 404

        g.db_session.commit()
        return jsonify({"message": _("Rate deleted successfully.")}), 200

    except ValueError:
        return jsonify({"error": _("Invalid rate ID format. Must be a valid UUID.")}), 400
    except Exception as e:
        g.db_session.rollback()
        logger.error(f"Failed to delete rate {rate_id}: {str(e)}")
        return jsonify({"error": _("Internal server error.")}), 500


@api_bp.route("/backup/export", methods=["GET"])
@login_required
def export_backup() -> Response:
    """
    Triggers the generation of a full system backup.
    Protected endpoint: Requires active session.

    Returns:
        A JSON file forced as a downloadable attachment via HTTP headers.
    """
    prod_repo = SqlAlchemyProductRepository(session=g.db_session)
    curr_repo = SqlAlchemyCurrencyRepository(session=g.db_session)
    tx_repo = SqlAlchemyTransactionRepository(session=g.db_session)

    use_case = ExportBackupUseCase(
        product_repo=prod_repo,
        currency_repo=curr_repo,
        transaction_repo=tx_repo
    )

    try:
        backup_data: Dict[str, Any] = use_case.execute()

        response: Response = jsonify(backup_data)

        date_str: str = datetime.now().strftime("%Y%m%d")
        filename: str = f"calcify_backup_{date_str}.json"

        response.headers["Content-Disposition"] = f"attachment; filename={filename}"

        return response

    except Exception as e:
        logger.error(f"Failed to export system backup: {str(e)}")
        return jsonify({"error": _("Failed to generate system backup.")}), 500


@api_bp.route("/sales", methods=["POST"])
@login_required
def register_sale():
    """Register a sale: validate stock, create OUT transaction, reduce stock."""
    payload = request.get_json()
    if not payload:
        return jsonify({"error": _("Invalid or missing JSON payload.")}), 400

    try:
        product_id = UUID(payload["product_id"])
        quantity = int(payload["quantity"])
        unit_price = Decimal(str(payload["unit_price"]))
        currency_code = str(payload["currency_code"])
        comment = str(payload.get("comment", ""))

        use_case = RegisterSaleUseCase(
            product_repo=SqlAlchemyProductRepository(session=g.db_session),
            transaction_repo=SqlAlchemyTransactionRepository(session=g.db_session),
        )
        result = use_case.execute(
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            currency_code=currency_code,
            comment=comment,
        )
        g.db_session.commit()

        return jsonify({
            "message": _("Sale registered successfully."),
            "data": {
                "transaction_id": str(result.transaction.id),
                "product_id": str(result.transaction.product_id),
                "remaining_stock": result.remaining_stock,
                "transaction_type": result.transaction.transaction_type,
                "quantity": result.transaction.quantity,
                "unit_price": str(result.transaction.unit_price),
                "currency_code": result.transaction.currency_code,
                "comment": result.transaction.comment,
                "created_at": result.transaction.created_at.isoformat(),
            },
        }), 201

    except KeyError as e:
        return jsonify({"error": _("Missing required field: %(field)s", field=str(e))}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except InvalidOperation:
        return jsonify({"error": _("Financial values must be valid decimal numbers.")}), 400
    except Exception as e:
        g.db_session.rollback()
        logger.error(f"Failed to register sale: {str(e)}")
        return jsonify({"error": _("Failed to process the sale request.")}), 500


@api_bp.route("/currencies/<string:code>/set_main", methods=["PUT"])
@login_required
def set_main_currency(code: str) -> Tuple[Response, int]:
    """Sets a currency as the main/base currency, unsetting all others."""
    repo = SqlAlchemyCurrencyRepository(session=g.db_session)

    try:
        code_upper: str = code.upper()
        existing: Optional[Currency] = repo.get_by_code(code_upper)
        if not existing:
            return jsonify({"error": _("Currency %(code)s not found.", code=code_upper)}), 404

        repo.set_main(code_upper)
        g.db_session.commit()

        return jsonify({"message": _("%(code)s set as main currency.", code=code_upper)}), 200

    except Exception as e:
        g.db_session.rollback()
        logger.error(f"Failed to set main currency {code}: {str(e)}")
        return jsonify({"error": _("Internal server error.")}), 500


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

        deleted: bool = repo.delete(parsed_id)

        if not deleted:
            return jsonify({"error": _("Product with ID %(id)s not found.", id=product_id)}), 404

        g.db_session.commit()
        return jsonify({"message": _("Product deleted successfully.")}), 200

    except ValueError:
        return jsonify({"error": _("Invalid product ID format. Must be a valid UUID.")}), 400
    except Exception as e:
        g.db_session.rollback()
        logger.error(f"Failed to delete product {product_id}: {str(e)}")
        return jsonify({"error": _("Internal server error.")}), 500
