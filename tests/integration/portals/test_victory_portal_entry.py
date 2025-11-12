"""
Tests for victory portal entry detection.

These tests ensure that stepping on the portal triggers the confrontation.
"""

import pytest
from unittest.mock import Mock, MagicMock
from victory_manager import VictoryManager
from entity import Entity


from components.component_registry import ComponentType
class TestPortalEntryDetection:
    """Tests for check_portal_entry method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.victory_mgr = VictoryManager()
        
        # Create mock player
        self.player = Mock(spec=Entity)
        self.player.x = 10
        self.player.y = 10
        
        # Create mock portal entity
        self.portal = Mock(spec=Entity)
        self.portal.x = 11
        self.portal.y = 10
        self.portal.is_portal = True
        
        # Create entities list
        self.entities = [self.portal]
    
    def test_portal_entry_detected_when_player_on_portal(self):
        """Portal entry should be detected when player stands on portal."""
        # Place player on portal
        self.player.x = 11
        self.player.y = 10
        
        result = self.victory_mgr.check_portal_entry(self.player, self.entities)
        
        assert result is True, "Portal entry should be detected when player is on portal"
    
    def test_portal_entry_not_detected_when_player_adjacent(self):
        """Portal entry should NOT be detected when player is adjacent to portal."""
        # Player at (10, 10), portal at (11, 10) - adjacent but not on it
        result = self.victory_mgr.check_portal_entry(self.player, self.entities)
        
        assert result is False, "Portal entry should not be detected when player is only adjacent"
    
    def test_portal_entry_not_detected_when_player_far_away(self):
        """Portal entry should NOT be detected when player is far from portal."""
        # Player at (10, 10), portal at (11, 10), but move player far away
        self.player.x = 5
        self.player.y = 5
        
        result = self.victory_mgr.check_portal_entry(self.player, self.entities)
        
        assert result is False, "Portal entry should not be detected when player is far away"
    
    def test_portal_entry_works_with_multiple_entities(self):
        """Portal entry detection should work when there are multiple entities."""
        # Add other entities (monsters, items, etc.)
        other_entity1 = Mock(spec=Entity)
        other_entity1.x = 5
        other_entity1.y = 5
        other_entity1.is_portal = False
        
        other_entity2 = Mock(spec=Entity)
        other_entity2.x = 15
        other_entity2.y = 15
        # No is_portal attribute (should be treated as False)
        
        self.entities = [other_entity1, self.portal, other_entity2]
        
        # Place player on portal
        self.player.x = 11
        self.player.y = 10
        
        result = self.victory_mgr.check_portal_entry(self.player, self.entities)
        
        assert result is True, "Portal entry should be detected even with other entities present"
    
    def test_portal_entry_not_detected_with_no_portal_entities(self):
        """Portal entry should not be detected when no portal entities exist."""
        # Empty entities list (no portal)
        self.entities = []
        
        # Place player at what would be portal location
        self.player.x = 11
        self.player.y = 10
        
        result = self.victory_mgr.check_portal_entry(self.player, self.entities)
        
        assert result is False, "Portal entry should not be detected when no portal exists"
    
    def test_portal_entry_not_detected_for_non_portal_entity(self):
        """Portal entry should not trigger for entities without is_portal=True."""
        # Create entity at player location but without is_portal
        fake_portal = Mock(spec=Entity)
        fake_portal.x = 10
        fake_portal.y = 10
        fake_portal.is_portal = False  # Explicitly False
        
        self.entities = [fake_portal]
        
        result = self.victory_mgr.check_portal_entry(self.player, self.entities)
        
        assert result is False, "Portal entry should not trigger for non-portal entities"
    
    def test_portal_entry_handles_missing_is_portal_attribute(self):
        """Portal entry should handle entities without is_portal attribute gracefully."""
        # Create entity without is_portal attribute
        entity_without_portal_attr = Mock(spec=Entity)
        entity_without_portal_attr.x = 10
        entity_without_portal_attr.y = 10
        # Don't set is_portal attribute at all
        
        self.entities = [entity_without_portal_attr]
        
        # Should not crash, should return False
        result = self.victory_mgr.check_portal_entry(self.player, self.entities)
        
        assert result is False, "Should handle missing is_portal attribute gracefully"
    
    def test_portal_entry_works_at_map_edges(self):
        """Portal entry should work correctly at map edges."""
        # Test at (0, 0)
        self.player.x = 0
        self.player.y = 0
        self.portal.x = 0
        self.portal.y = 0
        
        result = self.victory_mgr.check_portal_entry(self.player, self.entities)
        
        assert result is True, "Portal entry should work at map edge (0, 0)"
    
    def test_portal_entry_exact_coordinates_required(self):
        """Portal entry requires EXACT coordinate match, not just distance."""
        # Portal at (11, 10), player at (10, 11) - same distance but different coords
        self.player.x = 10
        self.player.y = 11
        self.portal.x = 11
        self.portal.y = 10
        
        result = self.victory_mgr.check_portal_entry(self.player, self.entities)
        
        assert result is False, "Portal entry requires exact x,y match, not just proximity"


class TestPortalEntryIntegration:
    """Integration tests for portal entry flow with game actions."""
    
    def test_portal_in_inventory_does_not_trigger(self):
        """Portal in player's inventory should not trigger entry.
        
        This is current expected behavior - portal must be on ground.
        Future: Add "use portal" action for inventory portals.
        """
        victory_mgr = VictoryManager()
        
        player = Mock(spec=Entity)
        player.x = 10
        player.y = 10
        
        # Portal in inventory (not in entities list)
        portal = Mock(spec=Entity)
        portal.x = 10  # Would match player position
        portal.y = 10
        portal.is_portal = True
        # But portal is NOT in entities list (it's in inventory)
        
        entities = []  # Empty - no portal on ground
        
        result = victory_mgr.check_portal_entry(player, entities)
        
        assert result is False, "Portal in inventory should not trigger entry (must be on ground)"
    
    def test_dropped_portal_triggers_entry(self):
        """Portal that was dropped should trigger entry when stepped on."""
        victory_mgr = VictoryManager()
        
        player = Mock(spec=Entity)
        player.x = 10
        player.y = 10
        
        # Portal that was dropped (back in entities list)
        portal = Mock(spec=Entity)
        portal.x = 10
        portal.y = 10
        portal.is_portal = True
        
        entities = [portal]  # Portal is on ground
        
        result = victory_mgr.check_portal_entry(player, entities)
        
        assert result is True, "Dropped portal should trigger entry when stepped on"
    
    def test_multiple_portals_any_triggers_entry(self):
        """If multiple portals exist, stepping on any should trigger entry.
        
        Edge case: Player somehow has 2 portals on the map.
        """
        victory_mgr = VictoryManager()
        
        player = Mock(spec=Entity)
        player.x = 10
        player.y = 10
        
        # Two portals at different locations
        portal1 = Mock(spec=Entity)
        portal1.x = 15
        portal1.y = 15
        portal1.is_portal = True
        
        portal2 = Mock(spec=Entity)
        portal2.x = 10
        portal2.y = 10
        portal2.is_portal = True
        
        entities = [portal1, portal2]
        
        result = victory_mgr.check_portal_entry(player, entities)
        
        assert result is True, "Any portal at player location should trigger entry"


class TestPortalEntryGameStateIntegration:
    """Tests for portal entry integration with game states."""
    
    def test_portal_entry_requires_amulet_obtained_state(self):
        """Portal entry should only work in AMULET_OBTAINED game state.
        
        This test documents the expected behavior:
        - Player can only enter portal AFTER obtaining amulet
        - Portal entry is checked during movement in AMULET_OBTAINED state
        """
        # This is more of a documentation test
        # The actual state check happens in game_actions.py _handle_movement
        # We're documenting that check_portal_entry alone doesn't care about state
        
        victory_mgr = VictoryManager()
        
        player = Mock(spec=Entity)
        player.x = 10
        player.y = 10
        
        portal = Mock(spec=Entity)
        portal.x = 10
        portal.y = 10
        portal.is_portal = True
        
        entities = [portal]
        
        # check_portal_entry doesn't know about game states
        # It just checks coordinates
        result = victory_mgr.check_portal_entry(player, entities)
        
        assert result is True, "check_portal_entry returns True based on coordinates"
        # NOTE: Game state check happens in game_actions.py, not here
        # This documents that the method is state-agnostic

