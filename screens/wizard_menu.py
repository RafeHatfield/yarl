"""Wizard Mode debug menu for testing and development.

This screen provides in-game debug commands for rapid testing:
- Heal to full HP
- Toggle god mode
- Reveal map
- Gain XP
- Spawn entities (NPCs, monsters, items)
- Unlock knowledge
- Teleport to level

Only accessible when wizard_mode is enabled (--wizard flag).
Press @ (Shift+2) or F12 to open the wizard menu in-game.
"""

import tcod as libtcod

from game_states import GameStates
from message_builder import MessageBuilder as MB


# Wizard mode color (purple to distinguish from game messages)
WIZARD_COLOR = (138, 43, 226)

# Global console reference for helper functions
_wizard_console = None


def show_wizard_menu(con, game_state_manager):
    """Display the wizard mode debug menu.
    
    Args:
        con: The console to draw on
        game_state_manager: Game state manager
        
    Returns:
        GameStates: The new game state (PLAYERS_TURN or current state)
    """
    from config.testing_config import get_testing_config
    config = get_testing_config()
    
    # Safety check - shouldn't be able to access without wizard mode
    if not config.wizard_mode:
        return game_state_manager.state.current_state
    
    # Store console for helper functions
    global _wizard_console
    _wizard_console = con
    
    # Menu dimensions
    menu_width = 40
    menu_height = 20
    
    # Center the menu
    screen_width = con.width
    screen_height = con.height
    x = screen_width // 2 - menu_width // 2
    y = screen_height // 2 - menu_height // 2
    
    # Draw solid black background for readability
    for i in range(menu_width):
        for j in range(menu_height):
            libtcod.console_set_char_background(con, x + i, y + j, libtcod.black, libtcod.BKGND_SET)
            libtcod.console_put_char(con, x + i, y + j, ' ')
    
    # Draw border
    # Top border
    libtcod.console_put_char(con, x, y, libtcod.CHAR_NE)
    libtcod.console_put_char(con, x + menu_width - 1, y, libtcod.CHAR_NW)
    for i in range(1, menu_width - 1):
        libtcod.console_put_char(con, x + i, y, libtcod.CHAR_HLINE)
    
    # Bottom border
    libtcod.console_put_char(con, x, y + menu_height - 1, libtcod.CHAR_SE)
    libtcod.console_put_char(con, x + menu_width - 1, y + menu_height - 1, libtcod.CHAR_SW)
    for i in range(1, menu_width - 1):
        libtcod.console_put_char(con, x + i, y + menu_height - 1, libtcod.CHAR_HLINE)
    
    # Side borders
    for j in range(1, menu_height - 1):
        libtcod.console_put_char(con, x, y + j, libtcod.CHAR_VLINE)
        libtcod.console_put_char(con, x + menu_width - 1, y + j, libtcod.CHAR_VLINE)
    
    # Title
    title = "WIZARD MODE"
    libtcod.console_print_ex(
        con, 
        x + menu_width // 2, 
        y + 1,
        libtcod.BKGND_NONE,
        libtcod.CENTER,
        title
    )
    
    # Menu options
    row = 3
    libtcod.console_print(con, x + 2, y + row, "H - Heal to Full HP")
    row += 1
    
    god_status = "[ON]" if config.god_mode else "[OFF]"
    libtcod.console_print(con, x + 2, y + row, f"G - Toggle God Mode {god_status}")
    row += 1
    
    libtcod.console_print(con, x + 2, y + row, "R - Reveal Entire Map")
    row += 1
    
    libtcod.console_print(con, x + 2, y + row, "X - Gain XP")
    row += 1
    
    libtcod.console_print(con, x + 2, y + row, "L - Teleport to Level...")
    row += 2
    
    # Separator
    for i in range(1, menu_width - 1):
        libtcod.console_put_char(con, x + i, y + row, libtcod.CHAR_HLINE)
    row += 1
    
    libtcod.console_print(con, x + 2, y + row, "N - Spawn NPC...")
    row += 1
    
    libtcod.console_print(con, x + 2, y + row, "M - Spawn Monster...")
    row += 1
    
    libtcod.console_print(con, x + 2, y + row, "I - Spawn Item...")
    row += 2
    
    # Separator
    for i in range(1, menu_width - 1):
        libtcod.console_put_char(con, x + i, y + row, libtcod.CHAR_HLINE)
    row += 1
    
    libtcod.console_print(con, x + 2, y + row, "K - Unlock Knowledge...")
    row += 2
    
    # Separator
    for i in range(1, menu_width - 1):
        libtcod.console_put_char(con, x + i, y + row, libtcod.CHAR_HLINE)
    row += 1
    
    libtcod.console_print(con, x + 2, y + row, "ESC - Close Menu")
    
    # Present the menu
    libtcod.console_flush()
    
    # Wait for input
    key = libtcod.console_wait_for_keypress(True)
    
    # Handle input
    key_char = chr(key.c) if key.c > 0 else None
    
    if key.vk == libtcod.KEY_ESCAPE:
        return GameStates.PLAYERS_TURN
    
    elif key_char and key_char.upper() == 'H':
        return wizard_heal(game_state_manager)
    
    elif key_char and key_char.upper() == 'G':
        return wizard_toggle_god_mode(game_state_manager)
    
    elif key_char and key_char.upper() == 'R':
        return wizard_reveal_map(game_state_manager)
    
    elif key_char and key_char.upper() == 'X':
        return wizard_gain_xp(game_state_manager)
    
    elif key_char and key_char.upper() == 'L':
        return wizard_teleport_to_level(game_state_manager)
    
    elif key_char and key_char.upper() == 'N':
        return wizard_spawn_npc(game_state_manager)
    
    elif key_char and key_char.upper() == 'M':
        return wizard_spawn_monster(game_state_manager)
    
    elif key_char and key_char.upper() == 'I':
        return wizard_spawn_item(game_state_manager)
    
    elif key_char and key_char.upper() == 'K':
        return wizard_unlock_knowledge(game_state_manager)
    
    # Invalid key, stay in menu
    return game_state_manager.state.current_state


# ============================================================================
# WIZARD COMMAND IMPLEMENTATIONS
# ============================================================================

def wizard_heal(game_state_manager):
    """Heal player to full HP.
    
    Args:
        game_state_manager: Game state manager
        
    Returns:
        GameStates: PLAYERS_TURN
    """
    state = game_state_manager.state
    player = state.player
    message_log = state.message_log
    
    if player and player.fighter:
        player.fighter.hp = player.fighter.max_hp
        message_log.add_message(MB.custom("🧙 WIZARD: Healed to full HP", WIZARD_COLOR))
    
    return GameStates.PLAYERS_TURN


def wizard_toggle_god_mode(game_state_manager):
    """Toggle god mode on/off.
    
    Args:
        game_state_manager: Game state manager
        
    Returns:
        GameStates: PLAYERS_TURN
    """
    from config.testing_config import get_testing_config
    config = get_testing_config()
    state = game_state_manager.state
    message_log = state.message_log
    
    config.god_mode = not config.god_mode
    status = "ENABLED" if config.god_mode else "DISABLED"
    message_log.add_message(MB.custom(f"🧙 WIZARD: God Mode {status}", WIZARD_COLOR))
    
    return GameStates.PLAYERS_TURN


def wizard_reveal_map(game_state_manager):
    """Reveal entire map.
    
    Args:
        game_state_manager: Game state manager
        
    Returns:
        GameStates: PLAYERS_TURN
    """
    state = game_state_manager.state
    game_map = state.game_map
    message_log = state.message_log
    
    if game_map:
        # Mark all tiles as explored
        for x in range(game_map.width):
            for y in range(game_map.height):
                game_map.tiles[x][y].explored = True
        
        message_log.add_message(MB.custom("🧙 WIZARD: Revealed entire map", WIZARD_COLOR))
    
    return GameStates.PLAYERS_TURN


def wizard_gain_xp(game_state_manager):
    """Grant player XP.
    
    Args:
        game_state_manager: Game state manager
        
    Returns:
        GameStates: PLAYERS_TURN
    """
    state = game_state_manager.state
    player = state.player
    message_log = state.message_log
    
    if player and player.level:
        xp_amount = 100
        player.level.add_xp(xp_amount)
        message_log.add_message(MB.custom(f"🧙 WIZARD: Gained {xp_amount} XP", WIZARD_COLOR))
    
    return GameStates.PLAYERS_TURN


def wizard_teleport_to_level(game_state_manager):
    """Teleport to a specific dungeon level.
    
    Descends floors until reaching target level, heals player each floor.
    
    Args:
        game_state_manager: Game state manager
        
    Returns:
        GameStates: PLAYERS_TURN
    """
    state = game_state_manager.state
    player = state.player
    game_map = state.game_map
    message_log = state.message_log
    entities = state.entities
    constants = state.constants
    
    # Prompt for target level
    message_log.add_message(MB.custom("🧙 WIZARD: Enter target level (1-25, ESC to cancel):", WIZARD_COLOR))
    
    # Simple number input loop
    target_level = _get_number_input(1, 25)
    
    if target_level is None:
        message_log.add_message(MB.custom("🧙 WIZARD: Teleport cancelled", WIZARD_COLOR))
        return GameStates.PLAYERS_TURN
    
    current_level = game_map.dungeon_level
    
    if target_level == current_level:
        message_log.add_message(MB.custom(f"🧙 WIZARD: Already on level {target_level}", WIZARD_COLOR))
        return GameStates.PLAYERS_TURN
    
    if target_level < current_level:
        message_log.add_message(MB.custom("🧙 WIZARD: Cannot teleport backwards (not implemented)", WIZARD_COLOR))
        return GameStates.PLAYERS_TURN
    
    # Descend to target level
    levels_to_descend = target_level - current_level
    message_log.add_message(MB.custom(f"🧙 WIZARD: Teleporting to level {target_level}...", WIZARD_COLOR))
    
    for i in range(levels_to_descend):
        # Use the same next_floor logic as normal descent
        game_map.next_floor(player, message_log, constants)
    
    # Heal player after teleport
    player.fighter.hp = player.fighter.max_hp
    
    # Force FOV recompute to ensure map renders correctly
    import tcod as libtcod
    from fov_functions import initialize_fov, recompute_fov
    
    fov_recompute = True
    fov_map = initialize_fov(game_map)
    recompute_fov(fov_map, player.x, player.y, constants['fov_radius'], constants['fov_light_walls'], constants['fov_algorithm'])
    
    # Update the FOV map in the game state
    if hasattr(state, 'fov_map'):
        state.fov_map = fov_map
    
    message_log.add_message(MB.custom(f"🧙 WIZARD: Arrived at dungeon level {game_map.dungeon_level}", WIZARD_COLOR))
    
    return GameStates.PLAYERS_TURN


def wizard_spawn_npc(game_state_manager):
    """Spawn an NPC near the player.
    
    Currently supports:
    - Ghost Guide (for Phase 3 testing)
    
    Args:
        game_state_manager: Game state manager
        
    Returns:
        GameStates: PLAYERS_TURN
    """
    state = game_state_manager.state
    player = state.player
    game_map = state.game_map
    entities = state.entities
    message_log = state.message_log
    
    # For now, just spawn the Ghost Guide
    # In future, could add a submenu for different NPCs
    from config.entity_factory import get_entity_factory
    entity_factory = get_entity_factory()
    
    # Find empty spot near player
    spawn_x, spawn_y = _find_empty_spot_near(player.x, player.y, game_map, entities)
    
    if spawn_x is None:
        message_log.add_message(MB.custom("🧙 WIZARD: No empty spot near player!", WIZARD_COLOR))
        return GameStates.PLAYERS_TURN
    
    # Spawn Ghost Guide
    guide = entity_factory.create_unique_npc('ghost_guide', spawn_x, spawn_y, game_map.dungeon_level)
    
    if guide:
        entities.append(guide)
        message_log.add_message(MB.custom(f"🧙 WIZARD: Spawned {guide.name} at ({spawn_x}, {spawn_y})", WIZARD_COLOR))
    else:
        message_log.add_message(MB.custom("🧙 WIZARD: Failed to spawn Ghost Guide", WIZARD_COLOR))
    
    return GameStates.PLAYERS_TURN


def wizard_spawn_monster(game_state_manager):
    """Spawn a monster near the player.
    
    Args:
        game_state_manager: Game state manager
        
    Returns:
        GameStates: PLAYERS_TURN
    """
    state = game_state_manager.state
    message_log = state.message_log
    
    # TODO: Implement monster spawning (needs submenu)
    message_log.add_message(MB.custom("🧙 WIZARD: Monster spawning not yet implemented", WIZARD_COLOR))
    
    return GameStates.PLAYERS_TURN


def wizard_spawn_item(game_state_manager):
    """Spawn an item near the player.
    
    Args:
        game_state_manager: Game state manager
        
    Returns:
        GameStates: PLAYERS_TURN
    """
    state = game_state_manager.state
    message_log = state.message_log
    
    # TODO: Implement item spawning (needs submenu)
    message_log.add_message(MB.custom("🧙 WIZARD: Item spawning not yet implemented", WIZARD_COLOR))
    
    return GameStates.PLAYERS_TURN


def wizard_unlock_knowledge(game_state_manager):
    """Unlock knowledge for victory conditions.
    
    Args:
        game_state_manager: Game state manager
        
    Returns:
        GameStates: PLAYERS_TURN
    """
    state = game_state_manager.state
    message_log = state.message_log
    
    # TODO: Implement knowledge unlocking (needs submenu)
    message_log.add_message(MB.custom("🧙 WIZARD: Knowledge unlock not yet implemented", WIZARD_COLOR))
    
    return GameStates.PLAYERS_TURN


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_number_input(min_val: int, max_val: int):
    """Get a number input from the user with visual feedback.
    
    Args:
        min_val: Minimum valid value
        max_val: Maximum valid value
        
    Returns:
        int or None: The entered number, or None if cancelled
    """
    import tcod as libtcod
    
    input_string = ""
    
    # Work with root console (0) directly for immediate visibility
    root = 0
    
    # Input box dimensions - use fixed screen size
    box_width = 50
    box_height = 5
    screen_width = 80  # Standard screen width
    screen_height = 50  # Standard screen height
    x = screen_width // 2 - box_width // 2
    y = screen_height // 2 - box_height // 2
    
    while True:
        # Draw input box with solid background directly to root console
        for i in range(box_width):
            for j in range(box_height):
                libtcod.console_set_char_background(root, x + i, y + j, libtcod.black, libtcod.BKGND_SET)
                libtcod.console_put_char(root, x + i, y + j, ' ')
        
        # Draw border
        for i in range(box_width):
            libtcod.console_put_char(root, x + i, y, libtcod.CHAR_HLINE)
            libtcod.console_put_char(root, x + i, y + box_height - 1, libtcod.CHAR_HLINE)
        for j in range(box_height):
            libtcod.console_put_char(root, x, y + j, libtcod.CHAR_VLINE)
            libtcod.console_put_char(root, x + box_width - 1, y + j, libtcod.CHAR_VLINE)
        
        # Draw prompt with green color (wizard mode theme)
        libtcod.console_set_default_foreground(root, libtcod.green)
        prompt = f"Enter level ({min_val}-{max_val}):"
        libtcod.console_print(root, x + 2, y + 1, prompt)
        
        # Draw input with bright green
        libtcod.console_set_default_foreground(root, libtcod.light_green)
        input_display = input_string + "_"
        libtcod.console_print(root, x + 2, y + 2, input_display)
        
        # Draw help text
        libtcod.console_set_default_foreground(root, libtcod.dark_green)
        help_text = "ENTER=confirm ESC=cancel"
        libtcod.console_print(root, x + 2, y + 3, help_text)
        
        # Flush to screen
        libtcod.console_flush()
        
        # Wait for key press
        key = libtcod.console_wait_for_keypress(True)
        
        if key.vk == libtcod.KEY_ESCAPE:
            return None
        
        elif key.vk == libtcod.KEY_ENTER:
            # Try to parse the input
            if input_string:
                try:
                    value = int(input_string)
                    if min_val <= value <= max_val:
                        return value
                except ValueError:
                    pass
            return None
        
        elif key.vk == libtcod.KEY_BACKSPACE:
            # Remove last character
            if input_string:
                input_string = input_string[:-1]
        
        elif key.c > 0:
            # Add character if it's a digit
            char = chr(key.c)
            if char.isdigit() and len(input_string) < 3:  # Max 3 digits (up to 999)
                input_string += char


def _find_empty_spot_near(x: int, y: int, game_map, entities, max_distance: int = 3):
    """Find an empty spot near the given coordinates.
    
    Args:
        x: Center x coordinate
        y: Center y coordinate
        game_map: Game map
        entities: List of entities
        max_distance: Maximum distance to search
        
    Returns:
        tuple: (x, y) of empty spot, or (None, None) if none found
    """
    # Try adjacent tiles first (distance 1)
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            
            new_x, new_y = x + dx, y + dy
            
            # Check if spot is valid
            if _is_spot_empty(new_x, new_y, game_map, entities):
                return (new_x, new_y)
    
    # Try further out (distance 2-3)
    for dist in range(2, max_distance + 1):
        for dx in range(-dist, dist + 1):
            for dy in range(-dist, dist + 1):
                if abs(dx) < dist and abs(dy) < dist:
                    continue  # Skip inner tiles (already checked)
                
                new_x, new_y = x + dx, y + dy
                
                if _is_spot_empty(new_x, new_y, game_map, entities):
                    return (new_x, new_y)
    
    return (None, None)


def _is_spot_empty(x: int, y: int, game_map, entities):
    """Check if a spot is empty and walkable.
    
    Args:
        x: X coordinate
        y: Y coordinate
        game_map: Game map
        entities: List of entities
        
    Returns:
        bool: True if spot is empty and walkable
    """
    # Check bounds and walkability
    if not game_map.is_in_bounds(x, y) or game_map.is_blocked(x, y):
        return False
    
    # Check for blocking entities
    for entity in entities:
        if entity.x == x and entity.y == y and getattr(entity, 'blocks', False):
            return False
    
    return True

