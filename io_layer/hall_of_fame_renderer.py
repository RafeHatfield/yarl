"""Renderer for Hall of Fame screen (IO-layer only)."""

import tcod

from systems.hall_of_fame import HallOfFame


def display_hall_of_fame(con, root_console, screen_width, screen_height) -> None:
    """Display the Hall of Fame screen using libtcod consoles."""

    hall = HallOfFame()
    recent = hall.get_recent_victories(10)
    stats = hall.get_statistics()

    menu_width = 70
    menu_height = 40
    x = screen_width // 2 - menu_width // 2
    y = screen_height // 2 - menu_height // 2

    # Clear console
    tcod.console_set_default_background(con, tcod.black)
    tcod.console_clear(con)

    # Title
    tcod.console_set_default_foreground(con, tcod.gold)
    tcod.console_print_ex(
        con, menu_width // 2, 2,
        tcod.BKGND_NONE, tcod.CENTER,
        "=== HALL OF FAME ==="
    )

    current_y = 4

    # Statistics
    tcod.console_set_default_foreground(con, tcod.light_blue)
    tcod.console_print(con, 3, current_y, "Overall Statistics:")
    current_y += 1

    tcod.console_set_default_foreground(con, tcod.white)
    tcod.console_print(con, 5, current_y, f"Total Victories: {stats['total_victories']}")
    current_y += 1
    tcod.console_print(con, 5, current_y, f"Good Endings: {stats['good_endings']}")
    current_y += 1
    tcod.console_print(con, 5, current_y, f"Bad Endings: {stats['bad_endings']}")
    current_y += 3

    # Recent victories
    if recent:
        tcod.console_set_default_foreground(con, tcod.light_blue)
        tcod.console_print(con, 3, current_y, "Recent Victories:")
        current_y += 2

        tcod.console_set_default_foreground(con, tcod.dark_gray)
        tcod.console_print(con, 3, current_y, "Date")
        tcod.console_print(con, 23, current_y, "Character")
        tcod.console_print(con, 38, current_y, "Ending")
        tcod.console_print(con, 48, current_y, "Turns")
        tcod.console_print(con, 58, current_y, "Deaths")
        current_y += 1

        tcod.console_set_default_foreground(con, tcod.white)
        for entry in recent[:10]:
            date_str = entry.get('date', 'Unknown')[:16]  # Trim seconds
            name = entry.get('character_name', 'Unknown')[:12]  # Limit length
            ending = entry.get('ending', 'unknown').title()
            turns = entry.get('turns', 0)
            deaths = entry.get('deaths', 0)

            # Color code by ending type
            if ending.lower() == 'good':
                tcod.console_set_default_foreground(con, tcod.light_green)
            else:
                tcod.console_set_default_foreground(con, tcod.light_red)

            tcod.console_print(con, 3, current_y, date_str)
            tcod.console_print(con, 23, current_y, name)
            tcod.console_print(con, 38, current_y, ending)
            tcod.console_print(con, 48, current_y, str(turns))
            tcod.console_print(con, 58, current_y, str(deaths))
            current_y += 1
    else:
        tcod.console_set_default_foreground(con, tcod.dark_gray)
        tcod.console_print(con, 3, current_y, "No victories yet. Be the first!")
        current_y += 1

    # Instructions
    current_y = menu_height - 3
    tcod.console_set_default_foreground(con, tcod.dark_gray)
    tcod.console_print_ex(
        con, menu_width // 2, current_y,
        tcod.BKGND_NONE, tcod.CENTER,
        "[Press any key to return]"
    )

    # Blit and wait
    tcod.console_blit(con, 0, 0, menu_width, menu_height, root_console, x, y, 1.0, 0.9)
    tcod.console_flush()

    tcod.console_wait_for_keypress(True)


