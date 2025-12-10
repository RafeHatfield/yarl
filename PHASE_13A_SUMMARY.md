# Phase 13A: Combat Feel Measurement Scaffolding

## Summary

Phase 13A extends the scenario harness with **combat metrics** to measure attack rates, hit percentages, and combat pacing. This provides the data infrastructure needed to tune speed bonuses, accuracy, and evasion values in future phases.

**Status**: ✅ Complete

---

## What Was Delivered

### 1. Extended Metrics (RunMetrics & AggregatedMetrics)

**File**: `services/scenario_harness.py`

Added four new fields to track combat statistics:

**RunMetrics** (per-run):
- `player_attacks: int` - Total attack attempts by player
- `player_hits: int` - Successful player hits
- `monster_attacks: int` - Total attack attempts by monsters
- `monster_hits: int` - Successful monster hits

**AggregatedMetrics** (across all runs):
- `total_player_attacks: int`
- `total_player_hits: int`
- `total_monster_attacks: int`
- `total_monster_hits: int`

Both `to_dict()` methods updated to include these fields in JSON export.

---

### 2. Metrics Collector Methods

**File**: `services/scenario_metrics.py`

Added two methods to `ScenarioMetricsCollector`:

```python
def record_player_attack(self, hit: bool) -> None:
    """Record a player attack attempt and whether it hit."""
    
def record_monster_attack(self, hit: bool) -> None:
    """Record a monster attack attempt and whether it hit."""
```

These methods increment both attack counts and hit counts when `hit=True`.

---

### 3. Combat Instrumentation

**File**: `components/fighter.py`

Instrumented the `attack_d20()` method (canonical d20 combat function) to record metrics:

- Determines if attacker is player (no AI component) or monster (has AI component)
- Calls appropriate metrics collector method with hit/miss result
- Works for all attack types: normal, surprise, critical, fumble, bonus/momentum

**Location**: After hit determination, before visual feedback (line ~890)

---

### 4. CLI Output Enhancement

**File**: `ecosystem_sanity.py`

Updated the Results section to display combat metrics:

```
Combat Metrics:
  Player Attacks: 287
  Player Hits: 191
  Player Hit Rate: 66.6%
  Monster Attacks: 187
  Monster Hits: 78
  Monster Hit Rate: 41.7%
```

Hit rates are calculated and displayed as percentages.

---

### 5. New Dueling Pit Scenario

**File**: `config/levels/scenario_dueling_pit.yaml`

Created a new baseline combat scenario:

- **Purpose**: Measure 1v1 combat feel (accuracy, evasion, momentum)
- **Setup**: Simple 12×12 enclosed arena
- **Combatants**: Player vs single orc at depth 5
- **Equipment**: Baseline (dagger + leather armor)
- **Turn Limit**: 100 turns per duel
- **Default Runs**: 50 duels

**Expected Outcomes** (conservative thresholds):
- `min_player_kills: 15` (~30% win rate minimum)
- `max_player_deaths: 40` (up to 80% loss rate allowed)

These thresholds are intentionally loose to catch regressions without enforcing strict balance.

---

### 6. JSON Export

All new metrics are automatically included in `--export-json` output:

```json
{
  "scenario_id": "dueling_pit",
  "runs": 50,
  "metrics": {
    "total_player_attacks": 287,
    "total_player_hits": 191,
    "total_monster_attacks": 187,
    "total_monster_hits": 78,
    ...
  }
}
```

This data can be used for analysis, tuning, and tracking combat balance over time.

---

## Verification Results

### Dueling Pit - 50 Runs

**Command**:
```bash
python3 ecosystem_sanity.py \
  --scenario dueling_pit \
  --runs 50 \
  --turn-limit 100 \
  --player-bot tactical_fighter \
  --fail-on-expected \
  --export-json dueling_pit_50runs.json
```

**Results**:
- **Player Hit Rate**: 66.6% (191 hits / 287 attacks)
- **Monster Hit Rate**: 41.7% (78 hits / 187 attacks)
- **Player Kills**: 50/50 (100% win rate at depth 5)
- **Player Deaths**: 0/50
- **Average Turns**: 50.0

**Observations**:
- Player has significant advantage with tactical_fighter bot at depth 5
- Suggests tactical positioning and equipment provide ~25% hit rate advantage
- Clean baseline data for future tuning

### Backward Compatibility

Verified existing scenarios still work:

- ✅ **backstab_training**: Combat metrics tracking correctly (66.1% player hit rate)
- ✅ **plague_arena**: Combat metrics tracking correctly (77.2% player hit rate)

All 28 existing tests pass.

---

## Files Modified

1. `services/scenario_harness.py` - Extended metrics dataclasses
2. `services/scenario_metrics.py` - Added combat tracking methods
3. `components/fighter.py` - Instrumented attack_d20() method
4. `ecosystem_sanity.py` - Enhanced CLI output
5. `tests/unit/test_scenario_harness_basic.py` - Updated test assertions
6. `config/levels/scenario_dueling_pit.yaml` - **NEW** scenario

---

## Next Steps (Future Phases)

Phase 13A provides **measurement scaffolding only**. We are NOT tuning numbers yet.

### Phase 13B (Combat Tuning)
1. Run dueling_pit across multiple depths (1, 5, 10, 15, 20)
2. Analyze hit rate curves vs depth
3. Add scenarios with varying speed bonuses
4. Measure momentum/bonus attack effectiveness
5. Tune accuracy/evasion values based on data

### Phase 13C (Advanced Scenarios)
1. Multi-enemy dueling (1v2, 1v3)
2. Speed-focused scenarios (fast vs slow opponents)
3. Critical hit impact scenarios
4. Defensive stance/parry scenarios

---

## Usage Examples

### Run Dueling Pit with Default Settings
```bash
python3 ecosystem_sanity.py --scenario dueling_pit
```

### Export Combat Data for Analysis
```bash
python3 ecosystem_sanity.py \
  --scenario dueling_pit \
  --runs 100 \
  --export-json combat_data.json
```

### Compare Hit Rates Across Scenarios
```bash
for scenario in backstab_training plague_arena dueling_pit; do
  python3 ecosystem_sanity.py \
    --scenario $scenario \
    --runs 20 \
    --export-json ${scenario}_data.json
done
```

### Parse JSON for Analysis
```bash
cat dueling_pit_50runs.json | jq '.metrics | {
  player_hit_rate: (.total_player_hits / .total_player_attacks * 100),
  monster_hit_rate: (.total_monster_hits / .total_monster_attacks * 100)
}'
```

---

## Testing

All tests pass:
```bash
pytest tests/unit/test_scenario_harness_basic.py -v
# 28 passed in 0.43s
```

No regressions detected in existing scenarios.

---

## Conclusion

Phase 13A successfully adds combat feel measurement infrastructure without changing any game balance. The dueling_pit scenario provides clean baseline data, and the JSON export enables data-driven tuning decisions in future phases.

**The scaffolding is ready. Tuning comes next.**
