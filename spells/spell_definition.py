"""Spell definition dataclass.

This module defines the SpellDefinition dataclass that holds all spell data
in a uniform, declarative format.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, List
from spells.spell_types import SpellCategory, TargetingType, DamageType, EffectType


@dataclass
class SpellDefinition:
    """Unified spell definition.
    
    This dataclass contains all the information needed to cast a spell,
    including damage, targeting, effects, and messages. It replaces the
    scattered parameters in the old spell functions.
    
    Attributes:
        spell_id: Unique identifier for the spell
        name: Display name
        category: Type of spell (offensive, utility, etc.)
        targeting: How the spell targets
        
        # Damage/Effect
        damage: Dice notation for damage ("3d6", "2d8+4")
        damage_type: Type of damage dealt
        radius: Radius for AoE spells
        cone_range: Range for cone spells
        cone_width: Width in degrees for cone spells
        
        # Requirements
        requires_los: Must have line of sight to target
        requires_target: Must have a valid target
        max_range: Maximum casting range
        
        # Status Effects
        duration: Duration in turns for effects
        effect_type: Type of status effect to apply
        effect_strength: Strength modifier for effects
        
        # Ground Hazards
        creates_hazard: Whether spell creates ground hazards
        hazard_type: Type of hazard ("fire", "poison")
        hazard_duration: How long hazards last
        hazard_damage: Damage per turn from hazards
        
        # Messages
        cast_message: Message when spell is cast
        success_message: Message on successful hit/effect
        fail_message: Message on failure
        no_target_message: Message when no valid target
        
        # Visual
        visual_effect: Function to show visual effect
        
        # Misc
        consumable: Whether item is consumed on use
        heal_amount: Amount of HP restored (for healing spells)
    """
    
    # Core properties
    spell_id: str
    name: str
    category: SpellCategory
    targeting: TargetingType
    
    # Damage/Effect (optional)
    damage: Optional[str] = None  # Dice notation
    damage_type: Optional[DamageType] = None
    radius: int = 0
    cone_range: int = 0
    cone_width: int = 45  # Degrees
    
    # Requirements
    requires_los: bool = True
    requires_target: bool = True
    max_range: int = 10
    
    # Status Effects
    duration: int = 0
    effect_type: Optional[EffectType] = None
    effect_strength: float = 1.0
    
    # Ground Hazards
    creates_hazard: bool = False
    hazard_type: Optional[str] = None
    hazard_duration: int = 0
    hazard_damage: int = 0
    
    # Messages
    cast_message: str = ""
    success_message: str = ""
    fail_message: str = ""
    no_target_message: str = "There is no valid target there."
    
    # Visual
    visual_effect: Optional[Callable] = None
    
    # Misc
    consumable: bool = True
    heal_amount: int = 0
    
    def __post_init__(self):
        """Validate spell definition after initialization."""
        if not self.spell_id:
            raise ValueError("spell_id cannot be empty")
        if not self.name:
            raise ValueError("name cannot be empty")
        if self.radius < 0:
            raise ValueError("radius cannot be negative")
        if self.max_range < 0:
            raise ValueError("max_range cannot be negative")

