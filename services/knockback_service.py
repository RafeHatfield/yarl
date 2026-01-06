"""Knockback service - weapon-based knockback with power-delta scaled distance.

Implements knockback mechanics for weapon attacks:
- Distance based on attacker vs defender power delta (cap 4 tiles)
- Staggered micro-stun when blocked early by hard obstacle
- Uses canonical movement execution (respects entangle/root/etc)
- Works for both player and monsters
"""

from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from entity import Entity
    from map_objects.game_map import GameMap


def _get_metrics_collector():
    """Get active scenario metrics collector if available."""
    try:
        from services.scenario_metrics import get_active_metrics_collector
        return get_active_metrics_collector()
    except Exception:
        return None


def calculate_knockback_distance(attacker_power: int, defender_power: int) -> int:
    """Calculate knockback distance based on power delta.
    
    Distance mapping (cap 4):
    - delta <= -1 → 1 tile
    - delta in [0, 1] → 2 tiles
    - delta in [2, 3] → 3 tiles
    - delta >= 4 → 4 tiles
    
    Args:
        attacker_power: Attacker's power stat
        defender_power: Defender's power stat
    
    Returns:
        Knockback distance in tiles (1-4)
    """
    delta = attacker_power - defender_power
    
    if delta <= -1:
        return 1
    elif delta <= 1:  # 0 or 1
        return 2
    elif delta <= 3:  # 2 or 3
        return 3
    else:  # >= 4
        return 4


def apply_knockback(
    attacker: 'Entity',
    defender: 'Entity',
    game_map: 'GameMap',
    entities: List['Entity']
) -> List[Dict[str, Any]]:
    """Apply knockback to defender after successful weapon hit.
    
    Pushes defender directly away from attacker using sign of (dx, dy).
    Attempts to move step-by-step up to computed distance.
    Stops early if blocked by solid terrain/wall or occupied tile.
    Applies stagger if blocked early by hard obstacle.
    
    Args:
        attacker: Entity delivering the knockback
        defender: Entity being knocked back
        game_map: Game map for terrain checks
        entities: List of all entities for blocking checks
    
    Returns:
        List of result dictionaries with messages and effects
    """
    results = []
    collector = _get_metrics_collector()
    
    # Safety checks
    if not attacker or not defender:
        return results
    if not game_map or not entities:
        return results
    
    # Get attacker and defender power
    from components.component_registry import ComponentType
    attacker_fighter = attacker.get_component_optional(ComponentType.FIGHTER)
    defender_fighter = defender.get_component_optional(ComponentType.FIGHTER)
    
    if not attacker_fighter or not defender_fighter:
        return results  # Can't apply knockback without fighter components
    
    # Calculate knockback distance
    distance = calculate_knockback_distance(attacker_fighter.power, defender_fighter.power)
    
    # Record knockback application
    if collector:
        collector.increment('knockback_applications')
    
    # Calculate knockback direction (sign of dx, dy)
    dx = defender.x - attacker.x
    dy = defender.y - attacker.y
    
    # Normalize to direction (-1, 0, 1)
    if dx != 0:
        dx = 1 if dx > 0 else -1
    if dy != 0:
        dy = 1 if dy > 0 else -1
    
    # Apply knockback step-by-step
    tiles_moved = 0
    blocked_early = False
    blocking_entity = None  # Track what blocked the knockback (for messaging)
    
    for step in range(distance):
        target_x = defender.x + dx
        target_y = defender.y + dy
        
        # Check if target position is valid
        can_move, blocker = _can_move_to(defender, target_x, target_y, game_map, entities)
        if not can_move:
            # Blocked by hard obstacle
            blocked_early = True
            blocking_entity = blocker  # None = wall, Entity = collision
            break
        
        # Move defender using canonical movement (respects entangle/root/etc)
        move_success = _execute_move(defender, target_x, target_y)
        
        if move_success:
            tiles_moved += 1
            if collector:
                collector.increment('knockback_tiles_moved')
        else:
            # Movement blocked by effect (entangle/root/etc)
            # This is NOT a "hard block" - don't apply stagger
            break
    
    # Report knockback result
    if tiles_moved > 0:
        from message_builder import MessageBuilder as MB
        results.append({
            'message': MB.combat(f"{defender.name} is knocked back {tiles_moved} tiles!")
        })
    
    # Apply stagger if blocked early by hard obstacle
    if blocked_early and tiles_moved < distance:
        if collector:
            collector.increment('knockback_blocked_events')
        
        # Apply StaggeredEffect (only to the shoved entity, not the blocker)
        from components.status_effects import StaggeredEffect, StatusEffectManager
        
        # Ensure defender has status_effects component
        if not defender.components.has(ComponentType.STATUS_EFFECTS):
            defender.status_effects = StatusEffectManager(defender)
            defender.components.add(ComponentType.STATUS_EFFECTS, defender.status_effects)
        
        # Apply stagger
        stagger = StaggeredEffect(owner=defender)
        stagger_results = defender.status_effects.add_effect(stagger)
        
        # Add blocked message (different for wall vs entity collision)
        from message_builder import MessageBuilder as MB
        if blocking_entity:
            # Collision with another entity
            results.append({
                'message': MB.warning(f"{defender.name} collides with {blocking_entity.name} and is staggered!")
            })
        else:
            # Impact with wall/terrain
            results.append({
                'message': MB.warning(f"{defender.name} slams into the wall and is staggered!")
            })
        
        results.extend(stagger_results)
    
    return results


def _can_move_to(
    entity: 'Entity',
    target_x: int,
    target_y: int,
    game_map: 'GameMap',
    entities: List['Entity']
) -> Tuple[bool, Optional['Entity']]:
    """Check if entity can move to target position (hard block check).
    
    Checks for:
    - Solid terrain/wall
    - Occupied tile by another entity
    
    Does NOT check for movement effects (entangle/root) - those are handled
    by the canonical movement execution.
    
    Args:
        entity: Entity attempting to move
        target_x: Target X coordinate
        target_y: Target Y coordinate
        game_map: Game map for terrain checks
        entities: List of all entities for blocking checks
    
    Returns:
        Tuple of (can_move, blocking_entity):
        - can_move: True if position is valid for movement, False if hard blocked
        - blocking_entity: Entity that blocked movement (None if wall/terrain)
    """
    # Safety check: ensure game_map has tiles
    if not game_map or not hasattr(game_map, 'tiles') or game_map.tiles is None:
        return (False, None)
    
    # Check map bounds
    if target_x < 0 or target_x >= game_map.width or target_y < 0 or target_y >= game_map.height:
        return (False, None)
    
    # Check if tile is walkable (not a wall)
    if game_map.tiles[target_x][target_y].blocked:
        return (False, None)
    
    # Check if tile is occupied by another entity
    for other in entities:
        if other != entity and other.x == target_x and other.y == target_y and other.blocks:
            return (False, other)  # Blocked by entity
    
    return (True, None)


def _execute_move(entity: 'Entity', target_x: int, target_y: int) -> bool:
    """Execute movement using canonical Entity.move() method.
    
    This respects all movement blockers (entangle/root/etc) via the
    entity's move() method, which checks status effects.
    
    Args:
        entity: Entity to move
        target_x: Target X coordinate
        target_y: Target Y coordinate
    
    Returns:
        True if move succeeded, False if blocked by effect
    """
    # Calculate direction
    dx = target_x - entity.x
    dy = target_y - entity.y
    
    # Use canonical move() which respects status effects
    # entity.move() returns None, but updates position if successful
    old_x, old_y = entity.x, entity.y
    
    # Call move - it will check entangle/root/etc and update position if allowed
    entity.move(dx, dy)
    
    # Check if position actually changed
    return entity.x != old_x or entity.y != old_y

