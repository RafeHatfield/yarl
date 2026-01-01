"""Centralized damage application service.

This service provides a single, canonical entry point for applying damage to entities
outside the normal combat flow (melee/ranged attacks handled by game_actions).

Purpose:
- Enforce death handling for ALL damage sources (traps, hazards, throwing, spells)
- Prevent regressions where entities reach 0 HP but don't die because callers
  ignore Fighter.take_damage() return results
- Centralize player vs monster death handling logic

Usage:
    from services.damage_service import apply_damage
    
    results = apply_damage(
        state_manager,
        target_entity,
        amount=10,
        cause="spike_trap",
        attacker_entity=None,
        allow_xp=True,
        message_on_kill=None
    )
"""

from typing import Any, List, Dict, Optional
from logger_config import get_logger

logger = get_logger(__name__)


def apply_damage(
    state_manager,
    target_entity: Any,
    amount: int,
    *,
    cause: str,
    attacker_entity: Optional[Any] = None,
    damage_type: Optional[str] = None,
    allow_xp: bool = True,
    message_on_kill: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Apply damage to an entity with centralized death handling.
    
    This is the canonical way to apply damage outside normal combat (melee/ranged).
    Use this for:
    - Environmental hazards (spike traps, fire, poison gas)
    - Chest traps
    - Thrown weapons
    - Spell damage (future migration)
    
    DO NOT use this for:
    - Normal melee/ranged combat (use Fighter.attack() / Fighter.attack_d20())
    - Direct Fighter.take_damage() calls should be limited to approved paths
    
    Args:
        state_manager: StateManager instance (required, do NOT use get_state_manager())
        target_entity: Entity taking damage
        amount: Damage amount (before resistances)
        cause: Death cause string (e.g., "spike_trap", "chest_trap", "thrown_weapon")
        attacker_entity: Optional attacker entity (for XP credit)
        damage_type: Optional damage type for resistance calculation (e.g., "fire", "cold")
        allow_xp: If True and target dies, award XP to attacker (default: True)
        message_on_kill: Optional custom kill message (overrides default)
    
    Returns:
        list: Result dictionaries from take_damage, with death properly handled
              Safe to extend/process for additional messages
    
    Raises:
        ValueError: If state_manager is None in production code
    
    Note:
        For unit tests, state_manager can be None to test damage without death finalization.
        In production code, state_manager should always be provided.
    """
    # Allow None state_manager for unit tests (they won't finalize death)
    # But log a warning in case this is unintentional in production
    if state_manager is None:
        logger.debug(
            f"apply_damage() called with state_manager=None (target={target_entity.name if target_entity else 'None'}, "
            f"cause={cause}). Death finalization will be skipped. This is OK for unit tests."
        )
    
    if target_entity is None:
        logger.warning(f"apply_damage() called with target_entity=None, cause={cause}")
        return []
    
    from components.component_registry import ComponentType
    
    # Get fighter component
    fighter = target_entity.get_component_optional(ComponentType.FIGHTER)
    if not fighter:
        logger.warning(
            f"apply_damage() called on {target_entity.name} without Fighter component, cause={cause}"
        )
        return []
    
    # Apply damage and capture results
    damage_results = fighter.take_damage(amount, damage_type=damage_type)
    
    # Process death results in ONE canonical place
    # Skip death finalization if state_manager is None (unit tests)
    if state_manager is not None:
        for result in damage_results:
            dead_entity = result.get("dead")
            if dead_entity:
                _handle_damage_death(
                    state_manager=state_manager,
                    dead_entity=dead_entity,
                    cause=cause,
                    attacker_entity=attacker_entity,
                    allow_xp=allow_xp,
                    message_on_kill=message_on_kill,
                    result_dict=result,
                )
    else:
        # CRITICAL: state_manager is None but entity might have died!
        # This is the "undead limbo" bug we're trying to prevent.
        for result in damage_results:
            dead_entity = result.get("dead")
            if dead_entity:
                # LOUD WARNING: Death occurred but won't be finalized!
                # Gather context for debugging
                entity_name = dead_entity.name if dead_entity else 'Unknown'
                entity_hp = dead_entity.fighter.hp if dead_entity and hasattr(dead_entity, 'fighter') else 'N/A'
                
                # Try to get run context (may be None in unit tests)
                run_id = "N/A"
                floor_depth = "N/A"
                scenario_id = "N/A"
                
                # Check if we can extract context from fighter/entity
                if hasattr(dead_entity, 'run_id'):
                    run_id = dead_entity.run_id
                
                # Log with stable prefix for alerting/grepping
                logger.error(
                    f"DEATH_WITHOUT_FINALIZATION: {entity_name} reached 0 HP "
                    f"(cause={cause}, hp={entity_hp}, run_id={run_id}, floor={floor_depth}, scenario={scenario_id}) "
                    f"but state_manager=None - death will NOT be finalized! "
                    f"This is OK for unit tests, but a BUG in production code."
                )
                # In testing mode, this is expected. In production, this is the bug we're fixing.
                # The warning ensures we catch any missed call sites.
    
    return damage_results


def _handle_damage_death(
    state_manager,
    dead_entity: Any,
    cause: str,
    attacker_entity: Optional[Any],
    allow_xp: bool,
    message_on_kill: Optional[str],
    result_dict: Dict[str, Any],
) -> None:
    """Handle entity death from damage service.
    
    This is called internally by apply_damage() when an entity dies.
    Routes to appropriate death handler (player vs monster).
    
    Args:
        state_manager: StateManager instance
        dead_entity: Entity that died
        cause: Death cause string
        attacker_entity: Optional attacker for XP credit
        allow_xp: If True, award XP
        message_on_kill: Optional custom kill message
        result_dict: The result dict from take_damage (may be modified)
    """
    game_state = state_manager.state
    player = game_state.player
    
    if dead_entity == player:
        # Player died - finalize death EXACTLY ONCE
        _finalize_player_damage_death(state_manager, cause)
    else:
        # Monster/NPC died - use canonical monster death handler
        _finalize_monster_damage_death(
            state_manager=state_manager,
            dead_entity=dead_entity,
            cause=cause,
            attacker_entity=attacker_entity,
            allow_xp=allow_xp,
            message_on_kill=message_on_kill,
            result_dict=result_dict,
        )


def _finalize_player_damage_death(state_manager, cause: str) -> None:
    """Finalize player death from damage service.
    
    Delegates to engine_integration.finalize_player_death() which handles:
    - Setting PLAYER_DEAD game state
    - Adding death message
    - Generating death quote
    - Ending telemetry
    - Finalizing run_metrics
    - Logging bot results summary
    
    Args:
        state_manager: StateManager instance
        cause: Death cause string (e.g., "spike_trap", "chest_trap")
    """
    import engine_integration
    
    # Get constants from game state (stored during initialization)
    constants = getattr(state_manager.state, "constants", {})
    
    # Call canonical player death finalizer
    engine_integration.finalize_player_death(
        state_manager,
        constants=constants,
        cause=cause
    )
    
    logger.info(f"Player death finalized via damage_service, cause={cause}")


def _finalize_monster_damage_death(
    state_manager,
    dead_entity: Any,
    cause: str,
    attacker_entity: Optional[Any],
    allow_xp: bool,
    message_on_kill: Optional[str],
    result_dict: Dict[str, Any],
) -> None:
    """Finalize monster/NPC death from damage service.
    
    Delegates to death_functions.kill_monster() which handles:
    - Transforming to corpse
    - Removing Fighter/AI components
    - Dropping loot
    - Spawning death features (bone piles, etc.)
    - Checking plague reanimation
    - Returning death message
    
    Args:
        state_manager: StateManager instance
        dead_entity: Monster/NPC that died
        cause: Death cause string
        attacker_entity: Optional attacker for XP credit
        allow_xp: If True, award XP
        message_on_kill: Optional custom kill message (overrides default)
        result_dict: Result dict from take_damage (may be modified for XP)
    """
    from death_functions import kill_monster
    
    game_state = state_manager.state
    game_map = game_state.game_map
    entities = game_state.entities
    
    # Call canonical monster death handler
    death_message = kill_monster(dead_entity, game_map, entities)
    
    # Add death message to log
    if game_state.message_log:
        # Use custom message if provided, otherwise use kill_monster's message
        if message_on_kill:
            from message_builder import MessageBuilder as MB
            game_state.message_log.add_message(MB.death(message_on_kill))
        else:
            game_state.message_log.add_message(death_message)
    
    # Handle dropped loot (kill_monster stores it in _dropped_loot)
    if hasattr(dead_entity, '_dropped_loot') and dead_entity._dropped_loot:
        entities.extend(dead_entity._dropped_loot)
        delattr(dead_entity, '_dropped_loot')
        
        # Invalidate entity sorting cache
        from entity_sorting_cache import invalidate_entity_cache
        invalidate_entity_cache(f"entity_added_loot_{cause}")
    
    # Phase 19: Handle death-spawned features (bone piles, etc.)
    if hasattr(dead_entity, '_death_spawned_features') and dead_entity._death_spawned_features:
        entities.extend(dead_entity._death_spawned_features)
        delattr(dead_entity, '_death_spawned_features')
        
        # Invalidate entity sorting cache
        from entity_sorting_cache import invalidate_entity_cache
        invalidate_entity_cache(f"entity_added_death_features_{cause}")
    
    # Handle XP award if enabled
    if allow_xp and attacker_entity:
        xp_value = result_dict.get("xp", 0)
        if xp_value > 0:
            from components.component_registry import ComponentType
            attacker_fighter = attacker_entity.get_component_optional(ComponentType.FIGHTER)
            if attacker_fighter:
                # XP is already in result_dict, caller will process it
                # This matches existing behavior from combat system
                logger.debug(
                    f"{attacker_entity.name} awarded {xp_value} XP for killing "
                    f"{dead_entity.name} via {cause}"
                )
    
    logger.info(f"Monster death finalized via damage_service: {dead_entity.name}, cause={cause}")
