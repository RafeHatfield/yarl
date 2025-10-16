"""Test that ESC key properly exits all menu states.

BUG FIXED: ESC doesn't exit throw menu
ROOT CAUSE: _handle_exit method was registered but not implemented
SOLUTION: Implemented _handle_exit to handle ESC for all menu states
"""

import pytest
from unittest.mock import Mock, MagicMock

from game_actions import ActionProcessor
from game_states import GameStates


@pytest.fixture
def mock_state_manager():
    """Create a mock state manager for testing."""
    state_manager = Mock()
    state_manager.state = Mock()
    state_manager.state.current_state = GameStates.PLAYERS_TURN
    state_manager.state.player = Mock()
    state_manager.state.message_log = Mock()
    state_manager.state.game_map = Mock()
    state_manager.state.entities = []
    state_manager.state.fov_map = Mock()
    return state_manager


class TestMenuExitHandling:
    """Test that ESC key exits all menu states correctly."""
    
    def test_exit_from_show_inventory(self, mock_state_manager):
        """ESC should close inventory and return to PLAYERS_TURN."""
        # Start in inventory
        mock_state_manager.state.current_state = GameStates.SHOW_INVENTORY
        
        processor = ActionProcessor(mock_state_manager)
        
        # Press ESC (calls _handle_exit)
        processor._handle_exit(None)
        
        # Should return to PLAYERS_TURN
        mock_state_manager.set_game_state.assert_called_with(GameStates.PLAYERS_TURN)
    
    def test_exit_from_drop_inventory(self, mock_state_manager):
        """ESC should close drop menu and return to PLAYERS_TURN."""
        mock_state_manager.state.current_state = GameStates.DROP_INVENTORY
        
        processor = ActionProcessor(mock_state_manager)
        processor._handle_exit(None)
        
        mock_state_manager.set_game_state.assert_called_with(GameStates.PLAYERS_TURN)
    
    def test_exit_from_throw_select_item(self, mock_state_manager):
        """ESC should close throw menu and return to PLAYERS_TURN.
        
        BUG: This was broken! _handle_exit wasn't implemented!
        """
        mock_state_manager.state.current_state = GameStates.THROW_SELECT_ITEM
        
        processor = ActionProcessor(mock_state_manager)
        processor._handle_exit(None)
        
        # Should return to PLAYERS_TURN
        mock_state_manager.set_game_state.assert_called_with(GameStates.PLAYERS_TURN)
        
        # Should clear throw_target
        mock_state_manager.set_extra_data.assert_called_with("throw_target", None)
    
    def test_exit_from_throw_targeting(self, mock_state_manager):
        """ESC should cancel throw targeting and return to PLAYERS_TURN."""
        mock_state_manager.state.current_state = GameStates.THROW_TARGETING
        
        processor = ActionProcessor(mock_state_manager)
        processor._handle_exit(None)
        
        # Should return to PLAYERS_TURN
        mock_state_manager.set_game_state.assert_called_with(GameStates.PLAYERS_TURN)
        
        # Should clear both throw_item and throw_target
        assert mock_state_manager.set_extra_data.call_count == 2
    
    def test_exit_from_targeting(self, mock_state_manager):
        """ESC should cancel spell targeting and return to PLAYERS_TURN."""
        mock_state_manager.state.current_state = GameStates.TARGETING
        
        processor = ActionProcessor(mock_state_manager)
        processor._handle_exit(None)
        
        # Should return to PLAYERS_TURN
        mock_state_manager.set_game_state.assert_called_with(GameStates.PLAYERS_TURN)
        
        # Should clear targeting_item
        mock_state_manager.set_extra_data.assert_called_with("targeting_item", None)
    
    def test_exit_from_character_screen(self, mock_state_manager):
        """ESC should close character screen and return to PLAYERS_TURN."""
        mock_state_manager.state.current_state = GameStates.CHARACTER_SCREEN
        
        processor = ActionProcessor(mock_state_manager)
        processor._handle_exit(None)
        
        mock_state_manager.set_game_state.assert_called_with(GameStates.PLAYERS_TURN)


class TestExitActionRegistration:
    """Test that exit action is properly registered and callable."""
    
    def test_exit_action_registered(self, mock_state_manager):
        """Verify 'exit' action is in action_handlers."""
        processor = ActionProcessor(mock_state_manager)
        
        assert 'exit' in processor.action_handlers
    
    def test_exit_action_callable(self, mock_state_manager):
        """Verify 'exit' action handler is callable."""
        processor = ActionProcessor(mock_state_manager)
        
        exit_handler = processor.action_handlers['exit']
        assert callable(exit_handler)
    
    def test_exit_action_is_handle_exit(self, mock_state_manager):
        """Verify 'exit' maps to _handle_exit method."""
        processor = ActionProcessor(mock_state_manager)
        
        exit_handler = processor.action_handlers['exit']
        assert exit_handler == processor._handle_exit


class TestExitActionProcessing:
    """Test that exit actions are processed correctly."""
    
    def test_process_exit_action_from_throw_menu(self, mock_state_manager):
        """Full flow: User in throw menu → presses ESC → returns to game."""
        mock_state_manager.state.current_state = GameStates.THROW_SELECT_ITEM
        
        processor = ActionProcessor(mock_state_manager)
        
        # Simulate ESC press (action = {'exit': True})
        action = {'exit': True}
        mouse_action = {}
        
        processor.process_actions(action, mouse_action)
        
        # Should have returned to PLAYERS_TURN
        mock_state_manager.set_game_state.assert_called_with(GameStates.PLAYERS_TURN)
    
    def test_process_exit_action_from_inventory(self, mock_state_manager):
        """Full flow: User in inventory → presses ESC → returns to game."""
        mock_state_manager.state.current_state = GameStates.SHOW_INVENTORY
        
        processor = ActionProcessor(mock_state_manager)
        
        # Simulate ESC press
        action = {'exit': True}
        mouse_action = {}
        
        processor.process_actions(action, mouse_action)
        
        mock_state_manager.set_game_state.assert_called_with(GameStates.PLAYERS_TURN)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

