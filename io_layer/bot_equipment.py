"""Bot equipment evaluation and auto-equip logic.

This module provides simple heuristics for the bot to evaluate and automatically
equip better weapons and armor. This only applies in --bot mode and does not
affect manual (human) play.

Design Philosophy:
- Simple, deterministic scoring based on existing item stats
- Prefer strictly "better" items according to the game's stat model
- No complex optimization; just "better than randomly equipped"
- Clear documentation of scoring logic

Scoring Logic:
- Weapons: Prioritize average damage, then to-hit bonus, then reach
- Armor: Prioritize AC bonus, then average defense, then armor type tier
"""

import logging
from typing import Any, Optional, List
from equipment_slots import EquipmentSlots
from components.component_registry import ComponentType

logger = logging.getLogger(__name__)

# Configuration constant for periodic re-equip check
# Bot will re-evaluate equipment every N turns when in EXPLORE state
REEQUIP_CHECK_INTERVAL = 10


def evaluate_weapon(item: Any) -> int:
    """Evaluate a weapon's overall power and return a numeric score.
    
    Scoring Formula:
    1. Average damage (primary factor): avg(damage_min, damage_max) * 100
       - Or calculate from damage_dice if available (e.g., "1d6" = 3.5 avg)
    2. To-hit bonus (accuracy): to_hit_bonus * 10
    3. Reach (tactical advantage): (reach - 1) * 5
    4. Power bonus: power_bonus * 10
    
    Higher scores = better weapons. Ties broken by to-hit, then reach.
    
    Args:
        item: Entity with equippable component (weapon)
        
    Returns:
        int: Weapon power score (higher is better), or 0 if not a weapon
    
    Examples:
        - Dagger (1d4, +1 to-hit): 250 + 10 = 260
        - Shortsword (1d6, +1 to-hit): 350 + 10 = 360
        - Longsword (1d8, +0 to-hit): 450
        - Greatsword (2d6, two-handed): 700
    """
    if not item or not hasattr(item, 'equippable') or not item.equippable:
        return 0
    
    equippable = item.equippable
    
    # Only score weapons (main_hand or off_hand items with damage)
    if equippable.slot not in [EquipmentSlots.MAIN_HAND, EquipmentSlots.OFF_HAND]:
        return 0
    
    if equippable.damage_min <= 0 and equippable.damage_max <= 0:
        return 0  # Not a weapon (e.g., a shield in off_hand)
    
    score = 0
    
    # 1. Average damage (primary factor)
    if equippable.damage_dice:
        # Parse dice notation to get average damage
        # e.g., "1d4" = (1+4)/2 = 2.5, "2d6" = 2*(1+6)/2 = 7
        try:
            avg_damage = _calculate_average_damage_from_dice(equippable.damage_dice)
            score += int(avg_damage * 100)
        except (ValueError, AttributeError):
            # Fall back to damage_min/max if dice parsing fails
            avg_damage = (equippable.damage_min + equippable.damage_max) / 2.0
            score += int(avg_damage * 100)
    else:
        # Use damage_min/max range
        avg_damage = (equippable.damage_min + equippable.damage_max) / 2.0
        score += int(avg_damage * 100)
    
    # 2. To-hit bonus (accuracy)
    if equippable.to_hit_bonus:
        score += equippable.to_hit_bonus * 10
    
    # 3. Reach (tactical advantage for spears, etc.)
    if equippable.reach > 1:
        score += (equippable.reach - 1) * 5
    
    # 4. Power bonus
    if equippable.power_bonus:
        score += equippable.power_bonus * 10
    
    return score


def evaluate_armor(item: Any) -> int:
    """Evaluate an armor piece's defensive value and return a numeric score.
    
    Scoring Formula:
    1. Armor Class bonus (primary factor): armor_class_bonus * 100
    2. Average defense: avg(defense_min, defense_max) * 10
    3. Defense bonus: defense_bonus * 10
    4. Armor type tier bonus:
       - light: +10 (no DEX penalty)
       - medium: +5 (small DEX cap)
       - heavy: +0 (no DEX bonus)
       - shield: +20 (shields are always good)
    
    Higher scores = better armor. Ties broken by defense, then armor type.
    
    Args:
        item: Entity with equippable component (armor)
        
    Returns:
        int: Armor defensive score (higher is better), or 0 if not armor
    
    Examples:
        - Leather armor (+2 AC, light): 200 + 10 = 210
        - Chain mail (+4 AC, medium): 400 + 5 = 405
        - Plate armor (+6 AC, heavy): 600
        - Shield (+2 AC, shield): 200 + 20 = 220
    """
    if not item or not hasattr(item, 'equippable') or not item.equippable:
        return 0
    
    equippable = item.equippable
    
    # Only score armor pieces (items with armor_class_bonus or defense_bonus)
    if equippable.armor_class_bonus <= 0 and equippable.defense_bonus <= 0:
        return 0  # Not armor
    
    score = 0
    
    # 1. Armor Class bonus (primary factor for d20 combat)
    if equippable.armor_class_bonus:
        score += equippable.armor_class_bonus * 100
    
    # 2. Average defense (for defense roll system)
    if equippable.defense_min > 0 or equippable.defense_max > 0:
        avg_defense = (equippable.defense_min + equippable.defense_max) / 2.0
        score += int(avg_defense * 10)
    
    # 3. Defense bonus
    if equippable.defense_bonus:
        score += equippable.defense_bonus * 10
    
    # 4. Armor type tier bonus (light armor is better for high-DEX characters)
    if equippable.armor_type:
        armor_type_bonus = {
            'shield': 20,  # Shields are always good (no DEX penalty)
            'light': 10,   # Best for high DEX (no cap)
            'medium': 5,   # Middle ground (DEX cap +2)
            'heavy': 0,    # Best for low DEX (no DEX bonus)
        }
        score += armor_type_bonus.get(equippable.armor_type, 0)
    
    return score


def _calculate_average_damage_from_dice(dice_notation: str) -> float:
    """Calculate average damage from dice notation.
    
    Args:
        dice_notation: Dice string like "1d4", "1d6", "2d6", etc.
        
    Returns:
        float: Average damage value
        
    Examples:
        "1d4" -> 2.5 (average of 1-4)
        "1d6" -> 3.5 (average of 1-6)
        "2d6" -> 7.0 (average of 2-12)
    """
    if not dice_notation or 'd' not in dice_notation.lower():
        return 0.0
    
    try:
        parts = dice_notation.lower().split('d')
        num_dice = int(parts[0])
        die_size = int(parts[1])
        
        # Average roll for a die is (1 + die_size) / 2
        avg_per_die = (1 + die_size) / 2.0
        return num_dice * avg_per_die
    except (ValueError, IndexError):
        return 0.0


def auto_equip_better_items(player: Any, is_bot_mode: bool = False) -> None:
    """Automatically equip the best weapons and armor for the bot.
    
    This function evaluates all equippable items in the player's inventory
    and automatically equips the best item for each slot. This ONLY runs
    in bot mode and does not affect manual (human) play.
    
    Strategy:
    1. Get all weapons and armor from inventory
    2. For each equipment slot, find the highest-scoring item
    3. If that item scores higher than currently equipped item, equip it
    4. Use the same equipment.toggle_equip() method as manual play
    
    Args:
        player: Player entity with inventory and equipment components
        is_bot_mode: Whether the game is in bot mode (default: False)
        
    Returns:
        None (equips items as side effect)
    """
    if not is_bot_mode:
        return  # Only auto-equip in bot mode
    
    if not player:
        return
    
    # Get components
    inventory = player.get_component_optional(ComponentType.INVENTORY)
    equipment = player.get_component_optional(ComponentType.EQUIPMENT)
    
    if not inventory or not equipment:
        return
    
    # Find best items for each slot
    best_items = _find_best_items_per_slot(inventory.items, equipment)
    
    # Equip better items
    for slot, (best_item, best_score) in best_items.items():
        if best_item is None:
            continue
        
        # Get currently equipped item for this slot
        current_item = _get_equipped_item_for_slot(equipment, slot)
        
        # Skip if already equipped
        if current_item == best_item:
            continue
        
        # Calculate current item score
        current_score = 0
        if current_item:
            if slot == EquipmentSlots.MAIN_HAND:
                current_score = evaluate_weapon(current_item)
            else:
                # All other slots are armor
                current_score = evaluate_armor(current_item)
        
        # Equip if better
        if best_score > current_score:
            logger.info(f"Bot auto-equipping {best_item.name} (score {best_score} > {current_score})")
            equipment.toggle_equip(best_item)


def _find_best_items_per_slot(
    inventory_items: List[Any],
    equipment: Any
) -> dict:
    """Find the best item for each equipment slot in inventory.
    
    Args:
        inventory_items: List of items in inventory
        equipment: Equipment component to check current items
        
    Returns:
        dict: Mapping of slot -> (best_item, score)
    """
    best_items = {
        EquipmentSlots.MAIN_HAND: (None, 0),
        EquipmentSlots.OFF_HAND: (None, 0),
        EquipmentSlots.HEAD: (None, 0),
        EquipmentSlots.CHEST: (None, 0),
        EquipmentSlots.FEET: (None, 0),
    }
    
    for item in inventory_items:
        if not hasattr(item, 'equippable') or not item.equippable:
            continue
        
        equippable = item.equippable
        slot = equippable.slot
        
        # Skip rings for now (more complex with left/right ring slots)
        if slot == EquipmentSlots.RING:
            continue
        
        # Evaluate item
        if slot == EquipmentSlots.MAIN_HAND:
            score = evaluate_weapon(item)
        else:
            score = evaluate_armor(item)
        
        # Update best item for this slot
        if slot in best_items:
            current_best_item, current_best_score = best_items[slot]
            if score > current_best_score:
                best_items[slot] = (item, score)
    
    # Also check currently equipped items (they might still be best)
    for slot in best_items.keys():
        current_item = _get_equipped_item_for_slot(equipment, slot)
        if current_item:
            if slot == EquipmentSlots.MAIN_HAND:
                score = evaluate_weapon(current_item)
            else:
                score = evaluate_armor(current_item)
            
            _, current_best_score = best_items[slot]
            if score > current_best_score:
                best_items[slot] = (current_item, score)
    
    return best_items


def _get_equipped_item_for_slot(equipment: Any, slot: Any) -> Optional[Any]:
    """Get the currently equipped item for a given slot.
    
    Args:
        equipment: Equipment component
        slot: Equipment slot (EquipmentSlots enum value)
        
    Returns:
        Currently equipped item or None
    """
    slot_map = {
        EquipmentSlots.MAIN_HAND: 'main_hand',
        EquipmentSlots.OFF_HAND: 'off_hand',
        EquipmentSlots.HEAD: 'head',
        EquipmentSlots.CHEST: 'chest',
        EquipmentSlots.FEET: 'feet',
    }
    
    slot_attr = slot_map.get(slot)
    if slot_attr:
        return getattr(equipment, slot_attr, None)
    
    return None

