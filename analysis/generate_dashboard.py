#!/usr/bin/env python3
"""Balance Dashboard Generator — Phase 24

Generates a single-page HTML dashboard from depth pressure report data.
Read-only visualization: no write-back or editing capability.

Usage:
    python3 analysis/generate_dashboard.py <report_dir>
    python3 analysis/generate_dashboard.py reports/depth_pressure/20260320_215803/

The report directory should contain:
  - manifest.json
  - on/depth_pressure_table.csv  (and optionally off/ for A/B mode)
  - depth_pressure_curve.png     (optional, embedded if present)

Output:
  - <report_dir>/dashboard.html
"""

import base64
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure repo root is on the path
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from balance.target_bands import TARGET_BANDS, evaluate_depth, diagnose


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_manifest(report_dir: Path) -> Dict[str, Any]:
    p = report_dir / "manifest.json"
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def load_csv_rows(csv_path: Path) -> List[Dict[str, str]]:
    if not csv_path.exists():
        return []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_png_base64(png_path: Path) -> Optional[str]:
    if not png_path.exists():
        return None
    data = png_path.read_bytes()
    return base64.b64encode(data).decode("ascii")


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

GEAR_PROBE_IDS = frozenset({
    "depth3_orc_brutal_gear_weapon_plus1",
    "depth3_orc_brutal_gear_armor_plus1",
})


def evaluate_rows(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Evaluate each CSV row against target bands."""
    results = []
    for row in rows:
        sid = row.get("scenario_id", "")
        is_gear_probe = sid in GEAR_PROBE_IDS
        try:
            depth = int(row["depth"])
            death_rate = float(row["player_death_rate"])
            h_pm = float(row["player_hits_to_kill"])
            h_mp = float(row["monster_hits_to_kill"])
        except (KeyError, ValueError):
            continue

        ev = evaluate_depth(depth, death_rate, h_pm, h_mp)
        diags = diagnose(ev) if ev else []

        results.append({
            "scenario_id": sid,
            "depth": depth,
            "faction": row.get("faction", ""),
            "runs": int(row.get("runs", 0)),
            "death_rate": death_rate,
            "h_pm": h_pm,
            "h_mp": h_mp,
            "player_dpr": float(row.get("player_dpr", 0)),
            "monster_dpr": float(row.get("monster_dpr", 0)),
            "player_hit_rate": float(row.get("player_hit_rate", 0)),
            "monster_hit_rate": float(row.get("monster_hit_rate", 0)),
            "dmg_per_encounter": float(row.get("avg_damage_per_encounter", 0)),
            "turns_per_kill": float(row.get("avg_turns_per_enemy", 0)),
            "evaluation": ev,
            "diagnosis": diags,
            "is_gear_probe": is_gear_probe,
        })
    return results


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

def _status_class(status: Optional[str]) -> str:
    if status == "OK":
        return "status-ok"
    elif status == "HIGH":
        return "status-high"
    elif status == "LOW":
        return "status-low"
    return ""


def _status_icon(status: Optional[str]) -> str:
    if status == "OK":
        return "&#x2713;"  # checkmark
    elif status == "HIGH":
        return "&#x25B2;"  # up triangle
    elif status == "LOW":
        return "&#x25BC;"  # down triangle
    return "—"


def _pct(v: float) -> str:
    return f"{v * 100:.0f}%"


def _fmt(v: float, d: int = 2) -> str:
    return f"{v:.{d}f}"


def generate_html(
    manifest: Dict[str, Any],
    on_evaluated: List[Dict[str, Any]],
    off_evaluated: Optional[List[Dict[str, Any]]],
    png_b64: Optional[str],
) -> str:
    ab_mode = off_evaluated is not None
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    git_sha = manifest.get("git_sha", "unknown")
    runs = manifest.get("runs_per_scenario", "?")
    seed = manifest.get("seed_base", "?")

    # Summary stats
    main_scenarios = [r for r in on_evaluated if not r["is_gear_probe"]]
    gear_probes = [r for r in on_evaluated if r["is_gear_probe"]]
    total = len(main_scenarios)
    passing = sum(
        1 for r in main_scenarios
        if r["evaluation"] and all(
            r["evaluation"][m]["status"] == "OK"
            for m in ("death_rate", "h_pm", "h_mp")
        )
    )
    failing = total - passing

    # Worst offender
    worst = None
    worst_gap = 0
    for r in main_scenarios:
        if r["evaluation"]:
            dr = r["evaluation"]["death_rate"]
            if dr["status"] == "HIGH" and dr["gap"] > worst_gap:
                worst = r
                worst_gap = dr["gap"]

    # Build HTML
    parts = []
    parts.append(_html_head(ts, git_sha, runs, seed, ab_mode))

    # Summary cards
    parts.append(_summary_cards(total, passing, failing, worst))

    # Curve chart
    if png_b64:
        parts.append(_curve_chart(png_b64))

    # Target comparison table
    parts.append(_target_table(main_scenarios, "Main Scenarios"))

    # Gear probes
    if gear_probes:
        parts.append(_gear_probe_section(gear_probes, main_scenarios))

    # A/B delta
    if ab_mode and off_evaluated:
        parts.append(_ab_delta_section(on_evaluated, off_evaluated))

    # Diagnosis
    parts.append(_diagnosis_section(main_scenarios))

    # Target bands reference
    parts.append(_target_bands_reference())

    parts.append("</div></body></html>")
    return "\n".join(parts)


def _html_head(ts, git_sha, runs, seed, ab_mode):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Balance Dashboard — Catacombs of YARL</title>
<style>
  :root {{
    --bg: #1a1a2e; --surface: #16213e; --card: #0f3460;
    --text: #e0e0e0; --muted: #8a8a9a; --accent: #e94560;
    --ok: #4ecca3; --warn: #f39c12; --fail: #e74c3c;
    --band-ok: rgba(78, 204, 163, 0.15);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Menlo', 'Consolas', monospace; background: var(--bg); color: var(--text); line-height: 1.5; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
  h1 {{ color: var(--accent); margin-bottom: 4px; font-size: 1.4em; }}
  h2 {{ color: var(--ok); margin: 24px 0 12px; font-size: 1.1em; border-bottom: 1px solid var(--card); padding-bottom: 4px; }}
  .meta {{ color: var(--muted); font-size: 0.8em; margin-bottom: 20px; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 20px; }}
  .card {{ background: var(--card); border-radius: 8px; padding: 16px; text-align: center; }}
  .card .value {{ font-size: 2em; font-weight: bold; }}
  .card .label {{ color: var(--muted); font-size: 0.8em; margin-top: 4px; }}
  .card.ok .value {{ color: var(--ok); }}
  .card.fail .value {{ color: var(--fail); }}
  .card.warn .value {{ color: var(--warn); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85em; margin-bottom: 16px; }}
  th {{ background: var(--card); padding: 8px 10px; text-align: left; font-weight: 600; position: sticky; top: 0; }}
  td {{ padding: 6px 10px; border-bottom: 1px solid rgba(255,255,255,0.05); }}
  tr:hover td {{ background: rgba(255,255,255,0.03); }}
  .status-ok {{ color: var(--ok); font-weight: bold; }}
  .status-high {{ color: var(--fail); font-weight: bold; }}
  .status-low {{ color: var(--warn); font-weight: bold; }}
  .gear-tag {{ background: var(--warn); color: #000; padding: 1px 6px; border-radius: 3px; font-size: 0.75em; }}
  .diag {{ background: var(--surface); border-left: 3px solid var(--accent); padding: 10px 14px; margin: 6px 0; font-size: 0.85em; }}
  .diag-ok {{ border-left-color: var(--ok); }}
  .chart-container {{ text-align: center; margin: 16px 0; }}
  .chart-container img {{ max-width: 100%; border-radius: 8px; border: 1px solid var(--card); }}
  .ref-table {{ font-size: 0.8em; }}
  .ref-table td, .ref-table th {{ padding: 4px 8px; }}
</style>
</head>
<body>
<div class="container">
<h1>Balance Dashboard</h1>
<div class="meta">
  Generated: {ts} &middot; Git: {git_sha} &middot;
  {runs} runs/scenario &middot; Seed: {seed} &middot;
  Mode: {"A/B (ON vs OFF)" if ab_mode else "Single variant"}
</div>"""


def _summary_cards(total, passing, failing, worst):
    worst_text = "—"
    worst_class = "ok"
    if worst:
        dr = worst["evaluation"]["death_rate"]
        worst_text = f"{worst['scenario_id']}<br><small>Death: {_pct(dr['observed'])} (target: {_pct(dr['target'][1])})</small>"
        worst_class = "fail"

    return f"""
<div class="cards">
  <div class="card ok"><div class="value">{passing}</div><div class="label">Passing</div></div>
  <div class="card fail"><div class="value">{failing}</div><div class="label">Failing</div></div>
  <div class="card"><div class="value">{total}</div><div class="label">Total Scenarios</div></div>
  <div class="card {worst_class}"><div class="value" style="font-size:0.9em">{worst_text}</div><div class="label">Worst Offender</div></div>
</div>"""


def _curve_chart(png_b64):
    return f"""
<h2>Depth Curve</h2>
<div class="chart-container">
  <img src="data:image/png;base64,{png_b64}" alt="Depth pressure curve with target bands">
</div>"""


def _target_table(scenarios, title):
    rows_html = []
    for r in sorted(scenarios, key=lambda x: (x["depth"], x["scenario_id"])):
        ev = r["evaluation"]
        if not ev:
            continue
        dr = ev["death_rate"]
        hpm = ev["h_pm"]
        hmp = ev["h_mp"]

        rows_html.append(f"""<tr>
  <td>{r['depth']}</td>
  <td>{ev['feel']}</td>
  <td>{r['scenario_id']}</td>
  <td class="{_status_class(dr['status'])}">{_pct(dr['observed'])} {_status_icon(dr['status'])}</td>
  <td>{_pct(dr['target'][0])}–{_pct(dr['target'][1])}</td>
  <td class="{_status_class(hpm['status'])}">{_fmt(hpm['observed'])} {_status_icon(hpm['status'])}</td>
  <td>{_fmt(hpm['target'][0], 0)}–{_fmt(hpm['target'][1], 0)}</td>
  <td class="{_status_class(hmp['status'])}">{_fmt(hmp['observed'])} {_status_icon(hmp['status'])}</td>
  <td>{_fmt(hmp['target'][0], 0)}–{_fmt(hmp['target'][1], 0)}</td>
</tr>""")

    return f"""
<h2>{title}</h2>
<table>
<tr>
  <th>Depth</th><th>Feel</th><th>Scenario</th>
  <th>Death%</th><th>Target</th>
  <th>H_PM</th><th>Target</th>
  <th>H_MP</th><th>Target</th>
</tr>
{"".join(rows_html)}
</table>"""


def _gear_probe_section(gear_probes, main_scenarios):
    # Find the baseline for comparison (depth3_orc_brutal)
    baseline = None
    for r in main_scenarios:
        if r["scenario_id"] == "depth3_orc_brutal":
            baseline = r
            break

    rows_html = []
    if baseline:
        rows_html.append(f"""<tr>
  <td><em>baseline</em></td>
  <td>{baseline['scenario_id']}</td>
  <td>{_pct(baseline['death_rate'])}</td>
  <td>{_fmt(baseline['h_pm'])}</td>
  <td>{_fmt(baseline['h_mp'])}</td>
  <td>—</td><td>—</td><td>—</td>
</tr>""")

    for r in gear_probes:
        dr_delta = ""
        hpm_delta = ""
        hmp_delta = ""
        if baseline:
            dd = r["death_rate"] - baseline["death_rate"]
            dh = r["h_pm"] - baseline["h_pm"]
            dm = r["h_mp"] - baseline["h_mp"]
            dr_delta = f'{dd:+.0%}'
            hpm_delta = f'{dh:+.2f}'
            hmp_delta = f'{dm:+.2f}'

        rows_html.append(f"""<tr>
  <td><span class="gear-tag">gear</span></td>
  <td>{r['scenario_id']}</td>
  <td>{_pct(r['death_rate'])}</td>
  <td>{_fmt(r['h_pm'])}</td>
  <td>{_fmt(r['h_mp'])}</td>
  <td>{dr_delta}</td><td>{hpm_delta}</td><td>{hmp_delta}</td>
</tr>""")

    return f"""
<h2>Gear Probes (Depth 3)</h2>
<table>
<tr>
  <th>Type</th><th>Scenario</th>
  <th>Death%</th><th>H_PM</th><th>H_MP</th>
  <th>&Delta;Death%</th><th>&Delta;H_PM</th><th>&Delta;H_MP</th>
</tr>
{"".join(rows_html)}
</table>"""


def _ab_delta_section(on_eval, off_eval):
    off_map = {r["scenario_id"]: r for r in off_eval}
    rows_html = []
    for r in sorted(on_eval, key=lambda x: (x["depth"], x["scenario_id"])):
        if r["is_gear_probe"]:
            continue
        off = off_map.get(r["scenario_id"])
        if not off:
            continue
        dd = off["death_rate"] - r["death_rate"]
        dh = off["h_pm"] - r["h_pm"]
        dm = off["h_mp"] - r["h_mp"]
        rows_html.append(f"""<tr>
  <td>{r['depth']}</td>
  <td>{r['scenario_id']}</td>
  <td>{_pct(r['death_rate'])}</td>
  <td>{_pct(off['death_rate'])}</td>
  <td class="{'status-high' if dd > 0.05 else ''}">{dd:+.0%}</td>
  <td>{_fmt(r['h_pm'])}</td>
  <td>{_fmt(off['h_pm'])}</td>
  <td>{dh:+.2f}</td>
</tr>""")

    return f"""
<h2>A/B Boon Impact (OFF &minus; ON)</h2>
<table>
<tr>
  <th>Depth</th><th>Scenario</th>
  <th>Death%(ON)</th><th>Death%(OFF)</th><th>&Delta;</th>
  <th>H_PM(ON)</th><th>H_PM(OFF)</th><th>&Delta;</th>
</tr>
{"".join(rows_html)}
</table>"""


def _diagnosis_section(scenarios):
    parts = ['<h2>Diagnosis</h2>']
    any_diag = False
    for r in sorted(scenarios, key=lambda x: (x["depth"], x["scenario_id"])):
        if r["diagnosis"]:
            any_diag = True
            for d in r["diagnosis"]:
                css = "diag"
                parts.append(f'<div class="{css}">{d}</div>')

    if not any_diag:
        parts.append('<div class="diag diag-ok">All scenarios within target bands.</div>')
    return "\n".join(parts)


def _target_bands_reference():
    rows = []
    for d in sorted(TARGET_BANDS):
        tb = TARGET_BANDS[d]
        dr_lo, dr_hi = tb.death_pct_range
        rows.append(f"""<tr>
  <td>{d}</td><td>{tb.feel}</td>
  <td>{dr_lo:.0f}–{dr_hi:.0f}%</td>
  <td>{tb.h_pm_min:.0f}–{tb.h_pm_max:.0f}</td>
  <td>{tb.h_mp_min:.0f}–{tb.h_mp_max:.0f}</td>
</tr>""")

    return f"""
<h2>Target Bands Reference</h2>
<table class="ref-table">
<tr><th>Depth</th><th>Feel</th><th>Death%</th><th>H_PM</th><th>H_MP</th></tr>
{"".join(rows)}
</table>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    report_dir = Path(sys.argv[1])
    if not report_dir.is_dir():
        print(f"ERROR: '{report_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    manifest = load_manifest(report_dir)
    ab_mode = manifest.get("boons_mode") == "ab"

    # Load ON variant
    if ab_mode:
        on_csv_path = report_dir / "on" / "depth_pressure_table.csv"
        off_csv_path = report_dir / "off" / "depth_pressure_table.csv"
    else:
        on_csv_path = report_dir / "depth_pressure_table.csv"
        off_csv_path = None

    on_rows = load_csv_rows(on_csv_path)
    off_rows = load_csv_rows(off_csv_path) if off_csv_path else None

    on_evaluated = evaluate_rows(on_rows)
    off_evaluated = evaluate_rows(off_rows) if off_rows else None

    # Load curve PNG
    png_b64 = load_png_base64(report_dir / "depth_pressure_curve.png")

    html = generate_html(manifest, on_evaluated, off_evaluated, png_b64)
    out_path = report_dir / "dashboard.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Dashboard written → {out_path}")


if __name__ == "__main__":
    main()
