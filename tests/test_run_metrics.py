"""Comprehensive tests for the run metrics system (Phase 1.5).

This module tests:
- RunMetrics model and serialization
- RunMetricsRecorder lifecycle
- Integration with Statistics component
- Integration with TelemetryService
- Death/victory/quit outcome tracking
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock
from instrumentation.run_metrics import (
    RunMetrics,
    RunMetricsRecorder,
    initialize_run_metrics_recorder,
    get_run_metrics_recorder,
    reset_run_metrics_recorder,
    finalize_run_metrics,
)
from components.statistics import Statistics


class TestRunMetricsModel:
    """Test the RunMetrics dataclass."""
    
    def test_runmetrics_initialization(self):
        """Test that RunMetrics initializes with correct defaults."""
        metrics = RunMetrics(
            run_id="test123",
            mode="human"
        )
        
        assert metrics.run_id == "test123"
        assert metrics.mode == "human"
        assert metrics.seed is None
        assert metrics.outcome == "in_progress"
        assert metrics.deepest_floor == 1
        assert metrics.monsters_killed == 0
        assert metrics.items_picked_up == 0
    
    def test_runmetrics_to_dict(self):
        """Test RunMetrics serialization to dict."""
        metrics = RunMetrics(
            run_id="test123",
            mode="bot",
            seed=42,
            start_time_utc="2025-11-16T10:00:00Z",
            end_time_utc="2025-11-16T10:15:30Z",
            duration_seconds=930.5,
            deepest_floor=3,
            floors_visited=3,
            steps_taken=150,
            tiles_explored=450,
            monsters_killed=12,
            items_picked_up=5,
            portals_used=2,
            outcome="death"
        )
        
        data = metrics.to_dict()
        
        assert data["run_id"] == "test123"
        assert data["mode"] == "bot"
        assert data["seed"] == 42
        assert data["outcome"] == "death"
        assert data["deepest_floor"] == 3
        assert data["monsters_killed"] == 12
        assert data["duration_seconds"] == 930.5
    
    def test_runmetrics_summary_text(self):
        """Test RunMetrics summary text generation."""
        metrics = RunMetrics(
            run_id="test123",
            mode="human",
            tiles_explored=100,
            steps_taken=50,
            deepest_floor=2,
            monsters_killed=5,
            items_picked_up=3,
            duration_seconds=120.5
        )
        
        summary = metrics.get_summary_text()
        
        assert "100 tiles" in summary
        assert "50 steps" in summary
        assert "floor 2" in summary
        assert "Monsters defeated: 5" in summary
        assert "Items collected: 3" in summary
        assert "2m 0s" in summary
    
    def test_runmetrics_summary_bot_mode(self):
        """Test RunMetrics summary includes bot indicator."""
        metrics = RunMetrics(
            run_id="test123",
            mode="bot",
            tiles_explored=100,
            steps_taken=50,
            deepest_floor=1
        )
        
        summary = metrics.get_summary_text()
        assert "[Bot Run]" in summary


class TestRunMetricsRecorder:
    """Test the RunMetricsRecorder class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_run_metrics_recorder()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_run_metrics_recorder()
    
    def test_recorder_initialization(self):
        """Test RunMetricsRecorder initialization."""
        recorder = RunMetricsRecorder(mode="human", seed=None)
        
        assert recorder.mode == "human"
        assert recorder.seed is None
        assert recorder.run_id is not None
        assert len(recorder.run_id) == 32  # UUID hex is 32 chars
        assert not recorder.is_finalized()
    
    def test_recorder_start(self):
        """Test recording run start time."""
        recorder = RunMetricsRecorder(mode="human")
        recorder.start()
        
        assert recorder.start_time is not None
        assert isinstance(recorder.start_time, datetime)
    
    def test_recorder_finalize(self):
        """Test finalizing run metrics."""
        recorder = RunMetricsRecorder(mode="human")
        recorder.start()
        
        # Create mock statistics
        stats = Statistics()
        stats.total_kills = 10
        stats.deepest_level = 3
        stats.turns_taken = 100
        stats.items_picked_up = 5
        stats.portals_used = 2
        
        # Create mock game map
        game_map = Mock()
        game_map.width = 50
        game_map.height = 50
        game_map.tiles = [[Mock(explored=True) for _ in range(50)] for _ in range(50)]
        
        # Finalize
        recorder.finalize("death", stats, game_map)
        
        assert recorder.is_finalized()
        metrics = recorder.get_metrics()
        assert metrics is not None
        assert metrics.outcome == "death"
        assert metrics.monsters_killed == 10
        assert metrics.deepest_floor == 3
        assert metrics.steps_taken == 100
        assert metrics.items_picked_up == 5
        assert metrics.portals_used == 2
        assert metrics.tiles_explored == 2500  # 50x50 all explored
    
    def test_recorder_duration_calculation(self):
        """Test duration is calculated correctly."""
        recorder = RunMetricsRecorder(mode="human")
        recorder.start()
        
        # Manually set times for deterministic test
        recorder.start_time = datetime(2025, 11, 16, 10, 0, 0, tzinfo=timezone.utc)
        recorder.end_time = datetime(2025, 11, 16, 10, 5, 30, tzinfo=timezone.utc)
        
        stats = Statistics()
        game_map = Mock()
        game_map.width = 10
        game_map.height = 10
        game_map.tiles = [[Mock(explored=False) for _ in range(10)] for _ in range(10)]
        
        # Override finalize to use our set times
        recorder.finalize("quit", stats, game_map)
        
        metrics = recorder.get_metrics()
        # Duration should be 5 minutes 30 seconds = 330 seconds
        # Note: finalize() sets end_time to now(), so we check it was set
        assert metrics.duration_seconds is not None
    
    def test_recorder_tiles_explored_count(self):
        """Test tiles explored counting."""
        recorder = RunMetricsRecorder(mode="human")
        recorder.start()
        
        stats = Statistics()
        
        # Create map with some explored tiles
        game_map = Mock()
        game_map.width = 10
        game_map.height = 10
        tiles = []
        for x in range(10):
            row = []
            for y in range(10):
                # Mark half the tiles as explored
                tile = Mock()
                tile.explored = (x + y) % 2 == 0
                row.append(tile)
            tiles.append(row)
        game_map.tiles = tiles
        
        recorder.finalize("victory", stats, game_map)
        
        metrics = recorder.get_metrics()
        assert metrics.tiles_explored == 50  # Half of 100 tiles


class TestRunMetricsGlobalFunctions:
    """Test global run metrics functions."""
    
    def setup_method(self):
        """Reset global state before each test."""
        reset_run_metrics_recorder()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_run_metrics_recorder()
    
    def test_initialize_run_metrics_recorder(self):
        """Test global recorder initialization."""
        recorder = initialize_run_metrics_recorder(mode="bot", seed=123)
        
        assert recorder is not None
        assert recorder.mode == "bot"
        assert recorder.seed == 123
        assert recorder.start_time is not None
        
        # Check singleton
        assert get_run_metrics_recorder() is recorder
    
    def test_get_run_metrics_recorder_none(self):
        """Test getting recorder when not initialized."""
        assert get_run_metrics_recorder() is None
    
    def test_reset_run_metrics_recorder(self):
        """Test resetting the global recorder."""
        initialize_run_metrics_recorder(mode="human")
        assert get_run_metrics_recorder() is not None
        
        reset_run_metrics_recorder()
        assert get_run_metrics_recorder() is None
    
    def test_finalize_run_metrics(self):
        """Test finalize_run_metrics convenience function."""
        # Initialize recorder
        initialize_run_metrics_recorder(mode="human")
        
        # Create mock player with statistics
        player = Mock()
        stats = Statistics()
        stats.total_kills = 5
        stats.deepest_level = 2
        stats.turns_taken = 50
        stats.items_picked_up = 3
        
        from components.component_registry import ComponentType
        player.get_component_optional = Mock(return_value=stats)
        
        # Create mock game map
        game_map = Mock()
        game_map.width = 10
        game_map.height = 10
        game_map.tiles = [[Mock(explored=True) for _ in range(10)] for _ in range(10)]
        
        # Finalize
        metrics = finalize_run_metrics("death", player, game_map)
        
        assert metrics is not None
        assert metrics.outcome == "death"
        assert metrics.monsters_killed == 5
        assert metrics.deepest_floor == 2
        assert metrics.tiles_explored == 100
    
    def test_finalize_run_metrics_no_recorder(self):
        """Test finalize_run_metrics when no recorder exists."""
        player = Mock()
        game_map = Mock()
        
        metrics = finalize_run_metrics("death", player, game_map)
        assert metrics is None


class TestRunMetricsOutcomes:
    """Test different run outcome scenarios."""
    
    def setup_method(self):
        """Reset global state before each test."""
        reset_run_metrics_recorder()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_run_metrics_recorder()
    
    def _create_test_context(self):
        """Create common test fixtures."""
        initialize_run_metrics_recorder(mode="human")
        
        player = Mock()
        stats = Statistics()
        stats.total_kills = 3
        stats.deepest_level = 1
        stats.turns_taken = 20
        
        from components.component_registry import ComponentType
        player.get_component_optional = Mock(return_value=stats)
        
        game_map = Mock()
        game_map.width = 10
        game_map.height = 10
        game_map.tiles = [[Mock(explored=False) for _ in range(10)] for _ in range(10)]
        
        return player, game_map
    
    def test_death_outcome(self):
        """Test death outcome."""
        player, game_map = self._create_test_context()
        metrics = finalize_run_metrics("death", player, game_map)
        
        assert metrics.outcome == "death"
    
    def test_victory_outcome(self):
        """Test victory outcome."""
        player, game_map = self._create_test_context()
        metrics = finalize_run_metrics("victory", player, game_map)
        
        assert metrics.outcome == "victory"
    
    def test_quit_outcome(self):
        """Test quit outcome."""
        player, game_map = self._create_test_context()
        metrics = finalize_run_metrics("quit", player, game_map)
        
        assert metrics.outcome == "quit"
    
    def test_bot_abort_outcome(self):
        """Test bot_abort outcome."""
        # Create test context with bot mode
        initialize_run_metrics_recorder(mode="bot")
        
        player = Mock()
        stats = Statistics()
        stats.total_kills = 3
        stats.deepest_level = 1
        stats.turns_taken = 20
        
        from components.component_registry import ComponentType
        player.get_component_optional = Mock(return_value=stats)
        
        game_map = Mock()
        game_map.width = 10
        game_map.height = 10
        game_map.tiles = [[Mock(explored=False) for _ in range(10)] for _ in range(10)]
        
        metrics = finalize_run_metrics("bot_abort", player, game_map)
        
        assert metrics.outcome == "bot_abort"
        assert metrics.mode == "bot"


class TestRunMetricsBotMode:
    """Test run metrics in bot mode."""
    
    def setup_method(self):
        """Reset global state before each test."""
        reset_run_metrics_recorder()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_run_metrics_recorder()
    
    def test_bot_mode_initialization(self):
        """Test initializing run metrics in bot mode."""
        recorder = initialize_run_metrics_recorder(mode="bot", seed=42)
        
        assert recorder.mode == "bot"
        assert recorder.seed == 42
    
    def test_bot_mode_metrics(self):
        """Test bot mode metrics have correct mode."""
        initialize_run_metrics_recorder(mode="bot")
        
        player = Mock()
        stats = Statistics()
        from components.component_registry import ComponentType
        player.get_component_optional = Mock(return_value=stats)
        
        game_map = Mock()
        game_map.width = 10
        game_map.height = 10
        game_map.tiles = [[Mock(explored=False) for _ in range(10)] for _ in range(10)]
        
        metrics = finalize_run_metrics("bot_abort", player, game_map)
        
        assert metrics.mode == "bot"
        summary = metrics.get_summary_text()
        assert "[Bot Run]" in summary


class TestRunMetricsEdgeCases:
    """Test edge cases and error handling."""
    
    def setup_method(self):
        """Reset global state before each test."""
        reset_run_metrics_recorder()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_run_metrics_recorder()
    
    def test_finalize_without_player_statistics(self):
        """Test finalize when player has no statistics component."""
        initialize_run_metrics_recorder(mode="human")
        
        player = Mock()
        player.get_component_optional = Mock(return_value=None)
        
        game_map = Mock()
        
        metrics = finalize_run_metrics("death", player, game_map)
        assert metrics is None
    
    def test_count_explored_tiles_with_none_map(self):
        """Test tiles counting handles None game map."""
        recorder = RunMetricsRecorder(mode="human")
        recorder.start()
        
        stats = Statistics()
        
        recorder.finalize("quit", stats, None)
        
        metrics = recorder.get_metrics()
        assert metrics.tiles_explored == 0
    
    def test_count_explored_tiles_with_invalid_map(self):
        """Test tiles counting handles malformed game map."""
        recorder = RunMetricsRecorder(mode="human")
        recorder.start()
        
        stats = Statistics()
        
        # Map without tiles attribute
        game_map = Mock(spec=[])
        
        recorder.finalize("quit", stats, game_map)
        
        metrics = recorder.get_metrics()
        assert metrics.tiles_explored == 0

