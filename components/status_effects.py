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
        if hasattr(self.owner, 'ai') and self.owner.ai:
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
        if self.previous_ai and hasattr(self.owner, 'ai'):
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