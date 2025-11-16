"""Tests for bot soak harness (Phase 1.6).

These tests verify that the soak harness can orchestrate multiple bot runs,
capture metrics correctly, and aggregate session statistics.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from engine.soak_harness import (
    SoakRunResult,
    SoakSessionResult,
    run_bot_soak,
)


class TestSoakRunResult:
    """Tests for SoakRunResult dataclass."""
    
    def test_from_run_metrics_and_telemetry_with_valid_metrics(self):
        """Test creating SoakRunResult from valid run_metrics."""
        # Mock RunMetrics
        mock_run_metrics = Mock()
        mock_run_metrics.run_id = "test-run-123"
        mock_run_metrics.outcome = "death"
        mock_run_metrics.duration_seconds = 42.5
        mock_run_metrics.deepest_floor = 3
        mock_run_metrics.floors_visited = 3
        mock_run_metrics.monsters_killed = 7
        mock_run_metrics.tiles_explored = 150
        mock_run_metrics.steps_taken = 200
        
        telemetry_stats = {
            'floors': 3,
            'avg_etp_per_floor': 25.5,
        }
        
        result = SoakRunResult.from_run_metrics_and_telemetry(
            run_number=1,
            run_metrics=mock_run_metrics,
            telemetry_stats=telemetry_stats,
            exception=None,
        )
        
        assert result.run_number == 1
        assert result.run_id == "test-run-123"
        assert result.outcome == "death"
        assert result.duration_seconds == 42.5
        assert result.deepest_floor == 3
        assert result.monsters_killed == 7
        assert result.floor_count == 3
        assert result.avg_etp_per_floor == 25.5
        assert result.exception is None
    
    def test_from_run_metrics_and_telemetry_with_none_metrics(self):
        """Test fallback when run_metrics is None."""
        telemetry_stats = {
            'floors': 2,
            'avg_etp_per_floor': 10.0,
        }
        
        result = SoakRunResult.from_run_metrics_and_telemetry(
            run_number=2,
            run_metrics=None,
            telemetry_stats=telemetry_stats,
            exception="Test exception",
        )
        
        assert result.run_number == 2
        assert result.run_id == ""
        assert result.outcome == "error"
        assert result.floor_count == 2
        assert result.exception == "Test exception"


class TestSoakSessionResult:
    """Tests for SoakSessionResult dataclass."""
    
    def test_compute_aggregates_with_multiple_runs(self):
        """Test aggregate computation across multiple runs."""
        session = SoakSessionResult(total_runs=3)
        
        # Add 3 successful runs
        session.runs = [
            SoakRunResult(
                run_number=1,
                run_id="run1",
                outcome="death",
                duration_seconds=30.0,
                deepest_floor=2,
                floors_visited=2,
                monsters_killed=5,
                exception=None,
            ),
            SoakRunResult(
                run_number=2,
                run_id="run2",
                outcome="death",
                duration_seconds=50.0,
                deepest_floor=4,
                floors_visited=4,
                monsters_killed=10,
                exception=None,
            ),
            SoakRunResult(
                run_number=3,
                run_id="run3",
                outcome="quit",
                duration_seconds=20.0,
                deepest_floor=1,
                floors_visited=1,
                monsters_killed=0,
                exception=None,
            ),
        ]
        
        session.compute_aggregates()
        
        # Check aggregates
        assert session.avg_duration == pytest.approx(33.33, rel=0.01)  # (30 + 50 + 20) / 3 ≈ 33.33
        assert session.avg_deepest_floor == pytest.approx(2.33, rel=0.1)  # (2 + 4 + 1) / 3
        assert session.avg_floors_per_run == pytest.approx(2.33, rel=0.1)  # (2 + 4 + 1) / 3
        assert session.total_monsters_killed == 15  # 5 + 10 + 0
    
    def test_compute_aggregates_filters_crashed_runs(self):
        """Test that crashed runs are excluded from aggregates."""
        session = SoakSessionResult(total_runs=3)
        
        session.runs = [
            SoakRunResult(
                run_number=1,
                outcome="death",
                duration_seconds=30.0,
                deepest_floor=2,
                floors_visited=2,
                monsters_killed=5,
                exception=None,
            ),
            SoakRunResult(
                run_number=2,
                outcome="crash",
                duration_seconds=0.0,
                deepest_floor=1,
                floors_visited=1,
                monsters_killed=0,
                exception="Test crash",
            ),
            SoakRunResult(
                run_number=3,
                outcome="death",
                duration_seconds=40.0,
                deepest_floor=3,
                floors_visited=3,
                monsters_killed=8,
                exception=None,
            ),
        ]
        
        session.compute_aggregates()
        
        # Aggregates should only include runs 1 and 3 (not crashed run 2)
        assert session.avg_duration == 35.0  # (30 + 40) / 2
        assert session.avg_deepest_floor == 2.5  # (2 + 3) / 2
        assert session.total_monsters_killed == 13  # 5 + 0 + 8 (crashed run still counts for total)
    
    def test_print_summary_does_not_crash(self, capsys):
        """Test that print_summary produces output without crashing."""
        session = SoakSessionResult(
            total_runs=2,
            completed_runs=2,
            bot_crashes=0,
            session_duration_seconds=100.0,
        )
        
        session.runs = [
            SoakRunResult(
                run_number=1,
                run_id="run1",
                outcome="death",
                duration_seconds=50.0,
                deepest_floor=2,
                monsters_killed=5,
            ),
            SoakRunResult(
                run_number=2,
                run_id="run2",
                outcome="death",
                duration_seconds=50.0,
                deepest_floor=3,
                monsters_killed=7,
            ),
        ]
        
        session.compute_aggregates()
        session.print_summary()
        
        captured = capsys.readouterr()
        assert "Bot Soak Session Summary" in captured.out
        assert "Runs: 2" in captured.out
        assert "Completed: 2" in captured.out
        assert "Crashes: 0" in captured.out


class TestRunBotSoakIntegration:
    """Integration-ish tests for run_bot_soak (with heavy mocking)."""
    
    @patch('tcod.libtcodpy.console_new')
    @patch('loader_functions.initialize_new_game.get_game_variables')
    @patch('engine_integration.play_game_with_engine')
    @patch('instrumentation.run_metrics.get_run_metrics_recorder')
    @patch('services.telemetry_service.get_telemetry_service')
    @patch('instrumentation.run_metrics.reset_run_metrics_recorder')
    @patch('services.telemetry_service.reset_telemetry_service')
    def test_run_bot_soak_completes_multiple_runs(
        self,
        mock_reset_telemetry,
        mock_reset_run_metrics,
        mock_get_telemetry,
        mock_get_recorder,
        mock_play_game,
        mock_get_game_vars,
        mock_console_new,
    ):
        """Test that run_bot_soak completes N runs successfully."""
        # Mock game setup
        mock_player = Mock()
        mock_entities = []
        mock_game_map = Mock()
        mock_message_log = Mock()
        mock_game_state = Mock()
        
        mock_get_game_vars.return_value = (
            mock_player, mock_entities, mock_game_map, 
            mock_message_log, mock_game_state
        )
        
        # Mock play_game returns successfully
        mock_play_game.return_value = {"restart": False}
        
        # Mock run metrics recorder
        mock_recorder = Mock()
        mock_run_metrics = Mock()
        mock_run_metrics.run_id = "test-run"
        mock_run_metrics.outcome = "death"
        mock_run_metrics.duration_seconds = 30.0
        mock_run_metrics.deepest_floor = 2
        mock_run_metrics.floors_visited = 2
        mock_run_metrics.monsters_killed = 5
        mock_run_metrics.tiles_explored = 100
        mock_run_metrics.steps_taken = 150
        mock_run_metrics.to_dict.return_value = {}
        
        mock_recorder.get_metrics.return_value = mock_run_metrics
        mock_get_recorder.return_value = mock_recorder
        
        # Mock telemetry service
        mock_telemetry = Mock()
        mock_telemetry.get_stats.return_value = {
            'floors': 2,
            'avg_etp_per_floor': 20.0,
            'total_traps': 1,
            'total_secrets': 0,
            'total_doors': 2,
            'total_keys': 1,
        }
        mock_get_telemetry.return_value = mock_telemetry
        
        # Mock console creation
        mock_console_new.return_value = Mock()
        
        # Run soak with 3 runs
        constants = {'input_config': {}}
        result = run_bot_soak(
            runs=3,
            telemetry_enabled=False,
            telemetry_output_path=None,
            constants=constants,
        )
        
        # Verify results
        assert result.total_runs == 3
        assert result.completed_runs == 3
        assert result.bot_crashes == 0
        assert len(result.runs) == 3
        
        # Verify all runs have correct structure
        for i, run in enumerate(result.runs, start=1):
            assert run.run_number == i
            assert run.outcome == "death"
            assert run.deepest_floor == 2
            assert run.monsters_killed == 5
        
        # Verify reset called before each run
        assert mock_reset_run_metrics.call_count == 3
        assert mock_reset_telemetry.call_count == 3
    
    @patch('tcod.libtcodpy.console_new')
    @patch('loader_functions.initialize_new_game.get_game_variables')
    @patch('engine_integration.play_game_with_engine')
    @patch('instrumentation.run_metrics.get_run_metrics_recorder')
    @patch('services.telemetry_service.get_telemetry_service')
    @patch('instrumentation.run_metrics.reset_run_metrics_recorder')
    @patch('services.telemetry_service.reset_telemetry_service')
    def test_run_bot_soak_handles_exceptions(
        self,
        mock_reset_telemetry,
        mock_reset_run_metrics,
        mock_get_telemetry,
        mock_get_recorder,
        mock_play_game,
        mock_get_game_vars,
        mock_console_new,
    ):
        """Test that run_bot_soak handles exceptions gracefully."""
        # First run succeeds, second run crashes, third run succeeds
        mock_get_game_vars.return_value = (Mock(), [], Mock(), Mock(), Mock())
        
        call_count = [0]
        def play_game_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise RuntimeError("Test crash in run 2")
            return {"restart": False}
        
        mock_play_game.side_effect = play_game_side_effect
        
        # Mock recorder and telemetry
        mock_recorder = Mock()
        mock_run_metrics = Mock()
        mock_run_metrics.run_id = "test-run"
        mock_run_metrics.outcome = "death"
        mock_run_metrics.duration_seconds = 30.0
        mock_run_metrics.deepest_floor = 2
        mock_run_metrics.floors_visited = 2
        mock_run_metrics.monsters_killed = 5
        mock_run_metrics.tiles_explored = 100
        mock_run_metrics.steps_taken = 150
        mock_run_metrics.to_dict.return_value = {}
        
        mock_recorder.get_metrics.return_value = mock_run_metrics
        mock_get_recorder.return_value = mock_recorder
        
        mock_telemetry = Mock()
        mock_telemetry.get_stats.return_value = {'floors': 2, 'avg_etp_per_floor': 20.0}
        mock_get_telemetry.return_value = mock_telemetry
        
        mock_console_new.return_value = Mock()
        
        # Run soak
        constants = {'input_config': {}}
        result = run_bot_soak(
            runs=3,
            telemetry_enabled=False,
            telemetry_output_path=None,
            constants=constants,
        )
        
        # Verify crash was recorded
        assert result.total_runs == 3
        assert result.completed_runs == 2  # Runs 1 and 3 succeeded
        assert result.bot_crashes == 1  # Run 2 crashed
        assert len(result.runs) == 3
        
        # Check crashed run
        crashed_run = result.runs[1]  # Run 2 (index 1)
        assert crashed_run.run_number == 2
        assert crashed_run.outcome == "crash"
        assert crashed_run.exception == "Test crash in run 2"

