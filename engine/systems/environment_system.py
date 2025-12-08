"""Environment System - Handles environmental effects during ENVIRONMENT turn phase.

This system processes:
- Ground hazards (fire, poison gas, etc.)
- Environmental damage and aging
- Future: Weather effects, traps, timed events

Separated from AISystem for cleaner architecture and turn phase management.
"""

import logging
from typing import Any, Optional

from ..system import System
from ..turn_manager import TurnPhase
from components.component_registry import ComponentType
from message_builder import MessageBuilder as MB
from entity_sorting_cache import invalidate_entity_cache

logger = logging.getLogger(__name__)


class EnvironmentSystem(System):
    """System for processing environmental effects.
    
    Handles all environmental effects during the ENVIRONMENT turn phase:
    - Ground hazards (fire, poison, etc.)
    - Hazard aging and expiration
    - Environmental damage to entities
    - Death handling from environmental effects
    
    Future enhancements:
    - Weather effects (rain weakening fire, etc.)
    - Trap activation
    - Timed dungeon events
    """
    
    def __init__(self, priority: int = 60):
        """Initialize environment system.

        Args:
            priority: System update priority (runs after AI)
        """
        super().__init__("environment", priority)
        self._turn_manager: Optional[Any] = None
        logger.info(f"{self.name} initialized")

    def initialize(self, engine) -> None:
        """Initialize the environment system with engine reference."""
        super().initialize(engine)

        turn_manager = getattr(engine, "turn_manager", None)
        if not turn_manager:
            logger.warning("EnvironmentSystem initialized without TurnManager; hazards will not process")
            return

        turn_manager.register_listener(TurnPhase.ENVIRONMENT, self._on_environment_phase_start, "start")
        turn_manager.register_listener(TurnPhase.ENVIRONMENT, self._on_environment_phase_end, "end")
        self._turn_manager = turn_manager
        logger.debug("EnvironmentSystem registered for ENVIRONMENT phase callbacks")

    def cleanup(self) -> None:
        """Unregister listeners when system is cleaned up."""
        if self._turn_manager:
            self._turn_manager.unregister_listener(TurnPhase.ENVIRONMENT, self._on_environment_phase_start, "start")
            self._turn_manager.unregister_listener(TurnPhase.ENVIRONMENT, self._on_environment_phase_end, "end")
            self._turn_manager = None

        super().cleanup()

    def _on_environment_phase_start(self) -> None:
        """Handle ENVIRONMENT phase start by processing hazards."""
        if not self.engine or not hasattr(self.engine, "state_manager"):
            logger.debug("EnvironmentSystem start callback without engine state; skipping")
            return

        game_state = getattr(self.engine.state_manager, "state", None)
        if not game_state:
            logger.debug("EnvironmentSystem start callback without game state; skipping")
            return

        self.process(game_state)

    def _on_environment_phase_end(self) -> None:
        """Handle ENVIRONMENT phase end."""
        logger.debug("EnvironmentSystem ENVIRONMENT phase completed")
    
    def update(self, dt: float) -> None:
        """Update the environment system for one frame.
        
        Required by System base class. For environment system,
        actual processing happens in process() during ENVIRONMENT phase.
        
        Args:
            dt: Delta time since last update in seconds
        """
        # Environment system processes during ENVIRONMENT turn phase
        # Actual work is done in process() method when called by turn manager
        pass
    
    def process(self, game_state) -> None:
        """Process all environmental effects for the current turn.
        
        Called during the ENVIRONMENT phase of the turn cycle.
        Processes hazards, applies damage, handles deaths, and ages effects.
        
        Args:
            game_state: Current game state containing map, entities, and message log
        """
        if not game_state:
            return
        
        # Process ground hazards
        self._process_hazards(game_state)
        
        # Phase 10.1: Process pending plague reanimations
        self._process_reanimations(game_state)
        
        # Future: Add weather processing
        # self._process_weather(game_state)
        
        # Future: Add trap processing
        # self._process_traps(game_state)
    
    def _process_hazards(self, game_state) -> None:
        """Process ground hazards for the current turn.
        
        Ages all active hazards, applies damage to entities standing on hazards,
        and removes expired hazards.
        
        Args:
            game_state: Current game state containing map and entities
        """
        if not game_state.game_map:
            return
            
        if not hasattr(game_state.game_map, 'hazard_manager'):
            return
            
        hazard_manager = game_state.game_map.hazard_manager
        if not hazard_manager:
            return
        
        from game_states import GameStates
        
        # Apply damage to entities standing on hazards BEFORE aging
        # This ensures entities take damage for the full current turn
        for entity in game_state.entities:
            fighter = entity.get_component_optional(ComponentType.FIGHTER)
            if not fighter:
                continue
                
            if fighter.hp <= 0:
                continue  # Don't damage dead entities
            
            hazard = hazard_manager.get_hazard_at(entity.x, entity.y)
            if hazard:
                damage = hazard.get_current_damage()
                if damage > 0:
                    # Create hazard type name for message
                    hazard_name = hazard.hazard_type.name.replace('_', ' ').title()
                    
                    # Add message for damage
                    if game_state.message_log:
                        if entity == game_state.player:
                            message = MB.custom(
                                f"The {hazard_name} burns you for {damage} damage!",
                                MB.ORANGE
                            )
                        else:
                            message = MB.custom(
                                f"The {entity.name} takes {damage} damage from the {hazard_name}!",
                                (255, 200, 150)
                            )
                        game_state.message_log.add_message(message)
                    
                    # Apply damage
                    damage_results = entity.fighter.take_damage(damage)
                    
                    # Process death if entity died from hazard damage
                    for result in damage_results:
                        dead_entity = result.get('dead')
                        if dead_entity:
                            self._handle_hazard_death(dead_entity, hazard_name, game_state)
        
        # Age all hazards after damage application
        # This removes expired hazards and decrements remaining_turns
        hazard_manager.age_all_hazards()
        logger.debug("Hazard processing complete for turn")
    
    def _handle_hazard_death(self, entity: Any, hazard_name: str, game_state) -> None:
        """Handle entity death from environmental hazard.
        
        Args:
            entity: The entity that died
            hazard_name: Name of the hazard that killed the entity
            game_state: Current game state
        """
        if entity == game_state.player:
            # Player died from hazard
            # Use shared finalization helper to ensure run_metrics are finalized
            # and bot summary is logged, regardless of which system detected the death
            if self.engine and hasattr(self.engine, 'state_manager'):
                # Get constants from game_state (stored there during initialization)
                constants = getattr(game_state, "constants", {})
                
                import engine_integration
                engine_integration.finalize_player_death(
                    self.engine.state_manager,
                    constants,
                    cause=f"hazard_{hazard_name}"
                )
                
                logger.info(f"Player killed by {hazard_name}")
        else:
            # Monster died from hazard
            from death_functions import kill_monster
            death_message = kill_monster(entity, game_state.game_map, game_state.entities)
            if game_state.message_log:
                game_state.message_log.add_message(death_message)
            
            # Handle dropped loot
            if hasattr(entity, '_dropped_loot') and entity._dropped_loot:
                game_state.entities.extend(entity._dropped_loot)
                delattr(entity, '_dropped_loot')
                invalidate_entity_cache("entity_added_loot_hazard")
            
            # Handle spawned entities (e.g., slime splitting)
            if hasattr(entity, '_spawned_entities') and entity._spawned_entities:
                game_state.entities.extend(entity._spawned_entities)
                delattr(entity, '_spawned_entities')
                invalidate_entity_cache("entity_added_spawned_hazard")
            
            logger.debug(f"Monster {entity.name} died from {hazard_name}")
    
    def _process_reanimations(self, game_state) -> None:
        """Process pending plague reanimations.
        
        Phase 10.1: Check all corpses for pending reanimation data and
        spawn revenant zombies when their timer expires.
        
        Args:
            game_state: Current game state containing entities and map
        """
        from death_functions import process_pending_reanimations
        from rendering.entity_sorting import invalidate_entity_cache
        
        entities = game_state.entities
        game_map = game_state.game_map
        
        # Get current turn number if available
        turn_number = getattr(game_state, 'turn_number', 0)
        
        # Process any pending reanimations
        results = process_pending_reanimations(entities, game_map, turn_number)
        
        for result in results:
            # Add message to log
            if 'message' in result and game_state.message_log:
                game_state.message_log.add_message(result['message'])
            
            # Add new revenant zombie to entities list
            if 'new_entity' in result:
                new_entity = result['new_entity']
                entities.append(new_entity)
                invalidate_entity_cache("entity_added_reanimation")
                logger.info(f"Plague reanimation: {new_entity.name} spawned at ({new_entity.x}, {new_entity.y})")

