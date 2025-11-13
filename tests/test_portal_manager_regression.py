"""Regression test for portal_manager UnboundLocalError fix.

Tests that ComponentType imports and key normalization work correctly,
especially in portal manager functions that handle component lookups.

Regression Issue: UnboundLocalError when creating portal entities due to
ComponentType being imported inside a function while also used in module scope.

Fix: Move ComponentType import to module scope and use _ck() helper to normalize keys.
"""

import pytest
from entity import Entity
from components.component_registry import ComponentType
from services.portal_manager import PortalManager, _ck, ComponentType as PM_ComponentType


class TestPortalManagerComponentType:
    """Test that ComponentType is properly available at module scope."""
    
    def test_component_type_import_at_module_scope(self):
        """Verify ComponentType is available at portal_manager module scope."""
        assert PM_ComponentType is not None, "ComponentType should be imported at module scope"
    
    def test_ck_helper_with_enum(self):
        """Test _ck helper normalizes Enum keys correctly."""
        if ComponentType is not None:
            result = _ck(ComponentType.ITEM)
            # _ck returns the value of the Enum, which is an auto() integer
            assert isinstance(result, int), f"Expected int, got {type(result)}"
            assert result == ComponentType.ITEM.value
    
    def test_ck_helper_with_string(self):
        """Test _ck helper handles string keys correctly."""
        result = _ck("item")
        assert result == "item", f"Expected 'item', got {result}"
    
    def test_ck_helper_with_none_component_type(self):
        """Test _ck helper gracefully handles when ComponentType is unavailable."""
        # This tests the fallback when ComponentType import fails
        result = _ck(None)
        assert result is None
    
    def test_create_portal_entity_no_unbound_error(self):
        """Regression test: creating a portal should not raise UnboundLocalError.
        
        This was the original bug - ComponentType was used before it was bound
        in the function's local scope due to a duplicate import.
        """
        # This should not raise UnboundLocalError
        try:
            portal = PortalManager.create_portal_entity(
                portal_type='entrance',
                x=10,
                y=10,
                from_yaml=False
            )
            # Portal creation might fail for other reasons (missing YAML, etc),
            # but it should NOT raise UnboundLocalError
            # If we get here, the UnboundLocalError is fixed
            assert True, "No UnboundLocalError raised"
        except UnboundLocalError as e:
            pytest.fail(f"UnboundLocalError should not occur: {e}")
        except Exception as e:
            # Other exceptions are OK - we're only testing for UnboundLocalError
            pass
    
    def test_ck_handles_both_enum_and_string_keys(self):
        """Test that _ck properly normalizes both Enum and string component keys."""
        # Test with string
        assert _ck("portal") == "portal"
        assert _ck("ai") == "ai"
        assert _ck("inventory") == "inventory"
        
        # Test with Enum (if available)
        # _ck returns the enum's integer value, not a string
        if ComponentType is not None:
            assert _ck(ComponentType.PORTAL) == ComponentType.PORTAL.value
            assert _ck(ComponentType.AI) == ComponentType.AI.value
            assert _ck(ComponentType.INVENTORY) == ComponentType.INVENTORY.value


class TestPortalManagerComponentAccess:
    """Test that portal manager can access components without UnboundLocalError."""
    
    def test_check_portal_collision_accesses_components(self):
        """Test that check_portal_collision can safely access entity components."""
        # Create a minimal test entity
        entity = Entity(10, 10, '@', (255, 255, 255), 'Player')
        entities = [entity]
        
        # This should not raise UnboundLocalError when checking components
        try:
            result = PortalManager.check_portal_collision(entity, entities)
            # Result should be None (no portal), but should execute without UnboundLocalError
            assert result is None
        except UnboundLocalError as e:
            pytest.fail(f"UnboundLocalError should not occur in check_portal_collision: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

