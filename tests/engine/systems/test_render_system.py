"""Tests for the RenderSystem."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from engine.systems.render_system import RenderSystem


class TestRenderSystemInitialization:
    """Test RenderSystem initialization."""

    def test_render_system_initialization(self):
        """Test RenderSystem initialization with required parameters."""
        console = Mock()
        panel = Mock()
        colors = {"light_wall": (130, 110, 50)}

        render_system = RenderSystem(
            console=console,
            panel=panel,
            screen_width=80,
            screen_height=50,
            colors=colors,
            priority=90,
        )

        assert render_system.name == "render"
        assert render_system.priority == 90
        assert render_system.console is console
        assert render_system.panel is panel
        assert render_system.screen_width == 80
        assert render_system.screen_height == 50
        assert render_system.colors is colors
        assert render_system.fov_map is None
        assert render_system.fov_recompute is True
        assert render_system.bar_width == 20
        assert render_system.panel_height == 7
        assert render_system.panel_y == 45  # ui_layout.viewport_height (updated in v3.5.0)

    def test_render_system_default_priority(self):
        """Test RenderSystem initialization with default priority."""
        console = Mock()
        panel = Mock()
        colors = {}

        render_system = RenderSystem(
            console=console,
            panel=panel,
            screen_width=80,
            screen_height=50,
            colors=colors,
        )

        assert render_system.priority == 100


class TestRenderSystemMethods:
    """Test RenderSystem methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.console = Mock()
        self.panel = Mock()
        self.colors = {"light_wall": (130, 110, 50)}
        self.render_system = RenderSystem(
            console=self.console,
            panel=self.panel,
            screen_width=80,
            screen_height=50,
            colors=self.colors,
        )

    def test_set_fov_map(self):
        """Test setting the FOV map."""
        fov_map = Mock()

        self.render_system.set_fov_map(fov_map)

        assert self.render_system.fov_map is fov_map
        assert self.render_system.fov_recompute is True

    def test_request_fov_recompute(self):
        """Test requesting FOV recomputation."""
        self.render_system.fov_recompute = False

        self.render_system.request_fov_recompute()

        assert self.render_system.fov_recompute is True

    @patch("engine.systems.render_system.clear_entity")
    def test_clear_entity(self, mock_clear_entity):
        """Test clearing a single entity."""
        entity = Mock()

        self.render_system.clear_entity(entity)

        mock_clear_entity.assert_called_once_with(self.console, entity)

    @patch("engine.systems.render_system.draw_entity")
    def test_draw_entity_with_fov_map(self, mock_draw_entity):
        """Test drawing a single entity with FOV map."""
        entity = Mock()
        fov_map = Mock()
        game_map = Mock()

        self.render_system.set_fov_map(fov_map)

        # Mock the game state
        with patch.object(
            self.render_system, "_get_game_state", return_value={"game_map": game_map}
        ):
            self.render_system.draw_entity(entity)

        mock_draw_entity.assert_called_once_with(
            self.console, entity, fov_map, game_map
        )

    @patch("engine.systems.render_system.draw_entity")
    def test_draw_entity_without_fov_map(self, mock_draw_entity):
        """Test drawing entity without FOV map doesn't call draw_entity."""
        entity = Mock()

        self.render_system.draw_entity(entity)

        mock_draw_entity.assert_not_called()

    def test_get_game_state_returns_none(self):
        """Test that _get_game_state returns None (temporary implementation)."""
        result = self.render_system._get_game_state()

        assert result is None

    def test_cleanup(self):
        """Test cleanup method runs without error."""
        # Should not raise any exceptions
        self.render_system.cleanup()


class TestRenderSystemUpdate:
    """Test RenderSystem update method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.console = Mock()
        self.panel = Mock()
        self.colors = {"light_wall": (130, 110, 50)}
        self.render_system = RenderSystem(
            console=self.console,
            panel=self.panel,
            screen_width=80,
            screen_height=50,
            colors=self.colors,
        )

    def test_update_with_no_game_state(self):
        """Test update when no game state is available."""
        with patch.object(self.render_system, "_get_game_state", return_value=None):
            # Should not raise any exceptions
            self.render_system.update(0.016)

    def test_update_with_incomplete_game_state(self):
        """Test update with incomplete game state."""
        incomplete_state = {
            "entities": [],
            "player": None,  # Missing player
            "game_map": Mock(),
            "message_log": Mock(),
        }

        with patch.object(
            self.render_system, "_get_game_state", return_value=incomplete_state
        ):
            # Should not raise any exceptions
            self.render_system.update(0.016)

    @patch("engine.systems.render_system.libtcod.console_flush")
    @patch("engine.systems.render_system.clear_all")
    @patch("engine.systems.render_system.render_all")
    @patch("engine.systems.render_system.recompute_fov")
    def test_update_with_complete_game_state(
        self, mock_recompute_fov, mock_render_all, mock_clear_all, mock_console_flush
    ):
        """Test update with complete game state."""
        # Set up complete game state
        entities = [Mock(), Mock()]
        player = Mock()
        player.x = 10
        player.y = 15
        game_map = Mock()
        message_log = Mock()
        current_state = Mock()
        mouse = Mock()

        complete_state = {
            "entities": entities,
            "player": player,
            "game_map": game_map,
            "message_log": message_log,
            "current_state": current_state,
            "mouse": mouse,
            "fov_radius": 8,
            "fov_light_walls": True,
            "fov_algorithm": 0,
        }

        fov_map = Mock()
        self.render_system.set_fov_map(fov_map)

        with patch.object(
            self.render_system, "_get_game_state", return_value=complete_state
        ):
            self.render_system.update(0.016)

        # Verify FOV recomputation
        mock_recompute_fov.assert_called_once_with(fov_map, 10, 15, 8, True, 0)

        # Verify render_all call
        mock_render_all.assert_called_once_with(
            self.console,
            self.panel,
            entities,
            player,
            game_map,
            fov_map,
            True,  # fov_recompute was True initially
            message_log,
            80,  # screen_width
            50,  # screen_height
            20,  # bar_width
            7,  # panel_height
            45,  # panel_y (ui_layout.viewport_height, updated in v3.5.0)
            mouse,
            self.colors,
            current_state,
            use_optimization=False,
            sidebar_console=None,  # Added in v3.5.0 split-screen update
            camera=None,  # Added in Phase 2 (camera following)
        )

        # Verify screen presentation
        mock_console_flush.assert_called_once()

        # Verify entity clearing
        mock_clear_all.assert_called_once_with(self.console, entities)

        # Verify fov_recompute is reset
        assert self.render_system.fov_recompute is False

    @patch("engine.systems.render_system.libtcod.console_flush")
    @patch("engine.systems.render_system.clear_all")
    @patch("engine.systems.render_system.render_all")
    @patch("engine.systems.render_system.recompute_fov")
    def test_update_without_fov_recompute(
        self, mock_recompute_fov, mock_render_all, mock_clear_all, mock_console_flush
    ):
        """Test update when FOV recompute is not needed."""
        # Set up game state
        complete_state = {
            "entities": [],
            "player": Mock(),
            "game_map": Mock(),
            "message_log": Mock(),
            "current_state": Mock(),
            "mouse": Mock(),
        }

        fov_map = Mock()
        self.render_system.set_fov_map(fov_map)
        self.render_system.fov_recompute = False  # Don't recompute

        with patch.object(
            self.render_system, "_get_game_state", return_value=complete_state
        ):
            self.render_system.update(0.016)

        # FOV should not be recomputed
        mock_recompute_fov.assert_not_called()

        # But rendering should still happen
        mock_render_all.assert_called_once()
        mock_console_flush.assert_called_once()
        mock_clear_all.assert_called_once()


class TestRenderSystemIntegration:
    """Integration tests for RenderSystem."""

    def test_render_system_with_engine(self):
        """Test RenderSystem integration with GameEngine."""
        from engine.game_engine import GameEngine

        console = Mock()
        panel = Mock()
        colors = {}

        render_system = RenderSystem(
            console=console,
            panel=panel,
            screen_width=80,
            screen_height=50,
            colors=colors,
            priority=50,
        )

        engine = GameEngine()
        engine.register_system(render_system)

        assert engine.get_system("render") is render_system
        assert render_system.engine is engine

        # Test update through engine
        with patch.object(render_system, "update") as mock_update:
            engine.update()
            mock_update.assert_called_once()
