"""Game action processing system.

This module provides a clean, modular way to handle game actions by breaking
down the monolithic action processing into focused, testable components.
Also integrates Entity dialogue for key game moments (Phase 1 expansion).
"""

from typing import Dict, Any, Optional, Tuple
import logging

from message_builder import MessageBuilder as MB
from game_states import GameStates
from config.game_constants import get_constants
from entity_sorting_cache import invalidate_entity_cache
from entity_dialogue import EntityDialogue
from components.component_registry import ComponentType

logger = logging.getLogger(__name__)


def _transition_to_enemy_turn(state_manager, turn_manager=None) -> None:
    """Helper function to transition from player turn to enemy turn.
    
    Phase 3: Uses TurnManager if available, otherwise falls back to GameStates.
    This provides a single point of control for turn transitions.
    
    Args:
        state_manager: Game state manager
        turn_manager: Optional turn manager (Phase 3 integration)
    """
    # Use TurnManager if available (Phase 3)
    if turn_manager:
        from engine.turn_manager import TurnPhase
        turn_manager.advance_turn(TurnPhase.ENEMY)
    
    # Always keep GameStates in sync (backward compatibility)
    state_manager.set_game_state(GameStates.ENEMY_TURN)


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
        
        # Map action types to their handler methods
        self.action_handlers = {
            'show_inventory': self._handle_show_inventory,
            'drop_inventory': self._handle_drop_inventory,
            'show_character_screen': self._handle_show_character_screen,
            'exit': self._handle_exit,
            'move': self._handle_movement,
            'wait': self._handle_wait,
            'pickup': self._handle_pickup,
            'inventory_index': self._handle_inventory_action,
            'take_stairs': self._handle_stairs,
            'level_up': self._handle_level_up,
            'start_auto_explore': self._handle_start_auto_explore,
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
        if current_state == GameStates.PLAYERS_TURN:
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
        for action_type, value in action.items():
            # Use 'is not None' instead of just 'value' to handle inventory_index=0
            if value is not None and action_type in self.action_handlers:
                try:
                    self.action_handlers[action_type](value)
                except Exception as e:
                    logger.error(f"Error processing action {action_type}: {e}", exc_info=True)
        
        # Process mouse actions
        for mouse_action_type, value in mouse_action.items():
            logger.warning(f"Mouse action type: {mouse_action_type}, value: {value}, has handler: {mouse_action_type in self.mouse_handlers}")
            if value and mouse_action_type in self.mouse_handlers:
                try:
                    logger.warning(f"Calling mouse handler for {mouse_action_type}")
                    self.mouse_handlers[mouse_action_type](value)
                except Exception as e:
                    logger.error(f"Error processing mouse action {mouse_action_type}: {e}", exc_info=True)
    
    def _handle_show_inventory(self, _) -> None:
        """Handle showing the inventory screen."""
        self.state_manager.set_game_state(GameStates.SHOW_INVENTORY)
    
    def _handle_drop_inventory(self, _) -> None:
        """Handle showing the drop inventory screen."""
        self.state_manager.set_game_state(GameStates.DROP_INVENTORY)
    
    def _handle_show_character_screen(self, _) -> None:
        """Handle showing the character screen."""
        self.state_manager.set_game_state(GameStates.CHARACTER_SCREEN)
    
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
        """Handle exit actions based on current game state."""
        current_state = self.state_manager.state.current_state
        
        if current_state in (
            GameStates.SHOW_INVENTORY,
            GameStates.DROP_INVENTORY,
            GameStates.CHARACTER_SCREEN,
            GameStates.LEVEL_UP,
        ):
            self.state_manager.set_game_state(GameStates.PLAYERS_TURN)
        elif current_state == GameStates.TARGETING:
            previous_state = self.state_manager.get_extra_data("previous_state", GameStates.PLAYERS_TURN)
            self.state_manager.set_game_state(previous_state)
            self.state_manager.set_extra_data("targeting_item", None)
            self.state_manager.set_extra_data("previous_state", None)
    
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
            self.state_manager.state.fov_map
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
            
            # Check if we should end the turn (continue pathfinding or interrupt after movement)
            if r.get("continue_pathfinding") or r.get("enemy_turn"):
                end_turn = True
        
        # Transition to enemy turn if player moved
        if end_turn:
            _transition_to_enemy_turn(self.state_manager, self.turn_manager)
    
    def _handle_movement(self, move_data: Tuple[int, int]) -> None:
        """Handle player movement.
        
        Args:
            move_data: Tuple of (dx, dy) movement deltas
        """
        current_state = self.state_manager.state.current_state
        if current_state != GameStates.PLAYERS_TURN:
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
        
        destination_x = player.x + dx
        destination_y = player.y + dy
        
        game_map = self.state_manager.state.game_map
        if not game_map or game_map.is_blocked(destination_x, destination_y):
            return
        
        # Check for blocking entities
        from entity import get_blocking_entities_at_location
        target = get_blocking_entities_at_location(
            self.state_manager.state.entities, destination_x, destination_y
        )
        
        if target:
            self._handle_combat(player, target)
        else:
            # Move player
            player.move(dx, dy)
            self.state_manager.request_fov_recompute()
            
            # Update camera to follow player (Phase 2)
            camera = self.state_manager.state.camera
            if camera:
                camera.update(player.x, player.y)
        
        # Process status effects at end of player turn
        self._process_player_status_effects()
        
        # Switch to enemy turn
        _transition_to_enemy_turn(self.state_manager, self.turn_manager)
    
    def _handle_combat(self, attacker, target) -> None:
        """Handle combat between attacker and target.
        
        Args:
            attacker: The attacking entity
            target: The target entity
        """
        if not (attacker.fighter and target.fighter):
            return
        
        # Break invisibility if the attacker is attacking
        if hasattr(attacker, 'invisible') and attacker.invisible:
            self._break_invisibility(attacker)
        
        # Use new d20-based attack system
        attack_results = attacker.fighter.attack_d20(target)
        
        for result in attack_results:
            message = result.get("message")
            if message:
                self.state_manager.state.message_log.add_message(message)
            
            dead_entity = result.get("dead")
            if dead_entity:
                # Combat deaths should transform to corpses (keep in entities list)
                self._handle_entity_death(dead_entity, remove_from_entities=False)
    
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
            _transition_to_enemy_turn(self.state_manager, self.turn_manager)
    
    def _handle_pickup(self, _) -> None:
        """Handle item pickup. TAKES 1 TURN."""
        current_state = self.state_manager.state.current_state
        if current_state != GameStates.PLAYERS_TURN:
            return
        
        player = self.state_manager.state.player
        entities = self.state_manager.state.entities
        message_log = self.state_manager.state.message_log
        
        if not all([player, entities is not None, message_log]):
            return
        
        # Look for items at player's position
        item_found = False
        for entity in entities:
            if entity.item and entity.x == player.x and entity.y == player.y:
                item_found = True
                if not player.inventory:
                    message = MB.warning("You cannot carry items.")
                    message_log.add_message(message)
                    break
                
                pickup_results = player.inventory.add_item(entity)
                
                for result in pickup_results:
                    message = result.get("message")
                    if message:
                        message_log.add_message(message)
                    
                    item_added = result.get("item_added")
                    item_consumed = result.get("item_consumed")
                    
                    # Remove entity if it was added to inventory OR consumed (e.g., scroll recharged a wand)
                    if item_added or item_consumed:
                        entities.remove(entity)
                        
                        # TURN ECONOMY: Picking up an item takes 1 turn
                        self._process_player_status_effects()
                        _transition_to_enemy_turn(self.state_manager, self.turn_manager)
                
                break
        
        if not item_found:
            message = MB.warning("There is nothing here to pick up.")
            message_log.add_message(message)
            # No item to pick up = no turn consumed
    
    def _handle_inventory_action(self, inventory_index: int) -> None:
        """Handle inventory item usage or dropping.
        
        Args:
            inventory_index: Index of item in inventory
        """
        current_state = self.state_manager.state.current_state
        player = self.state_manager.state.player
        
        if not player or not player.inventory:
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
        
        item = player.inventory.items[inventory_index]
        
        logger.warning(f"Current state: {current_state}, item: {item.name if item else None}")
        
        if current_state == GameStates.SHOW_INVENTORY:
            self._use_inventory_item(item)
        elif current_state == GameStates.DROP_INVENTORY:
            self._drop_inventory_item(item)
        elif current_state == GameStates.PLAYERS_TURN:
            # Sidebar click during normal gameplay - use the item!
            logger.warning(f"Using item from sidebar during PLAYERS_TURN")
            self._use_inventory_item(item)
    
    def _use_inventory_item(self, item) -> None:
        """Use an item from inventory. TAKES 1 TURN (unless entering targeting mode).
        
        Args:
            item: The item entity to use
        """
        if not item.item:
            return
        
        player = self.state_manager.state.player
        item_use_results = player.inventory.use(
            item,
            entities=self.state_manager.state.entities,
            fov_map=self.state_manager.state.fov_map
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
                _transition_to_enemy_turn(self.state_manager, self.turn_manager)
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
            _transition_to_enemy_turn(self.state_manager, self.turn_manager)
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
        current_state = self.state_manager.state.current_state
        if current_state != GameStates.PLAYERS_TURN:
            return
        
        player = self.state_manager.state.player
        entities = self.state_manager.state.entities
        game_map = self.state_manager.state.game_map
        message_log = self.state_manager.state.message_log
        
        if not all([player, entities is not None, game_map, message_log]):
            return
        
        # Check if player is on stairs
        for entity in entities:
            if (entity.components.has(ComponentType.STAIRS) and 
                entity.x == player.x and entity.y == player.y):
                
                # Generate next floor
                new_entities = game_map.next_floor(player, message_log, self.constants)
                self.state_manager.update_state(entities=new_entities)
                
                # Initialize new FOV map for the new level
                from fov_functions import initialize_fov
                new_fov_map = initialize_fov(game_map)
                self.state_manager.update_state(fov_map=new_fov_map)
                self.state_manager.request_fov_recompute()
                
                # Entity comments on level transition (Phase 1 feature!)
                entity_quote = EntityDialogue.get_level_transition_quote(game_map.dungeon_level)
                entity_message = MB.custom(entity_quote, (180, 180, 150))  # Muted gold for Entity
                message_log.add_message(entity_message)
                
                break
        else:
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
        
        if not player or not player.fighter or not message_log:
            return
        
        # Apply level up bonuses based on choice
        if level_up_choice == "hp":
            player.fighter.base_max_hp += 20
            player.fighter.hp += 20
            message = MB.level_up("Your health increases!")
        elif level_up_choice == "str":
            player.fighter.base_power += 1
            message = MB.level_up("You feel stronger!")
        elif level_up_choice == "def":
            player.fighter.base_defense += 1
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
        
        # Handle clicks on inventory/drop menus
        if current_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
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
                for item in player.inventory.items:
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
            else:
                header = "Press the key next to an item to drop it, or Esc to cancel.\n"
            
            # Check if click is on a menu item (click_pos is screen coordinates)
            mouse_x, mouse_y = click_pos
            clicked_index = get_menu_click_index(
                mouse_x, mouse_y, header, options, 50, 
                ui_layout.screen_width, ui_layout.screen_height
            )
            
            if clicked_index is not None and clicked_index < len(player.inventory.items):
                # User clicked on an inventory item!
                if current_state == GameStates.SHOW_INVENTORY:
                    self._handle_inventory_action(clicked_index)
                else:  # DROP_INVENTORY
                    self._handle_drop_inventory(clicked_index)
            return
        
        if current_state == GameStates.TARGETING:
            target_x, target_y = click_pos
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
                    
                    for result in item_use_results:
                        message = result.get("message")
                        if message:
                            self.state_manager.state.message_log.add_message(message)
                        
                        dead_entity = result.get("dead")
                        if dead_entity:
                            # Targeting/spell deaths should transform to corpse (not remove)
                            self._handle_entity_death(dead_entity, remove_from_entities=False)
                    
                    # Return to player turn after targeting
                    self.state_manager.set_game_state(GameStates.PLAYERS_TURN)
                    self.state_manager.set_extra_data("targeting_item", None)
                    self.state_manager.set_extra_data("previous_state", None)
        
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
                # User left-clicked on equipment - could show info or do nothing for now
                logger.warning(f"SIDEBAR EQUIPMENT CLICKED: slot {action['equipment_slot']}")
                # For now, left-click on equipment does nothing (could add "examine" later)
                pass
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
            if not player.inventory or not hasattr(player.inventory, 'items'):
                return
            
            if inventory_index < 0 or inventory_index >= len(player.inventory.items):
                message_log.add_message(
                    MB.warning(f"Invalid item selection.")
                )
                return
            
            item = player.inventory.items[inventory_index]
            
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
                _transition_to_enemy_turn(self.state_manager, self.turn_manager)
            
            # Handle pathfinding to enemy
            if result.get("pathfind_to_enemy"):
                target_x, target_y = result["pathfind_to_enemy"]
                if player.pathfinding.set_destination(target_x, target_y, game_map, entities):
                    # Successfully set path to enemy
                    _transition_to_enemy_turn(self.state_manager, self.turn_manager)
                else:
                    # Could not find path to enemy
                    message_log.add_message(MB.warning("Cannot reach that enemy."))
            
            # Handle immediate enemy turn (for attacks)
            if result.get("enemy_turn"):
                _transition_to_enemy_turn(self.state_manager, self.turn_manager)
    
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
        movement_result = process_pathfinding_movement(player, entities, game_map, fov_map)
        
        # Update camera to follow player (Phase 2)
        camera = self.state_manager.state.camera
        if camera:
            camera.update(player.x, player.y)
        
        # Process results
        end_turn = False
        for result in movement_result.get("results", []):
            message = result.get("message")
            if message:
                message_log.add_message(message)
            
            # Handle FOV recompute
            if result.get("fov_recompute"):
                self.state_manager.request_fov_recompute()
            
            # Check if we should end the turn (continue pathfinding or interrupt after movement)
            if result.get("continue_pathfinding") or result.get("enemy_turn"):
                end_turn = True
        
        # Transition to appropriate state
        if end_turn:
            # Player moved, give enemies their turn (which will cycle back to player)
            _transition_to_enemy_turn(self.state_manager, self.turn_manager)
        else:
            # Pathfinding completed/cancelled without movement, stay in player turn
            self.state_manager.set_game_state(GameStates.PLAYERS_TURN)
    
    def _handle_right_click(self, click_pos: Tuple[int, int]) -> None:
        """Handle right mouse click (context-aware: pickup items or cancel).
        
        Args:
            click_pos: Tuple of (world_x, world_y) click coordinates
        """
        current_state = self.state_manager.state.current_state
        
        if current_state == GameStates.TARGETING:
            # Cancel targeting
            previous_state = self.state_manager.get_extra_data("previous_state", GameStates.PLAYERS_TURN)
            self.state_manager.set_game_state(previous_state)
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
            
            # Check if there's an item at this location
            target_item = None
            for entity in entities:
                if entity.x == world_x and entity.y == world_y:
                    if entity.components.has(ComponentType.ITEM):
                        target_item = entity
                        break
            
            if target_item:
                # Right-click on item → pathfind and auto-pickup!
                distance = player.distance_to(target_item)
                
                if distance <= 1:
                    # Already adjacent - just pick it up
                    if player.inventory:
                        pickup_results = player.inventory.add_item(target_item)
                        for result in pickup_results:
                            message = result.get("message")
                            if message:
                                message_log.add_message(message)
                            
                            item_added = result.get("item_added")
                            item_consumed = result.get("item_consumed")
                            if item_added or item_consumed:
                                entities.remove(target_item)
                    
                    # End turn after pickup
                    _transition_to_enemy_turn(self.state_manager, self.turn_manager)
                else:
                    # Not adjacent - pathfind to it
                    pathfinding = player.get_component_optional(ComponentType.PATHFINDING)
                    if pathfinding:
                        success = pathfinding.set_destination(
                            target_item.x, target_item.y, game_map, entities, fov_map
                        )
                        
                        if success:
                            # Mark that we want to auto-pickup when we arrive
                            player.pathfinding.auto_pickup_target = target_item
                            
                            message_log.add_message(
                                MB.info(f"Moving to pick up {target_item.name}...")
                            )
                            
                            # Immediately start moving along the path
                            self._process_pathfinding_movement_action(None)
                        else:
                            message_log.add_message(
                                MB.warning("Cannot path to that location.")
                            )
            else:
                # No item at location - cancel pathfinding if active
                pathfinding = player.get_component_optional(ComponentType.PATHFINDING)
                if pathfinding and pathfinding.is_path_active():
                    pathfinding.cancel_movement()
                    if message_log:
                        message_log.add_message(MB.warning("Movement cancelled."))
    
    def _process_player_status_effects(self) -> None:
        """Process status effects at the end of the player's turn."""
        player = self.state_manager.state.player
        message_log = self.state_manager.state.message_log
        
        if not player or not message_log:
            return
        
        # Process status effects turn end
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
