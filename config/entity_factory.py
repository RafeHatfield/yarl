"""Entity factory for creating game entities from configuration.

This module provides factory methods for creating entities based on
definitions loaded from the EntityRegistry. It bridges the gap between
configuration data and actual game entities.
"""

import logging
from typing import Optional

from entity import Entity
from components.fighter import Fighter
from components.ai import BasicMonster, SlimeAI
from components.item import Item
from components.equippable import Equippable
from components.faction import Faction, get_faction_from_string
from equipment_slots import EquipmentSlots
from render_functions import RenderOrder
from config.entity_registry import (
    get_entity_registry,
    MonsterDefinition,
    WeaponDefinition,
    ArmorDefinition,
    SpellDefinition,
    EntityStats
)

logger = logging.getLogger(__name__)


class EntityFactory:
    """Factory for creating entities from configuration definitions.
    
    This factory provides clean methods for creating all types of entities
    based on their configuration definitions. It handles the conversion
    from configuration data to actual game entity instances.
    
    The factory supports:
    - Monster creation with AI and fighter components
    - Weapon creation with equippable components
    - Armor creation with equippable components
    - Spell/item creation with appropriate functions
    - Player stat retrieval for character creation
    - Fallback behavior for missing definitions
    """

    def __init__(self, entity_registry=None):
        """Initialize the entity factory.
        
        Args:
            entity_registry: EntityRegistry instance. If None, uses global registry.
        """
        self.registry = entity_registry or get_entity_registry()

    def create_monster(self, monster_type: str, x: int, y: int) -> Optional[Entity]:
        """Create a monster entity from configuration.
        
        Args:
            monster_type: The type of monster to create (e.g., "orc", "troll")
            x: X coordinate for the monster
            y: Y coordinate for the monster
            
        Returns:
            Entity instance if monster type exists, None otherwise
        """
        monster_def = self.registry.get_monster(monster_type)
        if not monster_def:
            logger.warning(f"Unknown monster type: {monster_type}")
            return self._create_fallback_monster(monster_type, x, y)

        try:
            # Create fighter component from stats
            fighter_component = Fighter(
                hp=monster_def.stats.hp,
                defense=monster_def.stats.defense,
                power=monster_def.stats.power,
                xp=monster_def.stats.xp,
                damage_min=monster_def.stats.damage_min or 0,
                damage_max=monster_def.stats.damage_max or 0,
                strength=getattr(monster_def.stats, 'strength', 10),
                dexterity=getattr(monster_def.stats, 'dexterity', 10),
                constitution=getattr(monster_def.stats, 'constitution', 10)
            )

            # Create AI component based on ai_type
            ai_component = self._create_ai_component(monster_def.ai_type)
            
            # Create equipment component for monsters (needed for equipment system)
            from components.equipment import Equipment
            equipment_component = Equipment()
            
            # Create inventory component for monsters that can seek items
            inventory_component = None
            if monster_def.can_seek_items and monster_def.inventory_size > 0:
                from components.inventory import Inventory
                inventory_component = Inventory(capacity=monster_def.inventory_size)
                logger.debug(f"Created inventory for {monster_def.name} with {monster_def.inventory_size} slots")

            # Get faction from monster definition
            faction = get_faction_from_string(getattr(monster_def, 'faction', 'neutral'))
            
            # Create entity
            monster = Entity(
                x=x,
                y=y,
                char=monster_def.char,
                color=monster_def.color,
                name=monster_def.name,
                blocks=monster_def.blocks,
                render_order=self._get_render_order(monster_def.render_order),
                faction=faction,
                fighter=fighter_component,
                ai=ai_component,
                equipment=equipment_component,
                inventory=inventory_component
            )
            
            # Set special abilities if defined
            if hasattr(monster_def, 'special_abilities') and monster_def.special_abilities:
                monster.special_abilities = monster_def.special_abilities
            
            # Create item-seeking AI if monster can seek items
            if monster_def.can_seek_items:
                from components.item_seeking_ai import create_item_seeking_ai
                item_seeking_ai = create_item_seeking_ai(monster, monster_def)
                if item_seeking_ai:
                    monster.item_seeking_ai = item_seeking_ai
                    logger.debug(f"Added item-seeking AI to {monster_def.name}")
                else:
                    logger.warning(f"Failed to create item-seeking AI for {monster_def.name}")
            
            # Create item usage component if monster has inventory
            if inventory_component:
                from components.monster_item_usage import create_monster_item_usage
                item_usage = create_monster_item_usage(monster)
                if item_usage:
                    monster.item_usage = item_usage
                    logger.debug(f"Added item usage capability to {monster_def.name}")
                else:
                    logger.warning(f"Failed to create item usage for {monster_def.name}")

            logger.debug(f"Created monster: {monster_def.name} at ({x}, {y})")
            return monster

        except Exception as e:
            logger.error(f"Error creating monster {monster_type}: {e}")
            return self._create_fallback_monster(monster_type, x, y)

    def create_weapon(self, weapon_type: str, x: int, y: int) -> Optional[Entity]:
        """Create a weapon entity from configuration.
        
        Args:
            weapon_type: The type of weapon to create (e.g., "sword", "dagger")
            x: X coordinate for the weapon
            y: Y coordinate for the weapon
            
        Returns:
            Entity instance if weapon type exists, None otherwise
        """
        weapon_def = self.registry.get_weapon(weapon_type)
        if not weapon_def:
            logger.debug(f"Unknown weapon type: {weapon_type}")
            return None  # Return None so caller can try armor

        try:
            # Create equippable component
            equippable_component = Equippable(
                slot=self._get_equipment_slot(weapon_def.slot),
                power_bonus=weapon_def.power_bonus,
                damage_min=weapon_def.damage_min,
                damage_max=weapon_def.damage_max,
                damage_dice=weapon_def.damage_dice,
                to_hit_bonus=weapon_def.to_hit_bonus,
                two_handed=weapon_def.two_handed,
                reach=weapon_def.reach
            )

            # Create entity
            weapon = Entity(
                x=x,
                y=y,
                char=weapon_def.char,
                color=weapon_def.color,
                name=weapon_def.name,
                equippable=equippable_component
            )

            logger.debug(f"Created weapon: {weapon_def.name} at ({x}, {y})")
            return weapon

        except Exception as e:
            logger.error(f"Error creating weapon {weapon_type}: {e}", exc_info=True)
            logger.error(f"Weapon definition: {weapon_def}")
            return self._create_fallback_weapon(weapon_type, x, y)

    def create_armor(self, armor_type: str, x: int, y: int) -> Optional[Entity]:
        """Create an armor entity from configuration.
        
        Args:
            armor_type: The type of armor to create (e.g., "shield")
            x: X coordinate for the armor
            y: Y coordinate for the armor
            
        Returns:
            Entity instance if armor type exists, None otherwise
        """
        armor_def = self.registry.get_armor(armor_type)
        if not armor_def:
            logger.debug(f"Unknown armor type: {armor_type}")
            return None  # Return None so caller can try weapon

        try:
            # Create equippable component
            equippable_component = Equippable(
                slot=self._get_equipment_slot(armor_def.slot),
                defense_bonus=armor_def.defense_bonus,
                defense_min=armor_def.defense_min,
                defense_max=armor_def.defense_max,
                armor_class_bonus=armor_def.armor_class_bonus,
                armor_type=armor_def.armor_type,
                dex_cap=armor_def.dex_cap
            )

            # Create entity
            armor = Entity(
                x=x,
                y=y,
                char=armor_def.char,
                color=armor_def.color,
                name=armor_def.name,
                equippable=equippable_component
            )

            logger.debug(f"Created armor: {armor_def.name} at ({x}, {y})")
            return armor

        except Exception as e:
            logger.error(f"Error creating armor {armor_type}: {e}")
            return self._create_fallback_armor(armor_type, x, y)

    def create_spell_item(self, spell_type: str, x: int, y: int) -> Optional[Entity]:
        """Create a spell/consumable item entity from configuration.
        
        Args:
            spell_type: The type of spell to create (e.g., "healing_potion")
            x: X coordinate for the spell item
            y: Y coordinate for the spell item
            
        Returns:
            Entity instance if spell type exists, None otherwise
        """
        spell_def = self.registry.get_spell(spell_type)
        if not spell_def:
            logger.warning(f"Unknown spell type: {spell_type}")
            return self._create_fallback_spell(spell_type, x, y)

        try:
            # Create item component with appropriate function
            item_component = self._create_item_component(spell_def)

            # Create entity
            spell_item = Entity(
                x=x,
                y=y,
                char=spell_def.char,
                color=spell_def.color,
                name=spell_def.name,
                item=item_component
            )

            logger.debug(f"Created spell item: {spell_def.name} at ({x}, {y})")
            return spell_item

        except Exception as e:
            logger.error(f"Error creating spell {spell_type}: {e}")
            return self._create_fallback_spell(spell_type, x, y)

    def create_wand(self, wand_type: str, x: int, y: int, dungeon_level: int = 1) -> Optional[Entity]:
        """Create a wand item entity with random charges.
        
        Wands are multi-charge spell casters that can be recharged by picking up
        matching scrolls. They spawn with random charges based on dungeon level:
        - Base charges: 2-4 (random)
        - Additional charges: +(dungeon_level - 1)
        - Max starting charges: 10
        
        Args:
            wand_type: The type of wand to create (e.g., "wand_of_fireball")
            x: X coordinate for the wand
            y: Y coordinate for the wand
            dungeon_level: Current dungeon level (affects starting charges)
            
        Returns:
            Entity instance if wand type exists, None otherwise
        """
        wand_def = self.registry.get_wand(wand_type)
        if not wand_def:
            logger.warning(f"Unknown wand type: {wand_type}")
            return None

        try:
            import random
            from components.wand import Wand
            
            # Calculate random starting charges
            # Base: 2-4, + (level-1), max 10
            base_charges = random.randint(2, 4)
            level_bonus = dungeon_level - 1
            starting_charges = min(base_charges + level_bonus, 10)
            
            # Create wand component
            wand_component = Wand(
                spell_type=wand_def.spell_name,
                charges=starting_charges
            )
            
            # Create item component (same as the spell it casts)
            item_component = self._create_item_component_from_wand(wand_def)
            
            # Create entity
            wand_entity = Entity(
                x=x,
                y=y,
                char=wand_def.char,
                color=wand_def.color,
                name=wand_def.name,
                item=item_component
            )
            
            # Attach wand component
            wand_entity.wand = wand_component
            wand_component.owner = wand_entity
            
            logger.debug(f"Created wand: {wand_def.name} ({starting_charges} charges) at ({x}, {y})")
            return wand_entity

        except Exception as e:
            logger.error(f"Error creating wand {wand_type}: {e}")
            return None

    def get_player_stats(self) -> Optional[EntityStats]:
        """Get player starting stats from configuration.
        
        Returns:
            EntityStats for player if configured, None otherwise
        """
        stats = self.registry.get_player_stats()
        if not stats:
            logger.warning("No player stats configured, using fallback values")
            return EntityStats(hp=100, power=0, defense=1, xp=0, damage_min=3, damage_max=4)  # Updated to new system
        
        return stats

    def _create_ai_component(self, ai_type: str):
        """Create an AI component based on type.
        
        Args:
            ai_type: The type of AI to create
            
        Returns:
            AI component instance
        """
        if ai_type == "basic":
            return BasicMonster()
        elif ai_type == "slime":
            return SlimeAI()
        else:
            logger.warning(f"Unknown AI type: {ai_type}, using basic AI")
            return BasicMonster()

    def _get_render_order(self, render_order_str: str):
        """Convert render order string to RenderOrder enum.
        
        Args:
            render_order_str: String representation of render order
            
        Returns:
            RenderOrder enum value
        """
        try:
            return getattr(RenderOrder, render_order_str.upper())
        except AttributeError:
            logger.warning(f"Unknown render order: {render_order_str}, using ACTOR")
            return RenderOrder.ACTOR

    def _get_equipment_slot(self, slot_str: str):
        """Convert equipment slot string to EquipmentSlots enum.
        
        Args:
            slot_str: String representation of equipment slot
            
        Returns:
            EquipmentSlots enum value
        """
        slot_map = {
            "main_hand": EquipmentSlots.MAIN_HAND,
            "off_hand": EquipmentSlots.OFF_HAND,
            "head": EquipmentSlots.HEAD,
            "chest": EquipmentSlots.CHEST,
            "feet": EquipmentSlots.FEET
        }
        
        slot = slot_map.get(slot_str)
        if slot:
            return slot
        else:
            logger.warning(f"Unknown equipment slot: {slot_str}, using MAIN_HAND")
            return EquipmentSlots.MAIN_HAND

    def _create_item_component(self, spell_def: SpellDefinition):
        """Create an item component with appropriate use function.
        
        Args:
            spell_def: Spell definition
            
        Returns:
            Item component with appropriate use function
        """
        # Import item functions dynamically to avoid circular imports
        from item_functions import (
            heal, cast_lightning, cast_fireball, cast_confuse,
            enhance_weapon, enhance_armor
        )

        # Map spell types to functions and parameters
        if spell_def.name.lower().replace(' ', '_') == "healing_potion":
            return Item(use_function=heal, amount=spell_def.heal_amount)
        elif spell_def.name.lower().replace(' ', '_') == "lightning_scroll":
            return Item(
                use_function=cast_lightning,
                damage=spell_def.damage,
                maximum_range=spell_def.maximum_range
            )
        elif spell_def.name.lower().replace(' ', '_') == "fireball_scroll":
            return Item(
                use_function=cast_fireball,
                targeting=True,
                damage=spell_def.damage,
                radius=spell_def.radius
            )
        elif spell_def.name.lower().replace(' ', '_') == "confusion_scroll":
            return Item(use_function=cast_confuse, targeting=True)
        elif spell_def.name.lower().replace(' ', '_') == "enhance_weapon_scroll":
            return Item(use_function=enhance_weapon)
        elif spell_def.name.lower().replace(' ', '_') == "enhance_armor_scroll":
            return Item(use_function=enhance_armor)
        elif spell_def.name.lower().replace(' ', '_') == "invisibility_scroll":
            from item_functions import cast_invisibility
            duration = getattr(spell_def, 'duration', 10)  # Default 10 turns
            return Item(use_function=cast_invisibility, duration=duration)
        elif spell_def.name.lower().replace(' ', '_') == "teleport_scroll":
            from item_functions import cast_teleport
            return Item(use_function=cast_teleport, targeting=True)
        elif spell_def.name.lower().replace(' ', '_') == "shield_scroll":
            from item_functions import cast_shield
            duration = getattr(spell_def, 'duration', 10)
            defense_bonus = getattr(spell_def, 'defense_bonus', 4)
            return Item(use_function=cast_shield, duration=duration, defense_bonus=defense_bonus)
        elif spell_def.name.lower().replace(' ', '_') == "dragon_fart_scroll":
            from item_functions import cast_dragon_fart
            duration = getattr(spell_def, 'duration', 20)
            spell_range = getattr(spell_def, 'range', 8)
            cone_width = getattr(spell_def, 'cone_width', 45)
            return Item(
                use_function=cast_dragon_fart,
                targeting=True,
                duration=duration,
                range=spell_range,
                cone_width=cone_width
            )
        elif spell_def.name.lower().replace(' ', '_') == "raise_dead_scroll":
            from item_functions import cast_raise_dead
            spell_range = getattr(spell_def, 'range', 5)
            return Item(
                use_function=cast_raise_dead,
                targeting=True,
                range=spell_range
            )
        elif spell_def.name.lower().replace(' ', '_') == "yo_mama_scroll":
            from item_functions import cast_yo_mama
            spell_range = getattr(spell_def, 'range', 10)
            return Item(
                use_function=cast_yo_mama,
                targeting=True,
                range=spell_range
            )
        else:
            logger.warning(f"Unknown spell function for {spell_def.name}, creating basic item")
            return Item()

    def _create_item_component_from_wand(self, wand_def):
        """Create an item component from a wand definition.
        
        This creates an Item component that matches the spell the wand casts.
        The wand's spell_name field determines which spell function to use.
        
        Args:
            wand_def: WandDefinition
            
        Returns:
            Item component with appropriate use function
        """
        # Import item functions dynamically to avoid circular imports
        from item_functions import (
            cast_lightning, cast_fireball, cast_confuse, cast_teleport,
            cast_dragon_fart
        )
        
        # Map spell names to functions and parameters
        spell_name = wand_def.spell_name.lower()
        
        if spell_name == "fireball_scroll":
            return Item(
                use_function=cast_fireball,
                targeting=True,
                damage=wand_def.damage,
                radius=wand_def.radius
            )
        elif spell_name == "lightning_scroll":
            return Item(
                use_function=cast_lightning,
                damage=wand_def.damage,
                maximum_range=wand_def.maximum_range
            )
        elif spell_name == "confusion_scroll":
            return Item(use_function=cast_confuse, targeting=True)
        elif spell_name == "teleport_scroll":
            return Item(use_function=cast_teleport, targeting=True)
        elif spell_name == "dragon_fart_scroll":
            return Item(
                use_function=cast_dragon_fart,
                targeting=True,
                duration=wand_def.duration,
                range=wand_def.range,
                cone_width=wand_def.cone_width
            )
        elif spell_name == "yo_mama_scroll":
            from item_functions import cast_yo_mama
            return Item(
                use_function=cast_yo_mama,
                targeting=True,
                range=wand_def.range
            )
        else:
            logger.warning(f"Unknown wand spell '{spell_name}', creating basic item")
            return Item()

    def _create_fallback_monster(self, monster_type: str, x: int, y: int) -> Entity:
        """Create a fallback monster when definition is missing.
        
        Args:
            monster_type: The requested monster type
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Basic monster entity with default stats
        """
        fighter_component = Fighter(hp=10, defense=0, power=2, xp=10)
        ai_component = BasicMonster()
        
        return Entity(
            x=x, y=y, char='?', color=(255, 0, 255), name=f"Unknown {monster_type}",
            blocks=True, render_order=RenderOrder.ACTOR,
            fighter=fighter_component, ai=ai_component
        )

    def _create_fallback_weapon(self, weapon_type: str, x: int, y: int) -> Entity:
        """Create a fallback weapon when definition is missing.
        
        Args:
            weapon_type: The requested weapon type
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Basic weapon entity with default stats
        """
        equippable_component = Equippable(
            slot=EquipmentSlots.MAIN_HAND,
            power_bonus=1
        )
        
        return Entity(
            x=x, y=y, char='?', color=(255, 0, 255), name=f"Unknown {weapon_type}",
            equippable=equippable_component
        )

    def _create_fallback_armor(self, armor_type: str, x: int, y: int) -> Entity:
        """Create a fallback armor when definition is missing.
        
        Args:
            armor_type: The requested armor type
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Basic armor entity with default stats
        """
        equippable_component = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            defense_bonus=1
        )
        
        return Entity(
            x=x, y=y, char='?', color=(255, 0, 255), name=f"Unknown {armor_type}",
            equippable=equippable_component
        )

    def _create_fallback_spell(self, spell_type: str, x: int, y: int) -> Entity:
        """Create a fallback spell when definition is missing.
        
        Args:
            spell_type: The requested spell type
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Basic spell entity
        """
        item_component = Item()
        
        return Entity(
            x=x, y=y, char='?', color=(255, 0, 255), name=f"Unknown {spell_type}",
            item=item_component
        )


# Global factory instance
_entity_factory = None


def get_entity_factory() -> EntityFactory:
    """Get the global entity factory instance.
    
    Returns:
        The global EntityFactory instance
    """
    global _entity_factory
    if _entity_factory is None:
        _entity_factory = EntityFactory()
    return _entity_factory


def set_entity_factory(factory: EntityFactory) -> None:
    """Set the global entity factory instance.
    
    Args:
        factory: EntityFactory instance to use globally
    """
    global _entity_factory
    _entity_factory = factory
