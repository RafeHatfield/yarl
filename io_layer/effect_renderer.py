"""Rendering helper for visual effects.

Keeps libtcod-bound drawing inside the IO layer. Core logic provides
draw calls via `visual_effect_queue`; this module turns them into console
glyphs.
"""

from typing import Iterable

import tcod.libtcodpy as libtcod

from visual_effect_queue import DrawCall


def render_effects(draw_calls: Iterable[DrawCall], console=0) -> None:
    """Render queued visual effects to the given console."""

    for call in draw_calls:
        libtcod.console_set_default_foreground(console, call.color)
        libtcod.console_put_char(
            console, call.x, call.y, call.char, libtcod.BKGND_NONE
        )














