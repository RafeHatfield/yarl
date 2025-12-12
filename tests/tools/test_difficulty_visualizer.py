import json
from pathlib import Path

from tools.difficulty_curve_visualizer import (
    NormalizedMetrics,
    _axis_mode_from_entries,
    _filter_entries,
    create_graphs,
    load_metrics,
)


def _write_metric(path: Path, scenario: str, *, depth=None) -> None:
    payload = {
        "scenario_id": scenario,
        "family": scenario.split("_")[0],
        "runs": 10,
        "depth": depth,
        "player_hit_rate": 0.6,
        "monster_hit_rate": 0.4,
        "bonus_attacks_per_run": 2.0,
        "death_rate": 0.1,
        "player_attacks_per_run": 8.0,
        "monster_attacks_per_run": 5.0,
        "pressure_index": -3.0,
        "raw": {"metrics": {"runs": 10}},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_graph_generation_smoke(tmp_path: Path) -> None:
    metrics_dir = tmp_path / "metrics"
    graphs_dir = tmp_path / "graphs"
    metrics_dir.mkdir()

    _write_metric(metrics_dir / "duel.json", "duel_family", depth=5)
    _write_metric(metrics_dir / "swarm.json", "swarm_family", depth=10)

    entries = load_metrics(metrics_dir)
    outputs = create_graphs(entries, graphs_dir)

    assert outputs
    assert (graphs_dir / "player_hit_rate_vs_depth.png").exists()
    assert (graphs_dir / "difficulty_curve_overview.png").exists()


def test_axis_mode_family_when_no_depth() -> None:
    entries = [
        NormalizedMetrics(
            scenario_id="orc_swarm_baseline",
            family="orc_swarm",
            runs=10,
            depth=None,
            player_hit_rate=0.7,
            monster_hit_rate=0.4,
            bonus_attacks_per_run=5.0,
            death_rate=0.1,
            player_attacks_per_run=10.0,
            monster_attacks_per_run=8.0,
            pressure_index=-2.0,
            raw={},
        )
    ]
    assert _axis_mode_from_entries(entries) == "family"


def test_axis_mode_depth_when_any_depth_present() -> None:
    entries = [
        NormalizedMetrics(
            scenario_id="dueling_pit",
            family="dueling_pit",
            runs=10,
            depth=None,
            player_hit_rate=0.6,
            monster_hit_rate=0.3,
            bonus_attacks_per_run=2.0,
            death_rate=0.0,
            player_attacks_per_run=7.0,
            monster_attacks_per_run=4.0,
            pressure_index=-3.0,
            raw={},
        ),
        NormalizedMetrics(
            scenario_id="depthy",
            family="depthy",
            runs=5,
            depth=3,
            player_hit_rate=0.5,
            monster_hit_rate=0.5,
            bonus_attacks_per_run=1.0,
            death_rate=0.2,
            player_attacks_per_run=6.0,
            monster_attacks_per_run=6.0,
            pressure_index=0.0,
            raw={},
        ),
    ]
    assert _axis_mode_from_entries(entries) == "depth"


def test_filtering_by_family_and_speed_variants() -> None:
    entries = [
        NormalizedMetrics(
            scenario_id="orc_swarm_speed_full",
            family="orc_swarm",
            runs=5,
            depth=None,
            player_hit_rate=0.5,
            monster_hit_rate=0.4,
            bonus_attacks_per_run=1.0,
            death_rate=0.1,
            player_attacks_per_run=4.0,
            monster_attacks_per_run=3.0,
            pressure_index=-1.0,
            raw={},
        ),
        NormalizedMetrics(
            scenario_id="orc_swarm_baseline",
            family="orc_swarm",
            runs=5,
            depth=None,
            player_hit_rate=0.7,
            monster_hit_rate=0.3,
            bonus_attacks_per_run=2.0,
            death_rate=0.05,
            player_attacks_per_run=5.0,
            monster_attacks_per_run=2.0,
            pressure_index=-3.0,
            raw={},
        ),
        NormalizedMetrics(
            scenario_id="plague_arena",
            family="plague_arena",
            runs=5,
            depth=None,
            player_hit_rate=0.8,
            monster_hit_rate=0.25,
            bonus_attacks_per_run=3.0,
            death_rate=0.2,
            player_attacks_per_run=6.0,
            monster_attacks_per_run=6.5,
            pressure_index=0.5,
            raw={},
        ),
    ]

    filtered = _filter_entries(entries, families=["plague_arena"], exclude_speed_variants=True)
    assert len(filtered) == 1
    assert filtered[0].scenario_id == "plague_arena"

    filtered_all = _filter_entries(entries, exclude_speed_variants=True)
    assert {e.scenario_id for e in filtered_all} == {"orc_swarm_baseline", "plague_arena"}
