"""
Fool's Freedom (Ending 4) - Pre-Battle Cutscene

Dramatic cutscene showing Zhyraxion's reaction to receiving the Ruby Heart.
The dragon displays his personality at its peak - overwhelmed joy followed
by cruel mockery of the player's foolish choice.

This is the only ending where the player simply GIVES the heart to Zhyraxion
without any plan, condition, or knowledge. It's the "bad" ending that shows
the dragon's true nature before the hopeless boss fight begins.

Dialogue is loaded from config/cutscenes.yaml for easy editing and internationalization.
"""

import tcod
import tcod.constants
import yaml
from pathlib import Path
from game_states import GameStates


def _load_cutscene_dialogue():
    """Load cutscene dialogue from YAML file.
    
    Returns:
        dict: Cutscene dialogue data
    """
    endings_file = Path("config/endings.yaml")
    with open(endings_file, 'r') as f:
        data = yaml.safe_load(f)
    return data['cutscenes']['fool_freedom']


def show_fool_freedom_cutscene(con, root_console, screen_width, screen_height):
    """Display the Fool's Freedom cutscene before the boss fight.
    
    Shows Zhyraxion's reaction to receiving the heart - overwhelming joy
    transforming into cruel mockery. This sets up the hopeless boss fight.
    
    Dialogue is loaded from config/cutscenes.yaml for easy editing.
    
    Args:
        con: Console to draw on
        root_console: Root console for rendering
        screen_width: Width of the screen
        screen_height: Height of the screen
        
    Returns:
        tuple: (continue, new_state) - continue=True to proceed to fight,
               False to exit, new_state is GameStates.PLAYERS_TURN to start fight
    """
    # Load dialogue from YAML
    dialogue = _load_cutscene_dialogue()
    
    # Dramatic color scheme - starts hopeful (gold), transitions to ominous (deep red)
    color_joy = tcod.gold
    color_mockery = tcod.dark_red
    
    title = dialogue['title']
    
    # Stage 1: Overwhelming gratitude (deceptive)
    cutscene_text = dialogue['stage_1']
    
    # Draw the first stage
    con.clear()
    
    # Title at top
    title_x = (screen_width - len(title)) // 2
    tcod.console_print(con, title_x, 2, title)
    
    # Story text
    y = 5
    for line in cutscene_text:
        if line.startswith("[Press"):
            # Instruction in white at bottom
            tcod.console_set_default_foreground(con, tcod.white)
            tcod.console_print(con, (screen_width - len(line)) // 2, screen_height - 3, line)
        else:
            # Story text in gold (hopeful color)
            tcod.console_set_default_foreground(con, color_joy)
            x = (screen_width - len(line)) // 2
            tcod.console_print(con, x, y, line)
            y += 1
    
    tcod.console_blit(con, 0, 0, screen_width, screen_height, root_console, 0, 0)
    tcod.console_flush()
    
    # Wait for space key
    while True:
        for event in tcod.event.wait():
            if event.type == "QUIT":
                return False, GameStates.PLAYERS_TURN
            elif event.type == "KEYDOWN":
                if event.sym == tcod.event.K_SPACE:
                    break
                elif event.sym == tcod.event.K_ESCAPE:
                    return False, GameStates.PLAYERS_TURN
        else:
            continue
        break
    
    # Stage 2: The transformation - joy becomes cruelty
    cutscene_text_2 = dialogue['stage_2']
    
    # Draw stage 2
    con.clear()
    
    # Title
    tcod.console_print(con, title_x, 2, title)
    
    y = 5
    for line in cutscene_text_2:
        if line.startswith("[Press"):
            tcod.console_set_default_foreground(con, tcod.white)
            tcod.console_print(con, (screen_width - len(line)) // 2, screen_height - 3, line)
        else:
            # Transition to darker, ominous color
            tcod.console_set_default_foreground(con, color_mockery)
            x = (screen_width - len(line)) // 2
            tcod.console_print(con, x, y, line)
            y += 1
    
    tcod.console_blit(con, 0, 0, screen_width, screen_height, root_console, 0, 0)
    tcod.console_flush()
    
    # Wait for space key
    while True:
        for event in tcod.event.wait():
            if event.type == "QUIT":
                return False, GameStates.PLAYERS_TURN
            elif event.type == "KEYDOWN":
                if event.sym == tcod.event.K_SPACE:
                    break
                elif event.sym == tcod.event.K_ESCAPE:
                    return False, GameStates.PLAYERS_TURN
        else:
            continue
        break
    
    # Stage 3: Final mockery and threat (Alan Rickman sardonic perfection)
    cutscene_text_3 = dialogue['stage_3']
    
    # Draw stage 3
    con.clear()
    
    # Title
    tcod.console_print(con, title_x, 2, title)
    
    y = 4
    for line in cutscene_text_3:
        if line.startswith("[Press"):
            tcod.console_set_default_foreground(con, tcod.red)
            tcod.console_print(con, (screen_width - len(line)) // 2, screen_height - 3, line)
        else:
            # Deep red - threatening and cruel
            tcod.console_set_default_foreground(con, tcod.dark_red)
            x = (screen_width - len(line)) // 2
            tcod.console_print(con, x, y, line)
            y += 1
    
    tcod.console_blit(con, 0, 0, screen_width, screen_height, root_console, 0, 0)
    tcod.console_flush()
    
    # Wait for space key to begin fight
    while True:
        for event in tcod.event.wait():
            if event.type == "QUIT":
                return False, GameStates.PLAYERS_TURN
            elif event.type == "KEYDOWN":
                if event.sym == tcod.event.K_SPACE:
                    return True, GameStates.PLAYERS_TURN  # Continue to boss fight
                elif event.sym == tcod.event.K_ESCAPE:
                    return False, GameStates.PLAYERS_TURN
        else:
            continue
        break
    
    return True, GameStates.PLAYERS_TURN

