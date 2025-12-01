# Manual Test: Keyboard Double-Move Bug

## Current Status

**Instrumentation Added**: Comprehensive logging has been added to trace the keyboard input path.

## How to Reproduce and Diagnose

1. **Start the game in manual mode**:
   ```bash
   cd /Users/rafehatfield/development/rlike
   python3 engine.py
   ```

2. **Start a new game** and move to an open area

3. **Tap ONE arrow key ONCE** (e.g., RIGHT arrow)
   - Make sure it's a clean tap (no holding, no OS key repeat)
   - Observe: Does the player move 1 tile or 2 tiles?

4. **Check the debug.log file** for the sequence of events:
   ```bash
   tail -100 debug.log | grep -E "\[PUMP_EVENTS\]|\[NEXT_ACTION|\[KEYBOARD INPUT\]|\[PROCESSING ACTION\]|\[ENGINE UPDATE|\[PLAYER_MOVE\]"
   ```

## What to Look For in Logs

For a SINGLE keypress, you should see:

```
[PUMP_EVENTS] key changed: before=(X, Y) -> after=(39, 0)    # RIGHT arrow key filled
[NEXT_ACTION START] key=(39, 0), pumped_externally=True
[NEXT_ACTION] Using externally pumped events
[NEXT_ACTION] Processing key: vk=39, c=0
[NEXT_ACTION] Key produced actions: {'move': (1, 0)}
[NEXT_ACTION] Cleared key after processing
[NEXT_ACTION END] returning actions={'move': (1, 0)}
[KEYBOARD INPUT] turn=N, action={'move': (1, 0)}
[PROCESSING ACTION] turn=N, action={'move': (1, 0)}, mouse={}
[ENGINE UPDATE START] turn=N, updating systems
[PLAYER_MOVE] SUCCESS: moved from (X, Y) to (X+1, Y) via keyboard
[ENGINE UPDATE END] turn changed: N -> N+1
```

### If There's a Double-Move Bug, You Might See:

**Scenario A: Two ENGINE_UPDATE calls per keypress**
```
[KEYBOARD INPUT] turn=N, action={'move': (1, 0)}
[ENGINE UPDATE START] turn=N, ...
[PLAYER_MOVE] ...
[ENGINE UPDATE END] turn changed: N -> N+1
[ENGINE UPDATE START] turn=N+1, ...    # ❌ Second update!
[PLAYER_MOVE] ...                       # ❌ Second move!
```

**Scenario B: Same key processed twice**
```
[NEXT_ACTION] Key produced actions: {'move': (1, 0)}
[NEXT_ACTION] Cleared key after processing
...
[PUMP_EVENTS] key changed: ... -> after=(39, 0)    # ❌ Key refilled!
[NEXT_ACTION START] key=(39, 0), ...                # ❌ Same key again!
```

**Scenario C: Two separate calls to process_actions or _handle_movement**
```
[PROCESSING ACTION] turn=N, action={'move': (1, 0)}, ...
[PLAYER_MOVE] SUCCESS: moved from (5, 5) to (6, 5) ...
[PROCESSING ACTION] turn=N, action={'move': (1, 0)}, ...    # ❌ Called again!
[PLAYER_MOVE] SUCCESS: moved from (6, 5) to (7, 5) ...      # ❌ Second move!
```

## Next Steps Based on Findings

### If Scenario A (Double engine.update):
- Look for multiple paths calling `engine.update()` in the main loop
- Check if systems are calling update recursively

### If Scenario B (Key refilled):
- Issue is in `pump_events_and_sleep` or libtcod event queue
- SDL might be queuing multiple events for one keypress

### If Scenario C (Double process_actions):
- Look for multiple calls to `action_processor.process_actions()` per frame
- Check if AutoExplore or pathfinding is triggering extra movement

### If NONE of these (Movement looks correct in logs):
- The "double move" might actually be something else (e.g., camera scroll, rendering issue)
- Or the turn counter is incrementing twice but movement only happens once

## Expected Behavior

- **One keypress** →
- **One `[NEXT_ACTION]` sequence** →
- **One `[PROCESSING ACTION]`** →
- **One `[ENGINE UPDATE]`** →
- **One `[PLAYER_MOVE]`** →
- **One turn increment**

If you see ANY of these happen twice for a single keypress, that's the bug!





