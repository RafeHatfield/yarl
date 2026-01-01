"""Phase 19: Necromancer AI - Corpse economy controller with raise dead + corpse seeking

Necromancer is a hang-back controller enemy with deterministic, corpse-focused gameplay:
1. Raise Dead (cooldown-based resurrection):
   - Raises corpses with CorpseComponent.can_be_raised() == True
   - Range: config-driven (default 5)
   - Cooldown: config-driven (default 4 turns)
   - Creates friendly zombies (raiser_faction override)
   - Deterministic corpse selection (nearest, tie-break by position)

2. Corpse-seeking movement:
   - Moves toward raisable corpses when out of range
   - Safety constraint: Never approach within danger_radius (default 2) of player
   - Deterministic pathfinding (no RNG)

3. Hang-back AI heuristic:
   - Prefers distance 4-7 from player
   - If too close (<=2), retreats if possible
   - Never stalls: attacks or waits if boxed in
"""

from typing import Optional, List, Tuple, TYPE_CHECKING
from components.ai.basic_monster import BasicMonster
from logger_config import get_logger
import math

if TYPE_CHECKING:
    from entity import Entity

logger = get_logger(__name__)


class NecromancerAI(BasicMonster):
    """AI for Necromancer with Raise Dead, corpse-seeking, and hang-back behavior.
    
    Phase 19: Necromancer is a controller enemy that:
    - Raises dead on cooldown when corpses are in range
    - Seeks corpses when out of range (respecting danger radius)
    - Hangs back to avoid melee combat (weak stats, prefers summons)
    """
    
    def __init__(self):
        """Initialize Necromancer AI."""
        super().__init__()
        # Cooldown tracking (turns remaining until raise is ready)
        self.raise_cooldown_remaining = 0
    
    def take_turn(self, target, fov_map, game_map, entities):
        """Execute one turn of necromancer AI behavior.
        
        Overrides BasicMonster to add:
        1. Raise Dead trigger (cooldown-based)
        2. Corpse-seeking movement (when no corpses in range)
        3. Hang-back heuristic (maintain distance 4-7)
        
        Priority:
        1. If corpse within raise range AND raise off cooldown: Raise dead
        2. Else if raisable corpse exists but out of range: Seek corpse (respect danger radius)
        3. Else hang back or attack if forced
        
        Args:
            target: The target entity (usually the player)
            fov_map: Field of view map
            game_map: Game map
            entities: List of all entities
            
        Returns:
            list: List of result dictionaries
        """
        from components.component_registry import ComponentType
        
        results = []
        
        # Decrement cooldown at start of turn
        if self.raise_cooldown_remaining > 0:
            self.raise_cooldown_remaining -= 1
        
        # Get necromancer config
        raise_enabled = getattr(self.owner, 'raise_dead_enabled', True)
        raise_range = getattr(self.owner, 'raise_dead_range', 5)
        raise_cooldown = getattr(self.owner, 'raise_dead_cooldown_turns', 4)
        danger_radius = getattr(self.owner, 'danger_radius_from_player', 2)
        preferred_min = getattr(self.owner, 'preferred_distance_min', 4)
        preferred_max = getattr(self.owner, 'preferred_distance_max', 7)
        
        # Phase 19.1: Try to raise dead if enabled and off cooldown
        if raise_enabled and self.raise_cooldown_remaining <= 0:
            raise_results = self._try_raise_dead(
                target, game_map, entities, raise_range, raise_cooldown
            )
            if raise_results:
                results.extend(raise_results)
                # Raising consumed the turn - return early
                status_effects = self.owner.get_component_optional(ComponentType.STATUS_EFFECTS)
                if status_effects:
                    end_results = status_effects.process_turn_end()
                    results.extend(end_results)
                return results
        
        # Phase 19.2: Try corpse-seeking movement if corpses exist but out of range
        corpse_seek_results = self._try_corpse_seeking_movement(
            target, game_map, entities, raise_range, danger_radius
        )
        if corpse_seek_results:
            results.extend(corpse_seek_results)
            # Movement consumed the turn - return early
            status_effects = self.owner.get_component_optional(ComponentType.STATUS_EFFECTS)
            if status_effects:
                end_results = status_effects.process_turn_end()
                results.extend(end_results)
            return results
        
        # Phase 19.3: Hang-back behavior or fallback to basic AI
        # If too close to player, try to retreat
        distance_to_player = self._distance_to(target)
        
        if distance_to_player <= danger_radius:
            # Too close - try to retreat
            retreat_results = self._try_retreat(target, game_map, entities)
            if retreat_results:
                results.extend(retreat_results)
                status_effects = self.owner.get_component_optional(ComponentType.STATUS_EFFECTS)
                if status_effects:
                    end_results = status_effects.process_turn_end()
                    results.extend(end_results)
                return results
        
        # Fallback: Use basic monster AI (attack if adjacent, or wait)
        basic_results = super().take_turn(target, fov_map, game_map, entities)
        results.extend(basic_results)
        
        return results
    
    def _try_raise_dead(
        self, 
        target, 
        game_map, 
        entities: List, 
        raise_range: int,
        raise_cooldown: int
    ) -> Optional[List]:
        """Attempt to raise a corpse if one is in range.
        
        Args:
            target: The player entity
            game_map: Game map
            entities: List of all entities
            raise_range: Maximum range for raising
            raise_cooldown: Cooldown after successful raise
            
        Returns:
            List of results if raise attempted, None otherwise
        """
        from components.component_registry import ComponentType
        from spells import cast_spell_by_id
        
        # Find best raisable corpse in range
        corpse = self._find_best_raisable_corpse(entities, max_range=raise_range)
        
        if corpse is None:
            return None
        
        # Attempt to raise the corpse
        logger.debug(f"{self.owner.name} attempting to raise {corpse.name} at ({corpse.x}, {corpse.y})")
        
        # Record metric: raise attempt
        try:
            from services.scenario_metrics import get_active_metrics_collector
            metrics = get_active_metrics_collector()
            if metrics:
                metrics.increment('necro_raise_attempts')
        except Exception:
            pass
        
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
                self.raise_cooldown_remaining = raise_cooldown
                logger.info(f"{self.owner.name} successfully raised {corpse.name}")
                
                # Record metric: raise success
                try:
                    from services.scenario_metrics import get_active_metrics_collector
                    metrics = get_active_metrics_collector()
                    if metrics:
                        metrics.increment('necro_raise_successes')
                except Exception:
                    pass
                
                return raise_results
            else:
                # Log failure reason for debugging
                if raise_results:
                    failure_msg = raise_results[0].get("message")
                    if failure_msg:
                        logger.warning(f"{self.owner.name} raise failed at ({corpse.x},{corpse.y}): {failure_msg.text if hasattr(failure_msg, 'text') else failure_msg}")
                    else:
                        logger.warning(f"{self.owner.name} raise failed: consumed={raise_results[0].get('consumed')}, results={raise_results}")
                else:
                    logger.warning(f"{self.owner.name} raise returned no results")
                return None
                
        except Exception as e:
            logger.warning(f"{self.owner.name} raise dead error: {e}")
            return None
    
    def _try_corpse_seeking_movement(
        self,
        target,
        game_map,
        entities: List,
        raise_range: int,
        danger_radius: int
    ) -> Optional[List]:
        """Attempt to move toward a raisable corpse while respecting danger radius.
        
        Args:
            target: The player entity
            game_map: Game map
            entities: List of all entities
            raise_range: Raise range (to know if corpse is out of range)
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
        if corpse_distance <= raise_range:
            # Corpse in range but raise must be on cooldown - don't seek
            return None
        
        # Try to move toward corpse while respecting danger radius
        move_result = self._try_safe_corpse_approach(
            corpse, target, game_map, entities, danger_radius
        )
        
        if move_result:
            # Record metric: corpse seek move
            try:
                from services.scenario_metrics import get_active_metrics_collector
                metrics = get_active_metrics_collector()
                if metrics:
                    metrics.increment('necro_corpse_seek_moves')
            except Exception:
                pass
            return move_result
        else:
            # Record metric: unsafe move blocked
            try:
                from services.scenario_metrics import get_active_metrics_collector
                metrics = get_active_metrics_collector()
                if metrics:
                    metrics.increment('necro_unsafe_move_blocks')
            except Exception:
                pass
            return None
    
    def _try_safe_corpse_approach(
        self,
        corpse,
        target,
        game_map,
        entities: List,
        danger_radius: int
    ) -> Optional[List]:
        """Try to move toward corpse while maintaining safe distance from player.
        
        Args:
            corpse: Corpse entity to approach
            target: Player entity
            game_map: Game map
            entities: List of all entities
            danger_radius: Never approach within this distance of player
            
        Returns:
            List of results with move action, or None if no safe move
        """
        # Compute ideal step toward corpse
        dx = corpse.x - self.owner.x
        dy = corpse.y - self.owner.y
        
        # Normalize to get direction
        distance = math.sqrt(dx**2 + dy**2)
        if distance == 0:
            return None
        
        # Try primary direction
        step_x = 0 if abs(dx) < 0.5 else (1 if dx > 0 else -1)
        step_y = 0 if abs(dy) < 0.5 else (1 if dy > 0 else -1)
        
        # Try primary step
        if self._is_safe_move(step_x, step_y, target, game_map, entities, danger_radius):
            return self._execute_move(step_x, step_y)
        
        # Try alternative steps (x-only, y-only)
        if step_x != 0 and self._is_safe_move(step_x, 0, target, game_map, entities, danger_radius):
            return self._execute_move(step_x, 0)
        
        if step_y != 0 and self._is_safe_move(0, step_y, target, game_map, entities, danger_radius):
            return self._execute_move(0, step_y)
        
        # No safe move found
        return None
    
    def _is_safe_move(
        self,
        dx: int,
        dy: int,
        target,
        game_map,
        entities: List,
        danger_radius: int
    ) -> bool:
        """Check if a move is safe (doesn't violate danger radius).
        
        Args:
            dx: X step (-1, 0, or 1)
            dy: Y step (-1, 0, or 1)
            target: Player entity
            game_map: Game map
            entities: List of all entities
            danger_radius: Minimum safe distance from player
            
        Returns:
            True if move is safe, False otherwise
        """
        new_x = self.owner.x + dx
        new_y = self.owner.y + dy
        
        # Check map bounds
        if new_x < 0 or new_x >= game_map.width or new_y < 0 or new_y >= game_map.height:
            return False
        
        # Check tile walkability
        if game_map.tiles[new_x][new_y].blocked:
            return False
        
        # Check for blocking entities
        for entity in entities:
            if entity.blocks and entity.x == new_x and entity.y == new_y:
                return False
        
        # Check danger radius
        distance_to_player = math.sqrt((new_x - target.x)**2 + (new_y - target.y)**2)
        if distance_to_player <= danger_radius:
            return False
        
        return True
    
    def _execute_move(self, dx: int, dy: int) -> List:
        """Execute a movement step.
        
        Args:
            dx: X step
            dy: Y step
            
        Returns:
            List of result dictionaries
        """
        self.owner.move(dx, dy)
        return [{
            "action": "move",
            "dx": dx,
            "dy": dy
        }]
    
    def _try_retreat(self, target, game_map, entities: List) -> Optional[List]:
        """Try to retreat away from player.
        
        Args:
            target: Player entity
            game_map: Game map
            entities: List of all entities
            
        Returns:
            List of results with move action, or None if no retreat possible
        """
        # Compute retreat direction (away from player)
        dx = self.owner.x - target.x
        dy = self.owner.y - target.y
        
        # Normalize to get direction
        distance = math.sqrt(dx**2 + dy**2)
        if distance == 0:
            return None
        
        # Try to move away
        step_x = 0 if abs(dx) < 0.5 else (1 if dx > 0 else -1)
        step_y = 0 if abs(dy) < 0.5 else (1 if dy > 0 else -1)
        
        # Try primary retreat step
        if self._is_walkable(step_x, step_y, game_map, entities):
            return self._execute_move(step_x, step_y)
        
        # Try alternative steps
        if step_x != 0 and self._is_walkable(step_x, 0, game_map, entities):
            return self._execute_move(step_x, 0)
        
        if step_y != 0 and self._is_walkable(0, step_y, game_map, entities):
            return self._execute_move(0, step_y)
        
        # No retreat possible
        return None
    
    def _is_walkable(self, dx: int, dy: int, game_map, entities: List) -> bool:
        """Check if a step is walkable.
        
        Args:
            dx: X step
            dy: Y step
            game_map: Game map
            entities: List of all entities
            
        Returns:
            True if walkable, False otherwise
        """
        new_x = self.owner.x + dx
        new_y = self.owner.y + dy
        
        # Check map bounds
        if new_x < 0 or new_x >= game_map.width or new_y < 0 or new_y >= game_map.height:
            return False
        
        # Check tile walkability
        if game_map.tiles[new_x][new_y].blocked:
            return False
        
        # Check for blocking entities
        for entity in entities:
            if entity.blocks and entity.x == new_x and entity.y == new_y:
                return False
        
        return True
    
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
            
            # Phase 19: Check if corpse tile is blocked by another entity
            # Skip if player or any other blocking entity is on the corpse
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
    
    def _distance_to(self, target) -> float:
        """Compute distance to target entity.
        
        Args:
            target: Target entity
            
        Returns:
            Euclidean distance
        """
        return self._distance_to_position(target.x, target.y)
    
    def _distance_to_position(self, x: int, y: int) -> float:
        """Compute distance to position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Euclidean distance
        """
        dx = x - self.owner.x
        dy = y - self.owner.y
        return math.sqrt(dx**2 + dy**2)

