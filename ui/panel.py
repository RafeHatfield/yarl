"""Panel UI component implementation.

This module provides the Panel class, which is a container component
that can hold other UI components and manage their layout. Panels
provide visual grouping and can have borders, backgrounds, and titles.
"""

from typing import Optional, List

from rendering import Surface, Color, Colors
from rendering.surface import Rect
from .component import Component, ComponentState, ComponentStyle
from .layout import Layout, AbsoluteLayout


class PanelStyle(ComponentStyle):
    """Extended style configuration for panels."""
    
    def __init__(self, **kwargs):
        # Set panel-specific defaults
        defaults = {
            'fg_color': Colors.TEXT_DEFAULT,
            'bg_color': Color(32, 32, 32),
            'border_color': Colors.TEXT_DISABLED,
        }
        
        # Override with provided values
        for key, value in kwargs.items():
            if hasattr(ComponentStyle, key):
                defaults[key] = value
        
        super().__init__(**defaults)


class Panel(Component):
    """Container panel component.
    
    The Panel component serves as a container for other UI components,
    providing visual grouping, layout management, and optional decorative
    elements like borders and titles.
    
    Features:
    - Container for child components
    - Automatic layout management
    - Optional title display
    - Configurable borders and backgrounds
    - Scrolling support for overflow content
    - Clipping to prevent child components from drawing outside bounds
    """
    
    def __init__(self, x: int = 0, y: int = 0, width: int = 20, height: int = 10,
                 title: str = "", visible: bool = True, enabled: bool = True,
                 style: Optional[PanelStyle] = None,
                 layout: Optional[Layout] = None,
                 scrollable: bool = False):
        """Initialize the panel.
        
        Args:
            x (int): X position
            y (int): Y position
            width (int): Panel width
            height (int): Panel height
            title (str): Panel title (displayed at top)
            visible (bool): Whether panel is visible
            enabled (bool): Whether panel is enabled
            style (PanelStyle, optional): Panel styling
            layout (Layout, optional): Layout manager for children
            scrollable (bool): Whether panel content can scroll
        """
        super().__init__(x, y, width, height, visible, enabled, style or PanelStyle())
        
        self._title = title
        self.layout_manager = layout or AbsoluteLayout()
        self.scrollable = scrollable
        
        # Scrolling state
        self.scroll_x = 0
        self.scroll_y = 0
        self.max_scroll_x = 0
        self.max_scroll_y = 0
        
        # Internal layout tracking
        self._layout_dirty = True
    
    @property
    def title(self) -> str:
        """Get panel title."""
        return self._title
    
    @title.setter
    def title(self, value: str) -> None:
        """Set panel title."""
        if self._title != value:
            self._title = value
            self.mark_dirty()
    
    @property
    def content_area(self) -> Rect:
        """Get the content area available for child components.
        
        Returns:
            Rect: Content area rectangle (relative to panel)
        """
        # Account for borders and title
        border_size = 1 if self.style.border_color else 0
        title_height = 1 if self.title else 0
        
        content_x = border_size
        content_y = border_size + title_height
        content_width = max(0, self.width - 2 * border_size)
        content_height = max(0, self.height - 2 * border_size - title_height)
        
        return Rect(content_x, content_y, content_width, content_height)
    
    def set_layout_manager(self, layout: Layout) -> None:
        """Set the layout manager for this panel.
        
        Args:
            layout (Layout): New layout manager
        """
        self.layout_manager = layout
        self._layout_dirty = True
        self.mark_dirty()
    
    def add_child(self, child: Component) -> None:
        """Add a child component and trigger layout update.
        
        Args:
            child (Component): Child component to add
        """
        super().add_child(child)
        self._layout_dirty = True
    
    def remove_child(self, child: Component) -> None:
        """Remove a child component and trigger layout update.
        
        Args:
            child (Component): Child component to remove
        """
        super().remove_child(child)
        self._layout_dirty = True
    
    def update_layout(self) -> None:
        """Update the layout of child components."""
        if self.layout_manager and self._layout_dirty:
            self.layout_manager.layout(self)
            self._update_scroll_bounds()
            self._layout_dirty = False
    
    def _update_scroll_bounds(self) -> None:
        """Update scrolling bounds based on child positions."""
        if not self.scrollable or not self.children:
            self.max_scroll_x = 0
            self.max_scroll_y = 0
            return
        
        content_area = self.content_area
        
        # Find the bounds of all children
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for child in self.children:
            if child.visible:
                min_x = min(min_x, child.x)
                min_y = min(min_y, child.y)
                max_x = max(max_x, child.x + child.width)
                max_y = max(max_y, child.y + child.height)
        
        if min_x != float('inf'):  # We have visible children
            # Calculate required scroll range
            content_width = max_x - min_x
            content_height = max_y - min_y
            
            self.max_scroll_x = max(0, content_width - content_area.width)
            self.max_scroll_y = max(0, content_height - content_area.height)
        else:
            self.max_scroll_x = 0
            self.max_scroll_y = 0
    
    def scroll(self, dx: int, dy: int) -> None:
        """Scroll the panel content.
        
        Args:
            dx (int): Horizontal scroll delta
            dy (int): Vertical scroll delta
        """
        if not self.scrollable:
            return
        
        old_scroll_x = self.scroll_x
        old_scroll_y = self.scroll_y
        
        self.scroll_x = max(0, min(self.max_scroll_x, self.scroll_x + dx))
        self.scroll_y = max(0, min(self.max_scroll_y, self.scroll_y + dy))
        
        if self.scroll_x != old_scroll_x or self.scroll_y != old_scroll_y:
            self.mark_dirty()
    
    def scroll_to_child(self, child: Component) -> None:
        """Scroll to make a child component visible.
        
        Args:
            child (Component): Child component to scroll to
        """
        if not self.scrollable or child not in self.children:
            return
        
        content_area = self.content_area
        
        # Calculate required scroll to make child visible
        child_left = child.x - self.scroll_x
        child_right = child_left + child.width
        child_top = child.y - self.scroll_y
        child_bottom = child_top + child.height
        
        # Horizontal scrolling
        if child_right > content_area.width:
            self.scroll_x += child_right - content_area.width
        elif child_left < 0:
            self.scroll_x += child_left
        
        # Vertical scrolling
        if child_bottom > content_area.height:
            self.scroll_y += child_bottom - content_area.height
        elif child_top < 0:
            self.scroll_y += child_top
        
        # Clamp to valid range
        self.scroll_x = max(0, min(self.max_scroll_x, self.scroll_x))
        self.scroll_y = max(0, min(self.max_scroll_y, self.scroll_y))
        
        self.mark_dirty()
    
    def on_mouse_event(self, x: int, y: int, button: int, pressed: bool) -> bool:
        """Handle mouse events.
        
        Args:
            x (int): Mouse X coordinate (relative to panel)
            y (int): Mouse Y coordinate (relative to panel)
            button (int): Mouse button
            pressed (bool): True if pressed, False if released
            
        Returns:
            bool: True if event was handled
        """
        if not self.enabled:
            return False
        
        # Check if event is in content area
        content_area = self.content_area
        if not content_area.contains(x, y):
            return False
        
        # Adjust coordinates for scrolling
        child_x = x - content_area.x + self.scroll_x
        child_y = y - content_area.y + self.scroll_y
        
        # Try to handle in children
        child = self.get_child_at(child_x, child_y)
        if child:
            relative_x = child_x - child.x
            relative_y = child_y - child.y
            if child.handle_mouse_event(relative_x, relative_y, button, pressed):
                return True
        
        # Handle scrolling with mouse wheel (if supported)
        # This would typically be handled by a higher-level input system
        
        return True  # Panel consumes mouse events in its content area
    
    def on_key_event(self, key: str, pressed: bool) -> bool:
        """Handle keyboard events.
        
        Args:
            key (str): Key identifier
            pressed (bool): True if pressed, False if released
            
        Returns:
            bool: True if event was handled
        """
        if not self.enabled:
            return False
        
        # Try focused children first
        for child in self.children:
            if child.state == ComponentState.FOCUSED:
                if child.handle_key_event(key, pressed):
                    return True
        
        # Handle panel-specific keys (scrolling)
        if self.scrollable and pressed:
            if key.lower() in ('up', 'w'):
                self.scroll(0, -1)
                return True
            elif key.lower() in ('down', 's'):
                self.scroll(0, 1)
                return True
            elif key.lower() in ('left', 'a'):
                self.scroll(-1, 0)
                return True
            elif key.lower() in ('right', 'd'):
                self.scroll(1, 0)
                return True
        
        return False
    
    def render_self(self, surface: Surface) -> None:
        """Render the panel.
        
        Args:
            surface (Surface): Surface to render to
        """
        # Update layout if needed
        self.update_layout()
        
        abs_rect = self.absolute_rect
        fg_color, bg_color = self.get_style_colors()
        
        # Fill background
        surface.fill_rect(abs_rect, ' ', fg_color, bg_color)
        
        # Draw border if specified
        if self.style.border_color:
            surface.draw_border(abs_rect, self.style.border_color, bg_color)
        
        # Draw title if specified
        if self.title:
            title_y = abs_rect.y if not self.style.border_color else abs_rect.y + 1
            title_x = abs_rect.x + 2 if self.style.border_color else abs_rect.x
            
            # Truncate title if too long
            max_title_width = abs_rect.width - 4 if self.style.border_color else abs_rect.width
            display_title = self.title
            if len(display_title) > max_title_width:
                display_title = display_title[:max_title_width-3] + "..."
            
            surface.print_string(title_x, title_y, display_title, fg_color)
    
    def render(self, surface: Surface) -> None:
        """Render the panel and its children with proper clipping.
        
        Args:
            surface (Surface): Surface to render to
        """
        if not self.visible:
            return
        
        # Render panel background and decorations
        self.render_self(surface)
        
        # Set up clipping for content area
        content_area = self.content_area
        abs_content_area = Rect(
            self.absolute_rect.x + content_area.x,
            self.absolute_rect.y + content_area.y,
            content_area.width,
            content_area.height
        )
        
        old_clip = surface.get_clip_rect()
        
        # Intersect with existing clip rect if any
        if old_clip:
            clip_rect = Rect(
                max(abs_content_area.x, old_clip.x),
                max(abs_content_area.y, old_clip.y),
                min(abs_content_area.right, old_clip.right) - max(abs_content_area.x, old_clip.x),
                min(abs_content_area.bottom, old_clip.bottom) - max(abs_content_area.y, old_clip.y)
            )
            if clip_rect.width <= 0 or clip_rect.height <= 0:
                return  # Content area is completely clipped
        else:
            clip_rect = abs_content_area
        
        surface.set_clip_rect(clip_rect)
        
        try:
            # Render children with scroll offset
            for child in self.children:
                if child.visible:
                    # Temporarily adjust child position for scrolling
                    original_x, original_y = child.x, child.y
                    child.x -= self.scroll_x
                    child.y -= self.scroll_y
                    
                    try:
                        child.render(surface)
                    finally:
                        # Restore original position
                        child.x, child.y = original_x, original_y
            
            self.clear_dirty()
            
        finally:
            # Restore previous clipping
            surface.set_clip_rect(old_clip)
    
    def __repr__(self) -> str:
        """String representation of panel."""
        return (f"Panel(title='{self.title}', x={self.x}, y={self.y}, "
                f"w={self.width}, h={self.height}, children={len(self.children)})")
