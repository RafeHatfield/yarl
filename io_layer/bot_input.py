"""Bot/autoplay input source implementation.

This module provides a BotInputSource class that implements the InputSource protocol
for automated/bot play modes. Phase 1 implements auto-exploration behavior, allowing
the bot to systematically explore the dungeon.
"""

import logging
from typing import Any, Optional

from io_layer.interfaces import ActionDict, InputSource

logger = logging.getLogger(__name__)


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
        self._failed_explore_attempts = 0  # Track consecutive failed explore start attempts on "fully explored"
        self._last_auto_explore_active = False  # Track if autoexplore was active last call
        self._fully_explored_detected = False  # Track if we've detected "All areas explored" condition

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
            self._last_auto_explore_active = True
            return {}
        
        # Auto-explore is not active - check if we can even start it
        # If autoexplore was active last frame and is now inactive, it completed or stopped
        if self._last_auto_explore_active and auto_explore and not auto_explore.is_active():
            # AutoExplore was just stopped - check the stop reason
            stop_reason = auto_explore.stop_reason or ""
            logger.debug(f"AutoExplore just stopped: {stop_reason}")
            
            # If it stopped because "All areas explored", we've reached a terminal condition in soak mode
            if "All areas explored" in stop_reason:
                self._fully_explored_detected = True
                logger.info(f"Bot soak: Floor fully explored condition detected")
            else:
                # Different stop reason - not a "fully explored" scenario
                self._fully_explored_detected = False
                self._failed_explore_attempts = 0
        
        # If we're in the "fully explored" state, track failed restart attempts
        if self._fully_explored_detected:
            # After 3 failed restart attempts on a fully explored floor, signal end of run
            if self._failed_explore_attempts >= 3:
                logger.info("Bot soak: Ending run - floor fully explored and cannot restart autoexplore after 3 failed attempts")
                self._failed_explore_attempts = 0
                self._fully_explored_detected = False
                self._last_auto_explore_active = False
                return {'bot_abort_run': True}
            
            # Log this restart attempt and increment counter
            self._failed_explore_attempts += 1
            logger.info(f"Bot soak: Floor fully explored. Restart attempt #{self._failed_explore_attempts}")
        
        # Try to start auto-explore (this will fail if map is fully explored, but we keep trying)
        self._auto_explore_started = True
        self._last_auto_explore_active = False
        return {'start_auto_explore': True}
    
    def reset_bot_run_state(self) -> None:
        """Reset bot run state for a new run.
        
        Called when starting a fresh bot run to clear exploration attempt tracking.
        """
        self._failed_explore_attempts = 0
        self._last_auto_explore_active = False
        self._auto_explore_started = False
        self._fully_explored_detected = False

