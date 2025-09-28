"""Integration layer between the new engine architecture and existing game systems.

This module provides functions to bridge the gap between the new GameEngine
architecture and the existing game loop, allowing for gradual migration.
"""

import tcod.libtcodpy as libtcod

from engine import GameEngine
from engine.systems import RenderSystem, InputSystem, AISystem, PerformanceSystem
from engine.systems.optimized_render_system import OptimizedRenderSystem
from fov_functions import initialize_fov
from game_messages import Message
from game_states import GameStates
from input_handlers import handle_keys, handle_mouse
from loader_functions.data_loaders import save_game


def create_game_engine(constants, con, panel):
    """Create and configure a GameEngine with all necessary systems.

    Args:
        constants (dict): Game configuration constants
        con: Main game console
        panel: UI panel console

    Returns:
        GameEngine: Configured game engine ready to run
    """
    # Create the engine
    engine = GameEngine(target_fps=60)  # Could be configurable

    # Create and register the performance system (very early priority)
    performance_system = PerformanceSystem(priority=5)
    engine.register_system(performance_system)

    # Create and register the input system (early priority)
    input_system = InputSystem(priority=10)
    engine.register_system(input_system)

    # Create and register the AI system (middle priority)
    ai_system = AISystem(priority=50)
    engine.register_system(ai_system)

    # Create and register the optimized render system (late priority)
    render_system = OptimizedRenderSystem(
        console=con,
        panel=panel,
        screen_width=constants["screen_width"],
        screen_height=constants["screen_height"],
        colors=constants["colors"],
        priority=100,  # Render last
        use_optimizations=False,  # DISABLE optimizations for debugging
    )
    engine.register_system(render_system)

    return engine


def initialize_game_engine(
    engine, player, entities, game_map, message_log, game_state, constants
):
    """Initialize the game engine with game state.

    Args:
        engine (GameEngine): The game engine to initialize
        player: Player entity
        entities: List of all entities
        game_map: Game map
        message_log: Message log
        game_state: Initial game state
        constants: Game configuration constants
    """
    # Initialize the game state manager
    engine.state_manager.initialize_game(
        player=player,
        entities=entities,
        game_map=game_map,
        message_log=message_log,
        game_state=game_state,
        constants=constants,
    )

    # Initialize FOV
    fov_map = initialize_fov(game_map)
    engine.state_manager.set_fov_data(fov_map, fov_recompute=True)

    # Set up the render system's FOV map
    render_system = engine.get_system("render")
    if render_system:
        render_system.set_fov_map(fov_map)


def play_game_with_engine(
    player, entities, game_map, message_log, game_state, con, panel, constants
):
    """Play the game using the new engine architecture.

    This function replaces the original play_game function and demonstrates
    how the new engine integrates with the existing game systems.

    Args:
        player: Player entity
        entities: List of all entities
        game_map: Game map
        message_log: Message log
        game_state: Initial game state
        con: Main game console
        panel: UI panel console
        constants: Game configuration constants
    """
    # Create and initialize the engine
    engine = create_game_engine(constants, con, panel)
    initialize_game_engine(
        engine, player, entities, game_map, message_log, game_state, constants
    )

    # Input objects
    key = libtcod.Key()
    mouse = libtcod.Mouse()

    # Game state tracking
    previous_game_state = game_state
    targeting_item = None
    first_frame = True

    # Main game loop
    while not libtcod.console_is_window_closed():
        # Handle input
        libtcod.sys_check_for_event(
            libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse
        )

        # Update input objects in state manager
        engine.state_manager.set_input_objects(key, mouse)

        # Clear console
        libtcod.console_clear(con)

        # Ensure FOV is recomputed on first frame
        if first_frame:
            engine.state_manager.request_fov_recompute()
            first_frame = False

        # Get actions from the input system BEFORE updating other systems
        # This ensures we process actions in the correct state
        input_systems = [s for s in engine.systems if isinstance(s, InputSystem)]
        if input_systems:
            input_systems[0].update(0.016)  # Update input system first
        
        action = engine.state_manager.get_extra_data("keyboard_actions", {})
        mouse_action = engine.state_manager.get_extra_data("mouse_actions", {})
        

        # Process actions BEFORE AI system runs
        # This prevents zombie actions after death
        if _should_exit_game(
            action, mouse_action, engine.state_manager.state.current_state
        ):
            # Save game before exiting
            try:
                game_state_data = engine.state_manager.state
                save_game(
                    game_state_data.player,
                    game_state_data.entities,
                    game_state_data.game_map,
                    game_state_data.message_log,
                    game_state_data.current_state
                )
                print("Game saved successfully!")
            except Exception as e:
                print(f"Failed to save game: {e}")
            break

        _process_game_actions(
            action,
            mouse_action,
            engine.state_manager,
            targeting_item,
            previous_game_state,
            constants,
        )

        # Update all systems (AI will run after player actions are processed)
        engine.update()

        # IMPORTANT: Reset FOV flag AFTER rendering is complete
        # This ensures the flag stays active for the entire frame
        if engine.state_manager.state.fov_recompute:
            engine.state_manager.state.fov_recompute = False

    # Clean up
    engine.stop()


def _should_exit_game(action, mouse_action, current_state):
    """Check if the game should exit.

    Args:
        action: Keyboard action
        mouse_action: Mouse action
        current_state: Current game state

    Returns:
        bool: True if game should exit
    """
    exit_action = action.get("exit")
    fullscreen = action.get("fullscreen")

    if fullscreen:
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
        return False

    if exit_action:
        if current_state in (
            GameStates.SHOW_INVENTORY,
            GameStates.DROP_INVENTORY,
            GameStates.CHARACTER_SCREEN,
            GameStates.LEVEL_UP,
        ):
            # Exit menu, don't exit game
            return False
        elif current_state == GameStates.TARGETING:
            # Exit targeting mode
            return False
        else:
            # Exit game
            return True

    return False


def _process_game_actions(
    action, mouse_action, state_manager, targeting_item, previous_game_state, constants
):
    """Process game actions and update state.

    This is a placeholder that maintains the existing game logic structure
    while we gradually migrate to the new system architecture.

    Args:
        action: Keyboard action
        mouse_action: Mouse action
        state_manager: Game state manager
        targeting_item: Currently targeted item
        previous_game_state: Previous game state
        constants: Game configuration constants
    """
    # CRITICAL: Don't process any game actions if player is dead
    current_state = state_manager.state.current_state
    if current_state == GameStates.PLAYER_DEAD:
        return  # Player is dead, no actions allowed except exit (handled elsewhere)
    
    # For now, this is a simplified version that just handles basic state changes
    # The full game logic would be migrated to dedicated systems over time

    # Handle state transitions
    if action.get("show_inventory"):
        state_manager.set_game_state(GameStates.SHOW_INVENTORY)
    elif action.get("drop_inventory"):
        state_manager.set_game_state(GameStates.DROP_INVENTORY)
    elif action.get("show_character_screen"):
        state_manager.set_game_state(GameStates.CHARACTER_SCREEN)
    elif action.get("exit"):
        if current_state in (
            GameStates.SHOW_INVENTORY,
            GameStates.DROP_INVENTORY,
            GameStates.CHARACTER_SCREEN,
            GameStates.LEVEL_UP,
        ):
            state_manager.set_game_state(GameStates.PLAYERS_TURN)
        elif current_state == GameStates.TARGETING:
            previous_state = state_manager.get_extra_data("previous_state", GameStates.PLAYERS_TURN)
            state_manager.set_game_state(previous_state)
            state_manager.set_extra_data("targeting_item", None)
            state_manager.set_extra_data("previous_state", None)

    # Handle movement and other actions
    move = action.get("move")
    if move and current_state == GameStates.PLAYERS_TURN:
        # Validate move input
        if not isinstance(move, (tuple, list)) or len(move) != 2:
            return  # Invalid move input, ignore
        
        dx, dy = move
        player = state_manager.state.player

        # Simple movement (full logic would be in a MovementSystem)
        if player:
            destination_x = player.x + dx
            destination_y = player.y + dy

            game_map = state_manager.state.game_map
            if game_map and not game_map.is_blocked(destination_x, destination_y):
                # Check for blocking entities
                from entity import get_blocking_entities_at_location

                target = get_blocking_entities_at_location(
                    state_manager.state.entities, destination_x, destination_y
                )

                if target:
                    # Combat would be handled by a CombatSystem
                    if player.fighter and target.fighter:
                        attack_results = player.fighter.attack(target)
                        
                        # Process attack results (messages, death, etc.)
                        for result in attack_results:
                            message = result.get("message")
                            if message:
                                state_manager.state.message_log.add_message(message)
                            
                            dead_entity = result.get("dead")
                            if dead_entity:
                                if dead_entity == player:
                                    # Player died - transition to death state
                                    state_manager.set_game_state(GameStates.PLAYER_DEAD)
                                    
                                    # Add player death message
                                    death_message = Message(
                                        "You died! Press any key to return to the main menu.",
                                        (255, 30, 30)
                                    )
                                    state_manager.state.message_log.add_message(death_message)
                                else:
                                    # Monster died - remove from entities and request FOV recompute
                                    if dead_entity in state_manager.state.entities:
                                        state_manager.state.entities.remove(dead_entity)
                                    state_manager.request_fov_recompute()
                                    
                                    # Add death message
                                    death_message = Message(
                                        f"{dead_entity.name.capitalize()} is dead!",
                                        (255, 30, 30)
                                    )
                                    state_manager.state.message_log.add_message(death_message)
                else:
                    # Move player
                    player.move(dx, dy)
                    state_manager.request_fov_recompute()

                # Switch to enemy turn
                state_manager.set_game_state(GameStates.ENEMY_TURN)

    # Handle wait action
    wait = action.get("wait")
    if wait and current_state == GameStates.PLAYERS_TURN:
        # Player waits (skips turn)
        state_manager.set_game_state(GameStates.ENEMY_TURN)

    # Handle item pickup
    pickup = action.get("pickup")
    if pickup and current_state == GameStates.PLAYERS_TURN:
        player = state_manager.state.player
        entities = state_manager.state.entities
        message_log = state_manager.state.message_log
        
        # Validate required objects exist
        if not (player and entities is not None and message_log):
            return
        
        # Look for items at player's position
        for entity in entities:
            if entity.item and entity.x == player.x and entity.y == player.y:
                # Validate player has inventory
                if not player.inventory:
                    message = Message("You cannot carry items.", (255, 255, 0))
                    message_log.add_message(message)
                    break
                
                # Try to pick up the item
                pickup_results = player.inventory.add_item(entity)
                
                # Process pickup results
                for result in pickup_results:
                    message = result.get("message")
                    if message:
                        message_log.add_message(message)
                    
                    item_added = result.get("item_added")
                    if item_added:
                        # Remove item from the map
                        entities.remove(entity)
                
                break
        else:
            # No item found at player position
            message = Message("There is nothing here to pick up.", (255, 255, 0))
            message_log.add_message(message)

    # Handle inventory item usage
    inventory_index = action.get("inventory_index")
    if inventory_index is not None and current_state == GameStates.SHOW_INVENTORY:
        player = state_manager.state.player
        
        if player and player.inventory and 0 <= inventory_index < len(player.inventory.items):
            item = player.inventory.items[inventory_index]
            
            if item.item:
                # Use the item - pass all necessary parameters including fov_map
                item_use_results = player.inventory.use(
                    item, 
                    entities=state_manager.state.entities,
                    fov_map=state_manager.state.fov_map
                )
                
                # Process item use results
                for result in item_use_results:
                    message = result.get("message")
                    if message:
                        state_manager.state.message_log.add_message(message)
                    
                    # Handle death results (critical for lightning scroll, etc.)
                    dead_entity = result.get("dead")
                    if dead_entity:
                        if dead_entity == player:
                            # Player died - transition to death state
                            state_manager.set_game_state(GameStates.PLAYER_DEAD)
                            
                            # Add player death message
                            death_message = Message(
                                "You died! Press any key to return to the main menu.",
                                (255, 30, 30)
                            )
                            state_manager.state.message_log.add_message(death_message)
                        else:
                            # Monster died - remove from entities and transform to corpse
                            if dead_entity in state_manager.state.entities:
                                # Import death function
                                from death_functions import kill_monster
                                
                                # Transform monster to corpse
                                death_message = kill_monster(dead_entity)
                                state_manager.state.message_log.add_message(death_message)
                                
                                # Request FOV recompute since entities changed
                                state_manager.request_fov_recompute()
                    
                    # Handle item consumption (already handled by inventory.use())
                    # The inventory.use() method already removes consumed items
                    
                    # Handle targeting
                    targeting = result.get("targeting")
                    if targeting:
                        state_manager.set_game_state(GameStates.TARGETING)
                        # Store targeting item and previous state
                        state_manager.set_extra_data("targeting_item", item)
                        state_manager.set_extra_data("previous_state", GameStates.SHOW_INVENTORY)
                    
                    # Handle equipment
                    equip = result.get("equip")
                    if equip and player.equipment:
                        # Equip the item
                        equip_results = player.equipment.toggle_equip(equip)
                        
                        # Process equipment results
                        for equip_result in equip_results:
                            equipped = equip_result.get("equipped")
                            dequipped = equip_result.get("dequipped")
                            
                            if equipped:
                                state_manager.state.message_log.add_message(
                                    Message(f"You equip the {equipped.name}.", (0, 255, 0))
                                )
                            elif dequipped:
                                state_manager.state.message_log.add_message(
                                    Message(f"You unequip the {dequipped.name}.", (255, 255, 0))
                                )
                
                # If no targeting, return to player turn
                if not any(result.get("targeting") for result in item_use_results):
                    state_manager.set_game_state(GameStates.PLAYERS_TURN)

    # Handle inventory item dropping
    elif inventory_index is not None and current_state == GameStates.DROP_INVENTORY:
        player = state_manager.state.player
        
        if player and player.inventory and 0 <= inventory_index < len(player.inventory.items):
            item = player.inventory.items[inventory_index]
            
            # Drop the item
            drop_results = player.inventory.drop_item(item)
            
            # Process drop results
            for result in drop_results:
                message = result.get("message")
                if message:
                    state_manager.state.message_log.add_message(message)
                
                # Place item on map at player position
                item_dropped = result.get("item_dropped")
                if item_dropped:
                    item_dropped.x = player.x
                    item_dropped.y = player.y
                    state_manager.state.entities.append(item_dropped)
            
            # Return to player turn
            state_manager.set_game_state(GameStates.PLAYERS_TURN)

    # Handle stairs
    take_stairs = action.get("take_stairs")
    if take_stairs and current_state == GameStates.PLAYERS_TURN:
        # Check if player is on stairs
        player = state_manager.state.player
        entities = state_manager.state.entities
        game_map = state_manager.state.game_map
        message_log = state_manager.state.message_log
        
        # Validate required objects exist
        if not (player and entities is not None and game_map and message_log):
            return
        
        for entity in entities:
            if hasattr(entity, 'stairs') and entity.stairs and entity.x == player.x and entity.y == player.y:
                # Generate next floor
                new_entities = game_map.next_floor(player, message_log, constants)
                
                # Update game state with new floor
                state_manager.update_state(entities=new_entities)
                
                # Initialize new FOV map for the new level
                from fov_functions import initialize_fov
                new_fov_map = initialize_fov(game_map)
                state_manager.update_state(fov_map=new_fov_map)
                
                # Request FOV recompute for new level
                state_manager.request_fov_recompute()
                
                # The render system will get the new FOV map from game state
                # and will reinitialize when it detects the map change
                
                break
        else:
            message = Message("There are no stairs here.", (255, 255, 0))
            message_log.add_message(message)

    # Handle targeting system
    if current_state == GameStates.TARGETING:
        # Handle mouse clicks for target selection
        left_click = mouse_action.get("left_click")
        right_click = mouse_action.get("right_click")
        
        if left_click:
            target_x, target_y = left_click
            
            # Get the targeting item from state manager
            targeting_item = state_manager.get_extra_data("targeting_item")
            if targeting_item and targeting_item.item:
                # Use the item with target coordinates
                player = state_manager.state.player
                if player and player.inventory:
                    item_use_results = player.inventory.use(
                        targeting_item, 
                        entities=state_manager.state.entities,
                        fov_map=state_manager.state.fov_map,
                        target_x=target_x,
                        target_y=target_y
                    )
                    
                    # Process item use results
                    for result in item_use_results:
                        message = result.get("message")
                        if message:
                            state_manager.state.message_log.add_message(message)
                        
                        # Handle death results (critical for fireball, lightning, etc.)
                        dead_entity = result.get("dead")
                        if dead_entity:
                            if dead_entity == player:
                                # Player died - transition to death state
                                state_manager.set_game_state(GameStates.PLAYER_DEAD)
                                
                                # Add player death message
                                death_message = Message(
                                    "You died! Press any key to return to the main menu.",
                                    (255, 30, 30)
                                )
                                state_manager.state.message_log.add_message(death_message)
                            else:
                                # Monster died - remove from entities and transform to corpse
                                if dead_entity in state_manager.state.entities:
                                    # Import death function
                                    from death_functions import kill_monster
                                    
                                    # Transform monster to corpse
                                    death_message = kill_monster(dead_entity)
                                    state_manager.state.message_log.add_message(death_message)
                                    
                                    # Request FOV recompute since entities changed
                                    state_manager.request_fov_recompute()
                    
                    # After successful targeting, return to player turn (game map)
                    state_manager.set_game_state(GameStates.PLAYERS_TURN)
                    state_manager.set_extra_data("targeting_item", None)
                    state_manager.set_extra_data("previous_state", None)
        
        elif right_click:
            # Cancel targeting
            previous_state = state_manager.get_extra_data("previous_state", GameStates.PLAYERS_TURN)
            state_manager.set_game_state(previous_state)
            state_manager.set_extra_data("targeting_item", None)

    # Enemy turns are now handled by the AISystem automatically
