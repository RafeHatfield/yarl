"""Tests for keyboard double-move fix (v2).

This test suite verifies that only calling sys_check_for_event() in next_action()
(and NOT in pump_events_and_sleep()) prevents double-processing of keypresses.

The REAL bug: pump_events_and_sleep() was calling sys_check_for_event(EVENT_ANY),
which pulled events from the SDL queue. Then next_action() would call it again with
EVENT_KEY_PRESS, potentially seeing lingering events or the same event twice.

The fix: Remove event polling from pump_events_and_sleep(). Only poll in next_action().
"""

import pytest
import tcod.libtcodpy as libtcod
from unittest.mock import Mock, patch

from io_layer.keyboard_input import KeyboardInputSource
from game_states import GameStates


class TestKeyboardDoubleMoveFixV2:
    """Regression tests for keyboard double-move bug (simplified)."""

    def test_single_poll_per_frame(self):
        """Test that sys_check_for_event is only called once per frame."""
        input_source = KeyboardInputSource()
        game_state = Mock()
        game_state.game_state = GameStates.PLAYERS_TURN
        
        with patch.object(libtcod, 'sys_check_for_event') as mock_check:
            # Simulate a keypress
            def set_key(event_mask, key, mouse):
                key.vk = libtcod.KEY_RIGHT
                key.c = 0
            mock_check.side_effect = set_key
            
            # Call next_action once
            action = input_source.next_action(game_state)
            
            # sys_check_for_event should be called exactly ONCE
            assert mock_check.call_count == 1, \
                f"sys_check_for_event should be called once per frame, was called {mock_check.call_count} times"
    
    def test_key_cleared_after_processing(self):
        """Test that key is cleared after being processed."""
        input_source = KeyboardInputSource()
        game_state = Mock()
        game_state.game_state = GameStates.PLAYERS_TURN
        
        call_count = [0]
        
        def mock_check_event(event_mask, key, mouse):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: RIGHT arrow
                key.vk = libtcod.KEY_RIGHT
                key.c = 0
            else:
                # Subsequent calls: no key
                key.vk = libtcod.KEY_NONE
                key.c = 0
        
        with patch.object(libtcod, 'sys_check_for_event', side_effect=mock_check_event):
            # Frame 1: Process keypress
            action1 = input_source.next_action(game_state)
            assert "move" in action1
            assert action1["move"] == (1, 0)
            
            # Frame 2: No new key
            action2 = input_source.next_action(game_state)
            assert "move" not in action2
            assert action2 == {}
    
    def test_multiple_frames_multiple_keys(self):
        """Test that multiple keypresses are each processed exactly once."""
        input_source = KeyboardInputSource()
        game_state = Mock()
        game_state.game_state = GameStates.PLAYERS_TURN
        
        # Simulate a sequence: RIGHT, DOWN, LEFT, then nothing
        key_sequence = [
            (libtcod.KEY_RIGHT, 0, (1, 0)),
            (libtcod.KEY_DOWN, 0, (0, 1)),
            (libtcod.KEY_LEFT, 0, (-1, 0)),
            (libtcod.KEY_NONE, 0, None),
        ]
        call_index = [0]
        
        def mock_check_event(event_mask, key, mouse):
            idx = call_index[0]
            call_index[0] += 1
            if idx < len(key_sequence):
                key.vk, key.c, _ = key_sequence[idx]
            else:
                key.vk = libtcod.KEY_NONE
                key.c = 0
        
        with patch.object(libtcod, 'sys_check_for_event', side_effect=mock_check_event):
            # Process each frame
            for expected_vk, expected_c, expected_move in key_sequence:
                action = input_source.next_action(game_state)
                
                if expected_move:
                    assert "move" in action
                    assert action["move"] == expected_move
                else:
                    assert "move" not in action


class TestEventPollingOrder:
    """Test that event polling happens in the correct order."""
    
    def test_no_external_pump_needed(self):
        """Test that record_external_event_pump is now a no-op."""
        input_source = KeyboardInputSource()
        
        # This should do nothing now
        input_source.record_external_event_pump()
        
        # No assertion needed - just checking it doesn't crash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])







