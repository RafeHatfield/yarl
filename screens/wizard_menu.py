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
    
    # Menu dimensions
    menu_width = 40
    menu_height = 20
    
    # Center the menu
    screen_width = con.width
    screen_height = con.height
    x = screen_width // 2 - menu_width // 2
    y = screen_height // 2 - menu_height // 2
    
    # Draw menu background
    for i in range(menu_width):
        for j in range(menu_height):
            libtcod.console_put_char_ex(con, x + i, y + j, ' ', libtcod.white, libtcod.black)
    
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
    
    Args:
        game_state_manager: Game state manager
        
    Returns:
        GameStates: PLAYERS_TURN
    """
    state = game_state_manager.state
    message_log = state.message_log
    
    # TODO: Implement level teleport (needs number input)
    message_log.add_message(MB.custom("🧙 WIZARD: Level teleport not yet implemented", WIZARD_COLOR))
    
    return GameStates.PLAYERS_TURN


def wizard_spawn_npc(game_state_manager):
    """Spawn an NPC near the player.
    
    Args:
        game_state_manager: Game state manager
        
    Returns:
        GameStates: PLAYERS_TURN
    """
    state = game_state_manager.state
    message_log = state.message_log
    
    # TODO: Implement NPC spawning (needs submenu)
    message_log.add_message(MB.custom("🧙 WIZARD: NPC spawning not yet implemented", WIZARD_COLOR))
    
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

