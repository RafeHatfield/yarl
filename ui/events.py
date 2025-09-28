"""UI event system for component interaction.

This module defines the event system used by UI components to communicate
with each other and with the application. It provides a clean, type-safe
way to handle user interactions and component state changes.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional, Dict


class UIEventType(Enum):
    """Enumeration of UI event types."""
    
    # Mouse events
    MOUSE_ENTER = auto()
    MOUSE_LEAVE = auto()
    MOUSE_MOVE = auto()
    MOUSE_DOWN = auto()
    MOUSE_UP = auto()
    MOUSE_CLICK = auto()
    MOUSE_DOUBLE_CLICK = auto()
    
    # Keyboard events
    KEY_DOWN = auto()
    KEY_UP = auto()
    KEY_PRESS = auto()  # Key down + up combination
    
    # Focus events
    FOCUS_GAINED = auto()
    FOCUS_LOST = auto()
    
    # Component events
    COMPONENT_ADDED = auto()
    COMPONENT_REMOVED = auto()
    COMPONENT_MOVED = auto()
    COMPONENT_RESIZED = auto()
    COMPONENT_STATE_CHANGED = auto()
    
    # Button events
    BUTTON_CLICKED = auto()
    BUTTON_PRESSED = auto()
    BUTTON_RELEASED = auto()
    
    # Menu events
    MENU_ITEM_SELECTED = auto()
    MENU_OPENED = auto()
    MENU_CLOSED = auto()
    
    # Dialog events
    DIALOG_OPENED = auto()
    DIALOG_CLOSED = auto()
    DIALOG_CONFIRMED = auto()
    DIALOG_CANCELLED = auto()
    
    # Text events
    TEXT_CHANGED = auto()
    TEXT_SUBMITTED = auto()
    
    # Layout events
    LAYOUT_CHANGED = auto()
    
    # Custom events (for application-specific events)
    CUSTOM = auto()


@dataclass
class UIEvent:
    """UI event data structure.
    
    This class encapsulates all information about a UI event including
    its type, source component, and any associated data.
    """
    
    event_type: UIEventType
    source: Optional[Any] = None  # Source component
    target: Optional[Any] = None  # Target component (if different from source)
    data: Optional[Dict[str, Any]] = None
    
    # Mouse-specific data
    mouse_x: Optional[int] = None
    mouse_y: Optional[int] = None
    mouse_button: Optional[int] = None
    
    # Keyboard-specific data
    key: Optional[str] = None
    key_code: Optional[int] = None
    modifiers: Optional[Dict[str, bool]] = None  # shift, ctrl, alt, etc.
    
    # Event flow control
    handled: bool = False
    cancelled: bool = False
    
    def __post_init__(self):
        """Initialize default values after creation."""
        if self.data is None:
            self.data = {}
        if self.modifiers is None:
            self.modifiers = {}
    
    def mark_handled(self) -> None:
        """Mark this event as handled."""
        self.handled = True
    
    def cancel(self) -> None:
        """Cancel this event (prevents further processing)."""
        self.cancelled = True
        self.handled = True
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get event data by key.
        
        Args:
            key (str): Data key
            default (Any): Default value if key not found
            
        Returns:
            Any: Event data value
        """
        return self.data.get(key, default) if self.data else default
    
    def set_data(self, key: str, value: Any) -> None:
        """Set event data.
        
        Args:
            key (str): Data key
            value (Any): Data value
        """
        if self.data is None:
            self.data = {}
        self.data[key] = value
    
    def is_mouse_event(self) -> bool:
        """Check if this is a mouse event.
        
        Returns:
            bool: True if mouse event
        """
        return self.event_type in {
            UIEventType.MOUSE_ENTER,
            UIEventType.MOUSE_LEAVE,
            UIEventType.MOUSE_MOVE,
            UIEventType.MOUSE_DOWN,
            UIEventType.MOUSE_UP,
            UIEventType.MOUSE_CLICK,
            UIEventType.MOUSE_DOUBLE_CLICK,
        }
    
    def is_keyboard_event(self) -> bool:
        """Check if this is a keyboard event.
        
        Returns:
            bool: True if keyboard event
        """
        return self.event_type in {
            UIEventType.KEY_DOWN,
            UIEventType.KEY_UP,
            UIEventType.KEY_PRESS,
        }
    
    def is_focus_event(self) -> bool:
        """Check if this is a focus event.
        
        Returns:
            bool: True if focus event
        """
        return self.event_type in {
            UIEventType.FOCUS_GAINED,
            UIEventType.FOCUS_LOST,
        }
    
    @classmethod
    def mouse_click(cls, source: Any, x: int, y: int, button: int = 0) -> 'UIEvent':
        """Create a mouse click event.
        
        Args:
            source (Any): Source component
            x (int): Mouse X coordinate
            y (int): Mouse Y coordinate
            button (int): Mouse button (0=left, 1=right, 2=middle)
            
        Returns:
            UIEvent: Mouse click event
        """
        return cls(
            event_type=UIEventType.MOUSE_CLICK,
            source=source,
            mouse_x=x,
            mouse_y=y,
            mouse_button=button
        )
    
    @classmethod
    def key_press(cls, source: Any, key: str, key_code: int = 0, 
                  modifiers: Optional[Dict[str, bool]] = None) -> 'UIEvent':
        """Create a key press event.
        
        Args:
            source (Any): Source component
            key (str): Key identifier
            key_code (int): Key code
            modifiers (Dict[str, bool], optional): Modifier keys
            
        Returns:
            UIEvent: Key press event
        """
        return cls(
            event_type=UIEventType.KEY_PRESS,
            source=source,
            key=key,
            key_code=key_code,
            modifiers=modifiers or {}
        )
    
    @classmethod
    def button_clicked(cls, source: Any, button_data: Optional[Dict[str, Any]] = None) -> 'UIEvent':
        """Create a button clicked event.
        
        Args:
            source (Any): Source button component
            button_data (Dict[str, Any], optional): Button-specific data
            
        Returns:
            UIEvent: Button clicked event
        """
        return cls(
            event_type=UIEventType.BUTTON_CLICKED,
            source=source,
            data=button_data
        )
    
    @classmethod
    def menu_item_selected(cls, source: Any, item_index: int, item_data: Any = None) -> 'UIEvent':
        """Create a menu item selected event.
        
        Args:
            source (Any): Source menu component
            item_index (int): Selected item index
            item_data (Any): Item data
            
        Returns:
            UIEvent: Menu item selected event
        """
        return cls(
            event_type=UIEventType.MENU_ITEM_SELECTED,
            source=source,
            data={'item_index': item_index, 'item_data': item_data}
        )
    
    @classmethod
    def custom(cls, source: Any, event_name: str, data: Optional[Dict[str, Any]] = None) -> 'UIEvent':
        """Create a custom event.
        
        Args:
            source (Any): Source component
            event_name (str): Custom event name
            data (Dict[str, Any], optional): Event data
            
        Returns:
            UIEvent: Custom event
        """
        event_data = data or {}
        event_data['event_name'] = event_name
        
        return cls(
            event_type=UIEventType.CUSTOM,
            source=source,
            data=event_data
        )
    
    def __repr__(self) -> str:
        """String representation of event."""
        parts = [f"UIEvent({self.event_type.name}"]
        
        if self.source:
            parts.append(f"source={type(self.source).__name__}")
        
        if self.is_mouse_event() and self.mouse_x is not None:
            parts.append(f"pos=({self.mouse_x},{self.mouse_y})")
            if self.mouse_button is not None:
                parts.append(f"button={self.mouse_button}")
        
        if self.is_keyboard_event() and self.key:
            parts.append(f"key='{self.key}'")
        
        if self.handled:
            parts.append("handled=True")
        
        if self.cancelled:
            parts.append("cancelled=True")
        
        return ", ".join(parts) + ")"
