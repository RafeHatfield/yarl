"""Spell type definitions and enumerations.

This module defines the core types and categories for the spell system.
"""

from enum import Enum, auto


class SpellCategory(Enum):
    """Categories of spells."""
    OFFENSIVE = auto()  # Damage dealing
    HEALING = auto()     # HP restoration
    UTILITY = auto()     # Control, movement, effects
    BUFF = auto()        # Enhancements, shields
    SUMMON = auto()      # Creature summoning
    
    
class TargetingType(Enum):
    """How a spell targets entities or locations."""
    SELF = auto()           # Casts on self
    SINGLE_ENEMY = auto()   # Single target enemy
    SINGLE_ANY = auto()     # Single target (friend or foe)
    AOE = auto()            # Area of effect (circular)
    CONE = auto()           # Cone from caster
    LOCATION = auto()       # Ground location
    DIRECTION = auto()      # Directional (for rays/beams)


class DamageType(Enum):
    """Type of damage dealt."""
    PHYSICAL = auto()
    FIRE = auto()
    COLD = auto()
    LIGHTNING = auto()
    POISON = auto()
    PSYCHIC = auto()  # For yo mama jokes


class EffectType(Enum):
    """Types of status effects."""
    CONFUSION = auto()
    SLOW = auto()
    GLUE = auto()  # Immobilized
    RAGE = auto()  # Berserk
    SHIELD = auto()  # Defense buff
    TAUNT = auto()  # Forced targeting
    INVISIBLE = auto()
    FEAR = auto()  # Causes enemies to flee
    IDENTIFY_MODE = auto()  # Can identify 1 item per turn

