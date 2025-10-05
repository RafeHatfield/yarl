"""Tooltip rendering system.

Provides hover tooltips for UI elements, particularly for items in the sidebar
that have abbreviated names.
"""

import tcod.libtcodpy as libtcod
from typing import Optional, Any


def get_sidebar_item_at_position(screen_x: int, screen_y: int, player, ui_layout) -> Optional[Any]:
    """Get the item being hovered over in the sidebar inventory.
    
    Args:
        screen_x: Mouse X position (screen coordinates)
        screen_y: Mouse Y position (screen coordinates)
        player: Player entity
        ui_layout: UILayoutConfig instance
        
    Returns:
        Item entity if hovering over an inventory item, None otherwise
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Verify mouse is in sidebar
    if not ui_layout.is_in_sidebar(screen_x, screen_y):
        return None
    
    logger.debug(f"Mouse in sidebar at ({screen_x}, {screen_y})")
    
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
    
    # Calculate where inventory section starts (must match sidebar.py rendering!)
    padding = ui_layout.sidebar_padding
    y_cursor = 2  # Title
    y_cursor += 2  # Title spacing + separator
    y_cursor += 2  # Separator spacing
    y_cursor += 1  # "HOTKEYS" header
    y_cursor += 6  # 6 hotkey lines
    y_cursor += 1  # Spacing after hotkeys
    y_cursor += 1  # "EQUIPMENT" header
    y_cursor += 5  # 5 equipment slots
    y_cursor += 1  # Spacing after equipment
    y_cursor += 1  # "INVENTORY (N/20)" header
    
    inventory_start_y = y_cursor
    
    # Check if mouse is on an inventory item line
    for i, item in enumerate(inventory_items):
        item_y = inventory_start_y + i
        
        # Check if hovering over this line
        if screen_y == item_y and screen_x >= padding and screen_x < ui_layout.sidebar_width - padding:
            logger.debug(f"Found hovered item: {item.name} at Y={item_y}")
            return item
    
    logger.debug(f"No item found. Inventory starts at Y={inventory_start_y}, mouse Y={screen_y}")
    return None


def render_tooltip(console, item: Any, mouse_x: int, mouse_y: int, ui_layout) -> None:
    """Render a tooltip for an item near the mouse cursor.
    
    The tooltip shows the full item name and relevant stats/info.
    
    Args:
        console: Console to render to (viewport console for proper positioning)
        item: The item entity to show info for
        mouse_x: Mouse X position (screen coordinates)
        mouse_y: Mouse Y position (screen coordinates)
        ui_layout: UILayoutConfig instance
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not item:
        return
    
    logger.debug(f"Rendering tooltip for {item.name} at mouse ({mouse_x}, {mouse_y})")
    
    # Get full item information
    item_name = item.get_display_name() if hasattr(item, 'get_display_name') else item.name
    
    # Build tooltip lines
    tooltip_lines = [item_name]
    
    # Add item type/description
    if hasattr(item, 'wand') and item.wand:
        tooltip_lines.append(f"Multi-use spell caster")
        tooltip_lines.append(f"{item.wand.charges} charges remaining")
    elif hasattr(item, 'equippable') and item.equippable:
        if hasattr(item.equippable, 'damage_dice') and item.equippable.damage_dice:
            tooltip_lines.append("Weapon")
        elif hasattr(item.equippable, 'defense_bonus') and item.equippable.defense_bonus:
            tooltip_lines.append("Armor")
    elif hasattr(item, 'item') and item.item:
        if item.item.use_function:
            tooltip_lines.append("Consumable")
    
    # Calculate tooltip dimensions
    tooltip_width = max(len(line) for line in tooltip_lines) + 4  # +4 for padding
    tooltip_height = len(tooltip_lines) + 2  # +2 for borders
    
    # Position tooltip near mouse, but keep it on screen
    # Convert screen coordinates to viewport coordinates for rendering
    tooltip_x = mouse_x - ui_layout.sidebar_width + 2  # Offset from sidebar
    tooltip_y = mouse_y - ui_layout.status_panel_height
    
    # Adjust if tooltip would go off screen
    if tooltip_x + tooltip_width > ui_layout.viewport_width:
        tooltip_x = ui_layout.viewport_width - tooltip_width - 1
    if tooltip_y + tooltip_height > ui_layout.viewport_height:
        tooltip_y = ui_layout.viewport_height - tooltip_height - 1
    
    # Ensure minimum position
    if tooltip_x < 1:
        tooltip_x = 1
    if tooltip_y < 1:
        tooltip_y = 1
    
    # Draw tooltip background
    for y in range(tooltip_height):
        for x in range(tooltip_width):
            libtcod.console_set_char_background(
                console,
                tooltip_x + x,
                tooltip_y + y,
                libtcod.Color(40, 40, 40),
                libtcod.BKGND_SET
            )
    
    # Draw border
    libtcod.console_set_default_foreground(console, libtcod.Color(200, 200, 200))
    
    # Top and bottom borders
    for x in range(tooltip_width):
        libtcod.console_put_char(console, tooltip_x + x, tooltip_y, ord('─'), libtcod.BKGND_NONE)
        libtcod.console_put_char(console, tooltip_x + x, tooltip_y + tooltip_height - 1, ord('─'), libtcod.BKGND_NONE)
    
    # Side borders
    for y in range(tooltip_height):
        libtcod.console_put_char(console, tooltip_x, tooltip_y + y, ord('│'), libtcod.BKGND_NONE)
        libtcod.console_put_char(console, tooltip_x + tooltip_width - 1, tooltip_y + y, ord('│'), libtcod.BKGND_NONE)
    
    # Corners
    libtcod.console_put_char(console, tooltip_x, tooltip_y, ord('┌'), libtcod.BKGND_NONE)
    libtcod.console_put_char(console, tooltip_x + tooltip_width - 1, tooltip_y, ord('┐'), libtcod.BKGND_NONE)
    libtcod.console_put_char(console, tooltip_x, tooltip_y + tooltip_height - 1, ord('└'), libtcod.BKGND_NONE)
    libtcod.console_put_char(console, tooltip_x + tooltip_width - 1, tooltip_y + tooltip_height - 1, ord('┘'), libtcod.BKGND_NONE)
    
    # Draw tooltip content
    libtcod.console_set_default_foreground(console, libtcod.Color(255, 255, 255))
    for i, line in enumerate(tooltip_lines):
        libtcod.console_print_ex(
            console,
            tooltip_x + 2,  # Padding from left border
            tooltip_y + 1 + i,  # +1 for top border
            libtcod.BKGND_NONE,
            libtcod.LEFT,
            line
        )
    
    logger.debug(f"Tooltip drawn at ({tooltip_x}, {tooltip_y}) size ({tooltip_width}x{tooltip_height})")

