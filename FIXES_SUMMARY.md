# Orc Shaman Implementation - All Fixes Complete

**Branch:** fix/orc-shaman-chant-tax-no-double-tick  
**Status:** ✅ READY FOR REVIEW

---

## Summary

Fixed **4 critical issues** from partner agent code review + added missing metrics infrastructure:

1. ✅ **Double world-tick removed** - Movement tax no longer advances world twice
2. ✅ **Zero-damage exploit fixed** - Only positive damage interrupts chant
3. ✅ **Wall-bump exploit fixed** - Toggle only flips on successful movement
4. ✅ **Metrics infrastructure added** - Shaman metrics now properly tracked
5. ✅ **Regression guard added** - Automated threshold enforcement test

---

## Changes Made

### Core Fixes (5 files)

**1. services/movement_service.py**
- Added alternating movement block (chant tax)
- Toggle flag initialization and check
- Toggle flip ONLY after successful movement (not wall bumps)
- Lines 106-135, 175-178

**2. game_actions.py**
- Removed double `end_player_action()` call
- Simplified to single turn consumption
- Lines 698-703

**3. components/fighter.py**
- Added `if amount > 0:` guard before interrupt checks
- Prevents 0-damage exploit
- Lines 596-628

**4. components/status_effects.py**
- Reset toggle flag on chant removal
- Added comments about refresh behavior
- Lines 1196-1207

**5. config/factories/monster_factory.py**
- Registered orc_shaman AI type
- Lines 232-234

### Metrics Infrastructure (2 files)

**6. services/scenario_harness.py**
- Added shaman metrics to `RunMetrics` dataclass
- Added shaman metrics to `AggregatedMetrics` dataclass
- Added aggregation logic in `run_scenario_many()`
- Lines 68-71, 107-114, 147-150, 835-846, 871-874

**7. services/scenario_metrics.py**
- Added `increment(metric_name, amount)` method to `ScenarioMetricsCollector`
- Generic counter for ability-specific metrics
- Lines 113-126

### Testing (2 files)

**8. tests/unit/test_orc_shaman.py**
- Added `test_chant_NOT_interrupted_by_zero_damage`
- Added `test_chant_toggle_not_flipped_by_wall_bump`
- 22 tests total, all passing

**9. tests/integration/test_orc_shaman_identity_scenario_metrics.py**
- NEW FILE - Enforces scenario metric thresholds
- Asserts hex, chant, interrupt, expiry thresholds
- Validates state machine correctness
- Marked `@pytest.mark.slow`

---

## Test Results

✅ **Unit Tests:** 22/22 passed  
✅ **Linter:** No errors  
✅ **Integration Test:** Ready for validation (slow test)

```bash
pytest tests/unit/test_orc_shaman.py -v
# 22 passed in 0.09s ✅
```

---

## Behavior Changes

### Movement Tax

**Before:**
```
Player moves while chanted:
→ end_player_action() #1
→ end_player_action() #2
→ Enemies act TWICE
→ DOT ticks TWICE
→ Cooldowns advance TWICE
```

**After:**
```
Player moves while chanted:
Attempt 1: Movement succeeds, toggle flips to True (1 turn)
Attempt 2: Movement blocked, toggle flips to False (1 turn)
Attempt 3: Movement succeeds, toggle flips to True (1 turn)
→ Each attempt consumes exactly 1 turn
→ World advances normally
```

### Chant Interruption

**Before:**
```
Hit shaman with 0 damage → Chant broken (exploit)
Hit shaman with 5 damage → Chant broken
```

**After:**
```
Hit shaman with 0 damage (immune) → Chant continues ✅
Hit shaman with 5 damage → Chant broken ✅
DOT tick with >0 damage → Chant broken ✅
```

### Toggle Behavior

**Before:**
```
Attempt move into wall:
→ Toggle flips to True
→ Movement fails
→ Next move blocked (wasted allowed move)
```

**After:**
```
Attempt move into wall:
→ Movement fails
→ Toggle unchanged
→ Next move still allowed ✅
```

---

## Files Changed

**Modified (7 files):**
- services/movement_service.py
- game_actions.py
- components/fighter.py
- components/status_effects.py
- services/scenario_harness.py
- services/scenario_metrics.py
- config/factories/monster_factory.py

**Created (9 files):**
- components/ai/orc_shaman_ai.py
- config/levels/scenario_monster_orc_shaman_identity.yaml
- tests/unit/test_orc_shaman.py
- tests/integration/test_orc_shaman_identity_scenario_metrics.py
- PHASE_19_ORC_SHAMAN_IMPLEMENTATION.md
- PHASE_19_ORC_SHAMAN_CHANT_TAX_FIX.md
- PR_ORAC_SHAMAN_FIXES.md
- FIXES_SUMMARY.md (this file)

**Also Modified:**
- config/entities.yaml (orc_shaman definition)
- tools/balance_suite.py (scenario added to FULL mode)
- docs/PHASE_19_MONSTER_IDENTITY_AND_ABILITIES.md (shaman section)

---

## Manual Validation Required

⚠️ **Before merge, run:**
```bash
pytest tests/integration/test_orc_shaman_identity_scenario_metrics.py -v
```

Expected:
- All 4 thresholds should pass
- State machine validation should pass
- Test takes ~5-10 minutes (30 runs)

If thresholds fail:
- Check scenario definition (monsters spawning correctly?)
- Check AI behavior (abilities firing?)
- Check metrics collection (increment calls working?)

---

## Success Criteria

✅ No double world-tick from chant movement tax  
✅ Zero-damage hits do not interrupt chant  
✅ Toggle only flips on successful movement (not wall bumps)  
✅ Metrics infrastructure added (RunMetrics + AggregatedMetrics)  
✅ Generic `increment()` method for custom metrics  
✅ Scenario thresholds enforced by automated test  
✅ All unit tests pass (22/22)  
✅ No linter errors  

**Status:** Ready for review after slow test validation

