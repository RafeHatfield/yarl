#!/usr/bin/env python3
"""Depth Pressure Report Generator — Phase 22.4

Loads a directory of exported scenario JSON files (produced by
tools/collect_depth_pressure_data.py or ecosystem_sanity.py --export-json)
and produces:

  - Markdown report: <dir>/depth_pressure_report.md
  - CSV table:       <dir>/depth_pressure_table.csv

Usage:
    python3 analysis/depth_pressure_report.py <json_dir>
    python3 analysis/depth_pressure_report.py reports/depth_pressure/20260303_120000/

The input directory must contain at least one JSON file whose `scenario_id`
matches a key in KNOWN_SCENARIO_CONFIGS (analysis/depth_pressure_model.py).

Scenarios whose IDs are not in KNOWN_SCENARIO_CONFIGS are skipped with a
warning (they cannot be processed without the monster HP budget).

Metric Definitions (canonical):
  All definitions match analysis/depth_pressure_model.py.

  E[DMG_P]  = avg player damage per landed hit
             = total_player_damage_dealt / total_player_hits

  P(hit_P)  = player hit rate
             = total_player_hits / total_player_attacks

  DPR_P     = player damage per round (expected)
             = E[DMG_P] * P(hit_P)

  E[DMG_M]  = avg monster damage per landed hit
             = total_monster_damage_dealt / total_monster_hits

  P(hit_M)  = monster hit rate
             = total_monster_hits / total_monster_attacks

  DPR_M     = monster damage per round (expected)
             = E[DMG_M] * P(hit_M)

  H_PM      = player hits-to-kill monster (proxy)
             = avg_monster_HP / DPR_P
             where avg_monster_HP = monster_hp_budget_per_run / avg_kills_per_run

  H_MP      = monster hits-to-kill player (survival budget)
             = player_HP / DPR_M
             (player_HP = 54 from entities.yaml)

  DMG/Enc   = avg monster damage taken per enemy killed
             = total_monster_damage_dealt / total_kills

  T/Kill    = avg turns per enemy killed
             = total_turns / total_kills

  Death%    = player death rate
             = player_deaths / runs

Known Limitations:
  - HP budget is pre-computed per scenario (see KNOWN_SCENARIO_CONFIGS).
    If the scenario composition changes, the budget must be updated manually.
  - H_PM uses average monster HP derived from observed kill count, not
    per-spawn HP tracking. If the player kills fewer enemies (e.g., dies
    early), avg_monster_HP may be inflated.
  - Zombie scenarios (depth 4 and 5) use the zombie override curve (no
    depth scaling) and are NOT directly comparable to orc scenarios at the
    same depth. The report marks these with a faction note.
  - Depth 4 has TWO data points: orcs (midgame_pressure_probe_orcs) and
    plague zombies (depth4_plague). They are listed separately in the table
    because their faction, scaling, and HP budgets are fundamentally different.
  - All metrics are averages over N runs. Variance is not reported here;
    use the raw JSON for per-run analysis.
  - 'total_player_damage_dealt' and 'total_monster_damage_dealt' require
    Phase 22.4 instrumentation. Pre-Phase-22.4 JSON files will produce
    STOP warnings and be excluded from the curve.
"""

import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure repo root is on the path when called as a script
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from analysis.depth_pressure_model import (
    KNOWN_SCENARIO_CONFIGS,
    PressureMetrics,
    DepthCurvePoint,
    compute_pressure_metrics,
    build_depth_curve,
    evaluate_against_targets,
    format_pressure_table,
    format_target_comparison,
    format_scaling_diagnosis,
)


# ---------------------------------------------------------------------------
# JSON loading
# ---------------------------------------------------------------------------

def load_json_exports(json_dir: Path) -> List[Dict[str, Any]]:
    """Load all *.json files from a directory, excluding manifest.json."""
    payloads = []
    skip = {"manifest.json"}
    for p in sorted(json_dir.glob("*.json")):
        if p.name in skip:
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["_source_file"] = p.name
            payloads.append(data)
        except Exception as e:
            print(f"WARNING: Could not load '{p}': {e}", file=sys.stderr)
    return payloads


# ---------------------------------------------------------------------------
# Pressure metric extraction
# ---------------------------------------------------------------------------

def extract_pressure_metrics(payloads: List[Dict[str, Any]]) -> List[PressureMetrics]:
    """Convert raw JSON payloads into PressureMetrics objects.

    Scenarios not in KNOWN_SCENARIO_CONFIGS are skipped.
    """
    results = []
    for payload in payloads:
        scenario_id = payload.get("scenario_id", "")
        source = payload.get("_source_file", "?")

        config = KNOWN_SCENARIO_CONFIGS.get(scenario_id)
        if config is None:
            print(
                f"  SKIP: '{scenario_id}' ({source}) — "
                "not in KNOWN_SCENARIO_CONFIGS; cannot compute H_PM without HP budget."
            )
            continue

        metrics_dict = payload.get("metrics", payload)
        pm = compute_pressure_metrics(
            aggregated_metrics=metrics_dict,
            scenario_id=scenario_id,
            depth=config["depth"],
            monster_hp_budget_per_run=config["monster_hp_budget_per_run"],
        )
        results.append(pm)
    return results


# ---------------------------------------------------------------------------
# Markdown report generation
# ---------------------------------------------------------------------------

_METRIC_DEFINITIONS = """\
## Metric Definitions

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| `E[DMG_P]` | `total_player_damage_dealt / total_player_hits` | Avg player damage per landed hit |
| `P(hit_P)` | `total_player_hits / total_player_attacks` | Player hit rate |
| `DPR_P` | `E[DMG_P] × P(hit_P)` | Player expected damage per round |
| `E[DMG_M]` | `total_monster_damage_dealt / total_monster_hits` | Avg monster damage per landed hit |
| `P(hit_M)` | `total_monster_hits / total_monster_attacks` | Monster hit rate |
| `DPR_M` | `E[DMG_M] × P(hit_M)` | Monster expected damage per round |
| `H_PM` | `avg_monster_HP / DPR_P` | Avg rounds for player to kill one monster |
| `H_MP` | `player_HP / DPR_M` | Avg rounds for monsters to kill player (survival budget) |
| `DMG/Enc` | `total_monster_dmg_dealt / total_kills` | Avg monster damage taken per enemy killed |
| `T/Kill` | `total_turns / total_kills` | Avg turns consumed per enemy killed |
| `Death%` | `player_deaths / runs` | Fraction of runs in which the player died |

**Player HP** is 54 (base from `entities.yaml`) and is held constant across all depths.

**avg_monster_HP** is derived from `monster_hp_budget_per_run / (total_kills / runs)`,
i.e., the scaled HP budget for the scenario's spawns divided by the observed average
kill count per run.  If the player consistently dies before clearing all enemies,
`avg_kills_per_run` will be low, inflating this estimate.
"""

_LIMITATIONS = """\
## Known Limitations

1. **Faction mixing across depths.**  Orc scenarios (depths 1–4, 6) and zombie
   scenarios (depths 4–5) use different monster types with different base stats and
   different scaling curves.  Metrics from zombie scenarios are not directly comparable
   to orc metrics at the same depth.  The table marks faction type explicitly.

2. **Zombie curve = no scaling.**  The zombie override curve (`ZOMBIE_CURVE` in
   `balance/depth_scaling.py`) applies 1.0× multipliers at depths 1–6.  Zombie
   scenarios therefore reflect unscaled base stats regardless of dungeon depth.

3. **Depth 4 has two data points.**  `midgame_pressure_probe_orcs` (orcs) and
   `depth4_plague` (plague zombies) are both depth-4 scenarios with different
   faction, composition, and HP budgets.  They are listed on separate rows.

4. **H_PM inflated by early player death.**  If the player dies before killing all
   monsters, the denominator `avg_kills_per_run` is artificially low, making
   `avg_monster_HP` appear larger than the scenario's actual HP budget per kill.

5. **No per-run variance.**  All metrics are aggregated across runs.  High-variance
   scenarios (e.g., a scenario where the player sometimes wins easily and sometimes
   dies immediately) look identical to low-variance scenarios with the same averages.

6. **Instrumentation required.**  `total_player_damage_dealt` and
   `total_monster_damage_dealt` require Phase 22.4 instrumentation in
   `services/scenario_harness.py` and `components/fighter.py`.  JSON exports from
   earlier versions will produce STOP warnings and be excluded from the curve.

7. **This report is purely descriptive.**  No multiplier recommendations are made
   here.  The goal is to establish the real observed pressure curve as ground-truth
   for future tuning decisions.
"""


def _scenario_table_rows(pressure_list: List[PressureMetrics]) -> str:
    """Generate a markdown table of per-scenario details."""
    lines = [
        "| Scenario ID | Depth | Faction | Runs | H_PM | H_MP | DPR_P | DPR_M | "
        "P(hit_P) | P(hit_M) | E[DMG_P] | E[DMG_M] | DMG/Enc | T/Kill | Death% | OK? |",
        "|-------------|-------|---------|------|------|------|-------|-------|"
        "---------|---------|---------|---------|---------|--------|--------|-----|",
    ]
    for pm in sorted(pressure_list, key=lambda x: (x.depth, x.scenario_id)):
        config = KNOWN_SCENARIO_CONFIGS.get(pm.scenario_id, {})
        faction = config.get("description", "—")

        if not pm.data_sufficient:
            warn_str = " / ".join(pm.warnings) if pm.warnings else "insufficient data"
            lines.append(
                f"| `{pm.scenario_id}` | {pm.depth} | {faction} | {pm.runs} | "
                f"— | — | — | — | — | — | — | — | — | — | — | "
                f"⚠ STOP: {warn_str} |"
            )
            continue

        lines.append(
            f"| `{pm.scenario_id}` | {pm.depth} | {faction} | {pm.runs} "
            f"| {pm.player_hits_to_kill:.2f} | {pm.monster_hits_to_kill:.2f} "
            f"| {pm.player_dpr:.2f} | {pm.monster_dpr:.2f} "
            f"| {pm.player_hit_rate:.1%} | {pm.monster_hit_rate:.1%} "
            f"| {pm.avg_player_dmg_per_hit:.2f} | {pm.avg_monster_dmg_per_hit:.2f} "
            f"| {pm.avg_damage_per_encounter:.1f} | {pm.avg_turns_per_enemy:.1f} "
            f"| {pm.player_death_rate:.1%} | ✓ |"
        )

    return "\n".join(lines)


def _warnings_section(pressure_list: List[PressureMetrics]) -> str:
    lines = []
    for pm in pressure_list:
        if pm.warnings:
            lines.append(f"**{pm.scenario_id}** (depth {pm.depth}):")
            for w in pm.warnings:
                lines.append(f"  - {w}")
    if not lines:
        return "_No data quality warnings._"
    return "\n".join(lines)


def generate_markdown_report(
    pressure_list: List[PressureMetrics],
    curve: Dict[int, DepthCurvePoint],
    json_dir: Path,
    runs_per_scenario: int,
    seed_base: Optional[int],
) -> str:
    """Generate the full Markdown pressure report."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    curve_table = format_pressure_table(curve) if curve else "_No complete scenarios to plot._"
    target_table = format_target_comparison(evaluate_against_targets(curve)) if curve else ""
    diag = format_scaling_diagnosis(curve) if len(curve) >= 2 else "_Insufficient depth points for trend analysis._"

    sufficient = [pm for pm in pressure_list if pm.data_sufficient]
    insufficient = [pm for pm in pressure_list if not pm.data_sufficient]

    report_lines = [
        "# Depth Pressure Data Report — Phase 22.4",
        "",
        f"**Generated:** {ts}  ",
        f"**Source directory:** `{json_dir}`  ",
        f"**Runs per scenario:** {runs_per_scenario}  ",
        f"**Seed base:** {seed_base if seed_base is not None else 'not set (non-deterministic)'}  ",
        f"**Scenarios processed:** {len(pressure_list)} total, "
        f"{len(sufficient)} complete, {len(insufficient)} with STOP conditions  ",
        "",
        "> **Purpose:** This report establishes the real observed depth pressure curve",
        "> as ground-truth for future tuning decisions (damage scaling + depth boons).",
        "> It is purely descriptive. No multiplier recommendations are made here.",
        "",
        "---",
        "",
        "## Scenario Coverage",
        "",
        _scenario_table_rows(pressure_list),
        "",
        "---",
        "",
        "## Observed Depth Pressure Curve",
        "",
        "```",
        curve_table,
        "```",
        "",
        "---",
        "",
        "## Target Curve Comparison",
        "",
        "> Targets are design aspirations defined in `analysis/depth_pressure_model.py`.",
        "> They are **not enforced** — this comparison is informational only.",
        "",
        "```",
        target_table if target_table else "_No complete scenarios to compare._",
        "```",
        "",
        "---",
        "",
        "## Scaling System Diagnosis",
        "",
        "```",
        diag,
        "```",
        "",
        "---",
        "",
        _METRIC_DEFINITIONS,
        "",
        "---",
        "",
        _LIMITATIONS,
        "",
        "---",
        "",
        "## Data Quality Warnings",
        "",
        _warnings_section(pressure_list),
        "",
    ]
    return "\n".join(report_lines)


# ---------------------------------------------------------------------------
# CSV generation
# ---------------------------------------------------------------------------

CSV_FIELDS = [
    "scenario_id", "depth", "faction", "runs",
    "data_sufficient",
    "total_player_attacks", "total_player_hits", "total_monster_attacks", "total_monster_hits",
    "total_player_damage_dealt", "total_monster_damage_dealt", "total_kills",
    "player_hit_rate", "monster_hit_rate",
    "avg_player_dmg_per_hit", "avg_monster_dmg_per_hit",
    "player_dpr", "monster_dpr",
    "player_hits_to_kill", "monster_hits_to_kill",
    "avg_damage_per_encounter", "avg_turns_per_enemy",
    "player_deaths", "player_death_rate",
    "monster_hp_budget_per_run",
]


def generate_csv(pressure_list: List[PressureMetrics]) -> str:
    """Generate CSV content from pressure metrics list."""
    import io
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()

    for pm in sorted(pressure_list, key=lambda x: (x.depth, x.scenario_id)):
        config = KNOWN_SCENARIO_CONFIGS.get(pm.scenario_id, {})
        faction = config.get("description", "unknown")
        row = {
            "scenario_id": pm.scenario_id,
            "depth": pm.depth,
            "faction": faction,
            "runs": pm.runs,
            "data_sufficient": pm.data_sufficient,
            "total_player_attacks": pm.total_player_attacks,
            "total_player_hits": pm.total_player_hits,
            "total_monster_attacks": pm.total_monster_attacks,
            "total_monster_hits": pm.total_monster_hits,
            "total_player_damage_dealt": pm.total_player_damage_dealt,
            "total_monster_damage_dealt": pm.total_monster_damage_dealt,
            "total_kills": pm.total_kills,
            "player_hit_rate": round(pm.player_hit_rate, 4),
            "monster_hit_rate": round(pm.monster_hit_rate, 4),
            "avg_player_dmg_per_hit": round(pm.avg_player_dmg_per_hit, 3),
            "avg_monster_dmg_per_hit": round(pm.avg_monster_dmg_per_hit, 3),
            "player_dpr": round(pm.player_dpr, 3),
            "monster_dpr": round(pm.monster_dpr, 3),
            "player_hits_to_kill": round(pm.player_hits_to_kill, 3) if pm.player_hits_to_kill != float("inf") else "inf",
            "monster_hits_to_kill": round(pm.monster_hits_to_kill, 3) if pm.monster_hits_to_kill != float("inf") else "inf",
            "avg_damage_per_encounter": round(pm.avg_damage_per_encounter, 3),
            "avg_turns_per_enemy": round(pm.avg_turns_per_enemy, 3),
            "player_deaths": pm.player_deaths,
            "player_death_rate": round(pm.player_death_rate, 4),
            "monster_hp_budget_per_run": pm.monster_hp_budget_per_run,
        }
        writer.writerow(row)

    return buf.getvalue()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    json_dir = Path(sys.argv[1])
    if not json_dir.is_dir():
        print(f"ERROR: '{json_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    print(f"\nDepth Pressure Report Generator")
    print(f"  Source directory: {json_dir}")

    # Load manifest for metadata if present
    manifest_path = json_dir / "manifest.json"
    runs_per_scenario = 50
    seed_base: Optional[int] = None
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        runs_per_scenario = manifest.get("runs_per_scenario", 50)
        seed_base = manifest.get("seed_base")
        print(f"  Manifest found: {runs_per_scenario} runs/scenario, seed_base={seed_base}")

    print("\nLoading JSON exports...")
    payloads = load_json_exports(json_dir)
    if not payloads:
        print("ERROR: No JSON files found in directory.", file=sys.stderr)
        sys.exit(1)
    print(f"  Loaded {len(payloads)} file(s).")

    print("\nComputing pressure metrics...")
    pressure_list = extract_pressure_metrics(payloads)
    if not pressure_list:
        print("ERROR: No scenarios matched KNOWN_SCENARIO_CONFIGS.", file=sys.stderr)
        sys.exit(1)

    sufficient = [pm for pm in pressure_list if pm.data_sufficient]
    insufficient = [pm for pm in pressure_list if not pm.data_sufficient]
    print(f"  {len(sufficient)} scenarios have complete data.")
    if insufficient:
        print(f"  {len(insufficient)} scenario(s) have STOP conditions (excluded from curve):")
        for pm in insufficient:
            print(f"    {pm.scenario_id}: {' | '.join(pm.warnings)}")

    print("\nBuilding depth curve...")
    curve = build_depth_curve(sufficient)
    print(f"  Depth points in curve: {sorted(curve.keys())}")

    print("\nGenerating Markdown report...")
    md = generate_markdown_report(
        pressure_list=pressure_list,
        curve=curve,
        json_dir=json_dir,
        runs_per_scenario=runs_per_scenario,
        seed_base=seed_base,
    )
    md_path = json_dir / "depth_pressure_report.md"
    md_path.write_text(md, encoding="utf-8")
    print(f"  Written: {md_path}")

    print("\nGenerating CSV table...")
    csv_content = generate_csv(pressure_list)
    csv_path = json_dir / "depth_pressure_table.csv"
    csv_path.write_text(csv_content, encoding="utf-8")
    print(f"  Written: {csv_path}")

    # Print ASCII curve to console for quick review
    if curve:
        print("\n" + format_pressure_table(curve))

    print(f"\nReport landing: {json_dir}")
    print(f"  {md_path.name}")
    print(f"  {csv_path.name}")


if __name__ == "__main__":
    main()
