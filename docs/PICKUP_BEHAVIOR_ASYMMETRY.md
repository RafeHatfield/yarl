# Pickup Behavior Asymmetry Analysis

**Date:** 2026-01-16  
**Status:** 📋 Documented (Potential Future Unification)

---

## Current State

### Player Pickup (Adjacent)
**Location:** `services/pickup_service.py:89-102`

```python
# Check if item is at player location or adjacent (Chebyshev distance <= 1)
dx = abs(entity.x - player.x)
dy = abs(entity.y - player.y)
chebyshev_dist = max(dx, dy)

if chebyshev_dist <= 1:
    items_in_range.append(entity)
```

- **Range:** Chebyshev distance ≤ 1 (8 adjacent tiles + same tile)
- **Rationale:** Quality of life - pick up items next to chests, on blocked tiles, etc.
- **Introduced:** Recent change to improve player UX

### Monster Pickup (Same-Tile Only)
**Location:** `components/item_seeking_ai.py:172-175`

```python
# Check if we're on the same tile as the item (can pick it up)
# Must be EXACTLY on the item, not just adjacent
if item.x == self.monster.x and item.y == self.monster.y:
    return self._get_pickup_action(item)
```

- **Range:** Exact same tile only
- **Rationale:** 
  - Monsters move as part of AI turn, naturally "step onto" items
  - Simpler logic - no need for adjacent pickup complexity
  - Monsters control their own movement (unlike player who might not want to step on dangerous tiles)

---

## Design Considerations

### Why Asymmetry Might Be Intentional

1. **Movement Control**
   - Players use keyboard/mouse and benefit from "reach" to avoid stepping on hazards
   - Monsters control their own pathfinding and can safely step onto item tiles

2. **AI Simplicity**
   - Monster AI already handles movement toward items
   - Adding adjacent pickup adds complexity without clear benefit

3. **Gameplay Balance**
   - Monsters stepping onto items is visible and predictable
   - Adjacent pickup might make monster looting feel "unfair" or "magical"

### Why Unification Might Be Better

1. **Consistency**
   - Single source of truth for pickup mechanics
   - Easier to reason about and test

2. **Edge Cases**
   - What if item is on a blocked tile? (Currently: monster can't reach it)
   - What if item is next to a hazard? (Currently: monster must step on hazard)

3. **Code Reuse**
   - Could use `PickupService` for both players and monsters
   - Reduces duplication

---

## Recommendation

**Current Status:** ✅ Working as designed, both behaviors tested and stable

**Future Consideration:** If unification is desired:

1. **Option A: Extend Monster Pickup to Adjacent**
   ```python
   # In ItemSeekingAI._get_move_towards_item()
   chebyshev_dist = max(abs(item.x - self.monster.x), abs(item.y - self.monster.y))
   if chebyshev_dist <= 1:  # Adjacent or same tile
       return self._get_pickup_action(item)
   ```
   - **Pros:** Consistent with player, handles blocked tiles
   - **Cons:** Monsters might pick up items without visibly reaching them

2. **Option B: Keep Asymmetry, Document Clearly**
   - **Pros:** Maintains current tested behavior, clear separation of concerns
   - **Cons:** Two different pickup implementations to maintain

**Current Decision:** Option B (document asymmetry, keep separate implementations)

---

## When to Reconsider Unification

Revisit this decision if any of the following occur:

1. **Items on Blocked Tiles Become Common**
   - If items frequently land on blocked tiles (e.g., chest drops, explosion scatter)
   - Monsters would be unable to pick them up with same-tile-only logic

2. **Chest Drops Can't Be Stepped Onto**
   - If chests drop items onto their own tile (blocked)
   - Monsters standing adjacent couldn't loot without adjacent pickup

3. **Ranged/Immobile Monsters Need Pickup**
   - If you add monsters that can't path (e.g., turrets, statues)
   - Or ranged monsters that shouldn't close distance to items
   - Adjacent pickup would allow them to grab nearby items

4. **"Reach" Stat or Grabber Tools**
   - If you introduce reach mechanics (long arms, telekinesis, etc.)
   - Would require distance-based pickup for both players and monsters

5. **Hazard Tiles Make Stepping Dangerous**
   - If items often land on fire/acid/spike tiles
   - Monsters would need adjacent pickup to avoid hazard damage

6. **AI Pathfinding Becomes Expensive**
   - If monster count increases significantly
   - Adjacent pickup reduces pathfinding calls (grab without moving)

**Trigger Threshold:** If 2+ of these scenarios occur, strongly consider unification.

---

## Testing Coverage

Both behaviors are now fully tested:

- **Player Adjacent Pickup:** Existing tests in `tests/test_interactions_*.py`
- **Monster Same-Tile Pickup:** New tests in `tests/integration/ai/test_monster_opportunistic_pickup.py`

All tests verify deterministic behavior under seed_base=1337.

---

## Related Files

- `services/pickup_service.py` - Player pickup (adjacent)
- `components/item_seeking_ai.py` - Monster item-seeking (same-tile)
- `components/ai/basic_monster.py` - Monster AI integration
- `tests/integration/ai/test_monster_opportunistic_pickup.py` - Monster pickup tests
