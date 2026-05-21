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
