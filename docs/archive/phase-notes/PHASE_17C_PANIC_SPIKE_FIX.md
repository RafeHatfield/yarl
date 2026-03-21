# Phase 17C: Panic Damage Spike Fix

**Date**: 2025-12-13  
**Branch**: `feature/phase17c-threshold-fix`  
**Status**: ✅ Fixed

## Critical Bug in Panic Logic

### Symptoms
Bot healing at extremely high HP (median 76.8%):
```
HP% at heal: mean 73.1% (P25 64.3%, P50 76.8%, P75 87.1%)
```

### Root Cause

**Panic Condition 2 had no HP check:**

```python
# BUGGY CODE:
if last_damage > fighter.max_hp * 0.12:  # 12% spike
    return True  # Panic regardless of current HP!
```

**What Happened:**
1. Player at 80% HP
2. Takes 13 damage (13% of max HP)
3. Panic triggers because spike > 12%
4. Bot heals at 80% HP ❌

**The Problem**: Damage spike panic had **no current HP requirement**, so bot panicked and healed at high HP after taking a single moderate hit.

## Solution

### Added HP Requirement to Spike Panic

```python
# FIXED CODE:
if hp_fraction <= 0.50 and last_damage > fighter.max_hp * 0.20:
    return True  # Only panic on spike if at moderate/low HP
```

**Changes:**
1. Added `hp_fraction <= 0.50` requirement (must be at ≤50% HP)
2. Raised spike threshold from 12% → 20% (more significant damage required)

**Rationale:**
- At 80% HP, taking 15% damage is not an emergency
- At 40% HP, taking 20% damage IS an emergency (could be fatal)
- Spike panic should be for "burst damage while vulnerable", not "any hit at any HP"

## Impact

### Before Fix
```
Panic triggers at: 80% HP (on 13% damage spike)
Heal HP% median: 76.8%
Result: Wasted potions at high HP
```

### After Fix
```
Panic triggers at: ≤50% HP AND 20%+ damage spike
Heal HP% median: ~28-32% (expected)
Result: Efficient potion use
```

## Panic Logic Summary (Corrected)

Panic triggers when **ANY** of these conditions are met:

1. **Low HP + Adjacent Enemy**:
   ```python
   if hp <= panic_threshold AND adjacent_enemies >= 1:
       return True
   ```

2. **Damage Spike at Moderate HP** (FIXED):
   ```python
   if hp <= 0.50 AND last_damage > 20% max_hp:
       return True
   ```

3. **Emergency HP**:
   ```python
   if hp <= emergency_threshold (10% for balanced):
       return True
   ```

All three now have appropriate HP requirements.

## Test Results

```bash
pytest tests/test_bot*.py -m "not slow" -q
# ✅ 207 passed, 15 skipped in 0.77s
```

All tests passing - no regressions.

## Files Modified

**`io_layer/bot_brain.py`:**
- `_is_panic_state()` Condition 2: Added `hp_fraction <= 0.50` requirement
- Raised spike threshold from 12% → 20% for more significant damage

## Expected Impact on Soak Runs

| Metric | Before (Buggy) | After (Fixed) |
|--------|----------------|---------------|
| Heal HP% P50 | 76.8% | ~28-32% |
| Heal HP% P25 | 64.3% | ~22-28% |
| Panic heal rate | ~60-80% of heals | ~10-20% of heals |
| Threshold heal rate | ~20-40% of heals | ~80-90% of heals |

## Conclusion

The damage spike panic condition was triggering at high HP, causing early healing. Fixed by requiring **moderate HP (≤50%)** for spike panic to trigger.

**Status**: ✅ **Fixed** - Bot should now heal at designed thresholds (25-35% HP).

---

**All Phase 17B/17C Fixes Complete:**
1. ✅ Combat healing enabled
2. ✅ Decision priority (heal before attack)  
3. ✅ Potions in starting inventory
4. ✅ Full HP infinite loop guard
5. ✅ Adaptive threshold disabled (inverted logic)
6. ✅ Panic spike requires moderate HP (THIS FIX)

**Ready for final soak validation!**
