"""IO-layer tooltip rendering helpers.

All libtcod drawing for tooltips lives here to keep `ui/tooltip.py`
data-only and renderer-agnostic.
"""

from typing import Sequence, Any, Tuple

import tcod.libtcodpy as libtcod

from config.ui_layout import get_ui_layout
from ui.tooltip import (
    TooltipAnchor,
    TooltipKind,
    TooltipModel,
    _screen_to_console_coords,
    _build_single_entity_lines,
    _build_multi_entity_lines,
)

# Tooltip offset from cursor to prevent obscuring the hovered element
# These are in console character coordinates, so small values = significant visual offset
TOOLTIP_OFFSET_X = 2
TOOLTIP_OFFSET_Y = 1


def _draw_tooltip_box(
    console,
    tooltip_lines: Sequence[str],
    tooltip_x: int,
    tooltip_y: int,
    bounds_width: int,
    bounds_height: int,
) -> None:
    tooltip_width = max(len(line) for line in tooltip_lines) + 4
    tooltip_height = len(tooltip_lines) + 2

    # Apply offset to prevent tooltip from obscuring the hovered element
    tooltip_x += TOOLTIP_OFFSET_X
    tooltip_y += TOOLTIP_OFFSET_Y

    # Positioning adjustments to keep tooltip on-screen
    # If offset pushes tooltip off right edge, flip it to the left of cursor
    if tooltip_x + tooltip_width >= bounds_width:
        tooltip_x = max(0, tooltip_x - TOOLTIP_OFFSET_X - tooltip_width - TOOLTIP_OFFSET_X)
    
    # If offset pushes tooltip off bottom edge, flip it above cursor
    if tooltip_y + tooltip_height >= bounds_height:
        tooltip_y = max(0, tooltip_y - TOOLTIP_OFFSET_Y - tooltip_height - TOOLTIP_OFFSET_Y)

    # Final clamp to ensure we don't go negative
    tooltip_x = max(0, tooltip_x)
    tooltip_y = max(0, tooltip_y)

    # Draw background and border
    for x in range(tooltip_width):
        for y in range(tooltip_height):
            libtcod.console_put_char(console, tooltip_x + x, tooltip_y + y, ord(' '), libtcod.BKGND_SET)
            libtcod.console_set_char_background(
                console,
                tooltip_x + x,
                tooltip_y + y,
                libtcod.Color(20, 20, 20),
                libtcod.BKGND_SET,
            )

    # Horizontal lines
    for x in range(tooltip_x + 1, tooltip_x + tooltip_width - 1):
        libtcod.console_put_char(console, x, tooltip_y, ord('─'), libtcod.BKGND_SET)
        libtcod.console_put_char(console, x, tooltip_y + tooltip_height - 1, ord('─'), libtcod.BKGND_SET)

    # Vertical lines
    for y in range(tooltip_y + 1, tooltip_y + tooltip_height - 1):
        libtcod.console_put_char(console, tooltip_x, y, ord('│'), libtcod.BKGND_SET)
        libtcod.console_put_char(
            console, tooltip_x + tooltip_width - 1, y, ord('│'), libtcod.BKGND_SET
        )

    libtcod.console_put_char(console, tooltip_x, tooltip_y, ord('┌'), libtcod.BKGND_SET)
    libtcod.console_put_char(console, tooltip_x + tooltip_width - 1, tooltip_y, ord('┐'), libtcod.BKGND_SET)
    libtcod.console_put_char(
        console, tooltip_x, tooltip_y + tooltip_height - 1, ord('└'), libtcod.BKGND_SET
    )
    libtcod.console_put_char(
        console,
        tooltip_x + tooltip_width - 1,
        tooltip_y + tooltip_height - 1,
        ord('┘'),
        libtcod.BKGND_SET,
    )

    libtcod.console_set_default_foreground(console, libtcod.Color(255, 255, 255))
    libtcod.console_set_default_background(console, libtcod.Color(40, 40, 40))
    for idx, line in enumerate(tooltip_lines):
        libtcod.console_print_ex(
            console,
            tooltip_x + 2,
            tooltip_y + 1 + idx,
            libtcod.BKGND_SET,
            libtcod.LEFT,
            line,
        )


def _render_lines_for_anchor(
    console,
    tooltip_lines: Sequence[str],
    screen_position: Tuple[int, int],
    anchor: TooltipAnchor,
    ui_layout,
) -> None:
    coords = _screen_to_console_coords(anchor, screen_position, ui_layout)
    if coords is None:
        return

    local_x, local_y, bounds_width, bounds_height = coords
    _draw_tooltip_box(console, tooltip_lines, local_x, local_y, bounds_width, bounds_height)


def render_tooltip(console, entity: Any, mouse_x: int, mouse_y: int, ui_layout) -> None:
    if not entity:
        return

    tooltip_lines = _build_single_entity_lines(entity)
    screen_pos = (int(mouse_x), int(mouse_y))
    _render_lines_for_anchor(console, tooltip_lines, screen_pos, TooltipAnchor.VIEWPORT, ui_layout)


def render_multi_entity_tooltip(console, entities: list, mouse_x: int, mouse_y: int, ui_layout) -> None:
    if not entities:
        return

    tooltip_lines = _build_multi_entity_lines(entities)
    screen_pos = (int(mouse_x), int(mouse_y))
    _render_lines_for_anchor(console, tooltip_lines, screen_pos, TooltipAnchor.VIEWPORT, ui_layout)


def render(model: TooltipModel, viewport_console, sidebar_console) -> None:
    """Draw the tooltip described by ``model`` onto the supplied console."""
    if model.kind == TooltipKind.NONE or model.screen_position is None:
        return

    target_console = viewport_console if model.anchor is TooltipAnchor.VIEWPORT else sidebar_console
    if target_console is None:
        return

    mouse_x, mouse_y = model.screen_position
    ui_layout = get_ui_layout()

    if model.lines:
        tooltip_lines = list(model.lines)
    elif model.kind == TooltipKind.MULTI:
        tooltip_lines = _build_multi_entity_lines(model.entities)
    else:
        entity = model.entities[0] if model.entities else None
        tooltip_lines = _build_single_entity_lines(entity)

    _render_lines_for_anchor(target_console, tooltip_lines, (mouse_x, mouse_y), model.anchor, ui_layout)
