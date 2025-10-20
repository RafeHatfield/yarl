"""Regression tests for map rendering issues.

This module contains tests to prevent regressions in map rendering,
specifically the issue where the map renders as completely black.
"""


# QUARANTINED: Rendering tests need display mocking
# See QUARANTINED_TESTS.md for details.

import pytest

# Quarantine entire file
# pytestmark = pytest.mark.skip(reason="Quarantined - Rendering tests need display mocking. See QUARANTINED_TESTS.md")  # REMOVED Session 2

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from loader_functions.initialize_new_game import get_game_variables, get_constants
from fov_functions import initialize_fov, recompute_fov
from render_functions import render_all, _render_tiles_original
from render_optimization import render_tiles_optimized, reset_tile_renderer


class TestMapRenderingRegression(unittest.TestCase):
    """Regression tests for map rendering issues."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Reset tile renderer to ensure clean state between tests
        reset_tile_renderer()
        
        # Create game state
        self.constants = get_constants()
        self.player, self.entities, self.game_map, self.message_log, self.game_state = get_game_variables(self.constants)
        
        # Initialize FOV
        self.fov_map = initialize_fov(self.game_map)
        recompute_fov(self.fov_map, self.player.x, self.player.y, 10)
        
        # Mock objects for rendering
        self.mock_con = Mock()
        self.mock_panel = Mock()
        self.mock_mouse = Mock()
        self.mock_mouse.cx = 0  # Add required mouse coordinates
        self.mock_mouse.cy = 0
        self.colors = self.constants['colors']
    
    def test_map_tiles_are_rendered_with_optimization(self):
        """Regression test: Map should not render as completely black with optimization.
        
        This test prevents the regression where tile optimization caused
        the entire map to render as black instead of showing visible tiles.
        """
        # Track console background setting calls
        with patch('tcod.libtcodpy.console_set_char_background') as mock_set_bg:
            with patch('tcod.libtcodpy.console_blit'):
                with patch('tcod.libtcodpy.console_clear'):
                    with patch('tcod.libtcodpy.console_set_default_background'):
                        with patch('tcod.libtcodpy.console_set_default_foreground'):
                            with patch('tcod.libtcodpy.console_put_char'):
                                with patch('tcod.libtcodpy.console_print_ex'):
                                    with patch('tcod.libtcodpy.console_rect'):
                                        # Test optimized tile rendering directly
                                        render_tiles_optimized(
                                            self.mock_con, self.game_map, self.fov_map, self.colors
                                        )
        
        # Verify that tiles were actually rendered (background colors set)
        self.assertGreater(mock_set_bg.call_count, 0, 
                          "Optimized rendering should set tile background colors")
        
        # Check that visible tiles around player were rendered
        player_area_calls = []
        for call in mock_set_bg.call_args_list:
            x, y = call[0][1], call[0][2]  # Extract x, y from call args
            # Check if call is near player position
            if (abs(x - self.player.x) <= 5 and abs(y - self.player.y) <= 5):
                player_area_calls.append(call)
        
        self.assertGreater(len(player_area_calls), 0,
                          "Should render tiles near player position")
    
    def test_map_tiles_are_rendered_without_optimization(self):
        """Test that original rendering still works correctly."""
        # Track console background setting calls
        with patch('tcod.libtcodpy.console_set_char_background') as mock_set_bg:
            # Test original tile rendering
            _render_tiles_original(self.mock_con, self.game_map, self.fov_map, self.colors)
        
        # Verify that tiles were rendered
        self.assertGreater(mock_set_bg.call_count, 0,
                          "Original rendering should set tile background colors")
        
        # Original rendering only renders visible/explored tiles, not all tiles
        # Just verify that a reasonable number of tiles were rendered (visible area around player)
        self.assertGreater(mock_set_bg.call_count, 50,
                          "Original rendering should process visible tiles around player")
    
    def test_optimization_vs_original_consistency(self):
        """Test that optimized and original rendering produce similar results."""
        # Test optimized rendering
        with patch('tcod.libtcodpy.console_set_char_background') as mock_set_bg_opt:
            render_tiles_optimized(self.mock_con, self.game_map, self.fov_map, self.colors)
        
        opt_calls = mock_set_bg_opt.call_args_list
        
        # Test original rendering
        with patch('tcod.libtcodpy.console_set_char_background') as mock_set_bg_orig:
            _render_tiles_original(self.mock_con, self.game_map, self.fov_map, self.colors)
        
        orig_calls = mock_set_bg_orig.call_args_list
        
        # Both should render some tiles
        self.assertGreater(len(opt_calls), 0, "Optimized rendering should render tiles")
        self.assertGreater(len(orig_calls), 0, "Original rendering should render tiles")
        
        # Extract positions that were rendered by each method
        opt_positions = {(call[0][1], call[0][2]) for call in opt_calls}
        orig_positions = {(call[0][1], call[0][2]) for call in orig_calls}
        
        # Find visible positions around player
        visible_positions = set()
        for dy in range(-10, 11):
            for dx in range(-10, 11):
                x, y = self.player.x + dx, self.player.y + dy
                if (0 <= x < self.game_map.width and 0 <= y < self.game_map.height):
                    from fov_functions import map_is_in_fov
                    if map_is_in_fov(self.fov_map, x, y):
                        visible_positions.add((x, y))
        
        # Both methods should render at least some visible positions
        opt_visible = opt_positions.intersection(visible_positions)
        orig_visible = orig_positions.intersection(visible_positions)
        
        self.assertGreater(len(opt_visible), 0,
                          "Optimized rendering should render visible tiles")
        self.assertGreater(len(orig_visible), 0,
                          "Original rendering should render visible tiles")
    
    def test_render_all_with_optimization_flag(self):
        """Test that render_all respects the use_optimization flag."""
        # Mock all the console functions that render_all uses
        patches = [
            'tcod.libtcodpy.console_set_char_background',
            'tcod.libtcodpy.console_blit',
            'tcod.libtcodpy.console_clear',
            'tcod.libtcodpy.console_set_default_background',
            'tcod.libtcodpy.console_set_default_foreground',
            'tcod.libtcodpy.console_put_char',
            'tcod.libtcodpy.console_print_ex',
            'tcod.libtcodpy.console_rect'
        ]
        
        # Mock the effect queue to prevent visual effects from running
        with patch('render_functions.get_effect_queue') as mock_effect_queue, \
             patch.multiple('tcod.libtcodpy', **{p.split('.')[-1]: Mock() for p in patches}):
            
            mock_queue = Mock()
            mock_queue.has_effects.return_value = False
            mock_effect_queue.return_value = mock_queue
            # Test with optimization enabled
            try:
                render_all(
                    self.mock_con, self.mock_panel, self.entities, self.player,
                    self.game_map, self.fov_map, True, self.message_log,
                    80, 43, 20, 7, 45, self.mock_mouse, self.colors, self.game_state,  # panel_y updated to 45
                    use_optimization=True
                )
                opt_success = True
            except Exception as e:
                opt_success = False
                opt_error = str(e)
            
            # Test with optimization disabled
            try:
                render_all(
                    self.mock_con, self.mock_panel, self.entities, self.player,
                    self.game_map, self.fov_map, True, self.message_log,
                    80, 43, 20, 7, 45, self.mock_mouse, self.colors, self.game_state,  # panel_y updated to 45
                    use_optimization=False
                )
                orig_success = True
            except Exception as e:
                orig_success = False
                orig_error = str(e)
        
        # Both should succeed
        if not opt_success:
            self.fail(f"Optimized render_all failed: {opt_error}")
        if not orig_success:
            self.fail(f"Original render_all failed: {orig_error}")
    
    def test_black_screen_regression(self):
        """Specific regression test for the black screen issue.
        
        This test specifically checks that visible tiles around the player
        are rendered with appropriate colors, not left black.
        """
        rendered_tiles = {}
        
        def capture_tile_render(con, x, y, color, flag):
            """Capture what tiles are being rendered with what colors."""
            rendered_tiles[(x, y)] = color
        
        with patch('tcod.libtcodpy.console_set_char_background', side_effect=capture_tile_render):
            render_tiles_optimized(self.mock_con, self.game_map, self.fov_map, self.colors)
        
        # Check that tiles around player were rendered
        player_tiles_rendered = 0
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                x, y = self.player.x + dx, self.player.y + dy
                if (0 <= x < self.game_map.width and 0 <= y < self.game_map.height):
                    from fov_functions import map_is_in_fov
                    if map_is_in_fov(self.fov_map, x, y):
                        if (x, y) in rendered_tiles:
                            player_tiles_rendered += 1
                            # Verify the tile has a proper color (not black/None)
                            color = rendered_tiles[(x, y)]
                            self.assertIsNotNone(color, f"Tile at ({x}, {y}) should have a color")
        
        self.assertGreater(player_tiles_rendered, 0,
                          "Should render visible tiles around player (not black screen)")


if __name__ == '__main__':
    unittest.main()
