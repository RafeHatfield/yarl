"""Integration test for keyboard double-move bug.

This test simulates the ACTUAL game loop, not just KeyboardInputSource in isolation.
It tests the full path: pump_events -> next_action -> process_actions -> engine.update
"""

import pytest
import tcod.libtcodpy as libtcod
from unittest.mock import Mock, MagicMock, patch

from io_layer.keyboard_input import KeyboardInputSource
from game_actions import ActionProcessor
from engine import GameEngine
from game_states import GameStates
from components.component_registry import ComponentType


class TestKeyboardDoubleMoveRealIntegration:
    """Integration tests that simulate the actual game loop."""
    
    def test_full_loop_single_keypress_single_move(self):
        """Test that one keypress results in one move through the full loop.
        
        This simulates what happens in play_game_with_engine():
        1. pump_events_and_sleep() fills current_key
        2. next_action() processes the key and clears it
        3. Action is split into action/mouse_action
        4. process_actions() is called once
        5. Movement happens once
        
        If this test fails, it means the full integration has a double-processing bug.
        """
        # Create a real input source
        input_source = KeyboardInputSource()
        
        # Create a minimal game state
        game_state = Mock()
        game_state.game_state = GameStates.PLAYERS_TURN
        game_state.player = Mock()
        game_state.player.x = 5
        game_state.player.y = 5
        game_state.message_log = Mock()
        game_state.game_map = Mock()
        game_state.entities = []
        
        # Track how many times move() is called
        move_count = 0
        original_x = game_state.player.x
        
        def mock_move(dx, dy):
            nonlocal move_count
            move_count += 1
            game_state.player.x += dx
            game_state.player.y += dy
        
        game_state.player.move = mock_move
        game_state.player.get_component_optional = Mock(return_value=None)  # No auto-explore
        
        # Create a mock state manager
        state_manager = Mock()
        state_manager.state = game_state
        
        # Create action processor
        action_processor = ActionProcessor(state_manager)
        action_processor.turn_controller = Mock()  # Mock turn controller to avoid turn transitions
        
        # === FRAME 1: Simulate a RIGHT arrow keypress ===
        
        # Step 1: Simulate pump_events_and_sleep filling the key
        input_source.current_key.vk = libtcod.KEY_RIGHT
        input_source.current_key.c = 0
        input_source._events_pumped_externally = True
        
        # Step 2: Get action from input source
        combined_action = input_source.next_action(game_state)
        
        # Step 3: Split action
        mouse_action_keys = {'left_click', 'right_click', 'sidebar_click', 'sidebar_right_click'}
        action = {k: v for k, v in combined_action.items() if k not in mouse_action_keys}
        mouse_action = {k: v for k, v in combined_action.items() if k in mouse_action_keys}
        
        # Step 4: Process actions (this should call _handle_movement once)
        with patch('services.movement_service.MovementService') as mock_movement_service:
            # Mock the MovementService to track calls
            mock_service_instance = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_result.blocked_by_wall = False
            mock_result.blocked_by_entity = None
            mock_result.blocked_by_status = False
            mock_result.messages = []
            mock_service_instance.execute_movement.return_value = mock_result
            mock_movement_service.return_value = mock_service_instance
            
            action_processor.process_actions(action, mouse_action)
            
            # Verify MovementService.execute_movement was called ONCE
            assert mock_service_instance.execute_movement.call_count == 1, \
                f"Movement should be called once, but was called {mock_service_instance.execute_movement.call_count} times"
        
        # === FRAME 2: No new keypress (key was cleared) ===
        
        # Step 1: pump_events_and_sleep with no new event (key should stay clear)
        # In real game, sys_check_for_event would be called, but with no new event, key stays clear
        input_source._events_pumped_externally = True
        
        # Step 2: Get action (should be empty)
        combined_action2 = input_source.next_action(game_state)
        
        # Step 3: Split action
        action2 = {k: v for k, v in combined_action2.items() if k not in mouse_action_keys}
        mouse_action2 = {k: v for k, v in combined_action2.items() if k in mouse_action_keys}
        
        # Actions should be empty
        assert action2 == {}, f"Frame 2 should have no action, but got {action2}"
        assert mouse_action2 == {}, f"Frame 2 should have no mouse action, but got {mouse_action2}"
        
        # Step 4: process_actions with empty actions (should not move)
        with patch('services.movement_service.MovementService') as mock_movement_service2:
            mock_service_instance2 = Mock()
            mock_movement_service2.return_value = mock_service_instance2
            
            action_processor.process_actions(action2, mouse_action2)
            
            # Verify MovementService was NOT called in frame 2
            assert mock_service_instance2.execute_movement.call_count == 0, \
                "Movement should not be called in frame 2 (no action)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

