"""Phase 19: Bone Necromancer AI - Raises bone piles into bone thralls

Bone Necromancer variant that:
- Targets bone piles (skeleton death remnants) only
- Summons weak bone thralls
- Uses deterministic targeting (nearest bone pile)
- Shares hang-back and safety behavior with base necromancer
"""

from typing import Optional, List, TYPE_CHECKING
from components.ai.necromancer_base import NecromancerBase
from logger_config import get_logger

if TYPE_CHECKING:
    from entity import Entity

logger = get_logger(__name__)


class BoneNecromancerAI(NecromancerBase):
    """AI for Bone Necromancer that targets bone piles.
    
    Overrides base necromancer to:
    - Find bone piles instead of corpses
    - Summon bone thralls via bone_raise action
    - Track bone-specific metrics
    """
    
    def _try_execute_action(
        self,
        target,
        game_map,
        entities: List,
        action_range: int,
        action_cooldown: int
    ) -> Optional[List]:
        """Attempt to raise a bone pile if one is in range.
        
        Args:
            target: The player entity
            game_map: Game map
            entities: List of all entities
            action_range: Maximum range for raising
            action_cooldown: Cooldown after successful raise
            
        Returns:
            List of results if raise attempted, None otherwise
        """
        # Find best bone pile in range
        bone_pile = self._find_best_bone_pile(entities, max_range=action_range)
        
        if bone_pile is None:
            return None
        
        # Attempt to raise the bone pile
        logger.debug(f"{self.owner.name} attempting to raise {bone_pile.name} at ({bone_pile.x}, {bone_pile.y})")
        
        # Record metric: raise attempt
        self._increment_metric('bone_raise_attempts')
        
        try:
            # Summon bone thrall at bone pile location
            summon_monster_id = getattr(self.owner, 'summon_monster_id', 'bone_thrall')
            raiser_faction = getattr(self.owner, 'faction', None)
            
            # Import entity factory to create bone thrall
            from config.factories.entity_factory import get_entity_factory
            factory = get_entity_factory()
            
            # Create bone thrall at bone pile location (with depth scaling)
            depth = 1
            if game_map:
                dungeon_level = getattr(game_map, 'dungeon_level', None)
                if isinstance(dungeon_level, int):
                    depth = dungeon_level
            bone_thrall = factory.create_monster(summon_monster_id, bone_pile.x, bone_pile.y, depth=depth)
            if bone_thrall is None:
                logger.warning(f"Failed to create {summon_monster_id} for {self.owner.name}")
                return None
            
            # Set faction to match necromancer
            if raiser_faction:
                bone_thrall.faction = raiser_faction
            
            # Add to entities list
            entities.append(bone_thrall)
            
            # Remove the bone pile
            if bone_pile in entities:
                entities.remove(bone_pile)
            
            # Record metrics
            self._increment_metric('bone_raise_successes')
            self._increment_metric('bone_piles_consumed')
            self._increment_metric('bone_thralls_spawned')
            
            # Set cooldown
            self.action_cooldown_remaining = action_cooldown
            
            logger.info(f"{self.owner.name} raised bone pile into {bone_thrall.name}")
            
            # Return success results
            from game_messages import Message
            return [{
                'consumed': True,
                'message': Message(f"{self.owner.name} raises a bone thrall from the pile!", (160, 100, 200))
            }]
            
        except Exception as e:
            logger.warning(f"{self.owner.name} bone raise error: {e}")
            return None
    
    def _try_target_seeking_movement(
        self,
        target,
        game_map,
        entities: List,
        action_range: int,
        danger_radius: int
    ) -> Optional[List]:
        """Attempt to move toward a bone pile while respecting danger radius.
        
        Args:
            target: The player entity
            game_map: Game map
            entities: List of all entities
            action_range: Raise range (to know if bone pile is out of range)
            danger_radius: Never approach within this distance of player
            
        Returns:
            List of results if movement made, None otherwise
        """
        # Find best bone pile (anywhere on map)
        bone_pile = self._find_best_bone_pile(entities, max_range=None)
        
        if bone_pile is None:
            return None
        
        # Check if bone pile is already in range
        pile_distance = self._distance_to_position(bone_pile.x, bone_pile.y)
        if pile_distance <= action_range:
            # Bone pile in range but raise must be on cooldown - don't seek
            return None
        
        # Try to move toward bone pile while respecting danger radius
        return self._try_safe_target_approach(
            bone_pile, target, game_map, entities, danger_radius, "bone_seek_moves"
        )
    
    def _find_best_bone_pile(
        self,
        entities: List,
        max_range: Optional[int] = None
    ) -> Optional['Entity']:
        """Find the best bone pile deterministically.
        
        Selection criteria (in order):
        1. Must have is_bone_pile=True attribute
        2. Tile must not be blocked by another entity
        3. If max_range provided, must be within range
        4. Prefer nearest bone pile
        5. Tie-break by (y, x) for determinism
        
        Args:
            entities: List of all entities
            max_range: Optional max range constraint
            
        Returns:
            Best bone pile entity, or None if no bone piles
        """
        bone_piles = []
        
        for entity in entities:
            # Check for bone pile attribute
            if not getattr(entity, 'is_bone_pile', False):
                continue
            
            # Check if tile is blocked by another entity
            tile_blocked = False
            for other in entities:
                if other != entity and other.blocks and other.x == entity.x and other.y == entity.y:
                    tile_blocked = True
                    break
            
            if tile_blocked:
                continue
            
            # Check range constraint
            if max_range is not None:
                distance = self._distance_to_position(entity.x, entity.y)
                if distance > max_range:
                    continue
            
            bone_piles.append(entity)
        
        if not bone_piles:
            return None
        
        # Sort by distance (nearest first), then by (y, x) for determinism
        bone_piles.sort(key=lambda b: (
            self._distance_to_position(b.x, b.y),
            b.y,
            b.x
        ))
        
        return bone_piles[0]


