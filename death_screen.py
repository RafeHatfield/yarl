"""Death screen rendering and statistics display.

This module handles the display of player statistics and options when the player dies.
"""

import tcod.libtcodpy as libtcodpy


def render_death_screen(con, player, screen_width, screen_height):
    """Render the death screen with statistics and restart options.
    
    Args:
        con: The console to render to (libtcodpy console)
        player: The player entity (to access statistics)
        screen_width: Width of the screen
        screen_height: Height of the screen
    """
    # Clear the console with a dark overlay
    libtcodpy.console_set_default_background(con, libtcodpy.black)
    libtcodpy.console_clear(con)
    
    # Get player statistics
    stats = player.statistics if hasattr(player, 'statistics') and player.statistics else None
    
    # Title
    title = "YOU DIED"
    title_x = screen_width // 2 - len(title) // 2
    libtcodpy.console_set_default_foreground(con, libtcodpy.Color(255, 50, 50))
    libtcodpy.console_print_ex(con, title_x, 5, libtcodpy.BKGND_NONE, libtcodpy.LEFT, title)
    
    # Draw a line under the title
    line = "=" * (len(title) + 4)
    libtcodpy.console_set_default_foreground(con, libtcodpy.Color(150, 50, 50))
    libtcodpy.console_print_ex(con, title_x - 2, 6, libtcodpy.BKGND_NONE, libtcodpy.LEFT, line)
    
    if stats:
        # Render statistics
        y = 8
        
        # Header
        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(200, 200, 200))
        libtcodpy.console_print_ex(con, screen_width // 2 - 10, y, 
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT, 
                                    "=== RUN STATISTICS ===")
        y += 2
        
        # Combat Statistics
        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(255, 200, 100))
        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y, 
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT, "COMBAT")
        y += 1
        
        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(200, 200, 200))
        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y, 
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"  Monsters Killed: {stats.total_kills}")
        y += 1
        
        # Show kill breakdown if there are kills
        if stats.monsters_killed and stats.total_kills > 0:
            kill_list = sorted(stats.monsters_killed.items(), key=lambda x: x[1], reverse=True)
            libtcodpy.console_set_default_foreground(con, libtcodpy.Color(180, 180, 180))
            for monster_name, count in kill_list[:5]:  # Show top 5
                display_name = monster_name.replace('_', ' ').title()
                libtcodpy.console_print_ex(con, screen_width // 2 - 13, y, 
                                           libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                           f"    {display_name}: {count}")
                y += 1
        
        y += 1
        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(200, 200, 200))
        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y, 
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"  Attacks Made: {stats.attacks_made}")
        y += 1
        
        attacks_missed = stats.attacks_made - stats.attacks_hit
        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y, 
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"  Hits / Misses: {stats.attacks_hit} / {attacks_missed}")
        y += 1
        
        if stats.attacks_made > 0:
            accuracy = (stats.attacks_hit / stats.attacks_made) * 100
            libtcodpy.console_print_ex(con, screen_width // 2 - 15, y, 
                                        libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                        f"  Accuracy: {accuracy:.1f}%")
            y += 1
        
        if stats.critical_hits > 0:
            libtcodpy.console_set_default_foreground(con, libtcodpy.Color(255, 215, 0))
            libtcodpy.console_print_ex(con, screen_width // 2 - 15, y, 
                                        libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                        f"  Critical Hits: {stats.critical_hits}")
            y += 1
        
        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(200, 200, 200))
        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y, 
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"  Damage Dealt: {stats.damage_dealt}")
        y += 1
        
        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(255, 100, 100))
        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y, 
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"  Damage Taken: {stats.damage_taken}")
        y += 2
        
        # Exploration Statistics
        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(100, 200, 255))
        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y, 
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT, "EXPLORATION")
        y += 1
        
        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(200, 200, 200))
        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y, 
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"  Deepest Level: {stats.deepest_level}")
        y += 1
        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y, 
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"  Rooms Explored: {stats.rooms_explored}")
        y += 1
        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y, 
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    f"  Turns Taken: {stats.turns_taken}")
        y += 2
        
        # Items & Resources
        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(150, 100, 255))
        libtcodpy.console_print_ex(con, screen_width // 2 - 15, y, 
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT, "ITEMS & RESOURCES")
        y += 1
        
        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(200, 200, 200))
        if stats.healing_received > 0:
            libtcodpy.console_print_ex(con, screen_width // 2 - 15, y, 
                                        libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                        f"  Healing Received: {stats.healing_received} HP")
            y += 1
        
        total_items = sum(stats.items_used.values()) if hasattr(stats.items_used, 'values') else 0
        if total_items > 0:
            libtcodpy.console_print_ex(con, screen_width // 2 - 15, y, 
                                        libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                        f"  Items Used: {total_items}")
            y += 1
        
        if stats.gold_collected > 0:
            libtcodpy.console_print_ex(con, screen_width // 2 - 15, y, 
                                        libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                        f"  Gold Collected: {stats.gold_collected}")
            y += 1
    else:
        # No statistics available
        y = 10
        libtcodpy.console_set_default_foreground(con, libtcodpy.Color(150, 150, 150))
        libtcodpy.console_print_ex(con, screen_width // 2 - 10, y, 
                                    libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                    "No statistics available")
        y += 3
    
    # Instructions at bottom
    y = screen_height - 8
    libtcodpy.console_set_default_foreground(con, libtcodpy.Color(100, 100, 100))
    libtcodpy.console_print_ex(con, screen_width // 2 - 20, y, 
                                libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                "=" * 40)
    y += 2
    
    libtcodpy.console_set_default_foreground(con, libtcodpy.Color(100, 255, 100))
    libtcodpy.console_print_ex(con, screen_width // 2 - 15, y, 
                                libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                "Press R to restart a new game")
    y += 1
    
    libtcodpy.console_set_default_foreground(con, libtcodpy.Color(200, 200, 200))
    libtcodpy.console_print_ex(con, screen_width // 2 - 15, y, 
                                libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                "Press ESC to return to menu")
    y += 1
    
    libtcodpy.console_set_default_foreground(con, libtcodpy.Color(150, 150, 150))
    libtcodpy.console_print_ex(con, screen_width // 2 - 15, y, 
                                libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                                "Press any other key to exit")
    
    # Blit the death screen console to the root console (0) to make it visible
    libtcodpy.console_blit(con, 0, 0, screen_width, screen_height, 0, 0, 0)
