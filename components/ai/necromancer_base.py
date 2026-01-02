"""Phase 19: Base Necromancer AI with config-driven action profiles

This module provides the base necromancer AI that supports different
action profiles for necromancer variants:
1. Bone Necromancer: Targets bone piles, summons weak bone thralls
2. Plague Necromancer: Raises corpses into plague zombies with infection
3. Exploder Necromancer: Consumes spent corpses for AoE damage

The action profile system is deterministic and data-driven via entity config.
"""

from typing import Optional, List, Tuple, TYPE_CHECKING, Callable
from components.ai.basic_monster import BasicMonster
from logger_config import get_logger
import math

if TYPE_CHECKING:
    from entity import Entity

logger = get_logger(__name__)


class NecromancerBase(BasicMonster):
    """Base AI for necromancer variants with config-driven action profiles.
    
    Action Profile Config (set on entity):
    - corpse_source: List of valid targets ["corpse", "bone_pile", "spent_corpse"]
    - action_type: "raise", "plague_raise", or "explode"
    - action_range: Range for ability (default 5)
    - action_cooldown_turns: Cooldown after action (default 4)
    - danger_radius_from_player: Safety distance (default 2)
    - preferred_distance_min/max: Hang-back range (default 4-7)
    - summon_monster_id: Monster to summon for raise actions
    - explosion_radius: AoE radius for explode action
    - explosion_damage_min/max: Damage range for explosions
    - explosion_damage_type: Damage type (default "necrotic")
    """
    
    def __init__(self):
        """Initialize necromancer base AI."""
        super().__init__()
        self.action_cooldown_remaining = 0
    
    def take_turn(self, target, fov_map, game_map, entities):
        """Execute one turn of necromancer AI behavior.
        
        Priority:
        1. If target within action range AND action off cooldown: Execute action
        2. Else if valid target exists but out of range: Seek target (respect danger radius)
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
        if self.action_cooldown_remaining > 0:
            self.action_cooldown_remaining -= 1
        
        # Get necromancer config
        action_enabled = getattr(self.owner, 'action_enabled', True)
        action_range = getattr(self.owner, 'action_range', 5)
        action_cooldown = getattr(self.owner, 'action_cooldown_turns', 4)
        danger_radius = getattr(self.owner, 'danger_radius_from_player', 2)
        preferred_min = getattr(self.owner, 'preferred_distance_min', 4)
        preferred_max = getattr(self.owner, 'preferred_distance_max', 7)
        
        # Try to execute action if enabled and off cooldown
        if action_enabled and self.action_cooldown_remaining <= 0:
            action_results = self._try_execute_action(
                target, game_map, entities, action_range, action_cooldown
            )
            if action_results:
                results.extend(action_results)
                # Action consumed the turn - return early
                status_effects = self.owner.get_component_optional(ComponentType.STATUS_EFFECTS)
                if status_effects:
                    end_results = status_effects.process_turn_end()
                    results.extend(end_results)
                return results
        
        # Try target-seeking movement if targets exist but out of range
        seek_results = self._try_target_seeking_movement(
            target, game_map, entities, action_range, danger_radius
        )
        if seek_results:
            results.extend(seek_results)
            # Movement consumed the turn - return early
            status_effects = self.owner.get_component_optional(ComponentType.STATUS_EFFECTS)
            if status_effects:
                end_results = status_effects.process_turn_end()
                results.extend(end_results)
            return results
        
        # Hang-back behavior or fallback to basic AI
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
    
    def _try_execute_action(
        self,
        target,
        game_map,
        entities: List,
        action_range: int,
        action_cooldown: int
    ) -> Optional[List]:
        """Attempt to execute the necromancer's primary action.
        
        This method should be overridden by subclasses to implement
        specific action behavior (raise, plague_raise, explode, etc.).
        
        Args:
            target: The player entity
            game_map: Game map
            entities: List of all entities
            action_range: Maximum range for action
            action_cooldown: Cooldown after successful action
            
        Returns:
            List of results if action attempted, None otherwise
        """
        raise NotImplementedError("Subclasses must implement _try_execute_action")
    
    def _try_target_seeking_movement(
        self,
        target,
        game_map,
        entities: List,
        action_range: int,
        danger_radius: int
    ) -> Optional[List]:
        """Attempt to move toward a valid target while respecting danger radius.
        
        This method should be overridden by subclasses to implement
        specific target selection logic (corpses, bone piles, spent corpses, etc.).
        
        Args:
            target: The player entity
            game_map: Game map
            entities: List of all entities
            action_range: Action range (to know if target is out of range)
            danger_radius: Never approach within this distance of player
            
        Returns:
            List of results if movement made, None otherwise
        """
        raise NotImplementedError("Subclasses must implement _try_target_seeking_movement")
    
    def _try_safe_target_approach(
        self,
        approach_target,
        player_target,
        game_map,
        entities: List,
        danger_radius: int,
        metric_name: str = "necro_seek_moves"
    ) -> Optional[List]:
        """Try to move toward target while maintaining safe distance from player.
        
        Args:
            approach_target: Target entity to approach
            player_target: Player entity
            game_map: Game map
            entities: List of all entities
            danger_radius: Never approach within this distance of player
            metric_name: Metric name for tracking successful moves
            
        Returns:
            List of results with move action, or None if no safe move
        """
        # Compute ideal step toward target
        dx = approach_target.x - self.owner.x
        dy = approach_target.y - self.owner.y
        
        # Normalize to get direction
        distance = math.sqrt(dx**2 + dy**2)
        if distance == 0:
            return None
        
        # Try primary direction
        step_x = 0 if abs(dx) < 0.5 else (1 if dx > 0 else -1)
        step_y = 0 if abs(dy) < 0.5 else (1 if dy > 0 else -1)
        
        # Try primary step
        if self._is_safe_move(step_x, step_y, player_target, game_map, entities, danger_radius):
            self._increment_metric(metric_name)
            return self._execute_move(step_x, step_y)
        
        # Try alternative steps (x-only, y-only)
        if step_x != 0 and self._is_safe_move(step_x, 0, player_target, game_map, entities, danger_radius):
            self._increment_metric(metric_name)
            return self._execute_move(step_x, 0)
        
        if step_y != 0 and self._is_safe_move(0, step_y, player_target, game_map, entities, danger_radius):
            self._increment_metric(metric_name)
            return self._execute_move(0, step_y)
        
        # No safe move found - record blocked attempt
        self._increment_metric("necro_unsafe_move_blocks")
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
    
    def _increment_metric(self, metric_name: str) -> None:
        """Increment a scenario metric if metrics are active.
        
        Args:
            metric_name: Name of metric to increment
        """
        try:
            from services.scenario_metrics import get_active_metrics_collector
            metrics = get_active_metrics_collector()
            if metrics:
                metrics.increment(metric_name)
        except Exception:
            pass  # Metrics are optional


