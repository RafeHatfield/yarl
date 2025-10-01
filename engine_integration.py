"""Integration layer between the new engine architecture and existing game systems.

This module provides functions to bridge the gap between the new GameEngine
architecture and the existing game loop, allowing for gradual migration.
"""

import tcod.libtcodpy as libtcod

from engine import GameEngine
from engine.systems import RenderSystem, InputSystem, AISystem, PerformanceSystem
from engine.systems.optimized_render_system import OptimizedRenderSystem
from fov_functions import initialize_fov
from game_actions import ActionProcessor
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
    # Create the engine with configurable FPS
    from config.game_constants import get_performance_config
    perf_config = get_performance_config()
    engine = GameEngine(target_fps=perf_config.TARGET_FPS)

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
    
    # Create action processor for clean action handling
    action_processor = ActionProcessor(engine.state_manager)

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
            # LOG: Track why game is exiting
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"=== GAME EXIT TRIGGERED ===")
            logger.warning(f"Action: {action}")
            logger.warning(f"Mouse action: {mouse_action}")
            logger.warning(f"Current state: {engine.state_manager.state.current_state}")
            logger.warning(f"Exit action in actions: {action.get('exit', False)}")
            logger.warning(f"========================")
            
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
                logger.error(f"Save failed: {e}")
            break

        # Use the new action processor for clean, modular action handling
        action_processor.process_actions(action, mouse_action)

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
    import logging
    logger = logging.getLogger(__name__)
    
    exit_action = action.get("exit")
    fullscreen = action.get("fullscreen")

    if fullscreen:
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
        return False

    if exit_action:
        logger.debug(f"Exit action detected in state {current_state}")
        
        if current_state in (
            GameStates.SHOW_INVENTORY,
            GameStates.DROP_INVENTORY,
            GameStates.CHARACTER_SCREEN,
            GameStates.LEVEL_UP,
        ):
            # Exit menu, don't exit game
            logger.debug(f"Exit from menu state {current_state} - closing menu, not exiting game")
            return False
        elif current_state == GameStates.TARGETING:
            # Exit targeting mode
            logger.debug("Exit from targeting - closing targeting, not exiting game")
            return False
        else:
            # Exit game
            logger.warning(f"EXIT GAME triggered from state {current_state}")
            return True

    return False


# DEPRECATED: Compatibility wrapper for tests that still use the old function signature
# TODO: Update all tests to use ActionProcessor directly and remove this wrapper
def _process_game_actions(action, mouse_action, state_manager, targeting_item=None, previous_game_state=None, constants=None):
    """DEPRECATED: Compatibility wrapper for the old _process_game_actions function.
    
    This function maintains backward compatibility with existing tests while
    using the new ActionProcessor internally. The legacy parameters are kept
    for compatibility but are no longer used.
    
    Args:
        action (dict): Keyboard action dictionary
        mouse_action (dict): Mouse action dictionary  
        state_manager (GameStateManager): Game state manager instance
        targeting_item (optional): DEPRECATED - Legacy parameter, no longer used
        previous_game_state (optional): DEPRECATED - Legacy parameter, no longer used
        constants (optional): DEPRECATED - Legacy parameter, no longer used
        
    Deprecated:
        This wrapper exists to maintain compatibility with existing tests.
        New code should use ActionProcessor directly. This will be removed
        in a future version once all tests are updated.
    """
    from game_actions import ActionProcessor
    
    # Create a temporary action processor for this call
    action_processor = ActionProcessor(state_manager)
    action_processor.process_actions(action, mouse_action)
