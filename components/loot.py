"""Loot quality and rarity system for item drops.

This module provides a comprehensive loot system with quality tiers,
level-scaled drop chances, and magic item generation. It adds depth
to monster loot drops and player progression.

Features:
- 4 rarity tiers: Common, Uncommon, Rare, Legendary
- Level-scaled drop chances (better loot at deeper levels)
- Quality affects item stats (+1 to +5 bonuses)
- Loot tables per monster type
- Magic prefix/suffix system

Usage:
    loot_gen = LootGenerator()
    item = loot_gen.generate_loot(dungeon_level, monster_type="orc")
"""

from enum import Enum
from typing import Optional, Tuple, Dict, Any
from random import randint, random, choice
import logging

from entity import Entity
from components.item import Item
from components.equippable import Equippable
from equipment_slots import EquipmentSlots
from render_functions import RenderOrder

logger = logging.getLogger(__name__)


class LootRarity(Enum):
    """Loot quality/rarity tiers.
    
    Each tier has different drop chances and stat bonuses:
    - COMMON: White color, +0-1 bonus, 60% drop rate
    - UNCOMMON: Green color, +1-2 bonus, 30% drop rate
    - RARE: Blue color, +2-4 bonus, 8% drop rate
    - LEGENDARY: Gold color, +3-5 bonus, 2% drop rate
    """
    COMMON = ("Common", (255, 255, 255), 0.60, (0, 1))      # White, 60%, +0-1
    UNCOMMON = ("Uncommon", (100, 255, 100), 0.30, (1, 2))  # Green, 30%, +1-2
    RARE = ("Rare", (100, 150, 255), 0.08, (2, 4))          # Blue, 8%, +2-4
    LEGENDARY = ("Legendary", (255, 215, 0), 0.02, (3, 5))  # Gold, 2%, +3-5
    
    def __init__(self, display_name: str, color: Tuple[int, int, int], 
                 base_chance: float, bonus_range: Tuple[int, int]):
        self.display_name = display_name
        self.color = color
        self.base_chance = base_chance
        self.bonus_range = bonus_range
    
    def get_bonus(self) -> int:
        """Get a random bonus value for this rarity tier."""
        return randint(*self.bonus_range)


class LootComponent:
    """Component for storing loot metadata on items.
    
    Tracks item rarity, quality bonuses, and magic properties.
    Displayed in tooltips and affects item value/power.
    """
    
    def __init__(self, rarity: LootRarity, quality_bonus: int = 0, is_magical: bool = False):
        """Initialize loot component.
        
        Args:
            rarity: LootRarity tier
            quality_bonus: Additional stat bonus from quality
            is_magical: Whether item has magic properties
        """
        self.rarity = rarity
        self.quality_bonus = quality_bonus
        self.is_magical = is_magical
        self.magic_prefix = None
        self.magic_suffix = None


class LootGenerator:
    """Generates loot with quality tiers and level scaling.
    
    Handles all loot generation logic including:
    - Determining item rarity based on dungeon level
    - Applying quality bonuses to item stats
    - Adding magic prefixes/suffixes
    - Creating themed loot for specific monster types
    """
    
    # Magic prefixes and suffixes for flavor
    WEAPON_PREFIXES = [
        ("Sharp", 1, 0),
        ("Keen", 2, 0),
        ("Deadly", 3, 0),
        ("Vicious", 2, 0),
        ("Masterwork", 3, 1),
    ]
    
    ARMOR_PREFIXES = [
        ("Sturdy", 0, 1),
        ("Reinforced", 0, 2),
        ("Blessed", 1, 2),
        ("Runed", 0, 3),
        ("Enchanted", 1, 3),
    ]
    
    WEAPON_SUFFIXES = [
        ("of Striking", 1, 0),
        ("of Power", 2, 0),
        ("of Slaying", 3, 0),
        ("of the Warrior", 2, 1),
    ]
    
    ARMOR_SUFFIXES = [
        ("of Protection", 0, 1),
        ("of Warding", 0, 2),
        ("of the Guardian", 1, 2),
        ("of Invulnerability", 0, 3),
    ]
    
    def __init__(self):
        """Initialize loot generator."""
        pass
    
    def determine_rarity(self, dungeon_level: int, luck_modifier: float = 0.0) -> LootRarity:
        """Determine loot rarity based on dungeon level and luck.
        
        Drop chances improve with dungeon level:
        - Level 1-3: Mostly common
        - Level 4-6: Some uncommon
        - Level 7-9: Rare items start appearing
        - Level 10+: Legendary possible
        
        Args:
            dungeon_level: Current dungeon level (1-15+)
            luck_modifier: Bonus to rare drop chance (0.0 - 1.0)
            
        Returns:
            LootRarity tier
        """
        # Calculate level scaling factor (0.0 at level 1, 1.0 at level 10)
        level_factor = min(dungeon_level / 10.0, 1.5)
        
        # Roll for rarity with level scaling
        roll = random() - (level_factor * 0.1) - luck_modifier
        
        # Check from best to worst
        cumulative = 0.0
        
        # Legendary (2% base, +level scaling)
        legendary_chance = LootRarity.LEGENDARY.base_chance * (1 + level_factor)
        cumulative += legendary_chance
        if roll < cumulative:
            logger.debug(f"Legendary drop! (level {dungeon_level}, roll {roll:.3f})")
            return LootRarity.LEGENDARY
        
        # Rare (8% base, +level scaling)
        rare_chance = LootRarity.RARE.base_chance * (1 + level_factor * 0.5)
        cumulative += rare_chance
        if roll < cumulative:
            return LootRarity.RARE
        
        # Uncommon (30% base, scales down slightly)
        uncommon_chance = LootRarity.UNCOMMON.base_chance * (1 - level_factor * 0.1)
        cumulative += uncommon_chance
        if roll < cumulative:
            return LootRarity.UNCOMMON
        
        # Common (everything else)
        return LootRarity.COMMON
    
    def generate_weapon(
        self,
        x: int,
        y: int,
        dungeon_level: int,
        rarity: Optional[LootRarity] = None
    ) -> Entity:
        """Generate a weapon with quality bonuses.
        
        Args:
            x: X coordinate
            y: Y coordinate
            dungeon_level: Current dungeon level for base stats
            rarity: Force specific rarity, or None for random
            
        Returns:
            Entity with Equippable component (weapon)
        """
        if rarity is None:
            rarity = self.determine_rarity(dungeon_level)
        
        # Base weapon stats scale with level
        base_power = 2 + (dungeon_level // 2)
        
        # Apply rarity bonus
        quality_bonus = rarity.get_bonus()
        final_power = base_power + quality_bonus
        
        # Create weapon
        weapon_equippable = Equippable(
            slot=EquipmentSlots.MAIN_HAND,
            power_bonus=final_power
        )
        
        # Generate name
        weapon_name = self._generate_weapon_name(rarity, quality_bonus)
        
        weapon = Entity(
            x, y, "/", rarity.color, weapon_name,
            equippable=weapon_equippable,
            item=Item(),
            render_order=RenderOrder.ITEM
        )
        
        # Add loot component for metadata
        weapon.loot = LootComponent(rarity, quality_bonus, is_magical=(rarity != LootRarity.COMMON))
        
        logger.info(f"Generated {rarity.display_name} weapon: {weapon_name} (+{final_power} power)")
        return weapon
    
    def generate_armor(
        self,
        x: int,
        y: int,
        dungeon_level: int,
        rarity: Optional[LootRarity] = None
    ) -> Entity:
        """Generate armor with quality bonuses.
        
        Args:
            x: X coordinate
            y: Y coordinate
            dungeon_level: Current dungeon level for base stats
            rarity: Force specific rarity, or None for random
            
        Returns:
            Entity with Equippable component (armor)
        """
        if rarity is None:
            rarity = self.determine_rarity(dungeon_level)
        
        # Base armor stats scale with level
        base_defense = 1 + (dungeon_level // 3)
        
        # Apply rarity bonus
        quality_bonus = rarity.get_bonus()
        final_defense = base_defense + quality_bonus
        
        # Create armor
        armor_equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,  # Shield for now
            defense_bonus=final_defense
        )
        
        # Generate name
        armor_name = self._generate_armor_name(rarity, quality_bonus)
        
        armor = Entity(
            x, y, "]", rarity.color, armor_name,
            equippable=armor_equippable,
            item=Item(),
            render_order=RenderOrder.ITEM
        )
        
        # Add loot component for metadata
        armor.loot = LootComponent(rarity, quality_bonus, is_magical=(rarity != LootRarity.COMMON))
        
        logger.info(f"Generated {rarity.display_name} armor: {armor_name} (+{final_defense} defense)")
        return armor
    
    def _generate_weapon_name(self, rarity: LootRarity, bonus: int) -> str:
        """Generate a flavorful weapon name based on rarity.
        
        Args:
            rarity: Item rarity tier
            bonus: Quality bonus value
            
        Returns:
            Weapon name string
        """
        base_names = ["Sword", "Axe", "Mace", "Dagger", "Spear"]
        base = choice(base_names)
        
        if rarity == LootRarity.COMMON:
            return f"{base}"
        elif rarity == LootRarity.UNCOMMON:
            prefix, _, _ = choice(self.WEAPON_PREFIXES[:2])  # Sharp, Keen
            return f"{prefix} {base}"
        elif rarity == LootRarity.RARE:
            prefix, _, _ = choice(self.WEAPON_PREFIXES[2:4])  # Deadly, Vicious
            return f"{prefix} {base}"
        else:  # LEGENDARY
            prefix, _, _ = choice(self.WEAPON_PREFIXES[3:])  # Vicious, Masterwork
            suffix, _, _ = choice(self.WEAPON_SUFFIXES[2:])  # of Slaying, of the Warrior
            return f"{prefix} {base} {suffix}"
    
    def _generate_armor_name(self, rarity: LootRarity, bonus: int) -> str:
        """Generate a flavorful armor name based on rarity.
        
        Args:
            rarity: Item rarity tier
            bonus: Quality bonus value
            
        Returns:
            Armor name string
        """
        base_names = ["Shield", "Buckler", "Tower Shield"]
        base = choice(base_names)
        
        if rarity == LootRarity.COMMON:
            return f"{base}"
        elif rarity == LootRarity.UNCOMMON:
            prefix, _, _ = choice(self.ARMOR_PREFIXES[:2])  # Sturdy, Reinforced
            return f"{prefix} {base}"
        elif rarity == LootRarity.RARE:
            prefix, _, _ = choice(self.ARMOR_PREFIXES[2:4])  # Blessed, Runed
            return f"{prefix} {base}"
        else:  # LEGENDARY
            prefix, _, _ = choice(self.ARMOR_PREFIXES[3:])  # Runed, Enchanted
            suffix, _, _ = choice(self.ARMOR_SUFFIXES[2:])  # of the Guardian, of Invulnerability
            return f"{prefix} {base} {suffix}"
    
    def should_monster_drop_loot(self, monster_name: str, dungeon_level: int) -> bool:
        """Determine if a monster should drop loot.
        
        Not all monsters drop equipment:
        - Slimes: No drops (they're blobs!)
        - Weak monsters: 30% chance
        - Normal monsters: 50% chance
        - Strong monsters: 70% chance
        - Bosses: 100% chance
        
        Args:
            monster_name: Name of the monster
            dungeon_level: Current dungeon level
            
        Returns:
            True if monster should drop loot
        """
        monster_lower = monster_name.lower()
        
        # Slimes never drop equipment
        if 'slime' in monster_lower:
            return False
        
        # Boss-type monsters always drop
        if any(boss in monster_lower for boss in ['dragon', 'demon', 'lord', 'king', 'champion']):
            return True
        
        # Weak monsters (rat, bat, etc.)
        if any(weak in monster_lower for weak in ['rat', 'bat', 'spider', 'goblin']):
            return random() < 0.30
        
        # Strong monsters
        if any(strong in monster_lower for strong in ['troll', 'ogre', 'warrior', 'knight']):
            return random() < 0.70
        
        # Normal monsters
        return random() < 0.50


# Global loot generator instance
_loot_generator = None

def get_loot_generator() -> LootGenerator:
    """Get the global loot generator instance.
    
    Returns:
        LootGenerator singleton
    """
    global _loot_generator
    if _loot_generator is None:
        _loot_generator = LootGenerator()
    return _loot_generator

