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
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Any, Sequence, Tuple, List
import logging

from components.component_registry import ComponentType
from ui.sidebar_layout import calculate_sidebar_layout, get_hotkey_list, get_equipment_slot_list
from config.ui_layout import get_ui_layout
# Tooltip rendering works with FrameContext/HoverProbe from the renderer pipeline
from rendering.frame_models import FrameContext, HoverProbe

logger = logging.getLogger(__name__)


class TooltipAnchor(Enum):
    VIEWPORT = auto()
    SIDEBAR = auto()


class TooltipKind(Enum):
    NONE = auto()
    SINGLE = auto()
    MULTI = auto()


@dataclass
class TooltipModel:
    kind: TooltipKind
    lines: Sequence[str]
    anchor: TooltipAnchor = TooltipAnchor.VIEWPORT
    screen_position: Optional[Tuple[int, int]] = None
    world_position: Optional[Tuple[int, int]] = None
    entities: Sequence[Any] = ()


def _screen_to_console_coords(
    anchor: TooltipAnchor,
    screen_position: Tuple[int, int],
    ui_layout,
) -> Optional[Tuple[int, int, int, int]]:
    """Translate absolute screen coordinates into the local console space."""

    screen_x, screen_y = screen_position

    if anchor is TooltipAnchor.VIEWPORT:
        offset_x, offset_y = ui_layout.viewport_position
        width, height = ui_layout.viewport_width, ui_layout.viewport_height
    elif anchor is TooltipAnchor.SIDEBAR:
        offset_x, offset_y = ui_layout.sidebar_position
        width, height = ui_layout.sidebar_width, ui_layout.screen_height
    else:
        offset_x = offset_y = 0
        width, height = ui_layout.screen_width, ui_layout.screen_height

    local_x = screen_x - offset_x
    local_y = screen_y - offset_y

    # If the cursor isn't over the target console, bail out gracefully.
    if local_x < 0 or local_y < 0 or local_x >= width or local_y >= height:
        return None

    return local_x, local_y, width, height


def _render_lines_for_anchor(
    console,
    tooltip_lines: Sequence[str],
    screen_position: Tuple[int, int],
    anchor: TooltipAnchor,
    ui_layout,
) -> None:
    coords = _screen_to_console_coords(anchor, screen_position, ui_layout)
    if coords is None:
        return

    local_x, local_y, bounds_width, bounds_height = coords
    _draw_tooltip_box(console, tooltip_lines, local_x, local_y, bounds_width, bounds_height)


def resolve_hover(hover_probe: Optional[HoverProbe], frame_ctx: FrameContext) -> TooltipModel:
    """Resolve the hover state into a :class:`TooltipModel`.

    The resolver inspects sidebar regions first, then falls back to viewport
    entities gathered via :class:`HoverProbe`. The resulting model is a pure
    data description with no console references, enabling the renderer to draw
    tooltips after all world/UI composition has completed.
    """
    mouse = getattr(frame_ctx, "mouse", None)
    if mouse is None or not hasattr(mouse, "cx") or not hasattr(mouse, "cy"):
        return TooltipModel(TooltipKind.NONE, [], TooltipAnchor.VIEWPORT)

    try:
        screen_pos = (int(mouse.cx), int(mouse.cy))
    except (TypeError, ValueError):
        return TooltipModel(TooltipKind.NONE, [], TooltipAnchor.VIEWPORT)
    ui_layout = get_ui_layout()

    sidebar_entity = get_sidebar_equipment_at_position(screen_pos[0], screen_pos[1], frame_ctx.player, ui_layout)
    if not sidebar_entity:
        sidebar_entity = get_sidebar_item_at_position(screen_pos[0], screen_pos[1], frame_ctx.player, ui_layout)

    if sidebar_entity:
        lines = _build_single_entity_lines(sidebar_entity)
        return TooltipModel(
            kind=TooltipKind.SINGLE,
            lines=lines,
            anchor=TooltipAnchor.SIDEBAR,
            screen_position=screen_pos,
            world_position=None,
            entities=[sidebar_entity],
        )

    if hover_probe is None or hover_probe.world_position is None:
        return TooltipModel(
            kind=TooltipKind.NONE,
            lines=[],
            anchor=TooltipAnchor.VIEWPORT,
            screen_position=screen_pos,
            world_position=None,
            entities=(),
        )

    entities = list(hover_probe.entities)
    if not entities:
        return TooltipModel(
            kind=TooltipKind.NONE,
            lines=[],
            anchor=TooltipAnchor.VIEWPORT,
            screen_position=hover_probe.screen_position or screen_pos,
            world_position=hover_probe.world_position,
            entities=(),
        )

    screen_reference = hover_probe.screen_position or screen_pos

    if len(entities) == 1:
        lines = _build_single_entity_lines(entities[0])
        kind = TooltipKind.SINGLE
    else:
        lines = _build_multi_entity_lines(entities)
        kind = TooltipKind.MULTI

    return TooltipModel(
        kind=kind,
        lines=lines,
        anchor=TooltipAnchor.VIEWPORT,
        screen_position=screen_reference,
        world_position=hover_probe.world_position,
        entities=entities,
    )


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
    
    # Check FOV if provided (respect TOOLTIP_IGNORE_FOV debug flag)
    in_fov = True
    if TOOLTIP_IGNORE_FOV:
        # Debug mode: ignore FOV, show everything
        in_fov = True
        if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "TOOLTIP_FOV_CHECK: pos=(%d,%d) in_fov=%s TOOLTIP_IGNORE_FOV_ENABLED",
                world_x, world_y, in_fov
            )
    elif fov_map:
        # Normal mode: check FOV
        from fov_functions import map_is_in_fov
        in_fov = map_is_in_fov(fov_map, world_x, world_y)
        if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "TOOLTIP_FOV_CHECK: pos=(%d,%d) in_fov=%s fov_map_present=True",
                world_x, world_y, in_fov
            )
    else:
        # No FOV map provided
        if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "TOOLTIP_FOV_CHECK: pos=(%d,%d) in_fov=%s fov_map_provided=False",
                world_x, world_y, in_fov
            )

    if not in_fov:
        if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "TOOLTIP_FOV_FILTERED: pos=(%d,%d) entity_list_empty",
                world_x, world_y
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
                        "TOOLTIP_ENTITY_CLASSIFIED: pos=(%d,%d) name=%s category=corpse",
                        world_x, world_y, getattr(entity, "name", "UNNAMED")
                    )
            # Living monster: has FIGHTER + AI components (removed from corpses by kill_monster)
            elif (entity.components.has(ComponentType.FIGHTER) and
                  entity.components.has(ComponentType.AI)):
                living_monsters.append(entity)
                if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        "TOOLTIP_ENTITY_CLASSIFIED: pos=(%d,%d) name=%s category=living_monster",
                        world_x, world_y, getattr(entity, "name", "UNNAMED")
                    )
            # Items and interactables: items, chests, signposts, murals, and ground features
            elif (entity.components.has(ComponentType.ITEM) or
                  entity.components.has(ComponentType.CHEST) or
                  entity.components.has(ComponentType.SIGNPOST) or
                  entity.components.has(ComponentType.MURAL)):
                items.append(entity)
                if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        "TOOLTIP_ENTITY_CLASSIFIED: pos=(%d,%d) name=%s category=item_or_feature",
                        world_x, world_y, getattr(entity, "name", "UNNAMED")
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
            "TOOLTIP_ENTITIES_FINAL: pos=(%d,%d) count=%d names=%s",
            world_x, world_y, len(all_entities), entity_names
        )
    
    return all_entities


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


def _build_monster_tooltip_lines(entity: Any, tooltip_lines: List[str]) -> List[str]:
    """Build tooltip lines for a monster using the monster knowledge system.
    
    Phase 11: Uses MonsterInfoView to display tier-gated information
    about the monster based on player's accumulated knowledge.
    
    Args:
        entity: The monster entity
        tooltip_lines: Initial tooltip lines (starting with name)
        
    Returns:
        List[str]: Complete tooltip lines for the monster
    """
    try:
        from services.monster_knowledge import (
            get_monster_knowledge_system,
            get_monster_info_view,
            KnowledgeTier,
        )
        
        knowledge = get_monster_knowledge_system()
        info = get_monster_info_view(entity, knowledge)
        
        # Tier 0: Only name shown (already in tooltip_lines)
        if info.knowledge_tier == KnowledgeTier.UNKNOWN:
            tooltip_lines.append("???")
            return tooltip_lines
        
        # Tier 1+: Show faction and role
        info_parts = []
        if info.faction_label:
            info_parts.append(info.faction_label)
        if info.role_label:
            info_parts.append(info.role_label)
        if info_parts:
            tooltip_lines.append(" · ".join(info_parts))
        
        # Tier 1+: Show coarse speed if notable
        if info.speed_label and info.speed_label != "normal":
            tooltip_lines.append(f"Speed: {info.speed_label}")
        
        # Tier 2+: Show combat stats
        if info.knowledge_tier >= KnowledgeTier.BATTLED:
            if info.durability_label:
                tooltip_lines.append(f"Durability: {info.durability_label}")
            if info.damage_label:
                tooltip_lines.append(f"Damage: {info.damage_label}")
            if info.accuracy_label:
                tooltip_lines.append(f"Accuracy: {info.accuracy_label}")
            if info.evasion_label:
                tooltip_lines.append(f"Evasion: {info.evasion_label}")
        
        # Tier 3: Show warnings and advice
        if info.knowledge_tier >= KnowledgeTier.UNDERSTOOD:
            for warning in info.special_warnings:
                tooltip_lines.append(warning)
            if info.advice_line:
                tooltip_lines.append(f"💡 {info.advice_line}")
        
        # Always show equipment (regardless of tier) - it's visible
        equipment = entity.get_component_optional(ComponentType.EQUIPMENT)
        if equipment:
            if equipment.main_hand:
                weapon_name = (
                    equipment.main_hand.get_display_name()
                    if hasattr(equipment.main_hand, "get_display_name")
                    else equipment.main_hand.name.replace("_", " ").title()
                )
                tooltip_lines.append(f"Wielding: {weapon_name}")

            armor_pieces: List[str] = []
            for attr in ("off_hand", "chest", "head", "feet"):
                item = getattr(equipment, attr, None)
                if item:
                    name = (
                        item.get_display_name()
                        if hasattr(item, "get_display_name")
                        else item.name.replace("_", " ").title()
                    )
                    armor_pieces.append(name)

            if equipment.left_ring:
                ring_name = (
                    equipment.left_ring.get_display_name()
                    if hasattr(equipment.left_ring, "get_display_name")
                    else equipment.left_ring.name.replace("_", " ").title()
                )
                armor_pieces.append(f"L:{ring_name}")
            if equipment.right_ring:
                ring_name = (
                    equipment.right_ring.get_display_name()
                    if hasattr(equipment.right_ring, "get_display_name")
                    else equipment.right_ring.name.replace("_", " ").title()
                )
                armor_pieces.append(f"R:{ring_name}")

            if armor_pieces:
                tooltip_lines.append(f"Wearing: {', '.join(armor_pieces)}")
        
        return tooltip_lines
        
    except ImportError:
        # Fall back to basic monster info if knowledge system unavailable
        equipment = entity.get_component_optional(ComponentType.EQUIPMENT)
        if equipment:
            if equipment.main_hand:
                weapon_name = (
                    equipment.main_hand.get_display_name()
                    if hasattr(equipment.main_hand, "get_display_name")
                    else equipment.main_hand.name.replace("_", " ").title()
                )
                tooltip_lines.append(f"Wielding: {weapon_name}")

            armor_pieces: List[str] = []
            for attr in ("off_hand", "chest", "head", "feet"):
                item = getattr(equipment, attr, None)
                if item:
                    name = (
                        item.get_display_name()
                        if hasattr(item, "get_display_name")
                        else item.name.replace("_", " ").title()
                    )
                    armor_pieces.append(name)

            if equipment.left_ring:
                ring_name = (
                    equipment.left_ring.get_display_name()
                    if hasattr(equipment.left_ring, "get_display_name")
                    else equipment.left_ring.name.replace("_", " ").title()
                )
                armor_pieces.append(f"L:{ring_name}")
            if equipment.right_ring:
                ring_name = (
                    equipment.right_ring.get_display_name()
                    if hasattr(equipment.right_ring, "get_display_name")
                    else equipment.right_ring.name.replace("_", " ").title()
                )
                armor_pieces.append(f"R:{ring_name}")

            if armor_pieces:
                tooltip_lines.append(f"Wearing: {', '.join(armor_pieces)}")
        
        return tooltip_lines


def _build_single_entity_lines(entity: Any) -> List[str]:
    if not entity:
        return []

    entity_name = (
        entity.get_display_name() if hasattr(entity, "get_display_name") else getattr(entity, "name", "")
    )
    tooltip_lines: List[str] = [entity_name]

    is_monster = (
        entity.components.has(ComponentType.FIGHTER)
        and entity.components.has(ComponentType.AI)
    )
    is_chest = entity.components.has(ComponentType.CHEST)
    is_signpost = entity.components.has(ComponentType.SIGNPOST)
    is_mural = entity.components.has(ComponentType.MURAL)

    if is_mural or is_signpost:
        pass  # Name only
    elif is_chest:
        chest = entity.get_component_optional(ComponentType.CHEST)
        if chest:
            state_str = chest.state.name.lower() if hasattr(chest.state, "name") else str(chest.state)
            tooltip_lines.append(f"State: {state_str.capitalize()}")
            if chest.trap_type:
                tooltip_lines.append("⚠ Trapped!")
    elif is_monster:
        # Phase 11: Use MonsterInfoView for tier-gated monster information
        tooltip_lines = _build_monster_tooltip_lines(entity, tooltip_lines)
    elif entity.components.has(ComponentType.WAND):
        tooltip_lines.append(f"Wand ({entity.wand.charges} charges)")
    elif entity.components.has(ComponentType.EQUIPPABLE):
        eq = entity.equippable

        if hasattr(eq, "damage_dice") and eq.damage_dice:
            weapon_info = f"Weapon: {eq.damage_dice} damage"
            if hasattr(eq, "to_hit_bonus") and eq.to_hit_bonus:
                weapon_info += f", +{eq.to_hit_bonus} to hit"
            tooltip_lines.append(weapon_info)

            if hasattr(eq, "reach") and eq.reach and eq.reach > 1:
                tooltip_lines.append(f"Range: {eq.reach} tiles")
            if hasattr(eq, "two_handed") and eq.two_handed:
                tooltip_lines.append("Two-handed")
        elif hasattr(eq, "defense_bonus") and eq.defense_bonus:
            tooltip_lines.append(f"Armor: +{eq.defense_bonus} AC")
            if hasattr(eq, "max_dex_bonus") and eq.max_dex_bonus is not None:
                tooltip_lines.append(f"Max DEX bonus: +{eq.max_dex_bonus}")

        if hasattr(eq, "slot"):
            slot_str = eq.slot.value if hasattr(eq.slot, "value") else str(eq.slot)
            tooltip_lines.append(f"Slot: {str(slot_str).replace('_', ' ').title()}")
    elif entity.components.has(ComponentType.ITEM) and entity.item:
        if entity.item.use_function:
            if entity.item.identified:
                func_name = (
                    entity.item.use_function.__name__
                    if hasattr(entity.item.use_function, "__name__")
                    else ""
                )
                tooltip_lines.append(_describe_identified_item(func_name))
            else:
                tooltip_lines.append("Unidentified")

    return tooltip_lines


def _describe_identified_item(func_name: str) -> str:
    lookup = {
        "heal": "Consumable: Healing",
        "lightning": "Scroll: Lightning Bolt",
        "fireball": "Scroll: Fireball",
        "confuse": "Scroll: Confusion",
        "teleport": "Scroll: Teleportation",
        "yo_mama": "Scroll: Yo Mama",
        "slow": "Scroll: Slow",
        "glue": "Scroll: Glue",
        "rage": "Scroll: Rage",
        "speed": "Potion: Speed",
        "regeneration": "Potion: Regeneration",
        "invisibility": "Potion: Invisibility",
        "levitation": "Potion: Levitation",
        "protection": "Potion: Protection",
        "heroism": "Potion: Heroism",
        "weakness": "Potion: Weakness",
        "slowness": "Potion: Slowness",
        "blindness": "Potion: Blindness",
        "paralysis": "Potion: Paralysis",
        "experience": "Potion: Experience",
    }

    for key, label in lookup.items():
        if key in func_name:
            return label
    return "Consumable"


def _build_multi_entity_lines(entities: Sequence[Any]) -> List[str]:
    tooltip_lines: List[str] = []

    from ui.debug_flags import ENABLE_TOOLTIP_DEBUG

    if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
        entity_names = [getattr(e, "name", "unknown") for e in entities]
        logger.debug("TOOLTIP_MULTI_ENTITY_ORDER: names=%s", entity_names)

    for index, entity in enumerate(entities):
        if index > 0:
            tooltip_lines.append("---")

        entity_name = (
            entity.get_display_name() if hasattr(entity, "get_display_name") else getattr(entity, "name", "")
        )
        tooltip_lines.append(entity_name)

        is_monster = (
            entity.components.has(ComponentType.FIGHTER)
            and entity.components.has(ComponentType.AI)
        )

        if is_monster:
            # Phase 11: Use monster knowledge system for tier-gated info
            try:
                from services.monster_knowledge import (
                    get_monster_knowledge_system,
                    get_monster_info_view,
                    KnowledgeTier,
                )
                
                knowledge = get_monster_knowledge_system()
                info = get_monster_info_view(entity, knowledge)
                
                # Show faction/role for Tier 1+
                if info.knowledge_tier >= KnowledgeTier.OBSERVED:
                    info_parts = []
                    if info.faction_label:
                        info_parts.append(info.faction_label)
                    if info.role_label:
                        info_parts.append(info.role_label)
                    if info_parts:
                        tooltip_lines.append(f"  {' · '.join(info_parts)}")
                elif info.knowledge_tier == KnowledgeTier.UNKNOWN:
                    tooltip_lines.append("  ???")
            except ImportError:
                pass  # Fall through to equipment display
            
            # Always show equipment
            equipment = entity.get_component_optional(ComponentType.EQUIPMENT)
            if equipment:
                if equipment.main_hand:
                    weapon_name = (
                        equipment.main_hand.get_display_name()
                        if hasattr(equipment.main_hand, "get_display_name")
                        else equipment.main_hand.name.replace("_", " ").title()
                    )
                    tooltip_lines.append(f"  Wielding: {weapon_name}")
                if equipment.off_hand:
                    armor_name = (
                        equipment.off_hand.get_display_name()
                        if hasattr(equipment.off_hand, "get_display_name")
                        else equipment.off_hand.name.replace("_", " ").title()
                    )
                    tooltip_lines.append(f"  Wearing: {armor_name}")
                elif equipment.chest:
                    armor_name = (
                        equipment.chest.get_display_name()
                        if hasattr(equipment.chest, "get_display_name")
                        else equipment.chest.name.replace("_", " ").title()
                    )
                    tooltip_lines.append(f"  Wearing: {armor_name}")
        elif entity.components.has(ComponentType.CHEST):
            chest = entity.get_component_optional(ComponentType.CHEST)
            if chest:
                state_str = chest.state.name.lower() if hasattr(chest.state, "name") else str(chest.state)
                state_label = f"[{state_str.capitalize()}]"
                if chest.trap_type:
                    state_label += " ⚠"
                tooltip_lines.append(f"  {state_label}")
        elif entity.components.has(ComponentType.SIGNPOST):
            tooltip_lines.append("  [Sign]")
        elif entity.components.has(ComponentType.MURAL):
            tooltip_lines.append("  [Mural]")
        elif entity.components.has(ComponentType.WAND):
            tooltip_lines.append(f"  Wand ({entity.wand.charges} charges)")
        elif entity.components.has(ComponentType.EQUIPPABLE):
            eq = entity.equippable
            if hasattr(eq, "damage_dice") and eq.damage_dice:
                tooltip_lines.append(f"  Damage: {eq.damage_dice}")
            elif hasattr(eq, "defense_bonus") and eq.defense_bonus:
                tooltip_lines.append(f"  +{eq.defense_bonus} AC")
        elif entity.components.has(ComponentType.ITEM):
            tooltip_lines.append("  Consumable")

    return tooltip_lines


def _draw_tooltip_box(
    console,
    tooltip_lines: Sequence[str],
    mouse_x: int,
    mouse_y: int,
    bounds_width: int,
    bounds_height: int,
) -> None:
    if not tooltip_lines:
        return

    tooltip_width = max(len(line) for line in tooltip_lines) + 4
    tooltip_height = len(tooltip_lines) + 2

    from ui.debug_flags import ENABLE_TOOLTIP_DEBUG

    if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "TOOLTIP_GEOMETRY_RAW: mouse=(%d,%d) w=%d h=%d",
            mouse_x,
            mouse_y,
            tooltip_width,
            tooltip_height,
        )

    tooltip_x = mouse_x + 2
    tooltip_y = mouse_y + 1

    if tooltip_x + tooltip_width > bounds_width:
        tooltip_x = bounds_width - tooltip_width - 1
    if tooltip_y + tooltip_height > bounds_height:
        tooltip_y = bounds_height - tooltip_height - 1

    tooltip_x = max(1, tooltip_x)
    tooltip_y = max(1, tooltip_y)

    if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "TOOLTIP_GEOMETRY_CLAMPED: x=%d y=%d w=%d h=%d",
            tooltip_x,
            tooltip_y,
            tooltip_width,
            tooltip_height,
        )

    for y in range(tooltip_height):
        for x in range(tooltip_width):
            libtcod.console_put_char(console, tooltip_x + x, tooltip_y + y, ord(' '), libtcod.BKGND_SET)
            libtcod.console_set_char_background(
                console,
                tooltip_x + x,
                tooltip_y + y,
                libtcod.Color(40, 40, 40),
                libtcod.BKGND_SET,
            )

    libtcod.console_set_default_foreground(console, libtcod.Color(200, 200, 200))
    libtcod.console_set_default_background(console, libtcod.Color(40, 40, 40))

    for x in range(tooltip_width):
        libtcod.console_put_char(console, tooltip_x + x, tooltip_y, ord('─'), libtcod.BKGND_SET)
        libtcod.console_put_char(
            console, tooltip_x + x, tooltip_y + tooltip_height - 1, ord('─'), libtcod.BKGND_SET
        )

    for y in range(tooltip_height):
        libtcod.console_put_char(console, tooltip_x, tooltip_y + y, ord('│'), libtcod.BKGND_SET)
        libtcod.console_put_char(
            console, tooltip_x + tooltip_width - 1, tooltip_y + y, ord('│'), libtcod.BKGND_SET
        )

    libtcod.console_put_char(console, tooltip_x, tooltip_y, ord('┌'), libtcod.BKGND_SET)
    libtcod.console_put_char(console, tooltip_x + tooltip_width - 1, tooltip_y, ord('┐'), libtcod.BKGND_SET)
    libtcod.console_put_char(
        console, tooltip_x, tooltip_y + tooltip_height - 1, ord('└'), libtcod.BKGND_SET
    )
    libtcod.console_put_char(
        console,
        tooltip_x + tooltip_width - 1,
        tooltip_y + tooltip_height - 1,
        ord('┘'),
        libtcod.BKGND_SET,
    )

    libtcod.console_set_default_foreground(console, libtcod.Color(255, 255, 255))
    libtcod.console_set_default_background(console, libtcod.Color(40, 40, 40))
    for idx, line in enumerate(tooltip_lines):
        libtcod.console_print_ex(
            console,
            tooltip_x + 2,
            tooltip_y + 1 + idx,
            libtcod.BKGND_SET,
            libtcod.LEFT,
            line,
        )


def render_tooltip(console, entity: Any, mouse_x: int, mouse_y: int, ui_layout) -> None:
    if not entity:
        return

    tooltip_lines = _build_single_entity_lines(entity)
    screen_pos = (int(mouse_x), int(mouse_y))
    _render_lines_for_anchor(console, tooltip_lines, screen_pos, TooltipAnchor.VIEWPORT, ui_layout)


def render_multi_entity_tooltip(console, entities: list, mouse_x: int, mouse_y: int, ui_layout) -> None:
    if not entities:
        return

    tooltip_lines = _build_multi_entity_lines(entities)
    screen_pos = (int(mouse_x), int(mouse_y))
    _render_lines_for_anchor(console, tooltip_lines, screen_pos, TooltipAnchor.VIEWPORT, ui_layout)


def render(model: TooltipModel, viewport_console, sidebar_console) -> None:
    """Draw the tooltip described by ``model`` onto the supplied console."""
    if model.kind == TooltipKind.NONE or model.screen_position is None:
        return

    target_console = viewport_console if model.anchor is TooltipAnchor.VIEWPORT else sidebar_console
    if target_console is None:
        return

    mouse_x, mouse_y = model.screen_position
    ui_layout = get_ui_layout()

    if model.lines:
        tooltip_lines = list(model.lines)
    elif model.kind == TooltipKind.MULTI:
        tooltip_lines = _build_multi_entity_lines(model.entities)
    else:
        entity = model.entities[0] if model.entities else None
        tooltip_lines = _build_single_entity_lines(entity)

    _render_lines_for_anchor(target_console, tooltip_lines, (mouse_x, mouse_y), model.anchor, ui_layout)



