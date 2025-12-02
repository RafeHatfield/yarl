"""Bot/autoplay input source implementation.

This module provides a BotInputSource class that implements the InputSource protocol
for automated/bot play modes. Phase 1 implements auto-exploration behavior, allowing
the bot to systematically explore the dungeon.
"""

import logging
from typing import Any, Optional

from io_layer.interfaces import ActionDict, InputSource
from io_layer.bot_brain import BotBrain

logger = logging.getLogger(__name__)


class BotInputSource:
    """Input source implementation for automated/bot play.

    Phase 1: Auto-Exploration Bot
    - Automatically triggers auto-explore when the player has no active exploration
    - Lets the existing auto-explore system handle pathfinding and movement
    - Falls back to waiting if exploration completes or fails
    
    Phase 0 behavior (enemies don't act) is preserved - this is controlled by
    the AISystem's bot-mode flag, not by this input source.
    
    Supports configurable bot personas for different playstyles.

    Attributes:
        _initialized: Marker flag indicating the bot is ready
        _frame_counter: Counter for throttling actions
        _action_interval: Number of frames between actions
        _auto_explore_started: Tracks if we've attempted to start auto-explore this session
        bot_brain: BotBrain instance with persona configuration
    """

    def __init__(
        self, 
        action_interval: int = 1, 
        debug: bool = False,
        persona: str = None
    ) -> None:
        """Initialize the BotInputSource.

        Args:
            action_interval: Number of frames to wait between actions. The bot
                             will emit an action every Nth call when the game
                             is in PLAYERS_TURN.
            debug: Enable debug logging in BotBrain
            persona: Bot persona name (balanced, cautious, aggressive, greedy, speedrunner).
                     Defaults to "balanced" if not specified.
        """
        self._initialized = True
        self._frame_counter = 0
        self._action_interval = action_interval
        self._auto_explore_started = False
        self._failed_explore_attempts = 0  # Track consecutive failed explore start attempts on "fully explored"
        self._last_auto_explore_active = False  # Track if autoexplore was active last call
        self._fully_explored_detected = False  # Track if we've detected "All areas explored" condition
        self.bot_brain = BotBrain(debug=debug, persona=persona)
    
    def _is_soak_mode(self, game_state: Any) -> bool:
        """Check if we are in bot soak mode.
        
        Soak mode is detected via game_state.constants["bot_soak_mode"] flag.
        In soak mode, enemies are disabled and bot should only explore, never engage in combat.
        
        Args:
            game_state: Game state object with constants dict
            
        Returns:
            True if in soak mode, False otherwise
        """
        if not game_state or not hasattr(game_state, 'constants'):
            return False
        
        constants = getattr(game_state, 'constants', {})
        return constants.get("bot_soak_mode", False)

    def next_action(self, game_state: Any) -> ActionDict:
        """Return the next bot action using auto-explore behavior with BotBrain delegation.

        Phase 1 + Phase 2 Strategy:
        1. Check if in PLAYERS_TURN and throttling allows action
        2. If auto-explore IS active: return {} immediately (Phase 1)
        3. Try BotBrain delegation for EXPLORE/COMBAT/LOOT decisions (Phase 2)
        4. Fall back to Phase 1 auto-explore behavior if BotBrain unavailable or fails
        5. Handle soak-specific terminal conditions
        
        Args:
            game_state: The current game state object with player, entities, map, etc.

        Returns:
            ActionDict: 
                - {'start_auto_explore': True} - to initiate auto-explore (Phase 1)
                - {} - when auto-explore is active or not in playing state
                - Other BotBrain actions (Phase 2) or bot_abort_run (soak)
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
        
        # Get player entity for auto-explore check and soak-related tracking
        player = getattr(game_state, 'player', None)
        if not player:
            return {'wait': True}
        
        # REQUIRED FIX 1: Defensive fallback for missing get_component_optional method
        if not hasattr(player, "get_component_optional"):
            return {'wait': True}
        
        # AUTO-EXPLORE SHORT-CIRCUIT (Phase 1 compatibility)
        # Check if auto-explore is already active
        auto_explore = None
        auto_explore_active = False
        
        if hasattr(player, 'get_component_optional') and callable(player.get_component_optional):
            try:
                auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
                auto_explore_active = auto_explore and callable(getattr(auto_explore, 'is_active', None)) and auto_explore.is_active()
            except (AttributeError, TypeError):
                # Player is a mock or incomplete - will use fallback below
                auto_explore_active = False
        
        # USE BOTBRAIN FOR ALL BOT MODES (regular --bot and --bot-soak)
        # BotBrain provides: combat, loot, potion-drinking, equipment, stairs descent
        # The only difference in soak mode is enemy AI being disabled (handled in engine_integration)
        # This ensures --bot and --bot-soak have identical bot behavior
        action = None
        try:
            action = self.bot_brain.decide_action(game_state)
        except Exception as e:
            # BotBrain raised an exception - will use fallback
            logger.debug(f"BotBrain.decide_action raised exception: {e}, falling back to Phase 1")
            action = None
        
        # If BotBrain returned a valid action dict, use it
        if isinstance(action, dict) and action:
            # BotBrain returned a non-empty action (Phase 2 behavior)
            self._auto_explore_started = True
            self._last_auto_explore_active = auto_explore_active
            return action
        
        # Fallback: Start auto-explore if available
        if auto_explore is not None or hasattr(player, 'get_component_optional'):
            self._auto_explore_started = True
            self._last_auto_explore_active = auto_explore_active
            return {"start_auto_explore": True}
        else:
            self._last_auto_explore_active = auto_explore_active
            return {}
    
    def reset_bot_run_state(self) -> None:
        """Reset bot run state for a new run.
        
        Called when starting a fresh bot run to clear exploration attempt tracking.
        """
        self._failed_explore_attempts = 0
        self._last_auto_explore_active = False
        self._auto_explore_started = False
        self._fully_explored_detected = False

