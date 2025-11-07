"""
Fool's Freedom (Ending 4) - Pre-Battle Cutscene

Dramatic cutscene showing Zhyraxion's reaction to receiving the Ruby Heart.
The dragon displays his personality at its peak - overwhelmed joy followed
by cruel mockery of the player's foolish choice.

This is the only ending where the player simply GIVES the heart to Zhyraxion
without any plan, condition, or knowledge. It's the "bad" ending that shows
the dragon's true nature before the hopeless boss fight begins.
"""

import tcod
import tcod.constants
from game_states import GameStates


def show_fool_freedom_cutscene(con, root_console, screen_width, screen_height):
    """Display the Fool's Freedom cutscene before the boss fight.
    
    Shows Zhyraxion's reaction to receiving the heart - overwhelming joy
    transforming into cruel mockery. This sets up the hopeless boss fight.
    
    Args:
        con: Console to draw on
        root_console: Root console for rendering
        screen_width: Width of the screen
        screen_height: Height of the screen
        
    Returns:
        tuple: (continue, new_state) - continue=True to proceed to fight,
               False to exit, new_state is GameStates.PLAYERS_TURN to start fight
    """
    # Dramatic color scheme - starts hopeful (gold), transitions to ominous (deep red)
    color_joy = tcod.gold
    color_mockery = tcod.dark_red
    
    title = "Fool's Freedom"
    
    # Multi-stage cutscene showing Zhyraxion's personality
    cutscene_text = [
        # Stage 1: Overwhelming gratitude (deceptive)
        "You step forward and extend the Ruby Heart toward Zhyraxion.",
        "",
        "His eyes WIDEN. His breath catches.",
        "",
        "\"You... you're GIVING it to me? Freely?\"",
        "",
        "He reaches out with trembling hands, reverently taking the heart.",
        "",
        "For a moment, you see genuine emotion in those ancient eyes.",
        "Centuries of grief. Desperation. Longing.",
        "",
        "\"After so long... after so many failures...\"",
        "",
        "His voice breaks.",
        "",
        "\"You actually... you actually did it. Aurelyn... I can finally—\"",
        "",
        "",
        "[Press SPACE to continue]"
    ]
    
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
    cutscene_text_2 = [
        "He absorbs the heart. Power floods through him.",
        "",
        "His form SHIFTS. The human facade cracks and falls away.",
        "",
        "What stands before you is NO LONGER HUMAN.",
        "",
        "An ANCIENT DRAGON. Massive. Overwhelming. Terrible.",
        "",
        "He spreads his wings and the chamber trembles.",
        "",
        "Then... he starts to LAUGH.",
        "",
        "\"Oh... oh this is RICH.\"",
        "",
        "\"You just... HANDED it to me. No bargain. No ritual.\"",
        "\"No clever plan. You just... GAVE it.\"",
        "",
        "The laugh grows crueler.",
        "",
        "",
        "[Press SPACE to continue]"
    ]
    
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
    
    # Stage 3: Final mockery and threat
    cutscene_text_3 = [
        "\"Did you think I'd be GRATEFUL? Did you think I'd let you GO?\"",
        "",
        "\"You're like all the others. Desperate. Naive. WEAK.\"",
        "",
        "\"The Ghost Guide tried to warn you, didn't he?\"",
        "\"He tried SO HARD. Poor bastard.\"",
        "",
        "\"But you... you thought you could trust a DRAGON.\"",
        "\"A dragon who's been ALONE for CENTURIES.\"",
        "\"A dragon with NOTHING LEFT TO LOSE.\"",
        "",
        "He looms over you, eyes blazing.",
        "",
        "\"I don't need you anymore. I have what I came for.\"",
        "",
        "\"But I can't let you leave. You've seen too much.\"",
        "\"You know too much. And honestly?\"",
        "",
        "His voice drops to a whisper.",
        "",
        "\"I'm BORED. And you look... entertaining.\"",
        "",
        "",
        "[Press SPACE to begin the fight]"
    ]
    
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

