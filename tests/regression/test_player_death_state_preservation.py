"""Regression test for player death state preservation.

This test prevents the bug where PLAYER_DEAD state was overwritten back to
PLAYERS_TURN by turn management logic, allowing the player to continue acting
after death.

Bug history:
- Player killed by monster attack during ENEMY_TURN
- finalize_player_death() correctly sets PLAYER_DEAD
- AI system finishes processing enemies
- AISystem.update() overwrote PLAYER_DEAD → PLAYERS_TURN (BUG)
- Player could move/act despite being dead

Fix:
- StateManager.set_game_state() now guards against overwriting terminal states
- AISystem.update() checks for PLAYER_DEAD before transitioning states
- This test ensures the bug never returns
"""

import pytest
from unittest.mock import Mock, MagicMock
from game_states import GameStates
from engine.game_state_manager import GameStateManager as StateManager


class TestPlayerDeathStatePreservation:
    """Test that PLAYER_DEAD state cannot be overwritten by turn logic."""
    
    def test_terminal_state_cannot_be_overwritten(self):
        """Test that set_game_state ignores attempts to overwrite terminal states."""
        # Create a real StateManager
        state_manager = StateManager()
        
        # Set to PLAYER_DEAD (terminal state)
        state_manager.set_game_state(GameStates.PLAYER_DEAD)
        assert state_manager.state.current_state == GameStates.PLAYER_DEAD
        
        # Attempt to overwrite with PLAYERS_TURN (should be ignored)
        state_manager.set_game_state(GameStates.PLAYERS_TURN)
        
        # Verify state remains PLAYER_DEAD
        assert state_manager.state.current_state == GameStates.PLAYER_DEAD, \
            "Terminal state PLAYER_DEAD should not be overwritten"
    
    def test_victory_state_cannot_be_overwritten(self):
        """Test that VICTORY state is also protected."""
        state_manager = StateManager()
        
        state_manager.set_game_state(GameStates.VICTORY)
        assert state_manager.state.current_state == GameStates.VICTORY
        
        # Attempt to overwrite
        state_manager.set_game_state(GameStates.PLAYERS_TURN)
        
        # Verify state remains VICTORY
        assert state_manager.state.current_state == GameStates.VICTORY, \
            "Terminal state VICTORY should not be overwritten"
    
    def test_failure_state_cannot_be_overwritten(self):
        """Test that FAILURE state is also protected."""
        state_manager = StateManager()
        
        state_manager.set_game_state(GameStates.FAILURE)
        assert state_manager.state.current_state == GameStates.FAILURE
        
        # Attempt to overwrite
        state_manager.set_game_state(GameStates.PLAYERS_TURN)
        
        # Verify state remains FAILURE
        assert state_manager.state.current_state == GameStates.FAILURE, \
            "Terminal state FAILURE should not be overwritten"
    
    def test_non_terminal_states_can_transition(self):
        """Test that normal state transitions still work."""
        state_manager = StateManager()
        
        # Normal state transition should work
        state_manager.set_game_state(GameStates.PLAYERS_TURN)
        assert state_manager.state.current_state == GameStates.PLAYERS_TURN
        
        state_manager.set_game_state(GameStates.ENEMY_TURN)
        assert state_manager.state.current_state == GameStates.ENEMY_TURN
        
        state_manager.set_game_state(GameStates.PLAYERS_TURN)
        assert state_manager.state.current_state == GameStates.PLAYERS_TURN
    
    def test_ai_system_preserves_player_dead_state(self):
        """Test that AISystem.update() preserves PLAYER_DEAD state.
        
        This is the critical regression test for the original bug.
        Simulates: player dies mid-enemy-turn, AISystem finishes turn processing,
        and ensures state remains PLAYER_DEAD.
        """
        from engine.systems.ai_system import AISystem
        from engine.game_engine import GameEngine
        
        # Create minimal game state
        class MockGameState:
            def __init__(self):
                self.current_state = GameStates.ENEMY_TURN
                self.previous_game_state = GameStates.PLAYERS_TURN
                self.player = Mock()
                self.player.components = Mock()
                self.player.components.has = Mock(return_value=False)
                self.entities = []
                self.game_map = Mock()
                self.message_log = Mock()
                self.constants = {}
        
        # Create state manager with mock state
        state_manager = StateManager()
        game_state = MockGameState()
        state_manager._state = game_state
        
        # Create engine and AI system
        engine = GameEngine()
        engine.state_manager = state_manager
        
        ai_system = AISystem()
        ai_system.initialize(engine)
        
        # Simulate player death during enemy turn
        # This happens in _process_ai_results when a monster kills the player
        state_manager.set_game_state(GameStates.PLAYER_DEAD)
        
        # Verify death state is set
        assert state_manager.state.current_state == GameStates.PLAYER_DEAD
        
        # Simulate AISystem.update() finishing the enemy turn
        # The old bug would overwrite PLAYER_DEAD → PLAYERS_TURN here
        ai_system.update(0.016)  # One frame (16ms)
        
        # CRITICAL: State must remain PLAYER_DEAD
        assert state_manager.state.current_state == GameStates.PLAYER_DEAD, \
            "AISystem.update() must not overwrite PLAYER_DEAD state"
    
    def test_is_terminal_state_helper(self):
        """Test the is_terminal_state helper function."""
        from state_management.state_config import StateManager as StateConfig
        
        # Terminal states
        assert StateConfig.is_terminal_state(GameStates.PLAYER_DEAD) is True
        assert StateConfig.is_terminal_state(GameStates.VICTORY) is True
        assert StateConfig.is_terminal_state(GameStates.FAILURE) is True
        
        # Non-terminal states
        assert StateConfig.is_terminal_state(GameStates.PLAYERS_TURN) is False
        assert StateConfig.is_terminal_state(GameStates.ENEMY_TURN) is False
        assert StateConfig.is_terminal_state(GameStates.TARGETING) is False
        assert StateConfig.is_terminal_state(GameStates.LEVEL_UP) is False
    
    def test_terminal_overwrite_warning_is_rate_limited(self):
        """Test that terminal state overwrite warnings are rate-limited.
        
        This prevents log spam if there's a runaway caller in a tight loop
        trying to overwrite terminal states every frame.
        """
        import logging
        from unittest.mock import patch
        
        state_manager = StateManager()
        
        # Set to terminal state
        state_manager.set_game_state(GameStates.PLAYER_DEAD)
        
        # Capture warnings
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Attempt to overwrite 100 times (simulating a tight loop bug)
            for _ in range(100):
                state_manager.set_game_state(GameStates.PLAYERS_TURN)
            
            # Warning should only be logged ONCE, not 100 times
            assert mock_logger.warning.call_count == 1, \
                f"Warning should be logged once, got {mock_logger.warning.call_count} calls"
        
        # State should still be PLAYER_DEAD
        assert state_manager.state.current_state == GameStates.PLAYER_DEAD
    
    def test_different_overwrites_each_get_one_warning(self):
        """Test that different overwrite attempts each get one warning.
        
        If code tries to overwrite PLAYER_DEAD with both PLAYERS_TURN and ENEMY_TURN,
        each unique pair should get exactly one warning.
        """
        import logging
        from unittest.mock import patch
        
        state_manager = StateManager()
        state_manager.set_game_state(GameStates.PLAYER_DEAD)
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Try to overwrite with PLAYERS_TURN (10 times)
            for _ in range(10):
                state_manager.set_game_state(GameStates.PLAYERS_TURN)
            
            # Try to overwrite with ENEMY_TURN (10 times)
            for _ in range(10):
                state_manager.set_game_state(GameStates.ENEMY_TURN)
            
            # Try to overwrite with TARGETING (10 times)
            for _ in range(10):
                state_manager.set_game_state(GameStates.TARGETING)
            
            # Should have exactly 3 warnings (one per unique pair)
            assert mock_logger.warning.call_count == 3, \
                f"Should have 3 warnings (one per state pair), got {mock_logger.warning.call_count}"


class TestDeathStateScenario:
    """Integration-style test simulating the exact bug scenario."""
    
    def test_monster_kills_player_state_preserved(self):
        """Simulate the exact bug: monster kills player, state must not revert.
        
        This test recreates the sequence:
        1. Game is in ENEMY_TURN
        2. Monster attacks player
        3. Player HP goes to 0
        4. finalize_player_death() sets PLAYER_DEAD
        5. AI system continues processing
        6. AI system tries to transition back to PLAYERS_TURN
        7. State must remain PLAYER_DEAD (the fix)
        """
        state_manager = StateManager()
        
        # Start in enemy turn
        state_manager.set_game_state(GameStates.ENEMY_TURN)
        assert state_manager.state.current_state == GameStates.ENEMY_TURN
        
        # Simulate player death (what finalize_player_death does)
        state_manager.set_game_state(GameStates.PLAYER_DEAD)
        assert state_manager.state.current_state == GameStates.PLAYER_DEAD
        
        # Simulate AISystem trying to transition back to PLAYERS_TURN
        # (This is what the old code did at line 234 of ai_system.py)
        state_manager.set_game_state(GameStates.PLAYERS_TURN)
        
        # CRITICAL ASSERTION: State must still be PLAYER_DEAD
        assert state_manager.state.current_state == GameStates.PLAYER_DEAD, \
            "Player death state must not be overwritten by turn transitions"
        
        # Verify the player cannot transition to any other non-terminal state
        for state in [GameStates.PLAYERS_TURN, GameStates.ENEMY_TURN, 
                      GameStates.TARGETING, GameStates.LEVEL_UP]:
            state_manager.set_game_state(state)
            assert state_manager.state.current_state == GameStates.PLAYER_DEAD, \
                f"PLAYER_DEAD must not transition to {state}"
