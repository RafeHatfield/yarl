"""Tests for the GameEngine class."""

import pytest
import time
from unittest.mock import Mock, patch

from engine.game_engine import GameEngine
from engine.system import System


class MockSystem(System):
    """Mock system for testing."""

    def __init__(self, name="mock_system", priority=100):
        super().__init__(name, priority)
        self.update_count = 0
        self.last_dt = 0.0
        self.initialize_called = False
        self.cleanup_called = False

    def initialize(self, engine):
        super().initialize(engine)
        self.initialize_called = True

    def update(self, dt):
        self.update_count += 1
        self.last_dt = dt

    def cleanup(self):
        self.cleanup_called = True


class TestGameEngineInitialization:
    """Test GameEngine initialization."""

    def test_default_initialization(self):
        """Test GameEngine initialization with default values."""
        engine = GameEngine()

        assert engine.target_fps == 60
        assert engine.running is False
        assert engine.delta_time == 0.0
        assert engine.system_count == 0
        assert len(engine.systems) == 0

    def test_custom_fps_initialization(self):
        """Test GameEngine initialization with custom FPS."""
        engine = GameEngine(target_fps=30)

        assert engine.target_fps == 30
        assert engine._frame_time == 1.0 / 30

    def test_zero_fps_initialization(self):
        """Test GameEngine initialization with zero FPS (unlimited)."""
        engine = GameEngine(target_fps=0)

        assert engine.target_fps == 0
        assert engine._frame_time == 0.0


class TestSystemManagement:
    """Test system registration and management."""

    def test_register_system(self):
        """Test registering a system."""
        engine = GameEngine()
        system = MockSystem("test_system", 50)

        engine.register_system(system)

        assert engine.system_count == 1
        assert engine.get_system("test_system") is system
        assert system.initialize_called is True
        assert system.engine is engine

    def test_register_duplicate_system_raises_error(self):
        """Test that registering a system with duplicate name raises error."""
        engine = GameEngine()
        system1 = MockSystem("duplicate")
        system2 = MockSystem("duplicate")

        engine.register_system(system1)

        with pytest.raises(
            ValueError, match="System 'duplicate' is already registered"
        ):
            engine.register_system(system2)

    def test_unregister_system(self):
        """Test unregistering a system."""
        engine = GameEngine()
        system = MockSystem("test_system")

        engine.register_system(system)
        removed_system = engine.unregister_system("test_system")

        assert removed_system is system
        assert system.cleanup_called is True
        assert engine.system_count == 0
        assert engine.get_system("test_system") is None

    def test_unregister_nonexistent_system(self):
        """Test unregistering a system that doesn't exist."""
        engine = GameEngine()

        result = engine.unregister_system("nonexistent")

        assert result is None

    def test_get_system(self):
        """Test retrieving a system by name."""
        engine = GameEngine()
        system = MockSystem("test_system")

        engine.register_system(system)

        assert engine.get_system("test_system") is system
        assert engine.get_system("nonexistent") is None

    def test_get_systems_by_type(self):
        """Test retrieving systems by type."""
        engine = GameEngine()
        system1 = MockSystem("system1")
        system2 = MockSystem("system2")

        engine.register_system(system1)
        engine.register_system(system2)

        mock_systems = engine.get_systems_by_type(MockSystem)

        assert len(mock_systems) == 2
        assert system1 in mock_systems
        assert system2 in mock_systems

    def test_system_priority_ordering(self):
        """Test that systems are ordered by priority."""
        engine = GameEngine()
        system_high = MockSystem("high_priority", 10)
        system_low = MockSystem("low_priority", 100)
        system_medium = MockSystem("medium_priority", 50)

        # Register in random order
        engine.register_system(system_low)
        engine.register_system(system_high)
        engine.register_system(system_medium)

        system_names = list(engine.systems.keys())
        assert system_names == ["high_priority", "medium_priority", "low_priority"]


class TestGameEngineLifecycle:
    """Test GameEngine lifecycle methods."""

    def test_start_engine(self):
        """Test starting the engine."""
        engine = GameEngine()

        with patch("time.time", return_value=1000.0):
            engine.start()

        assert engine.running is True
        assert engine._last_time == 1000.0

    def test_stop_engine(self):
        """Test stopping the engine."""
        engine = GameEngine()
        system = MockSystem("test_system")
        engine.register_system(system)

        engine.start()
        engine.stop()

        assert engine.running is False
        assert system.cleanup_called is True

    @patch("time.time")
    def test_update_calculates_delta_time(self, mock_time):
        """Test that update calculates delta time correctly."""
        engine = GameEngine()
        system = MockSystem("test_system")
        engine.register_system(system)

        # First update
        mock_time.return_value = 1000.0
        engine._last_time = 999.984  # Previous frame
        engine.update()

        assert abs(engine.delta_time - 0.016) < 0.001  # ~60 FPS
        assert system.update_count == 1
        assert abs(system.last_dt - 0.016) < 0.001

    def test_update_skips_disabled_systems(self):
        """Test that update skips disabled systems."""
        engine = GameEngine()
        system1 = MockSystem("enabled_system")
        system2 = MockSystem("disabled_system")
        system2.disable()

        engine.register_system(system1)
        engine.register_system(system2)

        engine.update()

        assert system1.update_count == 1
        assert system2.update_count == 0

    @patch("time.sleep")
    @patch("time.time")
    def test_run_maintains_target_fps(self, mock_time, mock_sleep):
        """Test that run method maintains target FPS."""
        engine = GameEngine(target_fps=60)

        # Mock time progression - need more values for all time.time() calls
        time_values = [
            1000.0,
            1000.0,
            1000.010,
            1000.010,
        ]  # start, frame_start, update, frame_duration
        mock_time.side_effect = time_values

        # Stop after one iteration
        def stop_after_update(*args):
            engine.stop()

        system = MockSystem("test_system")
        system.update = stop_after_update
        engine.register_system(system)

        engine.run()

        # Should sleep to maintain 60 FPS (16.67ms per frame)
        mock_sleep.assert_called_once()
        sleep_time = mock_sleep.call_args[0][0]
        assert abs(sleep_time - 0.00667) < 0.001


class TestGameEngineProperties:
    """Test GameEngine properties and info methods."""

    def test_system_count(self):
        """Test system_count property."""
        engine = GameEngine()

        assert engine.system_count == 0

        engine.register_system(MockSystem("system1"))
        assert engine.system_count == 1

        engine.register_system(MockSystem("system2"))
        assert engine.system_count == 2

    def test_enabled_system_count(self):
        """Test enabled_system_count property."""
        engine = GameEngine()
        system1 = MockSystem("system1")
        system2 = MockSystem("system2")
        system2.disable()

        engine.register_system(system1)
        engine.register_system(system2)

        assert engine.enabled_system_count == 1

    def test_get_system_info(self):
        """Test get_system_info method."""
        engine = GameEngine()
        system1 = MockSystem("system1", 10)
        system2 = MockSystem("system2", 20)
        system2.disable()

        engine.register_system(system1)
        engine.register_system(system2)

        info = engine.get_system_info()

        assert len(info) == 2
        assert info["system1"]["enabled"] is True
        assert info["system1"]["priority"] == 10
        assert info["system1"]["type"] == "MockSystem"
        assert info["system2"]["enabled"] is False
        assert info["system2"]["priority"] == 20


class TestGameEngineIntegration:
    """Integration tests for GameEngine."""

    def test_complete_engine_lifecycle(self):
        """Test complete engine lifecycle with multiple systems."""
        engine = GameEngine(target_fps=30)

        # Create systems with different priorities
        render_system = MockSystem("render", 100)
        input_system = MockSystem("input", 10)
        logic_system = MockSystem("logic", 50)

        # Register systems
        engine.register_system(render_system)
        engine.register_system(input_system)
        engine.register_system(logic_system)

        # Verify priority ordering
        system_names = list(engine.systems.keys())
        assert system_names == ["input", "logic", "render"]

        # Start and update
        engine.start()
        assert engine.running is True

        engine.update()

        # Verify all systems were updated
        assert input_system.update_count == 1
        assert logic_system.update_count == 1
        assert render_system.update_count == 1

        # Stop and verify cleanup
        engine.stop()
        assert engine.running is False
        assert input_system.cleanup_called is True
        assert logic_system.cleanup_called is True
        assert render_system.cleanup_called is True
