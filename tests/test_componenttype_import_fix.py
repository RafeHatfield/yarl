"""Test that ComponentType is properly imported in components that use it.

This test verifies the fix for the runtime error:
    ERROR: Error processing mouse action sidebar_click: name 'ComponentType' is not defined
    File components/item.py, line 126:
        if hasattr(entity, 'item') and entity.get_component_optional(ComponentType.ITEM) ...
"""

import pytest
import importlib
import sys


class TestComponentTypeImports:
    """Verify ComponentType is properly imported in component files that use it."""
    
    def test_item_py_imports_componenttype(self):
        """Test that item.py imports ComponentType and can reference it."""
        # Import the module fresh
        if 'components.item' in sys.modules:
            importlib.reload(sys.modules['components.item'])
        else:
            import components.item
        
        # Try to access ComponentType from the item module's namespace
        # This will raise NameError if ComponentType wasn't imported
        try:
            from components.item import Item
            # Check that the module has ComponentType in its namespace
            import components.item as item_module
            # ComponentType should be accessible in the module
            assert hasattr(item_module, 'ComponentType'), \
                "ComponentType not found in item.py module namespace"
        except NameError as e:
            if "ComponentType" in str(e):
                pytest.fail(f"ComponentType not properly imported in item.py: {e}")
            raise
    
    def test_chest_py_imports_componenttype(self):
        """Test that chest.py imports ComponentType and can reference it."""
        # Import the module fresh
        if 'components.chest' in sys.modules:
            importlib.reload(sys.modules['components.chest'])
        else:
            import components.chest
        
        try:
            from components.chest import Chest
            # Check that the module has ComponentType in its namespace
            import components.chest as chest_module
            assert hasattr(chest_module, 'ComponentType'), \
                "ComponentType not found in chest.py module namespace"
        except NameError as e:
            if "ComponentType" in str(e):
                pytest.fail(f"ComponentType not properly imported in chest.py: {e}")
            raise
    
    def test_ring_py_imports_componenttype(self):
        """Test that ring.py imports ComponentType and can reference it."""
        # Import the module fresh
        if 'components.ring' in sys.modules:
            importlib.reload(sys.modules['components.ring'])
        else:
            import components.ring
        
        try:
            from components.ring import Ring
            # Check that the module has ComponentType in its namespace
            import components.ring as ring_module
            assert hasattr(ring_module, 'ComponentType'), \
                "ComponentType not found in ring.py module namespace"
        except NameError as e:
            if "ComponentType" in str(e):
                pytest.fail(f"ComponentType not properly imported in ring.py: {e}")
            raise
    
    def test_all_three_modules_load_without_nameerror(self):
        """Integration test: All three fixed modules should load without NameError."""
        errors = []
        
        # Try importing all three modules that were fixed
        try:
            import components.item
        except NameError as e:
            if "ComponentType" in str(e):
                errors.append(f"item.py: {e}")
        
        try:
            import components.chest
        except NameError as e:
            if "ComponentType" in str(e):
                errors.append(f"chest.py: {e}")
        
        try:
            import components.ring
        except NameError as e:
            if "ComponentType" in str(e):
                errors.append(f"ring.py: {e}")
        
        if errors:
            pytest.fail(
                f"ComponentType NameErrors found in modules:\n" + "\n".join(errors)
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

