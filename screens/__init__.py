"""Screen modules for special game screens.

This package contains modules for displaying special screens like
confrontation choices, victory/failure endings, and other UI screens.
"""

from .confrontation_choice import confrontation_menu
from .victory_screen import (
    show_ending_screen,
    show_ending_1a, show_ending_1b, show_ending_2,
    show_ending_3, show_ending_4, show_ending_5,
    show_good_ending, show_bad_ending
)

__all__ = [
    'confrontation_menu',
    'show_ending_screen',
    'show_ending_1a',
    'show_ending_1b',
    'show_ending_2',
    'show_ending_3',
    'show_ending_4',
    'show_ending_5',
    'show_good_ending',
    'show_bad_ending'
]

