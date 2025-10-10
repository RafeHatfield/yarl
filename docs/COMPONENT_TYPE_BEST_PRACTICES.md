# ComponentType Best Practices

This document outlines best practices for using `ComponentType` to prevent scoping errors and ensure consistent behavior across the codebase.

## The Problem

Python's scoping rules can cause issues when imports are mixed between module-level and function-level. A local import inside a function can create a local scope that shadows or conflicts with references earlier in the same function, leading to `NameError: name 'ComponentType' is not defined`.

### Example of the Bug

```python
def some_method(self):
    # Line 406: Uses ComponentType - expects it from module-level import
    inventory = self.owner.components.get(ComponentType.INVENTORY)
    
    # ... other code ...
    
    # Line 425: Local import creates local scope
    from components.component_registry import ComponentType as CT
    if item.components.has(CT.EQUIPPABLE):
        # ...
```

This pattern causes ComponentType on line 406 to be undefined because Python sees the local import on line 425 and treats ComponentType as a local variable throughout the entire function scope.

## Best Practices

### 1. Always Use Module-Level Imports

**✅ DO THIS:**
```python
# At top of file
from components.component_registry import ComponentType

class MyComponent:
    def some_method(self):
        inventory = self.owner.components.get(ComponentType.INVENTORY)
        if item.components.has(ComponentType.EQUIPPABLE):
            # ...
```

**❌ DON'T DO THIS:**
```python
class MyComponent:
    def some_method(self):
        from components.component_registry import ComponentType
        inventory = self.owner.components.get(ComponentType.INVENTORY)
```

### 2. Never Mix Module and Local Imports

If you must use a local import (e.g., to avoid circular dependencies), ensure ALL uses of that import are AFTER the local import statement.

**❌ NEVER DO THIS:**
```python
def some_method(self):
    inventory = self.owner.components.get(ComponentType.INVENTORY)  # Uses ComponentType
    # ... 
    from components.component_registry import ComponentType  # Local import
```

### 3. Use Consistent Import Aliases

If you need to use an alias, use it consistently:

**✅ DO THIS:**
```python
# At top of file
from components.component_registry import ComponentType as CT

class MyComponent:
    def method_a(self):
        return self.owner.components.get(CT.INVENTORY)
    
    def method_b(self):
        return self.owner.components.has(CT.FIGHTER)
```

### 4. Prefer ComponentRegistry Over Attributes

When migrating from `hasattr()` checks, prefer using the ComponentRegistry:

**✅ DO THIS:**
```python
inventory = entity.components.get(ComponentType.INVENTORY)
if inventory:
    # Use inventory
```

**⚠️ FALLBACK (if needed for backward compatibility):**
```python
inventory = entity.components.get(ComponentType.INVENTORY)
if not inventory:
    inventory = getattr(entity, 'inventory', None)
if inventory:
    # Use inventory
```

## Testing for ComponentType Issues

Regression tests have been added in `tests/test_component_type_scoping.py` to catch these issues:

- Test picking up different item types (wands, scrolls, weapons, armor)
- Test methods that use ComponentType internally
- Test that ComponentType is accessible in all component methods

Run these tests regularly:
```bash
python -m pytest tests/test_component_type_scoping.py -v
```

## Files Fixed

The following files were identified and fixed for ComponentType scoping issues:

1. **components/ai.py**
   - Fixed: Removed local import in `_pickup_item` method
   - Uses: Module-level `from components.component_registry import ComponentType`

2. **components/item_seeking_ai.py**
   - Fixed: Added module-level import, removed 3 local imports
   - Uses: Module-level `from components.component_registry import ComponentType`

3. **item_functions.py**
   - Fixed: Added module-level imports for `GroundHazard`, `HazardType`, and status effects
   - Removed 5 local imports that caused scoping conflicts
   - Affected functions: `cast_dragon_fart`, `cast_slow`, `cast_glue`, `cast_rage`, `cast_teleportation`

## How to Find Violations

Search for local imports of ComponentType:
```bash
grep -rn "    from components.component_registry import ComponentType" --include="*.py" components/
```

Any results from this search indicate a potential scoping issue and should be refactored to use module-level imports.

## Why This Matters

This issue was discovered when:
1. An orc tried to pick up a wand → `NameError: name 'ComponentType' is not defined`
2. An orc tried to pick up a Yo Mama scroll → Same error
3. An orc tried to use a Lightning Scroll → Same error (item usage failure path)

These errors occurred due to the mixed import pattern. This was a **systemic issue** affecting:
- Monster item pickup (all item types)
- Monster scroll usage (all failure modes)
- Dragon Fart spell (hazard creation + AI checks)
- Status effect spells (Slow, Glue, Rage, Teleportation)

The bug could cause crashes during normal gameplay whenever monsters interacted with items or spells.

## Related Documentation

- `docs/COMPONENT_REGISTRY_DESIGN.md` - Overall component registry design
- `tests/test_component_type_scoping.py` - Regression tests
- `TECH_DEBT.md` - Tracks component migration progress

