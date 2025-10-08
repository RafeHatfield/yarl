from typing import List, Dict, Any, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from entity import Entity

class StatusEffect:
    """Base class for all status effects."""
    def __init__(self, name: str, duration: int, owner: 'Entity'):
        self.name = name
        self.duration = duration
        self.owner = owner
        self.is_active = False

    def apply(self) -> List[Dict[str, Any]]:
        """Apply the effect when it starts."""
        self.is_active = True
        return []

    def remove(self) -> List[Dict[str, Any]]:
        """Remove the effect when it ends."""
        self.is_active = False
        return []

    def process_turn_start(self) -> List[Dict[str, Any]]:
        """Process effect at the start of the owner's turn."""
        return []

    def process_turn_end(self) -> List[Dict[str, Any]]:
        """Process effect at the end of the owner's turn."""
        self.duration -= 1
        # Don't call remove() here - let the manager handle removal
        return []

    def __repr__(self):
        return f"{self.name}({self.duration} turns)"

class InvisibilityEffect(StatusEffect):
    """Makes the owner invisible to most AI."""
    def __init__(self, duration: int, owner: 'Entity'):
        super().__init__("invisibility", duration, owner)

    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        self.owner.invisible = True
        from game_messages import Message
        results.append({'message': Message(f"{self.owner.name} becomes invisible!", (150, 200, 255))})
        return results

    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        self.owner.invisible = False
        from game_messages import Message
        results.append({'message': Message(f"{self.owner.name} is no longer invisible.", (150, 200, 255))})
        return results

    def break_invisibility(self) -> List[Dict[str, Any]]:
        """Immediately remove invisibility, e.g., on attack."""
        if self.is_active:
            self.duration = 0 # Force removal next turn or immediately
            return self.remove()
        return []


class DisorientationEffect(StatusEffect):
    """Makes the owner move randomly for a short duration."""
    def __init__(self, duration: int, owner: 'Entity'):
        super().__init__("disorientation", duration, owner)
        self.previous_ai = None
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        
        # Store the current AI and replace with confused AI
        ai = self.owner.components.get(ComponentType.AI)
        if ai:
            from components.ai import ConfusedMonster
            self.previous_ai = self.owner.ai
            self.owner.ai = ConfusedMonster(self.previous_ai, self.duration)
            self.owner.ai.owner = self.owner
        
        from game_messages import Message
        results.append({
            'message': Message(
                f"{self.owner.name} feels disoriented!",
                (255, 165, 0)  # Orange
            )
        })
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        
        # Restore previous AI
        if self.previous_ai and self.owner.components.has(ComponentType.AI):
            self.owner.ai = self.previous_ai
            self.previous_ai = None
        
        from game_messages import Message
        results.append({
            'message': Message(
                f"{self.owner.name} is no longer disoriented.",
                (200, 200, 200)  # Gray
            )
        })
        return results


class ShieldEffect(StatusEffect):
    """Temporarily boosts defense, but monsters have a backfire chance."""
    def __init__(self, duration: int, owner: 'Entity', defense_bonus: int = 4):
        super().__init__("shield", duration, owner)
        self.defense_bonus = defense_bonus
        self.backfired = False
        self.original_base_defense = None
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        
        # Check if this is a monster using the scroll
        ai = self.owner.components.get(ComponentType.AI)
        is_monster = ai is not None
        
        if is_monster:
            # 10% chance to backfire for monsters!
            from random import random
            if random() < 0.10:
                self.backfired = True
                # Halve base defense (defense property is read-only)
                fighter = self.owner.components.get(ComponentType.FIGHTER)
                if fighter:
                    self.original_base_defense = self.owner.fighter.base_defense
                    self.owner.fighter.base_defense = max(0, self.owner.fighter.base_defense // 2)
                    
                    from game_messages import Message
                    results.append({
                        'message': Message(
                            f"The shield spell backfires on {self.owner.name}!",
                            (255, 100, 100)  # Red
                        )
                    })
                return results
        
        # Normal shield effect (player or non-backfired monster)
        fighter = self.owner.components.get(ComponentType.FIGHTER)
        if fighter:
            self.owner.fighter.base_defense += self.defense_bonus
            
            from game_messages import Message
            results.append({
                'message': Message(
                    f"{self.owner.name} is surrounded by a protective shield! (+{self.defense_bonus} defense)",
                    (100, 200, 255)  # Light blue
                )
            })
        
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        
        fighter = self.owner.components.get(ComponentType.FIGHTER)
        if fighter:
            if self.backfired and self.original_base_defense is not None:
                # Restore original base defense from backfire
                self.owner.fighter.base_defense = self.original_base_defense
                from game_messages import Message
                results.append({
                    'message': Message(
                        f"{self.owner.name}'s defense returns to normal.",
                        (200, 200, 200)  # Gray
                    )
                })
            else:
                # Remove normal shield bonus from base_defense
                self.owner.fighter.base_defense -= self.defense_bonus
                from game_messages import Message
                results.append({
                    'message': Message(
                        f"The protective shield around {self.owner.name} fades.",
                        (150, 150, 200)  # Light gray-blue
                    )
                })
        
        return results


class TauntedTargetEffect(StatusEffect):
    """Marks an entity as taunted - all hostiles will attack this target.
    
    Used by the 'Yo Mama' spell to redirect all aggro to a single entity.
    This creates tactical chaos and hilarious situations!
    """
    def __init__(self, duration: int, owner: 'Entity'):
        super().__init__("taunted", duration, owner)
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        # The joke message is handled by cast_yo_mama, not here
        # This just marks the entity as taunted
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        from game_messages import Message
        results.append({
            'message': Message(
                f"Monsters stop focusing on {self.owner.name}.",
                (200, 200, 200)  # Gray
            )
        })
        return results


class SlowedEffect(StatusEffect):
    """Makes the owner move slowly - only acts every 2nd turn.
    
    The entity skips turns when turn_counter is odd.
    This makes combat more strategic and gives the player/monsters time to reposition.
    
    Attributes:
        turn_counter (int): Tracks which turn we're on (even = act, odd = skip)
    """
    def __init__(self, duration: int, owner: 'Entity'):
        super().__init__("slowed", duration, owner)
        self.turn_counter = 0
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        from game_messages import Message
        results.append({
            'message': Message(
                f"{self.owner.name} moves sluggishly!",
                (150, 150, 255)  # Light blue
            )
        })
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        from game_messages import Message
        results.append({
            'message': Message(
                f"{self.owner.name} regains normal speed.",
                (200, 200, 200)  # Gray
            )
        })
        return results
    
    def process_turn_start(self) -> List[Dict[str, Any]]:
        """Check if entity should skip this turn."""
        results = []
        self.turn_counter += 1
        
        # Skip every other turn (odd turns)
        if self.turn_counter % 2 == 1:
            from game_messages import Message
            results.append({
                'message': Message(
                    f"{self.owner.name} is too slow to act!",
                    (100, 100, 200)  # Darker blue
                ),
                'skip_turn': True  # Signal to AI/player that this turn is skipped
            })
        
        return results


class ImmobilizedEffect(StatusEffect):
    """Prevents the owner from moving for X turns.
    
    The entity can still attack if enemies are adjacent, but cannot move.
    Used by the 'Glue' spell to create tactical zoning.
    """
    def __init__(self, duration: int, owner: 'Entity'):
        super().__init__("immobilized", duration, owner)
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        from game_messages import Message
        results.append({
            'message': Message(
                f"{self.owner.name} is stuck in place!",
                (139, 69, 19)  # Brown (glue color)
            )
        })
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        from game_messages import Message
        results.append({
            'message': Message(
                f"{self.owner.name} breaks free!",
                (200, 200, 200)  # Gray
            )
        })
        return results


class EnragedEffect(StatusEffect):
    """Makes the owner attack ANYONE nearby - friend or foe!
    
    Effects:
    - Deals 2x damage (damage multiplier)
    - Has 0.5x to-hit chance (wild, inaccurate swings)
    - AI attacks ANY adjacent entity, not just enemies
    - Creates absolute chaos!
    
    Attributes:
        damage_multiplier (float): Multiplier for damage (2.0 = double damage)
        to_hit_multiplier (float): Multiplier for to-hit (0.5 = half accuracy)
    """
    def __init__(self, duration: int, owner: 'Entity'):
        super().__init__("enraged", duration, owner)
        self.damage_multiplier = 2.0
        self.to_hit_multiplier = 0.5
        self.stored_faction = None
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        
        # Store original faction and make entity hostile to all
        faction = self.owner.components.get(ComponentType.FACTION)
        if faction:
            from components.faction import Faction
            self.stored_faction = self.owner.faction
            self.owner.faction = Faction.HOSTILE_ALL
        
        from game_messages import Message
        results.append({
            'message': Message(
                f"{self.owner.name} flies into a rage!",
                (255, 50, 50)  # Bright red
            )
        })
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        
        # Restore original faction
        if self.stored_faction is not None and self.owner.components.has(ComponentType.FACTION):
            self.owner.faction = self.stored_faction
        
        from game_messages import Message
        results.append({
            'message': Message(
                f"{self.owner.name} calms down.",
                (200, 200, 200)  # Gray
            )
        })
        return results


class StatusEffectManager:
    """Manages status effects for an entity."""
    def __init__(self, owner: 'Entity'):
        self.owner = owner
        self.active_effects: Dict[str, StatusEffect] = {}

    def add_effect(self, effect: StatusEffect) -> List[Dict[str, Any]]:
        results = []
        if effect.name in self.active_effects:
            # Replace existing effect if new one is added
            from game_messages import Message
            results.append({'message': Message(f"{self.owner.name}'s {effect.name} effect is refreshed.", (150, 200, 255))})
            self.active_effects[effect.name].remove() # Remove old effect
        
        self.active_effects[effect.name] = effect
        results.extend(effect.apply())
        return results

    def remove_effect(self, name: str) -> List[Dict[str, Any]]:
        if name in self.active_effects:
            effect = self.active_effects.pop(name)
            return effect.remove()
        return []

    def has_effect(self, name: str) -> bool:
        return name in self.active_effects

    def get_effect(self, name: str) -> Optional[StatusEffect]:
        return self.active_effects.get(name)

    def process_turn_start(self) -> List[Dict[str, Any]]:
        results = []
        for effect_name in list(self.active_effects.keys()): # Iterate over a copy
            effect = self.active_effects[effect_name]
            results.extend(effect.process_turn_start())
            if effect.duration <= 0 and effect_name in self.active_effects: # Check if effect was removed by itself
                results.extend(self.remove_effect(effect_name))
        return results

    def process_turn_end(self) -> List[Dict[str, Any]]:
        results = []
        expired_effects = []
        
        for effect_name in list(self.active_effects.keys()): # Iterate over a copy
            effect = self.active_effects[effect_name]
            turn_results = effect.process_turn_end()
            results.extend(turn_results)
            
            # Check if effect expired (process_turn_end already reduced duration)
            if effect.duration <= 0:
                expired_effects.append(effect_name)
        
        # Remove expired effects
        for effect_name in expired_effects:
            if effect_name in self.active_effects:  # Double-check it's still there
                results.extend(self.remove_effect(effect_name))
        
        return results