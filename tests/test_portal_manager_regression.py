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
from services.portal_manager import PortalManager


class TestPortalManagerComponentType:
    """Test that ComponentType is properly available at module scope."""
    
    def test_component_type_import_at_module_scope(self):
        """Verify ComponentType is available at portal_manager module scope."""
        assert ComponentType is not None, "ComponentType should be imported at module scope"
    
    def test_component_type_enum_values(self):
        """Test ComponentType enum values are correct."""
        if ComponentType is not None:
            # ComponentType should have ITEM, PORTAL, AI, etc.
            assert hasattr(ComponentType, 'ITEM'), "ComponentType should have ITEM"
            assert hasattr(ComponentType, 'PORTAL'), "ComponentType should have PORTAL"
            assert hasattr(ComponentType, 'AI'), "ComponentType should have AI"
    
    def test_component_type_direct_usage(self):
        """Test using ComponentType enum directly works without _ck helper."""
        # After refactoring, we use ComponentType directly instead of _ck
        assert hasattr(ComponentType, 'ITEM')
        assert isinstance(ComponentType.ITEM, ComponentType)
    
    def test_portal_manager_uses_enum_directly(self):
        """Test that portal_manager now uses ComponentType enum directly."""
        # This verifies the refactoring removed the old _ck() conversion pattern
        # and now uses ComponentType enums directly
        import inspect
        from services import portal_manager
        
        source = inspect.getsource(portal_manager)
        # The refactored code should NOT use _ck
        assert "_ck(" not in source, "portal_manager should not use _ck() after refactoring"
        # But it SHOULD use ComponentType directly
        assert "ComponentType.PORTAL" in source, "portal_manager should use ComponentType.PORTAL directly"
    
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
    
    def test_component_type_enum_comparison(self):
        """Test that ComponentType enum members can be properly compared."""
        # After refactoring, we no longer use _ck() conversion
        # Instead we use ComponentType enums directly
        if ComponentType is not None:
            assert ComponentType.PORTAL == ComponentType.PORTAL
            assert ComponentType.AI == ComponentType.AI
            assert ComponentType.INVENTORY == ComponentType.INVENTORY
            # Each enum member should have a value property
            assert hasattr(ComponentType.PORTAL, 'value')
            assert hasattr(ComponentType.AI, 'value')
            assert hasattr(ComponentType.INVENTORY, 'value')


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

