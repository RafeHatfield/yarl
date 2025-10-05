"""Tests for engine integration functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from engine_integration import (
    create_game_engine,
    initialize_game_engine,
    play_game_with_engine,
    _should_exit_game,
    _process_game_actions,
)
from engine import GameEngine
from engine.systems import RenderSystem
from engine.systems.input_system import InputSystem
from game_states import GameStates


class TestCreateGameEngine:
    """Test game engine creation and configuration."""

    def test_create_game_engine(self):
        """Test creating a configured game engine."""
        constants = {
            "screen_width": 80,
            "screen_height": 50,
            "colors": {"light_wall": (130, 110, 50)},
        }
        sidebar_console = Mock()
        viewport_console = Mock()
        status_console = Mock()

        engine = create_game_engine(constants, sidebar_console, viewport_console, status_console)

        assert isinstance(engine, GameEngine)
        assert engine.target_fps == 60
        assert (
            engine.system_count == 4
        )  # PerformanceSystem + InputSystem + AISystem + RenderSystem

        # Check that performance system was registered
        performance_system = engine.get_system("performance")
        assert performance_system is not None
        assert performance_system.priority == 5

        # Check that input system was registered
        input_system = engine.get_system("input")
        assert input_system is not None
        assert input_system.priority == 10

        # Check that AI system was registered
        ai_system = engine.get_system("ai")
        assert ai_system is not None
        assert ai_system.priority == 50

        # Check that render system was registered
        render_system = engine.get_system("render")
        # Note: Now using OptimizedRenderSystem with split-screen layout
        assert render_system is not None
        # OptimizedRenderSystem may have different attribute names
        assert render_system is not None
        assert render_system.screen_width == 80
        assert render_system.screen_height == 50
        assert render_system.priority == 100


class TestInitializeGameEngine:
    """Test game engine initialization with game state."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = GameEngine()
        self.player = Mock()
        self.player.x = 40  # Player position for camera initialization
        self.player.y = 20
        self.entities = [Mock(), Mock()]
        self.game_map = Mock()
        self.game_map.width = 80  # Map dimensions for camera initialization
        self.game_map.height = 43
        self.message_log = Mock()
        self.game_state = GameStates.PLAYERS_TURN
        self.constants = {"fov_radius": 10}

    @patch("engine_integration.initialize_fov")
    def test_initialize_game_engine(self, mock_initialize_fov):
        """Test initializing game engine with game state."""
        mock_fov_map = Mock()
        mock_initialize_fov.return_value = mock_fov_map

        # Add a render system to test FOV setup
        render_system = Mock()
        render_system.name = "render"
        self.engine.register_system(render_system)

        initialize_game_engine(
            self.engine,
            self.player,
            self.entities,
            self.game_map,
            self.message_log,
            self.game_state,
            self.constants,
        )

        # Check state manager was initialized
        state_data = self.engine.state_manager.get_state_data()
        assert state_data["player"] is self.player
        assert state_data["entities"] is self.entities
        assert state_data["game_map"] is self.game_map
        assert state_data["message_log"] is self.message_log
        assert state_data["current_state"] == GameStates.PLAYERS_TURN
        assert state_data["constants"] is self.constants

        # Check FOV was initialized
        mock_initialize_fov.assert_called_once_with(self.game_map)
        assert state_data["fov_map"] is mock_fov_map
        assert state_data["fov_recompute"] is True

        # Check render system got FOV map
        render_system.set_fov_map.assert_called_once_with(mock_fov_map)


class TestShouldExitGame:
    """Test game exit conditions."""

    def test_should_exit_game_with_fullscreen(self):
        """Test fullscreen toggle doesn't exit game."""
        action = {"fullscreen": True}
        mouse_action = {}

        with patch(
            "engine_integration.libtcod.console_set_fullscreen"
        ) as mock_fullscreen, patch(
            "engine_integration.libtcod.console_is_fullscreen", return_value=False
        ):

            result = _should_exit_game(action, mouse_action, GameStates.PLAYERS_TURN)

            assert result is False
            mock_fullscreen.assert_called_once_with(True)

    def test_should_exit_game_from_menu(self):
        """Test exit from menu doesn't exit game."""
        action = {"exit": True}
        mouse_action = {}

        result = _should_exit_game(action, mouse_action, GameStates.SHOW_INVENTORY)

        assert result is False

    def test_should_exit_game_from_targeting(self):
        """Test exit from targeting doesn't exit game."""
        action = {"exit": True}
        mouse_action = {}

        result = _should_exit_game(action, mouse_action, GameStates.TARGETING)

        assert result is False

    def test_should_exit_game_from_gameplay(self):
        """Test exit from gameplay exits game."""
        action = {"exit": True}
        mouse_action = {}

        result = _should_exit_game(action, mouse_action, GameStates.PLAYERS_TURN)

        assert result is True

    def test_should_not_exit_game_no_action(self):
        """Test no exit action doesn't exit game."""
        action = {}
        mouse_action = {}

        result = _should_exit_game(action, mouse_action, GameStates.PLAYERS_TURN)

        assert result is False


class TestProcessGameActions:
    """Test game action processing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.state_manager = Mock()
        self.state_manager.state.current_state = GameStates.PLAYERS_TURN
        self.state_manager.state.player = Mock()
        # Ensure player has no active pathfinding to avoid triggering pathfinding movement
        self.state_manager.state.player.pathfinding = None
        self.state_manager.state.entities = []
        self.state_manager.state.game_map = Mock()
        self.targeting_item = None
        self.previous_game_state = GameStates.PLAYERS_TURN
        self.constants = {}

    def test_process_show_inventory_action(self):
        """Test showing inventory changes state."""
        action = {"show_inventory": True}
        mouse_action = {}

        _process_game_actions(
            action,
            mouse_action,
            self.state_manager,
            self.targeting_item,
            self.previous_game_state,
            self.constants,
        )

        self.state_manager.set_game_state.assert_called_with(GameStates.SHOW_INVENTORY)

    def test_process_exit_from_inventory(self):
        """Test exiting from inventory returns to gameplay."""
        action = {"exit": True}
        mouse_action = {}
        self.state_manager.state.current_state = GameStates.SHOW_INVENTORY

        _process_game_actions(
            action,
            mouse_action,
            self.state_manager,
            self.targeting_item,
            self.previous_game_state,
            self.constants,
        )

        self.state_manager.set_game_state.assert_called_with(GameStates.PLAYERS_TURN)

    @patch("entity.get_blocking_entities_at_location")
    def test_process_movement_action(self, mock_get_blocking):
        """Test processing movement action."""
        action = {"move": (1, 0)}
        mouse_action = {}

        # Set up mocks
        player = Mock()
        player.x = 10
        player.y = 10
        player.pathfinding = None  # No active pathfinding
        player.process_status_effects_turn_end.return_value = []  # Return empty list for status effects
        self.state_manager.state.player = player
        self.state_manager.state.game_map.is_blocked.return_value = False
        mock_get_blocking.return_value = None

        _process_game_actions(
            action,
            mouse_action,
            self.state_manager,
            self.targeting_item,
            self.previous_game_state,
            self.constants,
        )

        # Check movement was processed
        player.move.assert_called_once_with(1, 0)
        self.state_manager.request_fov_recompute.assert_called_once()
        self.state_manager.set_game_state.assert_called_with(GameStates.ENEMY_TURN)


class TestPlayGameWithEngineIntegration:
    """Integration tests for the main game loop."""

    @patch("engine_integration.libtcod.console_is_window_closed")
    @patch("engine_integration.libtcod.sys_check_for_event")
    @patch("engine_integration.libtcod.console_clear")
    @patch("engine_integration.handle_keys")
    @patch("engine_integration.handle_mouse")
    @patch("engine_integration.create_game_engine")
    @patch("engine_integration.initialize_game_engine")
    def test_play_game_with_engine_basic_loop(
        self,
        mock_initialize,
        mock_create,
        mock_handle_mouse,
        mock_handle_keys,
        mock_console_clear,
        mock_sys_check,
        mock_window_closed,
    ):
        """Test basic game loop with engine."""
        # Set up mocks
        mock_engine = Mock()
        mock_input_system = Mock(spec=InputSystem)  # Make it pass isinstance check
        mock_input_system.update = Mock()  # Mock the update method
        mock_engine.systems = [mock_input_system]  # Make systems iterable
        mock_engine.update = Mock()  # Mock the engine update method
        
        # Mock state manager methods
        mock_state_manager = Mock()
        mock_state_manager.get_extra_data.return_value = {}
        mock_state_manager.state.current_state = GameStates.PLAYERS_TURN
        # Need to ensure state.player has pathfinding attribute
        mock_state_manager.state.player = Mock()
        mock_state_manager.state.player.pathfinding = None
        mock_engine.state_manager = mock_state_manager
        mock_create.return_value = mock_engine
        mock_window_closed.side_effect = [False, True]  # Run once then exit
        mock_handle_keys.return_value = {"exit": True}
        mock_handle_mouse.return_value = {}

        # Game state
        player = Mock()
        player.pathfinding = None  # No active pathfinding
        entities = []
        game_map = Mock()
        message_log = Mock()
        game_state = GameStates.PLAYERS_TURN
        con = Mock()
        panel = Mock()
        constants = {}

        # Run the game loop
        sidebar_console = Mock()
        viewport_console = Mock()
        status_console = Mock()
        play_game_with_engine(
            player, entities, game_map, message_log, game_state, 
            sidebar_console, viewport_console, status_console, constants
        )

        # Verify engine was created and initialized
        mock_create.assert_called_once_with(constants, sidebar_console, viewport_console, status_console)
        mock_initialize.assert_called_once_with(
            mock_engine, player, entities, game_map, message_log, game_state, constants
        )

        # Verify game loop ran
        mock_engine.update.assert_called()
        mock_engine.stop.assert_called_once()


class TestEngineIntegrationEnd2End:
    """End-to-end integration tests."""

    @patch("engine_integration.libtcod")
    def test_engine_integration_creates_working_system(self, mock_libtcod):
        """Test that the integration creates a working system."""
        # Set up game objects
        constants = {
            "screen_width": 80,
            "screen_height": 50,
            "colors": {"light_wall": (130, 110, 50)},
            "fov_radius": 10,
            "fov_light_walls": True,
            "fov_algorithm": 0,
        }
        con = Mock()
        panel = Mock()
        player = Mock()
        player.x = 40  # Player position for camera initialization
        player.y = 20
        entities = []
        game_map = Mock()
        game_map.width = 80  # Map dimensions for camera initialization
        game_map.height = 43
        message_log = Mock()
        game_state = GameStates.PLAYERS_TURN

        # Create and initialize engine
        with patch("engine_integration.initialize_fov") as mock_init_fov:
            mock_init_fov.return_value = Mock()

            engine = create_game_engine(constants, Mock(), Mock(), Mock())  # sidebar, viewport, status consoles
            initialize_game_engine(
                engine, player, entities, game_map, message_log, game_state, constants
            )

        # Verify engine is properly configured
        assert (
            engine.system_count == 4
        )  # PerformanceSystem + InputSystem + AISystem + RenderSystem
        assert engine.state_manager.state.player is player
        assert engine.state_manager.state.entities is entities

        # Test that systems can access state
        render_system = engine.get_system("render")
        state_data = render_system._get_game_state()

        assert state_data is not None
        assert state_data["player"] is player
        assert state_data["entities"] is entities
        assert state_data["game_map"] is game_map
