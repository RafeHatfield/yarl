"""Faction system for entity relationships and combat targeting.

This module defines the faction system that determines which entities
are hostile to each other, enabling monster-vs-monster combat and
complex tactical scenarios.

Phase 10: Extended faction system with:
- ORC_FACTION: Orcs, goblins, trolls (living society faction, assist each other)
- UNDEAD: Zombies, skeletons, wraiths (attack living/fleshy targets)
- CULTIST: Defensive/territorial (attack intruders in their territory)
- INDEPENDENT: Beasts, spiders, slimes (treat everything as food, simple behavior)
"""

from enum import Enum
from typing import Optional


class Faction(Enum):
    """Entity factions that determine combat relationships.
    
    Phase 10: Extended faction system for faction manipulation mechanics.
    
    Faction Behaviors:
    - PLAYER: Hero, hostile to all monster factions
    - ORC_FACTION: Orcs/goblins/trolls - assist each other, hostile to player
    - UNDEAD: Zombies/skeletons/wraiths - attack living targets, no coordination
    - CULTIST: Defensive/territorial - attack intruders, don't roam
    - INDEPENDENT: Beasts/spiders - simple predators, hostile to all
    - NEUTRAL: Legacy - monsters that only attack player
    - HOSTILE_ALL: Legacy - attacks everyone (deprecated, use INDEPENDENT)
    """
    
    PLAYER = "player"              # Player character
    ORC_FACTION = "orc"            # Orcs, goblins, trolls - living society
    UNDEAD = "undead"              # Zombies, skeletons, wraiths - attack living
    CULTIST = "cultist"            # Cultists - defensive/territorial
    INDEPENDENT = "independent"    # Beasts, spiders, slimes - predators
    NEUTRAL = "neutral"            # Legacy: Most monsters - only attack player
    HOSTILE_ALL = "hostile_all"    # Legacy: Slimes - attack everyone


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 10: FACTION HOSTILITY MATRIX
# ═══════════════════════════════════════════════════════════════════════════════
# Defines which factions are hostile to which. True = hostile.
# Read as: HOSTILITY_MATRIX[attacker][target] = is_hostile

HOSTILITY_MATRIX = {
    Faction.PLAYER: {
        # Player is hostile to all monster factions
        Faction.PLAYER: False,
        Faction.ORC_FACTION: True,
        Faction.UNDEAD: True,
        Faction.CULTIST: True,
        Faction.INDEPENDENT: True,
        Faction.NEUTRAL: True,
        Faction.HOSTILE_ALL: True,
    },
    Faction.ORC_FACTION: {
        # Orcs attack player and undead, but tolerate other living factions
        Faction.PLAYER: True,
        Faction.ORC_FACTION: False,  # Don't attack fellow orcs
        Faction.UNDEAD: True,        # Undead are enemies
        Faction.CULTIST: False,      # Neutral with cultists (could ally)
        Faction.INDEPENDENT: True,   # Defend against beasts
        Faction.NEUTRAL: False,
        Faction.HOSTILE_ALL: True,
    },
    Faction.UNDEAD: {
        # Undead attack all living creatures
        Faction.PLAYER: True,
        Faction.ORC_FACTION: True,   # Attack living orcs
        Faction.UNDEAD: False,       # Don't attack fellow undead
        Faction.CULTIST: True,       # Attack living cultists
        Faction.INDEPENDENT: True,   # Attack living beasts
        Faction.NEUTRAL: True,
        Faction.HOSTILE_ALL: True,
    },
    Faction.CULTIST: {
        # Cultists are defensive - attack intruders
        Faction.PLAYER: True,        # Attack player who enters territory
        Faction.ORC_FACTION: True,   # Attack orcs who intrude
        Faction.UNDEAD: True,        # Attack undead intruders
        Faction.CULTIST: False,      # Don't attack fellow cultists
        Faction.INDEPENDENT: True,   # Defend against beasts
        Faction.NEUTRAL: True,
        Faction.HOSTILE_ALL: True,
    },
    Faction.INDEPENDENT: {
        # Independents (beasts) treat everything as food
        Faction.PLAYER: True,
        Faction.ORC_FACTION: True,
        Faction.UNDEAD: True,        # Even attack undead (instinct)
        Faction.CULTIST: True,
        Faction.INDEPENDENT: False,  # Don't attack same species (usually)
        Faction.NEUTRAL: True,
        Faction.HOSTILE_ALL: True,
    },
    Faction.NEUTRAL: {
        # Legacy neutral - only attacks player
        Faction.PLAYER: True,
        Faction.ORC_FACTION: False,
        Faction.UNDEAD: False,
        Faction.CULTIST: False,
        Faction.INDEPENDENT: False,
        Faction.NEUTRAL: False,
        Faction.HOSTILE_ALL: True,
    },
    Faction.HOSTILE_ALL: {
        # Legacy hostile_all - attacks everyone except other hostile_all
        Faction.PLAYER: True,
        Faction.ORC_FACTION: True,
        Faction.UNDEAD: True,
        Faction.CULTIST: True,
        Faction.INDEPENDENT: True,
        Faction.NEUTRAL: True,
        Faction.HOSTILE_ALL: False,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 10: TARGET PRIORITY MATRIX
# ═══════════════════════════════════════════════════════════════════════════════
# Defines targeting priority when multiple valid targets exist.
# Higher values = higher priority. 0 = won't target.

TARGET_PRIORITY_MATRIX = {
    Faction.PLAYER: {
        # Player prioritizes closest threat
        Faction.ORC_FACTION: 5,
        Faction.UNDEAD: 5,
        Faction.CULTIST: 5,
        Faction.INDEPENDENT: 5,
        Faction.NEUTRAL: 5,
        Faction.HOSTILE_ALL: 5,
    },
    Faction.ORC_FACTION: {
        # Orcs prioritize: player > undead > beasts
        Faction.PLAYER: 10,
        Faction.UNDEAD: 6,       # Undead are a threat
        Faction.CULTIST: 0,      # Don't attack cultists
        Faction.INDEPENDENT: 4,  # Low priority
        Faction.NEUTRAL: 0,
        Faction.HOSTILE_ALL: 3,
    },
    Faction.UNDEAD: {
        # Undead prioritize living/fleshy targets
        Faction.PLAYER: 10,      # Player is primary target
        Faction.ORC_FACTION: 7,  # Living flesh
        Faction.CULTIST: 7,      # Living flesh
        Faction.INDEPENDENT: 5,  # Beasts have flesh too
        Faction.NEUTRAL: 5,
        Faction.HOSTILE_ALL: 3,  # Low priority (slimes have no flesh)
    },
    Faction.CULTIST: {
        # Cultists prioritize intruders by threat level
        Faction.PLAYER: 10,      # Player is most dangerous
        Faction.ORC_FACTION: 5,
        Faction.UNDEAD: 6,       # Undead are persistent
        Faction.INDEPENDENT: 4,
        Faction.NEUTRAL: 4,
        Faction.HOSTILE_ALL: 3,
    },
    Faction.INDEPENDENT: {
        # Beasts prioritize nearest prey
        Faction.PLAYER: 8,       # Player is good prey
        Faction.ORC_FACTION: 6,
        Faction.UNDEAD: 3,       # Low priority (no flesh)
        Faction.CULTIST: 6,
        Faction.NEUTRAL: 5,
        Faction.HOSTILE_ALL: 2,
    },
    Faction.NEUTRAL: {
        Faction.PLAYER: 10,
        Faction.HOSTILE_ALL: 3,
    },
    Faction.HOSTILE_ALL: {
        # Attacks everything equally
        Faction.PLAYER: 10,
        Faction.ORC_FACTION: 5,
        Faction.UNDEAD: 5,
        Faction.CULTIST: 5,
        Faction.INDEPENDENT: 5,
        Faction.NEUTRAL: 5,
    },
}


def get_faction_from_string(faction_str: str) -> Faction:
    """Convert string to Faction enum.
    
    Args:
        faction_str: String representation of faction
        
    Returns:
        Faction enum value, defaults to NEUTRAL if invalid
    """
    # Handle common aliases
    faction_aliases = {
        "orc_faction": "orc",
        "orcs": "orc",
        "beast": "independent",
        "beasts": "independent",
        "spider": "independent",
        "slime": "hostile_all",  # Slimes remain hostile_all for backward compat
    }
    
    normalized = faction_str.lower() if faction_str else "neutral"
    normalized = faction_aliases.get(normalized, normalized)
    
    try:
        return Faction(normalized)
    except ValueError:
        return Faction.NEUTRAL


def are_factions_hostile(faction1: Faction, faction2: Faction) -> bool:
    """Check if two factions are hostile to each other.
    
    Phase 10: Now uses hostility matrix for richer faction relationships.
    
    Args:
        faction1: First faction to check
        faction2: Second faction to check
        
    Returns:
        True if factions should attack each other
    """
    # Same faction entities don't attack each other
    if faction1 == faction2:
        return False
    
    # Check hostility matrix
    if faction1 in HOSTILITY_MATRIX:
        faction1_hostilities = HOSTILITY_MATRIX[faction1]
        if faction2 in faction1_hostilities:
            return faction1_hostilities[faction2]
    
    # Fallback: legacy behavior
    # HOSTILE_ALL attacks everyone except other HOSTILE_ALL
    if faction1 == Faction.HOSTILE_ALL:
        return faction2 != Faction.HOSTILE_ALL
    if faction2 == Faction.HOSTILE_ALL:
        return faction1 != Faction.HOSTILE_ALL
    
    # NEUTRAL monsters only attack PLAYER
    if faction1 == Faction.NEUTRAL:
        return faction2 == Faction.PLAYER
    if faction2 == Faction.NEUTRAL:
        return faction1 == Faction.PLAYER
    
    # PLAYER is hostile to all non-PLAYER factions
    if faction1 == Faction.PLAYER:
        return faction2 != Faction.PLAYER
    if faction2 == Faction.PLAYER:
        return faction1 != Faction.PLAYER
    
    return False


def get_target_priority(attacker_faction: Faction, target_faction: Faction) -> int:
    """Get targeting priority for different faction combinations.
    
    Phase 10: Now uses priority matrix for richer targeting decisions.
    Higher values indicate higher priority targets.
    
    Args:
        attacker_faction: Faction of the attacking entity
        target_faction: Faction of the potential target
        
    Returns:
        Priority value (higher = more priority, 0 = won't target)
    """
    if not are_factions_hostile(attacker_faction, target_faction):
        return 0  # Not hostile, no priority
    
    # Check priority matrix
    if attacker_faction in TARGET_PRIORITY_MATRIX:
        priorities = TARGET_PRIORITY_MATRIX[attacker_faction]
        if target_faction in priorities:
            return priorities[target_faction]
    
    # Fallback: legacy behavior
    # Player always gets highest priority
    if target_faction == Faction.PLAYER:
        return 10
    
    # Other hostile targets get lower priority
    return 5


def is_living_faction(faction: Faction) -> bool:
    """Check if a faction represents living creatures (for undead targeting).
    
    Phase 10: Used by undead AI to prioritize living targets.
    
    Args:
        faction: The faction to check
        
    Returns:
        True if faction is living (has flesh)
    """
    living_factions = {
        Faction.PLAYER,
        Faction.ORC_FACTION,
        Faction.CULTIST,
        Faction.NEUTRAL,
    }
    return faction in living_factions


def get_faction_display_name(faction: Faction) -> str:
    """Get a human-readable name for a faction.
    
    Phase 10: Used for UI/messages when describing factions.
    
    Args:
        faction: The faction to get name for
        
    Returns:
        Human-readable faction name
    """
    display_names = {
        Faction.PLAYER: "Player",
        Faction.ORC_FACTION: "Orcs",
        Faction.UNDEAD: "Undead",
        Faction.CULTIST: "Cultists",
        Faction.INDEPENDENT: "Beasts",
        Faction.NEUTRAL: "Monsters",
        Faction.HOSTILE_ALL: "Slimes",
    }
    return display_names.get(faction, faction.value.title())
