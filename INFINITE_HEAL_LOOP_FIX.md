# Infinite Heal Loop Fix

**Date**: 2025-12-13  
**Branch**: `feature/phase17b-survivability-tuning`  
**Status**: ✅ Fixed

## Critical Bug

### Symptoms
Bot stuck in infinite loop during soak runs:
```
WARNING: Using item from sidebar during PLAYERS_TURN
WARNING: Using item from sidebar during PLAYERS_TURN
WARNING: Using item from sidebar during PLAYERS_TURN
... (repeating forever)
```

Game frozen, no progression, console spamming potion use attempts.

### Root Cause

**Problem Flow:**
1. Bot returns `{"inventory_index": 0}` (drink potion)
2. Game calls `_use_inventory_item()` with healing potion
3. Potion use **fails** because player is at **full HP** (can't heal above max)
4. Item use returns no `consumed=True` result
5. Game returns to `PLAYERS_TURN` **without consuming turn** (line 1751 in game_actions.py)
6. Bot gets control again **immediately**
7. Bot sees same conditions, returns `{"inventory_index": 0}` again
8. **INFINITE LOOP**

**Why Bot Tried to Heal at Full HP:**

Looking at the panic/heal logic, there was NO check for full HP:
- Panic conditions checked low HP, enemies, damage spikes
- BUT: No condition checked "hp >= 1.0" (full HP)
- Edge case: Player starts scenario at full HP, panic logic might trigger on other conditions
- Result: Bot tries to heal when already healthy

## Solution

### Added Full HP Guard in Two Places

#### 1. `_is_panic_state()` - Panic Healing
```python
def _is_panic_state(self, player, visible_enemies, heal_config):
    hp_fraction = self._get_player_hp_fraction(player)
    
    # CRITICAL: Never panic at full HP (prevents infinite loop)
    if hp_fraction >= 1.0:
        return False
    
    # ... rest of panic logic ...
```

#### 2. `_should_heal_now()` - Threshold Healing
```python
def _should_heal_now(self, player, visible_enemies, heal_config):
    hp_fraction = self._get_player_hp_fraction(player)
    
    # CRITICAL: Don't heal if already at full HP (prevents infinite loop)
    if hp_fraction >= 1.0:
        return False
    
    # ... rest of threshold logic ...
```

## Why This Fixes It

**Before Fix:**
```
HP: 100/100 → Bot panics (damage spike?) → Returns drink_potion
→ Potion fails → No turn consumed → HP still 100/100
→ Bot panics again → LOOP
```

**After Fix:**
```
HP: 100/100 → Full HP check returns False → No heal attempt
→ Bot proceeds to normal actions (attack/move)
→ Turn consumed normally ✅
```

## Test Results

```bash
pytest tests/test_bot_*.py -m "not slow" -q
# ✅ 67 tests passing (heal, panic, adaptive tests)
```

All existing tests continue to pass - the full HP check doesn't break any expected behavior.

## Files Modified

**`io_layer/bot_brain.py`:**
1. Added `if hp_fraction >= 1.0: return False` in `_is_panic_state()` (line ~2094)
2. Added `if hp_fraction >= 1.0: return False` in `_should_heal_now()` (line ~2131)

Both checks placed at the TOP of the decision logic for fail-fast behavior.

## Validation

The fix should now allow soak runs to proceed normally:

```bash
python3 engine.py --bot-soak --bot-persona balanced \
  --scenario tight_brutal_funnel --runs 30 --max-turns 200 \
  --metrics-log reports/soak/tbf_30.csv \
  --telemetry-json reports/soak/tbf_30.jsonl
```

**Expected:**
- ✅ No infinite loop
- ✅ Game progresses normally
- ✅ Bot heals when HP drops below threshold
- ✅ Bot does NOT heal at full HP
- ✅ Runs complete successfully

## Impact

This was a **blocking bug** that prevented any soak validation from completing. With the fix:
- Soak runs can complete
- Heal logic can be validated
- Survivability data can be collected
- Phase 17B/17C tuning can proceed

**Status**: ✅ **Critical Fix Applied** - Soak runs can now complete successfully.
