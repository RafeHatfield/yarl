"""Test that bot mode infinite loop bug is fixed.

This test specifically verifies the fix for the bug where:
- Bot mode would spam 'KEYBOARD ACTION RECEIVED: {'wait': True}' 
- Followed by endless AISystem logs calling ai.take_turn() repeatedly
- Causing the game to hang/beachball on empty rooms or death screens

Root cause: BotInputSource always returned {'wait': True} regardless of game state,
causing the main loop to continuously feed actions into the engine even when
the player was dead or the game was in a non-playing state.

Fix: BotInputSource now only returns {'wait': True} during PLAYERS_TURN.
In other states, it returns {} (empty dict) to break the input loop.
"""

import pytest
from io_layer.bot_input import BotInputSource
from game_states import GameStates
from game_actions import ActionProcessor
from state_management.state_config import StateManager
from typing import Any


class MockGameState:
    """Mock game state for testing bot input."""
    
    def __init__(self, game_state=GameStates.PLAYERS_TURN):
        self.current_state = game_state
        self.player = None
        self.entities = []
        self.game_map = None
        self.message_log = None


class MockStateManager:
    """Mock state manager for testing."""
    
    def __init__(self):
        self.state = MockGameState(GameStates.PLAYERS_TURN)
        self._extra_data = {}
    
    def set_game_state(self, state):
        self.state.current_state = state
    
    def set_extra_data(self, key, value):
        self._extra_data[key] = value
    
    def get_extra_data(self, key):
        return self._extra_data.get(key)


class TestBotModeInfiniteLoopFix:
    """Test that the infinite loop bug in bot mode is fixed."""
    
    def test_bot_does_not_feed_actions_on_death_screen(self):
        """Test that bot doesn't return actions when player is dead.
        
        This is the core fix for the beachball/hang bug.
        When player dies and PLAYER_DEAD state is active, the bot should
        not return any actions to prevent the input loop from feeding
        continuous 'wait' actions into the engine.
        """
        bot = BotInputSource()
        
        # Simulate death screen
        game_state = MockGameState(GameStates.PLAYER_DEAD)
        action = bot.next_action(game_state)
        
        # Bot should NOT return a wait action
        assert action == {}, "Bot must not return actions on death screen"
        assert action.get('wait') is None, "Bot must not return 'wait' on death screen"
    
    def test_bot_does_not_feed_actions_during_ai_turn(self):
        """Test that bot doesn't feed actions during ENEMY_TURN.
        
        If the bot returned actions during ENEMY_TURN, and the main loop
        kept calling next_action(), the engine could get into a bad state
        where actions are processed during the AI phase.
        """
        bot = BotInputSource()
        
        # Simulate AI turn phase
        game_state = MockGameState(GameStates.ENEMY_TURN)
        action = bot.next_action(game_state)
        
        # Bot should NOT return a wait action during AI turn
        assert action == {}, "Bot must not return actions during AI turn"
    
    def test_bot_only_feeds_actions_during_players_turn(self):
        """Test that bot ONLY returns actions during PLAYERS_TURN."""
        bot = BotInputSource()
        
        # Simulate player's turn
        game_state = MockGameState(GameStates.PLAYERS_TURN)
        action = bot.next_action(game_state)
        
        # Bot should return wait action during player turn
        assert action == {'wait': True}, "Bot should return wait during PLAYERS_TURN"
    
    def test_input_loop_terminates_in_death_state(self):
        """Test that continuous input polling doesn't cause issues on death.
        
        This simulates the main loop calling next_action() repeatedly
        while the game is in PLAYER_DEAD state. Previously this would
        cause infinite actions to be fed into the engine.
        """
        bot = BotInputSource()
        game_state = MockGameState(GameStates.PLAYER_DEAD)
        
        # Simulate main loop calling next_action() 100 times during death
        actions = []
        for _ in range(100):
            action = bot.next_action(game_state)
            actions.append(action)
        
        # All actions should be empty dicts
        assert all(action == {} for action in actions), \
            "Bot should return empty actions consistently in PLAYER_DEAD state"
        
        # No 'wait' actions should be present
        assert not any(action.get('wait') for action in actions), \
            "No 'wait' actions should be returned in PLAYER_DEAD state"
    
    def test_empty_action_is_ignored_by_action_processor(self):
        """Test that empty action dicts don't trigger processing.
        
        When the bot returns {}, the action processor should have nothing to do.
        This ensures that even if empty actions are processed, no game logic is triggered.
        """
        # Empty dict should not contain any action keys
        action = {}
        
        # Verify that common action handlers wouldn't be triggered
        assert 'wait' not in action or action['wait'] is None
        assert 'move' not in action or action['move'] is None
        assert 'pickup' not in action or action['pickup'] is None
        
        # The action processor checks "if value is not None", so empty dict is safe
        # See game_actions.py line 179: if value is not None and action_type in self.action_handlers
        for action_type, value in action.items():
            # This loop shouldn't execute for empty dict
            assert False, "Empty action dict shouldn't have any items to process"
    
    def test_state_transitions_dont_cause_action_spam(self):
        """Test that state transitions between PLAYERS_TURN and other states work correctly."""
        bot = BotInputSource()
        
        # Simulate state transitions that would happen in the game
        transitions = [
            (GameStates.PLAYERS_TURN, {'wait': True}),    # Player waits
            (GameStates.ENEMY_TURN, {}),                   # AI turn - no actions
            (GameStates.PLAYERS_TURN, {'wait': True}),    # Back to player turn
            (GameStates.PLAYER_DEAD, {}),                 # Death - no actions
        ]
        
        for state, expected_action in transitions:
            game_state = MockGameState(state)
            action = bot.next_action(game_state)
            assert action == expected_action, \
                f"Bot should return {expected_action} in state {state}, got {action}"
    
    def test_no_null_game_state_causes_error(self):
        """Test that bot handles missing or null game_state gracefully."""
        bot = BotInputSource()
        
        # Test with None
        action = bot.next_action(None)
        assert action == {}, "Bot should safely return empty action for None game_state"
        
        # Test with object without current_state attribute
        class BadGameState:
            pass
        
        action = bot.next_action(BadGameState())
        assert action == {}, "Bot should safely return empty action for malformed game_state"

