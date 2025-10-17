"""Centralized game configuration and constants.

This module contains all game constants, magic numbers, and configuration
values in one place for easy maintenance and tuning.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, Union
import os
import json
import logging

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None

logger = logging.getLogger(__name__)


@dataclass
class PathfindingConfig:
    """Configuration for pathfinding and movement systems."""
    
    # A* pathfinding constants
    DIAGONAL_MOVE_COST: float = 1.41  # Normal diagonal movement cost
    MAX_PATH_LENGTH_IN_FOV: int = 40  # Maximum path length when destination is visible
    MAX_PATH_LENGTH_OUT_FOV: int = 25  # Maximum path length when destination is not visible
    MAX_PATH_LENGTH_EXPLORED: int = 150  # Maximum path length for explored (but not visible) tiles
    
    # Legacy compatibility
    @property
    def MAX_PATH_LENGTH(self) -> int:
        """Legacy property for backward compatibility. Returns out-of-FOV limit."""
        return self.MAX_PATH_LENGTH_OUT_FOV
    
    # Movement validation
    MAX_COORDINATE: int = 9999  # Maximum valid map coordinate


@dataclass
class PerformanceConfig:
    """Configuration for performance optimization systems."""
    
    # Spatial indexing
    SPATIAL_GRID_SIZE: int = 8  # Grid cell size for spatial entity indexing
    
    # FOV caching
    FOV_CACHE_SIZE: int = 100  # Maximum number of cached FOV results
    
    # Rendering
    TARGET_FPS: int = 60  # Target frames per second
    MAX_DIRTY_RECTANGLES: int = 50  # Maximum dirty rectangles before full redraw


@dataclass
class CombatConfig:
    """Configuration for combat and character stats."""
    
    # Default character stats
    DEFAULT_DEFENSE: int = 0
    DEFAULT_POWER: int = 1
    DEFAULT_HP: int = 1
    DEFAULT_XP: int = 0
    
    # Combat calculations
    MIN_DAMAGE: int = 0  # Minimum damage that can be dealt
    
    # Level progression
    DEFAULT_LEVEL_UP_BASE: int = 200  # Base XP required for level 2
    DEFAULT_LEVEL_UP_FACTOR: int = 150  # Additional XP per level


@dataclass
class InventoryConfig:
    """Configuration for inventory and item systems."""
    
    # Default inventory settings
    DEFAULT_INVENTORY_CAPACITY: int = 25  # Sidebar has plenty of room for more items!
    
    # Item usage
    MAX_ITEM_NAME_LENGTH: int = 50  # Maximum length for item names


@dataclass
class RenderingConfig:
    """Configuration for rendering and display systems."""
    
    # Screen dimensions (can be overridden by user config)
    DEFAULT_SCREEN_WIDTH: int = 80
    DEFAULT_SCREEN_HEIGHT: int = 50
    DEFAULT_PANEL_HEIGHT: int = 7
    DEFAULT_BAR_WIDTH: int = 20
    
    # FOV settings
    DEFAULT_FOV_RADIUS: int = 10
    DEFAULT_FOV_LIGHT_WALLS: bool = True
    DEFAULT_FOV_ALGORITHM: int = 0  # tcod.FOV_BASIC
    
    # Message log
    DEFAULT_MESSAGE_LOG_HEIGHT: int = 5
    DEFAULT_MESSAGE_LOG_WIDTH: int = 40


@dataclass
class EntityConfig:
    """Configuration for entity system and data loading."""
    
    # Entity configuration file paths
    ENTITIES_CONFIG_PATH: str = "config/entities.yaml"
    FALLBACK_ENTITIES_CONFIG_PATH: str = "config/entities_fallback.yaml"
    
    # Entity validation settings
    VALIDATE_ENTITY_STATS: bool = True
    ALLOW_MISSING_ENTITIES: bool = True  # Use fallback entities when definitions missing
    
    # Entity inheritance settings
    MAX_INHERITANCE_DEPTH: int = 5  # Prevent infinite inheritance loops
    ENABLE_ENTITY_INHERITANCE: bool = True
    
    # Logging settings for entity system
    LOG_ENTITY_CREATION: bool = False  # Enable for debugging entity creation
    LOG_MISSING_ENTITIES: bool = True  # Log when entities are missing from config


@dataclass
class MonsterEquipmentConfig:
    """Configuration for monster equipment spawning and behavior."""
    
    # Equipment spawn rates (normal mode)
    NORMAL_BASE_CHANCE: float = 0.1  # 10% base chance
    NORMAL_LEVEL_MULTIPLIER: float = 1.0  # Multiply by dungeon level
    NORMAL_MAX_CHANCE: float = 0.7  # 70% maximum chance
    
    # Equipment spawn rates (testing mode)
    TESTING_BASE_CHANCE: float = 0.5  # 50% flat chance
    TESTING_LEVEL_MULTIPLIER: float = 0.0  # No level scaling in testing
    TESTING_MAX_CHANCE: float = 0.5  # 50% maximum chance
    
    # Equipment types and weights
    WEAPON_SPAWN_WEIGHT: float = 0.6  # 60% chance for weapons
    ARMOR_SPAWN_WEIGHT: float = 0.4  # 40% chance for armor
    
    # Item seeking behavior
    ENABLE_ITEM_SEEKING: bool = True
    ITEM_SEEK_DISTANCE: int = 5  # Maximum distance to seek items
    ITEM_PRIORITY_OVER_PLAYER: bool = True  # Prioritize items over player pursuit
    
    # Scroll usage and failure rates
    SCROLL_FAILURE_RATE: float = 0.75  # 75% failure rate for monster scroll usage (orcs aren't smart!)
    POTION_FAILURE_RATE: float = 0.2  # 20% failure rate for monster potion usage


@dataclass
class ItemSpawnConfig:
    """Configuration for item spawn rates in normal gameplay."""
    
    # Healing potion spawn rates (level-dependent)
    HEALING_POTION_LEVEL_1: int = 50  # Higher rate on level 1 for balance (reduced from 55)
    HEALING_POTION_DEFAULT: int = 25  # Standard rate for other levels (reduced from 28)
    
    # NEW BUFF POTIONS - Utility and combat buffs
    SPEED_POTION_SPAWN: list = None  # [[15, 2]] - Common, early access
    REGENERATION_POTION_SPAWN: list = None  # [[12, 3]] - Healing over time
    INVISIBILITY_POTION_SPAWN: list = None  # [[10, 4]] - Longer than scroll
    LEVITATION_POTION_SPAWN: list = None  # [[10, 5]] - Hazard navigation
    PROTECTION_POTION_SPAWN: list = None  # [[12, 4]] - Defensive buff
    HEROISM_POTION_SPAWN: list = None  # [[8, 6]] - Powerful offensive buff
    
    # NEW DEBUFF POTIONS - Identification risk/reward
    WEAKNESS_POTION_SPAWN: list = None  # [[5, 3]] - Rare debuff
    SLOWNESS_POTION_SPAWN: list = None  # [[4, 4]] - Rare debuff
    BLINDNESS_POTION_SPAWN: list = None  # [[3, 5]] - Very rare debuff
    PARALYSIS_POTION_SPAWN: list = None  # [[2, 6]] - Extremely rare debuff
    
    # NEW SPECIAL POTIONS - Game-changing effects
    EXPERIENCE_POTION_SPAWN: list = None  # [[1, 8]] - Extremely rare, instant level-up
    
    # Equipment spawn rates (format: [[chance, min_level], ...])
    # Note: These are used by from_dungeon_level() function
    SWORD_SPAWN: list = None  # [[5, 4]] - 5% from level 4
    SHIELD_SPAWN: list = None  # [[15, 8]] - 15% from level 8
    
    # Scroll spawn rates (format: [[chance%, min_level], ...])
    LIGHTNING_SCROLL_SPAWN: list = None  # [[25, 4]]
    FIREBALL_SCROLL_SPAWN: list = None  # [[25, 6]]
    CONFUSION_SCROLL_SPAWN: list = None  # [[12, 2]] - increased from 10 for variety
    INVISIBILITY_SCROLL_SPAWN: list = None  # [[18, 3]] - increased from 15, starts level 3
    ENHANCE_WEAPON_SCROLL_SPAWN: list = None  # [[12, 5]] - increased from 10
    ENHANCE_ARMOR_SCROLL_SPAWN: list = None  # [[12, 6]] - increased from 10
    
    # Wand spawn rates (format: [[chance%, min_level], ...])
    # Wands are rare but powerful multi-use items
    WAND_OF_FIREBALL_SPAWN: list = None  # [[5, 7]] - rare, deep dungeon
    WAND_OF_LIGHTNING_SPAWN: list = None  # [[5, 5]] - rare, mid dungeon
    WAND_OF_CONFUSION_SPAWN: list = None  # [[8, 4]] - less rare
    WAND_OF_TELEPORTATION_SPAWN: list = None  # [[6, 6]] - rare utility
    WAND_OF_DRAGON_FARTS_SPAWN: list = None  # [[4, 8]] - very rare, powerful
    WAND_OF_YO_MAMA_SPAWN: list = None  # [[3, 9]] - extremely rare, chaotic
    WAND_OF_SLOW_SPAWN: list = None  # [[10, 5]] - tactical wand
    WAND_OF_GLUE_SPAWN: list = None  # [[8, 6]] - control wand
    WAND_OF_RAGE_SPAWN: list = None  # [[6, 7]] - chaos wand
    
    # Special/tactical scrolls
    YO_MAMA_SCROLL_SPAWN: list = None  # [[8, 7]] - rare tactical spell
    SLOW_SCROLL_SPAWN: list = None  # [[15, 4]] - common tactical spell
    GLUE_SCROLL_SPAWN: list = None  # [[12, 5]] - zoning/control spell
    RAGE_SCROLL_SPAWN: list = None  # [[10, 6]] - chaos spell
    
    # New scrolls (v3.11.0+)
    HASTE_SCROLL_SPAWN: list = None  # [[15, 3]] - buff scroll, common
    BLINK_SCROLL_SPAWN: list = None  # [[12, 4]] - tactical teleport
    LIGHT_SCROLL_SPAWN: list = None  # [[4, 6]] - rare discovery, "aha moment" vs vampires later
    MAGIC_MAPPING_SCROLL_SPAWN: list = None  # [[8, 5]] - powerful utility
    EARTHQUAKE_SCROLL_SPAWN: list = None  # [[10, 7]] - high-level offensive
    IDENTIFY_SCROLL_SPAWN: list = None  # [[18, 2]] - important utility
    
    # Ring spawn rates (format: [[chance%, min_level], ...])
    # Rings are rare, powerful items that provide passive bonuses
    # Common rings (Level 3-4)
    RING_OF_REGENERATION_SPAWN: list = None  # [[8, 3]] - useful survival ring
    RING_OF_CLARITY_SPAWN: list = None  # [[8, 3]] - anti-confusion
    RING_OF_SEARCHING_SPAWN: list = None  # [[7, 4]] - utility ring
    
    # Uncommon rings (Level 5-6)
    RING_OF_PROTECTION_SPAWN: list = None  # [[10, 5]] - popular defensive ring
    RING_OF_STRENGTH_SPAWN: list = None  # [[8, 5]] - combat stat boost
    RING_OF_DEXTERITY_SPAWN: list = None  # [[8, 5]] - combat stat boost
    RING_OF_SPEED_SPAWN: list = None  # [[6, 6]] - powerful utility
    
    # Rare rings (Level 7-8)
    RING_OF_CONSTITUTION_SPAWN: list = None  # [[8, 7]] - major HP boost
    RING_OF_MIGHT_SPAWN: list = None  # [[7, 7]] - damage boost
    RING_OF_FREE_ACTION_SPAWN: list = None  # [[6, 7]] - paralysis immunity
    RING_OF_RESISTANCE_SPAWN: list = None  # [[6, 8]] - all-around defense
    
    # Very rare rings (Level 9+)
    RING_OF_WIZARDRY_SPAWN: list = None  # [[5, 9]] - spell power boost
    RING_OF_TELEPORTATION_SPAWN: list = None  # [[4, 9]] - emergency escape
    RING_OF_INVISIBILITY_SPAWN: list = None  # [[4, 10]] - stealth power
    RING_OF_LUCK_SPAWN: list = None  # [[5, 9]] - crit chance + loot
    
    def __post_init__(self):
        """Initialize list values after dataclass creation."""
        if self.SWORD_SPAWN is None:
            self.SWORD_SPAWN = [[5, 4]]
        if self.SHIELD_SPAWN is None:
            self.SHIELD_SPAWN = [[15, 8]]
        if self.LIGHTNING_SCROLL_SPAWN is None:
            self.LIGHTNING_SCROLL_SPAWN = [[25, 4]]
        if self.FIREBALL_SCROLL_SPAWN is None:
            self.FIREBALL_SCROLL_SPAWN = [[25, 6]]
        if self.CONFUSION_SCROLL_SPAWN is None:
            self.CONFUSION_SCROLL_SPAWN = [[12, 2]]  # Increased for variety
        if self.INVISIBILITY_SCROLL_SPAWN is None:
            self.INVISIBILITY_SCROLL_SPAWN = [[18, 3]]  # Increased, starts earlier
        if self.ENHANCE_WEAPON_SCROLL_SPAWN is None:
            self.ENHANCE_WEAPON_SCROLL_SPAWN = [[12, 5]]  # Increased for variety
        if self.ENHANCE_ARMOR_SCROLL_SPAWN is None:
            self.ENHANCE_ARMOR_SCROLL_SPAWN = [[12, 6]]  # Increased for variety
        
        # Initialize wand spawn rates
        if self.WAND_OF_FIREBALL_SPAWN is None:
            self.WAND_OF_FIREBALL_SPAWN = [[5, 7]]
        if self.WAND_OF_LIGHTNING_SPAWN is None:
            self.WAND_OF_LIGHTNING_SPAWN = [[5, 5]]
        if self.WAND_OF_CONFUSION_SPAWN is None:
            self.WAND_OF_CONFUSION_SPAWN = [[8, 4]]
        if self.WAND_OF_TELEPORTATION_SPAWN is None:
            self.WAND_OF_TELEPORTATION_SPAWN = [[6, 6]]
        if self.WAND_OF_DRAGON_FARTS_SPAWN is None:
            self.WAND_OF_DRAGON_FARTS_SPAWN = [[4, 8]]
        if self.WAND_OF_YO_MAMA_SPAWN is None:
            self.WAND_OF_YO_MAMA_SPAWN = [[3, 9]]
        if self.WAND_OF_SLOW_SPAWN is None:
            self.WAND_OF_SLOW_SPAWN = [[10, 5]]
        if self.WAND_OF_GLUE_SPAWN is None:
            self.WAND_OF_GLUE_SPAWN = [[8, 6]]
        if self.WAND_OF_RAGE_SPAWN is None:
            self.WAND_OF_RAGE_SPAWN = [[6, 7]]
        if self.YO_MAMA_SCROLL_SPAWN is None:
            self.YO_MAMA_SCROLL_SPAWN = [[8, 7]]
        if self.SLOW_SCROLL_SPAWN is None:
            self.SLOW_SCROLL_SPAWN = [[15, 4]]
        if self.GLUE_SCROLL_SPAWN is None:
            self.GLUE_SCROLL_SPAWN = [[12, 5]]
        if self.RAGE_SCROLL_SPAWN is None:
            self.RAGE_SCROLL_SPAWN = [[10, 6]]
        
        # Initialize new scroll spawn rates (v3.11.0+)
        if self.HASTE_SCROLL_SPAWN is None:
            self.HASTE_SCROLL_SPAWN = [[15, 3]]
        if self.BLINK_SCROLL_SPAWN is None:
            self.BLINK_SCROLL_SPAWN = [[12, 4]]
        if self.LIGHT_SCROLL_SPAWN is None:
            self.LIGHT_SCROLL_SPAWN = [[4, 6]]  # Rare discovery, "aha moment" vs vampires
        if self.MAGIC_MAPPING_SCROLL_SPAWN is None:
            self.MAGIC_MAPPING_SCROLL_SPAWN = [[8, 5]]
        if self.EARTHQUAKE_SCROLL_SPAWN is None:
            self.EARTHQUAKE_SCROLL_SPAWN = [[10, 7]]
        if self.IDENTIFY_SCROLL_SPAWN is None:
            self.IDENTIFY_SCROLL_SPAWN = [[18, 2]]  # Important for item ID
        
        # Initialize new potion spawn rates
        if self.SPEED_POTION_SPAWN is None:
            self.SPEED_POTION_SPAWN = [[15, 2]]
        if self.REGENERATION_POTION_SPAWN is None:
            self.REGENERATION_POTION_SPAWN = [[12, 3]]
        if self.INVISIBILITY_POTION_SPAWN is None:
            self.INVISIBILITY_POTION_SPAWN = [[10, 4]]
        if self.LEVITATION_POTION_SPAWN is None:
            self.LEVITATION_POTION_SPAWN = [[10, 5]]
        if self.PROTECTION_POTION_SPAWN is None:
            self.PROTECTION_POTION_SPAWN = [[12, 4]]
        if self.HEROISM_POTION_SPAWN is None:
            self.HEROISM_POTION_SPAWN = [[8, 6]]
        if self.WEAKNESS_POTION_SPAWN is None:
            self.WEAKNESS_POTION_SPAWN = [[5, 3]]
        if self.SLOWNESS_POTION_SPAWN is None:
            self.SLOWNESS_POTION_SPAWN = [[4, 4]]
        if self.BLINDNESS_POTION_SPAWN is None:
            self.BLINDNESS_POTION_SPAWN = [[3, 5]]
        if self.PARALYSIS_POTION_SPAWN is None:
            self.PARALYSIS_POTION_SPAWN = [[2, 6]]
        if self.EXPERIENCE_POTION_SPAWN is None:
            self.EXPERIENCE_POTION_SPAWN = [[1, 8]]
        
        # Initialize ring spawn rates
        if self.RING_OF_REGENERATION_SPAWN is None:
            self.RING_OF_REGENERATION_SPAWN = [[8, 3]]
        if self.RING_OF_CLARITY_SPAWN is None:
            self.RING_OF_CLARITY_SPAWN = [[8, 3]]
        if self.RING_OF_SEARCHING_SPAWN is None:
            self.RING_OF_SEARCHING_SPAWN = [[7, 4]]
        if self.RING_OF_PROTECTION_SPAWN is None:
            self.RING_OF_PROTECTION_SPAWN = [[10, 5]]
        if self.RING_OF_STRENGTH_SPAWN is None:
            self.RING_OF_STRENGTH_SPAWN = [[8, 5]]
        if self.RING_OF_DEXTERITY_SPAWN is None:
            self.RING_OF_DEXTERITY_SPAWN = [[8, 5]]
        if self.RING_OF_SPEED_SPAWN is None:
            self.RING_OF_SPEED_SPAWN = [[6, 6]]
        if self.RING_OF_CONSTITUTION_SPAWN is None:
            self.RING_OF_CONSTITUTION_SPAWN = [[8, 7]]
        if self.RING_OF_MIGHT_SPAWN is None:
            self.RING_OF_MIGHT_SPAWN = [[7, 7]]
        if self.RING_OF_FREE_ACTION_SPAWN is None:
            self.RING_OF_FREE_ACTION_SPAWN = [[6, 7]]
        if self.RING_OF_RESISTANCE_SPAWN is None:
            self.RING_OF_RESISTANCE_SPAWN = [[6, 8]]
        if self.RING_OF_WIZARDRY_SPAWN is None:
            self.RING_OF_WIZARDRY_SPAWN = [[5, 9]]
        if self.RING_OF_TELEPORTATION_SPAWN is None:
            self.RING_OF_TELEPORTATION_SPAWN = [[4, 9]]
        if self.RING_OF_INVISIBILITY_SPAWN is None:
            self.RING_OF_INVISIBILITY_SPAWN = [[4, 10]]
        if self.RING_OF_LUCK_SPAWN is None:
            self.RING_OF_LUCK_SPAWN = [[5, 9]]
    
    def get_item_spawn_chances(self, dungeon_level: int) -> dict:
        """Get item spawn chances for normal gameplay.
        
        Args:
            dungeon_level: Current dungeon level
            
        Returns:
            Dictionary of item names to spawn chance configurations
        """
        # Level 1 gets increased healing potion chance for balance
        healing_potion_chance = self.HEALING_POTION_LEVEL_1 if dungeon_level == 1 else self.HEALING_POTION_DEFAULT
        
        return {
            "healing_potion": healing_potion_chance,
            # NEW POTIONS - Buff potions
            "speed_potion": self.SPEED_POTION_SPAWN,
            "regeneration_potion": self.REGENERATION_POTION_SPAWN,
            "invisibility_potion": self.INVISIBILITY_POTION_SPAWN,
            "levitation_potion": self.LEVITATION_POTION_SPAWN,
            "protection_potion": self.PROTECTION_POTION_SPAWN,
            "heroism_potion": self.HEROISM_POTION_SPAWN,
            # NEW POTIONS - Debuff potions (identification risk)
            "weakness_potion": self.WEAKNESS_POTION_SPAWN,
            "slowness_potion": self.SLOWNESS_POTION_SPAWN,
            "blindness_potion": self.BLINDNESS_POTION_SPAWN,
            "paralysis_potion": self.PARALYSIS_POTION_SPAWN,
            # NEW POTIONS - Special
            "experience_potion": self.EXPERIENCE_POTION_SPAWN,
            # Equipment
            "sword": self.SWORD_SPAWN,
            "shield": self.SHIELD_SPAWN,
            # Scrolls
            "lightning_scroll": self.LIGHTNING_SCROLL_SPAWN,
            "fireball_scroll": self.FIREBALL_SCROLL_SPAWN,
            "confusion_scroll": self.CONFUSION_SCROLL_SPAWN,
            "invisibility_scroll": self.INVISIBILITY_SCROLL_SPAWN,
            "enhance_weapon_scroll": self.ENHANCE_WEAPON_SCROLL_SPAWN,
            "enhance_armor_scroll": self.ENHANCE_ARMOR_SCROLL_SPAWN,
            # Wands
            "wand_of_fireball": self.WAND_OF_FIREBALL_SPAWN,
            "wand_of_lightning": self.WAND_OF_LIGHTNING_SPAWN,
            "wand_of_confusion": self.WAND_OF_CONFUSION_SPAWN,
            "wand_of_teleportation": self.WAND_OF_TELEPORTATION_SPAWN,
            "wand_of_dragon_farts": self.WAND_OF_DRAGON_FARTS_SPAWN,
            "wand_of_yo_mama": self.WAND_OF_YO_MAMA_SPAWN,
            "wand_of_slow": self.WAND_OF_SLOW_SPAWN,
            "wand_of_glue": self.WAND_OF_GLUE_SPAWN,
            "wand_of_rage": self.WAND_OF_RAGE_SPAWN,
            # Tactical scrolls
            "yo_mama_scroll": self.YO_MAMA_SCROLL_SPAWN,
            "slow_scroll": self.SLOW_SCROLL_SPAWN,
            "glue_scroll": self.GLUE_SCROLL_SPAWN,
            "rage_scroll": self.RAGE_SCROLL_SPAWN,
            # New scrolls (v3.11.0+)
            "haste_scroll": self.HASTE_SCROLL_SPAWN,
            "blink_scroll": self.BLINK_SCROLL_SPAWN,
            "light_scroll": self.LIGHT_SCROLL_SPAWN,
            "magic_mapping_scroll": self.MAGIC_MAPPING_SCROLL_SPAWN,
            "earthquake_scroll": self.EARTHQUAKE_SCROLL_SPAWN,
            "identify_scroll": self.IDENTIFY_SCROLL_SPAWN,
            # Rings (v3.12.0+)
            "ring_of_protection": self.RING_OF_PROTECTION_SPAWN,
            "ring_of_regeneration": self.RING_OF_REGENERATION_SPAWN,
            "ring_of_resistance": self.RING_OF_RESISTANCE_SPAWN,
            "ring_of_strength": self.RING_OF_STRENGTH_SPAWN,
            "ring_of_dexterity": self.RING_OF_DEXTERITY_SPAWN,
            "ring_of_might": self.RING_OF_MIGHT_SPAWN,
            "ring_of_teleportation": self.RING_OF_TELEPORTATION_SPAWN,
            "ring_of_invisibility": self.RING_OF_INVISIBILITY_SPAWN,
            "ring_of_searching": self.RING_OF_SEARCHING_SPAWN,
            "ring_of_free_action": self.RING_OF_FREE_ACTION_SPAWN,
            "ring_of_wizardry": self.RING_OF_WIZARDRY_SPAWN,
            "ring_of_clarity": self.RING_OF_CLARITY_SPAWN,
            "ring_of_speed": self.RING_OF_SPEED_SPAWN,
            "ring_of_constitution": self.RING_OF_CONSTITUTION_SPAWN,
            "ring_of_luck": self.RING_OF_LUCK_SPAWN,
        }


@dataclass
class GameplayConfig:
    """Configuration for core gameplay mechanics."""
    
    # Map generation (Phase 3: Larger maps for exploration!)
    DEFAULT_MAP_WIDTH: int = 120   # Was 80 - 50% larger
    DEFAULT_MAP_HEIGHT: int = 80   # Was 43 - ~86% larger
    
    # Room generation
    MIN_ROOM_SIZE: int = 6
    MAX_ROOM_SIZE: int = 10
    MAX_ROOMS_PER_FLOOR: int = 30
    
    # Entity spawning
    MAX_MONSTERS_PER_ROOM: int = 3
    MAX_ITEMS_PER_ROOM: int = 2


@dataclass
class IdentificationConfig:
    """Configuration for the item identification system.
    
    This system allows for dual-toggle control:
    1. Master toggle: Can completely disable identification mechanic
    2. Difficulty integration: When enabled, difficulty affects pre-identification percentages
    """
    enabled: bool = True  # Master toggle - if False, all items always identified


@dataclass
class DifficultyItemIdentification:
    """Item identification percentages for a specific difficulty level."""
    scrolls_pre_identified_percent: int = 40
    potions_pre_identified_percent: int = 50
    rings_pre_identified_percent: int = 40
    wands_pre_identified_percent: int = 30


@dataclass
class DifficultyConfig:
    """Configuration for difficulty-based game settings.
    
    Currently focuses on item identification, but can be expanded for other
    difficulty-related settings (monster health, damage, spawn rates, etc.)
    """
    easy: DifficultyItemIdentification = None
    medium: DifficultyItemIdentification = None
    hard: DifficultyItemIdentification = None
    
    def __post_init__(self):
        """Initialize difficulty levels with default values."""
        if self.easy is None:
            self.easy = DifficultyItemIdentification(
                scrolls_pre_identified_percent=80,
                potions_pre_identified_percent=80,
                rings_pre_identified_percent=90,
                wands_pre_identified_percent=75
            )
        if self.medium is None:
            self.medium = DifficultyItemIdentification(
                scrolls_pre_identified_percent=40,
                potions_pre_identified_percent=50,
                rings_pre_identified_percent=40,
                wands_pre_identified_percent=30
            )
        if self.hard is None:
            self.hard = DifficultyItemIdentification(
                scrolls_pre_identified_percent=5,
                potions_pre_identified_percent=5,
                rings_pre_identified_percent=0,
                wands_pre_identified_percent=0
            )
    
    def get_difficulty(self, difficulty_name: str) -> DifficultyItemIdentification:
        """Get difficulty settings by name.
        
        Args:
            difficulty_name: One of "easy", "medium", "hard"
            
        Returns:
            DifficultyItemIdentification for the specified difficulty
            
        Raises:
            ValueError: If difficulty_name is not recognized
        """
        difficulty_map = {
            "easy": self.easy,
            "medium": self.medium,
            "hard": self.hard
        }
        
        if difficulty_name.lower() not in difficulty_map:
            raise ValueError(f"Unknown difficulty: {difficulty_name}. Valid options: easy, medium, hard")
        
        return difficulty_map[difficulty_name.lower()]


@dataclass
class MetaProgressionConfig:
    """Configuration for meta-progression features that persist across runs."""
    auto_identify_after_first_win: bool = True  # Auto-ID common items after first win
    common_items_learned: bool = True  # Basic items stay identified


@dataclass
class GameConstants:
    """Main configuration container for all game constants."""
    
    pathfinding: PathfindingConfig = None
    performance: PerformanceConfig = None
    combat: CombatConfig = None
    inventory: InventoryConfig = None
    rendering: RenderingConfig = None
    gameplay: GameplayConfig = None
    entities: EntityConfig = None
    monster_equipment: MonsterEquipmentConfig = None
    item_spawns: ItemSpawnConfig = None
    identification_system: IdentificationConfig = None
    difficulty: DifficultyConfig = None
    meta_progression: MetaProgressionConfig = None
    
    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.pathfinding is None:
            self.pathfinding = PathfindingConfig()
        if self.performance is None:
            self.performance = PerformanceConfig()
        if self.combat is None:
            self.combat = CombatConfig()
        if self.inventory is None:
            self.inventory = InventoryConfig()
        if self.rendering is None:
            self.rendering = RenderingConfig()
        if self.gameplay is None:
            self.gameplay = GameplayConfig()
        if self.entities is None:
            self.entities = EntityConfig()
        if self.monster_equipment is None:
            self.monster_equipment = MonsterEquipmentConfig()
        if self.item_spawns is None:
            self.item_spawns = ItemSpawnConfig()
        if self.identification_system is None:
            self.identification_system = IdentificationConfig()
        if self.difficulty is None:
            self.difficulty = DifficultyConfig()
        if self.meta_progression is None:
            self.meta_progression = MetaProgressionConfig()
    
    @classmethod
    def load_from_file(cls, config_path: str = None) -> 'GameConstants':
        """Load configuration from a file.
        
        Supports JSON and YAML formats. File format is determined by extension.
        
        Args:
            config_path: Path to configuration file. If None, uses default values.
            
        Returns:
            GameConstants instance with loaded or default values.
            
        Raises:
            FileNotFoundError: If config_path is provided but file doesn't exist
            ValueError: If file format is unsupported or invalid
        """
        if not config_path:
            return cls()
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_ext = os.path.splitext(config_path)[1].lower()
                
                if file_ext == '.json':
                    config_data = json.load(f)
                elif file_ext in ('.yaml', '.yml'):
                    if not YAML_AVAILABLE:
                        raise ValueError("YAML support not available. Install PyYAML: pip install PyYAML")
                    config_data = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported configuration file format: {file_ext}. "
                                   "Supported formats: .json, .yaml, .yml")
            
            return cls._from_dict(config_data)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid configuration file format: {e}")
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            raise
    
    @classmethod
    def _from_dict(cls, config_data: Dict[str, Any]) -> 'GameConstants':
        """Create GameConstants from dictionary data.
        
        Args:
            config_data: Dictionary containing configuration values
            
        Returns:
            GameConstants instance with values from dictionary
        """
        instance = cls()
        
        # Update pathfinding config
        if 'pathfinding' in config_data:
            pathfinding_data = config_data['pathfinding']
            if isinstance(pathfinding_data, dict):
                for key, value in pathfinding_data.items():
                    if hasattr(instance.pathfinding, key):
                        # Skip read-only properties (e.g., MAX_PATH_LENGTH)
                        attr = getattr(type(instance.pathfinding), key, None)
                        if not isinstance(attr, property):
                            setattr(instance.pathfinding, key, value)
        
        # Update performance config
        if 'performance' in config_data:
            performance_data = config_data['performance']
            if isinstance(performance_data, dict):
                for key, value in performance_data.items():
                    if hasattr(instance.performance, key):
                        # Skip read-only properties
                        attr = getattr(type(instance.performance), key, None)
                        if not isinstance(attr, property):
                            setattr(instance.performance, key, value)
        
        # Update combat config
        if 'combat' in config_data:
            combat_data = config_data['combat']
            if isinstance(combat_data, dict):
                for key, value in combat_data.items():
                    if hasattr(instance.combat, key):
                        setattr(instance.combat, key, value)
        
        # Update inventory config
        if 'inventory' in config_data:
            inventory_data = config_data['inventory']
            if isinstance(inventory_data, dict):
                for key, value in inventory_data.items():
                    if hasattr(instance.inventory, key):
                        setattr(instance.inventory, key, value)
        
        # Update rendering config
        if 'rendering' in config_data:
            rendering_data = config_data['rendering']
            if isinstance(rendering_data, dict):
                for key, value in rendering_data.items():
                    if hasattr(instance.rendering, key):
                        setattr(instance.rendering, key, value)
        
        # Update gameplay config
        if 'gameplay' in config_data:
            gameplay_data = config_data['gameplay']
            if isinstance(gameplay_data, dict):
                for key, value in gameplay_data.items():
                    if hasattr(instance.gameplay, key):
                        setattr(instance.gameplay, key, value)
        
        # Update entities config
        if 'entities' in config_data:
            entities_data = config_data['entities']
            if isinstance(entities_data, dict):
                for key, value in entities_data.items():
                    if hasattr(instance.entities, key):
                        setattr(instance.entities, key, value)
        
        # Update monster equipment config
        if 'monster_equipment' in config_data:
            monster_equipment_data = config_data['monster_equipment']
            if isinstance(monster_equipment_data, dict):
                for key, value in monster_equipment_data.items():
                    if hasattr(instance.monster_equipment, key):
                        setattr(instance.monster_equipment, key, value)
        
        # Update identification system config
        if 'identification_system' in config_data:
            id_data = config_data['identification_system']
            if isinstance(id_data, dict):
                for key, value in id_data.items():
                    if hasattr(instance.identification_system, key):
                        setattr(instance.identification_system, key, value)
        
        # Update difficulty config
        if 'difficulty' in config_data:
            difficulty_data = config_data['difficulty']
            if isinstance(difficulty_data, dict):
                # Load each difficulty level
                for difficulty_level in ['easy', 'medium', 'hard']:
                    if difficulty_level in difficulty_data:
                        level_data = difficulty_data[difficulty_level]
                        if isinstance(level_data, dict):
                            difficulty_obj = getattr(instance.difficulty, difficulty_level)
                            for key, value in level_data.items():
                                if hasattr(difficulty_obj, key):
                                    setattr(difficulty_obj, key, value)
        
        # Update meta progression config
        if 'meta_progression' in config_data:
            meta_data = config_data['meta_progression']
            if isinstance(meta_data, dict):
                for key, value in meta_data.items():
                    if hasattr(instance.meta_progression, key):
                        setattr(instance.meta_progression, key, value)
        
        logger.info(f"Loaded configuration with {len(config_data)} sections")
        return instance
    
    def save_to_file(self, config_path: str, format: str = 'json') -> None:
        """Save configuration to a file.
        
        Args:
            config_path: Path where to save the configuration file
            format: File format ('json' or 'yaml')
            
        Raises:
            ValueError: If format is unsupported
            IOError: If file cannot be written
        """
        config_data = self.to_dict()
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                if format.lower() == 'json':
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                elif format.lower() in ('yaml', 'yml'):
                    if not YAML_AVAILABLE:
                        raise ValueError("YAML support not available. Install PyYAML: pip install PyYAML")
                    yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
                else:
                    raise ValueError(f"Unsupported format: {format}. Supported: 'json', 'yaml'")
            
            logger.info(f"Configuration saved to {config_path} in {format} format")
            
        except Exception as e:
            logger.error(f"Error saving configuration to {config_path}: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of the configuration
        """
        return {
            'pathfinding': asdict(self.pathfinding),
            'performance': asdict(self.performance),
            'combat': asdict(self.combat),
            'inventory': asdict(self.inventory),
            'rendering': asdict(self.rendering),
            'gameplay': asdict(self.gameplay),
        }
    
    def to_legacy_constants(self) -> Dict[str, Any]:
        """Convert to the legacy constants dictionary format.
        
        This maintains compatibility with existing code that expects
        the old constants dictionary format.
        
        Returns:
            Dictionary in the legacy format expected by existing code.
        """
        return {
            # Screen and rendering
            'screen_width': self.rendering.DEFAULT_SCREEN_WIDTH,
            'screen_height': self.rendering.DEFAULT_SCREEN_HEIGHT,
            'panel_height': self.rendering.DEFAULT_PANEL_HEIGHT,
            'panel_y': self.rendering.DEFAULT_SCREEN_HEIGHT - self.rendering.DEFAULT_PANEL_HEIGHT,
            'bar_width': self.rendering.DEFAULT_BAR_WIDTH,
            'window_title': 'Yarl (Catacombs of Yarl)',
            
            # FOV settings
            'fov_radius': self.rendering.DEFAULT_FOV_RADIUS,
            'fov_light_walls': self.rendering.DEFAULT_FOV_LIGHT_WALLS,
            'fov_algorithm': self.rendering.DEFAULT_FOV_ALGORITHM,
            
            # Map settings
            'map_width': self.gameplay.DEFAULT_MAP_WIDTH,
            'map_height': self.gameplay.DEFAULT_MAP_HEIGHT,
            
            # Room generation
            'room_max_size': self.gameplay.MAX_ROOM_SIZE,
            'room_min_size': self.gameplay.MIN_ROOM_SIZE,
            'max_rooms': self.gameplay.MAX_ROOMS_PER_FLOOR,
            
            # Entity limits
            'max_monsters_per_room': self.gameplay.MAX_MONSTERS_PER_ROOM,
            'max_items_per_room': self.gameplay.MAX_ITEMS_PER_ROOM,
            
            # Colors (keeping existing color definitions)
            'colors': {
                'dark_wall': (0, 0, 100),
                'dark_ground': (50, 50, 150),
                'light_wall': (130, 110, 50),
                'light_ground': (200, 180, 50),
                'desaturated_green': (63, 127, 63),
                'darker_green': (0, 127, 0),
                'dark_red': (191, 0, 0),
                'white': (255, 255, 255),
                'black': (0, 0, 0),
                'red': (255, 0, 0),
                'orange': (255, 127, 0),
                'light_red': (255, 114, 114),
                'darker_red': (127, 0, 0),
                'violet': (127, 0, 255),
                'yellow': (255, 255, 0),
                'blue': (0, 0, 255),
                'green': (0, 255, 0),
                'light_cyan': (114, 255, 255),
                'light_pink': (255, 114, 184),
            }
        }


# Global instance for easy access
# Try to load from YAML file first, fall back to defaults if not found
_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'game_constants.yaml')
if os.path.exists(_CONFIG_PATH):
    try:
        GAME_CONSTANTS = GameConstants.load_from_file(_CONFIG_PATH)
        logger.info(f"Loaded game constants from {_CONFIG_PATH}")
    except Exception as e:
        logger.warning(f"Failed to load game constants from {_CONFIG_PATH}: {e}. Using defaults.")
        GAME_CONSTANTS = GameConstants()
else:
    GAME_CONSTANTS = GameConstants()
    logger.debug("No game_constants.yaml found, using default values")

# Convenience functions for common access patterns
def get_constants() -> Dict[str, Any]:
    """Get constants in legacy dictionary format.
    
    This function maintains compatibility with existing code.
    
    Returns:
        Dictionary of game constants in legacy format.
    """
    return GAME_CONSTANTS.to_legacy_constants()


def get_pathfinding_config() -> PathfindingConfig:
    """Get pathfinding configuration.
    
    Returns:
        PathfindingConfig: Configuration object containing pathfinding-related constants
            including A* parameters, movement costs, and path length limits.
    """
    return GAME_CONSTANTS.pathfinding


def get_performance_config() -> PerformanceConfig:
    """Get performance configuration.
    
    Returns:
        PerformanceConfig: Configuration object containing performance-related constants
            including spatial indexing, FOV caching, and rendering optimization settings.
    """
    return GAME_CONSTANTS.performance


def get_combat_config() -> CombatConfig:
    """Get combat configuration.
    
    Returns:
        CombatConfig: Configuration object containing combat-related constants
            including default stats, damage calculations, and level progression.
    """
    return GAME_CONSTANTS.combat


def get_inventory_config() -> InventoryConfig:
    """Get inventory configuration.
    
    Returns:
        InventoryConfig: Configuration object containing inventory-related constants
            including default capacity and item name length limits.
    """
    return GAME_CONSTANTS.inventory


def get_rendering_config() -> RenderingConfig:
    """Get rendering configuration.
    
    Returns:
        RenderingConfig: Configuration object containing rendering-related constants
            including screen dimensions, FOV settings, and display parameters.
    """
    return GAME_CONSTANTS.rendering


def get_gameplay_config() -> GameplayConfig:
    """Get gameplay configuration.
    
    Returns:
        GameplayConfig: Configuration object containing gameplay-related constants
            including map generation and entity spawning parameters.
    """
    return GAME_CONSTANTS.gameplay


def get_entity_config() -> EntityConfig:
    """Get entity configuration.
    
    Returns:
        EntityConfig: Configuration object containing entity system settings
            including file paths, validation options, and inheritance settings.
    """
    return GAME_CONSTANTS.entities


def get_monster_equipment_config() -> MonsterEquipmentConfig:
    """Get monster equipment configuration.
    
    Returns:
        MonsterEquipmentConfig: Configuration object containing monster equipment settings
            including spawn rates, item seeking behavior, and failure rates.
    """
    return GAME_CONSTANTS.monster_equipment


def get_item_spawn_config() -> ItemSpawnConfig:
    """Get item spawn configuration.
    
    Returns:
        ItemSpawnConfig: Configuration object containing item spawn rates
            for normal gameplay mode.
    """
    return GAME_CONSTANTS.item_spawns
