"""Game-specific state implementations.

This module provides concrete state implementations for the roguelike game,
integrating with existing game systems while providing enhanced functionality.
"""

from typing import Any, Dict, Optional
from abc import abstractmethod
import logging

from game_states import GameStates
from events import EventBus, get_event_bus, Event, EventResult

from .core import State, StateContext, StateResult
from .hierarchical import HierarchicalState
from .events import StateEventType, create_state_lifecycle_event


logger = logging.getLogger(__name__)


class GameStateContext(StateContext):
    """Extended state context for game-specific data."""
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        """Initialize game state context.
        
        Args:
            event_bus (EventBus, optional): Event bus for integration
        """
        super().__init__(event_bus=event_bus)
        
        # Game-specific context data
        self.player = None
        self.entities = []
        self.game_map = None
        self.message_log = None
        self.fov_map = None
        self.fov_recompute = True
        self.targeting_item = None
        self.mouse = None
        self.key = None
        self.constants = None
    
    def update_from_legacy_state(self, legacy_state) -> None:
        """Update context from legacy GameState object.
        
        Args:
            legacy_state: Legacy GameState object
        """
        self.player = getattr(legacy_state, 'player', None)
        self.entities = getattr(legacy_state, 'entities', [])
        self.game_map = getattr(legacy_state, 'game_map', None)
        self.message_log = getattr(legacy_state, 'message_log', None)
        self.fov_map = getattr(legacy_state, 'fov_map', None)
        self.fov_recompute = getattr(legacy_state, 'fov_recompute', True)
        self.targeting_item = getattr(legacy_state, 'targeting_item', None)
        self.mouse = getattr(legacy_state, 'mouse', None)
        self.key = getattr(legacy_state, 'key', None)
        self.constants = getattr(legacy_state, 'constants', None)


class BaseGameState(State):
    """Base class for all game states with common functionality."""
    
    def __init__(self, state_id: str, name: str = None, legacy_state: GameStates = None):
        """Initialize base game state.
        
        Args:
            state_id (str): Unique identifier for this state
            name (str, optional): Human-readable name for this state
            legacy_state (GameStates, optional): Corresponding legacy state
        """
        super().__init__(state_id, name)
        self.legacy_state = legacy_state
        
        # Game state configuration
        self.handles_input = True
        self.renders_ui = True
        self.updates_entities = False
        self.processes_ai = False
        
        # Performance tracking
        self.update_count = 0
        self.total_update_time = 0.0
    
    def enter(self, context: StateContext) -> StateResult:
        """Enter the game state.
        
        Args:
            context (StateContext): State context
            
        Returns:
            StateResult: Result of entering the state
        """
        logger.debug(f"Entering game state: {self.state_id}")
        
        # Dispatch lifecycle event
        if self.event_bus:
            event = create_state_lifecycle_event(
                StateEventType.STATE_ENTER, self.state_id,
                {'legacy_state': self.legacy_state.name if self.legacy_state else None},
                source="game_state"
            )
            self.event_bus.dispatch(event)
        
        return self.on_enter(context)
    
    def exit(self, context: StateContext) -> StateResult:
        """Exit the game state.
        
        Args:
            context (StateContext): State context
            
        Returns:
            StateResult: Result of exiting the state
        """
        logger.debug(f"Exiting game state: {self.state_id}")
        
        # Calculate average update time
        avg_update_time = (self.total_update_time / self.update_count 
                          if self.update_count > 0 else 0.0)
        
        # Dispatch lifecycle event
        if self.event_bus:
            event = create_state_lifecycle_event(
                StateEventType.STATE_EXIT, self.state_id,
                {
                    'update_count': self.update_count,
                    'avg_update_time': avg_update_time,
                    'total_duration': self.get_duration(),
                },
                duration=self.get_duration(),
                source="game_state"
            )
            self.event_bus.dispatch(event)
        
        return self.on_exit(context)
    
    def update(self, context: StateContext, dt: float) -> StateResult:
        """Update the game state.
        
        Args:
            context (StateContext): State context
            dt (float): Delta time since last update
            
        Returns:
            StateResult: Result of the update
        """
        import time
        start_time = time.time()
        
        result = self.on_update(context, dt)
        
        # Update performance tracking
        self.update_count += 1
        self.total_update_time += time.time() - start_time
        
        return result
    
    @abstractmethod
    def on_enter(self, context: StateContext) -> StateResult:
        """Called when entering this game state.
        
        Args:
            context (StateContext): State context
            
        Returns:
            StateResult: Result of entering the state
        """
        pass
    
    @abstractmethod
    def on_exit(self, context: StateContext) -> StateResult:
        """Called when exiting this game state.
        
        Args:
            context (StateContext): State context
            
        Returns:
            StateResult: Result of exiting the state
        """
        pass
    
    @abstractmethod
    def on_update(self, context: StateContext, dt: float) -> StateResult:
        """Called when updating this game state.
        
        Args:
            context (StateContext): State context
            dt (float): Delta time since last update
            
        Returns:
            StateResult: Result of the update
        """
        pass
    
    def can_handle_input(self) -> bool:
        """Check if this state can handle input.
        
        Returns:
            bool: True if state handles input
        """
        return self.handles_input
    
    def should_render_ui(self) -> bool:
        """Check if this state should render UI.
        
        Returns:
            bool: True if state renders UI
        """
        return self.renders_ui
    
    def should_update_entities(self) -> bool:
        """Check if this state should update entities.
        
        Returns:
            bool: True if state updates entities
        """
        return self.updates_entities
    
    def should_process_ai(self) -> bool:
        """Check if this state should process AI.
        
        Returns:
            bool: True if state processes AI
        """
        return self.processes_ai


class PlayerTurnState(BaseGameState):
    """State for player turn processing."""
    
    def __init__(self):
        """Initialize player turn state."""
        super().__init__("player_turn", "Player Turn", GameStates.PLAYERS_TURN)
        self.handles_input = True
        self.renders_ui = True
        self.updates_entities = False
        self.processes_ai = False
    
    def on_enter(self, context: StateContext) -> StateResult:
        """Enter player turn state."""
        # Reset FOV recompute flag if needed
        if hasattr(context, 'fov_recompute'):
            context.fov_recompute = True
        
        return StateResult.CONTINUE
    
    def on_exit(self, context: StateContext) -> StateResult:
        """Exit player turn state."""
        return StateResult.CONTINUE
    
    def on_update(self, context: StateContext, dt: float) -> StateResult:
        """Update player turn state."""
        # Player turn state is primarily input-driven
        # Most logic happens in response to input events
        return StateResult.CONTINUE
    
    def handle_event(self, event: Event, context: StateContext) -> StateResult:
        """Handle events in player turn state."""
        # Handle player action events
        if event.event_type == "player.action":
            action_type = event.data.get("action_type")
            
            if action_type == "move":
                # Player moved, switch to enemy turn
                return StateResult.TRANSITION
            elif action_type == "wait":
                # Player waited, switch to enemy turn
                return StateResult.TRANSITION
            elif action_type == "inventory":
                # Open inventory, but stay in player turn
                return StateResult.CONTINUE
        
        return StateResult.CONTINUE


class EnemyTurnState(BaseGameState):
    """State for enemy turn processing."""
    
    def __init__(self):
        """Initialize enemy turn state."""
        super().__init__("enemy_turn", "Enemy Turn", GameStates.ENEMY_TURN)
        self.handles_input = False
        self.renders_ui = True
        self.updates_entities = True
        self.processes_ai = True
    
    def on_enter(self, context: StateContext) -> StateResult:
        """Enter enemy turn state."""
        # Mark that AI processing should begin
        context.set_data("ai_processing_started", True)
        return StateResult.CONTINUE
    
    def on_exit(self, context: StateContext) -> StateResult:
        """Exit enemy turn state."""
        # Clear AI processing flag
        context.set_data("ai_processing_started", False)
        return StateResult.CONTINUE
    
    def on_update(self, context: StateContext, dt: float) -> StateResult:
        """Update enemy turn state."""
        # Check if AI processing is complete
        ai_complete = context.get_data("ai_processing_complete", False)
        
        if ai_complete:
            # AI turn is done, transition back to player turn
            context.set_data("ai_processing_complete", False)
            return StateResult.TRANSITION
        
        return StateResult.CONTINUE
    
    def handle_event(self, event: Event, context: StateContext) -> StateResult:
        """Handle events in enemy turn state."""
        if event.event_type == "ai.turn_complete":
            # AI system finished processing all entities
            context.set_data("ai_processing_complete", True)
            return StateResult.CONTINUE
        
        return StateResult.CONTINUE


class InventoryState(HierarchicalState):
    """Hierarchical state for inventory management."""
    
    def __init__(self):
        """Initialize inventory state."""
        super().__init__("inventory", "Inventory Management")
        self.legacy_state = GameStates.SHOW_INVENTORY
        self.handles_input = True
        self.renders_ui = True
        
        # Add child states for different inventory modes
        self._setup_child_states()
    
    def _setup_child_states(self) -> None:
        """Set up child states for inventory management."""
        # Show inventory child state
        show_inventory = ShowInventoryState()
        self.add_child_state(show_inventory, is_default=True)
        
        # Drop inventory child state
        drop_inventory = DropInventoryState()
        self.add_child_state(drop_inventory)
    
    def on_enter(self, context: StateContext) -> StateResult:
        """Enter inventory state."""
        logger.debug("Entering inventory management state")
        return StateResult.CONTINUE
    
    def on_exit(self, context: StateContext) -> StateResult:
        """Exit inventory state."""
        logger.debug("Exiting inventory management state")
        return StateResult.CONTINUE
    
    def on_update(self, context: StateContext, dt: float) -> StateResult:
        """Update inventory state."""
        return StateResult.CONTINUE
    
    def handle_event(self, event: Event, context: StateContext) -> StateResult:
        """Handle events in inventory state."""
        if event.event_type == "input.key":
            key = event.data.get("key")
            
            if key == "escape":
                # Exit inventory
                return StateResult.TRANSITION
            elif key == "d":
                # Switch to drop inventory mode
                self.transition_child_to("drop_inventory")
                return StateResult.CONTINUE
            elif key == "i":
                # Switch to show inventory mode
                self.transition_child_to("show_inventory")
                return StateResult.CONTINUE
        
        return StateResult.CONTINUE


class ShowInventoryState(BaseGameState):
    """State for showing inventory items."""
    
    def __init__(self):
        """Initialize show inventory state."""
        super().__init__("show_inventory", "Show Inventory", GameStates.SHOW_INVENTORY)
    
    def on_enter(self, context: StateContext) -> StateResult:
        """Enter show inventory state."""
        return StateResult.CONTINUE
    
    def on_exit(self, context: StateContext) -> StateResult:
        """Exit show inventory state."""
        return StateResult.CONTINUE
    
    def on_update(self, context: StateContext, dt: float) -> StateResult:
        """Update show inventory state."""
        return StateResult.CONTINUE


class DropInventoryState(BaseGameState):
    """State for dropping inventory items."""
    
    def __init__(self):
        """Initialize drop inventory state."""
        super().__init__("drop_inventory", "Drop Inventory", GameStates.DROP_INVENTORY)
    
    def on_enter(self, context: StateContext) -> StateResult:
        """Enter drop inventory state."""
        return StateResult.CONTINUE
    
    def on_exit(self, context: StateContext) -> StateResult:
        """Exit drop inventory state."""
        return StateResult.CONTINUE
    
    def on_update(self, context: StateContext, dt: float) -> StateResult:
        """Update drop inventory state."""
        return StateResult.CONTINUE


class TargetingState(BaseGameState):
    """State for targeting spells and abilities."""
    
    def __init__(self):
        """Initialize targeting state."""
        super().__init__("targeting", "Targeting", GameStates.TARGETING)
        self.handles_input = True
        self.renders_ui = True
    
    def on_enter(self, context: StateContext) -> StateResult:
        """Enter targeting state."""
        # Store the item being targeted
        targeting_item = context.get_data("targeting_item")
        if targeting_item:
            context.set_data("current_targeting_item", targeting_item)
        
        return StateResult.CONTINUE
    
    def on_exit(self, context: StateContext) -> StateResult:
        """Exit targeting state."""
        # Clear targeting data
        context.set_data("current_targeting_item", None)
        context.set_data("target_position", None)
        
        return StateResult.CONTINUE
    
    def on_update(self, context: StateContext, dt: float) -> StateResult:
        """Update targeting state."""
        return StateResult.CONTINUE
    
    def handle_event(self, event: Event, context: StateContext) -> StateResult:
        """Handle events in targeting state."""
        if event.event_type == "input.mouse":
            mouse_action = event.data.get("action")
            
            if mouse_action == "left_click":
                # Target selected
                x, y = event.data.get("position", (0, 0))
                context.set_data("target_position", (x, y))
                return StateResult.TRANSITION
            elif mouse_action == "right_click":
                # Cancel targeting
                return StateResult.TRANSITION
        
        elif event.event_type == "input.key":
            key = event.data.get("key")
            
            if key == "escape":
                # Cancel targeting
                return StateResult.TRANSITION
        
        return StateResult.CONTINUE


class CharacterScreenState(BaseGameState):
    """State for character screen display."""
    
    def __init__(self):
        """Initialize character screen state."""
        super().__init__("character_screen", "Character Screen", GameStates.CHARACTER_SCREEN)
        self.handles_input = True
        self.renders_ui = True
    
    def on_enter(self, context: StateContext) -> StateResult:
        """Enter character screen state."""
        return StateResult.CONTINUE
    
    def on_exit(self, context: StateContext) -> StateResult:
        """Exit character screen state."""
        return StateResult.CONTINUE
    
    def on_update(self, context: StateContext, dt: float) -> StateResult:
        """Update character screen state."""
        return StateResult.CONTINUE
    
    def handle_event(self, event: Event, context: StateContext) -> StateResult:
        """Handle events in character screen state."""
        if event.event_type == "input.key":
            key = event.data.get("key")
            
            if key in ("escape", "c"):
                # Exit character screen
                return StateResult.TRANSITION
        
        return StateResult.CONTINUE


class LevelUpState(BaseGameState):
    """State for level up screen."""
    
    def __init__(self):
        """Initialize level up state."""
        super().__init__("level_up", "Level Up", GameStates.LEVEL_UP)
        self.handles_input = True
        self.renders_ui = True
    
    def on_enter(self, context: StateContext) -> StateResult:
        """Enter level up state."""
        # Store level up options
        level_up_options = context.get_data("level_up_options", [])
        context.set_data("current_level_up_options", level_up_options)
        
        return StateResult.CONTINUE
    
    def on_exit(self, context: StateContext) -> StateResult:
        """Exit level up state."""
        # Clear level up data
        context.set_data("current_level_up_options", None)
        context.set_data("selected_level_up_option", None)
        
        return StateResult.CONTINUE
    
    def on_update(self, context: StateContext, dt: float) -> StateResult:
        """Update level up state."""
        return StateResult.CONTINUE
    
    def handle_event(self, event: Event, context: StateContext) -> StateResult:
        """Handle events in level up state."""
        if event.event_type == "input.key":
            key = event.data.get("key")
            
            # Check for level up option selection
            if key in ("a", "b", "c"):
                option_index = ord(key) - ord("a")
                context.set_data("selected_level_up_option", option_index)
                return StateResult.TRANSITION
        
        return StateResult.CONTINUE


class PlayerDeadState(BaseGameState):
    """State for player death screen."""
    
    def __init__(self):
        """Initialize player dead state."""
        super().__init__("player_dead", "Player Dead", GameStates.PLAYER_DEAD)
        self.handles_input = True
        self.renders_ui = True
        self.updates_entities = False
        self.processes_ai = False
    
    def on_enter(self, context: StateContext) -> StateResult:
        """Enter player dead state."""
        # Log player death
        logger.info("Player has died - entering death state")
        
        # Dispatch player death event
        if self.event_bus:
            from events import create_player_event, GameEventType
            death_event = create_player_event(
                GameEventType.PLAYER_DEATH,
                player_id=context.get_data("player_id", "player")
            )
            self.event_bus.dispatch(death_event)
        
        return StateResult.CONTINUE
    
    def on_exit(self, context: StateContext) -> StateResult:
        """Exit player dead state."""
        return StateResult.CONTINUE
    
    def on_update(self, context: StateContext, dt: float) -> StateResult:
        """Update player dead state."""
        # Player dead state is primarily input-driven
        return StateResult.CONTINUE
    
    def handle_event(self, event: Event, context: StateContext) -> StateResult:
        """Handle events in player dead state."""
        if event.event_type == "input.key":
            # Any key press should exit to main menu
            return StateResult.TRANSITION
        
        return StateResult.CONTINUE


class GameStateMachine:
    """Factory and utility class for game state machine setup."""
    
    @staticmethod
    def create_default_states() -> Dict[str, BaseGameState]:
        """Create the default set of game states.
        
        Returns:
            Dict[str, BaseGameState]: Dictionary of created states
        """
        states = {
            "player_turn": PlayerTurnState(),
            "enemy_turn": EnemyTurnState(),
            "inventory": InventoryState(),
            "targeting": TargetingState(),
            "character_screen": CharacterScreenState(),
            "level_up": LevelUpState(),
            "player_dead": PlayerDeadState(),
        }
        
        return states
    
    @staticmethod
    def setup_default_transitions(state_machine) -> None:
        """Set up default transitions between game states.
        
        Args:
            state_machine: State machine to configure
        """
        from .core import StateTransition
        
        # Player turn -> Enemy turn (after player action)
        state_machine.add_transition(StateTransition(
            from_state_id="player_turn",
            to_state_id="enemy_turn",
            trigger="player_action_complete",
            priority=10
        ))
        
        # Enemy turn -> Player turn (after AI processing)
        state_machine.add_transition(StateTransition(
            from_state_id="enemy_turn",
            to_state_id="player_turn",
            trigger="ai_turn_complete",
            priority=10
        ))
        
        # Player turn -> Inventory
        state_machine.add_transition(StateTransition(
            from_state_id="player_turn",
            to_state_id="inventory",
            trigger="open_inventory",
            priority=5
        ))
        
        # Inventory -> Player turn
        state_machine.add_transition(StateTransition(
            from_state_id="inventory",
            to_state_id="player_turn",
            trigger="close_inventory",
            priority=5
        ))
        
        # Player turn -> Targeting
        state_machine.add_transition(StateTransition(
            from_state_id="player_turn",
            to_state_id="targeting",
            trigger="start_targeting",
            priority=5
        ))
        
        # Targeting -> Player turn
        state_machine.add_transition(StateTransition(
            from_state_id="targeting",
            to_state_id="player_turn",
            trigger="end_targeting",
            priority=5
        ))
        
        # Player turn -> Character screen
        state_machine.add_transition(StateTransition(
            from_state_id="player_turn",
            to_state_id="character_screen",
            trigger="open_character_screen",
            priority=5
        ))
        
        # Character screen -> Player turn
        state_machine.add_transition(StateTransition(
            from_state_id="character_screen",
            to_state_id="player_turn",
            trigger="close_character_screen",
            priority=5
        ))
        
        # Any state -> Player dead (on player death)
        for state_id in ["player_turn", "enemy_turn", "inventory", "targeting", "character_screen"]:
            state_machine.add_transition(StateTransition(
                from_state_id=state_id,
                to_state_id="player_dead",
                trigger="player_death",
                priority=100  # Highest priority
            ))
        
        # Level up transitions
        state_machine.add_transition(StateTransition(
            from_state_id="player_turn",
            to_state_id="level_up",
            trigger="level_up",
            priority=20
        ))
        
        state_machine.add_transition(StateTransition(
            from_state_id="level_up",
            to_state_id="player_turn",
            trigger="level_up_complete",
            priority=20
        ))
