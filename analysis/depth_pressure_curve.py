#!/usr/bin/env python3
"""Depth Pressure Curve Visualizer — Phase 23

Reads depth_pressure_table.csv file(s) produced by
tools/collect_depth_pressure_data.py and generates:

  - depth_pressure_curve.md   compact table + ASCII sparklines
  - depth_pressure_curve.png  line chart (H_PM and Death% vs depth)

CLI modes
---------
Single-variant mode:

    python3 analysis/depth_pressure_curve.py <variant_dir>

    Reads:   <variant_dir>/depth_pressure_table.csv
    Writes:  <variant_dir>/depth_pressure_curve.md
             <variant_dir>/depth_pressure_curve.png

A/B mode:

    python3 analysis/depth_pressure_curve.py --ab <on_csv> <off_csv> <out_dir>

    Writes:  <out_dir>/depth_pressure_curve.md
             <out_dir>/depth_pressure_curve.png

In single-variant mode the markdown table contains only ON columns.
In A/B mode the table contains both ON and OFF columns.

Gear probe rows are identified by scenario_id and marked with [gear probe]
in the Scenario column. They are excluded from sparkline computation but
appear as × markers in the PNG chart.

PNG generation requires matplotlib. If matplotlib is unavailable the PNG
step is silently skipped.

Missing CSV columns are handled gracefully: that metric column is omitted
from the table and a note is appended to the markdown.
"""

import argparse
import csv
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

# Ensure repo root is on the path when called as a script
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Scenario IDs that are gear pressure probes (not main curve scenarios).
GEAR_PROBE_IDS: frozenset = frozenset({
    "depth3_orc_brutal_gear_weapon_plus1",
    "depth3_orc_brutal_gear_armor_plus1",
})

# Unicode block characters for sparklines (index 0 = lowest, 8 = highest).
_BLOCK_CHARS = " ▁▂▃▄▅▆▇█"

# CSV column names → display label
_METRIC_COLS = {
    "player_hits_to_kill": "H_PM",
    "monster_hits_to_kill": "H_MP",
    "player_dpr": "DPR_P",
    "monster_dpr": "DPR_M",
    "player_death_rate": "Death%",
}

# Columns included in sparklines (subset of _METRIC_COLS keys)
_SPARKLINE_METRICS = ["player_hits_to_kill", "player_death_rate", "monster_hits_to_kill"]

# Row key type: (depth: int, scenario_id: str)
_RowKey = Tuple[int, str]


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------

def load_csv(path: Path) -> Dict[_RowKey, dict]:
    """Load a depth_pressure_table.csv into a dict keyed by (depth, scenario_id).

    Returns an empty dict with a stderr warning if the file is missing or
    unparseable. Rows with non-integer depth are skipped with a warning.
    """
    rows: Dict[_RowKey, dict] = {}
    if not path.exists():
        print(f"WARNING: CSV not found: {path}", file=sys.stderr)
        return rows
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = row.get("scenario_id", "").strip()
                try:
                    depth = int(row.get("depth", ""))
                except (ValueError, TypeError):
                    print(
                        f"WARNING: Skipping row with non-integer depth "
                        f"(scenario_id={sid!r}, depth={row.get('depth')!r})",
                        file=sys.stderr,
                    )
                    continue
                key: _RowKey = (depth, sid)
                rows[key] = row
    except Exception as exc:
        print(f"WARNING: Could not read CSV '{path}': {exc}", file=sys.stderr)
    return rows


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _safe_float(s: Optional[str]) -> Optional[float]:
    """Convert a CSV string to float, returning None on failure."""
    if s is None:
        return None
    try:
        v = float(s)
        return None if (math.isnan(v) or math.isinf(v)) else v
    except (ValueError, TypeError):
        return None


def _fmt(v: Optional[float], decimals: int = 3) -> str:
    """Format a float for display; '—' for None/nan/inf."""
    if v is None:
        return "—"
    return f"{v:.{decimals}f}"


def _is_gear_probe(scenario_id: str) -> bool:
    return scenario_id in GEAR_PROBE_IDS


# ---------------------------------------------------------------------------
# ASCII sparkline
# ---------------------------------------------------------------------------

def sparkline(values: Sequence[float]) -> str:
    """Map a sequence of floats to an ASCII sparkline string.

    Uses unicode block characters ▁▂▃▄▅▆▇█. Returns '(no data)' for an
    empty sequence. If all values are equal a flat midpoint line is returned.
    """
    vals = list(values)
    if not vals:
        return "(no data)"
    lo = min(vals)
    hi = max(vals)
    if lo == hi:
        return _BLOCK_CHARS[4] * len(vals)
    span = hi - lo
    return "".join(_BLOCK_CHARS[round((v - lo) / span * 8)] for v in vals)


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def generate_curve_md(
    on_rows: Dict[_RowKey, dict],
    off_rows: Optional[Dict[_RowKey, dict]] = None,
) -> str:
    """Build the depth_pressure_curve.md content as a string.

    Args:
        on_rows:  Rows from the ON variant (or the only variant in single mode).
        off_rows: Rows from the OFF variant. If None, single-variant mode.

    Returns:
        Full markdown string.
    """
    ab_mode = off_rows is not None
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    all_keys: List[_RowKey] = sorted(set(on_rows) | (set(off_rows) if off_rows else set()))

    # Detect which metric columns are actually present in the data
    all_on_cols = set()
    for row in on_rows.values():
        all_on_cols.update(row.keys())
    all_off_cols: set = set()
    if off_rows:
        for row in off_rows.values():
            all_off_cols.update(row.keys())

    present_metrics: List[str] = []
    missing_metrics: List[str] = []
    for col, label in _METRIC_COLS.items():
        if col in all_on_cols:
            present_metrics.append(col)
        else:
            missing_metrics.append(f"`{label}` (`{col}`)")

    lines: List[str] = [
        "# Depth Pressure Curve",
        "",
        f"**Generated:** {ts}  ",
        f"**Mode:** {'A/B (ON vs OFF)' if ab_mode else 'Single variant'}  ",
        "",
    ]

    # Missing column notes
    if missing_metrics:
        lines.append("> **Missing columns (metrics omitted from table):** " + ", ".join(missing_metrics))
        lines.append("")

    # -------------------------------------------------------------------------
    # Table
    # -------------------------------------------------------------------------
    lines += ["---", "", "## Curve Table", ""]

    # Build header
    header_parts = ["Depth", "Scenario"]
    for col in present_metrics:
        label = _METRIC_COLS[col]
        if ab_mode:
            header_parts += [f"{label}(on)", f"{label}(off)"]
        else:
            header_parts.append(f"{label}(on)")

    lines.append("| " + " | ".join(header_parts) + " |")
    lines.append("| " + " | ".join(["---"] * len(header_parts)) + " |")

    for key in all_keys:
        depth, sid = key
        on_row = on_rows.get(key, {})
        off_row = (off_rows or {}).get(key, {})

        probe_tag = " `[gear probe]`" if _is_gear_probe(sid) else ""
        row_parts = [str(depth), f"`{sid}`{probe_tag}"]

        for col in present_metrics:
            on_val = _safe_float(on_row.get(col))
            decimals = 1 if col == "player_death_rate" else 3
            if ab_mode:
                off_val = _safe_float(off_row.get(col))
                row_parts += [_fmt(on_val, decimals), _fmt(off_val, decimals)]
            else:
                row_parts.append(_fmt(on_val, decimals))

        lines.append("| " + " | ".join(row_parts) + " |")

    # -------------------------------------------------------------------------
    # Sparklines — ON variant only, gear probes excluded
    # -------------------------------------------------------------------------
    lines += ["", "---", "", "## Sparklines (ON variant · gear probes excluded)", ""]
    lines.append("Each character represents one depth point left-to-right (ascending depth).")
    lines.append("Block height = relative magnitude: `▁` = low, `█` = high.")
    lines.append("")

    main_keys = sorted(k for k in on_rows if not _is_gear_probe(k[1]))

    for col in _SPARKLINE_METRICS:
        label = _METRIC_COLS.get(col, col)
        if col not in all_on_cols:
            lines.append(f"| `{label}` | (column missing from data) |")
            continue
        vals = [_safe_float(on_rows[k].get(col)) for k in main_keys]
        clean_vals = [v for v in vals if v is not None]
        if len(clean_vals) < 2:
            spark = "(insufficient data)"
        else:
            # Rebuild vals replacing None with the mean of available values
            mean_v = sum(clean_vals) / len(clean_vals)
            filled = [v if v is not None else mean_v for v in vals]
            spark = sparkline(filled)
        lines.append(f"| `{label}` | `{spark}` |")

    # Sparkline table needs a header row
    spark_header_idx = lines.index("## Sparklines (ON variant · gear probes excluded)") + 3
    lines.insert(spark_header_idx, "| Metric | Trend (depth 1 → 6) |")
    lines.insert(spark_header_idx + 1, "|--------|---------------------|")

    # -------------------------------------------------------------------------
    # Target Bands reference table
    # -------------------------------------------------------------------------
    try:
        from balance.target_bands import TARGET_BANDS as _tb_ref
    except ImportError:
        _tb_ref = {}

    if _tb_ref:
        lines += ["", "---", "", "## Target Bands (from `balance/target_bands.py`)", ""]
        lines.append("| Depth | Feel | Death% | H_PM | H_MP |")
        lines.append("|-------|------|--------|------|------|")
        for d in sorted(_tb_ref):
            tb = _tb_ref[d]
            dr_lo, dr_hi = tb.death_pct_range
            lines.append(
                f"| {d} | {tb.feel} | "
                f"{dr_lo:.0f}–{dr_hi:.0f}% | "
                f"{tb.h_pm_min:.0f}–{tb.h_pm_max:.0f} | "
                f"{tb.h_mp_min:.0f}–{tb.h_mp_max:.0f} |"
            )

    # -------------------------------------------------------------------------
    # Legend
    # -------------------------------------------------------------------------
    lines += [
        "",
        "---",
        "",
        "## How to Read This Chart",
        "",
        "| Metric | Interpretation |",
        "|--------|---------------|",
        "| `H_PM` | Rounds for player to kill one monster. **Higher = harder for player.** |",
        "| `H_MP` | Rounds for monsters to kill player. **Lower = more dangerous.** |",
        "| `DPR_P` | Player expected damage per round. Higher = player hits harder. |",
        "| `DPR_M` | Monster expected damage per round. Higher = monsters hit harder. |",
        "| `Death%` | Fraction of runs the player died. **Higher = deadlier depth.** |",
        "",
        "**ON** = boons enabled (normal campaign).  ",
        "**OFF** = boons disabled (control).  ",
        "**`[gear probe]`** = row uses upgraded starting gear; not part of the main depth curve.  ",
        "",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# PNG generation
# ---------------------------------------------------------------------------

def generate_curve_png(
    on_rows: Dict[_RowKey, dict],
    off_rows: Optional[Dict[_RowKey, dict]],
    out_path: Path,
) -> None:
    """Write depth_pressure_curve.png with H_PM and Death% subplots.

    Silently returns if matplotlib is unavailable.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("WARNING: matplotlib not available; skipping PNG generation.", file=sys.stderr)
        return

    ab_mode = off_rows is not None

    def _extract_series(rows: Dict[_RowKey, dict], col: str, gear_probe: bool):
        """Return (depths, values) for main or gear-probe points."""
        pts = [
            (k[0], _safe_float(rows[k].get(col)))
            for k in sorted(rows)
            if _is_gear_probe(k[1]) == gear_probe
        ]
        pts = [(d, v) for d, v in pts if v is not None]
        if not pts:
            return [], []
        depths, vals = zip(*pts)
        return list(depths), list(vals)

    # Load target bands for shading (graceful fallback if unavailable)
    try:
        from balance.target_bands import TARGET_BANDS
    except ImportError:
        TARGET_BANDS = {}

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7), sharex=True)

    # --- Target band shading ---
    # Draw translucent green bands showing the acceptable range at each depth.
    # Bands are drawn as rectangles spanning depth ± 0.5 (so they tile cleanly).
    for d, tb in sorted(TARGET_BANDS.items()):
        # H_PM target band on ax1
        ax1.axhspan(
            tb.h_pm_min, tb.h_pm_max,
            xmin=0, xmax=1,  # Will be clipped by x-limits
            alpha=0.0,  # Invisible full-span (we use individual rects below)
        )
        ax1.fill_between(
            [d - 0.4, d + 0.4],
            tb.h_pm_min, tb.h_pm_max,
            color="green", alpha=0.12, linewidth=0,
        )
        # Death% target band on ax2
        ax2.fill_between(
            [d - 0.4, d + 0.4],
            tb.death_rate_min, tb.death_rate_max,
            color="green", alpha=0.12, linewidth=0,
        )

    # H_PM subplot
    d_on, v_on = _extract_series(on_rows, "player_hits_to_kill", gear_probe=False)
    if d_on:
        ax1.plot(d_on, v_on, color="steelblue", linestyle="-", marker="o", label="ON")
    if ab_mode and off_rows:
        d_off, v_off = _extract_series(off_rows, "player_hits_to_kill", gear_probe=False)
        if d_off:
            ax1.plot(d_off, v_off, color="darkorange", linestyle="--", marker="o", label="OFF")
    # Gear probes as × markers
    gd, gv = _extract_series(on_rows, "player_hits_to_kill", gear_probe=True)
    if gd:
        ax1.scatter(gd, gv, marker="x", color="steelblue", s=60, zorder=5, label="gear probe (ON)")
    if ab_mode and off_rows:
        gd2, gv2 = _extract_series(off_rows, "player_hits_to_kill", gear_probe=True)
        if gd2:
            ax1.scatter(gd2, gv2, marker="x", color="darkorange", s=60, zorder=5, label="gear probe (OFF)")
    ax1.set_ylabel("H_PM")
    ax1.set_title("Player Hits-to-Kill Monster (H_PM) vs Depth")
    if TARGET_BANDS:
        # Add a dummy patch for the legend
        from matplotlib.patches import Patch
        handles, labels = ax1.get_legend_handles_labels()
        handles.append(Patch(facecolor="green", alpha=0.15, label="target band"))
        ax1.legend(handles=handles, fontsize=8)
    else:
        ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)

    # Death% subplot
    d_on2, v_on2 = _extract_series(on_rows, "player_death_rate", gear_probe=False)
    if d_on2:
        ax2.plot(d_on2, v_on2, color="steelblue", linestyle="-", marker="o", label="ON")
    if ab_mode and off_rows:
        d_off2, v_off2 = _extract_series(off_rows, "player_death_rate", gear_probe=False)
        if d_off2:
            ax2.plot(d_off2, v_off2, color="darkorange", linestyle="--", marker="o", label="OFF")
    gd3, gv3 = _extract_series(on_rows, "player_death_rate", gear_probe=True)
    if gd3:
        ax2.scatter(gd3, gv3, marker="x", color="steelblue", s=60, zorder=5, label="gear probe (ON)")
    if ab_mode and off_rows:
        gd4, gv4 = _extract_series(off_rows, "player_death_rate", gear_probe=True)
        if gd4:
            ax2.scatter(gd4, gv4, marker="x", color="darkorange", s=60, zorder=5, label="gear probe (OFF)")
    ax2.set_xlabel("Depth")
    ax2.set_ylabel("Death%")
    ax2.set_title("Player Death Rate (Death%) vs Depth")
    if TARGET_BANDS:
        handles2, labels2 = ax2.get_legend_handles_labels()
        handles2.append(Patch(facecolor="green", alpha=0.15, label="target band"))
        ax2.legend(handles=handles2, fontsize=8)
    else:
        ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(str(out_path), dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"PNG written → {out_path}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--ab", action="store_true",
        help="A/B mode: compare ON and OFF variants.",
    )
    parser.add_argument(
        "args", nargs="*",
        help=(
            "Single-variant mode: <variant_dir>. "
            "A/B mode: <on_csv> <off_csv> <out_dir>."
        ),
    )
    parsed = parser.parse_args()

    if parsed.ab:
        if len(parsed.args) != 3:
            parser.error("--ab requires exactly three arguments: <on_csv> <off_csv> <out_dir>")
        on_csv = Path(parsed.args[0])
        off_csv = Path(parsed.args[1])
        out_dir = Path(parsed.args[2])
        out_dir.mkdir(parents=True, exist_ok=True)
        on_rows = load_csv(on_csv)
        off_rows = load_csv(off_csv)
    else:
        if len(parsed.args) != 1:
            parser.error("Single-variant mode requires exactly one argument: <variant_dir>")
        variant_dir = Path(parsed.args[0])
        on_rows = load_csv(variant_dir / "depth_pressure_table.csv")
        off_rows = None
        out_dir = variant_dir

    md = generate_curve_md(on_rows, off_rows)
    md_path = out_dir / "depth_pressure_curve.md"
    md_path.write_text(md, encoding="utf-8")
    print(f"Curve markdown written → {md_path}")

    png_path = out_dir / "depth_pressure_curve.png"
    generate_curve_png(on_rows, off_rows, png_path)


if __name__ == "__main__":
    main()
