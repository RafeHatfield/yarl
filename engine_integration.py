"""Integration layer between the new engine architecture and existing game systems.

This module provides functions to bridge the gap between the new GameEngine
architecture and the existing game loop, allowing for gradual migration.
"""

import logging
from contextlib import contextmanager

import tcod.libtcodpy as libtcod
from contextlib import contextmanager

from engine import GameEngine

logger = logging.getLogger(__name__)


from engine.systems import (
    RenderSystem,
    InputSystem,
    AISystem,
    PerformanceSystem,
    EnvironmentSystem,
)
from engine.systems.optimized_render_system import OptimizedRenderSystem
from fov_functions import initialize_fov
from game_actions import ActionProcessor
from game_messages import Message
from game_states import GameStates
from input_handlers import handle_keys, handle_mouse
from loader_functions.data_loaders import save_game


@contextmanager
def _manual_input_system_update(engine: GameEngine, dt: float):
    """Run the input system manually while pausing automatic updates.

    Older regression tests expect to control the input system directly to
    verify same-frame input availability. This context manager temporarily
    disables the engine-driven update cycle, invokes the input system once,
    and then restores its previous enabled state.

    Args:
        engine: The engine instance containing the input system.
        dt: Delta time to pass into the manual update.
    """

    input_systems = engine.get_systems_by_type(InputSystem)
    if not input_systems:
        raise RuntimeError("No InputSystem registered with engine")

    input_system = input_systems[0]
    was_enabled = input_system.enabled

    # Prevent the engine from updating the system a second time while we are
    # inside the context.
    input_system.disable()
    try:
        input_system.update(dt)
        yield
    finally:
        input_system.enabled = was_enabled


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

    # Create and register the environment system (after AI processing)
    environment_system = EnvironmentSystem(priority=60)
    engine.register_system(environment_system)

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
    engine.state_manager.update_state(camera=camera, death_screen_quote=None)

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
    # Create and initialize the engine with 3-console layout
    engine = create_game_engine(constants, sidebar_console, viewport_console, status_console)

    # Legacy aliases for compatibility during transition
    con = viewport_console
    panel = status_console
    
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

    # Persist the action processor for systems that need to reuse it between phases
    engine.state_manager.set_extra_data("action_processor", action_processor)

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
            # Show confrontation choice screen with full Phase 5 menu system
            from screens.confrontation_choice import confrontation_menu
            from victory_manager import get_victory_manager
            
            player = engine.state_manager.state.player
            choice, new_state = confrontation_menu(
                con, 0,  # 0 is the root console in libtcod
                constants['screen_width'], constants['screen_height'],
                player  # Pass player to check knowledge flags
            )
            
            if choice is None:
                # Player pressed ESC - exit confrontation and return to normal gameplay
                engine.state_manager.set_game_state(GameStates.PLAYERS_TURN)
                continue
            elif choice:
                # Check if this ending requires a boss fight
                boss_fights = {
                    '1a': 'zhyraxion_human',        # Human Zhyraxion (Medium-Hard)
                    '3': 'zhyraxion_full_dragon',   # Full Dragon (EXTREME)
                    '4': 'zhyraxion_grief_dragon'   # Grief Dragon (Hard)
                }
                
                if choice in boss_fights:
                    # Spawn boss and transition to combat
                    from config.entity_factory import get_entity_factory
                    entity_factory = get_entity_factory()
                    
                    # Get player position and spawn boss nearby
                    player = engine.state_manager.state.player
                    entities = engine.state_manager.state.entities
                    game_map = engine.state_manager.state.game_map
                    message_log = engine.state_manager.state.message_log
                    
                    # Find a valid spawn location near player (not in walls!)
                    # Try tiles in expanding radius: adjacent first, then 2 tiles away, etc.
                    from entity import get_blocking_entities_at_location
                    boss_x, boss_y = None, None
                    
                    # Directions to try (cardinal + diagonal)
                    directions = [
                        (1, 0), (-1, 0), (0, 1), (0, -1),  # Cardinal
                        (1, 1), (-1, 1), (1, -1), (-1, -1),  # Diagonal
                        (2, 0), (-2, 0), (0, 2), (0, -2),  # 2 tiles away
                        (2, 1), (-2, 1), (2, -1), (-2, -1),  # 2 tiles + 1
                        (1, 2), (-1, 2), (1, -2), (-1, -2),
                        (3, 0), (-3, 0), (0, 3), (0, -3),  # 3 tiles away
                    ]
                    
                    for dx, dy in directions:
                        test_x = player.x + dx
                        test_y = player.y + dy
                        
                        # Check bounds
                        if not (0 <= test_x < game_map.width and 0 <= test_y < game_map.height):
                            continue
                        
                        # Check if tile is walkable
                        if game_map.is_blocked(test_x, test_y):
                            continue
                        
                        # Check if no entity blocking
                        if get_blocking_entities_at_location(entities, test_x, test_y):
                            continue
                        
                        # Found a valid spot!
                        boss_x, boss_y = test_x, test_y
                        break
                    
                    # Fallback: spawn on player if no valid location found (shouldn't happen)
                    if boss_x is None:
                        logger.warning("No valid boss spawn location found, spawning on player!")
                        boss_x, boss_y = player.x, player.y
                    
                    logger.info(f"Boss spawn location: ({boss_x}, {boss_y}), player at ({player.x}, {player.y})")
                    print(f">>> BOSS SPAWN: Location ({boss_x}, {boss_y}), player at ({player.x}, {player.y})")
                    
                    # Create the appropriate boss (bosses are monsters, not items!)
                    from message_builder import MessageBuilder as MB
                    boss = entity_factory.create_monster(boss_fights[choice], boss_x, boss_y)
                    if boss:
                        entities.append(boss)
                        message_log.add_message(MB.warning(f"{boss.name} appears!"))
                        logger.info(f"=== CONFRONTATION: Boss spawned: {boss.name} at ({boss_x}, {boss_y}) for ending {choice} ===")
                        print(f">>> BOSS SPAWNED: {boss.name} for ending {choice}")
                        
                        # Store which ending this boss fight is for
                        engine.state_manager.set_extra_data("pending_ending", choice)
                        
                        # Transition to combat
                        engine.state_manager.set_game_state(GameStates.PLAYERS_TURN)
                        engine.state_manager.request_fov_recompute()
                        
                        # Continue game loop for combat
                        continue
                    else:
                        # Boss failed to spawn - critical error!
                        logger.error(f"=== CONFRONTATION: FAILED to spawn boss '{boss_fights[choice]}' for ending {choice} ===")
                        print(f">>> ERROR: Boss '{boss_fights[choice]}' failed to spawn!")
                        message_log.add_message(MB.failure(f"ERROR: Boss failed to spawn!"))
                
                # No boss fight needed - show ending screen immediately
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
                
                # Record victory in Hall of Fame for victory endings
                # Phase 5 endings: '1a', '1b', '5' are victories; '2' is failure; '3', '4' may vary
                if choice in ('1a', '1b', '5', 'good'):
                    hall = get_hall_of_fame()
                    player_name = engine.state_manager.state.player.name
                    hall.add_victory(player_name, choice, player_stats)
                
                if result == 'restart':
                    engine.stop()
                    return {"restart": True}
                elif result == 'quit':
                    break
        
        # Phase 5: Handle post-boss victory (show ending screen)
        elif current_state == GameStates.VICTORY:
            ending_code = engine.state_manager.get_extra_data("show_ending")
            if ending_code:
                from victory_manager import get_victory_manager
                from screens.victory_screen import show_ending_screen
                from systems.hall_of_fame import get_hall_of_fame
                
                victory_mgr = get_victory_manager()
                player_stats = victory_mgr.get_player_stats_for_ending(
                    engine.state_manager.state.player,
                    engine.state_manager.state.game_map
                )
                
                result = show_ending_screen(
                    con, 0,
                    constants['screen_width'], constants['screen_height'],
                    ending_code, player_stats
                )
                
                # Record in Hall of Fame (all endings are valid victories)
                hall = get_hall_of_fame()
                player_name = engine.state_manager.state.player.name
                hall.add_victory(player_name, ending_code, player_stats)
                
                # Clear the flag
                engine.state_manager.set_extra_data("show_ending", None)
                
                if result == 'restart':
                    engine.stop()
                    return {"restart": True}
                elif result == 'quit':
                    break
        
        # Phase 3: Handle NPC Dialogue
        elif current_state == GameStates.NPC_DIALOGUE:
            from screens.npc_dialogue_screen import show_npc_dialogue_screen
            
            # Get the NPC we're talking to
            npc = getattr(engine.state_manager.state, 'current_dialogue_npc', None)
            if npc:
                # Show dialogue screen (it handles its own loop)
                new_state = show_npc_dialogue_screen(npc, engine.state_manager)
                engine.state_manager.set_game_state(new_state)
                
                # Clean up
                engine.state_manager.state.current_dialogue_npc = None
            else:
                # No NPC found, exit dialogue
                engine.state_manager.set_game_state(GameStates.PLAYERS_TURN)
        
        # Tier 2: Handle Wizard Mode Debug Menu
        elif current_state == GameStates.WIZARD_MENU:
            from screens.wizard_menu import show_wizard_menu
            
            # Show wizard menu (it handles its own loop)
            new_state = show_wizard_menu(con, engine.state_manager)
            engine.state_manager.set_game_state(new_state)
        
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


@contextmanager
def _manual_input_system_update(engine, delta_time):
    """Context manager to manually update the input system.
    
    This helper temporarily disables normal input system scheduling and forces
    a single manual update pass within the context. Useful for testing input
    behavior with controlled timing.
    
    Args:
        engine (GameEngine): The game engine instance
        delta_time (float): Time delta to pass to the input system update
        
    Yields:
        None: Context is ready for code execution
        
    Example:
        with _manual_input_system_update(engine, 0.016):
            actions = engine.state_manager.get_extra_data("keyboard_actions")
            # Test the actions
    """
    # Find the input system in the engine
    input_systems = [s for s in engine.systems if isinstance(s, InputSystem)]
    if not input_systems:
        # No input system found, just yield without doing anything
        yield
        return
    
    input_system = input_systems[0]
    was_enabled = input_system.enabled
    
    try:
        # Force enable and manually update the input system
        input_system.enabled = True
        input_system.update(delta_time)
        actions = engine.state_manager.get_extra_data("keyboard_actions", {})
        if "stale" in actions:
            actions.pop("stale", None)
            engine.state_manager.set_extra_data("keyboard_actions", actions)
        yield
    finally:
        # Restore previous enabled state
        input_system.enabled = was_enabled


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
            GameStates.NPC_DIALOGUE,  # Phase 3: Exit dialogue menu
            GameStates.WIZARD_MENU,   # Tier 2: Exit wizard menu
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
