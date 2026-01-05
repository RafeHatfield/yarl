# Mouse Pathing "Cannot Reach That Location" Bug Fix

## Summary

Fixed a critical bug where all mouse clicks for movement showed "Cannot reach that location" due to an incorrect cost map construction for the A* pathfinding algorithm.

## Root Cause

The bug was in `components/player_pathfinding.py` line 308. The cost map passed to `tcod.path.AStar` had incorrect array indexing:

### The Problem

1. `fov.walkable` is a numpy array indexed as `[y, x]` (row, column order)
2. `tcod.path.AStar.get_path(x, y, target_x, target_y)` expects coordinates in `(x, y)` order
3. `tcod.path.AStar` expects the cost array to be indexed as `cost[x, y]`
4. **But we were passing `fov.walkable` directly without transposing it!**

This meant:
- When checking if position (x=8, y=5) was walkable
- AStar would check `cost[8, 5]` 
- But our array had the walkability info at `cost[5, 8]`
- Result: AStar thought all walkable tiles were blocked and vice versa

## The Fix

Changed line 308 in `components/player_pathfinding.py`:

```python
# BEFORE (broken):
cost = fov.walkable.astype("int8")

# AFTER (fixed):
cost = fov.walkable.T.astype("int8")  # Transpose to convert [y,x] to [x,y]
```

The `.T` (transpose) operation swaps the array dimensions from `[y, x]` to `[x, y]`, matching what AStar expects.

## Testing

Added comprehensive regression test in `tests/regression/test_mouse_pathing_regression.py`:

1. ✅ Can pathfind to adjacent tiles
2. ✅ Can pathfind to nearby tiles
3. ✅ Can pathfind around obstacles (walls)
4. ✅ Correctly rejects blocked destinations
5. ✅ Cost map construction is correct

All existing pathfinding tests (14 tests) pass.
All mouse interaction tests (94 tests) pass.

## Verification

To verify the fix works:

1. Start the game
2. Left-click on any open ground tile → player should pathfind there
3. Right-click on a distant item → player should pathfind to it and pick it up
4. Pathfinding should correctly route around walls and obstacles

## Technical Details

### tcod.path.AStar API

- **Input**: cost array where non-zero = walkable (with cost value), zero = blocked
- **Coordinates**: `get_path(start_x, start_y, end_x, end_y)` uses (x, y) order
- **Array indexing**: Expects `cost[x, y]` not `cost[y, x]`

### fov.walkable Array

- **Type**: numpy ndarray with shape `(height, width)` = `(y_size, x_size)`
- **Indexing**: `fov.walkable[y, x]` follows standard numpy row/column convention
- **Values**: True = walkable, False = blocked

### Why Transpose is Needed

```python
# fov.walkable shape: (height, width) = (y_max, x_max)
# AStar expects: (width, height) = (x_max, y_max)
# Solution: transpose with .T
```

## Related Files

- `components/player_pathfinding.py` - Main fix location
- `mouse_movement.py` - Calls pathfinding for mouse clicks
- `tests/regression/test_mouse_pathing_regression.py` - Regression tests
- `tests/test_player_explored_pathfinding.py` - Existing pathfinding tests




