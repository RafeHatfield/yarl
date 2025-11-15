"""Test bot mode basic functionality.

This test verifies that BotInputSource returns the correct actions
without blocking, allowing the game loop to tick forward.
"""

import pytest
from io_layer.bot_input import BotInputSource
from game_states import GameStates
from typing import Any


class MockGameState:
    """Mock game state for testing bot input."""
    
    def __init__(self, game_state=GameStates.PLAYERS_TURN):
        self.game_state = game_state
        self.player = None
        self.entities = []
        self.game_map = None
        self.message_log = None
        self.current_state = game_state


class TestBotInputSourceBasic:
    """Test that BotInputSource returns valid actions without blocking."""
    
    def test_bot_input_source_instantiation(self):
        """Test BotInputSource can be instantiated."""
        bot = BotInputSource()
        assert bot is not None
    
    def test_bot_returns_wait_action(self):
        """Test BotInputSource.next_action() returns {'wait': True}."""
        bot = BotInputSource()
        game_state = MockGameState()
        
        action = bot.next_action(game_state)
        
        assert isinstance(action, dict)
        assert action.get('wait') is True
    
    def test_bot_returns_action_immediately(self):
        """Test that BotInputSource.next_action() returns immediately (no blocking)."""
        import time
        
        bot = BotInputSource()
        game_state = MockGameState()
        
        start_time = time.time()
        action = bot.next_action(game_state)
        elapsed = time.time() - start_time
        
        # Should complete in < 1ms (definitely < 100ms)
        assert elapsed < 0.1, f"next_action took {elapsed}s (should be instant)"
        assert action == {'wait': True}
    
    def test_bot_works_in_different_game_states(self):
        """Test BotInputSource respects game state and only acts during PLAYERS_TURN.
        
        CRITICAL FIX: The bot should only return actions during PLAYERS_TURN.
        During other states (PLAYER_DEAD, menus, AI turns), it should return empty
        dict to prevent infinite loops and hangs in bot mode.
        """
        bot = BotInputSource()
        
        # States where bot should return {'wait': True}
        active_states = [GameStates.PLAYERS_TURN]
        
        # States where bot should return {} (no action)
        inactive_states = [
            GameStates.ENEMY_TURN,
            GameStates.PLAYER_DEAD,
            GameStates.SHOW_INVENTORY,
        ]
        
        # Test active states
        for state in active_states:
            game_state = MockGameState(state)
            action = bot.next_action(game_state)
            assert action == {'wait': True}, f"Bot should return wait action in PLAYERS_TURN state {state}"
        
        # Test inactive states (bot should NOT act)
        for state in inactive_states:
            game_state = MockGameState(state)
            action = bot.next_action(game_state)
            assert action == {}, f"Bot should return empty action in non-playing state {state}"
    
    def test_bot_returns_consistent_actions(self):
        """Test that BotInputSource returns the same action repeatedly in PLAYERS_TURN."""
        bot = BotInputSource()
        game_state = MockGameState(GameStates.PLAYERS_TURN)
        
        # Call multiple times during PLAYERS_TURN - should always return {'wait': True}
        for _ in range(10):
            action = bot.next_action(game_state)
            assert action == {'wait': True}
        
        # In non-playing states, should consistently return empty dict
        game_state_dead = MockGameState(GameStates.PLAYER_DEAD)
        for _ in range(10):
            action = bot.next_action(game_state_dead)
            assert action == {}
    
    def test_bot_input_conforms_to_input_source_protocol(self):
        """Test that BotInputSource conforms to InputSource protocol."""
        from io_layer.interfaces import InputSource
        
        bot = BotInputSource()
        
        # Should have next_action method
        assert hasattr(bot, 'next_action')
        assert callable(bot.next_action)
        
        # next_action should accept game_state and return ActionDict
        game_state = MockGameState()
        action = bot.next_action(game_state)
        assert isinstance(action, dict)

