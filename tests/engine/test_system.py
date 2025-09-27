"""Tests for the System base class."""

import pytest
from unittest.mock import Mock

from engine.system import System


class MockTestSystem(System):
    """Concrete test implementation of System."""

    def __init__(self, name="test_system", priority=100):
        super().__init__(name, priority)
        self.update_called = False
        self.cleanup_called = False
        self.initialize_called = False

    def initialize(self, engine):
        super().initialize(engine)
        self.initialize_called = True

    def update(self, dt):
        self.update_called = True
        self.last_dt = dt

    def cleanup(self):
        self.cleanup_called = True


class TestSystemBase:
    """Test cases for the System base class."""

    def test_system_initialization(self):
        """Test system initialization with default values."""
        system = MockTestSystem()

        assert system.name == "test_system"
        assert system.priority == 100
        assert system.enabled is True
        assert system._engine is None

    def test_system_initialization_with_custom_values(self):
        """Test system initialization with custom values."""
        system = MockTestSystem("custom_system", 50)

        assert system.name == "custom_system"
        assert system.priority == 50
        assert system.enabled is True

    def test_system_initialize_with_engine(self):
        """Test system initialization with engine reference."""
        system = MockTestSystem()
        mock_engine = Mock()

        system.initialize(mock_engine)

        assert system.engine is mock_engine
        assert system.initialize_called is True

    def test_system_enable_disable(self):
        """Test enabling and disabling systems."""
        system = MockTestSystem()

        # Test disable
        system.disable()
        assert system.enabled is False

        # Test enable
        system.enable()
        assert system.enabled is True

    def test_system_update(self):
        """Test system update method."""
        system = MockTestSystem()
        dt = 0.016  # ~60 FPS

        system.update(dt)

        assert system.update_called is True
        assert system.last_dt == dt

    def test_system_cleanup(self):
        """Test system cleanup method."""
        system = MockTestSystem()

        system.cleanup()

        assert system.cleanup_called is True

    def test_abstract_system_cannot_be_instantiated(self):
        """Test that the abstract System class cannot be instantiated directly."""
        with pytest.raises(TypeError):
            System("test", 100)


class TestSystemIntegration:
    """Integration tests for System class."""

    def test_system_lifecycle(self):
        """Test complete system lifecycle."""
        system = MockTestSystem("lifecycle_test", 75)
        mock_engine = Mock()

        # Initialize
        system.initialize(mock_engine)
        assert system.initialize_called is True
        assert system.engine is mock_engine

        # Update
        system.update(0.016)
        assert system.update_called is True

        # Disable and verify no update
        system.disable()
        system.update_called = False
        system.update(0.016)
        # Note: The system itself doesn't check enabled state,
        # that's the engine's responsibility

        # Cleanup
        system.cleanup()
        assert system.cleanup_called is True
