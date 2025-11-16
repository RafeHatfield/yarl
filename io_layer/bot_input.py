"""Bot/autoplay input source implementation.

This module provides a BotInputSource class that implements the InputSource protocol
for automated/bot play modes. Phase 1 implements auto-exploration behavior, allowing
the bot to systematically explore the dungeon.
"""

from typing import Any, Optional

from io_layer.interfaces import ActionDict, InputSource


class BotInputSource:
    """Input source implementation for automated/bot play.

    Phase 1: Auto-Exploration Bot
    - Automatically triggers auto-explore when the player has no active exploration
    - Lets the existing auto-explore system handle pathfinding and movement
    - Falls back to waiting if exploration completes or fails
    
    Phase 0 behavior (enemies don't act) is preserved - this is controlled by
    the AISystem's bot-mode flag, not by this input source.

    Attributes:
        _initialized: Marker flag indicating the bot is ready
        _frame_counter: Counter for throttling actions
        _action_interval: Number of frames between actions
        _auto_explore_started: Tracks if we've attempted to start auto-explore this session
    """

    def __init__(self, action_interval: int = 1) -> None:
        """Initialize the BotInputSource.

        Args:
            action_interval: Number of frames to wait between actions. The bot
                             will emit an action every Nth call when the game
                             is in PLAYERS_TURN.
        """
        self._initialized = True
        self._frame_counter = 0
        self._action_interval = action_interval
        self._auto_explore_started = False

    def next_action(self, game_state: Any) -> ActionDict:
        """Return the next bot action using auto-explore behavior.

        Phase 1 Strategy:
        1. If in PLAYERS_TURN and auto-explore is NOT active:
           - Trigger auto-explore via {'start_auto_explore': True}
        2. If auto-explore IS active:
           - Return {} to let ActionProcessor._process_auto_explore_turn() handle it
        3. If not in PLAYERS_TURN or game_state invalid:
           - Return {} to prevent infinite loops
        
        Args:
            game_state: The current game state object with player, entities, map, etc.

        Returns:
            ActionDict: 
                - {'start_auto_explore': True} - to initiate auto-explore
                - {} - when auto-explore is active or not in playing state
                - {'wait': True} - fallback if auto-explore cannot be started
        """
        # CRITICAL: Only return actions during PLAYERS_TURN
        # When in PLAYER_DEAD, menus, or other non-playing states, return empty action
        # to prevent the input loop from continuously feeding actions into the engine
        # and causing infinite AI loops or hangs
        from game_states import GameStates
        from components.component_registry import ComponentType
        
        # Defensive: Check for valid game_state with current_state attribute
        if not game_state or not hasattr(game_state, 'current_state'):
            return {}
        
        # Only generate actions during actual gameplay
        if game_state.current_state != GameStates.PLAYERS_TURN:
            # Return empty action dict for non-playing states
            # This prevents the infinite loop bug where the bot would feed
            # actions even after player death or when in a menu
            return {}
        
        # Throttle action generation to reduce tight-loop pressure
        self._frame_counter += 1
        if self._frame_counter < self._action_interval:
            return {}
        
        self._frame_counter = 0
        
        # Get player entity
        player = getattr(game_state, 'player', None)
        if not player:
            return {'wait': True}
        
        # Check if auto-explore is already active
        # Defensive: ensure player has get_component_optional method
        if not hasattr(player, 'get_component_optional'):
            return {'wait': True}
        
        auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
        
        if auto_explore and auto_explore.is_active():
            # Auto-explore is running - let ActionProcessor._process_auto_explore_turn() handle it
            # We return {} because the action processor automatically processes auto-explore turns
            return {}
        
        # Auto-explore is not active - trigger it
        # The ActionProcessor will handle creating/initializing the component if needed
        self._auto_explore_started = True
        return {'start_auto_explore': True}

