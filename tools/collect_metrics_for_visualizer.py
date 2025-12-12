#!/usr/bin/env python3
"""Collect ecosystem scenario metrics and normalize for the difficulty visualizer.

This script drives the existing Makefile JSON-export targets, copies the
resulting scenario exports into `reports/metrics/`, and adds normalized/derived
fields for downstream visualization:

- player_hit_rate
- monster_hit_rate
- bonus_attacks_per_run
- death_rate
- player_attacks_per_run
- monster_attacks_per_run
- pressure_index (monster_attacks_per_run - player_attacks_per_run)

Defaults assume repo-root execution, but paths can be overridden for tests.
All operations are headless and non-interactive.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METRICS_DIR = REPO_ROOT / "reports" / "metrics"


@dataclass(frozen=True)
class ScenarioJob:
    """Mapping between Makefile target and expected JSON output."""

    target: str
    output_json: Path


SCENARIO_JOBS: List[ScenarioJob] = [
    ScenarioJob("eco-plague-json", Path("plague_arena_100runs.json")),
    ScenarioJob("eco-backstab-json", Path("backstab_training_100runs.json")),
    ScenarioJob("eco-duel-baseline-json", Path("dueling_pit_50runs.json")),
    ScenarioJob("eco-duel-speed-light-json", Path("dueling_pit_speed_light_50runs.json")),
    ScenarioJob("eco-duel-speed-full-json", Path("dueling_pit_speed_full_50runs.json")),
    ScenarioJob("eco-duel-slow-zombie-baseline-json", Path("dueling_pit_slow_zombie_baseline_50runs.json")),
    ScenarioJob("eco-duel-slow-zombie-full-json", Path("dueling_pit_slow_zombie_speed_full_50runs.json")),
    ScenarioJob("eco-swarm-baseline-json", Path("orc_swarm_baseline_50runs.json")),
    ScenarioJob("eco-swarm-speed-full-json", Path("orc_swarm_speed_full_50runs.json")),
    ScenarioJob("eco-swarm-brutal-baseline-json", Path("orc_swarm_brutal_baseline_50runs.json")),
    ScenarioJob("eco-swarm-brutal-speed-full-json", Path("orc_swarm_brutal_speed_full_50runs.json")),
    ScenarioJob("eco-swarm-tight-json", Path("orc_swarm_tight_50runs.json")),
    ScenarioJob("eco-zombie-horde-json", Path("zombie_horde_50runs.json")),
]


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _scenario_family(scenario_id: str) -> str:
    parts = scenario_id.split("_")
    return "_".join(parts[:2]) if len(parts) > 1 else scenario_id


def _normalize_payload(payload: Dict, source_path: Path) -> Dict:
    """Return a normalized dict with derived fields."""
    metrics = payload.get("metrics", {})
    scenario_id = payload.get("scenario_id") or source_path.stem
    runs = metrics.get("runs") or payload.get("runs") or 0
    depth = payload.get("depth") or metrics.get("depth")

    total_player_attacks = metrics.get("total_player_attacks", 0)
    total_player_hits = metrics.get("total_player_hits", 0)
    total_monster_attacks = metrics.get("total_monster_attacks", 0)
    total_monster_hits = metrics.get("total_monster_hits", 0)
    total_bonus_attacks = metrics.get("total_bonus_attacks_triggered", 0)
    player_deaths = metrics.get("player_deaths", 0)

    player_attacks_per_run = _safe_div(total_player_attacks, runs)
    monster_attacks_per_run = _safe_div(total_monster_attacks, runs)

    normalized = {
        "scenario_id": scenario_id,
        "family": _scenario_family(scenario_id),
        "runs": runs,
        "depth": depth,
        "player_hit_rate": _safe_div(total_player_hits, total_player_attacks),
        "monster_hit_rate": _safe_div(total_monster_hits, total_monster_attacks),
        "bonus_attacks_per_run": _safe_div(total_bonus_attacks, runs),
        "death_rate": _safe_div(player_deaths, runs),
        "player_attacks_per_run": player_attacks_per_run,
        "monster_attacks_per_run": monster_attacks_per_run,
        "pressure_index": monster_attacks_per_run - player_attacks_per_run,
        "raw": payload,
    }
    return normalized


def run_make_targets(jobs: Iterable[ScenarioJob], *, dry_run: bool = False) -> None:
    """Execute each Makefile target serially (non-interactive)."""
    for job in jobs:
        if dry_run:
            print(f"[dry-run] skipping make {job.target}")
            continue
        print(f"[collect] make {job.target}")
        subprocess.run(["make", job.target], cwd=REPO_ROOT, check=True)


def collect_and_normalize(metrics_dir: Path, jobs: Iterable[ScenarioJob]) -> List[Path]:
    """Copy and normalize scenario JSON exports into metrics_dir."""
    metrics_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    for job in jobs:
        source_path = (REPO_ROOT / job.output_json).resolve()
        if not source_path.exists():
            print(f"[warn] missing expected export: {source_path}")
            continue
        try:
            payload = _load_json(source_path)
            normalized = _normalize_payload(payload, source_path)
            dest_name = f"{normalized['scenario_id']}_metrics.json"
            dest_path = metrics_dir / dest_name
            with dest_path.open("w", encoding="utf-8") as f:
                json.dump(normalized, f, indent=2, sort_keys=True)
            written.append(dest_path)
            print(f"[ok] wrote {dest_path.relative_to(REPO_ROOT)}")
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] failed to normalize {source_path}: {exc}")
    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect and normalize scenario metrics.")
    parser.add_argument(
        "--metrics-dir",
        type=Path,
        default=DEFAULT_METRICS_DIR,
        help="Destination directory for normalized metrics (default: reports/metrics).",
    )
    parser.add_argument(
        "--skip-make",
        action="store_true",
        help="Skip invoking Makefile targets (useful for tests when JSON already exists).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.skip_make:
        run_make_targets(SCENARIO_JOBS, dry_run=False)
    collect_and_normalize(args.metrics_dir, SCENARIO_JOBS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
