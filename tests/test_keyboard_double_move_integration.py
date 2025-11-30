"""Integration test for keyboard double-move bug.

This test verifies that one keypress results in exactly one action through
the input processing pipeline, and that the key is properly cleared after
processing to prevent double moves.
"""

import pytest
import tcod.libtcodpy as libtcod
from unittest.mock import Mock, patch

from io_layer.keyboard_input import KeyboardInputSource
from game_states import GameStates


class TestKeyboardDoubleMoveRealIntegration:
    """Integration tests that verify single keypress = single action."""
    
    @patch("io_layer.keyboard_input.handle_mouse")
    @patch("io_layer.keyboard_input.libtcod.sys_check_for_event")
    def test_full_loop_single_keypress_single_move(self, mock_check_event, mock_handle_mouse):
        """Test that one keypress produces one action and key is cleared.
        
        This test verifies the fix for the double-move bug by ensuring:
        1. next_action() processes the key correctly
        2. Key is cleared after processing (prevents double moves)
        3. Subsequent next_action() calls return empty (no phantom moves)
        
        If this test fails, it means the key clearing logic is broken.
        """
        # Setup mocks
        mock_handle_mouse.return_value = {}
        
        # Create input source
        input_source = KeyboardInputSource()
        
        # Create minimal game state
        game_state = Mock()
        game_state.game_state = GameStates.PLAYERS_TURN
        game_state.camera = None
        
        # === FRAME 1: Simulate a RIGHT arrow keypress ===
        
        # Set up the key for processing (sys_check_for_event is mocked, won't clear this)
        input_source.current_key.vk = libtcod.KEY_RIGHT
        input_source.current_key.c = 0
        
        # Get action from input source
        action1 = input_source.next_action(game_state)
        
        # Should have a move action
        assert "move" in action1, f"Expected 'move' action, got: {action1}"
        assert action1["move"] == (1, 0), f"Expected move (1,0) for RIGHT, got {action1['move']}"
        
        # CRITICAL: Key should be cleared after processing
        assert input_source.current_key.vk == libtcod.KEY_NONE, \
            "Key vk should be cleared to KEY_NONE after processing"
        assert input_source.current_key.c == 0, \
            "Key c should be 0 after processing"
        
        # === FRAME 2: No new keypress (key was already cleared) ===
        
        # Get action again - should be empty since key was cleared
        action2 = input_source.next_action(game_state)
        
        # Actions should be empty (no phantom keypress)
        assert action2 == {}, f"Frame 2 should have no action (key was cleared), but got {action2}"
        
        # === FRAME 3: Verify consistent empty behavior ===
        
        action3 = input_source.next_action(game_state)
        assert action3 == {}, f"Frame 3 should still have no action, but got {action3}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

