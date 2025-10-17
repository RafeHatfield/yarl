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
from components.component_registry import ComponentType

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
        # Slimes are just blobs - they can't carry equipment!
        if 'slime' in monster.name.lower():
            return []
        
        if not self.should_spawn_with_equipment(monster.name, dungeon_level):
            return []
        
        equipment_list = []
        
        # Determine what type of equipment to spawn
        equipment_roll = random.random()
        
        if equipment_roll < self.config.WEAPON_SPAWN_WEIGHT:
            # Spawn weapon
            weapon = self._create_weapon_for_level(dungeon_level)
            equipment = monster.get_component_optional(ComponentType.EQUIPMENT)
            if weapon and equipment:
                # Ensure it's actually a weapon before equipping
                if weapon.components.has(ComponentType.EQUIPPABLE):
                    equipment.toggle_equip(weapon)
                    equipment_list.append(weapon)
                    logger.debug(f"Equipped {monster.name} with {weapon.name}")
                else:
                    logger.warning(f"Failed to equip weapon - no equippable component: {weapon.name}")
        else:
            # Spawn armor
            logger.debug(f"Rolling for armor for {monster.name} at level {dungeon_level}")
            armor = self._create_armor_for_level(dungeon_level)
            equipment = monster.get_component_optional(ComponentType.EQUIPMENT)
            if armor and equipment:
                # Ensure it's actually armor before equipping
                if armor.components.has(ComponentType.EQUIPPABLE):
                    logger.debug(f"Attempting to equip {monster.name} with {armor.name}")
                    equipment.toggle_equip(armor)
                    equipment_list.append(armor)
                    logger.debug(f"Successfully equipped {monster.name} with {armor.name}")
                else:
                    logger.warning(f"Failed to equip armor - no equippable component: {armor.name}")
            elif armor:
                logger.warning(f"Armor created but monster has no equipment component: {armor.name}")
        
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
            elif dungeon_level <= 5:
                return self.entity_factory.create_weapon("shortsword", 0, 0)
            else:
                return self.entity_factory.create_weapon("longsword", 0, 0)
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
            logger.debug(f"Creating armor for level {dungeon_level}: requesting 'shield'")
            armor = self.entity_factory.create_armor("shield", 0, 0)
            if armor:
                logger.debug(f"Successfully created armor: {armor.name}")
            else:
                logger.warning(f"create_armor('shield') returned None!")
            return armor
        except Exception as e:
            logger.error(f"Exception creating armor for level {dungeon_level}: {e}", exc_info=True)
            return None


class MonsterLootDropper:
    """Handles dropping loot when monsters die."""
    
    @staticmethod
    def drop_monster_loot(monster, x: int, y: int, game_map=None) -> List:
        """Drop all items from a monster's inventory at the specified location.
        
        Uses the new loot quality system to generate level-scaled magical items.
        Chance of drops and quality scale with dungeon level.
        
        Args:
            monster: Monster entity that died
            x: X coordinate where to drop loot
            y: Y coordinate where to drop loot
            game_map: Game map to check for valid drop locations (optional)
            
        Returns:
            List: List of dropped item entities (includes both equipped and generated loot)
        """
        from components.loot import get_loot_generator
        from random import random
        
        # Slimes are just blobs - they don't carry items!
        if 'slime' in monster.name.lower():
            return []
        
        dropped_items = []
        loot_gen = get_loot_generator()
        
        # Get dungeon level for scaling
        dungeon_level = 1
        if game_map and hasattr(game_map, 'dungeon_level'):
            dungeon_level = game_map.dungeon_level
        
        # Drop equipped items
        equipment = monster.get_component_optional(ComponentType.EQUIPMENT)
        if equipment:
            # Drop main hand weapon
            if equipment.main_hand:
                weapon = equipment.main_hand
                # Unequip the weapon first to clear the reference
                equipment.main_hand = None
                weapon.owner = None  # Clear ownership
                drop_x, drop_y = MonsterLootDropper._find_drop_location(x, y, dropped_items, game_map)
                weapon.x = drop_x
                weapon.y = drop_y
                dropped_items.append(weapon)
                logger.debug(f"Dropped {weapon.name} from {monster.name} at ({drop_x}, {drop_y})")
            
            # Drop off hand (shield)
            if equipment.off_hand:
                shield = equipment.off_hand
                # Unequip the shield first to clear the reference
                equipment.off_hand = None
                shield.owner = None  # Clear ownership
                drop_x, drop_y = MonsterLootDropper._find_drop_location(x, y, dropped_items, game_map)
                shield.x = drop_x
                shield.y = drop_y
                dropped_items.append(shield)
                logger.debug(f"Dropped {shield.name} from {monster.name} at ({drop_x}, {drop_y})")
            
            # Drop chest armor
            if equipment.chest:
                armor = equipment.chest
                equipment.chest = None
                armor.owner = None
                drop_x, drop_y = MonsterLootDropper._find_drop_location(x, y, dropped_items, game_map)
                armor.x = drop_x
                armor.y = drop_y
                dropped_items.append(armor)
                logger.debug(f"Dropped {armor.name} from {monster.name} at ({drop_x}, {drop_y})")
            
            # Drop head armor
            if equipment.head:
                helmet = equipment.head
                equipment.head = None
                helmet.owner = None
                drop_x, drop_y = MonsterLootDropper._find_drop_location(x, y, dropped_items, game_map)
                helmet.x = drop_x
                helmet.y = drop_y
                dropped_items.append(helmet)
                logger.debug(f"Dropped {helmet.name} from {monster.name} at ({drop_x}, {drop_y})")
            
            # Drop feet armor
            if equipment.feet:
                boots = equipment.feet
                equipment.feet = None
                boots.owner = None
                drop_x, drop_y = MonsterLootDropper._find_drop_location(x, y, dropped_items, game_map)
                boots.x = drop_x
                boots.y = drop_y
                dropped_items.append(boots)
                logger.debug(f"Dropped {boots.name} from {monster.name} at ({drop_x}, {drop_y})")
        
        # Check if this is a boss kill - bosses drop guaranteed legendary loot!
        boss_component = monster.get_component_optional(ComponentType.BOSS)
        if boss_component:
            # Boss kill! Always drop 1-2 legendary items
            drop_x, drop_y = MonsterLootDropper._find_drop_location(x, y, dropped_items, game_map)
            primary_drop, secondary_drop = loot_gen.generate_boss_loot(
                drop_x, drop_y, dungeon_level, boss_component.boss_name
            )
            dropped_items.append(primary_drop)
            
            if secondary_drop:
                drop_x, drop_y = MonsterLootDropper._find_drop_location(x, y, dropped_items, game_map)
                secondary_drop.x = drop_x
                secondary_drop.y = drop_y
                dropped_items.append(secondary_drop)
                logger.info(f"Boss {boss_component.boss_name} dropped 2 LEGENDARY items!")
            else:
                logger.info(f"Boss {boss_component.boss_name} dropped 1 LEGENDARY item!")
        
        # Generate additional quality loot based on dungeon level (non-boss monsters)
        # This is the new loot quality system - monsters can drop magic items!
        elif loot_gen.should_monster_drop_loot(monster.name, dungeon_level):
            # Collect names of already-dropped items to avoid duplicates
            dropped_item_names = {item.name.lower() for item in dropped_items}
            
            # 70% chance for weapon, 30% chance for armor
            if random() < 0.70:
                drop_x, drop_y = MonsterLootDropper._find_drop_location(x, y, dropped_items, game_map)
                magic_weapon = loot_gen.generate_weapon(drop_x, drop_y, dungeon_level)
                
                # Only drop if not a duplicate
                if magic_weapon.name.lower() not in dropped_item_names:
                    dropped_items.append(magic_weapon)
                    logger.info(f"{monster.name} dropped BONUS {magic_weapon.loot.rarity.display_name} weapon: {magic_weapon.name}")
                else:
                    logger.debug(f"{monster.name} bonus weapon skipped (duplicate {magic_weapon.name})")
            else:
                drop_x, drop_y = MonsterLootDropper._find_drop_location(x, y, dropped_items, game_map)
                magic_armor = loot_gen.generate_armor(drop_x, drop_y, dungeon_level)
                
                # Only drop if not a duplicate
                if magic_armor.name.lower() not in dropped_item_names:
                    dropped_items.append(magic_armor)
                    logger.info(f"{monster.name} dropped BONUS {magic_armor.loot.rarity.display_name} armor: {magic_armor.name}")
                else:
                    logger.debug(f"{monster.name} bonus armor skipped (duplicate {magic_armor.name})")
        
        # Drop inventory items (if monster has inventory)
        # Drop items from monster inventory (items they picked up)
        # CRITICAL: Items are REMOVED from entities when picked up (see ai.py _pickup_item line 548-549)
        # So we MUST add them back to dropped_items so they're re-added to entities!
        inventory = monster.get_component_optional(ComponentType.INVENTORY)
        if inventory:
            # Create a copy of the items list to avoid modifying while iterating
            items_to_drop = list(inventory.items)
            for item in items_to_drop:
                # Remove from inventory first to clear the reference
                inventory.items.remove(item)
                item.owner = None  # Clear ownership
                drop_x, drop_y = MonsterLootDropper._find_drop_location(x, y, dropped_items, game_map)
                item.x = drop_x
                item.y = drop_y
                dropped_items.append(item)  # MUST add to dropped_items - they were removed from entities when picked up!
                logger.info(f"Dropped {item.name} from {monster.name} inventory at ({drop_x}, {drop_y})")
        
        if dropped_items:
            logger.info(f"{monster.name} dropped {len(dropped_items)} items around ({x}, {y})")
            # Log each dropped item in testing mode
            for item in dropped_items:
                MonsterActionLogger.log_action_result(monster, "loot_drop", True, 
                    f"dropped {item.name} at ({item.x}, {item.y})")
        
        return dropped_items
    
    @staticmethod
    def _find_drop_location(center_x: int, center_y: int, existing_items: List, game_map=None) -> tuple:
        """Find a suitable location to drop an item, avoiding stacking and walls.
        
        Args:
            center_x: Preferred X coordinate (monster's position)
            center_y: Preferred Y coordinate (monster's position)
            existing_items: Items already dropped (to avoid stacking)
            game_map: Game map to check for blocked tiles (optional)
            
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
            
            # Check if position is within map bounds
            if game_map and (drop_x < 0 or drop_x >= game_map.width or 
                           drop_y < 0 or drop_y >= game_map.height):
                continue
            
            # Check if tile is blocked (wall)
            if game_map and game_map.tiles[drop_x][drop_y].blocked:
                continue
            
            # Check if this position is already occupied by a dropped item
            position_occupied = any(
                item.x == drop_x and item.y == drop_y 
                for item in existing_items
            )
            
            if not position_occupied:
                return drop_x, drop_y
        
        # Fallback: use the original position if all adjacent spots are taken
        # This shouldn't happen often, but ensures items don't disappear
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


def drop_loot_from_monster(monster, x: int, y: int, game_map=None) -> List:
    """Convenience function to drop loot from a dead monster.
    
    Args:
        monster: Monster entity that died
        x: X coordinate where to drop loot
        y: Y coordinate where to drop loot
        game_map: Game map to check for valid drop locations (optional)
        
    Returns:
        List: List of dropped item entities
    """
    return MonsterLootDropper.drop_monster_loot(monster, x, y, game_map)
