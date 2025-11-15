# ENEMY_TURN Control Flow Simplification

**Date:** 2025-11-15  
**Goal:** Simplify and harden the ENEMY_TURN → PLAYERS_TURN flow to prevent infinite loops in bot mode

## Problem

Bot mode was experiencing tight loops where the AI phase appeared to run multiple times per player action:

```
>>> Calling handler for wait
>>> AISystem: Orc turn, ai_type=basic, has_strategy=False
>>> AISystem: Calling Orc.ai.take_turn()
>>> AISystem: Orc returned 0 results
>>> AISystem: Orc turn, ai_type=basic, has_strategy=False   <-- DUPLICATE
>>> AISystem: Calling Orc.ai.take_turn()
>>> AISystem: Orc returned 0 results
... (10+ times)
```

**Root Cause:** The turn transition logic was overly complex, lived outside the try/finally block, and wasn't guaranteed to execute immediately after AI processing.

## Solution

### File Changed: `engine/systems/ai_system.py`

### 1. Simplified `_process_ai_turns()` (lines 231-274)

**Added explicit comments and instrumentation:**
- Added debug log: `"AISystem: Processing {len(ai_entities)} AI entities"`
- Added comment: `"CRITICAL: Bounded loop - each enemy acts exactly ONCE per enemy phase"`
- Added debug log after loop: `"AISystem: processed {len(ai_entities)} enemies, ending ENEMY_TURN → PLAYERS_TURN"`

**Key invariant:** The for loop over enemies is **bounded** - each enemy gets **exactly one** `take_turn()` call per ENEMY phase. No while loops, no recursion, no "loop until results".

```python
# CRITICAL: Bounded loop - each enemy acts exactly ONCE per enemy phase
# No while loops, no recursion, no "loop until results"
for entity in ai_entities:
    if entity.fighter and entity.fighter.hp > 0:
        self._process_entity_turn(entity, game_state)
```

### 2. Restructured `update()` Method (lines 89-229)

**Old problematic structure:**
```python
def update(self, dt: float):
    try:
        # Check if ENEMY_TURN
        if not in_enemy_turn:
            return
        
        # Process AI
        self._process_ai_turns(game_state)
        
    finally:
        # cleanup
        ...
    
    # PROBLEM: Transition logic was HERE, outside try/finally
    # - Variables from try block not accessible
    # - Runs even when NOT in ENEMY_TURN
    # - Complex, duplicated conditional logic
    if not self.turn_processing:
        if turn_manager:
            # complex logic...
        else:
            # duplicate logic...
```

**New simplified structure:**
```python
def update(self, dt: float):
    try:
        # Check if ENEMY_TURN
        if not in_enemy_turn:
            return
        
        # ═════════════════════════════════════════════════════════════════
        # ENEMY TURN PROCESSING - SIMPLIFIED, BOUNDED, DETERMINISTIC
        # ═════════════════════════════════════════════════════════════════
        
        # Process AI turns (bounded loop)
        self._process_ai_turns(game_state)
        
        # ═════════════════════════════════════════════════════════════════
        # TRANSITION BACK TO PLAYER TURN
        # This happens IMMEDIATELY after AI processing completes.
        # No loops, no recursion, just one clean state transition.
        # ═════════════════════════════════════════════════════════════════
        
        # GUARD: If player died during AI turn, stay in PLAYER_DEAD state
        if state_manager.state.current_state == GameStates.PLAYER_DEAD:
            return
        
        # Handle pathfinding if active
        if pathfinding and pathfinding.is_path_active():
            self._process_pathfinding_turn(state_manager)
            return
        
        # Advance turn phases (ENEMY → ENVIRONMENT → PLAYER)
        if turn_manager:
            turn_manager.advance_turn()
            # Check for player death from environment
            if state == PLAYER_DEAD: return
            
            turn_manager.advance_turn()
            # Process player status effects
            self._process_player_status_effects(game_state)
            # Check for player death from status effects
            if state == PLAYER_DEAD: return
        
        # Restore preserved state or return to PLAYERS_TURN
        if turn_controller and turn_controller.is_state_preserved():
            state_manager.set_game_state(restored_state)
        else:
            state_manager.set_game_state(GameStates.PLAYERS_TURN)
        
        logger.debug(f"AISystem: Transitioned from ENEMY_TURN → {state}")
        
    finally:
        # cleanup
        ...
```

### 3. Key Improvements

**Simplified control flow:**
1. ✅ Check if we're in ENEMY_TURN (if not, early return)
2. ✅ Process all AI entities in ONE bounded loop
3. ✅ IMMEDIATELY transition back to PLAYERS_TURN (within same try block)
4. ✅ No while loops, no recursion, no "loop until results"

**Deterministic behavior:**
- Each enemy acts **exactly once** per ENEMY phase
- State transition happens **immediately** after AI processing
- No complex conditional branching in transition logic
- All variables are in scope (inside try block)

**Better instrumentation:**
- Debug logs show exactly how many enemies are processed
- Debug logs show the state transition
- Clear comments explain the invariants

## Expected Behavior

### Normal Mode (python engine.py)
```
>>> KEYBOARD ACTION RECEIVED: {'wait': True}
>>> Calling handler for wait
>>> AISystem: Processing 1 AI entities
>>> AISystem: Orc turn, ai_type=basic, has_strategy=False
>>> AISystem: Calling Orc.ai.take_turn()
>>> AISystem: Orc returned N results
>>> AISystem: processed 1 enemies, ending ENEMY_TURN → PLAYERS_TURN
>>> AISystem: Transitioned from ENEMY_TURN → PLAYERS_TURN
[next frame - back to waiting for player input]
```

### Bot Mode (python engine.py --bot)

**Empty room:**
```
>>> KEYBOARD ACTION RECEIVED: {'wait': True}
>>> Calling handler for wait
>>> AISystem: Processing 0 AI entities
>>> AISystem: processed 0 enemies, ending ENEMY_TURN → PLAYERS_TURN
>>> AISystem: Transitioned from ENEMY_TURN → PLAYERS_TURN
[next frame - bot waits again]
```

**Room with monster:**
```
>>> KEYBOARD ACTION RECEIVED: {'wait': True}
>>> Calling handler for wait
>>> AISystem: Processing 1 AI entities
>>> AISystem: Orc turn, ai_type=basic, has_strategy=False
>>> AISystem: Calling Orc.ai.take_turn()
>>> AISystem: Orc returned N results
>>> AISystem: processed 1 enemies, ending ENEMY_TURN → PLAYERS_TURN
>>> AISystem: Transitioned from ENEMY_TURN → PLAYERS_TURN
[next frame - if player still alive, bot waits again; if dead, PLAYER_DEAD state prevents AI from running]
```

## Testing

Run both modes to verify:

1. **Normal mode:**
   ```bash
   python engine.py
   ```
   - Enemies should act once per player action
   - No duplicated AI turns
   - Smooth gameplay

2. **Bot mode:**
   ```bash
   python engine.py --bot
   ```
   - No infinite loops
   - No beachballing
   - Clean console output (bounded number of AI turns per wait)
   - After player death, AI should NOT keep running

## Architecture Principles Followed

✅ **Simplification over guards:** Instead of adding more defensive checks, simplified the control flow  
✅ **Bounded loops:** Each enemy acts exactly once - no while loops based on "results"  
✅ **Deterministic transitions:** State always transitions back to PLAYERS_TURN after enemy phase  
✅ **Minimal changes:** Focused only on the ENEMY_TURN control flow, didn't touch rendering or input  
✅ **ECS boundaries:** AI processing stays within the system, doesn't leak into other layers

## Files Modified

- `engine/systems/ai_system.py` - Simplified ENEMY_TURN control flow

## Files NOT Modified

- `io_layer/bot_input.py` - BotInputSource is working correctly
- `engine_integration.py` - Main game loop is working correctly
- `game_actions.py` - Action processing is working correctly

