"""Mouse movement handling for click-to-move functionality.

This module provides functions to handle mouse clicks and convert them
into movement commands for the player pathfinding system.
"""

from typing import Tuple, Optional, List, TYPE_CHECKING
import logging

from game_messages import Message
from entity import get_blocking_entities_at_location

if TYPE_CHECKING:
    from entity import Entity
    from map_objects.game_map import GameMap
    from components.player_pathfinding import PlayerPathfinding

logger = logging.getLogger(__name__)


def handle_mouse_click(click_x: int, click_y: int, player: 'Entity', 
                      entities: List['Entity'], game_map: 'GameMap') -> dict:
    """Handle a mouse click for movement or combat.
    
    This function processes mouse clicks and determines the appropriate action:
    - Click on empty tile: Start pathfinding movement
    - Click on adjacent enemy: Attack the enemy
    - Click on non-adjacent enemy: Show message (future: pathfind to attack)
    - Click on invalid location: Show error message
    
    Args:
        click_x (int): X coordinate of mouse click
        click_y (int): Y coordinate of mouse click  
        player (Entity): The player entity
        entities (List[Entity]): List of all entities
        game_map (GameMap): The game map
        
    Returns:
        dict: Dictionary containing action results and messages
    """
    results = []
    
    # Validate click coordinates
    if not _is_valid_click(click_x, click_y, game_map):
        results.append({
            "message": Message("You cannot move there.", (255, 255, 0))
        })
        return {"results": results}
    
    # Check if there's an entity at the clicked location
    target_entity = get_blocking_entities_at_location(entities, click_x, click_y)
    
    if target_entity and target_entity.fighter:
        # Clicked on an entity with a fighter component (enemy)
        return _handle_enemy_click(player, target_entity, results)
    else:
        # Clicked on empty space - attempt movement
        return _handle_movement_click(click_x, click_y, player, entities, game_map, results)


def _handle_enemy_click(player: 'Entity', target: 'Entity', results: list) -> dict:
    """Handle clicking on an enemy entity.
    
    Args:
        player (Entity): The player entity
        target (Entity): The target enemy entity
        results (list): List to append results to
        
    Returns:
        dict: Dictionary containing action results
    """
    # Calculate distance to target
    distance = player.distance_to(target)
    
    if distance <= 1.5:  # Adjacent (including diagonals)
        # Attack the target
        if player.fighter:
            attack_results = player.fighter.attack(target)
            results.extend(attack_results)
            results.append({
                "enemy_turn": True  # Trigger enemy turn after attack
            })
        else:
            results.append({
                "message": Message("You cannot attack.", (255, 255, 0))
            })
    else:
        # Too far to attack
        results.append({
            "message": Message(f"The {target.name} is too far away to attack.", (255, 255, 0))
        })
    
    return {"results": results}


def _handle_movement_click(click_x: int, click_y: int, player: 'Entity', 
                          entities: List['Entity'], game_map: 'GameMap', results: list) -> dict:
    """Handle clicking on empty space for movement.
    
    Args:
        click_x (int): X coordinate of click
        click_y (int): Y coordinate of click
        player (Entity): The player entity
        entities (List[Entity]): List of all entities
        game_map (GameMap): The game map
        results (list): List to append results to
        
    Returns:
        dict: Dictionary containing action results
    """
    # Check if player has pathfinding component
    if not hasattr(player, 'pathfinding') or not player.pathfinding:
        results.append({
            "message": Message("Player pathfinding not available.", (255, 0, 0))
        })
        return {"results": results}
    
    # Attempt to set destination
    if player.pathfinding.set_destination(click_x, click_y, game_map, entities):
        # Successfully set path
        distance = player.distance(click_x, click_y)
        results.append({
            "message": Message(f"Moving to ({click_x}, {click_y})...", (0, 255, 0))
        })
        results.append({
            "start_pathfinding": True  # Signal to start pathfinding movement
        })
        logger.debug(f"Started pathfinding to ({click_x}, {click_y}), distance: {distance:.1f}")
    else:
        # Could not find path
        results.append({
            "message": Message("Cannot reach that location.", (255, 255, 0))
        })
        logger.debug(f"No path found to ({click_x}, {click_y})")
    
    return {"results": results}


def _is_valid_click(x: int, y: int, game_map: 'GameMap') -> bool:
    """Check if click coordinates are valid.
    
    Args:
        x (int): X coordinate
        y (int): Y coordinate
        game_map (GameMap): The game map
        
    Returns:
        bool: True if coordinates are valid
    """
    # Check bounds
    if x < 0 or y < 0 or x >= game_map.width or y >= game_map.height:
        return False
    
    return True


def process_pathfinding_movement(player: 'Entity', entities: List['Entity'], 
                                game_map: 'GameMap', fov_map) -> dict:
    """Process one step of pathfinding movement.
    
    This function should be called during the player's turn when they are
    following a pathfinding route. It handles:
    - Moving to the next step in the path
    - Checking for enemies in FOV (interruption)
    - Completing or continuing movement
    
    Args:
        player (Entity): The player entity
        entities (List[Entity]): List of all entities
        game_map (GameMap): The game map
        fov_map: Field of view map for enemy detection
        
    Returns:
        dict: Dictionary containing movement results and messages
    """
    results = []
    
    if not hasattr(player, 'pathfinding') or not player.pathfinding:
        return {"results": results}
    
    pathfinding = player.pathfinding
    
    if not pathfinding.is_path_active():
        return {"results": results}
    
    # Check for enemies in FOV before moving
    if _check_for_enemies_in_fov(player, entities, fov_map):
        pathfinding.interrupt_movement("Enemy spotted")
        results.append({
            "message": Message("Movement stopped - enemy spotted!", (255, 255, 0))
        })
        return {"results": results}
    
    # Get next move
    next_pos = pathfinding.get_next_move()
    if next_pos is None:
        # Movement completed
        results.append({
            "message": Message("Arrived at destination.", (0, 255, 0))
        })
        return {"results": results}
    
    next_x, next_y = next_pos
    
    # Validate the move is still possible
    if game_map.is_blocked(next_x, next_y):
        pathfinding.interrupt_movement("Path blocked")
        results.append({
            "message": Message("Path blocked - movement stopped.", (255, 255, 0))
        })
        return {"results": results}
    
    # Check for entities at destination
    blocking_entity = get_blocking_entities_at_location(entities, next_x, next_y)
    if blocking_entity:
        pathfinding.interrupt_movement("Entity blocking path")
        results.append({
            "message": Message(f"Path blocked by {blocking_entity.name}.", (255, 255, 0))
        })
        return {"results": results}
    
    # Move player
    player.move(next_x - player.x, next_y - player.y)
    
    # Request FOV recompute for next check
    results.append({
        "fov_recompute": True
    })
    
    # Continue movement if path is still active
    if pathfinding.is_path_active():
        results.append({
            "continue_pathfinding": True
        })
    else:
        results.append({
            "message": Message("Arrived at destination.", (0, 255, 0))
        })
    
    return {"results": results}


def _check_for_enemies_in_fov(player: 'Entity', entities: List['Entity'], fov_map) -> bool:
    """Check if any enemies are visible in the player's FOV.
    
    Args:
        player (Entity): The player entity
        entities (List[Entity]): List of all entities
        fov_map: Field of view map
        
    Returns:
        bool: True if any enemies are visible
    """
    from fov_functions import map_is_in_fov
    
    for entity in entities:
        if (entity != player and entity.fighter and 
            map_is_in_fov(fov_map, entity.x, entity.y)):
            return True
    
    return False
