"""Functions for handling entity death and cleanup.

This module contains functions that are called when entities die,
handling the visual and mechanical changes that occur.

═══════════════════════════════════════════════════════════════════════════════
MODULE CONTRACT: Death & Combat System
───────────────────────────────────────────────────────────────────────────────

OWNERSHIP:
  - Entity death handling (player and monsters)
  - Death message generation
  - Special death behaviors (slime splitting, boss drops, etc.)
  - Game state transitions on death

KEY CONTRACTS:
  - Use kill_monster() for monster death (not duplicated elsewhere)
  - Use kill_player() for player death
  - Loot generation is separate; see components/loot.py
  - Death messages use MessageBuilder
  - Special behaviors via monster components (boss, slime), not new functions

WHEN CHANGING BEHAVIOR:
  - Update tests/test_golden_path_floor1.py::test_kill_basic_monster_and_loot
  - Update tests/test_death_nonboss.py
  - Update tests/integration/combat/ as needed
  - Verify entity list consistency after death
  - Check that loot appears or messages generated

SEE ALSO:
  - game_messages.py - Message creation
  - components/fighter.py - Combat stats
  - components/loot.py - Loot generation
  - death_screen.py - Death screen rendering
═══════════════════════════════════════════════════════════════════════════════
"""

import random
from typing import List, Optional

from game_messages import Message
from message_builder import MessageBuilder as MB
from game_states import GameStates
from render_functions import RenderOrder
from components.component_registry import ComponentType
from config.factories import get_entity_factory


def kill_player(player):
    """Handle player death.

    Changes the player's appearance to a corpse and returns
    the death message and new game state.

    Args:
        player (Entity): The player entity that died

    Returns:
        tuple: (death_message, new_game_state) for game over handling
    """
    player.char = "%"
    player.color = (127, 0, 0)

    # return 'You died!', GameStates.PLAYER_DEAD
    return MB.death("You died!"), GameStates.PLAYER_DEAD


def _handle_slime_splitting(monster, game_map, entities=None) -> List:
    """Handle Large Slime splitting when it dies.
    
    Args:
        monster: The Large Slime that died
        game_map: Game map for spawning new slimes
        entities: List of all entities (to avoid spawning on occupied tiles)
        
    Returns:
        List of newly spawned slime entities, or empty list if no splitting
    """
    # Check if this monster can split
    if not _can_monster_split(monster):
        return []
    
    # 60% chance to split
    if random.random() > 0.6:
        return []
    
    # Spawn 2-3 regular slimes
    num_slimes = random.randint(2, 3)
    spawned_slimes = []
    
    # Get valid spawn positions around the dead slime
    spawn_positions = _get_valid_spawn_positions(monster.x, monster.y, game_map, num_slimes, entities)
    
    # Create new slimes
    entity_factory = get_entity_factory()
    
    for i, (x, y) in enumerate(spawn_positions):
        if i >= num_slimes:
            break
            
        # Create a fresh regular slime (not inheriting from large slime)
        new_slime = entity_factory.create_monster("slime", x, y)
        if new_slime:
            spawned_slimes.append(new_slime)
    
    return spawned_slimes


def _can_monster_split(monster) -> bool:
    """Check if a monster has splitting ability.
    
    Args:
        monster: Entity to check
        
    Returns:
        True if monster can split
    """
    return (hasattr(monster, 'special_abilities') and 
            monster.special_abilities and 
            'splitting' in monster.special_abilities)


def _get_valid_spawn_positions(center_x: int, center_y: int, game_map, max_positions: int, entities=None) -> List[tuple]:
    """Get valid positions around a center point for spawning entities.
    
    Args:
        center_x: X coordinate of center position
        center_y: Y coordinate of center position  
        game_map: Game map to check for valid tiles
        max_positions: Maximum number of positions to return
        entities: List of all entities to check for occupied tiles
        
    Returns:
        List of (x, y) tuples for valid spawn positions
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


def kill_monster(monster, game_map=None, entities=None):
    """Handle monster death.

    Transforms a monster into a non-blocking corpse, removes its
    combat and AI components, drops any equipped items, and returns a death message.
    
    For bosses, also triggers death dialogue and marks boss as defeated.
    
    This function is idempotent - calling it multiple times on the same monster
    will only process the death once.

    Args:
        monster (Entity): The monster entity that died
        game_map (GameMap, optional): Game map for proper item placement
        entities (list, optional): List of all entities to avoid spawning on occupied tiles

    Returns:
        Message: Death message to display to the player
    """
    # Import MessageBuilder at the top so it's available throughout the function
    
    # GUARD: Check if this monster has already been processed
    # This prevents duplicate loot drops if kill_monster is called multiple times
    if hasattr(monster, '_death_processed') and monster._death_processed:
        # Already processed - return a simple message and do nothing else
        return MB.combat(f"{monster.name} is already dead.")
    
    # Mark this monster as death-processed to prevent duplicate processing
    monster._death_processed = True
    
    # Check if this is a boss death (before components are removed)
    boss = monster.get_component_optional(ComponentType.BOSS) if monster else None
    death_dialogue = None
    
    if boss:
        # Get boss death dialogue
        death_dialogue = boss.get_dialogue("death")
        boss.mark_defeated()
    
    # Drop loot from monster's equipment and inventory
    try:
        from components.monster_equipment import MonsterLootDropper
        dropped_items = MonsterLootDropper.drop_monster_loot(monster, monster.x, monster.y, game_map)
        if dropped_items:
            # Store dropped items on the monster so callers (game_actions.py or ai_system.py) can add them to entities
            monster._dropped_loot = dropped_items
    except Exception as e:
        # Loot dropping can fail if game_map is not fully initialized or in test environments
        # Log the error but don't crash - the game can continue
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Loot dropping failed for {monster.name}: {e}")
    
    # Handle slime splitting before transforming to corpse
    spawned_slimes = _handle_slime_splitting(monster, game_map, entities)
    if spawned_slimes:
        # Store spawned slimes on the monster for the caller to handle
        monster._spawned_entities = spawned_slimes
        
        # Create special death message for splitting
        death_message = MB.custom(
            "{0} dies and splits into {1} smaller slimes!".format(
                monster.name.capitalize(), len(spawned_slimes)
            ), (0, 255, 0)  # Green for special event
        )
    elif death_dialogue:
        # Boss death with dialogue
        death_message = MB.custom(
            "{0} falls! \"{1}\"".format(monster.name.capitalize(), death_dialogue),
            MB.RED  # Epic red for boss death
        )
    else:
        # Normal death message
        death_message = MB.custom(
            "{0} is dead!".format(monster.name.capitalize()), MB.ORANGE
        )

    monster.char = "%"
    monster.color = (127, 0, 0)
    monster.blocks = False
    
    # Remove combat components from the registry (not just set to None)
    # This ensures get_all_entities_at_position() correctly identifies corpses
    # vs living monsters (checks components.has(ComponentType.FIGHTER/AI))
    if hasattr(monster, 'components'):
        monster.components.remove(ComponentType.FIGHTER)
        monster.components.remove(ComponentType.AI)
    monster.fighter = None
    monster.ai = None
    
    monster.name = "remains of " + monster.name
    monster.render_order = RenderOrder.CORPSE

    return death_message
