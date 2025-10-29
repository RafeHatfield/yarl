import tcod.libtcodpy as libtcod
from unittest.mock import patch

from engine.game_engine import GameEngine
from engine.systems import InputSystem
from engine_integration import _manual_input_system_update
from game_states import GameStates


def test_keyboard_action_available_same_frame():
    engine = GameEngine(target_fps=60)
    input_system = InputSystem(priority=10)
    engine.register_system(input_system)
    engine.state_manager.set_game_state(GameStates.PLAYERS_TURN)

    key = libtcod.Key()
    key.vk = libtcod.KEY_CHAR
    key.c = ord("g")
    key.lalt = False

    mouse = libtcod.Mouse()

    engine.state_manager.set_input_objects(key, mouse)
    engine.state_manager.set_extra_data("keyboard_actions", {"stale": True})
    engine.state_manager.set_extra_data("mouse_actions", {"stale": True})

    manual_dt = 1.0 / engine.target_fps if engine.target_fps else 0.0

    with patch.object(input_system, "update", wraps=input_system.update) as wrapped_update:
        with _manual_input_system_update(engine, manual_dt):
            actions = engine.state_manager.get_extra_data("keyboard_actions", {})

            assert actions.get("pickup") is True
            assert "stale" not in actions

            engine.update()

            # Actions remain available immediately after processing input
            assert engine.state_manager.get_extra_data("keyboard_actions", {}).get("pickup") is True

        # Manual update should have been invoked exactly once
        assert wrapped_update.call_count == 1

    # Input system should be re-enabled for the next frame
    assert input_system.enabled
