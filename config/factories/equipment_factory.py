"""Equipment creation factory.

Handles creation of all equippable items:
- Weapons (with damage bonuses, reach, etc.)
- Armor (with defense bonuses, armor class, etc.)
- Rings (with passive effects)
"""

import logging
from typing import Optional

from entity import Entity
from components.component_registry import ComponentType
from components.item import Item
from components.equippable import Equippable
from components.ring import Ring, RingEffect
from render_functions import RenderOrder
from config.factories._factory_base import FactoryBase

logger = logging.getLogger(__name__)


class EquipmentFactory(FactoryBase):
    """Factory for creating equippable items (weapons, armor, rings)."""
    
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
            # Don't log - this is called as part of smart fallback chain
            return None  # Return None so caller can try armor

        try:
            # Convert string resistance types to ResistanceType enums if resistances are defined
            resistances_dict = None
            if weapon_def.resistances:
                from components.fighter import ResistanceType, normalize_resistance_type
                resistances_dict = {}
                for resist_type_str, value in weapon_def.resistances.items():
                    resist_enum = normalize_resistance_type(resist_type_str)
                    if resist_enum:
                        resistances_dict[resist_enum] = value
            
            # Create equippable component
            equippable_component = Equippable(
                slot=self._get_equipment_slot(weapon_def.slot),
                power_bonus=weapon_def.power_bonus,
                damage_min=weapon_def.damage_min,
                damage_max=weapon_def.damage_max,
                damage_dice=weapon_def.damage_dice,
                to_hit_bonus=weapon_def.to_hit_bonus,
                two_handed=weapon_def.two_handed,
                reach=weapon_def.reach,
                resistances=resistances_dict,
                speed_bonus=weapon_def.speed_bonus  # Phase 5
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
            # Don't log - this is called as part of smart fallback chain
            return None  # Return None so caller can try weapon

        try:
            # Convert string resistance types to ResistanceType enums if resistances are defined
            resistances_dict = None
            if armor_def.resistances:
                from components.fighter import ResistanceType, normalize_resistance_type
                resistances_dict = {}
                for resist_type_str, value in armor_def.resistances.items():
                    resist_enum = normalize_resistance_type(resist_type_str)
                    if resist_enum:
                        resistances_dict[resist_enum] = value
            
            # Create equippable component
            equippable_component = Equippable(
                slot=self._get_equipment_slot(armor_def.slot),
                defense_bonus=armor_def.defense_bonus,
                defense_min=armor_def.defense_min,
                defense_max=armor_def.defense_max,
                armor_class_bonus=armor_def.armor_class_bonus,
                armor_type=armor_def.armor_type,
                dex_cap=armor_def.dex_cap,
                resistances=resistances_dict,
                speed_bonus=armor_def.speed_bonus  # Phase 5
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

    def create_ring(self, ring_type: str, x: int, y: int) -> Optional[Entity]:
        """Create a ring item entity from configuration.
        
        Rings provide passive effects when equipped in left or right ring slots.
        All rings start unidentified and must be identified to reveal their effects.
        
        Args:
            ring_type: The type of ring to create (e.g., "ring_of_protection")
            x: X coordinate for the ring
            y: Y coordinate for the ring
            
        Returns:
            Entity instance if ring type exists, None otherwise
        """
        ring_def = self.registry.get_ring(ring_type)
        if not ring_def:
            # Don't log - this is called as part of smart fallback chain
            return None

        try:
            # Convert ring_effect string to RingEffect enum
            ring_effect_map = {
                "protection": RingEffect.PROTECTION,
                "regeneration": RingEffect.REGENERATION,
                "resistance": RingEffect.RESISTANCE,
                "strength": RingEffect.STRENGTH,
                "dexterity": RingEffect.DEXTERITY,
                "might": RingEffect.MIGHT,
                "teleportation": RingEffect.TELEPORTATION,
                "invisibility": RingEffect.INVISIBILITY,
                "searching": RingEffect.SEARCHING,
                "free_action": RingEffect.FREE_ACTION,
                "wizardry": RingEffect.WIZARDRY,
                "clarity": RingEffect.CLARITY,
                "speed": RingEffect.SPEED,
                "constitution": RingEffect.CONSTITUTION,
                "luck": RingEffect.LUCK,
            }
            
            ring_effect_enum = ring_effect_map.get(ring_def.ring_effect.lower())
            if not ring_effect_enum:
                logger.error(f"Unknown ring effect: {ring_def.ring_effect}")
                return None
            
            # Create ring component with its passive effect
            ring_component = Ring(
                ring_effect=ring_effect_enum,
                effect_strength=ring_def.effect_strength
            )
            
            # Convert string resistance types to ResistanceType enums if resistances are defined
            resistances_dict = None
            if hasattr(ring_def, 'resistances') and ring_def.resistances:
                from components.fighter import ResistanceType, normalize_resistance_type
                resistances_dict = {}
                for resist_type_str, value in ring_def.resistances.items():
                    resist_enum = normalize_resistance_type(resist_type_str)
                    if resist_enum:
                        resistances_dict[resist_enum] = value
            
            # Create equippable component for ring slot
            from equipment_slots import EquipmentSlots
            equippable_component = Equippable(
                slot=EquipmentSlots.RING,  # Uses generic RING slot, will be assigned to left or right
                resistances=resistances_dict,
                speed_bonus=ring_def.speed_bonus  # Phase 5
            )
            
            # Create item component
            item_component = Item()
            
            # Apply identification logic for rings
            self._apply_identification_logic(item_component, ring_type, "ring")
            
            # Create entity
            ring_entity = Entity(
                x=x,
                y=y,
                char=ring_def.char,
                color=ring_def.color,
                name=ring_def.name,
                item=item_component,
                equippable=equippable_component
            )
            
            # Attach ring component
            # Note: Setting ring_entity.ring triggers __setattr__ which auto-registers in components
            ring_entity.ring = ring_component
            ring_component.owner = ring_entity
            
            logger.debug(f"Created ring: {ring_def.name} at ({x}, {y}) [identified: {item_component.identified}]")
            return ring_entity

        except Exception as e:
            logger.error(f"Error creating ring {ring_type}: {e}")
            return None

