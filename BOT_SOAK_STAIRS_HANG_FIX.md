# Bot Soak Stairs Hang Fix

**Date:** 2025-11-17  
**Status:** ✅ Complete  
**Related:** BOT_SOAK_CROSS_RUN_STATE_FIX.md

---

## Problem Summary

After fixing the cross-run state leakage bug, a second issue was discovered during testing:

**Bot would occasionally hang at the end of run 2+** when it encountered stairs during exploration.

---

## Root Cause

Auto-explore has a stop condition that triggers when the player is standing on stairs (to prevent accidentally descending in manual play). However, this created an **infinite loop** for the bot:

1. Bot explores and steps on stairs
2. Auto-explore immediately stops with "Stairs found"
3. Bot tries to restart auto-explore
4. Auto-explore starts, checks if on stairs → **stops immediately again**
5. **Infinite loop** - bot can't restart because it's still standing on the same stairs

**Code location:** `components/auto_explore.py` line 307:
```python
# 6. Check if standing on stairs
if self._on_stairs(entities):
    return "Stairs found"
```

The `_on_stairs()` method would return `True` **every time** the player was on stairs, with no memory of whether those stairs were already known.

---

## Solution

Track "known stairs" similar to how we track known monsters and known items. Auto-explore now only stops for **NEW stairs** (not previously discovered).

### Changes Made

**1. Added `known_stairs` tracking to AutoExplore component:**

```python
def __init__(self):
    # ... existing fields ...
    self.known_stairs: Set[Tuple[int, int]] = set()  # Positions of stairs discovered
```

**2. Reset known_stairs when starting exploration:**

```python
def start(self, game_map, entities, fov_map=None):
    # ... existing resets ...
    self.known_stairs = set()  # Reset known stairs
    
    # Snapshot any stairs visible when exploration starts
    if fov_map:
        for entity in entities:
            if entity.components.has(ComponentType.STAIRS):
                if map_is_in_fov(fov_map, entity.x, entity.y):
                    self.known_stairs.add((entity.x, entity.y))
```

**3. Modified `_on_stairs()` to only stop for NEW stairs:**

```python
def _on_stairs(self, entities: List['Entity']) -> bool:
    """Check if player is standing on NEW stairs (not already known).
    
    This prevents the bot from getting stuck in a loop when it stops on stairs
    and then tries to restart auto-explore while still standing on them.
    """
    player_pos = (self.owner.x, self.owner.y)
    
    for entity in entities:
        if entity.components.has(ComponentType.STAIRS):
            if entity.x == self.owner.x and entity.y == self.owner.y:
                # Only stop if these are NEW stairs
                if player_pos not in self.known_stairs:
                    self.known_stairs.add(player_pos)
                    logger.debug(f"New stairs discovered at {player_pos}")
                    return True  # Stop for new stairs
                else:
                    logger.debug(f"Standing on known stairs at {player_pos} - continuing")
                    return False  # Don't stop for known stairs
    
    return False
```

---

## Behavior After Fix

### First encounter with stairs:
1. Bot steps on stairs → auto-explore stops with "Stairs found"
2. Bot tries to restart → auto-explore starts successfully (stairs now in `known_stairs`)
3. Bot continues exploring from stairs position

### Manual play (unchanged):
- Still stops on first encounter with stairs (for safety)
- Player can manually restart auto-explore if desired
- Stairs are now tracked so auto-explore won't stop again on same stairs

---

## Files Modified

| File | Changes | Lines |
|------|---------|-------|
| `components/auto_explore.py` | Added known_stairs tracking | 98, 126, 161-166, 640-675 |

---

## Verification

**Test results (5 runs):**
```bash
$ python3 engine.py --bot-soak --runs 5
   Runs: 5
   Completed: 5  ✅ All runs completed
   Crashes: 0    ✅ No hangs on stairs
```

**Test results (10 runs):**
```bash
$ python3 engine.py --bot-soak --runs 10
   Runs: 10
   Completed: 10  ✅ All runs completed
   Crashes: 0     ✅ No hangs on stairs
```

---

## Pattern Consistency

This fix follows the same pattern used for monsters and items:

| Entity Type | Tracking Set | Stop Behavior |
|-------------|--------------|---------------|
| Monsters | `known_monsters: Set[int]` | Only stop for NEW monsters |
| Items | `known_items: Set[int]` | Only stop for NEW items |
| Stairs | `known_stairs: Set[Tuple[int, int]]` | Only stop for NEW stairs ✅ |

This ensures auto-explore can safely resume after stopping for any discovery without getting stuck in infinite loops.

---

## Related Issues

- **BOT_SOAK_CROSS_RUN_STATE_FIX.md** - MovementService singleton reset (primary fix)
- This fix addresses a secondary hang condition specific to stairs

Both fixes were necessary for stable multi-run bot soak testing.

