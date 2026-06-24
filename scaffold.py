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
Project scaffold generator for the Calcify application.

Creates the Clean Architecture directory structure with all required
packages when initializing a new project from scratch.
"""

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
