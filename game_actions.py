"""Game action processing system.

This module provides a clean, modular way to handle game actions by breaking
down the monolithic action processing into focused, testable components.
Also integrates Entity dialogue for key game moments (Phase 1 expansion).
"""

from typing import Dict, Any, Optional, Tuple
import logging

from message_builder import MessageBuilder as MB
from game_states import GameStates
from state_management.state_config import StateManager
from config.game_constants import get_constants
from entity_sorting_cache import invalidate_entity_cache
from entity_dialogue import EntityDialogue
from components.component_registry import ComponentType

logger = logging.getLogger(__name__)


class ActionProcessor:
    """Processes game actions in a modular, maintainable way.
    
    This class replaces the monolithic _process_game_actions function with
    a clean, extensible system that separates concerns and improves testability.
    
    Attributes:
        state_manager: Game state manager for accessing and updating game state
        constants: Game configuration constants
        action_handlers: Dictionary mapping action types to handler methods
    """
    
    def __init__(self, state_manager):
        """Initialize the ActionProcessor.
        
        Args:
            state_manager: Game state manager instance
        """
        self.state_manager = state_manager
        self.turn_manager = None  # Will be set by engine (Phase 3)
        self.constants = get_constants()
        
        # Initialize TurnController for centralized turn flow
        from systems.turn_controller import TurnController, initialize_turn_controller
        self.turn_controller = initialize_turn_controller(state_manager, self.turn_manager)
        
        # Map action types to their handler methods
        self.action_handlers = {
            'show_inventory': self._handle_show_inventory_deprecated,  # DEPRECATED - use sidebar
            'drop_inventory': self._handle_drop_inventory_deprecated,  # DEPRECATED - use sidebar
            'show_character_screen': self._handle_show_character_screen,
            'show_wizard_menu': self._handle_show_wizard_menu,  # Tier 2: Wizard Mode
            'exit': self._handle_exit,
            'move': self._handle_movement,
            'wait': self._handle_wait,
            'pickup': self._handle_pickup,
            'inventory_index': self._handle_inventory_action,
            'take_stairs': self._handle_stairs,
            'level_up': self._handle_level_up,
            'start_auto_explore': self._handle_start_auto_explore,
            'throw': self._handle_throw_action,
            'search': self._handle_search,
        }
        
        # Map mouse actions to their handlers
        self.mouse_handlers = {
            'left_click': self._handle_left_click,
            'right_click': self._handle_right_click,
            'sidebar_click': self._handle_sidebar_click,
            'sidebar_right_click': self._handle_sidebar_right_click,
        }
    
    def process_actions(self, action: Dict[str, Any], mouse_action: Dict[str, Any]) -> None:
        """Process keyboard and mouse actions.
        
        Args:
            action: Dictionary of keyboard actions
            mouse_action: Dictionary of mouse actions
        """
        import logging
        logger = logging.getLogger(__name__)
        if mouse_action:
            logger.warning(f"PROCESS_ACTIONS: mouse_action = {mouse_action}")
        current_state = self.state_manager.state.current_state
        
        # CRITICAL: Don't process any game actions if player is dead
        if current_state == GameStates.PLAYER_DEAD:
            return
        
        # AUTO-PROCESS: Handle auto-explore or pathfinding movement if active (before processing input)
        # This enables auto-exploration and continuous pathfinding
        # Use StateManager to check if movement/exploration is allowed
        if StateManager.allows_movement(current_state):
            player = self.state_manager.state.player
            
            # Check for auto-explore first (higher priority)
            auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE) if player else None
            if auto_explore and auto_explore.is_active():
                # Process auto-explore movement automatically
                self._process_auto_explore_turn()
                # Check if any key was pressed to cancel
                if action or mouse_action:
                    # Any input cancels auto-explore
                    auto_explore.stop("Cancelled")
                    self.state_manager.state.message_log.add_message(
                        MB.info("Auto-explore cancelled")
                    )
                return  # Don't process other input this turn
            
            # Fall back to pathfinding if no auto-explore
            pathfinding = player.get_component_optional(ComponentType.PATHFINDING) if player else None
            if pathfinding and pathfinding.is_path_active():
                # Process pathfinding movement automatically
                self._process_pathfinding_movement_action(None)
                return  # Don't process other input this turn
        
        # Process keyboard actions
        if action:
            print(f">>> KEYBOARD ACTION RECEIVED: {action}")
        for action_type, value in action.items():
            # Use 'is not None' instead of just 'value' to handle inventory_index=0
            if value is not None and action_type in self.action_handlers:
                try:
                    print(f">>> Calling handler for {action_type}")
                    self.action_handlers[action_type](value)
                except Exception as e:
                    logger.error(f"Error processing action {action_type}: {e}", exc_info=True)
            else:
                print(f">>> No handler for action {action_type}")
        
        # Process mouse actions
        for mouse_action_type, value in mouse_action.items():
            logger.warning(f"Mouse action type: {mouse_action_type}, value: {value}, has handler: {mouse_action_type in self.mouse_handlers}")
            if value and mouse_action_type in self.mouse_handlers:
                try:
                    logger.warning(f"Calling mouse handler for {mouse_action_type}")
                    self.mouse_handlers[mouse_action_type](value)
                except Exception as e:
                    logger.error(f"Error processing mouse action {mouse_action_type}: {e}", exc_info=True)
    
    
    def _handle_show_inventory_deprecated(self, _) -> None:
        """DEPRECATED: Handle showing inventory menu (use sidebar UI instead).
        
        This is maintained for backwards compatibility only.
        The 'i' key binding has been removed. Use the sidebar UI for inventory.
        """
        logger.warning("DEPRECATED: show_inventory action triggered. Use sidebar UI instead.")
        # Don't actually enter the old inventory state - it's deprecated
    
    def _handle_drop_inventory_deprecated(self, _) -> None:
        """DEPRECATED: Handle showing drop inventory menu (use sidebar UI instead).
        
        This is maintained for backwards compatibility only.
        The 'd' key binding has been removed. Use the sidebar UI for inventory.
        """
        logger.warning("DEPRECATED: drop_inventory action triggered. Use sidebar UI instead.")
        # Don't actually enter the old inventory state - it's deprecated
    
    def _handle_show_character_screen(self, _) -> None:
        """Handle showing the character screen."""
        self.state_manager.set_game_state(GameStates.CHARACTER_SCREEN)
    
    def _handle_show_wizard_menu(self, _) -> None:
        """Handle showing the wizard mode debug menu (Tier 2)."""
        self.state_manager.set_game_state(GameStates.WIZARD_MENU)
    
    def _handle_throw_action(self, _) -> None:
        """Handle throw action - select item then target.
        
        Opens inventory selection for choosing an item to throw.
        After item is selected, enters throw targeting mode.
        """
        current_state = self.state_manager.state.current_state
        if current_state != GameStates.PLAYERS_TURN:
            return
        
        player = self.state_manager.state.player
        message_log = self.state_manager.state.message_log
        
        if not player or not player.get_component_optional(ComponentType.INVENTORY) or not player.get_component_optional(ComponentType.INVENTORY).items:
            from message_builder import MessageBuilder as MB
            message = MB.warning("You have nothing to throw.")
            if message_log:
                message_log.add_message(message)
            return
        
        # Show inventory selection screen for throwing
        self.state_manager.set_game_state(GameStates.THROW_SELECT_ITEM)
    
    def _handle_start_auto_explore(self, _) -> None:
        """Handle starting auto-exploration.
        
        Initializes the auto-explore component on the player and starts exploring.
        Displays a pithy adventure quote and system message.
        """
        player = self.state_manager.state.player
        if not player:
            logger.error("No player found for auto-explore")
            return
        
        # Get or create auto-explore component
        auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
        if not auto_explore:
            from components.auto_explore import AutoExplore
            auto_explore = AutoExplore()
            auto_explore.owner = player
            player.auto_explore = auto_explore
            player.components.add(ComponentType.AUTO_EXPLORE, auto_explore)
        
        # Start exploring
        quote = auto_explore.start(
            self.state_manager.state.game_map,
            self.state_manager.state.entities,
            self.state_manager.state.fov_map
        )
        
        # Add messages
        self.state_manager.state.message_log.add_message(MB.info(quote))
        self.state_manager.state.message_log.add_message(
            MB.system("You begin exploring the dungeon")
        )
        
        logger.info("Auto-explore started")
    
    def _handle_exit(self, _) -> None:
        """Handle exit actions based on current game state.
        
        Closes menus and returns to appropriate previous state.
        """
        current_state = self.state_manager.state.current_state
        
        if current_state in (
            GameStates.SHOW_INVENTORY,
            GameStates.DROP_INVENTORY,
            GameStates.THROW_SELECT_ITEM,  # ← ADDED!
            GameStates.CHARACTER_SCREEN,
            GameStates.LEVEL_UP,
        ):
            # Close menu and return to gameplay
            self.state_manager.set_game_state(GameStates.PLAYERS_TURN)
            
            # Clear throw target if exiting throw menu
            if current_state == GameStates.THROW_SELECT_ITEM:
                self.state_manager.set_extra_data("throw_target", None)
        
        elif current_state in (GameStates.TARGETING, GameStates.THROW_TARGETING):  # ← ADDED THROW_TARGETING!
            # Exit targeting mode
            previous_state = self.state_manager.get_extra_data("previous_state", GameStates.PLAYERS_TURN)
            self.state_manager.set_game_state(previous_state)
            
            # Clear targeting data
            self.state_manager.set_extra_data("targeting_item", None)
            self.state_manager.set_extra_data("previous_state", None)
            
            # Clear throw-specific data if exiting throw targeting
            if current_state == GameStates.THROW_TARGETING:
                self.state_manager.set_extra_data("throw_item", None)
                self.state_manager.set_extra_data("throw_target", None)
    
    def _process_auto_explore_turn(self) -> None:
        """Process one turn of auto-exploration.
        
        Gets the next movement action from the auto-explore component and executes it.
        Handles stop conditions and messages. If auto-explore stops, a message is added
        to the log explaining why.
        """
        player = self.state_manager.state.player
        if not player:
            return
        
        auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
        if not auto_explore or not auto_explore.is_active():
            return
        
        # Get next action from auto-explore
        action = auto_explore.get_next_action(
            self.state_manager.state.game_map,
            self.state_manager.state.entities,
            self.state_manager.state.fov_map
        )
        
        if action is None:
            # Auto-explore stopped
            reason = auto_explore.stop_reason or "Unknown reason"
            self.state_manager.state.message_log.add_message(
                MB.system(f"Auto-explore stopped: {reason}")
            )
            return
        
        # Execute the movement
        dx = action.get('dx', 0)
        dy = action.get('dy', 0)
        
        if dx != 0 or dy != 0:
            # Use the normal movement handler
            self._handle_movement((dx, dy))
    
    def _process_pathfinding_movement_action(self, _value: Any) -> None:
        """Process pathfinding movement for auto-pickup and ranged weapon auto-attack.
        
        This method is called when right-clicking items or when pathfinding is active.
        It enables the player to continue moving along a path while checking
        for enemies to auto-attack when within weapon reach.
        
        Args:
            _value: Ignored (required for action handler signature)
        """
        from mouse_movement import process_pathfinding_movement
        
        player = self.state_manager.state.player
        if not player:
            return
        
        result = process_pathfinding_movement(
            player,
            self.state_manager.state.entities,
            self.state_manager.state.game_map,
            self.state_manager.state.fov_map,
            self.state_manager
        )
        
        # Process the results
        end_turn = False
        for r in result.get("results", []):
            # Handle FOV recompute
            if r.get("fov_recompute"):
                from fov_functions import recompute_fov
                from config.game_constants import GAME_CONSTANTS
                fov_radius = GAME_CONSTANTS.rendering.DEFAULT_FOV_RADIUS
                recompute_fov(
                    self.state_manager.state.fov_map,
                    player.x,
                    player.y,
                    fov_radius
                )
            
            # Handle messages
            message = r.get("message")
            if message:
                self.state_manager.state.message_log.add_message(message)
            
            # Handle death
            dead_entity = r.get("dead")
            if dead_entity:
                self._handle_entity_death(dead_entity)
            
            # Handle NPC dialogue trigger
            npc_dialogue = r.get("npc_dialogue")
            if npc_dialogue:
                self.state_manager.set_game_state(GameStates.NPC_DIALOGUE)
                self.state_manager.state.current_dialogue_npc = npc_dialogue
                return  # Don't consume turn for dialogue
            
            # Check if we should end the turn (continue pathfinding or interrupt after movement)
            if r.get("continue_pathfinding") or r.get("enemy_turn"):
                end_turn = True
        
        # Transition to enemy turn if player moved
        if end_turn:
            self.turn_controller.end_player_action(turn_consumed=True)
    
    def _handle_movement(self, move_data: Tuple[int, int]) -> None:
        """Handle player movement via MovementService (REFACTORED - single source of truth).
        
        Args:
            move_data: Tuple of (dx, dy) movement deltas
        """
        from game_states import GameStates
        from message_builder import MessageBuilder as MB
        
        current_state = self.state_manager.state.current_state
        
        # Use StateManager to check if movement is allowed in current state
        if not StateManager.allows_movement(current_state):
            return
        
        # Validate move input
        if not isinstance(move_data, (tuple, list)) or len(move_data) != 2:
            logger.warning(f"Invalid move data: {move_data}")
            return
        
        dx, dy = move_data
        player = self.state_manager.state.player
        
        if not player:
            logger.error("No player found for movement")
            return
        
        # Check for paralysis - completely prevents all actions BUT still consumes a turn
        if (hasattr(player, 'has_status_effect') and 
            callable(player.has_status_effect) and 
            player.has_status_effect('paralysis')):
            self.state_manager.state.message_log.add_message(
                MB.warning("You are paralyzed and cannot move!")
            )
            # IMPORTANT: Consume the turn so paralysis duration decrements
            self._process_player_status_effects()
            self.turn_controller.end_player_action(turn_consumed=True)
            return
        
        # Use MovementService for all movement logic (REFACTORED - single source of truth)
        from services.movement_service import get_movement_service
        movement_service = get_movement_service(self.state_manager)
        
        result = movement_service.execute_movement(dx, dy, source="keyboard")
        
        # Handle blocking entity (combat)
        if result.blocked_by_entity:
            self._handle_combat(player, result.blocked_by_entity)
            return
        
        # Handle blocked by wall (no action needed, just return)
        if result.blocked_by_wall:
            return

        # Handle blocked by status effect (immobilized, etc.)
        if result.blocked_by_status:
            # Display any messages
            message_log = self.state_manager.state.message_log
            for msg_dict in result.messages:
                # Handle both dict format and direct Message objects
                if isinstance(msg_dict, dict) and "message" in msg_dict:
                    message_log.add_message(msg_dict["message"])
                else:
                    message_log.add_message(msg_dict)
            return

        # Handle successful movement
        if result.success:
            # Display any messages
            message_log = self.state_manager.state.message_log
            for msg_dict in result.messages:
                # Handle both dict format and direct Message objects
                if isinstance(msg_dict, dict) and "message" in msg_dict:
                    message_log.add_message(msg_dict["message"])
                else:
                    message_log.add_message(msg_dict)
            
            # Request FOV recompute if needed
            if result.fov_recompute:
                self.state_manager.request_fov_recompute()
            
            # Handle portal entry (Phase 5)
            if result.portal_entry:
                # Transition to confrontation state
                self.state_manager.set_game_state(GameStates.CONFRONTATION)
                return  # Don't process turn end, go straight to confrontation
            
            # Process status effects at end of player turn
            self._process_player_status_effects()
            
            # Switch to enemy turn
            self.turn_controller.end_player_action(turn_consumed=True)
    
    def _check_secret_reveals(self, player, game_map) -> None:
        """Check for passive secret door reveals near the player.
        
        Args:
            player: The player entity
            game_map: The game map
        """
        # Check if the map has a secret door manager
        if not hasattr(game_map, 'secret_door_manager') or game_map.secret_door_manager is None:
            return
        
        # Check for reveals within 3 tiles
        reveal_results = game_map.secret_door_manager.check_reveals_near(player, max_distance=3)
        
        if not reveal_results:
            return
        
        message_log = self.state_manager.state.message_log
        if not message_log:
            return
        
        # Process reveals
        for result in reveal_results:
            if result.get('secret_revealed'):
                door = result.get('secret_door')
                distance = result.get('distance', 0)
                
                if door:
                    # Convert door tile to passable floor
                    if 0 <= door.x < game_map.width and 0 <= door.y < game_map.height:
                        game_map.tiles[door.x][door.y].blocked = False
                        game_map.tiles[door.x][door.y].block_sight = False
                    
                    # Create a visual marker entity for the revealed door
                    self._create_secret_door_marker(door.x, door.y)
                    
                    # Add reveal message
                    message = door.get_reveal_message(distance)
                    message_log.add_message(MB.success(message))
            
            elif result.get('secret_hint'):
                door = result.get('secret_door')
                
                if door:
                    # Give a hint message
                    hint = door.get_hint_message()
                    message_log.add_message(MB.info(hint))
    
    def _create_secret_door_marker(self, x: int, y: int) -> None:
        """Create a visual marker entity for a revealed secret door.
        
        The marker is a non-blocking entity that makes revealed doors visible
        and distinct from regular floors. Uses '+' symbol in cyan.
        
        Args:
            x: X coordinate of revealed door
            y: Y coordinate of revealed door
        """
        from entity import Entity
        from render_functions import RenderOrder
        
        entities = self.state_manager.state.entities
        if entities is None:
            return
        
        # Check if marker already exists at this location
        for entity in entities:
            if entity.x == x and entity.y == y and hasattr(entity, 'is_secret_door_marker'):
                return  # Marker already exists
        
        # Create the marker entity
        marker = Entity(
            x=x,
            y=y,
            char='+',  # Distinct character (door symbol)
            color=(0, 255, 255),  # Cyan - stands out clearly
            name='Secret Door',
            blocks=False
        )
        marker.render_order = RenderOrder.ITEM
        marker.is_secret_door_marker = True  # Tag for identification
        
        entities.append(marker)
        
        # Invalidate entity cache
        from entity_sorting_cache import invalidate_entity_cache
        invalidate_entity_cache("entity_added_secret_door")
    
    def _handle_combat(self, attacker, target) -> None:
        """Handle combat between attacker and target.
        
        Args:
            attacker: The attacking entity
            target: The target entity
        """
        attacker_fighter = attacker.get_component_optional(ComponentType.FIGHTER)
        target_fighter = target.get_component_optional(ComponentType.FIGHTER)
        if not (attacker_fighter and target_fighter):
            return
        
        # Break invisibility if the attacker is attacking
        if hasattr(attacker, 'invisible') and attacker.invisible:
            self._break_invisibility(attacker)
        
        # Use new d20-based attack system
        attack_results = attacker_fighter.attack_d20(target)
        
        for result in attack_results:
            message = result.get("message")
            if message:
                self.state_manager.state.message_log.add_message(message)
            
            dead_entity = result.get("dead")
            if dead_entity:
                # Combat deaths should transform to corpses (keep in entities list)
                self._handle_entity_death(dead_entity, remove_from_entities=False)

        # Player attacks should consume the turn (even if target survived)
        if attacker == self.state_manager.state.player:
            self._process_player_status_effects()
            self.turn_controller.end_player_action(turn_consumed=True)
    
    def _handle_entity_death(self, dead_entity, remove_from_entities=False) -> None:
        """Handle entity death.
        
        Args:
            dead_entity: The entity that died
            remove_from_entities: If True, remove from entities list; if False, transform to corpse
        """
        player = self.state_manager.state.player
        
        if dead_entity == player:
            # Player died - transition to death state
            self.state_manager.set_game_state(GameStates.PLAYER_DEAD)
            death_message = MB.death(
                "You died! Press any key to return to the main menu."
            )
            self.state_manager.state.message_log.add_message(death_message)
            
            # Add a frame counter to prevent immediate exit from death screen
            if not hasattr(self.state_manager.state, 'death_frame_counter'):
                self.state_manager.state.death_frame_counter = 0
            
            # Generate Entity death quote ONCE (don't regenerate every frame!)
            statistics = player.get_component_optional(ComponentType.STATISTICS)
            if statistics:
                from entity_dialogue import get_entity_quote_for_death
                self.state_manager.state.death_screen_quote = get_entity_quote_for_death(
                    statistics, 
                    statistics.deepest_level
                )
            else:
                self.state_manager.state.death_screen_quote = "How... disappointing."
        else:
            # Monster died - always transform to corpse first
            from death_functions import kill_monster
            game_map = self.state_manager.state.game_map
            entities = self.state_manager.state.entities
            death_message = kill_monster(dead_entity, game_map, entities)
            self.state_manager.state.message_log.add_message(death_message)
            
            # Record kill statistics (only for player kills)
            player = self.state_manager.state.player
            statistics = player.get_component_optional(ComponentType.STATISTICS) if player else None
            if statistics:
                # Track monster type killed
                monster_name = dead_entity.name.lower()
                statistics.record_kill(monster_name)
                
                # Entity comments on kills (Phase 1 feature!)
                message_log = self.state_manager.state.message_log
                total_kills = player.statistics.total_kills
                
                # First kill - Entity mocks basic combat
                if total_kills == 1:
                    entity_quote = EntityDialogue.get_first_kill_quote()
                    entity_message = MB.custom(entity_quote, (180, 180, 150))  # Muted gold
                    message_log.add_message(entity_message)
                
                # Kill milestones - Entity tracks your progress
                elif total_kills in [10, 25, 50, 100]:
                    entity_quote = EntityDialogue.get_milestone_kill_quote(total_kills)
                    entity_message = MB.custom(entity_quote, (180, 180, 150))  # Muted gold
                    message_log.add_message(entity_message)
            
            # Phase 5: Check if this was a boss for an ending fight
            pending_ending = self.state_manager.get_extra_data("pending_ending")
            if pending_ending and hasattr(dead_entity, 'is_boss') and dead_entity.is_boss:
                # Boss defeated! Trigger the ending screen
                logger.info(f"=== BOSS DEFEATED: Triggering ending {pending_ending} ===")
                print(f">>> BOSS DEFEATED: {dead_entity.name}, triggering ending '{pending_ending}'")

                # Store that we should show ending screen next frame
                self.state_manager.set_extra_data("show_ending", pending_ending)
                self.state_manager.set_extra_data("pending_ending", None)  # Clear pending

                # Transition to a victory state that will show the ending
                self.state_manager.set_game_state(GameStates.VICTORY)
            
            # Handle dropped loot
            if hasattr(dead_entity, '_dropped_loot') and dead_entity._dropped_loot:
                # Add dropped items to the entities list
                self.state_manager.state.entities.extend(dead_entity._dropped_loot)
                # Clean up the temporary attribute
                delattr(dead_entity, '_dropped_loot')
                # Invalidate entity sorting cache when new entities are added
                invalidate_entity_cache("entity_added_loot")
            
            # Handle spawned entities (e.g., slime splitting)
            if hasattr(dead_entity, '_spawned_entities') and dead_entity._spawned_entities:
                # Add spawned entities to the entities list
                self.state_manager.state.entities.extend(dead_entity._spawned_entities)
                # Clean up the temporary attribute
                delattr(dead_entity, '_spawned_entities')
                # Invalidate entity sorting cache when new entities are added
                invalidate_entity_cache("entity_added_spawned")
            
            # Then handle removal if requested (for combat deaths)
            if remove_from_entities:
                if dead_entity in self.state_manager.state.entities:
                    self.state_manager.state.entities.remove(dead_entity)
                    # Invalidate entity sorting cache when entities are removed
                    invalidate_entity_cache("entity_removed_combat")
            
            self.state_manager.request_fov_recompute()
    
    def _handle_wait(self, _) -> None:
        """Handle wait action (player skips turn)."""
        current_state = self.state_manager.state.current_state
        if current_state == GameStates.PLAYERS_TURN:
            # Process status effects at end of player turn
            self._process_player_status_effects()
            self.turn_controller.end_player_action(turn_consumed=True)
    
    def _handle_pickup(self, _) -> None:
        """Handle interaction - talk to NPCs or pick up items. 
        
        Priority:
        1. NPCs at player position - start dialogue (NO TURN)
        2. Items at player position - pick up via PickupService (TAKES 1 TURN)
        """
        current_state = self.state_manager.state.current_state
        
        # Use StateManager to check if pickup is allowed in current state
        if not StateManager.allows_pickup(current_state):
            return
        
        player = self.state_manager.state.player
        entities = self.state_manager.state.entities
        message_log = self.state_manager.state.message_log
        game_map = self.state_manager.state.game_map
        
        if not all([player, entities is not None, message_log]):
            return
        
        # FIRST: Check for NPCs at player position
        for entity in entities:
            if (entity.x == player.x and entity.y == player.y and
                hasattr(entity, 'is_npc') and entity.is_npc and
                hasattr(entity, 'npc_dialogue') and entity.npc_dialogue):
                
                # Found an NPC! Start dialogue
                dungeon_level = game_map.dungeon_level if game_map else 1
                
                if not entity.npc_dialogue.start_encounter(dungeon_level):
                    message_log.add_message(MB.info(f"{entity.name} has nothing to say right now."))
                    return  # Don't consume turn
                
                message_log.add_message(MB.info(f"You approach {entity.name}..."))
                
                # Transition to dialogue state
                self.state_manager.set_game_state(GameStates.NPC_DIALOGUE)
                
                # Store the NPC we're talking to
                self.state_manager.state.current_dialogue_npc = entity
                
                logger.info(f"Started conversation with {entity.name} at dungeon level {dungeon_level}")
                return  # Don't consume turn for dialogue
        
        # SECOND: Use PickupService for item pickup (REFACTORED - single source of truth)
        from services.pickup_service import get_pickup_service
        pickup_service = get_pickup_service(self.state_manager)
        
        result = pickup_service.execute_pickup(source="keyboard")
        
        # Display messages
        for msg_dict in result.messages:
            message_log.add_message(msg_dict["message"])
        
        # If pickup successful, consume turn
        if result.success:
            # TURN ECONOMY: Picking up an item takes 1 turn
            self._process_player_status_effects()
            self.turn_controller.end_player_action(turn_consumed=True)
            
            # If victory was triggered, state transition already handled by PickupService
            # No need to call end_player_action again
            # No item to pick up = no turn consumed
    
    def _handle_search(self, _) -> None:
        """Handle room-wide search action. TAKES 1 TURN.
        
        Searches the current room for secret doors, revealing any that are hidden.
        """
        current_state = self.state_manager.state.current_state
        if current_state != GameStates.PLAYERS_TURN:
            return
        
        player = self.state_manager.state.player
        game_map = self.state_manager.state.game_map
        message_log = self.state_manager.state.message_log
        
        if not all([player, game_map, message_log]):
            return
        
        # Check if the map has a secret door manager
        if not hasattr(game_map, 'secret_door_manager') or game_map.secret_door_manager is None:
            message_log.add_message(MB.info("You search carefully but find nothing."))
            # Still consumes a turn
            self._process_player_status_effects()
            self.turn_controller.end_player_action(turn_consumed=True)
            return
        
        # Find the room the player is in
        # For now, search a reasonable radius around the player (10 tiles)
        search_radius = 10
        search_bounds = (
            player.x - search_radius,
            player.y - search_radius,
            player.x + search_radius,
            player.y + search_radius
        )
        
        # Reveal all secret doors in the search area
        revealed_doors = game_map.secret_door_manager.search_room(search_bounds)
        
        if revealed_doors:
            # Convert revealed doors to passable floor tiles and add visual markers
            for door in revealed_doors:
                if 0 <= door.x < game_map.width and 0 <= door.y < game_map.height:
                    game_map.tiles[door.x][door.y].blocked = False
                    game_map.tiles[door.x][door.y].block_sight = False
                    
                # Create visual marker for revealed door
                self._create_secret_door_marker(door.x, door.y)
            
            # Add discovery messages
            if len(revealed_doors) == 1:
                message_log.add_message(MB.success("You discover a secret door!"))
            else:
                message_log.add_message(MB.success(f"You discover {len(revealed_doors)} secret doors!"))
        else:
            message_log.add_message(MB.info("You search carefully but find nothing hidden here."))
        
        # TURN ECONOMY: Searching takes 1 turn
        self._process_player_status_effects()
        self.turn_controller.end_player_action(turn_consumed=True)
    
    def _handle_inventory_action(self, inventory_index: int) -> None:
        """Handle inventory item usage or dropping.
        
        Args:
            inventory_index: Index of item in inventory
        """
        import logging
        logger = logging.getLogger(__name__)
        
        current_state = self.state_manager.state.current_state
        player = self.state_manager.state.player
        
        logger.warning(f"_handle_inventory_action called: index={inventory_index}, state={current_state}")
        
        if not player or not player.get_component_optional(ComponentType.INVENTORY):
            logger.warning(f"No player or inventory!")
            return
        
        # Defensive check: ensure inventory_index is an integer
        if inventory_index is None or not isinstance(inventory_index, int):
            logger.warning(f"Invalid inventory_index: {inventory_index} (type: {type(inventory_index)})")
            message = MB.failure(
                "Error: Invalid inventory selection. Please try again."
            )
            self.state_manager.state.message_log.add_message(message)
            return
        
        # Defensive check: ensure inventory items list is valid
        if not hasattr(player.inventory, 'items') or player.inventory.items is None:
            logger.error(f"Player inventory.items is invalid: {player.inventory.items}")
            message = MB.failure(
                "Error: Inventory is corrupted. Please report this bug."
            )
            self.state_manager.state.message_log.add_message(message)
            return
        
        # Get inventory size safely
        try:
            inventory_size = len(player.inventory.items)
        except (TypeError, AttributeError) as e:
            logger.error(f"Cannot get inventory size: {e}, items type: {type(player.inventory.items)}")
            message = MB.failure(
                "Error: Inventory is corrupted. Please report this bug."
            )
            self.state_manager.state.message_log.add_message(message)
            return
        
        # Extra safety check: ensure inventory_size is a valid integer
        if inventory_size is None or not isinstance(inventory_size, int):
            logger.error(f"Inventory size is not an integer! type={type(inventory_size)}, value={inventory_size}")
            message = MB.failure(
                "Error: Inventory is corrupted (invalid size). Please report this bug."
            )
            self.state_manager.state.message_log.add_message(message)
            return
        
        # Check if index is in valid range
        if inventory_index < 0 or inventory_index >= inventory_size:
            logger.warning(f"Inventory index {inventory_index} out of range (inventory size: {inventory_size})")
            message = MB.warning(
                f"Inventory slot '{chr(ord('a') + inventory_index)}' is empty."
            )
            self.state_manager.state.message_log.add_message(message)
            return
        
        # IMPORTANT: Inventory menu sorts items alphabetically!
        # We must use the same sorted order here or indices won't match
        sorted_items = sorted(player.inventory.items, key=lambda item: item.get_display_name().lower())
        item = sorted_items[inventory_index]
        
        logger.warning(f"Current state: {current_state}, item: {item.name if item else None}")
        
        if current_state == GameStates.SHOW_INVENTORY:
            self._use_inventory_item(item)
        elif current_state == GameStates.DROP_INVENTORY:
            self._drop_inventory_item(item)
        elif current_state == GameStates.TARGETING:
            # Switching targeted item while in targeting mode
            # Update the targeting_item to the newly selected item
            self.state_manager.set_extra_data("targeting_item", item)
            logger.warning(f"Switched targeting to: {item.name}")
        elif current_state == GameStates.THROW_SELECT_ITEM:
            # Selected item to throw - check if we have a pre-selected target from right-click
            throw_target = self.state_manager.get_extra_data("throw_target")
            self.state_manager.state.targeting_item = item
            
            if throw_target:
                # Auto-throw at the pre-selected target (from right-click on enemy)
                target_x, target_y = throw_target
                
                # Remove item from inventory (it's being thrown)
                player.require_component(ComponentType.INVENTORY).remove_item(item)
                
                # Execute throw
                from throwing import throw_item
                throw_results = throw_item(
                    thrower=player,
                    item=item,
                    target_x=target_x,
                    target_y=target_y,
                    entities=self.state_manager.state.entities,
                    game_map=self.state_manager.state.game_map,
                    fov_map=self.state_manager.state.fov_map
                )
                
                player_died = False
                for result in throw_results:
                    message = result.get("message")
                    if message:
                        self.state_manager.state.message_log.add_message(message)
                    
                    dead_entity = result.get("dead")
                    if dead_entity:
                        self._handle_entity_death(dead_entity, remove_from_entities=False)
                        if dead_entity == player:
                            player_died = True
                
                # Clear targeting state
                self.state_manager.state.targeting_item = None
                self.state_manager.set_extra_data("throw_target", None)
                
                # TURN ECONOMY: Throwing takes 1 turn
                if not player_died:
                    self._process_player_status_effects()
                    self.turn_controller.end_player_action(turn_consumed=True)
            else:
                # No pre-selected target - enter throw targeting mode
                self.state_manager.set_game_state(GameStates.THROW_TARGETING)
        elif current_state == GameStates.PLAYERS_TURN:
            # Sidebar click during normal gameplay - use the item!
            logger.warning(f"Using item from sidebar during PLAYERS_TURN")
            self._use_inventory_item(item)
    
    def _use_inventory_item(self, item) -> None:
        """Use an item from inventory. TAKES 1 TURN (unless entering targeting mode).

        Args:
            item: The item entity to use
        """
        player = self.state_manager.state.player
        message_log = self.state_manager.state.message_log

        # Check if this is equipment (weapon, armor, ring) - EQUIP instead of USE
        from components.component_registry import ComponentType
        if item.components.has(ComponentType.EQUIPPABLE):
            # This is equipment - toggle equip/unequip
            if player.equipment:
                equip_results = player.equipment.toggle_equip(item)
                for result in equip_results:
                    message = result.get("message")
                    if message:
                        message_log.add_message(message)

                # TURN ECONOMY: Equipping/unequipping takes 1 turn
                self._process_player_status_effects()
                self.turn_controller.end_player_action(turn_consumed=True)
            return

        # Not equipment - treat as consumable
        if not item.item:
            return

        # Check if this is a Wand of Portals - special handling for portal targeting
        # Use more robust check: verify it's actually a PortalPlacer instance, not just a mock
        from components.portal_placer import PortalPlacer
        portal_placer = getattr(item, 'portal_placer', None)
        
        if isinstance(portal_placer, PortalPlacer) and hasattr(item, 'item'):
            # Portal wand - call its use function directly with wand_entity kwarg
            # The use function will handle portal-specific targeting
            item_use_results = player.inventory.use(
                item,
                entities=self.state_manager.state.entities,
                fov_map=self.state_manager.state.fov_map,
                game_map=self.state_manager.state.game_map,
                wand_entity=item  # Pass the wand itself
            )
            
            for result in item_use_results:
                message = result.get("message")
                if message:
                    message_log.add_message(message)
                
                # Check if portal wand requested targeting mode
                if result.get("targeting_mode"):
                    # Store the wand in extra data for portal targeting
                    self.state_manager.set_extra_data("portal_wand", item)
                    self.state_manager.set_game_state(GameStates.TARGETING)
                    message_log.add_message(MB.success("Portal targeting active. Click to place entrance portal."))
            
            return  # Portal wand usage handled

        # Check if item requires targeting - if so, enter targeting mode
        if item.item.targeting:
            # Enter targeting mode for this item
            self.state_manager.set_extra_data("targeting_item", item)
            self.state_manager.set_game_state(GameStates.TARGETING)

            # Show targeting message
            item_name = item.item.get_display_name() if hasattr(item, 'item') and hasattr(item.item, 'get_display_name') else item.name
            message_log.add_message(MB.info(f"Select a target for {item_name}. (Right-click or ESC to cancel)"))

            return  # Don't consume turn yet - wait for targeting

        # Use item directly (no targeting required)
        item_use_results = player.inventory.use(
            item,
            entities=self.state_manager.state.entities,
            fov_map=self.state_manager.state.fov_map,
            game_map=self.state_manager.state.game_map  # CRITICAL: Pass game_map for spells like magic mapping
        )
        
        player_died = False
        entered_targeting = False
        item_consumed = False
        
        for result in item_use_results:
            message = result.get("message")
            if message:
                self.state_manager.state.message_log.add_message(message)
            
            # Handle death results
            dead_entity = result.get("dead")
            if dead_entity:
                # Item/spell deaths should transform to corpse (not remove)
                self._handle_entity_death(dead_entity, remove_from_entities=False)
                # Check if player died
                if dead_entity == player:
                    player_died = True
            
            # Handle targeting
            targeting = result.get("targeting")
            if targeting:
                entered_targeting = True
                self.state_manager.set_game_state(GameStates.TARGETING)
                self.state_manager.set_extra_data("targeting_item", item)
                self.state_manager.set_extra_data("previous_state", GameStates.SHOW_INVENTORY)
                return  # Don't end turn yet - wait for target selection
            
            # Check if item was consumed
            if result.get("consumed"):
                item_consumed = True
            
            # Handle equipment
            equip = result.get("equip")
            if equip and player.equipment:
                self._handle_equipment(equip)
                # TURN ECONOMY: Equipping takes 1 turn
                item_consumed = True
        
        # TURN ECONOMY: Using an item takes 1 turn if not entering targeting mode
        if not entered_targeting and not player_died:
            if item_consumed:
                # Item was used/consumed - end turn
                self._process_player_status_effects()
                self.turn_controller.end_player_action(turn_consumed=True)
            else:
                # Just return to player turn (e.g., examining item)
                self.state_manager.set_game_state(GameStates.PLAYERS_TURN)
    
    def _drop_inventory_item(self, item) -> None:
        """Drop an item from inventory. TAKES 1 TURN.
        
        Args:
            item: The item entity to drop
        """
        player = self.state_manager.state.player
        drop_results = player.inventory.drop_item(item)
        
        item_dropped = False
        for result in drop_results:
            message = result.get("message")
            if message:
                self.state_manager.state.message_log.add_message(message)
            
            item_dropped_entity = result.get("item_dropped")
            if item_dropped_entity:
                item_dropped = True
                item_dropped_entity.x = player.x
                item_dropped_entity.y = player.y
                self.state_manager.state.entities.append(item_dropped_entity)
        
        # TURN ECONOMY: Dropping an item takes 1 turn
        if item_dropped:
            self._process_player_status_effects()
            self.turn_controller.end_player_action(turn_consumed=True)
        else:
            # Failed to drop (shouldn't happen, but be safe)
            self.state_manager.set_game_state(GameStates.PLAYERS_TURN)
    
    def _handle_equipment(self, equip_item) -> None:
        """Handle equipment equipping/unequipping.
        
        Args:
            equip_item: The item to equip/unequip
        """
        player = self.state_manager.state.player
        if not player.equipment:
            return
        
        equip_results = player.equipment.toggle_equip(equip_item)
        
        for equip_result in equip_results:
            equipped = equip_result.get("equipped")
            dequipped = equip_result.get("dequipped")
            
            if equipped:
                message = MB.item_equipped(f"You equip the {equipped.name}.")
                self.state_manager.state.message_log.add_message(message)
            elif dequipped:
                message = MB.item_unequipped(f"You unequip the {dequipped.name}.")
                self.state_manager.state.message_log.add_message(message)
    
    def _handle_stairs(self, _) -> None:
        """Handle taking stairs to next level."""
        logger.debug("=== _handle_stairs() called ===")
        
        current_state = self.state_manager.state.current_state
        if current_state != GameStates.PLAYERS_TURN:
            logger.debug(f"_handle_stairs: Wrong state ({current_state}), returning")
            return
        
        player = self.state_manager.state.player
        entities = self.state_manager.state.entities
        game_map = self.state_manager.state.game_map
        message_log = self.state_manager.state.message_log
        
        if not all([player, entities is not None, game_map, message_log]):
            logger.warning("_handle_stairs: Missing required components!")
            return
        
        logger.info(f"_handle_stairs: Player at ({player.x}, {player.y}), checking for stairs")
        
        # Check if player is on stairs
        stairs_found = False
        for entity in entities:
            if (entity.components.has(ComponentType.STAIRS) and 
                entity.x == player.x and entity.y == player.y):
                stairs_found = True
                logger.info(f"=== TAKING STAIRS: Level {game_map.dungeon_level} → {game_map.dungeon_level + 1} ===")
                
                # Generate next floor
                new_entities = game_map.next_floor(player, message_log, self.constants)
                self.state_manager.update_state(entities=new_entities)
                logger.info(f"Floor generated: {len(new_entities)} entities")
                
                # Initialize new FOV map for the new level
                from fov_functions import initialize_fov
                new_fov_map = initialize_fov(game_map)
                logger.info(f"FOV map initialized: {new_fov_map is not None}")
                
                self.state_manager.update_state(fov_map=new_fov_map)
                self.state_manager.request_fov_recompute()
                logger.info("FOV recompute requested")
                
                # Center camera on player's new position (fixes black screen on level transition)
                camera = self.state_manager.state.camera
                if camera:
                    # CRITICAL: Update camera's map dimensions for the new level
                    # Without this, camera clamping uses old map size and positions incorrectly
                    old_dims = (camera.map_width, camera.map_height)
                    camera.map_width = game_map.width
                    camera.map_height = game_map.height
                    logger.info(f"Camera map dimensions updated: {old_dims} → ({camera.map_width}, {camera.map_height})")
                    
                    # Now center on player
                    camera.update(player.x, player.y)
                    logger.info(f"Camera centered on player at ({player.x}, {player.y}), camera at ({camera.x}, {camera.y})")
                else:
                    logger.warning("Camera not found! This may cause rendering issues.")
                
                # Entity comments on level transition (Phase 1 feature!)
                entity_quote = EntityDialogue.get_level_transition_quote(game_map.dungeon_level)
                entity_message = MB.custom(entity_quote, (180, 180, 150))  # Muted gold for Entity
                message_log.add_message(entity_message)
                
                # Trigger ring effects for new level (e.g., Ring of Invisibility)
                if player.equipment:
                    rings = [player.equipment.left_ring, player.equipment.right_ring]
                    for ring_entity in rings:
                        if ring_entity and hasattr(ring_entity, 'ring') and ring_entity.ring:
                            ring_results = ring_entity.ring.on_new_level(player)
                            for result in ring_results:
                                ring_message = result.get('message')
                                if ring_message:
                                    message_log.add_message(ring_message)
                
                logger.info("=== STAIRS TRANSITION COMPLETE ===")
                break
        else:
            logger.warning(f"No stairs found at player position ({player.x}, {player.y})")
            message = MB.warning("There are no stairs here.")
            message_log.add_message(message)
    
    def _handle_level_up(self, level_up_choice: str) -> None:
        """Handle level up stat selection.
        
        Args:
            level_up_choice: The stat to increase ('hp', 'str', 'def')
        """
        current_state = self.state_manager.state.current_state
        if current_state != GameStates.LEVEL_UP:
            return
        
        player = self.state_manager.state.player
        message_log = self.state_manager.state.message_log
        
        if not player or not message_log:
            return
        
        player_fighter = player.get_component_optional(ComponentType.FIGHTER)
        if not player_fighter:
            return
        
        # Apply level up bonuses based on choice
        if level_up_choice == "hp":
            player_fighter.base_max_hp += 20
            player_fighter.hp += 20
            message = MB.level_up("Your health increases!")
        elif level_up_choice == "str":
            player_fighter.base_power += 1
            message = MB.level_up("You feel stronger!")
        elif level_up_choice == "def":
            player_fighter.base_defense += 1
            message = MB.level_up("Your movements are getting swifter!")
        else:
            # Invalid choice, don't apply any bonuses
            message = MB.warning("Invalid level up choice.")
            message_log.add_message(message)
            return
        
        message_log.add_message(message)
        
        # Return to player turn
        self.state_manager.set_game_state(GameStates.PLAYERS_TURN)
    
    def _handle_left_click(self, click_pos: Tuple[int, int]) -> None:
        """Handle left mouse click.

        Args:
            click_pos: Tuple of (x, y) click coordinates (world coords for targeting, screen coords for menus)
        """
        current_state = self.state_manager.state.current_state

        # Handle clicks on inventory/drop/throw menus
        if current_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY, GameStates.THROW_SELECT_ITEM):
            player = self.state_manager.state.player
            if not player or not player.components.has(ComponentType.INVENTORY):
                return
            
            # Get menu parameters (same as render_functions.py)
            from menus import get_menu_click_index
            from config.ui_layout import get_ui_layout
            ui_layout = get_ui_layout()
            
            # Build options list (same as inventory_menu in menus.py)
            if len(player.inventory.items) == 0:
                options = ["Inventory is empty."]
            else:
                options = []
                # IMPORTANT: Sort inventory alphabetically to match menu display!
                sorted_items = sorted(player.inventory.items, key=lambda item: item.get_display_name().lower())
                for item in sorted_items:
                    display_name = item.get_display_name()
                    
                    # Check if item is equipped
                    if player.equipment.main_hand == item:
                        options.append("{0} (equipped)".format(display_name))
                    elif player.equipment.off_hand == item:
                        options.append("{0} (equipped)".format(display_name))
                    elif player.equipment.head == item:
                        options.append("{0} (equipped)".format(display_name))
                    elif player.equipment.chest == item:
                        options.append("{0} (equipped)".format(display_name))
                    elif player.equipment.feet == item:
                        options.append("{0} (equipped)".format(display_name))
                    else:
                        options.append(display_name)
            
            # Determine header based on state
            if current_state == GameStates.SHOW_INVENTORY:
                header = "Press the key next to an item to use it, or Esc to cancel.\n"
            elif current_state == GameStates.THROW_SELECT_ITEM:
                header = "Select an item to throw, or Esc to cancel.\n"
            else:  # DROP_INVENTORY
                header = "Press the key next to an item to drop it, or Esc to cancel.\n"
            
            # Check if click is on a menu item (click_pos is screen coordinates)
            mouse_x, mouse_y = click_pos
            clicked_index = get_menu_click_index(
                mouse_x, mouse_y, header, options, 50, 
                ui_layout.screen_width, ui_layout.screen_height
            )
            
            if clicked_index is not None and clicked_index < len(player.inventory.items):
                # User clicked on an inventory item!
                # All menu states use the same handler which properly sorts items
                self._handle_inventory_action(clicked_index)
            return
        
        elif current_state == GameStates.THROW_TARGETING:
            # Handle throw targeting click
            target_x, target_y = click_pos
            targeting_item = self.state_manager.state.targeting_item
            
            if targeting_item:
                player = self.state_manager.state.player
                if player and player.inventory:
                    # Remove item from inventory
                    player.require_component(ComponentType.INVENTORY).remove_item(targeting_item)
                    
                    # Execute throw
                    from throwing import throw_item
                    throw_results = throw_item(
                        thrower=player,
                        item=targeting_item,
                        target_x=target_x,
                        target_y=target_y,
                        entities=self.state_manager.state.entities,
                        game_map=self.state_manager.state.game_map,
                        fov_map=self.state_manager.state.fov_map
                    )
                    
                    # Process results
                    player_died = False
                    for result in throw_results:
                        message = result.get("message")
                        if message:
                            self.state_manager.state.message_log.add_message(message)
                        
                        dead_entity = result.get("dead")
                        if dead_entity:
                            self._handle_entity_death(dead_entity, remove_from_entities=False)
                            if dead_entity == player:
                                player_died = True
                    
                    # Clear targeting state
                    self.state_manager.state.targeting_item = None
                    
                    # TURN ECONOMY: Throwing takes 1 turn
                    if not player_died:
                        self._process_player_status_effects()
                        self.turn_controller.end_player_action(turn_consumed=True)
                    return
        
        if current_state == GameStates.TARGETING:
            print(f"DEBUG: TARGETING mode click at {click_pos}")
            logger.warning(f"TARGETING mode click at {click_pos}")
            target_x, target_y = click_pos
            targeting_item = self.state_manager.get_extra_data("targeting_item")
            print(f"DEBUG: targeting_item = {targeting_item.name if targeting_item else None}")

            if targeting_item and targeting_item.item:
                player = self.state_manager.state.player
                if player and player.inventory:
                    print(f"DEBUG: Using {targeting_item.name} at ({target_x}, {target_y})")
                    item_use_results = player.require_component(ComponentType.INVENTORY).use(
                        targeting_item,
                        entities=self.state_manager.state.entities,
                        fov_map=self.state_manager.state.fov_map,
                        game_map=self.state_manager.state.game_map,
                        target_x=target_x,
                        target_y=target_y
                    )
                    print(f"DEBUG: Item use results: {len(item_use_results) if item_use_results else 0} results")

                    player_died = False
                    for result in item_use_results:
                        message = result.get("message")
                        if message:
                            self.state_manager.state.message_log.add_message(message)

                        dead_entity = result.get("dead")
                        if dead_entity:
                            # Targeting/spell deaths should transform to corpse (not remove)
                            self._handle_entity_death(dead_entity, remove_from_entities=False)
                            if dead_entity == player:
                                player_died = True

                    # Clear targeting state
                    self.state_manager.set_extra_data("targeting_item", None)
                    self.state_manager.set_extra_data("previous_state", None)

                    # TURN ECONOMY: Completing targeting (using targeted item) takes 1 turn
                    if not player_died:
                        self._process_player_status_effects()
                        self.turn_controller.end_player_action(turn_consumed=True)
                else:
                    print("DEBUG: No player or inventory")
            else:
                print("DEBUG: No targeting item or item has no item component")
        
        elif current_state == GameStates.THROW_TARGETING:
            # Handle throw targeting completion
            target_x, target_y = click_pos
            targeting_item = self.state_manager.state.targeting_item
            
            if targeting_item:
                player = self.state_manager.state.player
                if player and player.inventory:
                    # Remove item from inventory (it's being thrown)
                    player.require_component(ComponentType.INVENTORY).remove_item(targeting_item)
                    
                    # Execute throw (Phase 3 will implement throwing.py)
                    from throwing import throw_item
                    throw_results = throw_item(
                        thrower=player,
                        item=targeting_item,
                        target_x=target_x,
                        target_y=target_y,
                        entities=self.state_manager.state.entities,
                        game_map=self.state_manager.state.game_map,
                        fov_map=self.state_manager.state.fov_map
                    )
                    
                    player_died = False
                    for result in throw_results:
                        message = result.get("message")
                        if message:
                            self.state_manager.state.message_log.add_message(message)
                        
                        dead_entity = result.get("dead")
                        if dead_entity:
                            self._handle_entity_death(dead_entity, remove_from_entities=False)
                            if dead_entity == player:
                                player_died = True
                    
                    # Clear targeting state
                    self.state_manager.state.targeting_item = None
                    
                    # TURN ECONOMY: Throwing takes 1 turn
                    if not player_died:
                        self._process_player_status_effects()
                        self.turn_controller.end_player_action(turn_consumed=True)
        
        elif current_state == GameStates.PLAYERS_TURN:
            # Handle mouse movement/combat during player turn
            self._handle_mouse_movement(click_pos)
    
    def _handle_sidebar_click(self, click_pos: Tuple[int, int]) -> None:
        """Handle mouse click in sidebar (hotkeys and inventory items).
        
        Args:
            click_pos: Tuple of (screen_x, screen_y) click coordinates
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"_handle_sidebar_click called with {click_pos}")
        
        from ui.sidebar_interaction import handle_sidebar_click
        from config.ui_layout import get_ui_layout
        
        screen_x, screen_y = click_pos
        player = self.state_manager.state.player
        game_map = self.state_manager.state.game_map
        entities = self.state_manager.state.entities
        ui_layout = get_ui_layout()
        
        logger.warning(f"About to call handle_sidebar_click with player={player}, ui_layout={ui_layout}")
        
        # Check if click is on a hotkey or inventory item
        action = handle_sidebar_click(screen_x, screen_y, player, ui_layout, game_map, entities)
        
        logger.warning(f"handle_sidebar_click returned: {action}")
        
        if action:
            # Process the action returned from sidebar
            if 'inventory_index' in action:
                # User clicked on an inventory item - use it!
                logger.warning(f"SIDEBAR INVENTORY ITEM CLICKED: index {action['inventory_index']}")
                self._handle_inventory_action(action['inventory_index'])
            elif 'equipment_slot' in action:
                # User left-clicked on equipment - unequip it!
                logger.warning(f"SIDEBAR EQUIPMENT CLICKED: slot {action['equipment_slot']}")
                equipment_item = action.get('equipment_item')
                if equipment_item and player.equipment:
                    # Unequip the item (toggle_equip on already equipped item = unequip)
                    message_log = self.state_manager.state.message_log
                    equip_results = player.equipment.toggle_equip(equipment_item)
                    
                    for result in equip_results:
                        message = result.get("message")
                        if message:
                            message_log.add_message(message)
                    
                    # Unequipping takes a turn
                    self._process_player_status_effects()
                    self.turn_controller.end_player_action(turn_consumed=True)
            else:
                # User clicked on a hotkey button - process it!
                logger.warning(f"SIDEBAR HOTKEY CLICKED: {action}")
                # Add action to the normal action processing queue
                for action_type, value in action.items():
                    if action_type in self.action_handlers:
                        self.action_handlers[action_type](value)
                    else:
                        logger.warning(f"Unknown action type from sidebar: {action_type}")
        else:
            logger.warning(f"No valid action returned from sidebar click")
    
    def _handle_sidebar_right_click(self, click_pos: Tuple[int, int]) -> None:
        """Handle right-click in sidebar (drop inventory items).
        
        Args:
            click_pos: Tuple of (screen_x, screen_y) click coordinates
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"_handle_sidebar_right_click called with {click_pos}")
        
        from ui.sidebar_interaction import handle_sidebar_click
        from config.ui_layout import get_ui_layout
        
        screen_x, screen_y = click_pos
        player = self.state_manager.state.player
        game_map = self.state_manager.state.game_map
        entities = self.state_manager.state.entities
        message_log = self.state_manager.state.message_log
        ui_layout = get_ui_layout()
        
        if not all([player, message_log]):
            return
        
        # Check if click is on an inventory item (reuse the same detection logic)
        action = handle_sidebar_click(screen_x, screen_y, player, ui_layout, game_map, entities)
        
        logger.warning(f"handle_sidebar_click returned: {action}")
        
        if action and 'inventory_index' in action:
            # User right-clicked on an inventory item - drop it!
            inventory_index = action['inventory_index']
            logger.warning(f"SIDEBAR INVENTORY ITEM RIGHT-CLICKED: dropping index {inventory_index}")
            
            # Safety checks (same as _handle_inventory_action)
            if not player.get_component_optional(ComponentType.INVENTORY) or not hasattr(player.inventory, 'items'):
                return
            
            # CRITICAL: Must use FULL sorted inventory, same as _handle_inventory_action!
            # The sidebar_click handler returns an index into the FULL sorted inventory,
            # NOT just the unequipped items (even though sidebar only displays unequipped).
            sorted_items = sorted(player.inventory.items, key=lambda item: item.get_display_name().lower())
            
            if inventory_index < 0 or inventory_index >= len(sorted_items):
                message_log.add_message(
                    MB.warning(f"Invalid item selection.")
                )
                return
            
            # Get the correct item from the sorted list
            item = sorted_items[inventory_index]
            
            # Drop the item!
            self._drop_inventory_item(item)
        elif action and 'equipment_slot' in action:
            # User right-clicked on equipment - unequip it!
            equipment_slot = action['equipment_slot']
            equipment_item = action['equipment_item']
            logger.warning(f"SIDEBAR EQUIPMENT RIGHT-CLICKED: unequipping {equipment_slot}")
            
            # Unequip the item (toggle_equip will move it to inventory)
            if player.equipment:
                results = player.equipment.toggle_equip(equipment_item)
                for result in results:
                    message = result.get("message")
                    if message:
                        message_log.add_message(message)
                    
                    unequipped = result.get("unequipped")
                    if unequipped:
                        logger.warning(f"Successfully unequipped {unequipped.name}")
        else:
            logger.warning(f"Right-click on sidebar but not on an inventory item or equipment")
    
    def _handle_mouse_movement(self, click_pos: Tuple[int, int]) -> None:
        """Handle mouse click for movement or combat.
        
        Args:
            click_pos: Tuple of (x, y) click coordinates (world space)
        """
        from mouse_movement import handle_mouse_click
        
        player = self.state_manager.state.player
        entities = self.state_manager.state.entities
        game_map = self.state_manager.state.game_map
        message_log = self.state_manager.state.message_log
        fov_map = self.state_manager.state.fov_map
        
        if not all([player, entities is not None, game_map, message_log]):
            return
        
        click_x, click_y = click_pos
        
        # Handle the mouse click (with FOV map for smart pathfinding limits)
        click_result = handle_mouse_click(click_x, click_y, player, entities, game_map, fov_map)
        
        # Process results
        for result in click_result.get("results", []):
            message = result.get("message")
            if message:
                message_log.add_message(message)
            
            # Handle combat results
            dead_entity = result.get("dead")
            if dead_entity:
                self._handle_entity_death(dead_entity, remove_from_entities=False)
            
            # Handle pathfinding start
            if result.get("start_pathfinding"):
                # Switch to enemy turn to begin pathfinding movement
                self.turn_controller.end_player_action(turn_consumed=True)
            
            # Handle pathfinding to enemy
            if result.get("pathfind_to_enemy"):
                target_x, target_y = result["pathfind_to_enemy"]
                if player.pathfinding.set_destination(target_x, target_y, game_map, entities):
                    # Successfully set path to enemy
                    self.turn_controller.end_player_action(turn_consumed=True)
                else:
                    # Could not find path to enemy
                    message_log.add_message(MB.warning("Cannot reach that enemy."))
            
            # Handle immediate enemy turn (for attacks)
            if result.get("enemy_turn"):
                self.turn_controller.end_player_action(turn_consumed=True)
    
    def process_pathfinding_turn(self) -> None:
        """Process one step of pathfinding movement during player turn.
        
        This should be called when the player is following a pathfinding route.
        """
        from mouse_movement import process_pathfinding_movement
        
        player = self.state_manager.state.player
        entities = self.state_manager.state.entities
        game_map = self.state_manager.state.game_map
        message_log = self.state_manager.state.message_log
        fov_map = self.state_manager.state.fov_map
        
        if not all([player, entities is not None, game_map, message_log, fov_map]):
            return
        
        # Check if player has pathfinding and is moving
        pathfinding = player.get_component_optional(ComponentType.PATHFINDING)
        if not (pathfinding and pathfinding.is_path_active()):
            return
        
        # Process pathfinding movement
        movement_result = process_pathfinding_movement(player, entities, game_map, fov_map, self.state_manager)
        
        # Update camera to follow player (Phase 2)
        camera = self.state_manager.state.camera
        if camera:
            camera.update(player.x, player.y)
        
        # Process results
        end_turn = False
        victory_triggered = False
        portal_entry = False
        
        for result in movement_result.get("results", []):
            message = result.get("message")
            if message:
                message_log.add_message(message)
            
            # Handle FOV recompute
            if result.get("fov_recompute"):
                self.state_manager.request_fov_recompute()
            
            # Handle portal entry (Phase 5)
            if result.get("portal_entry"):
                logger.info("=== PATHFINDING: Portal entry detected! Transitioning to CONFRONTATION ===")
                print(">>> PATHFINDING: Portal entry detected! Going to confrontation...")
                
                # Add portal entry messages
                from message_builder import MessageBuilder as MB
                message_log.add_message(MB.item_effect("You step through the portal..."))
                message_log.add_message(MB.warning("Reality twists around you!"))
                
                # Mark confrontation started on player
                # Note: victory is a direct attribute, not in ComponentRegistry
                if hasattr(player, 'victory') and player.victory:
                    player.victory.start_confrontation()
                
                portal_entry = True
                # Don't end turn normally, jump straight to confrontation
            
            # Handle victory trigger
            if result.get("victory_triggered"):
                logger.info("=== PATHFINDING: Victory sequence triggered via pathfinding pickup ===")
                print(">>> PATHFINDING: Calling handle_ruby_heart_pickup...")
                from victory_manager import get_victory_manager
                victory_mgr = get_victory_manager()
                
                if victory_mgr.handle_ruby_heart_pickup(player, entities, game_map, message_log):
                    logger.info("=== PATHFINDING: Victory sequence initiated successfully ===")
                    print(">>> PATHFINDING: Portal should have spawned! Transitioning to RUBY_HEART_OBTAINED state")
                    victory_triggered = True
                else:
                    logger.error("=== PATHFINDING: Victory sequence FAILED ===")
                    print(">>> PATHFINDING: Portal spawn FAILED!")
            
            # Check if we should end the turn (continue pathfinding or interrupt after movement)
            if result.get("continue_pathfinding") or result.get("enemy_turn"):
                end_turn = True
        
        # Transition to appropriate state
        if portal_entry:
            # Player stepped on portal - go straight to confrontation
            self.state_manager.set_game_state(GameStates.CONFRONTATION)
            logger.info("=== PATHFINDING: State transitioned to CONFRONTATION ===")
            print(">>> PATHFINDING: State is now CONFRONTATION")
        elif victory_triggered:
            # Victory sequence initiated - set to special state
            self.state_manager.set_game_state(GameStates.RUBY_HEART_OBTAINED)
        elif end_turn:
            # Player moved, give enemies their turn (which will cycle back to player)
            self.turn_controller.end_player_action(turn_consumed=True)
        else:
            # Pathfinding completed/cancelled without movement, stay in player turn
            self.state_manager.set_game_state(GameStates.PLAYERS_TURN)
    
    def _handle_left_click(self, click_pos: Tuple[int, int]) -> None:
        """Handle left mouse click (attack enemy or pathfind to location).

        Uses the same logic as right-click: check for enemies first,
        then items/chests/signposts, then pathfind to empty space.

        Args:
            click_pos: Tuple of (world_x, world_y) click coordinates
        """
        current_state = self.state_manager.state.current_state

        # Handle targeting mode first
        if current_state == GameStates.TARGETING:
            target_x, target_y = click_pos
            
            # Check for portal wand targeting FIRST
            from components.portal_placer import PortalPlacer
            portal_wand = self.state_manager.get_extra_data("portal_wand")
            if portal_wand and hasattr(portal_wand, 'portal_placer'):
                portal_placer = portal_wand.portal_placer
                game_map = self.state_manager.state.game_map
                message_log = self.state_manager.state.message_log
                entities = self.state_manager.state.entities
                logger = __import__('logging').getLogger(__name__)
                logger.warning(f"DEBUG: Portal targeting - entities list id: {id(entities)}, state_manager.state.entities id: {id(self.state_manager.state.entities)}")
                
                # Check if portal placer needs entrance portal
                if not portal_placer.active_entrance:
                    # Place entrance portal - use PortalManager for centralized creation
                    result = portal_placer.place_entrance(target_x, target_y, game_map)
                    if result.get('success'):
                        # PortalPlacer returns Portal component
                        # Now create full Entity using PortalManager
                        from services.portal_manager import get_portal_manager
                        portal_manager = get_portal_manager()
                        
                        entrance_entity = portal_manager.create_portal_entity('entrance', target_x, target_y)
                        if entrance_entity:
                            # Store reference in placer for later linking
                            portal_placer.active_entrance = entrance_entity.portal
                            
                            entities.append(entrance_entity)
                            message_log.add_message(MB.success("Entrance portal placed. Click to place exit portal."))
                        else:
                            message_log.add_message(MB.warning("Failed to create entrance portal"))
                    else:
                        message_log.add_message(MB.warning(result.get('message', 'Invalid placement')))
                
                # Check if portal placer needs exit portal
                elif not portal_placer.active_exit:
                    # Place exit portal - use PortalManager for centralized creation
                    result = portal_placer.place_exit(target_x, target_y, game_map)
                    if result.get('success'):
                        from services.portal_manager import get_portal_manager
                        portal_manager = get_portal_manager()
                        
                        # Get the entrance portal from placer
                        entrance_portal_component = result.get('entrance')
                        
                        # Create exit entity with link to entrance
                        exit_entity = portal_manager.create_portal_entity('exit', target_x, target_y, linked_portal=entrance_portal_component)
                        if exit_entity:
                            # Store reference and link both portals
                            portal_placer.active_exit = exit_entity.portal
                            entrance_portal_component.linked_portal = exit_entity.portal
                            
                            entities.append(exit_entity)
                            message_log.add_message(MB.success("Exit portal placed! Portals are now active."))
                            
                            # Exit targeting mode - portals placed
                            self.state_manager.set_extra_data("portal_wand", None)
                            self.state_manager.set_game_state(GameStates.PLAYERS_TURN)
                            
                            # TURN ECONOMY: Portal placement takes 1 turn
                            self._process_player_status_effects()
                            self.turn_controller.end_player_action(turn_consumed=True)
                        else:
                            message_log.add_message(MB.warning("Failed to create exit portal"))
                    else:
                        message_log.add_message(MB.warning(result.get('message', 'Invalid placement')))
                
                return  # Portal wand targeting handled
            
            # Otherwise handle regular targeting items
            targeting_item = self.state_manager.get_extra_data("targeting_item")

            if targeting_item and targeting_item.item:
                player = self.state_manager.state.player
                if player and player.inventory:
                    item_use_results = player.inventory.use(
                        targeting_item,
                        entities=self.state_manager.state.entities,
                        fov_map=self.state_manager.state.fov_map,
                        game_map=self.state_manager.state.game_map,
                        target_x=target_x,
                        target_y=target_y
                    )

                    # Process results
                    player_died = False
                    for result in item_use_results:
                        message = result.get("message")
                        if message:
                            self.state_manager.state.message_log.add_message(message)

                        dead_entity = result.get("dead")
                        if dead_entity:
                            # Targeting/spell deaths should transform to corpse (not remove)
                            self._handle_entity_death(dead_entity, remove_from_entities=False)
                            if dead_entity == player:
                                player_died = True

                    # Clear targeting state and restore to player turn
                    self.state_manager.set_game_state(GameStates.PLAYERS_TURN)
                    self.state_manager.set_extra_data("targeting_item", None)
                    self.state_manager.set_extra_data("previous_state", None)

                    # TURN ECONOMY: Completing targeting (using targeted item) takes 1 turn
                    if not player_died:
                        self._process_player_status_effects()
                        self.turn_controller.end_player_action(turn_consumed=True)
                else:
                    print("DEBUG: No player or inventory")
            else:
                print("DEBUG: No targeting item or item has no item component")
            return

        if current_state not in (GameStates.PLAYERS_TURN, GameStates.RUBY_HEART_OBTAINED):
            return

        # Delegate to the same handler as right-click
        # Left-click and right-click should do the same thing during gameplay
        self._handle_mouse_movement(click_pos)
    
    def _handle_right_click(self, click_pos: Tuple[int, int]) -> None:
        """Handle right mouse click using the clean InteractionSystem.
        
        Uses strategy pattern for clean, testable interaction handling:
        Priority 1: Enemies → Throw menu (combat is urgent!)
        Priority 2: Items → Auto-pickup (pathfind if far)
        Priority 3: NPCs → Dialogue (they can wait)
        
        Args:
            click_pos: Tuple of (world_x, world_y) click coordinates
        """
        current_state = self.state_manager.state.current_state
        
        if current_state == GameStates.TARGETING:
            # Cancel targeting
            self.state_manager.set_game_state(GameStates.PLAYERS_TURN)
            self.state_manager.set_extra_data("targeting_item", None)
            self.state_manager.set_extra_data("previous_state", None)
            
        elif current_state == GameStates.PLAYERS_TURN:
            player = self.state_manager.state.player
            entities = self.state_manager.state.entities
            game_map = self.state_manager.state.game_map
            message_log = self.state_manager.state.message_log
            fov_map = self.state_manager.state.fov_map
            
            if not all([player, entities, game_map, message_log]):
                return
            
            world_x, world_y = click_pos
            
            # Use the clean InteractionSystem
            from systems.interaction_system import get_interaction_system
            interaction_system = get_interaction_system()
            
            result = interaction_system.handle_click(
                world_x, world_y, player, entities, game_map, fov_map
            )
            
            # Process the result
            if result.action_taken:
                # Show message
                if result.message:
                    message_log.add_message(result.message)
                
                # Handle state change
                if result.state_change:
                    self.state_manager.set_game_state(result.state_change)
                    
                    # Store throw target if needed
                    if result.state_change == GameStates.THROW_SELECT_ITEM:
                        self.state_manager.set_extra_data("throw_target", (world_x, world_y))
                
                # Handle NPC dialogue
                if result.npc_dialogue:
                    self.state_manager.state.current_dialogue_npc = result.npc_dialogue
                
                # Handle victory trigger (Ruby Heart pickup)
                if result.victory_triggered:
                    logger.info("=== RIGHT-CLICK: Victory trigger detected from interaction system ===")
                    print(">>> RIGHT-CLICK: Ruby Heart picked up via interaction system!")
                    from victory_manager import get_victory_manager
                    victory_mgr = get_victory_manager()
                    
                    if victory_mgr.handle_ruby_heart_pickup(player, entities, game_map, message_log):
                        logger.info("=== RIGHT-CLICK: Victory sequence initiated successfully ===")
                        print(">>> RIGHT-CLICK: Portal spawned! Transitioning to RUBY_HEART_OBTAINED")
                        self.state_manager.set_game_state(GameStates.RUBY_HEART_OBTAINED)
                        # Don't consume turn here - already consumed by pickup
                        return
                    else:
                        logger.error("=== RIGHT-CLICK: Victory sequence FAILED ===")
                        print(">>> RIGHT-CLICK: Portal spawn FAILED!")
                
                # Start pathfinding if needed
                if result.start_pathfinding:
                    self._process_pathfinding_movement_action(None)
                
                # Consume turn if needed
                if result.consume_turn:
                    self.turn_controller.end_player_action(turn_consumed=True)
                
                return
            
            # No interaction handled by system - fallthrough to auto-explore
            # No item or enemy at location - start auto-explore!
            # This gives full mouse control - right-click anywhere to explore
            auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
            
            if auto_explore and auto_explore.is_active():
                # Already exploring - cancel it
                auto_explore.stop("Cancelled")
                message_log.add_message(MB.info("Auto-explore cancelled"))
            else:
                # Start auto-explore
                if not auto_explore:
                    from components.auto_explore import AutoExplore
                    auto_explore = AutoExplore()
                    auto_explore.owner = player
                    player.components.add(ComponentType.AUTO_EXPLORE, auto_explore)
                
                # Start exploring (returns adventure quote)
                adventure_quote = auto_explore.start(game_map, entities, fov_map)
                
                # Show adventure quote
                message_log.add_message(MB.custom(f'"{adventure_quote}"', MB.CYAN))
                message_log.add_message(MB.info("Auto-exploring... (any key to cancel)"))
    
    def _process_player_status_effects(self) -> None:
        """Process status effects at the end of the player's turn."""
        player = self.state_manager.state.player
        message_log = self.state_manager.state.message_log
        
        if not player or not message_log:
            return
        
        # Get current turn number from TurnManager (if available)
        turn_number = None
        if self.turn_manager:
            turn_number = self.turn_manager.turn_number
        
        # Process status effects at turn START (for Ring of Regeneration, etc.)
        # This happens BEFORE the turn ends to apply regeneration
        if hasattr(player, 'status_effects') and player.status_effects:
            start_results = player.status_effects.process_turn_start(turn_number=turn_number)
            for result in start_results:
                message = result.get("message")
                if message:
                    message_log.add_message(message)
        
        # Process status effects turn end (duration decrements, etc.)
        effect_results = player.process_status_effects_turn_end()
        
        # Add any messages from status effects
        for result in effect_results:
            message = result.get("message")
            if message:
                message_log.add_message(message)
    
    def _break_invisibility(self, entity) -> None:
        """Break invisibility effect on an entity when they attack.
        
        Args:
            entity: The entity whose invisibility should be broken
        """
        message_log = self.state_manager.state.message_log
        
        if not entity or not message_log:
            return
        
        # Get the invisibility effect and break it
        status_manager = entity.get_status_effect_manager()
        if status_manager and status_manager.has_effect("invisibility"):
            invisibility_effect = status_manager.get_effect("invisibility")
            if invisibility_effect:
                break_results = invisibility_effect.break_invisibility()
                
                # Add any messages from breaking invisibility
                for result in break_results:
                    message = result.get("message")
                    if message:
                        message_log.add_message(message)
