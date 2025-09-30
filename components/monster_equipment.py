"""Monster equipment spawning and management system.

This module handles the spawning of equipment on monsters, equipment drop mechanics,
and monster inventory management. It provides configurable spawn rates based on
dungeon level and game mode (normal vs testing).
"""

import random
import logging
from typing import List, Optional, Tuple
from config.game_constants import get_monster_equipment_config
from config.testing_config import is_testing_mode
from config.entity_factory import get_entity_factory
from components.monster_action_logger import MonsterActionLogger

logger = logging.getLogger(__name__)


class MonsterEquipmentSpawner:
    """Handles spawning equipment on monsters based on configurable rules."""
    
    def __init__(self):
        """Initialize the monster equipment spawner."""
        self.config = get_monster_equipment_config()
        self.entity_factory = get_entity_factory()
    
    def should_spawn_with_equipment(self, monster_type: str, dungeon_level: int) -> bool:
        """Determine if a monster should spawn with equipment.
        
        Args:
            monster_type: Type of monster (e.g., "orc", "troll")
            dungeon_level: Current dungeon level (1-based)
            
        Returns:
            bool: True if monster should spawn with equipment
        """
        if is_testing_mode():
            # Testing mode: flat chance
            chance = self.config.TESTING_BASE_CHANCE
        else:
            # Normal mode: level-scaled chance with cap
            base_chance = self.config.NORMAL_BASE_CHANCE
            level_bonus = (dungeon_level - 1) * self.config.NORMAL_LEVEL_MULTIPLIER * base_chance
            chance = min(base_chance + level_bonus, self.config.NORMAL_MAX_CHANCE)
        
        roll = random.random()
        should_spawn = roll < chance
        
        logger.debug(f"Equipment spawn check for {monster_type} at level {dungeon_level}: "
                    f"chance={chance:.2f}, roll={roll:.2f}, spawn={should_spawn}")
        
        return should_spawn
    
    def generate_equipment_for_monster(self, monster, dungeon_level: int) -> List:
        """Generate equipment for a monster and equip it.
        
        Args:
            monster: Monster entity to equip
            dungeon_level: Current dungeon level for equipment tier
            
        Returns:
            List: List of equipment entities that were created (for tracking)
        """
        if not self.should_spawn_with_equipment(monster.name, dungeon_level):
            return []
        
        equipment_list = []
        
        # Determine what type of equipment to spawn
        equipment_roll = random.random()
        
        if equipment_roll < self.config.WEAPON_SPAWN_WEIGHT:
            # Spawn weapon
            weapon = self._create_weapon_for_level(dungeon_level)
            if weapon and hasattr(monster, 'equipment') and monster.equipment:
                monster.equipment.toggle_equip(weapon)
                equipment_list.append(weapon)
                logger.debug(f"Equipped {monster.name} with {weapon.name}")
        else:
            # Spawn armor
            armor = self._create_armor_for_level(dungeon_level)
            if armor and hasattr(monster, 'equipment') and monster.equipment:
                monster.equipment.toggle_equip(armor)
                equipment_list.append(armor)
                logger.debug(f"Equipped {monster.name} with {armor.name}")
        
        return equipment_list
    
    def _create_weapon_for_level(self, dungeon_level: int):
        """Create an appropriate weapon for the dungeon level.
        
        Args:
            dungeon_level: Current dungeon level
            
        Returns:
            Entity: Weapon entity or None if creation failed
        """
        try:
            # For now, simple logic: daggers at level 1-2, swords at level 3+
            if dungeon_level <= 2:
                return self.entity_factory.create_weapon("dagger", 0, 0)
            else:
                return self.entity_factory.create_weapon("sword", 0, 0)
        except Exception as e:
            logger.warning(f"Failed to create weapon for level {dungeon_level}: {e}")
            return None
    
    def _create_armor_for_level(self, dungeon_level: int):
        """Create appropriate armor for the dungeon level.
        
        Args:
            dungeon_level: Current dungeon level
            
        Returns:
            Entity: Armor entity or None if creation failed
        """
        try:
            # For now, only shields available
            return self.entity_factory.create_armor("shield", 0, 0)
        except Exception as e:
            logger.warning(f"Failed to create armor for level {dungeon_level}: {e}")
            return None


class MonsterLootDropper:
    """Handles dropping loot when monsters die."""
    
    @staticmethod
    def drop_monster_loot(monster, x: int, y: int) -> List:
        """Drop all items from a monster's inventory at the specified location.
        
        Args:
            monster: Monster entity that died
            x: X coordinate where to drop loot
            y: Y coordinate where to drop loot
            
        Returns:
            List: List of dropped item entities
        """
        dropped_items = []
        
        # Drop equipped items
        if hasattr(monster, 'equipment') and monster.equipment:
            # Drop main hand weapon
            if monster.equipment.main_hand:
                weapon = monster.equipment.main_hand
                drop_x, drop_y = MonsterLootDropper._find_drop_location(x, y, dropped_items)
                weapon.x = drop_x
                weapon.y = drop_y
                dropped_items.append(weapon)
                logger.debug(f"Dropped {weapon.name} from {monster.name} at ({drop_x}, {drop_y})")
            
            # Drop off hand armor
            if monster.equipment.off_hand:
                armor = monster.equipment.off_hand
                drop_x, drop_y = MonsterLootDropper._find_drop_location(x, y, dropped_items)
                armor.x = drop_x
                armor.y = drop_y
                dropped_items.append(armor)
                logger.debug(f"Dropped {armor.name} from {monster.name} at ({drop_x}, {drop_y})")
        
        # Drop inventory items (if monster has inventory)
        if hasattr(monster, 'inventory') and monster.inventory:
            for item in monster.inventory.items:
                drop_x, drop_y = MonsterLootDropper._find_drop_location(x, y, dropped_items)
                item.x = drop_x
                item.y = drop_y
                dropped_items.append(item)
                logger.debug(f"Dropped {item.name} from {monster.name} inventory at ({drop_x}, {drop_y})")
        
        if dropped_items:
            logger.info(f"{monster.name} dropped {len(dropped_items)} items around ({x}, {y})")
            # Log each dropped item in testing mode
            for item in dropped_items:
                MonsterActionLogger.log_action_result(monster, "loot_drop", True, 
                    f"dropped {item.name} at ({item.x}, {item.y})")
        
        return dropped_items
    
    @staticmethod
    def _find_drop_location(center_x: int, center_y: int, existing_items: List) -> tuple:
        """Find a suitable location to drop an item, avoiding stacking.
        
        Args:
            center_x: Preferred X coordinate (monster's position)
            center_y: Preferred Y coordinate (monster's position)
            existing_items: Items already dropped (to avoid stacking)
            
        Returns:
            tuple: (x, y) coordinates for the drop location
        """
        # Try adjacent positions in a spiral pattern
        offsets = [
            (0, 0),   # Same position (fallback)
            (0, -1),  # North
            (1, 0),   # East
            (0, 1),   # South
            (-1, 0),  # West
            (1, -1),  # Northeast
            (1, 1),   # Southeast
            (-1, 1),  # Southwest
            (-1, -1), # Northwest
        ]
        
        for dx, dy in offsets:
            drop_x = center_x + dx
            drop_y = center_y + dy
            
            # Check if this position is already occupied by a dropped item
            position_occupied = any(
                item.x == drop_x and item.y == drop_y 
                for item in existing_items
            )
            
            if not position_occupied:
                return drop_x, drop_y
        
        # Fallback: use the original position if all adjacent spots are taken
        return center_x, center_y


# Convenience functions for easy integration
def spawn_equipment_on_monster(monster, dungeon_level: int) -> List:
    """Convenience function to spawn equipment on a monster.
    
    Args:
        monster: Monster entity to potentially equip
        dungeon_level: Current dungeon level
        
    Returns:
        List: List of equipment entities created
    """
    spawner = MonsterEquipmentSpawner()
    return spawner.generate_equipment_for_monster(monster, dungeon_level)


def drop_loot_from_monster(monster, x: int, y: int) -> List:
    """Convenience function to drop loot from a dead monster.
    
    Args:
        monster: Monster entity that died
        x: X coordinate where to drop loot
        y: Y coordinate where to drop loot
        
    Returns:
        List: List of dropped item entities
    """
    return MonsterLootDropper.drop_monster_loot(monster, x, y)
