"""Test that ComponentType is properly imported in components that use it.

This test verifies the fix for the runtime error:
    ERROR: Error processing mouse action sidebar_click: name 'ComponentType' is not defined
    File components/item.py, line 126:
        if hasattr(entity, 'item') and entity.get_component_optional(ComponentType.ITEM) ...

NOTE: These tests previously used importlib.reload() which caused issues with enum identity.
Now they simply verify that ComponentType is present in each module's namespace without reloading,
which is sufficient to verify the imports are correct.
"""

import pytest


class TestComponentTypeImports:
    """Verify ComponentType is properly imported in component files that use it."""
    
    def test_item_py_imports_componenttype(self):
        """Test that item.py imports ComponentType and can reference it."""
        # Import the module and verify ComponentType is in its namespace
        import components.item as item_module
        
        # ComponentType should be accessible in the module's namespace
        assert hasattr(item_module, 'ComponentType'), \
            "ComponentType not found in item.py module namespace"
        
        # Verify the import works by checking it's the correct type
        from components.component_registry import ComponentType as ExpectedType
        assert item_module.ComponentType is ExpectedType, \
            "ComponentType in item.py is not the expected ComponentType enum"
    
    def test_chest_py_imports_componenttype(self):
        """Test that chest.py imports ComponentType and can reference it."""
        import components.chest as chest_module
        
        assert hasattr(chest_module, 'ComponentType'), \
            "ComponentType not found in chest.py module namespace"
        
        from components.component_registry import ComponentType as ExpectedType
        assert chest_module.ComponentType is ExpectedType, \
            "ComponentType in chest.py is not the expected ComponentType enum"
    
    def test_ring_py_imports_componenttype(self):
        """Test that ring.py imports ComponentType and can reference it."""
        import components.ring as ring_module
        
        assert hasattr(ring_module, 'ComponentType'), \
            "ComponentType not found in ring.py module namespace"
        
        from components.component_registry import ComponentType as ExpectedType
        assert ring_module.ComponentType is ExpectedType, \
            "ComponentType in ring.py is not the expected ComponentType enum"
    
    def test_all_three_modules_have_componenttype(self):
        """Integration test: All three fixed modules should have ComponentType."""
        from components.component_registry import ComponentType as ExpectedType
        
        errors = []
        
        import components.item as item_mod
        if not hasattr(item_mod, 'ComponentType'):
            errors.append("item.py: ComponentType not in namespace")
        elif item_mod.ComponentType is not ExpectedType:
            errors.append("item.py: ComponentType is wrong type")
        
        import components.chest as chest_mod
        if not hasattr(chest_mod, 'ComponentType'):
            errors.append("chest.py: ComponentType not in namespace")
        elif chest_mod.ComponentType is not ExpectedType:
            errors.append("chest.py: ComponentType is wrong type")
        
        import components.ring as ring_mod
        if not hasattr(ring_mod, 'ComponentType'):
            errors.append("ring.py: ComponentType not in namespace")
        elif ring_mod.ComponentType is not ExpectedType:
            errors.append("ring.py: ComponentType is wrong type")
        
        if errors:
            pytest.fail(
                f"ComponentType issues found in modules:\n" + "\n".join(errors)
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

