# Monolithic File Refactoring - Break Up God Files

**Status:** Planning  
**Scope:** Split 2 large files into 13 smaller, focused modules  
**Total Lines:** 3,339 lines (game_actions: 2037, ai: 1302)  
**Estimated Time:** 5-7 hours  
**Risk Level:** MEDIUM (large refactoring, many dependencies)  

---

## Executive Summary

Two files contain ~45% of the codebase's logic and handle multiple responsibilities:

- **game_actions.py** (2,037 lines): Action dispatch, item handling, combat, equipment, pathfinding, turn transitions
- **components/ai.py** (1,302 lines): Basic AI, slime AI, item seeking, combat logic, pathfinding, taunt behavior, faction logic

**Problem:** Difficult to debug, hard to test, high merge conflict risk, cognitive overload.

**Solution:** Split into focused modules with single responsibilities.

---

## Game Actions Refactoring (2,037 lines → 6 modules)

### Current Structure
```
game_actions.py (2,037 lines)
├─ ActionProcessor.__init__() - Setup
├─ process_actions() - Main dispatch
├─ Item actions (_handle_pickup, _handle_inventory_action, etc.)
├─ Combat actions (_handle_attack)
├─ Equipment actions (_handle_equip, _handle_unequip)
├─ Movement actions (_handle_movement, pathfinding)
├─ Turn transitions (_handle_wait, _handle_stairs, _handle_level_up)
└─ Deprecated inventory methods
```

### Target Structure
```
game_actions/
├─ __init__.py (30 lines)
│  ├─ __all__ = ['ActionProcessor']
│  └─ Imports & re-exports
│
├─ action_processor.py (250 lines)
│  ├─ ActionProcessor.__init__()
│  ├─ process_actions()
│  ├─ _route_action()
│  └─ Handler registration
│
├─ item_actions.py (150 lines)
│  ├─ _handle_pickup()
│  ├─ _handle_inventory_action()
│  ├─ _handle_throw_action()
│  └─ Helper methods
│
├─ combat_actions.py (100 lines)
│  ├─ _handle_attack()
│  └─ Combat helpers
│
├─ equipment_actions.py (100 lines)
│  ├─ _handle_equip()
│  ├─ _handle_unequip()
│  └─ Equipment helpers
│
├─ movement_actions.py (250 lines)
│  ├─ _handle_movement()
│  ├─ _handle_start_auto_explore()
│  ├─ Pathfinding logic
│  └─ Movement helpers
│
└─ turn_actions.py (100 lines)
   ├─ _handle_wait()
   ├─ _handle_stairs()
   ├─ _handle_level_up()
   └─ Turn transition helpers
```

### Refactoring Strategy

**Step 1: Create Directory & __init__.py**
```bash
mkdir -p game_actions/
touch game_actions/__init__.py
```

**Step 2: Extract Each Module**
- Copy relevant methods to new file
- Keep imports minimal
- Share common utilities

**Step 3: Update game_actions/__init__.py**
```python
from .action_processor import ActionProcessor
__all__ = ['ActionProcessor']
```

**Step 4: Update Imports Everywhere**
```python
# Before
from game_actions import ActionProcessor

# After (same import works due to __init__.py)
from game_actions import ActionProcessor
```

**Step 5: Verify Tests Pass**
- All 955 tests should still pass
- No import errors
- No functional changes

### Files to Update
- `engine_integration.py` - Creates ActionProcessor
- `game_engine.py` - Uses ActionProcessor
- Tests importing ActionProcessor

---

## Components/AI Refactoring (1,302 lines → 7 modules)

### Current Structure
```
components/ai.py (1,302 lines)
├─ find_taunted_target() - Helper
├─ BaseAI (50 lines)
├─ BasicMonster (250 lines)
│  ├─ Initiative calculation
│  ├─ Target selection
│  ├─ Action determination
│  └─ Combat logic
├─ SlimeAI (150 lines)
├─ ConfusedMonster (50 lines)
├─ MindlessZombieAI (80 lines)
├─ Item seeking logic (200 lines)
├─ Item usage (200 lines)
├─ Equipment handling (150 lines)
├─ Faction logic (150 lines)
└─ Taunt behavior (100 lines)
```

### Target Structure
```
components/ai/
├─ __init__.py (40 lines)
│  ├─ __all__ = ['BaseAI', 'BasicMonster', ...]
│  └─ Imports & re-exports
│
├─ base_ai.py (50 lines)
│  ├─ BaseAI class
│  └─ Base methods
│
├─ basic_monster.py (250 lines)
│  ├─ BasicMonster class
│  ├─ take_turn()
│  ├─ Initiative calculation
│  ├─ Target selection
│  └─ Action determination
│
├─ slime_ai.py (150 lines)
│  ├─ SlimeAI class
│  └─ Slime-specific behavior
│
├─ confused_monster.py (50 lines)
│  ├─ ConfusedMonster class
│  └─ Confusion behavior
│
├─ mindless_zombie.py (80 lines)
│  ├─ MindlessZombieAI class
│  └─ Mindless behavior
│
├─ ai_actions.py (200 lines)
│  ├─ Shared action methods
│  ├─ Item seeking
│  ├─ Item usage helpers
│  └─ Combat helpers
│
├─ ai_targeting.py (150 lines)
│  ├─ Target selection logic
│  ├─ Initiative calculations
│  └─ Priority helpers
│
├─ ai_faction.py (150 lines)
│  ├─ Faction logic
│  ├─ Taunt handling
│  └─ Relationship checks
│
└─ ai_logger.py (100 lines)
   ├─ Monster action logging
   ├─ Debug formatting
   └─ Test mode helpers
```

### Refactoring Strategy

**Step 1: Create Directory & __init__.py**
```bash
mkdir -p components/ai/
touch components/ai/__init__.py
```

**Step 2: Extract Each Module**
- Copy relevant classes to new files
- Keep imports minimal
- Share common utilities via ai_actions.py

**Step 3: Update components/ai/__init__.py**
```python
from .base_ai import BaseAI
from .basic_monster import BasicMonster
from .slime_ai import SlimeAI
from .confused_monster import ConfusedMonster
from .mindless_zombie import MindlessZombieAI

__all__ = ['BaseAI', 'BasicMonster', 'SlimeAI', 'ConfusedMonster', 'MindlessZombieAI']
```

**Step 4: Update Imports Everywhere**
```python
# Before
from components.ai import BasicMonster

# After (same import works due to __init__.py)
from components.ai import BasicMonster
```

**Step 5: Verify Tests Pass**
- All 955 tests should still pass
- No import errors
- No functional changes

### Files to Update
- `config/entity_factory.py` - Creates AI entities
- `engine/systems/ai_system.py` - Uses AI classes
- Tests importing from components.ai

---

## Implementation Plan

### Phase A: Preparation (30 min)
1. ✅ Create detailed refactoring plan (this document)
2. Create git branch for tracking
3. Back up current files
4. List all import points

### Phase B: Game Actions Refactoring (2 hours)
1. Create `game_actions/` directory
2. Extract each module sequentially
3. Update imports in all files
4. Run tests after each module
5. Fix any import issues immediately

### Phase C: Components/AI Refactoring (2 hours)
1. Create `components/ai/` directory
2. Extract each module sequentially
3. Update imports in all files
4. Run tests after each module
5. Fix any import issues immediately

### Phase D: Verification (1 hour)
1. Run full test suite (955 tests)
2. Check for any runtime issues
3. Verify import behavior
4. Clean up any lingering issues

### Phase E: Documentation (30 min)
1. Update docstrings in new modules
2. Create module interaction diagram
3. Update README if needed
4. Mark old files as deprecated

---

## Risk Mitigation

### High-Risk Areas
1. **Circular imports** - Use TYPE_CHECKING for type hints
2. **Missing imports** - Test each module separately
3. **Behavior changes** - Run full test suite after each change
4. **Import path changes** - Use __init__.py re-exports for backward compatibility

### Testing Strategy
```bash
# After each module extraction:
pytest tests/ -x  # Stop on first failure

# Full verification:
pytest tests/ -v --tb=short  # Verbose with short tracebacks
```

### Rollback Plan
- Git allows easy rollback if something breaks
- Keep original files in git history
- Test frequently to catch issues early

---

## Benefits

### Short Term
✅ Clearer code organization
✅ Easier to find code
✅ Reduced cognitive load
✅ Fewer merge conflicts

### Medium Term
✅ Easier to add new AI types
✅ Easier to test components independently
✅ Better for team collaboration
✅ Reduced debugging time

### Long Term
✅ Scalable architecture
✅ Easier onboarding for new developers
✅ Foundation for more complex features
✅ Better code reusability

---

## Success Criteria

- ✅ All 955 tests passing
- ✅ No import errors
- ✅ No behavioral changes
- ✅ No performance degradation
- ✅ Code is easier to understand
- ✅ Module responsibilities are clear

---

## Timeline

**Total: ~5-7 hours**

| Phase | Time | Activity |
|-------|------|----------|
| A | 30 min | Preparation |
| B | 2 hours | game_actions.py refactoring |
| C | 2 hours | components/ai.py refactoring |
| D | 1 hour | Full verification |
| E | 30 min | Documentation |

Ready to proceed? (Y/N)

