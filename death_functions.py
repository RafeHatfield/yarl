"""Functions for handling entity death and cleanup.

This module contains functions that are called when entities die,
handling the visual and mechanical changes that occur.

═══════════════════════════════════════════════════════════════════════════════
MODULE CONTRACT: Death & Combat System
───────────────────────────────────────────────────────────────────────────────

OWNERSHIP:
  - Entity death handling (player and monsters)
  - Death message generation
  - Special death behaviors (boss drops, etc.)
  - Game state transitions on death
  - Phase 10: Plague reanimation (revenant zombie creation)
  - Phase 19: Slime splitting moved to Split Under Pressure (see slime_split_service.py)

KEY CONTRACTS:
  - Use kill_monster() for monster death (not duplicated elsewhere)
  - Use kill_player() for player death
  - Loot generation is separate; see components/loot.py
  - Death messages use MessageBuilder
  - Special behaviors via monster components (boss), not new functions

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
from typing import List, Optional, Dict, Any

from game_messages import Message
from message_builder import MessageBuilder as MB
from game_states import GameStates
from render_functions import RenderOrder
from components.component_registry import ComponentType
from config.factories import get_entity_factory
from components.corpse import CorpseComponent


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


# Phase 19: Slime split-on-death removed in favor of "Split Under Pressure"
# Old split-on-death functions removed - splitting now happens at low HP threshold
# See services/slime_split_service.py for new implementation


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 10: PLAGUE OF RESTLESS DEATH - REANIMATION SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════


def _spawn_death_feature(monster, game_map, entities) -> None:
    """Spawn a feature/item on monster death if configured.
    
    Phase 19: Skeletons spawn bone piles on death (future necromancer hook).
    
    Args:
        monster: The monster that just died
        game_map: Game map for position validation
        entities: List of all entities
    """
    if not hasattr(monster, 'death_spawns'):
        return
    
    death_spawn_type = monster.death_spawns
    if not death_spawn_type:
        return
    
    # Create the death feature at monster's position
    try:
        factory = get_entity_factory()
        feature = factory.create_map_feature(death_spawn_type, monster.x, monster.y)
        
        if feature and entities is not None:
            # Add to entities list (caller will handle this)
            # Store on monster so caller can add it
            if not hasattr(monster, '_death_spawned_features'):
                monster._death_spawned_features = []
            monster._death_spawned_features.append(feature)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Failed to spawn death feature {death_spawn_type} for {monster.name}: {e}")


def _trigger_death_siphon(monster, entities) -> None:
    """Phase 19: Trigger Death Siphon for nearby allied liches.
    
    Death Siphon: When an allied undead dies within radius 6 of a lich,
    the lich heals 2 HP (capped at missing HP).
    
    Args:
        monster: The monster that just died
        entities: List of all entities
    """
    # Only trigger for undead faction deaths
    monster_faction = getattr(monster, 'faction', None)
    if monster_faction != 'undead':
        return
    
    if not entities:
        return
    
    # Find living liches within radius 6
    siphon_radius = 6
    siphon_heal_amount = 2
    
    for entity in entities:
        # Check if entity is a lich
        ai = entity.get_component_optional(ComponentType.AI)
        if not ai:
            continue
        
        from components.ai.lich_ai import LichAI
        if not isinstance(ai, LichAI):
            continue
        
        # Check if lich is alive
        fighter = entity.get_component_optional(ComponentType.FIGHTER)
        if not fighter or fighter.hp <= 0:
            continue
        
        # Check faction match
        lich_faction = getattr(entity, 'faction', None)
        if lich_faction != monster_faction:
            continue
        
        # Check distance
        import math
        distance = math.sqrt((entity.x - monster.x)**2 + (entity.y - monster.y)**2)
        if distance <= siphon_radius:
            # Lich is within siphon range!
            missing_hp = fighter.max_hp - fighter.hp
            if missing_hp > 0:
                heal_amount = min(siphon_heal_amount, missing_hp)
                fighter.heal(heal_amount)
                
                # Add message to log
                from state_management.state_manager import get_state_manager
                state_manager = get_state_manager()
                if state_manager and state_manager.state and state_manager.state.message_log:
                    from message_builder import MessageBuilder as MB
                    state_manager.state.message_log.add_message(
                        MB.combat(f"💀 The {entity.name} siphons {heal_amount} HP from {monster.name}'s death!")
                    )
                
                # Record metric
                try:
                    from services.scenario_metrics import get_active_metrics_collector
                    metrics = get_active_metrics_collector()
                    if metrics:
                        metrics.increment('lich_death_siphon_heals')
                except Exception:
                    pass  # Metrics are optional
                
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"[DEATH SIPHON] {entity.name} healed {heal_amount} HP from {monster.name}'s death")


def _check_plague_reanimation(monster, game_map, entities) -> Optional[Dict[str, Any]]:
    """Check if a monster should reanimate as a revenant zombie.
    
    Phase 10: If the monster died while infected with Plague of Restless Death,
    schedule reanimation after 1-3 turns.
    
    Args:
        monster: The monster that just died
        game_map: Game map for position validation
        entities: List of all entities
        
    Returns:
        Dict with reanimation data if applicable, None otherwise
    """
    # Check if monster had plague effect
    status_effects = monster.get_component_optional(ComponentType.STATUS_EFFECTS)
    if not status_effects:
        return None
    
    plague_effect = status_effects.get_effect("plague_of_restless_death")
    if not plague_effect:
        return None
    
    # Get revenant stats from the plague effect
    revenant_stats = plague_effect.get_revenant_stats()
    if not revenant_stats:
        return None
    
    # Schedule reanimation in 1-3 turns
    reanimate_delay = random.randint(1, 3)
    
    return {
        'corpse_x': monster.x,
        'corpse_y': monster.y,
        'revenant_stats': revenant_stats,
        'reanimate_in_turns': reanimate_delay,
        'original_monster': monster,
    }


def create_revenant_zombie(
    x: int, 
    y: int, 
    revenant_stats: Dict[str, Any],
    game_map=None,
    entities=None
) -> Optional['Entity']:
    """Create a Revenant Zombie from plague reanimation.
    
    Phase 10: Creates a zombie with transformed stats from the original creature.
    
    Stats transformation (already calculated in revenant_stats):
    - new_max_hp = original_max_hp * 2
    - new_damage = floor(original_damage * 0.75)
    - new_accuracy = floor(original_accuracy * 0.75)
    - new_evasion = floor(original_evasion * 0.5)
    
    The revenant:
    - Drops all wielded weapons (uses unarmed/claw damage)
    - Keeps worn armor (chest, helmet, gloves, boots)
    - Removes shields/held gear
    - Faction set to UNDEAD
    - Uses zombie AI with swarm behavior
    
    Args:
        x: X coordinate for spawn
        y: Y coordinate for spawn
        revenant_stats: Dict with transformed stats
        game_map: Game map for position validation
        entities: List of all entities to check for occupied tiles
        
    Returns:
        Entity: The new revenant zombie, or None on failure
    """
    from entity import Entity
    from components.fighter import Fighter
    from components.ai import BasicMonster
    from components.equipment import Equipment
    from components.faction import Faction
    from components.status_effects import StatusEffectManager
    
    # Find valid spawn position (original or nearest free tile)
    spawn_x, spawn_y = x, y
    if entities and game_map:
        # Check if original position is blocked
        blocked = False
        for entity in entities:
            if entity.x == x and entity.y == y and entity.blocks:
                blocked = True
                break
        
        if blocked:
            # Find nearest free tile
            positions = _get_valid_spawn_positions(x, y, game_map, 1, entities)
            if positions:
                spawn_x, spawn_y = positions[0]
    
    # Create fighter component with transformed stats
    fighter = Fighter(
        hp=revenant_stats['max_hp'],
        defense=revenant_stats['defense'],
        power=revenant_stats['power'],
        xp=50,  # Fixed XP for revenants
        damage_min=revenant_stats['damage_min'],
        damage_max=revenant_stats['damage_max'],
        strength=12,  # Standard zombie strength
        dexterity=6,  # Slow
        constitution=14,  # Undead resilience
        accuracy=revenant_stats['accuracy'],
        evasion=revenant_stats['evasion']
    )
    
    # Create AI with swarm behavior (zombie-specific)
    ai = BasicMonster()
    ai.is_zombie = True  # Flag for swarm behavior
    ai.aware_of_player = True  # Revenants are immediately aware
    
    # Create equipment component (for keeping armor)
    equipment = Equipment()
    
    # Generate name
    original_name = revenant_stats.get('original_name', 'creature')
    revenant_name = f"Revenant {original_name}"
    
    # Create the revenant entity
    revenant = Entity(
        x=spawn_x,
        y=spawn_y,
        char='Z',  # Capital Z for revenant zombie
        color=(100, 150, 100),  # Sickly gray-green
        name=revenant_name,
        blocks=True,
        render_order=RenderOrder.ACTOR,
        faction=Faction.UNDEAD,
        fighter=fighter,
        ai=ai,
        equipment=equipment
    )
    
    # Add status effects manager
    revenant.status_effects = StatusEffectManager(revenant)
    revenant.components.add(ComponentType.STATUS_EFFECTS, revenant.status_effects)
    
    # Mark as revenant for identification
    revenant.is_revenant = True
    revenant.special_abilities = ['swarm']  # Enable swarm targeting
    
    # Queue VFX
    try:
        from visual_effects import show_reanimate_effect
        show_reanimate_effect(spawn_x, spawn_y, revenant)
    except ImportError:
        pass  # VFX optional
    
    return revenant


def process_pending_reanimations(entities, game_map, turn_number: int = 0) -> List[Dict[str, Any]]:
    """Process all pending plague reanimations.
    
    Phase 10: Called each turn to check for corpses that should reanimate.
    
    This function should be called from the game loop to handle deferred
    reanimation of plague-infected corpses.
    
    Args:
        entities: List of all entities (including corpses)
        game_map: Game map for position validation
        turn_number: Current turn number (for timing)
        
    Returns:
        List of result dicts with new revenant zombies and messages
    """
    results = []
    new_revenants = []
    
    for entity in list(entities):  # Copy list since we may modify
        # Check for pending reanimation
        if not hasattr(entity, '_pending_reanimation'):
            continue
        
        reanimation_data = entity._pending_reanimation
        
        # Decrement turns until reanimation
        reanimation_data['reanimate_in_turns'] -= 1
        
        if reanimation_data['reanimate_in_turns'] <= 0:
            # Time to reanimate!
            revenant = create_revenant_zombie(
                reanimation_data['corpse_x'],
                reanimation_data['corpse_y'],
                reanimation_data['revenant_stats'],
                game_map,
                entities
            )
            
            if revenant:
                new_revenants.append(revenant)
                
                results.append({
                    'message': MB.custom(
                        f"☠️ The plague takes hold! {entity.name} rises as {revenant.name}!",
                        (150, 200, 50)  # Sickly green
                    ),
                    'new_entity': revenant
                })
            
            # Clear reanimation data
            del entity._pending_reanimation
    
    return results


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
    
    # Phase 19: Log lich deaths for debugging (can be disabled in production)
    import logging
    logger = logging.getLogger(__name__)
    if 'lich' in monster.name.lower():
        has_fighter = hasattr(monster, 'fighter') and monster.fighter is not None
        hp_info = f"HP: {monster.fighter.hp}/{monster.fighter.max_hp}" if has_fighter and monster.fighter else "NO FIGHTER"
        logger.debug(f"[LICH DEATH] {monster.name} at ({monster.x}, {monster.y}), {hp_info}")
    
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
    
    # Phase 19: Check for death spawns (e.g., bone pile from skeleton)
    _spawn_death_feature(monster, game_map, entities)
    
    # Phase 19: Death Siphon - Lich heals when allied undead dies nearby
    _trigger_death_siphon(monster, entities)
    
    # Phase 10: Check for Plague of Restless Death - schedule reanimation
    pending_reanimation = _check_plague_reanimation(monster, game_map, entities)
    
    if pending_reanimation:
        # Plague reanimation pending - special death message
        death_message = MB.custom(
            "{0} falls... but the plague stirs within the corpse!".format(
                monster.name.capitalize()
            ), (150, 200, 50)  # Sickly green for plague
        )
        # Store reanimation data for caller to handle
        monster._pending_reanimation = pending_reanimation
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
    
    # Phase 19: Report lich diagnostics before removing AI component
    if hasattr(monster, 'ai') and monster.ai:
        from components.ai.lich_ai import LichAI
        if isinstance(monster.ai, LichAI):
            monster.ai.report_diagnostics()
    
    # Remove combat components from the registry (not just set to None)
    # This ensures get_all_entities_at_position() correctly identifies corpses
    # vs living monsters (checks components.has(ComponentType.FIGHTER/AI))
    if hasattr(monster, 'components'):
        monster.components.remove(ComponentType.FIGHTER)
        monster.components.remove(ComponentType.AI)
    monster.fighter = None
    monster.ai = None
    
    # Phase 19: Attach CorpseComponent for safe resurrection tracking
    # Extract original monster ID from entity (use monster_id if available, else derive from name)
    original_monster_id = getattr(monster, 'monster_id', monster.name.lower())
    
    # Get current turn number for death tracking (if available)
    death_turn = 0
    try:
        from engine.turn_manager import TurnManager
        turn_mgr = TurnManager.get_instance()
        if turn_mgr:
            death_turn = turn_mgr.turn_number
    except:
        pass  # Turn tracking optional
    
    # Create and attach corpse component
    corpse_component = CorpseComponent(
        original_monster_id=original_monster_id,
        death_turn=death_turn,
        raise_count=0,
        max_raises=1,
        consumed=False
    )
    corpse_component.owner = monster
    monster.components.add(ComponentType.CORPSE, corpse_component)
    
    monster.name = "remains of " + monster.name
    monster.render_order = RenderOrder.CORPSE

    return death_message
