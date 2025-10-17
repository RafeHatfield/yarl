"""Chest Component System.

This module provides the chest component for loot containers in the game.
Chests can be in various states (closed, open, trapped, locked) and contain
randomized loot based on dungeon depth and quality tier.

Example:
    >>> chest = Entity(10, 10, 'C', (139, 69, 19), 'Chest')
    >>> chest.chest = Chest(ChestState.CLOSED, loot_quality='rare')
    >>> results = chest.chest.open(player)
"""

from enum import Enum, auto
from typing import TYPE_CHECKING, Optional, Dict, Any, List

from components.map_feature import MapFeature, MapFeatureType

if TYPE_CHECKING:
    from entity import Entity


class ChestState(Enum):
    """States a chest can be in."""
    CLOSED = auto()     # Unopened, ready to loot
    OPEN = auto()       # Already opened, no loot
    TRAPPED = auto()    # Closed but trapped
    LOCKED = auto()     # Closed and requires key


class Chest(MapFeature):
    """Component for loot chests.
    
    Chests are interactive map features that contain randomized loot.
    They can be trapped, locked, or even mimics (monsters disguised as chests).
    
    Attributes:
        state: Current state of the chest
        loot: List of item entities contained in the chest
        is_mimic: Whether this is actually a mimic monster
        trap_type: Type of trap if trapped (damage, poison, monster_spawn)
        key_id: ID of key required if locked
        loot_quality: Quality tier for loot generation
    """
    
    def __init__(
        self,
        state: ChestState = ChestState.CLOSED,
        loot: Optional[List['Entity']] = None,
        is_mimic: bool = False,
        trap_type: Optional[str] = None,
        key_id: Optional[str] = None,
        loot_quality: str = 'common'
    ):
        """Initialize a chest component.
        
        Args:
            state: Initial state of the chest
            loot: Pre-generated loot items (None = generate on open)
            is_mimic: Whether this is a mimic in disguise
            trap_type: Type of trap ('damage', 'poison', 'monster_spawn')
            key_id: Key ID required to open if locked
            loot_quality: Loot quality tier ('common', 'uncommon', 'rare', 'legendary')
        """
        super().__init__(
            feature_type=MapFeatureType.CHEST,
            discovered=True,  # Chests are visible by default
            interactable=True
        )
        
        self.state = state
        self.loot = loot or []
        self.is_mimic = is_mimic
        self.trap_type = trap_type
        self.key_id = key_id
        self.loot_quality = loot_quality
    
    def can_interact(self) -> bool:
        """Check if chest can be interacted with.
        
        Returns:
            True if chest is not already open
        """
        return self.interactable and self.state != ChestState.OPEN
    
    def is_trapped(self) -> bool:
        """Check if chest is trapped.
        
        Returns:
            True if chest state is TRAPPED
        """
        return self.state == ChestState.TRAPPED
    
    def is_locked(self) -> bool:
        """Check if chest is locked.
        
        Returns:
            True if chest state is LOCKED
        """
        return self.state == ChestState.LOCKED
    
    def detect_trap(self, actor: 'Entity') -> bool:
        """Attempt to detect if chest is trapped.
        
        Uses actor's perception/searching ability to detect traps.
        
        Args:
            actor: Entity attempting detection
            
        Returns:
            True if trap was detected
        """
        if not self.is_trapped():
            return False
        
        # TODO: Implement perception check when we have stats
        # For now, give a base 50% chance + Ring of Searching bonus
        import random
        
        base_chance = 0.5
        
        # Check for Ring of Searching
        if hasattr(actor, 'equipment') and actor.equipment:
            from components.component_registry import ComponentType
            rings = [actor.equipment.left_ring, actor.equipment.right_ring]
            for ring_entity in rings:
                if ring_entity and ring_entity.components.has(ComponentType.RING):
                    from components.ring import RingEffect
                    if ring_entity.ring.ring_effect == RingEffect.SEARCHING:
                        return True  # Ring of Searching always detects
        
        return random.random() < base_chance
    
    def open(self, actor: 'Entity', has_key: bool = False) -> List[Dict[str, Any]]:
        """Attempt to open the chest.
        
        Args:
            actor: Entity attempting to open the chest
            has_key: Whether actor has the required key (if locked)
            
        Returns:
            List of result dictionaries from opening
        """
        results = []
        
        if not self.can_interact():
            if self.state == ChestState.OPEN:
                results.append({
                    'message': "This chest is already empty."
                })
            return results
        
        # Check if mimic
        if self.is_mimic:
            results.append({
                'mimic_revealed': True,
                'entity': self.owner,
                'message': "The chest comes alive and attacks!"
            })
            return results
        
        # Check if locked
        if self.is_locked():
            if not has_key:
                results.append({
                    'message': "This chest is locked. You need a key to open it."
                })
                return results
            else:
                results.append({
                    'message': "You unlock the chest with the key."
                })
        
        # Check if trapped
        if self.is_trapped():
            results.append({
                'message': "You trigger a trap!",
                'trap_triggered': True,
                'trap_type': self.trap_type
            })
            # Trap is now sprung, chest becomes normal
            self.state = ChestState.CLOSED
        
        # Open the chest
        self.state = ChestState.OPEN
        
        # Generate loot if not pre-generated
        if not self.loot:
            self.loot = self._generate_loot()
        
        results.append({
            'chest_opened': True,
            'loot': self.loot,
            'message': f"You open the chest and find {len(self.loot)} item(s)!"
        })
        
        return results
    
    def _generate_loot(self) -> List['Entity']:
        """Generate randomized loot based on quality tier.
        
        Returns:
            List of loot entities
        """
        # TODO: Implement proper loot generation
        # For now, return empty list
        # This will be implemented in Slice 2
        return []
    
    def get_description(self) -> str:
        """Get description of the chest.
        
        Returns:
            String description for tooltips
        """
        if self.is_mimic:
            return "Chest (something seems off...)"
        
        state_descriptions = {
            ChestState.CLOSED: "Chest",
            ChestState.OPEN: "Empty Chest",
            ChestState.TRAPPED: "Chest (looks suspicious)",
            ChestState.LOCKED: "Locked Chest"
        }
        
        return state_descriptions.get(self.state, "Chest")
    
    def __repr__(self):
        return (
            f"Chest(state={self.state}, "
            f"loot_count={len(self.loot)}, "
            f"is_mimic={self.is_mimic})"
        )

