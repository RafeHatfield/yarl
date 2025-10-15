"""Throwing system - handles thrown items and projectiles.

This module implements the throwing mechanics for the game:
- Calculating projectile paths using Bresenham's line algorithm
- Animating projectiles (arrows, potions, weapons)
- Applying effects based on item type (potions shatter, weapons deal damage)
- Collision detection with walls and entities

Used by game_actions.py when player throws an item (press 't').
"""

from typing import List, Dict, Any, Tuple
import tcod.line
from message_builder import MessageBuilder as MB


def calculate_throw_path(
    start_x: int,
    start_y: int,
    target_x: int,
    target_y: int,
    game_map,
    max_range: int = 10
) -> List[Tuple[int, int]]:
    """Calculate path projectile takes when thrown.
    
    Uses Bresenham line algorithm to trace a straight line from thrower
    to target. Stops at first blocking tile (wall) or max range.
    
    Args:
        start_x, start_y: Thrower's position
        target_x, target_y: Target position
        game_map: Game map for collision detection
        max_range: Maximum throw distance (default: 10)
        
    Returns:
        List of (x, y) tuples representing projectile path
        
    Example:
        >>> path = calculate_throw_path(5, 5, 10, 5, game_map)
        >>> # Returns: [(5,5), (6,5), (7,5), (8,5), (9,5), (10,5)]
    """
    # Get line from start to target using Bresenham's algorithm
    line = list(tcod.line.bresenham(start_x, start_y, target_x, target_y))
    
    # Limit to max range
    if len(line) > max_range:
        line = line[:max_range]
    
    # Stop at first blocking tile (wall)
    path = []
    for x, y in line:
        path.append((x, y))
        
        # Check if this tile blocks projectiles
        if game_map.tiles[x][y].blocked:
            break  # Hit a wall, stop here
    
    return path


def throw_item(
    thrower,
    item,
    target_x: int,
    target_y: int,
    entities: List,
    game_map,
    fov_map
) -> List[Dict[str, Any]]:
    """Execute a throw action - calculates path, animates projectile, applies effects.
    
    This is the main entry point for throwing. It:
    1. Calculates the projectile path
    2. Queues the projectile animation
    3. Determines what was hit (entity or ground)
    4. Applies appropriate effects based on item type
    
    Args:
        thrower: Entity throwing the item
        item: Item entity being thrown
        target_x, target_y: Target coordinates
        entities: All entities in game
        game_map: Game map
        fov_map: Field of view map
        
    Returns:
        List of result dictionaries with messages and effects
        
    Example:
        >>> results = throw_item(player, potion, 10, 5, entities, map, fov)
        >>> # Returns: [{"message": "Potion shatters!", "consumed": True}]
    """
    results = []
    
    # Calculate throw path
    path = calculate_throw_path(
        thrower.x, thrower.y,
        target_x, target_y,
        game_map,
        max_range=10  # Base throw range (could be modified by STR in future)
    )
    
    if not path:
        return [{
            "consumed": False,
            "message": MB.warning("Invalid throw target!")
        }]
    
    # Get final landing position (last tile in path)
    final_x, final_y = path[-1]
    
    # Queue projectile animation
    from visual_effect_queue import get_effect_queue
    effect_queue = get_effect_queue()
    
    # Determine projectile appearance
    item_char = ord(item.char) if hasattr(item, 'char') else ord('*')
    item_color = item.color if hasattr(item, 'color') else (255, 255, 255)
    
    effect_queue.queue_projectile(
        path=path,
        char=item_char,
        color=item_color,
        frame_duration=0.05  # 50ms per tile - visible but not too slow
    )
    
    # Check what we hit at final position
    target_entity = None
    for entity in entities:
        if entity.x == final_x and entity.y == final_y and entity != thrower:
            # Check if entity is a valid target (has fighter component = can be hit)
            if hasattr(entity, 'fighter') and entity.fighter:
                target_entity = entity
                break
    
    # Apply effects based on item type
    if item.item and item.item.use_function:
        # It's a potion/consumable - apply effect at target location
        results.extend(_throw_potion(
            item, thrower, target_entity, final_x, final_y, 
            entities, game_map, fov_map
        ))
    elif hasattr(item, 'item') and hasattr(item.item, 'equipment'):
        # It's a weapon - deal damage and drop at final position
        weapon_results = _throw_weapon(item, thrower, target_entity, final_x, final_y)
        results.extend(weapon_results)
        
        # Add weapon back to entities list so it can be picked up
        item.x = final_x
        item.y = final_y
        entities.append(item)
    else:
        # Generic throwable (e.g., wand, ring, misc item)
        item.x = final_x
        item.y = final_y
        entities.append(item)  # Drop item at final position
        
        results.append({
            "message": MB.info(f"You throw the {item.name}. It lands at ({final_x}, {final_y}).")
        })
    
    results.append({"consumed": True})  # Item is thrown (removed from inventory)
    return results


def _throw_potion(
    potion,
    thrower,
    target,
    final_x: int,
    final_y: int,
    entities: List,
    game_map,
    fov_map
) -> List[Dict[str, Any]]:
    """Handle throwing a potion - it shatters on impact and applies effects.
    
    Potions shatter when thrown and apply their effects:
    - If they hit an entity directly, full effect on that entity
    - If they miss, potion breaks on ground (currently wasted - could add splash)
    
    Args:
        potion: Potion item entity
        thrower: Entity that threw the potion
        target: Entity hit by potion (or None if missed)
        final_x, final_y: Final position where potion landed
        entities: All entities
        game_map: Game map
        fov_map: Field of view map
        
    Returns:
        List of result dictionaries
    """
    results = []
    
    if target:
        # Hit an entity directly - apply full effect
        results.append({
            "message": MB.spell_effect(
                f"The {potion.name} shatters on {target.name}!"
            )
        })
        
        # Apply potion effect to target
        # Call the potion's use_function with target as the entity
        use_results = potion.item.use_function(
            target,
            entities=entities,
            game_map=game_map,
            fov_map=fov_map
        )
        results.extend(use_results)
        
    else:
        # Missed - potion breaks on ground
        results.append({
            "message": MB.info(
                f"The {potion.name} shatters on the ground!"
            )
        })
        
        # TODO: Could add splash damage to adjacent tiles here for AOE potions
        # For now, just wasted
    
    return results


def _throw_weapon(
    weapon,
    thrower,
    target,
    final_x: int,
    final_y: int
) -> List[Dict[str, Any]]:
    """Handle throwing a weapon - deals damage based on weapon type.
    
    Thrown weapons:
    - Deal damage based on their damage dice (with -2 penalty for throwing)
    - Land on the ground at final position (whether hit or miss)
    - Can be picked up again
    
    Args:
        weapon: Weapon item entity
        thrower: Entity that threw the weapon
        target: Entity hit by weapon (or None if missed)
        final_x, final_y: Final position where weapon landed
        
    Returns:
        List of result dictionaries
    """
    results = []
    
    if target:
        # Hit! Roll damage
        from components.fighter import roll_dice
        
        # Get weapon damage (reduced for throwing vs melee)
        equipment = weapon.item.equipment
        damage_dice = equipment.damage_dice if equipment else "1d4"
        
        # Throwing penalty: -2 to damage (min 1)
        base_damage = roll_dice(damage_dice)
        throw_damage = max(1, base_damage - 2)
        
        # Apply damage to target
        if target.fighter:
            target.fighter.take_damage(throw_damage)
            
            results.append({
                "message": MB.damage(
                    f"The {weapon.name} hits {target.name} for {throw_damage} damage!"
                )
            })
            
            # Check if target died
            if target.fighter.hp <= 0:
                results.append({
                    "dead": target,
                    "message": MB.kill(f"{target.name} is killed by the thrown {weapon.name}!")
                })
    else:
        # Missed - weapon lands on ground
        results.append({
            "message": MB.info(f"The {weapon.name} clatters to the ground.")
        })
    
    # Drop weapon at final position (whether hit or miss)
    # It can be picked up again
    weapon.x = final_x
    weapon.y = final_y
    
    # Note: Weapon will be added back to entities list by throw_item() caller
    # (game_actions.py already has access to entities list)
    
    return results

