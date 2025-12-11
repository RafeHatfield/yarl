import json
from pathlib import Path

import pytest

from tools.eco_balance_report import (
    aggregate_bot_records,
    load_bot_records,
    load_ecosystem_summaries,
    load_worldgen_summaries,
)


def test_ecosystem_hit_rates(tmp_path: Path) -> None:
    path = tmp_path / "eco.json"
    path.write_text(
        json.dumps(
            {
                "scenario_id": "dueling_pit_speed_full",
                "runs": 10,
                "metrics": {
                    "runs": 10,
                    "average_turns": 50.0,
                    "player_deaths": 2,
                    "total_player_attacks": 100,
                    "total_player_hits": 60,
                    "total_monster_attacks": 80,
                    "total_monster_hits": 20,
                    "total_bonus_attacks_triggered": 30,
                    "total_plague_infections": 0,
                    "total_surprise_attacks": 5,
                },
            }
        )
    )

    summaries = load_ecosystem_summaries([path])
    assert len(summaries) == 1
    s = summaries[0]
    assert s.player_death_rate == pytest.approx(0.2)
    assert s.player_hit_rate == pytest.approx(0.6)
    assert s.monster_hit_rate == pytest.approx(0.25)
    assert s.bonus_attacks_per_run == pytest.approx(3.0)
    assert s.surprise_attacks_per_run == pytest.approx(0.5)


def test_worldgen_aggregates(tmp_path: Path) -> None:
    path = tmp_path / "worldgen.json"
    path.write_text(
        json.dumps(
            {
                "aggregates": [
                    {
                        "depth": 3,
                        "runs": 2,
                        "walkable_avg": 0.08,
                        "walkable_min": 0.07,
                        "walkable_max": 0.09,
                        "reachable_avg": 0.99,
                        "monsters_avg": 12.0,
                        "items_avg": 5.0,
                    }
                ]
            }
        )
    )
    summaries = load_worldgen_summaries([path])
    assert len(summaries) == 1
    assert summaries[0].walkable_avg == pytest.approx(0.08)
    assert summaries[0].monsters_avg == pytest.approx(12.0)


def test_bot_jsonl_aggregation(tmp_path: Path) -> None:
    path = tmp_path / "bot.jsonl"
    line = {
        "run_metrics": {"outcome": "run_complete", "floors_visited": 2, "steps_taken": 10},
        "bot_summary": {"total_steps": 10, "floors_seen": 2, "action_counts": {"attack": 6, "explore": 4}},
    }
    line2 = {
        "run_metrics": {"outcome": "bot_abort", "floors_visited": 1, "steps_taken": 6},
        "bot_summary": {"total_steps": 6, "floors_seen": 1, "action_counts": {"attack": 3, "explore": 3}},
    }
    path.write_text("\n".join(json.dumps(l) for l in [line, line2]))

    records = load_bot_records([path])
    agg = aggregate_bot_records(records)
    assert agg is not None
    assert agg.runs == 2
    assert agg.outcomes["run_complete"] == 1
    assert agg.outcomes["bot_abort"] == 1
    assert agg.avg_floors == pytest.approx(1.5)
    assert agg.avg_steps == pytest.approx(8.0)
    # 16 total actions across runs; 9 attacks, 7 explore
    assert agg.action_fractions["attack"] == pytest.approx(9 / 16)
    assert agg.action_fractions["explore"] == pytest.approx(7 / 16)


def test_handles_empty_bot_records() -> None:
    assert aggregate_bot_records([]) is None
