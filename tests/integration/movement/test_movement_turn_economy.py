"""
Test that movement consumes turns correctly.

This is CRITICAL functionality - movement must end the player's turn!
"""

import pytest
from unittest.mock import Mock
from game_actions import ActionProcessor
from game_states import GameStates
from services.movement_service import reset_movement_service


class TestMovementTurnEconomy:
    """Test that moving consumes a turn (CRITICAL)."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_movement_service()

    def test_normal_movement_ends_turn(self):
        """Moving to empty space should consume a turn.
        
        CRITICAL: This is core roguelike functionality!
        """
        # Setup
        state_manager = Mock()
        state_manager.state = Mock()
        state_manager.state.current_state = GameStates.PLAYERS_TURN
        
        # Create player
        player = Mock()
        player.x = 10
        player.y = 10
        player.move = Mock()  # Mock the move method
        player.has_status_effect = Mock(return_value=False)  # Not paralyzed
        player.status_effects = Mock()
        player.status_effects.process_turn_start = Mock(return_value=[])
        player.process_status_effects_turn_end = Mock(return_value=[])
        player.components = Mock()
        player.components.has = Mock(return_value=False)  # No status effects component
        
        state_manager.state.player = player
        
        # Create empty game map (movement target is valid)
        game_map = Mock()
        game_map.is_blocked = Mock(return_value=False)  # Path is clear
        game_map.secret_door_manager = None  # No secret doors to check
        state_manager.state.game_map = game_map
        
        # No entities blocking
        state_manager.state.entities = []
        
        # Mock camera
        state_manager.state.camera = Mock()
        
        processor = ActionProcessor(state_manager)
        # Mock TurnController
        processor.turn_controller = Mock()
        
        # Execute movement
        processor._handle_movement((1, 0))  # Move right
        
        # CRITICAL ASSERTION: Turn must end after movement!
        processor.turn_controller.end_player_action.assert_called_once_with(turn_consumed=True)
        
    def test_movement_into_wall_does_not_end_turn(self):
        """Bumping into a wall should NOT consume a turn."""
        # Setup
        state_manager = Mock()
        state_manager.state = Mock()
        state_manager.state.current_state = GameStates.PLAYERS_TURN
        
        player = Mock()
        player.x = 10
        player.y = 10
        player.has_status_effect = Mock(return_value=False)
        player.status_effects = Mock()
        player.status_effects.process_turn_start = Mock(return_value=[])
        player.process_status_effects_turn_end = Mock(return_value=[])
        player.components = Mock()
        player.components.has = Mock(return_value=False)  # No status effects component
        state_manager.state.player = player
        
        # Blocked destination
        game_map = Mock()
        game_map.is_blocked = Mock(return_value=True)  # Wall ahead!
        game_map.secret_door_manager = None
        state_manager.state.game_map = game_map
        
        # No entities blocking (must be iterable)
        state_manager.state.entities = []
        
        processor = ActionProcessor(state_manager)
        processor.turn_controller = Mock()
        
        # Execute movement into wall
        processor._handle_movement((1, 0))
        
        # Turn should NOT end (invalid move)
        processor.turn_controller.end_player_action.assert_not_called()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

