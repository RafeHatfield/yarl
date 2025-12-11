#!/usr/bin/env python3
"""World Generation Sanity Harness.

Generates many maps, captures basic invariants/metrics, and can export JSON
for offline analysis. This is renderer-agnostic and runs headless.
"""

import argparse
import json
import os
import warnings
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple

# Headless mode for tcod
os.environ["SDL_VIDEODRIVER"] = "dummy"
warnings.filterwarnings("ignore")

from balance.etp import get_monster_etp
from config.testing_config import get_testing_config, set_testing_mode
from loader_functions.initialize_new_game import get_constants, get_game_variables
from map_objects.rectangle import Rect


@dataclass
class RunRoomMetrics:
    room_id: int
    area: int
    monsters: int
    items: int
    monster_etp: float


@dataclass
class RunMetrics:
    depth: int
    run: int
    width: int
    height: int
    walkable: int
    total_tiles: int
    walkable_percent: float
    reachable_tiles: int
    reachable_percent: float
    monsters: int
    items: int
    rooms: List[RunRoomMetrics]


@dataclass
class AggregatedDepthMetrics:
    depth: int
    runs: int
    walkable_avg: float
    walkable_min: float
    walkable_max: float
    reachable_avg: float
    monsters_avg: float
    items_avg: float


def _reset_testing_config(depth: int) -> None:
    """Reset testing config for a clean run and set target depth."""
    from config import testing_config as tc_module
    tc_module._testing_config = None
    set_testing_mode(True)
    config = get_testing_config()
    config.start_level = depth


def _point_in_room(rect: Rect, x: int, y: int) -> bool:
    """Check if a point lies inside a room interior."""
    return rect.x1 < x < rect.x2 and rect.y1 < y < rect.y2


def _reachable_tiles(game_map, start: Tuple[int, int]) -> int:
    """Breadth-first search to count reachable walkable tiles."""
    width, height = game_map.width, game_map.height
    tiles = game_map.tiles
    visited = [[False for _ in range(height)] for _ in range(width)]
    sx, sy = start
    if sx < 0 or sy < 0 or sx >= width or sy >= height:
        return 0
    if tiles[sx][sy].blocked:
        return 0

    q = deque()
    q.append((sx, sy))
    visited[sx][sy] = True
    reachable = 1

    neighbors = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    while q:
        x, y = q.popleft()
        for dx, dy in neighbors:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and not visited[nx][ny]:
                if not tiles[nx][ny].blocked:
                    visited[nx][ny] = True
                    reachable += 1
                    q.append((nx, ny))
    return reachable


def _collect_run_metrics(depth: int, run_idx: int) -> RunMetrics:
    """Generate a single map and collect metrics."""
    _reset_testing_config(depth)
    constants = get_constants()
    player, entities, game_map, _, _ = get_game_variables(constants)

    walkable, total_tiles, walkable_percent = game_map.get_walkable_stats()
    reachable = _reachable_tiles(game_map, (player.x, player.y))
    reachable_percent = (reachable / walkable) if walkable else 0.0

    monsters = [
        e for e in entities
        if getattr(e, "fighter", None) and getattr(e, "ai", None) and e.name != "Player"
    ]
    items = [
        e for e in entities
        if getattr(e, "item", None) and e.x >= 0 and e.y >= 0
    ]

    # Per-room metrics
    room_metrics: List[RunRoomMetrics] = []
    for idx, room_entry in enumerate(getattr(game_map, "rooms", [])):
        rect = room_entry.get("rect")
        if not isinstance(rect, Rect):
            continue

        area = max(0, (rect.x2 - rect.x1 - 1) * (rect.y2 - rect.y1 - 1))
        room_monsters = [
            m for m in monsters if _point_in_room(rect, m.x, m.y)
        ]
        room_items = [
            it for it in items if _point_in_room(rect, it.x, it.y)
        ]

        room_etp = 0.0
        for m in room_monsters:
            monster_type = getattr(m, "name", "unknown")
            room_etp += get_monster_etp(monster_type, depth)

        room_metrics.append(
            RunRoomMetrics(
                room_id=idx,
                area=area,
                monsters=len(room_monsters),
                items=len(room_items),
                monster_etp=room_etp,
            )
        )

    return RunMetrics(
        depth=depth,
        run=run_idx,
        width=game_map.width,
        height=game_map.height,
        walkable=walkable,
        total_tiles=total_tiles,
        walkable_percent=walkable_percent,
        reachable_tiles=reachable,
        reachable_percent=reachable_percent,
        monsters=len(monsters),
        items=len(items),
        rooms=room_metrics,
    )


def _aggregate_by_depth(run_metrics: List[RunMetrics]) -> List[AggregatedDepthMetrics]:
    """Aggregate metrics across runs for each depth."""
    grouped: Dict[int, List[RunMetrics]] = defaultdict(list)
    for m in run_metrics:
        grouped[m.depth].append(m)

    aggregates: List[AggregatedDepthMetrics] = []
    for depth, metrics in sorted(grouped.items()):
        runs = len(metrics)
        walkables = [m.walkable_percent for m in metrics]
        reachables = [m.reachable_percent for m in metrics]
        monsters = [m.monsters for m in metrics]
        items = [m.items for m in metrics]

        aggregates.append(
            AggregatedDepthMetrics(
                depth=depth,
                runs=runs,
                walkable_avg=sum(walkables) / runs if runs else 0.0,
                walkable_min=min(walkables) if runs else 0.0,
                walkable_max=max(walkables) if runs else 0.0,
                reachable_avg=sum(reachables) / runs if runs else 0.0,
                monsters_avg=sum(monsters) / runs if runs else 0.0,
                items_avg=sum(items) / runs if runs else 0.0,
            )
        )

    return aggregates


def _print_summary(aggregates: List[AggregatedDepthMetrics], runs: int) -> None:
    """Print a concise CLI summary."""
    print("\nWorldgen Sanity Results")
    print("=" * 64)
    if not aggregates:
        print("No results to display.")
        return

    print(f"Runs per depth: {runs}")
    for agg in aggregates:
        print("-" * 64)
        print(f"Depth {agg.depth}")
        print(f"  Walkable %: avg {agg.walkable_avg * 100:.2f}% "
              f"(min {agg.walkable_min * 100:.2f}% / max {agg.walkable_max * 100:.2f}%)")
        print(f"  Reachable % of walkable: avg {agg.reachable_avg * 100:.2f}%")
        print(f"  Monsters per run (avg): {agg.monsters_avg:.1f}")
        print(f"  Items per run (avg):    {agg.items_avg:.1f}")
        if agg.walkable_avg < 0.03:
            print("  [WARN] Average walkable % < 3% — maps may be too cramped")
    print("-" * 64)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Headless world generation sanity harness (mapgen + spawns)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=10,
        help="Number of runs per depth",
    )
    parser.add_argument(
        "--depth",
        type=int,
        help="Single depth to generate (default 1 if neither depth nor range is provided)",
    )
    parser.add_argument(
        "--depth-range",
        type=str,
        help="Inclusive depth range, e.g. 1-3",
    )
    parser.add_argument(
        "--export-json",
        type=str,
        help="Path to write JSON with per-run metrics and per-depth aggregates",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-run results (walkable %, reachable %, counts)",
    )
    return parser.parse_args()


def _parse_depths(args: argparse.Namespace) -> List[int]:
    if args.depth is not None:
        return [args.depth]
    if args.depth_range:
        try:
            start, end = args.depth_range.split("-")
            start_i, end_i = int(start), int(end)
            if start_i > end_i:
                start_i, end_i = end_i, start_i
            return list(range(start_i, end_i + 1))
        except ValueError:
            raise SystemExit("Invalid --depth-range format. Use e.g. 1-3")
    return [1]


def main() -> None:
    args = parse_args()
    depths = _parse_depths(args)

    all_runs: List[RunMetrics] = []

    for depth in depths:
        for run_idx in range(1, args.runs + 1):
            metrics = _collect_run_metrics(depth, run_idx)
            all_runs.append(metrics)
            if args.verbose:
                print(
                    f"Depth {depth} run {run_idx}: "
                    f"walkable {metrics.walkable_percent*100:.2f}% | "
                    f"reachable {metrics.reachable_percent*100:.2f}% | "
                    f"monsters {metrics.monsters} | items {metrics.items}"
                )

    aggregates = _aggregate_by_depth(all_runs)
    _print_summary(aggregates, args.runs)

    if args.export_json:
        export_data = {
            "runs": [asdict(r) for r in all_runs],
            "aggregates": [asdict(a) for a in aggregates],
        }
        with open(args.export_json, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2)
        print(f"Exported metrics (runs + aggregates) to {args.export_json}")


if __name__ == "__main__":
    main()
