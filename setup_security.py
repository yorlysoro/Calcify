import logging
import getpass
import secrets
from typing import Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

# Infrastructure imports
from infrastructure.database.session import get_db_path
from infrastructure.repositories.sqlalchemy_repos import SqlAlchemyConfigRepository

# Configure basic logger for the setup script
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger: logging.Logger = logging.getLogger(__name__)


def initialize_security(app_name: str = "Calcify") -> None:
    """
    Bootstraps the initial security constraints for the application.

    Ensures that an admin password hash and a secure Flask session key
    exist in the database. Operates idempotently to prevent overwriting
    existing credentials or invalidating active user sessions.

    Args:
        app_name (str): The namespace used to locate the database path.
    """
    # 1. Resolve DB Path and Initialize Engine
    # We use .as_posix() to prevent URI parsing errors on Windows
    db_uri: str = f"sqlite:///{get_db_path(app_name).as_posix()}"
    engine: Engine = create_engine(db_uri)

    # 2. Scoped Database Session (Context Manager ensures safe teardown)
    with Session(engine) as session:
        repo: SqlAlchemyConfigRepository = SqlAlchemyConfigRepository(session)

        # --- PHASE 1: Admin Password Setup ---
        existing_admin_hash: Optional[str] = repo.get_value("admin_password_hash")

        if not existing_admin_hash:
            logger.info("First run detected: Admin password not found.")
            print("\n=== SYSTEM SECURITY SETUP ===")
            print("Please configure the master administrator PIN/Password.")
            print("(Leave blank to use the default 'admin123')")

            # getpass securely prompts without echoing keystrokes to the terminal
            raw_password: str = getpass.getpass(prompt="Enter new Admin PIN: ").strip()

            if not raw_password:
                raw_password = "admin123"
                logger.warning(
                    "No input detected. Defaulting to 'admin123'. Please change this later."
                )

            # Generate salted cryptographic hash
            hashed_password: str = generate_password_hash(raw_password)
            repo.set_value("admin_password_hash", hashed_password)
            logger.info("Admin password hash generated and stored successfully.")
        else:
            logger.info("Admin password already exists. Skipping setup.")

        # --- PHASE 2: Application Secret Key Setup ---
        existing_secret_key: Optional[str] = repo.get_value("app_secret_key")

        if not existing_secret_key:
            logger.info("Generating cryptographically secure App Secret Key...")
            # secrets.token_hex(16) generates exactly 32 random hexadecimal characters
            new_secret_key: str = secrets.token_hex(16)

            repo.set_value("app_secret_key", new_secret_key)
            logger.info(
                "App Secret Key stored successfully. Flask sessions are now secure."
            )
        else:
            logger.info(
                "App Secret Key already exists. Skipping generation to preserve active sessions."
            )

        # 3. Unit of Work: Commit all changes safely to disk
        session.commit()
        logger.info("Security setup completed successfully.\n")


if __name__ == "__main__":
    try:
        initialize_security()
    except Exception as e:
        logger.critical(f"Security initialization failed: {str(e)}")
        # Raise standard SystemExit exception for OS signaling
        raise SystemExit(1)
