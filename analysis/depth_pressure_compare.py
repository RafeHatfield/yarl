#!/usr/bin/env python3
"""Depth Pressure A/B Compare Report — Phase 23

Compares two depth_pressure_table.csv files produced by
tools/collect_depth_pressure_data.py --ab (or two independent runs) and
produces a delta Markdown table showing how key pressure metrics shift when
depth boons are enabled versus disabled.

Usage:
    python3 analysis/depth_pressure_compare.py <on_csv> <off_csv> <out_md>

    on_csv   — CSV from the boons-ON variant (normal campaign behaviour)
    off_csv  — CSV from the boons-OFF variant (control)
    out_md   — Path to write the resulting Markdown report

Key metrics reported:
    H_PM     player hits-to-kill monster
    H_MP     monster hits-to-kill player (survival budget)
    DPR_P    player damage per round
    DPR_M    monster damage per round
    Death%   player death rate

Delta convention:
    Δ = OFF − ON
    Positive Δ means the metric is HIGHER without boons (boons reduced it).
    Negative Δ means the metric is LOWER without boons (boons increased it).

Row key: (depth, scenario_id)
    Using both depth AND scenario_id as the compound key future-proofs the
    compare for suites that include multiple scenarios at the same depth
    (e.g., "depth4_orc_probe_A", "depth4_orc_probe_B", "depth4_plague").

Coverage notes:
    Rows missing from one variant, or flagged data_sufficient=False in either
    variant, are excluded from the delta table and listed in a Coverage Notes
    section at the end of the report.

No tuning recommendations are made here.  The report is purely descriptive.
"""

import csv
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------

# Compound key for every row: (depth as int, scenario_id as str)
_RowKey = Tuple[int, str]

_DELTA_FIELDS = [
    "player_hits_to_kill",   # H_PM
    "monster_hits_to_kill",  # H_MP
    "player_dpr",            # DPR_P
    "monster_dpr",           # DPR_M
    "player_death_rate",     # Death%
]

_FIELD_LABEL = {
    "player_hits_to_kill": "H_PM",
    "monster_hits_to_kill": "H_MP",
    "player_dpr": "DPR_P",
    "monster_dpr": "DPR_M",
    "player_death_rate": "Death%",
}


def _load_csv(path: Path) -> Dict[_RowKey, dict]:
    """Load a depth_pressure_table.csv into a dict keyed by (depth, scenario_id).

    Rows with non-integer depth are skipped with a warning.
    """
    rows: Dict[_RowKey, dict] = {}
    if not path.exists():
        print(f"WARNING: CSV not found: {path}", file=sys.stderr)
        return rows

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            scenario_id = row.get("scenario_id", "").strip()
            try:
                depth = int(row.get("depth", ""))
            except (ValueError, TypeError):
                print(
                    f"WARNING: Skipping row with non-integer depth "
                    f"(scenario_id={scenario_id!r}, depth={row.get('depth')!r})",
                    file=sys.stderr,
                )
                continue
            key: _RowKey = (depth, scenario_id)
            if key in rows:
                print(
                    f"WARNING: Duplicate key (depth={depth}, scenario_id={scenario_id!r}) "
                    f"in {path.name} — later row overwrites earlier.",
                    file=sys.stderr,
                )
            rows[key] = row
    return rows


def _safe_float(value: str, fallback: float = float("nan")) -> float:
    """Convert a CSV string to float, returning fallback on failure."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return fallback


def _is_sufficient(row: dict) -> bool:
    return str(row.get("data_sufficient", "")).strip().lower() == "true"


# ---------------------------------------------------------------------------
# Delta computation
# ---------------------------------------------------------------------------

def _fmt(value: float, decimals: int = 3) -> str:
    """Format a float for the table; return '—' for NaN/inf."""
    import math
    if math.isnan(value) or math.isinf(value):
        return "—"
    return f"{value:.{decimals}f}"


def _fmt_delta(value: float, decimals: int = 3) -> str:
    """Format a delta with an explicit sign; '—' for NaN/inf."""
    import math
    if math.isnan(value) or math.isinf(value):
        return "—"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.{decimals}f}"


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def compare_variants(on_csv: Path, off_csv: Path, out_path: Path) -> None:
    """Load two depth_pressure_table.csv files and write a delta Markdown report.

    Args:
        on_csv:   CSV from the boons-ON variant.
        off_csv:  CSV from the boons-OFF variant.
        out_path: Destination path for the Markdown report.
    """
    on_rows  = _load_csv(on_csv)
    off_rows = _load_csv(off_csv)

    all_keys: List[_RowKey] = sorted(set(on_rows) | set(off_rows))

    # Partition keys into: comparable, only-on, only-off, insufficient
    comparable: List[_RowKey] = []
    only_on:    List[_RowKey] = []
    only_off:   List[_RowKey] = []
    insufficient: List[Tuple[_RowKey, str]] = []  # (key, reason)

    for key in all_keys:
        in_on  = key in on_rows
        in_off = key in off_rows

        if in_on and not in_off:
            only_on.append(key)
            continue
        if in_off and not in_on:
            only_off.append(key)
            continue

        # Present in both — check data_sufficient
        on_ok  = _is_sufficient(on_rows[key])
        off_ok = _is_sufficient(off_rows[key])
        if not on_ok and not off_ok:
            insufficient.append((key, "data_sufficient=False in both variants"))
        elif not on_ok:
            insufficient.append((key, "data_sufficient=False in ON variant"))
        elif not off_ok:
            insufficient.append((key, "data_sufficient=False in OFF variant"))
        else:
            comparable.append(key)

    # -------------------------------------------------------------------------
    # Build the delta table rows
    # -------------------------------------------------------------------------
    table_lines: List[str] = []

    # Header
    header_cols = [
        "Depth", "Scenario",
        "H_PM(on)", "H_PM(off)", "ΔH_PM",
        "H_MP(on)", "H_MP(off)", "ΔH_MP",
        "DPR_P(on)", "DPR_P(off)", "ΔDPR_P",
        "DPR_M(on)", "DPR_M(off)", "ΔDPR_M",
        "Death%(on)", "Death%(off)",
    ]
    table_lines.append("| " + " | ".join(header_cols) + " |")
    table_lines.append(
        "| " + " | ".join(["---"] * len(header_cols)) + " |"
    )

    for key in comparable:
        depth, scenario_id = key
        on_row  = on_rows[key]
        off_row = off_rows[key]

        h_pm_on   = _safe_float(on_row.get("player_hits_to_kill",  ""))
        h_pm_off  = _safe_float(off_row.get("player_hits_to_kill", ""))
        h_mp_on   = _safe_float(on_row.get("monster_hits_to_kill",  ""))
        h_mp_off  = _safe_float(off_row.get("monster_hits_to_kill", ""))
        dpr_p_on  = _safe_float(on_row.get("player_dpr",  ""))
        dpr_p_off = _safe_float(off_row.get("player_dpr", ""))
        dpr_m_on  = _safe_float(on_row.get("monster_dpr",  ""))
        dpr_m_off = _safe_float(off_row.get("monster_dpr", ""))
        death_on  = _safe_float(on_row.get("player_death_rate",  ""))
        death_off = _safe_float(off_row.get("player_death_rate", ""))

        table_lines.append(
            f"| {depth} | `{scenario_id}` "
            f"| {_fmt(h_pm_on)} | {_fmt(h_pm_off)} | {_fmt_delta(h_pm_off - h_pm_on)} "
            f"| {_fmt(h_mp_on)} | {_fmt(h_mp_off)} | {_fmt_delta(h_mp_off - h_mp_on)} "
            f"| {_fmt(dpr_p_on)} | {_fmt(dpr_p_off)} | {_fmt_delta(dpr_p_off - dpr_p_on)} "
            f"| {_fmt(dpr_m_on)} | {_fmt(dpr_m_off)} | {_fmt_delta(dpr_m_off - dpr_m_on)} "
            f"| {_fmt(death_on, 1)} | {_fmt(death_off, 1)} |"
        )

    # -------------------------------------------------------------------------
    # Assemble full Markdown report
    # -------------------------------------------------------------------------
    from datetime import datetime as _dt
    ts = _dt.now().strftime("%Y-%m-%d %H:%M:%S")

    lines: List[str] = [
        "# Depth Pressure A/B Compare Report — Phase 23",
        "",
        f"**Generated:** {ts}  ",
        f"**ON variant CSV:** `{on_csv}`  ",
        f"**OFF variant CSV:** `{off_csv}`  ",
        f"**Comparable scenarios:** {len(comparable)}  ",
        "",
        "> **Delta convention:** Δ = OFF − ON",
        "> Positive Δ = metric is higher without boons (boons reduced it).",
        "> Negative Δ = metric is lower without boons (boons increased it).",
        "> No tuning recommendations are made here. This report is purely descriptive.",
        "",
        "---",
        "",
        "## Delta Table",
        "",
    ]

    if comparable:
        lines += table_lines
    else:
        lines.append("_No comparable scenarios found._")

    # Coverage notes
    lines += [
        "",
        "---",
        "",
        "## Coverage Notes",
        "",
    ]

    if only_on or only_off or insufficient:
        if only_on:
            lines.append("**Scenarios present in ON variant only (excluded from delta table):**")
            for depth, sid in only_on:
                lines.append(f"  - depth {depth}: `{sid}`")
            lines.append("")
        if only_off:
            lines.append("**Scenarios present in OFF variant only (excluded from delta table):**")
            for depth, sid in only_off:
                lines.append(f"  - depth {depth}: `{sid}`")
            lines.append("")
        if insufficient:
            lines.append("**Scenarios excluded due to insufficient data:**")
            for (depth, sid), reason in insufficient:
                lines.append(f"  - depth {depth}: `{sid}` — {reason}")
            lines.append("")
    else:
        lines.append("_All scenarios were present in both variants with sufficient data._")

    # Metric key
    lines += [
        "",
        "---",
        "",
        "## Metric Key",
        "",
        "| Abbreviation | Full Name | Formula |",
        "|---|---|---|",
        "| H_PM | Player hits-to-kill monster | `avg_monster_HP / DPR_P` |",
        "| H_MP | Monster hits-to-kill player | `player_HP / DPR_M` (player_HP = 54) |",
        "| DPR_P | Player damage per round | `E[DMG_P] × P(hit_P)` |",
        "| DPR_M | Monster damage per round | `E[DMG_M] × P(hit_M)` |",
        "| Death% | Player death rate | `player_deaths / runs` |",
        "",
        "> Death% is formatted to 1 decimal place (e.g., 0.1 = 10%).",
        "> All other metrics are formatted to 3 decimal places.",
        "",
    ]

    md = "\n".join(lines)
    out_path.write_text(md, encoding="utf-8")
    print(f"Compare report written → {out_path}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) != 4 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if sys.argv[1:] in (["-h"], ["--help"]) else 1)

    on_csv  = Path(sys.argv[1])
    off_csv = Path(sys.argv[2])
    out_md  = Path(sys.argv[3])

    compare_variants(on_csv, off_csv, out_md)


if __name__ == "__main__":
    main()
