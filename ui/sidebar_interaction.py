"""Sidebar interaction handling.

This module handles mouse interactions with the sidebar UI,
including clicking on inventory items to use them.
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def handle_sidebar_click(screen_x: int, screen_y: int, player, ui_layout) -> Optional[dict]:
    """Handle a mouse click in the sidebar region.
    
    Detects if click is on an inventory item and returns appropriate action.
    
    Args:
        screen_x: X coordinate of click (screen space)
        screen_y: Y coordinate of click (screen space)
        player: Player entity (to access inventory)
        ui_layout: UILayoutConfig instance
        
    Returns:
        dict: Action dictionary if item clicked, None otherwise
    """
    # Verify click is actually in sidebar
    if not ui_layout.is_in_sidebar(screen_x, screen_y):
        return None
    
    # Check if player has inventory
    if not hasattr(player, 'inventory') or not player.inventory:
        return None
    
    # Get unequipped items (same logic as sidebar rendering)
    equipped_items = set()
    if hasattr(player, 'equipment') and player.equipment:
        for slot_item in [player.equipment.main_hand, player.equipment.off_hand,
                        player.equipment.head, player.equipment.chest, player.equipment.feet]:
            if slot_item:
                equipped_items.add(slot_item)
    
    inventory_items = [item for item in player.inventory.items if item not in equipped_items]
    
    if len(inventory_items) == 0:
        return None
    
    # Calculate where inventory section starts in sidebar
    # This needs to match the rendering logic in ui/sidebar.py
    padding = ui_layout.sidebar_padding
    
    # Header layout (must match sidebar.py exactly!)
    y_cursor = 2  # Title
    y_cursor += 2  # Separator + spacing
    y_cursor += 3  # Hotkeys section (header + 2 lines)
    y_cursor += 1  # Spacing
    y_cursor += 7  # Equipment section (header + 5 slots + spacing)
    y_cursor += 1  # Inventory header
    
    # Now y_cursor is at first inventory item
    inventory_start_y = y_cursor
    
    # Check if click is on an inventory item
    # Items are rendered at: padding + 1, inventory_start_y + index
    clicked_item_index = None
    
    for i in range(len(inventory_items)):
        item_y = inventory_start_y + i
        
        # Check if click is on this line and within the item text area
        if screen_y == item_y and screen_x >= padding and screen_x < ui_layout.sidebar_width - padding:
            clicked_item_index = i
            break
    
    if clicked_item_index is not None:
        # User clicked on an item!
        logger.info(f"Sidebar inventory click: item index {clicked_item_index}")
        
        # Return action to use this item
        # The index corresponds to the unequipped items, so we need to find
        # the actual inventory index
        clicked_item = inventory_items[clicked_item_index]
        actual_inventory_index = player.inventory.items.index(clicked_item)
        
        return {
            "inventory_index": actual_inventory_index,
            "source": "sidebar_click"
        }
    
    return None


def get_sidebar_inventory_bounds(ui_layout) -> Tuple[int, int, int, int]:
    """Get the bounding box for the inventory section in the sidebar.
    
    Returns (x1, y1, x2, y2) in screen coordinates.
    
    Args:
        ui_layout: UILayoutConfig instance
        
    Returns:
        Tuple[int, int, int, int]: (x1, y1, x2, y2) bounding box
    """
    padding = ui_layout.sidebar_padding
    
    # Calculate inventory start Y (must match sidebar.py layout!)
    y_cursor = 2  # Title
    y_cursor += 2  # Separator + spacing  
    y_cursor += 3  # Hotkeys
    y_cursor += 1  # Spacing
    y_cursor += 7  # Equipment
    y_cursor += 1  # Inventory header
    
    inventory_start_y = y_cursor
    
    # Inventory can take up to ~32 lines
    inventory_end_y = min(inventory_start_y + 32, ui_layout.screen_height - 2)
    
    return (
        padding,  # x1
        inventory_start_y,  # y1
        ui_layout.sidebar_width - padding,  # x2
        inventory_end_y  # y2
    )

