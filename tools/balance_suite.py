#!/usr/bin/env python3
"""Balance Suite - Comprehensive ecosystem scenario matrix runner.

Phase 18 QOL: Orchestrates ecosystem_sanity runs across a curated scenario matrix,
generates unified reports, and compares against stored baselines.

Usage:
    # Compare mode (CI) - exits non-zero on FAIL
    python3 tools/balance_suite.py
    python3 tools/balance_suite.py --fast
    python3 tools/balance_suite.py --baseline reports/baselines/custom_baseline.json
    
    # Baseline update mode - writes baseline, exits 0 on success
    python3 tools/balance_suite.py --update-baseline
    python3 tools/balance_suite.py --update-baseline --fast
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# SCENARIO MATRIX CONFIGURATION
# ============================================================================

# Core scenarios to run (base + weapon variants)
SCENARIO_MATRIX = [
    # Depth 3 Orc Brutal + variants
    {"id": "depth3_orc_brutal", "runs": 50, "turn_limit": 110},
    {"id": "depth3_orc_brutal_keen", "runs": 50, "turn_limit": 110},
    {"id": "depth3_orc_brutal_vicious", "runs": 50, "turn_limit": 110},
    {"id": "depth3_orc_brutal_fine", "runs": 50, "turn_limit": 110},
    {"id": "depth3_orc_brutal_masterwork", "runs": 50, "turn_limit": 110},
    
    # Depth 5 Zombie + variants
    {"id": "depth5_zombie", "runs": 50, "turn_limit": 150},
    {"id": "depth5_zombie_keen", "runs": 50, "turn_limit": 150},
    {"id": "depth5_zombie_vicious", "runs": 50, "turn_limit": 150},
    {"id": "depth5_zombie_fine", "runs": 50, "turn_limit": 150},
    {"id": "depth5_zombie_masterwork", "runs": 50, "turn_limit": 150},
    
    # Depth 2 Orc Baseline + variants
    {"id": "depth2_orc_baseline", "runs": 40, "turn_limit": 100},
    {"id": "depth2_orc_baseline_keen", "runs": 40, "turn_limit": 100},
    {"id": "depth2_orc_baseline_vicious", "runs": 40, "turn_limit": 100},
    {"id": "depth2_orc_baseline_fine", "runs": 40, "turn_limit": 100},
    {"id": "depth2_orc_baseline_masterwork", "runs": 40, "turn_limit": 100},
    
    # Phase 19 Monster Identity Scenarios
    {"id": "monster_slime_identity", "runs": 30, "turn_limit": 80},
    {"id": "monster_skeleton_identity", "runs": 30, "turn_limit": 200},
    {"id": "monster_orc_chieftain_identity", "runs": 30, "turn_limit": 200},
    {"id": "monster_orc_shaman_identity", "runs": 30, "turn_limit": 200},
    {"id": "monster_necromancer_identity", "runs": 30, "turn_limit": 250},
    {"id": "monster_bone_necromancer_identity", "runs": 30, "turn_limit": 250},
    {"id": "monster_plague_necromancer_identity", "runs": 30, "turn_limit": 250},
    {"id": "monster_exploder_necromancer_identity", "runs": 30, "turn_limit": 250},
    {"id": "monster_wraith_identity", "runs": 30, "turn_limit": 200},
    {"id": "troll_identity", "runs": 30, "turn_limit": 100},
]

# Drift thresholds for WARN/FAIL classification
THRESHOLDS = {
    "death_rate": {"warn": 0.10, "fail": 0.20},
    "player_hit_rate": {"warn": 0.05, "fail": 0.10},
    "monster_hit_rate": {"warn": 0.05, "fail": 0.10},
    "pressure_index": {"warn": 5.0, "fail": 10.0},
    "bonus_attacks_per_run": {"warn": 2.0, "fail": 4.0},
}


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


def normalize_metrics(raw_json: Dict[str, Any]) -> Dict[str, Any]:
    """Extract normalized metrics from ecosystem_sanity JSON export.
    
    Args:
        raw_json: Raw JSON from ecosystem_sanity.py --export-json
        
    Returns:
        Normalized metrics dict
    """
    scenario_id = raw_json.get("scenario_id", "unknown")
    runs = raw_json.get("runs", 1)
    metrics = raw_json.get("metrics", {})
    
    player_attacks = metrics.get("total_player_attacks", 0)
    monster_attacks = metrics.get("total_monster_attacks", 0)
    player_hits = metrics.get("total_player_hits", 0)
    monster_hits = metrics.get("total_monster_hits", 0)
    bonus_attacks = metrics.get("total_bonus_attacks_triggered", 0)
    player_deaths = metrics.get("player_deaths", 0)
    
    def safe_div(n: float, d: float) -> float:
        return n / d if d else 0.0
    
    return {
        "scenario_id": scenario_id,
        "runs": runs,
        "deaths": player_deaths,
        "death_rate": safe_div(player_deaths, runs),
        "player_hit_rate": safe_div(player_hits, player_attacks),
        "monster_hit_rate": safe_div(monster_hits, monster_attacks),
        "pressure_index": safe_div(monster_attacks, runs) - safe_div(player_attacks, runs),
        "bonus_attacks_per_run": safe_div(bonus_attacks, runs),
    }


def compute_deltas(current: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, float]:
    """Compute deltas between current metrics and baseline.
    
    Args:
        current: Current normalized metrics
        baseline: Baseline normalized metrics
        
    Returns:
        Dict of metric_name -> delta
    """
    deltas = {}
    for key in ["death_rate", "player_hit_rate", "monster_hit_rate", "pressure_index", "bonus_attacks_per_run"]:
        curr_val = current.get(key, 0.0)
        base_val = baseline.get(key, 0.0)
        deltas[key] = curr_val - base_val
    return deltas


def classify_verdict(deltas: Dict[str, float]) -> str:
    """Classify verdict based on deltas and thresholds.
    
    Args:
        deltas: Dict of metric_name -> delta
        
    Returns:
        "PASS", "WARN", or "FAIL"
    """
    verdict = "PASS"
    for key, delta in deltas.items():
        if key not in THRESHOLDS:
            continue
        abs_delta = abs(delta)
        if abs_delta >= THRESHOLDS[key]["fail"]:
            return "FAIL"
        if abs_delta >= THRESHOLDS[key]["warn"]:
            verdict = "WARN"
    return verdict


def generate_markdown_report(
    summary: Dict[str, Dict[str, Any]],
    baseline: Optional[Dict[str, Dict[str, Any]]],
    verdict_summary: Dict[str, int],
    output_path: Path,
) -> None:
    """Generate unified markdown report.
    
    Args:
        summary: Dict of scenario_id -> normalized metrics
        baseline: Optional baseline summary
        verdict_summary: Dict of verdict -> count
        output_path: Where to write markdown
    """
    lines = []
    lines.append("# Balance Suite Report")
    lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"\n**Scenarios:** {len(summary)}")
    
    # Verdict summary
    lines.append("\n## Verdict Summary")
    if baseline is None:
        lines.append("\n**Status:** NO_BASELINE")
        lines.append("\nNo baseline found. Run `make balance-suite-update-baseline` to create one.")
    else:
        lines.append(f"\n- PASS: {verdict_summary.get('PASS', 0)}")
        lines.append(f"- WARN: {verdict_summary.get('WARN', 0)}")
        lines.append(f"- FAIL: {verdict_summary.get('FAIL', 0)}")
    
    # Per-scenario details
    lines.append("\n## Scenario Details")
    for scenario_id in sorted(summary.keys()):
        metrics = summary[scenario_id]
        lines.append(f"\n### {scenario_id}")
        lines.append(f"\n- Runs: {metrics['runs']}")
        lines.append(f"- Deaths: {metrics['deaths']} (rate: {metrics['death_rate']:.2%})")
        lines.append(f"- Player Hit Rate: {metrics['player_hit_rate']:.2%}")
        lines.append(f"- Monster Hit Rate: {metrics['monster_hit_rate']:.2%}")
        lines.append(f"- Pressure Index: {metrics['pressure_index']:.2f}")
        lines.append(f"- Bonus Attacks/Run: {metrics['bonus_attacks_per_run']:.2f}")
        
        if baseline and scenario_id in baseline:
            base_metrics = baseline[scenario_id]
            deltas = compute_deltas(metrics, base_metrics)
            verdict = classify_verdict(deltas)
            lines.append(f"\n**Verdict:** {verdict}")
            lines.append("\n**Deltas from Baseline:**")
            lines.append(f"- Death Rate: {deltas['death_rate']:+.2%}")
            lines.append(f"- Player Hit Rate: {deltas['player_hit_rate']:+.2%}")
            lines.append(f"- Monster Hit Rate: {deltas['monster_hit_rate']:+.2%}")
            lines.append(f"- Pressure Index: {deltas['pressure_index']:+.2f}")
            lines.append(f"- Bonus Attacks/Run: {deltas['bonus_attacks_per_run']:+.2f}")
    
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n✅ Markdown report written: {output_path}")


def generate_verdict_json(
    summary: Dict[str, Dict[str, Any]],
    baseline: Optional[Dict[str, Dict[str, Any]]],
    verdict_summary: Dict[str, int],
    output_path: Path,
) -> None:
    """Generate machine-readable verdict JSON.
    
    Args:
        summary: Dict of scenario_id -> normalized metrics
        baseline: Optional baseline summary
        verdict_summary: Dict of verdict -> count
        output_path: Where to write JSON
    """
    if baseline is None:
        verdict_data = {
            "status": "NO_BASELINE",
            "acceptance_status": "PASS",  # No baseline = not blocked
            "timestamp": datetime.now().isoformat(),
            "scenarios": len(summary),
            "verdicts": {},
        }
    else:
        # Determine acceptance_status based on verdicts
        if verdict_summary.get("FAIL", 0) > 0:
            acceptance_status = "FAIL"
        elif verdict_summary.get("WARN", 0) > 0:
            acceptance_status = "WARN"
        else:
            acceptance_status = "PASS"
        
        verdict_data = {
            "status": "COMPLETED",
            "acceptance_status": acceptance_status,
            "timestamp": datetime.now().isoformat(),
            "scenarios": len(summary),
            "verdicts": verdict_summary,
            "details": {},
        }
        for scenario_id, metrics in summary.items():
            if scenario_id in baseline:
                deltas = compute_deltas(metrics, baseline[scenario_id])
                verdict_data["details"][scenario_id] = {
                    "verdict": classify_verdict(deltas),
                    "deltas": deltas,
                }
    
    output_path.write_text(json.dumps(verdict_data, indent=2), encoding="utf-8")
    print(f"✅ Verdict JSON written: {output_path}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Balance Suite - Ecosystem scenario matrix runner")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory (default: reports/balance_suite/<timestamp>)",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("reports/baselines/balance_suite_baseline.json"),
        help="Baseline JSON file (default: reports/baselines/balance_suite_baseline.json)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip bot soak (not yet implemented)",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Update baseline mode: writes new baseline and exits 0 (ignores FAIL verdicts)",
    )
    parser.add_argument(
        "--seed-base",
        type=int,
        default=1337,
        help="Base seed for deterministic scenario runs (default: 1337)",
    )
    
    args = parser.parse_args()
    
    # Setup output directory
    if args.out_dir:
        out_dir = args.out_dir
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = Path("reports/balance_suite") / timestamp
    
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = out_dir / "metrics" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print("Balance Suite - Ecosystem Scenario Matrix")
    print(f"{'='*60}")
    print(f"Output Directory: {out_dir}")
    print(f"Baseline: {args.baseline}")
    print(f"Fast Mode: {args.fast}")
    print(f"Update Baseline Mode: {args.update_baseline}")
    print(f"Seed Base: {args.seed_base}")
    print(f"{'='*60}\n")
    
    # Load baseline (if exists) - for comparison/visibility only in update mode
    baseline_summary = None
    if args.baseline.exists():
        print(f"📊 Loading baseline: {args.baseline}")
        baseline_summary = json.loads(args.baseline.read_text(encoding="utf-8"))
        if args.update_baseline:
            print("    (comparison for visibility only; will write new baseline)")
    else:
        print(f"⚠️  No baseline found at {args.baseline}")
        if args.update_baseline:
            print("    (will create new baseline)")
        else:
            print("    Run 'make balance-suite-update-baseline' to create one.\n")
    
    # Run scenarios
    print(f"\n🎯 Running {len(SCENARIO_MATRIX)} scenarios...\n")
    summary = {}
    failed = []
    
    for scenario_config in SCENARIO_MATRIX:
        scenario_id = scenario_config["id"]
        runs = scenario_config["runs"]
        turn_limit = scenario_config["turn_limit"]
        raw_json_path = raw_dir / f"{scenario_id}.json"
        
        success = run_ecosystem_scenario(scenario_id, runs, turn_limit, raw_json_path, args.seed_base)
        if not success:
            failed.append(scenario_id)
            continue
        
        # Parse and normalize
        try:
            raw_json = json.loads(raw_json_path.read_text(encoding="utf-8"))
            normalized = normalize_metrics(raw_json)
            summary[scenario_id] = normalized
        except Exception as e:
            print(f"    ⚠️  Failed to parse {scenario_id}: {e}")
            failed.append(scenario_id)
    
    print(f"\n✅ Completed {len(summary)}/{len(SCENARIO_MATRIX)} scenarios")
    if failed:
        print(f"⚠️  Failed scenarios: {', '.join(failed)}")
    
    # Compute verdict summary
    verdict_summary = {"PASS": 0, "WARN": 0, "FAIL": 0}
    if baseline_summary:
        for scenario_id, metrics in summary.items():
            if scenario_id in baseline_summary:
                deltas = compute_deltas(metrics, baseline_summary[scenario_id])
                verdict = classify_verdict(deltas)
                verdict_summary[verdict] += 1
    
    # Generate reports
    print("\n📝 Generating reports...")
    generate_markdown_report(summary, baseline_summary, verdict_summary, out_dir / "balance_report.md")
    generate_verdict_json(summary, baseline_summary, verdict_summary, out_dir / "verdict.json")
    
    # Write summary JSON (for future baseline creation)
    summary_json_path = out_dir / "summary.json"
    summary_json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"✅ Summary JSON written: {summary_json_path}")
    
    # Create/update latest symlink (or latest.txt on macOS)
    latest_path = Path("reports/balance_suite/latest.txt")
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(str(out_dir.resolve()), encoding="utf-8")
    print(f"✅ Latest pointer updated: {latest_path}")
    
    # Handle baseline update mode
    if args.update_baseline:
        print(f"\n{'='*60}")
        print("🎯 BASELINE UPDATE MODE")
        print(f"{'='*60}")
        
        # Write summary.json directly to the baseline path
        args.baseline.parent.mkdir(parents=True, exist_ok=True)
        args.baseline.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"✅ Baseline written: {args.baseline}")
        
        # Show comparison for visibility (if old baseline existed)
        if baseline_summary is not None:
            print(f"\n📊 Comparison with previous baseline:")
            print(f"  PASS: {verdict_summary['PASS']}")
            print(f"  WARN: {verdict_summary['WARN']}")
            print(f"  FAIL: {verdict_summary['FAIL']}")
            if verdict_summary["FAIL"] > 0:
                print("\n⚠️  Note: FAILs against OLD baseline (now overwritten)")
        else:
            print("\n📊 First baseline created (no previous baseline to compare)")
        
        print(f"\n{'='*60}")
        print("✅ Baseline update complete - exiting with code 0")
        print(f"{'='*60}\n")
        return 0
    
    # Compare mode - final verdict
    print(f"\n{'='*60}")
    if baseline_summary is None:
        print("Status: NO_BASELINE")
        print("Acceptance: PASS (no baseline to compare against)")
        print("\nTo create a baseline, run:")
        print("  make balance-suite-update-baseline")
    else:
        print(f"Status: COMPLETED")
        print(f"  PASS: {verdict_summary['PASS']}")
        print(f"  WARN: {verdict_summary['WARN']}")
        print(f"  FAIL: {verdict_summary['FAIL']}")
        
        if verdict_summary["FAIL"] > 0:
            print("\n❌ FAIL: One or more scenarios exceeded thresholds")
            print("   Acceptance: FAIL (merge blocked)")
            print("   See docs/BALANCE_ACCEPTANCE_CONTRACT.md")
            print(f"{'='*60}\n")
            return 1
        elif verdict_summary["WARN"] > 0:
            print("\n⚠️  WARN: Some scenarios show notable drift")
            print("   Acceptance: WARN (may merge after review)")
            print("   See docs/BALANCE_ACCEPTANCE_CONTRACT.md")
        else:
            print("\n✅ PASS: All scenarios within acceptable thresholds")
            print("   Acceptance: PASS (may merge)")
    
    print(f"{'='*60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
