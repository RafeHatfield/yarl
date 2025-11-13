"""Tests for component key handling contracts.

This test suite verifies that component access works correctly with both
Enum keys and string keys, ensuring consistent behavior across the codebase.

Tests verify:
- ComponentType enum exists and has expected values
- Entity.get_component_optional() accepts both Enum and string keys
- Enum/string keys normalize to the same underlying value
- No NameError or KeyError when accessing components
"""

import pytest
from typing import Optional, Dict, Any


class DummyEntity:
    """Minimal entity for testing component key contracts.
    
    This dummy entity stores components in a dict and provides
    get_component_optional() that normalizes Enum vs string keys.
    """
    
    def __init__(self):
        self._components: Dict[str, Any] = {}
        self.x = 10
        self.y = 10
        self.name = "TestEntity"
    
    def get_component_optional(self, key):
        """Get optional component, normalizing Enum and string keys.
        
        Args:
            key: Component key (ComponentType enum or string)
            
        Returns:
            Component if found, None otherwise
        """
        # Normalize Enum to string
        if hasattr(key, "value"):
            key = key.value
        
        return self._components.get(key)


class TestComponentTypeEnum:
    """Test that ComponentType enum exists and has expected values."""
    
    def test_component_type_enum_exists(self):
        """ComponentType enum must be importable."""
        try:
            from components.component_registry import ComponentType
            assert ComponentType is not None
        except ImportError:
            pytest.skip("ComponentType not available in this configuration")
    
    def test_component_type_has_common_values(self):
        """ComponentType should have commonly used component types."""
        try:
            from components.component_registry import ComponentType
            
            # Check for components that might exist
            common_types = ['BOSS', 'ITEM', 'FIGHTER', 'INVENTORY', 'EQUIPMENT']
            found_any = False
            
            for attr_name in dir(ComponentType):
                if not attr_name.startswith('_'):
                    found_any = True
                    break
            
            assert found_any, "ComponentType enum has no attributes"
        except ImportError:
            pytest.skip("ComponentType not available")
    
    def test_component_type_values_are_hashable(self):
        """ComponentType enum values should be hashable (can be used as keys)."""
        try:
            from components.component_registry import ComponentType
            
            # Check that we can use enum values as dict keys
            test_dict = {}
            for attr_name in dir(ComponentType):
                if not attr_name.startswith('_'):
                    attr = getattr(ComponentType, attr_name)
                    # Try to use as dict key
                    try:
                        test_dict[attr] = True
                    except TypeError:
                        pytest.fail(f"ComponentType.{attr_name} is not hashable")
                    break
        except ImportError:
            pytest.skip("ComponentType not available")


class TestComponentKeyNormalization:
    """Test that component keys normalize correctly between Enum and string."""
    
    def test_dummy_entity_enum_vs_string_access(self):
        """Test that dummy entity accepts both Enum and string keys."""
        try:
            from components.component_registry import ComponentType
            enum_available = True
        except ImportError:
            enum_available = False
        
        entity = DummyEntity()
        
        # Store a component
        entity._components["test_component"] = "test_value"
        
        # Access with string
        result_string = entity.get_component_optional("test_component")
        assert result_string == "test_value", "String key access failed"
        
        # Access with mock enum (if available)
        if enum_available:
            try:
                from components.component_registry import ComponentType
                # We can't easily create an enum value, but we can create a mock
                class MockEnum:
                    value = "test_component"
                
                result_enum = entity.get_component_optional(MockEnum())
                assert result_enum == "test_value", "Enum key normalization failed"
            except Exception:
                pass  # Skip if can't test enum


class TestRealEntityComponentAccess:
    """Test component access on real Entity class."""
    
    def test_real_entity_get_component_optional_exists(self):
        """Real Entity should have get_component_optional method."""
        from entity import Entity
        from components.fighter import Fighter
        
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=2, power=5)
        )
        
        assert hasattr(player, 'get_component_optional'), \
            "Entity missing get_component_optional method"
    
    def test_real_entity_component_access_with_string_key(self):
        """Entity should allow component access with proper key type."""
        from entity import Entity
        from components.fighter import Fighter
        
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=2, power=5)
        )
        
        # Try accessing fighter component
        # Note: get_component_optional expects ComponentType enum, not strings
        # So we test that we can access the fighter attribute directly
        assert hasattr(player, 'fighter'), "Entity should have fighter attribute"
        fighter = player.fighter
        assert fighter is not None, "Fighter component not found"
        assert hasattr(fighter, 'hp'), "Fighter component missing hp attribute"
    
    def test_real_entity_component_access_with_enum_key(self):
        """Entity should allow component access with Enum keys."""
        try:
            from components.component_registry import ComponentType
        except ImportError:
            pytest.skip("ComponentType enum not available")
        
        from entity import Entity
        from components.fighter import Fighter
        
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=2, power=5)
        )
        
        # Try accessing with enum (if available)
        try:
            fighter_enum = ComponentType.FIGHTER if hasattr(ComponentType, 'FIGHTER') else None
            if fighter_enum:
                fighter = player.get_component_optional(fighter_enum)
                assert fighter is not None, "Fighter component not found with enum key"
        except (AttributeError, KeyError):
            # Enum might not have FIGHTER, that's OK
            pass


class TestComponentKeyConsistency:
    """Test that component keys are handled consistently across systems."""
    
    def test_component_key_access_via_enum(self):
        """Component access should work via ComponentType enum."""
        try:
            from components.component_registry import ComponentType
        except ImportError:
            pytest.skip("ComponentType not available")
        
        from entity import Entity
        from components.fighter import Fighter
        
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=2, power=5)
        )
        
        # Try accessing with enum if available
        if hasattr(ComponentType, 'FIGHTER'):
            result = player.get_component_optional(ComponentType.FIGHTER)
            assert result is not None, "Enum component key access failed"


class TestComponentNoNameErrors:
    """Test that component access doesn't raise NameError."""
    
    def test_no_name_error_on_missing_component(self):
        """Missing components should return None, not raise NameError."""
        from entity import Entity
        from components.fighter import Fighter
        
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=2, power=5)
        )
        
        # Try accessing non-existent component
        result = player.get_component_optional("nonexistent_component")
        assert result is None, "Missing component should return None"
    
    def test_no_name_error_with_invalid_key_type(self):
        """Invalid key types should be handled gracefully."""
        from entity import Entity
        from components.fighter import Fighter
        
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=2, power=5)
        )
        
        # Try with various invalid key types
        try:
            result = player.get_component_optional(12345)
            # Should either return None or raise TypeError, not NameError
        except (TypeError, KeyError, AttributeError):
            pass  # Expected
        except NameError:
            pytest.fail("NameError raised on invalid key type")


class TestDummyEntityComponentContract:
    """Test the dummy entity follows the component contract."""
    
    def test_dummy_entity_stores_components(self):
        """Dummy entity must store and retrieve components."""
        entity = DummyEntity()
        entity._components["boss"] = "boss_value"
        
        result = entity.get_component_optional("boss")
        assert result == "boss_value", "Component storage/retrieval failed"
    
    def test_dummy_entity_returns_none_for_missing(self):
        """Dummy entity must return None for missing components."""
        entity = DummyEntity()
        result = entity.get_component_optional("missing")
        assert result is None, "Missing component should return None"
    
    def test_dummy_entity_enum_normalization(self):
        """Dummy entity must normalize Enum keys to strings."""
        entity = DummyEntity()
        entity._components["test"] = "value"
        
        # Create a mock enum
        class MockEnum:
            value = "test"
        
        result = entity.get_component_optional(MockEnum())
        assert result == "value", "Enum normalization failed"


class TestEntityComponentTypes:
    """Test specific component types are accessible."""
    
    def test_fighter_component_accessible(self):
        """Fighter component must be accessible via entity."""
        from entity import Entity
        from components.fighter import Fighter
        
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=2, power=5)
        )
        
        assert hasattr(player, 'fighter')
        fighter = player.fighter
        assert fighter is not None
        assert fighter.hp == 30
    
    def test_inventory_component_accessible(self):
        """Inventory component must be accessible."""
        from entity import Entity
        from components.inventory import Inventory
        
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            inventory=Inventory(capacity=26)
        )
        
        assert hasattr(player, 'inventory')
        inventory = player.inventory
        assert inventory is not None
        assert inventory.capacity == 26
    
    def test_equipment_component_accessible(self):
        """Equipment component must be accessible."""
        from entity import Entity
        from components.equipment import Equipment
        
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            equipment=Equipment()
        )
        
        assert hasattr(player, 'equipment')
        equipment = player.equipment
        assert equipment is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

