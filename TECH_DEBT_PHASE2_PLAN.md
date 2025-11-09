# Tech Debt Phase 2: Component Access Helpers & Standardization

**Status:** IN PROGRESS  
**Start Date:** November 8, 2025  
**Target Duration:** 3-4 days  
**Goal:** Eliminate silent failures and standardize component access across all systems

---

## 🎯 Phase 2 Overview

**Problem:** Component access is inconsistent and causes silent failures:

```python
# ANTI-PATTERN 1: Returns None on missing (silent failure)
fighter = entity.components.get(ComponentType.FIGHTER)
if fighter is None:
    # Silent failure - hard to debug
    pass

# ANTI-PATTERN 2: Throws AttributeError (crashes)
fighter = entity.fighter  # If missing, crashes
```

**Solution:** Create helpers that enforce consistent patterns with clear error messages.

---

## 📋 Task Breakdown

### TASK 2.1: Create Component Access Helpers
**Duration:** 1 day  
**Status:** PENDING  
**Impact:** 🔴 HIGH - Makes debugging 50% faster

#### 2.1.1: Add Helpers to Entity Class
**File:** `entity.py`

```python
# Add to Entity class:

def require_component(self, component_type: ComponentType):
    """Get component or raise clear error.
    
    Use this when the component MUST exist.
    
    Args:
        component_type: The component to retrieve
        
    Returns:
        The component
        
    Raises:
        ComponentMissingError: If component doesn't exist
        
    Example:
        fighter = entity.require_component(ComponentType.FIGHTER)
        # If missing, raises: "Orc missing required FIGHTER component"
    """
    comp = self.components.get(component_type)
    if not comp:
        raise ComponentMissingError(
            f"{self.name} missing required {component_type.value} component"
        )
    return comp

def get_component_or_none(self, component_type: ComponentType):
    """Get component or None (for optional components).
    
    Use this when the component MIGHT NOT exist.
    
    Args:
        component_type: The component to retrieve
        
    Returns:
        The component, or None if not found
        
    Example:
        item_seeking = entity.get_component_or_none(ComponentType.ITEM_SEEKING_AI)
        if item_seeking:
            # Component exists, use it
```

#### 2.1.2: Add Custom Exception
**File:** `exceptions.py` (new file)

```python
class ComponentMissingError(Exception):
    """Raised when a required component is missing from an entity."""
    pass
```

#### 2.1.3: Add Tests
**File:** `tests/test_component_helpers.py`

```python
# Tests for:
- require_component returns when exists
- require_component raises ComponentMissingError when missing
- require_component error message is clear
- get_component_or_none returns when exists
- get_component_or_none returns None when missing
- Both methods work with different component types
```

**Acceptance Criteria:**
- ✅ Both helpers added to Entity class
- ✅ Custom exception created
- ✅ 6+ tests covering both methods
- ✅ 100% pass rate

---

### TASK 2.2: Add Deprecation Warning for Attribute Access
**Duration:** 0.5 days  
**Status:** PENDING  
**Impact:** 🟡 MEDIUM - Signals old pattern to developers

#### 2.2.1: Update Entity.__getattribute__
**File:** `entity.py`

```python
def __getattribute__(self, name):
    """Override to warn about deprecated component attribute access."""
    # List of component attribute names
    deprecated_attrs = {
        'fighter': ComponentType.FIGHTER,
        'inventory': ComponentType.INVENTORY,
        'ai': ComponentType.AI,
        'item': ComponentType.ITEM,
        'equipment': ComponentType.EQUIPMENT,
        # ... add others
    }
    
    if name in deprecated_attrs:
        import warnings
        warnings.warn(
            f"Accessing {name} via entity.{name} is deprecated. "
            f"Use entity.require_component(ComponentType.{deprecated_attrs[name].name}) "
            f"or entity.get_component_or_none(ComponentType.{deprecated_attrs[name].name})",
            DeprecationWarning,
            stacklevel=2
        )
    
    return super().__getattribute__(name)
```

**Acceptance Criteria:**
- ✅ Deprecation warnings show for attribute access
- ✅ Messages include how to fix
- ✅ Tests verify warnings are raised

---

### TASK 2.3: Refactor Priority Files
**Duration:** 2-3 days  
**Status:** PENDING  
**Impact:** 🔴 HIGH - Makes codebase consistent

#### Priority Order (by usage frequency):

**Tier 1 (Most Used - ~30% of codebase):**
1. `game_actions.py` (836 lines) - ~20 component accesses
2. `components/ai.py` (909 lines) - ~15 component accesses
3. `services/movement_service.py` (~400 lines) - ~10 accesses

**Tier 2 (Commonly Used - ~20%):**
4. `spells/spell_executor.py` (1466 lines) - ~15 accesses
5. `item_functions.py` (1323 lines) - ~10 accesses
6. `components/fighter.py` (1150 lines) - ~15 accesses

**Tier 3 (Regular Usage - ~50%):**
7-40. All other component-using files

#### Refactoring Pattern

**Before:**
```python
fighter = player.components.get(ComponentType.FIGHTER)
if fighter is None:
    return  # Silent failure!

inventory = player.inventory  # Might crash
```

**After:**
```python
fighter = player.require_component(ComponentType.FIGHTER)
# Now guaranteed to have fighter or get clear error

inventory = player.require_component(ComponentType.INVENTORY)
# Or use get_component_or_none for optional components
```

**Acceptance Criteria per File:**
- ✅ All component access uses helpers
- ✅ Tests pass for that system
- ✅ No regressions
- ✅ Committed with clear message

---

## 🎯 Success Criteria

### Technical
- ✅ All component access uses helpers (not direct `.get()` or attributes)
- ✅ No more silent failures (missing components raise clear errors)
- ✅ Deprecation warnings show on old pattern usage
- ✅ 2500+ tests pass (zero regressions)

### Developer Experience
- ✅ Error messages are clear and actionable
- ✅ Debugging time reduced (errors are immediate, not silent)
- ✅ IDE autocomplete works better (type hints on helpers)
- ✅ Onboarding clearer (one right way to access components)

---

## 📊 Expected Outcomes

### After Phase 2
- ✅ Component access is **consistent** across entire codebase
- ✅ Silent failures **impossible**
- ✅ Debugging time **50% faster** (errors are immediate)
- ✅ Code is **more readable** (explicit intent)
- ✅ IDE support **enhanced** (type checking)

### Metrics
- ~300 component access refactoring points
- ~40 files updated with helpers
- ~150 tests verifying new patterns
- Time to debug component issues: 30min → 5min

---

## 🔄 Workflow

1. Create helpers & tests (2.1)
2. Add deprecation warnings (2.2)
3. Refactor Tier 1 files (highest impact)
4. Refactor Tier 2 files
5. Refactor Tier 3 files (remaining)
6. Run full test suite
7. Verify no regressions
8. Document patterns in COMPONENT_TYPE_BEST_PRACTICES.md

---

## ⏱️ Timeline

**Day 1 (Today):**
- Create helpers & tests
- Add deprecation warnings
- Refactor Tier 1 (game_actions, ai, movement)

**Day 2:**
- Refactor Tier 2 (spell executor, items, fighter)
- Full test suite run

**Day 3:**
- Refactor Tier 3 (all other files)
- Final verification

**Day 4:**
- Documentation & polish
- Buffer for debugging

---

## 📝 Phase 2 Execution Log

### 2.1 Create Component Access Helpers
- [ ] Add `require_component()` to Entity
- [ ] Add `get_component_or_none()` to Entity
- [ ] Create `ComponentMissingError` exception
- [ ] Add tests for both helpers
- [ ] Verify 100% pass rate

### 2.2 Add Deprecation Warnings
- [ ] Update `Entity.__getattribute__`
- [ ] List all deprecated attributes
- [ ] Add tests for warnings
- [ ] Verify deprecation messages are clear

### 2.3 Refactor Files
- [ ] Tier 1: game_actions.py
- [ ] Tier 1: components/ai.py
- [ ] Tier 1: services/movement_service.py
- [ ] Tier 2: spells/spell_executor.py
- [ ] Tier 2: item_functions.py
- [ ] Tier 2: components/fighter.py
- [ ] Tier 3: All remaining files

### 2.4 Verification & Documentation
- [ ] Full test suite (2500+ tests)
- [ ] Zero regressions
- [ ] Update COMPONENT_TYPE_BEST_PRACTICES.md
- [ ] Document migration pattern

---

**Ready to execute Phase 2!**

