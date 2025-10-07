"""Tests for visual effects with camera coordinate translation.

This module tests that visual effects (fireball, lightning, dragon fart, etc.)
render at the correct screen position when the camera is scrolled.
"""

import unittest
from unittest.mock import Mock, patch, call
from visual_effect_queue import QueuedEffect, EffectType
from rendering.camera import Camera
from config.ui_layout import UILayoutConfig, set_ui_layout


class TestVisualEffectsWithCamera(unittest.TestCase):
    """Test visual effects coordinate translation with camera scrolling."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Set up a known UI layout (other tests might change the global singleton)
        self.test_layout = UILayoutConfig(sidebar_width=20)
        set_ui_layout(self.test_layout)
        
        # Create a camera centered on (60, 40) with 80x45 viewport
        self.camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80
        )
        self.camera.center_on(60, 40)
        
        # Mock console
        self.mock_con = Mock()
    
    def tearDown(self):
        """Clean up after tests."""
        # Reset UI layout to default
        set_ui_layout(None)
    
    @patch('visual_effect_queue.libtcodpy.console_flush')
    @patch('visual_effect_queue.libtcodpy.console_put_char')
    @patch('visual_effect_queue.libtcodpy.console_set_default_foreground')
    @patch('visual_effect_queue.time.sleep')
    def test_fireball_coordinates_with_camera_scroll(self, mock_sleep, mock_fg, mock_put, mock_flush):
        """Test that fireball renders at correct screen position with camera scrolling.
        
        Bug: Visual effects appeared "far off" from intended location.
        Cause: Area effects weren't translating world coords through camera.
        Fix: All area effects now use camera.world_to_viewport() before drawing.
        """
        # Fireball at world position (65, 42) - near camera center
        # Should appear near center of viewport
        fireball_tiles = [(65, 42), (66, 42), (65, 43)]
        
        effect = QueuedEffect(
            EffectType.FIREBALL,
            x=65,
            y=42,
            entity=None,
            tiles=fireball_tiles,
            color=(255, 100, 0),
            char=ord('*')
        )
        
        # Play effect with camera
        effect.play(con=self.mock_con, camera=self.camera)
        
        # Verify coordinates were translated correctly
        # Camera center: (60, 40), viewport: 80x45
        # Camera viewport top-left: (60 - 40, 40 - 22) = (20, 18)
        # World (65, 42) → Viewport (65-20, 42-18) = (45, 24)
        # Viewport (45, 24) + viewport_offset (20, 0) = Screen (65, 24)
        
        # Check that put_char was called for each tile
        self.assertEqual(mock_put.call_count, 3, "Should draw 3 fireball tiles")
        
        # Verify first tile coordinates (65, 42) in world
        # → (45, 24) in viewport → (65, 24) on screen
        first_call_args = mock_put.call_args_list[0][0]
        screen_x, screen_y = first_call_args[1], first_call_args[2]
        
        # Expected screen position: viewport (45, 24) + offset (20, 0) = (65, 24)
        expected_screen_x = 45 + 20  # viewport_x + viewport_offset_x
        expected_screen_y = 24  # viewport_y + viewport_offset_y (0)
        
        self.assertEqual(screen_x, expected_screen_x,
                        f"Fireball X should be {expected_screen_x}, got {screen_x}")
        self.assertEqual(screen_y, expected_screen_y,
                        f"Fireball Y should be {expected_screen_y}, got {screen_y}")
    
    @patch('visual_effect_queue.libtcodpy.console_flush')
    @patch('visual_effect_queue.libtcodpy.console_put_char')
    @patch('visual_effect_queue.libtcodpy.console_set_default_foreground')
    @patch('visual_effect_queue.time.sleep')
    def test_lightning_coordinates_with_camera_scroll(self, mock_sleep, mock_fg, mock_put, mock_flush):
        """Test that lightning renders at correct screen position with camera scrolling."""
        # Lightning path from (55, 40) to (60, 40) in world coords
        lightning_path = [(55, 40), (56, 40), (57, 40), (58, 40), (59, 40), (60, 40)]
        
        effect = QueuedEffect(
            EffectType.LIGHTNING,
            x=55,
            y=40,
            entity=None,
            path=lightning_path,
            color=(255, 255, 100),
            char=ord('|')
        )
        
        # Play effect with camera
        effect.play(con=self.mock_con, camera=self.camera)
        
        # Verify all path tiles were drawn
        self.assertEqual(mock_put.call_count, len(lightning_path),
                        f"Should draw {len(lightning_path)} lightning tiles")
        
        # Verify first tile (55, 40) in world
        # Camera viewport top-left: (20, 18)
        # World (55, 40) → Viewport (35, 22) → Screen (55, 22)
        first_call_args = mock_put.call_args_list[0][0]
        screen_x, screen_y = first_call_args[1], first_call_args[2]
        
        expected_screen_x = 35 + 20  # viewport 35 + offset 20
        expected_screen_y = 22  # viewport 22 + offset 0
        
        self.assertEqual(screen_x, expected_screen_x,
                        f"Lightning start X should be {expected_screen_x}, got {screen_x}")
        self.assertEqual(screen_y, expected_screen_y,
                        f"Lightning start Y should be {expected_screen_y}, got {screen_y}")
    
    @patch('visual_effect_queue.libtcodpy.console_flush')
    @patch('visual_effect_queue.libtcodpy.console_put_char')
    @patch('visual_effect_queue.libtcodpy.console_set_default_foreground')
    @patch('visual_effect_queue.time.sleep')
    def test_dragon_fart_coordinates_with_camera_scroll(self, mock_sleep, mock_fg, mock_put, mock_flush):
        """Test that dragon fart renders at correct screen position with camera scrolling."""
        # Dragon fart cone tiles in world coords
        cone_tiles = [(62, 40), (63, 41), (63, 39), (64, 42), (64, 38)]
        
        effect = QueuedEffect(
            EffectType.DRAGON_FART,
            x=62,
            y=40,
            entity=None,
            tiles=cone_tiles,
            color=(100, 200, 50),
            char=ord('~')
        )
        
        # Play effect with camera
        effect.play(con=self.mock_con, camera=self.camera)
        
        # Verify all cone tiles were drawn
        self.assertEqual(mock_put.call_count, len(cone_tiles),
                        f"Should draw {len(cone_tiles)} dragon fart tiles")
        
        # Verify first tile (62, 40) in world
        # Camera viewport top-left: (20, 18)
        # World (62, 40) → Viewport (42, 22) → Screen (62, 22)
        first_call_args = mock_put.call_args_list[0][0]
        screen_x, screen_y = first_call_args[1], first_call_args[2]
        
        expected_screen_x = 42 + 20
        expected_screen_y = 22
        
        self.assertEqual(screen_x, expected_screen_x,
                        f"Dragon fart X should be {expected_screen_x}, got {screen_x}")
        self.assertEqual(screen_y, expected_screen_y,
                        f"Dragon fart Y should be {expected_screen_y}, got {screen_y}")
    
    @patch('visual_effect_queue.libtcodpy.console_flush')
    @patch('visual_effect_queue.libtcodpy.console_put_char')
    @patch('visual_effect_queue.libtcodpy.console_set_default_foreground')
    @patch('visual_effect_queue.time.sleep')
    def test_effects_cull_outside_viewport(self, mock_sleep, mock_fg, mock_put, mock_flush):
        """Test that effects outside viewport are culled and not drawn.
        
        This prevents rendering effects that are off-screen, improving performance
        and avoiding potential coordinate errors.
        """
        # Fireball at world position (10, 10) - way outside camera viewport
        # Camera is centered at (60, 40), viewport is 80x45
        # Viewport bounds: x=[20, 100], y=[18, 63]
        # Position (10, 10) is outside viewport
        fireball_tiles = [(10, 10), (11, 10), (10, 11)]
        
        effect = QueuedEffect(
            EffectType.FIREBALL,
            x=10,
            y=10,
            entity=None,
            tiles=fireball_tiles,
            color=(255, 100, 0),
            char=ord('*')
        )
        
        # Play effect with camera
        effect.play(con=self.mock_con, camera=self.camera)
        
        # Should NOT draw any tiles (all outside viewport)
        self.assertEqual(mock_put.call_count, 0,
                        "Should not draw tiles outside viewport")
    
    @patch('visual_effect_queue.libtcodpy.console_flush')
    @patch('visual_effect_queue.libtcodpy.console_put_char')
    @patch('visual_effect_queue.libtcodpy.console_set_default_foreground')
    @patch('visual_effect_queue.time.sleep')
    def test_effects_partially_visible(self, mock_sleep, mock_fg, mock_put, mock_flush):
        """Test that partially visible effects only draw visible tiles.
        
        If an effect has some tiles in viewport and some outside, only the
        visible tiles should be drawn.
        """
        # Fireball with tiles both inside and outside viewport
        # Camera center (60, 40), viewport x=[20, 100], y=[18, 63]
        # Tiles at (25, 20) - visible, (15, 10) - not visible, (30, 25) - visible
        fireball_tiles = [(25, 20), (15, 10), (30, 25)]
        
        effect = QueuedEffect(
            EffectType.FIREBALL,
            x=25,
            y=20,
            entity=None,
            tiles=fireball_tiles,
            color=(255, 100, 0),
            char=ord('*')
        )
        
        # Play effect with camera
        effect.play(con=self.mock_con, camera=self.camera)
        
        # Should only draw 2 tiles (the ones inside viewport)
        self.assertEqual(mock_put.call_count, 2,
                        "Should only draw tiles inside viewport")


if __name__ == '__main__':
    unittest.main()

