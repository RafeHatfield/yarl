"""Integration layer between the new engine architecture and existing game systems.

This module provides functions to bridge the gap between the new GameEngine
architecture and the existing game loop, allowing for gradual migration.
"""

import tcod.libtcodpy as libtcod

from engine import GameEngine
from engine.systems import RenderSystem
from fov_functions import initialize_fov
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

    # Create and register the render system
    render_system = RenderSystem(
        console=con,
        panel=panel,
        screen_width=constants["screen_width"],
        screen_height=constants["screen_height"],
        colors=constants["colors"],
        priority=100,  # Render last
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

        # Update all systems (including rendering)
        engine.update()

        # Handle input actions (this part still uses the old system for now)
        action = handle_keys(key, engine.state_manager.state.current_state)
        mouse_action = handle_mouse(mouse)

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
                        player.fighter.attack(target)
                        if target.fighter.hp <= 0:
                            state_manager.request_fov_recompute()
                else:
                    # Move player
                    player.move(dx, dy)
                    state_manager.request_fov_recompute()

                # Switch to enemy turn
                state_manager.set_game_state(GameStates.ENEMY_TURN)

    # Handle enemy turns (would eventually be an AISystem)
    if current_state == GameStates.ENEMY_TURN:
        _process_enemy_turns(state_manager)
        state_manager.set_game_state(GameStates.PLAYERS_TURN)


def _process_enemy_turns(state_manager):
    """Process enemy AI turns.

    This is a simplified version that would eventually be replaced
    by a dedicated AISystem.

    Args:
        state_manager: Game state manager
    """
    player = state_manager.state.player
    entities = state_manager.state.entities
    game_map = state_manager.state.game_map

    for entity in entities:
        if entity.ai and entity != player:
            if entity.fighter and entity.fighter.hp > 0:
                # Simple AI processing (would be in AISystem)
                entity.ai.take_turn(player, game_map, entities)

                if entity.fighter.hp <= 0:
                    state_manager.request_fov_recompute()
