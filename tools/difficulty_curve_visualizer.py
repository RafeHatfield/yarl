#!/usr/bin/env python3
"""Generate difficulty curve graphs from normalized metrics."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import matplotlib

# Force headless plotting
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METRICS_DIR = REPO_ROOT / "reports" / "metrics"
DEFAULT_GRAPHS_DIR = REPO_ROOT / "reports" / "graphs"

# Heuristic identifiers for speed variants
SPEED_VARIANT_TOKENS = (
    "speed_full",
    "speed_light",
    "slow_zombie",
)


@dataclass
class NormalizedMetrics:
    scenario_id: str
    family: str
    runs: int
    depth: Optional[float]
    player_hit_rate: float
    monster_hit_rate: float
    bonus_attacks_per_run: float
    death_rate: float
    player_attacks_per_run: float
    monster_attacks_per_run: float
    pressure_index: float
    raw: Dict


def _load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _parse_metrics(path: Path) -> NormalizedMetrics:
    data = _load_json(path)
    return NormalizedMetrics(
        scenario_id=data.get("scenario_id", path.stem),
        family=data.get("family") or data.get("scenario_id", path.stem),
        runs=int(data.get("runs", 0) or 0),
        depth=data.get("depth"),
        player_hit_rate=float(data.get("player_hit_rate", 0.0)),
        monster_hit_rate=float(data.get("monster_hit_rate", 0.0)),
        bonus_attacks_per_run=float(data.get("bonus_attacks_per_run", 0.0)),
        death_rate=float(data.get("death_rate", 0.0)),
        player_attacks_per_run=float(data.get("player_attacks_per_run", 0.0)),
        monster_attacks_per_run=float(data.get("monster_attacks_per_run", 0.0)),
        pressure_index=float(data.get("pressure_index", 0.0)),
        raw=data.get("raw", {}),
    )


def load_metrics(metrics_dir: Path) -> List[NormalizedMetrics]:
    if not metrics_dir.exists():
        raise FileNotFoundError(f"Metrics directory not found: {metrics_dir}")
    metrics: List[NormalizedMetrics] = []
    for path in sorted(metrics_dir.glob("*.json")):
        try:
            metrics.append(_parse_metrics(path))
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] failed to parse {path}: {exc}", file=sys.stderr)
    return metrics


def _axis_mode_from_entries(entries: Sequence[NormalizedMetrics]) -> str:
    """Return 'depth' if any entry has depth, else 'family'."""
    return "depth" if any(e.depth is not None for e in entries) else "family"


def _filter_entries(
    entries: Sequence[NormalizedMetrics],
    *,
    families: Optional[Sequence[str]] = None,
    exclude_speed_variants: bool = False,
) -> List[NormalizedMetrics]:
    families_set = {f.strip() for f in families} if families else None
    filtered: List[NormalizedMetrics] = []
    for entry in entries:
        if families_set is not None and entry.family not in families_set:
            continue
        if exclude_speed_variants and any(token in entry.scenario_id for token in SPEED_VARIANT_TOKENS):
            continue
        filtered.append(entry)
    return filtered


def _aggregate_numeric(entries: Iterable[NormalizedMetrics], key: str) -> Tuple[List[float], List[float]]:
    grouped: Dict[float, List[NormalizedMetrics]] = defaultdict(list)
    for entry in entries:
        if entry.depth is None:
            continue
        grouped[float(entry.depth)].append(entry)

    xs: List[float] = []
    ys: List[float] = []
    for depth in sorted(grouped.keys()):
        bucket = grouped[depth]
        value = _weighted_mean(bucket, key)
        xs.append(depth)
        ys.append(value)
    return xs, ys


def _aggregate_categorical(entries: Iterable[NormalizedMetrics], key: str) -> Tuple[List[int], List[float], List[str]]:
    grouped: Dict[str, List[NormalizedMetrics]] = defaultdict(list)
    for entry in entries:
        grouped[entry.family].append(entry)

    xs: List[int] = []
    ys: List[float] = []
    labels: List[str] = []
    for idx, family in enumerate(sorted(grouped.keys())):
        bucket = grouped[family]
        value = _weighted_mean(bucket, key)
        xs.append(idx)
        ys.append(value)
        labels.append(family)
    return xs, ys, labels


def _weighted_mean(entries: List[NormalizedMetrics], key: str) -> float:
    """Weight by runs when present; otherwise simple mean."""
    numerator = 0.0
    denominator = 0.0
    for e in entries:
        weight = max(e.runs, 1)
        numerator += getattr(e, key, 0.0) * weight
        denominator += weight
    return numerator / denominator if denominator else 0.0


def _plot_line(xs: List[float], ys: List[float], *, title: str, x_label: str, y_label: str, out_path: Path, category_labels: Optional[List[str]] = None) -> None:
    fig, ax = plt.subplots(figsize=(12, 8))
    if category_labels:
        ax.plot(xs, ys, marker="o")
        ax.set_xticks(xs)
        ax.set_xticklabels(category_labels, rotation=20, ha="right")
    else:
        ax.plot(xs, ys, marker="o")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def _build_composite(depth_entries: List[NormalizedMetrics], family_entries: List[NormalizedMetrics], out_path: Path) -> None:
    metrics_keys = [
        ("player_hit_rate", "Player Hit Rate"),
        ("monster_hit_rate", "Monster Hit Rate"),
        ("death_rate", "Death Rate"),
        ("bonus_attacks_per_run", "Bonus Attacks / Run"),
        ("pressure_index", "Pressure Index"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    axes_flat = axes.flatten()

    use_depth = bool(depth_entries) or not family_entries
    entries = depth_entries if use_depth else family_entries
    x_label = "Depth" if use_depth else "Scenario Family"

    for ax, (key, title) in zip(axes_flat, metrics_keys):
        if use_depth:
            xs, ys = _aggregate_numeric(entries, key)
            ax.plot(xs, ys, marker="o")
            ax.set_xlabel(x_label)
            ax.set_title(f"{title} vs Depth")
        else:
            xs, ys, cats = _aggregate_categorical(entries, key)
            ax.plot(xs, ys, marker="o")
            ax.set_xticks(xs)
            ax.set_xticklabels(cats, rotation=25, ha="right")
            ax.set_xlabel(x_label)
            ax.set_title(f"{title} vs Scenario Family")
        ax.set_ylabel(title)
        ax.grid(True, linestyle="--", alpha=0.4)

    # Remove unused subplot (5 metrics -> 6 slots)
    if len(metrics_keys) < len(axes_flat):
        axes_flat[-1].axis("off")

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def create_graphs(entries: List[NormalizedMetrics], graphs_dir: Path) -> List[Path]:
    if not entries:
        raise ValueError("No metrics available for graphing.")

    axis_mode = _axis_mode_from_entries(entries)
    depth_entries = [e for e in entries if e.depth is not None]
    family_entries = [e for e in entries if e.depth is None]
    out_paths: List[Path] = []

    def emit(metric_key: str, title: str, y_label: str, filename: str) -> None:
        if axis_mode == "depth":
            xs, ys = _aggregate_numeric(depth_entries, metric_key)
            graph_title = f"{title} vs Depth"
            _plot_line(xs, ys, title=graph_title, x_label="Depth", y_label=y_label, out_path=graphs_dir / filename)
        else:
            xs, ys, labels = _aggregate_categorical(entries, metric_key)
            graph_title = f"{title} vs Scenario Family"
            _plot_line(
                xs,
                ys,
                title=graph_title,
                x_label="Scenario Family",
                y_label=y_label,
                out_path=graphs_dir / filename,
                category_labels=labels,
            )
        out_paths.append(graphs_dir / filename)

    emit("player_hit_rate", "Player Hit Rate", "Player Hit Rate", "player_hit_rate_vs_depth.png")
    emit("monster_hit_rate", "Monster Hit Rate", "Monster Hit Rate", "monster_hit_rate_vs_depth.png")
    emit("death_rate", "Death Rate", "Death Rate", "death_rate_vs_depth.png")
    emit("bonus_attacks_per_run", "Bonus Attacks per Run", "Bonus Attacks per Run", "bonus_attacks_per_run_vs_depth.png")
    emit("pressure_index", "Pressure Index", "Pressure Index", "pressure_index_vs_depth.png")

    composite_target = graphs_dir / "difficulty_curve_overview.png"
    _build_composite(depth_entries, entries if axis_mode == "depth" else family_entries, composite_target)
    out_paths.append(composite_target)
    return out_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate difficulty curve graphs.")
    parser.add_argument(
        "--metrics-dir",
        type=Path,
        default=DEFAULT_METRICS_DIR,
        help="Directory containing normalized metrics JSON files.",
    )
    parser.add_argument(
        "--graphs-dir",
        type=Path,
        default=DEFAULT_GRAPHS_DIR,
        help="Output directory for generated PNGs.",
    )
    parser.add_argument(
        "--families",
        type=str,
        default=None,
        help="Comma-separated list of families to include (default: all).",
    )
    parser.add_argument(
        "--exclude-speed-variants",
        action="store_true",
        help="Exclude speed variant scenarios (heuristic: speed_full, speed_light, slow_zombie).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    entries = load_metrics(args.metrics_dir)
    families = [f.strip() for f in args.families.split(",")] if args.families else None
    entries = _filter_entries(entries, families=families, exclude_speed_variants=args.exclude_speed_variants)
    if not entries:
        raise SystemExit("No metrics to plot after applying filters.")
    create_graphs(entries, args.graphs_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
