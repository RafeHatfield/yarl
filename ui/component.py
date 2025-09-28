"""Base UI component system.

This module defines the fundamental Component class that serves as the
foundation for all UI elements. It provides common functionality like
positioning, sizing, visibility, event handling, and rendering.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional, List, Dict, Any, Callable, Tuple
from dataclasses import dataclass

from rendering import Surface, Color, Colors
from rendering.surface import Rect


class ComponentState(Enum):
    """Enumeration of possible component states."""
    NORMAL = auto()
    HOVER = auto()
    PRESSED = auto()
    FOCUSED = auto()
    DISABLED = auto()


@dataclass
class ComponentStyle:
    """Style configuration for UI components.
    
    This class defines the visual appearance of components including
    colors, borders, and other styling properties.
    """
    fg_color: Color = Colors.TEXT_DEFAULT
    bg_color: Color = Colors.BLACK
    border_color: Optional[Color] = None
    hover_fg_color: Optional[Color] = None
    hover_bg_color: Optional[Color] = None
    pressed_fg_color: Optional[Color] = None
    pressed_bg_color: Optional[Color] = None
    disabled_fg_color: Color = Colors.TEXT_DISABLED
    disabled_bg_color: Optional[Color] = None
    
    def get_colors_for_state(self, state: ComponentState) -> Tuple[Color, Color]:
        """Get foreground and background colors for a given state.
        
        Args:
            state (ComponentState): Component state
            
        Returns:
            Tuple[Color, Color]: (foreground, background) colors
        """
        if state == ComponentState.DISABLED:
            return (self.disabled_fg_color, 
                   self.disabled_bg_color or self.bg_color)
        elif state == ComponentState.PRESSED:
            return (self.pressed_fg_color or self.fg_color,
                   self.pressed_bg_color or self.bg_color)
        elif state == ComponentState.HOVER:
            return (self.hover_fg_color or self.fg_color,
                   self.hover_bg_color or self.bg_color)
        else:
            return (self.fg_color, self.bg_color)


class Component(ABC):
    """Abstract base class for all UI components.
    
    This class provides the fundamental functionality that all UI components
    need including positioning, sizing, visibility, event handling, and
    basic rendering infrastructure.
    
    Key Features:
    - Hierarchical component structure (parent/children)
    - Flexible positioning and sizing
    - State management (normal, hover, pressed, etc.)
    - Event handling system
    - Style and theming support
    - Clipping and bounds checking
    """
    
    def __init__(self, x: int = 0, y: int = 0, width: int = 10, height: int = 1,
                 visible: bool = True, enabled: bool = True,
                 style: Optional[ComponentStyle] = None):
        """Initialize the component.
        
        Args:
            x (int): X position relative to parent
            y (int): Y position relative to parent
            width (int): Component width
            height (int): Component height
            visible (bool): Whether component is visible
            enabled (bool): Whether component is enabled
            style (ComponentStyle, optional): Component styling
        """
        # Position and size
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
        # State
        self.visible = visible
        self.enabled = enabled
        self.state = ComponentState.NORMAL
        
        # Hierarchy
        self.parent: Optional['Component'] = None
        self.children: List['Component'] = []
        
        # Style
        self.style = style or ComponentStyle()
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # Internal state
        self._needs_redraw = True
        self._absolute_bounds: Optional[Rect] = None
    
    @property
    def rect(self) -> Rect:
        """Get component rectangle in local coordinates.
        
        Returns:
            Rect: Component bounds
        """
        return Rect(self.x, self.y, self.width, self.height)
    
    @property
    def absolute_rect(self) -> Rect:
        """Get component rectangle in absolute coordinates.
        
        Returns:
            Rect: Absolute component bounds
        """
        if self.parent:
            parent_rect = self.parent.absolute_rect
            return Rect(
                parent_rect.x + self.x,
                parent_rect.y + self.y,
                self.width,
                self.height
            )
        else:
            return self.rect
    
    @property
    def needs_redraw(self) -> bool:
        """Check if component needs to be redrawn.
        
        Returns:
            bool: True if redraw is needed
        """
        return self._needs_redraw
    
    def mark_dirty(self) -> None:
        """Mark component as needing redraw."""
        self._needs_redraw = True
        if self.parent:
            self.parent.mark_dirty()
    
    def clear_dirty(self) -> None:
        """Clear the dirty flag."""
        self._needs_redraw = False
    
    # Hierarchy management
    def add_child(self, child: 'Component') -> None:
        """Add a child component.
        
        Args:
            child (Component): Child component to add
        """
        if child.parent:
            child.parent.remove_child(child)
        
        child.parent = self
        self.children.append(child)
        self.mark_dirty()
    
    def remove_child(self, child: 'Component') -> None:
        """Remove a child component.
        
        Args:
            child (Component): Child component to remove
        """
        if child in self.children:
            child.parent = None
            self.children.remove(child)
            self.mark_dirty()
    
    def get_child_at(self, x: int, y: int) -> Optional['Component']:
        """Get the topmost child component at the given coordinates.
        
        Args:
            x (int): X coordinate (relative to this component)
            y (int): Y coordinate (relative to this component)
            
        Returns:
            Component: Child component at coordinates, or None
        """
        # Check children in reverse order (topmost first)
        for child in reversed(self.children):
            if (child.visible and child.rect.contains(x, y)):
                # Check if the child has a more specific component at this point
                child_x = x - child.x
                child_y = y - child.y
                nested_child = child.get_child_at(child_x, child_y)
                return nested_child or child
        
        return None
    
    # Event handling
    def add_event_handler(self, event_type: str, handler: Callable) -> None:
        """Add an event handler.
        
        Args:
            event_type (str): Type of event to handle
            handler (Callable): Event handler function
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def remove_event_handler(self, event_type: str, handler: Callable) -> None:
        """Remove an event handler.
        
        Args:
            event_type (str): Type of event
            handler (Callable): Event handler function to remove
        """
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
            except ValueError:
                pass  # Handler not found
    
    def emit_event(self, event_type: str, event_data: Any = None) -> bool:
        """Emit an event to all registered handlers.
        
        Args:
            event_type (str): Type of event to emit
            event_data (Any): Event data to pass to handlers
            
        Returns:
            bool: True if event was handled, False otherwise
        """
        handled = False
        
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    result = handler(self, event_data)
                    if result:
                        handled = True
                except Exception as e:
                    print(f"Error in event handler: {e}")
        
        return handled
    
    # State management
    def set_state(self, state: ComponentState) -> None:
        """Set component state.
        
        Args:
            state (ComponentState): New component state
        """
        if self.state != state:
            old_state = self.state
            self.state = state
            self.on_state_changed(old_state, state)
            self.mark_dirty()
    
    def on_state_changed(self, old_state: ComponentState, new_state: ComponentState) -> None:
        """Called when component state changes.
        
        Args:
            old_state (ComponentState): Previous state
            new_state (ComponentState): New state
        """
        # Override in subclasses for custom behavior
        pass
    
    # Input handling
    def handle_mouse_event(self, x: int, y: int, button: int, pressed: bool) -> bool:
        """Handle mouse events.
        
        Args:
            x (int): Mouse X coordinate (relative to this component)
            y (int): Mouse Y coordinate (relative to this component)
            button (int): Mouse button (0=left, 1=right, 2=middle)
            pressed (bool): True if button pressed, False if released
            
        Returns:
            bool: True if event was handled
        """
        if not self.visible or not self.enabled:
            return False
        
        # Check if event is within bounds
        if not self.rect.contains(x, y):
            return False
        
        # Try children first
        child = self.get_child_at(x, y)
        if child:
            child_x = x - child.x
            child_y = y - child.y
            if child.handle_mouse_event(child_x, child_y, button, pressed):
                return True
        
        # Handle in this component
        return self.on_mouse_event(x, y, button, pressed)
    
    def handle_key_event(self, key: str, pressed: bool) -> bool:
        """Handle keyboard events.
        
        Args:
            key (str): Key identifier
            pressed (bool): True if key pressed, False if released
            
        Returns:
            bool: True if event was handled
        """
        if not self.visible or not self.enabled:
            return False
        
        # Try focused child first
        for child in self.children:
            if child.state == ComponentState.FOCUSED:
                if child.handle_key_event(key, pressed):
                    return True
        
        # Handle in this component
        return self.on_key_event(key, pressed)
    
    @abstractmethod
    def on_mouse_event(self, x: int, y: int, button: int, pressed: bool) -> bool:
        """Handle mouse events in this component.
        
        Args:
            x (int): Mouse X coordinate (relative to this component)
            y (int): Mouse Y coordinate (relative to this component)
            button (int): Mouse button
            pressed (bool): True if pressed, False if released
            
        Returns:
            bool: True if event was handled
        """
        pass
    
    @abstractmethod
    def on_key_event(self, key: str, pressed: bool) -> bool:
        """Handle keyboard events in this component.
        
        Args:
            key (str): Key identifier
            pressed (bool): True if pressed, False if released
            
        Returns:
            bool: True if event was handled
        """
        pass
    
    # Rendering
    def render(self, surface: Surface) -> None:
        """Render the component and its children.
        
        Args:
            surface (Surface): Surface to render to
        """
        if not self.visible:
            return
        
        # Set clipping to component bounds
        abs_rect = self.absolute_rect
        old_clip = surface.get_clip_rect()
        
        # Intersect with existing clip rect if any
        if old_clip:
            clip_rect = Rect(
                max(abs_rect.x, old_clip.x),
                max(abs_rect.y, old_clip.y),
                min(abs_rect.right, old_clip.right) - max(abs_rect.x, old_clip.x),
                min(abs_rect.bottom, old_clip.bottom) - max(abs_rect.y, old_clip.y)
            )
            if clip_rect.width <= 0 or clip_rect.height <= 0:
                return  # Component is completely clipped
        else:
            clip_rect = abs_rect
        
        surface.set_clip_rect(clip_rect)
        
        try:
            # Render this component
            self.render_self(surface)
            
            # Render children
            for child in self.children:
                child.render(surface)
            
            self.clear_dirty()
            
        finally:
            # Restore previous clipping
            surface.set_clip_rect(old_clip)
    
    @abstractmethod
    def render_self(self, surface: Surface) -> None:
        """Render this component's content.
        
        Args:
            surface (Surface): Surface to render to
        """
        pass
    
    # Utility methods
    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is within component bounds.
        
        Args:
            x (int): X coordinate (absolute)
            y (int): Y coordinate (absolute)
            
        Returns:
            bool: True if point is within bounds
        """
        abs_rect = self.absolute_rect
        return abs_rect.contains(x, y)
    
    def get_style_colors(self) -> Tuple[Color, Color]:
        """Get current foreground and background colors based on state.
        
        Returns:
            Tuple[Color, Color]: (foreground, background) colors
        """
        return self.style.get_colors_for_state(self.state)
    
    def __repr__(self) -> str:
        """String representation of component."""
        return (f"{self.__class__.__name__}(x={self.x}, y={self.y}, "
                f"w={self.width}, h={self.height}, state={self.state.name})")
