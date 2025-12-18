"""Phase 19: Skeleton Shield Wall Service

Provides utilities for skeleton identity mechanics:
- Shield wall AC bonus calculation (4-way adjacency)
- Formation awareness for AI
"""

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from entity import Entity


def count_adjacent_skeleton_allies(entity: 'Entity', entities: List['Entity']) -> int:
    """Count adjacent skeleton allies using 4-way adjacency (N, S, E, W).
    
    Phase 19: Used for shield wall AC bonus calculation.
    
    Args:
        entity: The skeleton entity to check
        entities: List of all entities on the map
        
    Returns:
        int: Number of adjacent skeleton allies (0-4)
    """
    if not entity or not entities:
        return 0
    
    # Check if this entity is a skeleton
    if not _is_skeleton(entity):
        return 0
    
    adjacent_count = 0
    
    # 4-way adjacency offsets: North, South, East, West
    offsets = [
        (0, -1),  # North
        (0, 1),   # South
        (1, 0),   # East
        (-1, 0),  # West
    ]
    
    for dx, dy in offsets:
        check_x = entity.x + dx
        check_y = entity.y + dy
        
        # Check if there's a skeleton ally at this position
        for other in entities:
            if other == entity:
                continue
            
            if other.x == check_x and other.y == check_y:
                # Check if it's a skeleton ally
                if _is_skeleton(other) and _are_allies(entity, other):
                    # Check if alive
                    from components.component_registry import ComponentType
                    fighter = other.get_component_optional(ComponentType.FIGHTER)
                    if fighter and fighter.hp > 0:
                        adjacent_count += 1
                        break  # Only count one entity per tile
    
    return adjacent_count


def update_skeleton_shield_wall_cache(entity: 'Entity', entities: List['Entity']) -> None:
    """Update the cached adjacent skeleton count for shield wall AC calculation.
    
    Phase 19: This should be called before combat/AC checks to ensure accurate AC.
    
    Args:
        entity: The skeleton entity to update
        entities: List of all entities on the map
    """
    if not entity or not _is_skeleton(entity):
        return
    
    adjacent_count = count_adjacent_skeleton_allies(entity, entities)
    entity._cached_adjacent_skeleton_count = adjacent_count


def update_all_skeleton_caches(entities: List['Entity']) -> None:
    """Update shield wall caches for all skeletons on the map.
    
    Phase 19: Call this at the start of each turn to keep AC calculations accurate.
    
    Args:
        entities: List of all entities on the map
    """
    for entity in entities:
        if _is_skeleton(entity):
            update_skeleton_shield_wall_cache(entity, entities)


def _is_skeleton(entity: 'Entity') -> bool:
    """Check if an entity is a skeleton.
    
    Args:
        entity: Entity to check
        
    Returns:
        bool: True if entity is a skeleton
    """
    if not entity:
        return False
    
    # Check for shieldwall_ac_per_adjacent attribute (skeleton identity)
    if hasattr(entity, 'shieldwall_ac_per_adjacent'):
        return getattr(entity, 'shieldwall_ac_per_adjacent', 0) > 0
    
    # Fallback: check name
    if hasattr(entity, 'name'):
        name_lower = entity.name.lower()
        return 'skeleton' in name_lower
    
    return False


def _are_allies(entity1: 'Entity', entity2: 'Entity') -> bool:
    """Check if two entities are allies (same faction).
    
    Args:
        entity1: First entity
        entity2: Second entity
        
    Returns:
        bool: True if entities are allies
    """
    if not entity1 or not entity2:
        return False
    
    # Check faction
    faction1 = getattr(entity1, 'faction', None)
    faction2 = getattr(entity2, 'faction', None)
    
    if faction1 and faction2:
        return faction1 == faction2
    
    return False


def find_best_formation_move(entity: 'Entity', entities: List['Entity'], game_map, 
                             target_pos: tuple) -> tuple:
    """Find the best move for a skeleton to maximize shield wall formation.
    
    Phase 19: Used by skeleton AI to prefer moves that increase adjacency.
    
    Args:
        entity: The skeleton entity
        entities: List of all entities
        game_map: Game map for walkability checks
        target_pos: Target position (usually player) as (x, y) tuple
        
    Returns:
        tuple: (dx, dy) move offset, or (0, 0) if no good move found
    """
    if not entity or not _is_skeleton(entity):
        return (0, 0)
    
    # Get all possible moves (8-way movement)
    possible_moves = [
        (-1, -1), (0, -1), (1, -1),
        (-1, 0),           (1, 0),
        (-1, 1),  (0, 1),  (1, 1),
    ]
    
    best_move = (0, 0)
    best_score = -999
    
    current_adjacent = count_adjacent_skeleton_allies(entity, entities)
    
    for dx, dy in possible_moves:
        new_x = entity.x + dx
        new_y = entity.y + dy
        
        # Check if move is valid
        if not _is_valid_move(new_x, new_y, game_map, entities):
            continue
        
        # Calculate score for this move
        # Temporarily move entity to check adjacency
        old_x, old_y = entity.x, entity.y
        entity.x, entity.y = new_x, new_y
        
        new_adjacent = count_adjacent_skeleton_allies(entity, entities)
        
        # Restore position
        entity.x, entity.y = old_x, old_y
        
        # Score: prioritize increasing adjacency, then distance to target
        adjacency_score = new_adjacent * 10  # High weight for formation
        
        # Distance to target (negative because closer is better)
        if target_pos:
            target_x, target_y = target_pos
            distance = abs(new_x - target_x) + abs(new_y - target_y)
            distance_score = -distance
        else:
            distance_score = 0
        
        total_score = adjacency_score + distance_score
        
        if total_score > best_score:
            best_score = total_score
            best_move = (dx, dy)
    
    return best_move


def _is_valid_move(x: int, y: int, game_map, entities: List['Entity']) -> bool:
    """Check if a position is valid for movement.
    
    Args:
        x: X coordinate
        y: Y coordinate
        game_map: Game map
        entities: List of entities
        
    Returns:
        bool: True if position is walkable and not blocked
    """
    # Check bounds
    if x < 0 or x >= game_map.width or y < 0 or y >= game_map.height:
        return False
    
    # Check if blocked by terrain
    if game_map.is_blocked(x, y):
        return False
    
    # Check if blocked by entity
    for entity in entities:
        if entity.x == x and entity.y == y and entity.blocks:
            return False
    
    return True
