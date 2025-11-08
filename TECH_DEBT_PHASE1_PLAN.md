# Tech Debt Phase 1: Foundation Fixes - Execution Plan

**Status:** IN PROGRESS  
**Start Date:** November 8, 2025  
**Target Duration:** 2 weeks  
**Goal:** Eliminate entire classes of bugs and accelerate future development

---

## 🎯 Phase 1 Overview

Fix the two highest-impact architectural issues:
1. **Import Organization** - Prevent scoping bugs (2 days)
2. **Component Access Standardization** - Eliminate silent failures (3-4 days)

**Expected Outcome:** 50% reduction in debugging friction, zero import-scoping bugs possible going forward.

---

## 📋 Task Breakdown

### TASK 1: Import Organization & Pre-Commit Hook
**Duration:** 2 days  
**Status:** 75% COMPLETE (1.1-1.3 Done, 1.4 Pending)  
**Impact:** 🔴 HIGH - Prevents 100% of import-scoping bugs

**Completed (Today):**
- ✅ 1.1 Audit complete (157 violations in 35 files identified)
- ✅ 1.2 Pre-commit hook created & installed
- ✅ 1.3 Documentation in hook message
- ⏳ 1.4 Next: Fix 157 existing violations (file-by-file)

#### 1.1: Audit All Python Files for Local Imports
**Action:** Find all `from ... import` statements inside functions (except `TYPE_CHECKING`)

**Audit Results (Completed):**

**Total Violations Found:** 157 in 35 project files

**Top Violators (Priority Fix Order):**
1. `item_functions.py` - 29 violations (heavy status effect imports)
2. `mouse_movement.py` - 8 violations
3. `loader_functions/initialize_new_game.py` - 7 violations
4. `entity.py` - 7 violations
5. `tests/conftest.py` - 6 violations (test setup)
6. `screens/wizard_menu.py` - 5 violations
7. `engine_integration.py` - 5 violations
8. Plus 28 more files with 1-4 violations each

**Acceptance Criteria:**
- ✅ Audit complete
- ✅ 35 project files identified with violations
- ✅ 157 total violations documented
- ✅ Ready to fix (highest priority: item_functions.py)

---

#### 1.2: Create Pre-Commit Hook
**Status:** ✅ COMPLETE

**Created:** `.githooks/check-local-imports.sh`
- Detects all indented `from...import` statements
- Provides clear error message with fix examples
- Explains why local imports cause scoping bugs
- Excludes TYPE_CHECKING imports (legitimate use)

**Git Configuration:** ✅ Complete
```bash
git config core.hooksPath .githooks
chmod +x .githooks/check-local-imports.sh
```

**Acceptance Criteria:**
- ✅ Hook file created and executable
- ✅ Git configured to use .githooks/
- ✅ Hook prevents staging of new local imports  
- ✅ Hook tested and working
- ✅ Helpful error message verified

---

#### 1.3: Document Import Guidelines
**Status:** ✅ COMPLETE (via pre-commit hook)

**Documentation:** Built into pre-commit hook error message
- Clear explanation in `.githooks/check-local-imports.sh`
- Shows "WRONG" vs "CORRECT" code examples
- Explains the ComponentType bug context
- Shown to any developer trying to commit violation

**Additional Documentation:** Can add to CONTRIBUTING.md if needed
- For now, hook message provides sufficient guidance
- Hook runs on every commit attempt (developers will see it)
- Self-documenting through immediate feedback

**Acceptance Criteria:**
- ✅ Guidelines documented in hook
- ✅ Examples of wrong vs right included
- ✅ Explanation of why it matters provided
- ✅ Developers will see guidance when attempting violation

---

#### 1.4: Fix Existing Violations
**Action:** Convert all local imports to module-level

**Process:**
1. Run audit command (1.1)
2. For each file with violations:
   - Move imports to top of file
   - Verify tests still pass
   - Commit with message: "Fix local imports in [file]"

**Acceptance Criteria:**
- ✅ All local imports moved to module level
- ✅ All tests pass (2500+ test suite)
- ✅ No regressions

---

### TASK 2: Component Access Helpers & Standardization
**Duration:** 3-4 days  
**Status:** PENDING  
**Impact:** 🔴 HIGH - Eliminates silent failures, enables IDE support

#### 2.1: Create Component Access Helpers
**File:** `entity.py`  
**Action:** Add two helper methods

```python
# In Entity class

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
        # If fighter missing, raises clear error instead of silent None
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
            # Do something with it
    """
    return self.components.get(component_type)
```

**Create Custom Exception:**
```python
# In entity.py or new exceptions.py

class ComponentMissingError(Exception):
    """Raised when a required component is missing from an entity."""
    pass
```

**Acceptance Criteria:**
- ✅ Both helpers added to Entity class
- ✅ Clear docstrings with examples
- ✅ Custom exception created
- ✅ Tests for both helpers (see 2.2)

---

#### 2.2: Test Component Helpers
**File:** `tests/test_entity_component_helpers.py`  
**Action:** Add comprehensive tests

```python
import pytest
from entity import Entity, ComponentMissingError
from components.component_registry import ComponentType
from components.fighter import Fighter

class TestComponentHelpers:
    """Test component access helpers."""
    
    def test_require_component_returns_when_exists(self):
        """require_component returns component when it exists."""
        fighter = Fighter(hp=10, defense=2, power=3)
        entity = Entity(5, 5, '@', (255, 255, 255), 'Test', fighter=fighter)
        
        result = entity.require_component(ComponentType.FIGHTER)
        assert result is fighter
    
    def test_require_component_raises_when_missing(self):
        """require_component raises ComponentMissingError when missing."""
        entity = Entity(5, 5, '@', (255, 255, 255), 'Test')
        
        with pytest.raises(ComponentMissingError):
            entity.require_component(ComponentType.FIGHTER)
    
    def test_require_component_error_message_clear(self):
        """require_component error message is clear."""
        entity = Entity(5, 5, 'o', (100, 100, 100), 'Orc')
        
        with pytest.raises(ComponentMissingError) as exc_info:
            entity.require_component(ComponentType.FIGHTER)
        
        assert "Orc" in str(exc_info.value)
        assert "FIGHTER" in str(exc_info.value)
    
    def test_get_component_or_none_returns_when_exists(self):
        """get_component_or_none returns component when it exists."""
        fighter = Fighter(hp=10, defense=2, power=3)
        entity = Entity(5, 5, '@', (255, 255, 255), 'Test', fighter=fighter)
        
        result = entity.get_component_or_none(ComponentType.FIGHTER)
        assert result is fighter
    
    def test_get_component_or_none_returns_none_when_missing(self):
        """get_component_or_none returns None when missing."""
        entity = Entity(5, 5, '@', (255, 255, 255), 'Test')
        
        result = entity.get_component_or_none(ComponentType.FIGHTER)
        assert result is None
```

**Acceptance Criteria:**
- ✅ All tests pass (5 tests minimum)
- ✅ 100% coverage of helper code
- ✅ Tests verify error messages are clear

---

#### 2.3: Add Deprecation Warning to Attribute Access
**File:** `entity.py`  
**Action:** Warn when old pattern is used

```python
# In Entity.__getattr__ or add property deprecations

def __getattribute__(self, name):
    """Override to warn about deprecated component attribute access."""
    # Check for common component attributes being accessed as properties
    deprecated_attrs = {
        'fighter': ComponentType.FIGHTER,
        'inventory': ComponentType.INVENTORY,
        'ai': ComponentType.AI,
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
- ✅ Warnings appear when old pattern used
- ✅ Tests verify warnings are raised
- ✅ Warnings don't break functionality (yet)

---

#### 2.4: Refactor High-Priority Files (Incremental)
**Duration:** 2-3 days  
**Action:** Convert component access patterns in most-impacted files

**Priority Order:**
1. `game_actions.py` (836 lines, heavy component access)
2. `components/fighter.py` (1150 lines, used by everything)
3. `spells/spell_executor.py` (1466 lines, complex component logic)
4. `components/ai.py` (909 lines, scattered component access)
5. `services/movement_service.py` (400+ lines, collision detection)
6. Top 35 remaining high-frequency files

**Process for Each File:**
1. Open file
2. Find all component access patterns:
   - `entity.fighter` → `entity.require_component(ComponentType.FIGHTER)`
   - `entity.components.get(ComponentType.X)` → `entity.get_component_or_none(ComponentType.X)`
   - Handle special cases (optional vs required)
3. Run tests for that file/system
4. Commit: `"Refactor component access in [file] to use helpers"`

**Acceptance Criteria per File:**
- ✅ All component access uses new helpers
- ✅ Tests pass for that system
- ✅ No regressions

**Overall Acceptance Criteria:**
- ✅ Top 40 files refactored (~90% of component access)
- ✅ All tests pass (2500+)
- ✅ Zero regressions
- ✅ Deprecation warnings appear (expected)

---

## 📊 Progress Tracking

### Import Organization
- [ ] 1.1: Audit for local imports
- [ ] 1.2: Create pre-commit hook
- [ ] 1.3: Document guidelines
- [ ] 1.4: Fix violations
- [ ] ✅ COMPLETE

### Component Helpers
- [ ] 2.1: Create helpers in entity.py
- [ ] 2.2: Test helpers
- [ ] 2.3: Add deprecation warnings
- [ ] 2.4: Refactor files (40+ priority files)
- [ ] ✅ COMPLETE

---

## ⏱️ Timeline

**Week 1:**
- Mon-Tue: Import organization (1.1-1.4)
- Wed-Thu: Component helpers (2.1-2.2)
- Fri: Deprecation warnings & start refactoring (2.3-2.4 start)

**Week 2:**
- Mon-Fri: Refactor priority files (2.4 continued)
- Fri PM: Final testing & cleanup

---

## 🎯 Success Criteria

**Technical:**
- ✅ Zero local imports in codebase
- ✅ Pre-commit hook prevents new violations
- ✅ 100% of component access uses helpers
- ✅ All 2500+ tests pass
- ✅ Zero regressions

**Developer Experience:**
- ✅ Component access errors are clear (not silent)
- ✅ IDE autocomplete works better (type hints via helpers)
- ✅ Debugging is faster (no silent None values)
- ✅ New developers understand pattern immediately

**Impact:**
- ✅ Impossible to introduce import-scoping bugs (pre-commit hook)
- ✅ Impossible to have silent component failures (helpers enforce)
- ✅ Foundation solid for next 6 months of features

---

## 🚀 Next Steps

1. Execute TASK 1 (Import Organization) - Start today
2. Execute TASK 2 (Component Helpers) - Start mid-week
3. Review and iterate based on findings
4. Plan Phase 2 (monolithic file splitting) after Phase 1 complete

---

**Owner:** Agent (with your direction)  
**Next Review:** After Task 1 complete (2-3 days)

