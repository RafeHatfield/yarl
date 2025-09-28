"""Comprehensive tests for the input system.

This module contains tests for all components of the input system
including events, backends, mapping, state management, and the
main input manager.
"""

import pytest
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from input import (
    InputManager, get_input_manager, initialize_input_manager,
    InputBackend, InputCapabilities, NullInputBackend,
    InputEvent, InputEventType, KeyEvent, MouseEvent, GamepadEvent,
    InputModifiers, MouseButton, GamepadButton, GamepadAxis,
    InputMapping, ActionMapping, InputProfile, KeyBinding, MouseBinding,
    InputAction, InputTrigger, InputState, InputStateManager,
    InputSequence, InputCombo, InputSequenceStep,
    create_key_event, create_mouse_event, create_gamepad_event,
    InputError, InputBackendError, InputMappingError
)


class TestInputEvents:
    """Test cases for input event classes."""
    
    def test_key_event_creation(self):
        """Test key event creation."""
        event = create_key_event(
            InputEventType.KEY_DOWN,
            "a",
            InputModifiers.CTRL,
            key_code=65,
            unicode="A"
        )
        
        assert event.event_type == InputEventType.KEY_DOWN
        assert event.key == "a"
        assert event.modifiers == InputModifiers.CTRL
        assert event.key_code == 65
        assert event.unicode == "A"
        assert not event.repeat
        assert not event.consumed
    
    def test_key_event_serialization(self):
        """Test key event serialization."""
        event = create_key_event(InputEventType.KEY_DOWN, "space")
        
        # Test to_dict
        data = event.to_dict()
        assert data['event_type'] == 'KEY_DOWN'
        assert data['key'] == 'space'
        
        # Test from_dict
        restored = KeyEvent.from_dict(data)
        assert restored.event_type == event.event_type
        assert restored.key == event.key
    
    def test_mouse_event_creation(self):
        """Test mouse event creation."""
        event = create_mouse_event(
            InputEventType.MOUSE_DOWN,
            x=100, y=200,
            button=MouseButton.LEFT,
            delta_x=5, delta_y=-3
        )
        
        assert event.event_type == InputEventType.MOUSE_DOWN
        assert event.x == 100
        assert event.y == 200
        assert event.button == MouseButton.LEFT
        assert event.delta_x == 5
        assert event.delta_y == -3
    
    def test_gamepad_event_creation(self):
        """Test gamepad event creation."""
        event = create_gamepad_event(
            InputEventType.GAMEPAD_BUTTON_DOWN,
            gamepad_id=1,
            button=GamepadButton.A,
            value=1.0
        )
        
        assert event.event_type == InputEventType.GAMEPAD_BUTTON_DOWN
        assert event.gamepad_id == 1
        assert event.button == GamepadButton.A
        assert event.value == 1.0
    
    def test_event_consumption(self):
        """Test event consumption mechanism."""
        event = create_key_event(InputEventType.KEY_DOWN, "escape")
        
        assert not event.is_consumed()
        event.consume()
        assert event.is_consumed()
    
    def test_input_modifiers(self):
        """Test input modifier flags."""
        # Test individual modifiers
        assert InputModifiers.CTRL != InputModifiers.NONE
        assert InputModifiers.SHIFT != InputModifiers.NONE
        
        # Test modifier combinations
        combo = InputModifiers.CTRL | InputModifiers.SHIFT
        assert combo & InputModifiers.CTRL
        assert combo & InputModifiers.SHIFT
        assert not (combo & InputModifiers.ALT)
    
    def test_key_event_string_representation(self):
        """Test key event string representation."""
        # Simple key
        event = KeyEvent(InputEventType.KEY_DOWN, 0.0, key="a")
        assert str(event) == "a"
        
        # Key with modifiers
        event = KeyEvent(
            InputEventType.KEY_DOWN, 0.0,
            key="c",
            modifiers=InputModifiers.CTRL | InputModifiers.SHIFT
        )
        assert "Ctrl" in str(event)
        assert "Shift" in str(event)
        assert "c" in str(event)


class TestInputBackend:
    """Test cases for input backend classes."""
    
    def test_null_backend_creation(self):
        """Test null backend creation."""
        backend = NullInputBackend()
        assert backend.name == "null"
        assert backend.capabilities == InputCapabilities.NONE
        assert not backend.initialized
    
    def test_null_backend_initialization(self):
        """Test null backend initialization."""
        backend = NullInputBackend()
        
        assert backend.initialize()
        assert backend.initialized
        
        backend.shutdown()
        assert not backend.initialized
    
    def test_null_backend_operations(self):
        """Test null backend operations."""
        backend = NullInputBackend()
        backend.initialize()
        
        # Should return empty/false for all operations
        assert backend.poll_events() == []
        assert backend.get_devices() == []
        assert not backend.is_key_pressed("a")
        assert not backend.is_mouse_button_pressed("left")
        assert backend.get_mouse_position() == (0, 0)
    
    def test_backend_capabilities(self):
        """Test backend capability checking."""
        backend = NullInputBackend()
        
        assert not backend.has_capability(InputCapabilities.KEYBOARD)
        assert not backend.has_capability(InputCapabilities.MOUSE)
        assert backend.has_capability(InputCapabilities.NONE)
    
    def test_backend_callbacks(self):
        """Test backend event callbacks."""
        backend = NullInputBackend()
        callback_called = []
        
        def test_callback(event):
            callback_called.append(event)
        
        backend.add_event_callback(test_callback)
        
        # Simulate event notification
        test_event = create_key_event(InputEventType.KEY_DOWN, "test")
        backend._notify_event_callbacks(test_event)
        
        assert len(callback_called) == 1
        assert callback_called[0] == test_event
        
        # Remove callback
        backend.remove_event_callback(test_callback)
        backend._notify_event_callbacks(test_event)
        
        # Should still be 1 (callback was removed)
        assert len(callback_called) == 1


class TestInputMapping:
    """Test cases for input mapping classes."""
    
    def test_key_binding_creation(self):
        """Test key binding creation."""
        binding = KeyBinding(
            key="a",
            trigger=InputTrigger.PRESS,
            modifiers=InputModifiers.CTRL
        )
        
        assert binding.key == "a"
        assert binding.trigger == InputTrigger.PRESS
        assert binding.modifiers == InputModifiers.CTRL
        assert binding.enabled
    
    def test_key_binding_matching(self):
        """Test key binding event matching."""
        binding = KeyBinding(key="space", trigger=InputTrigger.PRESS)
        
        # Should match
        matching_event = create_key_event(InputEventType.KEY_DOWN, "space")
        assert binding.matches(matching_event)
        
        # Should not match (wrong key)
        wrong_key_event = create_key_event(InputEventType.KEY_DOWN, "enter")
        assert not binding.matches(wrong_key_event)
        
        # Should not match (wrong event type)
        wrong_type_event = create_key_event(InputEventType.KEY_UP, "space")
        assert not binding.matches(wrong_type_event)
    
    def test_key_binding_serialization(self):
        """Test key binding serialization."""
        binding = KeyBinding(
            key="ctrl",
            trigger=InputTrigger.HOLD,
            modifiers=InputModifiers.SHIFT
        )
        
        # Test to_dict
        data = binding.to_dict()
        assert data['type'] == 'key'
        assert data['key'] == 'ctrl'
        assert data['trigger'] == 'HOLD'
        
        # Test from_dict
        restored = KeyBinding.from_dict(data)
        assert restored.key == binding.key
        assert restored.trigger == binding.trigger
        assert restored.modifiers == binding.modifiers
    
    def test_mouse_binding_creation(self):
        """Test mouse binding creation."""
        binding = MouseBinding(
            button=MouseButton.RIGHT,
            trigger=InputTrigger.PRESS
        )
        
        assert binding.button == MouseButton.RIGHT
        assert binding.trigger == InputTrigger.PRESS
    
    def test_mouse_binding_matching(self):
        """Test mouse binding event matching."""
        binding = MouseBinding(button=MouseButton.LEFT, trigger=InputTrigger.PRESS)
        
        # Should match
        matching_event = create_mouse_event(
            InputEventType.MOUSE_DOWN,
            button=MouseButton.LEFT
        )
        assert binding.matches(matching_event)
        
        # Should not match (wrong button)
        wrong_button_event = create_mouse_event(
            InputEventType.MOUSE_DOWN,
            button=MouseButton.RIGHT
        )
        assert not binding.matches(wrong_button_event)
    
    def test_action_mapping_creation(self):
        """Test action mapping creation."""
        key_binding = KeyBinding(key="w")
        mouse_binding = MouseBinding(button=MouseButton.LEFT)
        
        mapping = ActionMapping(
            action=InputAction.MOVE_UP,
            bindings=[key_binding, mouse_binding],
            description="Move character up"
        )
        
        assert mapping.action == InputAction.MOVE_UP
        assert len(mapping.bindings) == 2
        assert mapping.description == "Move character up"
        assert mapping.enabled
    
    def test_action_mapping_event_matching(self):
        """Test action mapping event matching."""
        mapping = ActionMapping(
            action=InputAction.CONFIRM,
            bindings=[
                KeyBinding(key="enter"),
                KeyBinding(key="space"),
                MouseBinding(button=MouseButton.LEFT)
            ]
        )
        
        # Should match any of the bindings
        enter_event = create_key_event(InputEventType.KEY_DOWN, "enter")
        assert mapping.matches(enter_event)
        
        space_event = create_key_event(InputEventType.KEY_DOWN, "space")
        assert mapping.matches(space_event)
        
        mouse_event = create_mouse_event(
            InputEventType.MOUSE_DOWN,
            button=MouseButton.LEFT
        )
        assert mapping.matches(mouse_event)
        
        # Should not match unbound events
        unbound_event = create_key_event(InputEventType.KEY_DOWN, "x")
        assert not mapping.matches(unbound_event)
    
    def test_input_profile_creation(self):
        """Test input profile creation."""
        profile = InputProfile("test_profile", "Test profile description")
        
        assert profile.name == "test_profile"
        assert profile.description == "Test profile description"
        assert profile.enabled
        assert len(profile.mappings) == 0
    
    def test_input_profile_mapping_management(self):
        """Test input profile mapping management."""
        profile = InputProfile("test")
        
        # Add mapping
        mapping = ActionMapping(
            action=InputAction.MOVE_UP,
            bindings=[KeyBinding(key="w")]
        )
        profile.add_mapping(mapping)
        
        assert len(profile.mappings) == 1
        assert profile.get_mapping(InputAction.MOVE_UP) == mapping
        
        # Remove mapping
        removed = profile.remove_mapping(InputAction.MOVE_UP)
        assert removed
        assert len(profile.mappings) == 0
        assert profile.get_mapping(InputAction.MOVE_UP) is None
    
    def test_input_profile_event_matching(self):
        """Test input profile event matching."""
        profile = InputProfile("test")
        
        # Add some mappings
        profile.add_mapping(ActionMapping(
            action=InputAction.MOVE_UP,
            bindings=[KeyBinding(key="w")]
        ))
        profile.add_mapping(ActionMapping(
            action=InputAction.ATTACK,
            bindings=[KeyBinding(key="space")]
        ))
        
        # Test event matching
        w_event = create_key_event(InputEventType.KEY_DOWN, "w")
        actions = profile.get_actions_for_event(w_event)
        assert "move_up" in actions
        
        space_event = create_key_event(InputEventType.KEY_DOWN, "space")
        actions = profile.get_actions_for_event(space_event)
        assert "attack" in actions
        
        # Test no match
        x_event = create_key_event(InputEventType.KEY_DOWN, "x")
        actions = profile.get_actions_for_event(x_event)
        assert len(actions) == 0
    
    def test_input_profile_serialization(self):
        """Test input profile serialization."""
        profile = InputProfile("test_profile", "Test description")
        
        # Add a mapping
        mapping = ActionMapping(
            action=InputAction.CONFIRM,
            bindings=[KeyBinding(key="enter")]
        )
        profile.add_mapping(mapping)
        
        # Test serialization
        data = profile.to_dict()
        assert data['name'] == "test_profile"
        assert data['description'] == "Test description"
        assert 'mappings' in data
        assert 'confirm' in data['mappings']
        
        # Test deserialization
        restored = InputProfile.from_dict(data)
        assert restored.name == profile.name
        assert restored.description == profile.description
        assert len(restored.mappings) == 1
        assert restored.get_mapping(InputAction.CONFIRM) is not None
    
    def test_input_mapping_manager(self):
        """Test input mapping manager."""
        mapping_manager = InputMapping()
        
        # Should have default profile
        assert mapping_manager.active_profile is not None
        assert mapping_manager.active_profile.name == "default"
        
        # Test profile management
        custom_profile = InputProfile("custom", "Custom profile")
        mapping_manager.add_profile(custom_profile)
        
        assert mapping_manager.get_profile("custom") == custom_profile
        
        # Test profile switching
        switched = mapping_manager.set_active_profile("custom")
        assert switched
        assert mapping_manager.active_profile == custom_profile


class TestInputState:
    """Test cases for input state management."""
    
    def test_input_state_manager_creation(self):
        """Test input state manager creation."""
        state_manager = InputStateManager()
        
        assert len(state_manager.key_states) == 0
        assert state_manager.mouse_state is not None
        assert len(state_manager.gamepad_states) == 0
    
    def test_key_state_tracking(self):
        """Test keyboard state tracking."""
        state_manager = InputStateManager()
        
        # Process key down event
        key_down = create_key_event(InputEventType.KEY_DOWN, "a")
        state_manager.process_event(key_down)
        
        assert state_manager.is_key_just_pressed("a")
        assert state_manager.is_key_pressed("a")
        
        # Update frame (converts PRESSED to DOWN)
        state_manager.update_frame()
        
        assert not state_manager.is_key_just_pressed("a")
        assert state_manager.is_key_pressed("a")
        
        # Process key up event
        key_up = create_key_event(InputEventType.KEY_UP, "a")
        state_manager.process_event(key_up)
        
        assert state_manager.is_key_just_released("a")
        assert not state_manager.is_key_pressed("a")
    
    def test_mouse_state_tracking(self):
        """Test mouse state tracking."""
        state_manager = InputStateManager()
        
        # Process mouse move
        mouse_move = create_mouse_event(
            InputEventType.MOUSE_MOVE,
            x=100, y=200,
            delta_x=10, delta_y=20
        )
        state_manager.process_event(mouse_move)
        
        assert state_manager.get_mouse_position() == (100, 200)
        assert state_manager.get_mouse_delta() == (10, 20)
        
        # Process mouse button
        mouse_down = create_mouse_event(
            InputEventType.MOUSE_DOWN,
            button=MouseButton.LEFT
        )
        state_manager.process_event(mouse_down)
        
        assert state_manager.mouse_state.is_button_just_pressed(MouseButton.LEFT)
        assert state_manager.mouse_state.is_button_pressed(MouseButton.LEFT)
    
    def test_input_sequence_creation(self):
        """Test input sequence creation."""
        steps = [
            InputSequenceStep(key="up"),
            InputSequenceStep(key="up"),
            InputSequenceStep(key="down"),
            InputSequenceStep(key="down"),
        ]
        
        sequence = InputSequence("konami_start", steps, timeout=2.0)
        
        assert sequence.name == "konami_start"
        assert len(sequence.steps) == 4
        assert sequence.timeout == 2.0
        assert not sequence.active
        assert not sequence.completed
    
    def test_input_sequence_processing(self):
        """Test input sequence processing."""
        steps = [
            InputSequenceStep(key="a"),
            InputSequenceStep(key="b"),
            InputSequenceStep(key="c"),
        ]
        
        sequence = InputSequence("abc", steps)
        
        # Process correct sequence
        a_event = create_key_event(InputEventType.KEY_DOWN, "a")
        assert not sequence.process_event(a_event)
        assert sequence.active
        assert sequence.current_step == 1
        
        b_event = create_key_event(InputEventType.KEY_DOWN, "b")
        assert not sequence.process_event(b_event)
        assert sequence.current_step == 2
        
        c_event = create_key_event(InputEventType.KEY_DOWN, "c")
        assert sequence.process_event(c_event)  # Should complete
        assert sequence.completed
    
    def test_input_combo_creation(self):
        """Test input combo creation."""
        combo = InputCombo(
            "ctrl_c",
            keys=["c"],
            modifiers=InputModifiers.CTRL
        )
        
        assert combo.name == "ctrl_c"
        assert combo.keys == ["c"]
        assert combo.modifiers == InputModifiers.CTRL
        assert not combo.active
    
    def test_input_combo_checking(self):
        """Test input combo state checking."""
        combo = InputCombo("ctrl_shift_s", keys=["s"], modifiers=InputModifiers.CTRL | InputModifiers.SHIFT)
        
        # Create mock states
        key_states = {
            "s": Mock(is_pressed=Mock(return_value=True), modifiers=InputModifiers.CTRL | InputModifiers.SHIFT)
        }
        mouse_state = Mock()
        gamepad_states = {}
        
        # Should be active
        assert combo.check_state(key_states, mouse_state, gamepad_states)
        assert combo.active
        
        # Change key state
        key_states["s"].is_pressed.return_value = False
        
        # Should not be active
        assert not combo.check_state(key_states, mouse_state, gamepad_states)
        assert not combo.active


class TestInputManager:
    """Test cases for input manager."""
    
    def test_input_manager_creation(self):
        """Test input manager creation."""
        manager = InputManager(auto_detect_backend=False)
        
        assert manager.backend is not None
        assert manager.mapping is not None
        assert manager.state_manager is not None
        assert manager.enabled
    
    def test_backend_management(self):
        """Test input backend management."""
        manager = InputManager(auto_detect_backend=False)
        
        # Should start with null backend
        assert manager.backend.name == "null"
        
        # Test backend switching
        available = manager.get_available_backends()
        assert "null" in available
        
        # Set backend
        success = manager.set_backend("null")
        assert success
        assert manager.backend.name == "null"
    
    def test_event_processing(self):
        """Test event processing."""
        manager = InputManager(auto_detect_backend=False)
        manager.set_backend("null")
        
        # Mock the backend to return events
        test_event = create_key_event(InputEventType.KEY_DOWN, "test")
        manager.backend.poll_events = Mock(return_value=[test_event])
        
        # Process events
        actions = manager.process_events()
        
        # Should have processed the event
        manager.backend.poll_events.assert_called_once()
    
    def test_action_callbacks(self):
        """Test action callbacks."""
        manager = InputManager(auto_detect_backend=False)
        
        callback_called = []
        
        def test_callback(action):
            callback_called.append(action)
        
        # Add callback
        manager.add_action_callback(InputAction.MOVE_UP, test_callback)
        
        # Trigger action manually
        manager._notify_action_callbacks("move_up")
        
        assert len(callback_called) == 1
        assert callback_called[0] == "move_up"
        
        # Remove callback
        manager.remove_action_callback(InputAction.MOVE_UP, test_callback)
        manager._notify_action_callbacks("move_up")
        
        # Should still be 1 (callback was removed)
        assert len(callback_called) == 1
    
    def test_input_profile_management(self):
        """Test input profile management."""
        manager = InputManager(auto_detect_backend=False)
        
        # Should have default profile
        profile = manager.get_input_profile()
        assert profile is not None
        assert profile.name == "default"
        
        # Test profile switching
        custom_profile = InputProfile("custom", "Custom profile")
        manager.mapping.add_profile(custom_profile)
        
        success = manager.set_input_profile("custom")
        assert success
        assert manager.get_input_profile().name == "custom"
    
    def test_capabilities(self):
        """Test capability checking."""
        manager = InputManager(auto_detect_backend=False)
        manager.set_backend("null")
        
        capabilities = manager.get_capabilities()
        assert capabilities == InputCapabilities.NONE
        
        assert not manager.has_capability(InputCapabilities.KEYBOARD)
        assert not manager.has_capability(InputCapabilities.MOUSE)
    
    def test_status_reporting(self):
        """Test status reporting."""
        manager = InputManager(auto_detect_backend=False)
        
        status = manager.get_status()
        
        assert 'enabled' in status
        assert 'backend' in status
        assert 'backend_initialized' in status
        assert 'active_profile' in status
        assert 'available_backends' in status
        assert 'capabilities' in status
    
    def test_enable_disable(self):
        """Test enabling/disabling input processing."""
        manager = InputManager(auto_detect_backend=False)
        
        assert manager.enabled
        
        manager.disable()
        assert not manager.enabled
        
        manager.enable()
        assert manager.enabled
    
    def test_shutdown(self):
        """Test input manager shutdown."""
        manager = InputManager(auto_detect_backend=False)
        manager.set_backend("null")
        
        assert manager.backend.initialized
        
        manager.shutdown()
        
        assert not manager.enabled
        assert not manager.backend.initialized


class TestGlobalFunctions:
    """Test cases for global functions."""
    
    def test_get_input_manager(self):
        """Test getting global input manager."""
        manager1 = get_input_manager()
        manager2 = get_input_manager()
        
        # Should be singleton
        assert manager1 is manager2
    
    def test_initialize_input_manager(self):
        """Test initializing input manager with custom settings."""
        manager = initialize_input_manager(
            preferred_backend="null",
            auto_detect_backend=False
        )
        
        assert manager.preferred_backend == "null"
        assert not manager.auto_detect_backend


class TestInputExceptions:
    """Test cases for input exceptions."""
    
    def test_input_error(self):
        """Test base input error."""
        error = InputError("Test error", "test_backend", "test_context")
        
        assert str(error) == "Test error | Backend: test_backend | Context: test_context"
        assert error.backend == "test_backend"
        assert error.context == "test_context"
    
    def test_input_backend_error(self):
        """Test input backend error."""
        cause = ValueError("Test cause")
        error = InputBackendError("test_backend", "initialize", cause)
        
        assert "Input backend operation failed" in str(error)
        assert "initialize" in str(error)
        assert error.operation == "initialize"
        assert error.cause == cause
    
    def test_input_mapping_error(self):
        """Test input mapping error."""
        error = InputMappingError("test_mapping", "test_action")
        
        assert "Input mapping error" in str(error)
        assert "test_mapping" in str(error)
        assert error.mapping_name == "test_mapping"
        assert error.action == "test_action"
