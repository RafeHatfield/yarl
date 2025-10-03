"""Tests for UI layout configuration system.

Tests the split-screen layout configuration, coordinate translation,
and region detection for the sidebar UI system.
"""

import unittest
from config.ui_layout import UILayoutConfig, get_ui_layout, set_ui_layout


class TestUILayoutConfig(unittest.TestCase):
    """Tests for UILayoutConfig dataclass."""
    
    def setUp(self):
        """Set up test layout configuration."""
        self.layout = UILayoutConfig(
            sidebar_width=25,
            viewport_width=50,
            viewport_height=60,
            status_panel_height=7
        )
    
    def test_screen_dimensions(self):
        """Test computed screen dimensions."""
        self.assertEqual(self.layout.screen_width, 75)  # 25 + 50
        self.assertEqual(self.layout.screen_height, 67)  # 60 + 7
    
    def test_sidebar_position(self):
        """Test sidebar is positioned at origin."""
        self.assertEqual(self.layout.sidebar_position, (0, 0))
    
    def test_viewport_position(self):
        """Test viewport is positioned after sidebar."""
        self.assertEqual(self.layout.viewport_position, (25, 0))
    
    def test_status_panel_position(self):
        """Test status panel is below viewport."""
        self.assertEqual(self.layout.status_panel_position, (25, 60))
    
    def test_status_panel_width(self):
        """Test status panel width matches viewport."""
        self.assertEqual(self.layout.status_panel_width, 50)
    
    def test_sidebar_content_width(self):
        """Test sidebar content width accounts for padding."""
        self.assertEqual(self.layout.sidebar_content_width, 23)  # 25 - 2


class TestCoordinateTranslation(unittest.TestCase):
    """Tests for coordinate translation methods."""
    
    def setUp(self):
        """Set up test layout."""
        self.layout = UILayoutConfig(
            sidebar_width=25,
            viewport_width=50,
            viewport_height=60
        )
    
    def test_world_to_viewport_simple(self):
        """Test world to viewport conversion without camera offset."""
        result = self.layout.world_to_viewport(10, 20)
        self.assertEqual(result, (10, 20))
    
    def test_world_to_viewport_with_camera(self):
        """Test world to viewport conversion with camera offset."""
        # Camera at (5, 10), world at (15, 20)
        # Should appear at (10, 10) in viewport
        result = self.layout.world_to_viewport(15, 20, camera_x=5, camera_y=10)
        self.assertEqual(result, (10, 10))
    
    def test_world_to_viewport_outside_bounds(self):
        """Test conversion returns None for coords outside viewport."""
        # Outside viewport bounds
        result = self.layout.world_to_viewport(100, 100)
        self.assertIsNone(result)
        
        result = self.layout.world_to_viewport(-5, -5)
        self.assertIsNone(result)
    
    def test_screen_to_world_in_viewport(self):
        """Test screen to world conversion for viewport clicks."""
        # Click at screen (30, 10) -> viewport (5, 10) -> world (5, 10)
        result = self.layout.screen_to_world(30, 10)
        self.assertEqual(result, (5, 10))
    
    def test_screen_to_world_with_camera(self):
        """Test screen to world conversion with camera offset."""
        # Screen (30, 10) -> viewport (5, 10) -> world (15, 20) with camera at (10, 10)
        result = self.layout.screen_to_world(30, 10, camera_x=10, camera_y=10)
        self.assertEqual(result, (15, 20))
    
    def test_screen_to_world_in_sidebar(self):
        """Test screen to world returns None for sidebar clicks."""
        # Click in sidebar (x < 25)
        result = self.layout.screen_to_world(10, 10)
        self.assertIsNone(result)
    
    def test_screen_to_world_in_status_panel(self):
        """Test screen to world returns None for status panel clicks."""
        # Click in status panel (y >= viewport_height)
        result = self.layout.screen_to_world(30, 65)
        self.assertIsNone(result)


class TestRegionDetection(unittest.TestCase):
    """Tests for screen region detection methods."""
    
    def setUp(self):
        """Set up test layout."""
        self.layout = UILayoutConfig(
            sidebar_width=25,
            viewport_width=50,
            viewport_height=60,
            status_panel_height=7
        )
    
    def test_is_in_sidebar(self):
        """Test sidebar region detection."""
        # Inside sidebar
        self.assertTrue(self.layout.is_in_sidebar(10, 30))
        self.assertTrue(self.layout.is_in_sidebar(0, 0))
        self.assertTrue(self.layout.is_in_sidebar(24, 66))
        
        # Outside sidebar
        self.assertFalse(self.layout.is_in_sidebar(25, 30))
        self.assertFalse(self.layout.is_in_sidebar(50, 30))
    
    def test_is_in_viewport(self):
        """Test viewport region detection."""
        # Inside viewport
        self.assertTrue(self.layout.is_in_viewport(30, 10))
        self.assertTrue(self.layout.is_in_viewport(25, 0))
        self.assertTrue(self.layout.is_in_viewport(74, 59))
        
        # Outside viewport (sidebar)
        self.assertFalse(self.layout.is_in_viewport(10, 30))
        
        # Outside viewport (status panel)
        self.assertFalse(self.layout.is_in_viewport(30, 65))
    
    def test_is_in_status_panel(self):
        """Test status panel region detection."""
        # Inside status panel
        self.assertTrue(self.layout.is_in_status_panel(30, 60))
        self.assertTrue(self.layout.is_in_status_panel(25, 66))
        self.assertTrue(self.layout.is_in_status_panel(74, 65))
        
        # Outside status panel (viewport)
        self.assertFalse(self.layout.is_in_status_panel(30, 30))
        
        # Outside status panel (sidebar)
        self.assertFalse(self.layout.is_in_status_panel(10, 65))
    
    def test_regions_dont_overlap(self):
        """Test that regions are mutually exclusive."""
        # Test a grid of points
        for x in range(0, 75, 5):
            for y in range(0, 67, 5):
                regions_hit = sum([
                    self.layout.is_in_sidebar(x, y),
                    self.layout.is_in_viewport(x, y),
                    self.layout.is_in_status_panel(x, y)
                ])
                # Each point should be in exactly one region
                self.assertEqual(regions_hit, 1,
                    f"Point ({x}, {y}) is in {regions_hit} regions, expected 1")


class TestGlobalLayoutAccess(unittest.TestCase):
    """Tests for global layout instance management."""
    
    def test_get_ui_layout(self):
        """Test getting global layout instance."""
        layout = get_ui_layout()
        self.assertIsInstance(layout, UILayoutConfig)
    
    def test_get_ui_layout_singleton(self):
        """Test global layout is singleton."""
        layout1 = get_ui_layout()
        layout2 = get_ui_layout()
        self.assertIs(layout1, layout2)
    
    def test_set_ui_layout(self):
        """Test setting custom layout."""
        custom_layout = UILayoutConfig(sidebar_width=30)
        set_ui_layout(custom_layout)
        
        retrieved_layout = get_ui_layout()
        self.assertIs(retrieved_layout, custom_layout)
        self.assertEqual(retrieved_layout.sidebar_width, 30)


if __name__ == '__main__':
    unittest.main()

