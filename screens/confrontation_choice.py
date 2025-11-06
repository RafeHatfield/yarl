"""Confrontation choice screen for Zhyraxion encounter.

This module handles the critical moment when the player faces Zhyraxion
with Aurelyn's Ruby Heart and must choose their fate across six possible endings.

Phase 5: The Six Endings
- Uses nested menu system (main choice → sub-choices)
- Conditional options based on knowledge flags
- Returns ending codes: '1', '2', '3', '4', '5', '6'

Ending Requirements:
  1 - Escape Through Battle: No knowledge required
  2 - Crimson Collector: BOTH entity_true_name_zhyraxion AND crimson_ritual_knowledge
  3 - Dragon's Bargain: No knowledge required
  4 - Fool's Freedom: No knowledge required
  5 - Mercy & Corruption: No knowledge required
  6 - Sacrifice & Redemption: entity_true_name_zhyraxion required
"""

import tcod
from typing import Optional, Tuple

from game_states import GameStates


def confrontation_menu(con, root_console, screen_width, screen_height, player):
    """Display Zhyraxion's confrontation and choice menu.
    
    Args:
        con: Console to draw on
        root_console: Root console for rendering
        screen_width: Width of the screen
        screen_height: Height of the screen
        player: Player entity (to check knowledge flags)
        
    Returns:
        tuple: (ending_code, new_game_state) or (None, current_state)
        ending_code: '1', '2', '3', '4', '5', '6' or None
    """
    # Get knowledge flags
    knows_true_name = False
    knows_ritual = False
    if hasattr(player, 'victory') and player.victory:
        knows_true_name = player.victory.knows_entity_true_name
        knows_ritual = player.victory.knows_crimson_ritual
    
    # Start with main menu
    return _main_choice_menu(con, root_console, screen_width, screen_height, 
                            knows_true_name, knows_ritual)

def _main_choice_menu(con, root_console, screen_width, screen_height, 
                     knows_true_name: bool, knows_ritual: bool) -> Tuple[Optional[str], GameStates]:
    """Display the main confrontation choice menu.
    
    Returns:
        tuple: (ending_code, game_state) or (None, CONFRONTATION)
        ending_code: '1', '2', '3', '4', '5', '6' or None
    """
    title = "The Confrontation Chamber"
    
    dialogue = [
        "You step through the portal into a circular chamber.",
        "",
        "Ritual circles glow on the floor. In the center lie golden scales -",
        "all that remains of a dragon named Aurelyn.",
        "",
        "A figure stands before you. Human in shape, but the eyes...",
        "ancient, draconic, burning with centuries of grief and rage.",
        "",
        "He speaks, voice like silk over steel:",
        "",
        "\"You have it. Aurelyn's heart. After all this time...\"",
        "",
        "\"I've waited centuries. Watched thousands die in this place.\"",
        "\"All for this moment.\"",
        "",
        "He extends a hand, trembling with barely contained desperation.",
        "",
        "\"Give it to me. I'll grant you your freedom. We can both escape.\"",
        "",
        "The Ruby Heart pulses warm in your hands, beating with a rhythm",
        "that isn't quite alive, isn't quite dead.",
        "",
        "What do you do with the heart?"
    ]
    
    # Main choices (3 options)
    choices = [
        ("K", "Keep the heart"),
        ("G", "Give the heart to him"),
        ("D", "Destroy the heart"),
    ]
    
    # Render the menu and get input
    key_char = _render_menu(con, root_console, screen_width, screen_height,
                           title, dialogue, choices)
    
    # Handle main choice
    if key_char is None:
        return None, GameStates.CONFRONTATION  # ESC pressed
    
    if key_char == 'k':
        # KEEP - Go to keep submenu
        return _keep_submenu(con, root_console, screen_width, screen_height, knows_ritual, knows_true_name)
    elif key_char == 'g':
        # GIVE - Ending 4 (Fool's Freedom - give heart immediately)
        return '4', GameStates.CONFRONTATION  # Will transition to appropriate outcome
    elif key_char == 'd':
        # DESTROY - Go to destroy submenu
        return _destroy_submenu(con, root_console, screen_width, screen_height, knows_true_name)
    
    return None, GameStates.CONFRONTATION  # Invalid input


def _keep_submenu(con, root_console, screen_width, screen_height, 
                 knows_ritual: bool, knows_true_name: bool) -> Tuple[Optional[str], GameStates]:
    """Display submenu for keeping the heart.
    
    Args:
        knows_ritual: Player has read Crimson Ritual Codex
        knows_true_name: Player knows Zhyraxion's true name
    
    Returns:
        tuple: (ending_code, game_state) or (None, CONFRONTATION)
        Possible endings:
          '1' - Escape Through Battle (fight)
          '2' - Crimson Collector (ritual - requires BOTH flags)
          '3' - Dragon's Bargain (accept transformation)
    """
    title = "You grip the heart tightly..."
    
    dialogue = [
        "You pull the Ruby Heart close to your chest.",
        "",
        "Zhyraxion's expression shifts - surprise, then anger.",
        "",
        "\"You would... keep it? DENY me?\"",
        "",
        "His form flickers, barely holding human shape.",
        "",
        "\"Very well. Let me offer you... alternatives.\"",
        "",
        "\"You could FIGHT me for your freedom - though I assure you,\"",
        "\"you won't win.\"",
        "",
        "\"Or... you could accept my gift. Become a dragon. We'll BOTH\"",
        "\"escape. You'll have power beyond imagining.\"",
        "",
        "His smile is thin, dangerous.",
    ]
    
    # Build choices based on knowledge
    choices = [
        ("F", "Fight for your freedom"),
        ("A", "Accept his transformation offer"),
    ]
    
    # CRITICAL: Ending 2 requires BOTH knowledge flags!
    if knows_ritual and knows_true_name:
        choices.append(("R", "Use the Crimson Ritual [SECRET]"))
    
    choices.append(("B", "Back"))
    
    # Render and get input
    key_char = _render_menu(con, root_console, screen_width, screen_height,
                           title, dialogue, choices)
    
    if key_char is None or key_char == 'b':
        return None, GameStates.CONFRONTATION  # Back to main menu
    
    if key_char == 'f':
        # Ending 1: Escape Through Battle
        return '1', GameStates.CONFRONTATION  # Will transition to Human Zhyraxion boss fight
    elif key_char == 'a':
        # Ending 3: Dragon's Bargain (accept transformation - trapped)
        return '3', GameStates.FAILURE  # Bad ending - player trapped
    elif key_char == 'r' and knows_ritual and knows_true_name:
        # Ending 2: Crimson Collector (dark power - ritual sequence)
        # CRITICAL: Only available if BOTH flags present
        return '2', GameStates.VICTORY  # Dark victory
    
    return None, GameStates.CONFRONTATION


def _destroy_submenu(con, root_console, screen_width, screen_height,
                    knows_true_name: bool) -> Tuple[Optional[str], GameStates]:
    """Display submenu for destroying the heart.
    
    Returns:
        tuple: (ending_code, game_state) or (None, CONFRONTATION)
        Possible endings:
          '5' - Mercy & Corruption (destroy without name - grief dragon fight)
          '6' - Sacrifice & Redemption (destroy with name - cutscene, best ending)
    """
    title = "You raise the heart..."
    
    dialogue = [
        "You lift Aurelyn's Ruby Heart above your head.",
        "",
        "Zhyraxion's eyes widen in horror.",
        "",
        "\"NO! Don't you DARE! That's all I have left of—\"",
        "",
        "\"Please. Don't do this. I'm begging you.\"",
        "",
        "The heart pulses in your hands. You feel its warmth,",
        "its not-quite-alive rhythm.",
        "",
        "This is someone's heart. Someone who was loved.",
    ]
    
    if knows_true_name:
        dialogue.extend([
            "",
            "You know his true name: Zhyraxion.",
            "",
            "If you speak it before destroying the heart...",
            "...perhaps there's another way."
        ])
    
    # Build choices
    choices = []
    
    if knows_true_name:
        choices.append(("N", "Speak his true name and destroy the heart"))
    
    choices.extend([
        ("J", "Just destroy it"),
        ("B", "Back")
    ])
    
    # Render and get input
    key_char = _render_menu(con, root_console, screen_width, screen_height,
                           title, dialogue, choices)
    
    if key_char is None or key_char == 'b':
        return None, GameStates.CONFRONTATION  # Back to main menu
    
    if key_char == 'n' and knows_true_name:
        # Ending 6: Sacrifice & Redemption (best ending - everyone freed)
        return '6', GameStates.VICTORY  # Golden light cutscene, everyone freed
    elif key_char == 'j':
        # Ending 5: Mercy & Corruption (tragic - grief dragon fight)
        return '5', GameStates.CONFRONTATION  # Will transition to Grief Dragon boss fight
    
    return None, GameStates.CONFRONTATION


def _render_menu(con, root_console, screen_width, screen_height,
                title: str, dialogue: list, choices: list) -> Optional[str]:
    """Render a menu and return the selected key.
    
    Args:
        con: Console to draw on
        root_console: Root console
        screen_width: Screen width
        screen_height: Screen height
        title: Menu title
        dialogue: List of dialogue lines
        choices: List of (key, text) tuples
        
    Returns:
        Selected key character (lowercase) or None if ESC pressed
    """
    # Calculate dimensions
    dialogue_height = len(dialogue) + 2
    choices_height = len(choices) + 2
    total_height = dialogue_height + choices_height + 6
    menu_width = 75
    
    x = screen_width // 2 - menu_width // 2
    y = max(2, screen_height // 2 - total_height // 2)
    
    # Draw background
    tcod.console_set_default_background(con, tcod.black)
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
    current_y = 5
    for line in dialogue:
        if line == "":
            current_y += 1
            continue
        
        # Highlight quoted speech
        if line.startswith("\""):
            tcod.console_set_default_foreground(con, tcod.crimson)
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
    for letter, text in choices:
        if "[SECRET]" in text:
            tcod.console_set_default_foreground(con, tcod.purple)
        else:
            tcod.console_set_default_foreground(con, tcod.white)
        
        choice_text = f"({letter}) {text}"
        tcod.console_print(con, 5, current_y, choice_text)
        current_y += 1
    
    # Draw instruction
    current_y += 2
    tcod.console_set_default_foreground(con, tcod.dark_gray)
    tcod.console_print_ex(
        con, menu_width // 2, current_y,
        tcod.BKGND_NONE, tcod.CENTER,
        "[Press a key to make your choice, ESC to go back]"
    )
    
    # Blit to root
    tcod.console_blit(con, 0, 0, menu_width, screen_height - 4, 
                     root_console, x, y, 1.0, 0.85)
    tcod.console_flush()
    
    # Wait for input
    key = tcod.console_wait_for_keypress(True)
    
    if key.vk == tcod.KEY_ESCAPE:
        return None
    
    key_char = chr(key.c).lower() if key.c > 0 else ''
    return key_char if key_char else None

