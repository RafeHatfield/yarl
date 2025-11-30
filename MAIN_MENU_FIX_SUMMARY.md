# Main Menu Regression Fix - Summary

## Problem

After implementing the manual play loop fix (which prevented AI spam), a **critical regression** was introduced:

- **Symptom**: Pressing 'a' on the main menu to start a new game did nothing - the screen stayed stuck on the menu
- **Console output**: Item registry warnings appeared (healing_potion, invisibility_scroll) indicating some code ran, but the game never rendered
- **Root Cause**: The `should_update_systems` gating was applying on the **first frame** after starting a new game, preventing `engine.update()` from running

## Technical Explanation

### The Flow

1. User presses 'a' on main menu (handled in `engine.py` lines 426-445)
2. `get_game_variables()` is called (produces item warnings)  
3. `show_main_menu = False` is set
4. Next loop iteration calls `play_game_with_engine()`
5. **First frame inside `play_game_with_engine()`**:
   - No keyboard input yet → `action = {}`, `mouse_action = {}`
   - My gating logic: `has_action = False`, `auto_explore_active = False`
   - Therefore: `should_update_systems = False`
   - `engine.update()` is SKIPPED (line 1000)
6. **Result**: RenderSystem never runs → FOV never computes → Screen stays black/stuck

### Why This Matters

`engine.update()` is responsible for:
- Running RenderSystem (draws the game)
- Computing FOV
- Centering camera on player
- Initial game state setup

Without calling it on the first frame, the game never renders!

## Solution

### Changes Made

**File**: `engine_integration.py`

#### 1. Added First Frame Tracking (line 521-524)

```python
# Track first frame to ensure initial render
# Without this, the first frame would skip engine.update() (no action yet)
# and the screen would stay black/stuck on menu
first_frame_needs_render = True
```

#### 2. Refined Gating Logic (lines 669-730)

The key changes:

1. **Added first frame exception**: Always update on first frame
2. **Scoped gating to PLAYERS_TURN only**: Other states (LEVEL_UP, CHARACTER_SCREEN, NPC_DIALOGUE, etc.) always update
3. **Clear documentation**: Comments explain when gating applies vs doesn't apply

```python
# SCOPE: This gating applies ONLY to in-dungeon gameplay (PLAYERS_TURN state),
#        NOT to menus, dialogs, or other UI states.

should_update_systems = True  # Default

# Get current game state to determine if gating should apply
current_state = engine.state_manager.state.current_state

if input_mode != "bot" and current_state == GameStates.PLAYERS_TURN:
    # MANUAL MODE IN-DUNGEON: Only update if there's an action OR auto-explore is active
    
    # EXCEPTION: First frame always needs to update for initial render
    if first_frame_needs_render:
        should_update_systems = True
        first_frame_needs_render = False
        logger.debug("MANUAL MODE: First frame - updating for initial render")
    else:
        # Apply normal gating logic...
        has_action = bool(action or mouse_action)
        auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE) if player else None
        auto_explore_active = bool(auto_explore and auto_explore.is_active())
        
        if not has_action and not auto_explore_active:
            should_update_systems = False
```

### Key Insights

The gating **ONLY applies during in-dungeon PLAYERS_TURN state**. It does NOT apply to:
- First frame (needs initial render)
- LEVEL_UP state
- CHARACTER_SCREEN state
- SHOW_INVENTORY, DROP_INVENTORY states
- TARGETING, THROW_TARGETING states  
- NPC_DIALOGUE state
- WIZARD_MENU state
- CONFRONTATION, VICTORY, FAILURE states
- ENEMY_TURN state (handled by AISystem)

This ensures that:
- ✅ Title → game transition works (first frame renders)
- ✅ All menu/dialog states work properly
- ✅ Manual play still enforces "one input → one tick" invariant
- ✅ Bot/soak modes continue to work unchanged

## Tests Added

**File**: `tests/test_engine_integration_io_loop.py`

Added 3 new tests to `TestManualPlayLoopInvariants` class:

### 1. `test_first_frame_always_updates`
- **Purpose**: Locks in the fix for the "menu stuck" regression
- **Verifies**: First frame always updates, regardless of input
- **Critical**: Without this, game never renders after starting

### 2. `test_gating_only_applies_to_players_turn`
- **Purpose**: Ensures gating is scoped correctly
- **Verifies**: 
  - Gating applies in PLAYERS_TURN with no action
  - Gating does NOT apply in LEVEL_UP
  - Gating does NOT apply in CHARACTER_SCREEN

### 3. Updated existing tests
- All 6 tests in `TestManualPlayLoopInvariants` pass ✅

## Item Registry Warnings (Side Issue)

The warnings about `'healing_potion'` and `'invisibility_scroll'` not found in registry are **unrelated** to the main menu bug. They occur during `get_game_variables()` when initializing the starting inventory.

- **Location**: `config/factories/spawn_factory.py` line 345
- **Impact**: Just warnings, don't block game start
- **Status**: Existing issue, not introduced by this fix

These warnings should be addressed separately (probably missing entries in the item registry YAML), but they don't prevent the game from running.

## Verification

### Tests Run

1. ✅ Manual play loop invariant tests (6/6 passed)
2. ✅ Bot mode turn transition tests (4/4 passed)  
3. ✅ AI system tests (38/38 passed)

### Manual Testing Checklist

Please verify:

1. **Title Screen → New Game**:
   - Press 'a' on main menu
   - Game should start immediately and render the dungeon
   - Player should see the map, FOV, entities, etc.

2. **Manual Play**:
   - Move with arrow keys
   - Each keypress should result in ONE enemy turn phase
   - No AI spam in logs

3. **AutoExplore**:
   - Press 'o' to start AutoExplore
   - Should work normally  
   - After stopping, manual control should resume

4. **Menu States**:
   - Press 'c' for character screen
   - Press 'i' for inventory (if using legacy UI)
   - All should render and respond properly

5. **Bot Mode**:
   - Run: `python3 engine.py --bot`
   - Should work normally

## Files Changed

- `/Users/rafehatfield/development/rlike/engine_integration.py`:
  - Lines 521-524: Added `first_frame_needs_render` flag
  - Lines 669-730: Refined gating logic with first-frame exception and PLAYERS_TURN scoping
  
- `/Users/rafehatfield/development/rlike/tests/test_engine_integration_io_loop.py`:
  - Added `from game_states import GameStates` import
  - Added 3 new tests (first frame, gating scope)
  - All 6 tests passing

## Summary

This fix resolves the "stuck on menu" regression by ensuring that:
1. **First frame always updates** (initial render)
2. **Gating only applies to PLAYERS_TURN** (not menus/dialogs)
3. **Manual play invariant preserved** (no AI spam)
4. **Bot mode unchanged** (still works)

The root cause was that my original gating was too broad - it prevented `engine.update()` on the first frame and potentially in menu states. The fix makes the gating **explicit and scoped** to exactly where it's needed: in-dungeon PLAYERS_TURN state after the first frame.

---

**Date**: 2025-11-24  
**Issue**: Main menu stuck after pressing 'a'  
**Root Cause**: First frame skipped `engine.update()` due to gating  
**Fix**: Added first-frame exception and scoped gating to PLAYERS_TURN only  
**Tests Added**: 3 (all pass)  
**Tests Verified**: 48+ (all pass)




