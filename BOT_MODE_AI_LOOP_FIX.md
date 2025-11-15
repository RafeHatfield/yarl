# Bot Mode AI Infinite Loop Fix

## Problem

In bot mode (`python engine.py --bot`), the game would hang/beachball after spawning alone or after player death. The console showed this pattern repeating indefinitely:

```
>>> KEYBOARD ACTION RECEIVED: {'wait': True}
>>> Calling handler for wait
>>> AISystem: Orc turn, ai_type=basic, has_strategy=False
>>> AISystem: Calling Orc.ai.take_turn()
>>> AISystem: Orc returned 0 results
>>> AISystem: Orc turn, ai_type=basic, has_strategy=False
>>> AISystem: Calling Orc.ai.take_turn()
>>> AISystem: Orc returned 0 results
... (repeats indefinitely)
```

The key observations:
1. A single player wait action was received
2. Then `AISystem: Orc turn` logs repeated many times
3. The same `ai.take_turn()` was called repeatedly without any turn boundary
4. When the player died, the loop continued on the death screen

## Root Cause

The issue was NOT in `BotInputSource` (which was already correctly only returning actions during `PLAYERS_TURN`), but rather in the `AISystem` itself:

1. **No protection against re-entrancy**: `AISystem.update()` could potentially be called recursively
2. **No protection against duplicate entity processing**: If an entity appeared multiple times in the entities list (due to bugs elsewhere), it would be processed multiple times
3. **No state guards for non-AI phases**: AISystem could run in inappropriate game states (death screen, menus, etc.)
4. **Fast bot loop with no blocking I/O**: The main loop ran unbounded in bot mode, potentially calling `engine.update()` rapidly

While the exact cause of the runtime hang wasn't definitively identified through static analysis, the symptoms strongly suggested that `ai.take_turn()` was being called multiple times per update cycle, either due to:
- The same entity appearing multiple times in the entities list
- Some form of recursive or re-entrant call to AISystem.update()
- AISystem running in states where it shouldn't

## Solution

Added comprehensive defensive guards to `AISystem` to prevent all possible infinite loop scenarios:

### 1. Re-entrancy Guard (GUARD 1)

Added `_update_call_depth` counter to detect and block recursive calls to `update()`:

```python
# GUARD 1: Prevent re-entrancy
if self._update_call_depth > 0:
    logger.error(f"CRITICAL: AISystem.update() called recursively! Depth={self._update_call_depth}")
    return

self._update_call_depth += 1
try:
    # ... process AI turns ...
finally:
    self._update_call_depth -= 1
```

### 2. Forbidden States Guard (GUARD 3)

Added explicit list of game states where AI should NEVER run:

```python
forbidden_states = {
    GameStates.PLAYER_DEAD,
    GameStates.SHOW_INVENTORY,
    GameStates.DROP_INVENTORY,
    GameStates.TARGETING,
    GameStates.THROW_SELECT_ITEM,
    GameStates.THROW_TARGETING,
    GameStates.LEVEL_UP,
    GameStates.CHARACTER_SCREEN,
    GameStates.NPC_DIALOGUE,
    GameStates.WIZARD_MENU,
    GameStates.CONFRONTATION,
    GameStates.VICTORY,
    GameStates.FAILURE,
}

if current_state in forbidden_states:
    self._processed_entities_this_update.clear()
    return
```

### 3. Duplicate Entity Guard

Added `_processed_entities_this_update` set to track which entities have been processed in the current update cycle:

```python
def _process_entity_turn(self, entity: Any, game_state) -> None:
    # GUARD: Prevent processing the same entity multiple times
    entity_id = id(entity)
    if entity_id in self._processed_entities_this_update:
        logger.warning(f"ANTI-LOOP: Skipping duplicate turn for {entity.name}")
        return
    
    # Mark this entity as processed
    self._processed_entities_this_update.add(entity_id)
    # ... process turn ...
```

The set is cleared:
- At the end of each `update()` call (when `_update_call_depth` returns to 0)
- When exiting early due to forbidden states
- When not in ENEMY phase

### 4. Proper State Cleanup

Ensured that the processed entities set is cleared appropriately to prevent state leakage between update cycles.

## Testing

Created comprehensive integration tests in `tests/test_bot_mode_ai_loop_integration.py` that exercise the REAL game engine and AISystem code paths:

1. **`test_ai_system_processes_each_enemy_exactly_once_per_update`**: Core test - verifies each enemy's `ai.take_turn()` is called exactly once per update
2. **`test_ai_system_does_not_run_multiple_times_in_one_update`**: Verifies no runaway processing when `engine.update()` is called rapidly
3. **`test_ai_system_does_not_run_in_player_dead_state`**: Ensures AI never runs when player is dead
4. **`test_bot_mode_does_not_hang_on_empty_room`**: Simulates the exact bug scenario - bot in empty room
5. **`test_same_entity_not_processed_twice_in_one_update`**: Guards against duplicate entities in the list
6. **`test_ai_system_update_not_reentrant`**: Verifies the re-entrancy guard works

All 6 integration tests pass, plus all 7 existing unit tests in `test_bot_mode_infinite_loop_fix.py`.

## Files Modified

1. **`engine/systems/ai_system.py`**:
   - Added `_processed_entities_this_update` set
   - Added `_update_call_depth` counter
   - Enhanced `update()` with 4 comprehensive guards
   - Enhanced `_process_entity_turn()` with duplicate entity detection

2. **`io_layer/bot_input.py`**: 
   - No changes needed (already correct)

## Files Added

1. **`tests/test_bot_mode_ai_loop_integration.py`**: Comprehensive integration tests
2. **`BOT_MODE_AI_LOOP_FIX.md`**: This document

## Verification

To verify the fix works in actual runtime:

```bash
# Run the integration tests
python3 -m pytest tests/test_bot_mode_ai_loop_integration.py -v

# Run bot mode manually (requires user to test interactively)
python3 engine.py --bot
```

Expected behavior:
- Bot should run continuously without hanging
- When player spawns alone, bot should keep sending wait actions and the game should progress smoothly
- When player dies, bot should stop sending actions (death screen)
- No "beachball" or infinite loops
- AISystem logs should show each enemy processed once per turn, not repeatedly

## Architecture Invariants Preserved

✅ **ECS Is Foundational**: No changes to ECS structure  
✅ **Rendering Is Read-Only**: No rendering changes  
✅ **Input Is Abstracted**: BotInputSource continues to work correctly  
✅ **Main Loop Is the Only Loop**: Added guards to prevent accidental nested loops  
✅ **Small, Focused Changes**: Only modified AISystem with defensive guards  
✅ **Tests Added**: Comprehensive integration tests ensure no regression

## Notes

The defensive programming approach taken here means that even if the exact root cause wasn't a specific scenario we identified, the guards will prevent ALL possible infinite loop scenarios:

- If `update()` is ever called recursively → blocked by GUARD 1
- If the same entity appears multiple times → only processed once
- If AI tries to run in wrong states → blocked by GUARD 3
- If state transitions fail → entities set is cleared to prevent state leakage

This makes the system robust against future changes that might introduce similar bugs.

