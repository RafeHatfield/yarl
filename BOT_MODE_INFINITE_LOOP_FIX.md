# Bot Mode Infinite Loop Fix

## Problem Summary

When running the game in bot mode (`python engine.py --bot`), the game would hang or "beachball" after a few seconds in certain scenarios:

1. **Empty rooms with no monsters**: Game would hang immediately
2. **Death screen**: After dying, console would spam endless logs like:
   ```
   >>> KEYBOARD ACTION RECEIVED: {'wait': True}
   >>> Calling handler for wait
   >>> AISystem: Orc turn, ai_type=basic, has_strategy=False
   >>> AISystem: Calling Orc.ai.take_turn()
   >>> AISystem: Orc returned 0 results
   >>> AISystem: Orc turn, ai_type=basic, has_strategy=False
   >>> AISystem: Calling Orc.ai.take_turn()
   >>> AISystem: Orc returned 0 results
   ... (repeats forever)
   ```

## Root Cause Analysis

The infinite loop was caused by **unguarded input feeding in bot mode**:

1. **BotInputSource always returned `{'wait': True}`** regardless of game state
2. **Main game loop called `input_source.next_action()` on every frame** without state checks
3. **When player was dead or in a non-playing state**, the bot would keep returning `wait` actions
4. **Each `wait` action triggered a full turn cycle**, including AISystem updates
5. **AISystem would try to process monsters' turns** even though the game should have stopped
6. **In bot mode with no blocking input (no keyboard to press)**, this became an infinite tight loop

### Key Issue: State Awareness

The problem was that `BotInputSource` had **zero awareness of game state**. It would return actions in ALL states:
- ✗ PLAYERS_TURN (correct)
- ✗ ENEMY_TURN (wrong - should not feed actions)
- ✗ PLAYER_DEAD (wrong - should not feed actions)
- ✗ Menus (wrong - should not feed actions)

## Solution

### Primary Fix: BotInputSource State Guard

Modified `io_layer/bot_input.py` to add **state-aware action filtering**:

```python
def next_action(self, game_state: Any) -> ActionDict:
    """Return the next bot action.
    
    CRITICAL: Only return actions during PLAYERS_TURN.
    When in PLAYER_DEAD, menus, or other non-playing states, return empty action
    to prevent the input loop from continuously feeding actions into the engine
    and causing infinite AI loops or hangs.
    """
    from game_states import GameStates
    
    # Defensive: Check for valid game_state with current_state attribute
    if game_state and hasattr(game_state, 'current_state'):
        # Only generate actions during actual gameplay
        if game_state.current_state == GameStates.PLAYERS_TURN:
            # During PLAYERS_TURN, return wait action (trivial bot behavior)
            return {'wait': True}
        else:
            # Return empty action dict for non-playing states
            # This prevents the infinite loop bug
            return {}
    
    # Safety fallback: No valid game state, return no action
    return {}
```

### Secondary Documentation: AISystem Invariant

Added comment to `engine/systems/ai_system.py` explaining the critical invariant:

```python
def _process_entity_turn(self, entity: Any, game_state) -> None:
    """Process a single entity's AI turn.
    
    CRITICAL INVARIANT:
    Each entity should only take ONE ai.take_turn() call per ENEMY phase.
    Calling take_turn() multiple times without state changes causes infinite loops,
    especially in bot mode where there's no blocking input to break the cycle.
    """
```

## Behavior Changes

### Before Fix
```
State: PLAYER_DEAD
BotInputSource.next_action() → {'wait': True}  ← BUG: Feeds actions even in death
Main loop continues
ActionProcessor tries to process 'wait'
```

### After Fix
```
State: PLAYER_DEAD
BotInputSource.next_action() → {}  ← Correct: No actions in death state
Main loop processes empty dict (safe, no-op)
Game waits for state change
```

## Test Coverage

Created comprehensive test suite in `tests/test_bot_mode_infinite_loop_fix.py`:

1. ✓ Bot does not feed actions on death screen
2. ✓ Bot does not feed actions during AI turn
3. ✓ Bot only feeds actions during PLAYERS_TURN
4. ✓ Input loop terminates in death state (100 calls return empty)
5. ✓ Empty actions are safe to process
6. ✓ State transitions work correctly
7. ✓ Null/malformed game_state handled gracefully

Updated existing tests in `tests/test_bot_mode_basic.py`:
- Now correctly expect empty actions in non-PLAYERS_TURN states
- All 18 bot mode tests pass

## Files Modified

1. **io_layer/bot_input.py**
   - Added state-aware filtering to `next_action()`
   - Returns `{}` when not in PLAYERS_TURN
   - Returns `{'wait': True}` only during PLAYERS_TURN

2. **engine/systems/ai_system.py**
   - Added CRITICAL INVARIANT comment to `_process_entity_turn()`
   - Documents why we must avoid looping on ai.take_turn()

3. **tests/test_bot_mode_basic.py**
   - Updated tests to reflect corrected behavior
   - Now tests that bot returns `{}` in non-playing states

4. **tests/test_bot_mode_infinite_loop_fix.py** (NEW)
   - Comprehensive test suite for the infinite loop fix
   - Tests edge cases and state transitions

## Verification

Run the test suite:
```bash
python3 -m pytest tests/test_bot_mode_*.py -v
# Result: 18 passed, 1 warning
```

Expected behavior after fix:
- ✓ Normal mode (`python engine.py`) - unchanged, works as before
- ✓ Bot mode with monsters - monsters can kill idle player (acceptable)
- ✓ Bot mode with empty room - does NOT hang/beachball
- ✓ Bot mode after death - does NOT spam AISystem logs, cleanly stops

## Design Principles Maintained

1. **Single Responsibility** - BotInputSource only handles input, not game logic
2. **State Awareness** - Input respects game state transitions
3. **No Blocking** - Bot input still returns immediately (non-blocking)
4. **Backward Compatible** - Normal keyboard mode unaffected
5. **Minimal Changes** - Only modified the input source, not game engine
6. **Defensive Coding** - Handles null/malformed game_state gracefully

## Future Improvements

When expanding bot AI capabilities, follow these patterns:

1. Continue checking `game_state.current_state` before returning actions
2. For menus: return action to navigate/select instead of `wait`
3. For death screen: optionally return action to restart/quit
4. For AI turn: return `{}` to let AI process
5. Add state-specific bot behaviors in future iterations

## Conclusion

The infinite loop bug is fixed by making `BotInputSource` **state-aware**. The bot now only returns actions during the player's turn, preventing the input loop from feeding continuous actions during game states where no input is needed.

This maintains the clean InputSource abstraction while preventing the tight loop that caused the beachball/hang behavior.

