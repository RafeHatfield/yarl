"""Resource and user data path helpers for Catacombs of YARL.

This module provides path resolution that works both during development
(running from source checkout) and in PyInstaller-packaged builds.

Usage:
    from utils.resource_paths import get_resource_path, get_user_data_dir
    
    # Get path to bundled asset (fonts, images, config, data)
    font_path = get_resource_path("arial10x10.png")
    
    # Get user data directory for writable files (saves, logs)
    user_dir = get_user_data_dir()
"""

import os
import sys
from pathlib import Path
from typing import Optional


def is_frozen() -> bool:
    """Check if running as a PyInstaller-frozen executable.
    
    Returns:
        True if running from a PyInstaller bundle, False otherwise.
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_base_path() -> Path:
    """Get the base path for bundled resources.
    
    In PyInstaller builds, this is sys._MEIPASS (the temp extraction directory).
    In development, this is the repository root (parent of this utils/ directory).
    
    Returns:
        Path to the base directory containing game resources.
    """
    if is_frozen():
        # PyInstaller extracts bundled files to _MEIPASS
        return Path(sys._MEIPASS)
    else:
        # Development: utils/resource_paths.py -> repo root
        return Path(__file__).resolve().parent.parent


def get_resource_path(relative_path: str) -> str:
    """Get the absolute path to a bundled resource file.
    
    This function resolves paths to game assets (fonts, images, config files)
    that are bundled with the application. It works in both development and
    PyInstaller builds.
    
    Args:
        relative_path: Path relative to the repo root (e.g., "arial10x10.png",
                       "config/game_constants.yaml", "data/entity_config.yaml")
    
    Returns:
        Absolute path to the resource file as a string.
        
    Example:
        >>> get_resource_path("arial10x10.png")
        '/path/to/rlike/arial10x10.png'  # dev
        '/var/folders/.../arial10x10.png'  # PyInstaller
    """
    base = get_base_path()
    return str(base / relative_path)


def get_user_data_dir(app_name: str = "CatacombsOfYARL", create: bool = False) -> Path:
    """Get the platform-appropriate user data directory.
    
    Returns a writable directory for storing user-generated data like
    save files, logs, and hall of fame records.
    
    Platform locations:
        - Windows: %APPDATA%/CatacombsOfYARL
        - macOS: ~/Library/Application Support/CatacombsOfYARL
        - Linux: ~/.local/share/catacombs-of-yarl
    
    Args:
        app_name: Application name for the directory (default: "CatacombsOfYARL")
        create: If True, create the directory if it doesn't exist (default: False)
    
    Returns:
        Path to the user data directory.
        
    Note:
        This function does NOT create directories by default. Callers should
        create subdirectories as needed (e.g., saves/, logs/).
    """
    if sys.platform == 'win32':
        # Windows: Use %APPDATA%
        appdata = os.environ.get('APPDATA')
        if appdata:
            base = Path(appdata)
        else:
            # Fallback to user home
            base = Path.home() / 'AppData' / 'Roaming'
        user_dir = base / app_name
    
    elif sys.platform == 'darwin':
        # macOS: Use ~/Library/Application Support/
        user_dir = Path.home() / 'Library' / 'Application Support' / app_name
    
    else:
        # Linux/BSD: Use XDG_DATA_HOME or ~/.local/share/
        xdg_data = os.environ.get('XDG_DATA_HOME')
        if xdg_data:
            base = Path(xdg_data)
        else:
            base = Path.home() / '.local' / 'share'
        # Use lowercase with hyphens for Linux convention
        user_dir = base / app_name.lower().replace(' ', '-')
    
    if create:
        user_dir.mkdir(parents=True, exist_ok=True)
    
    return user_dir


def get_save_dir(create: bool = True) -> Path:
    """Get the directory for save game files.
    
    Args:
        create: If True, create the directory if it doesn't exist (default: True)
    
    Returns:
        Path to the saves directory within the user data directory.
    """
    save_dir = get_user_data_dir() / 'saves'
    if create:
        save_dir.mkdir(parents=True, exist_ok=True)
    return save_dir


def get_log_dir(create: bool = True) -> Path:
    """Get the directory for log files.
    
    Args:
        create: If True, create the directory if it doesn't exist (default: True)
    
    Returns:
        Path to the logs directory within the user data directory.
    """
    log_dir = get_user_data_dir() / 'logs'
    if create:
        log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_hall_of_fame_path(create_dir: bool = True) -> Path:
    """Get the path to the Hall of Fame file.
    
    Args:
        create_dir: If True, create the parent directory if it doesn't exist
    
    Returns:
        Path to hall_of_fame.yaml within the user data directory.
    """
    data_dir = get_user_data_dir() / 'data'
    if create_dir:
        data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / 'hall_of_fame.yaml'


def migrate_legacy_save_if_needed() -> Optional[str]:
    """Check for and migrate legacy save files from CWD to user data dir.
    
    If a save file exists in the current working directory but not in the
    user data directory, this function copies it to the new location.
    
    This provides a one-time migration path for users upgrading from older
    versions that stored saves in the CWD.
    
    Returns:
        Migration message if files were migrated, None otherwise.
    """
    import shutil
    
    # Check for legacy saves in CWD
    legacy_json = Path('savegame.json')
    legacy_shelve = Path('savegame.dat.db')
    
    save_dir = get_save_dir(create=True)
    new_json = save_dir / 'savegame.json'
    new_shelve = save_dir / 'savegame.dat.db'
    
    migrated = []
    
    # Migrate JSON save if it exists in CWD but not in user data
    if legacy_json.exists() and legacy_json.is_file() and not new_json.exists():
        try:
            shutil.copy2(legacy_json, new_json)
            migrated.append(f"savegame.json -> {new_json}")
        except Exception as e:
            print(f"Warning: Could not migrate legacy save: {e}")
    
    # Migrate shelve save if it exists in CWD but not in user data
    if legacy_shelve.exists() and legacy_shelve.is_file() and not new_shelve.exists():
        try:
            shutil.copy2(legacy_shelve, new_shelve)
            migrated.append(f"savegame.dat.db -> {new_shelve}")
        except Exception as e:
            print(f"Warning: Could not migrate legacy save: {e}")
    
    if migrated:
        return "Migrated legacy saves: " + ", ".join(migrated)
    return None
