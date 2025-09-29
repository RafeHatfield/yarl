"""Menu and UI screen functions.

This module provides functions for displaying various game menus
including inventory, main menu, level up, character screen, and
message boxes. All menus are rendered as centered overlays.
"""

import tcod as libtcod


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
    header_height = libtcod.console_get_height_rect(
        con, 0, 0, width, screen_height, header
    )
    height = len(options) + header_height

    # create an off-screen console that represents the menu's window
    window = libtcod.console_new(width, height)

    # print the header, with auto-wrap
    libtcod.console_set_default_foreground(window, (255, 255, 255))
    libtcod.console_print_rect_ex(
        window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header
    )

    # print all the options
    y = header_height
    letter_index = ord("a")
    for option_text in options:
        text = "(" + chr(letter_index) + ") " + option_text
        libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
        y += 1
        letter_index += 1

    # blit the contents of "window" to the root console
    x = int(screen_width / 2 - width / 2)
    y = int(screen_height / 2 - height / 2)
    libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)


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
    libtcod.image_blit_2x(background_image, 0, 0, 0)

    libtcod.console_set_default_foreground(0, libtcod.light_yellow)
    libtcod.console_print_ex(
        0,
        int(screen_width / 2),
        int(screen_height / 2) - 4,
        libtcod.BKGND_NONE,
        libtcod.CENTER,
        "CATACOMBS OF YARL",
    )
    libtcod.console_print_ex(
        0,
        int(screen_width / 2),
        int(screen_height - 2),
        libtcod.BKGND_NONE,
        libtcod.CENTER,
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
    window = libtcod.console_new(character_screen_width, character_screen_height)

    libtcod.console_set_default_foreground(window, (255, 255, 255))

    libtcod.console_print_rect_ex(
        window,
        0,
        1,
        character_screen_width,
        character_screen_height,
        libtcod.BKGND_NONE,
        libtcod.LEFT,
        "Character Information",
    )
    libtcod.console_print_rect_ex(
        window,
        0,
        2,
        character_screen_width,
        character_screen_height,
        libtcod.BKGND_NONE,
        libtcod.LEFT,
        "Level: {0}".format(player.level.current_level),
    )
    libtcod.console_print_rect_ex(
        window,
        0,
        3,
        character_screen_width,
        character_screen_height,
        libtcod.BKGND_NONE,
        libtcod.LEFT,
        "Experience: {0}".format(player.level.current_xp),
    )
    libtcod.console_print_rect_ex(
        window,
        0,
        4,
        character_screen_width,
        character_screen_height,
        libtcod.BKGND_NONE,
        libtcod.LEFT,
        "Experience to Level: {0}".format(player.level.experience_to_next_level),
    )
    libtcod.console_print_rect_ex(
        window,
        0,
        6,
        character_screen_width,
        character_screen_height,
        libtcod.BKGND_NONE,
        libtcod.LEFT,
        "Maximum HP: {0}".format(player.fighter.max_hp),
    )
    libtcod.console_print_rect_ex(
        window,
        0,
        7,
        character_screen_width,
        character_screen_height,
        libtcod.BKGND_NONE,
        libtcod.LEFT,
        "Attack: {0}".format(player.fighter.power),
    )
    libtcod.console_print_rect_ex(
        window,
        0,
        8,
        character_screen_width,
        character_screen_height,
        libtcod.BKGND_NONE,
        libtcod.LEFT,
        "Defense: {0}".format(player.fighter.defense),
    )

    x = screen_width // 2 - character_screen_width // 2
    y = screen_height // 2 - character_screen_height // 2
    libtcod.console_blit(
        window, 0, 0, character_screen_width, character_screen_height, 0, x, y, 1.0, 0.7
    )
