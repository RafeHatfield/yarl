#!/usr/bin/env python3
"""Generate ecosystem, worldgen, and bot soak balance reports.

This script is tooling-only: it reads existing JSON/CSV exports produced by
ecosystem/worldgen sanity harnesses and the bot soak harness, then emits a
concise summary to stdout and optionally to a Markdown file.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _load_json(path: Path) -> object:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _try_parse_json_string(value):
    """Best-effort parse for dict-like strings found in CSV exports."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip().startswith("{"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    return {}


# ---------------------------------------------------------------------------
# Ecosystem parsing
# ---------------------------------------------------------------------------

@dataclass
class EcosystemScenarioSummary:
    scenario_id: str
    family: str
    runs: int
    average_turns: float
    player_death_rate: float
    player_hit_rate: float
    monster_hit_rate: float
    bonus_attacks_per_run: float
    plague_infections_per_run: float
    surprise_attacks_per_run: float


def _scenario_family(scenario_id: str) -> str:
    parts = scenario_id.split("_")
    return "_".join(parts[:2]) if len(parts) > 1 else scenario_id


def _parse_ecosystem_file(path: Path) -> Optional[EcosystemScenarioSummary]:
    data = _load_json(path)
    scenario_id = data.get("scenario_id") or path.stem
    metrics = data.get("metrics", {})
    runs = metrics.get("runs") or data.get("runs") or 0
    if not runs:
        return None

    total_player_attacks = metrics.get("total_player_attacks", 0)
    total_player_hits = metrics.get("total_player_hits", 0)
    total_monster_attacks = metrics.get("total_monster_attacks", 0)
    total_monster_hits = metrics.get("total_monster_hits", 0)
    total_bonus_attacks = metrics.get("total_bonus_attacks_triggered", 0)

    return EcosystemScenarioSummary(
        scenario_id=scenario_id,
        family=_scenario_family(scenario_id),
        runs=runs,
        average_turns=metrics.get("average_turns", 0.0),
        player_death_rate=_safe_div(metrics.get("player_deaths", 0), runs),
        player_hit_rate=_safe_div(total_player_hits, total_player_attacks),
        monster_hit_rate=_safe_div(total_monster_hits, total_monster_attacks),
        bonus_attacks_per_run=_safe_div(total_bonus_attacks, runs),
        plague_infections_per_run=_safe_div(
            metrics.get("total_plague_infections", 0), runs
        ),
        surprise_attacks_per_run=_safe_div(
            metrics.get("total_surprise_attacks", 0), runs
        ),
    )


def load_ecosystem_summaries(paths: Iterable[Path]) -> List[EcosystemScenarioSummary]:
    summaries: List[EcosystemScenarioSummary] = []
    for path in paths:
        try:
            summary = _parse_ecosystem_file(path)
            if summary:
                summaries.append(summary)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] failed to parse ecosystem file {path}: {exc}")
    return summaries


# ---------------------------------------------------------------------------
# Worldgen parsing
# ---------------------------------------------------------------------------

@dataclass
class WorldgenDepthSummary:
    depth: int
    runs: int
    walkable_avg: float
    walkable_min: float
    walkable_max: float
    reachable_avg: float
    monsters_avg: float
    items_avg: float


def _compute_worldgen_from_runs(runs: List[dict]) -> List[WorldgenDepthSummary]:
    grouped: Dict[int, List[dict]] = defaultdict(list)
    for run in runs:
        depth = int(run.get("depth", 0))
        grouped[depth].append(run)

    summaries: List[WorldgenDepthSummary] = []
    for depth, items in sorted(grouped.items()):
        walkable = [float(r.get("walkable_percent", 0.0)) for r in items]
        reachable = [float(r.get("reachable_percent", 0.0)) for r in items]
        monsters = [float(r.get("monsters", 0.0)) for r in items]
        items_count = [float(r.get("items", 0.0)) for r in items]
        runs = len(items)
        summaries.append(
            WorldgenDepthSummary(
                depth=depth,
                runs=runs,
                walkable_avg=sum(walkable) / runs if runs else 0.0,
                walkable_min=min(walkable) if runs else 0.0,
                walkable_max=max(walkable) if runs else 0.0,
                reachable_avg=sum(reachable) / runs if runs else 0.0,
                monsters_avg=sum(monsters) / runs if runs else 0.0,
                items_avg=sum(items_count) / runs if runs else 0.0,
            )
        )
    return summaries


def load_worldgen_summaries(paths: Iterable[Path]) -> List[WorldgenDepthSummary]:
    summaries: List[WorldgenDepthSummary] = []
    for path in paths:
        try:
            data = _load_json(path)
            if "aggregates" in data:
                for agg in data["aggregates"]:
                    summaries.append(
                        WorldgenDepthSummary(
                            depth=int(agg.get("depth", 0)),
                            runs=int(agg.get("runs", 0)),
                            walkable_avg=float(agg.get("walkable_avg", 0.0)),
                            walkable_min=float(agg.get("walkable_min", 0.0)),
                            walkable_max=float(agg.get("walkable_max", 0.0)),
                            reachable_avg=float(agg.get("reachable_avg", 0.0)),
                            monsters_avg=float(agg.get("monsters_avg", 0.0)),
                            items_avg=float(agg.get("items_avg", 0.0)),
                        )
                    )
            elif "runs" in data:
                summaries.extend(_compute_worldgen_from_runs(data.get("runs", [])))
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] failed to parse worldgen file {path}: {exc}")
    return summaries


# ---------------------------------------------------------------------------
# Bot soak parsing
# ---------------------------------------------------------------------------

@dataclass
class BotRunRecord:
    outcome: str
    floors: int
    steps: int
    actions: Dict[str, int]


def _normalize_bot_record(raw: dict) -> BotRunRecord:
    run_metrics = raw.get("run_metrics", raw)
    bot_summary = raw.get("bot_summary") or {}
    if isinstance(bot_summary, str):
        bot_summary = _try_parse_json_string(bot_summary)

    action_counts = bot_summary.get("action_counts") or bot_summary.get("bot_actions")
    if action_counts is None:
        action_counts = run_metrics.get("bot_actions")
    actions = _try_parse_json_string(action_counts)

    steps = (
        bot_summary.get("total_steps")
        or run_metrics.get("steps_taken")
        or run_metrics.get("bot_steps")
        or 0
    )
    floors = (
        bot_summary.get("floors_seen")
        or run_metrics.get("floors_visited")
        or run_metrics.get("deepest_floor")
        or 0
    )

    return BotRunRecord(
        outcome=str(run_metrics.get("outcome", "unknown")),
        floors=int(floors or 0),
        steps=int(steps or 0),
        actions={k: int(v) for k, v in (actions or {}).items()},
    )


def _load_bot_jsonl(path: Path) -> List[BotRunRecord]:
    records: List[BotRunRecord] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                records.append(_normalize_bot_record(obj))
            except Exception as exc:  # noqa: BLE001
                print(f"[warn] failed to parse line in {path}: {exc}")
    return records


def _load_bot_json(path: Path) -> List[BotRunRecord]:
    data = _load_json(path)
    if isinstance(data, list):
        return [_normalize_bot_record(item) for item in data]
    if isinstance(data, dict):
        if "runs" in data and isinstance(data["runs"], list):
            return [_normalize_bot_record(item) for item in data["runs"]]
        return [_normalize_bot_record(data)]
    return []


def _load_bot_csv(path: Path) -> List[BotRunRecord]:
    records: List[BotRunRecord] = []
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            actions = _try_parse_json_string(row.get("bot_actions") or row.get("action_counts"))
            floors = row.get("floors_visited") or row.get("bot_floors") or row.get("deepest_floor")
            steps = row.get("steps_taken") or row.get("bot_steps")
            record = BotRunRecord(
                outcome=row.get("outcome", "unknown"),
                floors=int(float(floors or 0)),
                steps=int(float(steps or 0)),
                actions={k: int(v) for k, v in (actions or {}).items()},
            )
            records.append(record)
    return records


def load_bot_records(paths: Iterable[Path]) -> List[BotRunRecord]:
    records: List[BotRunRecord] = []
    for path in paths:
        try:
            suffix = path.suffix.lower()
            if suffix == ".jsonl":
                records.extend(_load_bot_jsonl(path))
            elif suffix == ".csv":
                records.extend(_load_bot_csv(path))
            else:
                records.extend(_load_bot_json(path))
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] failed to parse bot file {path}: {exc}")
    return records


@dataclass
class BotAggregate:
    runs: int
    outcomes: Counter
    avg_floors: float
    avg_steps: float
    action_fractions: Dict[str, float]


def aggregate_bot_records(records: List[BotRunRecord]) -> Optional[BotAggregate]:
    if not records:
        return None
    runs = len(records)
    outcomes = Counter(r.outcome for r in records)
    avg_floors = sum(r.floors for r in records) / runs
    avg_steps = sum(r.steps for r in records) / runs

    total_actions: Counter = Counter()
    for r in records:
        total_actions.update(r.actions)

    action_total = sum(total_actions.values())
    action_fractions = {k: _safe_div(v, action_total) for k, v in total_actions.items()}

    return BotAggregate(
        runs=runs,
        outcomes=outcomes,
        avg_floors=avg_floors,
        avg_steps=avg_steps,
        action_fractions=action_fractions,
    )


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def _render_ecosystem_console(summaries: List[EcosystemScenarioSummary]) -> str:
    if not summaries:
        return "Ecosystem: no inputs provided."
    grouped: Dict[str, List[EcosystemScenarioSummary]] = defaultdict(list)
    for s in summaries:
        grouped[s.family].append(s)

    lines: List[str] = ["Ecosystem Scenarios", "-" * 24]
    for family, entries in sorted(grouped.items()):
        lines.append(f"{family} family:")
        header = (
            "  scenario".ljust(28)
            + "runs".rjust(6)
            + " death%".rjust(8)
            + " p_hit%".rjust(8)
            + " m_hit%".rjust(8)
            + " bonus/run".rjust(11)
            + " plague/run".rjust(12)
            + " surprise/run".rjust(14)
        )
        lines.append(header)
        for entry in sorted(entries, key=lambda e: e.scenario_id):
            lines.append(
                f"  {entry.scenario_id.ljust(26)}"
                f"{entry.runs:6d}"
                f"{entry.player_death_rate*100:8.1f}"
                f"{entry.player_hit_rate*100:8.1f}"
                f"{entry.monster_hit_rate*100:8.1f}"
                f"{entry.bonus_attacks_per_run:11.2f}"
                f"{entry.plague_infections_per_run:12.2f}"
                f"{entry.surprise_attacks_per_run:14.2f}"
            )
        lines.append("")
    return "\n".join(lines).rstrip()


def _render_worldgen_console(summaries: List[WorldgenDepthSummary]) -> str:
    if not summaries:
        return "Worldgen: no inputs provided."
    lines = ["Worldgen Sanity", "-" * 16]
    for agg in sorted(summaries, key=lambda s: s.depth):
        lines.append(f"Depth {agg.depth} (runs {agg.runs}):")
        lines.append(
            f"  Walkable % avg {agg.walkable_avg*100:.2f} "
            f"(min {agg.walkable_min*100:.2f} / max {agg.walkable_max*100:.2f})"
        )
        lines.append(f"  Reachable % of walkable: {agg.reachable_avg*100:.2f}")
        lines.append(f"  Monsters per run (avg): {agg.monsters_avg:.1f}")
        lines.append(f"  Items per run (avg):    {agg.items_avg:.1f}")
        if agg.walkable_avg < 0.03:
            lines.append("  [WARN] Average walkable % < 3% — maps may be too cramped")
        lines.append("")
    return "\n".join(lines).rstrip()


def _render_bot_console(aggregate: Optional[BotAggregate]) -> str:
    if not aggregate:
        return "Bot Soak: no inputs provided."
    lines = ["Bot Soak Summary", "-" * 17]
    lines.append(f"Runs: {aggregate.runs}")
    lines.append("Outcomes:")
    for outcome, count in aggregate.outcomes.most_common():
        lines.append(f"  {outcome}: {count}")
    lines.append(f"Average floors cleared: {aggregate.avg_floors:.1f}")
    lines.append(f"Average steps per run:  {aggregate.avg_steps:.1f}")

    if aggregate.action_fractions:
        lines.append("Action breakdown (fraction):")
        for action, frac in sorted(aggregate.action_fractions.items(), key=lambda kv: kv[0]):
            lines.append(f"  {action}: {frac*100:.1f}%")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def _markdown_table(headers: List[str], rows: List[List[str]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_line, separator, *body])


def _render_ecosystem_markdown(summaries: List[EcosystemScenarioSummary]) -> str:
    if not summaries:
        return "## Ecosystem\n\n_No ecosystem files provided._"

    grouped: Dict[str, List[EcosystemScenarioSummary]] = defaultdict(list)
    for s in summaries:
        grouped[s.family].append(s)

    sections: List[str] = ["## Ecosystem"]
    for family, entries in sorted(grouped.items()):
        sections.append(f"### {family} family")
        rows: List[List[str]] = []
        for entry in sorted(entries, key=lambda e: e.scenario_id):
            rows.append(
                [
                    entry.scenario_id,
                    str(entry.runs),
                    f"{entry.player_death_rate*100:.1f}%",
                    f"{entry.player_hit_rate*100:.1f}%",
                    f"{entry.monster_hit_rate*100:.1f}%",
                    f"{entry.bonus_attacks_per_run:.2f}",
                    f"{entry.plague_infections_per_run:.2f}",
                    f"{entry.surprise_attacks_per_run:.2f}",
                ]
            )
        sections.append(
            _markdown_table(
                [
                    "scenario_id",
                    "runs",
                    "death_rate",
                    "player_hit",
                    "monster_hit",
                    "bonus/run",
                    "plague/run",
                    "surprise/run",
                ],
                rows,
            )
        )
    return "\n\n".join(sections)


def _render_worldgen_markdown(summaries: List[WorldgenDepthSummary]) -> str:
    if not summaries:
        return "## Worldgen\n\n_No worldgen files provided._"

    lines = ["## Worldgen"]
    for agg in sorted(summaries, key=lambda s: s.depth):
        lines.append(f"### Depth {agg.depth}")
        lines.append(
            f"- Walkable %: avg {agg.walkable_avg*100:.2f}% "
            f"(min {agg.walkable_min*100:.2f}% / max {agg.walkable_max*100:.2f}%)"
        )
        lines.append(f"- Reachable % of walkable: {agg.reachable_avg*100:.2f}%")
        lines.append(f"- Monsters per run (avg): {agg.monsters_avg:.1f}")
        lines.append(f"- Items per run (avg): {agg.items_avg:.1f}")
        if agg.walkable_avg < 0.03:
            lines.append("- Warning: Average walkable % < 3% — maps may be too cramped")
        lines.append("")
    return "\n".join(lines).strip()


def _render_bot_markdown(aggregate: Optional[BotAggregate]) -> str:
    if not aggregate:
        return "## Bot Soak\n\n_No bot soak files provided._"

    lines = ["## Bot Soak", f"- Runs: {aggregate.runs}"]
    if aggregate.outcomes:
        lines.append("- Outcomes:")
        for outcome, count in aggregate.outcomes.most_common():
            lines.append(f"  - {outcome}: {count}")
    lines.append(f"- Average floors cleared: {aggregate.avg_floors:.1f}")
    lines.append(f"- Average steps per run: {aggregate.avg_steps:.1f}")
    if aggregate.action_fractions:
        lines.append("- Action breakdown:")
        for action, frac in sorted(aggregate.action_fractions.items(), key=lambda kv: kv[0]):
            lines.append(f"  - {action}: {frac*100:.1f}%")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate ecosystem/worldgen/bot soak balance report.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--ecosystem-json",
        nargs="*",
        default=[],
        help="Paths to ecosystem_sanity JSON exports.",
    )
    parser.add_argument(
        "--worldgen-json",
        nargs="*",
        default=[],
        help="Paths to worldgen_sanity JSON exports.",
    )
    parser.add_argument(
        "--bot-soak-json",
        nargs="*",
        default=[],
        help="Paths to bot soak summaries in JSON (list or dict).",
    )
    parser.add_argument(
        "--bot-soak-jsonl",
        nargs="*",
        default=[],
        help="Paths to bot soak summaries in JSONL format.",
    )
    parser.add_argument(
        "--bot-soak-csv",
        nargs="*",
        default=[],
        help="Paths to bot soak CSV summaries.",
    )
    parser.add_argument(
        "--output-markdown",
        type=str,
        help="Optional path to write Markdown report.",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="Ecosystem & Bot Balance Report",
        help="Optional report title.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    eco_paths = [Path(p) for p in args.ecosystem_json]
    worldgen_paths = [Path(p) for p in args.worldgen_json]
    bot_paths: List[Path] = []
    bot_paths.extend(Path(p) for p in args.bot_soak_json)
    bot_paths.extend(Path(p) for p in args.bot_soak_jsonl)
    bot_paths.extend(Path(p) for p in args.bot_soak_csv)

    eco_summaries = load_ecosystem_summaries(eco_paths)
    worldgen_summaries = load_worldgen_summaries(worldgen_paths)
    bot_records = load_bot_records(bot_paths)
    bot_aggregate = aggregate_bot_records(bot_records)

    sections = [
        args.title,
        "=" * len(args.title),
        _render_ecosystem_console(eco_summaries),
        "",
        _render_worldgen_console(worldgen_summaries),
        "",
        _render_bot_console(bot_aggregate),
    ]
    console_output = "\n".join(sections).rstrip()
    print(console_output)

    if args.output_markdown:
        md_parts = [
            f"# {args.title}",
            _render_ecosystem_markdown(eco_summaries),
            _render_worldgen_markdown(worldgen_summaries),
            _render_bot_markdown(bot_aggregate),
        ]
        output_path = Path(args.output_markdown)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n\n".join(md_parts).strip() + "\n", encoding="utf-8")
        print(f"\nMarkdown report written to: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
