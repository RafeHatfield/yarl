"""Game state enumeration for managing different game modes.

This module defines the various states the game can be in,
which determines how input is handled and what is displayed.
"""

from enum import Enum


class GameStates(Enum):
    """Enumeration of possible game states.

    Each state represents a different mode of gameplay or UI interaction
    that affects how the game processes input and renders the screen.
    """

    PLAYERS_TURN = 1
    ENEMY_TURN = 2
    PLAYER_DEAD = 3
    SHOW_INVENTORY = 4
    DROP_INVENTORY = 5
    TARGETING = 6
    LEVEL_UP = 7
    CHARACTER_SCREEN = 8
    THROW_SELECT_ITEM = 9  # Selecting item to throw
    THROW_TARGETING = 10   # Targeting throw location
