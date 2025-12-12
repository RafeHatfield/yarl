from pathlib import Path

from tools.bot_survivability_report import _iter_records, render_markdown, summarize


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join([json_dumps(r) for r in rows]), encoding="utf-8")


def json_dumps(obj: dict) -> str:
    import json

    return json.dumps(obj, separators=(",", ":"))


def test_survivability_report_basic(tmp_path):
    """Test basic survivability report with heals and deaths."""
    file_path = tmp_path / "soak.jsonl"
    rows = [
        {
            "run_metrics": {"outcome": "victory", "potions_used": 1},
            "bot_decisions": [
                {"decision_type": "drink_potion", "hp_percent": 0.30},
                {"decision_type": "drink_potion", "hp_percent": 0.50},
            ],
            "survivability": {"final_hp_percent": 0.8, "potions_remaining_on_death": 0},
        },
        {
            "run_metrics": {"outcome": "death", "potions_used": 0},
            "bot_decisions": [],
            "survivability": {
                "final_hp_percent": 0.0,
                "potions_remaining_on_death": 0,
                "scenario_id": "orc_swarm_baseline",
            },
        },
        {
            "run_metrics": {"outcome": "death", "potions_used": 0},
            "bot_decisions": [],
            "survivability": {
                "final_hp_percent": 0.1,
                "potions_remaining_on_death": 2,
                "scenario_id": "orc_swarm_baseline",
            },
        },
    ]
    _write_jsonl(file_path, rows)

    records = list(_iter_records([file_path]))
    summary = summarize(records)

    assert summary["heal_events"] == 2
    assert summary["deaths_total"] == 2
    assert summary["deaths_with_potions"] == 1
    assert summary["deaths_without_potions"] == 1

    report = render_markdown(summary)
    assert "Bot Survivability Report" in report
    assert "Heal events: 2" in report
    assert "orc_swarm_baseline" in report


def test_survivability_report_no_heals(tmp_path):
    """Test report when bot never healed (should show helpful message)."""
    file_path = tmp_path / "soak.jsonl"
    rows = [
        {
            "run_metrics": {"outcome": "death"},
            "bot_decisions": [
                {"decision_type": "move", "hp_percent": 0.20},
            ],
            "survivability": {
                "final_hp_percent": 0.0,
                "potions_remaining_on_death": 1,
            },
        },
    ]
    _write_jsonl(file_path, rows)

    records = list(_iter_records([file_path]))
    summary = summarize(records)
    report = render_markdown(summary)

    assert summary["heal_events"] == 0
    assert "No heal events found" in report
    assert "did the bot drink any potions" in report


def test_survivability_report_no_deaths(tmp_path):
    """Test report when bot never died (should show helpful message)."""
    file_path = tmp_path / "soak.jsonl"
    rows = [
        {
            "run_metrics": {"outcome": "victory"},
            "bot_decisions": [
                {"decision_type": "drink_potion", "hp_percent": 0.35},
            ],
            "survivability": {
                "final_hp_percent": 0.8,
                "potions_remaining_on_death": 0,
            },
        },
    ]
    _write_jsonl(file_path, rows)

    records = list(_iter_records([file_path]))
    summary = summarize(records)
    report = render_markdown(summary)

    assert summary["deaths_total"] == 0
    assert "No death events found" in report
    assert "survivability may be very high" in report
