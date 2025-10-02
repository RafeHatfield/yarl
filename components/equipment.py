"""Equipment management component.

This module defines the Equipment component which manages equipped items
and calculates total stat bonuses from all equipped gear.
"""

import logging
from equipment_slots import EquipmentSlots

logger = logging.getLogger(__name__)


class Equipment:
    """Component that manages equipped items and their stat bonuses.

    This component handles equipment slots (weapons, shields, armor) and
    calculates the total stat bonuses provided by all equipped items.
    It supports equipping, unequipping, and replacing items.

    Attributes:
        main_hand (Entity): Item equipped in the main hand slot (weapon)
        off_hand (Entity): Item equipped in the off hand slot (shield/weapon)
        head (Entity): Item equipped in the head slot (helmet)
        chest (Entity): Item equipped in the chest slot (armor)
        feet (Entity): Item equipped in the feet slot (boots)
        owner (Entity): The entity that owns this equipment component
    """

    def __init__(self, main_hand=None, off_hand=None, head=None, chest=None, feet=None):
        """Initialize the Equipment component.

        Args:
            main_hand (Entity, optional): Initial main hand equipment
            off_hand (Entity, optional): Initial off hand equipment
            head (Entity, optional): Initial head equipment
            chest (Entity, optional): Initial chest equipment
            feet (Entity, optional): Initial feet equipment
        """
        self.main_hand = main_hand
        self.off_hand = off_hand
        self.head = head
        self.chest = chest
        self.feet = feet
        self.owner = None  # Will be set by Entity when component is registered

    @property
    def max_hp_bonus(self):
        """Calculate total max HP bonus from all equipped items.

        Returns:
            int: Total maximum HP bonus from equipped items
        """
        bonus = 0

        for item in [self.main_hand, self.off_hand, self.head, self.chest, self.feet]:
            if item and item.equippable:
                item_bonus = item.equippable.max_hp_bonus
                # Defensive: treat None as 0
                if item_bonus is not None:
                    bonus += item_bonus

        return bonus

    @property
    def power_bonus(self):
        """Calculate total power bonus from all equipped items.

        Returns:
            int: Total attack power bonus from equipped items
        """
        bonus = 0

        for item in [self.main_hand, self.off_hand, self.head, self.chest, self.feet]:
            if item and item.equippable:
                item_bonus = item.equippable.power_bonus
                # Defensive: treat None as 0
                if item_bonus is not None:
                    bonus += item_bonus

        return bonus

    @property
    def defense_bonus(self):
        """Calculate total defense bonus from all equipped items.

        Returns:
            int: Total defense bonus from equipped items
        """
        bonus = 0

        for item in [self.main_hand, self.off_hand, self.head, self.chest, self.feet]:
            if item and item.equippable:
                item_bonus = item.equippable.defense_bonus
                # Defensive: treat None as 0
                if item_bonus is not None:
                    bonus += item_bonus

        return bonus

    def toggle_equip(self, equippable_entity):
        """Equip, unequip, or replace an item in the appropriate slot.

        If the item is already equipped, it will be unequipped.
        If the slot is empty, the item will be equipped.
        If the slot has a different item, it will be replaced.

        Args:
            equippable_entity (Entity): The entity with an equippable component

        Returns:
            list: List of result dictionaries with 'equipped' or 'dequipped' keys
        """
        results = []
        slot = equippable_entity.equippable.slot

        # Map slots to their attributes
        slot_map = {
            EquipmentSlots.MAIN_HAND: 'main_hand',
            EquipmentSlots.OFF_HAND: 'off_hand',
            EquipmentSlots.HEAD: 'head',
            EquipmentSlots.CHEST: 'chest',
            EquipmentSlots.FEET: 'feet'
        }

        slot_attr = slot_map.get(slot)
        if not slot_attr:
            return results  # Unknown slot

        current_item = getattr(self, slot_attr)

        if current_item == equippable_entity:
            # Unequip the item
            setattr(self, slot_attr, None)
            results.append({"dequipped": equippable_entity})
        else:
            # Replace or equip
            if current_item:
                results.append({"dequipped": current_item})

            setattr(self, slot_attr, equippable_entity)
            results.append({"equipped": equippable_entity})

        return results
