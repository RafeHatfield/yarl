"""Regression test for portal component double-add bug.

Tests that ensure portal entities are created with exactly one PORTAL component
and that PortalManager.create_portal_entity() doesn't attempt to add the component
twice.

Regression Issue: ValueError "Component PORTAL already exists in registry"
when using Wand of Portals. The bug was caused by:
1. Entity.__setattr__ auto-registering the PORTAL component when entity.portal = portal
2. PortalManager then calling entity.components.add(ComponentType.PORTAL, portal) again

Fix: Removed the explicit .add() call in PortalManager.create_portal_entity()
since the assignment already triggers auto-registration via __setattr__.
"""

import pytest
from entity import Entity
from components.component_registry import ComponentType
from components.portal import Portal
from services.portal_manager import PortalManager


class TestPortalComponentDoubleAdd:
    """Test suite for the portal component double-add regression."""
    
    def test_portal_entity_has_exactly_one_portal_component(self):
        """Verify portal entity has exactly one PORTAL component after creation.
        
        This is the core regression test - creating a portal should result in
        exactly one PORTAL component in the entity's component registry.
        """
        portal_entity = PortalManager.create_portal_entity(
            portal_type='entrance',
            x=10,
            y=10,
            from_yaml=False
        )
        
        assert portal_entity is not None, "Portal entity should be created"
        
        # Check that PORTAL component exists
        assert ComponentType.PORTAL in portal_entity.components, \
            "Portal entity must have PORTAL component"
        
        # Count PORTAL components (should be exactly 1)
        portal_count = sum(
            1 for ct in portal_entity.components.get_all_types()
            if ct == ComponentType.PORTAL
        )
        
        assert portal_count == 1, \
            f"Portal entity should have exactly 1 PORTAL component, found {portal_count}"
    
    def test_create_portal_entrance_no_double_add_error(self):
        """Regression test: creating entrance portal should not raise double-add error.
        
        Previously raised: ValueError: Component PORTAL already exists in registry
        """
        try:
            portal_entity = PortalManager.create_portal_entity(
                portal_type='entrance',
                x=15,
                y=15,
                from_yaml=False
            )
            
            assert portal_entity is not None, "Entrance portal should be created successfully"
            assert hasattr(portal_entity, 'portal'), "Entity should have portal attribute"
            assert portal_entity.portal is not None, "Portal attribute should not be None"
            
        except ValueError as e:
            if "already exists in registry" in str(e):
                pytest.fail(f"Double-add error should be fixed: {e}")
            else:
                raise
    
    def test_create_portal_exit_no_double_add_error(self):
        """Test that exit portal creation also doesn't trigger double-add error."""
        try:
            portal_entity = PortalManager.create_portal_entity(
                portal_type='exit',
                x=20,
                y=20,
                from_yaml=False
            )
            
            assert portal_entity is not None, "Exit portal should be created successfully"
            assert hasattr(portal_entity, 'portal'), "Entity should have portal attribute"
            assert portal_entity.portal is not None, "Portal attribute should not be None"
            
        except ValueError as e:
            if "already exists in registry" in str(e):
                pytest.fail(f"Double-add error should be fixed: {e}")
            else:
                raise
    
    def test_create_entity_portal_no_double_add_error(self):
        """Test that entity_portal (victory portal) creation doesn't trigger double-add error."""
        try:
            portal_entity = PortalManager.create_portal_entity(
                portal_type='entity_portal',
                x=25,
                y=25,
                from_yaml=False
            )
            
            # Victory portal creation might fail for other reasons, but not double-add
            if portal_entity is not None:
                assert hasattr(portal_entity, 'portal'), "Entity should have portal attribute"
                
        except ValueError as e:
            if "already exists in registry" in str(e):
                pytest.fail(f"Double-add error should be fixed: {e}")
            else:
                raise
    
    def test_portal_component_accessible_via_registry(self):
        """Verify the portal component is accessible via the registry after creation."""
        portal_entity = PortalManager.create_portal_entity(
            portal_type='entrance',
            x=30,
            y=30,
            from_yaml=False
        )
        
        assert portal_entity is not None, "Portal entity should be created"
        
        # Get portal via registry
        portal_from_registry = portal_entity.components.get(ComponentType.PORTAL)
        
        assert portal_from_registry is not None, \
            "Portal component should be retrievable from registry"
        
        # Should be the same object
        assert portal_from_registry is portal_entity.portal, \
            "Portal from registry should be the same object as entity.portal"
    
    def test_portal_component_accessible_via_attribute(self):
        """Verify the portal component is accessible via entity.portal attribute."""
        portal_entity = PortalManager.create_portal_entity(
            portal_type='entrance',
            x=35,
            y=35,
            from_yaml=False
        )
        
        assert portal_entity is not None, "Portal entity should be created"
        
        # Access via attribute
        portal_from_attr = portal_entity.portal
        
        assert portal_from_attr is not None, \
            "Portal should be accessible via entity.portal"
        
        assert isinstance(portal_from_attr, Portal), \
            "Portal attribute should be a Portal instance"
    
    def test_portal_pair_creation_no_double_add_error(self):
        """Test that linked portal pairs don't trigger double-add errors."""
        # Create entrance
        entrance_entity = PortalManager.create_portal_entity(
            portal_type='entrance',
            x=40,
            y=40,
            from_yaml=False
        )
        
        assert entrance_entity is not None, "Entrance should be created"
        entrance_portal = entrance_entity.portal
        
        # Create exit linked to entrance
        try:
            exit_entity = PortalManager.create_portal_entity(
                portal_type='exit',
                x=45,
                y=45,
                linked_portal=entrance_portal,
                from_yaml=False
            )
            
            assert exit_entity is not None, "Exit should be created with link"
            
            # Link them
            success = PortalManager.link_portal_pair(
                entrance_portal,
                exit_entity.portal
            )
            assert success, "Linking should succeed"
            
        except ValueError as e:
            if "already exists in registry" in str(e):
                pytest.fail(f"Double-add error in linked portal creation: {e}")
            else:
                raise
    
    def test_multiple_portal_creations_no_cumulative_errors(self):
        """Test that creating multiple portals sequentially doesn't accumulate errors."""
        portal_count = 5
        
        try:
            for i in range(portal_count):
                portal_entity = PortalManager.create_portal_entity(
                    portal_type='entrance' if i % 2 == 0 else 'exit',
                    x=50 + i,
                    y=50 + i,
                    from_yaml=False
                )
                
                assert portal_entity is not None, \
                    f"Portal {i} should be created successfully"
                
                # Each should have exactly one PORTAL component
                assert ComponentType.PORTAL in portal_entity.components, \
                    f"Portal {i} should have PORTAL component"
                    
        except ValueError as e:
            if "already exists in registry" in str(e):
                pytest.fail(f"Double-add error on iteration {i}: {e}")
            else:
                raise
    
    def test_portal_component_registry_has_correct_count(self):
        """Verify the component registry has the expected count of components."""
        portal_entity = PortalManager.create_portal_entity(
            portal_type='entrance',
            x=60,
            y=60,
            from_yaml=False
        )
        
        assert portal_entity is not None, "Portal entity should be created"
        
        # Portal entities created via PortalManager should have at minimum:
        # - PORTAL component
        # - ITEM component
        all_types = portal_entity.components.get_all_types()
        
        assert ComponentType.PORTAL in all_types, \
            "Must have PORTAL component"
        assert ComponentType.ITEM in all_types, \
            "Must have ITEM component"
        
        # Count should be at least 2
        assert len(all_types) >= 2, \
            f"Should have at least 2 components (PORTAL, ITEM), found {len(all_types)}"


class TestPortalComponentAutoRegistration:
    """Test Entity.__setattr__ auto-registration behavior with portals."""
    
    def test_entity_setattr_auto_registers_portal(self):
        """Test that setting entity.portal triggers auto-registration in component registry."""
        entity = Entity(10, 10, '[', (0, 255, 255), 'Test Portal')
        
        # Manually create and assign portal
        portal = Portal('entrance')
        entity.portal = portal
        
        # Should be auto-registered
        assert ComponentType.PORTAL in entity.components, \
            "Portal should be auto-registered via __setattr__"
        
        # Registry should return the same object
        registry_portal = entity.components.get(ComponentType.PORTAL)
        assert registry_portal is portal, \
            "Registry should contain the same portal object"
    
    def test_entity_setattr_prevents_double_registration(self):
        """Test that Entity.__setattr__ prevents double-registration of components."""
        entity = Entity(10, 10, '[', (0, 255, 255), 'Test Portal')
        
        portal = Portal('entrance')
        entity.portal = portal
        
        # Try to add the same component manually - should fail if not handled
        with pytest.raises(ValueError, match="already exists"):
            entity.components.add(ComponentType.PORTAL, portal)
    
    def test_entity_get_component_methods_work_with_portals(self):
        """Test that get_component_optional works with portals."""
        entity = Entity(10, 10, '[', (0, 255, 255), 'Test Portal')
        portal = Portal('entrance')
        entity.portal = portal
        
        # Should be retrievable via get_component_optional
        retrieved = entity.get_component_optional(ComponentType.PORTAL)
        assert retrieved is portal, \
            "get_component_optional should return the portal"


class TestPortalManagerIntegration:
    """Integration tests for PortalManager with game entities."""
    
    def test_portal_has_correct_owner_after_creation(self):
        """Test that portal.owner is correctly set to the entity."""
        portal_entity = PortalManager.create_portal_entity(
            portal_type='entrance',
            x=70,
            y=70,
            from_yaml=False
        )
        
        assert portal_entity is not None, "Portal entity should be created"
        assert portal_entity.portal.owner is portal_entity, \
            "Portal.owner should reference the entity"
    
    def test_portal_is_deployed_flag(self):
        """Test that newly created portals have is_deployed=True."""
        portal_entity = PortalManager.create_portal_entity(
            portal_type='entrance',
            x=75,
            y=75,
            from_yaml=False
        )
        
        assert portal_entity is not None, "Portal entity should be created"
        assert portal_entity.portal.is_deployed is True, \
            "Newly created portal should be deployed"
    
    def test_portal_type_is_preserved(self):
        """Test that portal_type is correctly assigned."""
        entrance = PortalManager.create_portal_entity(
            portal_type='entrance',
            x=80,
            y=80,
            from_yaml=False
        )
        
        exit_portal = PortalManager.create_portal_entity(
            portal_type='exit',
            x=85,
            y=85,
            from_yaml=False
        )
        
        assert entrance is not None, "Entrance should be created"
        assert exit_portal is not None, "Exit should be created"
        
        assert entrance.portal.portal_type == 'entrance', \
            "Entrance portal_type should be 'entrance'"
        assert exit_portal.portal.portal_type == 'exit', \
            "Exit portal_type should be 'exit'"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

