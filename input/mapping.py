"""Input mapping system for configurable controls.

This module provides a flexible input mapping system that allows users
to configure custom key bindings, create input profiles, and define
complex input actions and triggers.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Union, Callable, Set
from dataclasses import dataclass, field
import json
import time

from .events import (
    InputEvent, InputEventType, KeyEvent, MouseEvent, GamepadEvent,
    InputModifiers, MouseButton, GamepadButton, GamepadAxis
)
from .exceptions import InputMappingError


class InputTrigger(Enum):
    """Input trigger types."""
    
    PRESS = auto()      # Triggered on key/button press
    RELEASE = auto()    # Triggered on key/button release
    HOLD = auto()       # Triggered while key/button is held
    DOUBLE_PRESS = auto()  # Triggered on double press
    LONG_PRESS = auto() # Triggered on long press
    SEQUENCE = auto()   # Triggered by input sequence
    COMBO = auto()      # Triggered by input combination


class InputAction(Enum):
    """Standard game input actions."""
    
    # Movement
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    MOVE_NORTHWEST = "move_northwest"
    MOVE_NORTHEAST = "move_northeast"
    MOVE_SOUTHWEST = "move_southwest"
    MOVE_SOUTHEAST = "move_southeast"
    
    # Actions
    CONFIRM = "confirm"
    CANCEL = "cancel"
    ATTACK = "attack"
    USE_ITEM = "use_item"
    PICKUP = "pickup"
    DROP = "drop"
    REST = "rest"
    WAIT = "wait"
    
    # Interface
    SHOW_CHARACTER = "show_character"
    SHOW_HELP = "show_help"
    SHOW_MENU = "show_menu"
    TOGGLE_FULLSCREEN = "toggle_fullscreen"
    
    # System
    QUIT = "quit"
    SAVE = "save"
    LOAD = "load"
    PAUSE = "pause"
    
    # Custom actions (can be extended)
    CUSTOM_1 = "custom_1"
    CUSTOM_2 = "custom_2"
    CUSTOM_3 = "custom_3"
    CUSTOM_4 = "custom_4"
    CUSTOM_5 = "custom_5"


@dataclass
class InputBinding(ABC):
    """Base class for input bindings."""
    
    trigger: InputTrigger = InputTrigger.PRESS
    modifiers: InputModifiers = InputModifiers.NONE
    enabled: bool = True
    
    @abstractmethod
    def matches(self, event: InputEvent) -> bool:
        """Check if this binding matches an input event.
        
        Args:
            event (InputEvent): Input event to check
            
        Returns:
            bool: True if binding matches the event
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert binding to dictionary representation."""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InputBinding':
        """Create binding from dictionary representation."""
        pass


@dataclass
class KeyBinding(InputBinding):
    """Keyboard input binding."""
    
    key: str = ""
    
    def matches(self, event: InputEvent) -> bool:
        """Check if this key binding matches an event."""
        if not self.enabled or not isinstance(event, KeyEvent):
            return False
        
        # Check key match
        if event.key != self.key:
            return False
        
        # Check modifiers
        if event.modifiers != self.modifiers:
            return False
        
        # Check trigger type
        if self.trigger == InputTrigger.PRESS:
            return event.event_type == InputEventType.KEY_DOWN
        elif self.trigger == InputTrigger.RELEASE:
            return event.event_type == InputEventType.KEY_UP
        elif self.trigger == InputTrigger.HOLD:
            return event.event_type in (InputEventType.KEY_DOWN, InputEventType.KEY_REPEAT)
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert key binding to dictionary."""
        return {
            'type': 'key',
            'key': self.key,
            'trigger': self.trigger.name,
            'modifiers': self.modifiers.value,
            'enabled': self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeyBinding':
        """Create key binding from dictionary."""
        return cls(
            key=data['key'],
            trigger=InputTrigger[data.get('trigger', 'PRESS')],
            modifiers=InputModifiers(data.get('modifiers', 0)),
            enabled=data.get('enabled', True)
        )
    
    def __str__(self) -> str:
        """String representation of key binding."""
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
class MouseBinding(InputBinding):
    """Mouse input binding."""
    
    button: Optional[MouseButton] = None
    
    def matches(self, event: InputEvent) -> bool:
        """Check if this mouse binding matches an event."""
        if not self.enabled or not isinstance(event, MouseEvent):
            return False
        
        # Check button match (if specified)
        if self.button and event.button != self.button:
            return False
        
        # Check modifiers
        if event.modifiers != self.modifiers:
            return False
        
        # Check trigger type
        if self.trigger == InputTrigger.PRESS:
            return event.event_type == InputEventType.MOUSE_DOWN
        elif self.trigger == InputTrigger.RELEASE:
            return event.event_type == InputEventType.MOUSE_UP
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert mouse binding to dictionary."""
        return {
            'type': 'mouse',
            'button': self.button.name if self.button else None,
            'trigger': self.trigger.name,
            'modifiers': self.modifiers.value,
            'enabled': self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MouseBinding':
        """Create mouse binding from dictionary."""
        button = None
        if data.get('button'):
            button = MouseButton[data['button']]
        
        return cls(
            button=button,
            trigger=InputTrigger[data.get('trigger', 'PRESS')],
            modifiers=InputModifiers(data.get('modifiers', 0)),
            enabled=data.get('enabled', True)
        )


@dataclass
class GamepadBinding(InputBinding):
    """Gamepad input binding."""
    
    button: Optional[GamepadButton] = None
    axis: Optional[GamepadAxis] = None
    axis_threshold: float = 0.5  # Threshold for axis triggers
    gamepad_id: Optional[int] = None  # Specific gamepad ID (None = any)
    
    def matches(self, event: InputEvent) -> bool:
        """Check if this gamepad binding matches an event."""
        if not self.enabled or not isinstance(event, GamepadEvent):
            return False
        
        # Check gamepad ID (if specified)
        if self.gamepad_id is not None and event.gamepad_id != self.gamepad_id:
            return False
        
        # Check button binding
        if self.button:
            if event.button != self.button:
                return False
            
            if self.trigger == InputTrigger.PRESS:
                return event.event_type == InputEventType.GAMEPAD_BUTTON_DOWN
            elif self.trigger == InputTrigger.RELEASE:
                return event.event_type == InputEventType.GAMEPAD_BUTTON_UP
        
        # Check axis binding
        if self.axis:
            if event.axis != self.axis:
                return False
            
            if event.event_type == InputEventType.GAMEPAD_AXIS_MOTION:
                return abs(event.value) >= self.axis_threshold
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert gamepad binding to dictionary."""
        return {
            'type': 'gamepad',
            'button': self.button.name if self.button else None,
            'axis': self.axis.name if self.axis else None,
            'axis_threshold': self.axis_threshold,
            'gamepad_id': self.gamepad_id,
            'trigger': self.trigger.name,
            'modifiers': self.modifiers.value,
            'enabled': self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GamepadBinding':
        """Create gamepad binding from dictionary."""
        button = None
        if data.get('button'):
            button = GamepadButton[data['button']]
        
        axis = None
        if data.get('axis'):
            axis = GamepadAxis[data['axis']]
        
        return cls(
            button=button,
            axis=axis,
            axis_threshold=data.get('axis_threshold', 0.5),
            gamepad_id=data.get('gamepad_id'),
            trigger=InputTrigger[data.get('trigger', 'PRESS')],
            modifiers=InputModifiers(data.get('modifiers', 0)),
            enabled=data.get('enabled', True)
        )


@dataclass
class ActionMapping:
    """Maps an input action to one or more input bindings."""
    
    action: Union[InputAction, str]
    bindings: List[InputBinding] = field(default_factory=list)
    enabled: bool = True
    description: str = ""
    
    def add_binding(self, binding: InputBinding) -> None:
        """Add an input binding to this action.
        
        Args:
            binding (InputBinding): Binding to add
        """
        if binding not in self.bindings:
            self.bindings.append(binding)
    
    def remove_binding(self, binding: InputBinding) -> bool:
        """Remove an input binding from this action.
        
        Args:
            binding (InputBinding): Binding to remove
            
        Returns:
            bool: True if binding was removed
        """
        if binding in self.bindings:
            self.bindings.remove(binding)
            return True
        return False
    
    def clear_bindings(self) -> None:
        """Clear all bindings for this action."""
        self.bindings.clear()
    
    def matches(self, event: InputEvent) -> bool:
        """Check if any binding for this action matches an event.
        
        Args:
            event (InputEvent): Input event to check
            
        Returns:
            bool: True if any binding matches
        """
        if not self.enabled:
            return False
        
        return any(binding.matches(event) for binding in self.bindings if binding.enabled)
    
    def get_action_name(self) -> str:
        """Get the action name as string.
        
        Returns:
            str: Action name
        """
        if isinstance(self.action, InputAction):
            return self.action.value
        return str(self.action)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert action mapping to dictionary."""
        return {
            'action': self.get_action_name(),
            'bindings': [binding.to_dict() for binding in self.bindings],
            'enabled': self.enabled,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionMapping':
        """Create action mapping from dictionary."""
        # Try to match standard action, otherwise use as custom string
        action = data['action']
        try:
            action = InputAction(action)
        except ValueError:
            pass  # Keep as string for custom actions
        
        bindings = []
        for binding_data in data.get('bindings', []):
            binding_type = binding_data.get('type', 'key')
            if binding_type == 'key':
                bindings.append(KeyBinding.from_dict(binding_data))
            elif binding_type == 'mouse':
                bindings.append(MouseBinding.from_dict(binding_data))
            elif binding_type == 'gamepad':
                bindings.append(GamepadBinding.from_dict(binding_data))
        
        return cls(
            action=action,
            bindings=bindings,
            enabled=data.get('enabled', True),
            description=data.get('description', '')
        )


class InputProfile:
    """Collection of input mappings for a specific context or user."""
    
    def __init__(self, name: str, description: str = ""):
        """Initialize input profile.
        
        Args:
            name (str): Profile name
            description (str): Profile description
        """
        self.name = name
        self.description = description
        self.mappings: Dict[str, ActionMapping] = {}
        self.enabled = True
        self.created_time = time.time()
        self.modified_time = time.time()
    
    def add_mapping(self, mapping: ActionMapping) -> None:
        """Add an action mapping to this profile.
        
        Args:
            mapping (ActionMapping): Action mapping to add
        """
        action_name = mapping.get_action_name()
        self.mappings[action_name] = mapping
        self.modified_time = time.time()
    
    def remove_mapping(self, action: Union[InputAction, str]) -> bool:
        """Remove an action mapping from this profile.
        
        Args:
            action (Union[InputAction, str]): Action to remove
            
        Returns:
            bool: True if mapping was removed
        """
        action_name = action.value if isinstance(action, InputAction) else str(action)
        if action_name in self.mappings:
            del self.mappings[action_name]
            self.modified_time = time.time()
            return True
        return False
    
    def get_mapping(self, action: Union[InputAction, str]) -> Optional[ActionMapping]:
        """Get action mapping for a specific action.
        
        Args:
            action (Union[InputAction, str]): Action to get mapping for
            
        Returns:
            ActionMapping: Action mapping if found, None otherwise
        """
        action_name = action.value if isinstance(action, InputAction) else str(action)
        return self.mappings.get(action_name)
    
    def get_actions_for_event(self, event: InputEvent) -> List[str]:
        """Get all actions that match an input event.
        
        Args:
            event (InputEvent): Input event to check
            
        Returns:
            List[str]: List of matching action names
        """
        if not self.enabled:
            return []
        
        matching_actions = []
        for action_name, mapping in self.mappings.items():
            if mapping.matches(event):
                matching_actions.append(action_name)
        
        return matching_actions
    
    def clear_mappings(self) -> None:
        """Clear all mappings from this profile."""
        self.mappings.clear()
        self.modified_time = time.time()
    
    def copy(self, new_name: str) -> 'InputProfile':
        """Create a copy of this profile with a new name.
        
        Args:
            new_name (str): Name for the copied profile
            
        Returns:
            InputProfile: Copied profile
        """
        new_profile = InputProfile(new_name, f"Copy of {self.description}")
        
        # Deep copy all mappings
        for action_name, mapping in self.mappings.items():
            new_mapping = ActionMapping(
                action=mapping.action,
                bindings=mapping.bindings.copy(),  # Shallow copy of bindings list
                enabled=mapping.enabled,
                description=mapping.description
            )
            new_profile.add_mapping(new_mapping)
        
        return new_profile
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary representation."""
        return {
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'created_time': self.created_time,
            'modified_time': self.modified_time,
            'mappings': {
                action_name: mapping.to_dict()
                for action_name, mapping in self.mappings.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InputProfile':
        """Create profile from dictionary representation."""
        profile = cls(
            name=data['name'],
            description=data.get('description', '')
        )
        
        profile.enabled = data.get('enabled', True)
        profile.created_time = data.get('created_time', time.time())
        profile.modified_time = data.get('modified_time', time.time())
        
        # Load mappings
        mappings_data = data.get('mappings', {})
        for action_name, mapping_data in mappings_data.items():
            mapping = ActionMapping.from_dict(mapping_data)
            profile.add_mapping(mapping)
        
        return profile
    
    def save_to_file(self, filepath: str) -> None:
        """Save profile to a JSON file.
        
        Args:
            filepath (str): Path to save file
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            raise InputMappingError(self.name, "save_to_file", e)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'InputProfile':
        """Load profile from a JSON file.
        
        Args:
            filepath (str): Path to load file
            
        Returns:
            InputProfile: Loaded profile
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            raise InputMappingError(filepath, "load_from_file", e)


class InputMapping:
    """Main input mapping manager that handles profiles and action resolution."""
    
    def __init__(self):
        """Initialize input mapping manager."""
        self.profiles: Dict[str, InputProfile] = {}
        self.active_profile: Optional[InputProfile] = None
        self.profile_stack: List[InputProfile] = []  # For temporary profile overlays
        
        # Create default profile
        self._create_default_profile()
    
    def add_profile(self, profile: InputProfile) -> None:
        """Add an input profile.
        
        Args:
            profile (InputProfile): Profile to add
        """
        self.profiles[profile.name] = profile
        
        # Set as active if it's the first profile
        if self.active_profile is None:
            self.active_profile = profile
    
    def remove_profile(self, name: str) -> bool:
        """Remove an input profile.
        
        Args:
            name (str): Name of profile to remove
            
        Returns:
            bool: True if profile was removed
        """
        if name in self.profiles:
            profile = self.profiles[name]
            del self.profiles[name]
            
            # Switch to default if removing active profile
            if self.active_profile == profile:
                self.active_profile = self.profiles.get('default')
            
            return True
        return False
    
    def get_profile(self, name: str) -> Optional[InputProfile]:
        """Get an input profile by name.
        
        Args:
            name (str): Profile name
            
        Returns:
            InputProfile: Profile if found, None otherwise
        """
        return self.profiles.get(name)
    
    def set_active_profile(self, name: str) -> bool:
        """Set the active input profile.
        
        Args:
            name (str): Name of profile to activate
            
        Returns:
            bool: True if profile was activated
        """
        profile = self.profiles.get(name)
        if profile:
            self.active_profile = profile
            return True
        return False
    
    def push_profile(self, profile: InputProfile) -> None:
        """Push a profile onto the profile stack for temporary use.
        
        Args:
            profile (InputProfile): Profile to push
        """
        self.profile_stack.append(profile)
    
    def pop_profile(self) -> Optional[InputProfile]:
        """Pop the top profile from the profile stack.
        
        Returns:
            InputProfile: Popped profile, or None if stack is empty
        """
        if self.profile_stack:
            return self.profile_stack.pop()
        return None
    
    def get_actions_for_event(self, event: InputEvent) -> List[str]:
        """Get all actions that match an input event.
        
        Args:
            event (InputEvent): Input event to check
            
        Returns:
            List[str]: List of matching action names
        """
        actions = []
        
        # Check profile stack first (most recent first)
        for profile in reversed(self.profile_stack):
            profile_actions = profile.get_actions_for_event(event)
            actions.extend(profile_actions)
        
        # Check active profile if no stack matches
        if not actions and self.active_profile:
            actions = self.active_profile.get_actions_for_event(event)
        
        return actions
    
    def _create_default_profile(self) -> None:
        """Create the default input profile with standard bindings."""
        default_profile = InputProfile("default", "Default input mappings")
        
        # Movement mappings
        default_profile.add_mapping(ActionMapping(
            InputAction.MOVE_UP,
            [KeyBinding(key="up"), KeyBinding(key="k"), KeyBinding(key="8")]
        ))
        default_profile.add_mapping(ActionMapping(
            InputAction.MOVE_DOWN,
            [KeyBinding(key="down"), KeyBinding(key="j"), KeyBinding(key="2")]
        ))
        default_profile.add_mapping(ActionMapping(
            InputAction.MOVE_LEFT,
            [KeyBinding(key="left"), KeyBinding(key="h"), KeyBinding(key="4")]
        ))
        default_profile.add_mapping(ActionMapping(
            InputAction.MOVE_RIGHT,
            [KeyBinding(key="right"), KeyBinding(key="l"), KeyBinding(key="6")]
        ))
        
        # Diagonal movement
        default_profile.add_mapping(ActionMapping(
            InputAction.MOVE_NORTHWEST,
            [KeyBinding(key="y"), KeyBinding(key="7")]
        ))
        default_profile.add_mapping(ActionMapping(
            InputAction.MOVE_NORTHEAST,
            [KeyBinding(key="u"), KeyBinding(key="9")]
        ))
        default_profile.add_mapping(ActionMapping(
            InputAction.MOVE_SOUTHWEST,
            [KeyBinding(key="b"), KeyBinding(key="1")]
        ))
        default_profile.add_mapping(ActionMapping(
            InputAction.MOVE_SOUTHEAST,
            [KeyBinding(key="n"), KeyBinding(key="3")]
        ))
        
        # Action mappings
        default_profile.add_mapping(ActionMapping(
            InputAction.CONFIRM,
            [KeyBinding(key="enter"), KeyBinding(key="space")]
        ))
        default_profile.add_mapping(ActionMapping(
            InputAction.CANCEL,
            [KeyBinding(key="escape")]
        ))
        default_profile.add_mapping(ActionMapping(
            InputAction.SHOW_CHARACTER,
            [KeyBinding(key="c")]
        ))
        default_profile.add_mapping(ActionMapping(
            InputAction.QUIT,
            [KeyBinding(key="q")]
        ))
        
        self.add_profile(default_profile)
