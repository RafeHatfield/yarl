"""Tooltip rendering system.

Provides hover tooltips for UI elements, particularly for items in the sidebar
that have abbreviated names, and for items on the ground in the viewport.

TOOLTIP STABILITY GUARANTEE:
  Tooltip content is deterministic and stable per frame. Entity ordering within
  a tile is consistent (not dependent on non-deterministic list iteration). This
  prevents flickering when multiple entities (e.g., item + corpse) share the same tile.

FEATURE TOOLTIP BEHAVIOR:
  - Murals: Show only name/label in hover tooltip. Full mural text shown in message log on examine.
  - Signposts: Show only name/label in hover tooltip. Full message shown in message log on read.
  - Chests: Show name, state (open/closed/locked), and trap indicator in hover tooltip.
  
This short-label approach ensures stable, non-flickering tooltips and prevents information
overload during exploration. Full lore/story text is reserved for interaction messages.
"""

import tcod.libtcodpy as libtcod
from typing import Optional, Any
import logging

from components.component_registry import ComponentType
from ui.sidebar_layout import calculate_sidebar_layout, get_hotkey_list, get_equipment_slot_list
from io_layer.console_renderer import get_last_frame_counter

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


def get_all_entities_at_position(world_x: int, world_y: int, entities: list, player, fov_map=None) -> list:
    """Get ALL entities at the specified world coordinates.
    
    Returns living monsters, items (including chests, signposts, murals, and other interactables),
    and corpses at the position, prioritized in that order for display purposes.
    Entities within each category are sorted deterministically to ensure stable tooltip content across frames.
    
    CRITICAL: The ordering within each category (monsters, items, corpses) is deterministic
    and stable per frame. This prevents tooltip flickering when multiple entities
    occupy the same tile (e.g., weapon on top of corpse).
    
    CORPSE DETECTION: A corpse is identified by render_order == RenderOrder.CORPSE.
    This is set by kill_monster() when a monster dies, regardless of component state.
    
    ITEMS BUCKET: Includes:
      - Items (ComponentType.ITEM)
      - Chests (ComponentType.CHEST)
      - Signposts (ComponentType.SIGNPOST)
      - Murals (ComponentType.MURAL)
      - Any other ground features/interactables
    
    Args:
        world_x: X coordinate in world space
        world_y: Y coordinate in world space
        entities: List of all entities in the game
        player: Player entity (to exclude from results)
        fov_map: Optional FOV map to check visibility
        
    Returns:
        List of entities at this position, ordered by priority (living monsters first, then items/features, then corpses)
        Entities within each category are sorted deterministically by (render_order, name, id).
    """
    # Import RenderOrder for corpse detection
    from render_functions import RenderOrder
    from ui.debug_flags import ENABLE_TOOLTIP_DEBUG, TOOLTIP_IGNORE_FOV
    
    frame_id = get_last_frame_counter()
    
    # Check FOV if provided (respect TOOLTIP_IGNORE_FOV debug flag)
    in_fov = True
    if TOOLTIP_IGNORE_FOV:
        # Debug mode: ignore FOV, show everything
        in_fov = True
        if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "TOOLTIP_FOV_CHECK: frame=%d pos=(%d,%d) in_fov=%s TOOLTIP_IGNORE_FOV_ENABLED",
                frame_id, world_x, world_y, in_fov
            )
    elif fov_map:
        # Normal mode: check FOV
        from fov_functions import map_is_in_fov
        in_fov = map_is_in_fov(fov_map, world_x, world_y)
        if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "TOOLTIP_FOV_CHECK: frame=%d pos=(%d,%d) in_fov=%s fov_map_present=True",
                frame_id, world_x, world_y, in_fov
            )
    else:
        # No FOV map provided
        if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "TOOLTIP_FOV_CHECK: frame=%d pos=(%d,%d) in_fov=%s fov_map_provided=False",
                frame_id, world_x, world_y, in_fov
            )
    
    if not in_fov:
        if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "TOOLTIP_FOV_FILTERED: frame=%d pos=(%d,%d) entity_list_empty",
                frame_id, world_x, world_y
            )
        return []
    
    living_monsters = []
    items = []  # Includes chests, signposts, murals, and other interactables
    corpses = []
    
    for entity in entities:
        if entity.x == world_x and entity.y == world_y and entity != player:
            # Corpse detection: check render_order == CORPSE (not component state)
            if getattr(entity, 'render_order', None) == RenderOrder.CORPSE:
                corpses.append(entity)
                if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        "TOOLTIP_ENTITY_CLASSIFIED: frame=%d pos=(%d,%d) name=%s category=corpse",
                        frame_id, world_x, world_y, getattr(entity, "name", "UNNAMED")
                    )
            # Living monster: has FIGHTER + AI components (removed from corpses by kill_monster)
            elif (entity.components.has(ComponentType.FIGHTER) and
                  entity.components.has(ComponentType.AI)):
                living_monsters.append(entity)
                if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        "TOOLTIP_ENTITY_CLASSIFIED: frame=%d pos=(%d,%d) name=%s category=living_monster",
                        frame_id, world_x, world_y, getattr(entity, "name", "UNNAMED")
                    )
            # Items and interactables: items, chests, signposts, murals, and ground features
            elif (entity.components.has(ComponentType.ITEM) or
                  entity.components.has(ComponentType.CHEST) or
                  entity.components.has(ComponentType.SIGNPOST) or
                  entity.components.has(ComponentType.MURAL)):
                items.append(entity)
                if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        "TOOLTIP_ENTITY_CLASSIFIED: frame=%d pos=(%d,%d) name=%s category=item_or_feature",
                        frame_id, world_x, world_y, getattr(entity, "name", "UNNAMED")
                    )
            # Other entities are ignored (no tooltip)
    
    # Sort each category deterministically to ensure stable tooltip content
    # Use (render_order, name, id) as sort key for consistent ordering across frames
    def _sort_key(e):
        # Handle entities without render_order gracefully
        render_order = getattr(getattr(e, "render_order", None), "value", 0)
        name = getattr(e, 'name', '')
        entity_id = id(e)
        return (render_order, name, entity_id)
    
    living_monsters.sort(key=_sort_key)
    items.sort(key=_sort_key)
    corpses.sort(key=_sort_key)
    
    # Return in priority order: living monsters, then items, then corpses
    all_entities = living_monsters + items + corpses
    
    if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
        entity_names = [getattr(e, "name", "UNNAMED") for e in all_entities]
        logger.debug(
            "TOOLTIP_ENTITIES_FINAL: frame=%d pos=(%d,%d) count=%d names=%s",
            frame_id, world_x, world_y, len(all_entities), entity_names
        )
    
    return all_entities


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
                
                fighter = entity.get_component_optional(ComponentType.FIGHTER)
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
    equipment = player.get_component_optional(ComponentType.EQUIPMENT)
    if not equipment:
        return None
    
    padding = ui_layout.sidebar_padding
    
    # Get centralized layout positions
    hotkey_list = get_hotkey_list()
    slot_list = get_equipment_slot_list()
    layout = calculate_sidebar_layout(hotkey_count=len(hotkey_list), equipment_slot_count=len(slot_list))
    
    equipment_start_y = layout.equipment_start_y
    
    # Build equipment slots from player's equipment (using centralized slot list)
    equipment_slots = [getattr(equipment, slot_name) for slot_name in slot_list]
    
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
    inventory = player.get_component_optional(ComponentType.INVENTORY)
    if not inventory:
        return None
    
    # Get unequipped items (same logic as sidebar rendering)
    equipped_items = set()
    equipment = player.get_component_optional(ComponentType.EQUIPMENT)
    if equipment:
        for slot_item in [equipment.main_hand, equipment.off_hand,
                        equipment.head, equipment.chest, equipment.feet,
                        equipment.left_ring, equipment.right_ring]:
            if slot_item:
                equipped_items.add(slot_item)
    
    inventory_items = [item for item in inventory.items if item not in equipped_items]
    
    # IMPORTANT: Sort alphabetically to match sidebar rendering!
    # This ensures tooltip coordinates align with displayed items
    # Use display name for proper sorting of unidentified items
    inventory_items = sorted(inventory_items, key=lambda item: item.get_display_name().lower())
    
    if len(inventory_items) == 0:
        return None
    
    # Get centralized layout positions
    padding = ui_layout.sidebar_padding
    hotkey_list = get_hotkey_list()
    slot_list = get_equipment_slot_list()
    layout = calculate_sidebar_layout(hotkey_count=len(hotkey_list), equipment_slot_count=len(slot_list))
    
    inventory_start_y = layout.inventory_start_y
    
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
    
    # Get frame ID for correlation in logs
    frame_id = get_last_frame_counter()
    
    # Get full entity name
    entity_name = entity.get_display_name() if hasattr(entity, 'get_display_name') else entity.name
    
    # Build tooltip lines
    tooltip_lines = [entity_name]
    
    # Check if this is a monster (has fighter and AI)
    is_monster = (entity.components.has(ComponentType.FIGHTER) and 
                  entity.components.has(ComponentType.AI))
    
    # Check for chest, signpost, mural
    is_chest = entity.components.has(ComponentType.CHEST)
    is_signpost = entity.components.has(ComponentType.SIGNPOST)
    is_mural = entity.components.has(ComponentType.MURAL)
    
    if is_mural:
        # Hover tooltip for mural: show only short label (no lore text)
        # Full mural text is shown in message log when player interacts/examines
        # Just the name is shown in the tooltip
        pass  # Name already in tooltip_lines[0]
    elif is_signpost:
        # Hover tooltip for signpost: show only short label (no message text)
        # Full message is shown in message log when player interacts/reads
        # Just the name is shown in the tooltip
        pass  # Name already in tooltip_lines[0]
    elif is_chest:
        # Show chest state and trap info (concise)
        chest = entity.get_component_optional(ComponentType.CHEST)
        if chest:
            state_str = chest.state.name.lower() if hasattr(chest.state, 'name') else str(chest.state)
            tooltip_lines.append(f"State: {state_str.capitalize()}")
            if chest.trap_type:
                tooltip_lines.append(f"⚠ Trapped!")
    elif is_monster:
        # Monster tooltip - show name and equipment
        # Check if monster has equipment
        if entity.components.has(ComponentType.EQUIPMENT):
            equipment = entity.get_component_optional(ComponentType.EQUIPMENT)
            if equipment:
                # Show wielded weapon
                if equipment.main_hand:
                    weapon_name = (equipment.main_hand.get_display_name() 
                                 if hasattr(equipment.main_hand, 'get_display_name') 
                                 else equipment.main_hand.name.replace('_', ' ').title())
                    tooltip_lines.append(f"Wielding: {weapon_name}")
                
                # Show worn armor (check all armor slots)
                armor_pieces = []
                if equipment.off_hand:
                    armor_name = (equipment.off_hand.get_display_name() 
                                if hasattr(equipment.off_hand, 'get_display_name') 
                                else equipment.off_hand.name.replace('_', ' ').title())
                    armor_pieces.append(armor_name)
                if equipment.chest:
                    armor_name = (equipment.chest.get_display_name() 
                                if hasattr(equipment.chest, 'get_display_name') 
                                else equipment.chest.name.replace('_', ' ').title())
                    armor_pieces.append(armor_name)
                if equipment.head:
                    armor_name = (equipment.head.get_display_name() 
                                if hasattr(equipment.head, 'get_display_name') 
                                else equipment.head.name.replace('_', ' ').title())
                    armor_pieces.append(armor_name)
                if equipment.feet:
                    armor_name = (equipment.feet.get_display_name() 
                                if hasattr(equipment.feet, 'get_display_name') 
                                else equipment.feet.name.replace('_', ' ').title())
                    armor_pieces.append(armor_name)
                if equipment.left_ring:
                    ring_name = (equipment.left_ring.get_display_name() 
                                if hasattr(equipment.left_ring, 'get_display_name') 
                                else equipment.left_ring.name.replace('_', ' ').title())
                    armor_pieces.append(f"L:{ring_name}")
                if equipment.right_ring:
                    ring_name = (equipment.right_ring.get_display_name() 
                                if hasattr(equipment.right_ring, 'get_display_name') 
                                else equipment.right_ring.name.replace('_', ' ').title())
                    armor_pieces.append(f"R:{ring_name}")
                
                if armor_pieces:
                    tooltip_lines.append(f"Wearing: {', '.join(armor_pieces)}")
    
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
    
    elif entity.components.has(ComponentType.ITEM) and entity.item:
        if entity.item.use_function:
            # Only reveal function details if item is identified
            if entity.item.identified:
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
                elif 'speed' in func_name:
                    tooltip_lines.append("Potion: Speed")
                elif 'regeneration' in func_name:
                    tooltip_lines.append("Potion: Regeneration")
                elif 'invisibility' in func_name:
                    tooltip_lines.append("Potion: Invisibility")
                elif 'levitation' in func_name:
                    tooltip_lines.append("Potion: Levitation")
                elif 'protection' in func_name:
                    tooltip_lines.append("Potion: Protection")
                elif 'heroism' in func_name:
                    tooltip_lines.append("Potion: Heroism")
                elif 'weakness' in func_name:
                    tooltip_lines.append("Potion: Weakness")
                elif 'slowness' in func_name:
                    tooltip_lines.append("Potion: Slowness")
                elif 'blindness' in func_name:
                    tooltip_lines.append("Potion: Blindness")
                elif 'paralysis' in func_name:
                    tooltip_lines.append("Potion: Paralysis")
                elif 'experience' in func_name:
                    tooltip_lines.append("Potion: Experience")
                else:
                    tooltip_lines.append("Consumable")
            else:
                # Unidentified - don't reveal what it does!
                tooltip_lines.append("Unidentified")
    
    # Calculate tooltip dimensions
    tooltip_width = max(len(line) for line in tooltip_lines) + 4  # +4 for padding
    tooltip_height = len(tooltip_lines) + 2  # +2 for borders
    
    # DEBUG: Log tooltip content for flicker diagnosis
    from ui.debug_flags import ENABLE_TOOLTIP_DEBUG
    if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "TOOLTIP_SINGLE_CONTENT: frame=%d mouse=(%d,%d) entity=%s lines=%r",
            frame_id, mouse_x, mouse_y, getattr(entity, "name", None), tooltip_lines
        )
    
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
    
    # DEBUG: Log final tooltip geometry after clamping
    if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "TOOLTIP_SINGLE_GEOM: frame=%d x=%d y=%d w=%d h=%d",
            frame_id, tooltip_x, tooltip_y, tooltip_width, tooltip_height
        )
    
    # Draw tooltip background (set both char AND background to ensure clean rendering)
    for y in range(tooltip_height):
        for x in range(tooltip_width):
            # Clear the character (replace with space) to prevent text bleed-through
            libtcod.console_put_char(console, tooltip_x + x, tooltip_y + y, ord(' '), libtcod.BKGND_SET)
            # Set the background color
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


def render_multi_entity_tooltip(console, entities: list, mouse_x: int, mouse_y: int, ui_layout) -> None:
    """Render a tooltip showing multiple entities at the same location.
    
    Shows all entities at a tile: living monsters, items, and corpses.
    
    Args:
        console: Console to render to (usually root console 0)
        entities: List of entities to show (already filtered to same position)
        mouse_x: Mouse X position (screen coordinates)
        mouse_y: Mouse Y position (screen coordinates)
        ui_layout: UILayoutConfig instance
    """
    if not entities:
        return
    
    # Get frame ID for correlation in logs
    frame_id = get_last_frame_counter()
    from ui.debug_flags import ENABLE_TOOLTIP_DEBUG
    
    # Build tooltip lines showing all entities
    tooltip_lines = []
    
    # DEBUG: Log entity ordering for tooltip consistency checking
    if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
        entity_names = [getattr(e, 'name', 'unknown') for e in entities]
        logger.debug(
            "TOOLTIP_MULTI_ENTITY: frame=%d mouse=(%d,%d) count=%d names=%s",
            frame_id, mouse_x, mouse_y, len(entities), entity_names
        )
    
    for i, entity in enumerate(entities):
        # Add separator between entities (except before first)
        if i > 0:
            tooltip_lines.append("---")
        
        # Get entity name
        entity_name = entity.get_display_name() if hasattr(entity, 'get_display_name') else entity.name
        tooltip_lines.append(entity_name)
        
        # Check if this is a monster
        is_monster = (entity.components.has(ComponentType.FIGHTER) and 
                      entity.components.has(ComponentType.AI))
        
        if is_monster:
            # Show equipment for monsters
            if entity.components.has(ComponentType.EQUIPMENT):
                equipment = entity.get_component_optional(ComponentType.EQUIPMENT)
                if equipment:
                    if equipment.main_hand:
                        weapon_name = (equipment.main_hand.get_display_name() 
                                     if hasattr(equipment.main_hand, 'get_display_name') 
                                     else equipment.main_hand.name.replace('_', ' ').title())
                        tooltip_lines.append(f"  Wielding: {weapon_name}")
                    if equipment.off_hand:
                        armor_name = (equipment.off_hand.get_display_name() 
                                    if hasattr(equipment.off_hand, 'get_display_name') 
                                    else equipment.off_hand.name.replace('_', ' ').title())
                        tooltip_lines.append(f"  Wearing: {armor_name}")
                    elif equipment.chest:
                        armor_name = (equipment.chest.get_display_name() 
                                    if hasattr(equipment.chest, 'get_display_name') 
                                    else equipment.chest.name.replace('_', ' ').title())
                        tooltip_lines.append(f"  Wearing: {armor_name}")
        
        # Show chest information (short label only in multi-entity view)
        elif entity.components.has(ComponentType.CHEST):
            chest = entity.get_component_optional(ComponentType.CHEST)
            if chest:
                # Show chest state (concise for multi-entity tooltip)
                state_str = chest.state.name.lower() if hasattr(chest.state, 'name') else str(chest.state)
                state_label = f"[{state_str.capitalize()}]"
                if chest.trap_type:
                    state_label += " ⚠"
                tooltip_lines.append(f"  {state_label}")
        
        # Show signpost information (short label only)
        elif entity.components.has(ComponentType.SIGNPOST):
            # No full message text in hover tooltip - only shown on interaction
            tooltip_lines.append(f"  [Sign]")
        
        # Show mural information (short label only)
        elif entity.components.has(ComponentType.MURAL):
            # No full mural text in hover tooltip - only shown on interaction
            tooltip_lines.append(f"  [Mural]")
        
        # Show item information (abbreviated for multi-entity display)
        elif entity.components.has(ComponentType.WAND):
            tooltip_lines.append(f"  Wand ({entity.wand.charges} charges)")
        elif entity.components.has(ComponentType.EQUIPPABLE):
            eq = entity.equippable
            if hasattr(eq, 'damage_dice') and eq.damage_dice:
                tooltip_lines.append(f"  {eq.damage_dice} damage")
            elif hasattr(eq, 'defense_bonus') and eq.defense_bonus:
                tooltip_lines.append(f"  +{eq.defense_bonus} AC")
        elif entity.components.has(ComponentType.ITEM):
            # Just show it's consumable (abbreviated)
            tooltip_lines.append(f"  Consumable")
    
    # Calculate tooltip dimensions
    tooltip_width = max(len(line) for line in tooltip_lines) + 4
    tooltip_height = len(tooltip_lines) + 2
    
    # DEBUG: Log final tooltip content for consistency checking
    if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "TOOLTIP_MULTI_CONTENT: frame=%d lines=%r",
            frame_id, tooltip_lines
        )
    
    # Position tooltip near mouse, but keep it on screen
    tooltip_x = mouse_x + 2
    tooltip_y = mouse_y + 1
    
    if tooltip_x + tooltip_width > ui_layout.screen_width:
        tooltip_x = ui_layout.screen_width - tooltip_width - 1
    if tooltip_y + tooltip_height > ui_layout.screen_height:
        tooltip_y = ui_layout.screen_height - tooltip_height - 1
    if tooltip_x < 1:
        tooltip_x = 1
    if tooltip_y < 1:
        tooltip_y = 1
    
    # DEBUG: Log final geometry after clamping
    if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "TOOLTIP_MULTI_GEOM: frame=%d x=%d y=%d w=%d h=%d",
            frame_id, tooltip_x, tooltip_y, tooltip_width, tooltip_height
        )
    
    # Draw tooltip background
    for y in range(tooltip_height):
        for x in range(tooltip_width):
            libtcod.console_put_char(console, tooltip_x + x, tooltip_y + y, ord(' '), libtcod.BKGND_SET)
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
    
    for x in range(tooltip_width):
        libtcod.console_put_char(console, tooltip_x + x, tooltip_y, ord('─'), libtcod.BKGND_SET)
        libtcod.console_put_char(console, tooltip_x + x, tooltip_y + tooltip_height - 1, ord('─'), libtcod.BKGND_SET)
    
    for y in range(tooltip_height):
        libtcod.console_put_char(console, tooltip_x, tooltip_y + y, ord('│'), libtcod.BKGND_SET)
        libtcod.console_put_char(console, tooltip_x + tooltip_width - 1, tooltip_y + y, ord('│'), libtcod.BKGND_SET)
    
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
            tooltip_x + 2,
            tooltip_y + 1 + i,
            libtcod.BKGND_SET,
            libtcod.LEFT,
            line
        )

