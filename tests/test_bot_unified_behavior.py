"""Test that --bot and --bot-soak use identical bot behavior logic.

This test suite verifies that both regular bot mode and bot-soak mode
delegate to BotBrain for decision-making, ensuring all survivability
features (potion-drinking, equipment, loot, stairs) work in both modes.

The only difference between modes is the harness (single vs multi-run),
not the bot's in-game behavior.
"""

import pytest
from unittest.mock import Mock, patch

from io_layer.bot_input import BotInputSource
from game_states import GameStates
from components.component_registry import ComponentType


class TestUnifiedBotBehavior:
    """Test that bot behavior is identical in --bot and --bot-soak modes."""
    
    def test_regular_bot_mode_uses_botbrain(self):
        """Regular --bot mode should use BotBrain for decisions."""
        bot_input = BotInputSource()
        
        # Mock game state (regular bot mode)
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.constants = {"bot_soak_mode": False}  # Regular bot mode
        
        # Mock player
        player = Mock()
        player.get_component_optional = Mock(return_value=None)  # No AutoExplore
        game_state.player = player
        
        # Spy on BotBrain
        with patch.object(bot_input.bot_brain, 'decide_action', return_value={'start_auto_explore': True}) as mock_brain:
            action = bot_input.next_action(game_state)
        
        # Assert: BotBrain was called
        mock_brain.assert_called_once()
        assert action == {'start_auto_explore': True}
    
    def test_soak_mode_uses_botbrain(self):
        """Bot-soak mode should use BotBrain for decisions (same as regular bot)."""
        bot_input = BotInputSource()
        
        # Mock game state (soak mode)
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.constants = {"bot_soak_mode": True}  # Soak mode
        
        # Mock player
        player = Mock()
        player.get_component_optional = Mock(return_value=None)  # No AutoExplore
        game_state.player = player
        
        # Spy on BotBrain
        with patch.object(bot_input.bot_brain, 'decide_action', return_value={'start_auto_explore': True}) as mock_brain:
            action = bot_input.next_action(game_state)
        
        # Assert: BotBrain was called (same as regular bot mode)
        mock_brain.assert_called_once()
        assert action == {'start_auto_explore': True}
    
    def test_both_modes_get_same_action_from_botbrain(self):
        """Both modes should return identical actions from BotBrain."""
        # Test with LOOT action
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        player = Mock()
        player.get_component_optional = Mock(return_value=None)
        game_state.player = player
        
        # Test regular bot mode
        game_state.constants = {"bot_soak_mode": False}
        bot_input_regular = BotInputSource()
        
        with patch.object(bot_input_regular.bot_brain, 'decide_action', return_value={'pickup': True}):
            action_regular = bot_input_regular.next_action(game_state)
        
        # Test soak mode
        game_state.constants = {"bot_soak_mode": True}
        bot_input_soak = BotInputSource()
        
        with patch.object(bot_input_soak.bot_brain, 'decide_action', return_value={'pickup': True}):
            action_soak = bot_input_soak.next_action(game_state)
        
        # Assert: Both return same action
        assert action_regular == action_soak == {'pickup': True}, \
            "Both modes should return identical actions from BotBrain"

