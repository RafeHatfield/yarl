"""Tests for Entity component access helper methods.

This module tests the new standardized component access methods:
- require_component() - Must exist, raises error if missing
- get_component_optional() - May exist, returns None if missing
- has_component() - Check for component existence
"""

import pytest
from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from components.component_registry import ComponentType
from render_functions import RenderOrder


class TestComponentAccessHelpers:
    """Test the new component access helper methods."""
    
    def test_require_component_success(self):
        """Test require_component returns component when it exists."""
        # Create entity with Fighter component
        fighter = Fighter(hp=20, defense=2, power=5, xp=10)
        entity = Entity(
            0, 0, 'o', (255, 255, 255), 'Orc',
            blocks=True,
            render_order=RenderOrder.ACTOR,
            fighter=fighter
        )
        
        # Should return the component
        result = entity.require_component(ComponentType.FIGHTER)
        assert result is fighter
        assert result.hp == 20
    
    def test_require_component_raises_on_missing(self):
        """Test require_component raises ValueError when component missing."""
        # Create entity without Fighter component
        entity = Entity(
            0, 0, 'i', (255, 255, 255), 'Potion',
            blocks=False,
            render_order=RenderOrder.ITEM
        )
        
        # Should raise ValueError with clear message
        with pytest.raises(ValueError) as exc_info:
            entity.require_component(ComponentType.FIGHTER)
        
        assert "Potion" in str(exc_info.value)
        assert "missing required component" in str(exc_info.value)
        assert "fighter" in str(exc_info.value).lower()
    
    def test_get_component_optional_success(self):
        """Test get_component_optional returns component when it exists."""
        # Create entity with Inventory component
        inventory = Inventory(capacity=10)
        entity = Entity(
            0, 0, 'o', (255, 255, 255), 'Orc',
            blocks=True,
            render_order=RenderOrder.ACTOR,
            inventory=inventory
        )
        
        # Should return the component
        result = entity.get_component_optional(ComponentType.INVENTORY)
        assert result is inventory
        assert result.capacity == 10
    
    def test_get_component_optional_returns_none_when_missing(self):
        """Test get_component_optional returns None when component missing."""
        # Create entity without Inventory component
        entity = Entity(
            0, 0, 'i', (255, 255, 255), 'Potion',
            blocks=False,
            render_order=RenderOrder.ITEM
        )
        
        # Should return None (no exception)
        result = entity.get_component_optional(ComponentType.INVENTORY)
        assert result is None
    
    def test_has_component_returns_true_when_present(self):
        """Test has_component returns True when component exists."""
        # Create entity with Fighter component
        fighter = Fighter(hp=20, defense=2, power=5, xp=10)
        entity = Entity(
            0, 0, 'o', (255, 255, 255), 'Orc',
            blocks=True,
            render_order=RenderOrder.ACTOR,
            fighter=fighter
        )
        
        # Should return True
        assert entity.has_component(ComponentType.FIGHTER) is True
    
    def test_has_component_returns_false_when_missing(self):
        """Test has_component returns False when component missing."""
        # Create entity without Fighter component
        entity = Entity(
            0, 0, 'i', (255, 255, 255), 'Potion',
            blocks=False,
            render_order=RenderOrder.ITEM
        )
        
        # Should return False
        assert entity.has_component(ComponentType.FIGHTER) is False
    
    def test_multiple_components(self):
        """Test accessing multiple components on same entity."""
        # Create entity with multiple components
        fighter = Fighter(hp=20, defense=2, power=5, xp=10)
        inventory = Inventory(capacity=10)
        entity = Entity(
            0, 0, 'o', (255, 255, 255), 'Orc',
            blocks=True,
            render_order=RenderOrder.ACTOR,
            fighter=fighter,
            inventory=inventory
        )
        
        # All three methods should work correctly
        assert entity.has_component(ComponentType.FIGHTER) is True
        assert entity.has_component(ComponentType.INVENTORY) is True
        assert entity.has_component(ComponentType.AI) is False
        
        assert entity.require_component(ComponentType.FIGHTER) is fighter
        assert entity.require_component(ComponentType.INVENTORY) is inventory
        
        assert entity.get_component_optional(ComponentType.FIGHTER) is fighter
        assert entity.get_component_optional(ComponentType.INVENTORY) is inventory
        assert entity.get_component_optional(ComponentType.AI) is None


class TestComponentAccessPatternComparison:
    """Test that new helpers work identically to old patterns."""
    
    def test_require_vs_old_pattern(self):
        """Test require_component vs components.get() with manual check."""
        fighter = Fighter(hp=20, defense=2, power=5, xp=10)
        entity = Entity(
            0, 0, 'o', (255, 255, 255), 'Orc',
            blocks=True,
            render_order=RenderOrder.ACTOR,
            fighter=fighter
        )
        
        # Old pattern
        old_result = entity.components.get(ComponentType.FIGHTER)
        
        # New pattern
        new_result = entity.require_component(ComponentType.FIGHTER)
        
        # Should be identical
        assert old_result is new_result
        assert old_result is fighter
    
    def test_optional_vs_old_pattern(self):
        """Test get_component_optional vs components.get()."""
        fighter = Fighter(hp=20, defense=2, power=5, xp=10)
        entity = Entity(
            0, 0, 'o', (255, 255, 255), 'Orc',
            blocks=True,
            render_order=RenderOrder.ACTOR,
            fighter=fighter
        )
        
        # Old pattern
        old_result = entity.components.get(ComponentType.FIGHTER)
        
        # New pattern
        new_result = entity.get_component_optional(ComponentType.FIGHTER)
        
        # Should be identical
        assert old_result is new_result
        assert old_result is fighter
    
    def test_has_vs_old_pattern(self):
        """Test has_component vs components.has()."""
        fighter = Fighter(hp=20, defense=2, power=5, xp=10)
        entity = Entity(
            0, 0, 'o', (255, 255, 255), 'Orc',
            blocks=True,
            render_order=RenderOrder.ACTOR,
            fighter=fighter
        )
        
        # Old pattern
        old_result = entity.components.has(ComponentType.FIGHTER)
        
        # New pattern
        new_result = entity.has_component(ComponentType.FIGHTER)
        
        # Should be identical
        assert old_result is new_result
        assert old_result is True


class TestComponentAccessEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_require_component_with_none_component(self):
        """Test require_component behavior when component is explicitly None."""
        entity = Entity(
            0, 0, 'i', (255, 255, 255), 'Test',
            blocks=False,
            render_order=RenderOrder.ITEM
        )
        
        # Should raise ValueError
        with pytest.raises(ValueError):
            entity.require_component(ComponentType.FIGHTER)
    
    def test_multiple_require_calls_same_component(self):
        """Test calling require_component multiple times returns same instance."""
        fighter = Fighter(hp=20, defense=2, power=5, xp=10)
        entity = Entity(
            0, 0, 'o', (255, 255, 255), 'Orc',
            blocks=True,
            render_order=RenderOrder.ACTOR,
            fighter=fighter
        )
        
        # Multiple calls should return same instance
        first = entity.require_component(ComponentType.FIGHTER)
        second = entity.require_component(ComponentType.FIGHTER)
        third = entity.require_component(ComponentType.FIGHTER)
        
        assert first is second
        assert second is third
        assert first is fighter
    
    def test_error_message_includes_entity_name(self):
        """Test that error messages include the entity name for debugging."""
        entity = Entity(
            0, 0, 'o', (255, 255, 255), 'Specific Orc Name',
            blocks=True,
            render_order=RenderOrder.ACTOR
        )
        
        with pytest.raises(ValueError) as exc_info:
            entity.require_component(ComponentType.FIGHTER)
        
        # Error should mention the specific entity
        assert "Specific Orc Name" in str(exc_info.value)

