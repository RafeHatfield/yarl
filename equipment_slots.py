"""Equipment slot enumeration for the equipment system.

This module defines the different equipment slots where items
can be equipped on a character.
"""

from enum import Enum


class EquipmentSlots(Enum):
    """Enumeration of equipment slots.

    Defines the different slots where equippable items can be placed.
    Each slot can hold one item at a time.
    """

    MAIN_HAND = 1
    OFF_HAND = 2
