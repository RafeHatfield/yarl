"""Main game engine and entry point.

This module contains the main game loop, event handling, and core
game logic coordination. It manages the game state, rendering,
and player input processing.

LIBTCOD LIFECYCLE ACROSS DIFFERENT MODES:
------------------------------------------

NORMAL MODE (python3 engine.py):
1. main() calls console_set_custom_font() [line ~258]
2. main() calls console_init_root() [line ~263] - ROOT CONSOLE CREATED
3. main() creates sidebar/viewport/status consoles with console_new()
4. main() enters game loop → play_game_with_engine()
5. ConsoleRenderer.render() calls console_flush() ✅ WORKS (root exists)
6. On exit, root console persists until process ends

SINGLE BOT MODE (python3 engine.py --bot):
1-6. IDENTICAL to normal mode, just uses BotInputSource instead of KeyboardInputSource

BOT SOAK MODE (python3 engine.py --bot-soak):
1. main() detects --bot-soak flag early [line ~167]
2. main() calls run_bot_soak() which:
   a. Calls _initialize_libtcod_for_soak() ONCE - ROOT CONSOLE CREATED
   b. Loops N times, each iteration:
      - Creates new viewport/sidebar/status consoles
      - Calls play_game_with_engine()
      - ConsoleRenderer.render() calls console_flush() ✅ WORKS (root exists)
3. After all runs complete, returns to main() which exits
4. Root console persists until process ends

The key fix: bot-soak now initializes the root console via _initialize_libtcod_for_soak()
before running any games, preventing "Console must not be NULL" crashes.
"""

# =============================================================================
# CRITICAL: Early headless detection - MUST happen before tcod import!
# SDL_VIDEODRIVER must be set BEFORE SDL is initialized (which happens on
# tcod import). Once SDL starts, changing this env var has no effect.
# =============================================================================
import sys
import os

if '--headless' in sys.argv:
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
# =============================================================================

import argparse
import logging

import tcod.libtcodpy as libtcod
import warnings

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

from game_states import GameStates
from input_handlers import handle_main_menu
from loader_functions.data_loaders import load_game
from loader_functions.initialize_new_game import get_constants, get_game_variables
from menus import main_menu, message_box
from engine_integration import play_game_with_engine
from config.testing_config import set_testing_mode, get_testing_config, is_testing_mode
from config.ui_layout import get_ui_layout
from debug_logging import setup_debug_logging
from entity_dialogue import EntityDialogue
from rendering.camera import Camera, CameraMode
from engine.systems import (
    RenderSystem,
    InputSystem,
    AISystem,
    PerformanceSystem,
    EnvironmentSystem,
)
from engine.systems.optimized_render_system import OptimizedRenderSystem
from systems.turn_controller import initialize_turn_controller

# Initialize centralized logging system (DEBUG level for tooltip debugging)
from logger_config import setup_logging
setup_logging(log_level=logging.DEBUG)  # Enable DEBUG for tooltip instrumentation
print("📝 Centralized logging enabled: logs/rlike.log (DEBUG level for tooltip debugging)")

# Set up error file logging to capture all errors for later review
error_handler = logging.FileHandler('errors.log', mode='a')
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
error_handler.setFormatter(error_formatter)
logging.getLogger().addHandler(error_handler)
print("📝 Error logging also enabled: errors.log")

# Set up clean console output (suppress TCOD warnings and SDL messages)
from config.tcod_warnings import setup_clean_console
setup_clean_console()


def parse_arguments():
    """Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Yarl (Catacombs of Yarl) - A roguelike adventure game',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python engine.py                              # Normal gameplay
  python engine.py --testing                    # Enable testing mode (more items)
  python engine.py --testing --start-level 20   # Skip to level 20
  python engine.py --testing --god-mode         # Can't die (HP never <1)
  python engine.py --testing --no-monsters      # Peaceful mode (story testing)
  python engine.py --testing --reveal-map       # Full FOV (no fog of war)
  
  # Combine flags for ultimate testing power:
  python engine.py --testing --start-level 15 --god-mode --no-monsters --reveal-map
        """
    )
    
    # Basic testing mode
    parser.add_argument(
        '--testing', '-t',
        action='store_true',
        help='Enable testing mode with increased item spawn rates for easier testing'
    )
    
    # Tier 1 Debug Flags (require --testing)
    parser.add_argument(
        '--start-level',
        type=int,
        metavar='N',
        help='Start game on dungeon level N (requires --testing)'
    )
    
    parser.add_argument(
        '--god-mode',
        action='store_true',
        help='Enable god mode - player cannot die, HP never goes below 1 (requires --testing)'
    )
    
    parser.add_argument(
        '--no-monsters',
        action='store_true',
        help='Disable monster spawning - peaceful mode for story/UI testing (requires --testing)'
    )
    
    parser.add_argument(
        '--reveal-map',
        action='store_true',
        help='Reveal entire map - no fog of war, infinite FOV (requires --testing)'
    )
    
    # Tier 2: Wizard Mode - In-game debug menu
    parser.add_argument(
        '--wizard',
        action='store_true',
        help='Enable wizard mode - in-game debug menu with & key (requires --testing)'
    )
    
    # Telemetry collection
    parser.add_argument(
        '--telemetry-json',
        type=str,
        metavar='PATH',
        help='Enable telemetry collection and write floor-by-floor JSON to PATH'
    )
    
    # Bot/autoplay mode
    parser.add_argument(
        '--bot',
        action='store_true',
        help='Enable bot/autoplay input source instead of keyboard input'
    )
    
    parser.add_argument(
        '--bot-debug',
        action='store_true',
        help='Enable verbose BotBrain debug logging in bot mode'
    )
    
    parser.add_argument(
        '--bot-persona',
        type=str,
        default='balanced',
        choices=['balanced', 'cautious', 'aggressive', 'greedy', 'speedrunner'],
        help='Bot behavior persona (default: balanced). Options: balanced, cautious, aggressive, greedy, speedrunner'
    )
    
    # Bot soak testing (Phase 1.6)
    parser.add_argument(
        '--bot-soak',
        action='store_true',
        help='Run multiple bot games back-to-back for soak testing (implies --bot)'
    )
    
    parser.add_argument(
        '--runs',
        type=int,
        default=10,
        metavar='N',
        help='Number of bot runs to execute when --bot-soak is active (default: 10)'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run in headless mode (no window, for CI/automated testing)'
    )
    
    parser.add_argument(
        '--max-turns',
        type=int,
        metavar='N',
        help='Maximum turns per run (bot-soak only, ends run with "max_turns" outcome)'
    )
    
    parser.add_argument(
        '--max-floors',
        type=int,
        metavar='N',
        help='Maximum floor depth per run (bot-soak only, ends run at this floor)'
    )
    
    parser.add_argument(
        '--start-floor',
        type=int,
        metavar='N',
        default=1,
        help='Starting floor for bot runs (bot-soak only, default: 1)'
    )
    
    parser.add_argument(
        '--metrics-log',
        type=str,
        metavar='PATH',
        help='Output file for per-run metrics in JSONL format (bot-soak only)'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        metavar='N',
        help='RNG seed for deterministic runs (bot-soak only). If not provided, a random seed is generated and logged.'
    )
    
    parser.add_argument(
        '--replay-log',
        type=str,
        metavar='PATH',
        help='Path for action replay log output (bot-soak only). When provided, actions are logged for replay.'
    )
    
    parser.add_argument(
        '--scenario',
        type=str,
        metavar='NAME',
        help='Scenario name to use for bot-soak runs instead of normal worldgen (e.g., orc_swarm_tight)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the game.

    Initializes the game window, loads or creates a new game,
    and runs the main game loop until the player quits.
    """
    # Initialize debug logging FIRST (before anything else)
    debug_log = setup_debug_logging("debug.log", console_level="WARNING")
    print(f"🔍 Debug logging enabled: {debug_log}")
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Phase 1.6: Handle bot soak mode early (before rendering setup)
    if args.bot_soak:
        # Bot soak runs headless-ish (no main menu, direct to harness)
        # Force bot mode and enable telemetry
        from engine.soak_harness import run_bot_soak
        
        # Headless mode: SDL_VIDEODRIVER was already set at top of file (before tcod import)
        if args.headless:
            print("🔇 Headless mode enabled (no window)")
        else:
            print("🖥️  Window mode enabled (game visible)")
        
        # Enable telemetry (required for soak data collection)
        telemetry_path = args.telemetry_json or "telemetry/soak_output.json"
        
        print(f"🧪 BOT SOAK MODE: Running {args.runs} bot games")
        print(f"📊 Telemetry enabled: {telemetry_path}")
        
        # Get constants (needed for game initialization)
        constants = get_constants()
        
        # CRITICAL: Enable bot input mode for soak runs
        # This ensures ActionProcessor recognizes bot mode and enables:
        # - AutoExplore opportunistic loot (bot_mode=True)
        # - Auto-equipment optimization
        # - Proper bot behavior throughout the engine
        constants.setdefault("input_config", {})
        constants["input_config"]["bot_enabled"] = True
        
        # Set up bot config (persona, debug) for soak mode
        constants.setdefault("bot_config", {})
        if args.bot_debug:
            constants["bot_config"]["debug"] = True
        if args.bot_persona:
            constants["bot_config"]["persona"] = args.bot_persona
            print(f"🤖 BOT PERSONA: {args.bot_persona}")
        
        # Set scenario_id if provided (for scenario-based soaks)
        if args.scenario:
            constants["scenario_id"] = args.scenario
            constants["scenario"] = args.scenario  # Fallback for compatibility
            print(f"🎯 SCENARIO: {args.scenario}")
        
        # Handle seed
        if args.seed:
            print(f"🎲 RNG SEED: {args.seed} (explicit)")
        else:
            print(f"🎲 RNG SEED: Auto-generated per run (logged in CSV)")
        
        # Run soak harness
        session_result = run_bot_soak(
            runs=args.runs,
            telemetry_enabled=True,
            telemetry_output_path=telemetry_path,
            constants=constants,
            max_turns=args.max_turns,
            max_floors=args.max_floors,
            start_floor=args.start_floor,
            metrics_log_path=args.metrics_log,
            base_seed=args.seed,
            replay_log_path=args.replay_log,
        )
        
        # Print session summary
        session_result.print_summary()
        
        # Exit without launching interactive mode
        return
    
    # Validate that debug flags require --testing
    if (args.start_level or args.god_mode or args.no_monsters or args.reveal_map or args.wizard) and not args.testing:
        print("❌ ERROR: Debug flags (--start-level, --god-mode, --no-monsters, --reveal-map, --wizard) require --testing flag")
        print("   Example: python engine.py --testing --start-level 20 --god-mode")
        print("   Example: python engine.py --testing --wizard")
        return
    
    # Set testing mode if requested
    if args.testing:
        set_testing_mode(True)
        print("🧪 TESTING MODE ENABLED: Increased item spawn rates for testing")
    
    # Also check environment variable as fallback
    if os.environ.get('YARL_TESTING_MODE', '').lower() in ('true', '1', 'yes', 'on'):
        set_testing_mode(True)
        print("🧪 TESTING MODE ENABLED: Via environment variable YARL_TESTING_MODE")
    
    # Configure Tier 1 debug flags
    config = get_testing_config()
    
    if args.start_level:
        config.start_level = args.start_level
        print(f"⏭️  START LEVEL: Will begin on dungeon level {args.start_level}")
    
    if args.god_mode:
        config.god_mode = True
        print("🛡️  GOD MODE ENABLED: Player cannot die (HP never goes below 1)")
    
    if args.no_monsters:
        config.no_monsters = True
        print("☮️  PEACEFUL MODE: No monsters will spawn")
    
    if args.reveal_map:
        config.reveal_map = True
        print("👁️  REVEAL MAP: Entire map visible, no fog of war")
    
    if args.wizard:
        config.wizard_mode = True
        print("🧙 WIZARD MODE ENABLED: Press @ or F12 to open debug menu")
    
    # Initialize monster action logging if in testing mode
    if is_testing_mode():
        from components.monster_action_logger import MonsterActionLogger
        MonsterActionLogger.setup_logging()
    
    # Initialize telemetry service
    telemetry_service = None
    if args.telemetry_json:
        from services.telemetry_service import get_telemetry_service
        telemetry_service = get_telemetry_service(args.telemetry_json)
        print(f"📊 TELEMETRY ENABLED: Will write to {args.telemetry_json}")
    
    constants = get_constants()
    
    # Propagate bot/autoplay configuration into constants for engine_integration
    constants.setdefault("input_config", {})
    constants["input_config"]["bot_enabled"] = bool(args.bot)
    if args.bot:
        print("🤖 BOT MODE ENABLED: Using autoplay input source (behavior minimal for now)")
    
    # Propagate bot config
    constants.setdefault("bot_config", {})
    if args.bot_debug:
        constants["bot_config"]["debug"] = True
        if args.bot:
            print("🐛 BOT DEBUG LOGGING ENABLED: Verbose BotBrain decision logging")
    
    # Propagate bot persona
    if args.bot_persona:
        constants["bot_config"]["persona"] = args.bot_persona
        if args.bot or args.bot_soak:
            print(f"🤖 BOT PERSONA: {args.bot_persona}")
    
    # Get UI layout configuration for split-screen design
    ui_layout = get_ui_layout()

    libtcod.console_set_custom_font(
        "arial10x10.png", libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD
    )

    # Initialize root console with new layout dimensions
    libtcod.console_init_root(
        ui_layout.screen_width,
        ui_layout.screen_height,
        constants["window_title"],
        False,
    )

    # Create 3 consoles for split-screen layout
    # Sidebar: Full height, left side
    sidebar_console = libtcod.console_new(
        ui_layout.sidebar_width, 
        ui_layout.screen_height
    )
    
    # Viewport: Main game view, right side
    viewport_console = libtcod.console_new(
        ui_layout.viewport_width, 
        ui_layout.viewport_height
    )
    
    # Status Panel: Below viewport (HP, messages, dungeon info)
    status_console = libtcod.console_new(
        ui_layout.status_panel_width,
        ui_layout.status_panel_height
    )
    
    # Legacy consoles for compatibility during transition
    # TODO: Remove these once all systems updated
    con = viewport_console  # Main console points to viewport
    panel = status_console  # Panel points to status

    player = None
    entities = []
    game_map = None
    message_log = None
    game_state = None

    # Skip main menu if any debug flags are active (testing mode)
    skip_menu = args.testing and (args.start_level or args.god_mode or args.no_monsters or args.reveal_map)
    
    if skip_menu:
        print("⏩ SKIPPING MAIN MENU: Starting new game directly with debug flags")
        show_main_menu = False
        # Initialize new game immediately
        player, entities, game_map, message_log, game_state = (
            get_game_variables(constants)
        )
        game_state = GameStates.PLAYERS_TURN
    else:
        show_main_menu = True
    
    show_load_error_message = False

    main_menu_background_image = libtcod.image_load("menu_background1.png")
    
    # Generate Entity quote ONCE to prevent flickering (Phase 1 feature)
    entity_menu_quote = EntityDialogue.get_main_menu_quote()

    key = libtcod.Key()
    mouse = libtcod.Mouse()

    while not libtcod.console_is_window_closed():
        libtcod.sys_check_for_event(
            libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse
        )

        if show_main_menu:
            main_menu(
                con,
                main_menu_background_image,
                ui_layout.screen_width,  # Use actual screen dimensions
                ui_layout.screen_height,  # Not old constants!
                entity_menu_quote,  # Pass the pre-selected quote
            )

            if show_load_error_message:
                message_box(
                    con,
                    "No save game to load",
                    50,
                    ui_layout.screen_width,  # Use actual screen dimensions
                    ui_layout.screen_height,  # Not old constants!
                )

            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=DeprecationWarning, 
                                      message="This function is not supported if contexts are being used")
                libtcod.console_flush()

            action = handle_main_menu(key, mouse)

            new_game = action.get("new_game")
            load_saved_game = action.get("load_game")
            show_hall_of_fame = action.get("hall_of_fame")
            exit_game = action.get("exit")

            if show_load_error_message and (new_game or load_saved_game or show_hall_of_fame or exit_game):
                show_load_error_message = False
            elif show_hall_of_fame:
                # Display Hall of Fame screen (IO-layer renderer)
                from io_layer.hall_of_fame_renderer import display_hall_of_fame
                display_hall_of_fame(con, con, ui_layout.screen_width, ui_layout.screen_height)
            elif new_game:
                player, entities, game_map, message_log, game_state = (
                    get_game_variables(constants)
                )
                game_state = GameStates.PLAYERS_TURN

                show_main_menu = False
                # Generate new Entity quote for next time menu is shown
                entity_menu_quote = EntityDialogue.get_main_menu_quote()
            elif load_saved_game:
                try:
                    player, entities, game_map, message_log, game_state = load_game()
                    show_main_menu = False
                    # Generate new Entity quote for next time menu is shown
                    entity_menu_quote = EntityDialogue.get_main_menu_quote()
                except FileNotFoundError:
                    show_load_error_message = True
            elif exit_game:
                break

        else:
            libtcod.console_clear(con)
            
            # Use the modern engine architecture with 3-console layout
            result = play_game_with_engine(
                player,
                entities,
                game_map,
                message_log,
                game_state,
                sidebar_console,
                viewport_console,
                status_console,
                constants
            )

            # Check if player wants to restart or go to main menu
            if result and result.get("restart"):
                # Restart: create a new game immediately
                player, entities, game_map, message_log, game_state = (
                    get_game_variables(constants)
                )
                game_state = GameStates.PLAYERS_TURN
                # Don't show main menu, continue playing
            else:
                # Return to main menu
                show_main_menu = True
    
    # Dump telemetry on game exit
    if telemetry_service:
        try:
            # Get run metrics from current game state if available (Phase 1.5)
            from instrumentation.run_metrics import get_run_metrics_recorder, finalize_run_metrics
            run_metrics_recorder = get_run_metrics_recorder()
            run_metrics = None
            
            # If recorder exists but hasn't been finalized, finalize it now
            # (This handles quit from main menu or other exit paths)
            if run_metrics_recorder and not run_metrics_recorder.is_finalized():
                # Try to finalize with player/game_map if available
                if player and game_map:
                    run_metrics = finalize_run_metrics("quit", player, game_map)
                else:
                    logger.warning("Run metrics recorder exists but no player/game_map available for finalization")
            elif run_metrics_recorder:
                run_metrics = run_metrics_recorder.get_metrics()
            
            # Dump telemetry with run metrics
            telemetry_service.dump_json(run_metrics=run_metrics)
            stats = telemetry_service.get_stats()
            print(f"\n📊 Telemetry Summary:")
            print(f"   Floors: {stats.get('floors', 0)}")
            print(f"   Avg ETP: {stats.get('avg_etp_per_floor', 0):.1f}")
            print(f"   Traps: {stats.get('total_traps', 0)}")
            print(f"   Secrets: {stats.get('total_secrets', 0)}")
            print(f"   Doors: {stats.get('total_doors', 0)}")
            print(f"   Keys: {stats.get('total_keys', 0)}")
            
            # Show run metrics summary if available
            if run_metrics:
                print(f"\n🎮 Run Summary:")
                print(f"   Mode: {run_metrics.mode}")
                print(f"   Outcome: {run_metrics.outcome}")
                print(f"   Duration: {run_metrics.duration_seconds:.1f}s" if run_metrics.duration_seconds else "   Duration: N/A")
                print(f"   Floor: {run_metrics.deepest_floor}")
                print(f"   Kills: {run_metrics.monsters_killed}")
        except Exception as e:
            print(f"\n❌ Failed to dump telemetry: {e}")


if __name__ == "__main__":
    main()