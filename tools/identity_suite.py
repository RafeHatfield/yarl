#!/usr/bin/env python3
"""Identity Suite - Mechanic identity and invariant scenario runner.

Phase 22.4: Runs a curated set of scenarios focused on mechanic identity and
invariants. This suite validates that game mechanics behave correctly and
deterministically - oaths, abilities, monster behaviors, ranged doctrine, etc.

Distinct from:
  - Balance Suite: Ecosystem outcome drift (win rate, attrition, pacing)
  - Hazards Suite: Trap and environmental hazard correctness

Usage:
    python3 tools/identity_suite.py
    python3 tools/identity_suite.py --seed-base 42
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


# ============================================================================
# IDENTITY SCENARIO CONFIGURATION
# ============================================================================

# Canonical ordered list of identity scenarios.
# Suite doctrine: YAML tags decide membership, this list decides ordering.
# To add a scenario: add tag `identity` to YAML, then add here in logical order.

IDENTITY_SCENARIOS = [
    # =========================================================================
    # Phase 19: Monster Identity Scenarios
    # =========================================================================
    {"id": "monster_slime_identity", "runs": 30, "turn_limit": 80},
    {"id": "monster_skeleton_identity", "runs": 30, "turn_limit": 200},
    {"id": "monster_orc_chieftain_identity", "runs": 30, "turn_limit": 200},
    {"id": "monster_orc_shaman_identity", "runs": 30, "turn_limit": 200},
    {"id": "monster_necromancer_identity", "runs": 30, "turn_limit": 250},
    {"id": "monster_bone_necromancer_identity", "runs": 30, "turn_limit": 250},
    {"id": "monster_plague_necromancer_identity", "runs": 30, "turn_limit": 250},
    {"id": "monster_exploder_necromancer_identity", "runs": 30, "turn_limit": 250},
    {"id": "monster_wraith_identity", "runs": 30, "turn_limit": 200},
    {"id": "monster_lich_identity", "runs": 30, "turn_limit": 300},
    {"id": "monster_fire_beetle_identity", "runs": 30, "turn_limit": 150},
    {"id": "troll_identity", "runs": 30, "turn_limit": 100},
    {"id": "monster_cave_spider_identity", "runs": 30, "turn_limit": 150},
    {"id": "monster_web_spider_identity", "runs": 30, "turn_limit": 150},

    # =========================================================================
    # Phase 20: Ability Identity Scenarios
    # =========================================================================
    {"id": "player_reflex_potion_identity", "runs": 30, "turn_limit": 100},
    {"id": "root_potion_entangle_identity", "runs": 30, "turn_limit": 100},
    {"id": "sunburst_potion_blind_identity", "runs": 30, "turn_limit": 100},
    {"id": "scenario_disarm_scroll_identity", "runs": 30, "turn_limit": 100},
    {"id": "scenario_silence_orc_shaman_identity", "runs": 30, "turn_limit": 150},
    {"id": "scenario_silence_lich_identity", "runs": 30, "turn_limit": 200},
    
    # Weapon mechanics
    {"id": "knockback_weapon_identity", "runs": 30, "turn_limit": 100},
    
    # Scroll modernization
    {"id": "scroll_dragon_fart_identity", "runs": 30, "turn_limit": 30},
    {"id": "scroll_fireball_identity", "runs": 30, "turn_limit": 30},

    # =========================================================================
    # Phase 22.1: Oath Identity Scenarios
    # =========================================================================
    {"id": "oath_embers_identity", "runs": 20, "turn_limit": 120},
    {"id": "oath_venom_identity", "runs": 20, "turn_limit": 120},
    {"id": "oath_chains_identity", "runs": 20, "turn_limit": 120},

    # =========================================================================
    # Phase 22.2: Ranged Combat Identity Scenarios
    # =========================================================================
    {"id": "ranged_viability_arena", "runs": 10, "turn_limit": 50},
    {"id": "ranged_adjacent_punish_arena", "runs": 20, "turn_limit": 80},
    {"id": "ranged_max_range_denial_arena", "runs": 20, "turn_limit": 80},
    {"id": "ranged_chains_synergy", "runs": 20, "turn_limit": 100},
    {"id": "scenario_net_arrow_identity", "runs": 20, "turn_limit": 80},

    # =========================================================================
    # Phase 22.3: Skirmisher Identity Scenarios
    # =========================================================================
    {"id": "skirmisher_identity", "runs": 30, "turn_limit": 100},
    {"id": "skirmisher_vs_ranged_net_identity", "runs": 25, "turn_limit": 120},
]


# ============================================================================
# CORE LOGIC
# ============================================================================

def run_ecosystem_scenario(
    scenario_id: str,
    runs: int,
    turn_limit: int,
    output_path: Path,
    seed_base: int = 1337,
) -> bool:
    """Run ecosystem_sanity for a single scenario and export JSON.

    Args:
        scenario_id: Scenario identifier
        runs: Number of runs
        turn_limit: Turn limit per run
        output_path: Where to write JSON export
        seed_base: Base seed for deterministic runs (default: 1337)

    Returns:
        True if successful, False otherwise
    """
    cmd = [
        "python3",
        "ecosystem_sanity.py",
        "--scenario", scenario_id,
        "--runs", str(runs),
        "--turn-limit", str(turn_limit),
        "--player-bot", "tactical_fighter",
        "--export-json", str(output_path),
        "--seed-base", str(seed_base),
    ]

    print(f"  Running {scenario_id} ({runs} runs, {turn_limit} turns)...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(f"    ⚠️  Failed: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"    ⚠️  Exception: {e}")
        return False


def run_identity_suite(seed_base: int = 1337) -> int:
    """Run all identity suite scenarios.

    Args:
        seed_base: Base seed for deterministic runs

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("reports") / "identity_suite" / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("Identity Suite - Mechanic Identity & Invariant Scenarios")
    print("=" * 60)
    print(f"Output Directory: {output_dir}")
    print(f"Seed Base: {seed_base}")
    print(f"Scenarios: {len(IDENTITY_SCENARIOS)}")
    print("=" * 60)

    print(f"\n🎯 Running {len(IDENTITY_SCENARIOS)} scenarios...\n")

    # Run all scenarios
    success_count = 0
    fail_count = 0
    scenario_results: List[Dict[str, Any]] = []

    for scenario in IDENTITY_SCENARIOS:
        scenario_id = scenario["id"]
        runs = scenario["runs"]
        turn_limit = scenario["turn_limit"]

        output_path = output_dir / f"{scenario_id}.json"

        success = run_ecosystem_scenario(
            scenario_id=scenario_id,
            runs=runs,
            turn_limit=turn_limit,
            output_path=output_path,
            seed_base=seed_base,
        )

        if success:
            success_count += 1
            scenario_results.append({"id": scenario_id, "status": "success"})
        else:
            fail_count += 1
            scenario_results.append({"id": scenario_id, "status": "failed"})

    print(f"\n✅ Completed {success_count + fail_count}/{len(IDENTITY_SCENARIOS)} scenarios\n")

    # Generate summary report
    summary = {
        "suite": "identity",
        "timestamp": timestamp,
        "seed_base": seed_base,
        "total_scenarios": len(IDENTITY_SCENARIOS),
        "success_count": success_count,
        "fail_count": fail_count,
        "scenarios": [s["id"] for s in IDENTITY_SCENARIOS],
        "results": scenario_results,
    }

    summary_path = output_dir / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Write latest pointer
    latest_path = Path("reports") / "identity_suite" / "latest.txt"
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(latest_path, "w") as f:
        f.write(str(output_dir))

    print("=" * 60)
    print("Status: COMPLETED")
    print(f"  SUCCESS: {success_count}")
    print(f"  FAIL: {fail_count}")

    if fail_count == 0:
        print("\n✅ PASS: All identity scenarios completed successfully")
        print("=" * 60)
        return 0
    else:
        print(f"\n❌ FAIL: {fail_count} scenario(s) failed")
        print("=" * 60)
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run identity suite scenarios",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--seed-base",
        type=int,
        default=1337,
        help="Base seed for deterministic runs (default: 1337)",
    )

    args = parser.parse_args()

    exit_code = run_identity_suite(
        seed_base=args.seed_base,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
