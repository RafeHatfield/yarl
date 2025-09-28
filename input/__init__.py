"""Input abstraction system for multi-platform input handling.

This package provides a comprehensive input abstraction layer that supports
multiple input backends (keyboard, mouse, gamepad, touch) and provides a
unified interface for input handling across different platforms and rendering
systems.

Key Components:
- InputManager: Central input coordination and event dispatching
- InputBackend: Abstract interface for different input systems
- InputEvent: Unified event representation for all input types
- InputMapping: Configurable key/button mapping and action profiles
- InputState: Track input states, combinations, and sequences
"""

from .manager import InputManager, get_input_manager, initialize_input_manager
from .backend import InputBackend, InputCapabilities, NullInputBackend
from .events import (
    InputEvent, InputEventType, KeyEvent, MouseEvent, GamepadEvent, TouchEvent,
    InputModifiers, MouseButton, GamepadButton, GamepadAxis,
    create_key_event, create_mouse_event, create_gamepad_event
)
from .mapping import (
    InputMapping, ActionMapping, InputProfile, KeyBinding, MouseBinding,
    GamepadBinding, InputAction, InputTrigger
)
from .state import InputState, InputStateManager, InputSequence, InputCombo, InputSequenceStep
from .libtcod_backend import LibtcodInputBackend
from .exceptions import InputError, InputBackendError, InputMappingError

__all__ = [
    'InputManager',
    'get_input_manager', 
    'initialize_input_manager',
    'InputBackend',
    'InputCapabilities',
    'NullInputBackend',
    'InputEvent',
    'InputEventType',
    'KeyEvent',
    'MouseEvent', 
    'GamepadEvent',
    'TouchEvent',
    'InputModifiers',
    'MouseButton',
    'GamepadButton',
    'GamepadAxis',
    'create_key_event',
    'create_mouse_event',
    'create_gamepad_event',
    'InputMapping',
    'ActionMapping',
    'InputProfile',
    'KeyBinding',
    'MouseBinding',
    'GamepadBinding',
    'InputAction',
    'InputTrigger',
    'InputState',
    'InputStateManager',
    'InputSequence',
    'InputCombo',
    'InputSequenceStep',
    'LibtcodInputBackend',
    'InputError',
    'InputBackendError',
    'InputMappingError',
]
