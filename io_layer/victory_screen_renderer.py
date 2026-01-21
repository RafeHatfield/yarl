"""Victory and failure ending screens.

This module displays the final outcome screens after the player makes
their choice in the Entity confrontation.

All ending text is loaded from config/endings.yaml for easy editing and
internationalization.
"""

import tcod
import yaml
from typing import Dict, Any

from utils.resource_paths import get_resource_path


def _load_endings():
    """Load ending dialogue from YAML file.
    
    Returns:
        dict: All ending data
    """
    endings_file = get_resource_path("config/endings.yaml")
    with open(endings_file, 'r') as f:
        data = yaml.safe_load(f)
    return data['endings']


# Color mapping from string names to tcod colors
COLOR_MAP = {
    'amber': tcod.amber,
    'dark_crimson': tcod.dark_crimson,
    'dark_red': tcod.dark_red,
    'red': tcod.red,
    'grey': tcod.grey,
    'gold': tcod.gold,
    'light_green': tcod.light_green,
}


def show_ending_screen(con, root_console, screen_width, screen_height,
                       ending_type, player_stats):
    """Display the ending screen based on player's choice.

    Phase 5: The Six Endings
    - '1': Escape Through Battle (fight Human Zhyraxion, neutral-good)
    - '2': Crimson Collector (ritual, dark victory - requires BOTH knowledge flags)
    - '3': Dragon's Bargain (transformation trap, bad ending)
    - '4': Fool's Freedom (give heart immediately, bad ending)
    - '5': Mercy & Corruption (destroy without name, tragic ending)
    - '6': Sacrifice & Redemption (destroy with name, best ending)
    - Legacy: '1a', '1b', 'good', 'bad' (kept for backward compatibility)

    Args:
        con: Console to draw on
        root_console: Root console for rendering
        screen_width: Width of the screen
        screen_height: Height of the screen
        ending_type: Ending code ('1'-'6', '1a'/'1b', 'good'/'bad')
        player_stats: Dict containing player statistics

    Returns:
        str: 'restart' or 'quit' based on player input
    """
    # DEBUG: Log which ending is being shown
    print(f">>> VICTORY SCREEN: Showing ending type: '{ending_type}'")
    import logging
    logging.info(f"=== VICTORY SCREEN: Showing ending type: '{ending_type}' ===")
    # Phase 5: New six endings (primary codes)
    if ending_type == '1':
        return show_ending_1a(con, root_console, screen_width, screen_height, player_stats)
    elif ending_type == '2':
        return show_ending_1b(con, root_console, screen_width, screen_height, player_stats)
    elif ending_type == '3':
        return show_ending_2(con, root_console, screen_width, screen_height, player_stats)
    elif ending_type == '4':
        return show_ending_3(con, root_console, screen_width, screen_height, player_stats)
    elif ending_type == '5':
        return show_ending_4(con, root_console, screen_width, screen_height, player_stats)
    elif ending_type == '6':
        return show_ending_5(con, root_console, screen_width, screen_height, player_stats)
    
    # Backward compatibility with old codes
    elif ending_type == '1a':
        return show_ending_1a(con, root_console, screen_width, screen_height, player_stats)
    elif ending_type == '1b':
        return show_ending_1b(con, root_console, screen_width, screen_height, player_stats)
    elif ending_type == '2_old':
        return show_ending_2(con, root_console, screen_width, screen_height, player_stats)
    elif ending_type == '3_old':
        return show_ending_3(con, root_console, screen_width, screen_height, player_stats)
    elif ending_type == '4_old':
        return show_ending_4(con, root_console, screen_width, screen_height, player_stats)
    elif ending_type == '5_old':
        return show_ending_5(con, root_console, screen_width, screen_height, player_stats)
    
    # Legacy endings (kept for compatibility with very old code)
    elif ending_type == 'good':
        return show_good_ending(con, root_console, screen_width, screen_height, player_stats)
    elif ending_type == 'bad':
        return show_bad_ending(con, root_console, screen_width, screen_height, player_stats)
    
    return 'quit'


# =============================================================================
# PHASE 5: THE SIX ENDINGS
# =============================================================================

def show_ending_1a(con, root_console, screen_width, screen_height, player_stats):
    """Ending 1a: Escape Through Battle (Neutral-Good).
    
    Player kept heart, fought Human Zhyraxion, won.
    """
    endings = _load_endings()
    ending_data = endings['ending_1']
    
    return display_ending(con, root_console, screen_width, screen_height,
                         ending_data['title'], ending_data['story'], 
                         player_stats, COLOR_MAP[ending_data['color']])


def show_ending_1b(con, root_console, screen_width, screen_height, player_stats):
    """Ending 1b: Crimson Collector (Dark Victory).
    
    Player kept heart, used Crimson Ritual to extract both hearts.
    """
    endings = _load_endings()
    ending_data = endings['ending_2']
    
    return display_ending(con, root_console, screen_width, screen_height,
                         ending_data['title'], ending_data['story'], 
                         player_stats, COLOR_MAP[ending_data['color']])


def show_ending_2(con, root_console, screen_width, screen_height, player_stats):
    """Ending 2: Dragon's Bargain (Failure - Trapped).
    
    Player kept heart, accepted transformation offer.
    """
    endings = _load_endings()
    ending_data = endings['ending_3']
    
    return display_ending(con, root_console, screen_width, screen_height,
                         ending_data['title'], ending_data['story'], 
                         player_stats, COLOR_MAP[ending_data['color']])


def show_ending_3(con, root_console, screen_width, screen_height, player_stats):
    """Ending 3: Fool's Freedom (Death).
    
    Player gave heart to Zhyraxion, fought Full Dragon, died (or miracle win).
    """
    endings = _load_endings()
    ending_data = endings['ending_4']
    
    return display_ending(con, root_console, screen_width, screen_height,
                         ending_data['title'], ending_data['story'], 
                         player_stats, COLOR_MAP[ending_data['color']])


def show_ending_4(con, root_console, screen_width, screen_height, player_stats):
    """Ending 4: Mercy & Corruption (Tragic).
    
    Player destroyed heart without speaking true name, fought Grief Dragon.
    """
    endings = _load_endings()
    ending_data = endings['ending_5']
    
    return display_ending(con, root_console, screen_width, screen_height,
                         ending_data['title'], ending_data['story'], 
                         player_stats, COLOR_MAP[ending_data['color']])


def show_ending_5(con, root_console, screen_width, screen_height, player_stats):
    """Ending 5: Sacrifice & Redemption (Best Ending).
    
    Player destroyed heart while speaking Zhyraxion's true name.
    """
    endings = _load_endings()
    ending_data = endings['ending_6']
    
    return display_ending(con, root_console, screen_width, screen_height,
                         ending_data['title'], ending_data['story'], 
                         player_stats, COLOR_MAP[ending_data['color']])


# =============================================================================
# LEGACY ENDINGS (Kept for compatibility)
# =============================================================================

def show_good_ending(con, root_console, screen_width, screen_height, player_stats):
    """Display the good ending (player kept the Amulet and escaped).
    
    Returns:
        str: 'restart' or 'quit'
    """
    endings = _load_endings()
    ending_data = endings['ending_good']
    
    return display_ending(con, root_console, screen_width, screen_height, 
                         ending_data['title'], ending_data['story'], 
                         player_stats, COLOR_MAP[ending_data['color']])


def show_bad_ending(con, root_console, screen_width, screen_height, player_stats):
    """Display the bad ending (player gave away the Amulet).
    
    Returns:
        str: 'restart' or 'quit'
    """
    endings = _load_endings()
    ending_data = endings['ending_bad']
    
    return display_ending(con, root_console, screen_width, screen_height,
                         ending_data['title'], ending_data['story'], 
                         player_stats, COLOR_MAP[ending_data['color']])


def display_ending(con, root_console, screen_width, screen_height,
                   title, story_lines, player_stats, title_color):
    """Display an ending screen with story and statistics.
    
    Args:
        con: Console to draw on
        root_console: Root console
        screen_width: Screen width
        screen_height: Screen height
        title: Title of the ending
        story_lines: List of story text lines
        player_stats: Player statistics dictionary
        title_color: Color for the title
        
    Returns:
        str: 'restart' or 'quit'
    """
    # Calculate menu dimensions
    menu_width = 80
    story_height = len(story_lines) + 4
    stats_height = 12
    total_height = story_height + stats_height
    
    x = screen_width // 2 - menu_width // 2
    y = max(2, screen_height // 2 - total_height // 2)
    
    # Clear console
    tcod.console_set_default_background(con, tcod.black)
    tcod.console_clear(con)
    
    # Draw title
    tcod.console_set_default_foreground(con, title_color)
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
    
    # Draw story
    current_y = 5
    for line in story_lines:
        if line == "":
            current_y += 1
            continue
        
        # Highlight Entity speech
        if line.startswith("\""):
            tcod.console_set_default_foreground(con, tcod.light_yellow)
        # Highlight victory/defeat text
        elif "===" in line:
            tcod.console_set_default_foreground(con, title_color)
        else:
            tcod.console_set_default_foreground(con, tcod.light_gray)
        
        # Center align story text
        tcod.console_print_ex(
            con, menu_width // 2, current_y,
            tcod.BKGND_NONE, tcod.CENTER,
            line
        )
        current_y += 1
    
    # Draw statistics section
    current_y += 2
    tcod.console_set_default_foreground(con, tcod.light_blue)
    tcod.console_print_ex(
        con, menu_width // 2, current_y,
        tcod.BKGND_NONE, tcod.CENTER,
        "=== Your Journey ==="
    )
    current_y += 2
    
    # Display stats
    tcod.console_set_default_foreground(con, tcod.white)
    stats_to_show = [
        f"Deaths: {player_stats.get('deaths', 0)}",
        f"Turns Taken: {player_stats.get('turns', 0)}",
        f"Deepest Level: {player_stats.get('deepest_level', 0)}",
        f"Monsters Slain: {player_stats.get('kills', 0)}",
        f"Final Level: {player_stats.get('final_level', 0)}"
    ]
    
    for stat in stats_to_show:
        tcod.console_print_ex(
            con, menu_width // 2, current_y,
            tcod.BKGND_NONE, tcod.CENTER,
            stat
        )
        current_y += 1
    
    # Draw instructions
    current_y += 2
    tcod.console_set_default_foreground(con, tcod.dark_gray)
    tcod.console_print_ex(
        con, menu_width // 2, current_y,
        tcod.BKGND_NONE, tcod.CENTER,
        "[Press R to restart or ESC to quit]"
    )
    
    # Blit to root
    tcod.console_blit(con, 0, 0, menu_width, total_height, root_console, x, y, 1.0, 0.9)
    tcod.console_flush()
    
    # Wait for input
    while True:
        key = tcod.console_wait_for_keypress(True)
        
        if key.vk == tcod.KEY_ESCAPE:
            return 'quit'
        
        key_char = chr(key.c).lower() if key.c > 0 else ''
        if key_char == 'r':
            return 'restart'

