"""Menu and UI screen functions.

This module provides functions for displaying various game menus
including inventory, main menu, level up, character screen, and
message boxes. All menus are rendered as centered overlays.
"""

import tcod as libtcod
from tcod import libtcodpy


def menu(con, header, options, width, screen_width, screen_height):
    """Display a menu with options for the player to choose from.

    Creates a centered menu window with a header and lettered options.
    Supports up to 26 options (a-z).

    Args:
        con: The console to draw on
        header (str): Header text for the menu
        options (list): List of option strings
        width (int): Width of the menu window
        screen_width (int): Width of the screen for centering
        screen_height (int): Height of the screen for centering

    Raises:
        ValueError: If more than 26 options are provided
    """
    if len(options) > 26:
        raise ValueError("Cannot have a menu with more than 26 options.")

    # calculate total height for the header (after auto-wrap) and one line per option
    header_height = libtcodpy.console_get_height_rect(
        con, 0, 0, width, screen_height, header
    )
    height = len(options) + header_height

    # create an off-screen console that represents the menu's window
    window = libtcodpy.console_new(width, height)

    # print the header, with auto-wrap
    libtcodpy.console_set_default_foreground(window, (255, 255, 255))
    libtcodpy.console_print_rect_ex(
        window, 0, 0, width, height, libtcodpy.BKGND_NONE, libtcodpy.LEFT, header
    )

    # print all the options
    y = header_height
    letter_index = ord("a")
    for option_text in options:
        text = "(" + chr(letter_index) + ") " + option_text
        libtcodpy.console_print_ex(window, 0, y, libtcodpy.BKGND_NONE, libtcodpy.LEFT, text)
        y += 1
        letter_index += 1

    # blit the contents of "window" to the root console
    x = int(screen_width / 2 - width / 2)
    y = int(screen_height / 2 - height / 2)
    libtcodpy.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)


def inventory_menu(con, header, player, inventory_width, screen_width, screen_height):
    """Display the player's inventory as a selectable menu.

    Shows each item in the inventory with equipment status indicators.

    Args:
        con: Console to draw on
        header (str): Menu header text
        player (Entity): Player entity with inventory component
        inventory_width (int): Width of the inventory menu
        screen_width (int): Screen width for centering
        screen_height (int): Screen height for centering
    """
    # show a menu with each item of the inventory as an option
    if len(player.inventory.items) == 0:
        options = ["Inventory is empty."]
    else:
        options = []

        for item in player.inventory.items:
            display_name = item.get_display_name()
            if player.equipment.main_hand == item:
                options.append("{0} (on main hand)".format(display_name))
            elif player.equipment.off_hand == item:
                options.append("{0} (on off hand)".format(display_name))
            else:
                options.append(display_name)

    menu(con, header, options, inventory_width, screen_width, screen_height)


def main_menu(con, background_image, screen_width, screen_height):
    """Display the main menu screen.

    Args:
        con: Console to draw on
        background_image: Background image for the menu
        screen_width (int): Screen width
        screen_height (int): Screen height
    """
    # Use deprecated method but warnings are suppressed in engine.py
    libtcodpy.image_blit_2x(background_image, 0, 0, 0)

    # Use RGB tuple instead of deprecated color constant
    libtcodpy.console_set_default_foreground(0, (255, 255, 63))
    libtcodpy.console_print_ex(
        0,
        int(screen_width / 2),
        int(screen_height / 2) - 4,
        libtcodpy.BKGND_NONE,
        libtcodpy.CENTER,
        "CATACOMBS OF YARL",
    )
    libtcodpy.console_print_ex(
        0,
        int(screen_width / 2),
        int(screen_height - 2),
        libtcodpy.BKGND_NONE,
        libtcodpy.CENTER,
        "By Rastaphibian",
    )

    menu(
        con,
        "",
        ["Play a new game", "Continue last game", "Quit"],
        24,
        screen_width,
        screen_height,
    )


def level_up_menu(con, header, player, menu_width, screen_width, screen_height):
    """Display the level up menu for stat selection.

    Args:
        con: Console to draw on
        header (str): Menu header text
        player (Entity): Player entity with level component
        menu_width (int): Width of the menu
        screen_width (int): Screen width for centering
        screen_height (int): Screen height for centering
    """
    options = [
        "Constitution (+20 HP, from {0})".format(player.fighter.max_hp),
        "Strength (+1 attack, from {0})".format(player.fighter.power),
        "Agility (+1 defense, from {0})".format(player.fighter.defense),
    ]

    menu(con, header, options, menu_width, screen_width, screen_height)


def message_box(con, header, width, screen_width, screen_height):
    """Display a simple message box.

    Args:
        con: Console to draw on
        header (str): Message to display
        width (int): Width of the message box
        screen_width (int): Screen width for centering
        screen_height (int): Screen height for centering
    """
    menu(con, header, [], width, screen_width, screen_height)


def character_screen(
    player, character_screen_width, character_screen_height, screen_width, screen_height
):
    """Display the character information screen.

    Shows player stats, level, and equipment information.

    Args:
        player (Entity): Player entity with stats
        character_screen_width (int): Width of the character screen
        character_screen_height (int): Height of the character screen
        screen_width (int): Screen width for centering
        screen_height (int): Screen height for centering

    Returns:
        Console: The character screen console
    """
    window = libtcodpy.console_new(character_screen_width, character_screen_height)

    libtcodpy.console_set_default_foreground(window, (255, 255, 255))

    libtcodpy.console_print_rect_ex(
        window,
        0,
        1,
        character_screen_width,
        character_screen_height,
        libtcodpy.BKGND_NONE,
        libtcodpy.LEFT,
        "Character Information",
    )
    libtcodpy.console_print_rect_ex(
        window,
        0,
        2,
        character_screen_width,
        character_screen_height,
        libtcodpy.BKGND_NONE,
        libtcodpy.LEFT,
        "Level: {0}".format(player.level.current_level),
    )
    libtcodpy.console_print_rect_ex(
        window,
        0,
        3,
        character_screen_width,
        character_screen_height,
        libtcodpy.BKGND_NONE,
        libtcodpy.LEFT,
        "Experience: {0}".format(player.level.current_xp),
    )
    libtcodpy.console_print_rect_ex(
        window,
        0,
        4,
        character_screen_width,
        character_screen_height,
        libtcodpy.BKGND_NONE,
        libtcodpy.LEFT,
        "Experience to Level: {0}".format(player.level.experience_to_next_level),
    )
    libtcodpy.console_print_rect_ex(
        window,
        0,
        6,
        character_screen_width,
        character_screen_height,
        libtcodpy.BKGND_NONE,
        libtcodpy.LEFT,
        "Maximum HP: {0}".format(player.fighter.max_hp),
    )
    # Get attack info with weapon damage range
    attack_text = _get_attack_display_text(player)
    libtcodpy.console_print_rect_ex(
        window,
        0,
        7,
        character_screen_width,
        character_screen_height,
        libtcodpy.BKGND_NONE,
        libtcodpy.LEFT,
        attack_text,
    )
    
    # Get defense info with armor defense range
    defense_text = _get_defense_display_text(player)
    libtcodpy.console_print_rect_ex(
        window,
        0,
        8,
        character_screen_width,
        character_screen_height,
        libtcodpy.BKGND_NONE,
        libtcodpy.LEFT,
        defense_text,
    )

    x = screen_width // 2 - character_screen_width // 2
    y = screen_height // 2 - character_screen_height // 2
    libtcodpy.console_blit(
        window, 0, 0, character_screen_width, character_screen_height, 0, x, y, 1.0, 0.7
    )


def _get_attack_display_text(player):
    """Get attack display text with weapon damage range and power bonuses.
    
    Args:
        player (Entity): Player entity with fighter and equipment components
        
    Returns:
        str: Attack display text showing physical damage + magical power
    """
    # Get base power (should be 0 for natural, bonuses from equipment/magic)
    base_power = player.fighter.base_power
    
    # Check for equipped weapon with damage range
    if (hasattr(player, 'equipment') and player.equipment and
        player.equipment.main_hand and 
        player.equipment.main_hand.equippable):
        
        weapon = player.equipment.main_hand
        equippable = weapon.equippable
        
        # Get weapon damage range
        if hasattr(equippable, 'damage_min') and hasattr(equippable, 'damage_max'):
            if (equippable.damage_min is not None and equippable.damage_max is not None and
                equippable.damage_max > 0):
                weapon_range = f"{equippable.damage_min}-{equippable.damage_max}"
                
                # Get power bonus from weapon
                power_bonus = getattr(equippable, 'power_bonus', 0)
                total_power = base_power + power_bonus
                
                if total_power > 0:
                    total_min = equippable.damage_min + total_power
                    total_max = equippable.damage_max + total_power
                    return f"Attack: {weapon_range} + {total_power} power = {total_min}-{total_max}"
                else:
                    return f"Attack: {weapon_range} (weapon damage)"
        
        # Fallback to power bonus only if no damage range
        power_bonus = getattr(equippable, 'power_bonus', 0)
        if power_bonus > 0:
            total_power = base_power + power_bonus
            return f"Attack: {total_power} power"
    
    # No weapon - show natural damage + any base power
    if hasattr(player.fighter, 'damage_min') and hasattr(player.fighter, 'damage_max'):
        if (player.fighter.damage_min is not None and player.fighter.damage_max is not None and
            player.fighter.damage_max > 0):
            natural_range = f"{player.fighter.damage_min}-{player.fighter.damage_max}"
            
            if base_power > 0:
                total_min = player.fighter.damage_min + base_power
                total_max = player.fighter.damage_max + base_power
                return f"Attack: {natural_range} + {base_power} power = {total_min}-{total_max}"
            else:
                return f"Attack: {natural_range} (natural)"
    
    # Fallback to just power
    return f"Attack: {base_power} power"


def _get_defense_display_text(player):
    """Get defense display text with armor defense range.
    
    Args:
        player (Entity): Player entity with fighter and equipment components
        
    Returns:
        str: Defense display text with armor defense range if applicable
    """
    # Get base defense without equipment bonuses
    base_defense = player.fighter.base_defense
    
    # Check for equipped armor with defense range
    if (hasattr(player, 'equipment') and player.equipment and
        player.equipment.off_hand and 
        player.equipment.off_hand.equippable):
        
        armor = player.equipment.off_hand
        equippable = armor.equippable
        
        # If armor has meaningful defense range, show it
        if hasattr(equippable, 'defense_min') and hasattr(equippable, 'defense_max'):
            if (equippable.defense_min is not None and equippable.defense_max is not None and
                equippable.defense_max > 0):
                armor_range = f"{equippable.defense_min}-{equippable.defense_max}"
                total_min = base_defense + equippable.defense_min
                total_max = base_defense + equippable.defense_max
                return f"Defense: {base_defense} + {armor_range} = {total_min}-{total_max}"
        
        # Fallback to defense bonus if no defense range
        defense_bonus = getattr(equippable, 'defense_bonus', 0)
        if defense_bonus > 0:
            total_defense = base_defense + defense_bonus
            return f"Defense: {base_defense} + {defense_bonus} = {total_defense}"
    
    # No armor or no bonus
    return f"Defense: {base_defense}"
