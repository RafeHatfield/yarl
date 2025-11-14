"""Main game engine and entry point.

This module contains the main game loop, event handling, and core
game logic coordination. It manages the game state, rendering,
and player input processing.
"""

import argparse
import logging
import os

import tcod.libtcodpy as libtcod
import warnings

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
                # Display Hall of Fame screen
                from systems.hall_of_fame import display_hall_of_fame
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
            telemetry_service.dump_json()
            stats = telemetry_service.get_stats()
            print(f"\n📊 Telemetry Summary:")
            print(f"   Floors: {stats.get('floors', 0)}")
            print(f"   Avg ETP: {stats.get('avg_etp_per_floor', 0):.1f}")
            print(f"   Traps: {stats.get('total_traps', 0)}")
            print(f"   Secrets: {stats.get('total_secrets', 0)}")
            print(f"   Doors: {stats.get('total_doors', 0)}")
            print(f"   Keys: {stats.get('total_keys', 0)}")
        except Exception as e:
            print(f"\n❌ Failed to dump telemetry: {e}")


if __name__ == "__main__":
    main()