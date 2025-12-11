"""Victory screen wrapper.

Delegates libtcod rendering/input to IO-layer renderer.
"""

from io_layer.victory_screen_renderer import show_victory_screen

__all__ = ["show_victory_screen"]
