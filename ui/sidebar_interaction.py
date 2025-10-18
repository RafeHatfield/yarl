"""Sidebar interaction handling.

This module handles mouse interactions with the sidebar UI,
including clicking on inventory items and hotkey buttons.
"""

import logging
from typing import Optional, Tuple, Any
from components.component_registry import ComponentType
from ui.sidebar_layout import calculate_sidebar_layout, get_hotkey_list, get_equipment_slot_list

logger = logging.getLogger(__name__)


def _handle_hotkey_click(screen_x: int, screen_y: int, player: Any, ui_layout: Any, 
                        game_map: Optional[Any] = None, entities: Optional[list] = None) -> Optional[dict]:
    """Handle clicks on hotkey buttons in the sidebar.
    
    Uses centralized layout calculation to determine hotkey Y positions.
    
    Args:
        screen_x: X coordinate of click
        screen_y: Y coordinate of click
        player: Player entity
        ui_layout: UI layout configuration
        game_map: Game map (for stairs context)
        entities: Entity list (for Get action)
        
    Returns:
        Action dict if hotkey clicked, None otherwise
    """
    padding = ui_layout.sidebar_padding
    
    # Get centralized layout positions
    hotkey_list = get_hotkey_list()
    layout = calculate_sidebar_layout(hotkey_count=len(hotkey_list))
    
    # Map hotkeys to actions
    hotkey_actions = {
        "C - Character": {"show_character_screen": True},
        "I - Inventory": {"show_inventory": True},
        "O - Auto-Explore": {"start_auto_explore": True},
        "G - Get/Drop": None,  # Context-aware (handled below)
        "S - Search": {"search": True},
        "Z - Wait": {"wait": True},
        "Enter - Stairs": None,  # Context-aware (handled below)
    }
    
    # Check if click is on any hotkey line
    for i, (hotkey_text, is_context_aware) in enumerate(hotkey_list):
        hotkey_y = layout.hotkeys_start_y + i
        
        # Check if click is on this hotkey line
        if screen_y == hotkey_y and screen_x >= padding and screen_x < ui_layout.sidebar_width - padding:
            logger.info(f"Hotkey clicked: {hotkey_text} at Y={hotkey_y}")
            
            # Handle context-aware hotkeys
            if hotkey_text == "G - Get/Drop":
                return _handle_get_drop_click(player, entities)
            elif hotkey_text == "Enter - Stairs":
                return _handle_stairs_click(player, game_map)
            else:
                # Simple action
                return hotkey_actions.get(hotkey_text)
    
    return None


def _handle_get_drop_click(player: Any, entities: Optional[list]) -> Optional[dict]:
    """Handle Get/Drop hotkey click (context-aware).
    
    If standing on an item, pick it up.
    Otherwise, show drop inventory.
    
    Args:
        player: Player entity
        entities: List of entities
        
    Returns:
        Action dict for pickup or drop
    """
    # Check if standing on an item
    if entities:
        for entity in entities:
            if entity.x == player.x and entity.y == player.y and entity.components.has(ComponentType.ITEM):
                # Standing on item - pick it up!
                logger.info(f"Get action: picking up item at player position")
                return {"pickup": True}
    
    # Not standing on item - show drop menu
    logger.info(f"Drop action: showing drop inventory")
    return {"drop_inventory": True}


def _handle_stairs_click(player: Any, game_map: Optional[Any]) -> Optional[dict]:
    """Handle Stairs hotkey click (context-aware).
    
    If on upstairs, go up.
    If on downstairs, go down.
    Otherwise, do nothing (show message in game).
    
    Args:
        player: Player entity
        game_map: Game map
        
    Returns:
        Action dict for stairs or None
    """
    if not game_map:
        logger.warning("Stairs click: no game_map provided")
        return None
    
    # Check if player is on stairs
    from map_objects.tile import Tile
    tile = game_map.tiles[player.x][player.y]
    
    if hasattr(tile, 'tile_type'):
        if tile.tile_type == 'stairs_up':
            logger.info(f"Stairs click: going up")
            return {"take_stairs": True, "direction": "up"}
        elif tile.tile_type == 'stairs_down':
            logger.info(f"Stairs click: going down")
            return {"take_stairs": True}
    
    # Not on stairs - game will show error message
    logger.info(f"Stairs click: not on stairs")
    return {"take_stairs": True}  # Let game handle the error message


def _handle_equipment_click(screen_x: int, screen_y: int, player: Any, ui_layout: Any) -> Optional[dict]:
    """Handle clicks on equipment slots in the sidebar.
    
    Uses centralized layout calculation to determine equipment Y positions.
    
    Args:
        screen_x: X coordinate of click
        screen_y: Y coordinate of click
        player: Player entity
        ui_layout: UI layout configuration
        
    Returns:
        Action dict with equipment_slot if clicked, None otherwise
    """
    equipment = player.get_component_optional(ComponentType.EQUIPMENT)
    if not equipment:
        return None
    
    padding = ui_layout.sidebar_padding
    
    # Get centralized layout positions
    hotkey_list = get_hotkey_list()
    slot_list = get_equipment_slot_list()
    layout = calculate_sidebar_layout(hotkey_count=len(hotkey_list), equipment_slot_count=len(slot_list))
    
    # Build equipment slots from player's equipment
    equipment_slots = [(slot_name, getattr(player.equipment, slot_name)) for slot_name in slot_list]
    
    # Check if click is on any equipment line
    for i, (slot_name, item) in enumerate(equipment_slots):
        slot_y = layout.equipment_start_y + i
        
        # Check if click is on this equipment line
        if screen_y == slot_y and screen_x >= padding and screen_x < ui_layout.sidebar_width - padding:
            if item:  # Only return action if there's an item equipped
                logger.info(f"Equipment slot clicked: {slot_name} at Y={slot_y}")
                return {"equipment_slot": slot_name, "equipment_item": item}
    
    return None


def handle_sidebar_click(screen_x: int, screen_y: int, player, ui_layout, game_map=None, entities=None) -> Optional[dict]:
    """Handle a mouse click in the sidebar region.
    
    Detects if click is on a hotkey button, equipment slot, or inventory item and returns appropriate action.
    
    Args:
        screen_x: X coordinate of click (screen space)
        screen_y: Y coordinate of click (screen space)
        player: Player entity (to access inventory and equipment)
        ui_layout: UILayoutConfig instance
        game_map: Game map (for context-aware actions like stairs)
        entities: List of entities (for Get action)
        
    Returns:
        dict: Action dictionary if something clicked, None otherwise
    """
    logger.info(f"handle_sidebar_click called: ({screen_x}, {screen_y})")
    
    # Verify click is actually in sidebar
    if not ui_layout.is_in_sidebar(screen_x, screen_y):
        logger.info(f"Click not in sidebar bounds")
        return None
    
    # Check for hotkey clicks first (higher priority)
    hotkey_action = _handle_hotkey_click(screen_x, screen_y, player, ui_layout, game_map, entities)
    if hotkey_action:
        return hotkey_action
    
    # Check for equipment slot clicks
    equipment_action = _handle_equipment_click(screen_x, screen_y, player, ui_layout)
    if equipment_action:
        return equipment_action
    
    # Check if player has inventory
    inventory = player.get_component_optional(ComponentType.INVENTORY)
    if not inventory:
        return None
    
    # Get unequipped items (same logic as sidebar rendering)
    equipped_items = set()
    equipment = player.get_component_optional(ComponentType.EQUIPMENT)
    if equipment:
        for slot_item in [player.equipment.main_hand, player.equipment.off_hand,
                        player.equipment.head, player.equipment.chest, player.equipment.feet,
                        player.equipment.left_ring, player.equipment.right_ring]:
            if slot_item:
                equipped_items.add(slot_item)
    
    inventory_items = [item for item in player.inventory.items if item not in equipped_items]
    
    # IMPORTANT: Sort alphabetically to match sidebar rendering!
    # This ensures click coordinates align with displayed items
    # Use display name for proper sorting of unidentified items
    inventory_items = sorted(inventory_items, key=lambda item: item.get_display_name().lower())
    
    if len(inventory_items) == 0:
        return None
    
    # Calculate where inventory section starts in sidebar using centralized layout
    padding = ui_layout.sidebar_padding
    
    # Get centralized layout positions
    hotkey_list = get_hotkey_list()
    slot_list = get_equipment_slot_list()
    layout = calculate_sidebar_layout(hotkey_count=len(hotkey_list), equipment_slot_count=len(slot_list))
    
    inventory_start_y = layout.inventory_start_y
    
    logger.info(f"Calculated inventory_start_y = {inventory_start_y} (from centralized layout)")
    
    # Check if click is on an inventory item
    # Items are rendered at: padding + 1, inventory_start_y + index
    clicked_item_index = None
    
    for i in range(len(inventory_items)):
        item_y = inventory_start_y + i
        
        # Check if click is on this line and within the item text area
        if screen_y == item_y and screen_x >= padding and screen_x < ui_layout.sidebar_width - padding:
            clicked_item_index = i
            break
    
    logger.info(f"Checking {len(inventory_items)} items starting at Y={inventory_start_y}")
    logger.info(f"Click was at Y={screen_y}, clicked_item_index={clicked_item_index}")
    
    if clicked_item_index is not None:
        # User clicked on an item!
        logger.warning(f"ITEM CLICKED! Index: {clicked_item_index}")
        
        # IMPORTANT: We need to return the index into the FULL SORTED inventory
        # (including equipped items), not just the unequipped items shown in sidebar!
        # This matches what _handle_inventory_action expects.
        clicked_item = inventory_items[clicked_item_index]
        
        # Create full sorted inventory (same as game_actions.py does)
        full_sorted_inventory = sorted(player.inventory.items, key=lambda item: item.get_display_name().lower())
        actual_inventory_index = full_sorted_inventory.index(clicked_item)
        
        logger.warning(f"Returning inventory_index={actual_inventory_index}")
        
        return {
            "inventory_index": actual_inventory_index,
            "source": "sidebar_click"
        }
    
    logger.info(f"No item clicked at this position")
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
    y_cursor += 9  # Equipment (7 slots + header + spacing)
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

