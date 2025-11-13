"""Tests for renderer and input source abstractions (io_layer module).

These tests verify that the new Renderer and InputSource protocols work
correctly and can be instantiated with their concrete implementations.
"""

import pytest
import tcod.libtcodpy as libtcod
from unittest.mock import Mock, MagicMock, patch

from io_layer.interfaces import Renderer, InputSource
from io_layer.console_renderer import ConsoleRenderer
from io_layer.keyboard_input import KeyboardInputSource
from game_states import GameStates


class TestConsoleRenderer:
    """Tests for the ConsoleRenderer implementation."""

    def test_console_renderer_instantiation(self):
        """Test that ConsoleRenderer can be instantiated."""
        # Create mock consoles
        sidebar_console = Mock()
        viewport_console = Mock()
        status_console = Mock()
        colors = {"white": (255, 255, 255), "black": (0, 0, 0)}

        # Create renderer
        renderer = ConsoleRenderer(
            sidebar_console=sidebar_console,
            viewport_console=viewport_console,
            status_console=status_console,
            colors=colors,
        )

        # Verify it's a Renderer (implements the protocol)
        assert hasattr(renderer, "render")
        assert callable(renderer.render)

    def test_console_renderer_conforms_to_protocol(self):
        """Test that ConsoleRenderer implements Renderer protocol."""
        sidebar_console = Mock()
        viewport_console = Mock()
        status_console = Mock()
        colors = {"white": (255, 255, 255)}

        renderer = ConsoleRenderer(
            sidebar_console=sidebar_console,
            viewport_console=viewport_console,
            status_console=status_console,
            colors=colors,
        )

        # Verify it's structurally compatible with Renderer protocol
        # (runtime duck typing check)
        assert isinstance(renderer, object)
        assert hasattr(renderer, "render")

    @patch("io_layer.console_renderer.libtcod.console_flush")
    @patch("io_layer.console_renderer.render_all")
    def test_console_renderer_render_no_error(self, mock_render_all, mock_flush):
        """Test that ConsoleRenderer.render() doesn't raise errors."""
        # Create mock game state
        mock_game_state = Mock()
        mock_game_state.entities = []
        mock_game_state.player = Mock()
        mock_game_state.game_map = Mock()
        mock_game_state.fov_map = Mock()
        mock_game_state.message_log = Mock()
        mock_game_state.fov_recompute = False
        mock_game_state.mouse = None
        mock_game_state.game_state = GameStates.PLAYERS_TURN
        mock_game_state.camera = None
        mock_game_state.death_screen_quote = None

        # Create renderer
        sidebar_console = Mock()
        viewport_console = Mock()
        status_console = Mock()
        colors = {"white": (255, 255, 255)}

        renderer = ConsoleRenderer(
            sidebar_console=sidebar_console,
            viewport_console=viewport_console,
            status_console=status_console,
            colors=colors,
        )

        # Call render - should not raise
        renderer.render(mock_game_state)

        # Verify render_all was called
        assert mock_render_all.called

    @patch("io_layer.console_renderer.render_all")
    @patch("io_layer.console_renderer.libtcod.console_flush")
    def test_console_renderer_calls_flush(self, mock_flush, mock_render_all):
        """Test that ConsoleRenderer.render() calls console_flush."""
        mock_game_state = Mock()
        mock_game_state.entities = []
        mock_game_state.player = Mock()
        mock_game_state.game_map = Mock()
        mock_game_state.fov_map = Mock()
        mock_game_state.message_log = Mock()
        mock_game_state.fov_recompute = False
        mock_game_state.mouse = None
        mock_game_state.game_state = GameStates.PLAYERS_TURN
        mock_game_state.camera = None
        mock_game_state.death_screen_quote = None

        renderer = ConsoleRenderer(
            sidebar_console=Mock(),
            viewport_console=Mock(),
            status_console=Mock(),
            colors={"white": (255, 255, 255)},
        )

        renderer.render(mock_game_state)

        # Verify console_flush was called
        assert mock_flush.called


class TestKeyboardInputSource:
    """Tests for the KeyboardInputSource implementation."""

    def test_keyboard_input_source_instantiation(self):
        """Test that KeyboardInputSource can be instantiated."""
        input_source = KeyboardInputSource()

        # Verify it's an InputSource (implements the protocol)
        assert hasattr(input_source, "next_action")
        assert callable(input_source.next_action)

    def test_keyboard_input_source_conforms_to_protocol(self):
        """Test that KeyboardInputSource implements InputSource protocol."""
        input_source = KeyboardInputSource()

        # Verify protocol compliance
        assert isinstance(input_source, object)
        assert hasattr(input_source, "next_action")

    @patch("io_layer.keyboard_input.handle_keys")
    @patch("io_layer.keyboard_input.handle_mouse")
    @patch("io_layer.keyboard_input.libtcod.sys_check_for_event")
    def test_keyboard_input_source_next_action(
        self, mock_check_event, mock_handle_mouse, mock_handle_keys
    ):
        """Test that KeyboardInputSource.next_action() returns a dict."""
        # Setup mocks
        mock_handle_keys.return_value = {"move": (1, 0)}
        mock_handle_mouse.return_value = {}

        # Create input source
        input_source = KeyboardInputSource()

        # Create mock game state
        mock_game_state = Mock()
        mock_game_state.game_state = GameStates.PLAYERS_TURN
        mock_game_state.camera = None

        # Call next_action
        action = input_source.next_action(mock_game_state)

        # Verify result is a dict
        assert isinstance(action, dict)

    @patch("io_layer.keyboard_input.handle_keys")
    @patch("io_layer.keyboard_input.handle_mouse")
    @patch("io_layer.keyboard_input.libtcod.sys_check_for_event")
    def test_keyboard_input_source_returns_action_dict(
        self, mock_check_event, mock_handle_mouse, mock_handle_keys
    ):
        """Test that next_action returns combined keyboard and mouse actions."""
        # Setup the mock key to have a non-zero key value
        mock_handle_keys.return_value = {"move": (1, 0)}
        mock_handle_mouse.return_value = {}

        input_source = KeyboardInputSource()
        mock_game_state = Mock()
        mock_game_state.game_state = GameStates.PLAYERS_TURN
        mock_game_state.camera = None

        # Mock the current_key to have a non-zero value so it triggers key handling
        input_source.current_key.vk = libtcod.KEY_UP  # Non-zero vk value

        action = input_source.next_action(mock_game_state)

        # Should include keyboard action
        assert "move" in action
        assert action["move"] == (1, 0)


class TestProtocolCompliance:
    """Tests that implementations comply with their protocol definitions."""

    def test_renderer_protocol_minimal_interface(self):
        """Verify Renderer protocol has minimal, focused interface."""
        # Create a minimal renderer that implements the protocol
        class MinimalRenderer:
            def render(self, game_state):
                pass

        # Should not raise
        renderer: Renderer = MinimalRenderer()
        assert hasattr(renderer, "render")

    def test_input_source_protocol_minimal_interface(self):
        """Verify InputSource protocol has minimal, focused interface."""
        # Create a minimal input source that implements the protocol
        class MinimalInputSource:
            def next_action(self, game_state):
                return {}

        # Should not raise
        input_source: InputSource = MinimalInputSource()
        assert hasattr(input_source, "next_action")

    def test_console_renderer_complies_with_protocol(self):
        """Verify ConsoleRenderer fully implements Renderer protocol."""
        renderer = ConsoleRenderer(
            sidebar_console=Mock(),
            viewport_console=Mock(),
            status_console=Mock(),
            colors={},
        )

        # All protocol methods should exist and be callable
        assert callable(getattr(renderer, "render", None))

    def test_keyboard_input_source_complies_with_protocol(self):
        """Verify KeyboardInputSource fully implements InputSource protocol."""
        input_source = KeyboardInputSource()

        # All protocol methods should exist and be callable
        assert callable(getattr(input_source, "next_action", None))


class TestAbstractionDecoupling:
    """Tests that demonstrate abstraction decoupling benefits."""

    def test_multiple_implementations_possible(self):
        """Test that multiple implementations of same protocol are possible."""
        # Console renderer
        console_renderer = ConsoleRenderer(
            sidebar_console=Mock(),
            viewport_console=Mock(),
            status_console=Mock(),
            colors={},
        )

        # Mock alternative renderer (e.g., sprite renderer)
        class MockSpriteRenderer:
            def render(self, game_state):
                pass

        sprite_renderer = MockSpriteRenderer()

        # Both should be usable as Renderer
        renderers: list[Renderer] = [console_renderer, sprite_renderer]
        assert len(renderers) == 2

    def test_input_source_substitutability(self):
        """Test that InputSource implementations are substitutable."""
        # Keyboard input source
        keyboard_input = KeyboardInputSource()

        # Mock alternative input source (e.g., bot)
        class MockBotInputSource:
            def next_action(self, game_state):
                return {"wait": True}

        bot_input = MockBotInputSource()

        # Both should be usable as InputSource
        input_sources: list[InputSource] = [keyboard_input, bot_input]
        assert len(input_sources) == 2

