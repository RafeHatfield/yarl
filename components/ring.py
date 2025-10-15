"""Ring component for ring items with passive effects.

Rings are equippable items that provide continuous passive bonuses while worn.
Unlike other equipment that provides simple stat bonuses, rings can have
special effects that trigger under certain conditions (e.g., Ring of Teleportation)
or provide unique benefits (e.g., Ring of Regeneration).

This module defines the Ring component and the RingEffect enum for different
ring types and their effects.
"""

from enum import Enum, auto
from typing import Optional, List, Dict, Any


class RingEffect(Enum):
    """Types of ring effects.
    
    Each ring type has a unique effect that modifies gameplay:
    - Stat bonuses (STR, DEX, CON)
    - Combat bonuses (protection, might)
    - Passive effects (regeneration, teleportation)
    - Immunities (free action, clarity)
    - Utility effects (speed, searching, wizardry)
    """
    
    # Defensive
    PROTECTION = auto()      # +2 AC
    REGENERATION = auto()    # Heal 1 HP every 5 turns
    RESISTANCE = auto()      # +10% to all resistances
    
    # Offensive
    STRENGTH = auto()        # +2 STR
    DEXTERITY = auto()       # +2 DEX
    MIGHT = auto()           # +1d4 damage to all attacks
    
    # Utility
    TELEPORTATION = auto()   # 20% chance to teleport when hit
    INVISIBILITY = auto()    # Start each level invisible for 5 turns
    SEARCHING = auto()       # Reveal traps and secret doors within 3 tiles
    FREE_ACTION = auto()     # Immune to paralysis and slow
    
    # Magic
    WIZARDRY = auto()        # All scrolls/wands get +1 duration/damage
    CLARITY = auto()         # Immune to confusion
    SPEED = auto()           # Permanent +10% movement speed
    
    # Special
    CONSTITUTION = auto()    # +2 CON (+20 max HP)
    LUCK = auto()            # +5% critical hit chance, better loot


class Ring:
    """Component for ring items with passive effects.
    
    Rings provide continuous bonuses while equipped. The bonuses are applied
    passively and don't require activation. Some rings have special effects
    that trigger under certain conditions.
    
    Attributes:
        ring_effect (RingEffect): The type of effect this ring provides
        effect_strength (int): Strength modifier for the effect (default values if 0)
        owner (Entity): The entity that owns this component
    
    Example:
        >>> ring = Ring(RingEffect.PROTECTION, effect_strength=2)
        >>> ring.apply_passive_effects(player)
        # Player gains +2 AC while ring is equipped
    """
    
    def __init__(self, ring_effect: RingEffect, effect_strength: int = 0):
        """Initialize a Ring component.
        
        Args:
            ring_effect (RingEffect): The type of effect this ring provides
            effect_strength (int, optional): Strength modifier for the effect.
                If 0, uses default values for the ring type. Defaults to 0.
        """
        self.ring_effect = ring_effect
        self.effect_strength = effect_strength if effect_strength > 0 else self._get_default_strength()
        self.owner = None  # Will be set by Entity when component is registered
    
    def _get_default_strength(self) -> int:
        """Get default effect strength based on ring type.
        
        Returns:
            int: Default strength value for this ring's effect
        """
        # Map ring effects to their default strengths
        default_strengths = {
            RingEffect.PROTECTION: 2,        # +2 AC
            RingEffect.REGENERATION: 5,      # Heal every 5 turns
            RingEffect.RESISTANCE: 10,       # +10% resistance
            RingEffect.STRENGTH: 2,          # +2 STR
            RingEffect.DEXTERITY: 2,         # +2 DEX
            RingEffect.MIGHT: 4,             # +1d4 damage
            RingEffect.TELEPORTATION: 20,    # 20% chance
            RingEffect.INVISIBILITY: 5,      # 5 turns invisible
            RingEffect.SEARCHING: 3,         # 3 tile radius
            RingEffect.FREE_ACTION: 1,       # Boolean (1 = immune)
            RingEffect.WIZARDRY: 1,          # +1 to spell effects
            RingEffect.CLARITY: 1,           # Boolean (1 = immune)
            RingEffect.SPEED: 10,            # +10% speed
            RingEffect.CONSTITUTION: 2,      # +2 CON
            RingEffect.LUCK: 5,              # +5% crit chance
        }
        
        return default_strengths.get(self.ring_effect, 1)
    
    def get_ac_bonus(self) -> int:
        """Get AC bonus from this ring.
        
        Only Ring of Protection provides AC bonus.
        
        Returns:
            int: AC bonus (0 if no bonus)
        """
        if self.ring_effect == RingEffect.PROTECTION:
            return self.effect_strength
        return 0
    
    def get_stat_bonus(self, stat: str) -> int:
        """Get stat bonus from this ring.
        
        Args:
            stat (str): Stat name ('strength', 'dexterity', 'constitution')
            
        Returns:
            int: Stat bonus (0 if no bonus)
        """
        stat_map = {
            'strength': RingEffect.STRENGTH,
            'dexterity': RingEffect.DEXTERITY,
            'constitution': RingEffect.CONSTITUTION,
        }
        
        ring_for_stat = stat_map.get(stat.lower())
        if self.ring_effect == ring_for_stat:
            return self.effect_strength
        return 0
    
    def get_damage_bonus(self) -> str:
        """Get damage bonus dice from this ring.
        
        Ring of Might provides +1d4 damage.
        
        Returns:
            str: Damage bonus in dice notation (e.g., "1d4") or empty string
        """
        if self.ring_effect == RingEffect.MIGHT:
            return f"1d{self.effect_strength}"
        return ""
    
    def provides_immunity(self, status_effect: str) -> bool:
        """Check if this ring provides immunity to a status effect.
        
        Args:
            status_effect (str): Status effect name ('paralysis', 'slow', 'confusion')
            
        Returns:
            bool: True if ring provides immunity, False otherwise
        """
        # Ring of Free Action: immune to paralysis and slow
        if self.ring_effect == RingEffect.FREE_ACTION:
            return status_effect.lower() in ['paralysis', 'slow']
        
        # Ring of Clarity: immune to confusion
        if self.ring_effect == RingEffect.CLARITY:
            return status_effect.lower() == 'confusion'
        
        return False
    
    def process_turn(self, wearer) -> List[Dict[str, Any]]:
        """Process turn-based effects for this ring.
        
        Called at the start of each turn to handle effects like regeneration.
        
        Args:
            wearer (Entity): The entity wearing this ring
            
        Returns:
            List[Dict[str, Any]]: List of result dictionaries with effects/messages
        """
        results = []
        
        # Ring of Regeneration: heal every N turns
        if self.ring_effect == RingEffect.REGENERATION:
            if hasattr(wearer, 'turn_count'):
                # Heal every effect_strength turns (default: 5)
                if wearer.turn_count % self.effect_strength == 0:
                    if wearer.fighter and wearer.fighter.hp < wearer.fighter.max_hp:
                        wearer.fighter.heal(1)
                        results.append({
                            'message': f"{wearer.name}'s ring glows softly. (+1 HP)"
                        })
        
        return results
    
    def on_take_damage(self, wearer, damage: int) -> List[Dict[str, Any]]:
        """Handle ring effects that trigger when damage is taken.
        
        Args:
            wearer (Entity): The entity wearing this ring
            damage (int): Amount of damage taken
            
        Returns:
            List[Dict[str, Any]]: List of result dictionaries with effects/messages
        """
        results = []
        
        # Ring of Teleportation: chance to teleport when hit
        if self.ring_effect == RingEffect.TELEPORTATION:
            import random
            if random.randint(1, 100) <= self.effect_strength:  # Default: 20% chance
                # Trigger teleportation
                results.append({
                    'teleport': True,
                    'message': f"{wearer.name}'s ring flashes! You teleport away!"
                })
        
        return results
    
    def __repr__(self) -> str:
        """String representation for debugging.
        
        Returns:
            str: Debug string
        """
        return f"Ring({self.ring_effect.name}, strength={self.effect_strength})"

