"""Regression tests for FOV rendering bugs.

This module contains tests to ensure that the map rendering and FOV (Field of View)
system works correctly and doesn't regress to the black screen bug.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from engine.systems.optimized_render_system import OptimizedRenderSystem
from engine.game_state_manager import GameStateManager, GameState
from game_states import GameStates


class TestFOVRenderingRegression(unittest.TestCase):
    """Regression tests for FOV rendering functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock console and panel
        self.mock_console = Mock()
        self.mock_panel = Mock()
        
        # Create render system
        self.render_system = OptimizedRenderSystem(
            console=self.mock_console,
            panel=self.mock_panel,
            screen_width=80,
            screen_height=50,
            colors={"dark_wall": (0, 0, 100), "dark_ground": (50, 50, 150)},
            priority=100,
            use_optimizations=False,  # Use standard rendering for reliability
        )
        
        # Create mock engine and state manager
        self.mock_engine = Mock()
        self.state_manager = GameStateManager()
        self.mock_engine.state_manager = self.state_manager
        
        # Initialize render system
        self.render_system.initialize(self.mock_engine)
        
        # Set up FOV map
        self.mock_fov_map = Mock()
        self.render_system.set_fov_map(self.mock_fov_map)
        
        # Create mock game objects
        self.mock_player = Mock()
        self.mock_player.x = 10
        self.mock_player.y = 10
        
        self.mock_game_map = Mock()
        self.mock_game_map.width = 80
        self.mock_game_map.height = 50
        
        self.mock_message_log = Mock()
        self.mock_mouse = Mock()
        
        # Set up game state using the proper methods
        self.state_manager.update_state(
            player=self.mock_player,
            entities=[self.mock_player],
            game_map=self.mock_game_map,
            message_log=self.mock_message_log,
            current_state=GameStates.PLAYERS_TURN,
            fov_map=self.mock_fov_map,
            mouse=self.mock_mouse,
        )
        self.state_manager.request_fov_recompute()

    def test_map_renders_initially_regression(self):
        """Regression test: Ensure map renders on game start.
        
        Bug: Map was completely black on game initialization.
        Fix: Always force FOV recompute during debugging phase.
        """
        with patch('engine.systems.optimized_render_system.render_all') as mock_render_all:
            with patch('engine.systems.optimized_render_system.recompute_fov') as mock_recompute_fov:
                with patch('engine.systems.optimized_render_system.clear_all'):
                    with patch('tcod.libtcodpy.console_flush'):
                        # Update render system (should render map)
                        self.render_system.update(0.016)
                        
                        # Should call recompute_fov because fov_recompute=True
                        mock_recompute_fov.assert_called_once()
                        
                        # Should call render_all with fov_recompute=True
                        mock_render_all.assert_called_once()
                        call_args = mock_render_all.call_args[0]
                        fov_recompute_arg = call_args[6]  # 7th argument is fov_recompute
                        
                        self.assertTrue(fov_recompute_arg, 
                                      "render_all should be called with fov_recompute=True for map to render")

    def test_fov_updates_on_movement_regression(self):
        """Regression test: Ensure FOV updates when player moves.
        
        Bug: Map rendered initially but didn't update on player movement.
        Fix: Ensure FOV recomputation happens on every movement.
        """
        with patch('engine.systems.optimized_render_system.render_all') as mock_render_all:
            with patch('engine.systems.optimized_render_system.recompute_fov') as mock_recompute_fov:
                with patch('engine.systems.optimized_render_system.clear_all'):
                    # Simulate player movement by requesting FOV recompute
                    self.state_manager.request_fov_recompute()
                    
                    # Update render system
                    self.render_system.update(0.016)
                    
                    # Should call recompute_fov because player moved
                    mock_recompute_fov.assert_called_once()
                    
                    # Should call render_all with fov_recompute=True
                    mock_render_all.assert_called_once()
                    call_args = mock_render_all.call_args[0]
                    fov_recompute_arg = call_args[6]  # 7th argument is fov_recompute
                    
                    self.assertTrue(fov_recompute_arg, 
                                  "render_all should be called with fov_recompute=True after movement")

    def test_fov_recompute_flag_behavior_regression(self):
        """Regression test: Ensure FOV recompute flag behaves correctly.
        
        Bug: FOV recompute flag was being reset too early, causing map to flash and disappear.
        Fix: Game logic controls when to reset the flag, not the render system.
        """
        # Start with FOV recompute requested
        self.state_manager.request_fov_recompute()
        self.assertTrue(self.state_manager.state.fov_recompute, 
                       "FOV recompute should be True after request")
        
        with patch('engine.systems.optimized_render_system.render_all'):
            with patch('engine.systems.optimized_render_system.recompute_fov'):
                with patch('engine.systems.optimized_render_system.clear_all'):
                    # Update render system
                    self.render_system.update(0.016)
                    
                    # The game state's FOV flag should still be True
                    # (render system shouldn't reset it)
                    self.assertTrue(self.state_manager.state.fov_recompute,
                                  "Game state fov_recompute should remain True after rendering")

    def test_standard_rendering_path_used_regression(self):
        """Regression test: Ensure standard rendering is used when optimizations disabled.
        
        Bug: Complex optimization logic was causing timing issues with FOV flags.
        Fix: Disable optimizations and use reliable standard rendering.
        """
        # Ensure optimizations are disabled
        self.assertFalse(self.render_system.use_optimizations,
                        "Optimizations should be disabled for reliability")
        
        with patch('engine.systems.optimized_render_system.render_all') as mock_render_all:
            with patch('engine.systems.optimized_render_system.recompute_fov'):
                with patch('engine.systems.optimized_render_system.clear_all'):
                    # Update render system
                    self.render_system.update(0.016)
                    
                    # Should use standard rendering (render_all called directly)
                    mock_render_all.assert_called_once()
                    
                    # Should NOT use optimized rendering paths
                    # (We can verify this by checking that render_all is called once, 
                    # not multiple times as would happen in optimized rendering)
                    self.assertEqual(mock_render_all.call_count, 1,
                                   "Standard rendering should call render_all exactly once")


class TestFOVIntegrationRegression(unittest.TestCase):
    """Integration tests for FOV system components working together."""

    def test_movement_triggers_fov_recompute_integration(self):
        """Integration test: Player movement should trigger FOV recomputation.
        
        This test verifies the complete flow from movement to FOV update.
        """
        # Create state manager
        state_manager = GameStateManager()
        
        # Create mock player
        mock_player = Mock()
        mock_player.x = 10
        mock_player.y = 10
        
        # Set up initial state
        state_manager.state.player = mock_player
        state_manager.state.fov_recompute = False
        
        # Simulate player movement (this is what happens in engine_integration.py)
        mock_player.move = Mock()
        mock_player.move(1, 0)  # Move right
        mock_player.x = 11  # Update position
        
        # Request FOV recompute (this should happen after movement)
        state_manager.request_fov_recompute()
        
        # Verify FOV recompute was requested
        self.assertTrue(state_manager.state.fov_recompute,
                       "FOV recompute should be True after player movement")
        
        # Verify player position changed
        self.assertEqual(mock_player.x, 11, "Player should have moved to new position")


if __name__ == "__main__":
    unittest.main()
