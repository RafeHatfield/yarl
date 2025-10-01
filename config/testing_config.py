"""
Testing Configuration for Yarl (Catacombs of Yarl)

This module provides configuration options for testing mode, allowing developers
to easily modify game parameters for testing purposes without changing core game logic.
"""

import os
import logging
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
                "invisibility_scroll": [[25, 1], [40, 3]],  # Available from level 1 for testing
                "teleport_scroll": [[25, 1], [40, 3]],  # Available from level 1 for testing
                "shield_scroll": [[25, 1], [40, 3]],  # Available from level 1 for testing
                "enhance_weapon_scroll": [[20, 1], [35, 3]],  # Enhancement scrolls for testing
                "enhance_armor_scroll": [[20, 1], [35, 3]],
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
                "invisibility_scroll": [[15, 4]],  # Available from level 4 in normal mode
                "enhance_weapon_scroll": [[10, 5]],  # Rare enhancement scrolls
                "enhance_armor_scroll": [[10, 6]],
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
    """Enable or disable testing mode and configure combat debug logging.
    
    Args:
        enabled: Whether to enable testing mode
    """
    global _testing_config
    _testing_config = TestingConfig(testing_mode=enabled)
    
    # Configure combat debug logging
    combat_logger = logging.getLogger('combat_debug')
    if enabled:
        # Set up file handler for combat logs in testing mode
        if not combat_logger.handlers:
            handler = logging.FileHandler('combat_debug.log', mode='a')
            formatter = logging.Formatter('%(asctime)s - COMBAT: %(message)s', 
                                        datefmt='%H:%M:%S')
            handler.setFormatter(formatter)
            combat_logger.addHandler(handler)
            combat_logger.setLevel(logging.DEBUG)
        print("🔍 Combat debug logging enabled: combat_debug.log")
    else:
        # Disable combat logging
        combat_logger.setLevel(logging.CRITICAL)
        # Remove handlers to stop logging
        for handler in combat_logger.handlers[:]:
            combat_logger.removeHandler(handler)
            handler.close()


def is_testing_mode() -> bool:
    """Check if testing mode is currently enabled.
    
    Returns:
        True if testing mode is enabled
    """
    return get_testing_config().testing_mode
