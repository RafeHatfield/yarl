"""Bot/autoplay input source implementation.

This module provides a BotInputSource class that implements the InputSource protocol
for automated/bot play modes. The initial implementation is intentionally minimal,
serving as a clean integration point for future autoplay logic.
"""

from typing import Any

from io_layer.interfaces import ActionDict, InputSource


class BotInputSource:
    """Input source implementation for automated/bot play.

    This initial version is intentionally minimal and always returns {'wait': True}.
    It exists to provide a clean integration point for future autoplay logic
    (auto-explore, simple pathing, menu handling, etc.).

    In later iterations, this class will be extended to:
    - Detect game state and trigger appropriate behaviors (e.g., auto-explore)
    - Handle menu navigation
    - Process level transitions
    - Implement bot decision-making algorithms

    Attributes:
        _initialized: Marker flag indicating the bot is ready (placeholder for future state)
    """

    def __init__(self, action_interval: int = 1) -> None:
        """Initialize the BotInputSource.

        Sets up the bot for future behavioral logic. Currently a no-op initialization
        but structured to accept internal bot state in later iterations (e.g., run counters,
        decision trees, exploration logs).

        Args:
            action_interval: Number of frames to wait between actions. The bot
                             will emit an action every Nth call when the game
                             is in PLAYERS_TURN.
        """
        self._initialized = True
        self._frame_counter = 0
        self._action_interval = action_interval

    def next_action(self, game_state: Any) -> ActionDict:
        """Return the next bot action.

        The current implementation uses a trivial "wait every turn" policy, allowing the
        game loop to tick forward without the bot performing any meaningful actions. This
        serves as the base for future intelligent autoplay logic.
        
        Args:
            game_state: The current game state object. In future iterations, this will be
                       analyzed to make intelligent decisions (e.g., detecting PLAYERS_TURN
                       and triggering auto-explore, detecting menus, etc.).

        Returns:
            ActionDict: {'wait': True} - skips the turn (trivial bot behavior) when in PLAYERS_TURN.
                       {} - empty dict (no action) when not in a playing state to prevent
                            infinite loops on death screens or menus.
                       Later iterations will populate this with actual bot decisions based
                       on game_state (e.g., pathfinding, menu navigation, combat tactics).
        """
        # CRITICAL: Only return actions during PLAYERS_TURN
        # When in PLAYER_DEAD, menus, or other non-playing states, return empty action
        # to prevent the input loop from continuously feeding actions into the engine
        # and causing infinite AI loops or hangs
        from game_states import GameStates
        
        # Defensive: Check for valid game_state with current_state attribute
        if game_state and hasattr(game_state, 'current_state'):
            # Only generate actions during actual gameplay
            if game_state.current_state == GameStates.PLAYERS_TURN:
                # Throttle action generation to reduce tight-loop pressure; the
                # main loop handles frame pacing and event pumping.
                self._frame_counter += 1

                if self._frame_counter >= self._action_interval:
                    self._frame_counter = 0
                    return {'wait': True}

                return {}
            else:
                # Return empty action dict for non-playing states
                # This prevents the infinite loop bug where the bot would feed
                # actions even after player death or when in a menu
                return {}
        
        # Safety fallback: No valid game state, return no action
        return {}

