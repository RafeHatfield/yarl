# Bot Mode Console Log Suppression

**Date:** 2025-11-15  
**Status:** ✅ COMPLETE  
**Branch:** codex/fix-bot-mode-to-prevent-unresponsiveness

## Problem

When running the game in bot mode (`python3 engine.py --bot`), the console was flooded with per-frame debug messages:

```
>>> KEYBOARD ACTION RECEIVED: {'wait': True}
>>> Calling handler for wait
>>> KEYBOARD ACTION RECEIVED: {'wait': True}
>>> Calling handler for wait
...
```

These messages were printed continuously (many times per second) during bot mode soak testing, making it difficult to see actual errors or important logs. In normal keyboard mode, these debug messages are useful for understanding player actions, but in bot mode they create console spam.

## Solution

Introduced a minimal `is_bot_mode` flag to `ActionProcessor` to suppress per-frame debug logs during bot mode, while preserving them in normal keyboard mode.

### Implementation Details

**1. Added `is_bot_mode` parameter to ActionProcessor**

File: `game_actions.py`

- Added optional `is_bot_mode` parameter to `__init__()` (defaults to `False` for backward compatibility)
- Stored flag as instance variable: `self.is_bot_mode`

```python
def __init__(self, state_manager, is_bot_mode=False):
    """Initialize the ActionProcessor.
    
    Args:
        state_manager: Game state manager instance
        is_bot_mode: If True, suppress per-frame debug logs (for bot mode soak testing)
    """
    self.state_manager = state_manager
    self.turn_manager = None
    self.is_bot_mode = is_bot_mode  # Suppress spammy logs in bot mode
    # ... rest of init
```

**2. Gated debug print statements with bot mode check**

File: `game_actions.py`, lines 176-191

- Wrapped three print statements in `if not self.is_bot_mode:` guards:
  - "KEYBOARD ACTION RECEIVED:" (line 179)
  - "Calling handler for {action_type}" (line 185)
  - "No handler for action {action_type}" (line 191)

```python
# Process keyboard actions
if action:
    if not self.is_bot_mode:
        print(f">>> KEYBOARD ACTION RECEIVED: {action}")

for action_type, value in action.items():
    if value is not None and action_type in self.action_handlers:
        try:
            if not self.is_bot_mode:
                print(f">>> Calling handler for {action_type}")
            self.action_handlers[action_type](value)
        # ... error handling
    else:
        if not self.is_bot_mode:
            print(f">>> No handler for action {action_type}")
```

**3. Passed bot mode flag from engine_integration.py**

File: `engine_integration.py`

- Detected bot mode early (line 285) by checking `constants.get("input_config", {}).get("bot_enabled")`
- Passed `is_bot_mode=(input_mode == "bot")` when creating ActionProcessor (line 289)
- Removed duplicate `input_mode` detection that was later in the file (line 313)

```python
# Detect bot mode early (before creating ActionProcessor)
input_mode = "bot" if constants.get("input_config", {}).get("bot_enabled") else "keyboard"

# Create action processor for clean action handling
# Pass is_bot_mode to suppress spammy per-frame logs during soak testing
action_processor = ActionProcessor(engine.state_manager, is_bot_mode=(input_mode == "bot"))
```

## Files Changed

1. **game_actions.py** (3 changes)
   - Modified `ActionProcessor.__init__()` to accept `is_bot_mode` parameter
   - Added `self.is_bot_mode` instance variable
   - Gated 3 print statements with `if not self.is_bot_mode:` checks

2. **engine_integration.py** (2 changes)
   - Moved `input_mode` detection earlier (before ActionProcessor creation)
   - Passed `is_bot_mode` parameter when instantiating ActionProcessor

3. **tests/test_bot_mode_log_suppression.py** (NEW)
   - Added comprehensive test suite (5 tests) verifying log suppression works correctly
   - Tests verify normal mode still prints logs, bot mode suppresses them
   - Tests verify backward compatibility (defaults to False)
   - Tests verify bot mode still processes actions correctly (just doesn't log them)

## Behavior Changes

### Before (Bot Mode)
```
>>> KEYBOARD ACTION RECEIVED: {'wait': True}
>>> Calling handler for wait
>>> KEYBOARD ACTION RECEIVED: {'wait': True}
>>> Calling handler for wait
>>> KEYBOARD ACTION RECEIVED: {'wait': True}
>>> Calling handler for wait
... (hundreds of lines per second)
```

### After (Bot Mode)
```
(console is clean - no per-frame action logs)
```

### Normal Keyboard Mode
**No change** - debug logs still print as before for debugging player actions.

## Testing

All existing tests pass:
- ✅ 41 bot mode tests pass (`tests/test_bot_mode*.py`)
- ✅ 16 general action processing tests pass
- ✅ 5 new log suppression tests added and passing

New test coverage:
- `test_normal_mode_prints_action_logs` - Verifies normal mode still logs actions
- `test_bot_mode_suppresses_action_logs` - Verifies bot mode suppresses logs
- `test_bot_mode_flag_defaults_to_false` - Verifies backward compatibility
- `test_bot_mode_still_processes_actions_correctly` - Verifies actions still work
- `test_multiple_actions_in_bot_mode_no_spam` - Verifies no spam after 100 iterations

## Design Decisions

**Why not use logging.DEBUG?**
- The existing codebase uses `print()` statements for these debug messages
- Converting to proper logging would be a larger refactor (outside scope of this task)
- The simple flag-based approach is minimal, clear, and consistent with task requirements

**Why add a flag instead of detecting bot mode dynamically?**
- ActionProcessor doesn't have direct access to the engine or input_source
- A flag passed at construction time is simpler than threading dependencies
- Backward compatible (defaults to False for existing test code)
- Clear intent: "this instance should suppress debug logs"

**Why gate at the ActionProcessor level?**
- The spammy logs originate from `game_actions.py` in the action processing flow
- This is the correct architectural layer to suppress input-related debug logs
- Other ActionProcessor instances (e.g., in AISystem for enemy actions) are unaffected

## Architectural Compliance

✅ **No changes to:**
- Main loop structure
- AISystem logic
- TurnManager behavior
- State machine transitions
- Input handling flow (BotInputSource unchanged)
- Rendering pipeline

✅ **Follows project rules:**
- Small, focused change (logging only)
- No new patterns or abstractions (simple boolean flag)
- Backward compatible (defaults to False)
- Well tested (5 new tests, all existing tests pass)
- No refactoring of unrelated code

## Follow-up (Optional, Future Work)

If desired, the project could later:
- Convert all `print()` debug statements to proper `logging.debug()` calls
- Use a centralized logging configuration to control debug output
- Remove the `is_bot_mode` flag in favor of log level configuration

However, for Phase 0 bot mode stability/soak testing, the current flag-based approach is sufficient and maintains simplicity.

## Verification

To verify the fix works:

**Normal mode (should still print logs):**
```bash
python3 engine.py
# Press 's' to wait
# Console should print: ">>> KEYBOARD ACTION RECEIVED: {'wait': True}"
```

**Bot mode (should NOT print per-frame logs):**
```bash
python3 engine.py --bot
# Console should be clean (no "KEYBOARD ACTION RECEIVED" spam)
# Bot runs indefinitely for soak testing without console noise
```

## Summary

**What changed:**
- ActionProcessor now accepts optional `is_bot_mode` parameter
- Three debug print statements are now gated by `if not self.is_bot_mode:`
- engine_integration.py passes `is_bot_mode=True` when in bot mode

**Impact:**
- Bot mode console output is now clean (no per-frame spam)
- Normal keyboard mode behavior is unchanged
- All tests pass (41 bot mode tests + 16 general tests + 5 new tests)

**Trade-offs:**
- Adds one new parameter to ActionProcessor (minimal API change)
- Backward compatible (defaults to False)
- Simple, focused solution (no large refactors)

