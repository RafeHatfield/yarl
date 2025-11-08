"""Portal System - Extended Phase A Integration Tests

Tests for:
- Portal pickup from inventory
- Portal deployment from inventory
- Portal collision detection
- Wand discovery and activation
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from components.portal import Portal
from components.portal_placer import PortalPlacer
from components.inventory import Inventory
from config.entity_factory import get_entity_factory
from engine.portal_system import get_portal_system
from entity import Entity


class TestPortalPickupAndDeploy:
    """Test picking up and deploying portals from inventory."""
    
    @staticmethod
    def create_mock_dungeon():
        """Create a mock dungeon for testing."""
        class MockDungeon:
            def __init__(self):
                self.width = 80
                self.height = 45
                self.tiles = [[MockTile() for _ in range(45)] for _ in range(80)]
                self.entities = []
        
        class MockTile:
            def __init__(self):
                self.block_movement = False
                self.tile_type = 'floor'
        
        return MockDungeon()
    
    def test_portal_can_be_picked_up_from_dungeon(self):
        """Portal deployed on dungeon can be picked up."""
        factory = get_entity_factory()
        dungeon = self.create_mock_dungeon()
        
        # Create a deployed portal
        entrance_entity = factory.create_portal(10, 10, 'entrance')
        dungeon.entities.append(entrance_entity)
        
        # Pick it up
        portal_system = get_portal_system()
        result = portal_system.pick_up_portal(entrance_entity, dungeon)
        
        assert result['success']
        assert not entrance_entity.portal.is_deployed
        assert entrance_entity not in dungeon.entities
    
    def test_portal_can_be_deployed_from_inventory(self):
        """Portal in inventory can be deployed on dungeon."""
        factory = get_entity_factory()
        dungeon = self.create_mock_dungeon()
        player = Entity(10, 10, '@', (255, 255, 255), 'Player')
        player.inventory = Inventory(26)
        
        # Create wand
        wand = factory.create_wand_of_portals(10, 10)
        player.inventory.add_item(wand)
        
        # Create portal in inventory (not deployed)
        portal_entity = factory.create_portal(0, 0, 'entrance')
        portal_entity.portal.is_deployed = False
        player.inventory.add_item(portal_entity)
        
        # Deploy it
        portal_system = get_portal_system()
        result = portal_system.deploy_portal(player, portal_entity, 15, 15, dungeon)
        
        assert result['success']
        assert portal_entity.portal.is_deployed
        assert portal_entity.x == 15
        assert portal_entity.y == 15
        assert portal_entity in dungeon.entities
    
    def test_invalid_deployment_location_rejected(self):
        """Cannot deploy portal to invalid location."""
        factory = get_entity_factory()
        dungeon = self.create_mock_dungeon()
        player = Entity(10, 10, '@', (255, 255, 255), 'Player')
        player.inventory = Inventory(26)
        
        # Create wand
        wand = factory.create_wand_of_portals(10, 10)
        player.inventory.add_item(wand)
        
        # Create portal
        portal_entity = factory.create_portal(0, 0, 'entrance')
        
        # Create wall at target location
        dungeon.tiles[15][15].block_movement = True
        
        # Try to deploy to wall
        portal_system = get_portal_system()
        result = portal_system.deploy_portal(player, portal_entity, 15, 15, dungeon)
        
        assert not result['success']


class TestPortalCollisionDetection:
    """Test portal collision detection when entities move."""
    
    @staticmethod
    def create_mock_dungeon():
        """Create a mock dungeon for testing."""
        class MockDungeon:
            def __init__(self):
                self.width = 80
                self.height = 45
                self.tiles = [[MockTile() for _ in range(45)] for _ in range(80)]
                self.entities = []
        
        class MockTile:
            def __init__(self):
                self.block_movement = False
                self.tile_type = 'floor'
        
        return MockDungeon()
    
    def test_portal_collision_detects_stepping_on_portal(self):
        """Stepping on portal triggers teleportation."""
        factory = get_entity_factory()
        dungeon = self.create_mock_dungeon()
        
        # Create portal pair
        entrance_entity = factory.create_portal(10, 10, 'entrance')
        exit_entity = factory.create_portal(20, 20, 'exit')
        
        entrance_entity.portal.linked_portal = exit_entity.portal
        exit_entity.portal.linked_portal = entrance_entity.portal
        
        dungeon.entities.extend([entrance_entity, exit_entity])
        
        # Create player on portal
        player = Entity(10, 10, '@', (255, 255, 255), 'Player')
        
        # Check collision
        portal_system = get_portal_system()
        result = portal_system.check_portal_collision(player, dungeon)
        
        assert result is not None
        assert result.get('teleported')
        assert player.x == 20
        assert player.y == 20
    
    def test_no_collision_when_not_on_portal(self):
        """No teleportation when not on portal."""
        factory = get_entity_factory()
        dungeon = self.create_mock_dungeon()
        
        # Create portal pair
        entrance_entity = factory.create_portal(10, 10, 'entrance')
        exit_entity = factory.create_portal(20, 20, 'exit')
        
        entrance_entity.portal.linked_portal = exit_entity.portal
        exit_entity.portal.linked_portal = entrance_entity.portal
        
        dungeon.entities.extend([entrance_entity, exit_entity])
        
        # Create player NOT on portal
        player = Entity(15, 15, '@', (255, 255, 255), 'Player')
        
        # Check collision
        portal_system = get_portal_system()
        result = portal_system.check_portal_collision(player, dungeon)
        
        assert result is None


class TestWandDiscovery:
    """Test finding wand in inventory."""
    
    def test_wand_discovered_in_inventory(self):
        """Wand can be found in player inventory."""
        factory = get_entity_factory()
        player = Entity(10, 10, '@', (255, 255, 255), 'Player')
        player.inventory = Inventory(26)
        
        # Create and add wand
        wand = factory.create_wand_of_portals(10, 10)
        player.inventory.add_item(wand)
        
        # Discover wand
        portal_system = get_portal_system()
        discovered_wand = portal_system.get_wand(player.inventory)
        
        assert discovered_wand is not None
        assert discovered_wand == wand
    
    def test_wand_not_found_if_missing(self):
        """Returns None if no wand in inventory."""
        player = Entity(10, 10, '@', (255, 255, 255), 'Player')
        player.inventory = Inventory(26)
        
        # Don't add wand
        portal_system = get_portal_system()
        discovered_wand = portal_system.get_wand(player.inventory)
        
        assert discovered_wand is None


class TestPortalSystemIntegration:
    """Integration tests for full portal system."""
    
    @staticmethod
    def create_mock_dungeon():
        """Create a mock dungeon for testing."""
        class MockDungeon:
            def __init__(self):
                self.width = 80
                self.height = 45
                self.tiles = [[MockTile() for _ in range(45)] for _ in range(80)]
                self.entities = []
        
        class MockTile:
            def __init__(self):
                self.block_movement = False
                self.tile_type = 'floor'
        
        return MockDungeon()
    
    def test_full_portal_cycle_with_inventory(self):
        """Full cycle: create, deploy, pickup, redeploy, teleport."""
        factory = get_entity_factory()
        dungeon = self.create_mock_dungeon()
        player = Entity(10, 10, '@', (255, 255, 255), 'Player')
        player.inventory = Inventory(26)
        portal_system = get_portal_system()
        
        # Step 1: Create wand
        wand = factory.create_wand_of_portals(10, 10)
        player.inventory.add_item(wand)
        
        # Step 2: Create portal pair
        wand.portal_placer.start_targeting()
        entrance_result = wand.portal_placer.place_entrance(15, 15, dungeon)
        exit_result = wand.portal_placer.place_exit(25, 25, dungeon)
        
        assert entrance_result['success']
        assert exit_result['success']
        
        # Get portal components and create entity wrappers
        entrance_portal = exit_result['entrance']
        exit_portal = exit_result['exit']
        
        # Create entity wrappers for portals
        entrance_entity = Entity(15, 15, 'Θ', (100, 200, 255), 'Entrance Portal')
        entrance_entity.portal = entrance_portal
        entrance_portal.owner = entrance_entity
        
        exit_entity = Entity(25, 25, 'Θ', (255, 180, 80), 'Exit Portal')
        exit_entity.portal = exit_portal
        exit_portal.owner = exit_entity
        
        dungeon.entities.extend([entrance_entity, exit_entity])
        
        # Step 3: Teleport through portal
        player.x, player.y = 15, 15
        result = portal_system.check_portal_collision(player, dungeon)
        assert result and result.get('teleported')
        assert player.x == 25 and player.y == 25
        
        # Step 4: Pick up entrance portal
        player.x, player.y = 15, 15  # Move back
        pickup_result = portal_system.pick_up_portal(entrance_entity, dungeon)
        assert pickup_result['success']
        player.inventory.add_item(entrance_entity)
        
        # Step 5: Redeploy at different location
        deploy_result = portal_system.deploy_portal(player, entrance_entity, 30, 30, dungeon)
        assert deploy_result['success']
        
        # Update the link (in real game, this would be handled by portal system)
        entrance_entity.portal.x = 30
        entrance_entity.portal.y = 30
        
        # Verify new location
        assert entrance_entity.x == 30
        assert entrance_entity.y == 30
    
    def test_get_all_portals(self):
        """Can retrieve all active portals in dungeon."""
        factory = get_entity_factory()
        dungeon = self.create_mock_dungeon()
        
        # Create 2 portal pairs
        for i in range(2):
            entrance = factory.create_portal(10 + i * 10, 10, 'entrance')
            exit_p = factory.create_portal(20 + i * 10, 20, 'exit')
            entrance.portal.linked_portal = exit_p.portal
            exit_p.portal.linked_portal = entrance.portal
            dungeon.entities.extend([entrance, exit_p])
        
        # Get all portals
        portal_system = get_portal_system()
        all_portals = portal_system.get_all_portals(dungeon)
        
        assert len(all_portals) == 4
    
    def test_get_portal_at_location(self):
        """Can find portal at specific coordinates."""
        factory = get_entity_factory()
        dungeon = self.create_mock_dungeon()
        
        # Create portal at (10, 10)
        portal_entity = factory.create_portal(10, 10, 'entrance')
        dungeon.entities.append(portal_entity)
        
        # Find it
        portal_system = get_portal_system()
        found = portal_system.get_portal_at(10, 10, dungeon)
        
        assert found is not None
        assert found == portal_entity
        
        # Not found at wrong location
        not_found = portal_system.get_portal_at(20, 20, dungeon)
        assert not_found is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

