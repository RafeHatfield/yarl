"""
Grief & Rage (Ending 5) - Pre-Battle Cutscene

Dramatic cutscene showing Zhyraxion's reaction to the heart being destroyed
without his true name being spoken. His grief transforms into apocalyptic rage.

This cutscene shows Alan Rickman at his most intense - raw grief transforming
into murderous fury. The player's mercy becomes cruelty.

Dialogue is loaded from config/endings.yaml for easy editing and internationalization.
"""

import tcod
import tcod.constants
import yaml
from game_states import GameStates
from utils.resource_paths import get_resource_path


def _load_cutscene_dialogue():
    """Load cutscene dialogue from YAML file.
    
    Returns:
        dict: Cutscene dialogue data
    """
    endings_file = get_resource_path("config/endings.yaml")
    with open(endings_file, 'r') as f:
        data = yaml.safe_load(f)
    return data['cutscenes']['grief_rage']


def show_grief_rage_cutscene(con, root_console, screen_width, screen_height):
    """Display the Grief & Rage cutscene before the Grief Dragon boss fight.
    
    Shows Zhyraxion's transformation from desperate pleading to grief-mad rage
    after the player destroys Aurelyn's heart without speaking his true name.
    
    Dialogue is loaded from config/endings.yaml for easy editing.
    
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
    
    # Clear the console
    con.clear()
    
    # Title from YAML
    title = dialogue['title']
    title_x = (screen_width - len(title)) // 2
    
    # Color: Dark red for grief and rage
    color_grief = tcod.dark_red
    
    # Single-stage cutscene (destruction and transformation)
    cutscene_text = dialogue['stage_1']
    
    # Draw the cutscene
    con.clear()
    
    # Title at top
    tcod.console_print(con, title_x, 2, title)
    
    # Story text
    y = 5
    for line in cutscene_text:
        if line.startswith("[Press"):
            # Instruction in white at bottom
            tcod.console_set_default_foreground(con, tcod.white)
            tcod.console_print(con, (screen_width - len(line)) // 2, screen_height - 3, line)
        else:
            # Story text in dark red (grief and rage)
            tcod.console_set_default_foreground(con, color_grief)
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
                    return True, GameStates.PLAYERS_TURN  # Continue to boss fight
                elif event.sym == tcod.event.K_ESCAPE:
                    return False, GameStates.PLAYERS_TURN
        else:
            continue
        break
    
    return True, GameStates.PLAYERS_TURN

