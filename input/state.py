"""Input state management for tracking input states and sequences.

This module provides functionality for tracking the current state of
input devices, detecting input sequences and combinations, and managing
complex input patterns.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import time

from .events import (
    InputEvent, InputEventType, KeyEvent, MouseEvent, GamepadEvent,
    InputModifiers, MouseButton, GamepadButton, GamepadAxis
)


class InputState(Enum):
    """Input state values."""
    
    UP = auto()      # Input is not pressed
    DOWN = auto()    # Input is pressed
    PRESSED = auto() # Input was just pressed this frame
    RELEASED = auto() # Input was just released this frame


@dataclass
class KeyState:
    """State information for a keyboard key."""
    
    key: str
    state: InputState = InputState.UP
    press_time: float = 0.0
    release_time: float = 0.0
    repeat_count: int = 0
    modifiers: InputModifiers = InputModifiers.NONE
    
    def is_pressed(self) -> bool:
        """Check if key is currently pressed."""
        return self.state in (InputState.DOWN, InputState.PRESSED)
    
    def is_just_pressed(self) -> bool:
        """Check if key was just pressed this frame."""
        return self.state == InputState.PRESSED
    
    def is_just_released(self) -> bool:
        """Check if key was just released this frame."""
        return self.state == InputState.RELEASED
    
    def get_hold_duration(self) -> float:
        """Get how long the key has been held."""
        if self.is_pressed() and self.press_time > 0:
            return time.time() - self.press_time
        return 0.0


@dataclass
class MouseState:
    """State information for mouse input."""
    
    x: int = 0
    y: int = 0
    delta_x: int = 0
    delta_y: int = 0
    wheel_delta: float = 0.0
    buttons: Dict[MouseButton, InputState] = field(default_factory=dict)
    button_press_times: Dict[MouseButton, float] = field(default_factory=dict)
    
    def is_button_pressed(self, button: MouseButton) -> bool:
        """Check if mouse button is currently pressed."""
        state = self.buttons.get(button, InputState.UP)
        return state in (InputState.DOWN, InputState.PRESSED)
    
    def is_button_just_pressed(self, button: MouseButton) -> bool:
        """Check if mouse button was just pressed this frame."""
        return self.buttons.get(button, InputState.UP) == InputState.PRESSED
    
    def is_button_just_released(self, button: MouseButton) -> bool:
        """Check if mouse button was just released this frame."""
        return self.buttons.get(button, InputState.UP) == InputState.RELEASED
    
    def get_button_hold_duration(self, button: MouseButton) -> float:
        """Get how long a mouse button has been held."""
        if self.is_button_pressed(button):
            press_time = self.button_press_times.get(button, 0.0)
            if press_time > 0:
                return time.time() - press_time
        return 0.0


@dataclass
class GamepadState:
    """State information for gamepad input."""
    
    gamepad_id: int = 0
    connected: bool = False
    buttons: Dict[GamepadButton, InputState] = field(default_factory=dict)
    button_values: Dict[GamepadButton, float] = field(default_factory=dict)
    axes: Dict[GamepadAxis, float] = field(default_factory=dict)
    button_press_times: Dict[GamepadButton, float] = field(default_factory=dict)
    
    def is_button_pressed(self, button: GamepadButton) -> bool:
        """Check if gamepad button is currently pressed."""
        state = self.buttons.get(button, InputState.UP)
        return state in (InputState.DOWN, InputState.PRESSED)
    
    def is_button_just_pressed(self, button: GamepadButton) -> bool:
        """Check if gamepad button was just pressed this frame."""
        return self.buttons.get(button, InputState.UP) == InputState.PRESSED
    
    def is_button_just_released(self, button: GamepadButton) -> bool:
        """Check if gamepad button was just released this frame."""
        return self.buttons.get(button, InputState.UP) == InputState.RELEASED
    
    def get_button_value(self, button: GamepadButton) -> float:
        """Get analog value for a button (0.0-1.0)."""
        return self.button_values.get(button, 0.0)
    
    def get_axis_value(self, axis: GamepadAxis) -> float:
        """Get value for an axis (-1.0 to 1.0)."""
        return self.axes.get(axis, 0.0)
    
    def get_button_hold_duration(self, button: GamepadButton) -> float:
        """Get how long a gamepad button has been held."""
        if self.is_button_pressed(button):
            press_time = self.button_press_times.get(button, 0.0)
            if press_time > 0:
                return time.time() - press_time
        return 0.0


@dataclass
class InputSequenceStep:
    """A single step in an input sequence."""
    
    key: Optional[str] = None
    button: Optional[MouseButton] = None
    gamepad_button: Optional[GamepadButton] = None
    modifiers: InputModifiers = InputModifiers.NONE
    max_delay: float = 1.0  # Maximum time between this and next step
    
    def matches(self, event: InputEvent) -> bool:
        """Check if this step matches an input event."""
        if isinstance(event, KeyEvent) and self.key:
            return (event.key == self.key and 
                   event.modifiers == self.modifiers and
                   event.event_type == InputEventType.KEY_DOWN)
        elif isinstance(event, MouseEvent) and self.button:
            return (event.button == self.button and
                   event.modifiers == self.modifiers and
                   event.event_type == InputEventType.MOUSE_DOWN)
        elif isinstance(event, GamepadEvent) and self.gamepad_button:
            return (event.button == self.gamepad_button and
                   event.event_type == InputEventType.GAMEPAD_BUTTON_DOWN)
        
        return False


class InputSequence:
    """Represents a sequence of input events that trigger an action."""
    
    def __init__(self, name: str, steps: List[InputSequenceStep], 
                 timeout: float = 5.0):
        """Initialize input sequence.
        
        Args:
            name (str): Sequence name
            steps (List[InputSequenceStep]): Sequence steps
            timeout (float): Total timeout for sequence completion
        """
        self.name = name
        self.steps = steps
        self.timeout = timeout
        self.current_step = 0
        self.start_time = 0.0
        self.last_step_time = 0.0
        self.completed = False
        self.active = False
    
    def reset(self) -> None:
        """Reset sequence to initial state."""
        self.current_step = 0
        self.start_time = 0.0
        self.last_step_time = 0.0
        self.completed = False
        self.active = False
    
    def process_event(self, event: InputEvent) -> bool:
        """Process an input event for this sequence.
        
        Args:
            event (InputEvent): Input event to process
            
        Returns:
            bool: True if sequence was completed
        """
        current_time = time.time()
        
        # Check if sequence has timed out
        if self.active and (current_time - self.start_time) > self.timeout:
            self.reset()
            return False
        
        # Check if current step matches
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            
            if step.matches(event):
                if not self.active:
                    # Starting sequence
                    self.active = True
                    self.start_time = current_time
                
                self.current_step += 1
                self.last_step_time = current_time
                
                # Check if sequence is complete
                if self.current_step >= len(self.steps):
                    self.completed = True
                    return True
            else:
                # Wrong input, check if we need to reset or if this could start the sequence
                if self.active:
                    # Check if this event could start the sequence over
                    if self.steps[0].matches(event):
                        self.reset()
                        self.active = True
                        self.start_time = current_time
                        self.current_step = 1
                        self.last_step_time = current_time
                    else:
                        self.reset()
                elif self.steps[0].matches(event):
                    # Starting sequence
                    self.active = True
                    self.start_time = current_time
                    self.current_step = 1
                    self.last_step_time = current_time
        
        return False
    
    def is_completed(self) -> bool:
        """Check if sequence is completed."""
        return self.completed
    
    def get_progress(self) -> float:
        """Get sequence completion progress (0.0-1.0)."""
        if not self.steps:
            return 0.0
        return self.current_step / len(self.steps)


class InputCombo:
    """Represents a combination of inputs that must be held simultaneously."""
    
    def __init__(self, name: str, keys: List[str] = None, 
                 mouse_buttons: List[MouseButton] = None,
                 gamepad_buttons: List[GamepadButton] = None,
                 modifiers: InputModifiers = InputModifiers.NONE):
        """Initialize input combo.
        
        Args:
            name (str): Combo name
            keys (List[str], optional): Required keys
            mouse_buttons (List[MouseButton], optional): Required mouse buttons
            gamepad_buttons (List[GamepadButton], optional): Required gamepad buttons
            modifiers (InputModifiers): Required modifier keys
        """
        self.name = name
        self.keys = keys or []
        self.mouse_buttons = mouse_buttons or []
        self.gamepad_buttons = gamepad_buttons or []
        self.modifiers = modifiers
        self.active = False
        self.activation_time = 0.0
    
    def check_state(self, key_states: Dict[str, KeyState],
                   mouse_state: MouseState,
                   gamepad_states: Dict[int, GamepadState]) -> bool:
        """Check if combo is currently active.
        
        Args:
            key_states (Dict[str, KeyState]): Current key states
            mouse_state (MouseState): Current mouse state
            gamepad_states (Dict[int, GamepadState]): Current gamepad states
            
        Returns:
            bool: True if combo is active
        """
        # Check required keys
        for key in self.keys:
            key_state = key_states.get(key)
            if not key_state or not key_state.is_pressed():
                self.active = False
                return False
            
            # Check modifiers match
            if key_state.modifiers != self.modifiers:
                self.active = False
                return False
        
        # Check required mouse buttons
        for button in self.mouse_buttons:
            if not mouse_state.is_button_pressed(button):
                self.active = False
                return False
        
        # Check required gamepad buttons
        for button in self.gamepad_buttons:
            found = False
            for gamepad_state in gamepad_states.values():
                if gamepad_state.connected and gamepad_state.is_button_pressed(button):
                    found = True
                    break
            if not found:
                self.active = False
                return False
        
        # All requirements met
        if not self.active:
            self.active = True
            self.activation_time = time.time()
        
        return True
    
    def get_hold_duration(self) -> float:
        """Get how long combo has been held."""
        if self.active and self.activation_time > 0:
            return time.time() - self.activation_time
        return 0.0


class InputStateManager:
    """Manages the current state of all input devices."""
    
    def __init__(self):
        """Initialize input state manager."""
        self.key_states: Dict[str, KeyState] = {}
        self.mouse_state = MouseState()
        self.gamepad_states: Dict[int, GamepadState] = {}
        
        # Sequence and combo tracking
        self.sequences: Dict[str, InputSequence] = {}
        self.combos: Dict[str, InputCombo] = {}
        
        # Event callbacks
        self.sequence_callbacks: List[Callable[[str], None]] = []
        self.combo_callbacks: List[Callable[[str, bool], None]] = []
        
        # Configuration
        self.double_click_time = 0.3  # Maximum time between clicks for double-click
        self.long_press_time = 0.5    # Minimum time for long press
    
    def process_event(self, event: InputEvent) -> None:
        """Process an input event and update states.
        
        Args:
            event (InputEvent): Input event to process
        """
        if isinstance(event, KeyEvent):
            self._process_key_event(event)
        elif isinstance(event, MouseEvent):
            self._process_mouse_event(event)
        elif isinstance(event, GamepadEvent):
            self._process_gamepad_event(event)
        
        # Process sequences
        self._process_sequences(event)
        
        # Update combos
        self._update_combos()
    
    def _process_key_event(self, event: KeyEvent) -> None:
        """Process a keyboard event."""
        key = event.key
        current_time = time.time()
        
        # Get or create key state
        if key not in self.key_states:
            self.key_states[key] = KeyState(key)
        
        key_state = self.key_states[key]
        
        if event.event_type == InputEventType.KEY_DOWN:
            if key_state.state == InputState.UP:
                key_state.state = InputState.PRESSED
                key_state.press_time = current_time
                key_state.repeat_count = 0
            else:
                key_state.repeat_count += 1
            key_state.modifiers = event.modifiers
            
        elif event.event_type == InputEventType.KEY_UP:
            key_state.state = InputState.RELEASED
            key_state.release_time = current_time
            
        elif event.event_type == InputEventType.KEY_REPEAT:
            key_state.repeat_count += 1
    
    def _process_mouse_event(self, event: MouseEvent) -> None:
        """Process a mouse event."""
        current_time = time.time()
        
        # Update position
        if event.event_type == InputEventType.MOUSE_MOVE:
            # Use delta from event if provided, otherwise calculate
            if event.delta_x != 0 or event.delta_y != 0:
                self.mouse_state.delta_x = event.delta_x
                self.mouse_state.delta_y = event.delta_y
            else:
                self.mouse_state.delta_x = event.x - self.mouse_state.x
                self.mouse_state.delta_y = event.y - self.mouse_state.y
            self.mouse_state.x = event.x
            self.mouse_state.y = event.y
        
        # Update wheel
        elif event.event_type == InputEventType.MOUSE_WHEEL:
            self.mouse_state.wheel_delta = event.wheel_delta
        
        # Update button states
        elif event.button and event.event_type in (InputEventType.MOUSE_DOWN, InputEventType.MOUSE_UP):
            button = event.button
            
            if event.event_type == InputEventType.MOUSE_DOWN:
                current_state = self.mouse_state.buttons.get(button, InputState.UP)
                if current_state == InputState.UP:
                    self.mouse_state.buttons[button] = InputState.PRESSED
                    self.mouse_state.button_press_times[button] = current_time
            else:  # MOUSE_UP
                self.mouse_state.buttons[button] = InputState.RELEASED
    
    def _process_gamepad_event(self, event: GamepadEvent) -> None:
        """Process a gamepad event."""
        gamepad_id = event.gamepad_id
        current_time = time.time()
        
        # Get or create gamepad state
        if gamepad_id not in self.gamepad_states:
            self.gamepad_states[gamepad_id] = GamepadState(gamepad_id=gamepad_id)
        
        gamepad_state = self.gamepad_states[gamepad_id]
        
        if event.event_type == InputEventType.GAMEPAD_CONNECTED:
            gamepad_state.connected = True
        elif event.event_type == InputEventType.GAMEPAD_DISCONNECTED:
            gamepad_state.connected = False
        elif event.event_type == InputEventType.GAMEPAD_BUTTON_DOWN and event.button:
            button = event.button
            current_state = gamepad_state.buttons.get(button, InputState.UP)
            if current_state == InputState.UP:
                gamepad_state.buttons[button] = InputState.PRESSED
                gamepad_state.button_press_times[button] = current_time
            gamepad_state.button_values[button] = event.value
        elif event.event_type == InputEventType.GAMEPAD_BUTTON_UP and event.button:
            gamepad_state.buttons[event.button] = InputState.RELEASED
            gamepad_state.button_values[event.button] = event.value
        elif event.event_type == InputEventType.GAMEPAD_AXIS_MOTION and event.axis:
            gamepad_state.axes[event.axis] = event.value
    
    def _process_sequences(self, event: InputEvent) -> None:
        """Process input sequences."""
        for sequence_name, sequence in self.sequences.items():
            if sequence.process_event(event):
                # Sequence completed
                for callback in self.sequence_callbacks:
                    try:
                        callback(sequence_name)
                    except Exception as e:
                        print(f"Sequence callback error: {e}")
                
                # Reset sequence for next use
                sequence.reset()
    
    def _update_combos(self) -> None:
        """Update input combo states."""
        for combo_name, combo in self.combos.items():
            was_active = combo.active
            is_active = combo.check_state(self.key_states, self.mouse_state, self.gamepad_states)
            
            # Notify if combo state changed
            if was_active != is_active:
                for callback in self.combo_callbacks:
                    try:
                        callback(combo_name, is_active)
                    except Exception as e:
                        print(f"Combo callback error: {e}")
    
    def update_frame(self) -> None:
        """Update states for new frame (call once per frame)."""
        # Convert PRESSED to DOWN and RELEASED to UP
        for key_state in self.key_states.values():
            if key_state.state == InputState.PRESSED:
                key_state.state = InputState.DOWN
            elif key_state.state == InputState.RELEASED:
                key_state.state = InputState.UP
        
        # Update mouse button states
        for button in list(self.mouse_state.buttons.keys()):
            state = self.mouse_state.buttons[button]
            if state == InputState.PRESSED:
                self.mouse_state.buttons[button] = InputState.DOWN
            elif state == InputState.RELEASED:
                self.mouse_state.buttons[button] = InputState.UP
        
        # Update gamepad button states
        for gamepad_state in self.gamepad_states.values():
            for button in list(gamepad_state.buttons.keys()):
                state = gamepad_state.buttons[button]
                if state == InputState.PRESSED:
                    gamepad_state.buttons[button] = InputState.DOWN
                elif state == InputState.RELEASED:
                    gamepad_state.buttons[button] = InputState.UP
        
        # Reset mouse deltas and wheel
        self.mouse_state.delta_x = 0
        self.mouse_state.delta_y = 0
        self.mouse_state.wheel_delta = 0.0
    
    def add_sequence(self, sequence: InputSequence) -> None:
        """Add an input sequence to track.
        
        Args:
            sequence (InputSequence): Sequence to add
        """
        self.sequences[sequence.name] = sequence
    
    def remove_sequence(self, name: str) -> bool:
        """Remove an input sequence.
        
        Args:
            name (str): Name of sequence to remove
            
        Returns:
            bool: True if sequence was removed
        """
        if name in self.sequences:
            del self.sequences[name]
            return True
        return False
    
    def add_combo(self, combo: InputCombo) -> None:
        """Add an input combo to track.
        
        Args:
            combo (InputCombo): Combo to add
        """
        self.combos[combo.name] = combo
    
    def remove_combo(self, name: str) -> bool:
        """Remove an input combo.
        
        Args:
            name (str): Name of combo to remove
            
        Returns:
            bool: True if combo was removed
        """
        if name in self.combos:
            del self.combos[name]
            return True
        return False
    
    def is_key_pressed(self, key: str) -> bool:
        """Check if a key is currently pressed."""
        key_state = self.key_states.get(key)
        return key_state.is_pressed() if key_state else False
    
    def is_key_just_pressed(self, key: str) -> bool:
        """Check if a key was just pressed this frame."""
        key_state = self.key_states.get(key)
        return key_state.is_just_pressed() if key_state else False
    
    def is_key_just_released(self, key: str) -> bool:
        """Check if a key was just released this frame."""
        key_state = self.key_states.get(key)
        return key_state.is_just_released() if key_state else False
    
    def get_key_hold_duration(self, key: str) -> float:
        """Get how long a key has been held."""
        key_state = self.key_states.get(key)
        return key_state.get_hold_duration() if key_state else 0.0
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        return (self.mouse_state.x, self.mouse_state.y)
    
    def get_mouse_delta(self) -> Tuple[int, int]:
        """Get mouse movement delta for this frame."""
        return (self.mouse_state.delta_x, self.mouse_state.delta_y)
    
    def add_sequence_callback(self, callback: Callable[[str], None]) -> None:
        """Add callback for sequence completion events."""
        if callback not in self.sequence_callbacks:
            self.sequence_callbacks.append(callback)
    
    def add_combo_callback(self, callback: Callable[[str, bool], None]) -> None:
        """Add callback for combo activation/deactivation events."""
        if callback not in self.combo_callbacks:
            self.combo_callbacks.append(callback)
