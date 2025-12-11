"""Death screen rendering and statistics display.

Delegates libtcod drawing to the IO-layer renderer to preserve the
rendering boundary guardrail.
"""

from io_layer.death_screen_renderer import render_death_screen as _render_death_screen_io
from entity_dialogue import get_entity_quote_for_death


def render_death_screen(con, player, screen_width, screen_height, entity_quote=None, run_metrics=None):
    """Render the death screen via the IO-layer renderer."""
    return _render_death_screen_io(con, player, screen_width, screen_height, entity_quote, run_metrics)
