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


def test_survivability_small_dataset_warning(tmp_path, capsys):
    """Test warning when dataset has fewer than 200 events."""
    from tools.bot_survivability_report import main
    import sys
    
    file_path = tmp_path / "soak.jsonl"
    # Create very small dataset (1 record)
    rows = [
        {
            "run_metrics": {"outcome": "victory"},
            "bot_decisions": [],
            "survivability": {"final_hp_percent": 0.8, "potions_remaining_on_death": 0},
        }
    ]
    _write_jsonl(file_path, rows)
    
    # Mock sys.argv to pass file path
    original_argv = sys.argv
    try:
        sys.argv = ["bot_survivability_report.py", "--input", str(file_path)]
        main()
        
        captured = capsys.readouterr()
        assert "WARNING: Small dataset (1 events)" in captured.err
        assert "statistically significant" in captured.err
    finally:
        sys.argv = original_argv


def test_survivability_no_scenario_warning(tmp_path, capsys):
    """Test warning when no scenario data is found."""
    from tools.bot_survivability_report import main
    import sys
    
    file_path = tmp_path / "soak.jsonl"
    # Create dataset without scenario_id
    rows = [
        {
            "run_metrics": {"outcome": "death"},
            "bot_decisions": [],
            "survivability": {"final_hp_percent": 0.0, "potions_remaining_on_death": 0},
        }
    ]
    _write_jsonl(file_path, rows)
    
    original_argv = sys.argv
    try:
        sys.argv = ["bot_survivability_report.py", "--input", str(file_path)]
        main()
        
        captured = capsys.readouterr()
        assert "WARNING: No scenario data found" in captured.err
        assert "scenario_id" in captured.err
    finally:
        sys.argv = original_argv


def test_survivability_scenario_table_format(tmp_path):
    """Test that scenario breakdown uses table format."""
    file_path = tmp_path / "soak.jsonl"
    rows = [
        {
            "run_metrics": {"outcome": "death"},
            "bot_decisions": [],
            "survivability": {
                "final_hp_percent": 0.0,
                "potions_remaining_on_death": 2,
                "scenario_id": "test_scenario_a",
            },
        },
        {
            "run_metrics": {"outcome": "death"},
            "bot_decisions": [],
            "survivability": {
                "final_hp_percent": 0.1,
                "potions_remaining_on_death": 0,
                "scenario_id": "test_scenario_b",
            },
        },
    ]
    _write_jsonl(file_path, rows)

    records = list(_iter_records([file_path]))
    summary = summarize(records)
    report = render_markdown(summary)

    # Check for table formatting
    assert "| Scenario | Deaths | Unused Potion Deaths | % Unused |" in report
    assert "|----------|--------|---------------------|----------|" in report
    assert "| test_scenario_a |" in report
    assert "| test_scenario_b |" in report


def test_survivability_scenario_grouping(tmp_path):
    """Test that events are correctly grouped by scenario_id."""
    file_path = tmp_path / "soak.jsonl"
    rows = [
        {
            "run_metrics": {"outcome": "death", "scenario_id": "scenario_1"},
            "bot_decisions": [],
            "survivability": {
                "final_hp_percent": 0.0,
                "potions_remaining_on_death": 1,
                "scenario_id": "scenario_1",
            },
        },
        {
            "run_metrics": {"outcome": "death", "scenario_id": "scenario_1"},
            "bot_decisions": [],
            "survivability": {
                "final_hp_percent": 0.0,
                "potions_remaining_on_death": 0,
                "scenario_id": "scenario_1",
            },
        },
        {
            "run_metrics": {"outcome": "death", "scenario_id": "scenario_2"},
            "bot_decisions": [],
            "survivability": {
                "final_hp_percent": 0.0,
                "potions_remaining_on_death": 2,
                "scenario_id": "scenario_2",
            },
        },
    ]
    _write_jsonl(file_path, rows)

    records = list(_iter_records([file_path]))
    summary = summarize(records)

    # Verify scenario grouping
    assert "scenario_1" in summary["scenario_buckets"]
    assert "scenario_2" in summary["scenario_buckets"]
    
    scenario_1 = summary["scenario_buckets"]["scenario_1"]
    assert scenario_1["deaths"] == 2
    assert scenario_1["unused_potion_deaths"] == 1
    
    scenario_2 = summary["scenario_buckets"]["scenario_2"]
    assert scenario_2["deaths"] == 1
    assert scenario_2["unused_potion_deaths"] == 1
