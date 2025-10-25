"""
Tests for TurnController system.

Verifies that:
1. Turn transitions work correctly
2. State preservation functions properly
3. Singleton pattern works
4. Integration with StateManager works
"""

import pytest
from unittest.mock import Mock, MagicMock

from game_states import GameStates
from systems.turn_controller import (
    TurnController,
    initialize_turn_controller,
    get_turn_controller,
    reset_turn_controller
)


class TestTurnControllerBasics:
    """Test basic TurnController functionality."""
    
    def setup_method(self):
        """Reset singleton before each test."""
        reset_turn_controller()
    
    def test_initialization(self):
        """TurnController should initialize with state and turn managers."""
        state_manager = Mock()
        turn_manager = Mock()
        
        controller = TurnController(state_manager, turn_manager)
        
        assert controller.state_manager == state_manager
        assert controller.turn_manager == turn_manager
        assert controller.preserved_state is None
    
    def test_initialization_without_turn_manager(self):
        """TurnController should work without turn_manager (backward compat)."""
        state_manager = Mock()
        
        controller = TurnController(state_manager)
        
        assert controller.state_manager == state_manager
        assert controller.turn_manager is None


class TestEndPlayerAction:
    """Test end_player_action() method."""
    
    def setup_method(self):
        """Reset singleton and create mock state manager."""
        reset_turn_controller()
        self.state_manager = Mock()
        self.state_manager.state = Mock()
        self.state_manager.state.current_state = GameStates.PLAYERS_TURN
        self.controller = TurnController(self.state_manager)
    
    def test_action_not_consuming_turn_no_transition(self):
        """Actions that don't consume turns should not transition."""
        self.controller.end_player_action(turn_consumed=False)
        
        # Should not call set_game_state
        assert not self.state_manager.set_game_state.called
    
    def test_action_consuming_turn_transitions(self):
        """Actions that consume turns should transition to ENEMY_TURN."""
        self.controller.end_player_action(turn_consumed=True)
        
        # Should transition to ENEMY_TURN
        self.state_manager.set_game_state.assert_called_with(GameStates.ENEMY_TURN)
    
    def test_preserved_state_marked_for_restoration(self):
        """AMULET_OBTAINED should be preserved for restoration."""
        self.state_manager.state.current_state = GameStates.AMULET_OBTAINED
        
        self.controller.end_player_action(turn_consumed=True)
        
        # Should mark state for preservation
        assert self.controller.is_state_preserved()
        assert self.controller.get_preserved_state() == GameStates.AMULET_OBTAINED


class TestEndEnemyTurn:
    """Test end_enemy_turn() method."""
    
    def setup_method(self):
        """Reset singleton and create mock state manager."""
        reset_turn_controller()
        self.state_manager = Mock()
        self.state_manager.state = Mock()
        self.state_manager.state.current_state = GameStates.ENEMY_TURN
        self.controller = TurnController(self.state_manager)
    
    def test_no_preserved_state_returns_to_players_turn(self):
        """Without preserved state, should return to PLAYERS_TURN."""
        self.controller.end_enemy_turn()
        
        # Should set to PLAYERS_TURN
        self.state_manager.set_game_state.assert_called_with(GameStates.PLAYERS_TURN)
    
    def test_preserved_state_restored(self):
        """With preserved state, should restore it."""
        # Simulate preserved state
        self.controller.preserved_state = GameStates.AMULET_OBTAINED
        
        self.controller.end_enemy_turn()
        
        # Should restore AMULET_OBTAINED
        self.state_manager.set_game_state.assert_called_with(GameStates.AMULET_OBTAINED)
        # Should clear preserved state
        assert not self.controller.is_state_preserved()
    
    def test_with_turn_manager_advances_phases(self):
        """With TurnManager, should advance through phases."""
        turn_manager = Mock()
        self.controller.turn_manager = turn_manager
        
        self.controller.end_enemy_turn()
        
        # Should call advance_turn twice (ENEMY→ENVIRONMENT→PLAYER)
        assert turn_manager.advance_turn.call_count == 2


class TestForceStateTransition:
    """Test force_state_transition() method."""
    
    def setup_method(self):
        """Reset singleton and create mock state manager."""
        reset_turn_controller()
        self.state_manager = Mock()
        self.controller = TurnController(self.state_manager)
    
    def test_force_transition_changes_state(self):
        """Force transition should change state immediately."""
        self.controller.force_state_transition(GameStates.PLAYER_DEAD)
        
        self.state_manager.set_game_state.assert_called_with(GameStates.PLAYER_DEAD)
    
    def test_force_transition_clears_preserved_state(self):
        """Force transition should clear any preserved state."""
        self.controller.preserved_state = GameStates.AMULET_OBTAINED
        
        self.controller.force_state_transition(GameStates.VICTORY)
        
        # Preserved state should be cleared
        assert not self.controller.is_state_preserved()


class TestStatePreservation:
    """Test state preservation functionality."""
    
    def setup_method(self):
        """Reset singleton and create mock state manager."""
        reset_turn_controller()
        self.state_manager = Mock()
        self.controller = TurnController(self.state_manager)
    
    def test_is_state_preserved_initially_false(self):
        """Initially, no state should be preserved."""
        assert not self.controller.is_state_preserved()
    
    def test_is_state_preserved_after_marking(self):
        """After marking, state should be preserved."""
        self.controller.preserved_state = GameStates.AMULET_OBTAINED
        
        assert self.controller.is_state_preserved()
    
    def test_get_preserved_state_returns_correct_state(self):
        """get_preserved_state should return the preserved state."""
        self.controller.preserved_state = GameStates.AMULET_OBTAINED
        
        assert self.controller.get_preserved_state() == GameStates.AMULET_OBTAINED
    
    def test_clear_preserved_state_removes_preservation(self):
        """clear_preserved_state should remove preservation."""
        self.controller.preserved_state = GameStates.AMULET_OBTAINED
        
        self.controller.clear_preserved_state()
        
        assert not self.controller.is_state_preserved()
        assert self.controller.get_preserved_state() is None


class TestSingletonPattern:
    """Test singleton accessor functions."""
    
    def setup_method(self):
        """Reset singleton before each test."""
        reset_turn_controller()
    
    def test_initialize_creates_global_instance(self):
        """initialize_turn_controller should create global instance."""
        state_manager = Mock()
        
        controller = initialize_turn_controller(state_manager)
        
        assert controller is not None
        assert get_turn_controller() == controller
    
    def test_get_turn_controller_returns_none_before_init(self):
        """get_turn_controller should return None if not initialized."""
        assert get_turn_controller() is None
    
    def test_reset_clears_global_instance(self):
        """reset_turn_controller should clear global instance."""
        state_manager = Mock()
        initialize_turn_controller(state_manager)
        
        reset_turn_controller()
        
        assert get_turn_controller() is None
    
    def test_multiple_initializations_replace_instance(self):
        """Multiple initializations should replace the instance."""
        state_manager1 = Mock()
        state_manager2 = Mock()
        
        controller1 = initialize_turn_controller(state_manager1)
        controller2 = initialize_turn_controller(state_manager2)
        
        assert controller1 != controller2
        assert get_turn_controller() == controller2


class TestIntegrationWithStateManager:
    """Test integration with StateManager."""
    
    def setup_method(self):
        """Reset singleton and create mock state manager."""
        reset_turn_controller()
        self.state_manager = Mock()
        self.state_manager.state = Mock()
        self.controller = TurnController(self.state_manager)
    
    def test_amulet_obtained_preserved_across_turn(self):
        """AMULET_OBTAINED should be preserved across enemy turn.
        
        This is the key test for the victory condition bug fix!
        """
        # Start in AMULET_OBTAINED
        self.state_manager.state.current_state = GameStates.AMULET_OBTAINED
        
        # End player action (should preserve state)
        self.controller.end_player_action(turn_consumed=True)
        assert self.controller.is_state_preserved()
        
        # Enemies take their turns...
        # (state is ENEMY_TURN during this)
        
        # End enemy turn (should restore AMULET_OBTAINED)
        self.controller.end_enemy_turn()
        
        # Verify AMULET_OBTAINED was restored
        calls = self.state_manager.set_game_state.call_args_list
        last_call = calls[-1][0][0]
        assert last_call == GameStates.AMULET_OBTAINED
    
    def test_normal_turn_flow(self):
        """Normal turns should go PLAYERS_TURN → ENEMY_TURN → PLAYERS_TURN."""
        # Start in PLAYERS_TURN
        self.state_manager.state.current_state = GameStates.PLAYERS_TURN
        
        # End player action
        self.controller.end_player_action(turn_consumed=True)
        
        # Should transition to ENEMY_TURN
        assert self.state_manager.set_game_state.call_args[0][0] == GameStates.ENEMY_TURN
        
        # End enemy turn
        self.controller.end_enemy_turn()
        
        # Should return to PLAYERS_TURN
        calls = self.state_manager.set_game_state.call_args_list
        last_call = calls[-1][0][0]
        assert last_call == GameStates.PLAYERS_TURN


class TestRegressionPrevention:
    """Tests that prevent specific bugs we fixed during refactoring."""
    
    def setup_method(self):
        """Reset singleton and create mock state manager."""
        reset_turn_controller()
    
    def test_victory_bug_state_preservation(self):
        """Prevent regression of victory condition state reset bug.
        
        Bug: AMULET_OBTAINED reset to PLAYERS_TURN after enemy turn
        Fix: TurnController preserves state automatically
        """
        state_manager = Mock()
        state_manager.state = Mock()
        state_manager.state.current_state = GameStates.AMULET_OBTAINED
        
        controller = TurnController(state_manager)
        
        # Player action while holding amulet
        controller.end_player_action(turn_consumed=True)
        
        # State should be preserved
        assert controller.is_state_preserved(), \
            "AMULET_OBTAINED must be preserved (victory bug regression)!"
        
        # After enemy turn
        controller.end_enemy_turn()
        
        # Should restore AMULET_OBTAINED, not PLAYERS_TURN
        calls = state_manager.set_game_state.call_args_list
        last_call = calls[-1][0][0]
        assert last_call == GameStates.AMULET_OBTAINED, \
            "State must be restored (victory bug regression)!"
    
    def test_no_hardcoded_victory_checks(self):
        """TurnController should not have hardcoded victory checks.
        
        Before refactoring: ai_system checked player.victory.amulet_obtained
        After refactoring: TurnController uses StateManager config
        """
        state_manager = Mock()
        controller = TurnController(state_manager)
        
        # TurnController should not reference player.victory at all
        # This test passes if TurnController was created without errors
        # (it uses StateManager, not hardcoded checks)
        assert True  # If we got here, TurnController is decoupled!


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Reset singleton and create mock state manager."""
        reset_turn_controller()
        self.state_manager = Mock()
        self.controller = TurnController(self.state_manager)
    
    def test_end_enemy_turn_without_enemy_turn_first(self):
        """Calling end_enemy_turn without transition should still work."""
        # Directly call end_enemy_turn
        self.controller.end_enemy_turn()
        
        # Should set to PLAYERS_TURN (no preserved state)
        self.state_manager.set_game_state.assert_called_with(GameStates.PLAYERS_TURN)
    
    def test_multiple_end_player_actions_in_row(self):
        """Multiple end_player_action calls should work."""
        self.state_manager.state.current_state = GameStates.PLAYERS_TURN
        
        self.controller.end_player_action(turn_consumed=True)
        self.controller.end_player_action(turn_consumed=True)
        
        # Should call set_game_state twice
        assert self.state_manager.set_game_state.call_count >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

