"""Test that bot mode suppresses spammy console logs.

This test verifies that the console spam fix for bot mode works correctly:
- In normal keyboard mode: debug logs are printed to console
- In bot mode: per-frame action logs are suppressed to prevent console spam

The fix gates print statements in game_actions.py based on the is_bot_mode flag.
"""

import pytest
from io import StringIO
import sys
from game_actions import ActionProcessor
from state_management.state_config import StateManager
from game_states import GameStates


class MockGameState:
    """Mock game state for testing action processing."""
    
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


class TestBotModeLogSuppression:
    """Test that bot mode suppresses console spam."""
    
    def test_normal_mode_prints_action_logs(self):
        """Test that normal mode (is_bot_mode=False) prints action logs."""
        state_manager = MockStateManager()
        
        # Create action processor in normal mode (is_bot_mode=False)
        processor = ActionProcessor(state_manager, is_bot_mode=False)
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            # Process a wait action
            processor.process_actions({'wait': True}, {})
            
            # Get the printed output
            output = captured_output.getvalue()
            
            # Verify that the action was logged
            assert "KEYBOARD ACTION RECEIVED" in output, \
                "Normal mode should print 'KEYBOARD ACTION RECEIVED' message"
            assert "Calling handler for wait" in output, \
                "Normal mode should print 'Calling handler for' message"
        finally:
            # Restore stdout
            sys.stdout = sys.__stdout__
    
    def test_bot_mode_suppresses_action_logs(self):
        """Test that bot mode (is_bot_mode=True) suppresses action logs."""
        state_manager = MockStateManager()
        
        # Create action processor in bot mode (is_bot_mode=True)
        processor = ActionProcessor(state_manager, is_bot_mode=True)
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            # Process a wait action
            processor.process_actions({'wait': True}, {})
            
            # Get the printed output
            output = captured_output.getvalue()
            
            # Verify that the action logs are suppressed
            assert "KEYBOARD ACTION RECEIVED" not in output, \
                "Bot mode should NOT print 'KEYBOARD ACTION RECEIVED' message"
            assert "Calling handler for wait" not in output, \
                "Bot mode should NOT print 'Calling handler for' message"
        finally:
            # Restore stdout
            sys.stdout = sys.__stdout__
    
    def test_bot_mode_flag_defaults_to_false(self):
        """Test that is_bot_mode defaults to False for backward compatibility."""
        state_manager = MockStateManager()
        
        # Create action processor without specifying is_bot_mode
        processor = ActionProcessor(state_manager)
        
        # Verify that is_bot_mode defaults to False
        assert processor.is_bot_mode is False, \
            "is_bot_mode should default to False for backward compatibility"
    
    def test_bot_mode_still_processes_actions_correctly(self):
        """Test that bot mode still processes actions correctly (just doesn't log them)."""
        state_manager = MockStateManager()
        
        # Create action processor in bot mode
        processor = ActionProcessor(state_manager, is_bot_mode=True)
        
        # Verify that the wait handler is registered
        assert 'wait' in processor.action_handlers, \
            "Bot mode should still have wait handler registered"
        
        # Process a wait action (should work without errors)
        # We don't check the output, just that it doesn't raise an exception
        processor.process_actions({'wait': True}, {})
    
    def test_multiple_actions_in_bot_mode_no_spam(self):
        """Test that processing many actions in bot mode doesn't spam console."""
        state_manager = MockStateManager()
        processor = ActionProcessor(state_manager, is_bot_mode=True)
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            # Process 100 wait actions (simulating bot mode soak test)
            for _ in range(100):
                processor.process_actions({'wait': True}, {})
            
            # Get the printed output
            output = captured_output.getvalue()
            
            # Verify that no spam was printed
            assert "KEYBOARD ACTION RECEIVED" not in output, \
                "Bot mode should not print action logs even after many iterations"
            assert output.count("Calling handler") == 0, \
                "Bot mode should not print handler calls even after many iterations"
        finally:
            # Restore stdout
            sys.stdout = sys.__stdout__

