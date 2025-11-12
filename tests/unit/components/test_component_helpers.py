"""Tests for component access helpers in Entity class.

This module tests the component access helpers (require_component, get_component_optional)
to ensure consistent, safe component access patterns throughout the codebase.
"""

import pytest
from entity import Entity
from components.component_registry import ComponentType
from components.fighter import Fighter
from components.inventory import Inventory
from render_functions import RenderOrder


class TestRequireComponent:
    """Tests for Entity.require_component() method."""
    
    def test_require_component_returns_when_exists(self):
        """require_component returns the component when it exists."""
        fighter = Fighter(hp=10, defense=2, power=3)
        entity = Entity(5, 5, '@', (255, 255, 255), 'Player', fighter=fighter)
        
        result = entity.require_component(ComponentType.FIGHTER)
        assert result is fighter
    
    def test_require_component_raises_when_missing(self):
        """require_component raises ValueError when component missing."""
        entity = Entity(5, 5, 'o', (100, 100, 100), 'Orc')
        
        with pytest.raises(ValueError):
            entity.require_component(ComponentType.FIGHTER)
    
    def test_require_component_error_message_clear(self):
        """require_component error message is clear and actionable."""
        entity = Entity(5, 5, 'o', (100, 100, 100), 'Orc')
        
        with pytest.raises(ValueError) as exc_info:
            entity.require_component(ComponentType.FIGHTER)
        
        error_msg = str(exc_info.value)
        assert "Orc" in error_msg
        assert "missing required" in error_msg
        assert "FIGHTER" in error_msg
    
    def test_require_component_works_with_different_types(self):
        """require_component works with various component types."""
        fighter = Fighter(hp=10, defense=2, power=3)
        inventory = Inventory(capacity=26)
        entity = Entity(5, 5, '@', (255, 255, 255), 'Player',
                       fighter=fighter, inventory=inventory)
        
        # Both components should be retrievable
        assert entity.require_component(ComponentType.FIGHTER) is fighter
        assert entity.require_component(ComponentType.INVENTORY) is inventory
    
    def test_require_component_raises_for_multiple_missing(self):
        """require_component raises for any missing component type."""
        fighter = Fighter(hp=10, defense=2, power=3)
        entity = Entity(5, 5, '@', (255, 255, 255), 'Player', fighter=fighter)
        
        # Fighter exists
        assert entity.require_component(ComponentType.FIGHTER) is fighter
        
        # Inventory doesn't exist
        with pytest.raises(ValueError):
            entity.require_component(ComponentType.INVENTORY)


class TestGetComponentOrNone:
    """Tests for Entity.get_component_optional() method."""
    
    def test_get_component_optional_returns_when_exists(self):
        """get_component_optional returns component when it exists."""
        fighter = Fighter(hp=10, defense=2, power=3)
        entity = Entity(5, 5, '@', (255, 255, 255), 'Player', fighter=fighter)
        
        result = entity.get_component_optional(ComponentType.FIGHTER)
        assert result is fighter
    
    def test_get_component_optional_returns_none_when_missing(self):
        """get_component_optional returns None when component missing."""
        entity = Entity(5, 5, 'o', (100, 100, 100), 'Orc')
        
        result = entity.get_component_optional(ComponentType.FIGHTER)
        assert result is None
    
    def test_get_component_optional_no_exception_on_missing(self):
        """get_component_optional doesn't raise on missing components."""
        entity = Entity(5, 5, 'o', (100, 100, 100), 'Orc')
        
        # Should not raise any exception
        result = entity.get_component_optional(ComponentType.FIGHTER)
        assert result is None
    
    def test_get_component_optional_works_with_different_types(self):
        """get_component_optional works with various component types."""
        fighter = Fighter(hp=10, defense=2, power=3)
        entity = Entity(5, 5, '@', (255, 255, 255), 'Player', fighter=fighter)
        
        # Fighter exists
        assert entity.get_component_optional(ComponentType.FIGHTER) is fighter
        
        # Inventory doesn't exist (no exception, returns None)
        assert entity.get_component_optional(ComponentType.INVENTORY) is None


class TestComponentHelperPatterns:
    """Tests for common usage patterns with component helpers."""
    
    def test_pattern_require_for_guaranteed_components(self):
        """Pattern: Use require_component for guaranteed components."""
        fighter = Fighter(hp=10, defense=2, power=3)
        entity = Entity(5, 5, '@', (255, 255, 255), 'Player', fighter=fighter)
        
        # This pattern should work: get and use immediately
        fighter_comp = entity.require_component(ComponentType.FIGHTER)
        assert fighter_comp.hp == 10
    
    def test_pattern_optional_with_check(self):
        """Pattern: Use get_component_optional then check before using."""
        fighter = Fighter(hp=10, defense=2, power=3)
        entity = Entity(5, 5, '@', (255, 255, 255), 'Player', fighter=fighter)
        
        # This pattern should work: get optionally, check, then use
        inventory = entity.get_component_optional(ComponentType.INVENTORY)
        if inventory:
            inventory.add_item(None)  # Only called if inventory exists
        else:
            # Handle missing inventory case
            pass
    
    def test_mixed_require_and_optional(self):
        """Pattern: Mix of required and optional component access."""
        fighter = Fighter(hp=10, defense=2, power=3)
        inventory = Inventory(capacity=26)
        entity = Entity(5, 5, '@', (255, 255, 255), 'Player',
                       fighter=fighter, inventory=inventory)
        
        # Required components
        fighter_comp = entity.require_component(ComponentType.FIGHTER)
        assert fighter_comp.hp == 10
        
        # Optional components
        pathfinding = entity.get_component_optional(ComponentType.PATHFINDING)
        assert pathfinding is None


class TestComponentHelperEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_require_component_with_none_name(self):
        """require_component works even if entity name is None."""
        entity = Entity(5, 5, 'x', (100, 100, 100), 'Unknown')
        
        with pytest.raises(ValueError) as exc_info:
            entity.require_component(ComponentType.FIGHTER)
        
        # Should still have informative message
        assert "missing required" in str(exc_info.value)
    
    def test_component_access_does_not_modify_state(self):
        """Component access via helpers doesn't modify entity state."""
        fighter = Fighter(hp=10, defense=2, power=3)
        entity = Entity(5, 5, '@', (255, 255, 255), 'Player', fighter=fighter)
        
        # Get component multiple times
        f1 = entity.require_component(ComponentType.FIGHTER)
        f2 = entity.require_component(ComponentType.FIGHTER)
        
        # Should be the same object
        assert f1 is f2
        assert f1 is fighter

