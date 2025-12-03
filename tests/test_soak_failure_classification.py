"""Tests for rich failure classification in soak runs.

This test suite validates that the classify_failure() method correctly
maps run outcomes to structured failure types for analysis.

Test cases:
- death → failure_type="death"
- max_turns → failure_type="max_turns"
- bot_abort → failure_type="bot_abort" or sub-type
- crash/exception → failure_type="exception"
- bot_completed → failure_type="none" (success) or "stuck_autoexplore"
"""

import pytest
from engine.soak_harness import SoakRunResult


class TestClassifyFailureDeath:
    """Tests for death outcome classification."""
    
    def test_death_returns_death_failure_type(self):
        """Death outcome should classify as death failure type."""
        refined_outcome, failure_type, failure_detail = SoakRunResult.classify_failure(
            outcome="death"
        )
        
        assert refined_outcome == "death"
        assert failure_type == "death"
    
    def test_death_failure_detail_is_empty_by_default(self):
        """Death failure detail is empty (caller should set monster name)."""
        _, _, failure_detail = SoakRunResult.classify_failure(outcome="death")
        assert failure_detail == ""


class TestClassifyFailureMaxTurns:
    """Tests for max_turns outcome classification."""
    
    def test_max_turns_returns_max_turns_failure_type(self):
        """Max turns outcome should classify as max_turns failure type."""
        refined_outcome, failure_type, failure_detail = SoakRunResult.classify_failure(
            outcome="max_turns"
        )
        
        assert refined_outcome == "max_turns"
        assert failure_type == "max_turns"
    
    def test_max_turns_includes_limit_in_detail(self):
        """Max turns failure detail should include the limit if provided."""
        _, _, failure_detail = SoakRunResult.classify_failure(
            outcome="max_turns",
            max_turns_limit=2000,
        )
        
        assert "2000" in failure_detail
    
    def test_max_turns_without_limit_has_generic_detail(self):
        """Max turns failure detail should have generic message if no limit."""
        _, _, failure_detail = SoakRunResult.classify_failure(
            outcome="max_turns",
            max_turns_limit=None,
        )
        
        assert "maximum turn limit" in failure_detail.lower()


class TestClassifyFailureBotAbort:
    """Tests for bot_abort outcome classification."""
    
    def test_bot_abort_returns_bot_abort_failure_type(self):
        """Generic bot_abort should classify as bot_abort failure type."""
        refined_outcome, failure_type, _ = SoakRunResult.classify_failure(
            outcome="bot_abort"
        )
        
        assert refined_outcome == "bot_abort"
        assert failure_type == "bot_abort"
    
    def test_bot_abort_with_stuck_reason_returns_stuck_autoexplore(self):
        """Bot abort with 'stuck' reason should classify as stuck_autoexplore."""
        refined_outcome, failure_type, failure_detail = SoakRunResult.classify_failure(
            outcome="bot_abort",
            bot_abort_reason="Movement stuck at (10, 15)",
        )
        
        assert refined_outcome == "stuck"
        assert failure_type == "stuck_autoexplore"
        assert "stuck" in failure_detail.lower()
    
    def test_bot_abort_with_stairs_reason_returns_no_stairs(self):
        """Bot abort with 'stairs' reason should classify as no_stairs."""
        refined_outcome, failure_type, failure_detail = SoakRunResult.classify_failure(
            outcome="bot_abort",
            bot_abort_reason="Stairs unreachable",
        )
        
        assert refined_outcome == "no_stairs"
        assert failure_type == "no_stairs"
        assert "stairs" in failure_detail.lower()


class TestClassifyFailureException:
    """Tests for crash/exception outcome classification."""
    
    def test_crash_returns_exception_failure_type(self):
        """Crash outcome should classify as exception failure type."""
        refined_outcome, failure_type, _ = SoakRunResult.classify_failure(
            outcome="crash",
            exception="KeyError: 'missing_key'",
        )
        
        assert refined_outcome == "exception"
        assert failure_type == "exception"
    
    def test_error_returns_exception_failure_type(self):
        """Error outcome should classify as exception failure type."""
        refined_outcome, failure_type, _ = SoakRunResult.classify_failure(
            outcome="error",
        )
        
        assert refined_outcome == "exception"
        assert failure_type == "exception"
    
    def test_exception_message_in_failure_detail(self):
        """Exception message should be in failure detail."""
        _, _, failure_detail = SoakRunResult.classify_failure(
            outcome="crash",
            exception="ValueError: invalid value",
        )
        
        assert "ValueError" in failure_detail


class TestClassifyFailureBotCompleted:
    """Tests for bot_completed outcome classification."""
    
    def test_bot_completed_with_all_areas_explored_is_floor_complete(self):
        """Bot completed with all_areas_explored is success (floor_complete)."""
        refined_outcome, failure_type, _ = SoakRunResult.classify_failure(
            outcome="bot_completed",
            auto_explore_reason="all_areas_explored",
        )
        
        assert refined_outcome == "floor_complete"
        assert failure_type == "none"
    
    def test_bot_completed_with_cannot_reach_is_floor_complete(self):
        """Bot completed with cannot_reach_unexplored is success (floor_complete)."""
        refined_outcome, failure_type, _ = SoakRunResult.classify_failure(
            outcome="bot_completed",
            auto_explore_reason="cannot_reach_unexplored",
        )
        
        assert refined_outcome == "floor_complete"
        assert failure_type == "none"
    
    def test_bot_completed_with_movement_blocked_is_stuck(self):
        """Bot completed with movement_blocked is stuck_autoexplore failure."""
        refined_outcome, failure_type, _ = SoakRunResult.classify_failure(
            outcome="bot_completed",
            auto_explore_reason="movement_blocked",
        )
        
        assert refined_outcome == "stuck"
        assert failure_type == "stuck_autoexplore"
    
    def test_bot_completed_generic_is_floor_complete(self):
        """Bot completed without specific reason defaults to floor_complete."""
        refined_outcome, failure_type, _ = SoakRunResult.classify_failure(
            outcome="bot_completed",
            auto_explore_reason="",
        )
        
        assert refined_outcome == "floor_complete"
        assert failure_type == "none"


class TestClassifyFailureBotAbortReason:
    """Tests for bot_abort_reason classification (combat stuck, no_stairs, etc.)."""
    
    def test_stuck_combat_enemy_at_position(self):
        """Combat stuck with enemy position should classify as stuck_combat."""
        refined_outcome, failure_type, failure_detail = SoakRunResult.classify_failure(
            outcome="bot_completed",
            bot_abort_reason="stuck_combat:enemy_at_(5, 10)",
        )
        
        assert refined_outcome == "stuck"
        assert failure_type == "stuck_combat"
        assert "enemy_at" in failure_detail
    
    def test_stuck_enemy_too_far(self):
        """Enemy too far to engage should classify as stuck_combat."""
        refined_outcome, failure_type, failure_detail = SoakRunResult.classify_failure(
            outcome="bot_completed",
            bot_abort_reason="stuck_enemy_too_far:dist_8",
        )
        
        assert refined_outcome == "stuck"
        assert failure_type == "stuck_combat"
        assert "dist_8" in failure_detail
    
    def test_stuck_movement_blocked(self):
        """Movement blocked from BotBrain should classify as stuck_autoexplore."""
        refined_outcome, failure_type, _ = SoakRunResult.classify_failure(
            outcome="bot_completed",
            bot_abort_reason="stuck_movement_blocked",
        )
        
        assert refined_outcome == "stuck"
        assert failure_type == "stuck_autoexplore"
    
    def test_stuck_stairs_blocked(self):
        """Stuck trying to reach stairs should classify as stuck_autoexplore."""
        refined_outcome, failure_type, failure_detail = SoakRunResult.classify_failure(
            outcome="bot_completed",
            bot_abort_reason="stuck_stairs_blocked:at_(10, 15)",
        )
        
        assert refined_outcome == "stuck"
        assert failure_type == "stuck_autoexplore"
        assert "at_" in failure_detail
    
    def test_no_stairs_found(self):
        """No stairs found should classify as no_stairs."""
        refined_outcome, failure_type, _ = SoakRunResult.classify_failure(
            outcome="bot_completed",
            bot_abort_reason="no_stairs",
        )
        
        assert refined_outcome == "no_stairs"
        assert failure_type == "no_stairs"
    
    def test_no_stairs_unreachable(self):
        """Stairs unreachable should classify as no_stairs."""
        refined_outcome, failure_type, failure_detail = SoakRunResult.classify_failure(
            outcome="bot_completed",
            bot_abort_reason="no_stairs:unreachable_at_(20, 25)",
        )
        
        assert refined_outcome == "no_stairs"
        assert failure_type == "no_stairs"
        assert "unreachable" in failure_detail
    
    def test_exception_during_floor_complete(self):
        """Exception during bot operation should classify as exception."""
        refined_outcome, failure_type, _ = SoakRunResult.classify_failure(
            outcome="bot_completed",
            bot_abort_reason="exception_floor_complete",
        )
        
        assert refined_outcome == "exception"
        assert failure_type == "exception"
    
    def test_exception_with_message(self):
        """Exception with message should classify as exception."""
        refined_outcome, failure_type, failure_detail = SoakRunResult.classify_failure(
            outcome="bot_completed",
            bot_abort_reason="exception:KeyError('missing_key')",
        )
        
        assert refined_outcome == "exception"
        assert failure_type == "exception"
        assert "KeyError" in failure_detail
    
    def test_bot_abort_reason_takes_priority_over_auto_explore_reason(self):
        """bot_abort_reason should take priority over auto_explore_reason."""
        # Even if auto_explore says all_areas_explored, if bot_abort_reason
        # says stuck_combat, we should classify as stuck_combat
        refined_outcome, failure_type, _ = SoakRunResult.classify_failure(
            outcome="bot_completed",
            bot_abort_reason="stuck_combat:enemy_at_(3, 5)",
            auto_explore_reason="all_areas_explored",
        )
        
        assert refined_outcome == "stuck"
        assert failure_type == "stuck_combat"
    
    def test_floor_complete_when_no_abort_reason(self):
        """Without abort_reason, all_areas_explored should be floor_complete."""
        refined_outcome, failure_type, _ = SoakRunResult.classify_failure(
            outcome="bot_completed",
            bot_abort_reason=None,
            auto_explore_reason="all_areas_explored",
        )
        
        assert refined_outcome == "floor_complete"
        assert failure_type == "none"


class TestClassifyFailureSuccess:
    """Tests for success outcome classification."""
    
    def test_victory_returns_none_failure_type(self):
        """Victory should have none failure type (success)."""
        refined_outcome, failure_type, _ = SoakRunResult.classify_failure(
            outcome="victory"
        )
        
        assert refined_outcome == "victory"
        assert failure_type == "none"
    
    def test_max_floors_returns_run_complete(self):
        """Max floors reached should be run_complete with none failure type."""
        refined_outcome, failure_type, _ = SoakRunResult.classify_failure(
            outcome="max_floors"
        )
        
        assert refined_outcome == "run_complete"
        assert failure_type == "none"


class TestFromRunMetricsIntegration:
    """Integration tests for from_run_metrics_and_telemetry with classification."""
    
    def test_from_run_metrics_uses_refined_outcome(self):
        """from_run_metrics_and_telemetry should use refined outcome."""
        class MockRunMetrics:
            run_id = "test-123"
            seed = None
            outcome = "bot_completed"  # Raw outcome
            duration_seconds = 30.0
            deepest_floor = 2
            floors_visited = 2
            monsters_killed = 5
            items_picked_up = 3
            portals_used = 0
            tiles_explored = 200
            steps_taken = 150
            potions_used = 1
            max_turns_limit = None
        
        result = SoakRunResult.from_run_metrics_and_telemetry(
            run_number=1,
            run_metrics=MockRunMetrics(),
            telemetry_stats={'floors': 2, 'avg_etp_per_floor': 1.5},
            auto_explore_terminal_reason="all_areas_explored",
        )
        
        # Should be refined to "floor_complete", not raw "bot_completed"
        assert result.outcome == "floor_complete"
        assert result.failure_type == "none"
    
    def test_from_run_metrics_death_classified_correctly(self):
        """Death should be classified correctly through from_run_metrics."""
        class MockRunMetrics:
            run_id = "test-death"
            seed = None
            outcome = "death"
            duration_seconds = 15.0
            deepest_floor = 1
            floors_visited = 1
            monsters_killed = 2
            items_picked_up = 1
            portals_used = 0
            tiles_explored = 100
            steps_taken = 50
            potions_used = 0
            max_turns_limit = None
        
        result = SoakRunResult.from_run_metrics_and_telemetry(
            run_number=1,
            run_metrics=MockRunMetrics(),
            telemetry_stats={'floors': 1},
        )
        
        assert result.outcome == "death"
        assert result.failure_type == "death"
    
    def test_missing_run_metrics_classified_as_exception(self):
        """Missing run_metrics should be classified as exception."""
        result = SoakRunResult.from_run_metrics_and_telemetry(
            run_number=1,
            run_metrics=None,
            telemetry_stats={'floors': 0},
            exception="Run metrics not found",
        )
        
        assert result.outcome == "exception"
        assert result.failure_type == "exception"
        assert "Run metrics not found" in result.failure_detail

