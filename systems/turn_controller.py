"""
Turn Controller for centralized turn flow management.

This module provides the TurnController class which manages game turn flow,
state transitions, and state preservation. It replaces scattered turn
transition logic with a single, testable system.

Benefits:
- Centralized turn transitions (no more scattered _transition_to_enemy_turn calls)
- Automatic state preservation (e.g., AMULET_OBTAINED persists across turns)
- Clean integration with StateManager
- Easy to extend for complex turn mechanics (assassins, time limits, etc.)

Example:
    # Before (scattered):
    _transition_to_enemy_turn(state_manager, turn_manager)
    
    # After (centralized):
    turn_controller.end_player_action(turn_consumed=True)
"""

from typing import Optional
import logging

from game_states import GameStates
from state_management.state_config import StateManager

logger = logging.getLogger(__name__)


class TurnController:
    """Manages game turn flow and state transitions.
    
    The TurnController centralizes all turn transition logic, providing:
    - Single point of control for turn flow
    - Automatic state preservation (from StateManager config)
    - Integration with both TurnManager (Phase 3) and GameStates (legacy)
    - Support for complex turn mechanics
    
    Attributes:
        state_manager: Game state manager for state queries and updates
        turn_manager: Optional TurnManager for phase-based turns
        preserved_state: State to restore after enemy turn (if any)
    
    Example:
        # Initialize
        turn_controller = TurnController(state_manager, turn_manager)
        
        # After player action
        turn_controller.end_player_action(turn_consumed=True)
        
        # After enemy turn
        turn_controller.end_enemy_turn()
    """
    
    def __init__(self, state_manager, turn_manager=None):
        """Initialize the TurnController.
        
        Args:
            state_manager: Game state manager instance
            turn_manager: Optional TurnManager for phase-based turns
        """
        self.state_manager = state_manager
        self.turn_manager = turn_manager
        self.preserved_state: Optional[GameStates] = None
        
        logger.debug("TurnController initialized")
    
    def end_player_action(self, turn_consumed: bool = True) -> None:
        """Handle end of player action and determine turn transition.
        
        This is the main entry point after any player action. It determines:
        1. Should this action consume a turn?
        2. Should we transition to enemy turn?
        3. Should we preserve the current state?
        
        Args:
            turn_consumed: Did this action consume a turn? Default True.
                          Set to False for actions like opening menus.
        
        Example:
            # Movement consumes a turn
            turn_controller.end_player_action(turn_consumed=True)
            
            # Opening inventory doesn't consume a turn
            turn_controller.end_player_action(turn_consumed=False)
        """
        if not turn_consumed:
            logger.debug("Action didn't consume turn - no transition")
            return
        
        current_state = self.state_manager.state.current_state
        
        # Check if this state should transition to enemy turn
        if not StateManager.should_transition_to_enemy(current_state):
            logger.debug(f"State {current_state} doesn't transition to enemy turn")
            return
        
        # Check if we should preserve this state
        if StateManager.should_preserve_after_enemy_turn(current_state):
            self.preserved_state = current_state
            logger.info(f"Preserving state {current_state} for restoration after enemy turn")
        else:
            self.preserved_state = None
        
        # Transition to enemy turn
        self._transition_to_enemy_turn()
    
    def end_enemy_turn(self) -> None:
        """Handle end of enemy turn and restore preserved state if needed.
        
        Called after all enemies have taken their turns. This will:
        1. Process environment phase (if using TurnManager)
        2. Restore preserved state (e.g., AMULET_OBTAINED)
        3. Or return to normal PLAYERS_TURN
        
        This is the key to solving the "state reset bug" from victory implementation!
        
        Example:
            # In ai_system after enemies finish
            turn_controller.end_enemy_turn()
            # State automatically restored to AMULET_OBTAINED if needed!
        """
        # Use TurnManager if available (Phase 3)
        if self.turn_manager:
            from engine.turn_manager import TurnPhase
            self.turn_manager.advance_turn()  # ENEMY → ENVIRONMENT
            
            # Process environment phase (status effects, etc.)
            # This would happen in a separate system
            
            # Advance to player phase
            self.turn_manager.advance_turn()  # ENVIRONMENT → PLAYER
        
        # Restore preserved state or return to PLAYERS_TURN
        if self.preserved_state:
            logger.info(f"Restoring preserved state: {self.preserved_state}")
            self.state_manager.set_game_state(self.preserved_state)
            self.preserved_state = None  # Clear after restoration
        else:
            self.state_manager.set_game_state(GameStates.PLAYERS_TURN)
    
    def _transition_to_enemy_turn(self) -> None:
        """Internal: Transition from player turn to enemy turn.
        
        Uses TurnManager if available (Phase 3), always keeps GameStates in sync.
        """
        # Use TurnManager if available (Phase 3)
        if self.turn_manager:
            from engine.turn_manager import TurnPhase
            self.turn_manager.advance_turn(TurnPhase.ENEMY)
        
        # Always keep GameStates in sync (backward compatibility)
        self.state_manager.set_game_state(GameStates.ENEMY_TURN)
        logger.debug("Transitioned to ENEMY_TURN")
    
    def force_state_transition(self, new_state: GameStates) -> None:
        """Force a state transition without turn logic.
        
        Use this for special cases like death, victory, menus, etc.
        Does NOT preserve state or handle turn transitions.
        
        Args:
            new_state: State to transition to
        
        Example:
            # Player died
            turn_controller.force_state_transition(GameStates.PLAYER_DEAD)
            
            # Victory
            turn_controller.force_state_transition(GameStates.VICTORY)
        """
        logger.info(f"Forcing state transition to: {new_state}")
        self.state_manager.set_game_state(new_state)
        self.preserved_state = None  # Clear any preserved state
    
    def is_state_preserved(self) -> bool:
        """Check if a state is currently preserved for restoration.
        
        Returns:
            True if a state will be restored after enemy turn
        """
        return self.preserved_state is not None
    
    def get_preserved_state(self) -> Optional[GameStates]:
        """Get the currently preserved state, if any.
        
        Returns:
            Preserved state or None
        """
        return self.preserved_state
    
    def clear_preserved_state(self) -> None:
        """Clear any preserved state without restoring it.
        
        Use this if something interrupts the normal turn flow
        (e.g., player death, game over).
        """
        if self.preserved_state:
            logger.warning(f"Clearing preserved state {self.preserved_state} without restoring")
            self.preserved_state = None


# Singleton accessor for convenience
_turn_controller_instance: Optional[TurnController] = None


def initialize_turn_controller(state_manager, turn_manager=None) -> TurnController:
    """Initialize the global TurnController instance.
    
    Args:
        state_manager: Game state manager
        turn_manager: Optional turn manager
    
    Returns:
        Initialized TurnController instance
    """
    global _turn_controller_instance
    _turn_controller_instance = TurnController(state_manager, turn_manager)
    logger.info("TurnController initialized globally")
    return _turn_controller_instance


def get_turn_controller() -> Optional[TurnController]:
    """Get the global TurnController instance.
    
    Returns:
        TurnController instance or None if not initialized
    """
    return _turn_controller_instance


def reset_turn_controller() -> None:
    """Reset the global TurnController instance.
    
    Useful for testing or game restart.
    """
    global _turn_controller_instance
    _turn_controller_instance = None
    logger.info("TurnController reset")

