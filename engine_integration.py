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
        use_optimizations=True,  # Enable performance optimizations
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

        # Update all systems (including input and rendering)
        engine.update()

        # Get actions from the input system
        action = engine.state_manager.get_extra_data("keyboard_actions", {})
        mouse_action = engine.state_manager.get_extra_data("mouse_actions", {})

        # Process actions (keeping existing logic for now)
        if _should_exit_game(
            action, mouse_action, engine.state_manager.state.current_state
        ):
            break

        # Process game logic (this would eventually become systems too)
        _process_game_actions(
            action,
            mouse_action,
            engine.state_manager,
            targeting_item,
            previous_game_state,
            constants,
        )

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
    # For now, this is a simplified version that just handles basic state changes
    # The full game logic would be migrated to dedicated systems over time

    current_state = state_manager.state.current_state

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
            state_manager.set_game_state(previous_game_state)
            state_manager.set_targeting_item(None)

    # Handle movement and other actions
    move = action.get("move")
    if move and current_state == GameStates.PLAYERS_TURN:
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
                                    # Player died - would handle game over
                                    pass
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

    # Enemy turns are now handled by the AISystem automatically
