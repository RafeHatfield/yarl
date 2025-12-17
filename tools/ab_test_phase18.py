#!/usr/bin/env python3
"""A/B Test Script for Phase 18 Balance Fails Investigation.

This script tests which Phase 18 weapon property (crit_threshold or damage_type)
is causing the monster_hit_rate drift in the balance suite FAILs.

It runs the two failing scenarios in 4 different configurations:
1. MATERIAL_ONLY: Phase 18 properties disabled (baseline)
2. DAMAGE_TYPE_ONLY: Only damage_type enabled
3. CRIT_THRESHOLD_ONLY: Only crit_threshold enabled  
4. BOTH_ENABLED: Both properties enabled (current behavior)

Usage:
    python3 tools/ab_test_phase18.py
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple


# Scenarios to test (the two FAILs)
TEST_SCENARIOS = [
    {"id": "depth3_orc_brutal_vicious", "runs": 50, "turn_limit": 110},
    {"id": "depth2_orc_baseline_masterwork", "runs": 40, "turn_limit": 100},
]

# Test configurations
CONFIGURATIONS = {
    "MATERIAL_ONLY": {
        "PHASE18_CRIT_THRESHOLD": "0",
        "PHASE18_DAMAGE_TYPE": "0",
        "description": "Material only (Phase 18 disabled)",
    },
    "DAMAGE_TYPE_ONLY": {
        "PHASE18_CRIT_THRESHOLD": "0",
        "PHASE18_DAMAGE_TYPE": "1",
        "description": "Damage type only",
    },
    "CRIT_THRESHOLD_ONLY": {
        "PHASE18_CRIT_THRESHOLD": "1",
        "PHASE18_DAMAGE_TYPE": "0",
        "description": "Crit threshold only",
    },
    "BOTH_ENABLED": {
        "PHASE18_CRIT_THRESHOLD": "1",
        "PHASE18_DAMAGE_TYPE": "1",
        "description": "Both enabled (current)",
    },
}

# Baseline values from reports/baselines/balance_suite_baseline.json
BASELINE_MONSTER_HIT_RATES = {
    "depth3_orc_brutal_vicious": 0.2919254658385093,
    "depth2_orc_baseline_masterwork": 0.30303030303030304,
}


def run_scenario_with_config(
    scenario_id: str,
    runs: int,
    turn_limit: int,
    config_name: str,
    env_vars: Dict[str, str],
    output_path: Path
) -> Tuple[bool, Dict[str, Any]]:
    """Run a scenario with specific environment configuration.
    
    Args:
        scenario_id: Scenario to run
        runs: Number of runs
        turn_limit: Turn limit
        config_name: Name of configuration (for display)
        env_vars: Environment variables to set
        output_path: Where to write JSON output
        
    Returns:
        Tuple of (success: bool, metrics: dict)
    """
    print(f"    Config: {config_name} - {env_vars}")
    
    # Set up environment
    env = os.environ.copy()
    env.update(env_vars)
    
    # Run ecosystem_sanity
    cmd = [
        "python3",
        "ecosystem_sanity.py",
        "--scenario", scenario_id,
        "--runs", str(runs),
        "--turn-limit", str(turn_limit),
        "--player-bot", "tactical_fighter",
        "--export-json", str(output_path),
    ]
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode != 0:
            print(f"      ⚠️  Scenario failed (exit {result.returncode})")
            return False, {}
        
        # Load and extract metrics
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        metrics = data.get("metrics", {})
        monster_attacks = metrics.get("total_monster_attacks", 0)
        monster_hits = metrics.get("total_monster_hits", 0)
        
        monster_hit_rate = (monster_hits / monster_attacks) if monster_attacks > 0 else 0.0
        
        result_metrics = {
            "monster_attacks": monster_attacks,
            "monster_hits": monster_hits,
            "monster_hit_rate": monster_hit_rate,
        }
        
        print(f"      ✓ Monster hit rate: {monster_hit_rate:.4f}")
        return True, result_metrics
        
    except subprocess.TimeoutExpired:
        print(f"      ⚠️  Timeout (>10 minutes)")
        return False, {}
    except Exception as e:
        print(f"      ⚠️  Exception: {e}")
        return False, {}


def main():
    """Run A/B test matrix."""
    print("=" * 80)
    print("Phase 18 Balance Fails A/B Test")
    print("=" * 80)
    print()
    print("Testing scenarios:")
    for scenario in TEST_SCENARIOS:
        baseline = BASELINE_MONSTER_HIT_RATES.get(scenario["id"], 0.0)
        print(f"  - {scenario['id']} (baseline monster_hit_rate: {baseline:.4f})")
    print()
    print("Configurations:")
    for name, config in CONFIGURATIONS.items():
        print(f"  - {name}: {config['description']}")
    print()
    print("=" * 80)
    print()
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("reports/ab_test_phase18") / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Results storage
    all_results = {}
    
    # Run test matrix
    for scenario in TEST_SCENARIOS:
        scenario_id = scenario["id"]
        runs = scenario["runs"]
        turn_limit = scenario["turn_limit"]
        baseline_hit_rate = BASELINE_MONSTER_HIT_RATES.get(scenario_id, 0.0)
        
        print(f"Testing: {scenario_id}")
        print(f"  Baseline monster_hit_rate: {baseline_hit_rate:.4f}")
        print()
        
        scenario_results = {}
        
        for config_name, config in CONFIGURATIONS.items():
            env_vars = {k: v for k, v in config.items() if k.startswith("PHASE18")}
            output_path = output_dir / f"{scenario_id}_{config_name}.json"
            
            success, metrics = run_scenario_with_config(
                scenario_id, runs, turn_limit, config_name, env_vars, output_path
            )
            
            if success:
                hit_rate = metrics["monster_hit_rate"]
                delta = hit_rate - baseline_hit_rate
                scenario_results[config_name] = {
                    "monster_hit_rate": hit_rate,
                    "delta_from_baseline": delta,
                    "metrics": metrics,
                }
                print(f"      Delta from baseline: {delta:+.4f}")
            else:
                scenario_results[config_name] = None
            
            print()
        
        all_results[scenario_id] = scenario_results
        print()
    
    # Save full results
    results_path = output_dir / "ab_test_results.json"
    with open(results_path, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "scenarios": TEST_SCENARIOS,
            "configurations": CONFIGURATIONS,
            "baselines": BASELINE_MONSTER_HIT_RATES,
            "results": all_results,
        }, f, indent=2)
    
    print("=" * 80)
    print("A/B Test Complete")
    print("=" * 80)
    print()
    print(f"Results saved to: {output_dir}")
    print()
    
    # Print summary table
    print("SUMMARY TABLE")
    print("=" * 80)
    print()
    
    for scenario_id, scenario_results in all_results.items():
        baseline = BASELINE_MONSTER_HIT_RATES[scenario_id]
        print(f"Scenario: {scenario_id}")
        print(f"  Baseline: {baseline:.4f}")
        print()
        print(f"  {'Configuration':<25} {'Hit Rate':>10} {'Delta':>10} {'Status':>10}")
        print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*10}")
        
        for config_name in CONFIGURATIONS.keys():
            result = scenario_results.get(config_name)
            if result:
                hit_rate = result["monster_hit_rate"]
                delta = result["delta_from_baseline"]
                
                # Classify status (using balance suite thresholds)
                if abs(delta) < 0.05:
                    status = "PASS"
                elif abs(delta) < 0.10:
                    status = "WARN"
                else:
                    status = "FAIL"
                
                print(f"  {config_name:<25} {hit_rate:>10.4f} {delta:>+10.4f} {status:>10}")
            else:
                print(f"  {config_name:<25} {'FAILED':>10} {'N/A':>10} {'ERROR':>10}")
        
        print()
    
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Review the summary table above")
    print("  2. Identify which configuration(s) trigger the FAIL")
    print("  3. Analyze the causal mechanism")
    print("  4. Document findings in docs/INVESTIGATIONS/balance_suite_orc_hit_rate_fails.md")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

