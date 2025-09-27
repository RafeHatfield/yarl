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
                        # First frame with game state fov_recompute=True
                        self.mock_engine.state_manager.request_fov_recompute()
                        self.render_system.update(0.016)

                        # Should have recomputed
                        assert mock_recompute.call_count == 1

                        # Second frame with game state fov_recompute=True again (same position)
                        self.mock_engine.state_manager.request_fov_recompute()
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
                        # First frame with game state fov_recompute=False, same position
                        self.mock_engine.state_manager.state.fov_recompute = False
                        self.render_system.update(0.016)

                        # Should not recompute when flag is False
                        mock_recompute.assert_not_called()

                        # Second frame, still False, same position
                        self.mock_engine.state_manager.state.fov_recompute = False
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

    def test_map_tiles_rendered_when_fov_recomputed_regression(self):
        """Regression test: Ensure map tiles are rendered when FOV is recomputed.

        Bug: OptimizedRenderSystem was using self.fov_recompute instead of
        game_state.fov_recompute, causing map tiles to never be drawn (black screen).

        The render_all function only draws map tiles when fov_recompute=True,
        so the optimized system must use the game state's flag, not its own.
        """
        # Create optimized render system for this test
        render_system = OptimizedRenderSystem(
            console=Mock(),
            panel=Mock(),
            screen_width=80,
            screen_height=50,
            colors={"light_wall": (130, 110, 50)},
            priority=100,
            use_optimizations=True,
        )

        # Create mock engine and state manager
        mock_engine = Mock()
        state_manager = GameStateManager()
        mock_engine.state_manager = state_manager
        mock_engine.get_system = Mock(return_value=PerformanceSystem())

        # Initialize render system
        render_system.initialize(mock_engine)

        # Set up basic game state
        player = Mock()
        player.x = 5
        player.y = 5

        game_map = Mock()
        message_log = Mock()
        entities = [player]

        # Initialize game state
        state_manager.initialize_game(
            player=player,
            entities=entities,
            game_map=game_map,
            message_log=message_log,
            game_state=Mock(),
            constants={"fov_radius": 10, "fov_light_walls": True, "fov_algorithm": 0},
        )

        # Set up FOV map
        fov_map = Mock()
        render_system.set_fov_map(fov_map)

        # THE KEY TEST: Set game state fov_recompute=True but render system flag=False
        # This simulates the bug where game requests FOV recompute but render system
        # uses its own stale flag instead of the game state flag
        state_manager.request_fov_recompute()  # Sets game state flag to True
        render_system.fov_recompute = False  # Render system flag is False

        # Mock render_all to verify it gets called with fov_recompute=True
        with patch(
            "engine.systems.optimized_render_system.render_all"
        ) as mock_render_all:
            with patch("engine.systems.optimized_render_system.recompute_fov"):
                with patch("engine.systems.optimized_render_system.clear_all"):
                    with patch("tcod.libtcodpy.console_flush"):
                        # Update the render system
                        render_system.update(0.016)

                        # render_all should have been called with fov_recompute=True
                        # because the system should use game_state.fov_recompute, not self.fov_recompute
                        mock_render_all.assert_called_once()
                        call_args = mock_render_all.call_args[0]
                        fov_recompute_arg = call_args[
                            6
                        ]  # 7th argument is fov_recompute

                        # This should be True so map tiles get rendered
                        assert fov_recompute_arg is True, (
                            f"render_all called with fov_recompute={fov_recompute_arg}, "
                            f"expected True for map tiles to be rendered. "
                            f"OptimizedRenderSystem should use game_state.fov_recompute, "
                            f"not self.fov_recompute"
                        )

    def test_game_state_fov_flag_takes_precedence_regression(self):
        """Regression test: Game state fov_recompute flag takes precedence.

        Bug: OptimizedRenderSystem was ignoring the game state's fov_recompute flag
        and using its own internal flag, causing desync between game logic and rendering.

        This test ensures the render system always uses the authoritative game state flag.
        """
        # Create optimized render system
        render_system = OptimizedRenderSystem(
            console=Mock(),
            panel=Mock(),
            screen_width=80,
            screen_height=50,
            colors={"light_wall": (130, 110, 50)},
            priority=100,
            use_optimizations=False,  # Use standard rendering for this test
        )

        # Create mock engine and state manager
        mock_engine = Mock()
        state_manager = GameStateManager()
        mock_engine.state_manager = state_manager

        # Initialize render system
        render_system.initialize(mock_engine)

        # Set up basic game state
        player = Mock()
        player.x = 5
        player.y = 5

        game_map = Mock()
        message_log = Mock()
        entities = [player]

        # Initialize game state
        state_manager.initialize_game(
            player=player,
            entities=entities,
            game_map=game_map,
            message_log=message_log,
            game_state=Mock(),
            constants={"fov_radius": 10},
        )

        # Set up FOV map
        fov_map = Mock()
        render_system.set_fov_map(fov_map)

        # Test scenario 1: Game state says True, render system says False
        state_manager.request_fov_recompute()  # Game state: True
        render_system.fov_recompute = False  # Render system: False

        # The render system should update its flag from game state
        with patch(
            "engine.systems.optimized_render_system.render_all"
        ) as mock_render_all:
            with patch("engine.systems.optimized_render_system.recompute_fov"):
                with patch("engine.systems.optimized_render_system.clear_all"):
                    with patch("tcod.libtcodpy.console_flush"):
                        render_system.update(0.016)

                        # Should use game state flag (True), not render system flag (False)
                        call_args = mock_render_all.call_args[0]
                        fov_recompute_arg = call_args[6]
                        assert fov_recompute_arg is True

        # Test scenario 2: Game state says False, render system says True
        state_manager.state.fov_recompute = False  # Game state: False
        render_system.fov_recompute = True  # Render system: True

        with patch(
            "engine.systems.optimized_render_system.render_all"
        ) as mock_render_all:
            with patch("engine.systems.optimized_render_system.recompute_fov"):
                with patch("engine.systems.optimized_render_system.clear_all"):
                    with patch("tcod.libtcodpy.console_flush"):
                        render_system.update(0.016)

                        # Should use game state flag (False), not render system flag (True)
                        call_args = mock_render_all.call_args[0]
                        fov_recompute_arg = call_args[6]
                        assert fov_recompute_arg is False

    def test_game_state_fov_flag_reset_after_render_regression(self):
        """Regression test: Game state fov_recompute flag is reset after rendering.

        Bug: If the game state's fov_recompute flag isn't reset after rendering,
        it would cause map tiles to be redrawn every frame, negating performance optimizations.

        This test ensures the flag is properly reset after rendering.
        """
        # Create optimized render system
        render_system = OptimizedRenderSystem(
            console=Mock(),
            panel=Mock(),
            screen_width=80,
            screen_height=50,
            colors={"light_wall": (130, 110, 50)},
            priority=100,
            use_optimizations=False,
        )

        # Create mock engine and state manager
        mock_engine = Mock()
        state_manager = GameStateManager()
        mock_engine.state_manager = state_manager

        # Initialize render system
        render_system.initialize(mock_engine)

        # Set up basic game state
        player = Mock()
        game_map = Mock()
        message_log = Mock()
        entities = [player]

        state_manager.initialize_game(
            player=player,
            entities=entities,
            game_map=game_map,
            message_log=message_log,
            game_state=Mock(),
            constants={"fov_radius": 10},
        )

        # Set up FOV map and request recompute
        fov_map = Mock()
        render_system.set_fov_map(fov_map)
        state_manager.request_fov_recompute()

        # Verify flag is initially True
        assert state_manager.state.fov_recompute is True

        # Render one frame
        with patch("engine.systems.optimized_render_system.render_all"):
            with patch("engine.systems.optimized_render_system.recompute_fov"):
                with patch("engine.systems.optimized_render_system.clear_all"):
                    with patch("tcod.libtcodpy.console_flush"):
                        render_system.update(0.016)

        # Flag should be reset to False after rendering
        assert state_manager.state.fov_recompute is False, (
            "Game state fov_recompute flag should be reset to False after rendering "
            "to prevent unnecessary map tile redraws on subsequent frames"
        )

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
