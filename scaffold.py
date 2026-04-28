import logging
from pathlib import Path
from typing import List

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def create_clean_architecture_structure(base_path: Path) -> None:
    """
    Creates the core directory tree for a Clean Architecture project.

    Args:
        base_path (Path): The root directory where the project will be scaffolded.

    Returns:
        None
    """
    # Define the required directories based on architecture constraints
    directories: List[str] = [
        "domain",
        "use_cases",
        "infrastructure/repositories",
        "infrastructure/database",
        "presentation/api",
        "tests",
    ]

    for dir_path_str in directories:
        # Create full path using pathlib's operator
        current_dir: Path = base_path / dir_path_str

        try:
            # Create directory (parents=True acts like `mkdir -p`, exist_ok=True prevents errors if it exists)
            current_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created directory: {current_dir}")

            # Create __init__.py to make it a valid Python package
            init_file: Path = current_dir / "__init__.py"
            init_file.touch(exist_ok=True)
            logging.info(f"Created file: {init_file}")

        except OSError as e:  # <OSError> stands for Operating System Error
            logging.error(f"Failed to create {current_dir}: {e}")


if __name__ == "__main__":
    # Get the current working directory
    root_path: Path = Path.cwd()
    logging.info("Starting project scaffolding...")
    create_clean_architecture_structure(base_path=root_path)
    logging.info("Clean Architecture scaffolding completed successfully.")
