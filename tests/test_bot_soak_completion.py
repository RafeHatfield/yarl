"""Test bot soak completion logic (Phase 1.6).

Tests for the bot abort run signal when floor is fully explored.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from io_layer.bot_input import BotInputSource
from components.auto_explore import AutoExplore
from game_states import GameStates


class TestBotAbortRunSignal:
    """Test the bot_abort_run signal for soak mode completion."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.bot_input = BotInputSource()
        self.mock_game_state = Mock()
        self.mock_player = Mock()
        self.mock_game_state.current_state = GameStates.PLAYERS_TURN
        self.mock_game_state.player = self.mock_player
        self.mock_game_state.constants = {"bot_soak_mode": True}  # Soak mode enabled
    
    def test_bot_abort_run_after_fully_explored(self):
        """Bot should emit bot_abort_run immediately when floor is fully explored in soak mode."""
        mock_auto_explore = Mock(spec=AutoExplore)
        self.mock_player.get_component_optional = Mock(return_value=mock_auto_explore)
        
        # Frame 1: Auto-explore is active
        mock_auto_explore.is_active = Mock(return_value=True)
        mock_auto_explore.stop_reason = None
        action1 = self.bot_input.next_action(self.mock_game_state)
        assert action1 == {}, "Should return empty action while exploring"
        
        # Frame 2: Auto-explore stopped with "All areas explored" - should immediately abort
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "All areas explored"
        action2 = self.bot_input.next_action(self.mock_game_state)
        assert action2 == {'bot_abort_run': True}, "Should immediately emit bot_abort_run when fully explored"
    
    def test_bot_reset_state_on_new_run(self):
        """Bot should reset state when reset_bot_run_state is called."""
        # Simulate exploration state
        self.bot_input._failed_explore_attempts = 5
        self.bot_input._last_auto_explore_active = True
        self.bot_input._auto_explore_started = True
        
        # Reset state
        self.bot_input.reset_bot_run_state()
        
        # Verify reset
        assert self.bot_input._failed_explore_attempts == 0, "Failed attempts should be reset"
        assert self.bot_input._last_auto_explore_active is False, "Auto-explore state should be reset"
        assert self.bot_input._auto_explore_started is False, "Auto-explore started flag should be reset"
    
    def test_bot_abort_run_not_triggered_by_other_stop_reasons(self):
        """Bot should not emit bot_abort_run if stopped for other reasons (soak mode only)."""
        mock_auto_explore = Mock(spec=AutoExplore)
        self.mock_player.get_component_optional = Mock(return_value=mock_auto_explore)
        
        # Frame 1: Auto-explore is active
        mock_auto_explore.is_active = Mock(return_value=True)
        mock_auto_explore.stop_reason = None
        action1 = self.bot_input.next_action(self.mock_game_state)
        assert action1 == {}
        
        # Frame 2: Auto-explore stopped due to monster (not fully explored)
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "Monster spotted: Orc"
        action2 = self.bot_input.next_action(self.mock_game_state)
        assert action2 == {'start_auto_explore': True}, "Should try to restart after monster stop"
        
        # Continue trying - should never emit bot_abort_run because stop_reason is not "All areas explored"
        # In soak mode, bot_abort_run only triggers for "All areas explored"
        for attempt in range(10):
            mock_auto_explore.is_active = Mock(return_value=False)
            mock_auto_explore.stop_reason = "Monster spotted: Orc"
            action = self.bot_input.next_action(self.mock_game_state)
            assert action == {'start_auto_explore': True}, f"Should always try to restart with monster stop reason (attempt {attempt})"
            assert action != {'bot_abort_run': True}, f"Should never emit bot_abort_run with non-'All areas explored' reason (attempt {attempt})"
    
    def test_soak_mode_emits_bot_abort_run_when_fully_explored(self):
        """Soak mode should immediately emit bot_abort_run when auto-explore is inactive and stop_reason indicates fully explored."""
        mock_auto_explore = Mock(spec=AutoExplore)
        self.mock_player.get_component_optional = Mock(return_value=mock_auto_explore)
        
        # Auto-explore is inactive with "All areas explored" stop_reason
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "All areas explored"
        
        action = self.bot_input.next_action(self.mock_game_state)
        
        assert action == {"bot_abort_run": True}, "Should immediately return bot_abort_run when fully explored"
    
    def test_soak_mode_restarts_auto_explore_for_other_stop_reasons(self):
        """Soak mode should restart auto-explore when stopped for reasons other than fully explored."""
        mock_auto_explore = Mock(spec=AutoExplore)
        self.mock_player.get_component_optional = Mock(return_value=mock_auto_explore)
        
        # Auto-explore is inactive with non-fully-explored stop_reason
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "Monster spotted: Goblin"
        
        action = self.bot_input.next_action(self.mock_game_state)
        
        assert action == {"start_auto_explore": True}, "Should restart auto-explore for other stop reasons"
        assert action != {"bot_abort_run": True}, "Should not emit bot_abort_run for non-fully-explored reasons"
    
    def test_soak_mode_returns_empty_when_auto_explore_active(self):
        """Soak mode should return empty action when auto-explore is active."""
        mock_auto_explore = Mock(spec=AutoExplore)
        self.mock_player.get_component_optional = Mock(return_value=mock_auto_explore)
        
        # Auto-explore is active
        mock_auto_explore.is_active = Mock(return_value=True)
        mock_auto_explore.stop_reason = None
        
        action = self.bot_input.next_action(self.mock_game_state)
        
        assert action == {}, "Should return empty action when auto-explore is active"
    
    def test_soak_mode_initializes_auto_explore_when_none(self):
        """Soak mode should initialize auto-explore when component doesn't exist."""
        # No auto-explore component
        self.mock_player.get_component_optional = Mock(return_value=None)
        
        action = self.bot_input.next_action(self.mock_game_state)
        
        assert action == {"start_auto_explore": True}, "Should initialize auto-explore when component is None"


class TestBotAbortRunInActionProcessor:
    """Test handling of bot_abort_run action in ActionProcessor."""
    
    def test_handle_bot_abort_run_sets_marker(self):
        """_handle_bot_abort_run should set bot_abort_run marker in state."""
        from game_actions import ActionProcessor
        
        # Create mock state manager
        mock_state_manager = Mock()
        mock_state = Mock()
        mock_message_log = Mock()
        mock_state.message_log = mock_message_log
        mock_state_manager.state = mock_state
        mock_state_manager.set_extra_data = Mock()
        
        # Create action processor and handle bot_abort_run
        action_processor = ActionProcessor(mock_state_manager)
        action_processor._handle_bot_abort_run({})
        
        # Verify marker was set
        mock_state_manager.set_extra_data.assert_called_with("bot_abort_run", True)
        
        # Verify message was added to log
        mock_message_log.add_message.assert_called()


class TestNonSoakModeDoesNotAbortOnFullyExplored:
    """Test that non-soak bot mode does NOT emit bot_abort_run when fully explored."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.bot_input = BotInputSource()
        self.mock_game_state = Mock()
        self.mock_player = Mock()
        self.mock_game_state.current_state = GameStates.PLAYERS_TURN
        self.mock_game_state.player = self.mock_player
        self.mock_game_state.constants = {"bot_soak_mode": False}  # Non-soak mode
    
    def test_non_soak_mode_does_not_abort_on_fully_explored(self):
        """Non-soak bot mode should NOT emit bot_abort_run when floor is fully explored.
        
        In non-soak mode, BotBrain should handle exploration decisions, not the soak-specific
        fully explored → bot_abort_run logic.
        """
        mock_auto_explore = Mock(spec=AutoExplore)
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "All areas explored"
        self.mock_player.get_component_optional = Mock(return_value=mock_auto_explore)
        
        # Mock BotBrain to return an explore action (not bot_abort_run)
        from unittest.mock import patch
        with patch.object(self.bot_input.bot_brain, 'decide_action', return_value={'start_auto_explore': True}) as mock_brain:
            action = self.bot_input.next_action(self.mock_game_state)
            
            # BotBrain should be called (not soak logic)
            mock_brain.assert_called_once_with(self.mock_game_state)
            
            # Should return BotBrain's action, NOT bot_abort_run
            assert action == {'start_auto_explore': True}, \
                "Non-soak mode should return BotBrain action, not bot_abort_run"
            assert action != {'bot_abort_run': True}, \
                "Non-soak mode should never emit bot_abort_run (that's soak-only behavior)"

