import sys
import logging
import getpass
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

# Infrastructure imports
from infrastructure.database.session import get_db_path
from infrastructure.repositories.sqlalchemy_repos import SqlAlchemyConfigRepository

# Configure standard terminal logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger: logging.Logger = logging.getLogger(__name__)


def reset_admin_password(app_name: str = "Calcify") -> None:
    """
    Terminal utility to securely reset the system's master administrator password.

    Prompts the user for a new password, asks for strict confirmation to prevent
    lockouts due to typos, hashes it securely, and upserts it into the database.

    Args:
        app_name (str): The namespace used to resolve the database path.
    """
    print("\n=== SYSTEM SECURITY OVERRIDE ===")
    print("Initiating master password reset protocol.\n")

    try:
        # Prompt without echoing keystrokes
        new_password: str = getpass.getpass(
            "Enter the NEW Admin password/PIN: "
        ).strip()

        if not new_password:
            logger.error("Password cannot be empty. Process aborted.")
            sys.exit(1)

        confirm_password: str = getpass.getpass(
            "Confirm the NEW Admin password/PIN: "
        ).strip()

        if new_password != confirm_password:
            logger.error(
                "Passwords do not match. Integrity check failed. Process aborted."
            )
            sys.exit(1)

        print("\nEncrypting new credentials...")
        hashed_password: str = generate_password_hash(new_password)

        # 1. Resolve Path and Initialize Engine
        db_uri: str = f"sqlite:///{get_db_path(app_name).as_posix()}"
        engine: Engine = create_engine(db_uri)

        # 2. Database Transaction using Context Manager
        with Session(engine) as session:
            repo: SqlAlchemyConfigRepository = SqlAlchemyConfigRepository(session)

            # Upsert the new hash into the configurations table
            repo.set_value("admin_password_hash", hashed_password)

            # Commit the transaction safely
            session.commit()

        print("SUCCESS: Password has been reset successfully.")

    except KeyboardInterrupt:
        # Graceful exit if the user presses Ctrl+C during prompt
        print("\n\nProcess interrupted by user. No changes were made.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Critical failure during password reset: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    reset_admin_password()
