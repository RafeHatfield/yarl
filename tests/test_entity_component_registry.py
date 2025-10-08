"""Integration tests for Entity with ComponentRegistry.

Tests cover:
- Entity creation with ComponentRegistry
- Backward compatibility with direct attribute access
- Component retrieval through both old and new APIs
- Special case handling (equippable auto-item)
"""

import pytest
from unittest.mock import Mock

from entity import Entity
from components.fighter import Fighter
from components.ai import BasicMonster
from components.inventory import Inventory
from components.equipment import Equipment
from components.equippable import Equippable
from components.component_registry import ComponentType
from render_functions import RenderOrder


class TestEntityComponentRegistryIntegration:
    """Tests for ComponentRegistry integration with Entity."""
    
    def test_entity_has_component_registry(self):
        """Test that entities have a ComponentRegistry instance."""
        entity = Entity(5, 5, 'o', (255, 0, 0), "Orc")
        
        assert hasattr(entity, 'components')
        assert entity.components is not None
        assert len(entity.components) == 0
    
    def test_entity_with_fighter_registered(self):
        """Test that Fighter component is registered in ComponentRegistry."""
        fighter = Fighter(hp=10, defense=5, power=3)
        entity = Entity(5, 5, 'o', (255, 0, 0), "Orc", fighter=fighter)
        
        # NEW API: Registry access
        assert entity.components.has(ComponentType.FIGHTER)
        assert entity.components.get(ComponentType.FIGHTER) is fighter
        
        # OLD API: Direct attribute access (backward compatibility)
        assert entity.fighter is fighter
    
    def test_entity_with_multiple_components_registered(self):
        """Test that multiple components are all registered."""
        fighter = Fighter(hp=10, defense=5, power=3)
        ai = BasicMonster()
        
        entity = Entity(5, 5, 'o', (255, 0, 0), "Orc",
                       fighter=fighter, ai=ai)
        
        # Both components should be in registry
        assert len(entity.components) == 2
        assert entity.components.has(ComponentType.FIGHTER)
        assert entity.components.has(ComponentType.AI)
        
        # Both APIs work
        assert entity.fighter is fighter
        assert entity.ai is ai
        assert entity.components.get(ComponentType.FIGHTER) is fighter
        assert entity.components.get(ComponentType.AI) is ai
    
    def test_entity_without_component_not_in_registry(self):
        """Test that components not provided are not in registry."""
        entity = Entity(5, 5, 'o', (255, 0, 0), "Orc")
        
        # Should not have fighter in registry
        assert not entity.components.has(ComponentType.FIGHTER)
        assert entity.components.get(ComponentType.FIGHTER) is None
        
        # Old API also returns None
        assert entity.fighter is None
    
    def test_player_creation_with_registry(self):
        """Test player creation properly registers all components."""
        fighter = Fighter(hp=30, defense=2, power=5)
        inventory = Inventory(capacity=26)
        level = Mock()
        equipment = Equipment()
        
        player = Entity.create_player(10, 10, fighter, inventory, level, equipment)
        
        # All components should be registered
        assert player.components.has(ComponentType.FIGHTER)
        assert player.components.has(ComponentType.INVENTORY)
        assert player.components.has(ComponentType.LEVEL)
        assert player.components.has(ComponentType.EQUIPMENT)
        
        # Count should be 4
        assert len(player.components) == 4
    
    def test_component_registry_iteration(self):
        """Test iterating over entity components."""
        fighter = Fighter(hp=10, defense=5, power=3)
        ai = BasicMonster()
        entity = Entity(5, 5, 'o', (255, 0, 0), "Orc",
                       fighter=fighter, ai=ai)
        
        components_list = list(entity.components)
        
        assert len(components_list) == 2
        assert fighter in components_list
        assert ai in components_list
    
    def test_component_ownership_still_works(self):
        """Test that component ownership is still established."""
        fighter = Fighter(hp=10, defense=5, power=3)
        ai = BasicMonster()
        entity = Entity(5, 5, 'o', (255, 0, 0), "Orc",
                       fighter=fighter, ai=ai)
        
        # Ownership should be established
        assert fighter.owner is entity
        assert ai.owner is entity


class TestEntityEquippableAutoItem:
    """Tests for auto-Item component with equippable items."""
    
    def test_equippable_auto_creates_item_component(self):
        """Test that equippable items auto-create Item component."""
        equippable = Equippable(slot='main_hand', power_bonus=2)
        entity = Entity(5, 5, '/', (255, 255, 255), "Sword", equippable=equippable)
        
        # Item should be auto-created
        assert entity.item is not None
        
        # Item should be in registry
        assert entity.components.has(ComponentType.ITEM)
        assert entity.components.get(ComponentType.ITEM) is entity.item
    
    def test_equippable_with_explicit_item_doesnt_duplicate(self):
        """Test that providing Item explicitly doesn't create duplicate."""
        from components.item import Item
        
        item = Item(use_function=Mock())
        equippable = Equippable(slot='main_hand', power_bonus=2)
        entity = Entity(5, 5, '/', (255, 255, 255), "Sword",
                       item=item, equippable=equippable)
        
        # Should use the provided item, not create new one
        assert entity.item is item
        assert entity.components.get(ComponentType.ITEM) is item
        
        # Should only have 2 components (item + equippable)
        assert len(entity.components) == 2


class TestEntityComponentRegistryBackwardCompatibility:
    """Tests to ensure complete backward compatibility."""
    
    def test_old_hasattr_pattern_still_works(self):
        """Test that old hasattr() checks still work."""
        fighter = Fighter(hp=10, defense=5, power=3)
        entity1 = Entity(5, 5, 'o', (255, 0, 0), "Orc", fighter=fighter)
        entity2 = Entity(5, 5, 'i', (255, 255, 0), "Item")
        
        # Old pattern should work
        if hasattr(entity1, 'fighter') and entity1.fighter:
            assert entity1.fighter.hp == 10
        
        if hasattr(entity2, 'fighter') and entity2.fighter:
            pytest.fail("entity2 should not have fighter")
    
    def test_direct_component_attribute_modification_works(self):
        """Test that modifying component through old API works."""
        fighter = Fighter(hp=10, defense=5, power=3)
        entity = Entity(5, 5, 'o', (255, 0, 0), "Orc", fighter=fighter)
        
        # Modify through old API
        entity.fighter.hp = 5
        
        # Should be reflected in both APIs
        assert entity.fighter.hp == 5
        assert entity.components.get(ComponentType.FIGHTER).hp == 5
    
    def test_all_component_types_supported(self):
        """Test that all valid component types can be registered."""
        from components.item import Item
        from components.level import Level
        from components.player_pathfinding import PlayerPathfinding
        
        # Create entity with many components
        fighter = Fighter(hp=10, defense=5, power=3)
        ai = BasicMonster()
        item = Item()
        inventory = Inventory(capacity=10)
        equipment = Equipment()
        equippable = Equippable(slot='main_hand')
        level = Level()
        pathfinding = PlayerPathfinding()
        
        entity = Entity(5, 5, 'o', (255, 0, 0), "Complex Entity",
                       fighter=fighter, ai=ai, item=item,
                       inventory=inventory, equipment=equipment,
                       equippable=equippable, level=level,
                       pathfinding=pathfinding)
        
        # All should be registered
        assert len(entity.components) == 8
        assert entity.components.has(ComponentType.FIGHTER)
        assert entity.components.has(ComponentType.AI)
        assert entity.components.has(ComponentType.ITEM)
        assert entity.components.has(ComponentType.INVENTORY)
        assert entity.components.has(ComponentType.EQUIPMENT)
        assert entity.components.has(ComponentType.EQUIPPABLE)
        assert entity.components.has(ComponentType.LEVEL)
        assert entity.components.has(ComponentType.PATHFINDING)


class TestEntityComponentRegistryEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_unknown_component_raises_error(self):
        """Test that providing unknown component raises ValueError."""
        with pytest.raises(ValueError, match="Unknown component"):
            Entity(5, 5, 'o', (255, 0, 0), "Orc", fake_component=Mock())
    
    def test_none_component_registered_correctly(self):
        """Test that None components are handled gracefully."""
        # This shouldn't happen in practice, but ensure it doesn't crash
        entity = Entity(5, 5, 'o', (255, 0, 0), "Orc", fighter=None)
        
        # None should be registered
        assert entity.components.has(ComponentType.FIGHTER)
        assert entity.components.get(ComponentType.FIGHTER) is None
        assert entity.fighter is None
    
    def test_component_type_enum_contains_operator(self):
        """Test using 'in' operator with ComponentType."""
        fighter = Fighter(hp=10, defense=5, power=3)
        entity = Entity(5, 5, 'o', (255, 0, 0), "Orc", fighter=fighter)
        
        # Should work with 'in' operator
        assert ComponentType.FIGHTER in entity.components
        assert ComponentType.AI not in entity.components
