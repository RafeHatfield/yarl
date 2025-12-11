"""Sidebar UI wrapper.

Delegates libtcod rendering to IO-layer sidebar_renderer.
"""

from io_layer.sidebar_renderer import _render_sidebar  # noqa: F401
from io_layer.sidebar_renderer import *  # noqa: F401,F403

__all__ = ["_render_sidebar"] + [name for name in list(globals()) if not name.startswith("_")]
