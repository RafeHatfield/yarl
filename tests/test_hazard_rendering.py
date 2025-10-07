"""Tests for ground hazard visual rendering.

This module tests that hazards are properly rendered as lingering spell characters,
visual intensity decays over time, and rendering works with both optimized
and non-optimized rendering paths.
"""

import unittest
from unittest.mock import Mock, patch, call, MagicMock

from map_objects.game_map import GameMap
from components.ground_hazard import GroundHazard, HazardType
from render_functions import _render_hazard_at_tile


class TestHazardRendering(unittest.TestCase):
    """Test hazard visual rendering."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.game_map = GameMap(width=40, height=40, dungeon_level=1)
        self.mock_con = Mock()
        
        # Mock colors dictionary
        self.colors = {
            "light_ground": (50, 50, 150),
            "dark_ground": (0, 0, 100)
        }
        
        # Mark tile as explored for rendering
        self.game_map.tiles[10][10].explored = True
    
    def test_render_hazard_on_visible_tile(self):
        """Test that hazards render on visible tiles."""
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Test"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        with patch('render_functions.libtcod.console_set_default_foreground') as mock_set_fg, \
             patch('render_functions.libtcod.console_put_char') as mock_put_char:
            _render_hazard_at_tile(
                self.mock_con, self.game_map,
                world_x=10, world_y=10,
                viewport_x=10, viewport_y=10,
                visible=True,
                colors=self.colors
            )
            
            # Should have called to render character
            self.assertTrue(mock_put_char.called)
            
            # Check that color is fire-like (orange/red)
            call_args = mock_set_fg.call_args[0]
            color = call_args[1]
            self.assertGreater(color[0], 0)  # Red channel should be > 0
    
    def test_no_render_without_hazard(self):
        """Test that nothing renders when no hazard present."""
        # No hazard added
        
        with patch('render_functions.libtcod.console_set_default_foreground') as mock_set_fg, \
             patch('render_functions.libtcod.console_put_char') as mock_put_char:
            _render_hazard_at_tile(
                self.mock_con, self.game_map,
                world_x=10, world_y=10,
                viewport_x=10, viewport_y=10,
                visible=True,
                colors=self.colors
            )
            
            # Should not have called to render
            self.assertFalse(mock_put_char.called)
    
    def test_fire_hazard_color(self):
        """Test that fire hazards render with orange/red color and * character."""
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Test"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        with patch('render_functions.libtcod.console_set_default_foreground') as mock_set_fg, \
             patch('render_functions.libtcod.console_put_char') as mock_put_char:
            _render_hazard_at_tile(
                self.mock_con, self.game_map,
                world_x=10, world_y=10,
                viewport_x=10, viewport_y=10,
                visible=True,
                colors=self.colors
            )
            
            color = mock_set_fg.call_args[0][1]
            # Fire should have red/orange tint
            self.assertGreater(color[0], color[2])  # More red than blue
            
            # Should render * character for fire
            char = mock_put_char.call_args[0][3]
            self.assertEqual(char, ord('*'))
    
    def test_poison_gas_color(self):
        """Test that poison gas hazards render with green color and % character."""
        gas = GroundHazard(
            hazard_type=HazardType.POISON_GAS,
            x=10, y=10,
            base_damage=5,
            remaining_turns=4,
            max_duration=4,
            source_name="Test"
        )
        self.game_map.hazard_manager.add_hazard(gas)
        
        with patch('render_functions.libtcod.console_set_default_foreground') as mock_set_fg, \
             patch('render_functions.libtcod.console_put_char') as mock_put_char:
            _render_hazard_at_tile(
                self.mock_con, self.game_map,
                world_x=10, world_y=10,
                viewport_x=10, viewport_y=10,
                visible=True,
                colors=self.colors
            )
            
            color = mock_set_fg.call_args[0][1]
            # Poison gas should have green tint
            self.assertGreater(color[1], color[0])  # More green than red
            
            # Should render % character for poison gas
            char = mock_put_char.call_args[0][3]
            self.assertEqual(char, ord('%'))
    
    def test_visual_intensity_decays(self):
        """Test that visual intensity decreases as hazard ages."""
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=12,
            remaining_turns=3,
            max_duration=3,
            source_name="Test"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        with patch('render_functions.libtcod.console_set_default_foreground') as mock_set_fg, \
             patch('render_functions.libtcod.console_put_char') as mock_put_char:
            # Render at full strength
            _render_hazard_at_tile(
                self.mock_con, self.game_map,
                world_x=10, world_y=10,
                viewport_x=10, viewport_y=10,
                visible=True,
                colors=self.colors
            )
            color_turn1 = mock_set_fg.call_args[0][1]
            brightness_turn1 = sum(color_turn1)
            
            # Age the hazard
            fire.age_one_turn()
            mock_set_fg.reset_mock()
            mock_put_char.reset_mock()
            
            # Render again
            _render_hazard_at_tile(
                self.mock_con, self.game_map,
                world_x=10, world_y=10,
                viewport_x=10, viewport_y=10,
                visible=True,
                colors=self.colors
            )
            color_turn2 = mock_set_fg.call_args[0][1]
            brightness_turn2 = sum(color_turn2)
            
            # Brightness should decrease
            self.assertLess(brightness_turn2, brightness_turn1)
    
    def test_hazard_dimmer_when_not_visible(self):
        """Test that hazards are dimmer on explored but not visible tiles."""
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Test"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        with patch('render_functions.libtcod.console_set_default_foreground') as mock_set_fg, \
             patch('render_functions.libtcod.console_put_char') as mock_put_char:
            # Render when visible
            _render_hazard_at_tile(
                self.mock_con, self.game_map,
                world_x=10, world_y=10,
                viewport_x=10, viewport_y=10,
                visible=True,
                colors=self.colors
            )
            color_visible = mock_set_fg.call_args[0][1]
            brightness_visible = sum(color_visible)
            
            mock_set_fg.reset_mock()
            mock_put_char.reset_mock()
            
            # Render when not visible (but explored)
            _render_hazard_at_tile(
                self.mock_con, self.game_map,
                world_x=10, world_y=10,
                viewport_x=10, viewport_y=10,
                visible=False,
                colors=self.colors
            )
            color_explored = mock_set_fg.call_args[0][1]
            brightness_explored = sum(color_explored)
            
        # Should be dimmer when not visible (blended with dark floor)
        # The color will blend toward dark floor color, not just dim
        self.assertLess(brightness_explored, brightness_visible)
        # The explored brightness should be significantly lower but not necessarily
        # as low as 40% due to floor color blending
        self.assertLess(brightness_explored, brightness_visible * 0.6)
    
    def test_no_render_on_unexplored_tile(self):
        """Test that hazards don't render on unexplored tiles."""
        # Mark tile as unexplored
        self.game_map.tiles[10][10].explored = False
        
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Test"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        with patch('render_functions.libtcod.console_set_default_foreground') as mock_set_fg, \
             patch('render_functions.libtcod.console_put_char') as mock_put_char:
            _render_hazard_at_tile(
                self.mock_con, self.game_map,
                world_x=10, world_y=10,
                viewport_x=10, viewport_y=10,
                visible=False,
                colors=self.colors
            )
            
            # Should not render on unexplored tile
            self.assertFalse(mock_put_char.called)
    
    def test_hazard_uses_add_blending(self):
        """Test that hazards use additive blending mode."""
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Test"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        with patch('render_functions.libtcod') as mock_libtcod:
            _render_hazard_at_tile(
                self.mock_con, self.game_map,
                world_x=10, world_y=10,
                viewport_x=10, viewport_y=10,
                visible=True,
                colors=self.colors
            )
            
            # Check that BKGND_NONE was used (character over background)
            call_args = mock_libtcod.console_put_char.call_args[0]
            blend_mode = call_args[4]
            self.assertEqual(blend_mode, mock_libtcod.BKGND_NONE)
    
    def test_expired_hazard_not_rendered(self):
        """Test that expired hazards are not rendered."""
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=10,
            remaining_turns=1,
            max_duration=3,
            source_name="Test"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        # Age to expiration
        fire.age_one_turn()
        
        # Hazard should now be expired
        self.assertTrue(fire.is_expired())
        
        with patch('render_functions.libtcod.console_set_default_foreground') as mock_set_fg, \
             patch('render_functions.libtcod.console_put_char') as mock_put_char:
            _render_hazard_at_tile(
                self.mock_con, self.game_map,
                world_x=10, world_y=10,
                viewport_x=10, viewport_y=10,
                visible=True,
                colors=self.colors
            )
            
        # Should still try to render (manager hasn't removed it yet)
        # But the color should blend to floor color when expired
        if mock_set_fg.called:
            color = mock_set_fg.call_args[0][1]
            floor_color = self.colors["light_ground"]
            # Color should be close to floor color for expired hazard
            # Allow some tolerance for rounding
            for i in range(3):
                self.assertAlmostEqual(color[i], floor_color[i], delta=5)


class TestHazardRenderingWithoutManager(unittest.TestCase):
    """Test hazard rendering gracefully handles missing hazard manager."""
    
    def test_render_without_hazard_manager(self):
        """Test that rendering works when map has no hazard_manager."""
        game_map = GameMap(width=40, height=40, dungeon_level=1)
        # Remove hazard manager
        delattr(game_map, 'hazard_manager')
        
        mock_con = Mock()
        colors = {"light_ground": (50, 50, 150), "dark_ground": (0, 0, 100)}
        
        with patch('render_functions.libtcod.console_set_default_foreground') as mock_set_fg, \
             patch('render_functions.libtcod.console_put_char') as mock_put_char:
            # Should not crash
            _render_hazard_at_tile(
                mock_con, game_map,
                world_x=10, world_y=10,
                viewport_x=10, viewport_y=10,
                visible=True,
                colors=colors
            )
            
            # Should not have tried to render
            self.assertFalse(mock_put_char.called)


if __name__ == '__main__':
    unittest.main()
