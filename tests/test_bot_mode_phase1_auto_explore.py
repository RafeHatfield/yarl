"""Tests for Phase 1 bot mode auto-explore behavior.

This test suite validates that the bot correctly triggers and uses the existing
auto-explore system to navigate the dungeon, rather than just waiting every turn.
"""

import pytest
from unittest.mock import Mock, MagicMock

from io_layer.bot_input import BotInputSource
from game_states import GameStates
from components.component_registry import ComponentType
from components.auto_explore import AutoExplore


class TestBotModePhase1AutoExplore:
    """Test suite for Phase 1 bot auto-explore integration."""

    def setup_method(self):
        """Set up test fixtures before each test."""
        self.bot_input = BotInputSource(action_interval=1)
        self.mock_game_state = Mock()
        self.mock_player = Mock()
        self.mock_game_state.player = self.mock_player
        self.mock_game_state.current_state = GameStates.PLAYERS_TURN

    def test_triggers_auto_explore_when_not_active(self):
        """Bot should trigger auto-explore when it's not already active."""
        # Setup: No auto-explore component on player
        self.mock_player.get_component_optional = Mock(return_value=None)
        
        # Act
        action = self.bot_input.next_action(self.mock_game_state)
        
        # Assert
        assert action == {'start_auto_explore': True}
        self.mock_player.get_component_optional.assert_called_with(ComponentType.AUTO_EXPLORE)

    def test_returns_empty_when_auto_explore_active(self):
        """Bot should return empty action when auto-explore is already running."""
        # Setup: Auto-explore component exists and is active
        mock_auto_explore = Mock(spec=AutoExplore)
        mock_auto_explore.is_active = Mock(return_value=True)
        self.mock_player.get_component_optional = Mock(return_value=mock_auto_explore)
        
        # Act
        action = self.bot_input.next_action(self.mock_game_state)
        
        # Assert
        assert action == {}
        mock_auto_explore.is_active.assert_called_once()

    def test_triggers_auto_explore_when_inactive(self):
        """Bot should re-trigger auto-explore if component exists but is inactive."""
        # Setup: Auto-explore component exists but is not active
        mock_auto_explore = Mock(spec=AutoExplore)
        mock_auto_explore.is_active = Mock(return_value=False)
        self.mock_player.get_component_optional = Mock(return_value=mock_auto_explore)
        
        # Act
        action = self.bot_input.next_action(self.mock_game_state)
        
        # Assert
        assert action == {'start_auto_explore': True}

    def test_returns_empty_when_not_players_turn(self):
        """Bot should return empty action when not in PLAYERS_TURN state."""
        # Test various non-playing states
        non_playing_states = [
            GameStates.PLAYER_DEAD,
            GameStates.SHOW_INVENTORY,
            GameStates.DROP_INVENTORY,
            GameStates.TARGETING,
            GameStates.LEVEL_UP,
            GameStates.CHARACTER_SCREEN,
        ]
        
        for state in non_playing_states:
            self.mock_game_state.current_state = state
            action = self.bot_input.next_action(self.mock_game_state)
            assert action == {}, f"Expected empty action for state {state}"

    def test_returns_empty_when_game_state_invalid(self):
        """Bot should return empty action when game_state is None or malformed."""
        # Test None game_state
        action = self.bot_input.next_action(None)
        assert action == {}
        
        # Test game_state without current_state attribute
        invalid_state = Mock(spec=[])  # No attributes
        action = self.bot_input.next_action(invalid_state)
        assert action == {}

    def test_returns_wait_when_no_player(self):
        """Bot should wait if there's no player entity."""
        self.mock_game_state.player = None
        
        action = self.bot_input.next_action(self.mock_game_state)
        
        assert action == {'wait': True}

    def test_action_interval_throttling(self):
        """Bot should respect action_interval and not emit actions every frame."""
        # Create bot with 3-frame interval
        bot = BotInputSource(action_interval=3)
        self.mock_player.get_component_optional = Mock(return_value=None)
        
        # First call (counter = 1) should return empty (not >= 3)
        action1 = bot.next_action(self.mock_game_state)
        assert action1 == {}
        
        # Second call (counter = 2) should return empty
        action2 = bot.next_action(self.mock_game_state)
        assert action2 == {}
        
        # Third call (counter = 3) should trigger auto-explore and reset
        action3 = bot.next_action(self.mock_game_state)
        assert action3 == {'start_auto_explore': True}
        
        # Fourth call (counter = 1 again) should return empty
        action4 = bot.next_action(self.mock_game_state)
        assert action4 == {}

    def test_multiple_turns_with_active_auto_explore(self):
        """Bot should consistently return empty action while auto-explore is active."""
        mock_auto_explore = Mock(spec=AutoExplore)
        mock_auto_explore.is_active = Mock(return_value=True)
        self.mock_player.get_component_optional = Mock(return_value=mock_auto_explore)
        
        # Call multiple times
        for _ in range(10):
            action = self.bot_input.next_action(self.mock_game_state)
            assert action == {}

    def test_bot_restarts_auto_explore_after_it_stops(self):
        """Bot should restart auto-explore after it naturally stops (e.g., monster found)."""
        mock_auto_explore = Mock(spec=AutoExplore)
        self.mock_player.get_component_optional = Mock(return_value=mock_auto_explore)
        
        # First turn: auto-explore is active
        mock_auto_explore.is_active = Mock(return_value=True)
        mock_auto_explore.stop_reason = None  # Not stopped yet
        action1 = self.bot_input.next_action(self.mock_game_state)
        assert action1 == {}
        
        # Second turn: auto-explore stopped (e.g., found monster)
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "Monster spotted: Orc"  # Stopped due to monster
        action2 = self.bot_input.next_action(self.mock_game_state)
        assert action2 == {'start_auto_explore': True}

    def test_integration_with_game_states_enum(self):
        """Bot should correctly use GameStates enum for state checking."""
        # This test ensures the import and usage is correct
        from game_states import GameStates
        
        self.mock_game_state.current_state = GameStates.PLAYERS_TURN
        self.mock_player.get_component_optional = Mock(return_value=None)
        
        action = self.bot_input.next_action(self.mock_game_state)
        assert action == {'start_auto_explore': True}

    def test_integration_with_component_type_enum(self):
        """Bot should correctly use ComponentType enum for component lookup."""
        # This test ensures the import and usage is correct
        from components.component_registry import ComponentType
        
        self.mock_player.get_component_optional = Mock(return_value=None)
        self.bot_input.next_action(self.mock_game_state)
        
        self.mock_player.get_component_optional.assert_called_with(ComponentType.AUTO_EXPLORE)


class TestBotModePhase1EdgeCases:
    """Edge case tests for bot auto-explore behavior."""

    def test_bot_handles_missing_get_component_optional_method(self):
        """Bot should gracefully handle player without get_component_optional method."""
        bot = BotInputSource()
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.player = Mock(spec=[])  # No get_component_optional
        
        # Should return wait as fallback (defensive programming)
        action = bot.next_action(game_state)
        assert action == {'wait': True}

    def test_auto_explore_started_flag_tracking(self):
        """Bot should track when it has started auto-explore."""
        bot = BotInputSource()
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.player = Mock()
        game_state.player.get_component_optional = Mock(return_value=None)
        
        # Initially, flag should be False
        assert bot._auto_explore_started == False
        
        # After triggering auto-explore, flag should be True
        action = bot.next_action(game_state)
        assert action == {'start_auto_explore': True}
        assert bot._auto_explore_started == True


class TestBotModePhase0PreservationInvariant:
    """Tests to ensure Phase 0 invariants (enemies disabled) are preserved."""

    def test_bot_does_not_modify_enemy_ai_flag(self):
        """Bot input source should NOT touch the AISystem's enemy disable flag.
        
        This test is a documentation test - it verifies that BotInputSource doesn't
        try to control enemy AI, which is handled by AISystem's bot mode flag.
        """
        bot = BotInputSource()
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.player = Mock()
        game_state.player.get_component_optional = Mock(return_value=None)
        
        # Bot should only emit action dicts, not modify game state
        action = bot.next_action(game_state)
        
        # Assert: game_state should not have been modified
        # (In real usage, enemy AI is controlled by AISystem, not BotInputSource)
        assert action == {'start_auto_explore': True}
        assert not hasattr(bot, 'disable_enemy_ai')  # Bot doesn't manage this

