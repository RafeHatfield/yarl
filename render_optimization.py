"""Legacy shim for render optimization.

Rendering implementation now lives in `io_layer.render_optimization` to
keep libtcod usage confined to IO-layer renderers.
"""

from io_layer.render_optimization import *  # noqa: F401,F403
