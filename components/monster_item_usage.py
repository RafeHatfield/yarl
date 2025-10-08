"""Monster item usage system for consumables.

This module handles monster usage of consumable items like scrolls and potions.
It provides configurable usage patterns, failure mechanics, and extensible
design for different item types.
"""

import logging
import random
from typing import List, Optional, Dict, Any
from config.game_constants import get_monster_equipment_config
from game_messages import Message
from components.monster_action_logger import MonsterActionLogger
from components.component_registry import ComponentType

logger = logging.getLogger(__name__)


class MonsterItemUsage:
    """Handles monster usage of consumable items with configurable behavior."""
    
    def __init__(self, monster):
        """Initialize monster item usage system.
        
        Args:
            monster: The monster entity that will use items
        """
        self.monster = monster
        self.config = get_monster_equipment_config()
        
        # Item usage permissions (extensible for future additions)
        self.can_use_scrolls = True
        self.can_use_potions = False  # Disabled for balance, but extensible
        
    def get_item_usage_action(self, target, game_map, entities) -> Optional[Dict[str, Any]]:
        """Determine if monster should use an item and which one.
        
        Args:
            target: Target entity (usually the player)
            game_map: Current game map
            entities: List of all entities
            
        Returns:
            dict: Usage action if monster should use an item, None otherwise
        """
        inventory = self.monster.components.get(ComponentType.INVENTORY)
        if not inventory:
            return None
            
        if not inventory.items:
            return None
            
        # Find usable items in inventory
        usable_items = self._find_usable_items()
        if not usable_items:
            return None
            
        # Determine if monster should use an item based on situation
        should_use, item_to_use = self._should_use_item(usable_items, target, entities)
        
        if should_use and item_to_use:
            logger.debug(f"{self.monster.name} deciding to use {item_to_use.name}")
            return {"use_item": item_to_use, "target": target}
            
        return None
    
    def _find_usable_items(self) -> List[Any]:
        """Find items in inventory that the monster can use.
        
        Returns:
            List of usable item entities
        """
        usable_items = []
        
        inventory = self.monster.components.get(ComponentType.INVENTORY)
        if not inventory:
            return usable_items
        
        for item in inventory.items:
            if not item.components.has(ComponentType.ITEM):
                continue
                
            # Check item type and permissions
            # use_function is a direct attribute on Item component
            if hasattr(item.item, 'use_function'):  # Direct attribute check on item.item
                item_name = item.name.lower()
                
                # Scroll usage (enabled)
                if self.can_use_scrolls and 'scroll' in item_name:
                    usable_items.append(item)
                    
                # Potion usage (disabled for balance, but framework ready)
                elif self.can_use_potions and 'potion' in item_name:
                    usable_items.append(item)
                    
        return usable_items
    
    def _should_use_item(self, usable_items: List[Any], target, entities) -> tuple:
        """Determine if and which item the monster should use.
        
        Args:
            usable_items: List of items monster can use
            target: Target entity (player)
            entities: All entities in game
            
        Returns:
            tuple: (should_use: bool, item_to_use: Entity or None)
        """
        # Simple usage logic - can be expanded later
        for item in usable_items:
            item_name = item.name.lower()
            
            # Offensive scrolls - use when player is nearby
            if any(scroll_type in item_name for scroll_type in ['lightning', 'fireball']):
                distance_to_target = self._calculate_distance(
                    self.monster.x, self.monster.y, target.x, target.y
                )
                if distance_to_target <= 5:  # Within reasonable range
                    return True, item
                    
            # Confusion scroll - use when player is adjacent
            elif 'confusion' in item_name:
                distance_to_target = self._calculate_distance(
                    self.monster.x, self.monster.y, target.x, target.y
                )
                if distance_to_target <= 2:  # Close range
                    return True, item
                    
            # Enhancement scrolls - use immediately if monster has equipment
            elif 'enhance' in item_name:
                equipment = self.monster.components.get(ComponentType.EQUIPMENT)
                if equipment:
                    if ('weapon' in item_name and equipment.main_hand) or \
                       ('armor' in item_name and equipment.off_hand):
                        return True, item
        
        return False, None
    
    def _calculate_distance(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Calculate distance between two points."""
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    
    def use_item_with_failure(self, item, target, entities) -> List[Dict[str, Any]]:
        """Use an item with potential failure mechanics.
        
        Args:
            item: Item to use
            target: Target for the item usage
            entities: List of all entities
            
        Returns:
            List of result dictionaries from item usage
        """
        results = []
        item_name = item.name.lower()
        
        # Determine failure rate based on item type
        if 'scroll' in item_name:
            failure_rate = self.config.SCROLL_FAILURE_RATE
        elif 'potion' in item_name:
            failure_rate = self.config.POTION_FAILURE_RATE
        else:
            failure_rate = 0.0  # Unknown item type, no failure
            
        # Roll for failure
        if random.random() < failure_rate:
            failure_results = self._handle_item_failure(item, target, entities)
            results.extend(failure_results)
            # Extract failure mode from results for logging
            failure_mode = "unknown"
            for result in failure_results:
                if "message" in result:
                    msg_text = result["message"].text.lower()
                    if "fizzles" in msg_text:
                        failure_mode = "fizzle"
                    elif "wrong target" in msg_text or "confused" in msg_text:
                        failure_mode = "wrong_target"
                    elif "damage" in msg_text or "weaker" in msg_text:
                        failure_mode = "equipment_damage"
                    break
            MonsterActionLogger.log_item_usage(self.monster, item, target, False, failure_mode)
        else:
            results.extend(self._handle_item_success(item, target, entities))
            MonsterActionLogger.log_item_usage(self.monster, item, target, True)
            
        # Remove item from inventory after use (success or failure)
        if item in self.monster.inventory.items:
            self.monster.inventory.items.remove(item)
            MonsterActionLogger.log_inventory_change(self.monster, item, "removed (used)")
            
        return results
    
    def _handle_item_success(self, item, target, entities) -> List[Dict[str, Any]]:
        """Handle successful item usage.
        
        Args:
            item: Item being used
            target: Target for the item
            entities: List of all entities
            
        Returns:
            List of result dictionaries
        """
        results = []
        
        # Use the item's normal function
        # use_function is a direct attribute on Item component
        if hasattr(item.item, 'use_function') and item.item.use_function:
            try:
                # Call the item's use function
                use_results = item.item.use_function(
                    inventory=self.monster.inventory,
                    target_entity=target,
                    entities=entities,
                    **getattr(item.item, 'function_kwargs', {})
                )
                
                if use_results:
                    results.extend(use_results)
                    
                results.append({
                    "message": Message(
                        f"{self.monster.name.capitalize()} uses {item.name}!",
                        (255, 255, 0)
                    )
                })
                
            except Exception as e:
                logger.error(f"Error using item {item.name}: {e}")
                results.append({
                    "message": Message(
                        f"{self.monster.name.capitalize()}'s {item.name} fizzles!",
                        (128, 128, 128)
                    )
                })
                
        return results
    
    def _handle_item_failure(self, item, target, entities) -> List[Dict[str, Any]]:
        """Handle item usage failure with interesting failure modes.
        
        Args:
            item: Item that failed
            target: Original target
            entities: List of all entities
            
        Returns:
            List of result dictionaries
        """
        results = []
        item_name = item.name.lower()
        
        # Determine failure mode
        failure_modes = ['fizzle', 'wrong_target', 'equipment_damage']
        failure_mode = random.choice(failure_modes)
        
        if failure_mode == 'fizzle':
            # Item does nothing
            results.append({
                "message": Message(
                    f"{self.monster.name.capitalize()}'s {item.name} fizzles harmlessly!",
                    (128, 128, 128)
                )
            })
            
        elif failure_mode == 'wrong_target':
            # Beneficial effects go to wrong target, harmful effects backfire
            results.extend(self._handle_wrong_target_failure(item, target, entities))
            
        elif failure_mode == 'equipment_damage':
            # Scroll backfires and damages equipment
            results.extend(self._handle_equipment_damage_failure(item))
            
        return results
    
    def _handle_wrong_target_failure(self, item, original_target, entities) -> List[Dict[str, Any]]:
        """Handle wrong target failure mode.
        
        Args:
            item: Item that failed
            original_target: Original intended target
            entities: List of all entities
            
        Returns:
            List of result dictionaries
        """
        results = []
        item_name = item.name.lower()
        
        # Determine if item is beneficial or harmful
        beneficial_scrolls = ['enhance_weapon', 'enhance_armor']
        harmful_scrolls = ['lightning', 'fireball', 'confusion']
        
        if any(scroll_type in item_name for scroll_type in beneficial_scrolls):
            # Beneficial scroll cast on player instead of monster
            new_target = original_target
            target_name = "player"
        elif any(scroll_type in item_name for scroll_type in harmful_scrolls):
            # Harmful scroll cast on monster instead of player
            new_target = self.monster
            target_name = "themselves"
        else:
            # Unknown scroll type, just fizzle
            results.append({
                "message": Message(
                    f"{self.monster.name.capitalize()}'s {item.name} backfires and fizzles!",
                    (255, 128, 0)
                )
            })
            return results
        
        # Try to use item on wrong target
        try:
            # use_function is a direct attribute on Item component
            if hasattr(item.item, 'use_function') and item.item.use_function:  # Direct attribute check
                use_results = item.item.use_function(
                    inventory=self.monster.inventory,
                    target_entity=new_target,
                    entities=entities,
                    **getattr(item.item, 'function_kwargs', {})
                )
                
                if use_results:
                    results.extend(use_results)
                    
            results.append({
                "message": Message(
                    f"{self.monster.name.capitalize()}'s {item.name} backfires on {target_name}!",
                    (255, 128, 0)
                )
            })
            
        except Exception as e:
            logger.error(f"Error in wrong target failure for {item.name}: {e}")
            results.append({
                "message": Message(
                    f"{self.monster.name.capitalize()}'s {item.name} backfires chaotically!",
                    (255, 128, 0)
                )
            })
            
        return results
    
    def _handle_equipment_damage_failure(self, item) -> List[Dict[str, Any]]:
        """Handle equipment damage failure mode.
        
        Args:
            item: Item that failed
            
        Returns:
            List of result dictionaries
        """
        results = []
        
        # Check if monster has equipment to damage
        equipment = self.monster.components.get(ComponentType.EQUIPMENT)
        if not equipment:
            # No equipment to damage, just fizzle
            results.append({
                "message": Message(
                    f"{self.monster.name.capitalize()}'s {item.name} backfires harmlessly!",
                    (255, 128, 0)
                )
            })
            return results
        
        # Find equipment to damage
        equipment_to_damage = []
        if self.monster.equipment.main_hand:
            equipment_to_damage.append(('weapon', self.monster.equipment.main_hand))
        if self.monster.equipment.off_hand:
            equipment_to_damage.append(('armor', self.monster.equipment.off_hand))
            
        if not equipment_to_damage:
            # No equipment equipped, just fizzle
            results.append({
                "message": Message(
                    f"{self.monster.name.capitalize()}'s {item.name} backfires but finds no equipment to damage!",
                    (255, 128, 0)
                )
            })
            return results
        
        # Randomly select equipment to damage
        equipment_type, equipment_item = random.choice(equipment_to_damage)
        
        # For enhancement scrolls, reduce the equipment's effectiveness
        if equipment_item.components.has(ComponentType.EQUIPPABLE):
            equippable = equipment_item.equippable
            
            # damage_min, damage_max, defense_min, defense_max are direct attributes on equippable
            if equipment_type == 'weapon' and hasattr(equippable, 'damage_min'):
                # Reduce weapon damage
                if equippable.damage_min > 1:
                    equippable.damage_min -= 1
                if equippable.damage_max > 1:
                    equippable.damage_max -= 1
                    
                results.append({
                    "message": Message(
                        f"{self.monster.name.capitalize()}'s {equipment_item.name} is weakened by the backfire!",
                        (255, 64, 64)
                    )
                })
                
            elif equipment_type == 'armor' and hasattr(equippable, 'defense_min'):
                # Reduce armor defense
                if equippable.defense_min > 1:
                    equippable.defense_min -= 1
                if equippable.defense_max > 1:
                    equippable.defense_max -= 1
                    
                results.append({
                    "message": Message(
                        f"{self.monster.name.capitalize()}'s {equipment_item.name} is damaged by the backfire!",
                        (255, 64, 64)
                    )
                })
            else:
                # Equipment doesn't have variable stats, just show message
                results.append({
                    "message": Message(
                        f"{self.monster.name.capitalize()}'s {equipment_item.name} sparks from the backfire!",
                        (255, 128, 0)
                    )
                })
        
        return results


def create_monster_item_usage(monster) -> Optional[MonsterItemUsage]:
    """Create a MonsterItemUsage component for a monster.
    
    Args:
        monster: The monster entity
        
    Returns:
        MonsterItemUsage: Item usage component if monster has inventory, None otherwise
    """
    inventory = monster.components.get(ComponentType.INVENTORY)
    if not inventory:
        return None
        
    return MonsterItemUsage(monster)
