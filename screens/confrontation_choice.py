"""Confrontation choice screen for final Entity encounter.

This module handles the critical moment when the player faces the Entity
with the Amulet of Yendor. The player must choose their fate.
"""

import tcod

from game_states import GameStates


def confrontation_menu(con, root_console, screen_width, screen_height):
    """Display the Entity confrontation and choice menu.
    
    Args:
        con: Console to draw on
        root_console: Root console for rendering
        screen_width: Width of the screen
        screen_height: Height of the screen
        
    Returns:
        tuple: (choice_letter, new_game_state) or (None, current_state)
    """
    # Entity's confrontation dialogue
    title = "The Entity's Throne Room"
    
    dialogue = [
        "You step through the portal into a vast chamber outside time itself.",
        "",
        "The Entity materializes before you - no longer just a voice,",
        "but a towering figure wreathed in temporal distortions.",
        "",
        "\"At last. You've done it. The Amulet of Yendor. My prison... my key.\"",
        "",
        "\"Hand it over, and your service is complete. I'll grant you freedom.\"",
        "",
        "The Entity's eyes gleam with barely contained desperation.",
        "You sense this is the moment that defines everything.",
        "",
        "What do you do?"
    ]
    
    # Choice options
    choices = [
        ("a", "Give the Amulet to the Entity"),
        ("b", "Keep the Amulet for yourself"),
    ]
    
    # Calculate dimensions
    dialogue_height = len(dialogue) + 2
    choices_height = len(choices) + 3
    total_height = dialogue_height + choices_height + 2
    menu_width = 70
    
    x = screen_width // 2 - menu_width // 2
    y = screen_height // 2 - total_height // 2
    
    # Draw background window
    tcod.console_set_default_background(con, tcod.black)
    tcod.console_set_default_foreground(con, tcod.white)
    tcod.console_clear(con)
    
    # Draw title
    tcod.console_set_default_foreground(con, tcod.gold)
    tcod.console_print_ex(
        con, menu_width // 2, 2,
        tcod.BKGND_NONE, tcod.CENTER,
        title
    )
    
    # Draw separator
    tcod.console_set_default_foreground(con, tcod.dark_gray)
    tcod.console_print_ex(
        con, menu_width // 2, 3,
        tcod.BKGND_NONE, tcod.CENTER,
        "=" * (menu_width - 4)
    )
    
    # Draw dialogue
    tcod.console_set_default_foreground(con, tcod.light_gray)
    current_y = 5
    for line in dialogue:
        if line == "":  # Empty line for spacing
            current_y += 1
            continue
        
        # Highlight Entity's speech in different color
        if line.startswith("\""):
            tcod.console_set_default_foreground(con, tcod.light_red)
        else:
            tcod.console_set_default_foreground(con, tcod.light_gray)
        
        tcod.console_print(con, 3, current_y, line)
        current_y += 1
    
    # Draw separator before choices
    current_y += 1
    tcod.console_set_default_foreground(con, tcod.dark_gray)
    tcod.console_print_ex(
        con, menu_width // 2, current_y,
        tcod.BKGND_NONE, tcod.CENTER,
        "-" * (menu_width - 4)
    )
    current_y += 2
    
    # Draw choices
    tcod.console_set_default_foreground(con, tcod.white)
    for letter, text in choices:
        choice_text = f"({letter}) {text}"
        tcod.console_print(con, 5, current_y, choice_text)
        current_y += 2
    
    # Draw instruction
    current_y += 1
    tcod.console_set_default_foreground(con, tcod.dark_gray)
    tcod.console_print_ex(
        con, menu_width // 2, current_y,
        tcod.BKGND_NONE, tcod.CENTER,
        "[Press a key to make your choice]"
    )
    
    # Blit to root console
    tcod.console_blit(con, 0, 0, menu_width, total_height, root_console, x, y, 1.0, 0.8)
    tcod.console_flush()
    
    # Wait for key input
    key = tcod.console_wait_for_keypress(True)
    
    # Handle choice
    if key.vk == tcod.KEY_ESCAPE:
        return None, GameStates.CONFRONTATION  # Stay in confrontation
    
    key_char = chr(key.c).lower() if key.c > 0 else ''
    
    if key_char == 'a':
        # Give Amulet - Bad Ending
        return 'bad', GameStates.FAILURE
    elif key_char == 'b':
        # Keep Amulet - Good Ending
        return 'good', GameStates.VICTORY
    
    return None, GameStates.CONFRONTATION  # Invalid input, stay in confrontation


def get_entity_anxiety_dialogue(anxiety_level):
    """Get Entity's dialogue based on how long player has delayed.
    
    Args:
        anxiety_level: 0-3 representing Entity's anxiety
        
    Returns:
        str: Dialogue line to display
    """
    anxiety_lines = {
        0: "\"Excellent. Now, let's conclude our arrangement.\"",
        1: "\"What took you so long? No matter. Hand it over.\"",
        2: "\"Where have you BEEN? I've been waiting! The Amulet. NOW.\"",
        3: "\"FINALLY! Do you have ANY idea how long— Never mind. Give. It. To. Me.\""
    }
    return anxiety_lines.get(anxiety_level, anxiety_lines[0])

