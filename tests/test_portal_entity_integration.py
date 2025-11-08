"""Portal System - Entity Integration Tests

Tests the full workflow of portal creation, entity wrapping, and rendering.
These are end-to-end integration tests that verify portals work with the
rendering system, inventory system, and collision detection.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from components.portal import Portal
from components.portal_placer import PortalPlacer
from components.inventory import Inventory
from config.entity_factory import EntityFactory
from entity import Entity, RenderOrder
from render_functions import RenderOrder as RenderOrderEnum


class TestPortalEntityIntegration:
    """Test full integration of portals with entity system."""
    
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
                self.blocked = False
                self.tile_type = 'floor'
        
        return MockDungeon()
    
    def test_portal_entity_has_render_order(self):
        """Created portal entity must have render_order attribute."""
        factory = EntityFactory()
        portal_entity = factory.create_portal(10, 10, 'entrance')
        
        assert portal_entity is not None
        assert hasattr(portal_entity, 'render_order')
        assert portal_entity.render_order == RenderOrderEnum.ITEM
    
    def test_portal_entity_can_be_sorted(self):
        """Portal entities can be sorted by render_order for rendering."""
        factory = EntityFactory()
        dungeon = self.create_mock_dungeon()
        entities = []
        
        # Create multiple portals
        entrance = factory.create_portal(10, 10, 'entrance')
        exit_portal = factory.create_portal(20, 20, 'exit')
        
        entities.append(entrance)
        entities.append(exit_portal)
        
        # Should be able to sort without error
        sorted_entities = sorted(entities, key=lambda x: x.render_order.value)
        assert len(sorted_entities) == 2
    
    def test_portal_pair_link_entities(self):
        """Portal pair should have linked components and proper entities."""
        factory = EntityFactory()
        dungeon = self.create_mock_dungeon()
        
        # Create entrance
        entrance_entity = factory.create_portal(10, 10, 'entrance')
        assert entrance_entity is not None
        assert hasattr(entrance_entity, 'portal')
        
        # Create exit
        exit_entity = factory.create_portal(20, 20, 'exit')
        assert exit_entity is not None
        
        # Manually link them (as game_actions.py does)
        entrance_entity.portal.linked_portal = exit_entity.portal
        exit_entity.portal.linked_portal = entrance_entity.portal
        
        # Verify bidirectional linking
        assert entrance_entity.portal.linked_portal == exit_entity.portal
        assert exit_entity.portal.linked_portal == entrance_entity.portal
    
    def test_portal_placer_integration_entrance(self):
        """PortalPlacer.place_entrance returns portal component that can be wrapped in entity."""
        dungeon = self.create_mock_dungeon()
        placer = PortalPlacer()
        
        # Start targeting
        placer.start_targeting()
        
        # Place entrance
        result = placer.place_entrance(10, 10, dungeon)
        assert result['success']
        
        portal_component = result.get('portal')
        assert portal_component is not None
        assert isinstance(portal_component, Portal)
        
        # Now wrap it in an entity (as game_actions.py does)
        factory = EntityFactory()
        entity = factory.create_portal(10, 10, 'entrance')
        entity.portal = portal_component
        portal_component.owner = entity
        
        # Verify entity is valid
        assert entity.x == 10
        assert entity.y == 10
        assert entity.render_order == RenderOrderEnum.ITEM
        assert portal_component.owner == entity
    
    def test_portal_placer_integration_exit(self):
        """PortalPlacer creates linked portal pair."""
        dungeon = self.create_mock_dungeon()
        placer = PortalPlacer()
        
        # Start targeting and place entrance
        placer.start_targeting()
        result1 = placer.place_entrance(10, 10, dungeon)
        assert result1['success']
        
        # Place exit
        result2 = placer.place_exit(20, 20, dungeon)
        assert result2['success']
        
        entrance_component = result2.get('entrance')
        exit_component = result2.get('exit')
        
        # Create entity wrappers
        factory = EntityFactory()
        entrance_entity = factory.create_portal(10, 10, 'entrance')
        exit_entity = factory.create_portal(20, 20, 'exit')
        
        entrance_entity.portal = entrance_component
        exit_entity.portal = exit_component
        entrance_component.owner = entrance_entity
        exit_component.owner = exit_entity
        
        # Verify linking
        assert entrance_component.linked_portal == exit_component
        assert exit_component.linked_portal == entrance_component
        assert entrance_entity.portal.owner == entrance_entity
        assert exit_entity.portal.owner == exit_entity
    
    def test_portal_entities_in_entities_list_render(self):
        """Portal entities added to entities list can be rendered."""
        factory = EntityFactory()
        entities = []
        
        # Create portals
        entrance = factory.create_portal(5, 5, 'entrance')
        exit_portal = factory.create_portal(15, 15, 'exit')
        
        entities.append(entrance)
        entities.append(exit_portal)
        
        # Simulate rendering system (sorting by render_order)
        sorted_entities = sorted(entities, key=lambda x: x.render_order.value)
        
        # All entities should be sortable
        assert len(sorted_entities) == 2
        
        # All entities should have render_order
        for entity in sorted_entities:
            assert hasattr(entity, 'render_order')
            assert entity.render_order is not None
    
    def test_portal_wand_creates_entities_not_components(self):
        """When wand places portals, they must be wrapped in entities."""
        dungeon = self.create_mock_dungeon()
        placer = PortalPlacer()
        factory = EntityFactory()
        entities = []
        
        # Simulate wand placement
        placer.start_targeting()
        
        # Place entrance
        result = placer.place_entrance(10, 10, dungeon)
        if result['success']:
            portal_component = result.get('portal')
            # Must wrap in entity before adding to entities list
            entrance_entity = factory.create_portal(10, 10, 'entrance')
            entrance_entity.portal = portal_component
            portal_component.owner = entrance_entity
            entities.append(entrance_entity)
        
        # Place exit
        result = placer.place_exit(20, 20, dungeon)
        if result['success']:
            exit_portal_component = result.get('exit')
            # Must wrap in entity
            exit_entity = factory.create_portal(20, 20, 'exit')
            exit_entity.portal = exit_portal_component
            exit_portal_component.owner = exit_entity
            entities.append(exit_entity)
        
        # Verify entities list has Entity objects with render_order
        assert len(entities) == 2
        for entity in entities:
            assert isinstance(entity, Entity)
            assert hasattr(entity, 'render_order')
            assert hasattr(entity, 'portal')
    
    def test_portal_teleportation_with_entity_owners(self):
        """Portals can teleport when both have entity owners."""
        dungeon = self.create_mock_dungeon()
        factory = EntityFactory()
        
        # Create player
        player = Entity(x=10, y=10, char='@', color=(255, 255, 255), name='Player', blocks=True)
        player.inventory = Inventory(26)
        
        # Create entrance and exit portal entities
        entrance_entity = factory.create_portal(15, 15, 'entrance')
        exit_entity = factory.create_portal(40, 40, 'exit')
        
        # Link portals
        entrance_entity.portal.linked_portal = exit_entity.portal
        exit_entity.portal.linked_portal = entrance_entity.portal
        
        # Both portals must have entity owners
        entrance_entity.portal.owner = entrance_entity
        exit_entity.portal.owner = exit_entity
        
        # Teleport through entrance
        results = entrance_entity.portal.teleport_through(player, dungeon)
        
        # Should succeed
        assert len(results) > 0
        assert results[0].get('teleported', False)
        
        # Player should be at exit location
        assert player.x == exit_entity.x
        assert player.y == exit_entity.y


class TestPortalRenderingSystem:
    """Test portals with rendering system."""
    
    def test_multiple_portals_render_order(self):
        """Multiple portal entities maintain proper render order."""
        factory = EntityFactory()
        entities = []
        
        # Create many portals to ensure render order consistency
        for i in range(5):
            entrance = factory.create_portal(10 + i, 10 + i, 'entrance')
            exit_portal = factory.create_portal(20 + i, 20 + i, 'exit')
            entities.append(entrance)
            entities.append(exit_portal)
        
        # Should all be sortable
        sorted_entities = sorted(entities, key=lambda x: x.render_order.value)
        assert len(sorted_entities) == 10
        
        # All should have same render order (ITEM)
        for entity in sorted_entities:
            assert entity.render_order == RenderOrderEnum.ITEM
    
    def test_portal_position_updates(self):
        """Portal entities maintain correct position."""
        factory = EntityFactory()
        
        # Create portal at specific location
        entrance = factory.create_portal(25, 30, 'entrance')
        assert entrance.x == 25
        assert entrance.y == 30
        
        # Portal components should track position via owner
        assert entrance.portal.owner == entrance


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

