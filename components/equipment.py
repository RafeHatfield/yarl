"""Equipment management component.

This module defines the Equipment component which manages equipped items
and calculates total stat bonuses from all equipped gear.
"""

from equipment_slots import EquipmentSlots


class Equipment:
    """Component that manages equipped items and their stat bonuses.

    This component handles equipment slots (main hand and off hand) and
    calculates the total stat bonuses provided by all equipped items.
    It supports equipping, unequipping, and replacing items.

    Attributes:
        main_hand (Entity): Item equipped in the main hand slot
        off_hand (Entity): Item equipped in the off hand slot
        owner (Entity): The entity that owns this equipment component
    """

    def __init__(self, main_hand=None, off_hand=None):
        """Initialize the Equipment component.

        Args:
            main_hand (Entity, optional): Initial main hand equipment
            off_hand (Entity, optional): Initial off hand equipment
        """
        self.main_hand = main_hand
        self.off_hand = off_hand
        self.owner = None  # Will be set by Entity when component is registered

    @property
    def max_hp_bonus(self):
        """Calculate total max HP bonus from all equipped items.

        Returns:
            int: Total maximum HP bonus from equipped items
        """
        bonus = 0

        if self.main_hand and self.main_hand.equippable:
            bonus += self.main_hand.equippable.max_hp_bonus

        if self.off_hand and self.off_hand.equippable:
            bonus += self.off_hand.equippable.max_hp_bonus

        return bonus

    @property
    def power_bonus(self):
        """Calculate total power bonus from all equipped items.

        Returns:
            int: Total attack power bonus from equipped items
        """
        bonus = 0

        if self.main_hand and self.main_hand.equippable:
            bonus += self.main_hand.equippable.power_bonus

        if self.off_hand and self.off_hand.equippable:
            bonus += self.off_hand.equippable.power_bonus

        return bonus

    @property
    def defense_bonus(self):
        """Calculate total defense bonus from all equipped items.

        Returns:
            int: Total defense bonus from equipped items
        """
        bonus = 0

        if self.main_hand and self.main_hand.equippable:
            bonus += self.main_hand.equippable.defense_bonus

        if self.off_hand and self.off_hand.equippable:
            bonus += self.off_hand.equippable.defense_bonus

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

        if slot == EquipmentSlots.MAIN_HAND:
            if self.main_hand == equippable_entity:
                self.main_hand = None
                results.append({"dequipped": equippable_entity})
            else:
                if self.main_hand:
                    results.append({"dequipped": self.main_hand})

                self.main_hand = equippable_entity
                results.append({"equipped": equippable_entity})
        elif slot == EquipmentSlots.OFF_HAND:
            if self.off_hand == equippable_entity:
                self.off_hand = None
                results.append({"dequipped": equippable_entity})
            else:
                if self.off_hand:
                    results.append({"dequipped": self.off_hand})

                self.off_hand = equippable_entity
                results.append({"equipped": equippable_entity})

        return results
