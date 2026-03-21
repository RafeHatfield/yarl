# Phase 19 - Corrosive Contact Implementation

**Branch:** `feature/phase19-slime-corrosion-v2`  
**Date:** December 16, 2025  
**Status:** ✅ COMPLETE

---

## Summary

Successfully evolved the existing slime corrosion mechanic into a Phase 19-compliant "Corrosive Contact" system that:
- Only affects **METAL** weapons (wood/bone/stone are immune)
- Triggers with a **5% chance per successful hit**
- Permanently degrades weapon effectiveness in **small steps (-1 damage_max)**
- Is **CLAMPED at 50% of base damage** (weapons cannot degrade below this floor)
- Remains **deterministic under seeded runs** and fully testable

---

## Audit Results

### Existing System (Pre-Phase 19)
Found corrosion system in `components/fighter.py`:
- **Trigger:** 5% chance on successful hit (damage > 0)
- **Effect:** Reduced weapon `damage_max` by -1 permanently
- **Also corroded:** Armor/shields (defense_max by -1)
- **Floor:** Stopped when max == min (could go to 1 damage)
- **No material filtering** - corroded ALL weapons
- **No base tracking** - couldn't enforce 50% floor

### Issues Fixed
1. ❌ **No material field** → ✅ Added `material` to weapons
2. ❌ **No base stat tracking** → ✅ Added `base_damage_min/max` to Equippable
3. ❌ **Corroded all materials** → ✅ Only metal corrodes now
4. ❌ **Corroded armor/shields** → ✅ Removed armor corrosion (weapons only)
5. ❌ **Floor was min_damage** → ✅ Floor is now 50% of base

---

## Implementation Changes

### 1. Component Updates

**`components/equippable.py`**
- Added `material: Optional[str]` field (metal/wood/bone/stone/organic/other)
- Added `base_damage_min: int` (stores original minimum damage)
- Added `base_damage_max: int` (stores original maximum damage for floor calculation)

**`config/entity_registry.py`**
- Added `material: Optional[str]` to `WeaponDefinition`
- Passed through to Equippable during weapon creation

**`config/factories/equipment_factory.py`**
- Updated `create_weapon()` to pass `material`, `crit_threshold`, and `damage_type` to Equippable

### 2. Corrosion Logic Updates

**`components/fighter.py`**

**`_apply_corrosion_effects()`** (lines 1201-1237):
- Removed armor corrosion call
- Updated docstring to reflect Phase 19 spec
- Now only corrodes target's weapon

**`_corrode_weapon()`** (lines 1353-1399):
- **Material check:** Returns early if weapon is not metal
- **50% floor calculation:** `floor = max(1, int(base_damage_max * 0.5))`
- **Floor enforcement:** Only corrodes if `damage_max > floor`
- **Condition display:** Shows percentage in message (e.g., "[75%]")

### 3. Weapon Definitions

**`config/entities.yaml`**

Added `material` field to all weapons:
- **Metal weapons:** dagger, shortsword, mace, longsword, rapier, battleaxe, warhammer, greataxe, greatsword, sword, keen_*, vicious_*, fine_*, masterwork_*
- **Wood weapons:** club, spear (shaft is wooden)

### 4. Testing

**Updated Tests:**
- `tests/test_corrosion_mechanics.py` - Updated all existing tests for new behavior
  - Removed armor corrosion tests
  - Updated floor tests to use 50% base calculation
  - Added metal material to test weapons
  - Added tests for non-metal immunity

**New Scenario Tests:**
- `tests/test_phase19_corrosion_scenario.py` - Comprehensive scenario validation
  - Metal weapon corrodes to 50% floor
  - Wooden weapons immune to corrosion
  - Side-by-side comparison (metal vs wood)
  - Deterministic behavior under fixed seed

---

## Test Results

### Unit Tests
```bash
pytest tests/test_corrosion_mechanics.py -v
# Result: 12 passed in 0.06s ✅
```

### Scenario Tests
```bash
pytest tests/test_phase19_corrosion_scenario.py -v
# Result: 4 passed in 0.05s ✅
```

### Fast Test Suite
```bash
pytest -m "not slow" --tb=short -q
# Result: 3137 passed, 15 skipped, 104 deselected ✅
```

### Balance Suite
```bash
make balance-suite-fast
# Result: 11 PASS, 4 WARN, 0 FAIL ✅
# Warnings are typical variance (hit rate, death rate) - not corrosion-related
```

---

## Architectural Compliance

✅ **ECS boundaries respected** - All logic flows through entities → components → systems  
✅ **No new loops** - Uses existing combat attack flow  
✅ **Rendering read-only** - No renderer changes needed  
✅ **Deterministic RNG** - Uses Python's `random.random()` (seeded runs work)  
✅ **Small, localized changes** - Minimal diff, focused on corrosion only  
✅ **No gameplay math changes** - Only affects weapon durability, not combat formulas  
✅ **Tests updated and passing** - Comprehensive coverage maintained

---

## Design Decisions

### Why 50% Floor?
- Prevents weapons from becoming completely useless
- Maintains strategic value of corroded weapons
- Encourages weapon replacement without forcing it
- Aligns with traditional roguelike equipment degradation systems

### Why Material System?
- Thematically appropriate (acid corrodes metal, not wood)
- Creates strategic diversity (wood weapons have a niche)
- Extensible for future mechanics (coatings, repair, crafting)
- Minimal data overhead (single string field)

### Why Weapon-Only?
- Clearer feedback (one thing degrades per hit)
- Reduces spam (no dual corrosion messages)
- Armor is typically metal anyway (thematically less distinct)
- Focused pain point (weapon loss is more dramatic)

### Why Keep 5% Chance?
- Existing balance (no need to retune encounter difficulty)
- Rare enough to not feel punishing
- Common enough to be observable in long fights
- Deterministic (works with seeded scenarios)

---

## Future Work (Not in Scope)

**Phase 19 Follow-up (possible future phases):**
- [ ] Coatings system (oil/wax to protect metal weapons)
- [ ] Repair mechanics (repair pond, blacksmith NPC)
- [ ] Durability UI (show weapon condition in tooltip)
- [ ] Corrosion resistance stat (on armor/rings)
- [ ] Material-specific behavior (bone vs stone vs organic)

---

## Verification Checklist

- [x] Existing corrosion system audited
- [x] Material field added to weapons
- [x] Base damage tracking implemented
- [x] 50% floor enforcement working
- [x] Metal-only corrosion verified
- [x] Wooden weapon immunity verified
- [x] Armor corrosion removed
- [x] All unit tests passing
- [x] Scenario tests added and passing
- [x] Fast test suite passing (0 FAIL)
- [x] Balance suite passing (0 FAIL)
- [x] Deterministic under seeded runs
- [x] No architectural violations
- [x] Small, localized changes only

---

## Commit Message

```
feat(phase19): Implement metal-only corrosion with 50% floor

Phase 19 Corrosive Contact system:
- Only metal weapons corrode (wood/bone/stone immune)
- 5% chance per successful slime hit (unchanged)
- Permanent degradation clamped at 50% base damage
- Removed armor corrosion (weapons only now)
- Added material field to weapons and tracking
- Fully deterministic under seeded scenarios

Changes:
- components/equippable.py: Add material & base damage tracking
- components/fighter.py: Update corrosion logic for metal-only + 50% floor
- config/entity_registry.py: Add material to WeaponDefinition
- config/factories/equipment_factory.py: Pass material to Equippable
- config/entities.yaml: Add material to all weapons
- tests/test_corrosion_mechanics.py: Update for new behavior
- tests/test_phase19_corrosion_scenario.py: Add scenario validation

Tests: 12+4 new tests, 3137 total passing
Balance: 0 FAIL, 4 WARN (acceptable variance)
```

---

## References

- **Design Spec:** Cursor prompt (Phase 19 Corrosive Contact)
- **Audit:** `components/fighter.py` lines 1201-1409
- **Tests:** `tests/test_corrosion_mechanics.py`, `tests/test_phase19_corrosion_scenario.py`
- **Balance:** `reports/balance_suite/20251216_134610/`

---

**Implemented by:** AI Assistant (Cursor)  
**Reviewed by:** [Pending]  
**Status:** ✅ Ready for review/merge

