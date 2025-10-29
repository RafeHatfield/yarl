"""Tests ensuring death screen rendering uses provided state data."""

from unittest.mock import Mock, patch

import pytest

from game_states import GameStates
from render_functions import render_all


@pytest.fixture
def basic_player():
    """Create a minimal player mock with fighter statistics."""
    player = Mock()
    player.fighter = Mock()
    player.fighter.hp = 0
    player.fighter.max_hp = 10
    player.get_component_optional = Mock(return_value=None)
    return player


def _mock_message_log():
    message_log = Mock()
    message_log.messages = []
    message_log.x = 0
    return message_log


def _mock_mouse():
    mouse = Mock()
    mouse.cx = 0
    mouse.cy = 0
    return mouse


def _mock_game_map():
    game_map = Mock()
    game_map.dungeon_level = 1
    return game_map


def test_render_all_uses_passed_death_quote(basic_player):
    """render_all should forward the provided death quote to the renderer."""

    mock_con = Mock()
    mock_panel = Mock()
    message_log = _mock_message_log()
    mouse = _mock_mouse()
    game_map = _mock_game_map()
    quote = "The soul whispers in defeat."

    with patch("render_functions.render_tiles_optimized"), \
         patch("render_functions.get_sorted_entities", return_value=[]), \
         patch("render_functions.draw_entity"), \
         patch("render_functions.get_effect_queue") as mock_get_queue, \
         patch("render_functions.render_bar"), \
         patch("render_functions.get_names_under_mouse", return_value=""), \
         patch("render_functions.libtcod.console_blit"), \
         patch("render_functions.libtcod.console_set_default_background"), \
         patch("render_functions.libtcod.console_clear"), \
         patch("render_functions.libtcod.console_set_default_foreground"), \
         patch("render_functions.libtcod.console_print_ex"), \
         patch("render_functions.libtcod.console_rect"), \
         patch("render_functions.render_death_screen") as mock_render_death:
        queue_mock = Mock()
        queue_mock.has_effects.return_value = False
        mock_get_queue.return_value = queue_mock

        render_all(
            mock_con,
            mock_panel,
            [],
            basic_player,
            game_map,
            Mock(),
            False,
            message_log,
            80,
            50,
            20,
            7,
            45,
            mouse,
            {},
            GameStates.PLAYER_DEAD,
            use_optimization=True,
            sidebar_console=None,
            camera=None,
            death_screen_quote=quote,
        )

    mock_render_death.assert_called_once_with(mock_con, basic_player, 80, 50, quote)
