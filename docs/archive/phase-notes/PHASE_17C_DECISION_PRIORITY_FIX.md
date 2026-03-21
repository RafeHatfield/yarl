# Phase 17C: Decision Priority Fix

**Date**: 2025-12-13  
**Branch**: `feature/phase17c-decision-priority`  
**Status**: ✅ Complete

## Problem Statement

After Phase 17B implementation, soak testing revealed a critical issue:
- **119/119 deaths** had **UNUSED potions** (100% waste rate)
- Only **1 heal event** occurred across 120+ lethal runs
- Panic logic never triggered despite dangerous situations
- Bot consistently attacked instead of healing at low HP

### Root Cause
The healing logic was **correct** but **buried in the decision hierarchy**:
1. Healing check happened early (lines 364-393)
2. BUT: If heal check returned false, execution continued
3. State machine transitions happened (EXPLORE → COMBAT)
4. `_handle_combat()` returned attack/move actions
5. These combat actions **overrode** the healing decision

**Result**: Bot would check healing, decide not to heal, then attack and die with full potion inventory.

---

## Solution: Unified Decision Pipeline

### New Priority Order (STRICT)

```
PRIORITY 1: PANIC HEAL
  ↓ (if no panic)
PRIORITY 2: THRESHOLD HEAL  
  ↓ (if no heal needed)
PRIORITY 3: RETREAT (no potion + dangerous)
  ↓ (if no retreat needed)
PRIORITY 4-N: Combat/Explore/Loot (state machine)
```

### Key Changes

#### 1. **Absolute Priority for Healing**
```python
# OLD (Phase 17B):
if self._should_drink_potion(player, visible_enemies):
    return drink_potion()
# ... execution continues if false ...
# ... later: _handle_combat() returns attack action ...

# NEW (Phase 17C):
# PRIORITY 1: PANIC HEAL - always first
if has_potion and self._is_panic_state(...):
    return drink_potion()  # HARD RETURN

# PRIORITY 2: THRESHOLD HEAL - before combat
if has_potion and self._should_drink_potion(...):
    return drink_potion()  # HARD RETURN

# PRIORITY 3: RETREAT
if not has_potion and self._should_retreat(...):
    return retreat_action()  # HARD RETURN

# PRIORITY 4-N: Only reached if healing/retreat not needed
action = self._handle_combat(...)  # Now can't override healing
```

#### 2. **Strengthened Panic Logic**

**OLD Panic Triggers** (Phase 17B):
- HP ≤ panic_threshold AND 2+ adjacent enemies

**NEW Panic Triggers** (Phase 17C - ANY of these):
1. HP ≤ panic_threshold AND **ANY** adjacent enemy (lowered from 2+)
2. Recent damage spike > 12% max HP (burst damage detection)
3. HP ≤ emergency_threshold (67% of panic threshold, e.g., 10% for balanced)

**Rationale**: In lethal scenarios, waiting for 2+ enemies is often too late. One adjacent enemy at 15% HP is already critical.

#### 3. **Simplified Threshold Healing**

Removed duplicate panic check from `_should_heal_now()`:
- Panic handled separately in decision pipeline
- `_should_heal_now()` only checks HP threshold + combat healing flag
- Cleaner separation of concerns

---

## Implementation Details

### Files Modified

**`io_layer/bot_brain.py`:**

1. **Decision Pipeline** (lines ~362-415):
   - Restructured to strict priority order
   - Hard returns prevent override
   - Clear comments explaining priority

2. **`_is_panic_state()`** (strengthened):
   ```python
   # Condition 1: Low HP + ANY adjacent enemy
   if hp <= panic_threshold and adjacent_count >= 1:
       return True
   
   # Condition 2: Damage spike
   if last_damage > max_hp * 0.12:
       return True
   
   # Condition 3: Emergency HP
   if hp <= (panic_threshold * 0.67):
       return True
   ```

3. **`_should_heal_now()`** (simplified):
   - Removed panic check (handled separately)
   - Only checks: HP > threshold? Combat allowed?
   - Cleaner logic, no duplication

**`tests/test_bot_personas.py`:**
- Updated 2 panic tests to reflect strengthened logic
- Tests now expect panic with 1 adjacent enemy (correct behavior)

---

## Test Results

### Unit Tests
```bash
pytest tests/test_bot_*.py -m "not slow" -q
# ✅ 67 passed in 0.18s
```

**All test suites passing:**
- Persona configuration (27 tests)
- Potion drinking (10 tests)
- Combat healing (11 tests)
- Adaptive healing (19 tests)

### Strengthened Tests
- ✅ Panic triggers with 1 adjacent enemy at low HP
- ✅ Panic triggers on damage spikes
- ✅ Threshold healing occurs before combat
- ✅ All personas have combat healing enabled

---

## Expected Impact

### Before Phase 17C (Decision Priority Fix)
```
Deaths: 119/119
Unused potions: 119/119 (100%)
Heal events: 1 total
Panic triggers: 0
Heal HP% median: N/A (not healing)
```

### After Phase 17C (Target)
```
Deaths: 40-80/120 (scenario-dependent)
Unused potions: 5-10% (efficient use)
Heal events: 50-80+ per run
Panic triggers: 10-20% of combat encounters
Heal HP% median: 25-30%
```

### Specific Improvements

1. **Healing Priority**: Healing now **guaranteed** to execute before combat actions
2. **Panic Reliability**: 3 trigger conditions instead of 1 (more responsive)
3. **Potion Efficiency**: Bot will use potions instead of dying with full inventory
4. **Survivability**: Death rates should drop from 100% to 40-80% in lethal scenarios

---

## Decision Flow Diagram

```
┌─────────────────────────────────────┐
│  decide_action() called             │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  Get player, enemies, potions       │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  PRIORITY 1: Panic state?           │
│  (low HP + enemy OR spike OR        │
│   emergency HP)                     │
└─────────────┬───────────────────────┘
              │
       YES ───┼──→ DRINK POTION ──→ RETURN
              │
        NO    ▼
┌─────────────────────────────────────┐
│  PRIORITY 2: HP ≤ threshold?        │
│  (30% for balanced + adaptive)      │
└─────────────┬───────────────────────┘
              │
       YES ───┼──→ DRINK POTION ──→ RETURN
              │
        NO    ▼
┌─────────────────────────────────────┐
│  PRIORITY 3: Should retreat?        │
│  (no potion + low HP + danger)      │
└─────────────┬───────────────────────┘
              │
       YES ───┼──→ RETREAT ──→ RETURN
              │
        NO    ▼
┌─────────────────────────────────────┐
│  PRIORITY 4-N: State machine        │
│  - COMBAT → attack/move             │
│  - EXPLORE → autoexplore            │
│  - LOOT → pickup                    │
└─────────────────────────────────────┘
```

---

## Validation Plan

### 1. Quick Soak Test (10 runs)
```bash
python3 engine.py \
  --bot-soak \
  --bot-persona balanced \
  --scenario tight_brutal_funnel \
  --runs 10 \
  --max-turns 200 \
  --max-floors 1 \
  --metrics-log reports/soak/tbf_balanced_10_17c.csv \
  --telemetry-json reports/soak/tbf_balanced_10_17c.jsonl
```

**Expected Results:**
- Heal events: 5-10 per run (not 0-1)
- Potion usage: Most deaths with 0-1 potions (not unused full inventory)
- Death rate: 60-80% (down from 100%)

### 2. Full Soak Test (30 runs each)
Run all lethal scenarios with balanced persona:
- `tight_brutal_funnel`
- `orc_gauntlet_5rooms`
- `orc_swarm_wave3`
- `plague_gauntlet`

### 3. Generate Report
```bash
python3 tools/bot_survivability_report.py \
  --input reports/soak \
  --output reports/bot_survivability_scenarios_17c.md
```

**Target Metrics:**
- Heal HP% P50: 25-30% (up from 3.6%)
- Deaths with 0 potions: 90-95% (down from 99.7%)
- Panic heal events: 10-20% of total heals
- Death rate: 40-80% (scenario-dependent)

---

## Design Rationale

### Why Hard Returns?
**Problem**: Soft checks allow execution to continue → combat overrides  
**Solution**: Hard returns ensure action is final → no override possible

### Why Strengthen Panic?
**Problem**: Waiting for 2+ enemies often means death before second enemy arrives  
**Solution**: ANY adjacent enemy at low HP is already critical → heal immediately

### Why Damage Spike Detection?
**Problem**: 3 hits of 10% HP each = 30% lost, but no single "emergency"  
**Solution**: Track recent damage → detect burst patterns → raise threshold

### Why Emergency HP Threshold?
**Problem**: At 5% HP with 1 enemy, original logic might not trigger  
**Solution**: Very low HP (< 10%) is ALWAYS an emergency → panic unconditionally

---

## Guardrails Maintained

✅ **No changes to:**
- Combat formulas (accuracy, damage, evasion)
- TurnStateAdapter
- Scenario harness
- Worldgen
- IO/render boundary

✅ **Only modified:**
- BotBrain decision pipeline
- Panic trigger conditions
- Test expectations for strengthened panic

---

## Conclusion

Phase 17C Decision Priority Fix addresses the critical issue where healing logic existed but never executed due to decision priority problems.

**Key Achievements:**
1. ✅ Healing now has absolute priority (hard returns)
2. ✅ Panic triggers strengthened (3 conditions instead of 1)
3. ✅ All 67 bot tests passing
4. ✅ Clean architectural boundaries maintained
5. ✅ Persona configurability preserved

**Status**: ✅ **Ready for Soak Validation**

The bot should now:
- Heal at 25-30% HP consistently
- Panic heal when in danger
- Use potions efficiently (not die with full inventory)
- Survive 20-60% of lethal scenario runs (depending on difficulty)

---

**Next Step**: Run 10-run quick soak to validate healing occurs, then full 30-run validation.
