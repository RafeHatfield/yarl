# Manual Play Loop Fix - Summary

## Problem

Manual play was experiencing severe degradation where:
- **Symptom**: For each keyboard move, the AI system was being called MANY times
- **Player Experience**: Game felt "wrong and fragile", with repeated enemy AI processing per player action
- **Root Cause**: `engine.update()` was being called EVERY frame regardless of player input, violating the core invariant

## Core Invariant (Manual Mode)

```
One player input (or one AutoExplore step) → One world tick → One AI phase → Return to waiting for input
```

This invariant was being violated because:
1. `should_update_systems = True` was hardcoded (line 669 in `engine_integration.py`)
2. Even when `input_source.next_action()` returned `{}` (no input), `engine.update()` was still called
3. This caused state transition loops and repeated AI processing

## Solution

### Code Changes

**File**: `engine_integration.py`

**Lines 666-707**: Added conditional `should_update_systems` logic:

```python
# Manual Mode (input_mode != "bot"):
#   Only update when:
#     - Player performed an action (action or mouse_action not empty), OR
#     - AutoExplore is actively running
#
# Bot Mode (input_mode == "bot"):
#   Always update (bot continuously generates actions)

should_update_systems = True  # Default: update for bot mode

if input_mode != "bot":
    # MANUAL MODE: Only update if there's an action OR auto-explore is active
    has_action = bool(action or mouse_action)
    
    # Check if AutoExplore is active
    player = engine.state_manager.state.player
    auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE) if player else None
    auto_explore_active = bool(auto_explore and auto_explore.is_active())
    
    # CRITICAL INVARIANT: Only update if player acted or auto-explore is running
    if not has_action and not auto_explore_active:
        should_update_systems = False
```

**Key Points**:
- Manual mode: `engine.update()` only called when player acts or AutoExplore is active
- Bot mode: Unchanged - always updates every frame
- AutoExplore: Continues to update while active, stops cleanly when inactive

### Imports Added

Added missing import:
```python
from components.component_registry import ComponentType
```

## Tests Added

**File**: `tests/test_engine_integration_io_loop.py`

Added `TestManualPlayLoopInvariants` class with 4 unit tests:

1. **`test_should_update_logic_no_action_no_auto_explore`**
   - Verifies `should_update_systems = False` when no action and no AutoExplore
   - Core fix for "AI spam" bug

2. **`test_should_update_logic_has_action`**
   - Verifies `should_update_systems = True` when player acts

3. **`test_should_update_logic_auto_explore_active`**
   - Verifies `should_update_systems = True` when AutoExplore is active

4. **`test_should_update_logic_bot_mode_always_updates`**
   - Verifies bot mode always updates (unchanged behavior)

**All tests pass** ✅

## Verification

### Tests Run

1. ✅ Manual play loop invariant tests (4/4 passed)
2. ✅ Bot mode turn transition tests (4/4 passed)
3. ✅ AI system tests (38/38 passed)
4. ✅ Bot smoke test (2 runs, 0 crashes)

### Manual Testing Recommended

Before considering this complete, please manually test:

1. **Manual Play**:
   - Start game in manual mode
   - Press a movement key (arrow or vi-keys)
   - Verify: Each keypress results in exactly ONE set of enemy turns
   - Verify: No AI spam in logs

2. **Manual + AutoExplore**:
   - Press `o` to start AutoExplore
   - Let it run until it stops (hint sign, unreachable areas, etc.)
   - Verify: AutoExplore works normally
   - After it stops, press a movement key
   - Verify: Manual control resumes normally, no AI spam

3. **Bot Mode**:
   - Run: `python3 engine.py --bot`
   - Verify: Bot plays normally, no crashes

4. **Bot Soak Mode**:
   - Run: `python3 engine.py --bot-soak --runs 10 --max-turns 500 --max-floors 3`
   - Verify: All runs complete, no crashes

## Impact Analysis

### Unchanged Behavior
- ✅ Bot mode (`--bot` and `--bot-soak`): Always updates every frame
- ✅ AutoExplore: Continues to work as before
- ✅ State transitions: No changes to turn controller or AI system

### Fixed Behavior
- ✅ Manual play: No longer calls `engine.update()` every frame when idle
- ✅ Manual play: Exactly one AI phase per player action
- ✅ Manual play: Game feels responsive and correct

### Side Effects
- 🔍 **Diagnostic logging added** (lines 695-707): Temporary DEBUG logs to trace frame behavior
- 📝 **Can be removed** after verification period if desired

## Historical Context

This fix restores the behavior from **before the bot work**. During bot stabilization:
- The "only update on action" logic was disabled (see comment at line 671-675)
- This was meant as a temporary measure
- It inadvertently broke manual play

The fix implements the same logic but **correctly**, ensuring:
- Manual play works as intended
- Bot/soak modes remain stable
- AutoExplore transitions cleanly

## Next Steps

1. **Manual testing** by the user (see "Manual Testing Recommended" above)
2. **Monitor logs** for any unexpected behavior
3. **Remove diagnostic logging** (lines 695-707) after verification period
4. **Close related issues** if any exist in the tracker

---

**Date**: 2025-11-24  
**Files Modified**:
- `engine_integration.py` (lines 44, 666-707)
- `tests/test_engine_integration_io_loop.py` (added 4 tests)

**Tests Added**: 4  
**Tests Passing**: All (46+ tests run, 0 failures)  
**Bot Smoke Test**: ✅ Pass (2/2 runs completed)





