import pytest
from unittest.mock import MagicMock

from engine.game_state_manager import GameStateManager
from engine.turn_manager import TurnManager
from engine.systems.ai_system import AISystem
from game_actions import ActionProcessor
from systems.turn_controller import (
    get_turn_controller,
    initialize_turn_controller,
    reset_turn_controller,
)


@pytest.fixture(autouse=True)
def reset_turn_controller_fixture():
    """Ensure the global TurnController is reset before and after each test."""
    reset_turn_controller()
    yield
    reset_turn_controller()


def test_pathfinding_turn_preserves_configured_turn_controller():
    state_manager = GameStateManager()
    turn_manager = TurnManager()

    # Configure the shared ActionProcessor similar to the main game loop
    action_processor = ActionProcessor(state_manager)
    action_processor.turn_manager = turn_manager
    controller = initialize_turn_controller(state_manager, turn_manager)
    action_processor.turn_controller = controller
    action_processor.process_pathfinding_turn = MagicMock()

    state_manager.set_extra_data("action_processor", action_processor)

    ai_system = AISystem()
    ai_system._engine = MagicMock()
    ai_system.engine.turn_manager = turn_manager

    controller_before = get_turn_controller()
    assert controller_before is controller
    assert controller_before.turn_manager is turn_manager

    # Process pathfinding and ensure we reuse the shared processor
    ai_system._process_pathfinding_turn(state_manager)

    controller_after = get_turn_controller()
    assert controller_after is controller_before
    assert controller_after.turn_manager is turn_manager

    action_processor.process_pathfinding_turn.assert_called_once_with()
