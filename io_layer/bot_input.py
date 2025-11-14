"""Bot/autoplay input source implementation.

This module provides a BotInputSource class that implements the InputSource protocol
for automated/bot play modes. The initial implementation is intentionally minimal,
serving as a clean integration point for future autoplay logic.
"""

from typing import Any

from io_layer.interfaces import ActionDict, InputSource


class BotInputSource:
    """Input source implementation for automated/bot play.

    This initial version is intentionally minimal and always returns an empty action
    dictionary. It exists to provide a clean integration point for future autoplay logic
    (auto-explore, simple pathing, menu handling, etc.).

    In later iterations, this class will be extended to:
    - Detect game state and trigger appropriate behaviors (e.g., auto-explore)
    - Handle menu navigation
    - Process level transitions
    - Implement bot decision-making algorithms

    Attributes:
        _initialized: Marker flag indicating the bot is ready (placeholder for future state)
    """

    def __init__(self) -> None:
        """Initialize the BotInputSource.

        Sets up the bot for future behavioral logic. Currently a no-op initialization
        but structured to accept internal bot state in later iterations (e.g., run counters,
        decision trees, exploration logs).
        """
        self._initialized = True

    def next_action(self, game_state: Any) -> ActionDict:
        """Return the next bot action.

        Args:
            game_state: The current game state object. In future iterations, this will be
                       analyzed to make intelligent decisions (e.g., detecting PLAYERS_TURN
                       and triggering auto-explore, detecting menus, etc.).

        Returns:
            ActionDict: An empty dictionary for now (no actions). Later iterations will
                       populate this with actual bot decisions based on game_state.
        """
        return {}

