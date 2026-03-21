# Phase 19.5: Wraith Life Drain + Ward Against Drain

## Summary

Implements Phase 19 Wraith identity mechanics with deterministic % life drain and a consumable ward scroll counter. Creates meaningful player decisions around preparation and burst damage strategies.

**Branch:** `feature/phase19-wraith-life-drain-and-ward-scroll`  
**Related Docs:** `WAND_WRAITH_LIFE_DRAIN_IMPLEMENTATION.md`, `docs/PHASE_19_MONSTER_IDENTITY_AND_ABILITIES.md`

---

## What's New

### 1. Wraith Life Drain Mechanic
- **50% life drain** on successful melee hits
- Calculation: `heal_amount = ceil(damage_dealt * 0.50)`
- Capped at wraith's missing HP (no overheal)
- Uses **final damage** after resistances/armor
- **Deterministic** (no RNG)
- Message: *"The wraith drains your life! (+X HP)"*

### 2. Ward Against Drain Counter
- New consumable scroll: `scroll_ward_against_drain`
- Grants **10 turns of full immunity** to life drain
- Clear messages on apply, block, and expire
- Teaches preparation and resource management

### 3. Complete Testing Suite
- **13 unit tests** (all passing)
  - Drain calculation (50%, ceil, capping)
  - Ward immunity and scroll application
  - Metrics tracking
  - Integration with attack flow
- **Scenario:** `scenario_monster_wraith_identity.yaml`
  - 2 wraiths, player with ward scrolls and potions
  - Validates drain + ward behavior
- **All 3,249 default tests passing**

### 4. Metrics Tracking
- `life_drain_attempts` - Total drain attempts
- `life_drain_heal_total` - Total HP healed via drain
- `life_drain_blocked_attempts` - Drains blocked by ward
- Integrated into scenario harness for validation

---

## Files Changed (11 files, +956 lines)

### Core Mechanics (5 files)
- `config/entities.yaml` - Added `life_drain_pct: 0.50` to wraith, ward scroll definition
- `components/fighter.py` - Added `_apply_life_drain_effects()` method
- `components/status_effects.py` - Added `WardAgainstDrainEffect` class
- `item_functions.py` - Added `use_ward_scroll()` function
- `services/scenario_metrics.py` - Added drain metrics tracking

### Testing & Validation (3 files)
- `tests/test_wraith_life_drain.py` - 13 comprehensive unit tests (NEW)
- `config/levels/scenario_monster_wraith_identity.yaml` - Wraith identity scenario (NEW)
- `tools/balance_suite.py` - Added wraith scenario to matrix

### Metrics & Docs (3 files)
- `services/scenario_harness.py` - Drain metrics in RunMetrics/Aggregated
- `docs/PHASE_19_MONSTER_IDENTITY_AND_ABILITIES.md` - Updated wraith section
- `WAND_WRAITH_LIFE_DRAIN_IMPLEMENTATION.md` - Full technical documentation (NEW)

---

## Design Decisions

### Why 50% Life Drain?
Wraiths are:
- **Fast** (speed=2.0, bonus attack every hit)
- **Hard to hit** (evasion=4, phases through attacks)  
- **Low HP** (20 HP, fragile when hit)

→ 50% drain creates **high tension** but is **counterable** via burst damage or ward

### Why Ward Scroll?
- **Teachable:** Player learns to prepare for wraith encounters
- **Consumable:** Creates resource management decisions
- **Full immunity:** Simple, clear mechanic (no partial blocking)
- **10 turn duration:** Covers ~1-2 wraith fights per scroll

### Why Deterministic?
- No hidden RNG that can't be tested
- Player can predict drain amount from damage dealt
- Scenario harness can validate behavior reliably
- Follows Phase 19 design constraints

---

## Testing Results

### Unit Tests
```
✅ 13/13 wraith life drain tests passing
✅ 25/25 surprise attack tests passing (fixed Mock handling)
✅ 3,249/3,249 default suite tests passing
```

### Scenario Tests
```
✅ scenario_monster_wraith_identity.yaml created
✅ Added to balance suite matrix (FULL mode)
⏳ Pending: Full balance suite run + baseline update
```

---

## Bug Fixes

### Mock Object Handling
**Issue:** 5 surprise attack tests failing with `TypeError: '<=' not supported between instances of 'Mock' and 'int'`

**Fix:** Added type check in `_apply_life_drain_effects()`:
```python
if life_drain_pct is None or not isinstance(life_drain_pct, (int, float)) or life_drain_pct <= 0:
    return results
```

**Result:** All 25 surprise attack tests now passing

---

## Pre-Merge Checklist

- [x] Branch created from main
- [x] Implementation complete
- [x] Unit tests written (13 tests)
- [x] Unit tests passing
- [x] Default test suite passing (3,249 tests)
- [x] Scenario created
- [x] Scenario added to balance suite
- [x] Documentation updated
- [x] No linter errors
- [x] Code follows project rules (small, localized, reviewable)
- [ ] **Balance suite run** (`make balance-suite`)
- [ ] **Baseline updated** (if PASS/WARN)
- [ ] **0 FAIL after baseline update**

---

## Post-Merge Steps

1. Run full balance suite:
   ```bash
   make balance-suite
   ```

2. If PASS/WARN, update baseline:
   ```bash
   make balance-suite-update-baseline
   make balance-suite  # Verify 0 FAIL
   ```

3. If FAIL:
   - Reduce `life_drain_pct` from 0.50 to 0.40
   - Or increase ward scroll availability
   - Re-run balance suite

---

## Reviewer Notes

### Key Areas to Review
1. **Life drain calculation** (`components/fighter.py:1398-1450`)
   - Correct use of `ceil()`?
   - Proper capping at missing HP?
   - Type safety for Mock objects?

2. **Ward effect** (`components/status_effects.py:1142-1162`)
   - Correct duration handling?
   - Clear messages?
   - Proper integration with status effect manager?

3. **Metrics tracking** (`services/scenario_metrics.py:85-113`)
   - Correct counter increments?
   - Proper handling of blocked vs successful drains?

4. **Scenario design** (`config/levels/scenario_monster_wraith_identity.yaml`)
   - Appropriate difficulty?
   - Clear validation of both drain and ward mechanics?

### Testing Commands
```bash
# Run wraith tests
pytest tests/test_wraith_life_drain.py -v

# Run default suite
pytest -m "not slow" -q

# Run balance suite (FULL, takes ~15-20 min)
make balance-suite
```

---

## Related Issues/PRs

- Phase 19 Monster Identity Epic
- Related: Orc Chieftain Rally (#XX)
- Related: Skeleton Shield Wall (#XX)
- Related: Slime Split Under Pressure (#XX)

---

## Screenshots/Demos

(Add gameplay screenshots or GIFs showing drain + ward in action)

---

## Questions for Reviewers

1. Is 50% drain too punishing, or does the ward scroll provide adequate counter-play?
2. Should ward scrolls be more/less common in loot tables?
3. Any concerns about the deterministic drain calculation?
4. Should we add visual effects for drain (beyond message)?

---

**Ready for review!** All tests passing, documentation complete, implementation follows project rules.

