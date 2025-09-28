"""Libtcod input backend implementation.

This module provides an input backend that integrates with the libtcod
library, allowing the input system to work with the existing game
infrastructure while providing modern input abstraction.
"""

from typing import List, Dict, Optional, Tuple
import time

try:
    import tcod
    import tcod.libtcodpy as libtcodpy
    LIBTCOD_AVAILABLE = True
except ImportError:
    LIBTCOD_AVAILABLE = False

from .backend import InputBackend, InputCapabilities, InputDevice, InputDeviceType
from .events import (
    InputEvent, InputEventType, KeyEvent, MouseEvent, 
    InputModifiers, MouseButton, create_key_event, create_mouse_event
)
from .exceptions import InputBackendError


class LibtcodInputBackend(InputBackend):
    """Input backend implementation using libtcod.
    
    This backend provides keyboard and mouse input through the libtcod
    library, maintaining compatibility with existing libtcod-based games
    while providing modern input abstraction.
    """
    
    def __init__(self):
        """Initialize the libtcod input backend."""
        super().__init__("libtcod")
        
        if not LIBTCOD_AVAILABLE:
            raise InputBackendError("libtcod", "initialization", 
                                  Exception("libtcod library not available"))
        
        # Input state tracking
        self._key_states: Dict[str, bool] = {}
        self._mouse_button_states: Dict[MouseButton, bool] = {}
        self._mouse_position = (0, 0)
        self._last_mouse_position = (0, 0)
        
        # Event queue
        self._event_queue: List[InputEvent] = []
        
        # Key mapping from libtcod to our standard names
        self._key_map = self._create_key_map()
        self._reverse_key_map = {v: k for k, v in self._key_map.items()}
        
        # Mouse button mapping
        self._mouse_button_map = {
            1: MouseButton.LEFT,
            2: MouseButton.RIGHT,
            3: MouseButton.MIDDLE,
        }
    
    @property
    def capabilities(self) -> InputCapabilities:
        """Get the capabilities of the libtcod backend."""
        return (InputCapabilities.KEYBOARD | 
                InputCapabilities.MOUSE |
                InputCapabilities.KEY_REPEAT |
                InputCapabilities.WINDOW_EVENTS)
    
    def initialize(self) -> bool:
        """Initialize the libtcod input backend."""
        try:
            # Register virtual keyboard and mouse devices
            keyboard = InputDevice(
                device_id="libtcod_keyboard",
                device_type=InputDeviceType.KEYBOARD,
                name="Libtcod Keyboard",
                capabilities=InputCapabilities.KEYBOARD | InputCapabilities.KEY_REPEAT
            )
            self._register_device(keyboard)
            
            mouse = InputDevice(
                device_id="libtcod_mouse",
                device_type=InputDeviceType.MOUSE,
                name="Libtcod Mouse",
                capabilities=InputCapabilities.MOUSE
            )
            self._register_device(mouse)
            
            self.initialized = True
            return True
            
        except Exception as e:
            raise InputBackendError("libtcod", "initialize", e)
    
    def shutdown(self) -> None:
        """Shutdown the libtcod input backend."""
        self._event_queue.clear()
        self._key_states.clear()
        self._mouse_button_states.clear()
        self.devices.clear()
        self.initialized = False
    
    def poll_events(self) -> List[InputEvent]:
        """Poll for input events from libtcod."""
        if not self.initialized:
            return []
        
        events = []
        
        try:
            # Poll libtcod events
            key = libtcod.Key()
            mouse = libtcod.Mouse()
            
            # Get events using libtcod's event system
            event_mask = libtcod.EVENT_KEY_PRESS | libtcod.EVENT_KEY_RELEASE | libtcod.EVENT_MOUSE
            
            while True:
                event_type = libtcod.sys_check_for_event(event_mask, key, mouse)
                
                if event_type == libtcod.EVENT_NONE:
                    break
                
                # Process keyboard events
                if event_type & (libtcod.EVENT_KEY_PRESS | libtcod.EVENT_KEY_RELEASE):
                    key_events = self._process_key_event(key, event_type)
                    events.extend(key_events)
                
                # Process mouse events
                if event_type & libtcod.EVENT_MOUSE:
                    mouse_events = self._process_mouse_event(mouse)
                    events.extend(mouse_events)
        
        except Exception as e:
            # Don't let polling errors break the game
            print(f"Libtcod input polling error: {e}")
        
        # Notify callbacks
        for event in events:
            self._notify_event_callbacks(event)
        
        return events
    
    def _process_key_event(self, key: 'libtcod.Key', event_type: int) -> List[KeyEvent]:
        """Process a libtcod key event."""
        events = []
        
        # Convert libtcod key to our key name
        key_name = self._libtcod_key_to_name(key)
        if not key_name:
            return events
        
        # Determine event type
        if event_type & libtcod.EVENT_KEY_PRESS:
            input_event_type = InputEventType.KEY_DOWN
            self._key_states[key_name] = True
        else:  # EVENT_KEY_RELEASE
            input_event_type = InputEventType.KEY_UP
            self._key_states[key_name] = False
        
        # Convert modifiers
        modifiers = self._convert_modifiers(key)
        
        # Create key event
        key_event = create_key_event(
            event_type=input_event_type,
            key=key_name,
            modifiers=modifiers,
            key_code=key.vk,
            unicode=chr(key.c) if key.c > 0 else "",
            repeat=False  # libtcod doesn't provide repeat info directly
        )
        
        events.append(key_event)
        return events
    
    def _process_mouse_event(self, mouse: 'libtcod.Mouse') -> List[MouseEvent]:
        """Process a libtcod mouse event."""
        events = []
        current_time = time.time()
        
        # Check for position changes
        new_position = (mouse.x, mouse.y)
        if new_position != self._last_mouse_position:
            delta_x = mouse.x - self._last_mouse_position[0]
            delta_y = mouse.y - self._last_mouse_position[1]
            
            move_event = create_mouse_event(
                event_type=InputEventType.MOUSE_MOVE,
                x=mouse.x,
                y=mouse.y,
                delta_x=delta_x,
                delta_y=delta_y
            )
            events.append(move_event)
            
            self._last_mouse_position = new_position
            self._mouse_position = new_position
        
        # Check for button state changes
        current_buttons = {
            MouseButton.LEFT: mouse.lbutton,
            MouseButton.RIGHT: mouse.rbutton,
            MouseButton.MIDDLE: mouse.mbutton,
        }
        
        for button, pressed in current_buttons.items():
            was_pressed = self._mouse_button_states.get(button, False)
            
            if pressed and not was_pressed:
                # Button pressed
                button_event = create_mouse_event(
                    event_type=InputEventType.MOUSE_DOWN,
                    x=mouse.x,
                    y=mouse.y,
                    button=button
                )
                events.append(button_event)
                self._mouse_button_states[button] = True
                
            elif not pressed and was_pressed:
                # Button released
                button_event = create_mouse_event(
                    event_type=InputEventType.MOUSE_UP,
                    x=mouse.x,
                    y=mouse.y,
                    button=button
                )
                events.append(button_event)
                self._mouse_button_states[button] = False
        
        # Check for wheel events (if supported)
        if hasattr(mouse, 'wheel_up') and mouse.wheel_up:
            wheel_event = create_mouse_event(
                event_type=InputEventType.MOUSE_WHEEL,
                x=mouse.x,
                y=mouse.y,
                wheel_delta=1.0
            )
            events.append(wheel_event)
        
        if hasattr(mouse, 'wheel_down') and mouse.wheel_down:
            wheel_event = create_mouse_event(
                event_type=InputEventType.MOUSE_WHEEL,
                x=mouse.x,
                y=mouse.y,
                wheel_delta=-1.0
            )
            events.append(wheel_event)
        
        return events
    
    def get_devices(self) -> List[InputDevice]:
        """Get list of available input devices."""
        return list(self.devices.values())
    
    def is_key_pressed(self, key: str) -> bool:
        """Check if a key is currently pressed."""
        return self._key_states.get(key, False)
    
    def is_mouse_button_pressed(self, button: str) -> bool:
        """Check if a mouse button is currently pressed."""
        try:
            mouse_button = MouseButton[button.upper()]
            return self._mouse_button_states.get(mouse_button, False)
        except (KeyError, ValueError):
            return False
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        return self._mouse_position
    
    def _libtcod_key_to_name(self, key: 'libtcod.Key') -> Optional[str]:
        """Convert libtcod key to standard key name."""
        # Handle special keys first
        if key.vk in self._key_map:
            return self._key_map[key.vk]
        
        # Handle character keys
        if key.c > 0:
            char = chr(key.c).lower()
            if char.isalnum() or char in ' .,;:!?-_+=[]{}()':
                return char
        
        return None
    
    def _convert_modifiers(self, key: 'libtcod.Key') -> InputModifiers:
        """Convert libtcod key modifiers to our modifier flags."""
        modifiers = InputModifiers.NONE
        
        if key.shift:
            modifiers |= InputModifiers.SHIFT
        if key.lctrl or key.rctrl:
            modifiers |= InputModifiers.CTRL
        if key.lalt or key.ralt:
            modifiers |= InputModifiers.ALT
        if key.lmeta or key.rmeta:
            modifiers |= InputModifiers.META
        
        return modifiers
    
    def _create_key_map(self) -> Dict[int, str]:
        """Create mapping from libtcod key codes to standard key names."""
        if not LIBTCOD_AVAILABLE:
            return {}
        
        return {
            # Arrow keys
            libtcod.KEY_UP: "up",
            libtcod.KEY_DOWN: "down",
            libtcod.KEY_LEFT: "left",
            libtcod.KEY_RIGHT: "right",
            
            # Function keys
            libtcod.KEY_F1: "f1",
            libtcod.KEY_F2: "f2",
            libtcod.KEY_F3: "f3",
            libtcod.KEY_F4: "f4",
            libtcod.KEY_F5: "f5",
            libtcod.KEY_F6: "f6",
            libtcod.KEY_F7: "f7",
            libtcod.KEY_F8: "f8",
            libtcod.KEY_F9: "f9",
            libtcod.KEY_F10: "f10",
            libtcod.KEY_F11: "f11",
            libtcod.KEY_F12: "f12",
            
            # Special keys
            libtcod.KEY_ESCAPE: "escape",
            libtcod.KEY_BACKSPACE: "backspace",
            libtcod.KEY_TAB: "tab",
            libtcod.KEY_ENTER: "enter",
            libtcod.KEY_SPACE: "space",
            libtcod.KEY_DELETE: "delete",
            libtcod.KEY_INSERT: "insert",
            libtcod.KEY_HOME: "home",
            libtcod.KEY_END: "end",
            libtcod.KEY_PAGEUP: "pageup",
            libtcod.KEY_PAGEDOWN: "pagedown",
            
            # Keypad
            libtcod.KEY_KP0: "kp0",
            libtcod.KEY_KP1: "kp1",
            libtcod.KEY_KP2: "kp2",
            libtcod.KEY_KP3: "kp3",
            libtcod.KEY_KP4: "kp4",
            libtcod.KEY_KP5: "kp5",
            libtcod.KEY_KP6: "kp6",
            libtcod.KEY_KP7: "kp7",
            libtcod.KEY_KP8: "kp8",
            libtcod.KEY_KP9: "kp9",
            libtcod.KEY_KPADD: "kp_plus",
            libtcod.KEY_KPSUB: "kp_minus",
            libtcod.KEY_KPMUL: "kp_multiply",
            libtcod.KEY_KPDIV: "kp_divide",
            libtcod.KEY_KPENTER: "kp_enter",
            libtcod.KEY_KPDEC: "kp_decimal",
            
            # Modifier keys
            libtcod.KEY_SHIFT: "shift",
            libtcod.KEY_CONTROL: "ctrl",
            libtcod.KEY_ALT: "alt",
        }
    
    def get_backend_info(self) -> Dict[str, any]:
        """Get information about this backend."""
        info = super().get_backend_info()
        info.update({
            'libtcod_available': LIBTCOD_AVAILABLE,
            'key_states_count': len(self._key_states),
            'mouse_position': self._mouse_position,
            'supported_keys': len(self._key_map),
        })
        return info
