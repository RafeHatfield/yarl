"""Rendering functions and utilities for the game display.

This module handles all rendering operations including entity drawing,
UI panels, menus, and screen management. It defines render orders and
provides functions for drawing the game world and interface.

═══════════════════════════════════════════════════════════════════════════════
MODULE CONTRACT: Rendering & Visibility System
───────────────────────────────────────────────────────────────────────────────

OWNERSHIP:
  - Screen rendering, entity/map drawing
  - Visual display of game state
  - Death screen rendering and quote display

KEY CONTRACTS:
  - FOV visibility checks via fov_functions.py (NOT reimplemented here)
  - Visibility checks use: fov_map.is_in_fov(x, y)
  - Death screen quotes stored on game_state.death_screen_quote
  - Do NOT reimplement visibility logic; extend via rendering parameters

WHEN CHANGING BEHAVIOR:
  - Update tests/test_golden_path_floor1.py::test_basic_explore_floor1
  - Update tests/integration/portals/test_portal_visual_effects.py
  - Verify FOV rendering still works correctly
  - Check that visibility rules are respected

SEE ALSO:
  - fov_functions.py - FOV computation (don't duplicate)
  - rendering/ - Modular rendering subsystems
  - death_screen.py - Death screen specific rendering
═══════════════════════════════════════════════════════════════════════════════
"""

from enum import Enum, auto

import tcod.libtcodpy as libtcod

from game_states import GameStates
from menus import character_screen, inventory_menu, level_up_menu
from fov_functions import map_is_in_fov
from render_optimization import render_tiles_optimized
from entity_sorting_cache import get_sorted_entities
from death_screen import render_death_screen
from visual_effect_queue import get_effect_queue
from ui.sidebar import _render_sidebar
from config.ui_layout import get_ui_layout
from components.component_registry import ComponentType


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


def get_names_under_mouse(mouse, entities, fov_map, camera=None):
    """Get the names of all visible entities under the mouse cursor.

    Args:
        mouse: Mouse object with cursor coordinates (screen space), or None
        entities (list): List of all entities to check
        fov_map: Field of view map for visibility checking
        camera: Camera for coordinate translation (optional)

    Returns:
        str: Comma-separated string of entity names under the cursor, or empty string if mouse is None
    """
    # Handle case where mouse is None (e.g., at startup or in headless mode)
    if mouse is None:
        return ""
    
    # Get screen coordinates from mouse
    screen_x, screen_y = int(mouse.cx), int(mouse.cy)
    
    # Translate to world coordinates using ui_layout and camera
    ui_layout = get_ui_layout()
    
    # Get camera offset if available
    camera_x, camera_y = 0, 0
    if camera:
        camera_x, camera_y = camera.x, camera.y
    
    world_coords = ui_layout.screen_to_world(screen_x, screen_y, camera_x, camera_y)
    
    # If mouse is not over viewport, return empty string
    if world_coords is None:
        return ""
    
    (x, y) = world_coords

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
    sidebar_console=None,
    camera=None,
    death_screen_quote=None,
):
    """Render the entire game screen including map, entities, and UI.

    This is the main rendering function that draws everything visible
    on the screen including the game map, entities, UI panels, and menus.
    
    Now supports 3-console split-screen layout with camera (Phase 2):
    - Sidebar (left, full height): Menu, stats, equipment
    - Viewport (right, main): Map and entities (with camera scrolling!)
    - Status Panel (below viewport): HP, messages, dungeon info

    Args:
        con: Main game console (viewport in new layout)
        panel: UI panel console (status panel in new layout)
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
        sidebar_console: Left sidebar console (optional, for new layout)
        camera: Camera for viewport scrolling (optional, defaults to no scrolling)
        death_screen_quote: Pre-generated quote to show on the death screen
    """
    # Render map tiles with optional optimization
    if use_optimization:
        # Use optimized tile rendering with caching and camera
        render_tiles_optimized(con, game_map, fov_map, colors, force_full_redraw=fov_recompute, camera=camera)
    else:
        # Original tile rendering logic (kept for compatibility/debugging)
        _render_tiles_original(con, game_map, fov_map, colors, camera)

    # Use cached entity sorting for performance optimization
    entities_in_render_order = get_sorted_entities(entities)
    
    # Portal count check (silent)

    # Draw all entities in the list
    # for entity in entities:
    for entity in entities_in_render_order:
        draw_entity(con, entity, fov_map, game_map, camera)

    # libtcod.console_set_default_foreground(con, (255, 255, 255))
    # libtcod.console_print_ex(con, 1, screen_height - 2, libtcod.BKGND_NONE, libtcod.LEFT,
    #                      'HP: {0:02}/{1:02}'.format(player.fighter.hp, player.fighter.max_hp))

    # Get UI layout for positioning consoles
    ui_layout = get_ui_layout()
    
    # Blit viewport to screen
    viewport_pos = ui_layout.viewport_position
    libtcod.console_blit(
        con, 0, 0, ui_layout.viewport_width, ui_layout.viewport_height,
        0, viewport_pos[0], viewport_pos[1]
    )
    
    # NOTE: Visual effects are NOT played here anymore!
    # They are played AFTER frame flush to avoid blocking during rendering.
    # See ConsoleRenderer.render() for where effects are actually played.

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
        get_names_under_mouse(mouse, entities, fov_map, camera),
    )

    # Blit status panel below viewport (not full width, just viewport width)
    status_pos = ui_layout.status_panel_position
    libtcod.console_blit(
        panel, 0, 0, ui_layout.status_panel_width, ui_layout.status_panel_height,
        0, status_pos[0], status_pos[1]
    )
    
    # Render and blit sidebar (if provided)
    if sidebar_console:
        _render_sidebar(sidebar_console, player, ui_layout)
        sidebar_pos = ui_layout.sidebar_position
        libtcod.console_blit(
            sidebar_console, 0, 0, ui_layout.sidebar_width, ui_layout.screen_height,
            0, sidebar_pos[0], sidebar_pos[1]
        )

    if game_state == GameStates.THROW_SELECT_ITEM:
        # Throw selection menu (legacy - handled in sidebar now)
        inventory_title = "Select an item to throw, or Esc to cancel.\n"
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
    
    elif game_state == GameStates.PLAYER_DEAD:
        # Render death screen with statistics using the provided quote
        render_death_screen(con, player, screen_width, screen_height, death_screen_quote)
    
    # Render tooltips (if hovering over items or monsters)
    # This should be rendered LAST so it appears on top of everything
    if mouse and hasattr(mouse, 'cx') and hasattr(mouse, 'cy'):
        import logging
        tooltip_logger = logging.getLogger(__name__)
        from io_layer.console_renderer import get_last_frame_counter
        from ui.debug_flags import ENABLE_TOOLTIP_DEBUG, TOOLTIP_IGNORE_FOV
        
        # DEBUG: Very basic check to see if we're even in this code
        frame_id = get_last_frame_counter()
        is_debug_enabled = ENABLE_TOOLTIP_DEBUG
        log_level = tooltip_logger.level if hasattr(tooltip_logger, 'level') else 'unknown'
        # Print to console to verify tooltip code is running
        # (temporary diagnostic, will remove after we confirm the code path)
        # print(f"[TOOLTIP_DEBUG] frame={frame_id} debug_flag={is_debug_enabled} logger_level={log_level}")
        
        from ui.tooltip import (get_sidebar_item_at_position, get_sidebar_equipment_at_position, 
                               render_tooltip)
        
        # First check if hovering over equipment in sidebar
        hovered_entity = get_sidebar_equipment_at_position(mouse.cx, mouse.cy, player, ui_layout)
        
        # If not hovering over equipment, check if hovering over a sidebar inventory item
        if not hovered_entity:
            hovered_entity = get_sidebar_item_at_position(mouse.cx, mouse.cy, player, ui_layout)
        
        # If hovering over sidebar item, show single-entity tooltip
        if hovered_entity:
            if ENABLE_TOOLTIP_DEBUG and tooltip_logger.isEnabledFor(logging.DEBUG):
                tooltip_logger.debug("TOOLTIP_DRAW_CALL: frame=%d sidebar_entity", get_last_frame_counter())
            render_tooltip(0, hovered_entity, mouse.cx, mouse.cy, ui_layout)
        # Otherwise check viewport for monsters/items
        elif ui_layout.is_in_viewport(mouse.cx, mouse.cy):
            # Convert screen coordinates to world coordinates
            camera_x, camera_y = 0, 0
            if camera:
                camera_x, camera_y = camera.x, camera.y
            
            world_coords = ui_layout.screen_to_world(mouse.cx, mouse.cy, camera_x, camera_y)
            if world_coords:
                world_x, world_y = world_coords
                
                # DEBUG: Log viewport coordinates for flicker debugging
                if ENABLE_TOOLTIP_DEBUG and tooltip_logger.isEnabledFor(logging.DEBUG):
                    tooltip_logger.debug(
                        "TOOLTIP_VIEWPORT_START: frame=%d mouse=(%d,%d) world=(%d,%d)",
                        get_last_frame_counter(), mouse.cx, mouse.cy, world_x, world_y
                    )
                
                # Import functions for viewport entity tooltips
                from ui.tooltip import get_all_entities_at_position, render_multi_entity_tooltip
                
                # Debug: optionally ignore FOV for entity gathering
                effective_fov_map = None if TOOLTIP_IGNORE_FOV else fov_map
                
                # Get ALL entities at this position using unified, deterministic ordering
                entities_at_position = get_all_entities_at_position(world_x, world_y, entities, player, effective_fov_map)
                
                if ENABLE_TOOLTIP_DEBUG and tooltip_logger.isEnabledFor(logging.DEBUG):
                    entity_names = [getattr(e, "name", "UNNAMED") for e in entities_at_position]
                    tooltip_logger.debug(
                        "TOOLTIP_VIEWPORT_ENTITIES: frame=%d count=%d names=%s",
                        get_last_frame_counter(), len(entities_at_position), entity_names
                    )
                
                if entities_at_position:
                    if ENABLE_TOOLTIP_DEBUG and tooltip_logger.isEnabledFor(logging.DEBUG):
                        tooltip_logger.debug(
                            "TOOLTIP_DRAW_CALL: frame=%d kind=%s",
                            get_last_frame_counter(),
                            "multi" if len(entities_at_position) > 1 else "single"
                        )
                    
                    # Unified tooltip path: always use get_all_entities_at_position ordering
                    if len(entities_at_position) > 1:
                        # Multiple entities at same tile: show multi-entity tooltip
                        render_multi_entity_tooltip(0, entities_at_position, mouse.cx, mouse.cy, ui_layout)
                    else:
                        # Single entity: show single-entity tooltip
                        render_tooltip(0, entities_at_position[0], mouse.cx, mouse.cy, ui_layout)


def _render_tiles_original(con, game_map, fov_map, colors, camera=None):
    """Original tile rendering logic with camera support (kept for compatibility/debugging).
    
    This function contains the original tile rendering code that processes
    every tile on every frame. It's kept for compatibility and performance
    comparison purposes.
    
    Args:
        con: Console to render to
        game_map: Game map containing tile data
        fov_map: Field of view map for visibility checks
        colors: Color configuration dictionary
        camera: Camera for viewport scrolling (optional)
    """
    # Determine which tiles to render based on camera viewport
    if camera:
        start_x, start_y, end_x, end_y = camera.get_viewport_bounds()
        start_x = max(0, start_x)
        start_y = max(0, start_y)
        end_x = min(game_map.width, end_x)
        end_y = min(game_map.height, end_y)
    else:
        start_x, start_y = 0, 0
        end_x, end_y = game_map.width, game_map.height
    
    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            # Translate world coordinates to viewport coordinates
            if camera:
                if not camera.is_in_viewport(x, y):
                    continue
                viewport_x, viewport_y = camera.world_to_viewport(x, y)
            else:
                viewport_x, viewport_y = x, y
            
            visible = map_is_in_fov(fov_map, x, y)
            wall = game_map.tiles[x][y].block_sight
            tile = game_map.tiles[x][y]

            if visible:
                # Use tile's custom light color if set, otherwise use default
                if tile.light:
                    color = tile.light
                elif wall:
                    color = colors.get("light_wall")
                else:
                    color = colors.get("light_ground")
                
                libtcod.console_set_char_background(
                    con, viewport_x, viewport_y, color, libtcod.BKGND_SET
                )
                tile.explored = True
            elif tile.explored:
                # Use tile's custom dark color if set, otherwise use default
                if tile.dark:
                    color = tile.dark
                elif wall:
                    color = colors.get("dark_wall")
                else:
                    color = colors.get("dark_ground")
                
                libtcod.console_set_char_background(
                    con, viewport_x, viewport_y, color, libtcod.BKGND_SET
                )
            
            # Render ground hazard overlay if present
            _render_hazard_at_tile(con, game_map, x, y, viewport_x, viewport_y, visible, colors)


def _render_hazard_at_tile(con, game_map, world_x, world_y, viewport_x, viewport_y, visible, colors):
    """Render ground hazard visual overlay on a tile.
    
    This function renders hazard effects as lingering spell characters on tiles,
    showing persistent area effects like fire and poison gas. Visual intensity
    decays as the hazard ages, blending toward the floor color for a natural fade.
    
    Args:
        con: Console to render to
        game_map: Game map containing hazards
        world_x: World X coordinate
        world_y: World Y coordinate
        viewport_x: Viewport X coordinate for rendering
        viewport_y: Viewport Y coordinate for rendering
        visible: Whether the tile is currently visible in FOV
        colors: Color configuration dictionary for floor colors
    """
    # Skip if map doesn't have hazard manager
    if not hasattr(game_map, 'hazard_manager') or not game_map.hazard_manager:
        return
    
    # Check for hazard at this position
    hazard = game_map.hazard_manager.get_hazard_at(world_x, world_y)
    if not hazard:
        return
    
    # Only render hazards on visible or explored tiles
    if not visible and not game_map.tiles[world_x][world_y].explored:
        return
    
    # Get hazard character and color based on type
    
    if hazard.hazard_type == HazardType.FIRE:
        # Fireball leaves burning embers - use * character
        hazard_char = ord('*')
        base_color = (255, 100, 0)  # Orange fire
    elif hazard.hazard_type == HazardType.POISON_GAS:
        # Dragon Fart leaves toxic gas - use % character
        hazard_char = ord('%')
        base_color = (100, 200, 80)  # Green gas
    else:
        # Unknown hazard type, use generic character
        hazard_char = ord('~')
        base_color = (200, 200, 0)  # Yellow
    
    # Get intensity for fading effect
    intensity = hazard.get_visual_intensity()
    
    # Get floor color for blending (instead of fading to black)
    if visible:
        floor_color = colors.get("light_ground", (50, 50, 150))
    else:
        floor_color = colors.get("dark_ground", (0, 0, 100))
        intensity *= 0.3  # Dimmer when out of FOV
    
    # Blend hazard color with floor color as it ages
    # intensity=1.0 -> pure hazard color
    # intensity=0.0 -> pure floor color
    hazard_color = (
        int(base_color[0] * intensity + floor_color[0] * (1 - intensity)),
        int(base_color[1] * intensity + floor_color[1] * (1 - intensity)),
        int(base_color[2] * intensity + floor_color[2] * (1 - intensity))
    )
    
    # Render the hazard character on the tile
    libtcod.console_set_default_foreground(con, hazard_color)
    libtcod.console_put_char(con, viewport_x, viewport_y, hazard_char, libtcod.BKGND_NONE)


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


def draw_entity(con, entity, fov_map, game_map, camera=None):
    """Draw a single entity on the console if it's visible.

    Args:
        con: Console to draw on
        entity (Entity): Entity to draw
        fov_map: Field of view map for visibility checking
        game_map (GameMap): Game map for tile information
        camera: Camera for viewport translation (optional, defaults to no offset)
    """
    # Check if entity is a persistent feature (stairs, chests, signposts, murals, secret doors, portals)
    is_persistent_feature = (
        (hasattr(entity, "stairs") and entity.stairs) or
        (hasattr(entity, "chest") and entity.chest) or
        (hasattr(entity, "signpost") and entity.signpost) or
        (hasattr(entity, "mural") and entity.mural) or
        (hasattr(entity, "is_secret_door_marker") and entity.is_secret_door_marker) or
        (hasattr(entity, "is_portal") and entity.is_portal)
    )
    
    
    # SAFETY: Use GameMap safe accessor method instead of direct tile access
    is_explored = game_map.is_explored(entity.x, entity.y) if game_map else False
    
    in_fov = map_is_in_fov(fov_map, entity.x, entity.y)
    
    if in_fov or (is_persistent_feature and is_explored):
        # Translate world coordinates to viewport coordinates using camera
        if camera:
            # Check if entity is in viewport
            if not camera.is_in_viewport(entity.x, entity.y):
                return  # Entity is outside viewport, don't render
            
            # Translate to viewport coordinates
            viewport_x, viewport_y = camera.world_to_viewport(entity.x, entity.y)
        else:
            # No camera, use world coordinates directly (backward compatibility)
            viewport_x, viewport_y = entity.x, entity.y
        
        # Determine rendering color based on entity state
        render_color = entity.color
        render_char = entity.char
        
        # Check if entity is invisible (player invisibility effect)
        if hasattr(entity, 'invisible') and entity.invisible:
            # Render invisible entities with a translucent/faded appearance
            render_color = (
                max(0, entity.color[0] // 3),  # Reduce red by 2/3
                max(0, entity.color[1] // 3),  # Reduce green by 2/3  
                max(0, entity.color[2] // 3)   # Reduce blue by 2/3
            )
            render_char = '?' if entity.name == "Player" else entity.char
        
        # Check if entity is an opened chest (render as greyed out)
        elif hasattr(entity, 'chest') and entity.chest:
            from components.chest import ChestState
            if entity.chest.state == ChestState.OPEN:
                # Render opened chests in grey/whitewashed color
                render_color = (100, 100, 100)  # Dark grey
        
        # Get the current background color at this tile and render the entity
        bg_color = libtcod.console_get_char_background(con, viewport_x, viewport_y)
        libtcod.console_put_char_ex(con, viewport_x, viewport_y, render_char, render_color, bg_color)


def clear_entity(con, entity):
    """Clear a single entity from the console.

    Args:
        con: Console to clear from
        entity (Entity): Entity to clear
    """
    # erase the character that represents this object
    libtcod.console_put_char(con, entity.x, entity.y, " ", libtcod.BKGND_NONE)
