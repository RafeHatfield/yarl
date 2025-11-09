# Phase 2.3: Component Access Refactoring
## Standardizing ~300 Component Access Points

**Status:** IN PROGRESS  
**Start:** November 8, 2025  
**Goal:** Refactor all component access to use standardized helpers

---

## Overview

Entity class provides two helpers:
```python
def require_component(self, component_type: ComponentType):
    """Guaranteed component access - raises ValueError if missing"""
    
def get_component_optional(self, component_type: ComponentType):
    """Optional component access - returns None if missing"""
```

Task: Replace ~300 scattered access patterns with these helpers across 40+ files.

---

## Refactoring Strategy

### Pattern 1: Direct Attribute Access → require_component()

**Before:**
```python
fighter = player.fighter
if not fighter:
    return
```

**After:**
```python
fighter = player.require_component(ComponentType.FIGHTER)
# No need to check - guaranteed or raises ValueError
```

### Pattern 2: Silent .get() → require_component() or get_component_optional()

**Before:**
```python
fighter = entity.components.get(ComponentType.FIGHTER)
if fighter is None:
    return  # Silent failure
```

**After:**
```python
# If fighter is required:
fighter = entity.require_component(ComponentType.FIGHTER)

# If fighter is optional:
fighter = entity.get_component_optional(ComponentType.FIGHTER)
if fighter:
    # Do something
```

---

## Tier 1: High-Impact Files (Go First)

### 1. game_actions.py
- ~20 component accesses
- Lines: 836
- Priority: HIGH (main game loop)
- **Status:** ⏳ PENDING

### 2. components/ai.py
- ~35 component accesses
- Lines: 909
- Priority: HIGH (monster AI)
- **Status:** ⏳ PENDING

### 3. services/movement_service.py
- ~10 component accesses
- Lines: ~400
- Priority: HIGH (critical path)
- **Status:** ⏳ PENDING

---

## Tier 2: Moderate-Impact Files

### 4. spells/spell_executor.py (1466 lines)
### 5. item_functions.py (1323 lines)
### 6. components/fighter.py (1150 lines)

---

## Tier 3: All Remaining Files

All other component-using files systematically refactored.

---

## Execution Workflow

For each file:

1. **Audit:** Find all component accesses
2. **Map:** Decide require_component() vs get_component_optional()
3. **Refactor:** Apply transformation
4. **Test:** Verify all tests pass
5. **Commit:** Clear commit message with file + count

---

## Currently Using Helpers

These files already use the patterns well:
- game_actions.py: 8 instances of get_component_optional()
- components/ai.py: 19 instances of get_component_optional()

Extend this pattern to ALL accesses.

---

## Refactoring Checklist Template

```
File: [filename]
Accesses Found: [count]

Status: ✅ COMPLETE

Refactorings Applied:
- [ ] require_component() replacements: [count]
- [ ] get_component_optional() replacements: [count]
- [ ] All tests passing
- [ ] Zero regressions
```

---

**Ready to execute!**

