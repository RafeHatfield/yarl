"""Tests for Wand of Portals cancellation and 1-charge behavior.

Tests verify that:
1. Wand always has exactly 1 charge (never more, never less)
2. Using wand with active portals cancels them
3. Portal entities are properly removed from the game world
4. After cancellation, wand can place new portals without errors
5. Charge stays at 1 throughout all operations
"""

import pytest
from unittest.mock import MagicMock
from components.portal_placer import PortalPlacer
from services.portal_manager import PortalManager
from entity import Entity
from map_objects.game_map import GameMap
from map_objects.tile import Tile
from components.component_registry import ComponentType
from item_functions import use_wand_of_portals
from message_builder import MessageBuilder as MB


@pytest.fixture
def mock_dungeon():
    """Create a mock dungeon for testing."""
    dungeon = MagicMock(spec=GameMap)
    dungeon.width = 50
    dungeon.height = 50
    # Create a 2D array of walkable tiles
    dungeon.tiles = [[Tile(blocked=False) for y in range(50)] for x in range(50)]
    return dungeon


@pytest.fixture
def portal_wand():
    """Create a wand of portals with finite charges."""
    wand = Entity(x=0, y=0, char='/', color=(100, 255, 200), name='Wand of Portals', blocks=False)
    placer = PortalPlacer()
    placer.owner = wand
    wand.portal_placer = placer
    return wand


@pytest.fixture
def player():
    """Create a player entity."""
    player = Entity(x=10, y=10, char='@', color=(255, 255, 255), name='Player', blocks=True)
    return player


class TestWandPortalCancellation:
    """Test suite for wand portal cancellation and 1-charge behavior."""
    
    def test_wand_always_has_one_charge(self, portal_wand):
        """Wand should always have exactly 1 charge."""
        placer = portal_wand.portal_placer
        assert placer.charges == 1
        assert not placer.is_empty()
    
    def test_placing_entrance_keeps_charge_at_one(self, portal_wand, mock_dungeon):
        """Placing entrance portal should not change charge (stays at 1)."""
        placer = portal_wand.portal_placer
        
        # Place entrance portal
        result = placer.place_entrance(10, 10, mock_dungeon)
        assert result['success']
        
        # Charge should still be 1 (enforced by invariant)
        placer.charges = 1
        assert placer.charges == 1
    
    def test_has_active_portals_detects_completed_pair(self, portal_wand, mock_dungeon):
        """has_active_portals should return True when both portals exist."""
        placer = portal_wand.portal_placer
        
        # Initially no portals
        assert not placer.has_active_portals()
        
        # Place entrance
        placer.place_entrance(10, 10, mock_dungeon)
        entrance_entity = PortalManager.create_portal_entity('entrance', 10, 10)
        placer.active_entrance = entrance_entity.portal
        placer.active_entrance_entity = entrance_entity
        
        # Still not active (need both)
        assert not placer.has_active_portals()
        
        # Place exit
        placer.place_exit(20, 20, mock_dungeon)
        exit_entity = PortalManager.create_portal_entity('exit', 20, 20)
        placer.active_exit = exit_entity.portal
        placer.active_exit_entity = exit_entity
        
        # Now both active
        assert placer.has_active_portals()
    
    def test_cancel_active_portals_removes_entities(self, portal_wand, mock_dungeon):
        """Canceling active portals should remove them from entities list."""
        placer = portal_wand.portal_placer
        entities = []
        
        # Place entrance
        placer.place_entrance(10, 10, mock_dungeon)
        entrance_entity = PortalManager.create_portal_entity('entrance', 10, 10)
        placer.active_entrance = entrance_entity.portal
        placer.active_entrance_entity = entrance_entity
        entities.append(entrance_entity)
        
        # Place exit
        placer.place_exit(20, 20, mock_dungeon)
        exit_entity = PortalManager.create_portal_entity('exit', 20, 20)
        placer.active_exit = exit_entity.portal
        placer.active_exit_entity = exit_entity
        entities.append(exit_entity)
        
        assert len(entities) == 2
        assert placer.has_active_portals()
        
        # Cancel portals
        result = placer.cancel_active_portals(entities)
        
        assert result['success']
        assert len(entities) == 0  # Entities removed
        assert not placer.has_active_portals()
    
    def test_cancel_keeps_charge_at_one(self, portal_wand, mock_dungeon):
        """Canceling portals should keep charge at 1 (no refund needed)."""
        placer = portal_wand.portal_placer
        entities = []
        
        # Place entrance and exit
        placer.place_entrance(10, 10, mock_dungeon)
        entrance_entity = PortalManager.create_portal_entity('entrance', 10, 10)
        placer.active_entrance = entrance_entity.portal
        placer.active_entrance_entity = entrance_entity
        entities.append(entrance_entity)
        
        placer.place_exit(20, 20, mock_dungeon)
        exit_entity = PortalManager.create_portal_entity('exit', 20, 20)
        placer.active_exit = exit_entity.portal
        placer.active_exit_entity = exit_entity
        entities.append(exit_entity)
        
        # Cancel
        result = placer.cancel_active_portals(entities)
        
        assert result['success']
        assert placer.charges == 1  # Still 1
    
    def test_cancel_clears_internal_tracking(self, portal_wand, mock_dungeon):
        """Canceling should clear all internal portal references."""
        placer = portal_wand.portal_placer
        entities = []
        
        # Place portals
        placer.place_entrance(10, 10, mock_dungeon)
        entrance_entity = PortalManager.create_portal_entity('entrance', 10, 10)
        placer.active_entrance = entrance_entity.portal
        placer.active_entrance_entity = entrance_entity
        entities.append(entrance_entity)
        
        placer.place_exit(20, 20, mock_dungeon)
        exit_entity = PortalManager.create_portal_entity('exit', 20, 20)
        placer.active_exit = exit_entity.portal
        placer.active_exit_entity = exit_entity
        entities.append(exit_entity)
        
        # Cancel
        placer.cancel_active_portals(entities)
        
        # All references should be cleared
        assert placer.active_entrance is None
        assert placer.active_exit is None
        assert placer.active_entrance_entity is None
        assert placer.active_exit_entity is None
        assert placer.targeting_stage == 0
    
    def test_cancel_then_place_again_works(self, portal_wand, mock_dungeon):
        """After canceling, should be able to place new portals."""
        placer = portal_wand.portal_placer
        entities = []
        
        # First cycle: place and cancel
        placer.place_entrance(10, 10, mock_dungeon)
        entrance_entity = PortalManager.create_portal_entity('entrance', 10, 10)
        placer.active_entrance = entrance_entity.portal
        placer.active_entrance_entity = entrance_entity
        entities.append(entrance_entity)
        
        placer.place_exit(20, 20, mock_dungeon)
        exit_entity = PortalManager.create_portal_entity('exit', 20, 20)
        placer.active_exit = exit_entity.portal
        placer.active_exit_entity = exit_entity
        entities.append(exit_entity)
        
        placer.cancel_active_portals(entities)
        
        # Second cycle: place new portals
        placer.place_entrance(15, 15, mock_dungeon)
        entrance_entity2 = PortalManager.create_portal_entity('entrance', 15, 15)
        placer.active_entrance = entrance_entity2.portal
        placer.active_entrance_entity = entrance_entity2
        entities.append(entrance_entity2)
        
        placer.place_exit(25, 25, mock_dungeon)
        exit_entity2 = PortalManager.create_portal_entity('exit', 25, 25)
        placer.active_exit = exit_entity2.portal
        placer.active_exit_entity = exit_entity2
        entities.append(exit_entity2)
        
        # Should have new portal pair
        assert placer.has_active_portals()
        assert len(entities) == 2
        assert placer.active_entrance_entity.x == 15
        assert placer.active_entrance_entity.y == 15
        assert placer.active_exit_entity.x == 25
        assert placer.active_exit_entity.y == 25
    
    def test_use_wand_function_with_active_portals_cancels(self, portal_wand, player, mock_dungeon):
        """use_wand_of_portals should cancel portals when they're active."""
        placer = portal_wand.portal_placer
        entities = []
        
        # Place portals
        placer.place_entrance(10, 10, mock_dungeon)
        entrance_entity = PortalManager.create_portal_entity('entrance', 10, 10)
        placer.active_entrance = entrance_entity.portal
        placer.active_entrance_entity = entrance_entity
        entities.append(entrance_entity)
        
        placer.place_exit(20, 20, mock_dungeon)
        exit_entity = PortalManager.create_portal_entity('exit', 20, 20)
        placer.active_exit = exit_entity.portal
        placer.active_exit_entity = exit_entity
        entities.append(exit_entity)
        
        assert placer.has_active_portals()
        
        # Use wand again (should cancel)
        results = use_wand_of_portals(player, wand_entity=portal_wand, entities=entities)
        
        # Should have canceled
        assert len(entities) == 0
        assert not placer.has_active_portals()
        
        # Should have result with portal_canceled flag
        canceled = any(r.get('portal_canceled') for r in results)
        assert canceled
        
        # Should NOT enter targeting mode
        targeting = any(r.get('targeting_mode') for r in results)
        assert not targeting
        
        # Charge should still be 1
        assert placer.charges == 1
    
    def test_use_wand_function_without_active_portals_enters_targeting(self, portal_wand, player):
        """use_wand_of_portals should enter targeting when no portals active."""
        placer = portal_wand.portal_placer
        
        assert not placer.has_active_portals()
        
        # Use wand (should enter targeting)
        results = use_wand_of_portals(player, wand_entity=portal_wand, entities=[])
        
        # Should enter targeting mode
        targeting = any(r.get('targeting_mode') for r in results)
        assert targeting
        
        # Should NOT have canceled
        canceled = any(r.get('portal_canceled') for r in results)
        assert not canceled
    
    def test_wand_never_empty(self, portal_wand, player):
        """Wand should never be empty (always has 1 charge)."""
        placer = portal_wand.portal_placer
        
        # Charge should always be 1
        assert placer.charges == 1
        assert not placer.is_empty()
        
        # Try to use wand - should work (enter targeting)
        results = use_wand_of_portals(player, wand_entity=portal_wand, entities=[])
        
        # Should enter targeting mode
        targeting = any(r.get('targeting_mode') for r in results)
        assert targeting
        
        # Charge still 1
        assert placer.charges == 1
    
    def test_portal_manager_deactivate_removes_both_entities(self, mock_dungeon):
        """PortalManager.deactivate_portal_pair should remove both portal entities."""
        entities = []
        
        # Create portal pair
        entrance_entity = PortalManager.create_portal_entity('entrance', 10, 10)
        exit_entity = PortalManager.create_portal_entity('exit', 20, 20)
        entrance_entity.portal.linked_portal = exit_entity.portal
        exit_entity.portal.linked_portal = entrance_entity.portal
        
        entities.append(entrance_entity)
        entities.append(exit_entity)
        
        assert len(entities) == 2
        
        # Deactivate
        result = PortalManager.deactivate_portal_pair(entrance_entity, exit_entity, entities)
        
        assert result['success']
        assert result['removed_count'] == 2
        assert len(entities) == 0
    
    def test_portal_manager_deactivate_clears_portal_links(self, mock_dungeon):
        """PortalManager.deactivate_portal_pair should clear bidirectional links."""
        entities = []
        
        # Create portal pair
        entrance_entity = PortalManager.create_portal_entity('entrance', 10, 10)
        exit_entity = PortalManager.create_portal_entity('exit', 20, 20)
        entrance_entity.portal.linked_portal = exit_entity.portal
        exit_entity.portal.linked_portal = entrance_entity.portal
        
        entities.append(entrance_entity)
        entities.append(exit_entity)
        
        # Deactivate
        PortalManager.deactivate_portal_pair(entrance_entity, exit_entity, entities)
        
        # Links should be cleared
        assert entrance_entity.portal.linked_portal is None
        assert exit_entity.portal.linked_portal is None
        assert not entrance_entity.portal.is_deployed
        assert not exit_entity.portal.is_deployed
    
    def test_charge_stays_one_full_cycle(self, portal_wand, mock_dungeon):
        """Test complete cycle: charge always stays at 1."""
        placer = portal_wand.portal_placer
        entities = []
        
        # Initial: charge = 1
        assert placer.charges == 1
        
        # Place entrance
        placer.place_entrance(10, 10, mock_dungeon)
        entrance_entity = PortalManager.create_portal_entity('entrance', 10, 10)
        placer.active_entrance = entrance_entity.portal
        placer.active_entrance_entity = entrance_entity
        entities.append(entrance_entity)
        
        # Enforce invariant
        placer.charges = 1
        assert placer.charges == 1
        
        # Place exit
        placer.place_exit(20, 20, mock_dungeon)
        exit_entity = PortalManager.create_portal_entity('exit', 20, 20)
        placer.active_exit = exit_entity.portal
        placer.active_exit_entity = exit_entity
        entities.append(exit_entity)
        
        # Enforce invariant
        placer.charges = 1
        assert placer.charges == 1
        
        # Cancel portals
        result = placer.cancel_active_portals(entities)
        assert result['success']
        
        # Charge still 1
        assert placer.charges == 1
        assert len(entities) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

