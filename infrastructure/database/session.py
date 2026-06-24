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
Database session management for the Calcify application.

Resolves the OS-specific SQLite database path and provides the get_db_path
utility that ensures cross-platform compatibility (Windows, macOS, Linux).
"""

import os
import sys
from pathlib import Path

def get_db_path(app_name: str = "Calcify") -> Path:
    """
    Dynamically resolves the OS-specific user data directory for the application
    to safely store the SQLite database.
    
    Prevents permission errors caused by storing mutable databases in 
    read-only program directories (like 'C:\\Program Files').

    Args:
        app_name (str): The namespace/folder name for the application data.

    Returns:
        Path: The absolute path to the database.sqlite file.
    """
    home: Path = Path.home()
    
    if sys.platform == "win32":
        # Windows: Uses %APPDATA% for roaming profiles, fallback to manual path.
        app_data: str | None = os.getenv("APPDATA")
        if app_data:
            base_dir: Path = Path(app_data)
        else:
            base_dir = home / "AppData" / "Roaming"
            
    elif sys.platform == "darwin":
        # macOS: Standard application support directory.
        base_dir = home / "Library" / "Application Support"
        
    else:
        # Linux/Unix: Respects the XDG Base Directory Specification.
        # Uses XDG_CONFIG_HOME or defaults to ~/.config.
        xdg_config: str | None = os.getenv("XDG_CONFIG_HOME")
        if xdg_config:
            base_dir = Path(xdg_config)
        else:
            base_dir = home / ".config"

    # Define the isolated application directory
    app_dir: Path = base_dir / app_name
    
    # Create the directory structure if it doesn't exist.
    # parents=True acts like `mkdir -p` in bash.
    # exist_ok=True prevents crashes if the folder is already there.
    app_dir.mkdir(parents=True, exist_ok=True)
    
    # Define the final database file path
    db_file: Path = app_dir / "database.sqlite"
    
    return db_file
