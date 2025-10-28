"""Mouse movement handling for click-to-move functionality.

This module provides functions to handle mouse clicks and convert them
into movement commands for the player pathfinding system.
"""

from typing import Tuple, Optional, List, TYPE_CHECKING
import logging

from message_builder import MessageBuilder as MB
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
    - Click on chest: Open/interact with chest
    - Click on signpost: Read signpost message
    - Click on adjacent enemy: Attack the enemy
    - Click on non-adjacent enemy: Show message (future: pathfind to attack)
    - Click on empty tile: Start pathfinding movement
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
            "message": MB.warning("You cannot move there.")
        })
        return {"results": results}
    
    # Check ALL entities at the clicked location (not just blocking ones)
    # Chests and signposts don't block, so we need to check non-blocking entities too
    entities_at_location = [e for e in entities if e.x == click_x and e.y == click_y]
    
    # Priority 1: Check for interactive map features (chests, signposts, locked doors)
    for entity in entities_at_location:
        if entity.components.has(ComponentType.CHEST):
            # Clicked on a chest - interact with it
            return _handle_chest_click(player, entity, results, entities, game_map)
        elif entity.components.has(ComponentType.SIGNPOST):
            # Clicked on a signpost - read it
            return _handle_signpost_click(player, entity, results)
        elif entity.components.has(ComponentType.LOCKED_DOOR):
            # Clicked on a locked door - try to unlock it
            return _handle_door_click(player, entity, results, entities, game_map)
    
    # Priority 2: Check for blocking entities (enemies)
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
    equipment = entity.get_component_optional(ComponentType.EQUIPMENT)
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
                "message": MB.warning("You cannot attack.")
            })
    else:
        # Too far to attack - pathfind toward the enemy instead
        results.append({
            "message": MB.info(f"Moving toward the {target.name}...")
        })
        # Set pathfinding destination to the enemy's location
        # This will be handled by the movement system
        results.append({
            "pathfind_to_enemy": (target.x, target.y)
        })
    
    return {"results": results}


def _handle_chest_click(player: 'Entity', chest_entity: 'Entity', results: list, 
                       entities: List['Entity'], game_map: 'GameMap') -> dict:
    """Handle clicking on a chest.
    
    Opens the chest if the player is adjacent. If not adjacent, pathfinds to it.
    Drops loot on the ground near the chest for the player to pick up.
    
    Args:
        player (Entity): The player entity
        chest_entity (Entity): The chest entity
        results (list): List to append results to
        entities (List[Entity]): List of all entities
        game_map (GameMap): The game map for loot placement
        
    Returns:
        dict: Dictionary containing action results
    """
    # Calculate distance to chest
    distance = player.distance_to(chest_entity)
    
    if distance <= 1.5:  # Adjacent (including diagonals)
        # Open the chest
        chest = chest_entity.chest
        if chest:
            # Check if chest is locked and requires a key
            has_key = False
            key_consumed = False
            
            if chest.is_locked() and chest.key_id:
                # Check player inventory for matching key
                from components.component_registry import ComponentType
                inventory = player.get_component_optional(ComponentType.INVENTORY)
                
                if inventory:
                    # Look for key in inventory
                    matching_key = None
                    for item in inventory.items:
                        # Check if this is a key item
                        if item.item and hasattr(item, 'name'):
                            # Match key by name (e.g., "bronze_key" chest needs "Bronze Key" item)
                            item_name_normalized = item.name.lower().replace(' ', '_')
                            if item_name_normalized == chest.key_id:
                                matching_key = item
                                break
                    
                    if matching_key:
                        # Player has the key! Remove it from inventory
                        inventory.items.remove(matching_key)
                        has_key = True
                        key_consumed = True
                        
                        # Add message about using the key
                        results.append({
                            "message": MB.info(f"You use the {matching_key.name} to unlock the chest.")
                        })
                    else:
                        # Player doesn't have the key
                        key_name = chest.key_id.replace('_', ' ').title()
                        results.append({
                            "message": MB.warning(f"This chest is locked. You need a {key_name}.")
                        })
                        return {"results": results}
            
            # Open the chest (will handle locked state if has_key is True)
            open_results = chest.open(player, has_key=has_key)
            results.extend(open_results)
            
            # Process results - check for loot, traps, mimics
            for result in open_results:
                if result.get('mimic_revealed'):
                    # TODO: Spawn mimic monster here when mimic system is implemented
                    results.append({
                        "message": MB.warning("This will become a mimic encounter!")
                    })
                elif result.get('trap_triggered'):
                    # Handle trap damage
                    trap_type = result.get('trap_type')
                    if trap_type == 'damage' and player.fighter:
                        damage = 10  # Base trap damage
                        player.fighter.take_damage(damage)
                        results.append({
                            "message": MB.combat(f"The trap deals {damage} damage!")
                        })
                    elif trap_type == 'poison':
                        # TODO: Apply poison status effect
                        results.append({
                            "message": MB.warning("Poison gas erupts from the chest!")
                        })
                    elif trap_type == 'monster_spawn':
                        # TODO: Spawn monster near chest
                        results.append({
                            "message": MB.warning("Monsters burst from the chest!")
                        })
                elif result.get('chest_opened'):
                    # Drop loot on the ground near the chest for player to pick up
                    loot = result.get('loot', [])
                    if loot:
                        # Add items to entities so they appear on the map
                        entities.extend(loot)
                        
                        # Invalidate entity sorting cache when new entities are added
                        from entity_sorting_cache import invalidate_entity_cache
                        invalidate_entity_cache("entity_added_chest_loot")
                        
                        # Create a follow-up message listing what was in the chest
                        # Use display names to respect identification status
                        if len(loot) == 1:
                            display_name = loot[0].name
                            if loot[0].item:
                                display_name = loot[0].item.get_display_name(show_quantity=False)
                            results.append({
                                "message": MB.info(f"The chest contained: {display_name}")
                            })
                        else:
                            display_names = []
                            for item in loot:
                                if item.item:
                                    display_names.append(item.item.get_display_name(show_quantity=False))
                                else:
                                    display_names.append(item.name)
                            item_names = ", ".join(display_names)
                            results.append({
                                "message": MB.info(f"The chest contained: {item_names}")
                            })
            
            # Trigger enemy turn after interaction
            results.append({"enemy_turn": True})
        else:
            results.append({
                "message": MB.warning("This chest cannot be opened.")
            })
    else:
        # Too far - pathfind to the chest
        results.append({
            "message": MB.info(f"Moving toward the {chest_entity.name}...")
        })
        results.append({
            "pathfind_to_target": (chest_entity.x, chest_entity.y)
        })
    
    return {"results": results}


def _handle_signpost_click(player: 'Entity', sign_entity: 'Entity', results: list) -> dict:
    """Handle clicking on a signpost.
    
    Reads the signpost if the player is adjacent. If not adjacent, pathfinds to it.
    
    Args:
        player (Entity): The player entity
        sign_entity (Entity): The signpost entity
        results (list): List to append results to
        
    Returns:
        dict: Dictionary containing action results
    """
    # Calculate distance to signpost
    distance = player.distance_to(sign_entity)
    
    if distance <= 1.5:  # Adjacent (including diagonals)
        # Read the signpost
        signpost = sign_entity.signpost
        if signpost:
            read_results = signpost.read(player)
            results.extend(read_results)
            
            # Reading doesn't consume a turn - it's free information
            # No enemy_turn trigger
        else:
            results.append({
                "message": MB.warning("This sign cannot be read.")
            })
    else:
        # Too far - pathfind to the signpost
        results.append({
            "message": MB.info(f"Moving toward the {sign_entity.name}...")
        })
        results.append({
            "pathfind_to_target": (sign_entity.x, sign_entity.y)
        })
    
    return {"results": results}


def _handle_door_click(player: 'Entity', door_entity: 'Entity', results: list,
                      entities: List['Entity'], game_map: 'GameMap') -> dict:
    """Handle clicking on a locked door.
    
    Attempts to unlock the door if the player is adjacent and has the required key.
    If unlocked, the door transforms to passable floor.
    
    Args:
        player (Entity): The player entity
        door_entity (Entity): The locked door entity
        results (list): List to append results to
        entities (List[Entity]): List of all entities
        game_map (GameMap): The game map
        
    Returns:
        dict: Dictionary containing action results
    """
    # Calculate distance to door
    distance = player.distance_to(door_entity)
    
    if distance <= 1.5:  # Adjacent (including diagonals)
        # Try to unlock the door
        door = door_entity.locked_door
        if door:
            # Check if door is locked and requires a key
            has_key = False
            key_consumed = False
            
            if door.is_locked() and door.required_key:
                # Check player inventory for matching key
                inventory = player.get_component_optional(ComponentType.INVENTORY)
                
                if inventory:
                    # Look for key in inventory
                    matching_key = None
                    for item in inventory.items:
                        # Check if this is a key item
                        if item.item and hasattr(item, 'name'):
                            # Match key by name (e.g., "bronze_key" door needs "Bronze Key" item)
                            item_name_normalized = item.name.lower().replace(' ', '_')
                            if item_name_normalized == door.required_key:
                                matching_key = item
                                break
                    
                    if matching_key:
                        # Player has the key! Remove it from inventory
                        inventory.items.remove(matching_key)
                        has_key = True
                        key_consumed = True
                    else:
                        # Player doesn't have the key
                        key_name = door.required_key.replace('_', ' ').title()
                        results.append({
                            "message": MB.warning(f"This door is locked. You need a {key_name}.")
                        })
                        return {"results": results}
            
            # Unlock the door
            unlock_results = door.unlock(player, has_key=has_key)
            results.extend(unlock_results)
            
            # Process results - check if door was opened
            for result in unlock_results:
                if result.get('door_opened'):
                    # Remove the door entity from the map (it's now passable floor)
                    entities.remove(door_entity)
                    
                    # Update the tile to be passable
                    game_map.tiles[door_entity.x][door_entity.y].blocked = False
                    game_map.tiles[door_entity.x][door_entity.y].block_sight = False
            
            # Trigger enemy turn after interaction
            results.append({"enemy_turn": True})
        else:
            results.append({
                "message": MB.warning("This door cannot be opened.")
            })
    else:
        # Too far - pathfind to the door
        results.append({
            "message": MB.info(f"Moving toward the {door_entity.name}...")
        })
        results.append({
            "pathfind_to_target": (door_entity.x, door_entity.y)
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
    pathfinding = player.get_component_optional(ComponentType.PATHFINDING)
    if not pathfinding:
        results.append({
            "message": MB.failure("Player pathfinding not available.")
        })
        return {"results": results}

    # Attempt to set destination (with FOV awareness)
    if pathfinding.set_destination(click_x, click_y, game_map, entities, fov_map):
        # Successfully set path
        distance = player.distance(click_x, click_y)
        results.append({
            "message": MB.info(f"Moving to ({click_x}, {click_y})...")
        })
        results.append({
            "start_pathfinding": True  # Signal to start pathfinding movement
        })
        logger.debug(f"Started pathfinding to ({click_x}, {click_y}), distance: {distance:.1f}")
    else:
        # Could not find path
        results.append({
            "message": MB.warning("Cannot reach that location.")
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
    
    pathfinding = player.get_component_optional(ComponentType.PATHFINDING)
    if not pathfinding:
        return {"results": results}
    
    if not pathfinding.is_path_active():
        return {"results": results}
    
    # Get next move
    next_pos = pathfinding.get_next_move()
    if next_pos is None:
        # Movement completed
        results.append({
            "message": MB.info("Arrived at destination.")
        })
        return {"results": results}
    
    next_x, next_y = next_pos
    
    # Validate the move is still possible
    if game_map.is_blocked(next_x, next_y):
        pathfinding.interrupt_movement("Path blocked")
        results.append({
            "message": MB.warning("Path blocked - movement stopped.")
        })
        # Path blocked before moving, no enemy turn needed
        return {"results": results}
    
    # Check for entities at destination
    blocking_entity = get_blocking_entities_at_location(entities, next_x, next_y)
    if blocking_entity:
        pathfinding.interrupt_movement("Entity blocking path")
        results.append({
            "message": MB.warning(f"Path blocked by {blocking_entity.name}.")
        })
        # Path blocked before moving, no enemy turn needed
        return {"results": results}
    
    # Move player first
    player.move(next_x - player.x, next_y - player.y)
    
    # Request FOV recompute for enemy detection
    results.append({
        "fov_recompute": True
    })
    
    # Check if player stepped on victory portal (Phase 5)
    # Check if player has Ruby Heart (via victory component)
    from components.component_registry import ComponentType
    victory_comp = player.get_component_optional(ComponentType.VICTORY)
    
    if victory_comp and victory_comp.has_ruby_heart:
        from victory_manager import get_victory_manager
        victory_mgr = get_victory_manager()
        
        # Check if player stepped on portal
        if victory_mgr.check_portal_entry(player, entities):
            from game_messages import MessageLog
            # Get or create message log for portal entry messages
            # (It should already exist in game state, but we need a reference)
            # The calling function will handle the actual message log
            pathfinding.interrupt_movement("Stepped on portal")
            
            # Signal portal entry to game loop (calling function will handle messages and state transition)
            results.append({
                "portal_entry": True
            })
            results.append({
                "enemy_turn": False  # Don't give enemies a turn, go straight to confrontation
            })
            return {"results": results}
    
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
                    "message": MB.warning(f"Movement stopped - {hazard_name} ahead!")
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
            "message": MB.warning("Movement stopped - enemy spotted!")
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
            "message": MB.info("Arrived at destination.")
        })
        
        # Check if we were pathfinding to pick up an item
        # auto_pickup_target is a direct attribute on pathfinding
        if hasattr(pathfinding, 'auto_pickup_target') and pathfinding.auto_pickup_target:
            target_item = pathfinding.auto_pickup_target
            
            # Check if item is at player's location
            if target_item in entities and target_item.x == player.x and target_item.y == player.y:
                # Pick it up!
                print(f">>> PATHFINDING: Picking up item: {target_item.name}")
                print(f">>> Has triggers_victory attr: {hasattr(target_item, 'triggers_victory')}")
                if hasattr(target_item, 'triggers_victory'):
                    print(f">>> triggers_victory value: {target_item.triggers_victory}")
                inventory = player.get_component_optional(ComponentType.INVENTORY)
                if inventory:
                    pickup_results = inventory.add_item(target_item)
                    item_was_added = False
                    
                    for pickup_result in pickup_results:
                        message = pickup_result.get("message")
                        if message:
                            results.append({"message": message})
                        
                        item_added = pickup_result.get("item_added")
                        item_consumed = pickup_result.get("item_consumed")
                        if item_added or item_consumed:
                            entities.remove(target_item)
                            item_was_added = True
                            # Use display name to respect identification status
                            display_name = target_item.name
                            if target_item.item:
                                display_name = target_item.item.get_display_name(show_quantity=False)
                            results.append({
                                "message": MB.item_pickup(f"Auto-picked up {display_name}!")
                            })
                    
                    # Check for victory condition trigger (Ruby Heart)
                    if item_was_added and hasattr(target_item, 'triggers_victory') and target_item.triggers_victory:
                        logger.info("=== PATHFINDING ARRIVAL PICKUP: Victory trigger detected! ===")
                        print(">>> PATHFINDING: Ruby Heart picked up, signaling victory trigger!")
                        # Signal to caller to handle victory sequence
                        results.append({
                            "victory_triggered": True
                        })
            
            # Clear the auto-pickup target
            pathfinding.auto_pickup_target = None
        
        # Check if we were pathfinding to talk to an NPC
        if hasattr(pathfinding, 'auto_talk_target') and pathfinding.auto_talk_target:
            target_npc = pathfinding.auto_talk_target
            
            # Check if NPC is adjacent or at player's location
            # Use Euclidean distance (same as interaction system) to handle diagonals correctly
            distance = player.distance_to(target_npc)
            if target_npc in entities and distance <= 1.5:
                # Talk to them!
                if (hasattr(target_npc, 'is_npc') and target_npc.is_npc and
                    hasattr(target_npc, 'npc_dialogue') and target_npc.npc_dialogue):
                    
                    # Get dungeon level for dialogue
                    from config.game_constants import GAME_CONSTANTS
                    dungeon_level = 1
                    if game_map and hasattr(game_map, 'dungeon_level'):
                        dungeon_level = game_map.dungeon_level
                    
                    if target_npc.npc_dialogue.start_encounter(dungeon_level):
                        results.append({
                            "message": MB.info(f"You approach {target_npc.name}...")
                        })
                        
                        # Need to trigger dialogue state change
                        # This will be handled by the action processor
                        results.append({
                            "npc_dialogue": target_npc
                        })
                    else:
                        results.append({
                            "message": MB.info(f"{target_npc.name} has nothing to say right now.")
                        })
            
            # Clear the auto-talk target
            pathfinding.auto_talk_target = None
    
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
