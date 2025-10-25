"""Integration layer between the new engine architecture and existing game systems.

This module provides functions to bridge the gap between the new GameEngine
architecture and the existing game loop, allowing for gradual migration.
"""

import logging
import tcod.libtcodpy as libtcod

from engine import GameEngine

logger = logging.getLogger(__name__)


# Global reference to current state manager for accessing from render functions
_current_state_manager = None


def get_current_state_manager():
    """Get the current state manager instance.
    
    Returns:
        StateManager: The current state manager, or None if not set
    """
    return _current_state_manager
from engine.systems import RenderSystem, InputSystem, AISystem, PerformanceSystem
from engine.systems.optimized_render_system import OptimizedRenderSystem
from fov_functions import initialize_fov
from game_actions import ActionProcessor
from game_messages import Message
from game_states import GameStates
from input_handlers import handle_keys, handle_mouse
from loader_functions.data_loaders import save_game


def create_game_engine(constants, sidebar_console, viewport_console, status_console):
    """Create and configure a GameEngine with all necessary systems.

    Args:
        constants (dict): Game configuration constants
        sidebar_console: Left sidebar console (full height)
        viewport_console: Main viewport console (map view)
        status_console: Status panel console (HP, messages)

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
    # Pass all 3 consoles for split-screen layout
    render_system = OptimizedRenderSystem(
        console=viewport_console,  # Main viewport (legacy 'con')
        panel=status_console,       # Status panel (legacy 'panel')
        sidebar_console=sidebar_console,  # NEW: Sidebar console
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
    
    # Initialize Camera (Phase 2)
    from rendering.camera import Camera, CameraMode
    from config.ui_layout import get_ui_layout
    ui_layout = get_ui_layout()
    
    camera = Camera(
        viewport_width=ui_layout.viewport_width,
        viewport_height=ui_layout.viewport_height,
        map_width=game_map.width,
        map_height=game_map.height,
        mode=CameraMode.CENTER,  # Player is always centered
    )
    
    # Center camera on player initially
    camera.center_on(player.x, player.y)
    
    # Store camera in game state
    engine.state_manager.update_state(camera=camera)

    # Set up the render system's FOV map
    render_system = engine.get_system("render")
    if render_system:
        render_system.set_fov_map(fov_map)


def play_game_with_engine(
    player, entities, game_map, message_log, game_state, 
    sidebar_console, viewport_console, status_console, constants
):
    """Play the game using the new engine architecture with 3-console layout.

    This function replaces the original play_game function and demonstrates
    how the new engine integrates with the existing game systems.

    Args:
        player: Player entity
        entities: List of all entities
        game_map: Game map
        message_log: Message log
        game_state: Initial game state
        sidebar_console: Left sidebar console (full height)
        viewport_console: Main viewport console (map view)
        status_console: Status panel console (HP, messages)
        constants: Game configuration constants
    """
    global _current_state_manager
    
    # Create and initialize the engine with 3-console layout
    engine = create_game_engine(constants, sidebar_console, viewport_console, status_console)
    
    # Legacy aliases for compatibility during transition
    con = viewport_console
    panel = status_console
    
    # Store state manager globally for access from render functions
    _current_state_manager = engine.state_manager
    
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
    action_processor.turn_manager = engine.turn_manager  # Phase 3: Wire up TurnManager
    
    # Reinitialize TurnController with turn_manager now that it's set
    from systems.turn_controller import initialize_turn_controller
    action_processor.turn_controller = initialize_turn_controller(
        engine.state_manager, 
        engine.turn_manager
    )
    logger.info(f"ActionProcessor turn_controller reinitialized with TurnManager: {engine.turn_manager}")

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
        
        # Check for restart action (from death screen)
        if action.get("restart"):
            # Player wants to restart - return to main loop for new game
            engine.stop()
            return {"restart": True}

        # Process actions BEFORE AI system runs
        # This prevents zombie actions after death
        if _should_exit_game(
            action, mouse_action, engine.state_manager.state.current_state
        ):
            # LOG: Track why game is exiting
            logger.warning(f"=== GAME EXIT TRIGGERED ===")
            logger.warning(f"Action: {action}")
            logger.warning(f"Mouse action: {mouse_action}")
            logger.warning(f"Current state: {engine.state_manager.state.current_state}")
            logger.warning(f"Exit action in actions: {action.get('exit', False)}")
            logger.warning(f"========================")
            
            # Save game before exiting (unless player is dead)
            if engine.state_manager.state.current_state != GameStates.PLAYER_DEAD:
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
        
        # Handle victory condition states
        current_state = engine.state_manager.state.current_state
        
        if current_state == GameStates.CONFRONTATION:
            # Show confrontation choice screen
            from screens.confrontation_choice import confrontation_menu
            from victory_manager import get_victory_manager
            
            choice, new_state = confrontation_menu(
                con, 0,  # 0 is the root console in libtcod
                constants['screen_width'], constants['screen_height']
            )
            
            if choice:
                # Player made a choice, show ending screen
                victory_mgr = get_victory_manager()
                player_stats = victory_mgr.get_player_stats_for_ending(
                    engine.state_manager.state.player,
                    engine.state_manager.state.game_map
                )
                
                from screens.victory_screen import show_ending_screen
                from systems.hall_of_fame import get_hall_of_fame
                
                result = show_ending_screen(
                    con, 0,  # 0 is the root console in libtcod
                    constants['screen_width'], constants['screen_height'],
                    choice, player_stats
                )
                
                # Record victory in Hall of Fame if good ending
                if choice == 'good':
                    hall = get_hall_of_fame()
                    player_name = engine.state_manager.state.player.name
                    hall.add_victory(player_name, choice, player_stats)
                
                if result == 'restart':
                    engine.stop()
                    return {"restart": True}
                elif result == 'quit':
                    break
        
        elif current_state in (GameStates.VICTORY, GameStates.FAILURE):
            # These states are handled by confrontation, shouldn't reach here
            # But if we do, treat as game end
            break

        # Update all systems (AI will run after player actions are processed)
        engine.update()

        # IMPORTANT: Reset FOV flag AFTER rendering is complete
        # This ensures the flag stays active for the entire frame
        if engine.state_manager.state.fov_recompute:
            engine.state_manager.state.fov_recompute = False

    # Clean up
    engine.stop()
    
    # Return to main menu (no restart)
    return {"restart": False}


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
        logger.debug(f"Exit action detected in state {current_state}")
        
        if current_state in (
            GameStates.SHOW_INVENTORY,
            GameStates.DROP_INVENTORY,
            GameStates.THROW_SELECT_ITEM,
            GameStates.CHARACTER_SCREEN,
            GameStates.LEVEL_UP,
        ):
            # Exit menu, don't exit game
            logger.debug(f"Exit from menu state {current_state} - closing menu, not exiting game")
            return False
        elif current_state in (GameStates.TARGETING, GameStates.THROW_TARGETING):
            # Exit targeting mode
            logger.debug("Exit from targeting/throw targeting - closing targeting, not exiting game")
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
