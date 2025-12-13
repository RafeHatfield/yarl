#!/usr/bin/env python3
"""Generate bot survivability summary from soak telemetry JSONL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List, Tuple

DEFAULT_INPUT_DIR = Path("reports/soak")


def _percentiles(values: List[float]) -> Tuple[float, float, float]:
    if not values:
        return (0.0, 0.0, 0.0)
    ordered = sorted(values)
    n = len(ordered)

    def pick(p: float) -> float:
        if n == 1:
            return ordered[0]
        idx = p * (n - 1)
        lower = int(idx)
        upper = min(lower + 1, n - 1)
        weight = idx - lower
        return ordered[lower] * (1 - weight) + ordered[upper] * weight

    return (pick(0.25), pick(0.50), pick(0.75))


def _iter_records(paths: Iterable[Path]):
    """Iterate over all JSONL records from given paths.
    
    Yields dict records from JSONL files. If path is a directory,
    searches for *soak*.jsonl files (or *.jsonl as fallback).
    """
    import sys
    
    for path in paths:
        if not path.exists():
            continue
        if path.is_dir():
            # Find all JSONL files in directory with soak pattern
            jsonl_files = sorted(path.glob("*soak*.jsonl"))
            if not jsonl_files:
                # Fallback to any JSONL file
                jsonl_files = sorted(path.glob("*.jsonl"))
            
            for file_path in jsonl_files:
                yield from _iter_records([file_path])
            continue
        
        # It's a file - read all lines
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    yield json.loads(line)
        except Exception as e:
            print(f"Warning: Failed to read {path}: {e}", file=sys.stderr)
            continue


def _is_heal_event(decision: dict) -> bool:
    """Check if a bot decision represents a healing action."""
    decision_type = (decision.get("decision_type") or "").lower()
    action_type = (decision.get("action_type") or "").lower()
    action = (decision.get("action") or "").lower()
    
    # Check for potion/heal keywords in any action field
    return (
        "potion" in decision_type or "heal" in decision_type or
        "potion" in action_type or "heal" in action_type or
        "potion" in action or "heal" in action or
        decision_type == "drink_potion"
    )


def summarize(records: Iterable[dict]) -> dict:
    heal_percents: List[float] = []
    death_hp_percents: List[float] = []
    deaths_total = 0
    deaths_with_potions = 0
    deaths_without_potions = 0
    scenario_buckets = {}
    seen_scenarios = set()  # Track all scenarios seen, not just deaths

    for rec in records:
        bot_decisions = rec.get("bot_decisions") or []
        survivability = rec.get("survivability") or {}
        run_metrics = rec.get("run_metrics") or {}
        
        # Extract scenario_id from multiple possible locations
        scenario_id = (
            survivability.get("scenario_id")
            or run_metrics.get("scenario_id")
            or run_metrics.get("scenario")
        )
        
        # Fallback: extract from first bot_decision if available
        if not scenario_id and bot_decisions:
            scenario_id = bot_decisions[0].get("scenario_id")
        
        # Track scenario if found (even for non-death runs)
        if scenario_id and scenario_id not in seen_scenarios:
            seen_scenarios.add(scenario_id)
            # Initialize bucket if this is a new scenario
            if scenario_id not in scenario_buckets:
                scenario_buckets[scenario_id] = {"deaths": 0, "unused_potion_deaths": 0}

        # Heal decisions - iterate through bot_decisions array
        for decision in bot_decisions:
            if not _is_heal_event(decision):
                continue
            
            # Extract HP percentage at time of heal
            hp_percent = decision.get("hp_percent")
            if hp_percent is None and decision.get("hp") is not None and decision.get("max_hp"):
                try:
                    hp_percent = decision["hp"] / decision["max_hp"]
                except Exception:
                    hp_percent = None
            
            if hp_percent is not None:
                heal_percents.append(float(hp_percent))

        # Death classification - check run_metrics outcome
        outcome = run_metrics.get("outcome")
        if outcome == "death":
            deaths_total += 1
            potions_remaining = survivability.get("potions_remaining_on_death")
            
            # Count deaths with unused potions
            if potions_remaining and potions_remaining > 0:
                deaths_with_potions += 1
            else:
                deaths_without_potions += 1

            # Track HP at death
            hp_percent = survivability.get("final_hp_percent")
            if hp_percent is not None:
                death_hp_percents.append(float(hp_percent))

            # Scenario breakdown
            if scenario_id:
                bucket = scenario_buckets.setdefault(
                    scenario_id, {"deaths": 0, "unused_potion_deaths": 0}
                )
                bucket["deaths"] += 1
                if potions_remaining and potions_remaining > 0:
                    bucket["unused_potion_deaths"] += 1

    p25, p50, p75 = _percentiles(heal_percents)
    return {
        "heal_events": len(heal_percents),
        "heal_min": min(heal_percents) if heal_percents else 0.0,
        "heal_max": max(heal_percents) if heal_percents else 0.0,
        "heal_mean": sum(heal_percents) / len(heal_percents) if heal_percents else 0.0,
        "heal_p25": p25,
        "heal_p50": p50,
        "heal_p75": p75,
        "deaths_total": deaths_total,
        "deaths_with_potions": deaths_with_potions,
        "deaths_without_potions": deaths_without_potions,
        "death_hp_percents": death_hp_percents,
        "scenario_buckets": scenario_buckets,
    }


def render_markdown(summary: dict) -> str:
    deaths_total = summary["deaths_total"]
    with_potions = summary["deaths_with_potions"]
    without_potions = summary["deaths_without_potions"]
    deaths_pct = lambda x: (x / deaths_total * 100) if deaths_total else 0.0

    lines = []
    lines.append("# Bot Survivability Report")
    lines.append("")
    
    # Global Heal Thresholds
    lines.append("## Global Heal Thresholds")
    if summary["heal_events"] == 0:
        lines.append("- Heal events: 0")
        lines.append("")
        lines.append("_No heal events found in the input files — did the bot drink any potions during this soak run?_")
    else:
        lines.append(f"- Heal events: {summary['heal_events']}")
        lines.append(
            f"- HP% at heal: mean {summary['heal_mean']*100:.1f}% "
            f"(P25 {summary['heal_p25']*100:.1f}%, P50 {summary['heal_p50']*100:.1f}%, "
            f"P75 {summary['heal_p75']*100:.1f}%)"
        )
        lines.append(
            f"- Range: {summary['heal_min']*100:.1f}% – {summary['heal_max']*100:.1f}%"
        )
    lines.append("")
    
    # Deaths with Unused Potions
    lines.append("## Deaths with Unused Potions")
    if deaths_total == 0:
        lines.append("- Total deaths: 0")
        lines.append("")
        lines.append("_No death events found in the input files — survivability may be very high or the soak run was too short._")
    else:
        lines.append(f"- Total deaths: {deaths_total}")
        lines.append(
            f"- Died with 0 potions: {without_potions} ({deaths_pct(without_potions):.1f}%)"
        )
        lines.append(
            f"- Died with ≥1 potion: {with_potions} ({deaths_pct(with_potions):.1f}%)"
        )
    lines.append("")
    
    # HP% at Death
    lines.append("## HP% at Death")
    if summary["death_hp_percents"]:
        d25, d50, d75 = _percentiles(summary["death_hp_percents"])
        lines.append(
            f"- HP% at death: mean {sum(summary['death_hp_percents'])/len(summary['death_hp_percents'])*100:.1f}% "
            f"(P25 {d25*100:.1f}%, P50 {d50*100:.1f}%, P75 {d75*100:.1f}%)"
        )
    else:
        lines.append("- No death events recorded.")
    lines.append("")
    
    # Scenario Breakdown
    lines.append("## Scenario Breakdown")
    if not summary["scenario_buckets"]:
        lines.append("- No scenario data available.")
        lines.append("")
        lines.append("_Scenario-level breakdowns require scenario_id in the telemetry data._")
    else:
        lines.append("")
        lines.append("| Scenario | Deaths | Unused Potion Deaths | % Unused |")
        lines.append("|----------|--------|---------------------|----------|")
        for scenario_id, bucket in sorted(summary["scenario_buckets"].items()):
            deaths = bucket["deaths"]
            unused = bucket["unused_potion_deaths"]
            pct_unused = (unused / deaths * 100) if deaths else 0.0
            lines.append(
                f"| {scenario_id} | {deaths} | {unused} | {pct_unused:.1f}% |"
            )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bot survivability report from soak telemetry.")
    parser.add_argument(
        "--input",
        nargs="*",
        type=Path,
        default=[DEFAULT_INPUT_DIR],
        help="JSONL telemetry files or directories (default: logs/*soak*.jsonl)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output path for markdown (stdout if omitted).",
    )
    return parser.parse_args()


def main() -> int:
    import sys
    
    args = parse_args()
    
    # Collect all records
    records = list(_iter_records(args.input))
    
    # Log what we found
    if not records:
        print(f"WARNING: No events found in input files: {args.input}", file=sys.stderr)
        print(f"         Make sure you ran 'make bot-soak' with telemetry enabled.", file=sys.stderr)
    else:
        print(f"INFO: Read {len(records)} events from {args.input}", file=sys.stderr)
        
        # Warn if dataset is very small
        if len(records) < 200:
            print(f"WARNING: Small dataset ({len(records)} events) - results may not be statistically significant.", file=sys.stderr)
            print(f"         Consider running more soak runs for better insights.", file=sys.stderr)
    
    # Generate summary and report
    summary = summarize(records)
    
    # Warn if no scenario data found
    if records and not summary.get("scenario_buckets"):
        print(f"WARNING: No scenario data found in events.", file=sys.stderr)
        print(f"         Scenario breakdowns require scenario_id in the telemetry.", file=sys.stderr)
    
    report = render_markdown(summary)

    # Write or print report
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
