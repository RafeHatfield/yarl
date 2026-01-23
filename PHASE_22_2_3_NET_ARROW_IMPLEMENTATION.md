# Phase 22.2.3: Net Arrow Implementation

**Status**: ✅ Complete and Tested  
**Date**: 2026-01-23  
**Test Results**: 3623/3623 fast tests pass (no regressions)  
**New Tests**: 5 net_arrow-specific unit tests (all passing)

---

## Summary

Implemented **Net Arrow** as the first control-oriented special ammo type. Net arrows have a 50% chance to apply the **Entangled** status effect on hit, blocking the target's movement for 1 turn. This provides a tactical ranged control option for players using bows/crossbows.

---

## A) Implementation Details

### 1. Net Arrow Definition (`config/entities.yaml`)

```yaml
net_arrow:
  slot: "quiver"
  stackable: true
  quantity: 8              # Comes in stacks of 8
  char: "{"                # Arrow-like character
  color: [139, 90, 43]     # Brown (rope/net theme)
  effect_type: "entangled"
  effect_duration: 1       # 1 turn root
  effect_chance: 0.5       # 50% chance to apply on hit
```

**Design Choices:**
- **Stack size 8**: Middle of 6-10 range, balances scarcity with usability
- **50% chance**: Not guaranteed, creates tactical uncertainty
- **1 turn duration**: Short but impactful, prevents perma-lock
- **Entangled effect**: Reuses existing status effect from Root Potion

### 2. Effect Chance System (Phase 22.2.3)

**Added `effect_chance` parameter to special ammo:**

```python
# config/entity_registry.py
@dataclass
class SpecialAmmoDefinition:
    # ...existing fields...
    effect_chance: float = 1.0  # Phase 22.2.3: 0.0-1.0, default 100%
```

**Effect application with chance roll:**

```python
# components/fighter.py - _apply_special_ammo_effects()
import random
if random.random() >= effect_chance:
    # Effect didn't trigger
    return results
```

- Uses **seeded RNG** via `random.random()` for determinism
- Applies **before** effect application (not after)
- Fire arrows maintain 100% chance (default)

### 3. Entangled Effect Handler

**Added `entangled` case to `_apply_special_ammo_effects()`:**

```python
elif effect_type == 'entangled':
    # Create entangled effect
    entangled = EntangledEffect(
        duration=effect_duration,
        owner=target
    )
    
    # Apply to target
    target.status_effects.add_effect(entangled)
    
    results.append({
        "message": MB.custom(f"🕸️ {target.name} is snared by the net arrow!", (139, 90, 43))
    })
    
    # Track metric
    collector.increment('special_ammo_effects_applied')
```

**Behavior:**
- Reuses `EntangledEffect` (same as Root Potion)
- Blocks movement for `duration` turns
- Turn is consumed on blocked movement attempt
- Refreshes if reapplied (doesn't stack)

### 4. Metrics

Reuses existing special ammo metrics:
- `special_ammo_shots_fired`: Increments on hit OR miss
- `special_ammo_effects_applied`: Increments only on successful effect application (after chance roll)

**No per-type metrics** — keeps telemetry lean and focused.

---

## B) Testing

### 1. Unit Tests (`tests/scenarios/test_quiver_net_arrow.py`)

**5 tests, all passing:**

1. **`test_net_arrow_applies_entangled_on_hit`**
   - Verifies entangled effect is applied on hit (with seeded RNG)
   - Checks effect duration (1 turn)

2. **`test_net_arrow_effect_does_not_always_apply`**
   - Verifies 50% chance by testing multiple seeds
   - Confirms not 100% effect rate

3. **`test_net_arrow_consumed_on_miss`**
   - Verifies ammo consumption on miss (no effect applied)

4. **`test_entangled_blocks_movement`**
   - Verifies entangled effect blocks `entity.move()`
   - Confirms movement denial mechanics

5. **`test_net_arrow_auto_unequip_when_empty`**
   - Verifies quiver auto-unequips when quantity reaches 0
   - Confirms basic ammo fallback works

### 2. Scenario (`config/levels/scenario_net_arrow_identity.yaml`)

**Identity scenario for deterministic testing:**

- **Setup**: Player with shortbow + 8 net arrows vs 2 melee orcs
- **Seed**: `seed_base=1337` for reproducibility
- **Expected metrics** (20 runs):
  - `special_ammo_shots_fired`: ≥60 (3+ per run)
  - `special_ammo_effects_applied`: ≥15 (varies with hit rate and 50% chance)

**Purpose**: Validate net arrow in realistic combat context.

---

## C) Changes Summary

### Files Modified

1. **`config/entities.yaml`**
   - Added `net_arrow` definition under `special_ammo`

2. **`config/entity_registry.py`**
   - Added `effect_chance: float = 1.0` to `SpecialAmmoDefinition`
   - Updated `_process_special_ammo_with_inheritance()` to parse `effect_chance`

3. **`config/factories/equipment_factory.py`**
   - Store `ammo_effect_chance` attribute on created ammo entities

4. **`components/fighter.py`**
   - Added effect chance roll in `_apply_special_ammo_effects()`
   - Added `entangled` effect handler
   - Uses `import random` + `random.random()` for seeded RNG

### Files Created

5. **`tests/scenarios/test_quiver_net_arrow.py`**
   - 5 unit tests for net arrow mechanics

6. **`config/levels/scenario_net_arrow_identity.yaml`**
   - Deterministic scenario for net arrow validation

7. **`PHASE_22_2_3_NET_ARROW_IMPLEMENTATION.md`**
   - This summary document

---

## D) Design Rationale

### Why Entangled (not a new effect)?

- **Reuse existing status effect** (EntangledEffect from Root Potion)
- **Consistent mechanics**: Players already understand "rooted" from trap/potion context
- **No new code**: Entangled already has movement blocking, metrics, and messaging

### Why 50% chance?

- **Tactical uncertainty**: Not a guaranteed effect, creates risk/reward
- **Balances ranged control**: Prevents trivializing melee enemies
- **Design space**: Leaves room for 100% effect ammo in the future (e.g., ice arrows)

### Why 1 turn duration?

- **Short but impactful**: Enough to reposition or gain distance
- **No perma-lock**: Prevents frustrating gameplay (for player or enemy)
- **Scales with refresh**: Can maintain entangle by hitting repeatedly

### Why stack size 8?

- **Middle ground**: Between 6 (too scarce) and 10 (fire arrow baseline)
- **Scarcity encourages choice**: Not spammable like fire arrows
- **Fits control role**: Tactical use, not sustained DPS

---

## E) Integration with Existing Systems

### Status Effects

- Uses `EntangledEffect` (Phase 20D.1)
- Movement blocking enforced at `Entity.move()` level
- Metrics tracked via `entangle_applications` and `entangle_moves_blocked`

### Quiver System (Phase 22.2.2)

- Consumption on hit OR miss (not on denial)
- Auto-unequip when quantity reaches 0
- Uses existing quiver slot validation

### Ranged Doctrine

- Applies only to `is_ranged_weapon` weapons (shortbow, longbow, crossbow)
- No adjacent retaliation change (ranged mechanics unchanged)
- Knockback remains independent (no conflict)

---

## F) Follow-On Possibilities

### Future Special Ammo Types

Now that `effect_chance` is in place, we can easily add:
- **Ice arrows**: 100% chance to slow for 2 turns
- **Piercing arrows**: 30% chance to ignore armor
- **Poison arrows**: 60% chance to apply poison (existing status effect)

### Future Enhancements

- **Ammo crafting**: Combine basic arrows + ingredients → special ammo
- **Ammo rarities**: Common (8-stack), Rare (5-stack), Epic (3-stack)
- **Dual-mode ammo**: Different effects on thrown vs fired (like consumables)

---

## G) Verification

### Test Coverage

- **Unit tests**: 5 net_arrow-specific tests (all passing)
- **Integration tests**: 16 quiver tests (all passing)
- **Regression tests**: 3623 fast tests (all passing)

### Linter Status

- **No errors** in modified files
- **No warnings** in new files

### Determinism

- Seed `1337` produces consistent results in scenario
- RNG rolls use `random.random()` (seeded by test harness)
- Effect application order is deterministic

---

## H) Metrics Expectations (Scenario)

For 20 runs of `scenario_net_arrow_identity` (seed_base=1337):

| Metric | Expected Range | Rationale |
|--------|---------------|-----------|
| `special_ammo_shots_fired` | 60-160 | 3-8 shots per run (depends on combat length) |
| `special_ammo_effects_applied` | 15-60 | ~25-50% of shots apply (hit rate * 50% chance) |
| `player_kills` | 10-20 | Should win most fights with control |
| `player_deaths` | 0-10 | Some losses if RNG is bad |

**Note**: Metrics are probabilistic but deterministic per seed.

---

## I) Conclusion

Net Arrow implementation is **complete, tested, and integrated**. It provides a tactical ranged control option using existing status effects, maintains backward compatibility, and sets the foundation for future special ammo types with varied effect chances.

**Next steps**: Consider adding 1-2 more special ammo types (poison, ice) to validate the `effect_chance` system across different effect types and durations.
