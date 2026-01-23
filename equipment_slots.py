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
        LEFT_RING: Left ring slot
        RIGHT_RING: Right ring slot
        RING: Generic ring slot (will auto-select left or right)
        QUIVER: Special ammo slot for ranged weapons (Phase 22.2.2)
    """

    MAIN_HAND = 1
    OFF_HAND = 2
    HEAD = 3
    CHEST = 4
    FEET = 5
    LEFT_RING = 6
    RIGHT_RING = 7
    RING = 8  # Auto-selects left or right slot
    QUIVER = 9  # Phase 22.2.2: Special ammo for bows/crossbows
