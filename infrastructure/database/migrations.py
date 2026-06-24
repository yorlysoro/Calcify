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

"""
Programmatic Alembic migration runner for the Calcify application.

Provides the run_migrations function that executes Alembic upgrades to the
latest schema revision head, designed for packaged desktop environments where
CLI access is not available.
"""

import logging
from pathlib import Path
from alembic.config import Config
from alembic import command
from sqlalchemy.exc import SQLAlchemyError

# Ensure this import maps correctly to where get_db_path was defined
from infrastructure.database.session import get_db_path

logger: logging.Logger = logging.getLogger(__name__)

def run_migrations(app_name: str = "Calcify") -> None:
    """
    Programmatically executes Alembic migrations to upgrade the SQLite database 
    schema to the latest version ('head').
    
    Designed specifically for packaged desktop applications where the end-user 
    does not have access to a terminal or CLI tools.
    
    Args:
        app_name (str): The namespace used to resolve the dynamic database path.
        
    Raises:
        RuntimeError: If the migration process fails, aborting the application startup.
    """
    try:
        # 1. Resolve Absolute Paths safely
        # Artifacts live alongside the database in the AppData directory.
        db_path: Path = get_db_path(app_name)
        data_dir: Path = db_path.parent
        
        alembic_ini_path: Path = data_dir / "alembic.ini"
        migrations_dir: Path = data_dir / "migrations"
        
        if not alembic_ini_path.exists():
            raise FileNotFoundError(f"Alembic configuration not found at {alembic_ini_path}")

        # 2. Initialize Alembic Config object
        # <CLI> stands for Command Line Interface. We bypass it entirely here.
        alembic_cfg: Config = Config(str(alembic_ini_path))
        
        # Override the script_location dynamically to prevent CWD (Current Working Directory) issues 
        # when running packaged binaries.
        alembic_cfg.set_main_option("script_location", str(migrations_dir))
        
        # 3. Dynamic Database Path Injection
        # (db_path already resolved above)
        
        # Use .as_posix() to ensure Windows backslashes (\) are converted to forward 
        # slashes (/) to maintain a valid SQLAlchemy URI standard.
        sqlite_url: str = f"sqlite:///{db_path.as_posix()}"
        alembic_cfg.set_main_option("sqlalchemy.url", sqlite_url)
        
        logger.info(f"Applying database migrations targeting: {sqlite_url}")
        
        # 4. Execute the Upgrade
        # Equivalent to running `alembic upgrade head` in the terminal.
        command.upgrade(alembic_cfg, "head")
        
        logger.info("Database migrations successfully applied.")

    except SQLAlchemyError as db_error:
        # Log the specific database driver error
        logger.critical(f"Database error during migration: {str(db_error)}")
        raise RuntimeError("Failed to apply database migrations.") from db_error
        
    except Exception as e:
        # Catch-all for path resolution or internal Alembic configuration errors
        logger.critical(f"Unexpected error during Alembic startup: {str(e)}")
        raise RuntimeError("Critical application failure during schema setup.") from e
