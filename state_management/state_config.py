"""
Centralized game state configuration.

This module is the SINGLE SOURCE OF TRUTH for game state behavior.
All systems consult this configuration instead of hardcoding state checks.

Benefits:
- Adding new state = one config entry, not changes across 5 files
- Self-documenting (state behavior is explicit)
- Eliminates duplication (input_handlers + input_system no longer duplicate)
- Easy to test (test config, not scattered logic)

Example:
    # Before (scattered across files):
    if game_state in (GameStates.PLAYERS_TURN, GameStates.RUBY_HEART_OBTAINED):
        # Allow movement
    
    # After (centralized):
    if StateManager.allows_movement(game_state):
        # Allow movement
"""

from typing import Optional, Callable, Dict

from game_states import GameStates

try:  # Backwards compatibility for legacy imports
except Exception:  # pragma: no cover - fallback if engine module missing
    GameState = None  # type: ignore


# Legacy import support: GameState was moved to engine.game_state_manager
# but tests may still import it from here
from engine.game_state_manager import GameState


class StateConfig:
    """Configuration for a single game state.
    
    This class defines all behavioral properties of a game state:
    - What input handler to use
    - What actions are allowed (movement, pickup, inventory)
    - Turn flow behavior (transitions, preservation)
    - AI processing
    
    Attributes:
        input_handler: Function to handle keyboard input for this state
        allows_movement: Can player move in this state?
        allows_pickup: Can player pick up items?
        allows_inventory: Can player access inventory?
        transition_to_enemy: Should actions transition to enemy turn?
        preserve_after_enemy_turn: Should this state be restored after enemy turn?
        ai_processes: Do AI entities process turns in this state?
        description: Human-readable description of state
    """
    
    def __init__(
        self,
        input_handler: Optional[Callable] = None,
        allows_movement: bool = False,
        allows_pickup: bool = False,
        allows_inventory: bool = False,
        transition_to_enemy: bool = False,
        preserve_after_enemy_turn: bool = False,
        ai_processes: bool = False,
        description: str = ""
    ):
        self.input_handler = input_handler
        self.allows_movement = allows_movement
        self.allows_pickup = allows_pickup
        self.allows_inventory = allows_inventory
        self.transition_to_enemy = transition_to_enemy
        self.preserve_after_enemy_turn = preserve_after_enemy_turn
        self.ai_processes = ai_processes
        self.description = description


# =============================================================================
# THE SINGLE SOURCE OF TRUTH
# =============================================================================
# NOTE: Handler imports delayed to _initialize_state_configurations() to avoid circular imports

STATE_CONFIGURATIONS: Dict[GameStates, StateConfig] = {}


def _initialize_state_configurations():
    """Initialize state configurations with handler functions.
    
    This is called lazily to avoid circular import issues.
    input_handlers imports StateManager, so we can't import handlers at module level.
    """
    if STATE_CONFIGURATIONS:
        return  # Already initialized
    
    # Import handlers here to avoid circular import
        handle_player_turn_keys,
        handle_targeting_keys,
        handle_inventory_keys,  # Still used for THROW_SELECT_ITEM
        handle_player_dead_keys,
        handle_level_up_menu,
        handle_character_screen,
    )
    
    STATE_CONFIGURATIONS.update({
    # Normal player turn - full control
    GameStates.PLAYERS_TURN: StateConfig(
        input_handler=handle_player_turn_keys,
        allows_movement=True,
        allows_pickup=True,
        allows_inventory=True,
        transition_to_enemy=True,
        description="Normal player turn - can move, act, use inventory"
    ),
    
    # Player has Ruby Heart - looking for portal (same controls as PLAYERS_TURN)
    GameStates.RUBY_HEART_OBTAINED: StateConfig(
        input_handler=handle_player_turn_keys,
        allows_movement=True,
        allows_pickup=True,
        allows_inventory=True,
        transition_to_enemy=True,
        preserve_after_enemy_turn=True,  # KEY: Don't reset to PLAYERS_TURN!
        description="Player has Aurelyn's Ruby Heart - looking for portal to confrontation"
    ),
    
    # Enemies taking their turns
    GameStates.ENEMY_TURN: StateConfig(
        input_handler=None,  # No player input during enemy turn
        allows_movement=False,
        allows_pickup=False,
        allows_inventory=False,
        ai_processes=True,
        description="Enemies processing their turns"
    ),
    
    # Selecting spell/wand target
    GameStates.TARGETING: StateConfig(
        input_handler=handle_targeting_keys,
        allows_movement=False,  # Targeting, not moving
        allows_pickup=False,
        allows_inventory=False,
        description="Selecting spell or wand target"
    ),
    
    # Selecting item to throw
    GameStates.THROW_SELECT_ITEM: StateConfig(
        input_handler=handle_inventory_keys,
        allows_movement=False,
        allows_pickup=False,
        allows_inventory=False,
        description="Selecting item to throw"
    ),
    
    # Throwing item targeting
    GameStates.THROW_TARGETING: StateConfig(
        input_handler=handle_targeting_keys,
        allows_movement=False,
        allows_pickup=False,
        allows_inventory=False,
        description="Targeting thrown item"
    ),
    
    # DEPRECATED: Viewing inventory (use sidebar UI instead)
    GameStates.SHOW_INVENTORY: StateConfig(
        input_handler=handle_inventory_keys,
        allows_movement=False,
        allows_pickup=False,
        description="DEPRECATED: Viewing inventory to use item (use sidebar UI)"
    ),
    
    # DEPRECATED: Dropping items (use sidebar UI instead)
    GameStates.DROP_INVENTORY: StateConfig(
        input_handler=handle_inventory_keys,
        allows_movement=False,
        allows_pickup=False,
        description="DEPRECATED: Selecting item to drop (use sidebar UI)"
    ),
    
    # Player is dead
    GameStates.PLAYER_DEAD: StateConfig(
        input_handler=handle_player_dead_keys,
        allows_movement=False,
        allows_pickup=False,
        allows_inventory=False,
        description="Player has died"
    ),
    
    # Choosing level up bonus
    GameStates.LEVEL_UP: StateConfig(
        input_handler=handle_level_up_menu,
        allows_movement=False,
        allows_pickup=False,
        allows_inventory=False,
        description="Choosing level up bonus"
    ),
    
    # Viewing character stats
    GameStates.CHARACTER_SCREEN: StateConfig(
        input_handler=handle_character_screen,
        allows_movement=False,
        allows_pickup=False,
        allows_inventory=False,
        description="Viewing character sheet"
    ),
    
    # Talking to NPC (Phase 3: Ghost Guide)
    GameStates.NPC_DIALOGUE: StateConfig(
        input_handler=None,  # Handled by dialogue screen
        allows_movement=False,
        allows_pickup=False,
        allows_inventory=False,
        description="Talking to NPC - making dialogue choices"
    ),
    
    # Tier 2: Wizard Mode debug menu
    GameStates.WIZARD_MENU: StateConfig(
        input_handler=None,  # Handled by wizard menu screen
        allows_movement=False,
        allows_pickup=False,
        allows_inventory=False,
        description="Wizard Mode debug menu - testing/development commands"
    ),
    
    # Entity confrontation (final choice)
    GameStates.CONFRONTATION: StateConfig(
        input_handler=None,  # Handled by confrontation screen directly
        allows_movement=False,
        allows_pickup=False,
        allows_inventory=False,
        description="Entity confrontation - making final choice"
    ),
    
    # Victory screen
    GameStates.VICTORY: StateConfig(
        input_handler=None,  # Handled by victory screen
        allows_movement=False,
        allows_pickup=False,
        allows_inventory=False,
        description="Victory - good ending"
    ),
    
    # Failure screen
    GameStates.FAILURE: StateConfig(
        input_handler=None,  # Handled by failure screen
        allows_movement=False,
        allows_pickup=False,
        allows_inventory=False,
        description="Failure - bad ending"
    ),
    })  # Close the update() call


# =============================================================================
# STATE MANAGER - Centralized State Query Interface
# =============================================================================

class StateManager:
    """
    Centralized interface for querying game state behavior.
    
    All systems should use this instead of hardcoding state checks.
    This eliminates duplication and makes adding new states trivial.
    
    Example Usage:
        # Check if movement is allowed:
        if StateManager.allows_movement(current_state):
            player.move(dx, dy)
        
        # Get input handler:
        handler = StateManager.get_input_handler(current_state)
        if handler:
            action = handler(key)
        
        # Check if state should be preserved:
        if StateManager.should_preserve_after_enemy_turn(current_state):
            # Save state for restoration
    """
    
    @staticmethod
    def get_config(state: GameStates) -> StateConfig:
        """Get configuration for a state.
        
        Args:
            state: The game state to query
            
        Returns:
            StateConfig for the given state
            
        Raises:
            ValueError: If state has no configuration
        """
        # Lazy initialization to avoid circular imports
        _initialize_state_configurations()
        
        if state not in STATE_CONFIGURATIONS:
            raise ValueError(
                f"No configuration found for state: {state}. "
                f"Add it to STATE_CONFIGURATIONS in state_management/state_config.py"
            )
        return STATE_CONFIGURATIONS[state]
    
    @staticmethod
    def allows_movement(state: GameStates) -> bool:
        """Can player move in this state?
        
        Args:
            state: The game state to query
            
        Returns:
            True if movement is allowed, False otherwise
        """
        return StateManager.get_config(state).allows_movement
    
    @staticmethod
    def allows_pickup(state: GameStates) -> bool:
        """Can player pick up items in this state?
        
        Args:
            state: The game state to query
            
        Returns:
            True if pickup is allowed, False otherwise
        """
        return StateManager.get_config(state).allows_pickup
    
    @staticmethod
    def allows_inventory(state: GameStates) -> bool:
        """Can player access inventory in this state?
        
        Args:
            state: The game state to query
            
        Returns:
            True if inventory access is allowed, False otherwise
        """
        return StateManager.get_config(state).allows_inventory
    
    @staticmethod
    def get_input_handler(state: GameStates) -> Optional[Callable]:
        """Get the input handler function for this state.
        
        Args:
            state: The game state to query
            
        Returns:
            Input handler function, or None if state has no handler
        """
        return StateManager.get_config(state).input_handler
    
    @staticmethod
    def should_preserve_after_enemy_turn(state: GameStates) -> bool:
        """Should this state be restored after enemy turn?
        
        Some states (like RUBY_HEART_OBTAINED) need to persist across turns.
        This flag tells the turn system to restore the state after enemies act.
        
        Args:
            state: The game state to query
            
        Returns:
            True if state should be preserved, False if should return to PLAYERS_TURN
        """
        return StateManager.get_config(state).preserve_after_enemy_turn
    
    @staticmethod
    def should_transition_to_enemy(state: GameStates) -> bool:
        """Should actions in this state transition to enemy turn?
        
        Args:
            state: The game state to query
            
        Returns:
            True if actions should cause turn transitions, False otherwise
        """
        return StateManager.get_config(state).transition_to_enemy
    
    @staticmethod
    def ai_processes_in_state(state: GameStates) -> bool:
        """Do AI entities process turns in this state?
        
        Args:
            state: The game state to query
            
        Returns:
            True if AI should process, False otherwise
        """
        return StateManager.get_config(state).ai_processes
    
    @staticmethod
    def get_description(state: GameStates) -> str:
        """Get human-readable description of state.
        
        Args:
            state: The game state to query
            
        Returns:
            Description string
        """
        return StateManager.get_config(state).description
    
    @staticmethod
    def validate_all_states():
        """Validate that all GameStates have configurations.
        
        Raises:
            ValueError: If any state is missing a configuration
        """
        missing = []
        for state in GameStates:
            if state not in STATE_CONFIGURATIONS:
                missing.append(state)
        
        if missing:
            raise ValueError(
                f"The following states are missing configurations: {missing}. "
                f"Add them to STATE_CONFIGURATIONS in state_management/state_config.py"
            )

