"""Centralized game configuration and constants.

This module contains all game constants, magic numbers, and configuration
values in one place for easy maintenance and tuning.
"""

from dataclasses import dataclass
from typing import Dict, Any
import os


@dataclass
class PathfindingConfig:
    """Configuration for pathfinding and movement systems."""
    
    # A* pathfinding constants
    DIAGONAL_MOVE_COST: float = 1.41  # Normal diagonal movement cost
    MAX_PATH_LENGTH: int = 25  # Maximum path length before fallback to simple movement
    
    # Movement validation
    MAX_COORDINATE: int = 9999  # Maximum valid map coordinate


@dataclass
class PerformanceConfig:
    """Configuration for performance optimization systems."""
    
    # Spatial indexing
    SPATIAL_GRID_SIZE: int = 8  # Grid cell size for spatial entity indexing
    
    # FOV caching
    FOV_CACHE_SIZE: int = 100  # Maximum number of cached FOV results
    
    # Rendering
    TARGET_FPS: int = 60  # Target frames per second
    MAX_DIRTY_RECTANGLES: int = 50  # Maximum dirty rectangles before full redraw


@dataclass
class CombatConfig:
    """Configuration for combat and character stats."""
    
    # Default character stats
    DEFAULT_DEFENSE: int = 0
    DEFAULT_POWER: int = 1
    DEFAULT_HP: int = 1
    DEFAULT_XP: int = 0
    
    # Combat calculations
    MIN_DAMAGE: int = 0  # Minimum damage that can be dealt
    
    # Level progression
    DEFAULT_LEVEL_UP_BASE: int = 200  # Base XP required for level 2
    DEFAULT_LEVEL_UP_FACTOR: int = 150  # Additional XP per level


@dataclass
class InventoryConfig:
    """Configuration for inventory and item systems."""
    
    # Default inventory settings
    DEFAULT_INVENTORY_CAPACITY: int = 26  # Standard inventory size
    
    # Item usage
    MAX_ITEM_NAME_LENGTH: int = 50  # Maximum length for item names


@dataclass
class RenderingConfig:
    """Configuration for rendering and display systems."""
    
    # Screen dimensions (can be overridden by user config)
    DEFAULT_SCREEN_WIDTH: int = 80
    DEFAULT_SCREEN_HEIGHT: int = 50
    DEFAULT_PANEL_HEIGHT: int = 7
    DEFAULT_BAR_WIDTH: int = 20
    
    # FOV settings
    DEFAULT_FOV_RADIUS: int = 10
    DEFAULT_FOV_LIGHT_WALLS: bool = True
    DEFAULT_FOV_ALGORITHM: int = 0  # tcod.FOV_BASIC
    
    # Message log
    DEFAULT_MESSAGE_LOG_HEIGHT: int = 5
    DEFAULT_MESSAGE_LOG_WIDTH: int = 40


@dataclass
class GameplayConfig:
    """Configuration for core gameplay mechanics."""
    
    # Map generation
    DEFAULT_MAP_WIDTH: int = 80
    DEFAULT_MAP_HEIGHT: int = 43
    
    # Room generation
    MIN_ROOM_SIZE: int = 6
    MAX_ROOM_SIZE: int = 10
    MAX_ROOMS_PER_FLOOR: int = 30
    
    # Entity spawning
    MAX_MONSTERS_PER_ROOM: int = 3
    MAX_ITEMS_PER_ROOM: int = 2


@dataclass
class GameConstants:
    """Main configuration container for all game constants."""
    
    pathfinding: PathfindingConfig = None
    performance: PerformanceConfig = None
    combat: CombatConfig = None
    inventory: InventoryConfig = None
    rendering: RenderingConfig = None
    gameplay: GameplayConfig = None
    
    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.pathfinding is None:
            self.pathfinding = PathfindingConfig()
        if self.performance is None:
            self.performance = PerformanceConfig()
        if self.combat is None:
            self.combat = CombatConfig()
        if self.inventory is None:
            self.inventory = InventoryConfig()
        if self.rendering is None:
            self.rendering = RenderingConfig()
        if self.gameplay is None:
            self.gameplay = GameplayConfig()
    
    @classmethod
    def load_from_file(cls, config_path: str = None) -> 'GameConstants':
        """Load configuration from a file.
        
        Args:
            config_path: Path to configuration file. If None, uses default values.
            
        Returns:
            GameConstants instance with loaded or default values.
        """
        # For now, return defaults. Future enhancement could load from JSON/YAML
        if config_path and os.path.exists(config_path):
            # TODO: Implement file loading (JSON/YAML)
            pass
        
        return cls()
    
    def to_legacy_constants(self) -> Dict[str, Any]:
        """Convert to the legacy constants dictionary format.
        
        This maintains compatibility with existing code that expects
        the old constants dictionary format.
        
        Returns:
            Dictionary in the legacy format expected by existing code.
        """
        return {
            # Screen and rendering
            'screen_width': self.rendering.DEFAULT_SCREEN_WIDTH,
            'screen_height': self.rendering.DEFAULT_SCREEN_HEIGHT,
            'panel_height': self.rendering.DEFAULT_PANEL_HEIGHT,
            'panel_y': self.rendering.DEFAULT_SCREEN_HEIGHT - self.rendering.DEFAULT_PANEL_HEIGHT,
            'bar_width': self.rendering.DEFAULT_BAR_WIDTH,
            'window_title': 'Yarl (Catacombs of Yarl)',
            
            # FOV settings
            'fov_radius': self.rendering.DEFAULT_FOV_RADIUS,
            'fov_light_walls': self.rendering.DEFAULT_FOV_LIGHT_WALLS,
            'fov_algorithm': self.rendering.DEFAULT_FOV_ALGORITHM,
            
            # Map settings
            'map_width': self.gameplay.DEFAULT_MAP_WIDTH,
            'map_height': self.gameplay.DEFAULT_MAP_HEIGHT,
            
            # Room generation
            'room_max_size': self.gameplay.MAX_ROOM_SIZE,
            'room_min_size': self.gameplay.MIN_ROOM_SIZE,
            'max_rooms': self.gameplay.MAX_ROOMS_PER_FLOOR,
            
            # Entity limits
            'max_monsters_per_room': self.gameplay.MAX_MONSTERS_PER_ROOM,
            'max_items_per_room': self.gameplay.MAX_ITEMS_PER_ROOM,
            
            # Colors (keeping existing color definitions)
            'colors': {
                'dark_wall': (0, 0, 100),
                'dark_ground': (50, 50, 150),
                'light_wall': (130, 110, 50),
                'light_ground': (200, 180, 50),
                'desaturated_green': (63, 127, 63),
                'darker_green': (0, 127, 0),
                'dark_red': (191, 0, 0),
                'white': (255, 255, 255),
                'black': (0, 0, 0),
                'red': (255, 0, 0),
                'orange': (255, 127, 0),
                'light_red': (255, 114, 114),
                'darker_red': (127, 0, 0),
                'violet': (127, 0, 255),
                'yellow': (255, 255, 0),
                'blue': (0, 0, 255),
                'green': (0, 255, 0),
                'light_cyan': (114, 255, 255),
                'light_pink': (255, 114, 184),
            }
        }


# Global instance for easy access
GAME_CONSTANTS = GameConstants()

# Convenience functions for common access patterns
def get_constants() -> Dict[str, Any]:
    """Get constants in legacy dictionary format.
    
    This function maintains compatibility with existing code.
    
    Returns:
        Dictionary of game constants in legacy format.
    """
    return GAME_CONSTANTS.to_legacy_constants()


def get_pathfinding_config() -> PathfindingConfig:
    """Get pathfinding configuration.
    
    Returns:
        PathfindingConfig: Configuration object containing pathfinding-related constants
            including A* parameters, movement costs, and path length limits.
    """
    return GAME_CONSTANTS.pathfinding


def get_performance_config() -> PerformanceConfig:
    """Get performance configuration.
    
    Returns:
        PerformanceConfig: Configuration object containing performance-related constants
            including spatial indexing, FOV caching, and rendering optimization settings.
    """
    return GAME_CONSTANTS.performance


def get_combat_config() -> CombatConfig:
    """Get combat configuration.
    
    Returns:
        CombatConfig: Configuration object containing combat-related constants
            including default stats, damage calculations, and level progression.
    """
    return GAME_CONSTANTS.combat


def get_inventory_config() -> InventoryConfig:
    """Get inventory configuration.
    
    Returns:
        InventoryConfig: Configuration object containing inventory-related constants
            including default capacity and item name length limits.
    """
    return GAME_CONSTANTS.inventory


def get_rendering_config() -> RenderingConfig:
    """Get rendering configuration.
    
    Returns:
        RenderingConfig: Configuration object containing rendering-related constants
            including screen dimensions, FOV settings, and display parameters.
    """
    return GAME_CONSTANTS.rendering


def get_gameplay_config() -> GameplayConfig:
    """Get gameplay configuration.
    
    Returns:
        GameplayConfig: Configuration object containing gameplay-related constants
            including map generation and entity spawning parameters.
    """
    return GAME_CONSTANTS.gameplay
