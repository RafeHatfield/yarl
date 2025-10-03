"""Sidebar UI rendering.

This module handles rendering of the left sidebar UI, including:
- Menu buttons (Inventory, Character)
- Hotkey reference
- Player stats
- Equipment slots display

The sidebar is always visible and provides persistent game information.
"""

import tcod.libtcodpy as libtcod
from typing import Optional


def render_sidebar(console, player, ui_layout) -> None:
    """Render the sidebar UI with menu, stats, and equipment.
    
    Args:
        console: The sidebar console to render to
        player: The player entity
        ui_layout: UILayoutConfig instance for dimensions
    """
    # Clear the sidebar
    libtcod.console_set_default_background(console, libtcod.Color(20, 20, 20))
    libtcod.console_clear(console)
    
    y = 2  # Starting Y position
    padding = ui_layout.sidebar_padding
    
    # Title bar
    libtcod.console_set_default_foreground(console, libtcod.Color(200, 200, 200))
    title = "YARL"
    libtcod.console_print_ex(
        console, ui_layout.sidebar_width // 2, y,
        libtcod.BKGND_NONE, libtcod.CENTER, title
    )
    y += 2
    
    # Separator
    libtcod.console_set_default_foreground(console, libtcod.Color(100, 100, 100))
    separator = "─" * (ui_layout.sidebar_width - padding * 2)
    libtcod.console_print_ex(
        console, padding, y,
        libtcod.BKGND_NONE, libtcod.LEFT, separator
    )
    y += 2
    
    # Hotkeys Section (includes menu items!)
    libtcod.console_set_default_foreground(console, libtcod.Color(255, 255, 255))
    libtcod.console_print_ex(
        console, padding, y,
        libtcod.BKGND_NONE, libtcod.LEFT, "HOTKEYS"
    )
    y += 1
    
    libtcod.console_set_default_foreground(console, libtcod.Color(150, 150, 150))
    hotkeys = [
        "I - Inventory",
        "C - Character",
        "Z - Wait",
        "< - Stairs Up",
        "> - Stairs Down",
        "G - Pickup",
        "D - Drop",
        "/ - Look",
    ]
    
    for hotkey in hotkeys:
        libtcod.console_print_ex(
            console, padding + 1, y,
            libtcod.BKGND_NONE, libtcod.LEFT, hotkey
        )
        y += 1
    
    y += 2
    
    # Player Stats Section
    if player and hasattr(player, 'fighter') and player.fighter:
        libtcod.console_set_default_foreground(console, libtcod.Color(255, 255, 255))
        libtcod.console_print_ex(
            console, padding, y,
            libtcod.BKGND_NONE, libtcod.LEFT, "STATS"
        )
        y += 1
        
        libtcod.console_set_default_foreground(console, libtcod.Color(200, 200, 200))
        
        # HP
        hp_text = f"HP: {player.fighter.hp}/{player.fighter.max_hp}"
        libtcod.console_print_ex(
            console, padding + 2, y,
            libtcod.BKGND_NONE, libtcod.LEFT, hp_text
        )
        y += 1
        
        # Ability scores
        stats_to_show = [
            ("STR", player.fighter.strength),
            ("DEX", player.fighter.dexterity),
            ("CON", player.fighter.constitution),
        ]
        
        for stat_name, stat_value in stats_to_show:
            stat_text = f"{stat_name}: {stat_value}"
            libtcod.console_print_ex(
                console, padding + 2, y,
                libtcod.BKGND_NONE, libtcod.LEFT, stat_text
            )
            y += 1
        
        y += 2
        
        # Equipment Section
        if hasattr(player, 'equipment') and player.equipment:
            libtcod.console_set_default_foreground(console, libtcod.Color(255, 255, 255))
            libtcod.console_print_ex(
                console, padding, y,
                libtcod.BKGND_NONE, libtcod.LEFT, "EQUIPMENT"
            )
            y += 1
            
            libtcod.console_set_default_foreground(console, libtcod.Color(200, 200, 200))
            
            # Show equipped items
            equipment_slots = [
                ("Weapon", player.equipment.main_hand),
                ("Shield", player.equipment.off_hand),
                ("Helm", player.equipment.head),
                ("Armor", player.equipment.chest),
                ("Boots", player.equipment.feet),
            ]
            
            for slot_name, item in equipment_slots:
                if item:
                    # Truncate name if too long
                    item_name = item.name
                    max_name_len = ui_layout.sidebar_content_width - 6
                    if len(item_name) > max_name_len:
                        item_name = item_name[:max_name_len-2] + ".."
                    
                    slot_text = f"{slot_name[:3]}: {item_name}"
                else:
                    slot_text = f"{slot_name[:3]}: -"
                
                libtcod.console_print_ex(
                    console, padding + 2, y,
                    libtcod.BKGND_NONE, libtcod.LEFT, slot_text
                )
                y += 1


def _render_sidebar(console, player, ui_layout) -> None:
    """Internal wrapper for render_sidebar.
    
    Args:
        console: Sidebar console
        player: Player entity
        ui_layout: UI layout configuration
    """
    render_sidebar(console, player, ui_layout)

