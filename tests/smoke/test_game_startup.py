"""Smoke tests for game startup and initialization.

These tests ensure the game can start up correctly and all core systems
initialize without errors. This prevents runtime regressions that might
not be caught by unit tests.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestGameStartup(unittest.TestCase):
    """Test game startup and core system initialization."""
    
    def test_constants_loading(self):
        """Test that game constants load without errors."""
        from loader_functions.initialize_new_game import get_constants
        
        constants = get_constants()
        
        # Verify essential constants exist
        self.assertIn('screen_width', constants)
        self.assertIn('screen_height', constants)
        self.assertIn('window_title', constants)
        self.assertIsInstance(constants['screen_width'], int)
        self.assertIsInstance(constants['screen_height'], int)
        
    def test_game_variables_creation(self):
        """Test that game variables can be created without errors."""
        from loader_functions.initialize_new_game import get_game_variables, get_constants
        
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Verify all components were created
        self.assertIsNotNone(player)
        self.assertIsNotNone(entities)
        self.assertIsNotNone(game_map)
        self.assertIsNotNone(message_log)
        self.assertIsNotNone(game_state)
        
        # Verify player has required components
        self.assertTrue(hasattr(player, 'fighter'))
        self.assertTrue(hasattr(player, 'inventory'))
        self.assertTrue(hasattr(player, 'level'))
        self.assertTrue(hasattr(player, 'equipment'))
        
    def test_fov_system_initialization(self):
        """Test that FOV system initializes correctly with modern API."""
        from loader_functions.initialize_new_game import get_game_variables, get_constants
        from fov_functions import initialize_fov, recompute_fov, map_is_in_fov
        
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Test FOV map creation
        fov_map = initialize_fov(game_map)
        self.assertIsNotNone(fov_map)
        
        # Test FOV computation
        recompute_fov(fov_map, player.x, player.y, 10)
        
        # Test visibility checking - check if FOV computation worked
        # The exact visibility depends on map layout, so just verify the function works
        is_visible = map_is_in_fov(fov_map, player.x, player.y)
        self.assertIsInstance(is_visible, bool)  # Should return a boolean value
        
        # Test that FOV map has the expected structure
        self.assertTrue(hasattr(fov_map, 'compute_fov'))
        self.assertTrue(hasattr(fov_map, 'is_in_fov'))
        
    def test_game_engine_creation(self):
        """Test that game engine can be created without GUI."""
        from engine_integration import create_game_engine
        from loader_functions.initialize_new_game import get_constants
        
        # Mock console objects to avoid GUI initialization
        mock_con = Mock()
        mock_panel = Mock()
        
        constants = get_constants()
        engine = create_game_engine(constants, Mock(), Mock(), Mock())  # sidebar, viewport, status
        
        self.assertIsNotNone(engine)
        self.assertTrue(hasattr(engine, 'systems'))
        self.assertTrue(hasattr(engine, 'update'))
        
    def test_game_engine_initialization(self):
        """Test that game engine initializes all systems correctly."""
        from engine_integration import create_game_engine, initialize_game_engine
        from loader_functions.initialize_new_game import get_game_variables, get_constants
        
        # Mock console objects
        mock_con = Mock()
        mock_panel = Mock()
        
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Create and initialize engine
        engine = create_game_engine(constants, Mock(), Mock(), Mock())  # sidebar, viewport, status
        initialize_game_engine(engine, player, entities, game_map, message_log, game_state, constants)
        
        # Verify systems are initialized
        self.assertTrue(len(engine.systems) > 0)
        
        # Verify key systems exist
        system_names = [system.name for system in engine.systems.values()]
        self.assertIn('performance', system_names)
        self.assertIn('ai', system_names)
        
    def test_configuration_system_integrity(self):
        """Test that configuration system works correctly."""
        from config.game_constants import (
            get_constants, get_pathfinding_config, get_performance_config,
            get_combat_config, get_inventory_config, get_rendering_config,
            get_gameplay_config
        )
        
        # Test all configuration getters work
        constants = get_constants()
        pathfinding_config = get_pathfinding_config()
        performance_config = get_performance_config()
        combat_config = get_combat_config()
        inventory_config = get_inventory_config()
        rendering_config = get_rendering_config()
        gameplay_config = get_gameplay_config()
        
        # Verify configurations are valid
        self.assertIsNotNone(constants)
        self.assertIsNotNone(pathfinding_config)
        self.assertIsNotNone(performance_config)
        self.assertIsNotNone(combat_config)
        self.assertIsNotNone(inventory_config)
        self.assertIsNotNone(rendering_config)
        self.assertIsNotNone(gameplay_config)
        
    @patch('tcod.libtcodpy.console_init_root')
    @patch('tcod.libtcodpy.console_new')
    @patch('tcod.libtcodpy.image_load')
    def test_main_engine_startup_flow(self, mock_image_load, mock_console_new, mock_console_init):
        """Test the main engine startup flow without actual GUI initialization."""
        from loader_functions.initialize_new_game import get_constants
        
        # Mock GUI components
        mock_console_init.return_value = None
        mock_console_new.return_value = Mock()
        mock_image_load.return_value = Mock()
        
        # Test constants loading in main flow
        constants = get_constants()
        
        # Verify essential startup constants
        self.assertIn('screen_width', constants)
        self.assertIn('screen_height', constants)
        self.assertIn('window_title', constants)
        self.assertIn('panel_height', constants)
        
        # Verify console initialization would be called correctly
        # (This tests the parameters without actually initializing GUI)
        expected_width = constants['screen_width']
        expected_height = constants['screen_height']
        expected_title = constants['window_title']
        
        self.assertIsInstance(expected_width, int)
        self.assertIsInstance(expected_height, int)
        self.assertIsInstance(expected_title, str)
        
    def test_action_processor_initialization(self):
        """Test that action processor can be created and used."""
        from game_actions import ActionProcessor
        from engine.game_state_manager import GameStateManager
        from loader_functions.initialize_new_game import get_game_variables, get_constants
        
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Create state manager
        state_manager = GameStateManager()
        state_manager.initialize_game(player, entities, game_map, message_log, game_state, constants)
        
        # Create action processor
        action_processor = ActionProcessor(state_manager)
        
        self.assertIsNotNone(action_processor)
        self.assertTrue(hasattr(action_processor, 'process_actions'))
        self.assertTrue(hasattr(action_processor, 'action_handlers'))


if __name__ == '__main__':
    unittest.main()
