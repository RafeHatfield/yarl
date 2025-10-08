"""Mouse movement handling for click-to-move functionality.

This module provides functions to handle mouse clicks and convert them
into movement commands for the player pathfinding system.
"""

from typing import Tuple, Optional, List, TYPE_CHECKING
import logging

from game_messages import Message
from entity import get_blocking_entities_at_location
from components.component_registry import ComponentType

if TYPE_CHECKING:
    from entity import Entity
    from map_objects.game_map import GameMap
    from components.player_pathfinding import PlayerPathfinding

logger = logging.getLogger(__name__)


def handle_mouse_click(click_x: int, click_y: int, player: 'Entity', 
                      entities: List['Entity'], game_map: 'GameMap', fov_map=None) -> dict:
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
        fov_map: Optional FOV map for smart pathfinding limits
        
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
        return _handle_movement_click(click_x, click_y, player, entities, game_map, results, fov_map)


def _get_weapon_reach(entity: 'Entity') -> int:
    """Get the reach of the entity's equipped weapon.
    
    Args:
        entity (Entity): The entity to check
        
    Returns:
        int: The reach of the weapon in tiles (default 1 for adjacent)
    """
    equipment = entity.components.get(ComponentType.EQUIPMENT)
    if (equipment and equipment.main_hand and 
        equipment.main_hand.components.has(ComponentType.EQUIPPABLE)):
        weapon = equipment.main_hand.equippable
        return getattr(weapon, 'reach', 1)
    return 1  # Default reach for unarmed/no weapon


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
    
    # Get weapon reach (default 1 for adjacent, 2 for spear, etc.)
    weapon_reach = _get_weapon_reach(player)
    max_attack_distance = weapon_reach * 1.5  # 1.5 for diagonals (e.g., spear: 2 * 1.5 = 3.0)
    
    if distance <= max_attack_distance:
        # Within reach - attack the target
        if player.fighter:
            attack_results = player.fighter.attack_d20(target)
            results.extend(attack_results)
            results.append({
                "enemy_turn": True  # Trigger enemy turn after attack
            })
        else:
            results.append({
                "message": Message("You cannot attack.", (255, 255, 0))
            })
    else:
        # Too far to attack - pathfind toward the enemy instead
        results.append({
            "message": Message(f"Moving toward the {target.name}...", (255, 255, 0))
        })
        # Set pathfinding destination to the enemy's location
        # This will be handled by the movement system
        results.append({
            "pathfind_to_enemy": (target.x, target.y)
        })
    
    return {"results": results}


def _handle_movement_click(click_x: int, click_y: int, player: 'Entity', 
                          entities: List['Entity'], game_map: 'GameMap', results: list, fov_map=None) -> dict:
    """Handle clicking on empty space for movement.
    
    Args:
        click_x (int): X coordinate of click
        click_y (int): Y coordinate of click
        player (Entity): The player entity
        entities (List[Entity]): List of all entities
        game_map (GameMap): The game map
        results (list): List to append results to
        fov_map: Optional FOV map for smart pathfinding limits
        
    Returns:
        dict: Dictionary containing action results
    """
    # Check if player has pathfinding component
    pathfinding = player.components.get(ComponentType.PATHFINDING)
    if not pathfinding:
        results.append({
            "message": Message("Player pathfinding not available.", (255, 0, 0))
        })
        return {"results": results}

    # Attempt to set destination (with FOV awareness)
    if pathfinding.set_destination(click_x, click_y, game_map, entities, fov_map):
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
    - Interrupting on ground hazards (fire, poison gas)
    - Checking for enemies in FOV (interruption)
    - Auto-attacking enemies within weapon range
    - Completing or continuing movement
    
    Movement interrupts when:
    - Player steps on a ground hazard (damage tile)
    - Enemy comes into weapon range (auto-attack)
    - Enemy spotted within threat range (stops movement)
    
    Args:
        player (Entity): The player entity
        entities (List[Entity]): List of all entities
        game_map (GameMap): The game map (may include hazard_manager)
        fov_map: Field of view map for enemy detection
        
    Returns:
        dict: Dictionary containing movement results and messages
    """
    results = []
    
    pathfinding = player.components.get(ComponentType.PATHFINDING)
    if not pathfinding:
        return {"results": results}
    
    if not pathfinding.is_path_active():
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
        # Path blocked before moving, no enemy turn needed
        return {"results": results}
    
    # Check for entities at destination
    blocking_entity = get_blocking_entities_at_location(entities, next_x, next_y)
    if blocking_entity:
        pathfinding.interrupt_movement("Entity blocking path")
        results.append({
            "message": Message(f"Path blocked by {blocking_entity.name}.", (255, 255, 0))
        })
        # Path blocked before moving, no enemy turn needed
        return {"results": results}
    
    # Move player first
    player.move(next_x - player.x, next_y - player.y)
    
    # Request FOV recompute for enemy detection
    results.append({
        "fov_recompute": True
    })
    
    # Check if player stepped on a hazard - interrupt movement if so
    try:
        # hazard_manager is a direct attribute on game_map
        if (hasattr(game_map, 'hazard_manager') and 
            game_map.hazard_manager is not None):
            hazard = game_map.hazard_manager.get_hazard_at(player.x, player.y)
            # hazard_type is a direct attribute on hazard
            if hazard and hasattr(hazard, 'hazard_type'):
                hazard_name = hazard.hazard_type.name.replace('_', ' ').title()
                pathfinding.interrupt_movement(f"Stepped on {hazard_name}")
                results.append({
                    "message": Message(f"Movement stopped - {hazard_name} ahead!", (255, 165, 0))
                })
                # Player moved, so give enemies their turn
                results.append({
                    "enemy_turn": True
                })
                return {"results": results}
    except (AttributeError, TypeError):
        # No valid hazard manager or method, skip hazard check
        pass
    
    # DISABLED: Auto-attack during pathfinding
    # User requirement: "Player should never attack unless actually clicking on a target"
    # The auto-attack feature was causing unwanted attacks during movement
    # 
    # If re-enabling this feature, it should be:
    # 1. Optional (config/setting)
    # 2. Only for ranged weapons
    # 3. Only when explicitly requested by player
    #
    # enemy_in_range = _check_for_enemy_in_weapon_range(player, entities, fov_map)
    # if enemy_in_range:
    #     pathfinding.interrupt_movement("Enemy within weapon reach - attacking!")
    #     attack_results = player.fighter.attack_d20(enemy_in_range)
    #     results.extend(attack_results)
    #     results.append({"enemy_turn": True})
    #     return {"results": results}
    
    # Check for enemies CLOSER than weapon range (threat detection)
    # This allows ranged weapons to keep approaching until in range
    weapon_reach = _get_weapon_reach(player)
    if _check_for_close_enemies(player, entities, fov_map, weapon_reach):
        pathfinding.interrupt_movement("Enemy spotted")
        results.append({
            "message": Message("Movement stopped - enemy spotted!", (255, 255, 0))
        })
        # Player moved, so give enemies their turn
        results.append({
            "enemy_turn": True
        })
        return {"results": results}
    
    # Continue movement if path is still active
    if pathfinding.is_path_active():
        results.append({
            "continue_pathfinding": True
        })
    else:
        # Arrived at destination!
        results.append({
            "message": Message("Arrived at destination.", (0, 255, 0))
        })
        
        # Check if we were pathfinding to pick up an item
        # auto_pickup_target is a direct attribute on pathfinding
        if hasattr(pathfinding, 'auto_pickup_target') and pathfinding.auto_pickup_target:
            target_item = pathfinding.auto_pickup_target
            
            # Check if item is at player's location
            if target_item in entities and target_item.x == player.x and target_item.y == player.y:
                # Pick it up!
                inventory = player.components.get(ComponentType.INVENTORY)
                if inventory:
                    pickup_results = inventory.add_item(target_item)
                    
                    for pickup_result in pickup_results:
                        message = pickup_result.get("message")
                        if message:
                            results.append({"message": message})
                        
                        item_added = pickup_result.get("item_added")
                        item_consumed = pickup_result.get("item_consumed")
                        if item_added or item_consumed:
                            entities.remove(target_item)
                            results.append({
                                "message": Message(f"Auto-picked up {target_item.name}!", (100, 255, 100))
                            })
            
            # Clear the auto-pickup target
            pathfinding.auto_pickup_target = None
    
    return {"results": results}


def _check_for_enemy_in_weapon_range(player: 'Entity', entities: List['Entity'], fov_map) -> Optional['Entity']:
    """Check if any enemy is within weapon reach and visible.
    
    This is used during pathfinding to auto-attack when getting within range.
    
    Args:
        player (Entity): The player entity
        entities (List[Entity]): List of all entities
        fov_map: Field of view map
        
    Returns:
        Entity or None: The closest enemy within weapon range, or None
    """
    from fov_functions import map_is_in_fov
    
    weapon_reach = _get_weapon_reach(player)
    max_attack_distance = weapon_reach * 1.5  # Account for diagonals
    
    enemies_in_range = []
    
    for entity in entities:
        if (entity != player and entity.fighter and 
            map_is_in_fov(fov_map, entity.x, entity.y)):
            distance = player.distance_to(entity)
            if distance <= max_attack_distance:
                enemies_in_range.append((entity, distance))
    
    if enemies_in_range:
        # Return the closest enemy
        enemies_in_range.sort(key=lambda x: x[1])
        return enemies_in_range[0][0]
    
    return None


def _check_for_close_enemies(player: 'Entity', entities: List['Entity'], fov_map, weapon_reach: int) -> bool:
    """Check if any enemies are CLOSER than weapon range (threat detection).
    
    This prevents ranged weapons from continuing to approach when melee enemies
    are dangerously close. For ranged weapons (reach 8-10), only enemies within
    melee range will trigger this. For melee weapons, it works as before.
    
    Args:
        player (Entity): The player entity
        entities (List[Entity]): List of all entities
        fov_map: Field of view map
        weapon_reach (int): The reach of the player's weapon
        
    Returns:
        bool: True if any enemies are closer than weapon reach
    """
    from fov_functions import map_is_in_fov
    
    # For ranged weapons, only stop if enemy gets within melee range (2 tiles)
    # For melee weapons, stop immediately when spotted
    threat_distance = min(weapon_reach, 2) * 1.5  # Account for diagonals
    
    for entity in entities:
        if (entity != player and entity.fighter and 
            map_is_in_fov(fov_map, entity.x, entity.y)):
            distance = player.distance_to(entity)
            if distance <= threat_distance:
                return True
    
    return False


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
