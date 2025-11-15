"""Test bot mode throttling and turn transitions.

This test verifies that bot mode doesn't enter infinite loops and properly
throttles action generation to prevent OS unresponsiveness.
"""

import time
import pytest
from unittest.mock import Mock, MagicMock

from io_layer.bot_input import BotInputSource
from game_states import GameStates


class TestBotModeThrottle:
    """Test suite for bot mode throttling mechanism."""
    
    def test_bot_throttles_actions(self):
        """Bot should throttle actions to prevent tight loops.
        
        With action_interval=3, bot returns action on every 3rd call:
        - Call 1: counter 0→1, 1 >= 3? No, return {}
        - Call 2: counter 1→2, 2 >= 3? No, return {}
        - Call 3: counter 2→3, 3 >= 3? Yes, return {'wait': True}, reset to 0
        - Call 4: counter 0→1, 1 >= 3? No, return {}
        """
        bot = BotInputSource(action_interval=3)
        
        # Create mock game state in PLAYERS_TURN
        mock_state = Mock()
        mock_state.current_state = GameStates.PLAYERS_TURN
        
        # First call: counter 0→1, should return empty (throttling)
        action1 = bot.next_action(mock_state)
        assert action1 == {}, "Call 1 should be throttled (counter 1 < 3)"
        
        # Second call: counter 1→2, should return empty (throttling)
        action2 = bot.next_action(mock_state)
        assert action2 == {}, "Call 2 should be throttled (counter 2 < 3)"
        
        # Third call: counter 2→3, should return action
        action3 = bot.next_action(mock_state)
        assert action3 == {'wait': True}, "Call 3 should return action (counter 3 >= 3)"
        
        # Fourth call: counter 0→1 (reset), should return empty (throttling)
        action4 = bot.next_action(mock_state)
        assert action4 == {}, "Call 4 should be throttled (counter 1 < 3)"
    
    def test_bot_respects_game_state(self):
        """Bot should only generate actions during PLAYERS_TURN.
        
        With action_interval=1, first call increments counter 0→1, 1 >= 1, returns action.
        """
        bot = BotInputSource(action_interval=1)
        
        # Test PLAYER_DEAD state
        mock_state = Mock()
        mock_state.current_state = GameStates.PLAYER_DEAD
        action = bot.next_action(mock_state)
        assert action == {}, "Should return empty action when player is dead"
        
        # Test PLAYERS_TURN state - with action_interval=1, first call returns action
        mock_state.current_state = GameStates.PLAYERS_TURN
        action = bot.next_action(mock_state)
        assert action == {'wait': True}, "Should return wait action during PLAYERS_TURN (counter 0→1, 1>=1)"
        
        # Test SHOW_INVENTORY state
        mock_state.current_state = GameStates.SHOW_INVENTORY
        action = bot.next_action(mock_state)
        assert action == {}, "Should return empty action in menu state"
    
    def test_bot_handles_missing_state(self):
        """Bot should handle None or invalid game state gracefully."""
        bot = BotInputSource(action_interval=1)
        
        # Test None state
        action = bot.next_action(None)
        assert action == {}, "Should return empty action for None state"
        
        # Test state without current_state attribute
        mock_state = Mock(spec=[])  # Empty spec = no attributes
        action = bot.next_action(mock_state)
        assert action == {}, "Should return empty action for invalid state"
    
    def test_bot_does_not_block_when_returning_actions(self):
        """Bot should not block; pacing is handled by the main loop."""
        bot = BotInputSource(action_interval=1)

        mock_state = Mock()
        mock_state.current_state = GameStates.PLAYERS_TURN

        start = time.time()
        action = bot.next_action(mock_state)
        duration = time.time() - start

        assert action == {'wait': True}, "First call should return action (counter 0→1, 1>=1)"
        assert duration < 0.005, f"Bot action generation should not block, took {duration}s"
    
    def test_default_action_interval(self):
        """Bot should use action_interval=1 by default."""
        bot = BotInputSource()
        
        assert bot._action_interval == 1, "Default action_interval should be 1"
    
    def test_custom_action_interval(self):
        """Bot should accept custom action_interval.
        
        With action_interval=5:
        - Calls 1-4: counter 1,2,3,4 (all < 5), return {}
        - Call 5: counter 5 (>= 5), return {'wait': True}, reset
        - Call 6: counter 1 (< 5), return {}
        """
        bot = BotInputSource(action_interval=5)
        
        assert bot._action_interval == 5, "Custom action_interval should be set"
        
        mock_state = Mock()
        mock_state.current_state = GameStates.PLAYERS_TURN
        
        # Should throttle for first 4 calls, then return action on 5th
        for i in range(6):
            action = bot.next_action(mock_state)
            if i < 4:
                assert action == {}, f"Call {i+1} should be throttled (counter {i+1} < 5)"
            elif i == 4:
                assert action == {'wait': True}, f"Call 5 should return action (counter 5 >= 5)"
            else:
                assert action == {}, f"Call 6 should be throttled (counter reset to 1)"


class TestBotModeTurnTransitions:
    """Test suite for bot mode turn transition behavior."""
    
    def test_bot_mode_action_generation_pattern(self):
        """Verify bot generates actions in a predictable, bounded pattern.
        
        With action_interval=2:
        - Call 1: counter 0→1, 1 < 2, return {}
        - Call 2: counter 1→2, 2 >= 2, return {'wait': True}, reset to 0
        - Call 3: counter 0→1, 1 < 2, return {}
        - Call 4: counter 1→2, 2 >= 2, return {'wait': True}, reset to 0
        - ...
        Pattern: [{}, {'wait': True}] repeated
        """
        bot = BotInputSource(action_interval=2)
        
        mock_state = Mock()
        mock_state.current_state = GameStates.PLAYERS_TURN
        
        # Simulate 10 frames and track pattern
        actions = []
        for _ in range(10):
            action = bot.next_action(mock_state)
            actions.append(action)
        
        # With action_interval=2, pattern should be: {}, {'wait': True}, {}, {'wait': True}, ...
        expected_pattern = [{}, {'wait': True}] * 5
        assert actions == expected_pattern, f"Action pattern should be predictable: {actions}"
    
    def test_bot_mode_no_actions_in_non_player_states(self):
        """Verify bot doesn't generate actions in non-PLAYERS_TURN states."""
        bot = BotInputSource(action_interval=1)
        
        # Test various non-player states
        non_player_states = [
            GameStates.PLAYER_DEAD,
            GameStates.ENEMY_TURN,
            GameStates.SHOW_INVENTORY,
            GameStates.TARGETING,
            GameStates.CHARACTER_SCREEN,
            GameStates.CONFRONTATION,
            GameStates.VICTORY,
        ]
        
        for state in non_player_states:
            mock_state = Mock()
            mock_state.current_state = state
            
            # Try multiple frames - should always return empty
            for _ in range(5):
                action = bot.next_action(mock_state)
                assert action == {}, f"Bot should not generate actions in {state}"

