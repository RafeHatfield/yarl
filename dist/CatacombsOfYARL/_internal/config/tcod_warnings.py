"""TCOD warning suppression utilities.

This module provides centralized warning suppression for TCOD deprecation
warnings to keep console output clean during development.
"""

import warnings
import os


def suppress_tcod_warnings():
    """Suppress TCOD deprecation and future warnings for cleaner console output.
    
    This function consolidates all TCOD-related warning filters in one place
    for easier maintenance and cleaner main engine code.
    """
    # TCOD event system deprecation warnings
    warnings.filterwarnings("ignore", message=".*Use the tcod.event module.*")
    warnings.filterwarnings("ignore", message=".*Use tcod.event.get.*")
    warnings.filterwarnings("ignore", message=".*Call the.*method instead.*")
    
    # TCOD console deprecation warnings
    warnings.filterwarnings("ignore", message=".*Create a console using.*")
    warnings.filterwarnings("ignore", message=".*console_set_custom_font is deprecated.*")
    warnings.filterwarnings("ignore", message=".*console_init_root is deprecated.*")
    warnings.filterwarnings("ignore", message=".*Use.*Console.draw_semigraphics.*")
    
    # TCOD module and function deprecation warnings
    warnings.filterwarnings("ignore", message=".*Soon the.*module will no longer.*")
    warnings.filterwarnings("ignore", message=".*Color constants will be removed.*")
    warnings.filterwarnings("ignore", message=".*Call the classmethod.*tcod.image.Image.from_file.*")
    warnings.filterwarnings("ignore", message=".*It's recommended to load images.*")
    
    # Broad TCOD category filters
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="tcod")
    warnings.filterwarnings("ignore", category=FutureWarning, module="tcod")


def suppress_sdl_messages():
    """Suppress SDL system messages for cleaner console output.
    
    Sets environment variables to reduce SDL logging verbosity,
    showing only critical errors.
    """
    os.environ['SDL_LOG_PRIORITY_SYSTEM'] = '5'  # Only show critical errors
    os.environ['SDL_LOG_PRIORITY_RENDER'] = '5'  # Only show critical errors


def setup_clean_console():
    """Set up clean console output by suppressing unnecessary warnings and messages.
    
    This is the main function to call during game initialization to ensure
    clean console output during development and gameplay.
    """
    suppress_tcod_warnings()
    suppress_sdl_messages()
