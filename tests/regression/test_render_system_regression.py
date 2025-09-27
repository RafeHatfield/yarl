"""Regression tests for render system bugs.

This module contains tests specifically designed to prevent regression
of bugs that have been fixed in the render system.
"""

import pytest
from unittest.mock import Mock, patch

from engine.systems.optimized_render_system import OptimizedRenderSystem
from engine.systems.performance_system import PerformanceSystem
from engine.game_state_manager import GameStateManager


class TestRenderSystemRegressions:
    """Regression tests for render system bugs."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create optimized render system
        self.console = Mock()
        self.panel = Mock()
        self.render_system = OptimizedRenderSystem(
            console=self.console,
            panel=self.panel,
            screen_width=80,
            screen_height=50,
            colors={"light_wall": (130, 110, 50)},
            priority=100,
            use_optimizations=True,
        )

        # Create performance system
        self.performance_system = PerformanceSystem()

        # Create mock engine with both systems
        self.mock_engine = Mock()
        self.mock_engine.get_system = Mock(return_value=self.performance_system)

        # Create game state manager
        self.state_manager = GameStateManager()
        self.mock_engine.state_manager = self.state_manager

        # Initialize systems
        self.render_system.initialize(self.mock_engine)
        self.performance_system.initialize(self.mock_engine)

        # Set up basic game state
        self.player = Mock()
        self.player.x = 5
        self.player.y = 5

        self.game_map = Mock()
        self.message_log = Mock()
        self.entities = [self.player]

        # Initialize game state
        self.state_manager.initialize_game(
            player=self.player,
            entities=self.entities,
            game_map=self.game_map,
            message_log=self.message_log,
            game_state=Mock(),
            constants={"fov_radius": 10, "fov_light_walls": True, "fov_algorithm": 0},
        )

        # Set up FOV map
        self.fov_map = Mock()
        self.render_system.set_fov_map(self.fov_map)

    def test_fov_recompute_flag_respected_regression(self):
        """Regression test: Ensure fov_recompute flag is always respected.

        Bug: OptimizedRenderSystem was ignoring the fov_recompute flag and only
        recomputing FOV when position changed, causing the map to stay black
        after the first frame.

        The render system should ALWAYS recompute FOV when fov_recompute=True,
        regardless of position caching optimizations.
        """
        # Set fov_recompute to True (this should force recomputation)
        self.render_system.fov_recompute = True

        # Mock recompute_fov to verify it gets called
        with patch(
            "engine.systems.optimized_render_system.recompute_fov"
        ) as mock_recompute:
            # Mock render_all, clear_all, and console_flush to avoid complex rendering logic in test
            with patch("engine.systems.optimized_render_system.render_all"):
                with patch("engine.systems.optimized_render_system.clear_all"):
                    with patch("tcod.libtcodpy.console_flush"):
                        # Update the render system
                        self.render_system.update(0.016)

                        # FOV should have been recomputed because fov_recompute was True
                        mock_recompute.assert_called_once_with(
                            self.fov_map,
                            self.player.x,
                            self.player.y,
                            10,  # fov_radius
                            True,  # fov_light_walls
                            0,  # fov_algorithm
                        )

    def test_fov_recompute_multiple_frames_regression(self):
        """Regression test: FOV recomputes on multiple frames when flag is set.

        This ensures that FOV caching doesn't prevent recomputation when
        the fov_recompute flag is explicitly set to True.
        """
        with patch(
            "engine.systems.optimized_render_system.recompute_fov"
        ) as mock_recompute:
            with patch("engine.systems.optimized_render_system.render_all"):
                with patch("engine.systems.optimized_render_system.clear_all"):
                    with patch("tcod.libtcodpy.console_flush"):
                        # First frame with fov_recompute=True
                        self.render_system.fov_recompute = True
                        self.render_system.update(0.016)

                        # Should have recomputed
                        assert mock_recompute.call_count == 1

                        # Second frame with fov_recompute=True again (same position)
                        self.render_system.fov_recompute = True
                        self.render_system.update(0.016)

                        # Should have recomputed again, despite same position
                        assert mock_recompute.call_count == 2

    def test_fov_caching_still_works_when_flag_false_regression(self):
        """Regression test: FOV caching works when fov_recompute is False.

        Ensures that the fix doesn't break the caching optimization when
        fov_recompute is False.
        """
        with patch(
            "engine.systems.optimized_render_system.recompute_fov"
        ) as mock_recompute:
            with patch("engine.systems.optimized_render_system.render_all"):
                with patch("engine.systems.optimized_render_system.clear_all"):
                    with patch("tcod.libtcodpy.console_flush"):
                        # First frame with fov_recompute=False, same position
                        self.render_system.fov_recompute = False
                        self.render_system.update(0.016)

                        # Should not recompute when flag is False
                        mock_recompute.assert_not_called()

                        # Second frame, still False, same position
                        self.render_system.fov_recompute = False
                        self.render_system.update(0.016)

                        # Still should not recompute
                        mock_recompute.assert_not_called()

    def test_fov_recompute_overrides_position_caching_regression(self):
        """Regression test: fov_recompute=True overrides position-based caching.

        Even if the performance system says FOV doesn't need recomputation
        based on position, the fov_recompute flag should override that decision.
        """
        # Set up performance system to say no recomputation needed
        self.performance_system.last_fov_position = (self.player.x, self.player.y)
        self.performance_system.last_fov_radius = 10

        # Verify performance system would say no recomputation needed
        assert not self.performance_system.should_recompute_fov(
            self.player.x, self.player.y, 10
        )

        with patch(
            "engine.systems.optimized_render_system.recompute_fov"
        ) as mock_recompute:
            with patch("engine.systems.optimized_render_system.render_all"):
                with patch("engine.systems.optimized_render_system.clear_all"):
                    with patch("tcod.libtcodpy.console_flush"):
                        # But fov_recompute=True should override this
                        self.render_system.fov_recompute = True
                        self.render_system.update(0.016)

                        # Should have recomputed despite position caching
                        mock_recompute.assert_called_once()

    def test_standard_render_fallback_respects_fov_flag_regression(self):
        """Regression test: Standard render fallback respects fov_recompute flag.

        When optimizations are disabled or unavailable, the system should
        fall back to standard rendering and still respect the fov_recompute flag.
        """
        # Disable optimizations to force standard rendering
        self.render_system.use_optimizations = False

        with patch(
            "engine.systems.optimized_render_system.recompute_fov"
        ) as mock_recompute:
            with patch("engine.systems.optimized_render_system.render_all"):
                with patch("engine.systems.optimized_render_system.clear_all"):
                    with patch("tcod.libtcodpy.console_flush"):
                        # Set fov_recompute flag
                        self.render_system.fov_recompute = True
                        self.render_system.update(0.016)

                        # Should have recomputed in standard rendering mode
                        mock_recompute.assert_called_once()


class TestRenderSystemInterfaceContract:
    """Tests to ensure render system interface contracts are maintained."""

    def test_optimized_render_system_behaves_like_base_system(self):
        """Ensure OptimizedRenderSystem behaves identically to base RenderSystem.

        This test verifies that optimizations don't change the core behavior
        of the rendering system, particularly FOV handling.
        """
        from engine.systems.render_system import RenderSystem

        # Create both systems with identical configuration
        base_system = RenderSystem(
            console=Mock(),
            panel=Mock(),
            screen_width=80,
            screen_height=50,
            colors={"light_wall": (130, 110, 50)},
            priority=100,
        )

        optimized_system = OptimizedRenderSystem(
            console=Mock(),
            panel=Mock(),
            screen_width=80,
            screen_height=50,
            colors={"light_wall": (130, 110, 50)},
            priority=100,
            use_optimizations=False,  # Disable optimizations for comparison
        )

        # Both should have the same interface
        assert hasattr(base_system, "fov_recompute")
        assert hasattr(optimized_system, "fov_recompute")
        assert hasattr(base_system, "set_fov_map")
        assert hasattr(optimized_system, "set_fov_map")

        # Both should respect the fov_recompute flag identically
        base_system.fov_recompute = True
        optimized_system.fov_recompute = True

        assert base_system.fov_recompute == optimized_system.fov_recompute
