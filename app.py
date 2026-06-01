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

import logging
from typing import Optional
from flask import Flask, g
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Infrastructure Imports
from infrastructure.database.models import Base, ConfigModel
from infrastructure.database.session import get_db_path
from infrastructure.database.migrations import run_migrations
from infrastructure.repositories.sqlalchemy_repos import SqlAlchemyConfigRepository

# Security Import
from setup_security import initialize_security

# Blueprint Imports
from presentation.api.routes import api_bp
from presentation.api.auth import auth_bp

# Set up global logging config for the application
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger: logging.Logger = logging.getLogger(__name__)


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
    app: Flask = Flask(__name__)

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
            # Idempotent Security Bootstrap (Prevents locking out active sessions)
            initialize_security("Calcify")

            # Programmatic Migrations
            try:
                run_migrations("Calcify")
            except Exception as e:
                logger.critical(f"Application boot aborted. Migration failed: {str(e)}")
                raise SystemExit(1)

        # Dynamically inject the cryptographic App Secret Key into Flask
        with SessionLocal() as temp_session:
            repo = SqlAlchemyConfigRepository(temp_session)
            secret_key: Optional[str] = repo.get_value("app_secret_key")

            if not secret_key:
                raise RuntimeError(
                    "App Secret Key is missing from the database. Initialization failed."
                )

            app.secret_key = secret_key

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

    # 5. Blueprint Registration (Enforcing the Golden Rule)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)

    # <NOTE> Future UI Blueprint registration goes here.
    # e.g., app.register_blueprint(web_bp)

    return app


if __name__ == "__main__":
    # Local development server entrypoint
    application: Flask = create_app()

    # Binding to 0.0.0.0 exposes the server to the Local Area Network (LAN)
    application.run(host="0.0.0.0", port=5000, debug=True)
