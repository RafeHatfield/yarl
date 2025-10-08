"""Tooltip rendering system.

Provides hover tooltips for UI elements, particularly for items in the sidebar
that have abbreviated names, and for items on the ground in the viewport.
"""

import tcod.libtcodpy as libtcod
from typing import Optional, Any
import logging

from components.component_registry import ComponentType

logger = logging.getLogger(__name__)


def get_ground_item_at_position(world_x: int, world_y: int, entities: list, fov_map=None) -> Optional[Any]:
    """Get the item on the ground at the specified world coordinates.
    
    Args:
        world_x: X coordinate in world space
        world_y: Y coordinate in world space
        entities: List of all entities in the game
        fov_map: Optional FOV map to check visibility
        
    Returns:
        Item entity if there's an item at that position, None otherwise
    """
    # Check FOV if provided (only show tooltips for visible items)
    if fov_map:
        from fov_functions import map_is_in_fov
        if not map_is_in_fov(fov_map, world_x, world_y):
            return None
    
    # Find items at this position (prioritize items over corpses)
    items_at_pos = []
    for entity in entities:
        if entity.x == world_x and entity.y == world_y:
            # Check if it's an item (has item component and not the player)
            if entity.components.has(ComponentType.ITEM):
                items_at_pos.append(entity)
    
    # Return the first item found (if multiple items stacked, show top one)
    if items_at_pos:
        return items_at_pos[0]
    
    return None


def get_monster_at_position(world_x: int, world_y: int, entities: list, player, fov_map=None) -> Optional[Any]:
    """Get the monster at the specified world coordinates.
    
    Prioritizes LIVING monsters over dead ones (corpses). If a live monster
    is standing on a corpse, the live monster's tooltip is shown.
    
    Args:
        world_x: X coordinate in world space
        world_y: Y coordinate in world space
        entities: List of all entities in the game
        player: Player entity (to exclude from results)
        fov_map: Optional FOV map to check visibility
        
    Returns:
        Monster entity if there's a monster at that position, None otherwise
    """
    # Check FOV if provided (only show tooltips for visible monsters)
    if fov_map:
        from fov_functions import map_is_in_fov
        if not map_is_in_fov(fov_map, world_x, world_y):
            return None
    
    # Find monsters at this position, prioritizing LIVING ones
    living_monster = None
    dead_monster = None
    
    for entity in entities:
        if entity.x == world_x and entity.y == world_y:
            # Check if it's a monster (has fighter and AI, and is not the player)
            if (entity.components.has(ComponentType.FIGHTER) and
                entity.components.has(ComponentType.AI) and
                entity != player):
                
                fighter = entity.components.get(ComponentType.FIGHTER)
                if fighter and fighter.hp > 0:
                    # Living monster - prioritize this!
                    living_monster = entity
                elif not dead_monster:
                    # Dead monster (corpse) - only use if no living monster
                    dead_monster = entity
    
    # Return living monster if found, otherwise return dead one
    return living_monster if living_monster else dead_monster


def get_sidebar_equipment_at_position(screen_x: int, screen_y: int, player, ui_layout) -> Optional[Any]:
    """Get the equipment item being hovered over in the sidebar equipment section.
    
    Args:
        screen_x: Mouse X position (screen coordinates)
        screen_y: Mouse Y position (screen coordinates)
        player: Player entity
        ui_layout: UILayoutConfig instance
        
    Returns:
        Equipment item entity if hovering over an equipment slot, None otherwise
    """
    # Verify mouse is in sidebar
    if not ui_layout.is_in_sidebar(screen_x, screen_y):
        return None
    
    # Check if player has equipment
    equipment = player.components.get(ComponentType.EQUIPMENT)
    if not equipment:
        return None
    
    padding = ui_layout.sidebar_padding
    
    # Calculate equipment section Y positions (must match sidebar.py!)
    y_cursor = 2   # Starting Y
    y_cursor += 2  # Title + spacing
    y_cursor += 2  # Separator + spacing
    y_cursor += 1  # "HOTKEYS" header
    y_cursor += 6  # 6 hotkey lines
    y_cursor += 1  # Spacing after hotkeys
    y_cursor += 1  # "EQUIPMENT" header
    equipment_start_y = y_cursor  # Should be 15
    
    # Equipment slots (must match sidebar.py order!)
    equipment_slots = [
        equipment.main_hand,
        equipment.off_hand,
        equipment.head,
        equipment.chest,
        equipment.feet,
    ]
    
    # Check if hovering over any equipment line
    for i, item in enumerate(equipment_slots):
        slot_y = equipment_start_y + i
        
        # Check if hovering over this equipment line
        if screen_y == slot_y and screen_x >= padding and screen_x < ui_layout.sidebar_width - padding:
            if item:  # Only return item if there's something equipped
                return item
    
    return None


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
    # Verify mouse is in sidebar
    if not ui_layout.is_in_sidebar(screen_x, screen_y):
        return None
    
    # Check if player has inventory
    inventory = player.components.get(ComponentType.INVENTORY)
    if not inventory:
        return None
    
    # Get unequipped items (same logic as sidebar rendering)
    equipped_items = set()
    equipment = player.components.get(ComponentType.EQUIPMENT)
    if equipment:
        for slot_item in [equipment.main_hand, equipment.off_hand,
                        equipment.head, equipment.chest, equipment.feet]:
            if slot_item:
                equipped_items.add(slot_item)
    
    inventory_items = [item for item in inventory.items if item not in equipped_items]
    
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
            return item
    
    return None


def render_tooltip(console, entity: Any, mouse_x: int, mouse_y: int, ui_layout) -> None:
    """Render a tooltip for an entity (item or monster) near the mouse cursor.
    
    The tooltip shows the full name and relevant stats/info.
    
    Args:
        console: Console to render to (viewport console for proper positioning)
        entity: The entity to show info for (item or monster)
        mouse_x: Mouse X position (screen coordinates)
        mouse_y: Mouse Y position (screen coordinates)
        ui_layout: UILayoutConfig instance
    """
    if not entity:
        return
    
    # Get full entity name
    entity_name = entity.get_display_name() if hasattr(entity, 'get_display_name') else entity.name
    
    # Build tooltip lines
    tooltip_lines = [entity_name]
    
    # Check if this is a monster (has fighter and AI)
    is_monster = (entity.components.has(ComponentType.FIGHTER) and 
                  entity.components.has(ComponentType.AI))
    
    if is_monster:
        # Monster tooltip - just show the name
        # TODO: Future enhancement - add a skill/ability that reveals detailed monster stats
        # (HP, AC, equipment, status effects, etc.)
        pass  # Name is already added above
    
    # Otherwise, show item information
    elif entity.components.has(ComponentType.WAND):
        tooltip_lines.append(f"Wand ({entity.wand.charges} charges)")
    elif entity.components.has(ComponentType.EQUIPPABLE):
        eq = entity.equippable
        
        # Weapon information
        if hasattr(eq, 'damage_dice') and eq.damage_dice:
            weapon_info = f"Weapon: {eq.damage_dice} damage"
            if hasattr(eq, 'to_hit_bonus') and eq.to_hit_bonus:
                weapon_info += f", +{eq.to_hit_bonus} to hit"
            tooltip_lines.append(weapon_info)
            
            # Reach info
            if hasattr(eq, 'reach') and eq.reach and eq.reach > 1:
                tooltip_lines.append(f"Range: {eq.reach} tiles")
            
            # Two-handed
            if hasattr(eq, 'two_handed') and eq.two_handed:
                tooltip_lines.append("Two-handed")
        
        # Armor information
        elif hasattr(eq, 'defense_bonus') and eq.defense_bonus:
            armor_info = f"Armor: +{eq.defense_bonus} AC"
            tooltip_lines.append(armor_info)
            
            # DEX cap for armor
            if hasattr(eq, 'max_dex_bonus') and eq.max_dex_bonus is not None:
                tooltip_lines.append(f"Max DEX bonus: +{eq.max_dex_bonus}")
        
        # Slot information
        if hasattr(eq, 'slot'):
            # slot is an EquipmentSlots enum, convert to string
            slot_str = str(eq.slot.value) if hasattr(eq.slot, 'value') else str(eq.slot)
            slot_name = slot_str.replace('_', ' ').title()
            tooltip_lines.append(f"Slot: {slot_name}")
    
    elif entity.components.has(ComponentType.ITEM):
        if entity.item.use_function:
            # Get function name for better description
            func_name = entity.item.use_function.__name__ if hasattr(entity.item.use_function, '__name__') else 'Unknown'
            
            if 'heal' in func_name:
                tooltip_lines.append("Consumable: Healing")
            elif 'lightning' in func_name:
                tooltip_lines.append("Scroll: Lightning Bolt")
            elif 'fireball' in func_name:
                tooltip_lines.append("Scroll: Fireball")
            elif 'confuse' in func_name:
                tooltip_lines.append("Scroll: Confusion")
            elif 'teleport' in func_name:
                tooltip_lines.append("Scroll: Teleportation")
            elif 'yo_mama' in func_name:
                tooltip_lines.append("Scroll: Yo Mama")
            elif 'slow' in func_name:
                tooltip_lines.append("Scroll: Slow")
            elif 'glue' in func_name:
                tooltip_lines.append("Scroll: Glue")
            elif 'rage' in func_name:
                tooltip_lines.append("Scroll: Rage")
            else:
                tooltip_lines.append("Consumable")
    
    # Calculate tooltip dimensions
    tooltip_width = max(len(line) for line in tooltip_lines) + 4  # +4 for padding
    tooltip_height = len(tooltip_lines) + 2  # +2 for borders
    
    # Position tooltip near mouse, but keep it on screen
    # Using screen coordinates directly since rendering to root console (0)
    tooltip_x = mouse_x + 2  # Offset slightly from cursor
    tooltip_y = mouse_y + 1
    
    # Adjust if tooltip would go off screen (using full screen dimensions)
    if tooltip_x + tooltip_width > ui_layout.screen_width:
        tooltip_x = ui_layout.screen_width - tooltip_width - 1
    if tooltip_y + tooltip_height > ui_layout.screen_height:
        tooltip_y = ui_layout.screen_height - tooltip_height - 1
    
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
    libtcod.console_set_default_background(console, libtcod.Color(40, 40, 40))
    
    # Top and bottom borders
    for x in range(tooltip_width):
        libtcod.console_put_char(console, tooltip_x + x, tooltip_y, ord('─'), libtcod.BKGND_SET)
        libtcod.console_put_char(console, tooltip_x + x, tooltip_y + tooltip_height - 1, ord('─'), libtcod.BKGND_SET)
    
    # Side borders
    for y in range(tooltip_height):
        libtcod.console_put_char(console, tooltip_x, tooltip_y + y, ord('│'), libtcod.BKGND_SET)
        libtcod.console_put_char(console, tooltip_x + tooltip_width - 1, tooltip_y + y, ord('│'), libtcod.BKGND_SET)
    
    # Corners
    libtcod.console_put_char(console, tooltip_x, tooltip_y, ord('┌'), libtcod.BKGND_SET)
    libtcod.console_put_char(console, tooltip_x + tooltip_width - 1, tooltip_y, ord('┐'), libtcod.BKGND_SET)
    libtcod.console_put_char(console, tooltip_x, tooltip_y + tooltip_height - 1, ord('└'), libtcod.BKGND_SET)
    libtcod.console_put_char(console, tooltip_x + tooltip_width - 1, tooltip_y + tooltip_height - 1, ord('┘'), libtcod.BKGND_SET)
    
    # Draw tooltip content
    libtcod.console_set_default_foreground(console, libtcod.Color(255, 255, 255))
    libtcod.console_set_default_background(console, libtcod.Color(40, 40, 40))
    for i, line in enumerate(tooltip_lines):
        libtcod.console_print_ex(
            console,
            tooltip_x + 2,  # Padding from left border
            tooltip_y + 1 + i,  # +1 for top border
            libtcod.BKGND_SET,  # BKGND_SET ensures solid background behind text
            libtcod.LEFT,
            line
        )

