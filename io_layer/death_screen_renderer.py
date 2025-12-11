"""IO-layer renderer for the death screen."""

import tcod.libtcodpy as libtcodpy

from components.component_registry import ComponentType


def render_death_screen(con, player, screen_width, screen_height, entity_quote=None, run_metrics=None):
    """Render the death screen with statistics and restart options."""
    # Clear the console with a dark overlay
    libtcodpy.console_set_default_background(con, libtcodpy.black)
    libtcodpy.console_clear(con)

    stats = player.get_component_optional(ComponentType.STATISTICS)

    title = "YOU DIED"
    title_x = screen_width // 2 - len(title) // 2
    libtcodpy.console_set_default_foreground(con, libtcodpy.Color(255, 50, 50))
    libtcodpy.console_print_ex(con, title_x, 3, libtcodpy.BKGND_NONE, libtcodpy.LEFT, title)

    line = "=" * (len(title) + 4)
    libtcodpy.console_set_default_foreground(con, libtcodpy.Color(150, 50, 50))
    libtcodpy.console_print_ex(con, title_x - 2, 4, libtcodpy.BKGND_NONE, libtcodpy.LEFT, line)

    y = 6
    if stats and entity_quote:
        max_line_length = 50
        words = entity_quote.split()
        lines = []
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 <= max_line_length:
                current_line += word + " "
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())

        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(200, 200, 150))
        for line in lines:
            quote_x = screen_width // 2 - len(line) // 2
            libtcodpy.console_print_ex(con, quote_x, y, libtcodpy.BKGND_NONE, libtcodpy.LEFT, line)
            y += 1

        y += 1

    if stats:
        y += 1

        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(200, 200, 200))
        libtcodpy.console_print_ex(con, screen_width // 2 - 10, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    "=== RUN STATISTICS ===")
        y += 2

        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(255, 200, 100))
        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    "COMBAT")
        y += 1

        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(200, 200, 200))
        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Turns survived: {stats.turns_survived}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Monsters killed: {stats.monsters_killed}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Damage dealt: {stats.damage_dealt}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Damage taken: {stats.damage_taken}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Critical hits: {stats.critical_hits}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Times stunned: {stats.times_stunned}")
        y += 2

        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(180, 180, 180))
        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    "NON-COMBAT")
        y += 1

        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(200, 200, 200))
        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Floors descended: {stats.floors_descended}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Items picked up: {stats.items_picked_up}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Potions drunk: {stats.potions_drunk}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Scrolls read: {stats.scrolls_read}")
        y += 2

        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(150, 150, 150))
        libtcodpy.console_print_ex(con, screen_width // 2 - 10, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    "ACHIEVEMENTS")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Bosses defeated: {stats.bosses_defeated}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Secrets found: {stats.secrets_found}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Traps disarmed: {stats.traps_disarmed}")
        y += 2

        if run_metrics and hasattr(run_metrics, "turns_per_floor"):
            libtcodpy.console_set_default_foreground(con, libtcodpy.Color(100, 200, 100))
            libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                        libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                        "RUN METRICS")
            y += 1

            libtcodpy.console_set_default_foreground(con, libtcodpy.Color(180, 180, 180))
            for floor, turns in run_metrics.turns_per_floor.items():
                libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                            libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                            f"Floor {floor}: {turns} turns")
                y += 1

    libtcodpy.console_set_default_foreground(con, libtcodpy.Color(100, 100, 100))
    libtcodpy.console_print_ex(con, screen_width // 2 - 20, y,
                                libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                "Press Enter to restart or Esc to quit.")
