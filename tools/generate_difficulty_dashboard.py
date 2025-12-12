#!/usr/bin/env python3
"""Build a Markdown dashboard summarizing difficulty curve outputs."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Dict, List


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ECO_REPORT = REPO_ROOT / "reports" / "eco_balance_report.md"
DEFAULT_METRICS_DIR = REPO_ROOT / "reports" / "metrics"
DEFAULT_GRAPHS_DIR = REPO_ROOT / "reports" / "graphs"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "reports" / "difficulty_dashboard.md"


def _load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_metrics(metrics_dir: Path) -> List[Dict]:
    metrics: List[Dict] = []
    for path in sorted(metrics_dir.glob("*.json")):
        try:
            data = _load_json(path)
            data["_source_path"] = path
            metrics.append(data)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] failed to read {path}: {exc}")
    return metrics


def _markdown_table(headers: List[str], rows: List[List[str]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_line, separator, *body])


def _render_summary(metrics: List[Dict]) -> str:
    rows: List[List[str]] = []
    for item in metrics:
        rows.append(
            [
                item.get("scenario_id", "n/a"),
                item.get("family", "n/a"),
                str(item.get("depth", "—")),
                f"{item.get('runs', 0)}",
                f"{item.get('death_rate', 0.0)*100:.1f}%",
                f"{item.get('player_hit_rate', 0.0)*100:.1f}%",
                f"{item.get('monster_hit_rate', 0.0)*100:.1f}%",
                f"{item.get('bonus_attacks_per_run', 0.0):.2f}",
                f"{item.get('pressure_index', 0.0):.2f}",
            ]
        )
    return _markdown_table(
        [
            "scenario",
            "family",
            "depth",
            "runs",
            "death%",
            "player_hit%",
            "monster_hit%",
            "bonus/run",
            "pressure_index",
        ],
        rows,
    )


def _render_graphs_section(graphs_dir: Path) -> str:
    graph_files = [
        "player_hit_rate_vs_depth.png",
        "monster_hit_rate_vs_depth.png",
        "death_rate_vs_depth.png",
        "bonus_attacks_per_run_vs_depth.png",
        "pressure_index_vs_depth.png",
        "difficulty_curve_overview.png",
    ]
    lines = ["## Graphs"]
    for gf in graph_files:
        path = graphs_dir / gf
        if path.exists():
            lines.append(f"![{gf}]({path.relative_to(graphs_dir.parent)})")
    return "\n\n".join(lines)


def _tempo_descriptor(value: float) -> str:
    if value < -5:
        return "player drives tempo"
    if value > 5:
        return "monsters drive tempo"
    return "balanced tempo"


def _render_family_insights(metrics: List[Dict]) -> str:
    if not metrics:
        return ""

    grouped: Dict[str, List[Dict]] = {}
    for item in metrics:
        grouped.setdefault(item.get("family", "unknown"), []).append(item)

    lines: List[str] = ["## Family Insights"]
    for family, entries in sorted(grouped.items()):
        deaths = [float(e.get("death_rate", 0.0)) * 100 for e in entries]
        player_hits = [float(e.get("player_hit_rate", 0.0)) * 100 for e in entries]
        monster_hits = [float(e.get("monster_hit_rate", 0.0)) * 100 for e in entries]
        bonus = [float(e.get("bonus_attacks_per_run", 0.0)) for e in entries]
        pressure = [float(e.get("pressure_index", 0.0)) for e in entries]

        def _avg(values: List[float]) -> float:
            return sum(values) / len(values) if values else 0.0

        min_death = min(deaths) if deaths else 0.0
        max_death = max(deaths) if deaths else 0.0
        avg_player = _avg(player_hits)
        avg_monster = _avg(monster_hits)
        avg_bonus = _avg(bonus)
        avg_pressure = _avg(pressure)
        tempo = _tempo_descriptor(avg_pressure)

        lines.append(
            f"- **{family}** — deaths {min_death:.0f}–{max_death:.0f}%, "
            f"player hit ~{avg_player:.0f}%, monster hit ~{avg_monster:.0f}%, "
            f"bonus/run ~{avg_bonus:.0f}, pressure index ~{avg_pressure:.1f} ({tempo})."
        )
    return "\n".join(lines)


def _render_scenarios(metrics: List[Dict]) -> str:
    parts: List[str] = ["## Scenario Breakdown"]
    for item in metrics:
        parts.append(f"### {item.get('scenario_id', 'unknown')}")
        parts.append(
            "\n".join(
                [
                    f"- family: {item.get('family', 'n/a')}",
                    f"- depth: {item.get('depth', '—')}",
                    f"- runs: {item.get('runs', 0)}",
                    f"- death_rate: {item.get('death_rate', 0.0):.3f}",
                    f"- player_hit_rate: {item.get('player_hit_rate', 0.0):.3f}",
                    f"- monster_hit_rate: {item.get('monster_hit_rate', 0.0):.3f}",
                    f"- bonus_attacks_per_run: {item.get('bonus_attacks_per_run', 0.0):.3f}",
                    f"- pressure_index: {item.get('pressure_index', 0.0):.3f}",
                ]
            )
        )
        parts.append("")
    return "\n".join(parts).strip()


def _render_raw_appendix(metrics: List[Dict]) -> str:
    lines: List[str] = ["## Raw Metrics (appendix)"]
    for item in metrics:
        scenario_id = item.get("scenario_id", "unknown")
        # Avoid non-serializable Path objects
        serialized = dict(item)
        if "_source_path" in serialized:
            serialized["_source_path"] = str(serialized["_source_path"])
        pretty = json.dumps(serialized, indent=2, sort_keys=True)
        lines.append(f"<details><summary>{scenario_id}</summary>\n\n```json\n{pretty}\n```\n\n</details>")
    return "\n\n".join(lines)


def _render_eco_link(eco_report: Path) -> str:
    if not eco_report.exists():
        return "_Eco balance report not found._"
    try:
        rel = eco_report.relative_to(eco_report.parent.parent) if eco_report.is_absolute() else eco_report
    except ValueError:
        rel = eco_report
    return f"[Eco Balance Report]({rel})"


def build_dashboard(
    metrics_dir: Path = DEFAULT_METRICS_DIR,
    graphs_dir: Path = DEFAULT_GRAPHS_DIR,
    eco_report: Path = DEFAULT_ECO_REPORT,
) -> str:
    metrics = _load_metrics(metrics_dir)
    today = date.today().isoformat()

    header = [
        f"# Difficulty Curve Dashboard",
        f"_Updated: {today}_",
        "",
        _render_eco_link(eco_report),
        "",
        "## Overview",
        f"- Scenarios: {len(metrics)}",
        f"- Metrics source: `{metrics_dir}`",
        f"- Graphs: `{graphs_dir}`",
    ]

    sections = [
        "\n".join(header),
        "## Summary Table",
        _render_summary(metrics) if metrics else "_No metrics found._",
        _render_graphs_section(graphs_dir),
    ]

    if metrics:
        sections.append(_render_family_insights(metrics))
        sections.append(_render_scenarios(metrics))
        sections.append(_render_raw_appendix(metrics))
    else:
        sections.append("_No scenarios to display._")
        sections.append("_No raw metrics available._")
    return "\n\n".join(sections).strip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate difficulty dashboard Markdown.")
    parser.add_argument("--metrics-dir", type=Path, default=DEFAULT_METRICS_DIR, help="Directory with normalized metrics.")
    parser.add_argument("--graphs-dir", type=Path, default=DEFAULT_GRAPHS_DIR, help="Directory containing generated graphs.")
    parser.add_argument(
        "--eco-report",
        type=Path,
        default=DEFAULT_ECO_REPORT,
        help="Path to eco balance report (linked in header).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Output path for dashboard Markdown.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = build_dashboard(metrics_dir=args.metrics_dir, graphs_dir=args.graphs_dir, eco_report=args.eco_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(f"Dashboard written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
