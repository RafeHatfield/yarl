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
from components.component_registry import ComponentType


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
    
    # Hotkeys Section (clickable!)
    libtcod.console_set_default_foreground(console, libtcod.Color(255, 255, 255))
    libtcod.console_print_ex(
        console, padding, y,
        libtcod.BKGND_NONE, libtcod.LEFT, "HOTKEYS"
    )
    y += 1
    
    libtcod.console_set_default_foreground(console, libtcod.Color(150, 150, 150))
    # Option C: Hybrid clickable layout
    # Each line is a clickable action
    hotkeys = [
        "C - Character",
        "I - Inventory",
        "G - Get/Drop",
        "Z - Wait",
        "<> - Stairs",
        "/ - Look",
    ]
    
    for hotkey in hotkeys:
        libtcod.console_print_ex(
            console, padding + 1, y,
            libtcod.BKGND_NONE, libtcod.LEFT, hotkey
        )
        y += 1
    
    y += 1
        
    # Equipment Section
    equipment = player.components.get(ComponentType.EQUIPMENT)
    if equipment:
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
                console, padding + 1, y,
                libtcod.BKGND_NONE, libtcod.LEFT, slot_text
            )
            y += 1
        
        y += 1
        
    # Inventory Section (PERSISTENT!)
    inventory = player.components.get(ComponentType.INVENTORY)
    if inventory:
        # Get unequipped items only (equipped items shown in EQUIPMENT section)
        equipped_items = set()
        equipment = player.components.get(ComponentType.EQUIPMENT)
        if equipment:
            for slot_item in [player.equipment.main_hand, player.equipment.off_hand,
                            player.equipment.head, player.equipment.chest, player.equipment.feet]:
                if slot_item:
                    equipped_items.add(slot_item)
        
        # Filter out equipped items
        inventory_items = [item for item in player.inventory.items if item not in equipped_items]
        
        # Header with count
        libtcod.console_set_default_foreground(console, libtcod.Color(255, 255, 255))
        inv_header = f"INVENTORY ({len(inventory_items)}/{player.inventory.capacity})"
        libtcod.console_print_ex(
            console, padding, y,
            libtcod.BKGND_NONE, libtcod.LEFT, inv_header
        )
        y += 1
        
        if len(inventory_items) == 0:
            libtcod.console_set_default_foreground(console, libtcod.Color(128, 128, 128))
            libtcod.console_print_ex(
                console, padding + 1, y,
                libtcod.BKGND_NONE, libtcod.LEFT, "(empty)"
            )
        else:
            libtcod.console_set_default_foreground(console, libtcod.Color(200, 200, 200))
            letter_index = ord('a')
            
            for item in inventory_items:
                # Format: "a) Potion"
                # Use compact name for wands to fit in sidebar
                if hasattr(item, 'get_display_name'):
                    item_name = item.get_display_name(compact=True)
                else:
                    item_name = item.name
                
                # Truncate if too long
                max_name_len = ui_layout.sidebar_content_width - 4  # "a) " = 3 chars + 1 space
                if len(item_name) > max_name_len:
                    item_name = item_name[:max_name_len-2] + ".."
                
                item_text = f"{chr(letter_index)}) {item_name}"
                libtcod.console_print_ex(
                    console, padding + 1, y,
                    libtcod.BKGND_NONE, libtcod.LEFT, item_text
                )
                y += 1
                letter_index += 1
        
        y += 1
        
        # Click hint
        libtcod.console_set_default_foreground(console, libtcod.Color(100, 100, 100))
        libtcod.console_print_ex(
            console, padding + 1, y,
            libtcod.BKGND_NONE, libtcod.LEFT, "(Click to use!)"
        )


def _render_sidebar(console, player, ui_layout) -> None:
    """Internal wrapper for render_sidebar.
    
    Args:
        console: Sidebar console
        player: Player entity
        ui_layout: UI layout configuration
    """
    render_sidebar(console, player, ui_layout)

