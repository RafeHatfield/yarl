"""Screen modules for special game screens.

This package contains modules for displaying special screens like
confrontation choices, victory/failure endings, and other UI screens.
"""

from .confrontation_choice import confrontation_menu
from .victory_screen import show_ending_screen, show_good_ending, show_bad_ending

__all__ = [
    'confrontation_menu',
    'show_ending_screen',
    'show_good_ending',
    'show_bad_ending'
]

