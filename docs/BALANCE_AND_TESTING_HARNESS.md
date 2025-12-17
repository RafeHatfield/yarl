# Catacombs of YARL - Balance and Testing Harness Guide

Last updated: 2024-12-14 (Phase 18 QOL)

This document is the authoritative reference for all balance, difficulty,
soak, and validation tooling in Catacombs of YARL.

If you are ever unsure what to run, why a tool exists, or whether you are
overthinking things, start here.

-----------------------------------------------------------------------

## TL;DR (Read This First)

If you only remember three things:

### 1. For day-to-day balance confidence, run:

    make balance-suite

This is the one command that matters most. Exits non-zero if balance drifts beyond thresholds.

### 2. For fast iteration while tuning YAML or gear:

    make balance-suite-fast

This skips slow soaks but still catches balance regressions.

### 3. When results feel good and you want to lock them in:

    make balance-suite-update-baseline

This updates the canonical baseline used for future comparisons.
**Important:** This command exits 0 on success, even if the old baseline would have shown FAILs.

For fast baseline updates:

    make balance-suite-update-baseline-fast

Everything else exists to support, feed, or debug this pipeline.

-----------------------------------------------------------------------

## Mental Model: Why This Exists

YARL uses multiple complementary harnesses, each answering a different
question:

- Is this scenario fair, lethal, or interesting?
- Does difficulty scale smoothly across depth?
- Does the bot survive intelligently?
- Did my change break balance overall?

These tools are not alternatives. They are layers.

The Balance Suite is the orchestrator that ties them together.

-----------------------------------------------------------------------

## High-Level Pipeline

    Scenario YAMLs
        |
        v
    ecosystem_sanity.py
    (deterministic combat truth)
        |
        v
    Difficulty Dashboard
    (depth curves and pressure)
        |
        +--> Bot Soak (optional, realism)
        |
        v
    Balance Suite
    (baseline diff and verdict)

-----------------------------------------------------------------------

## Core Tools

### ecosystem_sanity.py

Purpose: Deterministic combat truth.

- Runs hand-authored scenarios
- No worldgen randomness
- Produces structured JSON metrics

Answers questions like:
- Is this fight fair?
- Did this weapon or affix matter?
- Did lethality change?

You rarely need to run this directly anymore; the Balance Suite calls it.

---

### Difficulty Dashboard

Purpose: Shape of the game over depth.

Aggregates results by depth and visualizes:
- Death rate
- Player hit rate
- Monster hit rate
- Pressure index
- Bonus attacks

This is the macro lens.

---

### Bot Soak and Survivability Reports

Purpose: Player realism.

Runs the full engine loop with bot personas and captures:
- Heal timing
- Panic behavior
- Deaths with unused potions

This is optional for balance validation, but essential for AI tuning.

---

### Balance Suite (The Unifier)

Purpose: Confidence.

**Phase 18 QOL: Comprehensive ecosystem + weapon variant testing**

The Balance Suite:
- Runs a curated matrix of 15 scenarios
- Covers 3 base scenarios (depth2, depth3, depth5)
- Tests 4 weapon affixes per base (keen, vicious, fine, masterwork)
- Compares results against a stored baseline
- Produces a human-readable report and a verdict

**What it measures:**
- `death_rate`: Player deaths / runs
- `player_hit_rate`: Combat accuracy
- `monster_hit_rate`: Incoming threat accuracy
- `pressure_index`: (Monster attacks/run) - (Player attacks/run)
- `bonus_attacks_per_run`: Extra attack triggers

**Drift thresholds:**
- WARN: ±10% death rate, ±5% hit rates, ±5 pressure, ±2 bonus attacks
- FAIL: ±20% death rate, ±10% hit rates, ±10 pressure, ±4 bonus attacks

If it says PASS, you can move on guilt-free.

**See also:** `docs/BALANCE_SUITE.md` for detailed usage and adding scenarios.

-----------------------------------------------------------------------

## When to Run What

If you changed YAML numbers:

    make balance-suite-fast

If you changed combat logic, affixes, or damage types:

    make balance-suite

Before merging or checkpointing a milestone:

    make balance-suite
    make balance-suite-update-baseline

**Note on baseline updates:**
- `balance-suite-update-baseline` writes the baseline and exits 0 (success)
- It does NOT fail due to thresholds against the old baseline
- This is intentional: you're declaring "this is the new ground truth"

-----------------------------------------------------------------------

## Baselines

Baselines answer one question:

"This felt good."

Baseline file:

    reports/baselines/balance_suite_baseline.json

Rules:
- Update only intentionally
- Never auto-update in CI
- Treat diffs as signals, not errors

-----------------------------------------------------------------------

## Balance Suite Verdicts

- **PASS**: All metrics within acceptable drift (changes < WARN threshold)
- **WARN**: One or more metrics show notable drift (≥ WARN, < FAIL)
- **FAIL**: One or more metrics exceed thresholds (≥ FAIL)
- **NO_BASELINE**: No baseline exists yet (run `make balance-suite-update-baseline`)

**Example drift classification:**
- Death rate +0.08 → PASS (below 0.10 WARN threshold)
- Death rate +0.12 → WARN (between 0.10 WARN and 0.20 FAIL)
- Death rate +0.25 → FAIL (exceeds 0.20 FAIL threshold)

Note: Drift can be positive or negative. The suite uses absolute values.
Large negative drifts (e.g., death rate dropping significantly) still trigger WARN/FAIL.

-----------------------------------------------------------------------

## Why This Is Not Overkill

You are building:
- Weapon identities
- Affixes
- Damage types
- Factions
- Depth scaling
- AI behavior

Without this harness:
- Balance becomes vibes
- Regressions become invisible
- Iteration slows due to fear

With it:
- You move fast without breaking the game
- Experimentation becomes safe

-----------------------------------------------------------------------

## Rules for This Document

- This is the single source of truth
- Other docs should link here, not duplicate content
- Confusion is a bug; fix the tool or update this doc

-----------------------------------------------------------------------

## Scenario Matrix (Phase 18)

The Balance Suite runs **15 scenarios total**:

**Base scenarios:**
1. `depth2_orc_baseline` (3 orcs, 40 runs)
2. `depth3_orc_brutal` (4 orcs tight arena, 50 runs)
3. `depth5_zombie` (8 zombies wide arena, 50 runs)

**Weapon variants per base (12 total):**
- `_keen`: Expanded crit range (19-20, 10% crit chance)
- `_vicious`: Bonus damage (+1)
- `_fine`: Improved accuracy (+1 to-hit)
- `_masterwork`: Combined bonuses (+1 hit, +1 damage)

**Estimated runtime:** 15-20 minutes for full suite

All scenarios maintain identical monster/item layouts to their base.
Only the player's starting weapon varies.

-----------------------------------------------------------------------

## Adding New Scenarios

To add a weapon variant or new base scenario:

1. Create YAML in `config/levels/scenario_<name>.yaml`
2. Add to `SCENARIO_MATRIX` in `tools/balance_suite.py`
3. Run `make balance-suite` to test
4. Update baseline with `make balance-suite-update-baseline` when ready

See `docs/BALANCE_SUITE.md` for detailed instructions.

### Phase 19 Monster Identity Scenarios

Phase 19 introduces monster-specific ability scenarios for regression testing:

- **`scenario_monster_slime_identity.yaml`**: Validates Phase 19 slime mechanics
  - Split Under Pressure (tiered splitting at low HP)
  - Corrosive Contact (metal weapons only, 50% damage floor)
  - Engulf (slow that persists while adjacent, decays after breaking contact)
  - Location: `config/levels/scenario_monster_slime_identity.yaml`
  - Included in full balance suite (30 runs, 80 turn limit)
  - Purpose: Ongoing regression anchor for slime identity kit

See `docs/PHASE_19_MONSTER_IDENTITY_AND_ABILITIES.md` for full details.

-----------------------------------------------------------------------

## References

Balance Suite detailed guide:
`docs/BALANCE_SUITE.md`

Repository:
https://github.com/RafeHatfield/rlike

Combat system:
https://github.com/RafeHatfield/rlike/blob/main/docs/COMBAT_SYSTEM.md
