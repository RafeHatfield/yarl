import json
from pathlib import Path

from tools.generate_difficulty_dashboard import _render_family_insights, build_dashboard


def _write_metric(path: Path, scenario: str) -> None:
    payload = {
        "scenario_id": scenario,
        "family": scenario.split("_")[0],
        "runs": 5,
        "depth": None,
        "player_hit_rate": 0.5,
        "monster_hit_rate": 0.25,
        "bonus_attacks_per_run": 1.5,
        "death_rate": 0.2,
        "player_attacks_per_run": 6.0,
        "monster_attacks_per_run": 4.0,
        "pressure_index": -2.0,
        "raw": {"metrics": {"runs": 5}},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_dashboard_writes(tmp_path: Path) -> None:
    metrics_dir = tmp_path / "metrics"
    graphs_dir = tmp_path / "graphs"
    metrics_dir.mkdir()
    graphs_dir.mkdir()

    _write_metric(metrics_dir / "sample.json", "sample_scenario")

    # add a fake graph so the link renders
    (graphs_dir / "player_hit_rate_vs_depth.png").write_bytes(b"fake")

    dashboard = build_dashboard(metrics_dir=metrics_dir, graphs_dir=graphs_dir, eco_report=tmp_path / "eco.md")
    output_path = tmp_path / "dashboard.md"
    output_path.write_text(dashboard, encoding="utf-8")

    contents = output_path.read_text(encoding="utf-8")
    assert "sample_scenario" in contents
    assert "Graphs" in contents


def test_family_insights_rendering() -> None:
    metrics = [
        {
            "scenario_id": "orc_swarm_baseline",
            "family": "orc_swarm",
            "runs": 5,
            "death_rate": 0.1,
            "player_hit_rate": 0.7,
            "monster_hit_rate": 0.35,
            "bonus_attacks_per_run": 8.0,
            "pressure_index": -6.0,
        },
        {
            "scenario_id": "plague_arena",
            "family": "plague_arena",
            "runs": 5,
            "death_rate": 0.2,
            "player_hit_rate": 0.8,
            "monster_hit_rate": 0.25,
            "bonus_attacks_per_run": 12.0,
            "pressure_index": 6.0,
        },
    ]

    rendered = _render_family_insights(metrics)
    assert "## Family Insights" in rendered
    assert "orc_swarm" in rendered
    assert "plague_arena" in rendered
    assert "deaths" in rendered
