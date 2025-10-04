"""Tests for the Camera system.

This test suite ensures the Camera class correctly:
- Tracks viewport position in world space
- Translates coordinates between world and viewport space
- Enforces viewport bounds
- Supports multiple follow modes
- Handles edge cases (small maps, large maps, boundaries)
"""

import pytest
from rendering.camera import Camera, CameraMode


class TestCameraInitialization:
    """Test Camera initialization."""
    
    def test_camera_initialization_default(self):
        """Test camera initializes with correct default values."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80
        )
        
        assert camera.viewport_width == 80
        assert camera.viewport_height == 45
        assert camera.map_width == 120
        assert camera.map_height == 80
        assert camera.mode == CameraMode.CENTER
        assert camera.x == 0
        assert camera.y == 0
    
    def test_camera_initialization_custom_mode(self):
        """Test camera can be initialized with custom mode."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80,
            mode=CameraMode.EDGE_FOLLOW
        )
        
        assert camera.mode == CameraMode.EDGE_FOLLOW
    
    def test_camera_initialization_custom_dead_zone(self):
        """Test camera can be initialized with custom dead zone."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80,
            dead_zone_width=15,
            dead_zone_height=10
        )
        
        assert camera.dead_zone_width == 15
        assert camera.dead_zone_height == 10


class TestCameraCenterOn:
    """Test camera centering functionality."""
    
    def test_center_on_middle_of_map(self):
        """Test camera centers on position in middle of map."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80
        )
        
        # Center on (60, 40) - middle of 120x80 map
        camera.center_on(60, 40)
        
        # Camera should be at (20, 18) to center viewport
        # X: 60 - (80//2) = 60 - 40 = 20
        # Y: 40 - (45//2) = 40 - 22 = 18
        assert camera.x == 20
        assert camera.y == 18
    
    def test_center_on_respects_left_boundary(self):
        """Test camera doesn't show area left of map."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80
        )
        
        # Try to center on (10, 40) - near left edge
        camera.center_on(10, 40)
        
        # Camera X should be clamped to 0 (can't go negative)
        assert camera.x == 0
        assert camera.y == 18
    
    def test_center_on_respects_right_boundary(self):
        """Test camera doesn't show area right of map."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80
        )
        
        # Try to center on (110, 40) - near right edge
        camera.center_on(110, 40)
        
        # Camera X should be clamped to max (120 - 80 = 40)
        assert camera.x == 40
        assert camera.y == 18
    
    def test_center_on_respects_top_boundary(self):
        """Test camera doesn't show area above map."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80
        )
        
        # Try to center on (60, 10) - near top edge
        camera.center_on(60, 10)
        
        # Camera Y should be clamped to 0
        assert camera.x == 20
        assert camera.y == 0
    
    def test_center_on_respects_bottom_boundary(self):
        """Test camera doesn't show area below map."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80
        )
        
        # Try to center on (60, 70) - near bottom edge
        camera.center_on(60, 70)
        
        # Camera Y should be clamped to max (80 - 45 = 35)
        assert camera.x == 20
        assert camera.y == 35
    
    def test_center_on_small_map(self):
        """Test camera behavior when map is smaller than viewport."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=60,
            map_height=30
        )
        
        # Center on (30, 15) - middle of small map
        camera.center_on(30, 15)
        
        # Camera should be clamped to (0, 0) since map is smaller
        assert camera.x == 0
        assert camera.y == 0


class TestCameraCoordinateTranslation:
    """Test coordinate translation between world and viewport space."""
    
    def test_world_to_viewport_at_origin(self):
        """Test world to viewport translation when camera at (0, 0)."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80
        )
        
        # Camera at origin
        assert camera.x == 0
        assert camera.y == 0
        
        # World (10, 20) should be viewport (10, 20)
        vp_x, vp_y = camera.world_to_viewport(10, 20)
        assert vp_x == 10
        assert vp_y == 20
    
    def test_world_to_viewport_after_movement(self):
        """Test world to viewport translation after camera moves."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80
        )
        
        # Move camera to (20, 15)
        camera.center_on(60, 37)
        assert camera.x == 20
        assert camera.y == 15
        
        # World (60, 37) should be viewport (40, 22) - centered
        vp_x, vp_y = camera.world_to_viewport(60, 37)
        assert vp_x == 40
        assert vp_y == 22
        
        # World (20, 15) should be viewport (0, 0) - top-left
        vp_x, vp_y = camera.world_to_viewport(20, 15)
        assert vp_x == 0
        assert vp_y == 0
    
    def test_viewport_to_world_at_origin(self):
        """Test viewport to world translation when camera at (0, 0)."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80
        )
        
        # Viewport (10, 20) should be world (10, 20)
        world_x, world_y = camera.viewport_to_world(10, 20)
        assert world_x == 10
        assert world_y == 20
    
    def test_viewport_to_world_after_movement(self):
        """Test viewport to world translation after camera moves."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80
        )
        
        # Move camera to (20, 15)
        camera.center_on(60, 37)
        
        # Viewport (40, 22) should be world (60, 37) - center
        world_x, world_y = camera.viewport_to_world(40, 22)
        assert world_x == 60
        assert world_y == 37
        
        # Viewport (0, 0) should be world (20, 15) - top-left
        world_x, world_y = camera.viewport_to_world(0, 0)
        assert world_x == 20
        assert world_y == 15
    
    def test_coordinate_round_trip(self):
        """Test that translating world->viewport->world returns original."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80
        )
        
        camera.center_on(60, 40)
        
        # Test several positions
        test_positions = [(50, 30), (60, 40), (70, 50), (25, 20), (90, 65)]
        
        for world_x, world_y in test_positions:
            vp_x, vp_y = camera.world_to_viewport(world_x, world_y)
            back_x, back_y = camera.viewport_to_world(vp_x, vp_y)
            assert back_x == world_x
            assert back_y == world_y


class TestCameraVisibilityCheck:
    """Test is_in_viewport functionality."""
    
    def test_position_in_viewport(self):
        """Test position within viewport returns True."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80
        )
        
        camera.center_on(60, 40)
        
        # Position at camera center should be visible
        assert camera.is_in_viewport(60, 40) is True
        
        # Position just inside edges should be visible
        assert camera.is_in_viewport(camera.x + 1, camera.y + 1) is True
        assert camera.is_in_viewport(camera.x + 78, camera.y + 43) is True
    
    def test_position_outside_viewport(self):
        """Test position outside viewport returns False."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80
        )
        
        camera.center_on(60, 40)
        
        # Positions outside viewport should not be visible
        assert camera.is_in_viewport(10, 10) is False
        assert camera.is_in_viewport(110, 70) is False
        assert camera.is_in_viewport(camera.x - 1, camera.y) is False
        assert camera.is_in_viewport(camera.x, camera.y - 1) is False
    
    def test_position_at_viewport_edges(self):
        """Test positions at exact viewport edges."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80
        )
        
        camera.center_on(60, 40)
        
        # Top-left corner should be visible
        assert camera.is_in_viewport(camera.x, camera.y) is True
        
        # Bottom-right corner (inclusive) should be visible
        assert camera.is_in_viewport(
            camera.x + camera.viewport_width - 1,
            camera.y + camera.viewport_height - 1
        ) is True
        
        # Just outside should not be visible
        assert camera.is_in_viewport(
            camera.x + camera.viewport_width,
            camera.y + camera.viewport_height
        ) is False


class TestCameraUpdateModes:
    """Test camera update with different follow modes."""
    
    def test_update_center_mode(self):
        """Test update in CENTER mode always centers on target."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80,
            mode=CameraMode.CENTER
        )
        
        # Update with target at (60, 40)
        changed = camera.update(60, 40)
        
        assert changed is True
        assert camera.x == 20
        assert camera.y == 18
        
        # Update again with same target - no change
        changed = camera.update(60, 40)
        assert changed is False
        
        # Update with new target
        changed = camera.update(80, 50)
        assert changed is True
    
    def test_update_edge_follow_mode_within_dead_zone(self):
        """Test EDGE_FOLLOW mode doesn't move when target in dead zone."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80,
            mode=CameraMode.EDGE_FOLLOW,
            dead_zone_width=10,
            dead_zone_height=10
        )
        
        # Center camera on (60, 40)
        camera.center_on(60, 40)
        initial_x, initial_y = camera.x, camera.y
        
        # Move target slightly (still in dead zone)
        # Dead zone is x:[30, 70], y:[27, 57] in viewport space
        # = world [50, 90], [44, 74]
        changed = camera.update(65, 45)
        
        # Camera shouldn't move
        assert changed is False
        assert camera.x == initial_x
        assert camera.y == initial_y
    
    def test_update_edge_follow_mode_outside_dead_zone(self):
        """Test EDGE_FOLLOW mode moves when target exits dead zone."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80,
            mode=CameraMode.EDGE_FOLLOW,
            dead_zone_width=10,
            dead_zone_height=10
        )
        
        # Center camera on (60, 40)
        camera.center_on(60, 40)
        initial_x, initial_y = camera.x, camera.y
        
        # Move target far right (outside dead zone)
        changed = camera.update(100, 40)
        
        # Camera should move
        assert changed is True
        assert camera.x > initial_x
    
    def test_update_manual_mode(self):
        """Test MANUAL mode doesn't auto-move camera."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80,
            mode=CameraMode.MANUAL
        )
        
        initial_x, initial_y = camera.x, camera.y
        
        # Update with any target - camera shouldn't move
        changed = camera.update(60, 40)
        
        assert changed is False
        assert camera.x == initial_x
        assert camera.y == initial_y


class TestCameraPan:
    """Test manual camera panning."""
    
    def test_pan_within_bounds(self):
        """Test panning camera within map bounds."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80
        )
        
        # Pan right and down
        camera.pan(10, 5)
        assert camera.x == 10
        assert camera.y == 5
        
        # Pan more
        camera.pan(5, 3)
        assert camera.x == 15
        assert camera.y == 8
    
    def test_pan_respects_boundaries(self):
        """Test panning respects map boundaries."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80
        )
        
        # Try to pan left (should clamp to 0)
        camera.pan(-10, 0)
        assert camera.x == 0
        
        # Try to pan too far right (should clamp to max)
        camera.pan(1000, 0)
        assert camera.x == 40  # max_x = 120 - 80 = 40
        
        # Try to pan too far down (should clamp to max)
        camera.pan(0, 1000)
        assert camera.y == 35  # max_y = 80 - 45 = 35


class TestCameraModeSwitching:
    """Test switching between camera modes."""
    
    def test_set_mode(self):
        """Test changing camera mode."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80,
            mode=CameraMode.CENTER
        )
        
        assert camera.mode == CameraMode.CENTER
        
        camera.set_mode(CameraMode.EDGE_FOLLOW)
        assert camera.mode == CameraMode.EDGE_FOLLOW
        
        camera.set_mode(CameraMode.MANUAL)
        assert camera.mode == CameraMode.MANUAL


class TestCameraViewportBounds:
    """Test get_viewport_bounds functionality."""
    
    def test_viewport_bounds_at_origin(self):
        """Test viewport bounds when camera at origin."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80
        )
        
        min_x, min_y, max_x, max_y = camera.get_viewport_bounds()
        
        assert min_x == 0
        assert min_y == 0
        assert max_x == 79  # 0 + 80 - 1
        assert max_y == 44  # 0 + 45 - 1
    
    def test_viewport_bounds_after_movement(self):
        """Test viewport bounds after camera moves."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=120,
            map_height=80
        )
        
        camera.center_on(60, 40)
        
        min_x, min_y, max_x, max_y = camera.get_viewport_bounds()
        
        assert min_x == camera.x
        assert min_y == camera.y
        assert max_x == camera.x + 79
        assert max_y == camera.y + 44


class TestCameraEdgeCases:
    """Test camera behavior in edge cases."""
    
    def test_map_smaller_than_viewport(self):
        """Test camera with map smaller than viewport."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=50,
            map_height=30
        )
        
        # Try to move camera - should stay at (0, 0)
        camera.center_on(25, 15)
        assert camera.x == 0
        assert camera.y == 0
        
        # Try to pan - should stay at (0, 0)
        camera.pan(10, 10)
        assert camera.x == 0
        assert camera.y == 0
    
    def test_map_same_size_as_viewport(self):
        """Test camera with map exactly same size as viewport."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=80,
            map_height=45
        )
        
        # Camera should always be at (0, 0)
        camera.center_on(40, 22)
        assert camera.x == 0
        assert camera.y == 0
        
        camera.pan(10, 10)
        assert camera.x == 0
        assert camera.y == 0
    
    def test_very_large_map(self):
        """Test camera with very large map."""
        camera = Camera(
            viewport_width=80,
            viewport_height=45,
            map_width=500,
            map_height=300
        )
        
        # Camera should be able to move freely in large map
        camera.center_on(250, 150)
        assert camera.x == 210  # 250 - 40
        assert camera.y == 128  # 150 - 22 (45//2)
        
        # Max camera position
        max_x = 500 - 80  # 420
        max_y = 300 - 45  # 255
        
        camera.center_on(490, 290)
        assert camera.x == max_x
        assert camera.y == max_y

