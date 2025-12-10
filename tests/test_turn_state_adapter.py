import pytest

from game_states import GameStates
from engine.turn_manager import TurnManager, TurnPhase
from engine.game_state_manager import GameStateManager
from engine.turn_state_adapter import TurnStateAdapter


def test_adapter_without_turn_manager_sets_states():
    state_manager = GameStateManager()
    adapter = TurnStateAdapter(state_manager, turn_manager=None)

    # Default is player turn
    assert adapter.is_player_turn()
    assert not adapter.is_enemy_turn()

    adapter.set_enemy_state()
    assert adapter.is_enemy_turn()
    assert state_manager.state.current_state == GameStates.ENEMY_TURN

    adapter.set_player_state()
    assert adapter.is_player_turn()
    assert state_manager.state.current_state == GameStates.PLAYERS_TURN


def test_adapter_with_turn_manager_advances_phases():
    state_manager = GameStateManager()
    turn_manager = TurnManager()
    adapter = TurnStateAdapter(state_manager, turn_manager=turn_manager)

    adapter.set_enemy_state()
    assert turn_manager.is_phase(TurnPhase.ENEMY)
    assert state_manager.state.current_state == GameStates.ENEMY_TURN

    adapter.advance_to_environment_phase()
    assert turn_manager.is_phase(TurnPhase.ENVIRONMENT)

    adapter.advance_to_player_phase()
    assert turn_manager.is_phase(TurnPhase.PLAYER)

    adapter.set_player_state()
    assert state_manager.state.current_state == GameStates.PLAYERS_TURN
    assert adapter.is_player_phase_consistent()


def test_adapter_consistency_detection():
    state_manager = GameStateManager()
    turn_manager = TurnManager()
    adapter = TurnStateAdapter(state_manager, turn_manager=turn_manager)

    adapter.set_enemy_state()
    # Force a mismatch: move TM to player without updating GameStates
    turn_manager.advance_turn(TurnPhase.PLAYER)
    assert not adapter.is_enemy_phase_consistent()

    adapter.set_enemy_state()
    assert adapter.is_enemy_phase_consistent()
