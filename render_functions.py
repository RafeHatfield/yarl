"""Rendering functions and utilities for the game display.

This module handles all rendering operations including entity drawing,
UI panels, menus, and screen management. It defines render orders and
provides functions for drawing the game world and interface.
"""

from enum import Enum, auto

import tcod.libtcodpy as libtcod

from game_states import GameStates
from menus import character_screen, inventory_menu, level_up_menu
from fov_functions import map_is_in_fov
from render_optimization import render_tiles_optimized
from entity_sorting_cache import get_sorted_entities


class RenderOrder(Enum):
    """Enumeration defining the order in which entities are rendered.

    Lower values are rendered first (behind), higher values last (in front).
    This ensures proper layering of game objects.
    """

    STAIRS = auto()
    CORPSE = auto()
    ITEM = auto()
    ACTOR = auto()
    # STAIRS = 1
    # CORPSE = 2
    # ITEM = 3
    # ACTOR = 4


def get_names_under_mouse(mouse, entities, fov_map):
    """Get the names of all visible entities under the mouse cursor.

    Args:
        mouse: Mouse object with cursor coordinates
        entities (list): List of all entities to check
        fov_map: Field of view map for visibility checking

    Returns:
        str: Comma-separated string of entity names under the cursor
    """
    (x, y) = (mouse.cx, mouse.cy)

    names = [
        entity.name
        for entity in entities
        if entity.x == x
        and entity.y == y
        and map_is_in_fov(fov_map, entity.x, entity.y)
    ]
    names = ", ".join(names)

    return names.capitalize()


def render_bar(panel, x, y, total_width, name, value, maximum, bar_color, back_color):
    """Render a status bar (like health or XP) on the UI panel.

    Args:
        panel: Console panel to draw on
        x (int): X position of the bar
        y (int): Y position of the bar
        total_width (int): Total width of the bar in characters
        name (str): Name/label for the bar
        value (int): Current value (filled portion)
        maximum (int): Maximum value (total bar length)
        bar_color (tuple): RGB color for the filled portion
        back_color (tuple): RGB color for the background
    """
    bar_width = int(float(value) / maximum * total_width)

    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

    libtcod.console_set_default_foreground(panel, (255, 255, 255))
    libtcod.console_print_ex(
        panel,
        int(x + total_width / 2),
        y,
        libtcod.BKGND_NONE,
        libtcod.CENTER,
        "{0}: {1}/{2}".format(name, value, maximum),
    )


def render_all(
    con,
    panel,
    entities,
    player,
    game_map,
    fov_map,
    fov_recompute,
    message_log,
    screen_width,
    screen_height,
    bar_width,
    panel_height,
    panel_y,
    mouse,
    colors,
    game_state,
    use_optimization=True,
):
    """Render the entire game screen including map, entities, and UI.

    This is the main rendering function that draws everything visible
    on the screen including the game map, entities, UI panels, and menus.

    Args:
        con: Main game console
        panel: UI panel console
        entities (list): All entities to potentially render
        player (Entity): The player entity
        game_map (GameMap): The game map to render
        fov_map: Field of view map
        fov_recompute (bool): Whether to recompute field of view
        message_log (MessageLog): Game message log
        screen_width (int): Width of the screen
        screen_height (int): Height of the screen
        bar_width (int): Width of status bars
        panel_height (int): Height of the UI panel
        panel_y (int): Y position of the UI panel
        mouse: Mouse object for cursor information
        colors (dict): Color configuration dictionary
        game_state (GameStates): Current game state
        use_optimization (bool): Whether to use optimized tile rendering
    """
    # Render map tiles with optional optimization
    if use_optimization:
        # Use optimized tile rendering with caching
        render_tiles_optimized(con, game_map, fov_map, colors, force_full_redraw=fov_recompute)
    else:
        # Original tile rendering logic (kept for compatibility/debugging)
        _render_tiles_original(con, game_map, fov_map, colors)

    # Use cached entity sorting for performance optimization
    entities_in_render_order = get_sorted_entities(entities)

    # Draw all entities in the list
    # for entity in entities:
    for entity in entities_in_render_order:
        draw_entity(con, entity, fov_map, game_map)

    # libtcod.console_set_default_foreground(con, (255, 255, 255))
    # libtcod.console_print_ex(con, 1, screen_height - 2, libtcod.BKGND_NONE, libtcod.LEFT,
    #                      'HP: {0:02}/{1:02}'.format(player.fighter.hp, player.fighter.max_hp))

    libtcod.console_blit(con, 0, 0, screen_width, screen_height, 0, 0, 0)

    libtcod.console_set_default_background(panel, (0, 0, 0))
    libtcod.console_clear(panel)

    # Print the game messages, one line at a time
    y = 1
    for message in message_log.messages:
        libtcod.console_set_default_foreground(panel, message.color)
        libtcod.console_print_ex(
            panel, message_log.x, y, libtcod.BKGND_NONE, libtcod.LEFT, message.text
        )
        y += 1

    render_bar(
        panel,
        1,
        1,
        bar_width,
        "HP",
        max(0, player.fighter.hp),  # Clamp HP display to 0 minimum
        player.fighter.max_hp,
        (255, 63, 63),
        (127, 0, 0),
    )
    libtcod.console_print_ex(
        panel,
        1,
        3,
        libtcod.BKGND_NONE,
        libtcod.LEFT,
        "Dungeon level: {0}".format(game_map.dungeon_level),
    )

    libtcod.console_set_default_foreground(panel, (159, 159, 159))
    libtcod.console_print_ex(
        panel,
        1,
        0,
        libtcod.BKGND_NONE,
        libtcod.LEFT,
        get_names_under_mouse(mouse, entities, fov_map),
    )

    libtcod.console_blit(panel, 0, 0, screen_width, panel_height, 0, 0, panel_y)

    if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
        if game_state == GameStates.SHOW_INVENTORY:
            inventory_title = (
                "Press the key next to an item to use it, or Esc to cancel.\n"
            )
        else:
            inventory_title = (
                "Press the key next to an item to drop it, or Esc to cancel.\n"
            )

        inventory_menu(con, inventory_title, player, 50, screen_width, screen_height)

    elif game_state == GameStates.LEVEL_UP:
        level_up_menu(
            con,
            "Level up! Choose a stat to raise:",
            player,
            40,
            screen_width,
            screen_height,
        )

    elif game_state == GameStates.CHARACTER_SCREEN:
        character_screen(player, 50, 40, screen_width, screen_height)


def _render_tiles_original(con, game_map, fov_map, colors):
    """Original tile rendering logic (kept for compatibility/debugging).
    
    This function contains the original tile rendering code that processes
    every tile on every frame. It's kept for compatibility and performance
    comparison purposes.
    
    Args:
        con: Console to render to
        game_map: Game map containing tile data
        fov_map: Field of view map for visibility checks
        colors: Color configuration dictionary
    """
    for y in range(game_map.height):
        for x in range(game_map.width):
            visible = map_is_in_fov(fov_map, x, y)
            wall = game_map.tiles[x][y].block_sight

            if visible:
                if wall:
                    libtcod.console_set_char_background(
                        con, x, y, colors.get("light_wall"), libtcod.BKGND_SET
                    )
                else:
                    libtcod.console_set_char_background(
                        con, x, y, colors.get("light_ground"), libtcod.BKGND_SET
                    )

                game_map.tiles[x][y].explored = True
            elif game_map.tiles[x][y].explored:
                if wall:
                    libtcod.console_set_char_background(
                        con, x, y, colors.get("dark_wall"), libtcod.BKGND_SET
                    )
                else:
                    libtcod.console_set_char_background(
                        con, x, y, colors.get("dark_ground"), libtcod.BKGND_SET
                    )


def clear_all(con, entities):
    """Clear all entities from the console.

    Args:
        con: Console to clear entities from
        entities (list): List of entities to clear
    """
    for entity in entities:
        clear_entity(con, entity)


# def draw_entity(con, entity):
#     libtcod.console_set_default_foreground(con, entity.color)
#     libtcod.console_put_char(con, entity.x, entity.y, entity.char, libtcod.BKGND_NONE)


def draw_entity(con, entity, fov_map, game_map):
    """Draw a single entity on the console if it's visible.

    Args:
        con: Console to draw on
        entity (Entity): Entity to draw
        fov_map: Field of view map for visibility checking
        game_map (GameMap): Game map for tile information
    """
    # Check if entity has stairs attribute (for backwards compatibility with saves)
    has_stairs = hasattr(entity, "stairs") and entity.stairs
    if map_is_in_fov(fov_map, entity.x, entity.y) or (
        has_stairs and game_map.tiles[entity.x][entity.y].explored
    ):
        libtcod.console_set_default_foreground(con, entity.color)
        libtcod.console_put_char(
            con, entity.x, entity.y, entity.char, libtcod.BKGND_NONE
        )


def clear_entity(con, entity):
    """Clear a single entity from the console.

    Args:
        con: Console to clear from
        entity (Entity): Entity to clear
    """
    # erase the character that represents this object
    libtcod.console_put_char(con, entity.x, entity.y, " ", libtcod.BKGND_NONE)
