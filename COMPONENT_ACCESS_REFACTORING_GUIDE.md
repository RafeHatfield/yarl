# Component Access Refactoring Guide
## Safe Patterns for Phase 2.3 Execution

**Date:** November 8, 2025  
**Purpose:** Enable consistent, safe component access refactoring across 40+ files  
**Scope:** ~300 component access points

---

## Quick Reference

### When to Use Each Helper

```python
# REQUIRED Component (will always exist)
# Use: require_component()
fighter = entity.require_component(ComponentType.FIGHTER)
# Guarantees: fighter is not None, or ValueError raised
# NO null check needed

# OPTIONAL Component (might not exist)
# Use: get_component_optional()
equipment = entity.get_component_optional(ComponentType.EQUIPMENT)
if equipment:
    # Only here if equipment exists
    pass
```

---

## Refactoring Patterns

### Pattern 1: Replace Direct Attribute Access

**BEFORE:**
```python
if not entity.fighter:
    return

power = entity.fighter.power
```

**AFTER:**
```python
fighter = entity.require_component(ComponentType.FIGHTER)
power = fighter.power
```

---

### Pattern 2: Replace Silent .get() Failures

**BEFORE:**
```python
fighter = entity.components.get(ComponentType.FIGHTER)
if not fighter:
    return  # Silent failure - hard to debug

attack_results = fighter.attack(target)
```

**AFTER:**
```python
fighter = entity.require_component(ComponentType.FIGHTER)
attack_results = fighter.attack(target)
# Clear error if missing - easier to debug
```

---

### Pattern 3: Replace Optional Component Checks

**BEFORE:**
```python
item = entity.components.get(ComponentType.ITEM)
if item:
    name = item.get_display_name()
```

**AFTER:**
```python
item = entity.get_component_optional(ComponentType.ITEM)
if item:
    name = item.get_display_name()
```

---

### Pattern 4: Avoid Double-Checking

**ANTI-PATTERN (Don't do this):**
```python
fighter = entity.require_component(ComponentType.FIGHTER)
if not fighter:  # Don't! require_component guarantees non-None
    return
```

**CORRECT:**
```python
fighter = entity.require_component(ComponentType.FIGHTER)
# fighter is guaranteed non-None, use directly
```

---

### Pattern 5: Inline Optional Checks

**BEFORE:**
```python
equipment = entity.components.get(ComponentType.EQUIPMENT)
if equipment:
    slot = equipment.get_equipped_slot()
```

**AFTER:**
```python
equipment = entity.get_component_optional(ComponentType.EQUIPMENT)
if equipment:
    slot = equipment.get_equipped_slot()
```

---

## Common Refactoring Mistakes

### ❌ WRONG: Using require_component() for optional things

```python
# BAD - equipment is optional, not always present
equipment = entity.require_component(ComponentType.EQUIPMENT)
# This will crash if entity has no equipment!
```

### ✅ CORRECT: Use get_component_optional() for optional things

```python
# GOOD - handles missing gracefully
equipment = entity.get_component_optional(ComponentType.EQUIPMENT)
if equipment:
    # Use it if it exists
```

---

### ❌ WRONG: Still checking None after require_component()

```python
fighter = entity.require_component(ComponentType.FIGHTER)
if fighter is None:  # IMPOSSIBLE! require_component guarantees non-None
    return
```

### ✅ CORRECT: Trust the guarantee

```python
fighter = entity.require_component(ComponentType.FIGHTER)
# fighter is GUARANTEED non-None
power = fighter.power  # Safe!
```

---

### ❌ WRONG: Mixing patterns inconsistently

```python
# Inconsistent - why sometimes .fighter and sometimes get_component_optional()?
fighter = player.fighter
equipment = player.get_component_optional(ComponentType.EQUIPMENT)
```

### ✅ CORRECT: Use helpers consistently

```python
# Consistent - all use helpers
fighter = player.require_component(ComponentType.FIGHTER)
equipment = player.get_component_optional(ComponentType.EQUIPMENT)
```

---

## How to Refactor a File

### Step 1: Audit
```bash
# Find all component accesses
grep -n "\.fighter\|\.ai\|\.inventory\|\.item\|\.equipment" filename.py | head -20
```

### Step 2: Categorize
For each access, decide:
- Is this component always required? → `require_component()`
- Is this component optional? → `get_component_optional()`

### Step 3: Refactor
Replace systematically, testing after each major change.

### Step 4: Test
```bash
python3 -m pytest tests/ -k "your_component_name" -v
```

### Step 5: Full Test
```bash
python3 -m pytest tests/ --tb=short
```

### Step 6: Commit
Create atomic commits per file with clear messages.

---

## File-by-File Guide

### Tier 1: High-Impact (Do First)

#### 1. game_actions.py
**Status:** STARTED (fighter + partial inventory)  
**Components Used:**
- `fighter` - REQUIRED for combat actions
- `inventory` - REQUIRED for item management
- `item` - REQUIRED for item interaction
- `auto_explore` - OPTIONAL

**Pattern:**
```python
# For combat
fighter = entity.require_component(ComponentType.FIGHTER)

# For inventory
inventory = entity.require_component(ComponentType.INVENTORY)

# For optionals
auto_explore = entity.get_component_optional(ComponentType.AUTO_EXPLORE)
```

#### 2. components/ai.py
**Status:** PENDING  
**Components Used:**
- `fighter` - REQUIRED for combat
- `ai` - REQUIRED for AI decisions
- `inventory` - OPTIONAL (only some monsters have it)

**Challenge:** Has many complex AI behaviors - refactor carefully with tests

#### 3. services/movement_service.py
**Status:** PENDING  
**Components Used:**
- `fighter` - For collision/blocking
- `ai` - For monster movement

---

### Tier 2: Moderate-Impact

#### 4. spells/spell_executor.py
- Multiple component accesses for spell effects

#### 5. item_functions.py  
- Item use functions access various components

#### 6. components/fighter.py
- Fighter component accessing other components

---

### Tier 3: Systematic Cleanup

All remaining files with component access.

---

## Safety Guarantees

### Pre-Commit Hook Protection
- ✅ No new local imports can be added
- ✅ Prevents entire class of scoping bugs
- ✅ Component access now standardized

### Test Coverage
- ✅ 14 tests verify both helpers work
- ✅ 2500+ tests catch regressions
- ✅ Run full suite after each file

### Rollback Safety
- ✅ Atomic commits per file
- ✅ Easy to revert individual files
- ✅ Git history shows every change

---

## Checklist per File

Use this template when refactoring each file:

```
File: [filename.py]
Lines: [X]
Components Found: fighter=[], inventory=[], ai=[], etc.

Refactoring Checklist:
- [ ] Audit: Found all component accesses
- [ ] Map: Decided require_component vs get_component_optional
- [ ] Refactor: Applied all transformations
- [ ] Test: Local tests pass (if applicable)
- [ ] Full Test: python3 -m pytest tests/ passes
- [ ] Commit: Committed with clear message

Result: ✅ COMPLETE / ⚠️ ISSUES / ❌ BLOCKED
Notes: [Any issues encountered]
```

---

## Anti-Patterns to Avoid

### ❌ Don't mix old and new patterns
```python
# BAD
if entity.fighter and hasattr(entity, 'ai'):
    # Mixed patterns!
```

### ✅ Use helpers consistently
```python
# GOOD
fighter = entity.get_component_optional(ComponentType.FIGHTER)
ai = entity.get_component_optional(ComponentType.AI)
if fighter and ai:
    # Both checked consistently
```

---

### ❌ Don't access before checking
```python
# BAD
result = entity.fighter.attack()  # Crashes if no fighter!
```

### ✅ Check with helper first
```python
# GOOD
fighter = entity.get_component_optional(ComponentType.FIGHTER)
if fighter:
    result = fighter.attack()
```

---

## Expected Outcomes

After refactoring all files:
- ✅ ~300 component accesses standardized
- ✅ 40+ files using consistent patterns
- ✅ Silent failures → clear errors
- ✅ Debugging time reduced 50%
- ✅ Codebase health significantly improved

---

## Questions?

Refer to:
- `entity.py` - See the actual helper implementations
- `tests/test_component_helpers.py` - See usage examples
- `TECH_DEBT_ANALYSIS_2025.md` - Context and rationale

---

**Ready to refactor!**

