"""UI Layout Configuration System.

This module defines the configurable layout system for the game UI,
supporting a split-screen design with sidebar, viewport, and status panel.

Architecture:
- Sidebar (left): Full height, contains menu/stats/equipment
- Viewport (right): Main game view, scrollable in future phases
- Status Panel (below viewport): HP bar, messages, dungeon info

All dimensions are configurable to support iteration and future features.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class UILayoutConfig:
    """Configuration for UI layout dimensions and positioning.
    
    This class defines all the dimensions and computed properties needed
    for the split-screen layout. All values are configurable to allow
    easy iteration and adjustment.
    
    Attributes:
        sidebar_width: Width of left sidebar in tiles
        viewport_width: Width of map viewport in tiles
        viewport_height: Height of map viewport in tiles
        status_panel_height: Height of status panel below viewport
        message_log_height: Lines allocated for message log
        sidebar_padding: Internal padding for sidebar content
    """
    
    # Sidebar dimensions
    sidebar_width: int = 20
    sidebar_enabled: bool = True
    sidebar_padding: int = 1
    
    # Viewport dimensions (sized to fit current maps: 80x43)
    # Slightly larger for comfortable view
    viewport_width: int = 80
    viewport_height: int = 45
    
    # Status panel dimensions
    status_panel_height: int = 7
    message_log_height: int = 4
    
    # Computed properties for console management
    
    @property
    def screen_width(self) -> int:
        """Total screen width in tiles.
        
        Returns:
            int: Sum of sidebar and viewport widths
        """
        return self.sidebar_width + self.viewport_width
    
    @property
    def screen_height(self) -> int:
        """Total screen height in tiles.
        
        Returns:
            int: Viewport height + status panel height
                 (sidebar spans full height separately)
        """
        return self.viewport_height + self.status_panel_height
    
    @property
    def sidebar_position(self) -> Tuple[int, int]:
        """Screen position for sidebar console (top-left corner).
        
        Returns:
            Tuple[int, int]: (x, y) coordinates for blitting sidebar
        """
        return (0, 0)
    
    @property
    def viewport_position(self) -> Tuple[int, int]:
        """Screen position for viewport console (top-left corner).
        
        Returns:
            Tuple[int, int]: (x, y) coordinates for blitting viewport
        """
        return (self.sidebar_width, 0)
    
    @property
    def status_panel_position(self) -> Tuple[int, int]:
        """Screen position for status panel console (top-left corner).
        
        Returns:
            Tuple[int, int]: (x, y) coordinates for blitting status panel
        """
        return (self.sidebar_width, self.viewport_height)
    
    @property
    def status_panel_width(self) -> int:
        """Width of status panel in tiles.
        
        Status panel spans only the viewport width, not full screen.
        
        Returns:
            int: Width matching viewport
        """
        return self.viewport_width
    
    @property
    def sidebar_content_width(self) -> int:
        """Usable width for sidebar content (accounting for padding).
        
        Returns:
            int: Sidebar width minus padding on both sides
        """
        return self.sidebar_width - (self.sidebar_padding * 2)
    
    def world_to_viewport(self, world_x: int, world_y: int, 
                         camera_x: int = 0, camera_y: int = 0) -> Tuple[int, int]:
        """Convert world coordinates to viewport coordinates.
        
        For Phase 1A/1B, camera is always at (0, 0) since we render
        the entire map 1:1. This will be enhanced in Phase 2 with
        proper camera support.
        
        Args:
            world_x: X coordinate in world space
            world_y: Y coordinate in world space
            camera_x: Camera X offset (default 0 for Phase 1)
            camera_y: Camera Y offset (default 0 for Phase 1)
            
        Returns:
            Tuple[int, int]: (x, y) in viewport space, or None if outside viewport
        """
        viewport_x = world_x - camera_x
        viewport_y = world_y - camera_y
        
        # Check if within viewport bounds
        if (0 <= viewport_x < self.viewport_width and 
            0 <= viewport_y < self.viewport_height):
            return (viewport_x, viewport_y)
        return None
    
    def screen_to_world(self, screen_x: int, screen_y: int,
                       camera_x: int = 0, camera_y: int = 0) -> Tuple[int, int]:
        """Convert screen coordinates to world coordinates.
        
        Used for mouse input translation. Checks if click is in viewport
        region and converts to world space.
        
        Args:
            screen_x: X coordinate on screen
            screen_y: Y coordinate on screen
            camera_x: Camera X offset (default 0 for Phase 1)
            camera_y: Camera Y offset (default 0 for Phase 1)
            
        Returns:
            Tuple[int, int]: (x, y) in world space, or None if not in viewport
        """
        # Check if click is in viewport region
        viewport_pos = self.viewport_position
        
        if (screen_x < viewport_pos[0] or 
            screen_x >= viewport_pos[0] + self.viewport_width or
            screen_y < viewport_pos[1] or
            screen_y >= viewport_pos[1] + self.viewport_height):
            return None
        
        # Convert to viewport-relative coords
        viewport_x = screen_x - viewport_pos[0]
        viewport_y = screen_y - viewport_pos[1]
        
        # Convert to world coords (accounting for camera in Phase 2)
        world_x = viewport_x + camera_x
        world_y = viewport_y + camera_y
        
        return (world_x, world_y)
    
    def is_in_sidebar(self, screen_x: int, screen_y: int) -> bool:
        """Check if screen coordinates are within sidebar region.
        
        Args:
            screen_x: X coordinate on screen
            screen_y: Y coordinate on screen
            
        Returns:
            bool: True if coordinates are in sidebar, False otherwise
        """
        return (0 <= screen_x < self.sidebar_width and
                0 <= screen_y < self.screen_height)
    
    def is_in_viewport(self, screen_x: int, screen_y: int) -> bool:
        """Check if screen coordinates are within viewport region.
        
        Args:
            screen_x: X coordinate on screen
            screen_y: Y coordinate on screen
            
        Returns:
            bool: True if coordinates are in viewport, False otherwise
        """
        viewport_pos = self.viewport_position
        return (viewport_pos[0] <= screen_x < viewport_pos[0] + self.viewport_width and
                viewport_pos[1] <= screen_y < viewport_pos[1] + self.viewport_height)
    
    def is_in_status_panel(self, screen_x: int, screen_y: int) -> bool:
        """Check if screen coordinates are within status panel region.
        
        Args:
            screen_x: X coordinate on screen
            screen_y: Y coordinate on screen
            
        Returns:
            bool: True if coordinates are in status panel, False otherwise
        """
        status_pos = self.status_panel_position
        return (status_pos[0] <= screen_x < status_pos[0] + self.status_panel_width and
                status_pos[1] <= screen_y < status_pos[1] + self.status_panel_height)


# Global layout instance
_ui_layout = None


def get_ui_layout() -> UILayoutConfig:
    """Get the global UI layout configuration.
    
    Returns:
        UILayoutConfig: The global layout instance
    """
    global _ui_layout
    if _ui_layout is None:
        _ui_layout = UILayoutConfig()
    return _ui_layout


def set_ui_layout(layout: UILayoutConfig) -> None:
    """Set a custom UI layout configuration.
    
    Args:
        layout: New layout configuration to use
    """
    global _ui_layout
    _ui_layout = layout

