"""Input event system for unified input representation.

This module defines the event types and structures used throughout
the input system to represent different types of input events in
a unified, platform-independent way.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto, Flag
from typing import Optional, Dict, Any, Union, Tuple
from dataclasses import dataclass
import time


class InputEventType(Enum):
    """Types of input events."""
    
    # Keyboard events
    KEY_DOWN = auto()
    KEY_UP = auto()
    KEY_REPEAT = auto()
    
    # Mouse events
    MOUSE_DOWN = auto()
    MOUSE_UP = auto()
    MOUSE_MOVE = auto()
    MOUSE_WHEEL = auto()
    MOUSE_ENTER = auto()
    MOUSE_LEAVE = auto()
    
    # Gamepad events
    GAMEPAD_BUTTON_DOWN = auto()
    GAMEPAD_BUTTON_UP = auto()
    GAMEPAD_AXIS_MOTION = auto()
    GAMEPAD_CONNECTED = auto()
    GAMEPAD_DISCONNECTED = auto()
    
    # Touch events
    TOUCH_DOWN = auto()
    TOUCH_UP = auto()
    TOUCH_MOVE = auto()
    TOUCH_CANCEL = auto()
    
    # System events
    WINDOW_FOCUS = auto()
    WINDOW_UNFOCUS = auto()
    WINDOW_RESIZE = auto()
    QUIT = auto()


class InputModifiers(Flag):
    """Input modifier flags."""
    
    NONE = 0
    SHIFT = auto()
    CTRL = auto()
    ALT = auto()
    META = auto()  # Windows key, Cmd key, etc.
    CAPS_LOCK = auto()
    NUM_LOCK = auto()
    SCROLL_LOCK = auto()


class MouseButton(Enum):
    """Mouse button identifiers."""
    
    LEFT = auto()
    RIGHT = auto()
    MIDDLE = auto()
    X1 = auto()      # Back button
    X2 = auto()      # Forward button
    WHEEL_UP = auto()
    WHEEL_DOWN = auto()
    WHEEL_LEFT = auto()
    WHEEL_RIGHT = auto()


class GamepadButton(Enum):
    """Gamepad button identifiers."""
    
    # Face buttons (Xbox naming convention)
    A = auto()
    B = auto()
    X = auto()
    Y = auto()
    
    # Shoulder buttons
    LEFT_BUMPER = auto()
    RIGHT_BUMPER = auto()
    LEFT_TRIGGER = auto()
    RIGHT_TRIGGER = auto()
    
    # D-pad
    DPAD_UP = auto()
    DPAD_DOWN = auto()
    DPAD_LEFT = auto()
    DPAD_RIGHT = auto()
    
    # Stick buttons
    LEFT_STICK = auto()
    RIGHT_STICK = auto()
    
    # System buttons
    START = auto()
    SELECT = auto()
    HOME = auto()
    
    # Additional buttons
    SHARE = auto()
    OPTIONS = auto()
    TOUCHPAD = auto()


class GamepadAxis(Enum):
    """Gamepad axis identifiers."""
    
    LEFT_STICK_X = auto()
    LEFT_STICK_Y = auto()
    RIGHT_STICK_X = auto()
    RIGHT_STICK_Y = auto()
    LEFT_TRIGGER = auto()
    RIGHT_TRIGGER = auto()
    DPAD_X = auto()
    DPAD_Y = auto()


@dataclass
class InputEvent(ABC):
    """Base class for all input events.
    
    This class provides the common interface and data that all
    input events share, including timing, modifiers, and device
    information.
    """
    
    event_type: InputEventType
    timestamp: float
    modifiers: InputModifiers = InputModifiers.NONE
    device_id: Optional[str] = None
    consumed: bool = False
    
    def __post_init__(self):
        """Initialize event with current timestamp if not provided."""
        if self.timestamp == 0:
            self.timestamp = time.time()
    
    def consume(self) -> None:
        """Mark this event as consumed to prevent further processing."""
        self.consumed = True
    
    def is_consumed(self) -> bool:
        """Check if this event has been consumed.
        
        Returns:
            bool: True if event is consumed
        """
        return self.consumed
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation.
        
        Returns:
            Dict[str, Any]: Event data as dictionary
        """
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InputEvent':
        """Create event from dictionary representation.
        
        Args:
            data (Dict[str, Any]): Event data dictionary
            
        Returns:
            InputEvent: Created event instance
        """
        pass


@dataclass
class KeyEvent(InputEvent):
    """Keyboard input event."""
    
    key: str = ""  # Key identifier (e.g., 'a', 'space', 'escape')
    key_code: int = 0  # Platform-specific key code
    unicode: str = ""  # Unicode character if applicable
    repeat: bool = False  # True if this is a key repeat event
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert key event to dictionary."""
        return {
            'event_type': self.event_type.name,
            'timestamp': self.timestamp,
            'modifiers': self.modifiers.value,
            'device_id': self.device_id,
            'key': self.key,
            'key_code': self.key_code,
            'unicode': self.unicode,
            'repeat': self.repeat
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeyEvent':
        """Create key event from dictionary."""
        return cls(
            event_type=InputEventType[data['event_type']],
            timestamp=data['timestamp'],
            modifiers=InputModifiers(data.get('modifiers', 0)),
            device_id=data.get('device_id'),
            key=data['key'],
            key_code=data.get('key_code', 0),
            unicode=data.get('unicode', ''),
            repeat=data.get('repeat', False)
        )
    
    def __str__(self) -> str:
        """String representation of key event."""
        modifiers_str = ""
        if self.modifiers != InputModifiers.NONE:
            mod_names = []
            if self.modifiers & InputModifiers.CTRL:
                mod_names.append("Ctrl")
            if self.modifiers & InputModifiers.SHIFT:
                mod_names.append("Shift")
            if self.modifiers & InputModifiers.ALT:
                mod_names.append("Alt")
            if self.modifiers & InputModifiers.META:
                mod_names.append("Meta")
            modifiers_str = "+".join(mod_names) + "+"
        
        return f"{modifiers_str}{self.key}"


@dataclass
class MouseEvent(InputEvent):
    """Mouse input event."""
    
    x: int = 0  # Mouse X coordinate
    y: int = 0  # Mouse Y coordinate
    button: Optional[MouseButton] = None  # Button for button events
    delta_x: int = 0  # Movement delta X
    delta_y: int = 0  # Movement delta Y
    wheel_delta: float = 0.0  # Wheel scroll delta
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert mouse event to dictionary."""
        return {
            'event_type': self.event_type.name,
            'timestamp': self.timestamp,
            'modifiers': self.modifiers.value,
            'device_id': self.device_id,
            'x': self.x,
            'y': self.y,
            'button': self.button.name if self.button else None,
            'delta_x': self.delta_x,
            'delta_y': self.delta_y,
            'wheel_delta': self.wheel_delta
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MouseEvent':
        """Create mouse event from dictionary."""
        button = None
        if data.get('button'):
            button = MouseButton[data['button']]
        
        return cls(
            event_type=InputEventType[data['event_type']],
            timestamp=data['timestamp'],
            modifiers=InputModifiers(data.get('modifiers', 0)),
            device_id=data.get('device_id'),
            x=data.get('x', 0),
            y=data.get('y', 0),
            button=button,
            delta_x=data.get('delta_x', 0),
            delta_y=data.get('delta_y', 0),
            wheel_delta=data.get('wheel_delta', 0.0)
        )


@dataclass
class GamepadEvent(InputEvent):
    """Gamepad input event."""
    
    gamepad_id: int = 0  # Gamepad instance ID
    button: Optional[GamepadButton] = None  # Button for button events
    axis: Optional[GamepadAxis] = None  # Axis for axis events
    value: float = 0.0  # Button state (0.0-1.0) or axis value (-1.0 to 1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert gamepad event to dictionary."""
        return {
            'event_type': self.event_type.name,
            'timestamp': self.timestamp,
            'modifiers': self.modifiers.value,
            'device_id': self.device_id,
            'gamepad_id': self.gamepad_id,
            'button': self.button.name if self.button else None,
            'axis': self.axis.name if self.axis else None,
            'value': self.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GamepadEvent':
        """Create gamepad event from dictionary."""
        button = None
        if data.get('button'):
            button = GamepadButton[data['button']]
        
        axis = None
        if data.get('axis'):
            axis = GamepadAxis[data['axis']]
        
        return cls(
            event_type=InputEventType[data['event_type']],
            timestamp=data['timestamp'],
            modifiers=InputModifiers(data.get('modifiers', 0)),
            device_id=data.get('device_id'),
            gamepad_id=data.get('gamepad_id', 0),
            button=button,
            axis=axis,
            value=data.get('value', 0.0)
        )


@dataclass
class TouchEvent(InputEvent):
    """Touch input event."""
    
    touch_id: int = 0  # Touch point identifier
    x: float = 0.0  # Touch X coordinate (normalized 0.0-1.0)
    y: float = 0.0  # Touch Y coordinate (normalized 0.0-1.0)
    pressure: float = 1.0  # Touch pressure (0.0-1.0)
    size: float = 1.0  # Touch size (0.0-1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert touch event to dictionary."""
        return {
            'event_type': self.event_type.name,
            'timestamp': self.timestamp,
            'modifiers': self.modifiers.value,
            'device_id': self.device_id,
            'touch_id': self.touch_id,
            'x': self.x,
            'y': self.y,
            'pressure': self.pressure,
            'size': self.size
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TouchEvent':
        """Create touch event from dictionary."""
        return cls(
            event_type=InputEventType[data['event_type']],
            timestamp=data['timestamp'],
            modifiers=InputModifiers(data.get('modifiers', 0)),
            device_id=data.get('device_id'),
            touch_id=data.get('touch_id', 0),
            x=data.get('x', 0.0),
            y=data.get('y', 0.0),
            pressure=data.get('pressure', 1.0),
            size=data.get('size', 1.0)
        )


# Type aliases for convenience
AnyInputEvent = Union[KeyEvent, MouseEvent, GamepadEvent, TouchEvent]
EventPosition = Tuple[int, int]  # (x, y) coordinate pair
EventDelta = Tuple[int, int]     # (delta_x, delta_y) movement pair


def create_key_event(event_type: InputEventType, key: str, 
                    modifiers: InputModifiers = InputModifiers.NONE,
                    key_code: int = 0, unicode: str = "", 
                    repeat: bool = False) -> KeyEvent:
    """Create a keyboard event with current timestamp.
    
    Args:
        event_type (InputEventType): Type of key event
        key (str): Key identifier
        modifiers (InputModifiers): Modifier keys pressed
        key_code (int): Platform-specific key code
        unicode (str): Unicode character
        repeat (bool): Whether this is a repeat event
        
    Returns:
        KeyEvent: Created key event
    """
    return KeyEvent(
        event_type=event_type,
        timestamp=time.time(),
        modifiers=modifiers,
        key=key,
        key_code=key_code,
        unicode=unicode,
        repeat=repeat
    )


def create_mouse_event(event_type: InputEventType, x: int = 0, y: int = 0,
                      button: Optional[MouseButton] = None,
                      delta_x: int = 0, delta_y: int = 0,
                      wheel_delta: float = 0.0,
                      modifiers: InputModifiers = InputModifiers.NONE) -> MouseEvent:
    """Create a mouse event with current timestamp.
    
    Args:
        event_type (InputEventType): Type of mouse event
        x (int): Mouse X coordinate
        y (int): Mouse Y coordinate
        button (MouseButton, optional): Mouse button
        delta_x (int): Movement delta X
        delta_y (int): Movement delta Y
        wheel_delta (float): Wheel scroll delta
        modifiers (InputModifiers): Modifier keys pressed
        
    Returns:
        MouseEvent: Created mouse event
    """
    return MouseEvent(
        event_type=event_type,
        timestamp=time.time(),
        modifiers=modifiers,
        x=x,
        y=y,
        button=button,
        delta_x=delta_x,
        delta_y=delta_y,
        wheel_delta=wheel_delta
    )


def create_gamepad_event(event_type: InputEventType, gamepad_id: int = 0,
                        button: Optional[GamepadButton] = None,
                        axis: Optional[GamepadAxis] = None,
                        value: float = 0.0) -> GamepadEvent:
    """Create a gamepad event with current timestamp.
    
    Args:
        event_type (InputEventType): Type of gamepad event
        gamepad_id (int): Gamepad instance ID
        button (GamepadButton, optional): Gamepad button
        axis (GamepadAxis, optional): Gamepad axis
        value (float): Button/axis value
        
    Returns:
        GamepadEvent: Created gamepad event
    """
    return GamepadEvent(
        event_type=event_type,
        timestamp=time.time(),
        gamepad_id=gamepad_id,
        button=button,
        axis=axis,
        value=value
    )
