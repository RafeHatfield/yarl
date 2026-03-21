# Phase 22.2.2: Quiver + Special Ammo Implementation

**Status**: ✅ Complete and Tested  
**Date**: 2026-01-22  
**Test Results**: 3618/3618 fast tests pass (no regressions)

---

## Summary

Implemented special ammo as an explicit player choice for bows/crossbows, without introducing normal ammo bookkeeping. Special ammo is loaded into a QUIVER slot, consumed on ranged attacks (hit OR miss, but not denied), and applies rider effects on hit only.

---

## A) Core Design

### 1. Quiver Slot (New Equipment Slot)
- **Added**: `EquipmentSlots.QUIVER` (value 9)
- **Behavior**: Holds exactly one stack of special ammo
- **Empty quiver**: Basic ranged attacks work with infinite basic ammo (no effects)
- **Loaded quiver**: Ranged attacks consume 1 ammo per shot (hit OR miss)

### 2. Special Ammo Items
- **Type**: `SpecialAmmoDefinition` in entity registry
- **Properties**: stackable, quantity, effect_type, effect_duration, effect_damage_dice
- **Example**: `fire_arrow` (10 arrows, applies burning 1 dmg/turn for 3 turns)

### 3. Consumption Logic (Fighter.attack_d20)
- **On hit**: Apply ammo-specific effect, consume 1 ammo
- **On miss**: Consume 1 ammo (no effect)
- **On denial** (out of range): No consumption, attack fails
- **Auto-unequip**: When ammo quantity reaches 0, quiver is auto-unequipped

### 4. Player Control
- **Load**: Equip special ammo from inventory (uses existing toggle_equip)
- **Unload**: Unequip special ammo from quiver (uses existing toggle_equip)
- **Explicit**: No auto-use of special ammo

---

## B) Follow-on Fixes

### 1. Balance Tuning
- **fire_arrow burning**: Reduced from 4 dmg/turn → 1 dmg/turn (3 turn duration)
- **Rationale**: Match existing burning norms (Fire Potion, etc.)

### 2. Explicit Ranged Weapon Tagging
- **Replaced**: `reach >= 3` heuristic
- **New approach**: Explicit `is_ranged_weapon: bool` field in WeaponDefinition
- **Tagged weapons**: shortbow, longbow, crossbow (all set `is_ranged_weapon: true`)
- **Benefit**: No accidental qualification of long-reach melee weapons as ranged

### 3. Quiver Slot Guard
- **Validation**: Only items with `ammo_effect_type` attribute can be equipped in QUIVER
- **Rejection**: Non-special-ammo items are rejected with warning message
- **Implementation**: `Equipment.toggle_equip()` validates before equipping

### 4. Out-of-Range Denial Guard
- **Confirmed**: Range validity check occurs BEFORE quiver consumption
- **Execution order**: 
  1. `check_ranged_attack_validity()` (denies if out of range)
  2. Hit/miss determination
  3. `_apply_special_ammo_effects()` (on hit only)
  4. `_consume_special_ammo()` (on hit OR miss, but not denial)
- **Result**: Denied attacks never consume ammo

### 5. Metrics Clarity
- **Renamed**: `special_ammo_consumed` → `special_ammo_shots_fired`
- **Semantics**: Increments on every ranged shot that consumes ammo (hit OR miss, not denial)
- **Other metrics**:
  - `special_ammo_loaded`: Count of load actions (future enhancement)
  - `special_ammo_unloaded`: Count of unload actions (future enhancement)
  - `special_ammo_effects_applied`: Count of rider effects applied (hits only)

---

## C) Files Modified

### Core System
1. `equipment_slots.py` - Added QUIVER slot (enum value 9)
2. `components/equipment.py` - Added quiver field, slot validation
3. `components/equippable.py` - Added is_ranged_weapon field
4. `components/fighter.py` - Added quiver consumption and effect application

### Data & Factory
5. `config/entity_registry.py` - Added SpecialAmmoDefinition, is_ranged_weapon field
6. `config/entities.yaml` - Added fire_arrow, tagged bows/crossbows as ranged
7. `config/factories/equipment_factory.py` - Added create_special_ammo()
8. `config/factories/_factory_base.py` - Added quiver to slot mapping

### Services
9. `services/ranged_combat_service.py` - Replaced reach heuristic with explicit flag check
10. `services/scenario_harness.py` - Added quiver metrics

### Tests
11. `tests/scenarios/test_quiver_special_ammo.py` - 5 core tests
12. `tests/scenarios/test_quiver_followon_fixes.py` - 6 validation tests
13. `tests/test_ranged_combat_doctrine.py` - Updated 3 tests for explicit tagging

---

## D) Test Coverage

### Core Functionality (5 tests)
✅ Consumption on hit  
✅ Infinite basic ammo when quiver empty  
✅ Consumption on miss  
✅ Burning effect application on hit  
✅ Auto-unequip when depleted  

### Follow-on Validations (6 tests)
✅ fire_arrow burning tuned to 1 dmg/turn  
✅ Explicit is_ranged_weapon tagging (bows/crossbows)  
✅ Out-of-range denial doesn't consume ammo  
✅ Quiver slot validation (rejects non-ammo)  
✅ special_ammo_shots_fired metric accuracy  
✅ Long-reach melee weapons NOT ranged (unless tagged)  

### Regression Tests
✅ 3618/3618 fast tests pass (no regressions)  
✅ All 34 ranged combat doctrine tests pass  

---

## E) Canonical Execution Points

### Quiver Consumption (Fighter.attack_d20)
```
1. Range validity check (check_ranged_attack_validity)
   └─ If denied → return early (NO CONSUMPTION)
2. Hit/miss determination (d20 + modifiers vs AC)
3. ON HIT:
   └─ _apply_special_ammo_effects() → apply rider effects
4. AFTER HIT/MISS:
   └─ _consume_special_ammo() → decrement quantity, auto-unequip if empty
```

### Effect Application (_apply_special_ammo_effects)
- **Only on hit**: Rider effects applied to target
- **Burning**: Creates BurningEffect with 1 dmg/turn for 3 turns
- **Extensible**: TODO for poison, etc.

### Ammo Consumption (_consume_special_ammo)
- **On hit OR miss**: Decrement quantity
- **On empty**: Auto-unequip from quiver, remove from inventory
- **Feedback**: Messages for remaining count and depletion

---

## F) Metrics Tracking

### Per-Run Metrics (RunMetrics)
- `special_ammo_loaded` (future enhancement)
- `special_ammo_unloaded` (future enhancement)
- `special_ammo_shots_fired` (increments on consumption)
- `special_ammo_effects_applied` (increments on hit with effect)

### Aggregated Metrics (AggregatedMetrics)
- `total_special_ammo_loaded`
- `total_special_ammo_unloaded`
- `total_special_ammo_shots_fired`
- `total_special_ammo_effects_applied`

### No Double Counting
- `shots_fired` = consumption events (hit OR miss, not denial)
- `effects_applied` = rider effects applied (hit only)
- These are distinct and correctly aggregated

---

## G) Design Adherence

✅ **Explicit player choice**: Must load/unload via inventory  
✅ **Consumption on hit OR miss**: Implemented in canonical execution point  
✅ **Effects only on hit**: Separate method, called only in hit branch  
✅ **Infinite basic ammo**: Empty quiver = no consumption  
✅ **Bows/crossbows only**: Explicit is_ranged_weapon tagging  
✅ **No thrown item changes**: Throwing mechanics untouched  
✅ **Deterministic**: All tests pass with seed_base=1337  
✅ **Canonical execution points**: Fighter.attack_d20 orchestrates everything  
✅ **Metrics first-class**: Full scenario harness integration  
✅ **No TurnManager changes**: All logic in Fighter/Equipment  
✅ **Respects Entity.move()**: No bypasses  

---

## H) Future Enhancements

### Potential Ammo Types
- Poison arrows (apply poison effect)
- Ice arrows (apply slow effect)
- Lightning arrows (chain damage to nearby enemies)
- Piercing arrows (ignore armor)

### Potential Features
- Ammo crafting (combine items to create special ammo)
- Quiver upgrade (hold multiple ammo types, switch between them)
- Ammo recovery (chance to retrieve arrows after combat)
- Quiver capacity (different quiver sizes)

---

## I) Known Limitations

1. **Single ammo type**: Quiver holds only one stack at a time
2. **Manual load**: Player must explicitly load/unload (no quick-swap)
3. **No auto-use**: Player decides when to use special ammo vs basic
4. **Burning only**: Currently only fire_arrow implemented (others TODO)

---

## J) Architectural Notes

### Why Not Item Stacking in Quiver?
Quiver holds exactly one stack (entity) at a time. This simplifies:
- Inventory management (no special quiver UI)
- State serialization (standard equipment slot)
- Player decision-making (one ammo type active at a time)

### Why Explicit Tagging vs Reach Heuristic?
Reach-based detection (`reach >= 3`) would incorrectly classify:
- Future long-reach melee weapons (polearms, whips)
- Spells with reach > 3 (if cast through weapon)

Explicit tagging ensures only bows/crossbows trigger quiver consumption.

### Why Consume on Miss?
Realism: Firing an arrow expends it regardless of accuracy. Prevents "save scumming" where players reload on miss to conserve ammo.

---

## K) Testing Strategy

### Unit Tests
- Direct component testing (Fighter, Equipment, Item)
- Mock-based isolation (no full game state)
- Fast execution (< 1 second per test)

### Integration Tests
- Full game state with EntityFactory
- Deterministic seeding (seed_base=1337)
- Multi-turn scenarios (load, fire, deplete, continue)

### Regression Guards
- All existing tests pass (3618/3618)
- Ranged combat doctrine tests updated (explicit tagging)
- No balance suite baseline changes

---

## L) Commit-Ready Checklist

✅ All quiver tests pass (11/11)  
✅ All ranged combat doctrine tests pass (34/34)  
✅ Full fast test suite passes (3618/3618)  
✅ No regressions in existing functionality  
✅ Deterministic behavior verified (seed_base=1337)  
✅ Metrics properly integrated and aggregated  
✅ Documentation complete (this file)  
✅ Code follows project architectural constraints  
✅ Ready for commit  

---

## M) Next Steps (Future Phases)

1. **Phase 22.2.3**: Additional ammo types (poison, ice, lightning)
2. **Phase 22.2.4**: Ammo crafting system
3. **Phase 22.3**: Thrown weapon ammo bookkeeping (if desired)
4. **Phase 22.4**: Quiver upgrades and capacity variations

---

**End of Phase 22.2.2 Implementation Notes**
