"""Game action processing system.

This module provides a clean, modular way to handle game actions by breaking
down the monolithic action processing into focused, testable components.
"""

from typing import Dict, Any, Optional, Tuple
import logging

from game_messages import Message
from game_states import GameStates
from config.game_constants import get_constants
from entity_sorting_cache import invalidate_entity_cache

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
        }
        
        # Map mouse actions to their handlers
        self.mouse_handlers = {
            'left_click': self._handle_left_click,
            'right_click': self._handle_right_click,
        }
    
    def process_actions(self, action: Dict[str, Any], mouse_action: Dict[str, Any]) -> None:
        """Process keyboard and mouse actions.
        
        Args:
            action: Dictionary of keyboard actions
            mouse_action: Dictionary of mouse actions
        """
        current_state = self.state_manager.state.current_state
        
        # CRITICAL: Don't process any game actions if player is dead
        if current_state == GameStates.PLAYER_DEAD:
            return
        
        # Process keyboard actions
        for action_type, value in action.items():
            # Use 'is not None' instead of just 'value' to handle inventory_index=0
            if value is not None and action_type in self.action_handlers:
                try:
                    self.action_handlers[action_type](value)
                except Exception as e:
                    logger.error(f"Error processing action {action_type}: {e}")
        
        # Process mouse actions
        for mouse_action_type, value in mouse_action.items():
            if value and mouse_action_type in self.mouse_handlers:
                try:
                    self.mouse_handlers[mouse_action_type](value)
                except Exception as e:
                    logger.error(f"Error processing mouse action {mouse_action_type}: {e}")
    
    def _handle_show_inventory(self, _) -> None:
        """Handle showing the inventory screen."""
        self.state_manager.set_game_state(GameStates.SHOW_INVENTORY)
    
    def _handle_drop_inventory(self, _) -> None:
        """Handle showing the drop inventory screen."""
        self.state_manager.set_game_state(GameStates.DROP_INVENTORY)
    
    def _handle_show_character_screen(self, _) -> None:
        """Handle showing the character screen."""
        self.state_manager.set_game_state(GameStates.CHARACTER_SCREEN)
    
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
        
        # Process status effects at end of player turn
        self._process_player_status_effects()
        
        # Switch to enemy turn
        self.state_manager.set_game_state(GameStates.ENEMY_TURN)
    
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
        
        attack_results = attacker.fighter.attack(target)
        
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
            death_message = Message(
                "You died! Press any key to return to the main menu.",
                (255, 30, 30)
            )
            self.state_manager.state.message_log.add_message(death_message)
        else:
            # Monster died - always transform to corpse first
            from death_functions import kill_monster
            game_map = self.state_manager.state.game_map
            death_message = kill_monster(dead_entity, game_map)
            self.state_manager.state.message_log.add_message(death_message)
            
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
            self.state_manager.set_game_state(GameStates.ENEMY_TURN)
    
    def _handle_pickup(self, _) -> None:
        """Handle item pickup."""
        current_state = self.state_manager.state.current_state
        if current_state != GameStates.PLAYERS_TURN:
            return
        
        player = self.state_manager.state.player
        entities = self.state_manager.state.entities
        message_log = self.state_manager.state.message_log
        
        if not all([player, entities is not None, message_log]):
            return
        
        # Look for items at player's position
        for entity in entities:
            if entity.item and entity.x == player.x and entity.y == player.y:
                if not player.inventory:
                    message = Message("You cannot carry items.", (255, 255, 0))
                    message_log.add_message(message)
                    break
                
                pickup_results = player.inventory.add_item(entity)
                
                for result in pickup_results:
                    message = result.get("message")
                    if message:
                        message_log.add_message(message)
                    
                    item_added = result.get("item_added")
                    if item_added:
                        entities.remove(entity)
                
                break
        else:
            message = Message("There is nothing here to pick up.", (255, 255, 0))
            message_log.add_message(message)
    
    def _handle_inventory_action(self, inventory_index: int) -> None:
        """Handle inventory item usage or dropping.
        
        Args:
            inventory_index: Index of item in inventory
        """
        current_state = self.state_manager.state.current_state
        player = self.state_manager.state.player
        
        if not player or not player.inventory:
            return
        
        if not (0 <= inventory_index < len(player.inventory.items)):
            return
        
        item = player.inventory.items[inventory_index]
        
        if current_state == GameStates.SHOW_INVENTORY:
            self._use_inventory_item(item)
        elif current_state == GameStates.DROP_INVENTORY:
            self._drop_inventory_item(item)
    
    def _use_inventory_item(self, item) -> None:
        """Use an item from inventory.
        
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
        
        for result in item_use_results:
            message = result.get("message")
            if message:
                self.state_manager.state.message_log.add_message(message)
            
            # Handle death results
            dead_entity = result.get("dead")
            if dead_entity:
                # Item/spell deaths should transform to corpse (not remove)
                self._handle_entity_death(dead_entity, remove_from_entities=False)
            
            # Handle targeting
            targeting = result.get("targeting")
            if targeting:
                self.state_manager.set_game_state(GameStates.TARGETING)
                self.state_manager.set_extra_data("targeting_item", item)
                self.state_manager.set_extra_data("previous_state", GameStates.SHOW_INVENTORY)
                return
            
            # Handle equipment
            equip = result.get("equip")
            if equip and player.equipment:
                self._handle_equipment(equip)
        
        # Return to player turn if no targeting
        if not any(result.get("targeting") for result in item_use_results):
            self.state_manager.set_game_state(GameStates.PLAYERS_TURN)
    
    def _drop_inventory_item(self, item) -> None:
        """Drop an item from inventory.
        
        Args:
            item: The item entity to drop
        """
        player = self.state_manager.state.player
        drop_results = player.inventory.drop_item(item)
        
        for result in drop_results:
            message = result.get("message")
            if message:
                self.state_manager.state.message_log.add_message(message)
            
            item_dropped = result.get("item_dropped")
            if item_dropped:
                item_dropped.x = player.x
                item_dropped.y = player.y
                self.state_manager.state.entities.append(item_dropped)
        
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
                message = Message(f"You equip the {equipped.name}.", (0, 255, 0))
                self.state_manager.state.message_log.add_message(message)
            elif dequipped:
                message = Message(f"You unequip the {dequipped.name}.", (255, 255, 0))
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
            if (hasattr(entity, 'stairs') and entity.stairs and 
                entity.x == player.x and entity.y == player.y):
                
                # Generate next floor
                new_entities = game_map.next_floor(player, message_log, self.constants)
                self.state_manager.update_state(entities=new_entities)
                
                # Initialize new FOV map for the new level
                from fov_functions import initialize_fov
                new_fov_map = initialize_fov(game_map)
                self.state_manager.update_state(fov_map=new_fov_map)
                self.state_manager.request_fov_recompute()
                
                break
        else:
            message = Message("There are no stairs here.", (255, 255, 0))
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
            message = Message("Your health increases!", (0, 255, 0))
        elif level_up_choice == "str":
            player.fighter.base_power += 1
            message = Message("You feel stronger!", (0, 255, 0))
        elif level_up_choice == "def":
            player.fighter.base_defense += 1
            message = Message("Your movements are getting swifter!", (0, 255, 0))
        else:
            # Invalid choice, don't apply any bonuses
            message = Message("Invalid level up choice.", (255, 255, 0))
            message_log.add_message(message)
            return
        
        message_log.add_message(message)
        
        # Return to player turn
        self.state_manager.set_game_state(GameStates.PLAYERS_TURN)
    
    def _handle_left_click(self, click_pos: Tuple[int, int]) -> None:
        """Handle left mouse click.
        
        Args:
            click_pos: Tuple of (x, y) click coordinates
        """
        current_state = self.state_manager.state.current_state
        
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
    
    def _handle_mouse_movement(self, click_pos: Tuple[int, int]) -> None:
        """Handle mouse click for movement or combat.
        
        Args:
            click_pos: Tuple of (x, y) click coordinates
        """
        from mouse_movement import handle_mouse_click
        
        player = self.state_manager.state.player
        entities = self.state_manager.state.entities
        game_map = self.state_manager.state.game_map
        message_log = self.state_manager.state.message_log
        
        if not all([player, entities is not None, game_map, message_log]):
            return
        
        click_x, click_y = click_pos
        
        # Handle the mouse click
        click_result = handle_mouse_click(click_x, click_y, player, entities, game_map)
        
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
                self.state_manager.set_game_state(GameStates.ENEMY_TURN)
            
            # Handle pathfinding to enemy
            if result.get("pathfind_to_enemy"):
                target_x, target_y = result["pathfind_to_enemy"]
                if player.pathfinding.set_destination(target_x, target_y, game_map, entities):
                    # Successfully set path to enemy
                    self.state_manager.set_game_state(GameStates.ENEMY_TURN)
                else:
                    # Could not find path to enemy
                    message_log.add_message(Message("Cannot reach that enemy.", (255, 255, 0)))
            
            # Handle immediate enemy turn (for attacks)
            if result.get("enemy_turn"):
                self.state_manager.set_game_state(GameStates.ENEMY_TURN)
    
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
        if not (hasattr(player, 'pathfinding') and player.pathfinding and 
                player.pathfinding.is_path_active()):
            return
        
        # Process pathfinding movement
        movement_result = process_pathfinding_movement(player, entities, game_map, fov_map)
        
        # Process results
        for result in movement_result.get("results", []):
            message = result.get("message")
            if message:
                message_log.add_message(message)
            
            # Handle FOV recompute
            if result.get("fov_recompute"):
                self.state_manager.request_fov_recompute()
            
            # Continue pathfinding or end turn
            if result.get("continue_pathfinding"):
                # Continue with enemy turn (which will cycle back to player)
                self.state_manager.set_game_state(GameStates.ENEMY_TURN)
            else:
                # Pathfinding completed or interrupted, stay in player turn
                self.state_manager.set_game_state(GameStates.PLAYERS_TURN)
    
    def _handle_right_click(self, _) -> None:
        """Handle right mouse click (usually cancels targeting)."""
        current_state = self.state_manager.state.current_state
        
        if current_state == GameStates.TARGETING:
            previous_state = self.state_manager.get_extra_data("previous_state", GameStates.PLAYERS_TURN)
            self.state_manager.set_game_state(previous_state)
            self.state_manager.set_extra_data("targeting_item", None)
            self.state_manager.set_extra_data("previous_state", None)
        elif current_state == GameStates.PLAYERS_TURN:
            # Right click during player turn cancels pathfinding
            player = self.state_manager.state.player
            if (hasattr(player, 'pathfinding') and player.pathfinding and 
                player.pathfinding.is_path_active()):
                player.pathfinding.cancel_movement()
                message_log = self.state_manager.state.message_log
                if message_log:
                    from game_messages import Message
                    message_log.add_message(Message("Movement cancelled.", (255, 255, 0)))
    
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
