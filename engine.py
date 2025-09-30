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
from config.testing_config import set_testing_mode

# Set up basic logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

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
  python engine.py                    # Normal gameplay
  python engine.py --testing          # Enable testing mode (more items)
  python engine.py -t                 # Short form of testing mode
        """
    )
    
    parser.add_argument(
        '--testing', '-t',
        action='store_true',
        help='Enable testing mode with increased item spawn rates for easier testing'
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the game.

    Initializes the game window, loads or creates a new game,
    and runs the main game loop until the player quits.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Set testing mode if requested
    if args.testing:
        set_testing_mode(True)
        print("🧪 TESTING MODE ENABLED: Increased item spawn rates for testing")
    
    # Also check environment variable as fallback
    if os.environ.get('YARL_TESTING_MODE', '').lower() in ('true', '1', 'yes', 'on'):
        set_testing_mode(True)
        print("🧪 TESTING MODE ENABLED: Via environment variable YARL_TESTING_MODE")
    
    # Initialize monster action logging if in testing mode
    from config.testing_config import is_testing_mode
    if is_testing_mode():
        from components.monster_action_logger import MonsterActionLogger
        MonsterActionLogger.setup_logging()
    constants = get_constants()

    libtcod.console_set_custom_font(
        "arial10x10.png", libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD
    )

    libtcod.console_init_root(
        constants["screen_width"],
        constants["screen_height"],
        constants["window_title"],
        False,
    )

    con = libtcod.console_new(constants["screen_width"], constants["screen_height"])
    panel = libtcod.console_new(constants["screen_width"], constants["panel_height"])

    player = None
    entities = []
    game_map = None
    message_log = None
    game_state = None

    show_main_menu = True
    show_load_error_message = False

    main_menu_background_image = libtcod.image_load("menu_background1.png")

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
                constants["screen_width"],
                constants["screen_height"],
            )

            if show_load_error_message:
                message_box(
                    con,
                    "No save game to load",
                    50,
                    constants["screen_width"],
                    constants["screen_height"],
                )

            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=DeprecationWarning, 
                                      message="This function is not supported if contexts are being used")
                libtcod.console_flush()

            action = handle_main_menu(key)

            new_game = action.get("new_game")
            load_saved_game = action.get("load_game")
            exit_game = action.get("exit")

            if show_load_error_message and (new_game or load_saved_game or exit_game):
                show_load_error_message = False
            elif new_game:
                player, entities, game_map, message_log, game_state = (
                    get_game_variables(constants)
                )
                game_state = GameStates.PLAYERS_TURN

                show_main_menu = False
            elif load_saved_game:
                try:
                    player, entities, game_map, message_log, game_state = load_game()
                    show_main_menu = False
                except FileNotFoundError:
                    show_load_error_message = True
            elif exit_game:
                break

        else:
            libtcod.console_clear(con)
            
            # Use the modern engine architecture
            play_game_with_engine(
                player,
                entities,
                game_map,
                message_log,
                game_state,
                con,
                panel,
                constants
            )

            show_main_menu = True


if __name__ == "__main__":
    main()