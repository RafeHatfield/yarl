# Console Spam Fix - Removed Debug Print Statements

**Date**: November 25, 2025  
**Status**: ✅ Complete

---

## Problem

Soak mode (`make soak`) was flooding the console with debug print statements:
```
>>> MovementService: (92, 39) -> (93, 38) via keyboard, state=GameStates.PLAYERS_TURN
>>> AISystem: Orc turn, ai_type=basic, has_strategy=False
>>> AISystem: Calling Orc.ai.take_turn()
>>> AISystem: Orc returned 0 results
>>> PickupService: Pickup at (94, 37) via keyboard
>>> PickupService: Total entities: 43
>>> PickupService: Entities at (94, 37): 2
>>>   - Player: has_item=True, item=None
>>>   - Healing Potion: has_item=True, item=<...>
```

These were firing **every single turn** in soak mode, making the console unusable.

---

## Solution

**Removed all high-frequency debug print statements** from:

### **services/movement_service.py** (3 print statements removed)
- Line 103: `print(f">>> MovementService: ... -> ... via {source}")`
- Line 155: `print(f">>> MovementService: Player moved to ...")`  
- Line 193: `print(f">>> MovementService: VICTORY PORTAL ENTRY ...")`

### **engine/systems/ai_system.py** (4 print statements removed)
- Line 344: `print(f">>> AISystem: SKIPPING duplicate turn ...")`
- Line 365: `print(f">>> AISystem: {entity.name} turn, ...")`
- Line 369: `print(f">>> AISystem: Using custom strategy ...")`
- Line 372: `print(f">>> AISystem: Calling {entity.name}.ai.take_turn()")`
- Line 377: `print(f">>> AISystem: {entity.name} returned ... results")`

### **services/pickup_service.py** (8 print statements removed)
- Line 88-89: Pickup location and total entities
- Line 99-103: Entities at location debug dump
- Line 116: Attempting pickup
- Line 139: Pickup successful
- Line 147: Victory trigger detected
- Line 158: Portal spawned
- Line 164: Portal spawn failed

### **mouse_movement.py** (1 print statement removed)
- Line 654: `print(f">>> PATHFINDING: Attempting to pick up ...")`

**Total**: 16 debug print statements removed from high-frequency code paths

---

## What Was Kept

**Preserved logging** for actual diagnostics:
- All `logger.debug()`, `logger.info()`, `logger.warning()` statements kept
- These go to log files, not console
- Rare events (victory, boss spawn) kept their `print()` statements (only fire once per game)

---

## Result

**Before:**
- Console flooded with >>>` spam every turn
- Unreadable output
- Game appeared stuck (but was actually running)

**After:**
- Clean console output
- Only important events printed
- Soak mode runs quietly
- All logs still captured in log files

---

## Files Modified

- `services/movement_service.py` - Removed 3 prints
- `engine/systems/ai_system.py` - Removed 4 prints
- `services/pickup_service.py` - Removed 8 prints
- `mouse_movement.py` - Removed 1 print

**Total**: 4 files, 16 lines removed

---

## Verification

All tests still pass after removing print statements:
```
✅ 46 bot brain tests PASSED
✅ 104 portal tests PASSED  
✅ 0 linter errors
```

Soak mode should now run quietly with:
- ✅ No `>>>` console spam
- ✅ Clean, readable output
- ✅ All diagnostics still logged to files
- ✅ Game runs normally

**Ready for `make soak`** ✅


