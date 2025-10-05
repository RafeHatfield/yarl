"""Tests for targeting system with camera/viewport scrolling.

This test suite ensures that targeting spells (raise dead, fireball, etc.)
work correctly when the camera is offset from (0, 0), which happens during
viewport scrolling.
"""

import unittest
from unittest.mock import Mock, patch

from input_handlers import handle_mouse
from rendering.camera import Camera, CameraMode
from config.ui_layout import get_ui_layout


class TestTargetingWithCamera(unittest.TestCase):
    """Test targeting spell mouse clicks with camera offset."""
    
    def setUp(self):
        """Set up test scenario with camera."""
        self.ui_layout = get_ui_layout()
        
        # Create camera centered on player at (50, 50)
        self.camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=160,
            map_height=100,
            mode=CameraMode.CENTER
        )
        self.camera.center_on(50, 50)
        
        # Create mock mouse
        self.mouse = Mock()
        self.mouse.lbutton_pressed = False
        self.mouse.rbutton_pressed = False
    
    def test_targeting_click_with_camera_offset(self):
        """Test that targeting clicks translate correctly with camera offset.
        
        Scenario: Player at (50, 50), camera centered on player.
        Click on corpse at world (52, 50) which should appear at viewport (2, 0).
        Screen coordinates for this would be viewport (2, 0) + sidebar width (20) = (22, 0).
        """
        # Player is at (50, 50), camera is centered on them
        # So camera top-left is at (50 - 40, 50 - 22) = (10, 28)
        
        # We want to click on world position (52, 50)
        target_world_x, target_world_y = 52, 50
        
        # Convert world to viewport coords
        viewport_x = target_world_x - self.camera.x
        viewport_y = target_world_y - self.camera.y
        
        # Convert viewport to screen coords (add sidebar offset)
        screen_x = viewport_x + self.ui_layout.sidebar_width
        screen_y = viewport_y
        
        # Simulate mouse click at these screen coords
        self.mouse.cx = screen_x
        self.mouse.cy = screen_y
        self.mouse.lbutton_pressed = True
        
        # Handle mouse click with camera
        result = handle_mouse(self.mouse, self.camera)
        
        # Should return left_click with world coords (52, 50)
        self.assertIn("left_click", result)
        click_x, click_y = result["left_click"]
        self.assertEqual(click_x, target_world_x, 
                        f"Expected world X={target_world_x}, got {click_x}")
        self.assertEqual(click_y, target_world_y,
                        f"Expected world Y={target_world_y}, got {click_y}")
    
    def test_targeting_click_no_camera(self):
        """Test that targeting clicks work when camera is None (backwards compat)."""
        # Target at world (10, 10)
        target_world_x, target_world_y = 10, 10
        
        # Without camera, screen coords = world coords + sidebar offset
        screen_x = target_world_x + self.ui_layout.sidebar_width
        screen_y = target_world_y
        
        self.mouse.cx = screen_x
        self.mouse.cy = screen_y
        self.mouse.lbutton_pressed = True
        
        # Handle mouse click WITHOUT camera
        result = handle_mouse(self.mouse, camera=None)
        
        # Should return left_click with world coords (10, 10)
        self.assertIn("left_click", result)
        click_x, click_y = result["left_click"]
        self.assertEqual(click_x, target_world_x)
        self.assertEqual(click_y, target_world_y)
    
    def test_targeting_adjacent_corpse(self):
        """Test clicking on corpse adjacent to player with camera scrolled.
        
        This is the bug scenario: Player next to corpse, camera scrolled,
        raise dead says corpse is "too far away".
        """
        # Player at (50, 50), camera centered on them
        self.camera.center_on(50, 50)
        
        # Corpse is adjacent at (51, 50) - should be reachable!
        corpse_world_x, corpse_world_y = 51, 50
        
        # Convert to screen coords
        viewport_x = corpse_world_x - self.camera.x
        viewport_y = corpse_world_y - self.camera.y
        screen_x = viewport_x + self.ui_layout.sidebar_width
        screen_y = viewport_y
        
        self.mouse.cx = screen_x
        self.mouse.cy = screen_y
        self.mouse.lbutton_pressed = True
        
        result = handle_mouse(self.mouse, self.camera)
        
        # Should return correct world coords
        self.assertIn("left_click", result)
        click_x, click_y = result["left_click"]
        self.assertEqual(click_x, corpse_world_x,
                        "Adjacent corpse X coord should translate correctly")
        self.assertEqual(click_y, corpse_world_y,
                        "Adjacent corpse Y coord should translate correctly")
        
        # Verify distance is actually 1 tile (adjacent)
        player_x, player_y = 50, 50
        distance = abs(click_x - player_x) + abs(click_y - player_y)
        self.assertEqual(distance, 1, "Corpse should be 1 tile away (adjacent)")
    
    def test_targeting_far_edge_of_viewport(self):
        """Test clicking at the edge of viewport with camera scrolled."""
        # Player at (50, 50), camera centered
        self.camera.center_on(50, 50)
        
        # Click at far right edge of viewport
        # Viewport is 80 wide, so rightmost visible is viewport_x=79
        viewport_x = 79
        viewport_y = 22  # Middle of viewport vertically
        
        # World coords should be camera.x + viewport_x
        expected_world_x = self.camera.x + viewport_x
        expected_world_y = self.camera.y + viewport_y
        
        screen_x = viewport_x + self.ui_layout.sidebar_width
        screen_y = viewport_y
        
        self.mouse.cx = screen_x
        self.mouse.cy = screen_y
        self.mouse.lbutton_pressed = True
        
        result = handle_mouse(self.mouse, self.camera)
        
        self.assertIn("left_click", result)
        click_x, click_y = result["left_click"]
        self.assertEqual(click_x, expected_world_x)
        self.assertEqual(click_y, expected_world_y)
    
    def test_targeting_sidebar_click_ignored(self):
        """Test that clicks in sidebar don't register as targeting clicks."""
        # Click in sidebar (x < sidebar_width)
        self.mouse.cx = 10  # Inside sidebar
        self.mouse.cy = 20
        self.mouse.lbutton_pressed = True
        
        result = handle_mouse(self.mouse, self.camera)
        
        # Should return sidebar_click, not left_click
        self.assertIn("sidebar_click", result)
        self.assertNotIn("left_click", result)
    
    def test_targeting_status_panel_click_ignored(self):
        """Test that clicks in status panel are ignored."""
        # Click in status panel (below viewport)
        self.mouse.cx = self.ui_layout.sidebar_width + 10
        self.mouse.cy = self.ui_layout.viewport_height + 2  # In status panel
        self.mouse.lbutton_pressed = True
        
        result = handle_mouse(self.mouse, self.camera)
        
        # Should return empty dict (click ignored)
        self.assertEqual(result, {})
    
    def test_camera_movement_updates_targeting(self):
        """Test that targeting coords update correctly as camera moves."""
        # Start with camera at (10, 28)
        self.camera.center_on(50, 50)
        initial_camera_x = self.camera.x
        
        # Click at world (55, 50)
        target_world_x = 55
        viewport_x = target_world_x - self.camera.x
        screen_x = viewport_x + self.ui_layout.sidebar_width
        
        self.mouse.cx = screen_x
        self.mouse.cy = 22
        self.mouse.lbutton_pressed = True
        
        result1 = handle_mouse(self.mouse, self.camera)
        click1_x, _ = result1["left_click"]
        self.assertEqual(click1_x, target_world_x)
        
        # Now move camera (player moved)
        self.camera.center_on(60, 50)
        self.assertNotEqual(self.camera.x, initial_camera_x, "Camera should have moved")
        
        # Click at SAME screen position
        result2 = handle_mouse(self.mouse, self.camera)
        click2_x, _ = result2["left_click"]
        
        # World coords should be DIFFERENT (camera moved)
        self.assertNotEqual(click2_x, click1_x, 
                           "World coords should change when camera moves")
        self.assertEqual(click2_x, target_world_x + (60 - 50),
                        "World coords should shift by camera movement")


if __name__ == '__main__':
    unittest.main()

