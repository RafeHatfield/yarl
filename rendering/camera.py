"""Camera system for viewport scrolling and large map support.

This module provides a Camera class that manages the viewport position
in world space, enabling:
- Dynamic camera following (center on player, edge-follow, manual)
- Large maps bigger than the viewport
- Smooth coordinate translation between world and screen space
- Viewport bounds management

The camera system is designed to be flexible and support multiple
follow modes, which can be selected by the player or game state.
"""

from enum import Enum, auto
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class CameraMode(Enum):
    """Camera follow modes.
    
    Different modes control how the camera tracks the player:
    - CENTER: Camera always centers on player (classic roguelike)
    - EDGE_FOLLOW: Camera moves only when player nears viewport edge
    - MANUAL: Player controls camera independently (advanced)
    """
    CENTER = auto()       # Player always centered (Phase 2 default)
    EDGE_FOLLOW = auto()  # Player can move within dead zone (future feature)
    MANUAL = auto()       # Manual camera control (Phase 6)


class Camera:
    """Manages viewport position and coordinate translation.
    
    The camera tracks a position in world space and provides methods
    to translate between world coordinates and viewport (screen) coordinates.
    
    Key concepts:
    - World space: The full map (e.g., 200x200)
    - Viewport space: What's visible on screen (e.g., 80x45)
    - Camera position: Top-left corner of viewport in world space
    
    Example:
        camera = Camera(viewport_width=80, viewport_height=45, map_width=120, map_height=80)
        camera.center_on(player_x=60, player_y=40)
        screen_x, screen_y = camera.world_to_viewport(60, 40)
    """
    
    def __init__(
        self,
        viewport_width: int,
        viewport_height: int,
        map_width: int,
        map_height: int,
        mode: CameraMode = CameraMode.CENTER,
        dead_zone_width: int = 10,
        dead_zone_height: int = 10
    ):
        """Initialize the camera.
        
        Args:
            viewport_width: Width of the visible viewport in tiles
            viewport_height: Height of the visible viewport in tiles
            map_width: Width of the full map in tiles
            map_height: Height of the full map in tiles
            mode: Camera follow mode (default: CENTER)
            dead_zone_width: Width of dead zone for EDGE_FOLLOW mode (tiles)
            dead_zone_height: Height of dead zone for EDGE_FOLLOW mode (tiles)
        """
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.map_width = map_width
        self.map_height = map_height
        self.mode = mode
        self.dead_zone_width = dead_zone_width
        self.dead_zone_height = dead_zone_height
        
        # Camera position (top-left corner of viewport in world space)
        self.x = 0
        self.y = 0
        
        # Track target for smooth interpolation (Phase 4)
        self._target_x = 0
        self._target_y = 0
        
        logger.debug(
            f"Camera initialized: viewport={viewport_width}x{viewport_height}, "
            f"map={map_width}x{map_height}, mode={mode.name}"
        )
    
    def center_on(self, world_x: int, world_y: int) -> None:
        """Center the camera on a world position.
        
        This is the core method for CENTER mode - it positions the camera
        so the given world position appears in the center of the viewport.
        
        Args:
            world_x: X coordinate in world space
            world_y: Y coordinate in world space
        """
        # Calculate camera position to center on target
        target_camera_x = world_x - (self.viewport_width // 2)
        target_camera_y = world_y - (self.viewport_height // 2)
        
        # Apply bounds (don't show area outside map)
        self.x = self._clamp_camera_x(target_camera_x)
        self.y = self._clamp_camera_y(target_camera_y)
        
        logger.debug(f"Camera centered on ({world_x}, {world_y}) -> camera at ({self.x}, {self.y})")
    
    def update(self, target_x: int, target_y: int) -> bool:
        """Update camera position based on target and current mode.
        
        This method implements different follow modes:
        - CENTER: Always centers on target
        - EDGE_FOLLOW: Moves only when target nears edge
        - MANUAL: Doesn't move automatically
        
        Args:
            target_x: Target X coordinate in world space (usually player)
            target_y: Target Y coordinate in world space (usually player)
            
        Returns:
            bool: True if camera position changed, False otherwise
        """
        old_x, old_y = self.x, self.y
        
        if self.mode == CameraMode.CENTER:
            # Always center on target
            self.center_on(target_x, target_y)
            
        elif self.mode == CameraMode.EDGE_FOLLOW:
            # Move only when target nears viewport edge
            self._update_edge_follow(target_x, target_y)
            
        elif self.mode == CameraMode.MANUAL:
            # Don't move automatically
            pass
        
        # Return whether camera moved
        return (self.x != old_x) or (self.y != old_y)
    
    def _update_edge_follow(self, target_x: int, target_y: int) -> None:
        """Update camera for EDGE_FOLLOW mode.
        
        In this mode, the target (player) can move within a "dead zone"
        in the center of the viewport without causing camera movement.
        The camera only moves when the target gets close to the edge.
        
        Args:
            target_x: Target X coordinate in world space
            target_y: Target Y coordinate in world space
        """
        # Convert target to viewport space
        viewport_x = target_x - self.x
        viewport_y = target_y - self.y
        
        # Calculate dead zone bounds
        dead_zone_left = self.dead_zone_width
        dead_zone_right = self.viewport_width - self.dead_zone_width
        dead_zone_top = self.dead_zone_height
        dead_zone_bottom = self.viewport_height - self.dead_zone_height
        
        # Check if target is outside dead zone
        if viewport_x < dead_zone_left:
            # Too far left - move camera left
            self.x = self._clamp_camera_x(target_x - dead_zone_left)
        elif viewport_x > dead_zone_right:
            # Too far right - move camera right
            self.x = self._clamp_camera_x(target_x - dead_zone_right)
        
        if viewport_y < dead_zone_top:
            # Too far up - move camera up
            self.y = self._clamp_camera_y(target_y - dead_zone_top)
        elif viewport_y > dead_zone_bottom:
            # Too far down - move camera down
            self.y = self._clamp_camera_y(target_y - dead_zone_bottom)
    
    def _clamp_camera_x(self, camera_x: int) -> int:
        """Clamp camera X to valid bounds.
        
        Ensures the camera doesn't show area outside the map.
        
        Args:
            camera_x: Desired camera X position
            
        Returns:
            int: Clamped camera X position
        """
        # Don't go below 0
        camera_x = max(0, camera_x)
        
        # Don't show past map edge
        max_camera_x = max(0, self.map_width - self.viewport_width)
        camera_x = min(camera_x, max_camera_x)
        
        return camera_x
    
    def _clamp_camera_y(self, camera_y: int) -> int:
        """Clamp camera Y to valid bounds.
        
        Ensures the camera doesn't show area outside the map.
        
        Args:
            camera_y: Desired camera Y position
            
        Returns:
            int: Clamped camera Y position
        """
        # Don't go below 0
        camera_y = max(0, camera_y)
        
        # Don't show past map edge
        max_camera_y = max(0, self.map_height - self.viewport_height)
        camera_y = min(camera_y, max_camera_y)
        
        return camera_y
    
    def world_to_viewport(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """Convert world coordinates to viewport (screen) coordinates.
        
        This is the core translation method used by rendering.
        
        Example:
            # Player at world position (100, 50)
            # Camera at world position (60, 20)
            # Result: Player appears at viewport (40, 30)
        
        Args:
            world_x: X coordinate in world space
            world_y: Y coordinate in world space
            
        Returns:
            Tuple[int, int]: (viewport_x, viewport_y)
        """
        viewport_x = world_x - self.x
        viewport_y = world_y - self.y
        return (viewport_x, viewport_y)
    
    def viewport_to_world(self, viewport_x: int, viewport_y: int) -> Tuple[int, int]:
        """Convert viewport (screen) coordinates to world coordinates.
        
        This is used for mouse clicks and other input.
        
        Args:
            viewport_x: X coordinate in viewport space
            viewport_y: Y coordinate in viewport space
            
        Returns:
            Tuple[int, int]: (world_x, world_y)
        """
        world_x = viewport_x + self.x
        world_y = viewport_y + self.y
        return (world_x, world_y)
    
    def is_in_viewport(self, world_x: int, world_y: int) -> bool:
        """Check if a world position is visible in the current viewport.
        
        Useful for culling entities/effects that are off-screen.
        
        Args:
            world_x: X coordinate in world space
            world_y: Y coordinate in world space
            
        Returns:
            bool: True if position is visible, False otherwise
        """
        viewport_x, viewport_y = self.world_to_viewport(world_x, world_y)
        return (
            0 <= viewport_x < self.viewport_width and
            0 <= viewport_y < self.viewport_height
        )
    
    def get_viewport_bounds(self) -> Tuple[int, int, int, int]:
        """Get the current viewport bounds in world space.
        
        Returns:
            Tuple[int, int, int, int]: (min_x, min_y, max_x, max_y)
        """
        min_x = self.x
        min_y = self.y
        max_x = self.x + self.viewport_width - 1
        max_y = self.y + self.viewport_height - 1
        return (min_x, min_y, max_x, max_y)
    
    def set_mode(self, mode: CameraMode) -> None:
        """Change camera follow mode.
        
        Args:
            mode: New camera mode
        """
        if mode != self.mode:
            logger.info(f"Camera mode changed: {self.mode.name} -> {mode.name}")
            self.mode = mode
    
    def pan(self, dx: int, dy: int) -> None:
        """Manually pan the camera (for MANUAL mode or keyboard control).
        
        Args:
            dx: Change in X position
            dy: Change in Y position
        """
        self.x = self._clamp_camera_x(self.x + dx)
        self.y = self._clamp_camera_y(self.y + dy)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"Camera(pos=({self.x}, {self.y}), "
            f"viewport={self.viewport_width}x{self.viewport_height}, "
            f"map={self.map_width}x{self.map_height}, "
            f"mode={self.mode.name})"
        )

