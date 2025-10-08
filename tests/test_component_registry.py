"""Unit tests for ComponentRegistry system.

Tests cover:
- Component addition and retrieval
- Type safety and error handling
- Existence checking
- Component removal
- Collection operations (iteration, length, contains)
- Edge cases and error conditions
"""

import pytest
from unittest.mock import Mock

from components.component_registry import ComponentRegistry, ComponentType
from components.fighter import Fighter
from components.ai import BasicMonster
from components.inventory import Inventory
from components.item import Item


class TestComponentType:
    """Tests for ComponentType enum."""
    
    def test_all_component_types_defined(self):
        """Test that all expected component types are defined."""
        expected_types = [
            'FIGHTER', 'AI', 'ITEM', 'INVENTORY', 'EQUIPMENT', 
            'EQUIPPABLE', 'LEVEL', 'STAIRS', 'PATHFINDING',
            'STATUS_EFFECTS', 'WAND', 'GROUND_HAZARD', 
            'STATISTICS', 'FACTION'
        ]
        
        for type_name in expected_types:
            assert hasattr(ComponentType, type_name), \
                f"ComponentType.{type_name} should be defined"
    
    def test_component_types_are_unique(self):
        """Test that all component type values are unique."""
        values = [ct.value for ct in ComponentType]
        assert len(values) == len(set(values)), \
            "All ComponentType values should be unique"


class TestComponentRegistryBasics:
    """Tests for basic ComponentRegistry operations."""
    
    def setUp(self):
        """Set up test fixtures before each test."""
        self.registry = ComponentRegistry()
        self.fighter = Fighter(hp=10, defense=5, power=3)
        self.ai = BasicMonster()
    
    def test_new_registry_is_empty(self):
        """Test that a new registry has no components."""
        registry = ComponentRegistry()
        
        assert len(registry) == 0
        assert not registry.has(ComponentType.FIGHTER)
    
    def test_add_component(self):
        """Test adding a component to the registry."""
        registry = ComponentRegistry()
        fighter = Fighter(hp=10, defense=5, power=3)
        
        registry.add(ComponentType.FIGHTER, fighter)
        
        assert registry.has(ComponentType.FIGHTER)
        assert registry.get(ComponentType.FIGHTER) == fighter
        assert len(registry) == 1
    
    def test_add_multiple_components(self):
        """Test adding multiple components."""
        registry = ComponentRegistry()
        fighter = Fighter(hp=10, defense=5, power=3)
        ai = BasicMonster()
        
        registry.add(ComponentType.FIGHTER, fighter)
        registry.add(ComponentType.AI, ai)
        
        assert len(registry) == 2
        assert registry.get(ComponentType.FIGHTER) == fighter
        assert registry.get(ComponentType.AI) == ai
    
    def test_add_duplicate_component_raises_error(self):
        """Test that adding duplicate component type raises ValueError."""
        registry = ComponentRegistry()
        fighter1 = Fighter(hp=10, defense=5, power=3)
        fighter2 = Fighter(hp=20, defense=10, power=6)
        
        registry.add(ComponentType.FIGHTER, fighter1)
        
        with pytest.raises(ValueError, match="already exists"):
            registry.add(ComponentType.FIGHTER, fighter2)
    
    def test_add_with_invalid_type_raises_error(self):
        """Test that adding with non-ComponentType raises TypeError."""
        registry = ComponentRegistry()
        fighter = Fighter(hp=10, defense=5, power=3)
        
        with pytest.raises(TypeError, match="must be ComponentType"):
            registry.add("fighter", fighter)  # String instead of enum


class TestComponentRetrieval:
    """Tests for retrieving components from registry."""
    
    def test_get_existing_component(self):
        """Test getting a component that exists."""
        registry = ComponentRegistry()
        fighter = Fighter(hp=10, defense=5, power=3)
        registry.add(ComponentType.FIGHTER, fighter)
        
        retrieved = registry.get(ComponentType.FIGHTER)
        
        assert retrieved is fighter
        assert retrieved.hp == 10
    
    def test_get_nonexistent_component_returns_none(self):
        """Test that getting non-existent component returns None."""
        registry = ComponentRegistry()
        
        result = registry.get(ComponentType.FIGHTER)
        
        assert result is None
    
    def test_has_existing_component(self):
        """Test has() returns True for existing component."""
        registry = ComponentRegistry()
        fighter = Fighter(hp=10, defense=5, power=3)
        registry.add(ComponentType.FIGHTER, fighter)
        
        assert registry.has(ComponentType.FIGHTER)
    
    def test_has_nonexistent_component(self):
        """Test has() returns False for non-existent component."""
        registry = ComponentRegistry()
        
        assert not registry.has(ComponentType.FIGHTER)
    
    def test_contains_operator(self):
        """Test 'in' operator for component existence."""
        registry = ComponentRegistry()
        fighter = Fighter(hp=10, defense=5, power=3)
        registry.add(ComponentType.FIGHTER, fighter)
        
        assert ComponentType.FIGHTER in registry
        assert ComponentType.AI not in registry


class TestComponentRemoval:
    """Tests for removing components from registry."""
    
    def test_remove_existing_component(self):
        """Test removing a component that exists."""
        registry = ComponentRegistry()
        fighter = Fighter(hp=10, defense=5, power=3)
        registry.add(ComponentType.FIGHTER, fighter)
        
        removed = registry.remove(ComponentType.FIGHTER)
        
        assert removed is fighter
        assert not registry.has(ComponentType.FIGHTER)
        assert len(registry) == 0
    
    def test_remove_nonexistent_component_returns_none(self):
        """Test removing non-existent component returns None."""
        registry = ComponentRegistry()
        
        result = registry.remove(ComponentType.FIGHTER)
        
        assert result is None
    
    def test_remove_does_not_affect_other_components(self):
        """Test that removing one component doesn't affect others."""
        registry = ComponentRegistry()
        fighter = Fighter(hp=10, defense=5, power=3)
        ai = BasicMonster()
        registry.add(ComponentType.FIGHTER, fighter)
        registry.add(ComponentType.AI, ai)
        
        registry.remove(ComponentType.FIGHTER)
        
        assert not registry.has(ComponentType.FIGHTER)
        assert registry.has(ComponentType.AI)
        assert registry.get(ComponentType.AI) is ai
    
    def test_clear_removes_all_components(self):
        """Test that clear() removes all components."""
        registry = ComponentRegistry()
        registry.add(ComponentType.FIGHTER, Fighter(hp=10, defense=5, power=3))
        registry.add(ComponentType.AI, BasicMonster())
        
        assert len(registry) == 2
        
        registry.clear()
        
        assert len(registry) == 0
        assert not registry.has(ComponentType.FIGHTER)
        assert not registry.has(ComponentType.AI)


class TestComponentCollectionOperations:
    """Tests for collection-style operations on registry."""
    
    def test_iteration_over_components(self):
        """Test iterating over all components."""
        registry = ComponentRegistry()
        fighter = Fighter(hp=10, defense=5, power=3)
        ai = BasicMonster()
        registry.add(ComponentType.FIGHTER, fighter)
        registry.add(ComponentType.AI, ai)
        
        components = list(registry)
        
        assert len(components) == 2
        assert fighter in components
        assert ai in components
    
    def test_iteration_over_empty_registry(self):
        """Test iterating over empty registry."""
        registry = ComponentRegistry()
        
        components = list(registry)
        
        assert len(components) == 0
    
    def test_length_reflects_component_count(self):
        """Test that len() returns correct count."""
        registry = ComponentRegistry()
        
        assert len(registry) == 0
        
        registry.add(ComponentType.FIGHTER, Fighter(hp=10, defense=5, power=3))
        assert len(registry) == 1
        
        registry.add(ComponentType.AI, BasicMonster())
        assert len(registry) == 2
        
        registry.remove(ComponentType.FIGHTER)
        assert len(registry) == 1
    
    def test_get_all_types(self):
        """Test getting list of all component types."""
        registry = ComponentRegistry()
        registry.add(ComponentType.FIGHTER, Fighter(hp=10, defense=5, power=3))
        registry.add(ComponentType.AI, BasicMonster())
        
        types = registry.get_all_types()
        
        assert len(types) == 2
        assert ComponentType.FIGHTER in types
        assert ComponentType.AI in types
    
    def test_get_all_types_empty_registry(self):
        """Test get_all_types() on empty registry."""
        registry = ComponentRegistry()
        
        types = registry.get_all_types()
        
        assert types == []


class TestComponentRegistryRepr:
    """Tests for registry string representation."""
    
    def test_repr_shows_component_types(self):
        """Test that repr() shows component types."""
        registry = ComponentRegistry()
        registry.add(ComponentType.FIGHTER, Fighter(hp=10, defense=5, power=3))
        
        repr_str = repr(registry)
        
        assert "ComponentRegistry" in repr_str
        assert "FIGHTER" in repr_str
        assert "count=1" in repr_str
    
    def test_repr_empty_registry(self):
        """Test repr() for empty registry."""
        registry = ComponentRegistry()
        
        repr_str = repr(registry)
        
        assert "ComponentRegistry" in repr_str
        assert "count=0" in repr_str


class TestComponentRegistryEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_add_none_component(self):
        """Test that adding None as component works (for compatibility)."""
        registry = ComponentRegistry()
        
        # Some entities might have None for optional components
        registry.add(ComponentType.AI, None)
        
        assert registry.has(ComponentType.AI)
        assert registry.get(ComponentType.AI) is None
    
    def test_multiple_sequential_operations(self):
        """Test complex sequence of operations."""
        registry = ComponentRegistry()
        fighter = Fighter(hp=10, defense=5, power=3)
        
        # Add
        registry.add(ComponentType.FIGHTER, fighter)
        assert registry.has(ComponentType.FIGHTER)
        
        # Get
        retrieved = registry.get(ComponentType.FIGHTER)
        assert retrieved is fighter
        
        # Remove
        removed = registry.remove(ComponentType.FIGHTER)
        assert removed is fighter
        assert not registry.has(ComponentType.FIGHTER)
        
        # Add again (should work after removal)
        fighter2 = Fighter(hp=20, defense=10, power=6)
        registry.add(ComponentType.FIGHTER, fighter2)
        assert registry.get(ComponentType.FIGHTER) is fighter2
        assert registry.get(ComponentType.FIGHTER) is not fighter
