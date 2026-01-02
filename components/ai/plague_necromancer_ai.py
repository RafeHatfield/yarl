"""Phase 19: Plague Necromancer AI - Raises corpses into plague zombies

Plague Necromancer variant that:
- Targets regular corpses (with CorpseComponent)
- Summons plague zombies that spread infection
- Reuses existing plague mechanics (plague_attack ability)
- Shares hang-back and safety behavior with base necromancer
"""

from typing import Optional, List, TYPE_CHECKING
from components.ai.necromancer_base import NecromancerBase
from logger_config import get_logger

if TYPE_CHECKING:
    from entity import Entity

logger = get_logger(__name__)


class PlagueNecromancerAI(NecromancerBase):
    """AI for Plague Necromancer that raises plague zombies.
    
    Overrides base necromancer to:
    - Raise corpses into plague zombies (not regular zombies)
    - Plague zombies have plague_attack ability (existing mechanic)
    - Track plague-specific metrics
    """
    
    def _try_execute_action(
        self,
        target,
        game_map,
        entities: List,
        action_range: int,
        action_cooldown: int
    ) -> Optional[List]:
        """Attempt to raise a corpse into a plague zombie if one is in range.
        
        Args:
            target: The player entity
            game_map: Game map
            entities: List of all entities
            action_range: Maximum range for raising
            action_cooldown: Cooldown after successful raise
            
        Returns:
            List of results if raise attempted, None otherwise
        """
        from components.component_registry import ComponentType
        from spells import cast_spell_by_id
        
        # Find best raisable corpse in range
        corpse = self._find_best_raisable_corpse(entities, max_range=action_range)
        
        if corpse is None:
            return None
        
        # Attempt to raise the corpse as a plague zombie
        logger.debug(f"{self.owner.name} attempting to raise {corpse.name} as plague zombie at ({corpse.x}, {corpse.y})")
        
        # Record metric: plague raise attempt
        self._increment_metric('plague_raise_attempts')
        
        try:
            # Cast raise dead with raiser_faction override
            raiser_faction = getattr(self.owner, 'faction', None)
            
            raise_results = cast_spell_by_id(
                "raise_dead",
                caster=self.owner,
                entities=entities,
                game_map=game_map,
                fov_map=None,  # Raise dead doesn't need FOV
                target_x=corpse.x,
                target_y=corpse.y,
                raiser_faction=raiser_faction
            )
            
            # Check if raise was successful
            if raise_results and any(r.get("consumed", False) for r in raise_results):
                # Raise succeeded - now convert to plague zombie
                # Find the newly raised zombie
                raised_zombie = None
                for entity in entities:
                    if entity.x == corpse.x and entity.y == corpse.y:
                        if hasattr(entity, 'ai') and entity.ai is not None:
                            raised_zombie = entity
                            break
                
                if raised_zombie:
                    # Convert to plague zombie by adding plague abilities
                    if not hasattr(raised_zombie, 'special_abilities'):
                        raised_zombie.special_abilities = []
                    if "plague_attack" not in raised_zombie.special_abilities:
                        raised_zombie.special_abilities.append("plague_attack")
                    
                    # Add plague_carrier tag
                    if not hasattr(raised_zombie, 'tags'):
                        raised_zombie.tags = []
                    if "plague_carrier" not in raised_zombie.tags:
                        raised_zombie.tags.append("plague_carrier")
                    
                    # Update appearance for plague zombie
                    raised_zombie.char = "Z"
                    raised_zombie.color = (100, 180, 80)  # Sickly green
                    
                    # Boost stats slightly (plague zombies are stronger)
                    if hasattr(raised_zombie, 'fighter') and raised_zombie.fighter:
                        raised_zombie.fighter.hp = min(raised_zombie.fighter.hp + 6, raised_zombie.fighter.max_hp + 6)
                        raised_zombie.fighter.base_max_hp += 6
                        if hasattr(raised_zombie.fighter, 'damage_min'):
                            raised_zombie.fighter.damage_min += 1
                        if hasattr(raised_zombie.fighter, 'damage_max'):
                            raised_zombie.fighter.damage_max += 1
                
                self.action_cooldown_remaining = action_cooldown
                logger.info(f"{self.owner.name} successfully raised plague zombie")
                
                # Record metrics
                self._increment_metric('plague_raise_successes')
                self._increment_metric('plague_zombies_spawned')
                
                return raise_results
            else:
                # Log failure reason for debugging
                if raise_results:
                    failure_msg = raise_results[0].get("message")
                    if failure_msg:
                        logger.warning(f"{self.owner.name} plague raise failed at ({corpse.x},{corpse.y}): {failure_msg.text if hasattr(failure_msg, 'text') else failure_msg}")
                return None
                
        except Exception as e:
            logger.warning(f"{self.owner.name} plague raise error: {e}")
            return None
    
    def _try_target_seeking_movement(
        self,
        target,
        game_map,
        entities: List,
        action_range: int,
        danger_radius: int
    ) -> Optional[List]:
        """Attempt to move toward a raisable corpse while respecting danger radius.
        
        Args:
            target: The player entity
            game_map: Game map
            entities: List of all entities
            action_range: Raise range (to know if corpse is out of range)
            danger_radius: Never approach within this distance of player
            
        Returns:
            List of results if movement made, None otherwise
        """
        # Find best raisable corpse (anywhere on map)
        corpse = self._find_best_raisable_corpse(entities, max_range=None)
        
        if corpse is None:
            return None
        
        # Check if corpse is already in range
        corpse_distance = self._distance_to_position(corpse.x, corpse.y)
        if corpse_distance <= action_range:
            # Corpse in range but raise must be on cooldown - don't seek
            return None
        
        # Try to move toward corpse while respecting danger radius
        return self._try_safe_target_approach(
            corpse, target, game_map, entities, danger_radius, "plague_corpse_seek_moves"
        )
    
    def _find_best_raisable_corpse(
        self,
        entities: List,
        max_range: Optional[int] = None
    ) -> Optional['Entity']:
        """Find the best raisable corpse deterministically.
        
        Selection criteria (in order):
        1. Must have CorpseComponent with can_be_raised() == True
        2. Tile must not be blocked by another entity (especially player)
        3. If max_range provided, must be within range
        4. Prefer nearest corpse
        5. Tie-break by (y, x) for determinism
        
        Args:
            entities: List of all entities
            max_range: Optional max range constraint
            
        Returns:
            Best corpse entity, or None if no raisable corpses
        """
        from components.component_registry import ComponentType
        
        raisable_corpses = []
        
        for entity in entities:
            # Check for CorpseComponent
            corpse_comp = entity.get_component_optional(ComponentType.CORPSE)
            if corpse_comp is None:
                continue
            
            # Check if corpse can be raised
            if not corpse_comp.can_be_raised():
                continue
            
            # Check if corpse tile is blocked by another entity
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
            
            raisable_corpses.append(entity)
        
        if not raisable_corpses:
            return None
        
        # Sort by distance (nearest first), then by (y, x) for determinism
        raisable_corpses.sort(key=lambda c: (
            self._distance_to_position(c.x, c.y),
            c.y,
            c.x
        ))
        
        return raisable_corpses[0]


