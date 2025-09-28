"""Equippable item component.

This module defines the Equippable component which makes items
equippable and defines their stat bonuses and equipment slot.
"""


class Equippable:
    """Component that makes an entity equippable with stat bonuses.

    This component defines an item that can be equipped in a specific slot
    and provides various stat bonuses to the entity that equips it.

    Attributes:
        slot (EquipmentSlots): The equipment slot this item fits in
        power_bonus (int): Attack power bonus provided by this item
        defense_bonus (int): Defense bonus provided by this item
        max_hp_bonus (int): Maximum HP bonus provided by this item
        owner (Entity): The entity that owns this component
    """

    def __init__(self, slot, power_bonus=0, defense_bonus=0, max_hp_bonus=0):
        """Initialize an Equippable component.

        Args:
            slot (EquipmentSlots): The equipment slot this item fits in
            power_bonus (int, optional): Attack power bonus. Defaults to 0.
            defense_bonus (int, optional): Defense bonus. Defaults to 0.
            max_hp_bonus (int, optional): Maximum HP bonus. Defaults to 0.
        """
        self.slot = slot
        self.power_bonus = power_bonus
        self.defense_bonus = defense_bonus
        self.max_hp_bonus = max_hp_bonus
        self.owner = None  # Will be set by Entity when component is registered
