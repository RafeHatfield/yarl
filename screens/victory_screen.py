"""Victory and failure ending screens.

This module displays the final outcome screens after the player makes
their choice in the Entity confrontation.
"""

import tcod
from typing import Dict, Any


def show_ending_screen(con, root_console, screen_width, screen_height, 
                       ending_type, player_stats):
    """Display the ending screen based on player's choice.
    
    Phase 5: The Five Endings
    - '1a': Escape Through Battle (fight Human Zhyraxion, neutral-good)
    - '1b': Crimson Collector (ritual, dark victory)
    - '2': Dragon's Bargain (transformation trap, failure)
    - '3': Fool's Freedom (give heart, death or miracle)
    - '4': Mercy & Corruption (destroy without name, tragic)
    - '5': Sacrifice & Redemption (destroy with name, best ending)
    - 'good'/'bad': Legacy endings (kept for compatibility)
    
    Args:
        con: Console to draw on
        root_console: Root console for rendering
        screen_width: Width of the screen
        screen_height: Height of the screen
        ending_type: Ending code ('1a', '1b', '2', '3', '4', '5', 'good', 'bad')
        player_stats: Dict containing player statistics
        
    Returns:
        str: 'restart' or 'quit' based on player input
    """
    # Phase 5 endings
    if ending_type == '1a':
        return show_ending_1a(con, root_console, screen_width, screen_height, player_stats)
    elif ending_type == '1b':
        return show_ending_1b(con, root_console, screen_width, screen_height, player_stats)
    elif ending_type == '2':
        return show_ending_2(con, root_console, screen_width, screen_height, player_stats)
    elif ending_type == '3':
        return show_ending_3(con, root_console, screen_width, screen_height, player_stats)
    elif ending_type == '4':
        return show_ending_4(con, root_console, screen_width, screen_height, player_stats)
    elif ending_type == '5':
        return show_ending_5(con, root_console, screen_width, screen_height, player_stats)
    
    # Legacy endings (kept for compatibility)
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
    title = "ESCAPE - Freedom Through Strength"
    
    story = [
        "Zhyraxion falls, defeated.",
        "",
        "\"You... you would condemn me... to stay here... forever?\"",
        "",
        "He collapses, still breathing but broken.",
        "",
        "You grip Aurelyn's Ruby Heart and turn away.",
        "The portal shimmers, offering escape.",
        "",
        "Behind you, Zhyraxion's voice, barely a whisper:",
        "\"Aurelyn... I tried... I'm sorry...\"",
        "",
        "You step through the portal.",
        "",
        "The last thing you hear is his anguished cry,",
        "fading as the portal closes behind you.",
        "",
        "You're free.",
        "",
        "But at what cost?",
        "",
        "=== VICTORY ACHIEVED ==="
    ]
    
    return display_ending(con, root_console, screen_width, screen_height,
                         title, story, player_stats, tcod.amber)


def show_ending_1b(con, root_console, screen_width, screen_height, player_stats):
    """Ending 1b: Crimson Collector (Dark Victory).
    
    Player kept heart, used Crimson Ritual to extract both hearts.
    """
    title = "ASCENSION - The Crimson Collector"
    
    story = [
        "You place Aurelyn's heart on the ritual circle.",
        "",
        "The ancient symbols flare to life.",
        "",
        "Zhyraxion: \"What... what are you doing?\"",
        "",
        "You begin the ritual chant from the codex.",
        "",
        "\"No. NO! You can't—\"",
        "",
        "The ritual binds him, just as it bound Aurelyn.",
        "",
        "His screams echo through the chamber as you",
        "complete what the Crimson Order started.",
        "",
        "Minutes later, you hold TWO ruby hearts,",
        "both pulsing in your hands.",
        "",
        "Immense power flows through you.",
        "",
        "The portal opens—but it's different now.",
        "Darker. Red-tinted.",
        "",
        "You step through, leaving behind the ashes",
        "of two ancient dragons.",
        "",
        "You've become what the ritualists wanted to be.",
        "",
        "=== DARK VICTORY ===",
        "",
        "Dragon Hearts Collected: 2"
    ]
    
    return display_ending(con, root_console, screen_width, screen_height,
                         title, story, player_stats, tcod.dark_crimson)


def show_ending_2(con, root_console, screen_width, screen_height, player_stats):
    """Ending 2: Dragon's Bargain (Failure - Trapped).
    
    Player kept heart, accepted transformation offer.
    """
    title = "BOUND - The Dragon's Bargain"
    
    story = [
        "Zhyraxion smiles.",
        "",
        "\"You're smarter than the others. Why be a puppet",
        "when you could be a DRAGON?\"",
        "",
        "He gestures to the heart.",
        "",
        "\"Touch it. Take the power. We'll BOTH escape.\"",
        "",
        "You reach out... the heart pulses... power floods",
        "through your veins...",
        "",
        "Your form shifts. Scales emerge. Wings unfurl.",
        "",
        "For one glorious moment, you ARE a dragon.",
        "",
        "Then you feel it.",
        "",
        "The binding curse. Transferring. Snapping shut",
        "around YOUR soul instead of his.",
        "",
        "Zhyraxion transforms before your eyes, his true",
        "dragon form restored.",
        "",
        "\"Oh, don't look so betrayed. I offered you EXACTLY",
        "what I promised: dragon transformation. Not MY fault",
        "you didn't read the fine print about the binding curse.\"",
        "",
        "He stretches his wings.",
        "",
        "\"Marvelous view from up here, isn't it? The sky,",
        "the freedom... I'll visit when I'm bored. Might be",
        "a few centuries. You understand, I'm sure.\"",
        "",
        "He flies away, leaving you trapped in the chamber",
        "that held him for so long.",
        "",
        "Forever.",
        "",
        "=== GAME OVER ===",
        "",
        "\"Ta-ta!\""
    ]
    
    return display_ending(con, root_console, screen_width, screen_height,
                         title, story, player_stats, tcod.dark_red)


def show_ending_3(con, root_console, screen_width, screen_height, player_stats):
    """Ending 3: Fool's Freedom (Death).
    
    Player gave heart to Zhyraxion, fought Full Dragon, died (or miracle win).
    """
    title = "CONSUMED - Fool's Freedom"
    
    story = [
        "You hand Aurelyn's Ruby Heart to Zhyraxion.",
        "",
        "\"YES! FINALLY! After all these centuries...\"",
        "",
        "He absorbs the heart, and power erupts from him.",
        "",
        "His human shell SHATTERS.",
        "",
        "What emerges is an ANCIENT DRAGON.",
        "Massive. Terrible. Glorious.",
        "",
        "He spreads his wings and roars.",
        "",
        "You realize your mistake.",
        "",
        "The dragon's claw descends—",
        "",
        "—You are crushed.",
        "",
        "As your vision fades, you see him fly away,",
        "not even acknowledging your existence.",
        "",
        "\"...Finally. Aurelyn, I'm coming.\"",
        "",
        "Your soul joins the Guide's.",
        "Just another failure in the collection.",
        "",
        "Your gear will scatter on the dungeon floor.",
        "Loot for the next poor soul.",
        "",
        "=== YOU DIED ===",
        "",
        "You trusted the dragon. The dragon did not care."
    ]
    
    return display_ending(con, root_console, screen_width, screen_height,
                         title, story, player_stats, tcod.red)


def show_ending_4(con, root_console, screen_width, screen_height, player_stats):
    """Ending 4: Mercy & Corruption (Tragic).
    
    Player destroyed heart without speaking true name, fought Grief Dragon.
    """
    title = "FREEDOM - The Cruelest Mercy"
    
    story = [
        "You raise Aurelyn's Ruby Heart and SHATTER it.",
        "",
        "Golden essence explodes outward.",
        "",
        "Zhyraxion: \"NO! WHAT HAVE YOU—AURELYN!\"",
        "",
        "His scream of anguish is inhuman.",
        "",
        "The binding breaks from the sheer force of his grief.",
        "",
        "His form twists, shifts, transforms.",
        "But it's WRONG. Corrupted. Incomplete.",
        "",
        "What emerges is a GRIEF-MAD dragon,",
        "twisted by centuries of suffering and rage.",
        "",
        "[You fought him. You won.]",
        "",
        "As he falls, his eyes clear for just a moment.",
        "",
        "\"You... destroyed... her heart...\"",
        "",
        "\"The only... thing I had left... of her...\"",
        "",
        "He dies, broken twice over.",
        "",
        "You escape.",
        "",
        "But the cost...",
        "The cost was too high.",
        "",
        "You showed mercy by freeing him from his prison.",
        "But destroyed his last connection to the one he loved.",
        "",
        "Some victories feel like defeat.",
        "",
        "=== TRAGIC VICTORY ==="
    ]
    
    return display_ending(con, root_console, screen_width, screen_height,
                         title, story, player_stats, tcod.grey)


def show_ending_5(con, root_console, screen_width, screen_height, player_stats):
    """Ending 5: Sacrifice & Redemption (Best Ending).
    
    Player destroyed heart while speaking Zhyraxion's true name.
    """
    title = "REDEMPTION - Sacrifice & Compassion"
    
    story = [
        "You raise Aurelyn's Ruby Heart.",
        "",
        "Zhyraxion tenses: \"Don't you DARE—\"",
        "",
        "You speak: \"ZHYRAXION.\"",
        "",
        "His eyes widen.",
        "\"You... you know my name?\"",
        "",
        "The heart shatters—but DIFFERENTLY.",
        "Golden light, not red.",
        "",
        "The curse doesn't just BREAK—it PURIFIES.",
        "The binding dissolves.",
        "",
        "Zhyraxion transforms, but the corruption is GONE.",
        "He's whole again.",
        "",
        "From the shattered heart, a second form emerges:",
        "Aurelyn's spirit, freed at last.",
        "",
        "Zhyraxion: \"Aurelyn? Is it... is it really you?\"",
        "",
        "They circle each other, two dragons reunited.",
        "",
        "Zhyraxion looks at you.",
        "",
        "\"You... you knew what I was. What I'd done.",
        "And you still... spoke my name...\"",
        "",
        "Your soul contract SHATTERS.",
        "",
        "The Guide appears beside you, corporeal again.",
        "Guide: \"Huh. You actually did it. Freed us all.\"",
        "",
        "The portal opens—but this time it's GOLDEN.",
        "",
        "Zhyraxion and Aurelyn fade into light,",
        "together at last.",
        "",
        "Where they go, you don't know.",
        "But it's right.",
        "",
        "Guide: \"Come on, kid. Let's get out of here.\"",
        "",
        "You step through the portal.",
        "Side by side with the ghost who warned you.",
        "",
        "Both of you finally, truly free.",
        "",
        "=== TRUE VICTORY ===",
        "",
        "Everyone wins."
    ]
    
    return display_ending(con, root_console, screen_width, screen_height,
                         title, story, player_stats, tcod.gold)


# =============================================================================
# LEGACY ENDINGS (Kept for compatibility)
# =============================================================================

def show_good_ending(con, root_console, screen_width, screen_height, player_stats):
    """Display the good ending (player kept the Amulet and escaped).
    
    Returns:
        str: 'restart' or 'quit'
    """
    title = "VICTORY - You Are Free"
    
    story = [
        "You clutch the Amulet tightly and channel its power.",
        "",
        "\"Oh. OH. You think— Wait. No. You COULDN'T.\"",
        "",
        "The Entity's eyes widen in horror as golden light",
        "erupts from the Amulet, severing the binding on your soul.",
        "",
        "\"Im...impossible. I... HOW—\"",
        "",
        "The chains dissolve. For the first time in an eternity,",
        "your soul is truly your own.",
        "",
        "As you turn to leave, you glimpse the dungeon floors above—",
        "centuries of scattered swords, broken armor, abandoned gear.",
        "The accumulated failures of those who came before.",
        "",
        "But not you.",
        "",
        "The Entity remains trapped in its temporal prison,",
        "unable to stop you as you walk through a rift back to reality.",
        "",
        "Behind you, you hear its fading roar of impotent rage.",
        "",
        "You are free.",
        "",
        "=== YOU HAVE WON ==="
    ]
    
    return display_ending(con, root_console, screen_width, screen_height, 
                         title, story, player_stats, tcod.light_green)


def show_bad_ending(con, root_console, screen_width, screen_height, player_stats):
    """Display the bad ending (player gave away the Amulet).
    
    Returns:
        str: 'restart' or 'quit'
    """
    title = "YOU FAILED - Bound for Eternity"
    
    story = [
        "You hand the Amulet to the Entity.",
        "",
        "\"Ah. There we are. I knew you'd see sense eventually.\"",
        "",
        "The Entity's form ripples and expands, ancient draconic",
        "power flooding back into its body. Scales emerge, wings unfurl.",
        "",
        "\"Your service has been... adequate. As promised, you are free.\"",
        "",
        "Hope surges in your chest—",
        "",
        "\"Oh, one more thing...\"",
        "",
        "The Entity smiles with far too many teeth.",
        "",
        "\"Thank you for taking my place.\"",
        "",
        "Reality TWISTS. The temporal prison that held the Entity",
        "snaps shut around YOU instead. Ancient binding magic",
        "floods your being, and you understand with horror:",
        "",
        "Only a dragon can replace a dragon.",
        "Only a bound soul can free a bound soul.",
        "",
        "The Entity—now a magnificent dragon once more—spreads its wings.",
        "",
        "\"Better luck next time. Oh wait, there won't be a next time.\"",
        "",
        "Its laughter echoes as it flies free, leaving you",
        "trapped in the prison outside time, just as it was.",
        "",
        "As your consciousness fades into the binding, you realize:",
        "All that gear scattered through the dungeon? Your sword will",
        "join it soon. Loot for the next poor soul in the cycle.",
        "",
        "Forever.",
        "",
        "=== GAME OVER ==="
    ]
    
    return display_ending(con, root_console, screen_width, screen_height,
                         title, story, player_stats, tcod.dark_red)


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

