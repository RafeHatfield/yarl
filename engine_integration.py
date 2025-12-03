"""Integration layer between the new engine architecture and existing game systems.

This module provides functions to bridge the gap between the new GameEngine
architecture and the existing game loop, allowing for gradual migration.

After the renderer/input abstraction refactoring, the game loop is decoupled
from specific rendering and input technologies through the Renderer and
InputSource protocols defined in io_layer/interfaces.py.

LIBTCOD LIFECYCLE ASSUMPTIONS:
-------------------------------
play_game_with_engine() assumes that the libtcod root console has ALREADY been
initialized by the caller (either engine.py main() or engine/soak_harness.py).

It does NOT initialize libtcod itself. It only:
1. Creates the GameEngine and systems
2. Creates ConsoleRenderer (which wraps existing consoles)
3. Runs the game loop with rendering via ConsoleRenderer.render()

ConsoleRenderer.render() calls libtcod.console_flush(), which REQUIRES a valid
root console. If the root console doesn't exist, flush() will crash with:
"Console must not be NULL or root console must exist."

Callers are responsible for:
- Calling console_set_custom_font() before console_init_root()
- Calling console_init_root() to create the root console
- Creating viewport/sidebar/status consoles with console_new()
- Passing those consoles to play_game_with_engine()

See engine.py and engine/soak_harness.py for examples of proper initialization.
"""

import logging
import time
from contextlib import contextmanager
from typing import Any

import tcod.libtcodpy as libtcod
from engine import GameEngine
from performance.config import get_performance_config
from io_layer.interfaces import Renderer, InputSource, ActionDict
from io_layer.console_renderer import ConsoleRenderer
from io_layer.keyboard_input import KeyboardInputSource
from io_layer.bot_input import BotInputSource
from components.component_registry import ComponentType

logger = logging.getLogger(__name__)


def _log_bot_results_summary(run_metrics, constants: dict) -> None:
    """Log bot run results summary to a dedicated log file.
    
    This function logs a summary after each bot run when running with --bot or --bot-soak.
    It includes floors explored, enemies killed, death cause (or success), turn count,
    and optionally final inventory.
    
    The summary is written to 'bot_results.log' in the project root to avoid timing
    issues with console output and ensure it's always captured.
    
    Args:
        run_metrics: RunMetrics instance with run statistics
        constants: Game constants dict (to check if bot mode is enabled)
    """
    # Check bot mode - try multiple ways to detect it
    bot_enabled = False
    if constants:
        # Method 1: Check input_config.bot_enabled
        input_config = constants.get("input_config", {})
        if isinstance(input_config, dict):
            bot_enabled = input_config.get("bot_enabled", False)
        
        # Method 2: Check bot_soak_mode flag (soak mode always implies bot mode)
        if not bot_enabled:
            bot_enabled = constants.get("bot_soak_mode", False)
    
    # Only log if bot mode is enabled
    if not bot_enabled:
        return
    
    # Determine death cause or success
    outcome_str = run_metrics.outcome
    if outcome_str == "death":
        outcome_str = "Death"
    elif outcome_str == "bot_completed":
        outcome_str = "Completed (all explored)"
    elif outcome_str == "victory":
        outcome_str = "Victory!"
    elif outcome_str == "quit":
        outcome_str = "Quit"
    else:
        outcome_str = outcome_str.capitalize()
    
    # Build summary text
    summary_lines = [
        "",
        "="*60,
        "🤖 Bot Run Results",
        "="*60,
        f"   Outcome: {outcome_str}",
        f"   Floors Explored: {run_metrics.floors_visited}",
        f"   Deepest Floor: {run_metrics.deepest_floor}",
        f"   Enemies Killed: {run_metrics.monsters_killed}",
        f"   Turn Count: {run_metrics.steps_taken}",
        f"   Tiles Explored: {run_metrics.tiles_explored}",
    ]
    if run_metrics.duration_seconds:
        summary_lines.append(f"   Duration: {run_metrics.duration_seconds:.1f}s")
    summary_lines.append("="*60)
    summary_text = "\n".join(summary_lines)
    
    # Write to bot_results.log file
    import os
    log_file_path = os.path.join(os.path.dirname(__file__), "bot_results.log")
    try:
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(summary_text + "\n\n")
        logger.info(f"Bot results summary written to {log_file_path}")
    except Exception as e:
        logger.error(f"Failed to write bot results summary: {e}")
        # Fallback to console if file write fails
        print(summary_text)


def finalize_player_death(state_manager, constants: dict, cause: str = "death") -> None:
    """Finalize player death: metrics, telemetry, and bot summary logging.
    
    This is the canonical place to finalize bot run metrics and write the bot
    results summary when the player dies, regardless of which system detected
    the death (ActionProcessor, AISystem, EnvironmentSystem, etc.).
    
    This function:
    - Sets PLAYER_DEAD game state
    - Adds death message to message log
    - Generates death quote for death screen
    - Ends telemetry for current floor
    - Finalizes run_metrics and stores on game_state
    - Logs bot results summary if bot mode is enabled
    
    Args:
        state_manager: StateManager instance with access to game_state
        constants: Game constants dict (for bot mode detection)
        cause: Optional cause string (e.g., "enemy_attack", "player_action_combat", "hazard")
                Defaults to "death". Used for logging context.
    """
    game_state = state_manager.state
    player = game_state.player
    
    # Set PLAYER_DEAD state
    state_manager.set_game_state(GameStates.PLAYER_DEAD)
    
    # Add death message
    from message_builder import MessageBuilder as MB
    death_message = MB.death(
        "You died! Press any key to return to the main menu."
    )
    game_state.message_log.add_message(death_message)
    
    # Add a frame counter to prevent immediate exit from death screen
    if not hasattr(game_state, 'death_frame_counter'):
        game_state.death_frame_counter = 0
    
    # Generate Entity death quote ONCE (don't regenerate every frame!)
    from components.component_registry import ComponentType
    statistics = player.get_component_optional(ComponentType.STATISTICS)
    if statistics:
        from entity_dialogue import get_entity_quote_for_death
        game_state.death_screen_quote = get_entity_quote_for_death(
            statistics, 
            statistics.deepest_level
        )
    else:
        game_state.death_screen_quote = "How... disappointing."
    
    # Phase 1.5b: End telemetry for current floor on death
    from services.telemetry_service import get_telemetry_service
    telemetry_service = get_telemetry_service()
    if telemetry_service.enabled:
        telemetry_service.end_floor()
        logger.info(f"Telemetry ended for floor on death")
    
    # Finalize run metrics on player death (Phase 1.5: Run Metrics)
    from instrumentation.run_metrics import finalize_run_metrics
    game_map = game_state.game_map
    run_metrics = finalize_run_metrics("death", player, game_map)
    if run_metrics:
        # Store metrics on game state for death screen display and telemetry
        game_state.run_metrics = run_metrics
        logger.info(f"Run metrics finalized on death (cause={cause}): {run_metrics.run_id}")
        
        # Log bot results summary if bot mode is enabled
        bot_enabled = constants.get("input_config", {}).get("bot_enabled", False)
        if not bot_enabled:
            bot_enabled = constants.get("bot_soak_mode", False)
        
        if bot_enabled:
            _log_bot_results_summary(run_metrics, constants)
    else:
        logger.warning(f"Failed to finalize run_metrics on player death (cause={cause})")


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
from config.ui_layout import get_ui_layout
from rendering.camera import Camera, CameraMode
from systems.turn_controller import initialize_turn_controller


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


def create_renderer_and_input_source(
    sidebar_console: Any,
    viewport_console: Any,
    status_console: Any,
    colors: dict,
    input_mode: str = "keyboard",
    constants: dict = None,
) -> tuple[Renderer, InputSource]:
    """Create renderer and input source instances.

    This factory function instantiates the concrete implementations of the
    Renderer and InputSource protocols, decoupling the game loop from specific
    technologies. Future changes (e.g., sprite renderer, bot input) only require
    creating new implementations; the game loop remains unchanged.

    Args:
        sidebar_console: libtcod console for sidebar
        viewport_console: libtcod console for viewport
        status_console: libtcod console for status panel
        colors: Color configuration dictionary
        input_mode: Input source mode - "keyboard" (default) or "bot" for autoplay
        constants: Game constants dictionary (optional, needed for bot debug flag)

    Returns:
        tuple: (Renderer instance, InputSource instance)
    """
    renderer: Renderer = ConsoleRenderer(
        sidebar_console=sidebar_console,
        viewport_console=viewport_console,
        status_console=status_console,
        colors=colors,
    )

    if input_mode == "bot":
        # Extract bot config from constants
        bot_debug = False
        bot_persona = None  # Will default to "balanced" in BotInputSource
        if constants:
            bot_config = constants.get("bot_config")
            if isinstance(bot_config, dict):
                bot_debug = bool(bot_config.get("debug", False))
                bot_persona = bot_config.get("persona")
        input_source: InputSource = BotInputSource(
            action_interval=1, debug=bot_debug, persona=bot_persona
        )
    else:
        input_source: InputSource = KeyboardInputSource()

    return renderer, input_source


def pump_events_and_sleep(input_source: InputSource, frame_delay: float = 0.016) -> None:
    """Pump OS/window events and throttle frame rate.

    CRITICAL FIX (see KEYBOARD_DOUBLE_MOVE_REAL_FIX.md):
    - For BOT mode: We must pump SDL events for the window to appear/update,
      because BotInputSource.next_action() doesn't call sys_check_for_event.
    - For KEYBOARD mode: Do NOT pump here! KeyboardInputSource.next_action()
      already calls sys_check_for_event, and double-pumping causes edge-triggered
      mouse flags (lbutton_pressed, rbutton_pressed) to be consumed by dummy
      objects, requiring multiple clicks for actions to register.
    
    The principle: Poll input in ONE place only.
    """
    from io_layer.bot_input import BotInputSource
    
    # Only pump events for bot mode - KeyboardInputSource already pumps in next_action()
    if isinstance(input_source, BotInputSource):
        dummy_key = libtcod.Key()
        dummy_mouse = libtcod.Mouse()
        libtcod.sys_check_for_event(0, dummy_key, dummy_mouse)  # 0 = EVENT_NONE
    
    # Sleep to throttle frame rate
    time.sleep(frame_delay)


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
    # Get performance config (precedence: env vars → constants["performance"] → defaults)
    perf_config = get_performance_config(constants)
    logger.info("Performance config: %s", perf_config)
    
    # Create the engine with configurable FPS
    engine = GameEngine(target_fps=perf_config["frame_rate_limit"])

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
    # NOTE: Phase 2 - skip_drawing=True because ConsoleRenderer handles drawing
    #       RenderSystem still runs for FOV recompute and state management
    render_system = OptimizedRenderSystem(
        console=viewport_console,  # Main viewport (legacy 'con')
        panel=status_console,       # Status panel (legacy 'panel')
        sidebar_console=sidebar_console,  # NEW: Sidebar console
        screen_width=constants["screen_width"],
        screen_height=constants["screen_height"],
        colors=constants["colors"],
        priority=100,  # Render last
        use_optimizations=False,  # DISABLE optimizations for debugging
        skip_drawing=False,  # RenderSystem handles rendering for now
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
    
    # Detect bot mode early (before creating ActionProcessor)
    input_mode = "bot" if constants.get("input_config", {}).get("bot_enabled") else "keyboard"
    
    # Create action processor for clean action handling
    # Pass is_bot_mode to suppress spammy per-frame logs during soak testing
    action_processor = ActionProcessor(engine.state_manager, is_bot_mode=(input_mode == "bot"))
    action_processor.turn_manager = engine.turn_manager  # Phase 3: Wire up TurnManager

    # Reinitialize TurnController with turn_manager now that it's set
    action_processor.turn_controller = initialize_turn_controller(
        engine.state_manager, 
        engine.turn_manager
    )
    logger.info(f"ActionProcessor turn_controller reinitialized with TurnManager: {engine.turn_manager}")

    # Persist the action processor for systems that need to reuse it between phases
    engine.state_manager.set_extra_data("action_processor", action_processor)

    # =========================================================================
    # ABSTRACTION LAYER: Create Renderer and InputSource instances
    # 
    # Phase 1 (COMPLETE): Input is now abstraction-driven via input_source.next_action()
    # Phase 2 (IN PROGRESS): Rendering will be driven via renderer.render()
    # 
    # For now:
    # - input_source.next_action() IS the primary input path
    # - renderer.render() exists but is not yet called from main loop
    # - Rendering still via systems (RenderSystem, etc.)
    # =========================================================================
    # input_mode was already detected above (before ActionProcessor creation)
    renderer, input_source = create_renderer_and_input_source(
        sidebar_console=sidebar_console,
        viewport_console=viewport_console,
        status_console=status_console,
        colors=constants["colors"],
        input_mode=input_mode,
        constants=constants,
    )
    
    # Differentiate regular bot mode from soak bot mode
    if input_mode == "bot":
        engine.bot_mode = True
        engine.bot_soak_mode = constants.get("bot_soak_mode", False)
        # UNIFIED: Enemy AI enabled in both --bot and --bot-soak modes
        # BotBrain combat is now reliable enough for full end-to-end soak testing
        engine.disable_enemy_ai_for_bot = False
        
        if engine.bot_soak_mode:
            logger.info("BOT SOAK MODE: Enemy AI ENABLED - full combat testing")
        else:
            logger.info("BOT MODE: Enemy AI enabled, bot will fight monsters")

    # Track first frame to ensure initial render
    # Without this, the first frame would skip engine.update() (no action yet)
    # and the screen would stay black/stuck on menu
    first_frame_needs_render = True
    
    # Main game loop
    # PHASE 1 (INPUT): ✅ COMPLETE - input_source.next_action() is the primary input path
    # PHASE 2 (RENDERING): ✅ COMPLETE - renderer.render() is called each frame
    # PHASE 3+ (OPTIONAL): System cleanup (not required for functionality)
    while not libtcod.console_is_window_closed():
        # Pump OS events and throttle frame rate so bot mode doesn't spin
        # in a tight loop. Keyboard input still works because the pumped
        # key/mouse objects are handed off to the input source.
        pump_events_and_sleep(input_source)

        # =====================================================================
        # INPUT HANDLING (PHASE 1: COMPLETE)
        # Input comes ONLY from input_source.next_action() - no InputSystem.update()
        # Mouse and keyboard actions are mixed in the dict from KeyboardInputSource
        # =====================================================================
        combined_action: ActionDict = input_source.next_action(engine.state_manager.state)
        
        # KEYBOARD DEBUG: Log keyboard input for debugging double-move issue
        if combined_action and input_mode != "bot":
            turn_num = engine.turn_manager.turn_number if engine.turn_manager else 0
            logger.debug(f"[KEYBOARD INPUT] turn={turn_num}, action={combined_action}")
        
        # BOT LIMITS CHECK: Enforce --max-turns and --max-floors if configured
        # This prevents infinite loops and provides deterministic run termination
        if input_mode == "bot" and engine.turn_manager:
            soak_config = constants.get("soak_config", {})
            max_turns = soak_config.get("max_turns")
            max_floors = soak_config.get("max_floors")
            
            # Defensive: Only check limits if player and game_map exist
            player = engine.state_manager.state.player
            game_map = engine.state_manager.state.game_map
            
            if not player or not game_map:
                # Skip limit checks if core objects missing (e.g., in tests)
                pass
            # Check turn limit
            elif max_turns and engine.turn_manager.turn_number >= max_turns:
                logger.info(f"Turn limit reached ({engine.turn_manager.turn_number} >= {max_turns}), ending run")
                
                # Finalize metrics with "max_turns" outcome
                from instrumentation.run_metrics import finalize_run_metrics
                if player and game_map:
                    run_metrics = finalize_run_metrics("max_turns", player, game_map)
                    engine.state_manager.state.run_metrics = run_metrics
                
                engine.stop()
                return {"ended": "max_turns"}
            
            # Check floor limit
            if max_floors and game_map and game_map.dungeon_level >= max_floors:
                logger.info(f"Floor limit reached (floor {game_map.dungeon_level} >= {max_floors}), ending run")
                
                # Finalize metrics with "max_floors" outcome
                from instrumentation.run_metrics import finalize_run_metrics
                if player and game_map:
                    run_metrics = finalize_run_metrics("max_floors", player, game_map)
                    engine.state_manager.state.run_metrics = run_metrics
                
                engine.stop()
                return {"ended": "max_floors"}
        
        # BOT MODE DIAGNOSTIC: Log frame state for debugging tight loops
        if input_mode == "bot" and combined_action:
            current_state = engine.state_manager.state.current_state
            turn_phase = engine.turn_manager.current_phase if engine.turn_manager else None
            logger.debug(
                f"BOT FRAME: state={current_state}, turn_phase={turn_phase}, action={combined_action}"
            )
        
        # Update game state with current mouse position for tooltip rendering
        # KeyboardInputSource maintains current_mouse with libtcod mouse events
        if isinstance(input_source, KeyboardInputSource):
            engine.state_manager.state.mouse = input_source.current_mouse
        
        # Separate mouse actions from keyboard actions
        # KeyboardInputSource mixes both into one dict, but ActionProcessor expects them separate
        mouse_action_keys = {'left_click', 'right_click', 'sidebar_click', 'sidebar_right_click'}
        action: ActionDict = {k: v for k, v in combined_action.items() if k not in mouse_action_keys}
        mouse_action: ActionDict = {k: v for k, v in combined_action.items() if k in mouse_action_keys}
        
        # Phase 1.5.5: Auto-exit on death in bot mode
        # In bot mode, when player dies, automatically exit after a short delay
        # This allows run_metrics to be finalized and summary to be printed
        if input_mode == "bot" and engine.state_manager.state.current_state == GameStates.PLAYER_DEAD:
            # Check if we've been in death state for a few frames (allow metrics to finalize)
            death_frame_counter = getattr(engine.state_manager.state, 'death_frame_counter', 0)
            engine.state_manager.state.death_frame_counter = death_frame_counter + 1
            
            # After 5 frames in death state, auto-exit in bot mode
            if death_frame_counter >= 5:
                logger.info("Bot mode: Auto-exiting after player death")
                # Trigger exit action - this will go through normal exit flow
                action = {"exit": True}
        
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
            
            # Phase 1.5b: End telemetry for current floor on quit
            if engine.state_manager.state.current_state != GameStates.PLAYER_DEAD:
                from services.telemetry_service import get_telemetry_service
                telemetry_service = get_telemetry_service()
                if telemetry_service.enabled:
                    telemetry_service.end_floor()
                    logger.info(f"Telemetry ended for floor on quit")
            
            # Finalize run metrics on quit (Phase 1.5: Run Metrics)
            # Only finalize if player is alive (death is handled separately)
            if engine.state_manager.state.current_state != GameStates.PLAYER_DEAD:
                from instrumentation.run_metrics import finalize_run_metrics
                player = engine.state_manager.state.player
                game_map = engine.state_manager.state.game_map
                run_metrics = finalize_run_metrics("quit", player, game_map)
                if run_metrics:
                    engine.state_manager.state.run_metrics = run_metrics
                    logger.info(f"Run metrics finalized on quit: {run_metrics.run_id}")
                    
                    # Log bot results summary if bot mode is enabled
                    _log_bot_results_summary(run_metrics, constants)
            
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
        # KEYBOARD DEBUG: Log before processing
        if (action or mouse_action) and input_mode != "bot":
            turn_num = engine.turn_manager.turn_number if engine.turn_manager else 0
            logger.debug(f"[PROCESSING ACTION] turn={turn_num}, action={action}, mouse={mouse_action}")
        
        action_processor.process_actions(action, mouse_action)
        
        # ═════════════════════════════════════════════════════════════════════════
        # MAIN LOOP INVARIANT ENFORCEMENT (Manual vs Bot Update Rules)
        # ═════════════════════════════════════════════════════════════════════════
        # 
        # SCOPE: This gating applies ONLY to in-dungeon gameplay (PLAYERS_TURN state),
        #        NOT to menus, dialogs, or other UI states.
        #
        # MANUAL MODE (input_mode != "bot") during PLAYERS_TURN:
        #   The world should ONLY tick when:
        #     a) First frame (needs initial render/FOV), OR
        #     b) The player performed an action (action or mouse_action not empty), OR
        #     c) AutoExplore is actively running
        #   Otherwise, we just render and wait for input.
        #   This enforces the invariant: "one player input → one world tick"
        #
        # BOT MODE (input_mode == "bot"):
        #   Always update - the bot continuously generates actions.
        #   BotInputSource already handles throttling and state-aware action generation.
        #
        # OTHER STATES (menus, dialogs, level-up, etc.):
        #   Always update - these states may need continuous rendering or state updates
        #   independent of player actions.
        # ═════════════════════════════════════════════════════════════════════════
        
        should_update_systems = True  # Default: update for bot mode and non-PLAYERS_TURN states
        
        # Get current game state to determine if gating should apply
        current_state = engine.state_manager.state.current_state
        
        if input_mode != "bot" and current_state == GameStates.PLAYERS_TURN:
            # MANUAL MODE IN-DUNGEON: Only update if there's an action OR auto-explore is active
            # This gating ONLY applies during active dungeon play, not menus/dialogs/etc.
            
            # EXCEPTION: First frame always needs to update for initial render
            if first_frame_needs_render:
                should_update_systems = True
                first_frame_needs_render = False
                logger.debug("MANUAL MODE: First frame - updating for initial render")
            else:
                has_action = bool(action or mouse_action)
                
                # Check if AutoExplore is active
                player = engine.state_manager.state.player
                auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE) if player else None
                auto_explore_active = bool(auto_explore and auto_explore.is_active())
                
                # Diagnostic logging (temporary - can be removed after verification)
                logger.debug(
                    f"MANUAL FRAME: state={current_state}, has_action={has_action}, "
                    f"auto_explore_active={auto_explore_active}, should_update={has_action or auto_explore_active}"
                )
                
                # CRITICAL INVARIANT: Only update if player acted or auto-explore is running
                # This prevents the "empty action spam" bug where engine.update() is called
                # every frame even when the player is idle, causing repeated AI cycles
                if not has_action and not auto_explore_active:
                    should_update_systems = False
                    logger.debug("MANUAL MODE: No action and auto-explore inactive - skipping engine.update()")
        
        # Phase 1.6: Check for bot run abort signal (floor fully explored in soak mode)
        # This is a bot-only terminal condition that should exit the current run
        if engine.state_manager.get_extra_data("bot_abort_run"):
            # Capture the abort reason for soak harness classification
            bot_abort_reason = engine.state_manager.get_extra_data("bot_abort_reason") or "unspecified"
            logger.info(f"Bot abort run detected - reason: {bot_abort_reason}, finalizing run with bot_completed outcome")
            
            # End telemetry for current floor
            from services.telemetry_service import get_telemetry_service
            telemetry_service = get_telemetry_service()
            if telemetry_service and telemetry_service.enabled:
                telemetry_service.end_floor()
                logger.info("Telemetry ended for floor on bot abort")
            
            # Finalize run metrics with bot_completed outcome
            from instrumentation.run_metrics import finalize_run_metrics
            player = engine.state_manager.state.player
            game_map = engine.state_manager.state.game_map
            run_metrics = finalize_run_metrics("bot_completed", player, game_map)
            if run_metrics:
                engine.state_manager.state.run_metrics = run_metrics
                logger.info(f"Run metrics finalized on bot abort: {run_metrics.run_id}")
                
                # Log bot results summary
                _log_bot_results_summary(run_metrics, constants)
            
            # Clean up and return with bot_completed outcome and abort reason
            engine.stop()
            return {"bot_completed": True, "bot_abort_reason": bot_abort_reason}
        
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
                # Special handling for Ending 4 (Fool's Freedom) - show cutscene first
                if choice == '4':
                    from screens.fool_freedom_cutscene import show_fool_freedom_cutscene
                    continue_to_fight, _ = show_fool_freedom_cutscene(
                        con, 0,
                        constants['screen_width'], constants['screen_height']
                    )
                    
                    if not continue_to_fight:
                        # Player escaped cutscene, return to normal gameplay
                        engine.state_manager.set_game_state(GameStates.PLAYERS_TURN)
                        continue
                    # Otherwise, fall through to boss fight below
                
                # Special handling for Ending 5 (Mercy & Corruption) - show grief cutscene first
                if choice == '5':
                    from screens.grief_rage_cutscene import show_grief_rage_cutscene
                    continue_to_fight, _ = show_grief_rage_cutscene(
                        con, 0,
                        constants['screen_width'], constants['screen_height']
                    )
                    
                    if not continue_to_fight:
                        # Player escaped cutscene, return to normal gameplay
                        engine.state_manager.set_game_state(GameStates.PLAYERS_TURN)
                        continue
                    # Otherwise, fall through to boss fight below
                
                # Check if this ending requires a boss fight
                # Phase 5: Six Endings with boss fights
                boss_fights = {
                    # New ending codes (1-6)
                    '1': 'zhyraxion_human',         # Escape Through Battle - Human form (Medium-Hard)
                    '4': 'zhyraxion_full_dragon',   # Fool's Freedom - Full Dragon form (EXTREME)
                    '5': 'zhyraxion_grief_dragon',  # Mercy & Corruption - Grief Dragon (Hard)
                    # Old codes (for backward compatibility)
                    '1a': 'zhyraxion_human',        # Escape Through Battle
                    # '3': REMOVED - Ending 3 is not a boss fight, it's a failure ending
                    '4_old': 'zhyraxion_grief_dragon'  # Mercy & Corruption (old code)
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
                        print(f">>> BOSS FIGHT START: pending_ending set to '{choice}' for boss {boss.name}")
                        import logging
                        logging.info(f"=== BOSS FIGHT START: pending_ending set to '{choice}' ===")
                        
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
                
                # Phase 1.5b: End telemetry for current floor on victory
                from services.telemetry_service import get_telemetry_service
                telemetry_service = get_telemetry_service()
                if telemetry_service.enabled:
                    telemetry_service.end_floor()
                    logger.info(f"Telemetry ended for floor on victory")
                
                # Finalize run metrics on victory (Phase 1.5: Run Metrics)
                from instrumentation.run_metrics import finalize_run_metrics
                player = engine.state_manager.state.player
                game_map = engine.state_manager.state.game_map
                run_metrics = finalize_run_metrics("victory", player, game_map)
                if run_metrics:
                    engine.state_manager.state.run_metrics = run_metrics
                    logger.info(f"Run metrics finalized on victory: {run_metrics.run_id}")
                    
                    # Log bot results summary if bot mode is enabled
                    _log_bot_results_summary(run_metrics, constants)
                
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

        # =====================================================================
        # RENDERING & GAME STATE UPDATES
        #
        # CRITICAL SEPARATION: World updates vs Rendering
        # =====================================================================
        # 
        # WORLD UPDATES (AI, Environment, etc.):
        #   Only tick when should_update_systems is True (player acted, auto-explore, bot mode)
        #   This prevents AI spam and maintains manual-loop invariants
        # 
        # RENDERING (screen refresh, visual effects, tooltips):
        #   Must run EVERY frame to:
        #     - Clear hit-flash effects from the visual effect queue
        #     - Update tooltips based on current mouse position
        #     - Refresh transient UI state
        # 
        # Implementation: Update non-render systems conditionally, then always render
        # =====================================================================
        
        # Update delta_time for this frame (needed for all systems)
        current_time = time.time()
        engine.delta_time = current_time - engine._last_time
        engine._last_time = current_time
        
        # Update world systems (AI, Environment) only when the world should tick
        if should_update_systems:
            # KEYBOARD DEBUG: Log engine update
            if input_mode != "bot":
                turn_num_before = engine.turn_manager.turn_number if engine.turn_manager else 0
                logger.debug(f"[ENGINE UPDATE START] turn={turn_num_before}, updating systems")
            
            # Update all systems EXCEPT render system
            # Render system will be updated separately below to ensure it runs every frame
            for system in engine.systems.values():
                # Skip render system here - it will be called explicitly below
                if system.name == "render" or not system.enabled:
                    continue
                system.update(engine.delta_time)
            
            # KEYBOARD DEBUG: Log turn counter after update
            if input_mode != "bot":
                turn_num_after = engine.turn_manager.turn_number if engine.turn_manager else 0
                if turn_num_after != turn_num_before:
                    logger.debug(f"[ENGINE UPDATE END] turn changed: {turn_num_before} -> {turn_num_after}")
        
        # ALWAYS update render system, regardless of world tick
        # This ensures:
        # 1. Visual effects queue is played and cleared each frame
        # 2. Tooltips are recomputed based on current mouse position
        # 3. Transient UI state (hit flashes, hover) updates properly
        render_system = engine.get_system("render")
        if render_system and render_system.enabled:
            render_system.update(engine.delta_time)

        # IMPORTANT: Reset FOV flag AFTER rendering is complete
        # This ensures the flag stays active for the entire frame
        if engine.state_manager.state.fov_recompute:
            engine.state_manager.state.fov_recompute = False

    # Clean up
    engine.stop()
    
    # Print bot results summary AFTER game loop exits (so it's visible)
    # Check if run_metrics exist and bot mode was enabled
    # NOTE: We do NOT create or finalize run_metrics here - that should have been
    # done by finalize_player_death() when the player died, or by quit handling.
    # This code only consumes whatever was produced earlier.
    run_metrics = getattr(engine.state_manager.state, 'run_metrics', None)
    bot_enabled = constants.get("input_config", {}).get("bot_enabled", False)
    if not bot_enabled:
        bot_enabled = constants.get("bot_soak_mode", False)
    
    # Diagnostic logging
    logger.info(f"Game loop exited: run_metrics exists={run_metrics is not None}, bot_enabled={bot_enabled}")
    if run_metrics:
        logger.info(f"Run metrics: outcome={run_metrics.outcome}, floors={run_metrics.floors_visited}, kills={run_metrics.monsters_killed}")
    
    if run_metrics and bot_enabled:
        # Bot summary should already have been logged by finalize_player_death() for deaths.
        # Only log here if it's NOT a death (e.g., bot completed successfully, quit, or victory).
        # This prevents double logging when player dies.
        current_state = engine.state_manager.state.current_state
        if current_state != GameStates.PLAYER_DEAD:
            # Not a death - log the summary (quit, victory, bot_completed, etc.)
            _log_bot_results_summary(run_metrics, constants)
        else:
            # Death case - summary already logged by finalize_player_death(), skip to avoid double logging
            logger.debug("Bot results summary skipped: already logged by finalize_player_death()")
    elif run_metrics and not bot_enabled:
        logger.debug("Bot results summary skipped: bot mode not enabled")
    elif not run_metrics and bot_enabled:
        logger.warning("Bot results summary skipped: run_metrics not found on game state (player may have died without finalization)")
    
    # Return to main menu (no restart)
    return {"restart": False}


@contextmanager
def _manual_input_system_update(engine, delta_time):
    """Context manager to manually update the input system.
    
    ⚠️  DEPRECATED - Legacy helper for old-style tests
    New code should use InputSource.next_action() directly
    
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
            # Test the actions (legacy - use KeyboardInputSource instead)
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
    
    # Create a temporary action processor for this call
    action_processor = ActionProcessor(state_manager)
    action_processor.process_actions(action, mouse_action)
