#!/usr/bin/env python3
"""Hazards Suite - Environmental hazards and trap scenario runner.

Phase 21.4: Runs a curated subset of scenarios focused on environmental hazards
and traps. This is separate from the balance suite to keep ecology-focused
scenarios distinct from mechanics-focused scenarios.

Usage:
    python3 tools/hazards_suite.py
    python3 tools/hazards_suite.py --fast
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


# ============================================================================
# HAZARDS SCENARIO CONFIGURATION
# ============================================================================

# Scenarios in the hazards suite (traps, environmental effects, etc.)
HAZARDS_SCENARIOS = [
    # Phase 21.1: Root Trap
    {"id": "trap_root_identity", "runs": 30, "turn_limit": 20},
    
    # Phase 21.2: Spike Trap
    {"id": "trap_spike_identity", "runs": 30, "turn_limit": 20},
    
    # Phase 21.3: Teleport Trap
    {"id": "trap_teleport_identity", "runs": 30, "turn_limit": 20},
    
    # Phase 21.4: Gas Trap
    {"id": "trap_gas_identity", "runs": 30, "turn_limit": 20},
    
    # Phase 21.4: Fire Trap
    {"id": "trap_fire_identity", "runs": 30, "turn_limit": 20},
    
    # Phase 21.5: Hole Trap
    {"id": "trap_hole_identity", "runs": 30, "turn_limit": 20},
    
    # Phase 21.6: Trapped Chest (Spike)
    {"id": "trapped_chest_spike_identity", "runs": 30, "turn_limit": 20},
    
    # Phase 21.7: Trap Detection
    {"id": "trap_detect_identity", "runs": 30, "turn_limit": 20},
    
    # Phase 21.7: Trap Disarm
    {"id": "trap_disarm_identity", "runs": 30, "turn_limit": 20},
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


def run_hazards_suite(fast_mode: bool = False, seed_base: int = 1337) -> int:
    """Run all hazards suite scenarios.
    
    Args:
        fast_mode: If True, run fewer iterations for faster feedback
        seed_base: Base seed for deterministic runs
        
    Returns:
        Exit code (0 = success, 1 = failure)
    """
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("reports") / "hazards_suite" / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 60)
    print("Hazards Suite - Environmental Hazards & Trap Scenarios")
    print("=" * 60)
    print(f"Output Directory: {output_dir}")
    print(f"Fast Mode: {fast_mode}")
    print(f"Seed Base: {seed_base}")
    print("=" * 60)
    
    # Adjust runs if fast mode
    scenarios = HAZARDS_SCENARIOS.copy()
    if fast_mode:
        for scenario in scenarios:
            scenario["runs"] = max(10, scenario["runs"] // 3)
    
    print(f"\n🎯 Running {len(scenarios)} scenarios...\n")
    
    # Run all scenarios
    success_count = 0
    fail_count = 0
    
    for scenario in scenarios:
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
        else:
            fail_count += 1
    
    print(f"\n✅ Completed {success_count + fail_count}/{len(scenarios)} scenarios\n")
    
    # Generate summary report
    summary = {
        "timestamp": timestamp,
        "fast_mode": fast_mode,
        "seed_base": seed_base,
        "total_scenarios": len(scenarios),
        "success_count": success_count,
        "fail_count": fail_count,
        "scenarios": [s["id"] for s in scenarios],
    }
    
    summary_path = output_dir / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    # Write latest pointer
    latest_path = Path("reports") / "hazards_suite" / "latest.txt"
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(latest_path, "w") as f:
        f.write(str(output_dir))
    
    print("=" * 60)
    print("Status: COMPLETED")
    print(f"  SUCCESS: {success_count}")
    print(f"  FAIL: {fail_count}")
    
    if fail_count == 0:
        print("\n✅ PASS: All scenarios completed successfully")
        print("=" * 60)
        return 0
    else:
        print(f"\n❌ FAIL: {fail_count} scenario(s) failed")
        print("=" * 60)
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run hazards suite scenarios",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast mode: run fewer iterations for quicker feedback",
    )
    parser.add_argument(
        "--seed-base",
        type=int,
        default=1337,
        help="Base seed for deterministic runs (default: 1337)",
    )
    
    args = parser.parse_args()
    
    exit_code = run_hazards_suite(
        fast_mode=args.fast,
        seed_base=args.seed_base,
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
