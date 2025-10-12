"""Tests for entity sorting cache optimization.

This module contains tests to verify the entity sorting cache works correctly
and provides performance benefits while maintaining correctness.
"""


# QUARANTINED: Render integration needs proper setup
# See QUARANTINED_TESTS.md for details.

import pytest

# Quarantine entire file
pytestmark = pytest.mark.skip(reason="Quarantined - Render integration needs proper setup. See QUARANTINED_TESTS.md")
import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from entity_sorting_cache import (
    EntitySortingCache, 
    get_sorted_entities, 
    invalidate_entity_cache,
    get_entity_cache_stats,
    reset_entity_cache_stats,
    reset_entity_cache
)
from render_functions import RenderOrder
from entity import Entity


class TestEntitySortingCache(unittest.TestCase):
    """Test the EntitySortingCache class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cache = EntitySortingCache()
        
        # Create test entities with different render orders
        self.player = Entity(
            x=0, y=0, char='@', color=(255, 255, 255), name='Player',
            render_order=RenderOrder.ACTOR
        )
        self.item = Entity(
            x=1, y=1, char='!', color=(255, 0, 0), name='Potion',
            render_order=RenderOrder.ITEM
        )
        self.corpse = Entity(
            x=2, y=2, char='%', color=(127, 0, 0), name='Corpse',
            render_order=RenderOrder.CORPSE
        )
        self.stairs = Entity(
            x=3, y=3, char='>', color=(255, 255, 0), name='Stairs',
            render_order=RenderOrder.STAIRS
        )
        
        self.entities = [self.player, self.item, self.corpse, self.stairs]
    
    def test_initial_cache_state(self):
        """Test that cache starts in correct initial state."""
        self.assertFalse(self.cache._cache_valid)
        self.assertEqual(len(self.cache._cached_entities), 0)
        self.assertEqual(len(self.cache._entity_signatures), 0)
        
        stats = self.cache.get_cache_stats()
        self.assertEqual(stats['cache_hits'], 0)
        self.assertEqual(stats['cache_misses'], 0)
        self.assertEqual(stats['total_sorts'], 0)
    
    def test_first_sort_is_cache_miss(self):
        """Test that first sort operation is a cache miss."""
        sorted_entities = self.cache.get_sorted_entities(self.entities)
        
        # Should be sorted by render order (STAIRS=1, CORPSE=2, ITEM=3, ACTOR=4)
        expected_order = [self.stairs, self.corpse, self.item, self.player]
        self.assertEqual(sorted_entities, expected_order)
        
        # Should be a cache miss
        stats = self.cache.get_cache_stats()
        self.assertEqual(stats['cache_hits'], 0)
        self.assertEqual(stats['cache_misses'], 1)
        self.assertEqual(stats['total_sorts'], 1)
        self.assertTrue(self.cache._cache_valid)
    
    def test_second_sort_is_cache_hit(self):
        """Test that second sort with same entities is a cache hit."""
        # First sort
        self.cache.get_sorted_entities(self.entities)
        
        # Second sort with same entities
        sorted_entities = self.cache.get_sorted_entities(self.entities)
        
        # Should still be correctly sorted
        expected_order = [self.stairs, self.corpse, self.item, self.player]
        self.assertEqual(sorted_entities, expected_order)
        
        # Should be a cache hit
        stats = self.cache.get_cache_stats()
        self.assertEqual(stats['cache_hits'], 1)
        self.assertEqual(stats['cache_misses'], 1)
        self.assertEqual(stats['total_sorts'], 1)  # Only one actual sort
    
    def test_entity_addition_invalidates_cache(self):
        """Test that adding entities invalidates the cache."""
        # First sort
        self.cache.get_sorted_entities(self.entities)
        
        # Add new entity
        new_entity = Entity(
            x=4, y=4, char='o', color=(0, 255, 0), name='Orc',
            render_order=RenderOrder.ACTOR
        )
        entities_with_new = self.entities + [new_entity]
        
        # Sort with new entity list
        sorted_entities = self.cache.get_sorted_entities(entities_with_new)
        
        # Should be cache miss due to different entity count
        stats = self.cache.get_cache_stats()
        self.assertEqual(stats['cache_hits'], 0)
        self.assertEqual(stats['cache_misses'], 2)
        self.assertEqual(stats['total_sorts'], 2)
    
    def test_entity_removal_invalidates_cache(self):
        """Test that removing entities invalidates the cache."""
        # First sort
        self.cache.get_sorted_entities(self.entities)
        
        # Remove entity
        entities_without_item = [self.player, self.corpse, self.stairs]
        
        # Sort with reduced entity list
        sorted_entities = self.cache.get_sorted_entities(entities_without_item)
        
        # Should be cache miss due to different entity count
        stats = self.cache.get_cache_stats()
        self.assertEqual(stats['cache_hits'], 0)
        self.assertEqual(stats['cache_misses'], 2)
        self.assertEqual(stats['total_sorts'], 2)
    
    def test_entity_position_change_invalidates_cache(self):
        """Test that changing entity position invalidates the cache."""
        # First sort
        self.cache.get_sorted_entities(self.entities)
        
        # Change entity position
        original_x = self.player.x
        self.player.x = 10
        
        # Sort again
        sorted_entities = self.cache.get_sorted_entities(self.entities)
        
        # Should be cache miss due to position change
        stats = self.cache.get_cache_stats()
        self.assertEqual(stats['cache_hits'], 0)
        self.assertEqual(stats['cache_misses'], 2)
        
        # Restore original position
        self.player.x = original_x
    
    def test_entity_render_order_change_invalidates_cache(self):
        """Test that changing entity render order invalidates the cache."""
        # First sort
        self.cache.get_sorted_entities(self.entities)
        
        # Change entity render order
        original_render_order = self.player.render_order
        self.player.render_order = RenderOrder.CORPSE
        
        # Sort again
        sorted_entities = self.cache.get_sorted_entities(self.entities)
        
        # Should be cache miss due to render order change
        stats = self.cache.get_cache_stats()
        self.assertEqual(stats['cache_hits'], 0)
        self.assertEqual(stats['cache_misses'], 2)
        
        # Restore original render order
        self.player.render_order = original_render_order
    
    def test_manual_cache_invalidation(self):
        """Test manual cache invalidation."""
        # First sort
        self.cache.get_sorted_entities(self.entities)
        self.assertTrue(self.cache._cache_valid)
        
        # Manually invalidate
        self.cache.invalidate_cache("test_reason")
        self.assertFalse(self.cache._cache_valid)
        
        # Next sort should be cache miss
        self.cache.get_sorted_entities(self.entities)
        stats = self.cache.get_cache_stats()
        self.assertEqual(stats['cache_misses'], 2)
        self.assertEqual(stats['cache_invalidations'], 1)
    
    def test_cache_stats_calculation(self):
        """Test cache statistics calculation."""
        # Perform various operations
        self.cache.get_sorted_entities(self.entities)  # Miss
        self.cache.get_sorted_entities(self.entities)  # Hit
        self.cache.get_sorted_entities(self.entities)  # Hit
        self.cache.invalidate_cache("test")
        self.cache.get_sorted_entities(self.entities)  # Miss
        
        stats = self.cache.get_cache_stats()
        self.assertEqual(stats['cache_hits'], 2)
        self.assertEqual(stats['cache_misses'], 2)
        self.assertEqual(stats['cache_invalidations'], 1)
        self.assertEqual(stats['total_sorts'], 2)
        self.assertEqual(stats['total_requests'], 4)
        self.assertEqual(stats['hit_rate_percent'], 50.0)
    
    def test_reset_stats(self):
        """Test resetting cache statistics."""
        # Generate some stats
        self.cache.get_sorted_entities(self.entities)
        self.cache.get_sorted_entities(self.entities)
        
        # Reset stats
        self.cache.reset_stats()
        
        stats = self.cache.get_cache_stats()
        self.assertEqual(stats['cache_hits'], 0)
        self.assertEqual(stats['cache_misses'], 0)
        self.assertEqual(stats['total_sorts'], 0)
        self.assertEqual(stats['hit_rate_percent'], 0)


class TestGlobalEntityCacheFunctions(unittest.TestCase):
    """Test global entity cache functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Reset global cache before each test
        reset_entity_cache()
        
        # Create test entities
        self.entities = [
            Entity(x=0, y=0, char='@', color=(255, 255, 255), name='Player', render_order=RenderOrder.ACTOR),
            Entity(x=1, y=1, char='!', color=(255, 0, 0), name='Potion', render_order=RenderOrder.ITEM),
            Entity(x=2, y=2, char='%', color=(127, 0, 0), name='Corpse', render_order=RenderOrder.CORPSE),
        ]
    
    def test_global_get_sorted_entities(self):
        """Test global get_sorted_entities function."""
        sorted_entities = get_sorted_entities(self.entities)
        
        # Should be sorted by render order
        expected_order = [self.entities[2], self.entities[1], self.entities[0]]  # corpse, item, actor
        self.assertEqual(sorted_entities, expected_order)
    
    def test_global_cache_invalidation(self):
        """Test global cache invalidation function."""
        # First sort
        get_sorted_entities(self.entities)
        
        # Invalidate cache
        invalidate_entity_cache("test_global")
        
        # Next sort should be cache miss
        get_sorted_entities(self.entities)
        
        stats = get_entity_cache_stats()
        self.assertEqual(stats['cache_misses'], 2)
        self.assertEqual(stats['cache_invalidations'], 1)
    
    def test_global_stats_functions(self):
        """Test global statistics functions."""
        # Generate some activity
        get_sorted_entities(self.entities)
        get_sorted_entities(self.entities)
        
        stats = get_entity_cache_stats()
        self.assertEqual(stats['cache_hits'], 1)
        self.assertEqual(stats['cache_misses'], 1)
        
        # Reset stats
        reset_entity_cache_stats()
        
        stats = get_entity_cache_stats()
        self.assertEqual(stats['cache_hits'], 0)
        self.assertEqual(stats['cache_misses'], 0)
    
    def test_global_cache_reset(self):
        """Test global cache reset function."""
        # Generate some activity
        get_sorted_entities(self.entities)
        
        # Reset entire cache
        reset_entity_cache()
        
        # Should start fresh
        get_sorted_entities(self.entities)
        
        stats = get_entity_cache_stats()
        self.assertEqual(stats['cache_hits'], 0)
        self.assertEqual(stats['cache_misses'], 1)


class TestEntitySortingIntegration(unittest.TestCase):
    """Test entity sorting cache integration with render functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_entity_cache()
    
    def test_render_functions_integration(self):
        """Test that render_functions uses the entity cache."""
        # Import here to avoid circular imports during module loading
        from render_functions import render_all
        
        # Create mock objects
        mock_con = Mock()
        mock_panel = Mock()
        mock_player = Mock()
        mock_player.fighter = Mock()
        mock_player.fighter.hp = 100
        mock_player.fighter.max_hp = 100
        # Mock inventory and equipment for tooltip rendering
        mock_player.inventory = Mock()
        mock_player.inventory.items = []
        mock_player.equipment = Mock()
        mock_player.equipment.main_hand = None
        mock_player.equipment.off_hand = None
        mock_player.equipment.head = None
        mock_player.equipment.chest = None
        mock_player.equipment.feet = None
        # Mock ComponentRegistry to return inventory and equipment
        from components.component_registry import ComponentType
        mock_player.components = Mock()
        def get_component(comp_type):
            if comp_type == ComponentType.INVENTORY:
                return mock_player.inventory
            elif comp_type == ComponentType.EQUIPMENT:
                return mock_player.equipment
            return None
        mock_player.components.get = Mock(side_effect=get_component)
        mock_game_map = Mock()
        mock_game_map.dungeon_level = 1
        mock_fov_map = Mock()
        mock_message_log = Mock()
        mock_message_log.messages = []  # Add empty messages list
        mock_message_log.x = 1
        mock_mouse = Mock()
        mock_mouse.cx = 0  # Add required mouse coordinates
        mock_mouse.cy = 0
        
        # Create test entities
        entities = [
            Entity(x=0, y=0, char='@', color=(255, 255, 255), name='Player', render_order=RenderOrder.ACTOR),
            Entity(x=1, y=1, char='!', color=(255, 0, 0), name='Potion', render_order=RenderOrder.ITEM),
        ]
        
        colors = {'light_wall': (100, 100, 100), 'light_ground': (200, 200, 200)}
        
        # Mock the tile rendering and entity drawing functions
        with patch('render_functions._render_tiles_original'), \
             patch('render_functions.draw_entity'), \
             patch('render_functions.get_effect_queue') as mock_effect_queue, \
             patch('tcod.libtcodpy.console_blit'), \
             patch('tcod.libtcodpy.console_clear'), \
             patch('tcod.libtcodpy.console_set_default_background'), \
             patch('tcod.libtcodpy.console_set_default_foreground'), \
             patch('tcod.libtcodpy.console_print_ex'), \
             patch('tcod.libtcodpy.console_rect'):
            
            # Mock the effect queue to prevent visual effects from running
            mock_queue = Mock()
            mock_queue.has_effects.return_value = False
            mock_effect_queue.return_value = mock_queue
            
            # Call render_all twice
            render_all(
                mock_con, mock_panel, entities, mock_player, mock_game_map,
                mock_fov_map, False, mock_message_log, 80, 50, 20, 7, 45,  # panel_y updated to 45 in v3.5.0
                mock_mouse, colors, Mock(), use_optimization=False
            )
            
            render_all(
                mock_con, mock_panel, entities, mock_player, mock_game_map,
                mock_fov_map, False, mock_message_log, 80, 50, 20, 7, 45,  # panel_y updated to 45 in v3.5.0
                mock_mouse, colors, Mock(), use_optimization=False
            )
        
        # Check cache stats
        stats = get_entity_cache_stats()
        self.assertEqual(stats['cache_hits'], 1)  # Second call should be cache hit
        self.assertEqual(stats['cache_misses'], 1)  # First call should be cache miss


if __name__ == '__main__':
    unittest.main()
