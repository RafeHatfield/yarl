# Phase 1.6 - Bot Soak Run Completion Fix

## Problem

In bot soak mode (`python3 engine.py --bot-soak`), when the bot finished exploring a floor:
1. AutoExplore component would refuse to start again (correct behavior)
2. BotInputSource would keep trying to start it anyway (infinite attempts)
3. Result: Infinite idle loop, run never completes, soak harness hangs on run 1

This prevented the soak harness from running multiple sequential bot games (N=2,3,... runs).

## Solution

Implemented a clean terminal condition for bot runs in soak mode:

### 1. **BotInputSource Detection** (`io_layer/bot_input.py`)

**New State Tracking:**
- `_fully_explored_detected`: Flags when "All areas explored" stop reason is detected
- `_failed_explore_attempts`: Counts attempts to restart autoexplore on fully explored floors

**Logic:**
```
Frame N: AutoExplore is active → return {}

Frame N+1: AutoExplore stops with "All areas explored"
         → Set _fully_explored_detected = True

Frames N+2..N+4: Each frame with _fully_explored_detected:
                → Check if _failed_explore_attempts >= 3
                → If yes: return {'bot_abort_run': True}
                → If no: increment counter, try to restart

Result: After 3 failed restart attempts, emit bot_abort_run signal
```

**Key:** Tracks stop reason to distinguish between:
- "All areas explored" → run terminal condition
- "Monster spotted", "Found chest", etc. → try again normally

### 2. **ActionProcessor Handler** (`game_actions.py`)

**New handler:** `_handle_bot_abort_run()`
- Sets marker: `engine.state_manager.set_extra_data("bot_abort_run", True)`
- Logs reason
- Adds message to message log (for --bot single mode visibility)

**Registration:** Added to `action_handlers` dict for `'bot_abort_run'` action key

### 3. **Engine Integration** (`engine_integration.py`)

**In play_game_with_engine() main loop:**
- Detect `bot_abort_run` marker after action processor runs
- Finalize run metrics with outcome = `"bot_completed"`
- End telemetry for current floor
- Return `{"bot_completed": True}` to exit game loop cleanly

### 4. **Soak Harness** (`engine/soak_harness.py`)

**Per-run:**
- Reset bot input source state at start of each run via `reset_bot_run_state()`
- Capture `"bot_completed"` outcome from `play_game_with_engine()` return dict
- Record in run metrics

**Session Summary:**
- Count `"bot_completed"` runs as valid completions (not crashes)
- Display in per-run breakdown table
- Include in session summary statistics

### 5. **Tests**

**Updated:** `tests/test_bot_mode_phase1_auto_explore.py`
- Fixed mock setup to include `stop_reason` attribute

**Added:** `tests/test_bot_soak_completion.py`
- Test bot_abort_run signal after 3 failed restarts on fully explored floor
- Test reset_bot_run_state() clears tracking state
- Test bot doesn't abort for other stop reasons (monster, etc.)
- Test ActionProcessor handler sets correct marker

## Behavior Changes

### Normal Gameplay (`python3 engine.py`)
**No change.** Humans still play normally. Autoexplore still works as before.

### Single Bot Mode (`python3 engine.py --bot`)
**Before:** Infinite idle loop after full exploration (hangs forever)
**After:** Bot completes cleanly after 3 failed restart attempts, exits gracefully
- Message shown: "🤖 Floor fully explored. Bot run complete."
- No crash, just quiet exit

### Bot Soak Mode (`python3 engine.py --bot-soak`)
**Before:** Run 1 hangs forever, never reaches run 2..N
**After:** 
- Run 1 completes with outcome `"bot_completed"`
- Soak harness proceeds to run 2, run 3, etc.
- Session summary shows:
  ```
  Runs: N
  Completed: N (includes bot_completed outcomes)
  Crashes: 0
  ```

## Implementation Details

### State Reset Between Runs
- Each new soak run resets: `_failed_explore_attempts`, `_last_auto_explore_active`, `_auto_explore_started`, `_fully_explored_detected`
- Prevents contamination from previous runs

### Outcome Flow
```
BotInputSource emits {'bot_abort_run': True}
    ↓
ActionProcessor._handle_bot_abort_run()
    ↓
Sets state marker: engine.state_manager.set_extra_data("bot_abort_run", True)
    ↓
play_game_with_engine() detects marker
    ↓
Finalizes metrics with outcome="bot_completed"
    ↓
Returns {"bot_completed": True}
    ↓
Soak harness records outcome, proceeds to next run
```

### Why 3 Attempts?
- Arbitrary threshold to filter noise (e.g., one-off timing issues)
- Balances responsiveness (not too quick) with termination (not infinite)
- Easily tunable if needed (lines 132-137 in bot_input.py)

## Design Decisions

1. **Option A chosen: BotInputSource-driven**
   - Simpler than Option B (AutoExplore component changes)
   - Keeps bot logic centralized in input layer
   - Minimal diff to existing code

2. **Explicit "bot_completed" outcome**
   - Not using death/victory/quit states
   - Clear intent: "bot finished exploring"
   - Easy to track and report separately

3. **No effect on normal gameplay**
   - All changes are bot-specific
   - Human players unaffected
   - Autoexplore for humans works exactly as before

## Testing

✅ All existing bot tests pass (14 tests)
✅ All soak tests pass (8 tests)
✅ New completion tests pass (4 tests)
✅ No linter errors
✅ Proper logging for debugging

## Manual Verification Checklist

- [ ] `python3 engine.py` – normal play works
- [ ] `python3 engine.py --bot` – bot explores, completes cleanly after full exploration
- [ ] `python3 engine.py --bot-soak 3` – runs 3 bot games sequentially, all complete with appropriate outcomes
- [ ] Session summary shows realistic statistics
- [ ] No crashes or hangs

## Future Work

None needed for this phase. The terminal condition properly separates:
- **Phase 1.6 (now):** Bot soak runs complete cleanly without enemy AI
- **Later phases:** Can re-enable enemy AI when ready

