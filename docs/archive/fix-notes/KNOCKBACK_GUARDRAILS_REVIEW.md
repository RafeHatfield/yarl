# Knockback Implementation - Code Review Guardrails

## A) Entity.move() Bypass Check ✅ PASS

**Verification performed:**
```bash
grep "self\.x\s*=" entity.py
grep "entity\.x\s*=" services/knockback_service.py
```

**Results:**
- ✅ `services/knockback_service.py` has **zero direct position assignments**
- ✅ Uses `_execute_move()` which calls canonical `entity.move(dx, dy)`
- ✅ Respects all movement blockers (entangle/root/etc)

**Other direct assignments found are all legitimate teleport mechanics:**
- `item_functions.py:333` - Scroll of Confusion (random teleport)
- `item_functions.py:394` - Scroll of Teleportation (targeted teleport)
- `services/portal_manager.py:209` - Portal system (entrance/exit teleport)

**Conclusion:** No bypass reintroduced. Knockback uses canonical movement execution.

---

## B) "Blocked Early" Definition ✅ IMPLEMENTED WITH GUARDRAILS

### Design Choice: Option A (Occupied Tile Counts as Hard Block)

**Rationale:**
1. Makes knockback feel physical and tactical immediately
2. Body-blocking matters; positioning creates value
3. Portal-friendly: "pushing into stuff" ≠ "pushing into empty space"
4. Easier to tighten later than to add depth after baselining

### Guardrails Implemented

#### 1. No Chain Effects ✅
- **Only the shoved entity is staggered** (not the blocker)
- No damage, extra shove, or secondary stagger
- Code location: `services/knockback_service.py:145-161`

```python
# Apply StaggeredEffect (only to the shoved entity, not the blocker)
stagger = StaggeredEffect(owner=defender)
stagger_results = defender.status_effects.add_effect(stagger)
```

#### 2. Message Clarity ✅
- **Wall impact**: "X slams into the wall and is staggered!"
- **Entity collision**: "X collides with Y and is staggered!"
- Code location: `services/knockback_service.py:154-161`

```python
if blocking_entity:
    # Collision with another entity
    results.append({
        'message': MB.warning(f"{defender.name} collides with {blocking_entity.name} and is staggered!")
    })
else:
    # Impact with wall/terrain
    results.append({
        'message': MB.warning(f"{defender.name} slams into the wall and is staggered!")
    })
```

#### 3. Scenario Coverage ✅
- **Wall-blocked stagger**: 2 trolls positioned near walls (positions [3, 5] and [11, 5])
- **Entity-blocked stagger**: 1 blocker orc at position [9, 5]
- Total enemies: 5 (2 weak orcs + 1 strong orc + 2 trolls + 1 blocker)
- Scenario file: `config/levels/scenario_knockback_weapon_identity.yaml`

---

## Implementation Details

### Modified Function Signature

**Before:**
```python
def _can_move_to(...) -> bool:
    return False  # or True
```

**After:**
```python
def _can_move_to(...) -> Tuple[bool, Optional['Entity']]:
    return (False, None)        # Blocked by wall/terrain
    return (False, other)       # Blocked by entity
    return (True, None)         # Can move
```

### Caller Update

```python
can_move, blocker = _can_move_to(defender, target_x, target_y, game_map, entities)
if not can_move:
    blocked_early = True
    blocking_entity = blocker  # None = wall, Entity = collision
    break
```

---

## Testing

### Unit Tests ✅
All 7 tests pass:
- Distance mapping (4 tests)
- Stagger application (2 tests)
- Canonical movement execution (1 test)

### Scenario Coverage ✅
Identity scenario exercises:
- Wall-impact stagger (trolls near walls)
- Entity-collision stagger (blocker orc)
- Power-delta distance scaling (weak/strong orcs)

---

## Metrics Expectations

Lower-bound invariants (30 runs, deterministic):
- `knockback_applications >= 20`
- `knockback_tiles_moved >= 20`
- `knockback_blocked_events >= 5` (wall + entity blocks)
- `stagger_applications >= 5` (wall + entity staggers)
- `stagger_turns_skipped >= 5`
- `player_deaths <= 20` (sanity check only, generous to avoid flakiness)

**Design principle:** Use lower-bound invariants (`>=`) rather than expected ranges to avoid flakiness from kill ordering changes. Upper bounds are only for sanity checks and should be generous.

---

## Future Tightening Options (If Needed)

If entity-collision stagger proves too chaotic in practice:

```python
# Option: Only wall/terrain causes stagger (not entity collision)
if not can_move:
    # Check if blocked by wall/terrain (not just entity)
    if game_map.tiles[target_x][target_y].blocked:
        blocked_early = True  # Only wall/terrain causes stagger
    break
```

**Recommendation:** Baseline with current behavior (Option A), observe in practice, tighten if needed.

---

## Sign-Off

✅ No Entity.move() bypass
✅ No chain effects (only shoved entity staggered)
✅ Message clarity (wall vs entity)
✅ Scenario coverage (both types tested)
✅ All unit tests pass
✅ All fast tests pass

**Ready for integration testing and baselining.**

