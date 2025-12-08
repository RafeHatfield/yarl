"""Hit/Dodge model for Phase 8: Accuracy and Evasion system.

This module implements the hit chance calculation for combat, providing
a separate axis of combat reliability from the speed/momentum system.

Key concepts:
- Accuracy (attacker stat): Higher = more likely to hit
- Evasion (defender stat): Higher = more likely to dodge
- Speed determines how often you act; accuracy determines how often you connect

Formula:
    hit_chance = BASE_HIT + (attacker_accuracy - defender_evasion) * STEP
    clamped to [MIN_HIT, MAX_HIT]

Example with defaults:
    - Base 75%, Step 5%, Min 5%, Max 95%
    - Player (acc=2) vs Zombie (eva=0): 75% + (2-0)*5% = 85% hit
    - Player (acc=2) vs Wraith (eva=4): 75% + (2-4)*5% = 65% hit
    - Wraith (acc=3) vs Player (eva=1): 75% + (3-1)*5% = 85% hit
"""

import random
from typing import TYPE_CHECKING, Callable, Optional

from logger_config import get_logger

if TYPE_CHECKING:
    from entity import Entity

logger = get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# HIT MODEL CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
# These can be tuned for balance. All values are in range [0.0, 1.0].

BASE_HIT: float = 0.75      # 75% base chance to hit
STEP: float = 0.05          # Each point of accuracy/evasion = 5%
MIN_HIT: float = 0.05       # 5% floor (always some chance to hit)
MAX_HIT: float = 0.95       # 95% ceiling (always some chance to miss)

# Default accuracy/evasion for entities without explicit values
DEFAULT_ACCURACY: int = 2
DEFAULT_EVASION: int = 1


def compute_hit_chance(attacker_accuracy: int, defender_evasion: int) -> float:
    """Compute the probability of hitting based on accuracy vs evasion.
    
    Formula:
        hit_chance = BASE_HIT + (attacker_accuracy - defender_evasion) * STEP
        clamped to [MIN_HIT, MAX_HIT]
    
    Args:
        attacker_accuracy: Attacker's accuracy stat (higher = more accurate)
        defender_evasion: Defender's evasion stat (higher = harder to hit)
        
    Returns:
        float: Hit probability in range [MIN_HIT, MAX_HIT]
        
    Examples:
        >>> compute_hit_chance(2, 1)  # Player vs orc
        0.80
        >>> compute_hit_chance(2, 4)  # Player vs wraith
        0.65
        >>> compute_hit_chance(1, 0)  # Zombie vs player
        0.80
    """
    raw_chance = BASE_HIT + (attacker_accuracy - defender_evasion) * STEP
    clamped = max(MIN_HIT, min(MAX_HIT, raw_chance))
    
    logger.debug(
        f"Hit chance: {attacker_accuracy} acc vs {defender_evasion} eva = "
        f"{raw_chance:.0%} raw -> {clamped:.0%} clamped"
    )
    
    return clamped


def roll_to_hit(
    attacker_accuracy: int,
    defender_evasion: int,
    rng: Optional[Callable[[], float]] = None
) -> bool:
    """Roll to determine if an attack hits.
    
    Uses compute_hit_chance() to get probability, then rolls RNG.
    
    Args:
        attacker_accuracy: Attacker's accuracy stat
        defender_evasion: Defender's evasion stat
        rng: Optional RNG function returning float in [0.0, 1.0).
            Defaults to random.random(). Useful for testing.
            
    Returns:
        bool: True if attack hits, False if it misses
    """
    if rng is None:
        rng = random.random
    
    hit_chance = compute_hit_chance(attacker_accuracy, defender_evasion)
    roll = rng()
    
    hit = roll < hit_chance
    
    logger.debug(
        f"Hit roll: {roll:.3f} vs {hit_chance:.3f} = {'HIT' if hit else 'MISS'}"
    )
    
    return hit


def get_accuracy(entity: "Entity") -> int:
    """Get accuracy stat from an entity.
    
    Looks for accuracy on Fighter component, falls back to DEFAULT_ACCURACY.
    
    Args:
        entity: Entity to get accuracy from
        
    Returns:
        int: Accuracy stat value
    """
    from components.component_registry import ComponentType
    
    if not entity:
        return DEFAULT_ACCURACY
    
    fighter = entity.get_component_optional(ComponentType.FIGHTER)
    if fighter:
        return getattr(fighter, 'accuracy', DEFAULT_ACCURACY)
    
    return DEFAULT_ACCURACY


def get_evasion(entity: "Entity") -> int:
    """Get evasion stat from an entity.
    
    Looks for evasion on Fighter component, falls back to DEFAULT_EVASION.
    
    Args:
        entity: Entity to get evasion from
        
    Returns:
        int: Evasion stat value
    """
    from components.component_registry import ComponentType
    
    if not entity:
        return DEFAULT_EVASION
    
    fighter = entity.get_component_optional(ComponentType.FIGHTER)
    if fighter:
        return getattr(fighter, 'evasion', DEFAULT_EVASION)
    
    return DEFAULT_EVASION


def get_hit_chance_for_entities(attacker: "Entity", defender: "Entity") -> float:
    """Compute hit chance between two entities.
    
    Convenience wrapper that extracts accuracy/evasion from entities.
    
    Args:
        attacker: Attacking entity
        defender: Defending entity
        
    Returns:
        float: Hit probability in range [MIN_HIT, MAX_HIT]
    """
    return compute_hit_chance(get_accuracy(attacker), get_evasion(defender))


def roll_to_hit_entities(
    attacker: "Entity",
    defender: "Entity",
    rng: Optional[Callable[[], float]] = None
) -> bool:
    """Roll to hit between two entities.
    
    Convenience wrapper that extracts accuracy/evasion from entities.
    
    Args:
        attacker: Attacking entity
        defender: Defending entity
        rng: Optional RNG function for testing
        
    Returns:
        bool: True if attack hits, False if it misses
    """
    return roll_to_hit(get_accuracy(attacker), get_evasion(defender), rng)


def get_accuracy_bonus_display(accuracy: int) -> str:
    """Get display string for accuracy bonus.
    
    Shows the percentage modifier from the accuracy stat.
    
    Args:
        accuracy: Accuracy stat value
        
    Returns:
        str: Display string like "+10%" or "-5%"
    """
    diff_from_default = accuracy - DEFAULT_ACCURACY
    bonus_pct = diff_from_default * STEP * 100
    
    if bonus_pct >= 0:
        return f"+{bonus_pct:.0f}%"
    else:
        return f"{bonus_pct:.0f}%"


def get_evasion_bonus_display(evasion: int) -> str:
    """Get display string for evasion bonus.
    
    Shows the percentage modifier from the evasion stat.
    
    Args:
        evasion: Evasion stat value
        
    Returns:
        str: Display string like "+5%" or "-5%"
    """
    diff_from_default = evasion - DEFAULT_EVASION
    bonus_pct = diff_from_default * STEP * 100
    
    if bonus_pct >= 0:
        return f"+{bonus_pct:.0f}%"
    else:
        return f"{bonus_pct:.0f}%"
