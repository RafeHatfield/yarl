"""Centralized game configuration management.

This module provides GameSettings dataclass for managing all game configuration
in a single, testable location. Configuration can be loaded from:
- Environment variables
- Config files
- Defaults

This replaces scattered configuration across multiple files and enables
easy testing with different configurations.
"""

import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class GameSettings:
    """Centralized game configuration.
    
    All game settings are managed through this dataclass. This provides:
    - Type safety (mypy support)
    - Easy override for testing
    - Single source of truth
    - Clear default values
    - Environment variable support
    
    Attributes:
        testing_mode: Whether the game is in testing mode
        log_level: Python logging level (DEBUG, INFO, WARNING, ERROR)
        debug_logging: Enable debug logging to console
        monster_ai_debug: Enable detailed monster AI logging
        resistance_debug: Enable resistance system logging
        show_fps: Show FPS counter in UI
        show_debug_menu: Enable F12 debug menu (wizard mode)
        max_dungeon_level: Maximum dungeon depth
        save_game_path: Path to save games directory
    """
    
    # Runtime Modes
    testing_mode: bool = False
    debug_mode: bool = False
    
    # Logging Configuration
    log_level: str = "WARNING"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    debug_logging: bool = False
    monster_ai_debug: bool = False
    resistance_debug: bool = False
    
    # UI Configuration
    show_fps: bool = False
    show_debug_menu: bool = False
    
    # Game Configuration
    max_dungeon_level: int = 25
    save_game_path: str = "saves"
    
    @classmethod
    def from_environment(cls) -> "GameSettings":
        """Load configuration from environment variables.
        
        Supported environment variables:
        - RLIKE_TESTING: Set to '1' to enable testing mode
        - RLIKE_DEBUG: Set to '1' to enable debug mode
        - RLIKE_LOG_LEVEL: Set to DEBUG, INFO, WARNING, ERROR, CRITICAL
        - RLIKE_DEBUG_LOGGING: Set to '1' for debug logging
        - RLIKE_MONSTER_AI_DEBUG: Set to '1' for monster AI debug
        - RLIKE_RESISTANCE_DEBUG: Set to '1' for resistance debug
        - RLIKE_SHOW_FPS: Set to '1' to show FPS counter
        - RLIKE_SHOW_DEBUG_MENU: Set to '1' to enable debug menu
        - RLIKE_MAX_DUNGEON_LEVEL: Set to dungeon depth limit
        - RLIKE_SAVE_GAME_PATH: Set to save directory path
        
        Returns:
            GameSettings with values from environment variables
        """
        def get_bool_env(key: str, default: bool = False) -> bool:
            """Parse boolean environment variable."""
            value = os.environ.get(key)
            if value is None:
                return default
            return value.lower() in ('1', 'true', 'yes', 'on')
        
        def get_int_env(key: str, default: int) -> int:
            """Parse integer environment variable."""
            value = os.environ.get(key)
            if value is None:
                return default
            try:
                return int(value)
            except ValueError:
                return default
        
        return cls(
            testing_mode=get_bool_env("RLIKE_TESTING"),
            debug_mode=get_bool_env("RLIKE_DEBUG"),
            log_level=os.environ.get("RLIKE_LOG_LEVEL", "WARNING"),
            debug_logging=get_bool_env("RLIKE_DEBUG_LOGGING"),
            monster_ai_debug=get_bool_env("RLIKE_MONSTER_AI_DEBUG"),
            resistance_debug=get_bool_env("RLIKE_RESISTANCE_DEBUG"),
            show_fps=get_bool_env("RLIKE_SHOW_FPS"),
            show_debug_menu=get_bool_env("RLIKE_SHOW_DEBUG_MENU"),
            max_dungeon_level=get_int_env("RLIKE_MAX_DUNGEON_LEVEL", 25),
            save_game_path=os.environ.get("RLIKE_SAVE_GAME_PATH", "saves"),
        )
    
    @classmethod
    def for_testing(cls) -> "GameSettings":
        """Create settings optimized for testing.
        
        Returns:
            GameSettings configured for unit/integration tests
        """
        return cls(
            testing_mode=True,
            debug_mode=False,
            log_level="WARNING",
            debug_logging=False,
            monster_ai_debug=False,
            resistance_debug=False,
            show_fps=False,
            show_debug_menu=False,
            max_dungeon_level=3,  # Shorter dungeons for testing
            save_game_path="tests/fixtures/saves",
        )
    
    @classmethod
    def for_debugging(cls) -> "GameSettings":
        """Create settings optimized for debugging.
        
        Returns:
            GameSettings with all debug features enabled
        """
        return cls(
            testing_mode=False,
            debug_mode=True,
            log_level="DEBUG",
            debug_logging=True,
            monster_ai_debug=True,
            resistance_debug=True,
            show_fps=True,
            show_debug_menu=True,
            max_dungeon_level=25,
            save_game_path="saves",
        )
    
    def get_save_directory(self) -> Path:
        """Get the save game directory, creating it if needed.
        
        Returns:
            Path to save game directory
        """
        save_dir = Path(self.save_game_path)
        save_dir.mkdir(parents=True, exist_ok=True)
        return save_dir


# Global settings instance (initialized on import)
_global_settings: Optional[GameSettings] = None


def initialize_settings(settings: Optional[GameSettings] = None) -> None:
    """Initialize global settings.
    
    Args:
        settings: GameSettings instance. If None, loads from environment.
    """
    global _global_settings
    if settings is None:
        settings = GameSettings.from_environment()
    _global_settings = settings


def get_settings() -> GameSettings:
    """Get the current global settings.
    
    Returns:
        Current GameSettings instance
        
    Raises:
        RuntimeError: If settings have not been initialized
    """
    global _global_settings
    if _global_settings is None:
        raise RuntimeError(
            "Settings not initialized. Call initialize_settings() first."
        )
    return _global_settings


def reset_settings() -> None:
    """Reset settings to None (for testing).
    
    This is primarily used in test fixtures to reset state between tests.
    """
    global _global_settings
    _global_settings = None

