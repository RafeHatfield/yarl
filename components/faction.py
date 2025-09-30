"""Faction system for entity relationships and combat targeting.

This module defines the faction system that determines which entities
are hostile to each other, enabling monster-vs-monster combat and
complex tactical scenarios.
"""

from enum import Enum
from typing import Optional


class Faction(Enum):
    """Entity factions that determine combat relationships."""
    
    PLAYER = "player"           # Player character
    NEUTRAL = "neutral"         # Most monsters - only attack player
    HOSTILE_ALL = "hostile_all" # Slimes - attack everyone including other monsters
    
    # Future faction possibilities:
    # UNDEAD = "undead"         # Skeletons, zombies, liches
    # HUMANOID = "humanoid"     # Orcs, goblins, bandits  
    # BEAST = "beast"           # Wolves, bears, spiders
    # ELEMENTAL = "elemental"   # Fire/ice/earth elementals


def get_faction_from_string(faction_str: str) -> Faction:
    """Convert string to Faction enum.
    
    Args:
        faction_str: String representation of faction
        
    Returns:
        Faction enum value, defaults to NEUTRAL if invalid
    """
    try:
        return Faction(faction_str)
    except ValueError:
        return Faction.NEUTRAL


def are_factions_hostile(faction1: Faction, faction2: Faction) -> bool:
    """Check if two factions are hostile to each other.
    
    Args:
        faction1: First faction to check
        faction2: Second faction to check
        
    Returns:
        True if factions should attack each other
    """
    # Same faction entities don't attack each other
    if faction1 == faction2:
        return False
    
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
    
    Higher values indicate higher priority targets.
    
    Args:
        attacker_faction: Faction of the attacking entity
        target_faction: Faction of the potential target
        
    Returns:
        Priority value (higher = more priority)
    """
    if not are_factions_hostile(attacker_faction, target_faction):
        return 0  # Not hostile, no priority
    
    # Player always gets highest priority
    if target_faction == Faction.PLAYER:
        return 10
    
    # Other hostile targets get lower priority
    return 5
