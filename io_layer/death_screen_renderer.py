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

        # Defensive stat lookups - handle schema changes gracefully
        turns_survived = getattr(stats, 'turns_survived', None) or getattr(stats, 'turns_taken', 0)
        monsters_killed = getattr(stats, 'total_kills', getattr(stats, 'monsters_killed', 0))
        if isinstance(monsters_killed, dict):
            monsters_killed = sum(monsters_killed.values())
        damage_dealt = getattr(stats, 'damage_dealt', 0)
        damage_taken = getattr(stats, 'damage_taken', 0)
        critical_hits = getattr(stats, 'critical_hits', 0)
        times_stunned = getattr(stats, 'times_stunned', 0)
        
        floors_descended = getattr(stats, 'floors_descended', None) or getattr(stats, 'deepest_level', 1) - 1
        items_picked_up = getattr(stats, 'items_picked_up', 0)
        potions_drunk = getattr(stats, 'potions_drunk', None) or getattr(stats, 'potions_used', 0)
        scrolls_read = getattr(stats, 'scrolls_read', 0)
        
        bosses_defeated = getattr(stats, 'bosses_defeated', 0)
        secrets_found = getattr(stats, 'secrets_found', 0)
        traps_disarmed = getattr(stats, 'traps_disarmed', 0)

        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(200, 200, 200))
        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Turns survived: {turns_survived}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Monsters killed: {monsters_killed}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Damage dealt: {damage_dealt}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Damage taken: {damage_taken}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Critical hits: {critical_hits}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Times stunned: {times_stunned}")
        y += 2

        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(180, 180, 180))
        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    "NON-COMBAT")
        y += 1

        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(200, 200, 200))
        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Floors descended: {floors_descended}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Items picked up: {items_picked_up}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Potions drunk: {potions_drunk}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Scrolls read: {scrolls_read}")
        y += 2

        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(150, 150, 150))
        libtcodpy.console_print_ex(con, screen_width // 2 - 10, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    "ACHIEVEMENTS")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Bosses defeated: {bosses_defeated}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Secrets found: {secrets_found}")
        y += 1

        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y,
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"Traps disarmed: {traps_disarmed}")
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
