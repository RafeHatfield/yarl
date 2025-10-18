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
from ui.sidebar_layout import calculate_sidebar_layout, get_hotkey_list, get_equipment_slot_list


def render_sidebar(console, player, ui_layout) -> None:
    """Render the sidebar UI with menu, stats, and equipment.
    
    Uses centralized layout calculation to ensure consistency with interaction and tooltips.
    
    Args:
        console: The sidebar console to render to
        player: The player entity
        ui_layout: UILayoutConfig instance for dimensions
    """
    # Clear the sidebar
    libtcod.console_set_default_background(console, libtcod.Color(20, 20, 20))
    libtcod.console_clear(console)
    
    padding = ui_layout.sidebar_padding
    
    # Get centralized layout
    hotkey_list = get_hotkey_list()
    slot_list = get_equipment_slot_list()
    layout = calculate_sidebar_layout(hotkey_count=len(hotkey_list), equipment_slot_count=len(slot_list))
    
    # Title bar
    libtcod.console_set_default_foreground(console, libtcod.Color(200, 200, 200))
    title = "YARL"
    libtcod.console_print_ex(
        console, ui_layout.sidebar_width // 2, layout.title_y,
        libtcod.BKGND_NONE, libtcod.CENTER, title
    )
    
    # Separator
    libtcod.console_set_default_foreground(console, libtcod.Color(100, 100, 100))
    separator = "─" * (ui_layout.sidebar_width - padding * 2)
    libtcod.console_print_ex(
        console, padding, layout.separator_y,
        libtcod.BKGND_NONE, libtcod.LEFT, separator
    )
    
    # Hotkeys Section (clickable!)
    libtcod.console_set_default_foreground(console, libtcod.Color(255, 255, 255))
    libtcod.console_print_ex(
        console, padding, layout.hotkeys_header_y,
        libtcod.BKGND_NONE, libtcod.LEFT, "HOTKEYS"
    )
    
    libtcod.console_set_default_foreground(console, libtcod.Color(150, 150, 150))
    for i, (hotkey_text, is_context_aware) in enumerate(hotkey_list):
        libtcod.console_print_ex(
            console, padding + 1, layout.hotkeys_start_y + i,
            libtcod.BKGND_NONE, libtcod.LEFT, hotkey_text
        )
        
    # Equipment Section
    equipment = player.get_component_optional(ComponentType.EQUIPMENT)
    if equipment:
        libtcod.console_set_default_foreground(console, libtcod.Color(255, 255, 255))
        libtcod.console_print_ex(
            console, padding, layout.equipment_header_y,
            libtcod.BKGND_NONE, libtcod.LEFT, "EQUIPMENT"
        )
        
        libtcod.console_set_default_foreground(console, libtcod.Color(200, 200, 200))
        
        # Show equipped items (using centralized slot list)
        equipment_labels = {
            "main_hand": "Weapon",
            "off_hand": "Shield",
            "head": "Helm",
            "chest": "Armor",
            "feet": "Boots",
            "left_ring": "L Ring",
            "right_ring": "R Ring",
        }
        
        for i, slot_name in enumerate(slot_list):
            label = equipment_labels[slot_name]
            item = getattr(player.equipment, slot_name)
            
            if item:
                # Truncate name if too long
                item_name = item.name
                max_name_len = ui_layout.sidebar_content_width - 6
                if len(item_name) > max_name_len:
                    item_name = item_name[:max_name_len-2] + ".."
                
                slot_text = f"{label[:3]}: {item_name}"
            else:
                slot_text = f"{label[:3]}: -"
            
            libtcod.console_print_ex(
                console, padding + 1, layout.equipment_start_y + i,
                libtcod.BKGND_NONE, libtcod.LEFT, slot_text
            )
        
    # Inventory Section (PERSISTENT!)
    inventory = player.get_component_optional(ComponentType.INVENTORY)
    if inventory:
        # Get unequipped items only (equipped items shown in EQUIPMENT section)
        equipped_items = set()
        equipment = player.get_component_optional(ComponentType.EQUIPMENT)
        if equipment:
            for slot_item in [player.equipment.main_hand, player.equipment.off_hand,
                            player.equipment.head, player.equipment.chest, player.equipment.feet,
                            player.equipment.left_ring, player.equipment.right_ring]:
                if slot_item:
                    equipped_items.add(slot_item)
        
        # Filter out equipped items
        inventory_items = [item for item in player.inventory.items if item not in equipped_items]
        
        # Sort alphabetically for better UX (use display name for proper sorting of unidentified items)
        inventory_items = sorted(inventory_items, key=lambda item: item.get_display_name().lower())
        
        # Header with count
        libtcod.console_set_default_foreground(console, libtcod.Color(255, 255, 255))
        inv_header = f"INVENTORY ({len(inventory_items)}/{player.inventory.capacity})"
        libtcod.console_print_ex(
            console, padding, layout.inventory_header_y,
            libtcod.BKGND_NONE, libtcod.LEFT, inv_header
        )
        
        if len(inventory_items) == 0:
            libtcod.console_set_default_foreground(console, libtcod.Color(128, 128, 128))
            libtcod.console_print_ex(
                console, padding + 1, layout.inventory_start_y,
                libtcod.BKGND_NONE, libtcod.LEFT, "(empty)"
            )
        else:
            libtcod.console_set_default_foreground(console, libtcod.Color(200, 200, 200))
            letter_index = ord('a')
            
            for i, item in enumerate(inventory_items):
                # Format: "a) 5x Potion" or "a) Potion"
                # Use item component's display name to include quantity for stacks
                if hasattr(item, 'item') and item.item:
                    # Use item component's get_display_name which handles quantity
                    item_name = item.item.get_display_name(compact=True, show_quantity=True)
                elif hasattr(item, 'get_display_name'):
                    item_name = item.get_display_name(compact=True)
                else:
                    item_name = item.name
                
                # Truncate if too long
                max_name_len = ui_layout.sidebar_content_width - 4  # "a) " = 3 chars + 1 space
                if len(item_name) > max_name_len:
                    item_name = item_name[:max_name_len-2] + ".."
                
                item_text = f"{chr(letter_index)}) {item_name}"
                libtcod.console_print_ex(
                    console, padding + 1, layout.inventory_start_y + i,
                    libtcod.BKGND_NONE, libtcod.LEFT, item_text
                )
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

