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

import os
import sys
import logging
import traceback
from typing import Optional
from werkzeug.exceptions import HTTPException
from flask import Flask, g, jsonify, request, session
from flask_babel import Babel, get_translations
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Infrastructure Imports
from infrastructure.database.models import Base, ConfigModel
from infrastructure.database.session import get_db_path
from infrastructure.database.migrations import run_migrations
from infrastructure.database.auto_migrate import bootstrap_migrations
from infrastructure.repositories.sqlalchemy_repos import SqlAlchemyConfigRepository

# Security Import
from setup_security import initialize_security

# Blueprint Imports
from presentation.api.routes import api_bp
from presentation.api.auth import auth_bp
from presentation.web.routes import web_bp

# Set up global logging config for the application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(module)s: %(message)s",
)
logger: logging.Logger = logging.getLogger(__name__)


def get_locale() -> str:
    if session.get("locale"):
        return session["locale"]
    return request.accept_languages.best_match(["en", "es"]) or "en"


def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Application Factory Pattern.
    Constructs, configures, and returns a fully initialized Flask application instance.

    Args:
        config_name (Optional[str]): Environment flag ('testing', 'production', etc.)

    Returns:
        Flask: The configured WSGI application object.
    """
    # 1. Instantiate the core framework
    app: Flask = Flask(__name__, template_folder="presentation/templates")

    # 1.5 Internationalization (i18n)
    babel: Babel = Babel(app, locale_selector=get_locale)

    @app.context_processor
    def inject_i18n_globals() -> dict:
        from flask_babel import gettext as _
        return {
            "current_locale": get_locale(),
            "js_translations": {
                "calculator": _("Calculator"),
                "inventory": _("Inventory"),
                "configuration": _("Configuration"),
                "reports": _("Reports"),
                "sales": _("Sales"),
                "daily_report": _("Daily Report"),
                "total_purchases": _("Total Purchases"),
                "total_sales": _("Total Sales"),
                "net_profit": _("Net Profit"),
                "product_name": _("Product Name"),
                "category": _("Category"),
                "stock": _("Stock"),
                "cost_price": _("Cost Price"),
                "margin": _("Margin"),
                "sale_price": _("Sale Price"),
                "actions": _("Actions"),
                "search_product": _("Search product..."),
                "add_product": _("Add Product"),
                "edit": _("Edit"),
                "delete": _("Delete"),
                "save": _("Save"),
                "update": _("Update"),
                "cancel": _("Cancel"),
                "no_products": _("No products found."),
                "are_you_sure": _("Are you sure you want to delete this product?"),
                "error_saving": _("Error saving product:"),
                "error_deleting": _("Error deleting:"),
                "estimated_sale_price": _("Estimated Sale Price"),
                "product": _("Product"),
                "quantity": _("Quantity"),
                "unit_price": _("Unit Price"),
                "currency": _("Currency"),
                "comment_optional": _("Comment (optional)"),
                "notes_about_sale": _("Notes about the sale..."),
                "register_sale": _("Register Sale"),
                "registering": _("Registering..."),
                "sale_registered": _("\u2713 Sale registered successfully."),
                "no_results": _("\u2014 No results \u2014"),
                "main": _("\u2605 Main"),
                "set_base": _("Set Base"),
                "error_adding_currency": _("Error adding currency:"),
                "error_setting_base": _("Error setting base currency:"),
                "no_rates": _("No rates configured."),
                "delete_rate": _("Delete"),
                "error_adding_rate": _("Error adding rate:"),
                "error_deleting_rate": _("Error deleting rate:"),
                "delete_confirm": _("Delete this exchange rate?"),
                "no_transactions": _("No transactions for this date."),
                "failed_load_transactions": _("Failed to load transactions."),
                "no_data_export": _("No data to export."),
                "export_csv": _("Export CSV"),
                "time": _("Time"),
                "type": _("Type"),
                "qty": _("Qty"),
                "unit_price_original": _("Unit Price (Original)"),
                "converted_values": _("Converted Values"),
                "please_set_base": _("Please set a base currency in"),
                "settings_link": _("Settings"),
                "to_use_calculator": _("to use the calculator."),
                "loading": _("Loading..."),
                "online": _("Online"),
                "offline": _("Offline"),
                "decrypting": _("Decrypting..."),
                "access_granted": _("Access Granted"),
                "init_session": _("Initialize Session"),
                "access_denied": _("Access Denied"),
                "auth_failed": _("Authentication Failed"),
                "authorized_personnel": _("Authorized Personnel Only"),
                "cash_register": _("Cash Register"),
                "manage_daily_sales": _("Manage daily sales and inventory."),
                "spa_mode": _("SPA MODE"),
                "new_pin": _("New PIN"),
                "confirm_pin": _("Confirm PIN"),
                "update_credentials": _("Update Credentials"),
                "security": _("Security"),
                "data_backup": _("Data Backup"),
                "export_desc": _("Export all currencies, products, and transactions to a secure JSON file."),
                "download_backup": _("Download JSON Backup"),
                "currency_management": _("Currency Management"),
                "exchange_rates": _("Exchange Rates"),
                "code": _("Code"),
                "name": _("Name"),
                "symbol": _("Symbol"),
                "rate": _("Rate"),
                "add_currency": _("Add Currency"),
                "add_rate": _("Add Rate"),
                "base_amount": _("Base Amount"),
                "source": _("Source"),
                "filter_by_date": _("Filter by Date"),
                "product_inventory": _("Product Inventory"),
                "manage_assets": _("Manage assets and margins."),
                "daily_ledger": _("Daily ledger with multi-currency conversion."),
                "system_settings": _("System Settings"),
                "security_data": _("Security and data management."),
                "real_time_engine": _("Real-time cross-currency engine."),
                "financial_matrix": _("Financial Matrix"),
                "transaction_reports": _("Transaction Reports"),
                "e_g_hardware": _("e.g. Hardware, Services..."),
                "uncategorized": _("Uncategorized"),
            },
        }

    # 2. Dynamic Configuration & Engine Setup
    if config_name == "testing":
        app.config["TESTING"] = True
        app.config["SESSION_COOKIE_SECURE"] = (
            False  # Allows unencrypted cookies in tests
        )

        # In-memory database isolated for network testing
        db_uri: str = "sqlite:///:memory:"
        engine: Engine = create_engine(
            db_uri, connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        logger.info("Application booted in TESTING mode.")
    else:
        app.config["TESTING"] = False

        # Resolve OS-agnostic dynamic AppData path
        db_path = get_db_path("Calcify")
        db_uri = f"sqlite:///{db_path.as_posix()}"
        engine = create_engine(db_uri)

    # Create an isolated Session Factory bound to the configured engine
    SessionLocal = sessionmaker(bind=engine)

    # 3. Application Context Initialization
    try:
        with app.app_context():
            if config_name == "testing":
                # Bypass Alembic for tests: build schema directly in RAM (O(1) time)
                Base.metadata.create_all(engine)
                with SessionLocal() as test_session:
                    test_session.add(
                        ConfigModel(key="app_secret_key", value="test_secret_123")
                    )
                    test_session.commit()
            else:
                # Auto-migrations: bootstraps Alembic, generates, and applies schema updates
                # MUST run before initialize_security so Alembic tracks the schema.
                logger.info("Starting migration bootstrap...")
                bootstrap_migrations(str(engine.url), Base.metadata)
                logger.info("Migration bootstrap completed.")

                # Idempotent Security Bootstrap (Prevents locking out active sessions)
                logger.info("Starting security setup...")
                initialize_security("Calcify", engine=engine)
                logger.info("Security setup completed.")

            # Dynamically inject the cryptographic App Secret Key into Flask
            with SessionLocal() as temp_session:
                repo = SqlAlchemyConfigRepository(temp_session)
                secret_key: Optional[str] = repo.get_value("app_secret_key")

                if not secret_key:
                    raise RuntimeError(
                        "App Secret Key is missing from the database. Initialization failed."
                    )

                app.secret_key = secret_key
                logger.info("App secret key loaded successfully.")
    except SystemExit:
        raise
    except Exception as boot_err:
        msg: str = f"Application boot aborted: {type(boot_err).__name__}: {boot_err}"
        logger.critical(msg)
        print(f"\n*** {msg} ***", file=sys.stderr, flush=True)
        traceback.print_exc()
        print("*** Application will now exit ***", file=sys.stderr, flush=True)
        raise SystemExit(1)

    # 4. Request Lifecycle Middlewares
    @app.before_request
    def inject_db_session() -> None:
        """
        Hooks into the start of the Flask request lifecycle.
        Injects a pristine SQLAlchemy session into the global 'g' object,
        making it accessible to all Blueprints without circular dependencies.
        """
        g.db_session = SessionLocal()

    @app.teardown_request
    def remove_db_session(exception: Optional[BaseException] = None) -> None:
        """
        Hooks into the end of the Flask request lifecycle.
        Ensures the database connection is cleanly released to the pool.
        Rolls back uncommitted transactions if an unhandled Exception was thrown (e.g., HTTP 500).
        """
        db_session: Optional[Session] = getattr(g, "db_session", None)
        if db_session is not None:
            if exception:
                db_session.rollback()
            db_session.close()

    # 5. Global Application Error Handler (Catches all unhandled exceptions)
    @app.errorhandler(Exception)
    def handle_global_exception(error: Exception) -> tuple:
        """Catches any unhandled exception across the entire system."""
        if isinstance(error, HTTPException):
            return jsonify({"error": error.name, "message": error.description}), error.code
        logging.error("Unhandled exception:\n%s", traceback.format_exc())
        return jsonify({"error": "Internal Server Error", "message": str(error)}), 500

    # 6. Locale Switching Route
    @app.route("/api/v1/locale/<locale>", methods=["GET"])
    def set_locale(locale: str) -> tuple:
        if locale in ("en", "es"):
            session["locale"] = locale
        referrer = request.headers.get("Referer", "/")
        from flask import redirect
        return redirect(referrer), 302

    @app.route("/api/v1/locale", methods=["POST"])
    def set_locale_json() -> tuple:
        payload = request.get_json()
        locale = payload.get("locale", "en") if payload else "en"
        if locale in ("en", "es"):
            session["locale"] = locale
        from flask_babel import gettext as _
        from flask import jsonify as flask_jsonify
        return flask_jsonify({"message": _("Locale changed."), "locale": locale}), 200

    # 7. Blueprint Registration (Enforcing the Golden Rule)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(web_bp)

    return app


if __name__ == "__main__":
    # Local development server entrypoint
    application: Flask = create_app()

    sys.stdout.flush()
    sys.stderr.flush()
    print("=== APP CREATED, STARTING SERVER ===", flush=True)

    # 127.0.0.1 avoids Windows firewall prompts and port-binding issues with 0.0.0.0
    # Override via FLASK_RUN_HOST env var (e.g. "0.0.0.0" for LAN access)
    debug_mode: bool = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    application.run(
        host=os.environ.get("FLASK_RUN_HOST", "127.0.0.1"),
        port=5000,
        debug=debug_mode,
    )

    sys.stdout.flush()
    print("=== SERVER STOPPED (UNEXPECTED) ===", flush=True)
