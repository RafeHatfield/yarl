from typing import List, Dict, Any, TYPE_CHECKING, Optional
from message_builder import MessageBuilder as MB
from components.component_registry import ComponentType

if TYPE_CHECKING:
    pass

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

    def process_turn_start(self, entities=None) -> List[Dict[str, Any]]:
        """Process effect at the start of the owner's turn.
        
        Args:
            entities: Optional list of all game entities (for effects that need global access)
        
        Returns:
            List of result dictionaries
        """
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
    
    def process_turn_start(self, entities=None) -> List[Dict[str, Any]]:
        """Check if entity should skip this turn.
        
        Args:
            entities: Optional list of all game entities (not used by this effect)
        
        Returns:
            List of result dictionaries
        """
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


class EngulfedEffect(StatusEffect):
    """Phase 19: Slime Engulf - Movement penalty that persists while adjacent to slimes.
    
    Identity: Slimes envelope targets; being adjacent is dangerous.
    Creates "break contact" decision for players.
    
    Mechanics:
    - Applies on successful slime hit (no RNG)
    - Slows movement (acts every 2nd turn, like SlowedEffect)
    - Duration DOES NOT decay while adjacent to ANY slime
    - Duration decays normally when not adjacent to slimes
    - Refresh to max duration if hit again while already engulfed
    
    Attributes:
        turn_counter (int): Tracks turn parity for movement slowdown
        max_duration (int): Maximum duration for refresh logic
        was_adjacent_last_turn (bool): Tracks adjacency for messaging
    """
    def __init__(self, duration: int, owner: 'Entity'):
        super().__init__("engulfed", duration, owner)
        self.turn_counter = 0
        self.max_duration = duration
        self.was_adjacent_last_turn = True  # Assume true on first application
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        results.append({
            'message': MB.status_effect(
                f"{self.owner.name} is engulfed by slime!"
            )
        })
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        results.append({
            'message': MB.status_effect(
                f"{self.owner.name} pulls free of the slime's grasp!"
            )
        })
        return results
    
    def process_turn_start(self, entities=None) -> List[Dict[str, Any]]:
        """Process engulf at turn start - check adjacency and apply movement penalty.
        
        Args:
            entities: List of all game entities (needed for adjacency check)
        
        Returns:
            List of result dictionaries
        """
        results = []
        
        # Check if owner is adjacent to any slime
        adjacent_to_slime = self._is_adjacent_to_slime(entities)
        
        # If adjacent to slime, refresh duration to max and don't decay
        if adjacent_to_slime:
            self.duration = self.max_duration
            # Don't spam message if already adjacent
            if not self.was_adjacent_last_turn:
                results.append({
                    'message': MB.status_effect(
                        f"{self.owner.name} is still engulfed by slime!"
                    )
                })
            self.was_adjacent_last_turn = True
        else:
            # Not adjacent - show message first time breaking contact
            if self.was_adjacent_last_turn:
                results.append({
                    'message': MB.status_effect(
                        f"{self.owner.name} starts pulling free of the slime!"
                    )
                })
            self.was_adjacent_last_turn = False
        
        # Apply movement penalty (slow - skip every other turn)
        self.turn_counter += 1
        if self.turn_counter % 2 == 1:
            results.append({
                'message': MB.status_effect(
                    f"{self.owner.name} moves sluggishly through the slime!"
                ),
                'skip_turn': True  # Signal to AI/player that this turn is skipped
            })
        
        return results
    
    def process_turn_end(self) -> List[Dict[str, Any]]:
        """Process at turn end - decay duration if not adjacent to slime.
        
        Returns:
            List of result dictionaries
        """
        # Only decay if not adjacent to slime
        if not self.was_adjacent_last_turn:
            self.duration -= 1
        # Don't call super().process_turn_end() as we handle duration manually
        return []
    
    def _is_adjacent_to_slime(self, entities) -> bool:
        """Check if owner is adjacent to any slime.
        
        Args:
            entities: List of all game entities
        
        Returns:
            bool: True if adjacent to at least one slime
        """
        if not entities or not self.owner:
            return False
        
        owner_x, owner_y = self.owner.x, self.owner.y
        
        for entity in entities:
            if entity == self.owner:
                continue
            
            # Check if entity is a slime (has special_abilities with 'engulf')
            if (hasattr(entity, 'special_abilities') and 
                entity.special_abilities and 
                'engulf' in entity.special_abilities):
                
                # Check adjacency (Chebyshev distance <= 1)
                dx = abs(entity.x - owner_x)
                dy = abs(entity.y - owner_y)
                if max(dx, dy) <= 1 and (dx != 0 or dy != 0):  # Adjacent but not same tile
                    return True
        
        return False


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


class LightningReflexesEffect(StatusEffect):
    """Temporarily boosts combat speed bonus (Phase 5).
    
    Grants +50% bonus attack chance for the duration, overriding any
    equipment-based speed bonuses. Reverts to normal when effect ends.
    """
    def __init__(self, duration: int, owner: 'Entity', speed_bonus: float = 0.50):
        super().__init__("lightning_reflexes", duration, owner)
        self.speed_bonus = speed_bonus
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        
        # Get or create speed bonus tracker
        from components.component_registry import ComponentType
        speed_tracker = self.owner.get_component_optional(ComponentType.SPEED_BONUS_TRACKER)
        
        if not speed_tracker:
            # Create new tracker for this entity
            from components.speed_bonus_tracker import SpeedBonusTracker
            speed_tracker = SpeedBonusTracker(speed_bonus_ratio=0.0)
            self.owner.speed_bonus_tracker = speed_tracker
            speed_tracker.owner = self.owner
            self.owner.components.add(ComponentType.SPEED_BONUS_TRACKER, speed_tracker)
        
        # Set temporary bonus (overrides equipment bonus during effect)
        speed_tracker.set_temporary_bonus(self.speed_bonus)
        
        results.append({'message': MB.status_effect(
            f"{self.owner.name} feels lightning-fast reflexes! (+{int(self.speed_bonus * 100)}% speed)"
        )})
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        
        # Clear temporary bonus
        from components.component_registry import ComponentType
        speed_tracker = self.owner.get_component_optional(ComponentType.SPEED_BONUS_TRACKER)
        if speed_tracker:
            speed_tracker.clear_temporary_bonus()
        
        results.append({'message': MB.status_effect(
            f"{self.owner.name}'s lightning reflexes fade."
        )})
        return results


class SluggishEffect(StatusEffect):
    """Applies a negative speed bonus that stacks with equipment bonuses (Phase 7).
    
    Unlike SlowedEffect which skips turns, SluggishEffect reduces the
    speed_bonus_ratio through the SpeedBonusTracker's debuff system.
    This means affected entities get fewer bonus attacks, not fewer turns.
    
    Attributes:
        speed_penalty (float): Speed penalty as a ratio (e.g., 0.25 for -25% speed)
    
    Example:
        - Entity with +50% speed bonus from equipment
        - SluggishEffect applies -25% penalty
        - Net speed bonus = 50% - 25% = 25%
    """
    def __init__(self, duration: int, owner: 'Entity', speed_penalty: float = 0.25):
        super().__init__("sluggish", duration, owner)
        self.speed_penalty = speed_penalty
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        
        # Get or create speed bonus tracker
        from components.component_registry import ComponentType
        speed_tracker = self.owner.get_component_optional(ComponentType.SPEED_BONUS_TRACKER)
        
        if not speed_tracker:
            # Create new tracker for this entity
            from components.speed_bonus_tracker import SpeedBonusTracker
            speed_tracker = SpeedBonusTracker(speed_bonus_ratio=0.0)
            self.owner.speed_bonus_tracker = speed_tracker
            speed_tracker.owner = self.owner
            self.owner.components.add(ComponentType.SPEED_BONUS_TRACKER, speed_tracker)
        
        # Apply debuff (stacks additively with equipment bonuses)
        speed_tracker.add_debuff(self.speed_penalty, "sluggish")
        
        results.append({'message': MB.warning(
            f"{self.owner.name} feels sluggish... (-{int(self.speed_penalty * 100)}% speed)"
        )})
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        
        # Remove debuff
        from components.component_registry import ComponentType
        speed_tracker = self.owner.get_component_optional(ComponentType.SPEED_BONUS_TRACKER)
        if speed_tracker:
            speed_tracker.remove_debuff(self.speed_penalty, "sluggish")
        
        results.append({'message': MB.status_effect(
            f"{self.owner.name} no longer feels sluggish."
        )})
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
    
    def process_turn_start(self, entities=None) -> List[Dict[str, Any]]:
        """Regenerate HP at turn start.
        
        Args:
            entities: Optional list of all game entities (not used by this effect)
        
        Returns:
            List of result dictionaries
        """
        results = super().process_turn_start(entities=entities)
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
    
    def process_turn_start(self, entities=None) -> List[Dict[str, Any]]:
        """Automatically identify 1 random unidentified item at turn start.
        
        Args:
            entities: List of all game entities (needed for global identification sync)
        
        Returns:
            List of result dictionaries
        """
        results = super().process_turn_start(entities=entities)
        
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
            
            # Identify the item (and all others of the same type)
            # Pass entities list for global sync
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


class FearEffect(StatusEffect):
    """Makes the owner flee from enemies in terror.
    
    Used by the Fear scroll - causes enemies to run away from threats.
    Affected creatures will attempt to move away from the player.
    """
    
    def __init__(self, duration: int, owner: 'Entity'):
        super().__init__("fear", duration, owner)
        self.previous_ai = None
    
    def apply(self) -> List[Dict[str, Any]]:
        """Apply the fear effect."""
        results = super().apply()
        
        # Store the current AI and replace with fleeing behavior
        # We'll modify the AI to flee in the actual AI processing
        results.append({
            'message': MB.warning(f"{self.owner.name} flees in terror!")
        })
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        """Remove the fear effect."""
        results = super().remove()
        results.append({
            'message': MB.status_effect(f"{self.owner.name} is no longer afraid.")
        })
        return results


class DetectMonsterEffect(StatusEffect):
    """Allows the owner to sense the presence and location of all monsters.
    
    Used by the Detect Monster scroll - grants temporary monster detection.
    The player can see all monsters on the current level regardless of FOV.
    """
    
    def __init__(self, duration: int, owner: 'Entity'):
        super().__init__("detect_monster", duration, owner)
    
    def apply(self) -> List[Dict[str, Any]]:
        """Apply the detect monster buff."""
        results = super().apply()
        # Set a flag on the owner to indicate they can detect monsters
        self.owner.detecting_monsters = True
        results.append({
            'message': MB.status_effect(
                f"👁️ {self.owner.name} senses the presence of all monsters for {self.duration} turns!"
            )
        })
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        """Remove the detect monster buff."""
        results = super().remove()
        self.owner.detecting_monsters = False
        results.append({
            'message': MB.status_effect(
                f"{self.owner.name}'s monster detection fades."
            )
        })
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 10: FACTION MANIPULATION STATUS EFFECTS
# ═══════════════════════════════════════════════════════════════════════════════


class EnragedAgainstFactionEffect(StatusEffect):
    """Makes the owner attack a specific faction above all other targets.
    
    Phase 10: Used by Scroll of Unreasonable Aggravation.
    
    The enraged monster will prioritize attacking members of the target faction
    over all others (including the player), until death. The effect is permanent
    (until death) and cannot be removed by time.
    
    Attributes:
        target_faction (Faction): The faction this monster is enraged against
    """
    def __init__(self, owner: 'Entity', target_faction: 'Faction'):
        # Duration of -1 means permanent until death
        super().__init__("enraged_against_faction", -1, owner)
        self.target_faction = target_faction
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        from components.faction import get_faction_display_name
        
        faction_name = get_faction_display_name(self.target_faction)
        results.append({
            'message': MB.custom(
                f"📜 {self.owner.name} is consumed by unreasonable aggravation toward {faction_name}!",
                (255, 100, 50)  # Orange-red for anger
            )
        })
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        # This effect is permanent - only removed on death
        results = super().remove()
        return results
    
    def process_turn_end(self) -> List[Dict[str, Any]]:
        # Override to prevent duration decrement (permanent effect)
        return []


class PlagueOfRestlessDeathEffect(StatusEffect):
    """Plague that causes reanimation as a Revenant Zombie on death.
    
    Phase 10: Plague of Restless Death mechanics.
    
    This plague:
    - Only affects "corporeal_flesh" creatures (tagged appropriately)
    - Deals negligible damage over time (cannot kill; stops at 1 HP)
    - If victim dies while infected, they reanimate as Revenant Zombie
    
    The reanimation creates a zombie with:
    - new_max_hp = original_max_hp * 2
    - new_damage = floor(original_damage * 0.75)
    - new_accuracy = floor(original_accuracy * 0.75)
    - new_evasion = floor(original_evasion * 0.5)
    - Weapons dropped, armor kept, faction set to UNDEAD
    
    Attributes:
        damage_per_turn (int): Damage dealt per turn (default 1)
        original_stats (dict): Stored stats for reanimation calculation
    """
    def __init__(self, duration: int, owner: 'Entity', damage_per_turn: int = 1):
        super().__init__("plague_of_restless_death", duration, owner)
        self.damage_per_turn = damage_per_turn
        # Store original stats on application for revenant calculation
        self.original_stats = None
        self._stats_captured = False
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        
        # Capture original stats for revenant zombie calculation
        self._capture_original_stats()
        
        results.append({
            'message': MB.custom(
                f"☠️ {self.owner.name} is infected with the Plague of Restless Death!",
                (150, 200, 50)  # Sickly green
            )
        })
        
        # Queue VFX
        try:
            from visual_effects import show_effect_vfx
            from visual_effect_queue import EffectType
            if hasattr(self.owner, 'x') and hasattr(self.owner, 'y'):
                show_effect_vfx(self.owner.x, self.owner.y, EffectType.PLAGUE, self.owner)
        except ImportError:
            pass  # VFX optional
        
        # Phase 11: If player was infected by a monster, register plague_carrier trait
        # The "infector" would be tracked separately, but for now we just note
        # that the player experienced plague (which unlocks Tier 3 for plague carriers)
        
        return results
    
    def _capture_original_stats(self) -> None:
        """Capture the entity's original stats for revenant calculation."""
        if self._stats_captured:
            return
        
        fighter = self.owner.get_component_optional(ComponentType.FIGHTER)
        if fighter:
            self.original_stats = {
                'max_hp': fighter.max_hp,
                'damage_min': getattr(fighter, 'damage_min', 0),
                'damage_max': getattr(fighter, 'damage_max', 0),
                'accuracy': getattr(fighter, 'accuracy', 2),
                'evasion': getattr(fighter, 'evasion', 1),
                'defense': fighter.base_defense,
                'power': fighter.power,
                'name': self.owner.name,
                'char': self.owner.char,
                'color': self.owner.color,
            }
            self._stats_captured = True
    
    def process_turn_start(self, entities=None) -> List[Dict[str, Any]]:
        """Deal plague damage, but never reduce below 1 HP.
        
        Args:
            entities: List of all game entities
        
        Returns:
            List of result dictionaries
        """
        results = super().process_turn_start(entities=entities)
        
        fighter = self.owner.get_component_optional(ComponentType.FIGHTER)
        if fighter and fighter.hp > 1:
            # Deal damage but don't kill
            actual_damage = min(self.damage_per_turn, fighter.hp - 1)
            if actual_damage > 0:
                fighter.hp -= actual_damage
                results.append({
                    'message': MB.custom(
                        f"☠️ The plague ravages {self.owner.name} for {actual_damage} damage!",
                        (150, 200, 50)  # Sickly green
                    )
                })
        
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        results.append({
            'message': MB.status_effect(
                f"{self.owner.name} is no longer infected with the plague."
            )
        })
        return results
    
    def get_revenant_stats(self) -> Optional[Dict[str, Any]]:
        """Get the calculated stats for a revenant zombie.
        
        Called when the infected entity dies to create the revenant.
        
        Returns:
            Dict with transformed stats, or None if stats weren't captured
        """
        if not self.original_stats:
            return None
        
        import math
        
        return {
            'max_hp': self.original_stats['max_hp'] * 2,
            'hp': self.original_stats['max_hp'] * 2,  # Full HP on reanimate
            'damage_min': math.floor(self.original_stats['damage_min'] * 0.75),
            'damage_max': math.floor(self.original_stats['damage_max'] * 0.75),
            'accuracy': math.floor(self.original_stats['accuracy'] * 0.75),
            'evasion': math.floor(self.original_stats['evasion'] * 0.5),
            'defense': self.original_stats['defense'],
            'power': self.original_stats['power'],
            'original_name': self.original_stats['name'],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 19: ORC CHIEFTAIN ABILITIES
# ═══════════════════════════════════════════════════════════════════════════════

class RallyBuffEffect(StatusEffect):
    """Phase 19: Orc Chieftain Rally Cry buff.
    
    Applied to orc allies within rally radius when chieftain uses Rally Cry.
    Provides:
    - +1 to-hit bonus
    - +1 damage bonus
    - AI directive to prioritize chieftain's target
    
    Rally ends immediately when the chieftain takes damage (first time).
    """
    def __init__(self, duration: int, owner: 'Entity', chieftain_id: int, 
                 to_hit_bonus: int = 1, damage_bonus: int = 1):
        super().__init__("rally_buff", duration, owner)
        self.chieftain_id = chieftain_id  # Track which chieftain applied this
        self.to_hit_bonus = to_hit_bonus
        self.damage_bonus = damage_bonus
        self.directive_target_id = None  # Set by rally system
        # Tag for cleansing: rally cleanses fear/morale debuffs
        self.tags = []
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        # Don't spam per-orc messages - chieftain rally message is enough
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        # Clear AI directive when rally ends
        if hasattr(self.owner, 'ai') and hasattr(self.owner.ai, 'rally_directive_target_id'):
            self.owner.ai.rally_directive_target_id = None
        return results


class SonicBellowDebuffEffect(StatusEffect):
    """Phase 19: Orc Chieftain Sonic Bellow debuff.
    
    Applied to player when chieftain drops below 50% HP (one-time).
    Provides:
    - -1 to-hit penalty for 2 turns
    
    Deterministic, no RNG.
    """
    def __init__(self, duration: int, owner: 'Entity', to_hit_penalty: int = 1):
        super().__init__("sonic_bellow_debuff", duration, owner)
        self.to_hit_penalty = to_hit_penalty
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        results.append({'message': MB.warning(f"{self.owner.name}'s ears ring from the bellow!")})
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        results.append({'message': MB.status_effect(f"{self.owner.name} recovers from the bellow.")})
        return results


class CripplingHexEffect(StatusEffect):
    """Phase 19: Orc Shaman Crippling Hex debuff.
    
    Applied to player by Orc Shaman (cooldown-based ability).
    Provides:
    - -1 to-hit penalty
    - -1 AC penalty
    
    Duration: config-driven (default 5 turns)
    Cooldown: config-driven (default 10 turns)
    Deterministic, no RNG.
    """
    def __init__(self, duration: int, owner: 'Entity', to_hit_delta: int = -1, ac_delta: int = -1):
        super().__init__("crippling_hex", duration, owner)
        self.to_hit_delta = to_hit_delta  # Negative value = penalty
        self.ac_delta = ac_delta          # Negative value = penalty
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        results.append({
            'message': MB.warning(f"🔮 A dark hex settles over {self.owner.name}!")
        })
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        results.append({
            'message': MB.status_effect(f"The hex on {self.owner.name} fades away.")
        })
        return results


class DissonantChantEffect(StatusEffect):
    """Phase 19: Orc Shaman Chant of Dissonance (movement tax).
    
    Applied to player by Orc Shaman while channeling (interruptible by damage).
    Provides:
    - +1 energy cost per movement (movement tax)
    
    Duration: config-driven (default 3 turns, while channeling)
    Cooldown: config-driven (default 15 turns)
    Chant is interruptible: ends immediately if shaman takes damage.
    Deterministic, no RNG.
    """
    def __init__(self, duration: int, owner: 'Entity', move_energy_tax: int = 1):
        super().__init__("dissonant_chant", duration, owner)
        self.move_energy_tax = move_energy_tax  # Additional energy cost per move
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        results.append({
            'message': MB.warning(f"🎵 A dissonant chant assaults {self.owner.name}'s senses!")
        })
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        results.append({
            'message': MB.status_effect(f"The chant affecting {self.owner.name} ceases.")
        })
        
        # Reset alternating movement block toggle when chant ends
        # This ensures no sticky block state after effect expires/interrupts
        # Note: Effect refresh (shaman re-casts chant) also calls remove(), resetting toggle
        # This gives player a "free" allowed move after refresh, but player trades this
        # for extended chant duration - minor edge case, acceptable behavior
        if hasattr(self.owner, '_chant_move_block_next'):
            self.owner._chant_move_block_next = False
        
        return results


class WardAgainstDrainEffect(StatusEffect):
    """Phase 19: Temporary immunity to wraith life drain.
    
    Applied by scroll_ward_against_drain consumable.
    Blocks life drain heals from wraith hits completely.
    Duration: 10 turns (from scroll config).
    """
    def __init__(self, duration: int, owner: 'Entity'):
        super().__init__(name='ward_against_drain', duration=duration, owner=owner)
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        results.append({'message': MB.status_effect("A pale ward surrounds you, repelling life drain!")})
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        results.append({'message': MB.status_effect("The ward against drain fades away.")})
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 19: LICH (ARCH-NECROMANCER) ABILITIES
# ═══════════════════════════════════════════════════════════════════════════════

class ChargingSoulBoltEffect(StatusEffect):
    """Phase 19: Lich is charging Soul Bolt (telegraph turn).
    
    Applied to lich when it starts charging Soul Bolt.
    Next turn, if lich still has LOS + range to player, Soul Bolt fires.
    This gives the player 1 turn to react (retreat, use Soul Ward scroll, etc.)
    
    Duration: 2 turns because:
    - Turn 1 (apply): duration=2
    - End of turn 1: process_turn_end() → duration=1
    - Turn 2 (resolve): is_charging still True, resolve Soul Bolt
    - End of turn 2: process_turn_end() → duration=0, removed
    """
    def __init__(self, owner: 'Entity'):
        super().__init__(name='charging_soul_bolt', duration=2, owner=owner)
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        results.append({'message': MB.combat(f"⚡ The {self.owner.name} begins channeling dark energy!")})
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        # No message on natural expiry - Soul Bolt resolution will message
        return results


class SoulWardEffect(StatusEffect):
    """Phase 19: Soul Ward - Reshapes Soul Bolt damage into DOT.
    
    Applied by scroll_soul_ward consumable.
    When Soul Bolt hits while this is active:
    - Reduces upfront damage by 70% (rounded up)
    - Converts prevented damage to Soul Burn DOT over 3 turns
    Duration: 10 turns.
    """
    def __init__(self, duration: int, owner: 'Entity'):
        super().__init__(name='soul_ward', duration=duration, owner=owner)
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        results.append({'message': MB.status_effect("🛡️ A spectral ward envelops you, protecting your soul!")})
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        results.append({'message': MB.status_effect("The soul ward dissipates.")})
        return results


class SoulBurnEffect(StatusEffect):
    """Phase 19: Soul Burn DOT - Residual damage from Soul Ward conversion.
    
    Applied when Soul Ward converts Soul Bolt damage to DOT.
    Deals deterministic damage over 3 turns (total_damage split evenly, remainder on last tick).
    """
    def __init__(self, total_damage: int, owner: 'Entity'):
        super().__init__(name='soul_burn', duration=3, owner=owner)
        self.total_damage = total_damage
        self.damage_per_turn = total_damage // 3
        self.remainder = total_damage % 3
        self.ticks_remaining = 3
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        results.append({'message': MB.status_effect(f"🔥 {self.owner.name} is burning with soul fire!")})
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        results.append({'message': MB.status_effect(f"The soul burn affecting {self.owner.name} fades.")})
        return results
    
    def process_turn_start(self, entities=None, state_manager=None) -> List[Dict[str, Any]]:
        """Tick Soul Burn damage at start of turn.
        
        Args:
            entities: Optional list of all game entities (not used by this effect)
            state_manager: Optional state manager for death finalization (CRITICAL)
        
        Returns:
            List of result dictionaries including death results if applicable
        """
        results = []
        
        # Calculate damage for this tick
        damage_this_tick = self.damage_per_turn
        if self.ticks_remaining == 1:
            # Last tick gets remainder
            damage_this_tick += self.remainder
        
        if damage_this_tick > 0:
            # Add message about burn damage BEFORE applying damage
            results.append({'message': MB.combat(f"🔥 {self.owner.name} takes {damage_this_tick} soul burn damage!")})
            
            # CRITICAL: Route through damage_service to ensure death finalization
            # This prevents "0 HP undead limbo" bug where entities hit 0 HP but don't die
            if state_manager:
                from services.damage_service import apply_damage
                
                damage_results = apply_damage(
                    state_manager=state_manager,
                    target_entity=self.owner,
                    amount=damage_this_tick,
                    cause="soul_burn_dot",
                    attacker_entity=None,  # DOT has no attacker
                    damage_type="necrotic",
                    allow_xp=False,  # DOT doesn't award XP
                )
                results.extend(damage_results)
            else:
                # FALLBACK: state_manager not available (unit tests, edge cases)
                # Use direct Fighter.take_damage() but log LOUD warning if death occurs
                fighter = self.owner.get_component_optional(ComponentType.FIGHTER)
                if fighter:
                    damage_results = fighter.take_damage(damage_this_tick)
                    
                    # Check if death occurred without finalization
                    for result in damage_results:
                        if result.get('dead'):
                            logger.error(
                                f"⚠️ DEATH_WITHOUT_FINALIZATION: Soul Burn killed {self.owner.name} "
                                f"but state_manager=None - death will NOT be finalized! "
                                f"This is OK for unit tests, but a BUG in production."
                            )
                    
                    results.extend(damage_results)
        
        self.ticks_remaining -= 1
        
        return results


class PoisonEffect(StatusEffect):
    """Phase 20A: Poison DOT - Damage over time from venomous attacks.
    
    Applied by monsters with poison_attack ability (e.g., cave_spider).
    
    Design decisions:
    - Duration: 6 turns
    - Damage: 1 per tick (6 total damage)
    - Stacking: NON-STACKING (reapplication refreshes duration only)
    - Resistance: poison_resistance_pct reduces damage per tick (rounds down)
    
    This is the canonical DOT model for future effects.
    
    Metrics semantics (IMPORTANT - reference for all DOTs):
    - poison_applications: Count of add_effect() calls (including refreshes)
    - poison_ticks_processed: Count of ALL ticks (including 0-damage ticks from resistance)
    - poison_damage_dealt: Actual damage dealt (after resistance)
    - poison_kills: Kills where poison dealt the killing blow
    - Metrics track damage TO THE EFFECT OWNER (typically player for monster abilities)
    
    Death finalization:
    - With state_manager: Routes through damage_service, proper finalization
    - Without state_manager: CLAMPS TO NON-LETHAL (min 1 HP) to prevent limbo deaths
    """
    
    # Class-level constants for easy tuning
    DEFAULT_DURATION = 6
    DEFAULT_DAMAGE_PER_TICK = 1
    
    def __init__(self, owner: 'Entity', duration: int = None, damage_per_tick: int = None):
        """Initialize poison effect.
        
        Args:
            owner: Entity afflicted by poison
            duration: Duration in turns (default: 6)
            damage_per_tick: Damage per tick before resistance (default: 1)
        """
        actual_duration = duration if duration is not None else self.DEFAULT_DURATION
        super().__init__(name='poison', duration=actual_duration, owner=owner)
        self.damage_per_tick = damage_per_tick if damage_per_tick is not None else self.DEFAULT_DAMAGE_PER_TICK
        self.total_damage_dealt = 0
        self.ticks_processed = 0
    
    def apply(self) -> List[Dict[str, Any]]:
        """Apply poison effect with message."""
        results = super().apply()
        results.append({'message': MB.status_effect(f"☠️ {self.owner.name} is poisoned!")})
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        """Remove poison effect with message."""
        results = super().remove()
        results.append({'message': MB.status_effect(f"The poison affecting {self.owner.name} wears off.")})
        return results
    
    def process_turn_start(self, entities=None, state_manager=None) -> List[Dict[str, Any]]:
        """Tick poison damage at start of turn.
        
        Args:
            entities: Optional list of all game entities (not used by this effect)
            state_manager: Optional state manager for death finalization (CRITICAL)
        
        Returns:
            List of result dictionaries including death results if applicable
        
        CRITICAL: Without state_manager, damage is CLAMPED TO NON-LETHAL (min 1 HP)
        to prevent limbo deaths. This is intentional - only unit tests should run
        without state_manager, and they shouldn't cause death finalization issues.
        """
        from services.scenario_metrics import get_active_metrics_collector
        
        results = []
        collector = get_active_metrics_collector()
        
        # Calculate damage after resistance
        damage_this_tick = self._calculate_damage_after_resistance()
        
        # ALWAYS track ticks (including 0-damage ticks from full resistance)
        # This is semantic: "how many times did poison try to tick?"
        self.ticks_processed += 1
        if collector:
            collector.increment('poison_ticks_processed')
        
        if damage_this_tick > 0:
            # Add message about poison damage BEFORE applying damage
            results.append({'message': MB.combat(f"☠️ {self.owner.name} takes {damage_this_tick} poison damage!")})
            
            # CRITICAL: Route through damage_service to ensure death finalization
            if state_manager:
                from services.damage_service import apply_damage
                
                damage_results = apply_damage(
                    state_manager=state_manager,
                    target_entity=self.owner,
                    amount=damage_this_tick,
                    cause="poison_dot",
                    attacker_entity=None,  # DOT has no attacker
                    damage_type="poison",
                    allow_xp=False,  # DOT doesn't award XP
                )
                results.extend(damage_results)
                
                # Track damage metric
                if collector:
                    collector.increment('poison_damage_dealt', damage_this_tick)
                    
                    # Check if this tick killed the entity
                    for result in damage_results:
                        if result.get('dead'):
                            collector.increment('poison_kills')
            else:
                # FALLBACK: state_manager not available (unit tests, edge cases)
                # CLAMP TO NON-LETHAL to prevent death without finalization
                from logger_config import get_logger
                logger = get_logger(__name__)
                
                fighter = self.owner.get_component_optional(ComponentType.FIGHTER)
                if fighter:
                    current_hp = fighter.hp
                    
                    # Check if this damage would be lethal
                    if current_hp - damage_this_tick <= 0:
                        # CLAMP: Only deal damage down to 1 HP
                        clamped_damage = max(0, current_hp - 1)
                        
                        logger.error(
                            f"⚠️ POISON_LETHAL_CLAMP: Poison would kill {self.owner.name} "
                            f"(HP={current_hp}, damage={damage_this_tick}) but state_manager=None. "
                            f"CLAMPING to {clamped_damage} damage (leaving 1 HP). "
                            f"This prevents DEATH_WITHOUT_FINALIZATION. "
                            f"In production, state_manager MUST be provided for DOT effects."
                        )
                        
                        if clamped_damage > 0:
                            damage_results = fighter.take_damage(clamped_damage, damage_type="poison")
                            results.extend(damage_results)
                            if collector:
                                collector.increment('poison_damage_dealt', clamped_damage)
                        # else: No damage dealt, entity survives at 1 HP
                    else:
                        # Non-lethal damage - safe to apply
                        damage_results = fighter.take_damage(damage_this_tick, damage_type="poison")
                        results.extend(damage_results)
                        if collector:
                                collector.increment('poison_damage_dealt', damage_this_tick)
            
            # Track effect-level damage counter
            self.total_damage_dealt += damage_this_tick
        
        return results
    
    def _calculate_damage_after_resistance(self) -> int:
        """Calculate poison damage after applying resistance.
        
        Resistance reduces damage per tick (not duration).
        Damage = base_damage * (1 - resistance_pct/100), rounded down.
        Minimum 0 damage (complete immunity at 100% resistance).
        
        Returns:
            Final damage after resistance
        """
        base_damage = self.damage_per_tick
        
        # Get poison resistance from entity
        resistance_pct = getattr(self.owner, 'poison_resistance_pct', 0)
        
        # Also check fighter component for resistance
        fighter = self.owner.get_component_optional(ComponentType.FIGHTER)
        if fighter and hasattr(fighter, 'poison_resistance_pct'):
            resistance_pct = max(resistance_pct, fighter.poison_resistance_pct)
        
        # Cap resistance at 100%
        resistance_pct = min(resistance_pct, 100)
        
        # Calculate reduced damage
        if resistance_pct >= 100:
            return 0
        
        # Damage reduction: multiply by (1 - resistance/100)
        damage = int(base_damage * (1 - resistance_pct / 100))
        
        return max(0, damage)
    
    def __repr__(self):
        return f"PoisonEffect({self.duration} turns, {self.damage_per_tick}/tick)"


class StatusEffectManager:
    """Manages status effects for an entity."""
    
    # Class-level cache for effect signature introspection
    # Maps effect class to whether it accepts state_manager parameter
    _signature_cache: Dict[type, bool] = {}
    
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

    def process_turn_start(self, entities=None, turn_number: int = None, state_manager=None) -> List[Dict[str, Any]]:
        """Process status effects at turn start.
        
        Args:
            entities: Optional list of all game entities (for effects that need global access)
            turn_number: Optional current turn number (for time-based effects like Ring of Regeneration)
            state_manager: Optional state manager (CRITICAL for death finalization in DOT effects)
        
        Returns:
            List of result dictionaries
        """
        results = []
        
        # Process ring effects first (Ring of Regeneration)
        from components.component_registry import ComponentType
        equipment = self.owner.equipment if hasattr(self.owner, 'equipment') else None
        if equipment:
            for ring in [equipment.left_ring, equipment.right_ring]:
                if ring and ring.components.has(ComponentType.RING):
                    ring_results = ring.ring.process_turn(self.owner, turn_number=turn_number)
                    results.extend(ring_results)
        
        # Then process status effects (pass entities AND state_manager to effects that need them)
        for effect_name in list(self.active_effects.keys()): # Iterate over a copy
            effect = self.active_effects[effect_name]
            
            # Pass state_manager to process_turn_start for death finalization
            # Check if effect accepts state_manager parameter (new Soul Burn does, old effects don't)
            # Cache the signature check per effect class to avoid reflection cost every turn
            effect_class = type(effect)
            if effect_class not in StatusEffectManager._signature_cache:
                import inspect
                sig = inspect.signature(effect.process_turn_start)
                StatusEffectManager._signature_cache[effect_class] = 'state_manager' in sig.parameters
            
            accepts_state_manager = StatusEffectManager._signature_cache[effect_class]
            
            if accepts_state_manager:
                results.extend(effect.process_turn_start(entities=entities, state_manager=state_manager))
            else:
                results.extend(effect.process_turn_start(entities=entities))
            
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