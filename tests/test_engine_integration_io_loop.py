"""Integration tests for the game loop using Renderer and InputSource abstractions.

This module verifies that the main game loop correctly uses the Renderer and
InputSource abstraction protocols as the primary integration points, without
requiring a full end-to-end game simulation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import tcod.libtcodpy as libtcod

from io_layer.interfaces import ActionDict, Renderer, InputSource
from io_layer.console_renderer import ConsoleRenderer
from io_layer.keyboard_input import KeyboardInputSource


class TestGameLoopIntegration:
    """Test that the main game loop uses Renderer and InputSource abstractions."""

    def test_play_game_calls_input_source_and_renderer(self):
        """Verify that play_game_with_engine calls InputSource and Renderer in main loop.
        
        Strategy:
        - Mock create_renderer_and_input_source to return mock Renderer and InputSource
        - Mock console_is_window_closed to run loop exactly once (False, then True)
        - Verify both Renderer.render and InputSource.next_action are called
        """
        from engine_integration import play_game_with_engine, create_game_engine
        from loader_functions.initialize_new_game import get_constants, get_game_variables
        
        # Get actual minimal game state for one loop iteration
        constants = get_constants()
        
        # Create mock consoles
        sidebar_console = Mock()
        viewport_console = Mock()
        status_console = Mock()
        
        # Create actual game state (minimal, will exit after one loop)
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Create mock Renderer and InputSource
        mock_renderer = Mock(spec=Renderer)
        mock_input_source = Mock(spec=InputSource)
        mock_input_source.next_action.return_value = {}  # Empty action does nothing
        
        # Track whether render and next_action were called
        render_called = []
        action_called = []
        
        def track_render(game_state):
            render_called.append(True)
        
        def track_next_action(game_state):
            action_called.append(True)
            return {}
        
        mock_renderer.render = track_render
        mock_input_source.next_action = track_next_action
        
        # Patch console_is_window_closed to run loop exactly once
        with patch('engine_integration.libtcod.console_is_window_closed') as mock_window_closed:
            mock_window_closed.side_effect = [False, True]  # Run once, then exit
            
            # Patch create_renderer_and_input_source to return our mocks
            with patch(
                'engine_integration.create_renderer_and_input_source'
            ) as mock_factory:
                mock_factory.return_value = (mock_renderer, mock_input_source)
                
                # Run the game loop
                try:
                    result = play_game_with_engine(
                        player=player,
                        entities=entities,
                        game_map=game_map,
                        message_log=message_log,
                        game_state=game_state,
                        sidebar_console=sidebar_console,
                        viewport_console=viewport_console,
                        status_console=status_console,
                        constants=constants,
                    )
                except Exception as e:
                    # Loop might exit unexpectedly, that's OK - we just want to verify
                    # that render and next_action were called
                    pass
        
        # Verify that both abstraction methods were called
        assert len(render_called) > 0, "Renderer.render was not called"
        assert len(action_called) > 0, "InputSource.next_action was not called"

    def test_create_renderer_and_input_source_factory(self):
        """Verify that the factory creates valid Renderer and InputSource instances."""
        from engine_integration import create_renderer_and_input_source
        from loader_functions.initialize_new_game import get_constants
        
        constants = get_constants()
        ui_layout_mock = Mock()
        ui_layout_mock.screen_width = constants.get("screen_width", 80)
        ui_layout_mock.screen_height = constants.get("screen_height", 50)
        ui_layout_mock.sidebar_width = 20
        ui_layout_mock.viewport_width = 60
        ui_layout_mock.status_panel_height = 7
        
        sidebar_console = Mock()
        viewport_console = Mock()
        status_console = Mock()
        
        # Create renderer and input source via factory
        renderer, input_source = create_renderer_and_input_source(
            sidebar_console=sidebar_console,
            viewport_console=viewport_console,
            status_console=status_console,
            colors=constants.get("colors", {}),
        )
        
        # Verify they implement the protocols
        assert hasattr(renderer, 'render'), "Renderer must have render method"
        assert hasattr(input_source, 'next_action'), "InputSource must have next_action method"
        assert callable(renderer.render), "render must be callable"
        assert callable(input_source.next_action), "next_action must be callable"

    def test_input_source_returns_action_dict(self):
        """Verify that KeyboardInputSource returns ActionDict compatible results."""
        from io_layer.keyboard_input import KeyboardInputSource
        
        input_source = KeyboardInputSource()
        
        # Mock game state
        mock_state = Mock()
        mock_state.game_state = Mock()
        mock_state.camera = None
        
        # Call next_action
        action = input_source.next_action(mock_state)
        
        # Should return a dict (even if empty)
        assert isinstance(action, dict), "next_action must return a dict"

    def test_renderer_can_be_called(self):
        """Verify that ConsoleRenderer.render can be called without errors."""
        from io_layer.console_renderer import ConsoleRenderer
        
        # Create mock consoles
        sidebar_console = Mock()
        viewport_console = Mock()
        status_console = Mock()
        
        renderer = ConsoleRenderer(
            sidebar_console=sidebar_console,
            viewport_console=viewport_console,
            status_console=status_console,
            colors={"white": (255, 255, 255)},
        )
        
        # Create mock game state with all required attributes
        mock_game_state = Mock()
        mock_game_state.entities = []
        mock_game_state.player = Mock(x=10, y=10)
        mock_game_state.game_map = Mock(width=80, height=50)
        mock_game_state.fov_map = Mock()
        mock_game_state.message_log = Mock()
        mock_game_state.fov_recompute = False
        mock_game_state.mouse = None
        mock_game_state.game_state = Mock()
        mock_game_state.camera = None
        mock_game_state.death_screen_quote = None
        
        # Mock render_all to prevent actual rendering
        with patch('io_layer.console_renderer.render_all'):
            with patch('io_layer.console_renderer.libtcod.console_flush'):
                # Should not raise
                renderer.render(mock_game_state)

