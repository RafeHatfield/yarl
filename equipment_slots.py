"""Equipment slot enumeration for the equipment system.

This module defines the different equipment slots where items
can be equipped on a character.
"""

from enum import Enum


class EquipmentSlots(Enum):
    """Enumeration of equipment slots.

    Defines the different slots where equippable items can be placed.
    Each slot can hold one item at a time.
    
    Slots:
        MAIN_HAND: Primary weapon slot
        OFF_HAND: Shield or secondary weapon slot
        HEAD: Helmet/hat slot
        CHEST: Chest armor slot
        FEET: Boots/shoes slot
    """

    MAIN_HAND = 1
    OFF_HAND = 2
    HEAD = 3
    CHEST = 4
    FEET = 5
