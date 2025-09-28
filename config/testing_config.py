"""
Testing Configuration for Yarl (Catacombs of Yarl)

This module provides configuration options for testing mode, allowing developers
to easily modify game parameters for testing purposes without changing core game logic.
"""

import os
from typing import Dict, List, Tuple, Any


class TestingConfig:
    """Configuration class for testing mode settings."""
    
    def __init__(self, testing_mode: bool = False):
        """Initialize testing configuration.
        
        Args:
            testing_mode: Whether testing mode is enabled
        """
        self.testing_mode = testing_mode
        
    def get_max_items_per_room(self, dungeon_level: int) -> List[List[int]]:
        """Get maximum items per room based on testing mode.
        
        Args:
            dungeon_level: Current dungeon level
            
        Returns:
            List of [value, level] pairs for from_dungeon_level function
        """
        if self.testing_mode:
            # TESTING: Dramatically increased for easier testing
            return [[10, 1], [15, 4], [20, 6]]
        else:
            # NORMAL: Balanced gameplay
            return [[1, 1], [2, 4]]
    
    def get_item_spawn_chances(self, dungeon_level: int) -> Dict[str, Any]:
        """Get item spawn chances based on testing mode.
        
        Args:
            dungeon_level: Current dungeon level
            
        Returns:
            Dictionary of item names to spawn chance configurations
        """
        if self.testing_mode:
            # TESTING: Higher chances and earlier availability for all items
            return {
                "healing_potion": 50,  # Increased from 35
                "sword": [[25, 1], [40, 4]],  # Available from level 1
                "shield": [[25, 1], [40, 4]],  # Available from level 1  
                "lightning_scroll": [[30, 1], [45, 4]],  # Available from level 1
                "fireball_scroll": [[30, 1], [45, 6]],  # Available from level 1
                "confusion_scroll": [[30, 1], [45, 2]],  # Available from level 1
            }
        else:
            # NORMAL: Balanced gameplay progression
            return {
                "healing_potion": 35,
                "sword": [[5, 4]],
                "shield": [[15, 8]],
                "lightning_scroll": [[25, 4]],
                "fireball_scroll": [[25, 6]],
                "confusion_scroll": [[10, 2]],
            }
    
    def get_max_monsters_per_room(self, dungeon_level: int) -> List[List[int]]:
        """Get maximum monsters per room (unchanged by testing mode).
        
        Args:
            dungeon_level: Current dungeon level
            
        Returns:
            List of [value, level] pairs for from_dungeon_level function
        """
        # Monster spawning remains the same in testing mode
        return [[2, 1], [3, 4], [5, 6]]


# Global testing configuration instance
_testing_config = None


def get_testing_config() -> TestingConfig:
    """Get the global testing configuration instance.
    
    Returns:
        TestingConfig instance
    """
    global _testing_config
    if _testing_config is None:
        # Check environment variable or command line args
        testing_mode = os.environ.get('YARL_TESTING_MODE', '').lower() in ('true', '1', 'yes', 'on')
        _testing_config = TestingConfig(testing_mode=testing_mode)
    return _testing_config


def set_testing_mode(enabled: bool) -> None:
    """Enable or disable testing mode.
    
    Args:
        enabled: Whether to enable testing mode
    """
    global _testing_config
    _testing_config = TestingConfig(testing_mode=enabled)


def is_testing_mode() -> bool:
    """Check if testing mode is currently enabled.
    
    Returns:
        True if testing mode is enabled
    """
    return get_testing_config().testing_mode
