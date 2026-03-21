# Phase 17B: Potion Availability Fix

**Date**: 2025-12-13  
**Branch**: `feature/phase17b-survivability-tuning`  
**Status**: ✅ Complete

## Critical Issue Discovered

### Problem
Latest survivability report showed:
- **Heal events: 0**
- **Deaths: 118**
- **Deaths with unused potions: 0/118 (all had 0 potions)**

Visual inspection during soak runs confirmed: **Player starts with NO healing potions**.

### Root Cause
All lethal scenario YAMLs defined:
- Potions **on the map** (as items to pick up)
- Player **inventory: []** (empty starting inventory)

**Result**: In immediate-combat scenarios, bot never had a chance to pick up potions before dying.

---

## Solution

### 1. Updated Scenario YAMLs (Starting Inventory)

Added healing potions directly to player starting inventory:

#### `scenario_tight_brutal_funnel.yaml`
```yaml
player:
  inventory:
    - "healing_potion"
    - "healing_potion"  # 2 potions for forced surround scenario
```

#### `scenario_orc_gauntlet_5rooms.yaml`
```yaml
player:
  inventory:
    - "healing_potion"
    - "healing_potion"
    - "healing_potion"  # 3 potions for sustained gauntlet
```

#### `scenario_orc_swarm_wave3.yaml`
```yaml
player:
  inventory:
    - "healing_potion"
    - "healing_potion"
    - "healing_potion"  # 3 potions for wave pressure
```

#### `scenario_plague_gauntlet.yaml`
```yaml
player:
  inventory:
    - "healing_potion"
    - "healing_potion"
    - "healing_potion"
    - "healing_potion"  # 4 potions (plague DoT + melee attrition)
```

**Rationale**:
- Immediate availability for heal testing
- Map potions still present (can pick up more if needed)
- Counts based on scenario difficulty and expected damage

### 2. Enhanced Telemetry (Potion Tracking)

**`engine/soak_harness.py`:**

Added potion counting after player creation:
```python
# Phase 17B: Count initial healing potions
initial_potions_count = 0
for item in player.inventory.items:
    if item.name == "healing_potion":
        initial_potions_count += 1
logger.info(f"Player starts with {initial_potions_count} healing potions")
```

Enhanced `_build_survivability_snapshot()`:
```python
def _build_survivability_snapshot(
    player, 
    run_metrics, 
    scenario_id,
    initial_potions  # NEW parameter
):
    potions_used = run_metrics.potions_used
    potions_remaining = count_potions_in_inventory(player)
    
    # Calculate potions_seen = initial + used + remaining
    potions_seen = initial_potions + potions_used + potions_remaining
    
    return {
        "potions_seen": potions_seen,      # NEW
        "potions_used": potions_used,      # Enhanced
        "potions_remaining": potions_remaining,
        # ... existing fields ...
    }
```

### 3. Enhanced Survivability Report

**`tools/bot_survivability_report.py`:**

Added potion availability section:
```markdown
## ⚠️ WARNING: Zero Potions Available

**CRITICAL**: These runs had ZERO healing potions available.
This makes heal threshold analysis meaningless - the bot cannot drink what doesn't exist.

**Action Required**: Update scenario YAMLs to include starting potions.
```

Or when potions exist:
```markdown
## Potion Availability
- Total potions seen: 360
- Total potions used: 245
- Usage rate: 68.1%
- Runs with potion data: 120
```

**Added tracking:**
- `total_potions_seen`: Sum of all potions available across runs
- `total_potions_used`: Sum of all potions consumed
- `runs_with_potions_data`: Count of runs with potion telemetry

---

## Test Results

```bash
pytest tests/test_bot*.py tests/test_soak*.py -m "not slow" -q
# ✅ 280 passed, 15 skipped in 0.90s
```

All existing tests pass - no regressions.

---

## Expected Impact

### Before Fix
```
Heal events: 0
Deaths: 118
Potions seen: 0 (effectively)
Deaths with 0 potions: 118 (100%)
Heal HP% median: N/A (no heals occurred)
```

### After Fix (Expected)
```
Heal events: 50-150 per 30-run soak
Deaths: 40-90 (40-80% death rate depending on scenario)
Potions seen: 90-120 (3-4 per run)
Potions used: 60-100 (60-80% usage rate)
Deaths with 0 potions: 85-95% (used all available healing)
Heal HP% median: 25-30%
```

### Per-Scenario Expectations

| Scenario | Potions | Expected Death Rate | Expected Usage |
|----------|---------|---------------------|----------------|
| tight_brutal_funnel | 2 | 60-80% (lethal funnel) | 90-100% |
| orc_gauntlet_5rooms | 3 | 40-60% (sustained) | 80-95% |
| orc_swarm_wave3 | 3 | 40-60% (wave pressure) | 75-90% |
| plague_gauntlet | 4 | 50-70% (DoT + melee) | 85-95% |

---

## Validation Plan

### 1. Quick Validation (10 runs)
```bash
python3 engine.py \
  --bot-soak \
  --bot-persona balanced \
  --scenario tight_brutal_funnel \
  --runs 10 \
  --max-turns 200 \
  --max-floors 1 \
  --metrics-log reports/soak/tbf_balanced_10_potions.csv \
  --telemetry-json reports/soak/tbf_balanced_10_potions.jsonl
```

**Expected**:
- ✅ Player starts with 2 potions (check logs)
- ✅ Heal events > 0
- ✅ Potions_seen = 20 (2 per run * 10 runs)
- ✅ Potions_used > 0

### 2. Generate Report
```bash
python3 tools/bot_survivability_report.py \
  --input reports/soak/tbf_balanced_10_potions.jsonl \
  --output reports/bot_survivability_quick.md
```

**Check for**:
- ✅ "Potion Availability" section shows non-zero values
- ✅ NO "Zero Potions Available" warning
- ✅ Heal HP% distribution is populated
- ✅ Usage rate is reasonable (60-100%)

### 3. Full Validation (30 runs each)
Run all 4 lethal scenarios with 30 runs each:
```bash
# All scenarios
for scenario in tight_brutal_funnel orc_gauntlet_5rooms orc_swarm_wave3 plague_gauntlet; do
  python3 engine.py \
    --bot-soak \
    --bot-persona balanced \
    --scenario $scenario \
    --runs 30 \
    --max-turns 300 \
    --max-floors 1 \
    --metrics-log reports/soak/${scenario}_balanced_30.csv \
    --telemetry-json reports/soak/${scenario}_balanced_30.jsonl
done

# Generate combined report
python3 tools/bot_survivability_report.py \
  --input reports/soak \
  --output reports/bot_survivability_scenarios.md
```

---

## Files Modified

### Scenario YAMLs (4 files)
1. `config/levels/scenario_tight_brutal_funnel.yaml` - Added 2 starting potions
2. `config/levels/scenario_orc_gauntlet_5rooms.yaml` - Added 3 starting potions
3. `config/levels/scenario_orc_swarm_wave3.yaml` - Added 3 starting potions
4. `config/levels/scenario_plague_gauntlet.yaml` - Added 4 starting potions

### Telemetry & Reporting (2 files)
1. `engine/soak_harness.py`:
   - Count initial potions after player creation
   - Pass `initial_potions` to `_build_survivability_snapshot()`
   - Calculate `potions_seen = initial + used + remaining`

2. `tools/bot_survivability_report.py`:
   - Track `total_potions_seen`, `total_potions_used`, `runs_with_potions_data`
   - Add "Potion Availability" section to report
   - Add "Zero Potions Available" warning when applicable

3. `services/scenario_level_loader.py`:
   - Enhanced `_apply_player_loadout()` to support both string and dict inventory formats
   - Uses `create_spell_item()` for potions (potions are spell items, not regular items)

---

## Design Rationale

### Why Starting Inventory vs Map Pickups?
**Map Pickups**:
- ❌ Requires bot to spot items
- ❌ Requires bot to navigate to items
- ❌ Dangerous in immediate-combat scenarios
- ❌ May never be collected if bot dies first

**Starting Inventory**:
- ✅ Immediately available
- ✅ No navigation required
- ✅ Heal logic can execute turn 1
- ✅ Tests actual heal decision making

### Why These Potion Counts?
- **2 potions** (funnel): Tight resource constraint, forces optimal healing
- **3 potions** (gauntlet/wave): Sustained pressure, moderate resources
- **4 potions** (plague): DoT + melee requires more healing resources

### Why Keep Map Potions?
- Allows testing of pickup behavior if bot survives initial waves
- Provides recovery opportunity mid-fight
- Doesn't hurt to have extras

---

## Guardrails Maintained

✅ **No changes to:**
- Combat formulas
- TurnStateAdapter
- Scenario harness core logic
- Worldgen
- ECS architecture

✅ **Only modified:**
- Scenario YAML configurations (player inventory)
- Soak telemetry (potion counting)
- Report generation (potion availability display)

---

## Next Steps

1. **Run Quick Validation** (10 runs) - Verify potions are present
2. **Check Logs** - Confirm "Player starts with N healing potions" message
3. **Generate Report** - Verify "Potion Availability" section shows data
4. **Run Full Soaks** (30 runs each) - Get meaningful heal distribution
5. **Analyze Results** - Compare heal HP% median vs target (25-30%)

---

## Conclusion

This fix addresses the fundamental issue preventing survivability testing: **no potions = no heals**.

With starting inventory potions:
- ✅ Healing logic can execute immediately
- ✅ Meaningful heal threshold distribution data
- ✅ Panic logic can be validated
- ✅ Death rates will reflect actual bot decision quality

**Status**: ✅ **Ready for Soak Validation** - Potions guaranteed available, heal testing now possible.
