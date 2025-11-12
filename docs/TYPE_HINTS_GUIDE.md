# Type Hints Implementation Guide

**Date:** November 9, 2025  
**Status:** Phase 6 - Type Hints & Interfaces (IN PROGRESS)  
**Impact:** IDE autocompletion, type checking, documentation through types

---

## Overview

This guide documents how to add comprehensive type hints to Yarl's codebase using Python's `typing` module and Protocols.

## Key Principles

1. **Non-Breaking**: Type hints are advisory; they don't change runtime behavior
2. **Forward References**: Use `'Entity'` for forward references to avoid circular imports
3. **TYPE_CHECKING Blocks**: Use for imports only needed during type checking
4. **Optional Usage**: Use `Optional[T]` for nullable types, not just `T | None`
5. **List/Dict Consistency**: Use `List[T]` and `Dict[K, V]` from `typing`, not built-ins

---

## Files Completed ✅

### 1. `components/interfaces.py` (NEW)
- **Status**: ✅ COMPLETE
- **Impact**: Core Protocols for all components and services
- **What**: Defines AIProtocol, ComponentProtocol, ServiceProtocol, etc.

### 2. `entity.py`
- **Status**: ✅ COMPLETE  
- **Changes**:
  - Added `Dict` to imports
  - Typed all factory methods (`create_player`, `create_monster`, `create_item`)
  - Typed status effect management methods
- **Return Types Added**:
  ```python
  def create_player(...) -> 'Entity'
  def add_status_effect(self, effect: Any) -> List[Dict[str, Any]]
  def process_status_effects_turn_start(self) -> List[Dict[str, Any]]
  ```

### 3. `components/fighter.py`
- **Status**: ✅ COMPLETE
- **Changes**:
  - Added `Optional, Dict, Any, List` to imports
  - Typed helper functions and critical combat methods
- **Return Types Added**:
  ```python
  def take_damage(self, amount: int, damage_type: Optional[str] = None) -> List[Dict[str, Any]]
  def heal(self, amount: int) -> None
  def attack(self, target: Any) -> List[Dict[str, Any]]
  ```

---

## Pattern Template

For any Python function/method:

```python
# BAD - No type hints
def take_action(entity, target):
    """Do something."""
    return results

# GOOD - Full type hints
from typing import List, Dict, Any, Optional

def take_action(entity: 'Entity', target: Optional['Entity'] = None) -> List[Dict[str, Any]]:
    """Do something.
    
    Args:
        entity: The acting entity
        target: Optional target entity
        
    Returns:
        List of result dictionaries
    """
    return results
```

## Most Common Type Signatures

### Return Types
- `-> None` - No return value
- `-> bool` - Returns True/False
- `-> int` - Returns integer
- `-> str` - Returns string
- `-> 'Entity'` - Returns Entity (forward reference)
- `-> List[Dict[str, Any]]` - Returns list of result dictionaries (VERY COMMON in game code)

### Parameter Types
- `: int` - Integer parameter
- `: str` - String parameter
- `: 'Entity'` - Entity parameter (forward reference)
- `: List['Entity']` - List of entities
- `: Optional[str] = None` - Optional string with default
- `: Any` - Any type (use sparingly, when type is truly unknown)

### Forward References for Circular Imports
```python
# At top of file in TYPE_CHECKING block:
if TYPE_CHECKING:
    from entity import Entity
    from components.fighter import Fighter

# In function signature:
def method(self, entity: 'Entity') -> Optional['Fighter']:
    ...
```

---

## Priority Order for Remaining Files

### HIGH PRIORITY (Most used, biggest impact)
1. `services/movement_service.py` - Game loop critical
2. `game_actions.py` - Main dispatcher
3. `services/portal_manager.py` - Portal system
4. `components/inventory.py` - Item management

### MEDIUM PRIORITY (Visible but less critical)
5. `components/ai/basic_monster.py` - Most common AI
6. `components/ai/boss_ai.py` - Boss behavior
7. `config/factories/__init__.py` - Entity creation

### LOWER PRIORITY (Nice to have)
8. `spells/spell_executor.py` - Spell system
9. `components/equipment.py` - Equipment slots
10. Other component files

---

## Implementation Strategy

For each file:
1. Add `from typing import ...` with needed types (List, Dict, Any, Optional, etc.)
2. Add TYPE_CHECKING block for forward references
3. Add return types to **public methods** (don't need private helper types)
4. Add parameter types to **key public methods**
5. Verify compilation: `python3 -c "import module; print('OK')"`

---

## Testing Type Coverage

Run:
```bash
# Check if module imports
python3 -c "from components.fighter import Fighter; print('✅')"

# Run type checker (requires mypy/pyright)
mypy components/fighter.py --no-error-summary 2>&1 | grep -c "error:"
```

---

## Benefits Achieved

✅ **IDE Autocompletion**: IDEs can now autocomplete method names and parameters  
✅ **Type Checking**: Tools like mypy can catch type errors before runtime  
✅ **Documentation**: Types serve as inline documentation for methods  
✅ **Refactoring Safety**: Easier to rename/restructure with type awareness  
✅ **Developer Onboarding**: New developers understand what types methods expect/return  

---

## Next Steps

- [ ] Complete HIGH PRIORITY files (4 files × 20 min = 80 min)
- [ ] Spot-check MEDIUM PRIORITY (sample 2-3 files)
- [ ] Document as PHASE 6 COMPLETE
- [ ] Use as blueprint for future PRs

---

**Session Time Estimate**: 2-3 hours for comprehensive coverage of top 8 files  
**ROI**: Massive - Type hints save 10+ hours in debugging over next 6 months

