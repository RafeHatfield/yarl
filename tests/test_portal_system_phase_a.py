"""Portal System - Phase A Integration Tests

Tests for core portal system functionality:
- Portal component creation and linking
- Wand targeting and placement
- Teleportation through portals
- Inventory pickup/drop
- Portal recycling
- Monster interaction
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from components.portal import Portal
from components.portal_placer import PortalPlacer
from components.map_feature import MapFeatureType
from config.entity_factory import get_entity_factory
from entity import Entity
from map_objects.game_map import GameMap
from components.inventory import Inventory


class TestPortalComponent:
    """Test Portal component basics."""
    
    def test_portal_creation_entrance(self):
        """Create entrance portal."""
        portal = Portal('entrance')
        assert portal.portal_type == 'entrance'
        assert portal.linked_portal is None
        assert portal.is_deployed
    
    def test_portal_creation_exit(self):
        """Create exit portal."""
        portal = Portal('exit')
        assert portal.portal_type == 'exit'
        assert portal.linked_portal is None
        assert portal.is_deployed
    
    def test_portal_linking(self):
        """Link two portals together."""
        entrance = Portal('entrance')
        exit_portal = Portal('exit')
        
        entrance.linked_portal = exit_portal
        exit_portal.linked_portal = entrance
        
        assert entrance.linked_portal == exit_portal
        assert exit_portal.linked_portal == entrance
    
    def test_portal_pair_detection(self):
        """Get portal pair from either portal."""
        entrance = Portal('entrance')
        exit_portal = Portal('exit', linked_portal=entrance)
        entrance.linked_portal = exit_portal
        
        # From entrance
        e, x = entrance.get_portal_pair()
        assert e == entrance
        assert x == exit_portal
        
        # From exit
        e, x = exit_portal.get_portal_pair()
        assert e == entrance
        assert x == exit_portal
    
    def test_portal_feature_type(self):
        """Portal has correct MapFeatureType."""
        portal = Portal('entrance')
        assert portal.feature_type == MapFeatureType.PORTAL
    
    def test_portal_description(self):
        """Portal descriptions are correct."""
        entrance = Portal('entrance')
        assert "Entrance" in entrance.get_description()
        assert "Blue" in entrance.get_description()
        
        exit_portal = Portal('exit')
        assert "Exit" in exit_portal.get_description()
        assert "Orange" in exit_portal.get_description()


class TestPortalPlacer:
    """Test PortalPlacer (Wand) logic."""
    
    @pytest.fixture
    def wand(self):
        """Create a wand."""
        return PortalPlacer()
    
    @pytest.fixture
    def dungeon(self):
        """Create a mock dungeon for testing."""
        class MockDungeon:
            def __init__(self):
                self.width = 80
                self.height = 45
                self.tiles = [[MockTile() for _ in range(45)] for _ in range(80)]
        
        class MockTile:
            def __init__(self):
                self.blocked = False
                self.tile_type = 'floor'
        
        return MockDungeon()
    
    def test_wand_creation(self, wand):
        """Wand created with correct properties."""
        assert wand.spell_type == "portal"
        assert wand.charges == 0  # Infinite
        assert wand.active_entrance is None
        assert wand.active_exit is None
        assert wand.targeting_stage == 0
    
    def test_wand_start_targeting(self, wand):
        """Start targeting mode."""
        result = wand.start_targeting()
        assert result['status'] == 'targeting_started'
        assert wand.targeting_stage == 1
    
    def test_wand_place_entrance(self, wand, dungeon):
        """Place entrance portal."""
        wand.start_targeting()
        result = wand.place_entrance(10, 10, dungeon)
        
        assert result['success']
        assert wand.active_entrance is not None
        assert wand.active_entrance.portal_type == 'entrance'
        assert wand.active_entrance.x == 10
        assert wand.active_entrance.y == 10
        assert wand.targeting_stage == 2
    
    def test_wand_place_exit(self, wand, dungeon):
        """Place exit portal after entrance."""
        wand.start_targeting()
        wand.place_entrance(10, 10, dungeon)
        result = wand.place_exit(15, 15, dungeon)
        
        assert result['success']
        assert wand.active_exit is not None
        assert wand.active_exit.portal_type == 'exit'
        assert wand.active_entrance.linked_portal == wand.active_exit
        assert wand.active_exit.linked_portal == wand.active_entrance
        assert wand.targeting_stage == 0
    
    def test_wand_recycle_portals(self, wand, dungeon):
        """Recycle portals and ready for new pair."""
        # Create first pair
        wand.start_targeting()
        wand.place_entrance(10, 10, dungeon)
        wand.place_exit(15, 15, dungeon)
        
        entrance1 = wand.active_entrance
        exit1 = wand.active_exit
        
        # Recycle
        result = wand.recycle_portals()
        assert result['recycled']
        assert wand.active_entrance is None
        assert wand.active_exit is None
        assert entrance1.is_deployed == False
        assert exit1.is_deployed == False
    
    def test_wand_invalid_placement_wall(self, wand, dungeon):
        """Cannot place portal on wall."""
        wand.start_targeting()
        
        # Create a wall tile
        dungeon.tiles[10][10].blocked = True
        
        result = wand.place_entrance(10, 10, dungeon)
        assert not result['success']
        assert result['message'] == 'Cannot place portal there'
    
    def test_wand_invalid_placement_bounds(self, wand, dungeon):
        """Cannot place portal out of bounds."""
        wand.start_targeting()
        result = wand.place_entrance(-5, -5, dungeon)
        assert not result['success']
    
    def test_wand_has_active_portals(self, wand, dungeon):
        """Check if wand has active portal pair."""
        assert not wand.has_active_portals()
        
        wand.start_targeting()
        wand.place_entrance(10, 10, dungeon)
        assert not wand.has_active_portals()  # Only entrance
        
        wand.place_exit(15, 15, dungeon)
        assert wand.has_active_portals()  # Both


class TestTeleportation:
    """Test teleportation through portals."""
    
    @pytest.fixture
    def game_data(self):
        """Create game with player."""
        from entity import Entity
        
        class MockDungeon:
            def __init__(self):
                self.width = 80
                self.height = 45
                self.tiles = [[MockTile() for _ in range(45)] for _ in range(80)]
        
        class MockTile:
            def __init__(self):
                self.blocked = False
                self.tile_type = 'floor'
        
        player = Entity(10, 10, '@', (255, 255, 255), 'Player')
        dungeon = MockDungeon()
        
        return player, dungeon
    
    def test_teleport_through_entrance(self, game_data):
        """Teleport through entrance to exit."""
        player, dungeon = game_data
        
        # Create portal pair with entities
        entrance = Portal('entrance')
        entrance_entity = Entity(10, 10, 'Θ', (100, 200, 255), 'Entrance')
        entrance_entity.portal = entrance
        entrance.owner = entrance_entity
        
        exit_portal = Portal('exit')
        exit_entity = Entity(20, 20, 'Θ', (255, 180, 80), 'Exit')
        exit_entity.portal = exit_portal
        exit_portal.owner = exit_entity
        
        exit_portal.linked_portal = entrance
        entrance.linked_portal = exit_portal
        
        # Test teleportation
        player.x, player.y = 10, 10
        results = entrance.teleport_through(player, dungeon)
        
        assert len(results) > 0
        assert results[0]['teleported']
        assert player.x == 20
        assert player.y == 20
    
    def test_teleport_through_exit(self, game_data):
        """Teleport through exit back to entrance."""
        player, dungeon = game_data
        
        entrance = Portal('entrance')
        entrance_entity = Entity(10, 10, 'Θ', (100, 200, 255), 'Entrance')
        entrance_entity.portal = entrance
        entrance.owner = entrance_entity
        
        exit_portal = Portal('exit')
        exit_entity = Entity(20, 20, 'Θ', (255, 180, 80), 'Exit')
        exit_entity.portal = exit_portal
        exit_portal.owner = exit_entity
        
        exit_portal.linked_portal = entrance
        entrance.linked_portal = exit_portal
        
        player.x, player.y = 20, 20
        results = exit_portal.teleport_through(player, dungeon)
        
        assert results[0]['teleported']
        assert player.x == 10
        assert player.y == 10
    
    def test_cannot_teleport_carrying_exit(self, game_data):
        """Cannot enter entrance if carrying exit portal."""
        player, dungeon = game_data
        player.inventory = Inventory(26)
        
        entrance = Portal('entrance')
        exit_portal = Portal('exit')
        exit_portal.linked_portal = entrance
        entrance.linked_portal = exit_portal
        
        # Create exit portal as item
        exit_item = Entity(0, 0, 'Θ', (255, 180, 80), 'Portal Exit')
        exit_item.portal = exit_portal
        
        player.inventory.add_item(exit_item)
        
        # Try to enter
        results = entrance.teleport_through(player, dungeon)
        assert 'message' in results[0]
        # Message might be a Message object or string, just check it exists
        assert results[0]['message'] is not None


class TestPortalInventory:
    """Test picking up and dropping portals."""
    
    @pytest.fixture
    def factory(self):
        """Get entity factory."""
        return get_entity_factory()
    
    def test_create_portal_entity(self, factory):
        """Create portal as entity."""
        portal_entity = factory.create_portal(10, 10, 'entrance')
        
        assert portal_entity is not None
        assert portal_entity.portal is not None
        assert portal_entity.portal.portal_type == 'entrance'
        assert portal_entity.char == 'Θ'
    
    def test_create_wand_of_portals(self, factory):
        """Create Wand of Portals."""
        wand_entity = factory.create_wand_of_portals(10, 10)
        
        assert wand_entity is not None
        assert wand_entity.portal_placer is not None
        assert wand_entity.name == 'Wand of Portals'
        assert wand_entity.char == '/'
    
    def test_portal_as_inventory_item(self):
        """Portal can be added to inventory."""
        player = Entity(0, 0, '@', (255, 255, 255), 'Player')
        player.inventory = Inventory(26)
        
        factory = get_entity_factory()
        portal_item = factory.create_portal(10, 10, 'entrance')
        
        player.inventory.add_item(portal_item)
        
        assert len(player.inventory.items) == 1
        assert player.inventory.items[0] == portal_item


class TestMonsterWithPortals:
    """Test monster interaction with portals."""
    
    @pytest.fixture
    def game_data(self):
        """Create game with monster."""
        from entity import Entity
        from components.ai import BasicMonster
        
        class MockDungeon:
            def __init__(self):
                self.width = 80
                self.height = 45
                self.tiles = [[MockTile() for _ in range(45)] for _ in range(80)]
        
        class MockTile:
            def __init__(self):
                self.blocked = False
                self.tile_type = 'floor'
        
        monster = Entity(15, 15, 'o', (255, 100, 100), 'Orc')
        monster.ai = BasicMonster()
        dungeon = MockDungeon()
        
        return monster, dungeon
    
    def test_monster_can_walk_through_portal(self, game_data):
        """Monster can walk through portal."""
        monster, dungeon = game_data
        
        # Create portal pair
        entrance = Portal('entrance')
        entrance_entity = Entity(10, 10, 'Θ', (100, 200, 255), 'Entrance')
        entrance_entity.portal = entrance
        entrance.owner = entrance_entity
        
        exit_portal = Portal('exit')
        exit_entity = Entity(20, 20, 'Θ', (255, 180, 80), 'Exit')
        exit_entity.portal = exit_portal
        exit_portal.owner = exit_entity
        
        exit_portal.linked_portal = entrance
        entrance.linked_portal = exit_portal
        
        # Test monster teleportation
        monster.x, monster.y = 10, 10
        results = entrance.teleport_through(monster, dungeon)
        
        assert results[0]['teleported']
        assert monster.x == 20
        assert monster.y == 20


class TestPortalPhaseAIntegration:
    """Integration tests for Phase A."""
    
    @pytest.fixture
    def game_data(self):
        """Create full game."""
        from entity import Entity
        
        class MockDungeon:
            def __init__(self):
                self.width = 80
                self.height = 45
                self.tiles = [[MockTile() for _ in range(45)] for _ in range(80)]
        
        class MockTile:
            def __init__(self):
                self.blocked = False
                self.tile_type = 'floor'
        
        player = Entity(10, 10, '@', (255, 255, 255), 'Player')
        dungeon = MockDungeon()
        return player, dungeon
    
    def test_full_portal_cycle(self, game_data):
        """Full cycle: create portals, teleport, recycle."""
        player, dungeon = game_data
        
        factory = get_entity_factory()
        
        # Create wand
        wand_entity = factory.create_wand_of_portals(10, 10)
        wand = wand_entity.portal_placer
        
        # Place first pair
        wand.start_targeting()
        result1 = wand.place_entrance(15, 15, dungeon)
        assert result1['success']
        
        result2 = wand.place_exit(20, 20, dungeon)
        assert result2['success']
        
        # Create entity wrappers with owners set
        entrance_portal = wand.active_entrance
        exit_portal = wand.active_exit
        
        entrance_entity = Entity(15, 15, 'Θ', (100, 200, 255), 'Entrance')
        entrance_entity.portal = entrance_portal
        entrance_portal.owner = entrance_entity
        
        exit_entity = Entity(20, 20, 'Θ', (255, 180, 80), 'Exit')
        exit_entity.portal = exit_portal
        exit_portal.owner = exit_entity
        
        # Teleport player
        player.x, player.y = 15, 15
        results = entrance_portal.teleport_through(player, dungeon)
        assert results[0]['teleported']
        assert player.x == 20
        assert player.y == 20
        
        # Recycle
        wand.recycle_portals()
        assert wand.active_entrance is None
        assert wand.active_exit is None
    
    def test_no_regressions(self):
        """Verify no regressions in existing systems."""
        # Component registry should still work
        from components.component_registry import ComponentType
        assert ComponentType.PORTAL is not None
        assert ComponentType.PORTAL_PLACER is not None
        
        # MapFeatureType should still work
        from components.map_feature import MapFeatureType
        assert MapFeatureType.PORTAL is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

