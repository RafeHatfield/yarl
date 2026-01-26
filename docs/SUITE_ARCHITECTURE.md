# Suite Architecture

This document describes the test suite organization for Catacombs of YARL.

## Overview

The testing infrastructure is organized into three distinct suites, each with a specific purpose:

| Suite | Purpose | Baseline Policy |
|-------|---------|-----------------|
| **Identity Suite** | Mechanic invariants, trigger logic, determinism | Expectations/invariants |
| **Hazards Suite** | Trap and environmental correctness | Expectations/invariants |
| **Balance Suite** | Ecosystem outcome drift (win rate, attrition, pacing) | Deliberate baselines |

## Suite Doctrine

**Tags decide membership; lists decide ordering.**

- Each scenario YAML file should include a `suites:` field listing which suite(s) it belongs to
- Each suite tool (e.g., `tools/identity_suite.py`) maintains an ordered list of scenarios
- Validation tests ensure the list matches the tagged scenarios

## Suite Details

### Identity Suite

**Location:** `tools/identity_suite.py`  
**Target:** `make identity-suite`

**Purpose:** Validates that game mechanics behave correctly and deterministically:
- Monster identity behaviors (slime split, skeleton shield wall, necromancer raise, etc.)
- Ability mechanics (potions, scrolls, oaths)
- Ranged combat doctrine (range bands, penalties, special ammo)
- Enemy abilities (skirmisher leap/pressure, chieftain rally, etc.)

**Membership criteria:**
- Scenarios testing specific mechanic triggers or behaviors
- Scenarios validating invariants (e.g., "entangle always blocks movement")
- Scenarios with expected metric thresholds (not baseline comparisons)

**Example scenarios:**
- `monster_slime_identity` - Split Under Pressure, Corrosive Contact, Engulf
- `oath_embers_identity` - Oath of Embers burning proc
- `skirmisher_identity` - Pouncing Leap, Fast Pressure
- `ranged_viability_arena` - Range band damage modifiers

### Hazards Suite

**Location:** `tools/hazards_suite.py`  
**Target:** `make hazards-suite`

**Purpose:** Validates trap and environmental hazard correctness:
- Trap triggering mechanics
- Status effect application (entangle, blind, poison, etc.)
- Trap detection and disarm
- Environmental hazard interactions

**Membership criteria:**
- Scenarios focused on trap/hazard mechanics
- Scenarios testing trap detection and disarm
- Environmental effect validation

**Example scenarios:**
- `trap_root_identity` - Root trap entangle on step
- `trap_spike_identity` - Spike trap damage
- `trap_teleport_identity` - Teleport trap displacement
- `trap_detect_identity` - Trap detection skill check

### Balance Suite

**Location:** `tools/balance_suite.py`  
**Target:** `make balance-suite`

**Purpose:** Tracks ecosystem outcome drift across scenarios and weapon variants:
- Win rate tracking
- Attrition (death rate) monitoring
- Combat pacing metrics
- Weapon quality impact on outcomes

**Membership criteria:**
- Representative ecosystem scenarios (depth probes)
- Weapon variant comparisons
- Scenarios with deliberate baseline expectations

**Baseline policy:**
- Balance suite uses stored baselines for comparison
- Baselines are updated deliberately via `make balance-suite-update-baseline`
- Drift thresholds determine PASS/WARN/FAIL verdicts

**Example scenarios:**
- `depth3_orc_brutal` - Depth 3 baseline encounter
- `depth5_zombie` - Depth 5 zombie horde
- `depth2_orc_baseline_keen` - Weapon variant (keen dagger)

## Running Suites

### Individual Suites

```bash
# Run identity suite
make identity-suite

# Run hazards suite
make hazards-suite

# Run balance suite
make balance-suite

# Run balance suite with baseline update
make balance-suite-update-baseline
```

### All Suites

```bash
# Run all suites in sequence (identity → hazards → balance)
make all-suites
```

The all-suites command runs suites in order and reports a combined status.

## Suite Tags in YAML

Each scenario YAML should include a `suites:` field:

```yaml
# For identity scenarios
suites: ["identity"]

# For hazards scenarios
suites: ["hazards"]

# For balance scenarios
suites: ["balance"]

# Multiple tags are allowed (for scenarios in multiple suites)
suites: ["identity", "enemy_abilities", "phase_22"]
```

## Adding New Scenarios to Suites

1. Add the appropriate `suites:` tag to the scenario YAML file
2. Add the scenario to the corresponding suite tool's ordered list
3. Run the validation tests to ensure list/tag consistency:
   ```bash
   pytest tests/test_identity_suite.py -v
   pytest tests/test_hazards_suite.py -v
   ```

## Validation Tests

Each suite has validation tests that ensure:
- All scenarios in the list are tagged correctly
- All tagged scenarios are in the list (no orphans)
- Suites are disjoint (no scenario in multiple primary suites)

```bash
# Run suite validation tests
pytest tests/test_identity_suite.py tests/test_hazards_suite.py -v
```

## Determinism

All suites use deterministic execution:
- Default seed base: 1337
- Configurable via `--seed-base` argument
- Same seed produces identical results across runs

## Output

Each suite run produces:
- Timestamped output directory under `reports/<suite_name>/`
- Per-scenario JSON metrics
- Summary JSON with pass/fail counts
- Latest pointer (`latest.txt`) for easy access

## Line Between Suites

| If the scenario tests... | It belongs in... |
|--------------------------|------------------|
| "Does the mechanic trigger correctly?" | Identity Suite |
| "Does the trap work as designed?" | Hazards Suite |
| "Is the win rate acceptable?" | Balance Suite |
| "Is the death rate within bounds?" | Balance Suite |
| "Does the ability apply the correct effect?" | Identity Suite |
| "Is ecosystem drift under control?" | Balance Suite |
