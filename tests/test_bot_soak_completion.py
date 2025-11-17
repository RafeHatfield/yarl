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
    
    def test_bot_abort_run_after_fully_explored(self):
        """Bot should emit bot_abort_run after 3 failed attempts to restart when floor is fully explored."""
        mock_auto_explore = Mock(spec=AutoExplore)
        self.mock_player.get_component_optional = Mock(return_value=mock_auto_explore)
        
        # Frame 1: Auto-explore is active
        mock_auto_explore.is_active = Mock(return_value=True)
        mock_auto_explore.stop_reason = None
        action1 = self.bot_input.next_action(self.mock_game_state)
        assert action1 == {}, "Should return empty action while exploring"
        
        # Frame 2: Auto-explore stopped with "All areas explored"
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "All areas explored"
        action2 = self.bot_input.next_action(self.mock_game_state)
        assert action2 == {'start_auto_explore': True}, "Should try to restart auto-explore"
        
        # Frames 3-4: Try to restart again (failed attempts)
        for attempt in range(2):
            mock_auto_explore.is_active = Mock(return_value=False)
            mock_auto_explore.stop_reason = "All areas explored"
            action = self.bot_input.next_action(self.mock_game_state)
            assert action == {'start_auto_explore': True}, f"Attempt {attempt+2}: Should try to restart"
        
        # Frame 5: After 3 failed attempts, should emit bot_abort_run
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "All areas explored"
        action5 = self.bot_input.next_action(self.mock_game_state)
        assert action5 == {'bot_abort_run': True}, "Should emit bot_abort_run after 3 failed restart attempts"
    
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
        """Bot should not emit bot_abort_run if stopped for other reasons."""
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
        for attempt in range(10):
            mock_auto_explore.is_active = Mock(return_value=False)
            mock_auto_explore.stop_reason = "Monster spotted: Orc"
            action = self.bot_input.next_action(self.mock_game_state)
            assert action == {'start_auto_explore': True}, f"Should always try to restart with monster stop reason (attempt {attempt})"
            assert action != {'bot_abort_run': True}, f"Should never emit bot_abort_run with non-'All areas explored' reason (attempt {attempt})"


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

