"""Tests for soak metrics tracking in Statistics component.

These tests verify that the metrics wiring works correctly:
- record_turn() increments steps_taken
- record_item_pickup() increments items_picked_up
- record_level_reached() updates deepest_floor
- record_potion_used() increments potions_used
"""

import pytest
from components.statistics import Statistics


class TestStatisticsMetricsTracking:
    """Tests for soak-relevant metrics tracking in Statistics."""

    def test_record_turn_increments_turns_taken(self):
        """record_turn() should increment turns_taken (used for steps_taken)."""
        stats = Statistics()
        
        assert stats.turns_taken == 0
        
        stats.record_turn()
        assert stats.turns_taken == 1
        
        stats.record_turn()
        stats.record_turn()
        assert stats.turns_taken == 3

    def test_record_item_pickup_increments_items_picked_up(self):
        """record_item_pickup() should increment items_picked_up."""
        stats = Statistics()
        
        assert stats.items_picked_up == 0
        
        stats.record_item_pickup()
        assert stats.items_picked_up == 1
        
        stats.record_item_pickup()
        stats.record_item_pickup()
        assert stats.items_picked_up == 3

    def test_record_level_reached_updates_deepest_level(self):
        """record_level_reached() should update deepest_level only if higher."""
        stats = Statistics()
        
        assert stats.deepest_level == 1
        
        # Going to floor 2 should update
        stats.record_level_reached(2)
        assert stats.deepest_level == 2
        
        # Going to floor 5 should update
        stats.record_level_reached(5)
        assert stats.deepest_level == 5
        
        # Going back to floor 3 should NOT update (already reached 5)
        stats.record_level_reached(3)
        assert stats.deepest_level == 5
        
        # Going to floor 1 should NOT update
        stats.record_level_reached(1)
        assert stats.deepest_level == 5

    def test_record_potion_used_increments_potions_used(self):
        """record_potion_used() should increment potions_used."""
        stats = Statistics()
        
        assert stats.potions_used == 0
        
        stats.record_potion_used()
        assert stats.potions_used == 1
        
        stats.record_potion_used()
        stats.record_potion_used()
        assert stats.potions_used == 3

    def test_statistics_serialization_includes_new_fields(self):
        """to_dict() should include all soak-relevant fields."""
        stats = Statistics()
        stats.record_turn()
        stats.record_turn()
        stats.record_item_pickup()
        stats.record_level_reached(3)
        stats.record_potion_used()
        
        data = stats.to_dict()
        
        assert data['turns_taken'] == 2
        assert data['items_picked_up'] == 1
        assert data['deepest_level'] == 3
        assert data['potions_used'] == 1

    def test_statistics_deserialization_includes_new_fields(self):
        """from_dict() should restore all soak-relevant fields."""
        data = {
            'turns_taken': 100,
            'items_picked_up': 10,
            'deepest_level': 4,
            'potions_used': 5,
        }
        
        stats = Statistics.from_dict(data)
        
        assert stats.turns_taken == 100
        assert stats.items_picked_up == 10
        assert stats.deepest_level == 4
        assert stats.potions_used == 5


class TestRunMetricsPotionsUsed:
    """Tests for potions_used in RunMetrics."""
    
    def test_run_metrics_has_potions_used_field(self):
        """RunMetrics should have potions_used field."""
        from instrumentation.run_metrics import RunMetrics
        
        metrics = RunMetrics(run_id="test", mode="bot")
        assert hasattr(metrics, 'potions_used')
        assert metrics.potions_used == 0
        
    def test_run_metrics_potions_used_in_to_dict(self):
        """RunMetrics.to_dict() should include potions_used."""
        from instrumentation.run_metrics import RunMetrics
        
        metrics = RunMetrics(run_id="test", mode="bot", potions_used=5)
        data = metrics.to_dict()
        
        assert 'potions_used' in data
        assert data['potions_used'] == 5


class TestSoakRunResultPotionsUsedSource:
    """Tests that SoakRunResult pulls potions_used from run_metrics."""
    
    def test_soak_run_result_potions_from_run_metrics(self):
        """SoakRunResult should pull potions_used from run_metrics, not telemetry."""
        from engine.soak_harness import SoakRunResult
        
        # Create mock run_metrics with potions_used
        class MockRunMetrics:
            run_id = "test-123"
            seed = None
            outcome = "death"
            duration_seconds = 30.0
            deepest_floor = 2
            floors_visited = 2
            monsters_killed = 5
            items_picked_up = 3
            portals_used = 0
            tiles_explored = 200
            steps_taken = 150
            potions_used = 7  # This should be the source
        
        # Telemetry stats (should be ignored for potions_used now)
        telemetry_stats = {
            'floors': 2,
            'avg_etp_per_floor': 1.5,
            'potions_used': 999,  # This should be ignored
        }
        
        result = SoakRunResult.from_run_metrics_and_telemetry(
            run_number=1,
            run_metrics=MockRunMetrics(),
            telemetry_stats=telemetry_stats,
        )
        
        # Should use run_metrics.potions_used (7), not telemetry (999)
        assert result.potions_used == 7

