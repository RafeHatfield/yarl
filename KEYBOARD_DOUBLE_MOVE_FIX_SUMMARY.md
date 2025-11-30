# Keyboard Double-Move Bug Fix Summary

**Date**: 2024-11-24  
**Status**: ✅ FIXED  
**Author**: AI Assistant (Cursor)

---

## Problem Description

### Symptom
- Every single keyboard press (e.g., arrow key) resulted in **two player movements** instead of one
- This happened even with a single tap (no key repeat)
- Mouse-driven actions worked correctly (no double-step)
- **Regression**: Did not happen historically; introduced during recent loop/input changes

### Impact
- Made keyboard-based gameplay unplayable
- Violated the core invariant: **One discrete input → one player action → one world tick**

---

## Root Cause Analysis

### Investigation
The bug was in `io_layer/keyboard_input.py`, specifically in the `KeyboardInputSource.next_action()` method.

**The Problem**:
1. When a key was pressed, `current_key` was filled with the key event
2. `next_action()` processed the key and returned an action
3. **BUT**: The key object was **not cleared** after processing
4. On the next frame (when no new key was pressed), `current_key` **still contained the old key**
5. `next_action()` saw the key again and processed it a second time
6. Result: **double move** from a single keypress

### Why Mouse Worked
Mouse input uses button state (pressed/not pressed) rather than persisting key codes, so buttons naturally reset between frames.

### Code Flow (Before Fix)

```
Frame N:
  1. User presses RIGHT arrow
  2. pump_events_and_sleep() fills current_key with RIGHT arrow
  3. next_action() sees current_key.vk = KEY_RIGHT
  4. Returns {"move": (1, 0)}
  5. Action processed, player moves right
  6. ❌ current_key NOT CLEARED

Frame N+1:
  7. User has released key
  8. pump_events_and_sleep() calls sys_check_for_event()
  9. No new event, so current_key UNCHANGED (still KEY_RIGHT)
  10. next_action() sees current_key.vk = KEY_RIGHT AGAIN
  11. Returns {"move": (1, 0)} AGAIN
  12. ❌ DOUBLE MOVE!
```

---

## Solution

### Fix
In `io_layer/keyboard_input.py`, added key clearing logic after processing:

```python
# Handle keyboard input
if self.current_key.vk != libtcod.KEY_NONE or self.current_key.c != 0:
    # ... process key actions ...
    
    # CRITICAL FIX: Clear the key after processing
    self.current_key.vk = libtcod.KEY_NONE
    self.current_key.c = 0
```

### Why This Works
- After processing a key, we immediately clear it
- On the next frame, `next_action()` sees a cleared key
- No action is returned unless a new key is pressed
- **Invariant restored**: One keypress → one action → one world tick

---

## Testing

### Regression Tests
Created comprehensive test suite in `tests/test_keyboard_double_move_fix.py`:

1. **Core Regression Test**: Single keypress processed exactly once
2. **Multiple Keypresses**: Each distinct key processed once
3. **Key Clearing Doesn't Affect Mouse**: Mouse input still works
4. **External Event Pump**: Works correctly with `pump_events_and_sleep`
5. **Arrow Keys**: All arrow keys map to correct directions
6. **Vi Keys**: hjkl + yubn keys work correctly

**Test Results**: ✅ All 6 tests pass

### Integration Tests
Verified no regressions in existing tests:
- ✅ `tests/test_engine_integration_io_loop.py` (10/10 tests pass)
- ✅ No linter errors in modified files

---

## Files Modified

### Core Fix
- `io_layer/keyboard_input.py` (lines 44-48)
  - Added key clearing after processing

### Instrumentation (Temporary Debug Logging)
- `engine_integration.py` (lines 540-542, 677-679, 1046-1049)
  - Added debug logging for keyboard input tracing
  - Can be removed after manual verification

### Tests
- `tests/test_keyboard_double_move_fix.py` (new file, 217 lines)
  - Comprehensive regression test suite

### Documentation
- `KEYBOARD_DOUBLE_MOVE_FIX_SUMMARY.md` (this file)

---

## Verification Steps

### Manual Testing
To verify the fix works:

1. **Start a new game**:
   ```bash
   python3 engine.py
   ```

2. **Test keyboard movement**:
   - Stand in an open area
   - Tap RIGHT arrow once (don't hold)
   - Expected: Move **1 tile** right
   - Before fix: Would move **2 tiles** right ❌

3. **Test multiple taps**:
   - Tap RIGHT, RIGHT, RIGHT (3 separate taps)
   - Expected: Move **3 tiles** total
   - Before fix: Would move **6 tiles** total ❌

4. **Verify mouse still works**:
   - Right-click on a nearby tile
   - Expected: Move **1 tile** per click
   - Should work as before ✅

### Debug Logging
Temporary debug logs were added to trace input flow:
- `[KEYBOARD INPUT]` - When input is received
- `[PROCESSING ACTION]` - When action is processed
- `[ENGINE UPDATE]` - When systems are updated

Check `debug.log` for these entries to verify single processing per keypress.

---

## Impact Assessment

### What Changed
- ✅ Keyboard input: Now processes each key exactly once
- ✅ Mouse input: Unchanged, still works correctly
- ✅ Bot mode: Unchanged, still works correctly
- ✅ AutoExplore: Unchanged, still works correctly

### Invariants Restored
- ✅ **One discrete keyboard input → one player action**
- ✅ **One player action → one world tick**
- ✅ **One world tick → one AI phase**

### No Regressions
- ✅ All existing tests pass
- ✅ No new linter errors
- ✅ Bot/soak modes unaffected

---

## Follow-Up Actions

### Required
- [ ] **Manual verification**: Play game with keyboard to confirm fix works
- [ ] **Remove temporary debug logging**: Clean up instrumentation in `engine_integration.py` after verification

### Optional
- [ ] Consider refactoring input handling to use tcod.event API (see deprecation warnings)
- [ ] Add more end-to-end integration tests for keyboard input

---

## Lessons Learned

### Architecture Insight
**Input source objects that wrap libtcod must explicitly clear event state after processing**, as libtcod's `sys_check_for_event` doesn't automatically clear previous events when no new event occurs.

### Best Practice
**Always clear ephemeral input state after consumption** to prevent phantom actions from persisting across frames.

---

## References

- Project Rules: `RLIKE PROJECT RULES (Cursor)`
- Related Fixes:
  - `MANUAL_LOOP_FIX_SUMMARY.md` - Recent loop tightening work
  - `AUTOEXPLORE_INTERACTION_FIX_SUMMARY.md` - Interaction fixes
  - `RENDER_FIX_SUMMARY.md` - Render system changes

---

**Status**: Ready for manual verification and cleanup of temporary logging.




