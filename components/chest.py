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
                from message_builder import MessageBuilder as MB
                results.append({
                    'message': MB.info("This chest is already empty.")
                })
            return results
        
        # Check if mimic
        if self.is_mimic:
            from message_builder import MessageBuilder as MB
            results.append({
                'mimic_revealed': True,
                'entity': self.owner,
                'message': MB.warning("The chest comes alive and attacks!")
            })
            return results
        
        # Check if locked
        if self.is_locked():
            from message_builder import MessageBuilder as MB
            if not has_key:
                results.append({
                    'message': MB.warning("This chest is locked. You need a key to open it.")
                })
                return results
            else:
                results.append({
                    'message': MB.info("You unlock the chest with the key.")
                })
        
        # Check if trapped
        if self.is_trapped():
            from message_builder import MessageBuilder as MB
            results.append({
                'message': MB.warning("You trigger a trap!"),
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
        
        from message_builder import MessageBuilder as MB
        
        # Message depends on whether chest had loot
        if self.loot:
            message = MB.success("You open the chest!")
        else:
            message = MB.info("You open the chest, but it's empty.")
        
        results.append({
            'chest_opened': True,
            'loot': self.loot,
            'message': message
        })
        
        return results
    
    def _generate_loot(self) -> List['Entity']:
        """Generate randomized loot based on quality tier.
        
        Returns:
            List of loot entities
        """
        import random
        from config.entity_factory import EntityFactory
        
        loot = []
        
        # Quality determines number and rarity of items
        loot_counts = {
            'common': (1, 2),      # 1-2 items
            'uncommon': (2, 3),    # 2-3 items
            'rare': (3, 4),        # 3-4 items
            'legendary': (4, 6)    # 4-6 items
        }
        
        min_items, max_items = loot_counts.get(self.loot_quality, (1, 2))
        num_items = random.randint(min_items, max_items)
        
        # Loot tables by quality
        # Format: [(item_type, weight), ...]
        loot_tables = {
            'common': [
                ('healing_potion', 40),
                ('scroll_of_lightning_bolt', 20),
                ('scroll_of_fireball', 20),
                ('scroll_of_confusion', 20),
            ],
            'uncommon': [
                ('healing_potion', 30),
                ('strength_potion', 20),
                ('scroll_of_lightning_bolt', 15),
                ('scroll_of_fireball', 15),
                ('wand_of_lightning', 10),
                ('wand_of_fireball', 10),
            ],
            'rare': [
                ('healing_potion', 20),
                ('strength_potion', 15),
                ('wand_of_lightning', 15),
                ('wand_of_fireball', 15),
                ('ring_of_protection', 10),
                ('ring_of_strength', 10),
                ('ring_of_regeneration', 10),
                ('scroll_of_identify', 5),
            ],
            'legendary': [
                ('wand_of_fireball', 20),
                ('ring_of_might', 15),
                ('ring_of_protection', 15),
                ('ring_of_invisibility', 10),
                ('ring_of_regeneration', 10),
                ('scroll_of_magic_mapping', 10),
                ('scroll_of_teleportation', 10),
                ('strength_potion', 10),
            ]
        }
        
        loot_table = loot_tables.get(self.loot_quality, loot_tables['common'])
        
        # Determine chest position for spawning items
        chest_x = self.owner.x if self.owner else 0
        chest_y = self.owner.y if self.owner else 0
        
        try:
            factory = EntityFactory()
            
            for _ in range(num_items):
                # Weighted random selection
                items = [item for item, weight in loot_table]
                weights = [weight for item, weight in loot_table]
                
                item_type = random.choices(items, weights=weights, k=1)[0]
                
                # Create the item
                # Try different factory methods based on item type
                item = None
                
                # Try spell/consumable
                if 'scroll' in item_type or 'potion' in item_type:
                    item = factory.create_spell_item(item_type, chest_x, chest_y)
                
                # Try wand
                if not item and 'wand' in item_type:
                    item = factory.create_wand(item_type, chest_x, chest_y)
                
                # Try ring
                if not item and 'ring' in item_type:
                    item = factory.create_ring(item_type, chest_x, chest_y)
                
                if item:
                    loot.append(item)
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating chest loot: {e}")
        
        return loot
    
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

