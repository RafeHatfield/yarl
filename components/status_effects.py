from typing import List, Dict, Any, TYPE_CHECKING, Optional
from message_builder import MessageBuilder as MB
from components.component_registry import ComponentType

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
        results.append({'message': MB.status_effect(f"{self.owner.name} becomes invisible!")})
        return results

    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        self.owner.invisible = False
        results.append({'message': MB.status_effect(f"{self.owner.name} is no longer invisible.")})
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
        ai = self.owner.get_component_optional(ComponentType.AI)
        if ai:
            from components.ai import ConfusedMonster
            self.previous_ai = self.owner.ai
            self.owner.ai = ConfusedMonster(self.previous_ai, self.duration)
            self.owner.ai.owner = self.owner
        
        from game_messages import Message
        results.append({
            'message': MB.status_effect(
                f"{self.owner.name} feels disoriented!"
            )
        })
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        
        # Restore previous AI
        if self.previous_ai and self.owner.components.has(ComponentType.AI):
            self.owner.ai = self.previous_ai
            self.previous_ai = None
        
        results.append({
            'message': MB.status_effect(
                f"{self.owner.name} is no longer disoriented."
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
        ai = self.owner.get_component_optional(ComponentType.AI)
        is_monster = ai is not None
        
        if is_monster:
            # 10% chance to backfire for monsters!
            from random import random
            if random() < 0.10:
                self.backfired = True
                # Halve base defense (defense property is read-only)
                fighter = self.owner.get_component_optional(ComponentType.FIGHTER)
                if fighter:
                    self.original_base_defense = self.owner.fighter.base_defense
                    self.owner.fighter.base_defense = max(0, self.owner.fighter.base_defense // 2)
                    
                    from game_messages import Message
                    results.append({
                        'message': MB.spell_fail(
                            f"The shield spell backfires on {self.owner.name}!"
                        )
                    })
                return results
        
        # Normal shield effect (player or non-backfired monster)
        fighter = self.owner.get_component_optional(ComponentType.FIGHTER)
        if fighter:
            self.owner.fighter.base_defense += self.defense_bonus
            
            from game_messages import Message
            results.append({
                'message': MB.status_effect(
                    f"{self.owner.name} is surrounded by a protective shield! (+{self.defense_bonus} defense)"
                )
            })
        
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        
        fighter = self.owner.get_component_optional(ComponentType.FIGHTER)
        if fighter:
            if self.backfired and self.original_base_defense is not None:
                # Restore original base defense from backfire
                self.owner.fighter.base_defense = self.original_base_defense
                from game_messages import Message
                results.append({
                    'message': MB.status_effect(
                        f"{self.owner.name}'s defense returns to normal."
                    )
                })
            else:
                # Remove normal shield bonus from base_defense
                self.owner.fighter.base_defense -= self.defense_bonus
                from game_messages import Message
                results.append({
                    'message': MB.status_effect(
                        f"The protective shield around {self.owner.name} fades."
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
            'message': MB.status_effect(
                f"Monsters stop focusing on {self.owner.name}."
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
            'message': MB.status_effect(
                f"{self.owner.name} moves sluggishly!"
            )
        })
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        from game_messages import Message
        results.append({
            'message': MB.status_effect(
                f"{self.owner.name} regains normal speed."
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
                'message': MB.status_effect(
                    f"{self.owner.name} is too slow to act!"
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
            'message': MB.status_effect(
                f"{self.owner.name} is stuck in place!"
            )
        })
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        from game_messages import Message
        results.append({
            'message': MB.status_effect(
                f"{self.owner.name} breaks free!"
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
        faction = self.owner.get_component_optional(ComponentType.FACTION)
        if faction:
            from components.faction import Faction
            self.stored_faction = self.owner.faction
            self.owner.faction = Faction.HOSTILE_ALL
        
        from game_messages import Message
        results.append({
            'message': MB.status_effect(
                f"{self.owner.name} flies into a rage!"
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
            'message': MB.status_effect(
                f"{self.owner.name} calms down."
            )
        })
        return results


class SpeedEffect(StatusEffect):
    """Doubles the owner's movement speed."""
    def __init__(self, duration: int, owner: 'Entity'):
        super().__init__("speed", duration, owner)
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        results.append({'message': MB.status_effect(f"{self.owner.name} feels incredibly fast!")})
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        results.append({'message': MB.status_effect(f"{self.owner.name} returns to normal speed.")})
        return results


class RegenerationEffect(StatusEffect):
    """Heals the owner over time."""
    def __init__(self, duration: int, owner: 'Entity', heal_per_turn: int = 1):
        super().__init__("regeneration", duration, owner)
        self.heal_per_turn = heal_per_turn
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        results.append({'message': MB.status_effect(f"{self.owner.name} begins regenerating!")})
        return results
    
    def process_turn_start(self) -> List[Dict[str, Any]]:
        results = super().process_turn_start()
        fighter = self.owner.get_component_optional(ComponentType.FIGHTER)
        if fighter and fighter.hp < fighter.max_hp:
            heal_amount = min(self.heal_per_turn, fighter.max_hp - fighter.hp)
            fighter.hp += heal_amount
            results.append({'message': MB.healing(f"{self.owner.name} regenerates {heal_amount} HP.")})
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        results.append({'message': MB.status_effect(f"{self.owner.name} stops regenerating.")})
        return results


class LevitationEffect(StatusEffect):
    """Allows the owner to float over ground hazards."""
    def __init__(self, duration: int, owner: 'Entity'):
        super().__init__("levitation", duration, owner)
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        self.owner.levitating = True
        results.append({'message': MB.status_effect(f"{self.owner.name} begins to levitate!")})
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        self.owner.levitating = False
        results.append({'message': MB.status_effect(f"{self.owner.name} gently floats back to the ground.")})
        return results


class ProtectionEffect(StatusEffect):
    """Provides a temporary AC bonus."""
    def __init__(self, duration: int, owner: 'Entity', ac_bonus: int = 4):
        super().__init__("protection", duration, owner)
        self.ac_bonus = ac_bonus
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        results.append({'message': MB.status_effect(f"{self.owner.name} is surrounded by a protective aura!")})
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        results.append({'message': MB.status_effect(f"{self.owner.name}'s protective aura fades.")})
        return results


class HeroismEffect(StatusEffect):
    """Provides temporary attack and damage bonuses."""
    def __init__(self, duration: int, owner: 'Entity', attack_bonus: int = 3, damage_bonus: int = 3):
        super().__init__("heroism", duration, owner)
        self.attack_bonus = attack_bonus
        self.damage_bonus = damage_bonus
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        results.append({'message': MB.status_effect(f"{self.owner.name} feels heroic!")})
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        results.append({'message': MB.status_effect(f"{self.owner.name}'s heroism fades.")})
        return results


class WeaknessEffect(StatusEffect):
    """Reduces the owner's damage output."""
    def __init__(self, duration: int, owner: 'Entity', damage_penalty: int = 2):
        super().__init__("weakness", duration, owner)
        self.damage_penalty = damage_penalty
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        results.append({'message': MB.warning(f"{self.owner.name} feels weak!")})
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        results.append({'message': MB.status_effect(f"{self.owner.name} feels stronger again.")})
        return results


class BlindnessEffect(StatusEffect):
    """Severely limits the owner's field of view."""
    def __init__(self, duration: int, owner: 'Entity', fov_radius: int = 1):
        super().__init__("blindness", duration, owner)
        self.fov_radius = fov_radius
        self.original_fov_radius = None
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        # Store original FOV radius if entity has fighter component
        fighter = self.owner.get_component_optional(ComponentType.FIGHTER)
        if fighter and hasattr(fighter, 'fov_radius'):
            self.original_fov_radius = fighter.fov_radius
        results.append({'message': MB.warning(f"{self.owner.name} is blinded!")})
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        results.append({'message': MB.status_effect(f"{self.owner.name} can see again.")})
        return results


class ParalysisEffect(StatusEffect):
    """Prevents the owner from taking any action."""
    def __init__(self, duration: int, owner: 'Entity'):
        super().__init__("paralysis", duration, owner)
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        self.owner.paralyzed = True
        results.append({'message': MB.warning(f"{self.owner.name} is paralyzed!")})
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        self.owner.paralyzed = False
        results.append({'message': MB.status_effect(f"{self.owner.name} can move again.")})
        return results


class IdentifyModeEffect(StatusEffect):
    """Automatically identifies 1 random item per turn for the duration.
    
    Used by the Identify scroll - grants temporary identification powers.
    At the start of each turn, automatically identifies 1 random unidentified item.
    """
    
    def __init__(self, duration: int, owner: 'Entity'):
        super().__init__("identify_mode", duration, owner)
    
    def apply(self) -> List[Dict[str, Any]]:
        """Apply the identification buff."""
        results = super().apply()
        results.append({
            'message': MB.status_effect(
                f"✨ {self.owner.name}'s mind expands with knowledge! "
                f"Items will be identified automatically for {self.duration} turns."
            )
        })
        return results
    
    def process_turn_start(self) -> List[Dict[str, Any]]:
        """Automatically identify 1 random unidentified item at turn start."""
        results = super().process_turn_start()
        
        # Find all unidentified items in inventory
        if not hasattr(self.owner, 'inventory') or not self.owner.inventory:
            return results
        
        unidentified_items = []
        for item in self.owner.inventory.items:
            item_comp = getattr(item, 'item', None)
            if item_comp and hasattr(item_comp, 'identified') and not item_comp.identified:
                unidentified_items.append(item)
        
        # If there are unidentified items, identify one randomly
        if unidentified_items:
            import random
            item_to_identify = random.choice(unidentified_items)
            item_comp = item_to_identify.item
            old_appearance = item_comp.appearance if hasattr(item_comp, 'appearance') else "mysterious item"
            
            # Get entities list for global sync (try multiple sources)
            entities = None
            if hasattr(self.owner, 'game_map') and hasattr(self.owner.game_map, 'entities'):
                entities = self.owner.game_map.entities
            # Fallback: pass None, identification will still work for this item
            
            # Identify the item (and all others of the same type)
            was_unidentified = item_comp.identify(entities=entities)
            
            if was_unidentified:
                results.append({
                    'message': MB.item_pickup(
                        f"🔍 You identify the {old_appearance} as {item_to_identify.name}!"
                    )
                })
        else:
            # No more unidentified items - effect can end early
            results.append({
                'message': MB.info("🔍 All items identified! Identify mode ends.")
            })
            self.duration = 0  # End effect early
        
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        """Remove the identification buff."""
        results = super().remove()
        results.append({
            'message': MB.status_effect(
                f"{self.owner.name}'s identification powers fade."
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
        
        # Check for ring immunities
        from components.component_registry import ComponentType
        equipment = self.owner.equipment if hasattr(self.owner, 'equipment') else None
        if equipment:
            for ring in [equipment.left_ring, equipment.right_ring]:
                if ring and ring.components.has(ComponentType.RING):
                    if ring.ring.provides_immunity(effect.name):
                        results.append({
                            'message': MB.status_effect(
                                f"{self.owner.name}'s ring protects them from {effect.name}!"
                            )
                        })
                        return results  # Immunity blocks the effect
        
        if effect.name in self.active_effects:
            # Replace existing effect if new one is added
            results.append({'message': MB.status_effect(f"{self.owner.name}'s {effect.name} effect is refreshed.")})
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
        
        # Process ring effects first (Ring of Regeneration)
        from components.component_registry import ComponentType
        equipment = self.owner.equipment if hasattr(self.owner, 'equipment') else None
        if equipment:
            for ring in [equipment.left_ring, equipment.right_ring]:
                if ring and ring.components.has(ComponentType.RING):
                    ring_results = ring.ring.process_turn(self.owner)
                    results.extend(ring_results)
        
        # Then process status effects
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