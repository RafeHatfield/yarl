"""Input handling functions for keyboard and mouse events.

This module processes player input and translates it into game actions
based on the current game state. Different states have different input
handlers for context-appropriate controls.

Input routing is now handled by StateManager (state_management/state_config.py)
to maintain a single source of truth for state behavior.
"""

import tcod.libtcodpy as libtcod

from game_states import GameStates
from state_management.state_config import StateManager


def handle_keys(key, game_state, death_frame_counter=None):
    """Route key input to the appropriate handler based on game state.
    
    Now uses StateManager to eliminate hardcoded state lists.
    See state_management/state_config.py for state configurations.

    Args:
        key: tcod Key object containing key press information
        game_state (GameStates): Current game state
        death_frame_counter: Number of frames since death (optional, for PLAYER_DEAD state)

    Returns:
        dict: Dictionary of actions to perform based on the key press
    """
    # Get handler from StateManager (single source of truth!)
    handler = StateManager.get_input_handler(game_state)
    
    if handler:
        # Special case: PLAYER_DEAD needs death_frame_counter
        if game_state == GameStates.PLAYER_DEAD:
            return handler(key, death_frame_counter)
        else:
            return handler(key)
    
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
    key_char = chr(key.c) if key.c > 0 else None

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
    elif key_char == "t":
        return {"throw": True}
    elif key.vk == libtcod.KEY_ENTER:
        return {"take_stairs": True}
    elif key_char == "c":
        return {"show_character_screen": True}
    elif key_char == "o":
        return {"start_auto_explore": True}
    elif key_char == "s":
        return {"search": True}
    
    # Tier 2: Wizard Mode - Use @ (Shift+2) or F12
    if key_char == "@" or key.vk == libtcod.KEY_F12:
        # Only available in wizard mode
        from config.testing_config import get_testing_config
        if get_testing_config().wizard_mode:
            return {"show_wizard_menu": True}

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle full screen
        return {"fullscreen": True}
    elif key.vk == libtcod.KEY_ESCAPE:
        # Exit the game
        return {"exit": True}

    # No key was pressed
    return {}


def handle_player_dead_keys(key, death_frame_counter=None):
    """Handle input when the player is dead (game over screen).

    When the player is dead, they should be able to:
    - Press R to restart a new game
    - Press ESC to return to main menu
    - Press Alt+Enter to toggle fullscreen
    - Press any other key to exit
    
    No other actions (movement, inventory, etc.) should be allowed.

    Args:
        key: tcod Key object containing key press information
        death_frame_counter: Number of frames since death (to prevent immediate exit)

    Returns:
        dict: Dictionary with 'restart', 'exit', or 'fullscreen' keys
    """
    # Ignore input for the first 10 frames after death to prevent accidental exit
    if death_frame_counter is not None and death_frame_counter < 10:
        return {}
    
    # Only respond to actual key presses (not key releases or no-key state)
    if key.vk == libtcod.KEY_NONE and key.c == 0:
        return {}
    
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle full screen
        return {"fullscreen": True}
    elif key.vk == libtcod.KEY_ESCAPE:
        # ESC: return to main menu
        return {"exit": True}
    elif key.c == ord('r') or key.c == ord('R'):
        # R: restart a new game
        return {"restart": True}
    elif key.vk != libtcod.KEY_NONE or key.c != 0:
        # Any other key press exits to main menu
        return {"exit": True}

    return {}


def handle_mouse(mouse, camera=None, game_state=None):
    """Handle mouse input events with coordinate translation for split-screen layout.

    Args:
        mouse: tcod Mouse object containing mouse state information
        camera: Optional Camera object for coordinate translation with viewport scrolling
        game_state: Optional GameState for context-aware coordinate handling

    Returns:
        dict: Dictionary with mouse action keys (coordinates vary by context)
    """
    
    # Get raw screen coordinates
    screen_x, screen_y = int(mouse.cx), int(mouse.cy)
    
    # For menu states (SHOW_INVENTORY, DROP_INVENTORY, THROW_SELECT_ITEM), return screen coordinates
    # because menus are rendered as overlays at screen positions
    if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY, GameStates.THROW_SELECT_ITEM):
        if mouse.lbutton_pressed:
            return {"left_click": (screen_x, screen_y)}
        elif mouse.rbutton_pressed:
            return {"right_click": (screen_x, screen_y)}
        return {}
    
    # Translate screen coordinates to world coordinates
    # This accounts for sidebar offset, viewport positioning, AND camera offset
    ui_layout = get_ui_layout()
    
    # Get camera coordinates for proper translation
    camera_x, camera_y = 0, 0
    if camera:
        camera_x, camera_y = camera.x, camera.y
    
    world_coords = ui_layout.screen_to_world(screen_x, screen_y, camera_x, camera_y)

    # Check if click is in sidebar (for inventory interaction!)
    if ui_layout.is_in_sidebar(screen_x, screen_y):
        # Handle sidebar clicks (inventory items)
        if mouse.lbutton_pressed:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"SIDEBAR LEFT-CLICK detected at screen ({screen_x}, {screen_y})")
            return {"sidebar_click": (screen_x, screen_y)}
        elif mouse.rbutton_pressed:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"SIDEBAR RIGHT-CLICK detected at screen ({screen_x}, {screen_y})")
            return {"sidebar_right_click": (screen_x, screen_y)}
        return {}
    
    # If click is not in viewport or sidebar, ignore
    if world_coords is None:
        # Click was in status panel or outside bounds
        return {}
    
    x, y = world_coords

    if mouse.lbutton_pressed:
        return {"left_click": (x, y)}
    elif mouse.rbutton_pressed:
        return {"right_click": (x, y)}

    return {}


def handle_main_menu(key, mouse=None):
    """Handle input in the main menu.

    Args:
        key: tcod Key object containing key press information
        mouse: tcod Mouse object containing mouse state (optional)

    Returns:
        dict: Dictionary with 'new_game', 'load_game', 'fullscreen', or 'exit' keys
    """
    # Handle keyboard input
    key_char = chr(key.c)

    if key_char == "a":
        return {"new_game": True}
    elif key_char == "b":
        return {"load_game": True}
    elif key_char == "c":
        return {"hall_of_fame": True}
    elif key_char == "d" or key.vk == libtcod.KEY_ESCAPE:
        return {"exit": True}
    
    # Handle mouse clicks
    if mouse and mouse.lbutton_pressed:
        from menus import get_menu_click_index
        from config.ui_layout import get_ui_layout
        
        ui_layout = get_ui_layout()
        
        # Main menu options
        options = ["Play a new game", "Continue last game", "Hall of Fame", "Quit"]
        
        # Check if click is on a menu option
        # Main menu uses empty header and width of 24
        clicked_index = get_menu_click_index(
            mouse.cx, mouse.cy, "", options, 24,
            ui_layout.screen_width, ui_layout.screen_height
        )
        
        if clicked_index is not None:
            if clicked_index == 0:  # Play a new game
                return {"new_game": True}
            elif clicked_index == 1:  # Continue last game
                return {"load_game": True}
            elif clicked_index == 2:  # Hall of Fame
                return {"hall_of_fame": True}
            elif clicked_index == 3:  # Quit
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
