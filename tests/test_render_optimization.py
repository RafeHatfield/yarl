"""Tests for tile rendering optimization system.

This module contains tests to verify that the optimized tile rendering
system provides performance improvements while maintaining correctness
and backward compatibility with the original rendering system.
"""

import unittest
from unittest.mock import Mock, patch, call
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from render_optimization import (
    OptimizedTileRenderer, TileRenderState, TileCache,
    render_tiles_optimized, get_tile_optimization_stats, reset_tile_optimization_stats
)
from map_objects.game_map import GameMap
from fov_functions import initialize_fov, recompute_fov


class TestTileRenderState(unittest.TestCase):
    """Test the TileRenderState enumeration."""
    
    def test_tile_render_states_exist(self):
        """Test that all expected tile render states are defined."""
        expected_states = [
            'UNEXPLORED', 'EXPLORED_WALL', 'EXPLORED_FLOOR', 
            'VISIBLE_WALL', 'VISIBLE_FLOOR'
        ]
        
        for state_name in expected_states:
            self.assertTrue(hasattr(TileRenderState, state_name))
            self.assertIsInstance(getattr(TileRenderState, state_name), TileRenderState)


class TestTileCache(unittest.TestCase):
    """Test the TileCache dataclass."""
    
    def test_tile_cache_creation(self):
        """Test TileCache creation and initialization."""
        cache = TileCache(
            render_state=TileRenderState.VISIBLE_FLOOR,
            last_fov_frame=10
        )
        
        self.assertEqual(cache.render_state, TileRenderState.VISIBLE_FLOOR)
        self.assertEqual(cache.last_fov_frame, 10)
        self.assertTrue(cache.needs_redraw)  # Should default to True
    
    def test_tile_cache_explicit_needs_redraw(self):
        """Test TileCache with explicit needs_redraw value."""
        cache = TileCache(
            render_state=TileRenderState.EXPLORED_WALL,
            last_fov_frame=5,
            needs_redraw=False
        )
        
        self.assertEqual(cache.render_state, TileRenderState.EXPLORED_WALL)
        self.assertEqual(cache.last_fov_frame, 5)
        self.assertFalse(cache.needs_redraw)


class TestOptimizedTileRenderer(unittest.TestCase):
    """Test the OptimizedTileRenderer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.renderer = OptimizedTileRenderer()
        self.mock_con = Mock()
        self.mock_colors = {
            'light_wall': Mock(),
            'light_ground': Mock(),
            'dark_wall': Mock(),
            'dark_ground': Mock()
        }
        
        # Create a simple test map
        self.game_map = GameMap(10, 10)
        # Make some tiles walls and some floors
        for x in range(10):
            for y in range(10):
                # Make border walls, interior floors
                if x == 0 or x == 9 or y == 0 or y == 9:
                    self.game_map.tiles[x][y].block_sight = True
                    self.game_map.tiles[x][y].blocked = True
                else:
                    self.game_map.tiles[x][y].block_sight = False
                    self.game_map.tiles[x][y].blocked = False
        
        self.fov_map = initialize_fov(self.game_map)
        recompute_fov(self.fov_map, 5, 5, 10)  # Center of map
    
    def test_renderer_initialization(self):
        """Test renderer initializes with correct default values."""
        renderer = OptimizedTileRenderer()
        
        self.assertEqual(len(renderer.tile_cache), 0)
        self.assertEqual(len(renderer.dirty_tiles), 0)
        self.assertEqual(renderer.last_fov_frame, -1)
        self.assertEqual(renderer.frame_counter, 0)
        self.assertEqual(renderer.map_width, 0)
        self.assertEqual(renderer.map_height, 0)
        
        # Check stats initialization
        expected_stats = [
            'total_frames', 'tiles_cached', 'tiles_redrawn', 'cache_hits',
            'cache_misses', 'fov_changes', 'full_redraws'
        ]
        for stat in expected_stats:
            self.assertIn(stat, renderer.optimization_stats)
            self.assertEqual(renderer.optimization_stats[stat], 0)
    
    def test_render_tiles_optimized_first_call(self):
        """Test first call to render_tiles_optimized forces full redraw."""
        with patch.object(self.renderer, '_render_all_tiles') as mock_render_all:
            self.renderer.render_tiles_optimized(
                self.mock_con, self.game_map, self.fov_map, self.mock_colors
            )
            
            # First call should trigger full redraw due to map size change
            mock_render_all.assert_called_once()
            self.assertEqual(self.renderer.frame_counter, 1)
            self.assertEqual(self.renderer.optimization_stats['total_frames'], 1)
            self.assertEqual(self.renderer.optimization_stats['full_redraws'], 1)
    
    @patch('tcod.libtcodpy.console_set_char_background')
    def test_render_tiles_optimized_subsequent_calls(self, mock_console_set):
        """Test subsequent calls use dirty rectangle rendering."""
        # First call to initialize
        self.renderer.render_tiles_optimized(
            self.mock_con, self.game_map, self.fov_map, self.mock_colors
        )
        
        # Reset mock and make second call
        self.mock_con.reset_mock()
        with patch.object(self.renderer, '_render_dirty_tiles') as mock_render_dirty:
            self.renderer.render_tiles_optimized(
                self.mock_con, self.game_map, self.fov_map, self.mock_colors
            )
            
            # Second call should use dirty rendering (no dirty tiles = no rendering)
            mock_render_dirty.assert_called_once()
            self.assertEqual(self.renderer.frame_counter, 2)
    
    def test_mark_tile_dirty(self):
        """Test marking individual tiles as dirty."""
        self.renderer.mark_tile_dirty(5, 5)
        
        self.assertIn((5, 5), self.renderer.dirty_tiles)
        
        # If tile is cached, it should be marked for redraw
        cache_key = (5, 5)
        self.renderer.tile_cache[cache_key] = TileCache(
            render_state=TileRenderState.VISIBLE_FLOOR,
            last_fov_frame=1,
            needs_redraw=False
        )
        
        self.renderer.mark_tile_dirty(5, 5)
        self.assertTrue(self.renderer.tile_cache[cache_key].needs_redraw)
    
    def test_mark_area_dirty(self):
        """Test marking rectangular areas as dirty."""
        self.renderer.mark_area_dirty(2, 2, 4, 4)
        
        # Should mark all tiles in the 3x3 area
        expected_tiles = {(2, 2), (2, 3), (2, 4), (3, 2), (3, 3), (3, 4), (4, 2), (4, 3), (4, 4)}
        for tile in expected_tiles:
            self.assertIn(tile, self.renderer.dirty_tiles)
    
    @patch('tcod.libtcodpy.console_set_char_background')
    def test_cache_rebuild_on_map_size_change(self, mock_console_set):
        """Test cache rebuilds when map size changes."""
        # Initialize with one size
        self.renderer.render_tiles_optimized(
            self.mock_con, self.game_map, self.fov_map, self.mock_colors
        )
        
        initial_cache_size = len(self.renderer.tile_cache)
        
        # Create new map with different size
        new_map = GameMap(15, 15)
        new_fov = initialize_fov(new_map)
        
        with patch.object(self.renderer, '_rebuild_cache') as mock_rebuild:
            self.renderer.render_tiles_optimized(
                self.mock_con, new_map, new_fov, self.mock_colors
            )
            
            mock_rebuild.assert_called_once_with(15, 15)
    
    @patch('tcod.libtcodpy.console_set_char_background')
    def test_optimization_stats(self, mock_console_set):
        """Test optimization statistics tracking."""
        # Render a few frames
        for _ in range(3):
            self.renderer.render_tiles_optimized(
                self.mock_con, self.game_map, self.fov_map, self.mock_colors
            )
        
        stats = self.renderer.get_optimization_stats()
        
        self.assertEqual(stats['total_frames'], 3)
        self.assertGreaterEqual(stats['full_redraws'], 1)  # At least first frame
        self.assertIn('cache_hit_rate', stats)
        self.assertIn('avg_tiles_per_frame', stats)
    
    @patch('tcod.libtcodpy.console_set_char_background')
    def test_reset_stats(self, mock_console_set):
        """Test resetting optimization statistics."""
        # Generate some stats
        self.renderer.render_tiles_optimized(
            self.mock_con, self.game_map, self.fov_map, self.mock_colors
        )
        
        # Reset and verify
        self.renderer.reset_stats()
        
        for value in self.renderer.optimization_stats.values():
            self.assertEqual(value, 0)


class TestGlobalFunctions(unittest.TestCase):
    """Test global convenience functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_tile_optimization_stats()  # Start with clean stats
        
        self.mock_con = Mock()
        self.mock_colors = {'light_wall': Mock(), 'light_ground': Mock()}
        self.game_map = GameMap(5, 5)
        self.fov_map = initialize_fov(self.game_map)
    
    def test_render_tiles_optimized_global(self):
        """Test global render_tiles_optimized function."""
        # Should not raise any exceptions
        render_tiles_optimized(
            self.mock_con, self.game_map, self.fov_map, self.mock_colors
        )
        
        # Should update global stats
        stats = get_tile_optimization_stats()
        self.assertGreater(stats['total_frames'], 0)
    
    def test_get_tile_optimization_stats_global(self):
        """Test global stats function."""
        stats = get_tile_optimization_stats()
        
        self.assertIsInstance(stats, dict)
        expected_keys = [
            'total_frames', 'tiles_cached', 'tiles_redrawn', 'cache_hits',
            'cache_misses', 'fov_changes', 'full_redraws', 'cache_hit_rate',
            'avg_tiles_per_frame'
        ]
        for key in expected_keys:
            self.assertIn(key, stats)
    
    def test_reset_tile_optimization_stats_global(self):
        """Test global stats reset function."""
        # Generate some stats
        render_tiles_optimized(
            self.mock_con, self.game_map, self.fov_map, self.mock_colors
        )
        
        # Reset and verify
        reset_tile_optimization_stats()
        stats = get_tile_optimization_stats()
        
        # All basic stats should be 0
        basic_stats = ['total_frames', 'tiles_cached', 'tiles_redrawn', 'cache_hits',
                      'cache_misses', 'fov_changes', 'full_redraws']
        for stat in basic_stats:
            self.assertEqual(stats[stat], 0)


class TestRenderingCorrectness(unittest.TestCase):
    """Test that optimized rendering produces correct results."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.renderer = OptimizedTileRenderer()
        self.mock_con = Mock()
        self.mock_colors = {
            'light_wall': 'light_wall_color',
            'light_ground': 'light_ground_color',
            'dark_wall': 'dark_wall_color',
            'dark_ground': 'dark_ground_color'
        }
        
        # Create test map with known layout
        self.game_map = GameMap(5, 5)
        # Make center tile a floor, others walls
        for x in range(5):
            for y in range(5):
                if x == 2 and y == 2:
                    self.game_map.tiles[x][y].block_sight = False
                    self.game_map.tiles[x][y].blocked = False
                else:
                    self.game_map.tiles[x][y].block_sight = True
                    self.game_map.tiles[x][y].blocked = True
        
        self.fov_map = initialize_fov(self.game_map)
        recompute_fov(self.fov_map, 2, 2, 10)  # Center position
    
    @patch('tcod.libtcodpy.console_set_char_background')
    def test_visible_tiles_rendered_correctly(self, mock_console_set):
        """Test that visible tiles are rendered with correct colors."""
        self.renderer.render_tiles_optimized(
            self.mock_con, self.game_map, self.fov_map, self.mock_colors
        )
        
        # Should have calls to set background for visible tiles
        mock_console_set.assert_called()
        
        # Check that visible center tile (floor) gets light_ground color
        center_calls = [call for call in mock_console_set.call_args_list 
                       if call[0][:3] == (self.mock_con, 2, 2)]
        self.assertTrue(any('light_ground_color' in str(call) for call in center_calls))


if __name__ == '__main__':
    unittest.main()
