"""Loot tags and metadata system for item categorization.

This module provides structured metadata for loot items that can be queried
from code and the loot sanity harness. It parallels the ETP system for
encounter budgeting.

Loot Categories:
    - healing: HP restoration items (potions)
    - panic: Emergency escape/survival items (teleport, haste, invisibility)
    - offensive: Direct damage items (fireball, lightning)
    - defensive: Protection/buff items (shield, protection)
    - utility: Tactical/situational items (confusion, slow, glue)
    - upgrade_weapon: Weapon enhancements or better weapons
    - upgrade_armor: Armor enhancements or better armor
    - rare: Valuable items like rings
    - key: Key items for locked areas

Band System (aligned with ETP):
    B1: Depths 1-5 (Early Game)
    B2: Depths 6-10 (Early-Mid Game)
    B3: Depths 11-15 (Mid Game)
    B4: Depths 16-20 (Mid-Late Game)
    B5: Depths 21-25 (Late Game)
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LootTags:
    """Metadata for a loot item.
    
    Attributes:
        categories: List of category tags (e.g., ["healing"], ["panic", "utility"])
        band_min: Minimum band (1-5) where this item starts appearing (default 1)
        band_max: Maximum band (1-5) where this item appears (default 5)
        weight: Base loot weight for sanity harness calculations (default 1.0)
    """
    categories: List[str] = field(default_factory=list)
    band_min: int = 1
    band_max: int = 5
    weight: float = 1.0
    
    def has_category(self, category: str) -> bool:
        """Check if this item has a specific category tag.
        
        Args:
            category: Category to check for
            
        Returns:
            True if the category is present
        """
        return category in self.categories
    
    def is_available_in_band(self, band: int) -> bool:
        """Check if this item is available in a given band.
        
        Args:
            band: Band number (1-5)
            
        Returns:
            True if item can appear in this band
        """
        return self.band_min <= band <= self.band_max


# ═══════════════════════════════════════════════════════════════════════════════
# LOOT TAGS REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════
# Global registry mapping item IDs to their LootTags.
# Item IDs match those in config/entities.yaml (e.g., "healing_potion", "sword")

LOOT_TAGS: Dict[str, LootTags] = {
    # ─────────────────────────────────────────────────────────────────────────
    # HEALING ITEMS
    # ─────────────────────────────────────────────────────────────────────────
    "healing_potion": LootTags(
        categories=["healing"],
        band_min=1, band_max=5,
        weight=10.0  # Common, essential
    ),
    "regeneration_potion": LootTags(
        categories=["healing", "defensive"],
        band_min=2, band_max=5,
        weight=3.0
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # PANIC / ESCAPE ITEMS
    # ─────────────────────────────────────────────────────────────────────────
    "teleport_scroll": LootTags(
        categories=["panic"],
        band_min=1, band_max=5,
        weight=5.0
    ),
    "haste_scroll": LootTags(
        categories=["panic"],
        band_min=1, band_max=5,
        weight=4.0
    ),
    "blink_scroll": LootTags(
        categories=["panic", "utility"],
        band_min=1, band_max=5,
        weight=4.0
    ),
    "invisibility_scroll": LootTags(
        categories=["panic", "defensive"],
        band_min=2, band_max=5,
        weight=3.0
    ),
    "invisibility_potion": LootTags(
        categories=["panic", "defensive"],
        band_min=2, band_max=5,
        weight=2.5
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # OFFENSIVE / NUKE ITEMS
    # ─────────────────────────────────────────────────────────────────────────
    "fireball_scroll": LootTags(
        categories=["offensive"],
        band_min=2, band_max=5,
        weight=5.0
    ),
    "lightning_scroll": LootTags(
        categories=["offensive"],
        band_min=1, band_max=5,
        weight=5.0
    ),
    "earthquake_scroll": LootTags(
        categories=["offensive"],
        band_min=3, band_max=5,
        weight=2.0
    ),
    "wand_of_fireball": LootTags(
        categories=["offensive"],
        band_min=2, band_max=5,
        weight=2.0  # Rarer than scrolls
    ),
    "wand_of_lightning": LootTags(
        categories=["offensive"],
        band_min=2, band_max=5,
        weight=2.0
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # DEFENSIVE / BUFF ITEMS
    # ─────────────────────────────────────────────────────────────────────────
    "protection_potion": LootTags(
        categories=["defensive"],
        band_min=1, band_max=5,
        weight=4.0
    ),
    "shield_scroll": LootTags(
        categories=["defensive"],
        band_min=1, band_max=5,
        weight=4.0
    ),
    "heroism_potion": LootTags(
        categories=["defensive", "offensive"],
        band_min=2, band_max=5,
        weight=2.5
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # UTILITY / TRICK ITEMS
    # ─────────────────────────────────────────────────────────────────────────
    "confusion_scroll": LootTags(
        categories=["utility"],
        band_min=1, band_max=5,
        weight=5.0
    ),
    "yo_mama_scroll": LootTags(
        categories=["utility"],
        band_min=1, band_max=5,
        weight=3.0
    ),
    "raise_dead_scroll": LootTags(
        categories=["utility"],
        band_min=2, band_max=5,
        weight=2.0
    ),
    "glue_scroll": LootTags(
        categories=["utility"],
        band_min=1, band_max=5,
        weight=4.0
    ),
    "slow_scroll": LootTags(
        categories=["utility"],
        band_min=1, band_max=5,
        weight=4.0
    ),
    "dragon_fart_scroll": LootTags(
        categories=["utility", "offensive"],
        band_min=2, band_max=5,
        weight=2.5
    ),
    "rage_scroll": LootTags(
        categories=["utility"],
        band_min=2, band_max=5,
        weight=3.0
    ),
    "fear_scroll": LootTags(
        categories=["utility", "panic"],
        band_min=2, band_max=5,
        weight=3.0
    ),
    "identify_scroll": LootTags(
        categories=["utility"],
        band_min=1, band_max=5,
        weight=4.0
    ),
    "light_scroll": LootTags(
        categories=["utility"],
        band_min=1, band_max=5,
        weight=3.0
    ),
    "magic_mapping_scroll": LootTags(
        categories=["utility"],
        band_min=1, band_max=5,
        weight=2.5
    ),
    "detect_monster_scroll": LootTags(
        categories=["utility"],
        band_min=1, band_max=5,
        weight=3.0
    ),
    
    # Utility wands
    "wand_of_confusion": LootTags(
        categories=["utility"],
        band_min=2, band_max=5,
        weight=1.5
    ),
    "wand_of_teleportation": LootTags(
        categories=["panic", "utility"],
        band_min=2, band_max=5,
        weight=1.5
    ),
    "wand_of_dragon_farts": LootTags(
        categories=["utility", "offensive"],
        band_min=3, band_max=5,
        weight=1.0
    ),
    "wand_of_yo_mama": LootTags(
        categories=["utility"],
        band_min=2, band_max=5,
        weight=1.0
    ),
    "wand_of_slow": LootTags(
        categories=["utility"],
        band_min=2, band_max=5,
        weight=1.5
    ),
    "wand_of_glue": LootTags(
        categories=["utility"],
        band_min=2, band_max=5,
        weight=1.5
    ),
    "wand_of_rage": LootTags(
        categories=["utility"],
        band_min=2, band_max=5,
        weight=1.0
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # WEAPON UPGRADES
    # ─────────────────────────────────────────────────────────────────────────
    "enhance_weapon_scroll": LootTags(
        categories=["upgrade_weapon"],
        band_min=1, band_max=5,
        weight=3.0
    ),
    "dagger": LootTags(
        categories=["upgrade_weapon"],
        band_min=1, band_max=2,
        weight=5.0
    ),
    "club": LootTags(
        categories=["upgrade_weapon"],
        band_min=1, band_max=2,
        weight=5.0
    ),
    "shortsword": LootTags(
        categories=["upgrade_weapon"],
        band_min=1, band_max=3,
        weight=4.0
    ),
    "mace": LootTags(
        categories=["upgrade_weapon"],
        band_min=1, band_max=3,
        weight=4.0
    ),
    "longsword": LootTags(
        categories=["upgrade_weapon"],
        band_min=2, band_max=4,
        weight=3.0
    ),
    "rapier": LootTags(
        categories=["upgrade_weapon"],
        band_min=2, band_max=4,
        weight=2.5
    ),
    "spear": LootTags(
        categories=["upgrade_weapon"],
        band_min=2, band_max=4,
        weight=3.0
    ),
    "battleaxe": LootTags(
        categories=["upgrade_weapon"],
        band_min=3, band_max=5,
        weight=2.0
    ),
    "warhammer": LootTags(
        categories=["upgrade_weapon"],
        band_min=3, band_max=5,
        weight=2.0
    ),
    "greataxe": LootTags(
        categories=["upgrade_weapon"],
        band_min=4, band_max=5,
        weight=1.0
    ),
    "greatsword": LootTags(
        categories=["upgrade_weapon"],
        band_min=4, band_max=5,
        weight=1.0
    ),
    "sword": LootTags(
        categories=["upgrade_weapon"],
        band_min=2, band_max=4,
        weight=3.0
    ),
    "shortbow": LootTags(
        categories=["upgrade_weapon"],
        band_min=1, band_max=3,
        weight=2.5
    ),
    "longbow": LootTags(
        categories=["upgrade_weapon"],
        band_min=3, band_max=5,
        weight=1.5
    ),
    "crossbow": LootTags(
        categories=["upgrade_weapon"],
        band_min=2, band_max=4,
        weight=2.0
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # ARMOR UPGRADES
    # ─────────────────────────────────────────────────────────────────────────
    "enhance_armor_scroll": LootTags(
        categories=["upgrade_armor"],
        band_min=1, band_max=5,
        weight=3.0
    ),
    "shield": LootTags(
        categories=["upgrade_armor", "defensive"],
        band_min=1, band_max=5,
        weight=4.0
    ),
    "leather_armor": LootTags(
        categories=["upgrade_armor"],
        band_min=1, band_max=2,
        weight=5.0
    ),
    "leather_helmet": LootTags(
        categories=["upgrade_armor"],
        band_min=1, band_max=2,
        weight=4.0
    ),
    "leather_boots": LootTags(
        categories=["upgrade_armor"],
        band_min=1, band_max=2,
        weight=4.0
    ),
    "studded_leather_armor": LootTags(
        categories=["upgrade_armor"],
        band_min=2, band_max=3,
        weight=3.0
    ),
    "chain_mail": LootTags(
        categories=["upgrade_armor"],
        band_min=2, band_max=4,
        weight=2.5
    ),
    "chain_coif": LootTags(
        categories=["upgrade_armor"],
        band_min=2, band_max=4,
        weight=2.5
    ),
    "chain_boots": LootTags(
        categories=["upgrade_armor"],
        band_min=2, band_max=4,
        weight=2.5
    ),
    "scale_mail": LootTags(
        categories=["upgrade_armor"],
        band_min=3, band_max=5,
        weight=2.0
    ),
    "plate_mail": LootTags(
        categories=["upgrade_armor"],
        band_min=4, band_max=5,
        weight=1.0
    ),
    "plate_helmet": LootTags(
        categories=["upgrade_armor"],
        band_min=4, band_max=5,
        weight=1.0
    ),
    "plate_boots": LootTags(
        categories=["upgrade_armor"],
        band_min=4, band_max=5,
        weight=1.0
    ),
    "full_plate": LootTags(
        categories=["upgrade_armor"],
        band_min=5, band_max=5,
        weight=0.5
    ),
    "dragon_scale_mail": LootTags(
        categories=["upgrade_armor", "rare"],
        band_min=4, band_max=5,
        weight=0.5
    ),
    "frost_mail": LootTags(
        categories=["upgrade_armor", "rare"],
        band_min=4, band_max=5,
        weight=0.5
    ),
    "shield_of_resistance": LootTags(
        categories=["upgrade_armor", "rare", "defensive"],
        band_min=3, band_max=5,
        weight=0.5
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # RINGS (RARE)
    # ─────────────────────────────────────────────────────────────────────────
    # BALANCE: All rings start at B2+ minimum, exotic rings start at B3-B4.
    # Weights reduced to ensure rings are uncommon finds.
    # The RARE_BAND_MULTIPLIER further reduces these in early bands.
    
    # Common rings - start at B2 (depth 6+)
    "ring_of_protection": LootTags(
        categories=["rare", "defensive"],
        band_min=2, band_max=5,
        weight=0.6  # Reduced from 1.0
    ),
    "ring_of_regeneration": LootTags(
        categories=["rare", "healing"],
        band_min=2, band_max=5,
        weight=0.6  # Reduced from 1.0
    ),
    "ring_of_strength": LootTags(
        categories=["rare", "offensive"],
        band_min=2, band_max=5,
        weight=0.6  # Reduced from 1.0
    ),
    "ring_of_dexterity": LootTags(
        categories=["rare", "offensive"],
        band_min=2, band_max=5,
        weight=0.6  # Reduced from 1.0
    ),
    "ring_of_searching": LootTags(
        categories=["rare", "utility"],
        band_min=2, band_max=5,
        weight=0.6  # Reduced from 1.0
    ),
    "ring_of_clarity": LootTags(
        categories=["rare", "defensive"],
        band_min=2, band_max=5,
        weight=0.5  # Reduced from 0.8
    ),
    
    # Uncommon rings - start at B3 (depth 11+)
    "ring_of_constitution": LootTags(
        categories=["rare", "defensive"],
        band_min=3, band_max=5,  # Pushed from B2 to B3
        weight=0.5  # Reduced from 1.0
    ),
    "ring_of_resistance": LootTags(
        categories=["rare", "defensive"],
        band_min=3, band_max=5,
        weight=0.5  # Reduced from 0.8
    ),
    "ring_of_might": LootTags(
        categories=["rare", "offensive"],
        band_min=3, band_max=5,
        weight=0.5  # Reduced from 0.8
    ),
    "ring_of_free_action": LootTags(
        categories=["rare", "defensive"],
        band_min=3, band_max=5,
        weight=0.5  # Reduced from 0.8
    ),
    "ring_of_luck": LootTags(
        categories=["rare"],
        band_min=3, band_max=5,  # Pushed from B2 to B3
        weight=0.5  # Reduced from 0.8
    ),
    
    # Exotic/powerful rings - start at B4 (depth 16+)
    "ring_of_teleportation": LootTags(
        categories=["rare", "panic"],
        band_min=4, band_max=5,  # Pushed from B3 to B4
        weight=0.4  # Reduced from 0.8
    ),
    "ring_of_invisibility": LootTags(
        categories=["rare", "panic"],
        band_min=4, band_max=5,  # Pushed from B3 to B4
        weight=0.3  # Reduced from 0.6
    ),
    "ring_of_wizardry": LootTags(
        categories=["rare", "offensive"],
        band_min=4, band_max=5,  # Pushed from B3 to B4
        weight=0.3  # Reduced from 0.6
    ),
    "ring_of_speed": LootTags(
        categories=["rare", "panic"],
        band_min=4, band_max=5,  # Pushed from B3 to B4
        weight=0.3  # Reduced from 0.6
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # KEYS
    # ─────────────────────────────────────────────────────────────────────────
    "bronze_key": LootTags(
        categories=["key"],
        band_min=1, band_max=3,
        weight=2.0
    ),
    "silver_key": LootTags(
        categories=["key"],
        band_min=2, band_max=4,
        weight=1.5
    ),
    "gold_key": LootTags(
        categories=["key"],
        band_min=3, band_max=5,
        weight=1.0
    ),
    "dragon_scale": LootTags(
        categories=["key", "rare"],
        band_min=4, band_max=5,
        weight=0.5
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # MISC POTIONS
    # ─────────────────────────────────────────────────────────────────────────
    "speed_potion": LootTags(
        categories=["panic", "utility"],
        band_min=2, band_max=5,
        weight=2.5
    ),
    "levitation_potion": LootTags(
        categories=["utility"],
        band_min=2, band_max=5,
        weight=2.0
    ),
    "experience_potion": LootTags(
        categories=["rare", "utility"],
        band_min=3, band_max=5,
        weight=0.5
    ),
    
    # Phase 7: Tar Potion (speed debuff)
    # Categorized as panic item - can be used tactically or as emergency escape aid
    "tar_potion": LootTags(
        categories=["panic", "utility"],
        band_min=2, band_max=5,
        weight=2.0
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def get_loot_tags(item_id: str) -> Optional[LootTags]:
    """Get loot tags for an item by its ID.
    
    Args:
        item_id: Item identifier (e.g., "healing_potion", "sword")
        
    Returns:
        LootTags for the item, or None if not found
    """
    # Normalize item_id (handle display names)
    normalized_id = item_id.lower().replace(" ", "_")
    return LOOT_TAGS.get(normalized_id)


def get_band_for_depth(depth: int) -> int:
    """Get the band number (1-5) for a given dungeon depth.
    
    Aligned with ETP band system:
        B1: Depths 1-5
        B2: Depths 6-10
        B3: Depths 11-15
        B4: Depths 16-20
        B5: Depths 21-25+
    
    Args:
        depth: Dungeon depth (1-25+)
        
    Returns:
        Band number (1-5)
    """
    if depth <= 5:
        return 1
    elif depth <= 10:
        return 2
    elif depth <= 15:
        return 3
    elif depth <= 20:
        return 4
    else:
        return 5


def get_depth_for_band(band: int) -> int:
    """Get a representative depth for a given band number.
    
    Returns the center depth of the band for consistent testing.
    
    Args:
        band: Band number (1-5)
        
    Returns:
        Representative depth (3, 8, 13, 18, or 23)
    """
    band_centers = {1: 3, 2: 8, 3: 13, 4: 18, 5: 23}
    return band_centers.get(band, 3)


def get_items_by_category(category: str) -> List[str]:
    """Get all item IDs that have a specific category tag.
    
    Args:
        category: Category to search for (e.g., "healing", "panic")
        
    Returns:
        List of item IDs with that category
    """
    return [
        item_id for item_id, tags in LOOT_TAGS.items()
        if tags.has_category(category)
    ]


def get_items_for_band(band: int) -> List[str]:
    """Get all item IDs that can appear in a specific band.
    
    Args:
        band: Band number (1-5)
        
    Returns:
        List of item IDs available in that band
    """
    return [
        item_id for item_id, tags in LOOT_TAGS.items()
        if tags.is_available_in_band(band)
    ]


def get_category_summary() -> Dict[str, int]:
    """Get a summary of how many items are in each category.
    
    Returns:
        Dictionary mapping category names to item counts
    """
    summary: Dict[str, int] = {}
    for tags in LOOT_TAGS.values():
        for category in tags.categories:
            summary[category] = summary.get(category, 0) + 1
    return summary


# All loot categories for reference
LOOT_CATEGORIES = [
    "healing",
    "panic",
    "offensive",
    "defensive",
    "utility",
    "upgrade_weapon",
    "upgrade_armor",
    "rare",
    "key",
]


# ═══════════════════════════════════════════════════════════════════════════════
# BAND-BASED BALANCE MULTIPLIERS
# ═══════════════════════════════════════════════════════════════════════════════
# These multipliers adjust loot density and category weights per band.
# B1-B2 get drastically reduced spawns; B3-B5 are baseline (1.0).

# Item density multiplier: scales max_items_per_room
# Target: B1 ~5-8 items/room, B2 ~6-9 items/room, B3-B5 ~8-10 items/room
BAND_ITEM_DENSITY_MULTIPLIER: Dict[int, float] = {
    1: 0.35,   # B1: ~35% of normal (target 5-8 items/room)
    2: 0.45,   # B2: ~45% of normal (target 6-9 items/room)
    3: 1.0,    # B3: baseline
    4: 1.0,    # B4: baseline
    5: 1.0,    # B5: baseline
}

# Healing spawn weight multiplier: reduces healing flood in early bands
# Target: B1 ~0.7-1.2/room, B2 ~0.8-1.5/room
HEALING_BAND_MULTIPLIER: Dict[int, float] = {
    1: 0.25,   # B1: 25% of normal healing chance
    2: 0.35,   # B2: 35% of normal healing chance
    3: 1.0,    # B3: baseline
    4: 1.1,    # B4: slightly more healing for harder content
    5: 1.1,    # B5: slightly more healing for harder content
}

# Rare item (rings) spawn weight multiplier: near-zero in B1, slow ramp
# Target: B1 ~0-0.1/room, B2 ~0.1-0.3/room, B5 ~0.5/room
RARE_BAND_MULTIPLIER: Dict[int, float] = {
    1: 0.05,   # B1: almost no rings (5% of normal)
    2: 0.15,   # B2: very few rings (15% of normal)
    3: 0.5,    # B3: some rings (50% of normal)
    4: 0.8,    # B4: most rings
    5: 1.0,    # B5: full ring rates
}


def get_band_density_multiplier(band: int) -> float:
    """Get the item density multiplier for a band.
    
    This scales the max_items_per_room to reduce loot flood in early game.
    
    Args:
        band: Band number (1-5)
        
    Returns:
        Multiplier (0.0-1.0+) for item density
    """
    return BAND_ITEM_DENSITY_MULTIPLIER.get(band, 1.0)


def get_healing_multiplier(band: int) -> float:
    """Get the healing spawn weight multiplier for a band.
    
    This reduces natural healing rates in early bands while pity backs us up.
    
    Args:
        band: Band number (1-5)
        
    Returns:
        Multiplier (0.0-1.0+) for healing spawn weight
    """
    return HEALING_BAND_MULTIPLIER.get(band, 1.0)


def get_rare_multiplier(band: int) -> float:
    """Get the rare item (rings) spawn weight multiplier for a band.
    
    Rings should be very rare in B1, slowly ramping up.
    
    Args:
        band: Band number (1-5)
        
    Returns:
        Multiplier (0.0-1.0) for rare item spawn weight
    """
    return RARE_BAND_MULTIPLIER.get(band, 1.0)

