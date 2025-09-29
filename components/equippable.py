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
        damage_min (int): Minimum damage for weapons (0 for non-weapons)
        damage_max (int): Maximum damage for weapons (0 for non-weapons)
        defense_min (int): Minimum defense for armor (0 for non-armor)
        defense_max (int): Maximum defense for armor (0 for non-armor)
        owner (Entity): The entity that owns this component
    """

    def __init__(self, slot, power_bonus=0, defense_bonus=0, max_hp_bonus=0,
                 damage_min=0, damage_max=0, defense_min=0, defense_max=0):
        """Initialize an Equippable component.

        Args:
            slot (EquipmentSlots): The equipment slot this item fits in
            power_bonus (int, optional): Attack power bonus. Defaults to 0.
            defense_bonus (int, optional): Defense bonus. Defaults to 0.
            max_hp_bonus (int, optional): Maximum HP bonus. Defaults to 0.
            damage_min (int, optional): Minimum weapon damage. Defaults to 0.
            damage_max (int, optional): Maximum weapon damage. Defaults to 0.
            defense_min (int, optional): Minimum armor defense. Defaults to 0.
            defense_max (int, optional): Maximum armor defense. Defaults to 0.
        """
        self.slot = slot
        self.power_bonus = power_bonus
        self.defense_bonus = defense_bonus
        self.max_hp_bonus = max_hp_bonus
        self.damage_min = damage_min if damage_min > 0 else 0
        self.damage_max = damage_max if damage_max >= damage_min else damage_min
        self.defense_min = defense_min if defense_min > 0 else 0
        self.defense_max = defense_max if defense_max >= defense_min else defense_min
        self.owner = None  # Will be set by Entity when component is registered
    
    def get_damage_range_text(self) -> str:
        """Get formatted damage range text for display.
        
        Returns:
            str: Formatted damage range like "(2-5 damage)" or empty string if no damage
        """
        if self.damage_min > 0 and self.damage_max > 0:
            if self.damage_min == self.damage_max:
                return f"({self.damage_min} damage)"
            else:
                return f"({self.damage_min}-{self.damage_max} damage)"
        return ""
    
    def get_defense_range_text(self) -> str:
        """Get formatted defense range text for display.
        
        Returns:
            str: Formatted defense range like "(1-3 defense)" or empty string if no defense
        """
        if self.defense_min > 0 and self.defense_max > 0:
            if self.defense_min == self.defense_max:
                return f"({self.defense_min} defense)"
            else:
                return f"({self.defense_min}-{self.defense_max} defense)"
        return ""
    
    def roll_damage(self) -> int:
        """Roll damage within the weapon's damage range.
        
        Returns:
            int: Random damage value between damage_min and damage_max (inclusive)
        """
        if self.damage_min > 0 and self.damage_max > 0:
            import random
            return random.randint(self.damage_min, self.damage_max)
        return 0
    
    def roll_defense(self) -> int:
        """Roll defense within the armor's defense range.
        
        Returns:
            int: Random defense value between defense_min and defense_max (inclusive)
        """
        if self.defense_min > 0 and self.defense_max > 0:
            import random
            return random.randint(self.defense_min, self.defense_max)
        return 0
    
    def modify_damage_range(self, min_bonus: int, max_bonus: int) -> None:
        """Modify the weapon's damage range (used by enhancement scrolls).
        
        Args:
            min_bonus (int): Amount to add to minimum damage
            max_bonus (int): Amount to add to maximum damage
        """
        if self.damage_min > 0 or self.damage_max > 0:
            self.damage_min = max(1, self.damage_min + min_bonus)
            self.damage_max = max(self.damage_min, self.damage_max + max_bonus)
    
    def modify_defense_range(self, min_bonus: int, max_bonus: int) -> None:
        """Modify the armor's defense range (used by enhancement scrolls).
        
        Args:
            min_bonus (int): Amount to add to minimum defense
            max_bonus (int): Amount to add to maximum defense
        """
        if self.defense_min > 0 or self.defense_max > 0:
            self.defense_min = max(1, self.defense_min + min_bonus)
            self.defense_max = max(self.defense_min, self.defense_max + max_bonus)
