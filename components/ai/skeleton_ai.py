"""Phase 19: Skeleton AI - Formation-based combat AI

Skeletons prefer to group up to maximize their shield wall AC bonus.
They will attempt to form defensive walls while still engaging the player.
"""

from typing import Optional, List, TYPE_CHECKING
from components.ai.basic_monster import BasicMonster
from logger_config import get_logger

if TYPE_CHECKING:
    from entity import Entity

logger = get_logger(__name__)


class SkeletonAI(BasicMonster):
    """AI for skeletons that prefers formation fighting.
    
    Phase 19: Skeletons try to group up to maximize shield wall AC bonus.
    They will:
    - Move toward skeleton allies when not adjacent to any
    - Prefer moves that maintain/increase adjacency when multiple options exist
    - Still attack the player when in range (combat takes priority)
    """
    
    def __init__(self):
        """Initialize Skeleton AI."""
        super().__init__()
        self.formation_preference = True  # Prefer staying in formation
    
    def take_turn(self, target, fov_map, game_map, entities):
        """Execute one turn of skeleton AI behavior.
        
        Overrides BasicMonster to add formation-seeking behavior.
        
        Args:
            target: The target entity (usually the player)
            fov_map: Field of view map
            game_map: Game map
            entities: List of all entities
            
        Returns:
            list: List of result dictionaries
        """
        # Update shield wall cache before taking action
        from services.skeleton_service import update_skeleton_shield_wall_cache
        update_skeleton_shield_wall_cache(self.owner, entities)
        
        # Check if we should use formation logic
        # Only use formation AI when:
        # 1. Not in immediate attack range of target
        # 2. Can see the player (aware)
        # 3. Not immobilized or otherwise prevented from moving
        
        from components.component_registry import ComponentType
        from components.ai._helpers import get_weapon_reach
        
        # Check weapon reach for attack range
        distance = self.owner.chebyshev_distance_to(target)
        weapon_reach = get_weapon_reach(self.owner)
        
        # If in attack range, use normal combat behavior
        if distance <= weapon_reach:
            return super().take_turn(target, fov_map, game_map, entities)
        
        # Check if we can see the player
        from fov_functions import map_is_in_fov
        can_see_player = map_is_in_fov(fov_map, self.owner.x, self.owner.y)
        
        if not can_see_player and not self.in_combat:
            # Can't see player and not in combat - use normal behavior
            return super().take_turn(target, fov_map, game_map, entities)
        
        # Check for status effects that prevent movement
        if (hasattr(self.owner, 'has_status_effect') and 
            callable(self.owner.has_status_effect)):
            if self.owner.has_status_effect('paralysis'):
                return super().take_turn(target, fov_map, game_map, entities)
            if self.owner.has_status_effect('immobilized'):
                return super().take_turn(target, fov_map, game_map, entities)
        
        # Try formation movement
        formation_results = self._try_formation_movement(target, game_map, entities)
        if formation_results is not None:
            # Formation movement succeeded - process status effects and return
            status_effects = self.owner.get_component_optional(ComponentType.STATUS_EFFECTS)
            if status_effects:
                end_results = status_effects.process_turn_end()
                formation_results.extend(end_results)
            return formation_results
        
        # Formation movement failed or not beneficial - use normal behavior
        return super().take_turn(target, fov_map, game_map, entities)
    
    def _try_formation_movement(self, target, game_map, entities) -> Optional[List]:
        """Try to move in a way that improves formation.
        
        Args:
            target: Target entity (player)
            game_map: Game map
            entities: List of all entities
            
        Returns:
            list: Results if formation movement taken, None if should use normal movement
        """
        from services.skeleton_service import (
            count_adjacent_skeleton_allies,
            find_best_formation_move
        )
        from components.monster_action_logger import MonsterActionLogger
        
        results = []
        
        # Count current adjacent allies
        current_adjacent = count_adjacent_skeleton_allies(self.owner, entities)
        
        # If we have 0 adjacent allies, try to move toward formation
        # If we have 1+ adjacent allies, prefer moves that maintain/increase adjacency
        
        # Find best formation move
        target_pos = (target.x, target.y)
        best_move = find_best_formation_move(self.owner, entities, game_map, target_pos)
        
        if best_move == (0, 0):
            # No good formation move found - use normal pathfinding
            return None
        
        dx, dy = best_move
        new_x = self.owner.x + dx
        new_y = self.owner.y + dy
        
        # Check if this move improves our situation
        # Temporarily move to check adjacency
        old_x, old_y = self.owner.x, self.owner.y
        self.owner.x, self.owner.y = new_x, new_y
        new_adjacent = count_adjacent_skeleton_allies(self.owner, entities)
        self.owner.x, self.owner.y = old_x, old_y
        
        # Only use formation movement if it improves adjacency OR maintains it while moving toward player
        distance_to_target = abs(old_x - target.x) + abs(old_y - target.y)
        new_distance_to_target = abs(new_x - target.x) + abs(new_y - target.y)
        
        moving_toward_player = new_distance_to_target < distance_to_target
        
        if new_adjacent > current_adjacent:
            # Improves formation - take this move
            self.owner.move(dx, dy)
            MonsterActionLogger.log_turn_summary(self.owner, ["formation_movement_improve"])
            logger.debug(f"[SKELETON AI] {self.owner.name} moved to improve formation: {current_adjacent} → {new_adjacent} adjacent")
            return results
        elif new_adjacent == current_adjacent and current_adjacent > 0 and moving_toward_player:
            # Maintains formation while moving toward player - good move
            self.owner.move(dx, dy)
            MonsterActionLogger.log_turn_summary(self.owner, ["formation_movement_maintain"])
            logger.debug(f"[SKELETON AI] {self.owner.name} moved toward player while maintaining formation")
            return results
        elif current_adjacent == 0 and moving_toward_player:
            # No formation yet, but moving toward player - use normal pathfinding
            # This prevents skeletons from wandering away from combat to find allies
            return None
        
        # Formation move doesn't help - use normal pathfinding
        return None
