"""Tests for the game constants configuration system.

This module tests the centralized configuration system to ensure all
constants are accessible and properly configured. Includes regression
tests to prevent import errors and missing functions.
"""

import unittest
from typing import Dict, Any

from config.game_constants import (
    GameConstants,
    PathfindingConfig,
    PerformanceConfig,
    CombatConfig,
    InventoryConfig,
    RenderingConfig,
    GameplayConfig,
    GAME_CONSTANTS,
    get_constants,
    get_pathfinding_config,
    get_performance_config,
    get_combat_config,
    get_inventory_config,
    get_rendering_config,
    get_gameplay_config,
)


class TestGameConstants(unittest.TestCase):
    """Test the GameConstants dataclass and its initialization."""

    def test_game_constants_initialization(self):
        """Test that GameConstants initializes with all required components."""
        constants = GameConstants()
        
        # Verify all config objects are created
        self.assertIsInstance(constants.pathfinding, PathfindingConfig)
        self.assertIsInstance(constants.performance, PerformanceConfig)
        self.assertIsInstance(constants.combat, CombatConfig)
        self.assertIsInstance(constants.inventory, InventoryConfig)
        self.assertIsInstance(constants.rendering, RenderingConfig)
        self.assertIsInstance(constants.gameplay, GameplayConfig)

    def test_game_constants_load_from_file(self):
        """Test loading constants from file (currently returns defaults)."""
        constants = GameConstants.load_from_file()
        
        # Should return a valid GameConstants instance
        self.assertIsInstance(constants, GameConstants)
        self.assertIsInstance(constants.pathfinding, PathfindingConfig)

    def test_to_legacy_constants_format(self):
        """Test conversion to legacy constants dictionary format."""
        constants = GameConstants()
        legacy_dict = constants.to_legacy_constants()
        
        # Verify it's a dictionary with expected keys
        self.assertIsInstance(legacy_dict, dict)
        
        # Check for critical legacy keys
        expected_keys = [
            'screen_width', 'screen_height', 'panel_height', 'panel_y',
            'bar_width', 'window_title', 'fov_radius', 'fov_light_walls',
            'fov_algorithm', 'map_width', 'map_height', 'room_max_size',
            'room_min_size', 'max_rooms', 'max_monsters_per_room',
            'max_items_per_room', 'colors'
        ]
        
        for key in expected_keys:
            self.assertIn(key, legacy_dict, f"Missing legacy key: {key}")

    def test_colors_format_in_legacy_constants(self):
        """Test that colors are properly formatted in legacy constants."""
        constants = GameConstants()
        legacy_dict = constants.to_legacy_constants()
        
        colors = legacy_dict['colors']
        self.assertIsInstance(colors, dict)
        
        # Check for some expected colors
        expected_colors = ['dark_wall', 'dark_ground', 'light_wall', 'light_ground']
        for color_name in expected_colors:
            self.assertIn(color_name, colors)
            # Colors should be tuples of 3 integers
            color_value = colors[color_name]
            self.assertIsInstance(color_value, tuple)
            self.assertEqual(len(color_value), 3)
            for component in color_value:
                self.assertIsInstance(component, int)
                self.assertGreaterEqual(component, 0)
                self.assertLessEqual(component, 255)


class TestConfigurationClasses(unittest.TestCase):
    """Test individual configuration dataclasses."""

    def test_pathfinding_config(self):
        """Test PathfindingConfig has expected attributes."""
        config = PathfindingConfig()
        
        self.assertIsInstance(config.DIAGONAL_MOVE_COST, float)
        self.assertGreater(config.DIAGONAL_MOVE_COST, 0)
        
        self.assertIsInstance(config.MAX_PATH_LENGTH, int)
        self.assertGreater(config.MAX_PATH_LENGTH, 0)
        
        self.assertIsInstance(config.MAX_COORDINATE, int)
        self.assertGreater(config.MAX_COORDINATE, 0)

    def test_performance_config(self):
        """Test PerformanceConfig has expected attributes."""
        config = PerformanceConfig()
        
        self.assertIsInstance(config.SPATIAL_GRID_SIZE, int)
        self.assertGreater(config.SPATIAL_GRID_SIZE, 0)
        
        self.assertIsInstance(config.FOV_CACHE_SIZE, int)
        self.assertGreater(config.FOV_CACHE_SIZE, 0)
        
        self.assertIsInstance(config.TARGET_FPS, int)
        self.assertGreater(config.TARGET_FPS, 0)

    def test_combat_config(self):
        """Test CombatConfig has expected attributes."""
        config = CombatConfig()
        
        self.assertIsInstance(config.DEFAULT_DEFENSE, int)
        self.assertGreaterEqual(config.DEFAULT_DEFENSE, 0)
        
        self.assertIsInstance(config.DEFAULT_POWER, int)
        self.assertGreater(config.DEFAULT_POWER, 0)
        
        self.assertIsInstance(config.DEFAULT_HP, int)
        self.assertGreater(config.DEFAULT_HP, 0)

    def test_inventory_config(self):
        """Test InventoryConfig has expected attributes."""
        config = InventoryConfig()
        
        self.assertIsInstance(config.DEFAULT_INVENTORY_CAPACITY, int)
        self.assertGreater(config.DEFAULT_INVENTORY_CAPACITY, 0)
        
        self.assertIsInstance(config.MAX_ITEM_NAME_LENGTH, int)
        self.assertGreater(config.MAX_ITEM_NAME_LENGTH, 0)

    def test_rendering_config(self):
        """Test RenderingConfig has expected attributes."""
        config = RenderingConfig()
        
        self.assertIsInstance(config.DEFAULT_SCREEN_WIDTH, int)
        self.assertGreater(config.DEFAULT_SCREEN_WIDTH, 0)
        
        self.assertIsInstance(config.DEFAULT_SCREEN_HEIGHT, int)
        self.assertGreater(config.DEFAULT_SCREEN_HEIGHT, 0)
        
        self.assertIsInstance(config.DEFAULT_FOV_RADIUS, int)
        self.assertGreater(config.DEFAULT_FOV_RADIUS, 0)

    def test_gameplay_config(self):
        """Test GameplayConfig has expected attributes."""
        config = GameplayConfig()
        
        self.assertIsInstance(config.DEFAULT_MAP_WIDTH, int)
        self.assertGreater(config.DEFAULT_MAP_WIDTH, 0)
        
        self.assertIsInstance(config.DEFAULT_MAP_HEIGHT, int)
        self.assertGreater(config.DEFAULT_MAP_HEIGHT, 0)
        
        self.assertIsInstance(config.MAX_MONSTERS_PER_ROOM, int)
        self.assertGreaterEqual(config.MAX_MONSTERS_PER_ROOM, 0)


class TestGlobalConstantsInstance(unittest.TestCase):
    """Test the global GAME_CONSTANTS instance."""

    def test_global_constants_exists(self):
        """Test that the global GAME_CONSTANTS instance exists and is valid."""
        self.assertIsInstance(GAME_CONSTANTS, GameConstants)
        self.assertIsInstance(GAME_CONSTANTS.pathfinding, PathfindingConfig)
        self.assertIsInstance(GAME_CONSTANTS.performance, PerformanceConfig)
        self.assertIsInstance(GAME_CONSTANTS.combat, CombatConfig)
        self.assertIsInstance(GAME_CONSTANTS.inventory, InventoryConfig)
        self.assertIsInstance(GAME_CONSTANTS.rendering, RenderingConfig)
        self.assertIsInstance(GAME_CONSTANTS.gameplay, GameplayConfig)


class TestConfigAccessorFunctions(unittest.TestCase):
    """Test all configuration accessor functions.
    
    This is the critical regression test that would have caught the
    missing get_inventory_config() function.
    """

    def test_get_constants_function(self):
        """Test get_constants() returns proper legacy format."""
        constants = get_constants()
        
        self.assertIsInstance(constants, dict)
        self.assertIn('screen_width', constants)
        self.assertIn('colors', constants)

    def test_get_pathfinding_config_function(self):
        """Test get_pathfinding_config() function exists and works."""
        config = get_pathfinding_config()
        
        self.assertIsInstance(config, PathfindingConfig)
        self.assertIsInstance(config.DIAGONAL_MOVE_COST, float)

    def test_get_performance_config_function(self):
        """Test get_performance_config() function exists and works."""
        config = get_performance_config()
        
        self.assertIsInstance(config, PerformanceConfig)
        self.assertIsInstance(config.TARGET_FPS, int)

    def test_get_combat_config_function(self):
        """Test get_combat_config() function exists and works."""
        config = get_combat_config()
        
        self.assertIsInstance(config, CombatConfig)
        self.assertIsInstance(config.DEFAULT_POWER, int)

    def test_get_inventory_config_function(self):
        """Test get_inventory_config() function exists and works.
        
        This is the regression test for the ImportError bug.
        """
        config = get_inventory_config()
        
        self.assertIsInstance(config, InventoryConfig)
        self.assertIsInstance(config.DEFAULT_INVENTORY_CAPACITY, int)
        self.assertGreater(config.DEFAULT_INVENTORY_CAPACITY, 0)

    def test_get_rendering_config_function(self):
        """Test get_rendering_config() function exists and works."""
        config = get_rendering_config()
        
        self.assertIsInstance(config, RenderingConfig)
        self.assertIsInstance(config.DEFAULT_SCREEN_WIDTH, int)

    def test_get_gameplay_config_function(self):
        """Test get_gameplay_config() function exists and works."""
        config = get_gameplay_config()
        
        self.assertIsInstance(config, GameplayConfig)
        self.assertIsInstance(config.DEFAULT_MAP_WIDTH, int)


class TestImportRegression(unittest.TestCase):
    """Regression tests to prevent import errors.
    
    These tests specifically check that all expected functions
    can be imported from the config.game_constants module.
    """

    def test_all_expected_imports_work(self):
        """Test that all expected functions can be imported without error.
        
        This test would have caught the missing get_inventory_config() function.
        """
        # This should not raise ImportError
        try:
            from config.game_constants import (
                get_constants,
                get_pathfinding_config,
                get_performance_config,
                get_combat_config,
                get_inventory_config,  # This was missing and caused the bug
                get_rendering_config,
                get_gameplay_config,
            )
        except ImportError as e:
            self.fail(f"Import failed: {e}")

    def test_all_functions_are_callable(self):
        """Test that all imported functions are actually callable."""
        from config.game_constants import (
            get_constants,
            get_pathfinding_config,
            get_performance_config,
            get_combat_config,
            get_inventory_config,
            get_rendering_config,
            get_gameplay_config,
        )
        
        functions_to_test = [
            get_constants,
            get_pathfinding_config,
            get_performance_config,
            get_combat_config,
            get_inventory_config,
            get_rendering_config,
            get_gameplay_config,
        ]
        
        for func in functions_to_test:
            self.assertTrue(callable(func), f"{func.__name__} is not callable")
            
            # Test that calling the function doesn't raise an exception
            try:
                result = func()
                self.assertIsNotNone(result, f"{func.__name__} returned None")
            except Exception as e:
                self.fail(f"{func.__name__}() raised exception: {e}")


class TestConfigurationConsistency(unittest.TestCase):
    """Test that configuration values are consistent and reasonable."""

    def test_screen_dimensions_consistency(self):
        """Test that screen dimensions are consistent between configs."""
        rendering_config = get_rendering_config()
        legacy_constants = get_constants()
        
        self.assertEqual(
            rendering_config.DEFAULT_SCREEN_WIDTH,
            legacy_constants['screen_width']
        )
        self.assertEqual(
            rendering_config.DEFAULT_SCREEN_HEIGHT,
            legacy_constants['screen_height']
        )

    def test_map_dimensions_consistency(self):
        """Test that map dimensions are consistent between configs."""
        gameplay_config = get_gameplay_config()
        legacy_constants = get_constants()
        
        self.assertEqual(
            gameplay_config.DEFAULT_MAP_WIDTH,
            legacy_constants['map_width']
        )
        self.assertEqual(
            gameplay_config.DEFAULT_MAP_HEIGHT,
            legacy_constants['map_height']
        )

    def test_reasonable_default_values(self):
        """Test that all default values are reasonable."""
        combat_config = get_combat_config()
        inventory_config = get_inventory_config()
        
        # Combat values should be positive
        self.assertGreater(combat_config.DEFAULT_HP, 0)
        self.assertGreater(combat_config.DEFAULT_POWER, 0)
        self.assertGreaterEqual(combat_config.DEFAULT_DEFENSE, 0)
        
        # Inventory capacity should be reasonable
        self.assertGreaterEqual(inventory_config.DEFAULT_INVENTORY_CAPACITY, 1)
        self.assertLessEqual(inventory_config.DEFAULT_INVENTORY_CAPACITY, 100)


if __name__ == '__main__':
    unittest.main()
