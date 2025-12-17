# Balance Suite

**Phase 18 QOL: Comprehensive ecosystem scenario matrix + weapon variant testing**

The Balance Suite is a curated set of ecosystem scenarios designed to detect combat balance drift across weapon variants, damage types, and difficulty levels.

## What It Runs

The suite executes 15 scenarios:
- **3 base scenarios** (depth2_orc_baseline, depth3_orc_brutal, depth5_zombie)
- **12 weapon variants** (4 affixes × 3 base scenarios)

Each scenario runs via `ecosystem_sanity.py` with tactical_fighter bot and exports normalized metrics.

### Weapon Variants Tested

- **Keen**: Expanded crit range (19-20, 10% crit chance)
- **Vicious**: Bonus damage (+1)
- **Fine**: Improved accuracy (+1 to-hit)
- **Masterwork**: Combined bonuses (+1 hit, +1 damage)

### Metrics Collected

For each scenario variant:
- `death_rate`: Player deaths / runs
- `player_hit_rate`: Player hits / player attacks
- `monster_hit_rate`: Monster hits / monster attacks
- `pressure_index`: (Monster attacks/run) - (Player attacks/run)
- `bonus_attacks_per_run`: Bonus attacks triggered / runs

## Running the Suite

### Quick Run (No Baseline)

```bash
make balance-suite-fast
```

This runs all scenarios and generates a report. If no baseline exists, the report shows current metrics only.

### Full Run (With Comparison)

```bash
make balance-suite
```

Compares current metrics against baseline (if exists) and classifies each scenario as PASS/WARN/FAIL.

### Creating/Updating Baseline

```bash
make balance-suite-update-baseline
```

Runs the full suite and stores the results as the new baseline in `reports/baselines/balance_suite_baseline.json`.

**Note:** This command exits 0 on success, even if the old baseline would have shown FAILs.
The intent is to declare "this is the new ground truth."

For a fast baseline update:

```bash
make balance-suite-update-baseline-fast
```

## Output Structure

Results are stored in `reports/balance_suite/<timestamp>/`:

```
reports/balance_suite/
├── 20241214_153045/
│   ├── balance_report.md          # Human-readable markdown report
│   ├── verdict.json                # Machine-readable verdict
│   ├── summary.json                # Normalized metrics (for baseline creation)
│   └── metrics/
│       └── raw/
│           ├── depth2_orc_baseline.json
│           ├── depth2_orc_baseline_keen.json
│           └── ...
└── latest.txt                      # Pointer to most recent run
```

### balance_report.md

Unified markdown report showing:
- Verdict summary (PASS/WARN/FAIL counts)
- Per-scenario metrics and deltas from baseline
- Recommendations if thresholds exceeded

### verdict.json

Machine-readable JSON containing:
- Overall status (PASS/WARN/FAIL/NO_BASELINE)
- Per-scenario verdicts and deltas
- Timestamp and scenario count

## Verdict Classification

Each scenario is classified based on deltas from baseline:

| Metric | WARN Threshold | FAIL Threshold |
|--------|----------------|----------------|
| death_rate | ±0.10 | ±0.20 |
| player_hit_rate | ±0.05 | ±0.10 |
| monster_hit_rate | ±0.05 | ±0.10 |
| pressure_index | ±5.0 | ±10.0 |
| bonus_attacks_per_run | ±2.0 | ±4.0 |

- **PASS**: All deltas below WARN thresholds
- **WARN**: At least one delta ≥ WARN, all < FAIL
- **FAIL**: At least one delta ≥ FAIL

## Adding Scenarios

To add a new scenario variant:

1. Create a YAML file in `config/levels/` following naming convention: `scenario_<base>_<variant>.yaml`
2. Ensure it has the same monster/item layout as the base scenario
3. Only vary the player's starting weapon (in `player.equipment.weapon`)
4. Add the scenario to `SCENARIO_MATRIX` in `tools/balance_suite.py`

Example:

```yaml
# config/levels/scenario_depth2_orc_baseline_flame.yaml
player:
  position: [3, 6]
  facing: "east"
  inventory: []
  equipment:
    weapon: "flaming_longsword"  # Only change this
    armor: "leather_armor"        # Keep armor consistent
```

Then update `tools/balance_suite.py`:

```python
SCENARIO_MATRIX = [
    # ... existing scenarios ...
    {"id": "depth2_orc_baseline_flame", "runs": 40, "turn_limit": 100},
]
```

## Setting/Updating Baseline

The baseline represents the "expected" state of combat balance. Update it when:
- Intentionally rebalancing combat (damage, to-hit, HP, etc.)
- Adding new scenarios to the matrix
- Fixing bugs that affect combat metrics

**DO NOT** update the baseline casually. Drift detection is the point.

### Workflow

1. Make combat changes
2. Run `make balance-suite` to see drift
3. Validate changes are intentional
4. Run `make balance-suite-update-baseline` to establish new baseline
5. Commit the new baseline file to version control

## Interpreting Reports

### Scenario Shows WARN

- Minor drift detected
- Review deltas in report
- Consider if changes are expected
- May indicate subtle balance shift

### Scenario Shows FAIL

- Major drift detected
- Likely caused by recent combat changes
- Review code changes affecting combat math
- Update baseline if intentional, fix if bug

### No Baseline

- First run or baseline missing
- Report shows current metrics only
- Run `make balance-suite-update-baseline` to create one

## Integration with CI

The suite can be integrated into CI/CD:

```bash
# In CI script
make balance-suite

# Check exit code
if [ $? -ne 0 ]; then
  echo "Balance suite failed - review drift"
  exit 1
fi
```

Exit codes:
- `0`: PASS or NO_BASELINE
- `1`: FAIL (one or more scenarios exceeded thresholds)

## Performance Notes

- Full suite: ~15-20 minutes (15 scenarios × 40-50 runs each)
- Fast mode: Same duration (bot soak not yet implemented)
- Parallelization: Not yet implemented (future improvement)

## Troubleshooting

### "Scenario not found"

Ensure the scenario YAML file exists in `config/levels/` and matches the `scenario_id` in `SCENARIO_MATRIX`.

### Metrics look wrong

Check that:
- Weapon exists in `config/entities.yaml`
- Scenario YAML is valid (run `python3 ecosystem_sanity.py --list`)
- Raw JSON exports exist in `metrics/raw/`

### Baseline missing after creation

Check that:
- `reports/baselines/` directory exists
- Latest run succeeded and produced `summary.json`
- You have write permissions to `reports/baselines/`
