"""Menu helpers wrapper.

Delegates libtcod rendering to IO-layer menu_renderer.
"""

from io_layer import menu_renderer as _menu_renderer

globals().update({name: getattr(_menu_renderer, name) for name in dir(_menu_renderer) if not name.startswith("__")})

__all__ = [name for name in globals() if not name.startswith("__")]
