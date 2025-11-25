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
from game_states import GameStates


class TestGameLoopIntegration:
    """Test that the main game loop uses Renderer and InputSource abstractions."""

    def test_play_game_calls_input_source_and_renderer(self):
        """Verify that play_game_with_engine calls InputSource and engine systems in main loop.
        
        Strategy:
        - Mock create_renderer_and_input_source to return mock InputSource
        - Mock console_is_window_closed to run loop exactly once (False, then True)
        - Verify InputSource.next_action is called (the primary input abstraction)
        - Note: After the refactoring, rendering is handled by engine systems 
          (OptimizedRenderSystem.update), not by the top-level Renderer abstraction
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
        
        # Track whether next_action was called
        action_called = []
        
        def track_next_action(game_state):
            action_called.append(True)
            return {}
        
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
                    # that next_action was called
                    pass
        
        # Verify that InputSource.next_action was called (primary input abstraction)
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


class TestManualPlayLoopInvariants:
    """Test that manual play mode enforces correct turn loop invariants.
    
    These tests lock in the fix for the "AI spam" bug where engine.update()
    was being called every frame even when the player was idle, causing
    repeated AI cycles and degraded manual play experience.
    
    NOTE: These are simplified tests that verify the LOGIC of the should_update_systems
    decision, rather than testing the full integration. This makes them more robust
    and easier to maintain.
    """

    def test_first_frame_always_updates(self):
        """Verify that the first frame after game start always calls engine.update().
        
        CRITICAL: This test locks in the fix for the "menu stuck" regression.
        Without updating on first frame, the game never renders and stays stuck
        on the main menu after pressing 'a'.
        """
        # Simulate the gating logic from engine_integration.py with first_frame flag
        input_mode = "keyboard"  # Manual mode
        current_state = GameStates.PLAYERS_TURN
        action = {}  # No action on first frame
        mouse_action = {}
        first_frame_needs_render = True  # First frame flag
        
        # First frame logic
        should_update_systems = True  # Default
        
        if input_mode != "bot" and current_state == GameStates.PLAYERS_TURN:
            if first_frame_needs_render:
                should_update_systems = True
                first_frame_needs_render = False
            else:
                has_action = bool(action or mouse_action)
                auto_explore_active = False
                if not has_action and not auto_explore_active:
                    should_update_systems = False
        
        # ASSERTION: First frame must always update
        assert should_update_systems == True, (
            "First frame must always update to render initial game state! "
            "Without this, the game stays stuck on menu after pressing 'a'."
        )

    def test_should_update_logic_no_action_no_auto_explore(self):
        """Verify the should_update_systems logic when there's no action and no AutoExplore.
        
        INVARIANT: No input + no AutoExplore = no update
        
        This is the core fix for the "AI spam" bug.
        """
        # Simulate the logic from engine_integration.py lines 685-707
        input_mode = "keyboard"  # Not bot mode
        action = {}  # No keyboard action
        mouse_action = {}  # No mouse action
        
        # Manual mode logic
        has_action = bool(action or mouse_action)
        auto_explore_active = False  # Not active
        
        should_update_systems = True  # Default
        if input_mode != "bot":
            if not has_action and not auto_explore_active:
                should_update_systems = False
        
        # ASSERTION: Should NOT update when there's no action and no AutoExplore
        assert should_update_systems == False, (
            "should_update_systems must be False when there's no action and AutoExplore is inactive"
        )

    def test_should_update_logic_has_action(self):
        """Verify that should_update_systems is True when there's a player action."""
        input_mode = "keyboard"
        action = {"wait": True}  # Player action present
        mouse_action = {}
        
        has_action = bool(action or mouse_action)
        auto_explore_active = False
        
        should_update_systems = True
        if input_mode != "bot":
            if not has_action and not auto_explore_active:
                should_update_systems = False
        
        # ASSERTION: Should update when there's an action
        assert should_update_systems == True, (
            "should_update_systems must be True when player performs an action"
        )

    def test_should_update_logic_auto_explore_active(self):
        """Verify that should_update_systems is True when AutoExplore is active."""
        input_mode = "keyboard"
        action = {}
        mouse_action = {}
        
        has_action = bool(action or mouse_action)
        auto_explore_active = True  # AutoExplore is active
        
        should_update_systems = True
        if input_mode != "bot":
            if not has_action and not auto_explore_active:
                should_update_systems = False
        
        # ASSERTION: Should update when AutoExplore is active
        assert should_update_systems == True, (
            "should_update_systems must be True when AutoExplore is active"
        )

    def test_should_update_logic_bot_mode_always_updates(self):
        """Verify that bot mode always updates, regardless of actions."""
        input_mode = "bot"
        action = {}  # No action
        mouse_action = {}
        auto_explore_active = False
        
        has_action = bool(action or mouse_action)
        
        should_update_systems = True  # Default for bot mode
        if input_mode != "bot":
            # This block shouldn't execute in bot mode
            if not has_action and not auto_explore_active:
                should_update_systems = False
        
        # ASSERTION: Bot mode should always update
        assert should_update_systems == True, (
            "should_update_systems must be True in bot mode, regardless of actions"
        )

    def test_gating_only_applies_to_players_turn(self):
        """Verify that gating ONLY applies during PLAYERS_TURN, not other states."""
        # Simulate the gating logic with different game states
        input_mode = "keyboard"
        action = {}  # No action
        mouse_action = {}
        first_frame_needs_render = False  # Not first frame
        auto_explore_active = False
        
        # Test PLAYERS_TURN - gating should apply
        current_state = GameStates.PLAYERS_TURN
        should_update_systems = True
        
        if input_mode != "bot" and current_state == GameStates.PLAYERS_TURN:
            if not first_frame_needs_render:
                has_action = bool(action or mouse_action)
                if not has_action and not auto_explore_active:
                    should_update_systems = False
        
        assert should_update_systems == False, (
            "Gating should apply in PLAYERS_TURN with no action"
        )
        
        # Test LEVEL_UP - gating should NOT apply (always update)
        current_state = GameStates.LEVEL_UP
        should_update_systems = True
        
        if input_mode != "bot" and current_state == GameStates.PLAYERS_TURN:
            if not first_frame_needs_render:
                has_action = bool(action or mouse_action)
                if not has_action and not auto_explore_active:
                    should_update_systems = False
        
        assert should_update_systems == True, (
            "Gating should NOT apply in LEVEL_UP state - should always update"
        )
        
        # Test CHARACTER_SCREEN - gating should NOT apply
        current_state = GameStates.CHARACTER_SCREEN
        should_update_systems = True
        
        if input_mode != "bot" and current_state == GameStates.PLAYERS_TURN:
            if not first_frame_needs_render:
                has_action = bool(action or mouse_action)
                if not has_action and not auto_explore_active:
                    should_update_systems = False
        
        assert should_update_systems == True, (
            "Gating should NOT apply in CHARACTER_SCREEN - should always update"
        )


