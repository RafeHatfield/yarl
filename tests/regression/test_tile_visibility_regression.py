"""Regression tests that ensure tiles remain visible after redraws.

These tests guard against regressions where the optimized tile renderer skips
repainting tiles after the orchestrator clears the viewport each frame.  The
tests exercise the caching path directly so that explored tiles continue to be
drawn even when they fall out of the player's current FOV.
"""

from unittest.mock import Mock, patch

import tcod.libtcodpy as libtcod

from render_optimization import OptimizedTileRenderer


class _DummyHazardManager:
    """Minimal hazard manager stub used by the tests."""

    def get_hazard_at(self, *_args, **_kwargs):
        return None


class _DummyTile:
    def __init__(self, block_sight: bool = False):
        self.block_sight = block_sight
        self.explored = False
        self.light = None
        self.dark = None


class _DummyGameMap:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.tiles = [[_DummyTile(False) for _ in range(height)] for _ in range(width)]
        self.hazard_manager = _DummyHazardManager()


def test_force_full_redraw_renders_visible_and_explored_tiles():
    """Tiles must be redrawn every frame even when cached state is unchanged."""

    renderer = OptimizedTileRenderer()
    game_map = _DummyGameMap(2, 2)
    console = Mock()
    colors = {
        "light_wall": (200, 180, 50),
        "light_ground": (130, 110, 50),
        "dark_wall": (0, 0, 100),
        "dark_ground": (50, 50, 150),
    }

    visible_tiles = {(0, 0)}

    def fake_in_fov(_fov_map, x, y):
        return (x, y) in visible_tiles

    with patch("render_optimization.map_is_in_fov", side_effect=fake_in_fov):
        with patch("render_optimization.libtcod.console_set_char_background") as mock_bg:
            # First frame: tile (0, 0) is visible and should become explored.
            renderer.render_tiles_optimized(
                console,
                game_map,
                fov_map=object(),
                colors=colors,
                force_full_redraw=True,
            )

            assert game_map.tiles[0][0].explored is True
            assert mock_bg.call_count > 0

            # Second frame: tile leaves FOV but should still draw as explored/dim.
            visible_tiles.clear()
            mock_bg.reset_mock()

            renderer.render_tiles_optimized(
                console,
                game_map,
                fov_map=object(),
                colors=colors,
                force_full_redraw=True,
            )

            mock_bg.assert_any_call(console, 0, 0, colors["dark_ground"], libtcod.BKGND_SET)
