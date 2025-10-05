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
        armor_class_bonus (int): Armor Class bonus for d20 combat (0 for non-armor)
        to_hit_bonus (int): To-hit bonus for d20 combat (0 for non-weapons)
        damage_min (int): Minimum damage for weapons (0 for non-weapons)
        damage_max (int): Maximum damage for weapons (0 for non-weapons)
        defense_min (int): Minimum defense for armor (0 for non-armor)
        defense_max (int): Maximum defense for armor (0 for non-armor)
        armor_type (str): Type of armor (light/medium/heavy/shield/weapon)
        dex_cap (int): Maximum DEX modifier that applies to AC (None = no cap)
        two_handed (bool): Requires both hands, prevents shield use
        reach (int): Attack range in tiles (1 = adjacent, 2 = spear reach)
        owner (Entity): The entity that owns this component
    """

    def __init__(self, slot, power_bonus=0, defense_bonus=0, max_hp_bonus=0,
                 armor_class_bonus=0, to_hit_bonus=0,
                 damage_min=0, damage_max=0, defense_min=0, defense_max=0,
                 armor_type=None, dex_cap=None, damage_dice=None,
                 two_handed=False, reach=1):
        """Initialize an Equippable component.

        Args:
            slot (EquipmentSlots): The equipment slot this item fits in
            power_bonus (int, optional): Attack power bonus. Defaults to 0.
            defense_bonus (int, optional): Defense bonus. Defaults to 0.
            max_hp_bonus (int, optional): Maximum HP bonus. Defaults to 0.
            armor_class_bonus (int, optional): AC bonus for d20 combat. Defaults to 0.
            to_hit_bonus (int, optional): To-hit bonus for d20 combat. Defaults to 0.
            damage_min (int, optional): Minimum weapon damage. Defaults to 0.
            damage_max (int, optional): Maximum weapon damage. Defaults to 0.
            defense_min (int, optional): Minimum armor defense. Defaults to 0.
            defense_max (int, optional): Maximum armor defense. Defaults to 0.
            armor_type (str, optional): Armor type (light/medium/heavy). Defaults to None.
            dex_cap (int, optional): Max DEX modifier for AC (None = no cap). Defaults to None.
            damage_dice (str, optional): Dice notation for damage (e.g., "1d4", "2d6"). Defaults to None.
            two_handed (bool, optional): Requires both hands, prevents shield use. Defaults to False.
            reach (int, optional): Attack range in tiles (1 = adjacent, 2 = spear). Defaults to 1.
        """
        self.slot = slot
        self.power_bonus = power_bonus
        self.defense_bonus = defense_bonus
        self.max_hp_bonus = max_hp_bonus
        self.armor_class_bonus = armor_class_bonus
        self.to_hit_bonus = to_hit_bonus
        self.damage_min = damage_min if damage_min > 0 else 0
        self.damage_max = damage_max if damage_max >= damage_min else damage_min
        self.defense_min = defense_min if defense_min > 0 else 0
        self.defense_max = defense_max if defense_max >= defense_min else defense_min
        self.armor_type = armor_type  # light, medium, heavy, shield, or weapon
        self.dex_cap = dex_cap  # Maximum DEX modifier that applies to AC (None = no cap)
        self.damage_dice = damage_dice  # Dice notation like "1d4", "1d6", "2d6"
        self.two_handed = two_handed  # Requires both hands, prevents shield use
        self.reach = reach  # Attack range in tiles (1 = adjacent, 2 = spear reach)
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
        """Roll damage using dice notation or damage range.
        
        Prefers dice notation if available, otherwise uses damage_min/max range.
        
        Returns:
            int: Random damage value
        """
        # Use dice notation if available
        if self.damage_dice:
            from dice import roll_dice
            return roll_dice(self.damage_dice)
        
        # Fall back to legacy damage range
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
