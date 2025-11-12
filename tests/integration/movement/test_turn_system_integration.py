"""
Integration tests for the complete turn system.

These tests verify the entire turn flow:
- TurnController initialization
- Turn transitions (player → enemy → environment → player)
- State preservation (e.g., AMULET_OBTAINED)
- Multiple consecutive turns

This prevents regression of the "move once, freeze" bug.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from game_states import GameStates
from systems.turn_controller import TurnController, initialize_turn_controller, get_turn_controller
from state_management.state_config import StateManager


class TestTurnSystemIntegration:
    """Integration tests for the complete turn flow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Reset the global turn controller
        import systems.turn_controller
        systems.turn_controller._turn_controller_instance = None
        
        # Create mock state manager
        self.state_manager = Mock()
        self.state_manager.state = Mock()
        self.state_manager.state.current_state = GameStates.PLAYERS_TURN
        
        # Create mock turn manager
        self.turn_manager = Mock()
        self.turn_manager.current_phase = Mock(value="player")
        
    def test_turn_controller_receives_turn_manager(self):
        """Test that TurnController properly receives TurnManager reference."""
        controller = initialize_turn_controller(self.state_manager, self.turn_manager)
        
        assert controller is not None
        assert controller.state_manager == self.state_manager
        assert controller.turn_manager == self.turn_manager
        assert controller.turn_manager is not None, "TurnManager should not be None!"
        
    def test_turn_transition_advances_turn_manager(self):
        """Test that ending player action advances TurnManager phase."""
        controller = initialize_turn_controller(self.state_manager, self.turn_manager)
        
        # Player takes an action that consumes a turn
        controller.end_player_action(turn_consumed=True)
        
        # Verify TurnManager.advance_turn was called
        self.turn_manager.advance_turn.assert_called_once()
        
        # Verify GameStates was set to ENEMY_TURN
        self.state_manager.set_game_state.assert_called_with(GameStates.ENEMY_TURN)
        
    def test_multiple_consecutive_turns(self):
        """Test that multiple turns can be processed without freezing."""
        controller = initialize_turn_controller(self.state_manager, self.turn_manager)
        
        # Simulate 5 consecutive player actions
        for i in range(5):
            self.state_manager.state.current_state = GameStates.PLAYERS_TURN
            controller.end_player_action(turn_consumed=True)
            
        # Verify TurnManager.advance_turn was called 5 times
        assert self.turn_manager.advance_turn.call_count == 5
        
        # Verify GameStates was set to ENEMY_TURN 5 times
        assert self.state_manager.set_game_state.call_count == 5
        
    def test_turn_controller_without_turn_manager_still_works(self):
        """Test backward compatibility when TurnManager is None."""
        controller = initialize_turn_controller(self.state_manager, turn_manager=None)
        
        # Should still transition game state even without TurnManager
        controller.end_player_action(turn_consumed=True)
        
        # Verify GameStates was still set to ENEMY_TURN
        self.state_manager.set_game_state.assert_called_with(GameStates.ENEMY_TURN)
        
    def test_state_preservation_across_turns(self):
        """Test that AMULET_OBTAINED state is preserved across enemy turn."""
        controller = initialize_turn_controller(self.state_manager, self.turn_manager)
        
        # Set current state to AMULET_OBTAINED
        self.state_manager.state.current_state = GameStates.AMULET_OBTAINED
        
        # Player action should preserve this state
        with patch.object(StateManager, 'should_transition_to_enemy', return_value=True):
            with patch.object(StateManager, 'should_preserve_after_enemy_turn', return_value=True):
                controller.end_player_action(turn_consumed=True)
        
        # Verify state was preserved
        assert controller.preserved_state == GameStates.AMULET_OBTAINED
        
        # Verify TurnManager was still advanced
        self.turn_manager.advance_turn.assert_called_once()
        
    def test_singleton_pattern(self):
        """Test that get_turn_controller returns the same instance."""
        controller1 = initialize_turn_controller(self.state_manager, self.turn_manager)
        controller2 = get_turn_controller()
        
        assert controller1 is controller2, "get_turn_controller should return singleton"
        
    def test_non_turn_consuming_action(self):
        """Test that actions that don't consume turns don't transition."""
        controller = initialize_turn_controller(self.state_manager, self.turn_manager)
        
        # Opening inventory doesn't consume a turn
        controller.end_player_action(turn_consumed=False)
        
        # Verify TurnManager was NOT advanced
        self.turn_manager.advance_turn.assert_not_called()
        
        # Verify GameStates was NOT changed
        self.state_manager.set_game_state.assert_not_called()


class TestTurnSystemWithRealStateManager:
    """Integration tests using real StateManager (not mocked)."""
    
    def test_state_transition_logic(self):
        """Test that StateManager correctly identifies states that should transition."""
        # PLAYERS_TURN should transition to enemy
        assert StateManager.should_transition_to_enemy(GameStates.PLAYERS_TURN) is True
        
        # AMULET_OBTAINED should transition to enemy
        assert StateManager.should_transition_to_enemy(GameStates.AMULET_OBTAINED) is True
        
        # SHOW_INVENTORY should NOT transition to enemy
        assert StateManager.should_transition_to_enemy(GameStates.SHOW_INVENTORY) is False
        
        # ENEMY_TURN should NOT transition to enemy (already there!)
        assert StateManager.should_transition_to_enemy(GameStates.ENEMY_TURN) is False
        
    def test_state_preservation_logic(self):
        """Test that StateManager correctly identifies states to preserve."""
        # AMULET_OBTAINED should be preserved
        assert StateManager.should_preserve_after_enemy_turn(GameStates.AMULET_OBTAINED) is True
        
        # PLAYERS_TURN should NOT be preserved
        assert StateManager.should_preserve_after_enemy_turn(GameStates.PLAYERS_TURN) is False
        
        # SHOW_INVENTORY should NOT be preserved
        assert StateManager.should_preserve_after_enemy_turn(GameStates.SHOW_INVENTORY) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

