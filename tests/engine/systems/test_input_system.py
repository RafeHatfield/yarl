"""Tests for the InputSystem (Refactored - StateManager integration)."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from engine.systems.input_system import InputSystem
from game_states import GameStates
from state_management.state_config import StateManager


class TestInputSystemInitialization:
    """Test InputSystem initialization."""

    def test_input_system_initialization(self):
        """Test InputSystem initialization with default values."""
        input_system = InputSystem()

        assert input_system.name == "input"
        assert input_system.priority == 10  # Early priority
        # NOTE: key_handlers removed - now uses StateManager.get_input_handler()
        assert len(input_system.mouse_handlers) > 0
        assert input_system.action_callbacks == {}
        assert input_system.input_buffer == []
        assert input_system.recording is False
        assert input_system.playing_back is False

    def test_input_system_custom_priority(self):
        """Test InputSystem initialization with custom priority."""
        input_system = InputSystem(priority=5)

        assert input_system.priority == 5

    def test_input_system_has_required_handlers(self):
        """Test that StateManager has handlers for all game states.
        
        NOTE: InputSystem no longer stores key_handlers directly.
        It queries StateManager.get_input_handler() dynamically.
        """
        # Trigger StateManager initialization
        StateManager.get_config(GameStates.PLAYERS_TURN)
        
        # Check that StateManager has handlers for major game states
        assert StateManager.get_input_handler(GameStates.PLAYERS_TURN) is not None
        assert StateManager.get_input_handler(GameStates.PLAYER_DEAD) is not None
        assert StateManager.get_input_handler(GameStates.TARGETING) is not None
        assert StateManager.get_input_handler(GameStates.SHOW_INVENTORY) is not None
        assert StateManager.get_input_handler(GameStates.DROP_INVENTORY) is not None
        assert StateManager.get_input_handler(GameStates.LEVEL_UP) is not None
        assert StateManager.get_input_handler(GameStates.CHARACTER_SCREEN) is not None
        
        # Check mouse handlers still exist in InputSystem
        input_system = InputSystem()
        assert "default" in input_system.mouse_handlers


class TestInputSystemMethods:
    """Test InputSystem methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.input_system = InputSystem()
        self.mock_engine = Mock()
        self.mock_state_manager = Mock()
        self.mock_engine.state_manager = self.mock_state_manager
        self.input_system.initialize(self.mock_engine)

    def test_register_action_callback(self):
        """Test registering action callbacks."""
        callback = Mock()

        self.input_system.register_action_callback("move", callback)

        assert "move" in self.input_system.action_callbacks
        assert self.input_system.action_callbacks["move"] is callback

    def test_unregister_action_callback(self):
        """Test unregistering action callbacks."""
        callback = Mock()
        self.input_system.register_action_callback("move", callback)

        self.input_system.unregister_action_callback("move")

        assert "move" not in self.input_system.action_callbacks

    def test_unregister_nonexistent_callback(self):
        """Test unregistering a callback that doesn't exist."""
        # Should not raise an exception
        self.input_system.unregister_action_callback("nonexistent")

    def test_register_key_handler(self):
        """Test that key handlers are managed by StateManager (no longer directly registered).
        
        NOTE: After refactoring, InputSystem no longer has register_key_handler().
        Key handlers are configured in state_management/state_config.py.
        """
        # The old method doesn't exist - this is expected after refactoring
        assert not hasattr(self.input_system, 'register_key_handler')
        
        # Instead, handlers are retrieved from StateManager
        handler = StateManager.get_input_handler(GameStates.PLAYERS_TURN)
        assert handler is not None

    def test_register_mouse_handler(self):
        """Test registering custom mouse handlers."""
        custom_handler = Mock()

        self.input_system.register_mouse_handler("custom", custom_handler)

        assert self.input_system.mouse_handlers["custom"] is custom_handler

    def test_start_stop_recording(self):
        """Test input recording functionality."""
        assert self.input_system.recording is False

        self.input_system.start_recording()
        assert self.input_system.recording is True
        assert len(self.input_system.input_buffer) == 0

        self.input_system.stop_recording()
        assert self.input_system.recording is False

    def test_start_stop_playback(self):
        """Test input playback functionality."""
        # Add some test input to buffer
        self.input_system.input_buffer = [
            {"type": "key", "actions": {"move": (1, 0)}},
            {"type": "mouse", "actions": {"left_click": True}},
        ]

        assert self.input_system.playing_back is False

        self.input_system.start_playback()
        assert self.input_system.playing_back is True
        assert self.input_system.playback_index == 0

        self.input_system.stop_playback()
        assert self.input_system.playing_back is False
        assert self.input_system.playback_index == 0

    def test_start_playback_empty_buffer(self):
        """Test starting playback with empty buffer."""
        self.input_system.input_buffer = []

        self.input_system.start_playback()

        # Should not start playback if buffer is empty
        assert self.input_system.playing_back is False

    def test_has_action(self):
        """Test checking for specific actions."""
        self.input_system.current_actions = {"move": (1, 0)}
        self.input_system.current_mouse_actions = {"left_click": True}

        assert self.input_system.has_action("move") is True
        assert self.input_system.has_action("left_click") is True
        assert self.input_system.has_action("nonexistent") is False

    def test_get_action_value(self):
        """Test getting action values."""
        self.input_system.current_actions = {"move": (1, 0)}
        self.input_system.current_mouse_actions = {"left_click": True}

        assert self.input_system.get_action_value("move") == (1, 0)
        assert self.input_system.get_action_value("left_click") is True
        assert self.input_system.get_action_value("nonexistent") is None

    def test_get_current_actions(self):
        """Test getting current actions."""
        test_actions = {"move": (1, 0), "pickup": True}
        self.input_system.current_actions = test_actions

        result = self.input_system.get_current_actions()

        assert result == test_actions
        assert result is not test_actions  # Should be a copy

    def test_get_current_mouse_actions(self):
        """Test getting current mouse actions."""
        test_actions = {"left_click": True, "right_click": False}
        self.input_system.current_mouse_actions = test_actions

        result = self.input_system.get_current_mouse_actions()

        assert result == test_actions
        assert result is not test_actions  # Should be a copy

    def test_cleanup(self):
        """Test cleanup method."""
        # Set up some state
        self.input_system.register_action_callback("test", Mock())
        self.input_system.input_buffer = [{"test": "data"}]
        self.input_system.start_recording()
        self.input_system.start_playback()

        self.input_system.cleanup()

        assert len(self.input_system.action_callbacks) == 0
        assert len(self.input_system.input_buffer) == 0
        assert self.input_system.recording is False
        assert self.input_system.playing_back is False


class TestInputSystemUpdate:
    """Test InputSystem update method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.input_system = InputSystem()
        self.mock_engine = Mock()
        self.mock_state_manager = Mock()
        self.mock_game_state = Mock()

        self.mock_engine.state_manager = self.mock_state_manager
        self.mock_state_manager.state = self.mock_game_state
        self.mock_game_state.current_state = GameStates.PLAYERS_TURN
        # Set up proper mock key and mouse objects
        self.mock_key = Mock()
        self.mock_key.c = 65  # 'A' key
        self.mock_key.vk = 65

        self.mock_mouse = Mock()
        self.mock_mouse.cx = 10
        self.mock_mouse.cy = 15

        self.mock_game_state.key = self.mock_key
        self.mock_game_state.mouse = self.mock_mouse

        self.input_system.initialize(self.mock_engine)

    def test_update_without_engine(self):
        """Test update when no engine is available."""
        self.input_system._engine = None

        # Should not raise any exceptions
        self.input_system.update(0.016)

    def test_update_without_state_manager(self):
        """Test update when engine has no state manager."""
        self.mock_engine.state_manager = None

        # Should not raise any exceptions
        self.input_system.update(0.016)

    def test_update_without_key_input(self):
        """Test update when no key input is available."""
        self.mock_game_state.key = None

        # Should not raise any exceptions
        self.input_system.update(0.016)

    def test_update_with_input(self):
        """Test update with valid input."""
        # Mock the handlers directly in the system
        mock_key_handler = Mock(return_value={"move": (1, 0)})
        mock_mouse_handler = Mock(return_value={"left_click": True})

        self.input_system.key_handlers[GameStates.PLAYERS_TURN] = mock_key_handler
        self.input_system.mouse_handlers["default"] = mock_mouse_handler

        self.input_system.update(0.016)

        # Verify handlers were called
        mock_key_handler.assert_called_once_with(self.mock_key)
        # Mouse handler now receives camera parameter and game_state
        mock_mouse_handler.assert_called_once_with(self.mock_mouse, self.mock_game_state.camera, GameStates.PLAYERS_TURN)

        # Verify actions were stored
        self.mock_state_manager.set_extra_data.assert_any_call(
            "keyboard_actions", {"move": (1, 0)}
        )
        self.mock_state_manager.set_extra_data.assert_any_call(
            "mouse_actions", {"left_click": True}
        )

    def test_update_with_different_game_state(self):
        """Test update with different game state uses correct handler."""
        self.mock_game_state.current_state = GameStates.TARGETING

        # Mock the targeting handler directly
        mock_targeting_handler = Mock(return_value={"exit": True})
        self.input_system.key_handlers[GameStates.TARGETING] = mock_targeting_handler

        self.input_system.update(0.016)

        mock_targeting_handler.assert_called_once_with(self.mock_key)

    def test_update_with_action_callbacks(self):
        """Test update executes action callbacks."""
        callback = Mock()
        self.input_system.register_action_callback("move", callback)

        # Mock the input processing to return a move action
        with patch.object(
            self.input_system, "_process_keyboard_input", return_value={"move": (1, 0)}
        ):
            self.input_system.update(0.016)

        callback.assert_called_once_with((1, 0))

    def test_update_with_callback_exception(self):
        """Test update handles callback exceptions gracefully."""

        def failing_callback(value):
            raise Exception("Test exception")

        self.input_system.register_action_callback("move", failing_callback)

        # Mock the input processing to return a move action
        with patch.object(
            self.input_system, "_process_keyboard_input", return_value={"move": (1, 0)}
        ):
            # Should not raise an exception
            self.input_system.update(0.016)

    def test_update_during_recording(self):
        """Test update records input when recording is enabled."""
        self.input_system.start_recording()

        with patch.object(
            self.input_system, "_process_keyboard_input", return_value={"move": (1, 0)}
        ):
            self.input_system.update(0.016)

        # Should have recorded the input
        assert len(self.input_system.input_buffer) > 0

    def test_update_during_playback(self):
        """Test update uses playback input when playing back."""
        # Set up playback data
        self.input_system.input_buffer = [{"type": "key", "actions": {"move": (0, 1)}}]
        self.input_system.start_playback()

        self.input_system.update(0.016)

        # Should use playback actions
        assert self.input_system.current_actions == {"move": (0, 1)}


class TestInputSystemProcessing:
    """Test input processing methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.input_system = InputSystem()

    def test_process_keyboard_input(self):
        """Test keyboard input processing."""
        mock_key = Mock()
        mock_key.c = 65
        mock_key.vk = 65

        # Test without current_key
        result = self.input_system._process_keyboard_input(GameStates.PLAYERS_TURN)
        assert result == {}

        # Test with current_key but mock the handler
        mock_handler = Mock(return_value={"move": (1, 0)})
        self.input_system.key_handlers[GameStates.PLAYERS_TURN] = mock_handler
        self.input_system.current_key = mock_key

        result = self.input_system._process_keyboard_input(GameStates.PLAYERS_TURN)

        mock_handler.assert_called_once_with(mock_key)
        assert result == {"move": (1, 0)}

    def test_process_keyboard_input_unknown_state(self):
        """Test keyboard input processing with unknown game state."""
        self.input_system.current_key = Mock()

        # Create a custom game state that's not in handlers
        class CustomState:
            pass

        result = self.input_system._process_keyboard_input(CustomState())

        assert result == {}

    def test_process_mouse_input(self):
        """Test mouse input processing."""
        mock_mouse = Mock()
        mock_mouse.cx = 10
        mock_mouse.cy = 15

        # Test without current_mouse
        result = self.input_system._process_mouse_input(GameStates.PLAYERS_TURN)
        assert result == {}

        # Test with current_mouse but mock the handler
        mock_handler = Mock(return_value={"left_click": True})
        self.input_system.mouse_handlers["default"] = mock_handler
        self.input_system.current_mouse = mock_mouse

        result = self.input_system._process_mouse_input(GameStates.PLAYERS_TURN)

        # Mouse handler now receives camera parameter and game_state (None camera when no engine)
        mock_handler.assert_called_once_with(mock_mouse, None, GameStates.PLAYERS_TURN)
        assert result == {"left_click": True}


class TestInputSystemRecordingPlayback:
    """Test input recording and playback functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.input_system = InputSystem()
        self.input_system.current_key = Mock()
        self.input_system.current_key.vk = 65  # 'A' key
        self.input_system.current_key.c = ord("a")

    def test_record_input_keyboard(self):
        """Test recording keyboard input."""
        self.input_system.current_actions = {"move": (1, 0)}

        self.input_system._record_input()

        assert len(self.input_system.input_buffer) == 1
        record = self.input_system.input_buffer[0]
        assert record["type"] == "key"
        assert record["key_code"] == 65
        assert record["char"] == ord("a")
        assert record["actions"] == {"move": (1, 0)}

    def test_record_input_mouse(self):
        """Test recording mouse input."""
        self.input_system.current_key = None  # No keyboard input
        self.input_system.current_mouse_actions = {"left_click": True}

        self.input_system._record_input()

        assert len(self.input_system.input_buffer) == 1
        record = self.input_system.input_buffer[0]
        assert record["type"] == "mouse"
        assert record["actions"] == {"left_click": True}

    def test_process_playback_keyboard(self):
        """Test playing back keyboard input."""
        self.input_system.input_buffer = [{"type": "key", "actions": {"move": (0, -1)}}]
        self.input_system.playback_index = 0

        self.input_system._process_playback()

        assert self.input_system.current_actions == {"move": (0, -1)}
        assert self.input_system.playback_index == 1

    def test_process_playback_mouse(self):
        """Test playing back mouse input."""
        self.input_system.input_buffer = [
            {"type": "mouse", "actions": {"right_click": True}}
        ]
        self.input_system.playback_index = 0

        self.input_system._process_playback()

        assert self.input_system.current_mouse_actions == {"right_click": True}
        assert self.input_system.playback_index == 1

    def test_process_playback_end_of_buffer(self):
        """Test playback stops at end of buffer."""
        self.input_system.input_buffer = [{"type": "key", "actions": {}}]
        self.input_system.playback_index = 1  # Beyond buffer
        self.input_system.playing_back = True

        self.input_system._process_playback()

        assert self.input_system.playing_back is False
        assert self.input_system.playback_index == 0


class TestInputSystemIntegration:
    """Integration tests for InputSystem."""

    def test_input_system_with_engine(self):
        """Test InputSystem integration with GameEngine."""
        from engine.game_engine import GameEngine

        input_system = InputSystem(priority=5)
        engine = GameEngine()
        engine.register_system(input_system)

        assert engine.get_system("input") is input_system
        assert input_system.engine is engine

        # Test update through engine
        with patch.object(input_system, "update") as mock_update:
            engine.update()
            mock_update.assert_called_once()

    def test_input_system_priority_ordering(self):
        """Test that InputSystem has early priority for proper ordering."""
        from engine.game_engine import GameEngine
        from engine.systems import RenderSystem

        input_system = InputSystem()  # Priority 10
        render_system = RenderSystem(Mock(), Mock(), 80, 50, {}, priority=100)

        engine = GameEngine()
        engine.register_system(render_system)
        engine.register_system(input_system)

        # Input should come before render in the system order
        system_names = list(engine.systems.keys())
        assert system_names.index("input") < system_names.index("render")
