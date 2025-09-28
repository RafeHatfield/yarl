"""Input handling functions for keyboard and mouse events.

This module processes player input and translates it into game actions
based on the current game state. Different states have different input
handlers for context-appropriate controls.
"""

import tcod.libtcodpy as libtcod

from game_states import GameStates


def handle_keys(key, game_state):
    """Route key input to the appropriate handler based on game state.

    Args:
        key: tcod Key object containing key press information
        game_state (GameStates): Current game state

    Returns:
        dict: Dictionary of actions to perform based on the key press
    """
    if game_state == GameStates.PLAYERS_TURN:
        return handle_player_turn_keys(key)
    elif game_state == GameStates.PLAYER_DEAD:
        return handle_player_dead_keys(key)
    elif game_state == GameStates.TARGETING:
        return handle_targeting_keys(key)
    elif game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
        return handle_inventory_keys(key)
    elif game_state == GameStates.LEVEL_UP:
        return handle_level_up_menu(key)
    elif game_state == GameStates.CHARACTER_SCREEN:
        return handle_character_screen(key)

    return {}


def handle_targeting_keys(key):
    """Handle input during targeting mode (for spells).

    Args:
        key: tcod Key object containing key press information

    Returns:
        dict: Dictionary with 'exit' key if targeting should be cancelled
    """
    if key.vk == libtcod.KEY_ESCAPE:
        return {"exit": True}

    return {}


def handle_inventory_keys(key):
    """Handle input in inventory menus (show/drop inventory).

    Args:
        key: tcod Key object containing key press information

    Returns:
        dict: Dictionary with 'inventory_index', 'fullscreen', or 'exit' keys
    """
    index = key.c - ord("a")

    if index >= 0:
        return {"inventory_index": index}

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle full screen
        return {"fullscreen": True}
    elif key.vk == libtcod.KEY_ESCAPE:
        # Exit the menu
        return {"exit": True}

    return {}


def handle_player_turn_keys(key):
    """Handle input during the player's turn (main gameplay).

    Processes movement, actions, and menu commands during normal gameplay.

    Args:
        key: tcod Key object containing key press information

    Returns:
        dict: Dictionary with action keys like 'move', 'pickup', 'show_inventory', etc.
    """
    key_char = chr(key.c)

    # Movement keys
    if key.vk == libtcod.KEY_UP or key_char == "k":
        return {"move": (0, -1)}
    elif key.vk == libtcod.KEY_DOWN or key_char == "j":
        return {"move": (0, 1)}
    elif key.vk == libtcod.KEY_LEFT or key_char == "h":
        return {"move": (-1, 0)}
    elif key.vk == libtcod.KEY_RIGHT or key_char == "l":
        return {"move": (1, 0)}
    elif key_char == "y":
        return {"move": (-1, -1)}
    elif key_char == "u":
        return {"move": (1, -1)}
    elif key_char == "b":
        return {"move": (-1, 1)}
    elif key_char == "n":
        return {"move": (1, 1)}
    elif key_char == "z":
        return {"wait": True}

    if key_char == "g":
        return {"pickup": True}
    elif key_char == "i":
        return {"show_inventory": True}
    elif key_char == "d":
        return {"drop_inventory": True}
    elif key.vk == libtcod.KEY_ENTER:
        return {"take_stairs": True}
    elif key_char == "c":
        return {"show_character_screen": True}

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle full screen
        return {"fullscreen": True}
    elif key.vk == libtcod.KEY_ESCAPE:
        # Exit the game
        return {"exit": True}

    # No key was pressed
    return {}


def handle_player_dead_keys(key):
    """Handle input when the player is dead (game over screen).

    When the player is dead, they should only be able to:
    - Press any key to return to the main menu
    - Toggle fullscreen
    - Exit the game
    
    No other actions (movement, inventory, etc.) should be allowed.

    Args:
        key: tcod Key object containing key press information

    Returns:
        dict: Dictionary with 'fullscreen' or 'exit' keys
    """
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle full screen
        return {"fullscreen": True}
    elif key.vk == libtcod.KEY_ESCAPE:
        # Exit the game completely
        return {"exit": True}
    elif key.vk != libtcod.KEY_NONE:
        # Any other key press returns to main menu
        return {"exit": True}

    return {}


def handle_mouse(mouse):
    """Handle mouse input events.

    Args:
        mouse: tcod Mouse object containing mouse state information

    Returns:
        dict: Dictionary with mouse action keys
    """
    (x, y) = (int(mouse.cx), int(mouse.cy))

    if mouse.lbutton_pressed:
        return {"left_click": (x, y)}
    elif mouse.rbutton_pressed:
        return {"right_click": (x, y)}

    return {}


def handle_main_menu(key):
    """Handle input in the main menu.

    Args:
        key: tcod Key object containing key press information

    Returns:
        dict: Dictionary with 'new_game', 'load_game', 'fullscreen', or 'exit' keys
    """
    key_char = chr(key.c)

    if key_char == "a":
        return {"new_game": True}
    elif key_char == "b":
        return {"load_game": True}
    elif key_char == "c" or key.vk == libtcod.KEY_ESCAPE:
        return {"exit": True}

    return {}


def handle_level_up_menu(key):
    """Handle input in the level up menu.

    Args:
        key: tcod Key object containing key press information

    Returns:
        dict: Dictionary with 'level_up' key containing the chosen stat
    """
    if key:
        key_char = chr(key.c)

        if key_char == "a":
            return {"level_up": "hp"}
        elif key_char == "b":
            return {"level_up": "str"}
        elif key_char == "c":
            return {"level_up": "def"}

    return {}


def handle_character_screen(key):
    """Handle input in the character screen.

    Args:
        key: tcod Key object containing key press information

    Returns:
        dict: Dictionary with 'exit' key to close the character screen
    """
    if key.vk == libtcod.KEY_ESCAPE:
        return {"exit": True}

    return {}
