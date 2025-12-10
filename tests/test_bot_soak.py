"""Tests for bot soak harness (Phase 1.6).

These tests verify that the soak harness can orchestrate multiple bot runs,
capture metrics correctly, and aggregate session statistics.

NOTE: This entire module is marked slow because bot soak tests involve
extensive mocking and multi-run orchestration.
"""

import pytest

# Mark entire module as slow
pytestmark = pytest.mark.slow
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
        mock_run_metrics.seed = None
        mock_run_metrics.outcome = "death"
        mock_run_metrics.duration_seconds = 42.5
        mock_run_metrics.deepest_floor = 3
        mock_run_metrics.floors_visited = 3
        mock_run_metrics.monsters_killed = 7
        mock_run_metrics.items_picked_up = 5
        mock_run_metrics.portals_used = 1
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
        # With failure classification, "error" is refined to "exception"
        assert result.outcome == "exception"
        assert result.failure_type == "exception"
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
    
    @patch('engine.soak_harness.libtcod.console_init_root')
    @patch('engine.soak_harness.libtcod.console_set_custom_font')
    @patch('tcod.libtcodpy.console_new')
    @patch('loader_functions.initialize_new_game.get_game_variables')
    @patch('engine_integration.play_game_with_engine')
    @patch('instrumentation.run_metrics.get_run_metrics_recorder')
    @patch('services.telemetry_service.get_telemetry_service')
    @patch('instrumentation.run_metrics.reset_run_metrics_recorder')
    @patch('services.telemetry_service.reset_telemetry_service')
    def test_run_bot_soak_initializes_libtcod_root_console(
        self,
        mock_reset_telemetry,
        mock_reset_run_metrics,
        mock_get_telemetry,
        mock_get_recorder,
        mock_play_game,
        mock_get_game_vars,
        mock_console_new,
        mock_set_font,
        mock_init_root,
    ):
        """Test that run_bot_soak initializes libtcod root console before running games.
        
        This is the critical fix for the bug where bot-soak mode crashed with:
        "Console must not be NULL or root console must exist."
        
        The fix ensures _initialize_libtcod_for_soak() is called ONCE before any
        game runs, creating the root console that ConsoleRenderer.render() needs.
        """
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
        mock_run_metrics.seed = None
        mock_run_metrics.outcome = "death"
        mock_run_metrics.duration_seconds = 30.0
        mock_run_metrics.deepest_floor = 2
        mock_run_metrics.floors_visited = 2
        mock_run_metrics.monsters_killed = 5
        mock_run_metrics.items_picked_up = 3
        mock_run_metrics.portals_used = 0
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
            'potions_used': 0,
        }
        mock_get_telemetry.return_value = mock_telemetry
        
        # Mock console creation
        mock_console_new.return_value = Mock()
        
        # Run soak with 2 runs
        constants = {
            'input_config': {},
            'window_title': 'Test Game',
        }
        result = run_bot_soak(
            runs=2,
            telemetry_enabled=False,
            telemetry_output_path=None,
            constants=constants,
        )
        
        # CRITICAL ASSERTIONS: Verify libtcod root console was initialized ONCE
        # before any game runs started
        mock_set_font.assert_called_once()
        mock_init_root.assert_called_once()
        
        # Verify initialization happened with correct parameters
        # (screen dimensions from ui_layout, window title from constants)
        init_call_args = mock_init_root.call_args
        assert init_call_args is not None
        # Args are (width, height, title, fullscreen)
        assert len(init_call_args[0]) >= 3
        assert init_call_args[0][2] == 'Test Game'  # window title
        
        # Verify runs completed successfully (no crashes due to missing root console)
        assert result.total_runs == 2
        assert result.completed_runs == 2
        assert result.bot_crashes == 0
        assert len(result.runs) == 2
    
    @patch('tcod.libtcodpy.console_init_root')
    @patch('tcod.libtcodpy.console_set_custom_font')
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
        mock_set_font,
        mock_init_root,
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
        mock_run_metrics.seed = None
        mock_run_metrics.outcome = "death"
        mock_run_metrics.duration_seconds = 30.0
        mock_run_metrics.deepest_floor = 2
        mock_run_metrics.floors_visited = 2
        mock_run_metrics.monsters_killed = 5
        mock_run_metrics.items_picked_up = 2
        mock_run_metrics.portals_used = 0
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
            'potions_used': 0,
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
    
    @patch('tcod.libtcodpy.console_init_root')
    @patch('tcod.libtcodpy.console_set_custom_font')
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
        mock_set_font,
        mock_init_root,
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
        mock_run_metrics.seed = None
        mock_run_metrics.outcome = "death"
        mock_run_metrics.duration_seconds = 30.0
        mock_run_metrics.deepest_floor = 2
        mock_run_metrics.floors_visited = 2
        mock_run_metrics.monsters_killed = 5
        mock_run_metrics.items_picked_up = 2
        mock_run_metrics.portals_used = 0
        mock_run_metrics.tiles_explored = 100
        mock_run_metrics.steps_taken = 150
        mock_run_metrics.to_dict.return_value = {}
        
        mock_recorder.get_metrics.return_value = mock_run_metrics
        mock_get_recorder.return_value = mock_recorder
        
        mock_telemetry = Mock()
        mock_telemetry.get_stats.return_value = {'floors': 2, 'avg_etp_per_floor': 20.0, 'potions_used': 0}
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
        assert crashed_run.outcome == "exception"  # classify_failure refines "crash" to "exception"
        assert crashed_run.exception == "Test crash in run 2"
    
    @patch('tcod.libtcodpy.console_init_root')
    @patch('tcod.libtcodpy.console_set_custom_font')
    @patch('tcod.libtcodpy.console_new')
    @patch('loader_functions.initialize_new_game.get_game_variables')
    @patch('engine_integration.play_game_with_engine')
    @patch('instrumentation.run_metrics.get_run_metrics_recorder')
    @patch('services.telemetry_service.get_telemetry_service')
    @patch('instrumentation.run_metrics.reset_run_metrics_recorder')
    @patch('services.telemetry_service.reset_telemetry_service')
    @patch('services.movement_service.reset_movement_service')
    @patch('services.pickup_service.reset_pickup_service')
    @patch('services.floor_state_manager.reset_floor_state_manager')
    def test_run_bot_soak_resets_singleton_services_between_runs(
        self,
        mock_reset_floor_state,
        mock_reset_pickup,
        mock_reset_movement,
        mock_reset_telemetry,
        mock_reset_run_metrics,
        mock_get_telemetry,
        mock_get_recorder,
        mock_play_game,
        mock_get_game_vars,
        mock_console_new,
        mock_set_font,
        mock_init_root,
    ):
        """Test that singleton services are reset between runs to prevent state leakage.
        
        This is the critical fix for the bug where run 2+ would fail because
        MovementService and other singletons held stale references to run 1's
        state_manager, causing movement validation against the wrong map.
        
        The fix ensures reset_*_service() is called for all singleton services
        before each run starts, so each run gets fresh service instances with
        the correct state_manager reference.
        """
        # Mock game setup
        mock_player = Mock()
        mock_player.get_component_optional.return_value = None
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
        mock_run_metrics.seed = None
        mock_run_metrics.outcome = "bot_completed"
        mock_run_metrics.duration_seconds = 30.0
        mock_run_metrics.deepest_floor = 1
        mock_run_metrics.floors_visited = 1
        mock_run_metrics.monsters_killed = 0
        mock_run_metrics.items_picked_up = 0
        mock_run_metrics.portals_used = 0
        mock_run_metrics.tiles_explored = 100
        mock_run_metrics.steps_taken = 150
        mock_run_metrics.to_dict.return_value = {}
        
        mock_recorder.get_metrics.return_value = mock_run_metrics
        mock_get_recorder.return_value = mock_recorder
        
        # Mock telemetry service
        mock_telemetry = Mock()
        mock_telemetry.enabled = False
        mock_telemetry.get_stats.return_value = {
            'floors': 1,
            'avg_etp_per_floor': 15.0,
            'potions_used': 0,
        }
        mock_get_telemetry.return_value = mock_telemetry
        
        # Mock console creation
        mock_console_new.return_value = Mock()
        
        # Run soak with 3 runs to verify reset happens between each
        constants = {'input_config': {}}
        result = run_bot_soak(
            runs=3,
            telemetry_enabled=False,
            telemetry_output_path=None,
            constants=constants,
        )
        
        # CRITICAL ASSERTIONS: Verify all singleton services were reset before EACH run
        # This prevents state leakage where run 2+ uses run 1's stale references
        
        # Each service should be reset 3 times (once before each of 3 runs)
        assert mock_reset_run_metrics.call_count == 3, \
            "RunMetricsRecorder should be reset before each run"
        assert mock_reset_telemetry.call_count == 3, \
            "TelemetryService should be reset before each run"
        assert mock_reset_movement.call_count == 3, \
            "MovementService should be reset before each run (fixes movement validation bug)"
        assert mock_reset_pickup.call_count == 3, \
            "PickupService should be reset before each run"
        assert mock_reset_floor_state.call_count == 3, \
            "FloorStateManager should be reset before each run"
        
        # Verify all runs completed successfully (no hangs/crashes from stale state)
        assert result.total_runs == 3
        assert result.completed_runs == 3
        assert result.bot_crashes == 0
        
        # Verify each run has valid results (not stuck in movement loops)
        for i, run in enumerate(result.runs, start=1):
            assert run.run_number == i
            # classify_failure refines "bot_completed" to "floor_complete" when floor is explored
            assert run.outcome == "floor_complete"  # Bot successfully completed exploration
            assert run.exception is None  # No crashes from stale state

