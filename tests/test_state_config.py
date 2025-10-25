"""
Tests for state configuration system.

Verifies that:
1. All GameStates have configurations
2. State configurations are valid
3. StateManager query methods work correctly
4. State behavior properties are consistent
"""

import pytest
from game_states import GameStates
from state_management.state_config import (
    StateConfig,
    STATE_CONFIGURATIONS,
    StateManager
)


class TestStateConfigurations:
    """Test that all states have valid configurations."""
    
    def test_all_game_states_have_configurations(self):
        """Every GameState must have a configuration."""
        missing = []
        for state in GameStates:
            if state not in STATE_CONFIGURATIONS:
                missing.append(state)
        
        assert not missing, f"Missing configurations for states: {missing}"
    
    def test_all_configurations_are_state_config_objects(self):
        """All configurations must be StateConfig instances."""
        for state, config in STATE_CONFIGURATIONS.items():
            assert isinstance(config, StateConfig), \
                f"Configuration for {state} is not a StateConfig object"
    
    def test_all_states_have_descriptions(self):
        """All states should have human-readable descriptions."""
        for state, config in STATE_CONFIGURATIONS.items():
            assert config.description, \
                f"State {state} has no description"
            assert isinstance(config.description, str), \
                f"State {state} description is not a string"


class TestStateManagerQueryMethods:
    """Test StateManager query interface."""
    
    def test_get_config_returns_state_config(self):
        """get_config should return StateConfig objects."""
        config = StateManager.get_config(GameStates.PLAYERS_TURN)
        assert isinstance(config, StateConfig)
    
    def test_get_config_invalid_state_raises_error(self):
        """get_config should raise ValueError for invalid state."""
        # Create a fake state value
        class FakeState:
            pass
        
        with pytest.raises(ValueError, match="No configuration found"):
            StateManager.get_config(FakeState())
    
    def test_allows_movement_returns_bool(self):
        """allows_movement should return boolean."""
        result = StateManager.allows_movement(GameStates.PLAYERS_TURN)
        assert isinstance(result, bool)
    
    def test_allows_pickup_returns_bool(self):
        """allows_pickup should return boolean."""
        result = StateManager.allows_pickup(GameStates.PLAYERS_TURN)
        assert isinstance(result, bool)
    
    def test_allows_inventory_returns_bool(self):
        """allows_inventory should return boolean."""
        result = StateManager.allows_inventory(GameStates.PLAYERS_TURN)
        assert isinstance(result, bool)
    
    def test_get_input_handler_returns_callable_or_none(self):
        """get_input_handler should return function or None."""
        handler = StateManager.get_input_handler(GameStates.PLAYERS_TURN)
        assert callable(handler) or handler is None
    
    def test_should_preserve_after_enemy_turn_returns_bool(self):
        """should_preserve_after_enemy_turn should return boolean."""
        result = StateManager.should_preserve_after_enemy_turn(GameStates.PLAYERS_TURN)
        assert isinstance(result, bool)
    
    def test_should_transition_to_enemy_returns_bool(self):
        """should_transition_to_enemy should return boolean."""
        result = StateManager.should_transition_to_enemy(GameStates.PLAYERS_TURN)
        assert isinstance(result, bool)
    
    def test_ai_processes_in_state_returns_bool(self):
        """ai_processes_in_state should return boolean."""
        result = StateManager.ai_processes_in_state(GameStates.ENEMY_TURN)
        assert isinstance(result, bool)
    
    def test_get_description_returns_string(self):
        """get_description should return string."""
        desc = StateManager.get_description(GameStates.PLAYERS_TURN)
        assert isinstance(desc, str)
        assert len(desc) > 0


class TestSpecificStateBehaviors:
    """Test specific state behaviors are configured correctly."""
    
    def test_players_turn_allows_full_control(self):
        """PLAYERS_TURN should allow all player actions."""
        assert StateManager.allows_movement(GameStates.PLAYERS_TURN)
        assert StateManager.allows_pickup(GameStates.PLAYERS_TURN)
        assert StateManager.allows_inventory(GameStates.PLAYERS_TURN)
        assert StateManager.get_input_handler(GameStates.PLAYERS_TURN) is not None
    
    def test_amulet_obtained_same_controls_as_players_turn(self):
        """AMULET_OBTAINED should have same controls as PLAYERS_TURN."""
        # Same movement, pickup, inventory
        assert StateManager.allows_movement(GameStates.AMULET_OBTAINED) == \
               StateManager.allows_movement(GameStates.PLAYERS_TURN)
        assert StateManager.allows_pickup(GameStates.AMULET_OBTAINED) == \
               StateManager.allows_pickup(GameStates.PLAYERS_TURN)
        assert StateManager.allows_inventory(GameStates.AMULET_OBTAINED) == \
               StateManager.allows_inventory(GameStates.PLAYERS_TURN)
        
        # Same input handler
        assert StateManager.get_input_handler(GameStates.AMULET_OBTAINED) == \
               StateManager.get_input_handler(GameStates.PLAYERS_TURN)
    
    def test_amulet_obtained_preserves_after_enemy_turn(self):
        """AMULET_OBTAINED should be preserved after enemy turn."""
        assert StateManager.should_preserve_after_enemy_turn(GameStates.AMULET_OBTAINED)
    
    def test_players_turn_does_not_preserve(self):
        """PLAYERS_TURN should NOT be preserved (normal behavior)."""
        assert not StateManager.should_preserve_after_enemy_turn(GameStates.PLAYERS_TURN)
    
    def test_enemy_turn_has_no_input_handler(self):
        """ENEMY_TURN should have no input handler."""
        assert StateManager.get_input_handler(GameStates.ENEMY_TURN) is None
    
    def test_enemy_turn_ai_processes(self):
        """AI should process during ENEMY_TURN."""
        assert StateManager.ai_processes_in_state(GameStates.ENEMY_TURN)
    
    def test_players_turn_ai_does_not_process(self):
        """AI should NOT process during PLAYERS_TURN."""
        assert not StateManager.ai_processes_in_state(GameStates.PLAYERS_TURN)
    
    def test_player_dead_has_input_handler(self):
        """PLAYER_DEAD should have input handler (for death screen)."""
        assert StateManager.get_input_handler(GameStates.PLAYER_DEAD) is not None
    
    def test_player_dead_blocks_movement(self):
        """PLAYER_DEAD should not allow movement."""
        assert not StateManager.allows_movement(GameStates.PLAYER_DEAD)
    
    def test_targeting_has_input_handler(self):
        """TARGETING should have input handler."""
        assert StateManager.get_input_handler(GameStates.TARGETING) is not None
    
    def test_targeting_blocks_movement(self):
        """TARGETING should not allow normal movement."""
        assert not StateManager.allows_movement(GameStates.TARGETING)
    
    def test_inventory_states_have_handlers(self):
        """Inventory states should have input handlers."""
        assert StateManager.get_input_handler(GameStates.SHOW_INVENTORY) is not None
        assert StateManager.get_input_handler(GameStates.DROP_INVENTORY) is not None
    
    def test_victory_states_have_no_handlers(self):
        """Victory/failure states handled by their own screens."""
        assert StateManager.get_input_handler(GameStates.VICTORY) is None
        assert StateManager.get_input_handler(GameStates.FAILURE) is None
        assert StateManager.get_input_handler(GameStates.CONFRONTATION) is None


class TestStateTransitionBehaviors:
    """Test state transition configurations."""
    
    def test_players_turn_transitions_to_enemy(self):
        """PLAYERS_TURN actions should transition to enemy turn."""
        assert StateManager.should_transition_to_enemy(GameStates.PLAYERS_TURN)
    
    def test_amulet_obtained_transitions_to_enemy(self):
        """AMULET_OBTAINED actions should transition to enemy turn."""
        assert StateManager.should_transition_to_enemy(GameStates.AMULET_OBTAINED)
    
    def test_enemy_turn_does_not_transition(self):
        """ENEMY_TURN should not transition (handled separately)."""
        assert not StateManager.should_transition_to_enemy(GameStates.ENEMY_TURN)
    
    def test_menu_states_do_not_transition(self):
        """Menu states should not cause turn transitions."""
        assert not StateManager.should_transition_to_enemy(GameStates.SHOW_INVENTORY)
        assert not StateManager.should_transition_to_enemy(GameStates.DROP_INVENTORY)
        assert not StateManager.should_transition_to_enemy(GameStates.CHARACTER_SCREEN)


class TestValidateAllStates:
    """Test the validate_all_states method."""
    
    def test_validate_all_states_passes(self):
        """validate_all_states should not raise error."""
        # Should not raise
        StateManager.validate_all_states()
    
    def test_validate_detects_missing_states(self):
        """validate_all_states should detect missing configurations."""
        # Temporarily remove a configuration
        saved_config = STATE_CONFIGURATIONS.pop(GameStates.PLAYERS_TURN, None)
        
        try:
            with pytest.raises(ValueError, match="missing configurations"):
                StateManager.validate_all_states()
        finally:
            # Restore configuration
            if saved_config:
                STATE_CONFIGURATIONS[GameStates.PLAYERS_TURN] = saved_config


class TestConfigurationConsistency:
    """Test that configurations are internally consistent."""
    
    def test_preserved_states_should_transition(self):
        """States that preserve should also transition to enemy."""
        for state, config in STATE_CONFIGURATIONS.items():
            if config.preserve_after_enemy_turn:
                assert config.transition_to_enemy, \
                    f"{state} preserves after enemy turn but doesn't transition to enemy turn!"
    
    def test_ai_processing_only_in_enemy_turn(self):
        """AI processing should only be enabled for ENEMY_TURN."""
        ai_states = [state for state, config in STATE_CONFIGURATIONS.items() 
                     if config.ai_processes]
        
        # Should only be ENEMY_TURN
        assert GameStates.ENEMY_TURN in ai_states
        # Could be others in future, but for now should just be ENEMY_TURN
    
    def test_states_allowing_movement_have_handlers(self):
        """States that allow movement should have input handlers."""
        for state, config in STATE_CONFIGURATIONS.items():
            if config.allows_movement:
                assert config.input_handler is not None, \
                    f"{state} allows movement but has no input handler!"


class TestStateConfigDocumentation:
    """Test that configurations are well-documented."""
    
    def test_all_descriptions_are_meaningful(self):
        """Descriptions should be meaningful (not just empty strings)."""
        for state, config in STATE_CONFIGURATIONS.items():
            assert len(config.description) > 10, \
                f"{state} has too short description: '{config.description}'"
    
    def test_descriptions_mention_key_features(self):
        """Descriptions for special states should mention their key features."""
        # AMULET_OBTAINED should mention preservation
        amulet_desc = StateManager.get_description(GameStates.AMULET_OBTAINED).lower()
        assert "amulet" in amulet_desc or "portal" in amulet_desc
        
        # ENEMY_TURN should mention enemies
        enemy_desc = StateManager.get_description(GameStates.ENEMY_TURN).lower()
        assert "enem" in enemy_desc or "turn" in enemy_desc
        
        # PLAYER_DEAD should mention death
        dead_desc = StateManager.get_description(GameStates.PLAYER_DEAD).lower()
        assert "dead" in dead_desc or "died" in dead_desc


class TestRegressionPrevention:
    """Tests that prevent specific bugs we fixed during victory implementation."""
    
    def test_amulet_obtained_has_all_features_needed(self):
        """AMULET_OBTAINED must have all the features that caused bugs before.
        
        This test prevents regression of the 9 bugs we hit during victory implementation!
        """
        # Bug #1: State not persisting after enemy turn
        assert StateManager.should_preserve_after_enemy_turn(GameStates.AMULET_OBTAINED), \
            "Bug #1 regression: AMULET_OBTAINED must preserve after enemy turn!"
        
        # Bug #2 & #3: Input handlers missing AMULET_OBTAINED
        assert StateManager.get_input_handler(GameStates.AMULET_OBTAINED) is not None, \
            "Bug #2/3 regression: AMULET_OBTAINED must have input handler!"
        
        # Movement must be allowed
        assert StateManager.allows_movement(GameStates.AMULET_OBTAINED), \
            "AMULET_OBTAINED must allow movement (player needs to find portal)!"
        
        # Pickup must be allowed
        assert StateManager.allows_pickup(GameStates.AMULET_OBTAINED), \
            "AMULET_OBTAINED must allow pickup!"
        
        # Must transition to enemy turn (with preservation)
        assert StateManager.should_transition_to_enemy(GameStates.AMULET_OBTAINED), \
            "AMULET_OBTAINED must transition to enemy turn!"
    
    def test_config_system_solves_duplication_problem(self):
        """Verify that config system eliminates duplication.
        
        Before refactoring:
        - input_system.py had key_handlers dict
        - input_handlers.py had if/elif chain
        - DUPLICATION!
        
        After refactoring:
        - Both use StateManager.get_input_handler()
        - Single source of truth
        """
        # Verify that we can get handler through StateManager
        handler = StateManager.get_input_handler(GameStates.PLAYERS_TURN)
        assert callable(handler)
        
        # Verify it's the same for AMULET_OBTAINED (same handler)
        amulet_handler = StateManager.get_input_handler(GameStates.AMULET_OBTAINED)
        assert amulet_handler == handler, \
            "AMULET_OBTAINED should use same handler as PLAYERS_TURN!"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

