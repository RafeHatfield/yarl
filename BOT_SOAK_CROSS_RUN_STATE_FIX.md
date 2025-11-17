# Bot Soak Cross-Run State Leakage Fix

**Date:** 2025-11-17  
**Status:** ✅ Complete  
**Branch:** `phase-1.6-bot-soak-harness`

---

## Problem Summary

After implementing Phase 1.6 (bot soak harness), the following bug was discovered:

- **Bot Run 1/10**: Works perfectly - bot explores the floor, detects completion, exits cleanly
- **Bot Run 2/10 and beyond**: Bot gets stuck in a tight loop attempting moves that never succeed

**Symptoms in Run 2+:**
```
>>> MovementService: (111, 58) -> (111, 56) via keyboard, state=GameStates.PLAYERS_TURN
>>> MovementService: (111, 58) -> (111, 55) via keyboard, state=GameStates.PLAYERS_TURN
>>> MovementService: (111, 58) -> (111, 54) via keyboard, state=GameStates.PLAYERS_TURN
...
(no "Player moved to ..." lines - movements are failing validation)
```

The bot would repeatedly attempt moves from the same tile, with no actual movement occurring, causing the run to hang indefinitely.

---

## Root Cause Analysis

### The Issue

**Singleton services** (particularly `MovementService` and `PickupService`) were NOT being reset between bot soak runs. These services hold references to the `state_manager` from run 1, and when run 2 starts with a fresh game and fresh `state_manager`, the singletons are still pointing to the old one.

### How This Caused the Bug

1. **Run 1:** Creates game → state_manager₁ → MovementService singleton (with state_manager₁) → success
2. **Run 2:** Creates NEW game → state_manager₂ → but MovementService singleton STILL has state_manager₁
3. **Movement validation:** Bot tries to move in run 2, but MovementService validates against run 1's stale map
4. **Result:** All movements fail validation (tiles appear "blocked" from old map), bot gets stuck in loop

### Code Location of the Bug

**`services/movement_service.py` (lines 524-541):**
```python
# Singleton instance
_movement_service = None

def get_movement_service(state_manager=None):
    global _movement_service
    if _movement_service is None:
        if state_manager is None:
            raise ValueError("state_manager required to initialize MovementService")
        _movement_service = MovementService(state_manager)
    return _movement_service
```

The singleton is created once and never reset between runs, carrying stale state_manager references across runs.

---

## Solution

### Core Fix

Add explicit singleton service resets in the bot soak harness **before each run starts**:

**`engine/soak_harness.py` (lines 294-317):**
```python
try:
    # Reset global singletons for clean run
    # CRITICAL: These must be reset before each run to prevent state leakage
    reset_run_metrics_recorder()
    reset_telemetry_service()
    
    # Reset movement service (holds reference to state_manager)
    # Without this, run 2+ will use run 1's stale state_manager for movement
    # validation, causing all moves to fail against the wrong map
    from services.movement_service import reset_movement_service
    reset_movement_service()
    
    # Reset pickup service (also holds state_manager reference)
    from services.pickup_service import reset_pickup_service
    reset_pickup_service()
    
    # Reset floor state manager (tracks cross-floor state)
    from services.floor_state_manager import reset_floor_state_manager
    reset_floor_state_manager()
    
    # ... continue with run setup
```

### Supporting Changes

1. **Added `reset_pickup_service()` function** (`services/pickup_service.py` lines 196-203):
   ```python
   def reset_pickup_service() -> None:
       """Reset the global pickup service instance.
       
       This should be called between bot soak runs to ensure each run gets a fresh
       service instance with the correct state_manager reference.
       """
       global _pickup_service
       _pickup_service = None
   ```

2. **Added comprehensive documentation** explaining singleton reset requirements in `run_bot_soak()` docstring (lines 235-254)

3. **Added test coverage** (`tests/test_bot_soak.py` lines 481-595):
   - `test_run_bot_soak_resets_singleton_services_between_runs()`
   - Verifies all singleton services are reset before each run
   - Confirms no cross-run state leakage

---

## Files Modified

### Core Fixes
- `engine/soak_harness.py`: Added singleton service resets (lines 301-317)
- `services/pickup_service.py`: Added reset_pickup_service() function (lines 196-203)

### Documentation
- `engine/soak_harness.py`: Added SINGLETON SERVICE RESET REQUIREMENTS section to docstring (lines 235-254)

### Tests
- `tests/test_bot_soak.py`: Added test_run_bot_soak_resets_singleton_services_between_runs() (lines 481-595)

---

## Verification

### Test Results

**Unit tests:**
```bash
$ python3 -m pytest tests/test_bot_soak.py -v
============================= test session starts ==============================
...
tests/test_bot_soak.py::TestRunBotSoakIntegration::test_run_bot_soak_resets_singleton_services_between_runs PASSED [100%]
...
=============================== 9 passed, 1 warning in 0.06s =========================
```

**Integration test (3 runs):**
```bash
$ python3 engine.py --bot-soak --runs 3
🧪 Bot Soak Session Summary
   Runs: 3
   Completed: 3
   Crashes: 0
   
Run  Outcome       Duration   Floor   Kills  
1     bot_completed 30.3s      1       0       
2     bot_completed 27.6s      1       0       ✅ FIXED - was failing before!
3     bot_completed 36.2s      1       0       
```

**Full soak test (10 runs):**
```bash
$ python3 engine.py --bot-soak --runs 10
🧪 Bot Soak Session Summary
   Runs: 10
   Completed: 10  ✅ All runs completed successfully
   Crashes: 0     ✅ No crashes or hangs
```

### Behavior Verification

- ✅ **Run 1:** Works perfectly (always did)
- ✅ **Run 2:** Now works perfectly (was stuck in movement loop before fix)
- ✅ **Runs 3-10:** All complete successfully (all were failing before)
- ✅ **No crashes:** Crashes: 0 across all runs
- ✅ **Normal mode:** `python3 engine.py` - still works
- ✅ **Bot mode:** `python3 engine.py --bot` - still works

---

## Lessons Learned

### Singleton Pattern Pitfall

**The Problem:**
Singleton services are convenient for avoiding parameter passing, but they can cause **subtle state leakage bugs** in scenarios where the "world" is recreated (like bot soak runs, tests, or game restarts).

**The Solution:**
- Every singleton that holds game object references MUST have a `reset_*()` function
- Every scenario that creates a fresh game world MUST call these reset functions
- Document this requirement prominently so future engineers know to add resets for new singletons

### Cross-Run Testing is Critical

This bug only manifested in **run 2** of a multi-run sequence. Single-run tests would never have caught it. This highlights the importance of:
- Testing sequences of operations, not just isolated single runs
- Verifying that "fresh start" scenarios truly start fresh
- Checking for unexpected shared state between test runs

---

## Future Work / Recommendations

1. **Audit remaining singletons:** Check if other singleton services need reset functions:
   - `PortalManager` (probably stateless, but verify)
   - `MuralManager` (static content, likely OK)
   - `EncounterBudgetEngine` (per-floor state, might need reset)
   - Others in `services/` directory

2. **Consider dependency injection:** For critical services like MovementService, consider passing state_manager explicitly rather than storing it as an instance variable. This prevents stale reference bugs entirely.

3. **Add integration test:** Create a full end-to-end bot soak test that verifies multiple runs complete without hangs (currently mocked).

---

## Related Documentation

- `BOT_MODE_PHASE1_AUTO_EXPLORE.md` - Phase 1 bot implementation
- `BOT_MODE_AI_LOOP_FIX.md` - Earlier bot mode fix
- `BOT_SOAK_LIBTCOD_FIX.md` - Libtcod initialization fix for bot soak
- `engine/soak_harness.py` - Bot soak harness implementation

---

## Conclusion

The cross-run state leakage bug was caused by singleton services holding stale references to `state_manager` from previous runs. The fix ensures all singleton services are properly reset before each bot soak run, allowing run 2+ to work correctly.

**Status:** ✅ Complete - All 10 runs now complete successfully with no crashes or hangs.

