# Phase 19.5: Wraith Life Drain + Ward Against Drain Implementation

**Branch:** `feature/phase19-wraith-life-drain-and-ward-scroll`  
**Date:** 2025-12-20  
**Status:** ✅ COMPLETE (pending balance suite baseline update)

---

## Summary

Implemented Phase 19 Wraith identity mechanics:
1. **Life Drain:** Wraiths heal for 50% of damage dealt (deterministic, capped at missing HP)
2. **Ward Against Drain:** Consumable scroll that grants 10-turn immunity to life drain
3. **Complete test coverage:** 13 unit tests, all passing
4. **Scenario validation:** `scenario_monster_wraith_identity.yaml` for balance suite
5. **Metrics tracking:** drain attempts, heals, and blocks

---

## Implementation Details

### 1. Life Drain Mechanic

**File:** `components/fighter.py`  
**Method:** `_apply_life_drain_effects(target, damage_dealt)`

```python
# Calculate drain amount: ceil(damage * drain_pct)
drain_amount = ceil(damage_dealt * life_drain_pct)

# Cap at missing HP (no overheal)
drain_amount = min(drain_amount, attacker.max_hp - attacker.hp)

# Heal attacker if drain_amount > 0
attacker.hp += drain_amount
```

**Integration Point:**
- Called from `Fighter.attack_d20()` after damage is applied
- Uses final damage dealt (after resistances/armor)
- Only applies if `entity.life_drain_pct` attribute exists and `damage_dealt > 0`

**Config:**
- Added `life_drain_pct: 0.50` to wraith definition in `config/entities.yaml`

---

### 2. Ward Against Drain Counter

**Status Effect:** `WardAgainstDrainEffect`  
**File:** `components/status_effects.py`

- Duration: 10 turns (configurable via scroll)
- Blocks all life drain healing while active
- Emits message on apply: "A pale ward surrounds you, repelling life drain!"
- Emits message on drain block: "The ward repels the drain!"
- Emits message on expire: "The ward against drain fades away."

**Consumable Scroll:** `scroll_ward_against_drain`  
**File:** `config/entities.yaml` + `item_functions.py`

- Spell type: utility
- Color: Pale silvery-blue (200, 220, 255)
- Effect function: `use_ward_scroll()`
- Applies `WardAgainstDrainEffect` to caster for 10 turns
- One-time use (consumed on activation)

---

### 3. Metrics Tracking

**Files:** `services/scenario_metrics.py`, `services/scenario_harness.py`

Added three metrics for wraith drain validation:
- `life_drain_attempts`: Total wraith hits that attempted drain
- `life_drain_heal_total`: Total HP healed by wraiths via drain
- `life_drain_blocked_attempts`: Drain attempts blocked by ward effect

Metrics are:
- Collected per-run in `RunMetrics`
- Aggregated across runs in `AggregatedMetrics`
- Recorded in `ScenarioMetricsCollector.record_life_drain_attempt()`
- Called from `Fighter._apply_life_drain_effects()` for both successful and blocked drains

---

### 4. Scenario Validation

**File:** `config/levels/scenario_monster_wraith_identity.yaml`

**Setup:**
- 2 wraiths in 13x13 arena
- Player starts with:
  - Dagger (weak weapon to ensure wraiths survive and drain)
  - 2 ward scrolls (test drain immunity)
  - 3 healing potions (sustain combat)
  - 1 longsword (weapon upgrade option)

**Expected Behavior:**
- Wraiths drain life and heal themselves when ward is not active
- Ward blocks drain completely when active (message displayed)
- Bot should use ward scrolls tactically when fighting wraiths

**Metrics Assertions:**
- `drain_attempts >= 30` (at least 1 per run across 30 runs)
- `blocked_attempts >= 5` (ward used in some runs)
- `heal_total > 0` (drain works without ward)

**Added to Balance Suite:**
- File: `tools/balance_suite.py`
- Entry: `{"id": "monster_wraith_identity", "runs": 30, "turn_limit": 200}`
- Included in FULL balance suite (not fast mode)

---

### 5. Unit Tests

**File:** `tests/test_wraith_life_drain.py`

**13 tests, all passing:**

**TestLifeDrainMechanics (6 tests):**
- ✅ `test_life_drain_heals_50_percent_of_damage`
- ✅ `test_life_drain_uses_ceil`
- ✅ `test_life_drain_caps_at_missing_hp`
- ✅ `test_life_drain_does_not_apply_when_damage_zero`
- ✅ `test_life_drain_does_not_apply_when_full_hp`
- ✅ `test_life_drain_does_not_apply_without_life_drain_pct`

**TestWardAgainstDrain (4 tests):**
- ✅ `test_ward_blocks_life_drain_completely`
- ✅ `test_ward_scroll_applies_effect`
- ✅ `test_ward_effect_applies_and_removes_messages`
- ✅ `test_life_drain_works_without_ward`

**TestLifeDrainMetrics (2 tests):**
- ✅ `test_metrics_recorded_on_successful_drain`
- ✅ `test_metrics_recorded_on_blocked_drain`

**TestLifeDrainIntegration (1 test):**
- ✅ `test_life_drain_in_attack_d20_flow`

---

## Files Changed

### Core Mechanics
- `config/entities.yaml` - Added `life_drain_pct` to wraith, added ward scroll
- `components/fighter.py` - Added `_apply_life_drain_effects()` method
- `components/status_effects.py` - Added `WardAgainstDrainEffect` class
- `item_functions.py` - Added `use_ward_scroll()` function

### Scenario & Metrics
- `config/levels/scenario_monster_wraith_identity.yaml` - New scenario
- `services/scenario_metrics.py` - Added drain metrics tracking
- `services/scenario_harness.py` - Added drain metrics to RunMetrics/AggregatedMetrics
- `tools/balance_suite.py` - Added wraith scenario to matrix

### Documentation & Tests
- `docs/PHASE_19_MONSTER_IDENTITY_AND_ABILITIES.md` - Wraith section complete
- `tests/test_wraith_life_drain.py` - New unit tests (13 tests, all passing)

---

## Design Decisions

### 1. Why 50% Life Drain?
- Wraiths are **fast** (speed=2.0, bonus attack every hit)
- Wraiths are **hard to hit** (evasion=4, phases through attacks)
- Wraiths are **low HP** (20 HP, fragile when hit)
- 50% drain creates **high tension** but is **deterministic** and **counterable**
- Encourages burst damage strategy (kill fast before drain adds up)

### 2. Why Ward Scroll?
- **Teachable:** Player learns to prepare for wraith encounters
- **Consumable:** Creates resource management decision
- **Full immunity:** Simple, clear mechanic (no partial blocking)
- **10 turn duration:** Covers ~1-2 wraith fights per scroll
- **Deterministic:** No RNG, works every time

### 3. Why Ceil for Drain Amount?
- Ensures drain is always meaningful (no fractional HP loss)
- Matches existing damage rounding conventions
- Example: 7 damage → ceil(7 * 0.5) = 4 HP healed (not 3.5)

### 4. Why Cap at Missing HP?
- Prevents overheal (wraith can't exceed max HP)
- Keeps drain "fair" (wraith at full HP doesn't waste drain)
- Follows existing healing conventions

---

## Testing Strategy

### Unit Tests (Completed)
- ✅ Drain calculation (50%, ceil, capping)
- ✅ Ward blocks drain completely
- ✅ Scroll application and removal
- ✅ Metrics tracking
- ✅ Integration with attack_d20 flow

### Scenario Tests (Completed)
- ✅ Wraith identity scenario created
- ✅ Added to balance suite matrix
- ⏳ **Pending:** Run `make balance-suite` to generate baseline

### Integration Tests (Pending)
- ⏳ Run full balance suite (`make balance-suite`)
- ⏳ Update baseline if PASS/WARN (`make balance-suite-update-baseline`)
- ⏳ Verify 0 FAIL after baseline update

---

## Balance Validation (Next Steps)

### Step 1: Run Balance Suite
```bash
make balance-suite
```

Expected outcomes:
- **PASS:** Ship immediately
- **WARN:** Expected for new ability, review drift magnitude
- **FAIL:** Tune down drain_pct or increase ward availability

### Step 2: Update Baseline (if PASS/WARN)
```bash
make balance-suite-update-baseline
make balance-suite  # Verify 0 FAIL
```

### Step 3: Commit
```bash
git add .
git commit -m "Phase 19.5: Wraith Life Drain + Ward Against Drain

- Life drain: 50% of damage dealt, capped at missing HP
- Ward scroll: 10-turn immunity to life drain
- 13 unit tests (all passing)
- Scenario: scenario_monster_wraith_identity.yaml
- Metrics: drain attempts, heals, blocks
- Added to balance suite matrix"
```

---

## Success Criteria

### ✅ Completed
- [x] Life drain heals wraith deterministically (50% of damage dealt)
- [x] Drain capped at missing HP (no overheal)
- [x] Ward scroll grants full immunity for 10 turns
- [x] Metrics tracking for drain attempts, heals, and blocks
- [x] 13 unit tests (all passing)
- [x] Scenario created and added to balance suite
- [x] Documentation updated (PHASE_19_MONSTER_IDENTITY_AND_ABILITIES.md)

### ⏳ Pending
- [ ] Run `make balance-suite` (full run)
- [ ] Update baseline if needed (`make balance-suite-update-baseline`)
- [ ] Verify 0 FAIL after baseline update
- [ ] Final commit to branch

---

## References

- **Prompt:** START CURSOR PROMPT in chat history
- **Documentation:** `docs/PHASE_19_MONSTER_IDENTITY_AND_ABILITIES.md`
- **Scenario:** `config/levels/scenario_monster_wraith_identity.yaml`
- **Unit Tests:** `tests/test_wraith_life_drain.py`
- **Balance Suite:** `tools/balance_suite.py`

---

## Notes

- All changes follow project rules: small, localized, reviewable
- No global combat math changes
- No changes to other monsters or balance
- Deterministic only (no RNG except weighted child count, which uses seed)
- Respects IO boundary (no renderer changes needed)
- Tests pass without flakiness

## Bug Fixes

### Mock Object Handling in Tests
**Issue:** Surprise attack tests were failing with `TypeError: '<=' not supported between instances of 'Mock' and 'int'`

**Root Cause:** In test scenarios, `getattr(self.owner, 'life_drain_pct', None)` returns a Mock object instead of None, causing the comparison `life_drain_pct <= 0` to fail.

**Fix:** Added type check before numeric comparison:
```python
# Before:
if life_drain_pct is None or life_drain_pct <= 0:
    return results

# After:
if life_drain_pct is None or not isinstance(life_drain_pct, (int, float)) or life_drain_pct <= 0:
    return results
```

**Validation:** All 25 surprise attack tests now pass + 3249 total tests passing in default suite


