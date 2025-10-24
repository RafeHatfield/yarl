"""
Tests for victory state persistence bug.

Ensures that after picking up the Amulet of Yendor, the game state
remains AMULET_OBTAINED and doesn't get overwritten by turn transitions.

This is a regression test for the bug where:
1. Amulet picked up
2. State set to AMULET_OBTAINED
3. _transition_to_enemy_turn() called
4. State overwritten to PLAYERS_TURN
5. Portal entry check skipped (wrong state)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from game_states import GameStates
from game_actions import GameActions
from entity import Entity


class TestVictoryStatePersistence:
    """Tests that AMULET_OBTAINED state persists after amulet pickup."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock state manager
        self.state_manager = Mock()
        self.state_manager.state = Mock()
        
        # Create mock player
        self.player = Mock(spec=Entity)
        self.player.x = 10
        self.player.y = 10
        self.player.inventory = Mock()
        self.player.inventory.add_item = Mock()
        
        # Create mock amulet
        self.amulet = Mock(spec=Entity)
        self.amulet.x = 10
        self.amulet.y = 10
        self.amulet.item = Mock()
        self.amulet.triggers_victory = True
        
        # Set up state
        self.state_manager.state.player = self.player
        self.state_manager.state.entities = [self.amulet]
        self.state_manager.state.message_log = Mock()
        self.state_manager.state.game_map = Mock()
        self.state_manager.state.current_state = GameStates.PLAYERS_TURN
        
        # Track state changes
        self.state_changes = []
        def track_state(new_state):
            self.state_changes.append(new_state)
        self.state_manager.set_game_state = Mock(side_effect=track_state)
        
        # Create game actions handler
        self.turn_manager = Mock()
        self.game_actions = GameActions(self.state_manager, self.turn_manager)
    
    @patch('game_actions.get_victory_manager')
    def test_g_key_pickup_sets_amulet_obtained_and_returns(self, mock_get_victory_mgr):
        """Test that 'g' key pickup sets AMULET_OBTAINED and returns immediately.
        
        This is the regression test for the bug.
        """
        # Setup
        victory_mgr = Mock()
        victory_mgr.handle_amulet_pickup = Mock(return_value=True)
        mock_get_victory_mgr.return_value = victory_mgr
        
        # Simulate successful pickup
        self.player.inventory.add_item.return_value = [
            {'message': Mock(), 'item_added': self.amulet}
        ]
        
        # Execute
        self.game_actions._handle_pickup(None)
        
        # Verify state was set to AMULET_OBTAINED
        assert GameStates.AMULET_OBTAINED in self.state_changes, \
            "State should be set to AMULET_OBTAINED after amulet pickup"
        
        # Verify _transition_to_enemy_turn was NOT called (because we returned early)
        # If it was called, state would change again
        assert len(self.state_changes) == 1, \
            "State should only be set once (no transition to enemy turn)"
        
        # Verify victory manager was called
        assert victory_mgr.handle_amulet_pickup.called
    
    @patch('game_actions.get_victory_manager')
    def test_right_click_adjacent_pickup_sets_amulet_obtained_and_returns(self, mock_get_victory_mgr):
        """Test that right-click adjacent pickup sets AMULET_OBTAINED and returns."""
        # Setup
        victory_mgr = Mock()
        victory_mgr.handle_amulet_pickup = Mock(return_value=True)
        mock_get_victory_mgr.return_value = victory_mgr
        
        # Add required mocks for right-click handler
        self.state_manager.state.fov_map = Mock()
        self.state_manager.state.camera = Mock()
        
        # Amulet is adjacent (distance <= 1)
        self.player.distance_to = Mock(return_value=1)
        
        # Simulate successful pickup
        self.player.inventory.add_item.return_value = [
            {'message': Mock(), 'item_added': self.amulet}
        ]
        
        # Execute - right click on amulet position
        self.game_actions._handle_right_click((self.amulet.x, self.amulet.y))
        
        # Verify state was set to AMULET_OBTAINED
        assert GameStates.AMULET_OBTAINED in self.state_changes, \
            "State should be set to AMULET_OBTAINED after right-click amulet pickup"
        
        # Verify only one state change (no transition to enemy turn)
        assert len(self.state_changes) == 1, \
            "State should only be set once (handler should return after victory)"
    
    @patch('game_actions.get_victory_manager')
    def test_non_amulet_pickup_transitions_to_enemy_turn(self, mock_get_victory_mgr):
        """Test that picking up normal items still transitions to enemy turn.
        
        Ensures the fix didn't break normal item pickup.
        """
        # Setup - create normal item (not amulet)
        normal_item = Mock(spec=Entity)
        normal_item.x = 10
        normal_item.y = 10
        normal_item.item = Mock()
        normal_item.triggers_victory = False  # Not amulet
        
        self.state_manager.state.entities = [normal_item]
        
        # Simulate successful pickup
        self.player.inventory.add_item.return_value = [
            {'message': Mock(), 'item_added': normal_item}
        ]
        
        # Mock the turn transition function
        with patch('game_actions._transition_to_enemy_turn') as mock_transition:
            # Execute
            self.game_actions._handle_pickup(None)
            
            # Verify transition WAS called for normal items
            assert mock_transition.called, \
                "Normal item pickup should still transition to enemy turn"
            
            # Verify AMULET_OBTAINED was NOT set
            assert GameStates.AMULET_OBTAINED not in self.state_changes, \
                "AMULET_OBTAINED should not be set for normal items"
    
    @patch('game_actions.get_victory_manager')
    def test_amulet_pickup_failure_still_transitions(self, mock_get_victory_mgr):
        """Test that if victory sequence fails, turn still transitions normally."""
        # Setup
        victory_mgr = Mock()
        victory_mgr.handle_amulet_pickup = Mock(return_value=False)  # Failure
        mock_get_victory_mgr.return_value = victory_mgr
        
        # Simulate successful pickup
        self.player.inventory.add_item.return_value = [
            {'message': Mock(), 'item_added': self.amulet}
        ]
        
        # Mock the turn transition function
        with patch('game_actions._transition_to_enemy_turn') as mock_transition:
            # Execute
            self.game_actions._handle_pickup(None)
            
            # Verify transition WAS called (because victory failed)
            assert mock_transition.called, \
                "If victory sequence fails, should still transition to enemy turn"


class TestPortalEntryRequiresAmuletObtainedState:
    """Tests that portal entry only works in AMULET_OBTAINED state."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock state manager
        self.state_manager = Mock()
        self.state_manager.state = Mock()
        
        # Create mock player
        self.player = Mock(spec=Entity)
        self.player.x = 10
        self.player.y = 10
        self.player.move = Mock()
        
        # Create mock portal
        self.portal = Mock(spec=Entity)
        self.portal.x = 11
        self.portal.y = 10
        self.portal.is_portal = True
        
        # Set up state
        self.state_manager.state.player = self.player
        self.state_manager.state.entities = [self.portal]
        self.state_manager.state.message_log = Mock()
        self.state_manager.state.game_map = Mock()
        self.state_manager.state.game_map.is_blocked = Mock(return_value=False)
        self.state_manager.state.fov_map = Mock()
        self.state_manager.state.camera = Mock()
        
        # Create game actions handler
        self.turn_manager = Mock()
        self.game_actions = GameActions(self.state_manager, self.turn_manager)
    
    @patch('game_actions.get_victory_manager')
    def test_portal_entry_checked_in_amulet_obtained_state(self, mock_get_victory_mgr):
        """Test that portal entry is checked when state is AMULET_OBTAINED."""
        # Setup
        self.state_manager.state.current_state = GameStates.AMULET_OBTAINED
        
        victory_mgr = Mock()
        victory_mgr.check_portal_entry = Mock(return_value=True)
        victory_mgr.enter_portal = Mock()
        mock_get_victory_mgr.return_value = victory_mgr
        
        # Execute - move player onto portal
        self.player.move = Mock()
        self.game_actions._handle_movement({'move': (1, 0)})  # Move right onto portal
        
        # Verify portal entry was checked
        assert victory_mgr.check_portal_entry.called, \
            "Portal entry should be checked in AMULET_OBTAINED state"
        
        # Verify confrontation triggered
        self.state_manager.set_game_state.assert_called_with(GameStates.CONFRONTATION)
    
    def test_portal_entry_not_checked_in_players_turn_state(self):
        """Test that portal entry is NOT checked in normal PLAYERS_TURN state.
        
        This is the bug symptom - if state reverts to PLAYERS_TURN,
        portal entry check is skipped.
        """
        # Setup - wrong state (this is what happened in the bug)
        self.state_manager.state.current_state = GameStates.PLAYERS_TURN
        
        with patch('game_actions.get_victory_manager') as mock_get_victory_mgr:
            victory_mgr = Mock()
            victory_mgr.check_portal_entry = Mock(return_value=True)
            mock_get_victory_mgr.return_value = victory_mgr
            
            # Move player onto portal position
            self.player.x = self.portal.x
            self.player.y = self.portal.y
            
            # Execute movement
            with patch('game_actions._transition_to_enemy_turn'):
                self.game_actions._handle_movement({'move': (0, 0)})
            
            # Verify portal entry was NOT checked (wrong state)
            assert not victory_mgr.check_portal_entry.called, \
                "Portal entry should NOT be checked in PLAYERS_TURN state"
    
    @patch('game_actions.get_victory_manager')
    def test_state_persistence_through_movement(self, mock_get_victory_mgr):
        """Integration test: State stays AMULET_OBTAINED through movement."""
        # Setup
        self.state_manager.state.current_state = GameStates.AMULET_OBTAINED
        
        victory_mgr = Mock()
        victory_mgr.check_portal_entry = Mock(return_value=False)  # Not on portal yet
        mock_get_victory_manager.return_value = victory_mgr
        
        # Move player (not onto portal)
        with patch('game_actions._transition_to_enemy_turn') as mock_transition:
            self.game_actions._handle_movement({'move': (0, 1)})
            
            # Verify turn still transitions (movement takes a turn)
            assert mock_transition.called, \
                "Movement should still end turn in AMULET_OBTAINED state"
            
            # But state should have been preserved during portal check
            # (The check runs BEFORE transition)
            assert victory_mgr.check_portal_entry.called, \
                "Portal check should run while state is still AMULET_OBTAINED"


class TestStatePersistenceScenario:
    """End-to-end scenario test for the bug."""
    
    @patch('game_actions.get_victory_manager')
    @patch('game_actions._transition_to_enemy_turn')
    def test_complete_victory_sequence_scenario(self, mock_transition, mock_get_victory_mgr):
        """Test complete scenario: pickup amulet, move, enter portal.
        
        This reproduces the exact user flow that triggered the bug.
        """
        # Setup victory manager
        victory_mgr = Mock()
        victory_mgr.handle_amulet_pickup = Mock(return_value=True)
        victory_mgr.check_portal_entry = Mock(return_value=True)
        victory_mgr.enter_portal = Mock()
        mock_get_victory_mgr.return_value = victory_mgr
        
        # Setup game state
        state_manager = Mock()
        state_manager.state = Mock()
        
        player = Mock(spec=Entity)
        player.x = 10
        player.y = 10
        player.inventory = Mock()
        
        amulet = Mock(spec=Entity)
        amulet.x = 10
        amulet.y = 10
        amulet.item = Mock()
        amulet.triggers_victory = True
        
        portal = Mock(spec=Entity)
        portal.x = 11
        portal.y = 10
        portal.is_portal = True
        
        state_manager.state.player = player
        state_manager.state.entities = [amulet, portal]
        state_manager.state.message_log = Mock()
        state_manager.state.game_map = Mock()
        state_manager.state.game_map.is_blocked = Mock(return_value=False)
        state_manager.state.fov_map = Mock()
        state_manager.state.camera = Mock()
        state_manager.state.current_state = GameStates.PLAYERS_TURN
        
        # Track state changes
        state_changes = []
        def track_state(new_state):
            state_changes.append(new_state)
            state_manager.state.current_state = new_state
        state_manager.set_game_state = Mock(side_effect=track_state)
        
        turn_manager = Mock()
        game_actions = GameActions(state_manager, turn_manager)
        
        # STEP 1: Pick up amulet
        player.inventory.add_item.return_value = [
            {'message': Mock(), 'item_added': amulet}
        ]
        game_actions._handle_pickup(None)
        
        # Verify state is AMULET_OBTAINED and didn't transition
        assert GameStates.AMULET_OBTAINED in state_changes
        assert len([s for s in state_changes if s == GameStates.AMULET_OBTAINED]) == 1
        assert state_manager.state.current_state == GameStates.AMULET_OBTAINED
        
        # STEP 2: Move onto portal
        player.move = Mock()
        game_actions._handle_movement({'move': (1, 0)})
        
        # Verify portal entry was checked
        assert victory_mgr.check_portal_entry.called
        
        # Verify confrontation triggered
        assert GameStates.CONFRONTATION in state_changes
        
        print("✅ Complete victory sequence test passed!")
        print(f"   State changes: {[s.name for s in state_changes]}")

