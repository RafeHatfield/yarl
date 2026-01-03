"""Phase 19: Exploder Necromancer AI - Corpse explosion specialist

Exploder Necromancer variant that:
- Targets spent/consumed corpses (CorpseComponent.consumed == True)
- Detonates corpses for deterministic AoE damage
- Removes corpses after explosion
- Shares hang-back and safety behavior with base necromancer
"""

from typing import Optional, List, TYPE_CHECKING
from components.ai.necromancer_base import NecromancerBase
from logger_config import get_logger
import math

if TYPE_CHECKING:
    from entity import Entity

logger = get_logger(__name__)


class ExploderNecromancerAI(NecromancerBase):
    """AI for Exploder Necromancer that detonates spent corpses.
    
    Overrides base necromancer to:
    - Find spent corpses (consumed=True or raise_count>0)
    - Detonate them for AoE damage
    - Track explosion-specific metrics
    """
    
    def _try_execute_action(
        self,
        target,
        game_map,
        entities: List,
        action_range: int,
        action_cooldown: int
    ) -> Optional[List]:
        """Attempt to explode a spent corpse if one is in range.
        
        Args:
            target: The player entity
            game_map: Game map
            entities: List of all entities
            action_range: Maximum range for explosion
            action_cooldown: Cooldown after successful explosion
            
        Returns:
            List of results if explosion attempted, None otherwise
        """
        from components.component_registry import ComponentType
        
        # Find best spent corpse in range
        spent_corpse = self._find_best_spent_corpse(entities, max_range=action_range)
        
        if spent_corpse is None:
            return None
        
        # Attempt to explode the corpse
        logger.debug(f"{self.owner.name} attempting to explode {spent_corpse.name} at ({spent_corpse.x}, {spent_corpse.y})")
        
        # Record metric: explosion attempt
        self._increment_metric('corpse_explosions_cast')
        
        try:
            # Get explosion parameters
            explosion_radius = getattr(self.owner, 'explosion_radius', 2)
            damage_min = getattr(self.owner, 'explosion_damage_min', 4)
            damage_max = getattr(self.owner, 'explosion_damage_max', 8)
            damage_type = getattr(self.owner, 'explosion_damage_type', 'necrotic')
            
            # Calculate deterministic damage (use position for determinism)
            damage_range = damage_max - damage_min + 1
            position_seed = (spent_corpse.x * 1000 + spent_corpse.y) % damage_range
            damage = damage_min + position_seed
            
            # Find all entities in explosion radius
            explosion_x = spent_corpse.x
            explosion_y = spent_corpse.y
            damaged_entities = []
            total_damage_dealt = 0
            player_hit = False
            
            for entity in entities:
                # Skip the corpse itself
                if entity == spent_corpse:
                    continue
                
                # Check if entity is in explosion radius
                distance = math.sqrt((entity.x - explosion_x)**2 + (entity.y - explosion_y)**2)
                if distance <= explosion_radius:
                    # Check if entity has fighter component
                    fighter = entity.get_component_optional(ComponentType.FIGHTER)
                    if fighter and entity.fighter.hp > 0:
                        # Apply damage
                        entity.fighter.hp -= damage
                        total_damage_dealt += damage
                        damaged_entities.append(entity)
                        
                        # Check if player was hit
                        if entity == target:
                            player_hit = True
                        
                        logger.debug(f"Corpse explosion hits {entity.name} for {damage} damage")
            
            # Phase 20: Mark corpse as CONSUMED and remove from map
            corpse_comp = spent_corpse.get_component_optional(ComponentType.CORPSE)
            if corpse_comp:
                corpse_comp.mark_consumed()
            
            if spent_corpse in entities:
                entities.remove(spent_corpse)
            
            # Record metrics (Phase 20: use 'spent_corpses_exploded' instead of 'consumed')
            self._increment_metric('spent_corpses_exploded')
            self._increment_metric('explosion_damage_total', total_damage_dealt)
            if player_hit:
                self._increment_metric('player_hits_from_explosion')
            
            # Set cooldown
            self.action_cooldown_remaining = action_cooldown
            
            logger.info(f"{self.owner.name} exploded corpse, hit {len(damaged_entities)} entities for {damage} damage each")
            
            # Create visual effect and messages
            results = []
            
            # Import visual effects
            try:
                from visual_effects import show_effect_vfx
                from visual_effect_queue import EffectType
                show_effect_vfx(explosion_x, explosion_y, EffectType.EXPLOSION, None)
            except ImportError:
                pass  # VFX optional
            
            # Create message
            from game_messages import Message
            results.append({
                'consumed': True,
                'message': Message(
                    f"{self.owner.name} detonates a corpse! BOOM!",
                    (220, 80, 80)
                )
            })
            
            # Add damage messages for each damaged entity
            for damaged_entity in damaged_entities:
                results.append({
                    'message': Message(
                        f"{damaged_entity.name} takes {damage} {damage_type} damage from the explosion!",
                        (200, 100, 100)
                    )
                })
                
                # Check if entity died
                if damaged_entity.fighter.hp <= 0:
                    results.append({'dead': damaged_entity})
            
            return results
            
        except Exception as e:
            logger.warning(f"{self.owner.name} corpse explosion error: {e}")
            return None
    
    def _try_target_seeking_movement(
        self,
        target,
        game_map,
        entities: List,
        action_range: int,
        danger_radius: int
    ) -> Optional[List]:
        """Attempt to move toward a spent corpse while respecting danger radius.
        
        Args:
            target: The player entity
            game_map: Game map
            entities: List of all entities
            action_range: Explosion range (to know if corpse is out of range)
            danger_radius: Never approach within this distance of player
            
        Returns:
            List of results if movement made, None otherwise
        """
        # Find best spent corpse (anywhere on map)
        spent_corpse = self._find_best_spent_corpse(entities, max_range=None)
        
        if spent_corpse is None:
            return None
        
        # Check if corpse is already in range
        corpse_distance = self._distance_to_position(spent_corpse.x, spent_corpse.y)
        if corpse_distance <= action_range:
            # Corpse in range but explosion must be on cooldown - don't seek
            return None
        
        # Try to move toward corpse while respecting danger radius
        return self._try_safe_target_approach(
            spent_corpse, target, game_map, entities, danger_radius, "exploder_corpse_seek_moves"
        )
    
    def _find_best_spent_corpse(
        self,
        entities: List,
        max_range: Optional[int] = None
    ) -> Optional['Entity']:
        """Find the best spent corpse deterministically.
        
        Phase 20: Now enforces SPENT state explicitly.
        
        Selection criteria (in order):
        1. Must have CorpseComponent with corpse_state == SPENT
        2. If max_range provided, must be within range
        3. Prefer nearest spent corpse
        4. Tie-break by (y, x) for determinism
        
        Args:
            entities: List of all entities
            max_range: Optional max range constraint
            
        Returns:
            Best spent corpse entity, or None if no spent corpses
        """
        from components.component_registry import ComponentType
        from components.corpse import CorpseState
        
        spent_corpses = []
        
        for entity in entities:
            # Check for CorpseComponent
            corpse_comp = entity.get_component_optional(ComponentType.CORPSE)
            if corpse_comp is None:
                continue
            
            # Phase 20: Enforce SPENT state only
            if corpse_comp.corpse_state != CorpseState.SPENT:
                continue
            
            # Check range constraint
            if max_range is not None:
                distance = self._distance_to_position(entity.x, entity.y)
                if distance > max_range:
                    continue
            
            spent_corpses.append(entity)
        
        if not spent_corpses:
            return None
        
        # Sort by distance (nearest first), then by (y, x) for determinism
        spent_corpses.sort(key=lambda c: (
            self._distance_to_position(c.x, c.y),
            c.y,
            c.x
        ))
        
        return spent_corpses[0]


