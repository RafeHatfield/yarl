"""Phase 19: Split Under Pressure - Slime splitting service.

This module handles the new slime splitting mechanic where slimes split when HP
falls below a threshold (not on death).

═══════════════════════════════════════════════════════════════════════════════
MODULE CONTRACT: Split Under Pressure
───────────────────────────────────────────────────────────────────────────────

OWNERSHIP:
  - Slime splitting at low HP threshold
  - Tiered child type spawning (minor -> normal -> greater)
  - Weighted random child count selection
  - One-time split guard to prevent double-splitting

KEY CONTRACTS:
  - Split triggers ONLY when HP < split_trigger_hp_pct
  - Original slime is removed (effectively dies) when split triggers
  - Spawns >= 1 children (never 0)
  - Split happens at most ONCE per slime
  - Uses deterministic RNG (existing game random pathways)

INTEGRATION:
  - Called from Fighter.take_damage() after HP reduction
  - Spawned entities added to game_state.entities by caller
  - Returns message for combat log

WHEN CHANGING BEHAVIOR:
  - Update tests/test_slime_split_under_pressure.py
  - Verify balance suite still passes
  - Check that split never triggers twice on same entity

SEE ALSO:
  - components/fighter.py - take_damage() integration point
  - config/entities.yaml - slime split configuration
  - death_functions.py - split-on-death removed in Phase 19
═══════════════════════════════════════════════════════════════════════════════
"""

import random
from typing import List, Optional, Tuple, Dict, Any

from message_builder import MessageBuilder as MB


def check_split_trigger(entity, game_map=None, entities=None) -> Optional[Dict[str, Any]]:
    """Check if an entity should trigger Split Under Pressure.
    
    Called after HP damage is applied. If conditions are met:
    - Entity has split config (split_trigger_hp_pct, split_child_type, etc.)
    - HP has fallen below the threshold
    - Entity has not already split (_has_split flag)
    
    Then prepare split data to be executed by the caller.
    
    Args:
        entity: The entity to check (typically a slime)
        game_map: Game map for spawn position validation
        entities: List of all entities to avoid spawn collisions
        
    Returns:
        Dict with split data if split should trigger, None otherwise.
        Split data includes:
            - 'original_entity': The entity that is splitting
            - 'child_type': Monster type to spawn
            - 'num_children': How many children to spawn
            - 'spawn_positions': List of (x, y) tuples for spawns
            - 'message': Combat log message
    """
    # Guard: Has entity already split?
    if hasattr(entity, '_has_split') and entity._has_split:
        return None
    
    # Check if entity has split configuration
    if not hasattr(entity, 'split_trigger_hp_pct') or entity.split_trigger_hp_pct is None:
        return None
    
    # Get fighter component to check HP
    from components.component_registry import ComponentType
    fighter = entity.get_component_optional(ComponentType.FIGHTER)
    if not fighter:
        return None
    
    # Check if HP has fallen below threshold
    hp_pct = fighter.hp / fighter.max_hp if fighter.max_hp > 0 else 0
    if hp_pct >= entity.split_trigger_hp_pct:
        return None  # Still above threshold
    
    # Split triggered! Mark entity so it can't split again
    entity._has_split = True
    
    # Determine number of children to spawn
    num_children = _determine_child_count(entity)
    
    # Prepare split data
    # Note: Spawn positions will be calculated during execute_split()
    # when we have access to game_map and entities
    split_data = {
        'original_entity': entity,
        'child_type': entity.split_child_type,
        'num_children': num_children,
        'message': MB.custom(
            f"{entity.name.capitalize()} splits under pressure into {num_children} smaller slimes!",
            (0, 255, 0)  # Bright green for special event
        )
    }
    
    return split_data


def execute_split(split_data: Dict[str, Any], game_map=None, entities=None) -> List:
    """Execute a slime split, creating child entities.
    
    Args:
        split_data: Split data from check_split_trigger()
        game_map: Game map (for spawn position validation)
        entities: List of all entities (for collision checking and removal)
        
    Returns:
        List of newly spawned child entities
    """
    from config.factories import get_entity_factory
    
    entity_factory = get_entity_factory()
    spawned_children = []
    
    original = split_data['original_entity']
    child_type = split_data['child_type']
    num_children = split_data['num_children']
    
    # Calculate spawn positions NOW (when we have game_map/entities)
    # Exclude the splitting entity from blocking check (it will be removed)
    entities_excluding_self = [e for e in (entities or []) if e != original]
    spawn_positions = _get_valid_spawn_positions(
        original.x, original.y, game_map, num_children, entities_excluding_self
    )
    
    # Spawn children at calculated positions
    actual_children = min(num_children, len(spawn_positions))
    for i in range(actual_children):
        x, y = spawn_positions[i]
        # Create child slime
        child = entity_factory.create_monster(child_type, x, y)
        if child:
            spawned_children.append(child)
    
    # Remove original entity (it "died" by splitting)
    if entities and original in entities:
        entities.remove(original)
    
    return spawned_children


def _determine_child_count(entity) -> int:
    """Determine how many children to spawn using weighted random selection.
    
    Uses entity.split_min_children, split_max_children, and split_weights.
    
    Args:
        entity: The entity that is splitting
        
    Returns:
        Number of children to spawn (>= 1)
    """
    min_children = getattr(entity, 'split_min_children', 2)
    max_children = getattr(entity, 'split_max_children', 3)
    weights = getattr(entity, 'split_weights', None)
    
    # If no weights specified, uniform random
    if not weights:
        return random.randint(min_children, max_children)
    
    # Weighted selection
    # weights[i] corresponds to (min_children + i) children
    num_options = max_children - min_children + 1
    
    # Ensure weights list matches number of options
    if len(weights) != num_options:
        # Fallback to uniform if misconfigured
        return random.randint(min_children, max_children)
    
    # Use random.choices for weighted selection
    options = list(range(min_children, max_children + 1))
    selected = random.choices(options, weights=weights, k=1)[0]
    
    return selected


def _get_valid_spawn_positions(center_x: int, center_y: int, game_map, max_positions: int, entities=None) -> List[Tuple[int, int]]:
    """Get valid positions around a center point for spawning entities.
    
    Searches in expanding rings around the center, avoiding blocked tiles
    and occupied positions.
    
    Args:
        center_x: X coordinate of center position
        center_y: Y coordinate of center position  
        game_map: Game map to check for valid tiles
        max_positions: Maximum number of positions to return
        entities: List of all entities to check for occupied tiles
        
    Returns:
        List of (x, y) tuples for valid spawn positions.
        Guaranteed to return at least 1 position (center as fallback).
    """
    if not game_map:
        return [(center_x, center_y)]  # Fallback to center if no map
    
    valid_positions = []
    
    # Check positions in expanding rings around the center
    for radius in range(1, 4):  # Check up to 3 tiles away
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                # Skip positions not on the current radius ring
                if abs(dx) != radius and abs(dy) != radius:
                    continue
                    
                x, y = center_x + dx, center_y + dy
                
                # Check bounds and if tile is blocked
                if (0 <= x < game_map.width and 0 <= y < game_map.height and
                    not game_map.tiles[x][y].blocked):
                    
                    # Check if position is occupied by an entity
                    position_occupied = False
                    if entities:
                        for entity in entities:
                            if entity.x == x and entity.y == y and entity.blocks:
                                position_occupied = True
                                break
                    
                    # Only add if not occupied
                    if not position_occupied:
                        valid_positions.append((x, y))
                        
                        if len(valid_positions) >= max_positions:
                            return valid_positions
    
    # If we couldn't find enough positions, return what we have
    # If no valid positions found, fall back to center (shouldn't happen but safety)
    return valid_positions if valid_positions else [(center_x, center_y)]

