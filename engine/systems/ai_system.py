"""AI system for managing entity artificial intelligence.

This module contains the AISystem which handles all AI-controlled entity
behavior, including pathfinding, decision making, and turn processing.
It provides a centralized place for AI logic that can be extended with
different AI behaviors and strategies.
"""

from typing import Dict, Any, List, Optional, Callable
import logging

from ..system import System
from message_builder import MessageBuilder as MB
from game_states import GameStates
from entity_sorting_cache import invalidate_entity_cache
from components.component_registry import ComponentType
from state_management.state_config import StateManager
from engine.turn_state_adapter import TurnStateAdapter

logger = logging.getLogger(__name__)


class AISystem(System):
    """System responsible for processing AI entity behavior.

    The AISystem manages all AI-controlled entities, processing their
    turns, decision making, and interactions with the game world.
    It provides a framework for different AI behaviors and can be
    extended with new AI strategies.

    Attributes:
        ai_strategies (Dict): Mapping of AI types to strategy functions
        ai_callbacks (Dict): Callbacks for AI events (death, state changes, etc.)
        turn_queue (List): Queue of entities waiting to take their turn
        current_turn_entity: Entity currently taking its turn
        ai_debug_mode (bool): Whether to log detailed AI decisions
    """

    def __init__(self, priority: int = 50):
        """Initialize the AISystem.

        Args:
            priority (int, optional): System update priority. Defaults to 50 (middle).
        """
        super().__init__("ai", priority)

        # AI strategy registry
        self.ai_strategies: Dict[str, Callable] = {}

        # Event callbacks
        self.ai_callbacks: Dict[str, List[Callable]] = {
            "entity_death": [],
            "turn_start": [],
            "turn_end": [],
            "state_change": [],
        }

        # Turn management
        self.turn_queue: List[Any] = []
        self.current_turn_entity = None
        self.turn_processing = False
        
        # State preservation for turn transitions
        # Tracks what state we should restore after enemy turn
        self.state_before_enemy_turn = None

        # Debug and profiling
        self.ai_debug_mode = False
        self.turn_stats = {
            "total_turns": 0,
            "average_turn_time": 0.0,
            "entities_processed": 0,
        }

        # Turn/state coordination
        self.turn_adapter: TurnStateAdapter | None = None
        
        # ANTI-INFINITE-LOOP GUARDS
        # Track which entities have been processed this update to prevent duplicates
        self._processed_entities_this_update: set = set()
        # Track update call depth to detect re-entrancy
        self._update_call_depth: int = 0

    def initialize(self, engine) -> None:
        """Initialize the AI system with engine reference.

        Args:
            engine: Reference to the main GameEngine instance
        """
        super().initialize(engine)
        self.turn_adapter = TurnStateAdapter(
            engine.state_manager, getattr(engine, "turn_manager", None)
        )
        logger.info("AISystem initialized")

    def update(self, dt: float) -> None:
        """Update the AI system for one frame.

        Processes AI entity turns when it's the enemy turn phase.

        Args:
            dt (float): Delta time since last update in seconds
        """
        # GUARD 1: Prevent re-entrancy (detect if update() is called recursively)
        if self._update_call_depth > 0:
            logger.error(f"CRITICAL: AISystem.update() called recursively! Depth={self._update_call_depth}. Blocking to prevent infinite loop.")
            return
        
        self._update_call_depth += 1
        try:
            # GUARD 2: Ensure engine and state_manager exist
            if not self.engine or not hasattr(self.engine, "state_manager"):
                return

            state_manager = self.engine.state_manager
            if not state_manager:
                return

            game_state = state_manager.state
            current_state = game_state.current_state

            # GUARD 3: Don't process AI if player is dead or in other non-AI states
            # These states should NEVER trigger AI processing
            forbidden_states = {
                GameStates.PLAYER_DEAD,
                GameStates.SHOW_INVENTORY,
                GameStates.DROP_INVENTORY,
                GameStates.TARGETING,
                GameStates.THROW_SELECT_ITEM,
                GameStates.THROW_TARGETING,
                GameStates.LEVEL_UP,
                GameStates.CHARACTER_SCREEN,
                GameStates.NPC_DIALOGUE,
                GameStates.WIZARD_MENU,
                GameStates.CONFRONTATION,
                GameStates.VICTORY,
                GameStates.FAILURE,
            }
            
            if current_state in forbidden_states:
                # Reset processed entities set when not in AI phase
                self._processed_entities_this_update.clear()
                return

            # GUARD 4: Only process AI during enemy turn (via adapter)
            adapter = self.turn_adapter
            if adapter:
                if not adapter.is_enemy_turn():
                    # Only log mismatch if the state claims enemy turn but TM disagrees
                    if (
                        adapter.has_turn_manager
                        and current_state == GameStates.ENEMY_TURN
                        and not adapter.is_enemy_phase_consistent()
                        and not hasattr(self, "_mismatch_logged")
                    ):
                        phase = adapter.turn_manager_phase
                        logger.error(
                            f"CRITICAL: State mismatch! GameState={current_state}, "
                            f"TurnManager phase={phase}"
                        )
                        self._mismatch_logged = True
                    self._processed_entities_this_update.clear()
                    return
                else:
                    if hasattr(self, "_mismatch_logged"):
                        delattr(self, "_mismatch_logged")
            else:
                # Backward compatibility: Fall back to GameStates check
                if current_state != GameStates.ENEMY_TURN:
                    self._processed_entities_this_update.clear()
                    return

            # ═════════════════════════════════════════════════════════════════
            # ENEMY TURN PROCESSING - SIMPLIFIED, BOUNDED, DETERMINISTIC
            # ═════════════════════════════════════════════════════════════════
            
            # Determine if AI should be disabled (Phase 2: only in bot soak mode, not regular bot mode)
            disable_ai = getattr(self.engine, "disable_enemy_ai_for_bot", False)
            
            if not disable_ai:
                # Process AI turns normally (will use _processed_entities_this_update to prevent duplicates)
                self._process_ai_turns(game_state)
            else:
                logger.debug("AISystem: bot mode active, skipping enemy AI processing but preserving turn transitions")
            
            # ═════════════════════════════════════════════════════════════════
            # TRANSITION BACK TO PLAYER TURN
            # This happens IMMEDIATELY after AI processing completes.
            # No loops, no recursion, just one clean state transition.
            # ═════════════════════════════════════════════════════════════════
            
            # GUARD: If player died during AI turn, stay in PLAYER_DEAD state
            if state_manager.state.current_state == GameStates.PLAYER_DEAD:
                return
            
            # Check if player has active pathfinding before switching to player turn
            player = game_state.player
            pathfinding = player.get_component_optional(ComponentType.PATHFINDING)
            if pathfinding and pathfinding.is_path_active():
                # Process pathfinding movement instead of switching to player turn
                self._process_pathfinding_turn(state_manager)
                return
            
            # ─────────────────────────────────────────────────────────────────
            # SIMPLIFIED TURN TRANSITION: Always go back to PLAYERS_TURN
            # ─────────────────────────────────────────────────────────────────
            
            adapter = self.turn_adapter
            if adapter and adapter.has_turn_manager:
                adapter.advance_to_environment_phase()  # ENEMY → ENVIRONMENT

                if state_manager.state.current_state == GameStates.PLAYER_DEAD:
                    return

                adapter.advance_to_player_phase()  # ENVIRONMENT → PLAYER

                # Process player status effects at start of their turn
                self._process_player_status_effects(game_state)

                if state_manager.state.current_state == GameStates.PLAYER_DEAD:
                    return
            
            # Restore preserved state or return to PLAYERS_TURN
            # (handles RUBY_HEART_OBTAINED preservation automatically)
            from systems.turn_controller import get_turn_controller
            turn_controller = get_turn_controller()
            
            if turn_controller and turn_controller.is_state_preserved():
                restored_state = turn_controller.get_preserved_state()
                state_manager.set_game_state(restored_state)
                turn_controller.clear_preserved_state()
            else:
                # DEFAULT: Always return to PLAYERS_TURN after enemy phase
                state_manager.set_game_state(GameStates.PLAYERS_TURN)
            
            logger.debug(f"AISystem: Transitioned from ENEMY_TURN → {state_manager.state.current_state}")
            
        finally:
            # Always decrement depth counter, even if exception occurs
            self._update_call_depth -= 1
            # Clear processed entities set at end of update for next cycle
            if self._update_call_depth == 0:
                self._processed_entities_this_update.clear()

    def _process_ai_turns(self, game_state) -> None:
        """Process all AI entity turns.

        Args:
            game_state: Current game state containing entities and world data
        """
        if self.turn_processing:
            return

        self.turn_processing = True

        try:
            # Get all AI entities that need to take turns
            ai_entities = self._get_ai_entities(game_state.entities, game_state.player)
            
            logger.debug(f"AISystem: Processing {len(ai_entities)} AI entities")

            # CRITICAL: Bounded loop - each enemy acts exactly ONCE per enemy phase
            # No while loops, no recursion, no "loop until results"
            for entity in ai_entities:
                if entity.fighter and entity.fighter.hp > 0:
                    self._process_entity_turn(entity, game_state)

                    # Check if entity died during turn processing
                    if entity.fighter.hp <= 0:
                        self._handle_entity_death(entity, game_state)
            
            logger.debug(f"AISystem: processed {len(ai_entities)} enemies, ending ENEMY_TURN → PLAYERS_TURN")

        finally:
            self.turn_processing = False
    
    def _process_pathfinding_turn(self, state_manager) -> None:
        """Process pathfinding movement for the player.
        
        Args:
            state_manager: Game state manager
        """
        # Try to reuse the shared action processor configured by the engine
        action_processor = state_manager.get_extra_data("action_processor")

        if action_processor is None:
            logger.warning("AISystem: Missing shared ActionProcessor; creating fallback instance")

            # Import here to avoid circular imports
            from game_actions import ActionProcessor

            action_processor = ActionProcessor(state_manager)

            # If the engine has a turn manager, make sure the processor uses it
            turn_manager = getattr(self.engine, "turn_manager", None) if self.engine else None
            if turn_manager:
                action_processor.turn_manager = turn_manager

                from systems.turn_controller import (
                    get_turn_controller,
                    initialize_turn_controller,
                )

                existing_controller = get_turn_controller()
                if existing_controller and existing_controller.turn_manager is turn_manager:
                    action_processor.turn_controller = existing_controller
                else:
                    action_processor.turn_controller = initialize_turn_controller(
                        state_manager, turn_manager
                    )

            state_manager.set_extra_data("action_processor", action_processor)

        action_processor.process_pathfinding_turn()

    def _get_ai_entities(self, entities: List[Any], player: Any) -> List[Any]:
        """Get all entities that have AI and should take turns.

        Args:
            entities (List): All entities in the game
            player: The player entity (excluded from AI processing)

        Returns:
            List: Entities with AI that should take turns
        """
        return [
            entity
            for entity in entities
            if entity.ai
            and entity != player
            and entity.fighter
            and entity.fighter.hp > 0
        ]

    def _process_entity_turn(self, entity: Any, game_state) -> None:
        """Process a single entity's AI turn.

        Args:
            entity: The entity taking its turn
            game_state: Current game state
        
        CRITICAL INVARIANT:
        Each entity should only take ONE ai.take_turn() call per ENEMY phase.
        Calling take_turn() multiple times without state changes causes infinite loops,
        especially in bot mode where there's no blocking input to break the cycle.
        """
        # GUARD: Prevent processing the same entity multiple times in one update cycle
        # Use entity's id() as a unique identifier (entities don't have stable IDs)
        entity_id = id(entity)
        if entity_id in self._processed_entities_this_update:
            logger.warning(f"ANTI-LOOP: Skipping duplicate turn for {entity.name} (already processed this update)")
            return
        
        # Mark this entity as processed
        self._processed_entities_this_update.add(entity_id)
        
        import time

        turn_start_time = time.time()

        self.current_turn_entity = entity

        # Notify turn start callbacks
        self._notify_callbacks("turn_start", entity)

        try:
            # Get AI strategy for this entity
            ai_type = getattr(entity.ai, "ai_type", "basic")
            strategy = self.ai_strategies.get(ai_type)
            
            logger.debug(f"Processing AI turn for {entity.name}: ai_type={ai_type}, has_strategy={strategy is not None}")

            if strategy:
                # Use custom strategy
                strategy(
                    entity, game_state.player, game_state.game_map, game_state.entities
                )
            else:
                # Use default AI behavior and process results
                ai_results = entity.ai.take_turn(
                    game_state.player, game_state.fov_map, game_state.game_map, game_state.entities
                )
                
                # Process AI turn results (combat, death, etc.)
                self._process_ai_results(ai_results, game_state)
            
            # Phase 19: Apply regeneration after entity completes its turn
            self._apply_regeneration(entity, game_state)
            
            # Check for portal collision AFTER AI moves (for monsters with portal_usable=True)
            from services.portal_manager import get_portal_manager
            portal_manager = get_portal_manager()
            portal_collision = portal_manager.check_portal_collision(entity, game_state.entities)
            if portal_collision and portal_collision.get('teleported'):
                logger.info(f"Monster portal teleportation: {entity.name} {portal_collision.get('from_pos')} -> {portal_collision.get('to_pos')}")
                message = portal_collision.get('message', f"{entity.name} vanishes through the portal!")
                # Add message to results (handles both string messages and Message objects)
                ai_results.append({'message': message})

            # Update turn statistics
            turn_time = time.time() - turn_start_time
            self._update_turn_stats(turn_time)

            if self.ai_debug_mode:
                logger.debug(f"Entity {entity.name} completed turn in {turn_time:.3f}s")

        except Exception as e:
            logger.error(f"Error processing AI turn for {entity.name}: {e}")

        finally:
            # Notify turn end callbacks
            self._notify_callbacks("turn_end", entity)
            self.current_turn_entity = None

    def _process_ai_results(self, results: List[Dict[str, Any]], game_state) -> None:
        """Process results from AI actions (combat, movement, etc.).
        
        Args:
            results: List of result dictionaries from AI actions
            game_state: Current game state
        """
        if not results:
            return
            
        from game_messages import Message
        
        for result in results:
            # Handle messages
            message = result.get("message")
            if message and game_state.message_log:
                game_state.message_log.add_message(message)
            
            # Phase 19: Handle Split Under Pressure
            split_data = result.get("split")
            if split_data:
                # Entity is splitting - execute the split
                from services.slime_split_service import execute_split
                spawned_children = execute_split(
                    split_data,
                    game_map=game_state.game_map,
                    entities=game_state.entities
                )
                # Add children to entities list
                if spawned_children:
                    game_state.entities.extend(spawned_children)
                    invalidate_entity_cache("entity_added_split_ai")
                
                logger.debug(f"Entity {split_data['original_entity'].name} split into {len(spawned_children)} children")
            
            # Phase 19: Handle rally ending (when chieftain is damaged)
            if result.get('end_rally'):
                chieftain_id = result.get('chieftain_id')
                if chieftain_id:
                    # Remove rally buff from all entities with rally_buff from this chieftain
                    from components.component_registry import ComponentType
                    for entity in game_state.entities:
                        status_effects = entity.get_component_optional(ComponentType.STATUS_EFFECTS)
                        if status_effects and status_effects.has_effect('rally_buff'):
                            rally_buff = status_effects.get_effect('rally_buff')
                            if rally_buff and hasattr(rally_buff, 'chieftain_id') and rally_buff.chieftain_id == chieftain_id:
                                # Remove rally buff
                                remove_results = status_effects.remove_effect('rally_buff')
                                # Add messages to game log
                                for remove_result in remove_results:
                                    msg = remove_result.get('message')
                                    if msg and game_state.message_log:
                                        game_state.message_log.add_message(msg)
                                
                                # Clear AI directive
                                if hasattr(entity, 'ai') and hasattr(entity.ai, 'rally_directive_target_id'):
                                    entity.ai.rally_directive_target_id = None
                    
                    logger.info(f"[ORC CHIEFTAIN] Rally ended - chieftain {chieftain_id} was damaged")
            
            # Phase 19: Handle chant interruption (when shaman is damaged)
            if result.get('interrupt_chant'):
                shaman_id = result.get('shaman_id')
                if shaman_id:
                    # Remove dissonant_chant effect from all entities (should just be player)
                    from components.component_registry import ComponentType
                    for entity in game_state.entities:
                        status_effects = entity.get_component_optional(ComponentType.STATUS_EFFECTS)
                        if status_effects and status_effects.has_effect('dissonant_chant'):
                            # Remove chant effect
                            remove_results = status_effects.remove_effect('dissonant_chant')
                            # Add messages to game log
                            for remove_result in remove_results:
                                msg = remove_result.get('message')
                                if msg and game_state.message_log:
                                    game_state.message_log.add_message(msg)
                    
                    # Record interrupt metric
                    try:
                        from services.scenario_metrics import get_active_metrics_collector
                        metrics = get_active_metrics_collector()
                        if metrics:
                            metrics.increment('shaman_chant_interrupts')
                    except Exception:
                        pass
                    
                    logger.info(f"[ORC SHAMAN] Chant interrupted - shaman {shaman_id} was damaged")
            
            # Handle death (critical for player death detection)
            dead_entity = result.get("dead")
            if dead_entity:
                if dead_entity == game_state.player:
                    # CRITICAL: Player died during AI turn
                    # Use shared finalization helper to ensure run_metrics are finalized
                    # and bot summary is logged, regardless of which system detected the death
                    if self.engine and hasattr(self.engine, "state_manager"):
                        # Get constants from game_state (stored there during initialization)
                        constants = getattr(game_state, "constants", {})
                        
                        import engine_integration
                        engine_integration.finalize_player_death(
                            self.engine.state_manager,
                            constants,
                            cause="enemy_attack"
                        )
                        
                        logger.info(f"Player killed by {self.current_turn_entity.name if self.current_turn_entity else 'unknown'}")
                else:
                    # Monster died - transform to corpse and handle loot
                    from death_functions import kill_monster
                    death_message = kill_monster(dead_entity, game_state.game_map, game_state.entities)
                    if game_state.message_log:
                        game_state.message_log.add_message(death_message)
                    
                    # Handle dropped loot
                    if hasattr(dead_entity, '_dropped_loot') and dead_entity._dropped_loot:
                        # Add dropped items to the entities list
                        game_state.entities.extend(dead_entity._dropped_loot)
                        # Clean up the temporary attribute
                        delattr(dead_entity, '_dropped_loot')
                        # Invalidate entity sorting cache when new entities are added
                        invalidate_entity_cache("entity_added_loot_ai")
                    
                    # Phase 19: Old split-on-death mechanism removed
                    # _spawned_entities no longer used (Split Under Pressure replaced it)
                    
                    logger.debug(f"Monster {dead_entity.name} died and transformed to corpse")
    
    def _apply_regeneration(self, entity: Any, game_state) -> None:
        """Apply regeneration to entities with regeneration_amount attribute.
        
        Phase 19: Troll regeneration ability.
        Heals the entity at the end of its turn if:
        - Entity has regeneration_amount attribute
        - Entity has fighter component
        - Entity is not at max HP
        - Regeneration is not suppressed by acid/fire damage
        
        Args:
            entity: The entity to potentially regenerate
            game_state: Current game state (for message logging)
        """
        # Check if entity has regeneration ability
        if not hasattr(entity, 'regeneration_amount'):
            return
        
        regeneration_amount = entity.regeneration_amount
        if regeneration_amount <= 0:
            return
        
        # Check if entity has fighter component and is alive
        if not hasattr(entity, 'fighter') or not entity.fighter:
            return
        
        fighter = entity.fighter
        
        # Only regenerate if below max HP
        if fighter.hp >= fighter.max_hp:
            return
        
        # Phase 19: Check for regeneration suppression (acid/fire damage)
        # Get current turn number from TurnManager
        turn_number = None
        try:
            from engine.turn_manager import TurnManager
            turn_mgr = TurnManager.get_instance()
            if turn_mgr:
                turn_number = turn_mgr.turn_number
        except:
            pass
        
        # Check if regeneration is suppressed
        suppressed_until = getattr(entity, 'regeneration_suppressed_until_turn', None)
        if suppressed_until is not None and turn_number is not None:
            if turn_number < suppressed_until:
                # Regeneration is suppressed - show message
                if game_state.message_log:
                    from game_messages import Message
                    message = Message(
                        f"The acid prevents the {entity.name} from regenerating!",
                        (200, 100, 0)  # Orange for suppression
                    )
                    game_state.message_log.add_message(message)
                    logger.debug(f"{entity.name} regeneration suppressed (turn {turn_number}, suppressed until {suppressed_until})")
                
                # Record suppression metric
                if hasattr(game_state, 'scenario_metrics'):
                    game_state.scenario_metrics['troll_regen_suppressed'] = game_state.scenario_metrics.get('troll_regen_suppressed', 0) + 1
                
                return
        
        # Record regeneration attempt metric
        if hasattr(game_state, 'scenario_metrics'):
            game_state.scenario_metrics['troll_regen_attempts'] = game_state.scenario_metrics.get('troll_regen_attempts', 0) + 1
        
        # Calculate healing amount (don't exceed max HP)
        old_hp = fighter.hp
        fighter.hp = min(fighter.hp + regeneration_amount, fighter.max_hp)
        actual_heal = fighter.hp - old_hp
        
        # Log regeneration message
        if actual_heal > 0 and game_state.message_log:
            from game_messages import Message
            message = Message(
                f"The {entity.name} regenerates {actual_heal} HP!",
                (0, 200, 0)  # Green for regeneration
            )
            game_state.message_log.add_message(message)
            logger.debug(f"{entity.name} regenerated {actual_heal} HP ({old_hp} -> {fighter.hp})")
            
            # Record successful regeneration metric
            if hasattr(game_state, 'scenario_metrics'):
                game_state.scenario_metrics['troll_regen_successes'] = game_state.scenario_metrics.get('troll_regen_successes', 0) + 1
    
    def _process_player_status_effects(self, game_state) -> None:
        """Process player status effects at the start of their turn.
        
        This handles effects like:
        - IdentifyModeEffect (auto-identify items)
        - RegenerationEffect (heal over time)
        - Status effect durations and expiration
        
        Args:
            game_state: Current game state
        """
        player = game_state.player
        if not player or not hasattr(player, 'status_effects') or not player.status_effects:
            return
        
        # Process status effects at turn start
        # Pass entities list so effects like IdentifyMode can sync globally
        status_results = player.status_effects.process_turn_start(entities=game_state.entities)
        
        # Add any messages to the message log
        for result in status_results:
            if 'message' in result:
                game_state.message_log.add_message(result['message'])
            
            # Check for player death from status effects (e.g., poison, bleeding)
            if result.get('dead'):
                from game_states import GameStates
                self.engine.state_manager.set_game_state(GameStates.PLAYER_DEAD)

    def _handle_entity_death(self, entity: Any, game_state) -> None:
        """Handle an entity's death during AI processing.

        Args:
            entity: The entity that died
            game_state: Current game state
        """
        # Notify death callbacks
        self._notify_callbacks("entity_death", entity)

        # Request FOV recompute if needed
        if hasattr(self.engine.state_manager, "request_fov_recompute"):
            self.engine.state_manager.request_fov_recompute()

        if self.ai_debug_mode:
            logger.debug(f"Entity {entity.name} died during AI processing")

    def _update_turn_stats(self, turn_time: float) -> None:
        """Update turn processing statistics.

        Args:
            turn_time (float): Time taken for the turn in seconds
        """
        self.turn_stats["total_turns"] += 1
        self.turn_stats["entities_processed"] += 1

        # Update rolling average
        total_time = (
            self.turn_stats["average_turn_time"] * (self.turn_stats["total_turns"] - 1)
            + turn_time
        )
        self.turn_stats["average_turn_time"] = (
            total_time / self.turn_stats["total_turns"]
        )

    def register_ai_strategy(self, ai_type: str, strategy_func: Callable) -> None:
        """Register a custom AI strategy.

        Args:
            ai_type (str): Identifier for this AI strategy
            strategy_func (Callable): Function that implements the AI behavior
        """
        self.ai_strategies[ai_type] = strategy_func
        logger.info(f"Registered AI strategy: {ai_type}")

    def unregister_ai_strategy(self, ai_type: str) -> None:
        """Unregister an AI strategy.

        Args:
            ai_type (str): Identifier of the strategy to remove
        """
        if ai_type in self.ai_strategies:
            del self.ai_strategies[ai_type]
            logger.info(f"Unregistered AI strategy: {ai_type}")

    def register_ai_callback(self, event_type: str, callback: Callable) -> None:
        """Register a callback for AI events.

        Args:
            event_type (str): Type of event to listen for
            callback (Callable): Function to call when event occurs
        """
        if event_type in self.ai_callbacks:
            self.ai_callbacks[event_type].append(callback)
        else:
            self.ai_callbacks[event_type] = [callback]

    def unregister_ai_callback(self, event_type: str, callback: Callable) -> None:
        """Unregister an AI event callback.

        Args:
            event_type (str): Type of event to stop listening for
            callback (Callable): Function to remove from callbacks
        """
        if (
            event_type in self.ai_callbacks
            and callback in self.ai_callbacks[event_type]
        ):
            self.ai_callbacks[event_type].remove(callback)

    def _notify_callbacks(self, event_type: str, entity: Any) -> None:
        """Notify all callbacks for a specific event type.

        Args:
            event_type (str): Type of event that occurred
            entity: Entity involved in the event
        """
        for callback in self.ai_callbacks.get(event_type, []):
            try:
                callback(entity)
            except Exception as e:
                logger.error(f"Error in AI callback for {event_type}: {e}")

    def set_debug_mode(self, enabled: bool) -> None:
        """Enable or disable AI debug logging.

        Args:
            enabled (bool): Whether to enable debug mode
        """
        self.ai_debug_mode = enabled
        logger.info(f"AI debug mode {'enabled' if enabled else 'disabled'}")

    def get_turn_stats(self) -> Dict[str, Any]:
        """Get AI turn processing statistics.

        Returns:
            Dict: Statistics about AI turn processing
        """
        return self.turn_stats.copy()

    def reset_turn_stats(self) -> None:
        """Reset turn processing statistics."""
        self.turn_stats = {
            "total_turns": 0,
            "average_turn_time": 0.0,
            "entities_processed": 0,
        }
        logger.info("AI turn statistics reset")

    def get_active_ai_entities(self) -> List[Any]:
        """Get all currently active AI entities.

        Returns:
            List: Active AI entities
        """
        if not self.engine or not hasattr(self.engine, "state_manager"):
            return []

        state_manager = self.engine.state_manager
        if not state_manager:
            return []

        game_state = state_manager.state
        return self._get_ai_entities(game_state.entities, game_state.player)

    def pause_ai(self) -> None:
        """Pause AI processing (for debugging or special game states)."""
        self.enabled = False
        logger.info("AI processing paused")

    def resume_ai(self) -> None:
        """Resume AI processing."""
        self.enabled = True
        logger.info("AI processing resumed")

    def cleanup(self) -> None:
        """Clean up AI system resources."""
        self.ai_strategies.clear()
        self.ai_callbacks.clear()
        self.turn_queue.clear()
        self.current_turn_entity = None
        self.turn_processing = False
        logger.info("AISystem cleaned up")
