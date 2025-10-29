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

    def initialize(self, engine) -> None:
        """Initialize the AI system with engine reference.

        Args:
            engine: Reference to the main GameEngine instance
        """
        super().initialize(engine)
        logger.info("AISystem initialized")

    def update(self, dt: float) -> None:
        """Update the AI system for one frame.

        Processes AI entity turns when it's the enemy turn phase.

        Args:
            dt (float): Delta time since last update in seconds
        """
        if not self.engine or not hasattr(self.engine, "state_manager"):
            return

        state_manager = self.engine.state_manager
        if not state_manager:
            return

        game_state = state_manager.state
        current_state = game_state.current_state

        # CRITICAL: Don't process AI if player is dead
        if current_state == GameStates.PLAYER_DEAD:
            return

        # Only process AI during enemy turn
        # Phase 2: Use TurnManager instead of GameStates check
        turn_manager = getattr(self.engine, 'turn_manager', None)
        if turn_manager:
            # New system: Check TurnManager
            from engine.turn_manager import TurnPhase
            if not turn_manager.is_phase(TurnPhase.ENEMY):
                # Only log mismatch if it occurs (critical error)
                if current_state == GameStates.ENEMY_TURN and not hasattr(self, '_mismatch_logged'):
                    logger.error(f"CRITICAL: State mismatch! GameState={current_state}, TurnManager phase={turn_manager.current_phase}")
                    self._mismatch_logged = True
                return
            else:
                # Reset mismatch flag when we're back in sync
                if hasattr(self, '_mismatch_logged'):
                    delattr(self, '_mismatch_logged')
        else:
            # Backward compatibility: Fall back to GameStates check
            if current_state != GameStates.ENEMY_TURN:
                return

        # Process AI turns
        self._process_ai_turns(game_state)

        # Switch back to player turn when done (unless player died)
        if not self.turn_processing:
            # Check if player died during AI turn
            if state_manager.state.current_state == GameStates.PLAYER_DEAD:
                return
            
            # Check if player has active pathfinding before switching to player turn
            player = game_state.player
            pathfinding = player.get_component_optional(ComponentType.PATHFINDING)
            if (pathfinding and pathfinding.is_path_active()):
                # Process pathfinding movement instead of switching to player turn
                self._process_pathfinding_turn(state_manager)
            else:
                # Advance to ENVIRONMENT phase
                if turn_manager:
                    turn_manager.advance_turn()  # ENEMY → ENVIRONMENT
                    
                    # Process environment effects (hazards, etc.)
                    self._process_environment_phase(game_state)
                    
                    # Check if player died from environmental effects
                    if state_manager.state.current_state == GameStates.PLAYER_DEAD:
                        return
                    
                    # Advance to PLAYER phase
                    turn_manager.advance_turn()  # ENVIRONMENT → PLAYER
                    
                    # Process player status effects at start of their turn
                    self._process_player_status_effects(game_state)
                    
                    # Check if player died from status effects
                    if state_manager.state.current_state == GameStates.PLAYER_DEAD:
                        return
                    
                    # Use TurnController to restore appropriate state
                    # (handles RUBY_HEART_OBTAINED preservation automatically)
                    from systems.turn_controller import get_turn_controller
                    turn_controller = get_turn_controller()
                    if turn_controller:
                        # Restore preserved state or return to PLAYERS_TURN
                        if turn_controller.is_state_preserved():
                            restored_state = turn_controller.get_preserved_state()
                            state_manager.set_game_state(restored_state)
                            turn_controller.clear_preserved_state()
                        else:
                            state_manager.set_game_state(GameStates.PLAYERS_TURN)
                    else:
                        # Fallback if turn_controller not available
                        state_manager.set_game_state(GameStates.PLAYERS_TURN)
                else:
                    # Backward compatibility
                    # Process player status effects at start of their turn
                    self._process_player_status_effects(game_state)
                    
                    # Check if player died from status effects
                    if state_manager.state.current_state == GameStates.PLAYER_DEAD:
                        return
                    
                    # Use TurnController to restore appropriate state
                    # (handles RUBY_HEART_OBTAINED preservation automatically)
                    from systems.turn_controller import get_turn_controller
                    turn_controller = get_turn_controller()
                    if turn_controller:
                        # Restore preserved state or return to PLAYERS_TURN
                        if turn_controller.is_state_preserved():
                            restored_state = turn_controller.get_preserved_state()
                            state_manager.set_game_state(restored_state)
                            turn_controller.clear_preserved_state()
                        else:
                            state_manager.set_game_state(GameStates.PLAYERS_TURN)
                    else:
                        # Fallback if turn_controller not available
                        state_manager.set_game_state(GameStates.PLAYERS_TURN)

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

            for entity in ai_entities:
                if entity.fighter and entity.fighter.hp > 0:
                    self._process_entity_turn(entity, game_state)

                    # Check if entity died during turn processing
                    if entity.fighter.hp <= 0:
                        self._handle_entity_death(entity, game_state)

        finally:
            self.turn_processing = False
    
    def _process_pathfinding_turn(self, state_manager) -> None:
        """Process pathfinding movement for the player.
        
        Args:
            state_manager: Game state manager
        """
        # Import here to avoid circular imports
        from game_actions import ActionProcessor
        
        # Create action processor and process pathfinding
        action_processor = ActionProcessor(state_manager)
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
        """
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
            print(f">>> AISystem: {entity.name} turn, ai_type={ai_type}, has_strategy={strategy is not None}")

            if strategy:
                # Use custom strategy
                print(f">>> AISystem: Using custom strategy for {entity.name}")
                strategy(
                    entity, game_state.player, game_state.game_map, game_state.entities
                )
            else:
                # Use default AI behavior and process results
                print(f">>> AISystem: Calling {entity.name}.ai.take_turn()")
                ai_results = entity.ai.take_turn(
                    game_state.player, game_state.fov_map, game_state.game_map, game_state.entities
                )
                
                print(f">>> AISystem: {entity.name} returned {len(ai_results)} results")
                
                # Process AI turn results (combat, death, etc.)
                self._process_ai_results(ai_results, game_state)

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
            
            # Handle death (critical for player death detection)
            dead_entity = result.get("dead")
            if dead_entity:
                if dead_entity == game_state.player:
                    # CRITICAL: Player died during AI turn
                    if self.engine and hasattr(self.engine, "state_manager"):
                        self.engine.state_manager.set_game_state(GameStates.PLAYER_DEAD)
                        
                        # Add death message
                        death_message = MB.death(
                            "You died! Press any key to return to the main menu."
                        )
                        game_state.message_log.add_message(death_message)
                        
                        # Generate Entity death quote ONCE (don't regenerate every frame!)
                        player = game_state.player
                        statistics = player.get_component_optional(ComponentType.STATISTICS)
                        if statistics:
                            from entity_dialogue import get_entity_quote_for_death
                            self.engine.state_manager.state.death_screen_quote = get_entity_quote_for_death(
                                statistics, 
                                statistics.deepest_level
                            )
                        else:
                            self.engine.state_manager.state.death_screen_quote = "How... disappointing."
                        
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
                    
                    # Handle spawned entities (e.g., slime splitting)
                    if hasattr(dead_entity, '_spawned_entities') and dead_entity._spawned_entities:
                        # Add spawned entities to the entities list
                        game_state.entities.extend(dead_entity._spawned_entities)
                        # Clean up the temporary attribute
                        delattr(dead_entity, '_spawned_entities')
                        # Invalidate entity sorting cache when new entities are added
                        invalidate_entity_cache("entity_added_spawned_ai")
                    
                    logger.debug(f"Monster {dead_entity.name} died and transformed to corpse")
    
    def _process_environment_phase(self, game_state) -> None:
        """Process environmental effects during ENVIRONMENT phase.
        
        This is a temporary integration point. In the future, this should be
        handled by EnvironmentSystem as a registered turn phase listener.
        
        Args:
            game_state: Current game state
        """
        from engine.systems.environment_system import EnvironmentSystem
        
        # Create environment system and process
        env_system = EnvironmentSystem(self.engine)
        env_system.process(game_state)
    
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
