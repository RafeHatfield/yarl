"""Tests for soak harness metrics and CSV output.

Tests that:
1. SoakRunResult correctly captures metrics
2. SoakSessionResult aggregates correctly
3. CSV output is valid and contains expected data
"""

import csv
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from engine.soak_harness import SoakRunResult, SoakSessionResult


class TestSoakRunResult:
    """Tests for SoakRunResult dataclass."""
    
    def test_default_values(self):
        """SoakRunResult should have sensible defaults."""
        result = SoakRunResult(run_number=1)
        assert result.run_number == 1
        assert result.outcome == "unknown"
        assert result.persona == "balanced"
        assert result.monsters_killed == 0
        assert result.items_picked_up == 0
        assert result.exception is None
    
    def test_to_dict_includes_all_fields(self):
        """to_dict() should include all metrics fields."""
        result = SoakRunResult(
            run_number=1,
            run_id="abc123",
            seed=42,
            persona="aggressive",
            outcome="death",
            failure_type="death",
            failure_detail="",
            duration_seconds=60.5,
            deepest_floor=3,
            floors_visited=3,
            monsters_killed=15,
            items_picked_up=7,
            potions_used=2,
            portals_used=1,
            tiles_explored=500,
            steps_taken=300,
            floor_count=3,
            avg_etp_per_floor=1.5,
            exception=None,
            timestamp="2024-01-01T12:00:00",
        )
        
        d = result.to_dict()
        
        assert d['run_number'] == 1
        assert d['run_id'] == "abc123"
        assert d['seed'] == 42
        assert d['persona'] == "aggressive"
        assert d['outcome'] == "death"
        assert d['failure_type'] == "death"
        assert d['failure_detail'] == ""
        assert d['duration_seconds'] == 60.5
        assert d['deepest_floor'] == 3
        assert d['monsters_killed'] == 15
        assert d['items_picked_up'] == 7
        assert d['potions_used'] == 2
        assert d['portals_used'] == 1
        assert d['tiles_explored'] == 500
        assert d['steps_taken'] == 300
        assert d['timestamp'] == "2024-01-01T12:00:00"
    
    def test_from_run_metrics_and_telemetry_with_mock_metrics(self):
        """from_run_metrics_and_telemetry should extract data from mock metrics."""
        # Create a mock RunMetrics object
        class MockRunMetrics:
            run_id = "test-run-123"
            seed = None
            outcome = "death"
            duration_seconds = 45.0
            deepest_floor = 2
            floors_visited = 2
            monsters_killed = 10
            items_picked_up = 5
            portals_used = 0
            tiles_explored = 300
            steps_taken = 200
        
        mock_metrics = MockRunMetrics()
        telemetry_stats = {
            'floors': 2,
            'avg_etp_per_floor': 1.2,
            'potions_used': 1,
        }
        
        result = SoakRunResult.from_run_metrics_and_telemetry(
            run_number=1,
            run_metrics=mock_metrics,
            telemetry_stats=telemetry_stats,
            persona="cautious",
        )
        
        assert result.run_number == 1
        assert result.run_id == "test-run-123"
        assert result.persona == "cautious"
        assert result.outcome == "death"
        assert result.monsters_killed == 10
        assert result.potions_used == 1
        assert result.timestamp  # Should have a timestamp
    
    def test_from_run_metrics_and_telemetry_without_metrics(self):
        """from_run_metrics_and_telemetry should handle None metrics."""
        result = SoakRunResult.from_run_metrics_and_telemetry(
            run_number=5,
            run_metrics=None,
            telemetry_stats={'floors': 0},
            exception="Test crash",
            persona="greedy",
        )
        
        assert result.run_number == 5
        assert result.persona == "greedy"
        assert result.outcome == "error"
        assert result.exception == "Test crash"


class TestSoakSessionResult:
    """Tests for SoakSessionResult dataclass."""
    
    def test_compute_aggregates_with_multiple_runs(self):
        """compute_aggregates should correctly aggregate run data."""
        runs = [
            SoakRunResult(run_number=1, outcome="death", duration_seconds=30.0,
                         deepest_floor=2, floors_visited=2, monsters_killed=5, items_picked_up=3),
            SoakRunResult(run_number=2, outcome="death", duration_seconds=60.0,
                         deepest_floor=4, floors_visited=4, monsters_killed=15, items_picked_up=7),
            SoakRunResult(run_number=3, outcome="max_turns", duration_seconds=90.0,
                         deepest_floor=3, floors_visited=3, monsters_killed=10, items_picked_up=5),
        ]
        
        session = SoakSessionResult(total_runs=3, runs=runs)
        session.compute_aggregates()
        
        assert session.total_monsters_killed == 30  # 5 + 15 + 10
        assert session.total_items_picked_up == 15  # 3 + 7 + 5
        assert session.avg_duration == 60.0  # (30 + 60 + 90) / 3
        assert session.avg_deepest_floor == 3.0  # (2 + 4 + 3) / 3
    
    def test_compute_aggregates_excludes_crashed_runs(self):
        """compute_aggregates should exclude crashed runs from averages."""
        runs = [
            SoakRunResult(run_number=1, outcome="death", duration_seconds=30.0,
                         deepest_floor=2, monsters_killed=5),
            SoakRunResult(run_number=2, outcome="crash", duration_seconds=0.0,
                         deepest_floor=1, monsters_killed=0, exception="Crash!"),
        ]
        
        session = SoakSessionResult(total_runs=2, runs=runs)
        session.compute_aggregates()
        
        # Averages should only use valid run (run 1)
        assert session.avg_duration == 30.0
        assert session.avg_deepest_floor == 2.0
        # Totals include all runs
        assert session.total_monsters_killed == 5


class TestCSVOutput:
    """Tests for CSV file output."""
    
    def test_write_csv_creates_file(self):
        """write_csv should create a valid CSV file."""
        runs = [
            SoakRunResult(run_number=1, run_id="run-1", persona="balanced",
                         outcome="death", duration_seconds=30.0, monsters_killed=5),
            SoakRunResult(run_number=2, run_id="run-2", persona="balanced",
                         outcome="max_turns", duration_seconds=60.0, monsters_killed=10),
        ]
        
        session = SoakSessionResult(total_runs=2, runs=runs, persona="balanced")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "output" / "metrics.csv"
            session.write_csv(csv_path)
            
            # File should exist
            assert csv_path.exists()
            
            # Read and verify contents
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 2
            assert rows[0]['run_number'] == '1'
            assert rows[0]['run_id'] == 'run-1'
            assert rows[0]['persona'] == 'balanced'
            assert rows[0]['outcome'] == 'death'
            assert rows[1]['run_number'] == '2'
            assert rows[1]['monsters_killed'] == '10'
    
    def test_write_csv_creates_parent_directories(self):
        """write_csv should create parent directories if they don't exist."""
        runs = [SoakRunResult(run_number=1)]
        session = SoakSessionResult(total_runs=1, runs=runs)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Deeply nested path that doesn't exist
            csv_path = Path(tmpdir) / "a" / "b" / "c" / "metrics.csv"
            session.write_csv(csv_path)
            
            assert csv_path.exists()
    
    def test_csv_headers_match_expected_fields(self):
        """CSV headers should match the expected field names."""
        runs = [SoakRunResult(run_number=1)]
        session = SoakSessionResult(total_runs=1, runs=runs)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "metrics.csv"
            session.write_csv(csv_path)
            
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)
            
            expected_headers = [
                'run_number', 'run_id', 'seed', 'persona', 'outcome',
                'failure_type', 'failure_detail',
                'duration_seconds', 'deepest_floor', 'floors_visited',
                'monsters_killed', 'items_picked_up', 'potions_used', 'portals_used',
                'tiles_explored', 'steps_taken', 'floor_count', 'avg_etp_per_floor',
                'exception', 'timestamp'
            ]
            assert headers == expected_headers


class TestPersonaIntegration:
    """Tests for persona field in metrics."""
    
    def test_persona_preserved_in_run_result(self):
        """Persona should be preserved through the metrics pipeline."""
        result = SoakRunResult(run_number=1, persona="speedrunner")
        assert result.persona == "speedrunner"
        assert result.to_dict()['persona'] == "speedrunner"
    
    def test_session_persona_tracked(self):
        """SoakSessionResult should track the session persona."""
        session = SoakSessionResult(total_runs=10, persona="aggressive")
        assert session.persona == "aggressive"


class TestFailureClassification:
    """Tests for failure classification in SoakRunResult."""
    
    def test_classify_death(self):
        """Death outcome should classify as death."""
        failure_type, detail = SoakRunResult.classify_failure("death")
        assert failure_type == "death"
        assert detail == ""
    
    def test_classify_victory(self):
        """Victory outcome should classify as none (success)."""
        failure_type, detail = SoakRunResult.classify_failure("victory")
        assert failure_type == "none"
    
    def test_classify_max_floors(self):
        """max_floors outcome should classify as none (success)."""
        failure_type, detail = SoakRunResult.classify_failure("max_floors")
        assert failure_type == "none"
    
    def test_classify_max_turns(self):
        """max_turns outcome should classify as turn_limit."""
        failure_type, detail = SoakRunResult.classify_failure("max_turns")
        assert failure_type == "turn_limit"
        assert "turn limit" in detail.lower()
    
    def test_classify_bot_abort_stuck(self):
        """bot_abort with stuck reason should classify as stuck."""
        failure_type, detail = SoakRunResult.classify_failure(
            "bot_abort", bot_abort_reason="Stuck at position (5,10)"
        )
        assert failure_type == "stuck"
        assert "5,10" in detail
    
    def test_classify_bot_abort_movement_blocked(self):
        """bot_abort with movement blocked should classify as stuck."""
        failure_type, detail = SoakRunResult.classify_failure(
            "bot_abort", bot_abort_reason="Movement blocked 3 times"
        )
        assert failure_type == "stuck"
    
    def test_classify_bot_abort_stairs(self):
        """bot_abort with stairs reason should classify as no_stairs."""
        failure_type, detail = SoakRunResult.classify_failure(
            "bot_abort", bot_abort_reason="Floor complete but not on stairs"
        )
        assert failure_type == "no_stairs"
    
    def test_classify_crash(self):
        """crash outcome should classify as error."""
        failure_type, detail = SoakRunResult.classify_failure(
            "crash", exception="KeyError: 'x'"
        )
        assert failure_type == "error"
        assert "KeyError" in detail
    
    def test_classify_error_from_exception(self):
        """Presence of exception should classify as error."""
        failure_type, detail = SoakRunResult.classify_failure(
            "unknown", exception="Something went wrong"
        )
        assert failure_type == "error"
        assert "Something went wrong" in detail
    
    def test_failure_fields_in_to_dict(self):
        """failure_type and failure_detail should appear in to_dict()."""
        result = SoakRunResult(
            run_number=1,
            outcome="bot_abort",
            failure_type="stuck",
            failure_detail="Movement blocked at (3,4)",
        )
        d = result.to_dict()
        assert d['failure_type'] == "stuck"
        assert d['failure_detail'] == "Movement blocked at (3,4)"
    
    def test_failure_fields_in_csv(self):
        """failure_type and failure_detail should appear in CSV output."""
        runs = [
            SoakRunResult(
                run_number=1,
                outcome="death",
                failure_type="death",
                failure_detail="",
            ),
            SoakRunResult(
                run_number=2,
                outcome="bot_abort",
                failure_type="stuck",
                failure_detail="Oscillation detected",
            ),
        ]
        
        session = SoakSessionResult(total_runs=2, runs=runs)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "metrics.csv"
            session.write_csv(csv_path)
            
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert rows[0]['failure_type'] == 'death'
            assert rows[0]['failure_detail'] == ''
            assert rows[1]['failure_type'] == 'stuck'
            assert rows[1]['failure_detail'] == 'Oscillation detected'

