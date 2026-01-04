"""Equippable item component.

This module defines the Equippable component which makes items
equippable and defines their stat bonuses and equipment slot.
"""

from typing import Optional, Any


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
        resistances (dict): Dict mapping ResistanceType to percentage (0-100)
        speed_bonus (float): Combat speed bonus ratio (Phase 5, e.g., 0.25 = +25%)
        material (str): Material type (metal/wood/bone/stone/organic/other) for corrosion
        base_damage_min (int): Original minimum damage (for corrosion floor calculation)
        base_damage_max (int): Original maximum damage (for corrosion floor calculation)
        owner (Entity): The entity that owns this component
    """

    def __init__(self, slot: Any, power_bonus: int = 0, defense_bonus: int = 0, max_hp_bonus: int = 0,
                 armor_class_bonus: int = 0, to_hit_bonus: int = 0,
                 damage_min: int = 0, damage_max: int = 0, defense_min: int = 0, defense_max: int = 0,
                 armor_type: Optional[str] = None, dex_cap: Optional[int] = None, damage_dice: Optional[str] = None,
                 two_handed: bool = False, reach: int = 1, resistances: Optional[dict] = None,
                 speed_bonus: float = 0.0,
                 crit_threshold: int = 20, damage_type: Optional[str] = None, material: Optional[str] = None,
                 applies_poison_on_hit: bool = False) -> None:
        """Initialize an Equippable component.

        Args:
            slot (Any): The equipment slot this item fits in (EquipmentSlots type)
            power_bonus (int, optional): Attack power bonus. Defaults to 0.
            defense_bonus (int, optional): Defense bonus. Defaults to 0.
            max_hp_bonus (int, optional): Maximum HP bonus. Defaults to 0.
            armor_class_bonus (int, optional): AC bonus for d20 combat. Defaults to 0.
            to_hit_bonus (int, optional): To-hit bonus for d20 combat. Defaults to 0.
            damage_min (int, optional): Minimum weapon damage. Defaults to 0.
            damage_max (int, optional): Maximum weapon damage. Defaults to 0.
            defense_min (int, optional): Minimum armor defense. Defaults to 0.
            defense_max (int, optional): Maximum armor defense. Defaults to 0.
            armor_type (Optional[str], optional): Armor type (light/medium/heavy). Defaults to None.
            dex_cap (Optional[int], optional): Max DEX modifier for AC (None = no cap). Defaults to None.
            damage_dice (Optional[str], optional): Dice notation for damage (e.g., "1d4", "2d6"). Defaults to None.
            two_handed (bool, optional): Requires both hands, prevents shield use. Defaults to False.
            reach (int, optional): Attack range in tiles (1 = adjacent, 2 = spear). Defaults to 1.
            resistances (Optional[dict], optional): Dict mapping ResistanceType to percentage (0-100). Defaults to None.
            speed_bonus (float, optional): Combat speed bonus ratio (Phase 5). Defaults to 0.0.
            material (Optional[str], optional): Material type (metal/wood/bone/stone/organic/other). Defaults to None.
        """
        self.slot: Any = slot
        self.power_bonus: int = power_bonus
        self.defense_bonus: int = defense_bonus
        self.max_hp_bonus: int = max_hp_bonus
        self.armor_class_bonus: int = armor_class_bonus
        self.to_hit_bonus: int = to_hit_bonus
        self.damage_min: int = damage_min if damage_min > 0 else 0
        self.damage_max: int = damage_max if damage_max >= damage_min else damage_min
        self.defense_min: int = defense_min if defense_min > 0 else 0
        self.defense_max: int = defense_max if defense_max >= defense_min else defense_min
        self.armor_type: Optional[str] = armor_type  # light, medium, heavy, shield, or weapon
        self.dex_cap: Optional[int] = dex_cap  # Maximum DEX modifier that applies to AC (None = no cap)
        self.damage_dice: Optional[str] = damage_dice  # Dice notation like "1d4", "1d6", "2d6"
        self.two_handed: bool = two_handed  # Requires both hands, prevents shield use
        self.reach: int = reach  # Attack range in tiles (1 = adjacent, 2 = spear reach)
        self.resistances: dict = resistances if resistances is not None else {}  # Resistance bonuses (ResistanceType: percentage)
        self.speed_bonus: float = speed_bonus  # Combat speed bonus ratio (Phase 5)
        # Phase 18: Affix mechanics
        self.crit_threshold: int = crit_threshold  # D20 roll needed for crit (default 20, Keen weapons 19)
        self.damage_type: Optional[str] = damage_type  # slashing, piercing, bludgeoning
        # Phase 19: Corrosion mechanics
        self.material: Optional[str] = material  # Material type for corrosion (metal/wood/bone/stone/organic/other)
        self.base_damage_min: int = damage_min  # Store original damage for corrosion floor (50% base)
        self.base_damage_max: int = damage_max  # Store original damage for corrosion floor (50% base)
        # Phase 20A.1: Player-facing poison delivery via weapon property
        self.applies_poison_on_hit: bool = bool(applies_poison_on_hit)
        self.owner: Optional[Any] = None  # Entity, Will be set when component is registered
    
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
        
        Returns:
            None
        """
        if self.damage_min > 0 or self.damage_max > 0:
            self.damage_min = max(1, self.damage_min + min_bonus)
            self.damage_max = max(self.damage_min, self.damage_max + max_bonus)
    
    def modify_defense_range(self, min_bonus: int, max_bonus: int) -> None:
        """Modify the armor's defense range (used by enhancement scrolls).
        
        Args:
            min_bonus (int): Amount to add to minimum defense
            max_bonus (int): Amount to add to maximum defense
        
        Returns:
            None
        """
        if self.defense_min > 0 or self.defense_max > 0:
            self.defense_min = max(1, self.defense_min + min_bonus)
            self.defense_max = max(self.defense_min, self.defense_max + max_bonus)
