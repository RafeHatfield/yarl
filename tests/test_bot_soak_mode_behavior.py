"""Test bot soak mode behavior (bypasses BotBrain combat logic).

Tests verify that in soak mode, BotInputSource skips BotBrain delegation
and uses only auto-explore behavior, preventing infinite loops when monsters are visible.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from io_layer.bot_input import BotInputSource
from components.auto_explore import AutoExplore
from game_states import GameStates


class TestSoakModeDetection:
    """Test soak mode detection in BotInputSource."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.bot_input = BotInputSource()
        self.mock_game_state = Mock()
        self.mock_player = Mock()
        self.mock_game_state.current_state = GameStates.PLAYERS_TURN
        self.mock_game_state.player = self.mock_player
    
    def test_is_soak_mode_detects_soak_flag(self):
        """_is_soak_mode should return True when constants["bot_soak_mode"] is True."""
        self.mock_game_state.constants = {"bot_soak_mode": True}
        
        result = self.bot_input._is_soak_mode(self.mock_game_state)
        
        assert result is True, "Should detect soak mode when flag is True"
    
    def test_is_soak_mode_detects_non_soak_mode(self):
        """_is_soak_mode should return False when constants["bot_soak_mode"] is False or missing."""
        # Test with False flag
        self.mock_game_state.constants = {"bot_soak_mode": False}
        result = self.bot_input._is_soak_mode(self.mock_game_state)
        assert result is False, "Should return False when flag is False"
        
        # Test with missing flag
        self.mock_game_state.constants = {}
        result = self.bot_input._is_soak_mode(self.mock_game_state)
        assert result is False, "Should return False when flag is missing"
        
        # Test with None game_state
        result = self.bot_input._is_soak_mode(None)
        assert result is False, "Should return False when game_state is None"
        
        # Test with game_state without constants
        mock_state_no_constants = Mock()
        del mock_state_no_constants.constants
        result = self.bot_input._is_soak_mode(mock_state_no_constants)
        assert result is False, "Should return False when constants attribute is missing"


class TestSoakModeBypassesBotBrain:
    """Test that soak mode bypasses BotBrain combat logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.bot_input = BotInputSource()
        self.mock_game_state = Mock()
        self.mock_player = Mock()
        self.mock_game_state.current_state = GameStates.PLAYERS_TURN
        self.mock_game_state.player = self.mock_player
        self.mock_game_state.constants = {"bot_soak_mode": True}  # Soak mode enabled
    
    def test_soak_mode_skips_botbrain_when_autoexplore_not_active(self):
        """In soak mode, BotBrain should not be called when auto-explore is not active."""
        # Mock auto-explore component
        mock_auto_explore = Mock(spec=AutoExplore)
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = None
        self.mock_player.get_component_optional = Mock(return_value=mock_auto_explore)
        
        # Spy on BotBrain to verify it's not called
        with patch.object(self.bot_input.bot_brain, 'decide_action') as mock_brain:
            action = self.bot_input.next_action(self.mock_game_state)
            
            # BotBrain should NOT be called in soak mode
            mock_brain.assert_not_called()
            
            # Should return start_auto_explore action instead
            assert action == {'start_auto_explore': True}, \
                "Soak mode should return start_auto_explore, not BotBrain action"
    
    def test_soak_mode_returns_empty_when_autoexplore_active(self):
        """In soak mode, should return empty action when auto-explore is active."""
        # Mock auto-explore component as active
        mock_auto_explore = Mock(spec=AutoExplore)
        mock_auto_explore.is_active = Mock(return_value=True)
        mock_auto_explore.stop_reason = None
        self.mock_player.get_component_optional = Mock(return_value=mock_auto_explore)
        
        # Spy on BotBrain to verify it's not called
        with patch.object(self.bot_input.bot_brain, 'decide_action') as mock_brain:
            action = self.bot_input.next_action(self.mock_game_state)
            
            # BotBrain should NOT be called in soak mode
            mock_brain.assert_not_called()
            
            # Should return empty action to let auto-explore handle movement
            assert action == {}, "Soak mode should return empty action when auto-explore is active"
    
    def test_soak_mode_handles_fully_explored_without_botbrain(self):
        """In soak mode, fully explored condition should immediately trigger bot_abort_run without BotBrain."""
        # Mock auto-explore component stopped with "All areas explored"
        mock_auto_explore = Mock(spec=AutoExplore)
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "All areas explored"
        self.mock_player.get_component_optional = Mock(return_value=mock_auto_explore)
        
        # Spy on BotBrain to verify it's not called
        with patch.object(self.bot_input.bot_brain, 'decide_action') as mock_brain:
            # Should immediately emit bot_abort_run when fully explored
            action = self.bot_input.next_action(self.mock_game_state)
            mock_brain.assert_not_called()
            assert action == {'bot_abort_run': True}, \
                "Soak mode should immediately emit bot_abort_run when fully explored, without BotBrain"


class TestNonSoakModeUsesBotBrain:
    """Test that non-soak bot mode uses BotBrain for combat behavior."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.bot_input = BotInputSource()
        self.mock_game_state = Mock()
        self.mock_player = Mock()
        self.mock_game_state.current_state = GameStates.PLAYERS_TURN
        self.mock_game_state.player = self.mock_player
        self.mock_game_state.constants = {"bot_soak_mode": False}  # Regular bot mode
    
    def test_non_soak_mode_calls_botbrain(self):
        """In non-soak mode, BotBrain should be called for combat decisions."""
        # Mock auto-explore component not active
        mock_auto_explore = Mock(spec=AutoExplore)
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = None
        self.mock_player.get_component_optional = Mock(return_value=mock_auto_explore)
        
        # Mock BotBrain to return a combat action
        mock_combat_action = {"move": (1, 0)}
        with patch.object(self.bot_input.bot_brain, 'decide_action', return_value=mock_combat_action) as mock_brain:
            action = self.bot_input.next_action(self.mock_game_state)
            
            # BotBrain should be called in non-soak mode
            mock_brain.assert_called_once_with(self.mock_game_state)
            
            # Should return BotBrain's action
            assert action == mock_combat_action, \
                "Non-soak mode should return BotBrain action"
    
    def test_non_soak_mode_falls_back_to_autoexplore_if_botbrain_fails(self):
        """In non-soak mode, if BotBrain fails, should fall back to auto-explore."""
        # Mock auto-explore component not active
        mock_auto_explore = Mock(spec=AutoExplore)
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = None
        self.mock_player.get_component_optional = Mock(return_value=mock_auto_explore)
        
        # Mock BotBrain to return empty dict (no action)
        with patch.object(self.bot_input.bot_brain, 'decide_action', return_value={}) as mock_brain:
            action = self.bot_input.next_action(self.mock_game_state)
            
            # BotBrain should be called
            mock_brain.assert_called_once()
            
            # Should fall back to start_auto_explore
            assert action == {'start_auto_explore': True}, \
                "Non-soak mode should fall back to auto-explore if BotBrain returns empty"


class TestSoakModeMonsterHandling:
    """Test that soak mode handles monsters correctly (treats as obstacles, no combat)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.bot_input = BotInputSource()
        self.mock_game_state = Mock()
        self.mock_player = Mock()
        self.mock_game_state.current_state = GameStates.PLAYERS_TURN
        self.mock_game_state.player = self.mock_player
        self.mock_game_state.constants = {"bot_soak_mode": True}  # Soak mode enabled
    
    def test_soak_mode_does_not_move_into_monsters(self):
        """In soak mode, bot should not generate movement actions that move into monsters.
        
        This test verifies that BotBrain's combat logic (which would try to move toward
        enemies) is bypassed, preventing the infinite loop bug where the bot repeatedly
        tries to move into a monster's tile.
        """
        # Mock auto-explore component not active (simulating monster encounter stopping it)
        mock_auto_explore = Mock(spec=AutoExplore)
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "Monster spotted: Orc"
        self.mock_player.get_component_optional = Mock(return_value=mock_auto_explore)
        
        # Spy on BotBrain to verify it's not called
        with patch.object(self.bot_input.bot_brain, 'decide_action') as mock_brain:
            action = self.bot_input.next_action(self.mock_game_state)
            
            # BotBrain should NOT be called (would generate move toward monster)
            mock_brain.assert_not_called()
            
            # Should return start_auto_explore to restart exploration (auto-explore will path around)
            assert action == {'start_auto_explore': True}, \
                "Soak mode should restart auto-explore, not move into monster"
            
            # Verify action is NOT a direct movement action
            assert 'move' not in action, \
                "Soak mode should not generate direct movement actions toward monsters"
    
    def test_soak_mode_autoexplore_paths_around_monsters(self):
        """In soak mode, auto-explore should handle pathfinding around monsters."""
        # Mock auto-explore component as active (exploring around monster)
        mock_auto_explore = Mock(spec=AutoExplore)
        mock_auto_explore.is_active = Mock(return_value=True)
        mock_auto_explore.stop_reason = None
        self.mock_player.get_component_optional = Mock(return_value=mock_auto_explore)
        
        # Spy on BotBrain to verify it's not called
        with patch.object(self.bot_input.bot_brain, 'decide_action') as mock_brain:
            action = self.bot_input.next_action(self.mock_game_state)
            
            # BotBrain should NOT be called
            mock_brain.assert_not_called()
            
            # Should return empty action to let auto-explore handle movement
            assert action == {}, \
                "Soak mode should return empty action when auto-explore is active, letting it path around monsters"

