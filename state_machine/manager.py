"""Enhanced state manager that integrates with existing game systems.

This module provides an enhanced state manager that extends the existing
GameStateManager with hierarchical states, event integration, and
advanced state management features.
"""

from typing import Any, Dict, List, Optional, Callable, Type
from dataclasses import dataclass, field
import logging
from enum import Enum, auto

from game_states import GameStates
from engine.game_state_manager import GameStateManager, GameState
from events import EventBus, get_event_bus, Event, EventResult, EventListener, event_handler

from .core import StateMachine, State, StateContext, StateResult, StateMachineError
from .hierarchical import HierarchicalState, StateHierarchy
from .events import StateEvent, StateEventType, StateChangeEvent, StateTransitionEvent


logger = logging.getLogger(__name__)


class StateManagerMode(Enum):
    """Operating modes for the enhanced state manager."""
    
    LEGACY = auto()         # Use legacy GameStates enum only
    ENHANCED = auto()       # Use enhanced state machine only
    HYBRID = auto()         # Use both systems with synchronization


@dataclass
class StateManagerConfig:
    """Configuration for the enhanced state manager."""
    
    # Operating mode
    mode: StateManagerMode = StateManagerMode.HYBRID
    
    # Event integration
    enable_events: bool = True
    event_bus: Optional[EventBus] = None
    
    # State machine configuration
    enable_hierarchical_states: bool = True
    enable_state_persistence: bool = True
    enable_state_history: bool = True
    max_history_size: int = 50
    
    # Performance settings
    enable_state_caching: bool = True
    enable_transition_validation: bool = True
    
    # Debugging and monitoring
    enable_state_logging: bool = True
    enable_performance_monitoring: bool = True
    log_level: str = "INFO"


class EnhancedStateManager(EventListener):
    """Enhanced state manager with hierarchical states and event integration.
    
    This class extends the existing GameStateManager with advanced features
    while maintaining backward compatibility with the existing game systems.
    """
    
    def __init__(self, config: StateManagerConfig = None, 
                 legacy_manager: GameStateManager = None):
        """Initialize the enhanced state manager.
        
        Args:
            config (StateManagerConfig, optional): Configuration options
            legacy_manager (GameStateManager, optional): Existing state manager to wrap
        """
        super().__init__("enhanced_state_manager")
        
        self.config = config or StateManagerConfig()
        self.legacy_manager = legacy_manager or GameStateManager()
        
        # Event integration
        self.event_bus = self.config.event_bus or get_event_bus()
        
        # Enhanced state machine
        self.state_machine = StateMachine("game_state_machine", self.event_bus)
        
        # Register as event listener after state machine is created
        if self.config.enable_events:
            try:
                self.event_bus.register_listener(self)
            except Exception as e:
                # Listener might already be registered, which is fine
                logger.debug(f"Could not register listener (might already exist): {e}")
        self.state_hierarchy = StateHierarchy(None)  # Will be set when states are added
        
        # State management
        self.state_registry: Dict[str, Type[State]] = {}
        self.state_instances: Dict[str, State] = {}
        self.context = StateContext(event_bus=self.event_bus)
        
        # State history and caching
        self.state_history: List[str] = []
        self.state_cache: Dict[str, Any] = {}
        
        # Synchronization between legacy and enhanced systems
        self.legacy_to_enhanced_map: Dict[GameStates, str] = {}
        self.enhanced_to_legacy_map: Dict[str, GameStates] = {}
        
        # Performance monitoring
        self.performance_stats = {
            'state_changes': 0,
            'transitions_executed': 0,
            'events_processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
        }
        
        # Callbacks
        self.state_change_callbacks: List[Callable[[str, str, StateContext], None]] = []
        self.transition_callbacks: List[Callable[[str, str, StateContext], None]] = []
        
        # Initialize default state mappings
        self._initialize_default_mappings()
        
        logger.info(f"Enhanced state manager initialized in {self.config.mode.name} mode")
    
    def _initialize_default_mappings(self) -> None:
        """Initialize default mappings between legacy and enhanced states."""
        # Map legacy GameStates to enhanced state IDs
        self.legacy_to_enhanced_map = {
            GameStates.PLAYERS_TURN: "player_turn",
            GameStates.ENEMY_TURN: "enemy_turn",
            GameStates.PLAYER_DEAD: "player_dead",
            GameStates.SHOW_INVENTORY: "show_inventory",
            GameStates.DROP_INVENTORY: "drop_inventory",
            GameStates.TARGETING: "targeting",
            GameStates.LEVEL_UP: "level_up",
            GameStates.CHARACTER_SCREEN: "character_screen",
        }
        
        # Create reverse mapping
        self.enhanced_to_legacy_map = {
            v: k for k, v in self.legacy_to_enhanced_map.items()
        }
    
    def register_state_class(self, state_class: Type[State], 
                           legacy_state: GameStates = None) -> None:
        """Register a state class with the manager.
        
        Args:
            state_class (Type[State]): State class to register
            legacy_state (GameStates, optional): Corresponding legacy state
        """
        # Create instance to get state_id
        try:
            # Try creating without parameters first (for game states)
            temp_instance = state_class()
            state_id = temp_instance.state_id
        except TypeError:
            # Fall back to creating with temp parameter
            temp_instance = state_class("temp")
            state_id = temp_instance.state_id
        
        self.state_registry[state_id] = state_class
        
        # Update mappings if legacy state provided
        if legacy_state:
            self.legacy_to_enhanced_map[legacy_state] = state_id
            self.enhanced_to_legacy_map[state_id] = legacy_state
        
        logger.debug(f"Registered state class: {state_class.__name__} -> {state_id}")
    
    def create_state_instance(self, state_id: str) -> Optional[State]:
        """Create an instance of a registered state.
        
        Args:
            state_id (str): ID of state to create
            
        Returns:
            State: Created state instance, None if not found
        """
        if state_id not in self.state_registry:
            logger.error(f"State class not registered: {state_id}")
            return None
        
        if state_id in self.state_instances:
            return self.state_instances[state_id]
        
        state_class = self.state_registry[state_id]
        try:
            # Try creating without parameters first (for game states)
            state_instance = state_class()
        except TypeError:
            # Fall back to creating with state_id parameter
            state_instance = state_class(state_id)
        
        self.state_instances[state_id] = state_instance
        self.state_machine.add_state(state_instance)
        
        logger.debug(f"Created state instance: {state_id}")
        return state_instance
    
    def start(self, initial_state: str = "player_turn") -> bool:
        """Start the enhanced state manager.
        
        Args:
            initial_state (str): Initial state to start with
            
        Returns:
            bool: True if started successfully
        """
        # Ensure initial state exists
        if not self.create_state_instance(initial_state):
            logger.error(f"Cannot start - initial state not found: {initial_state}")
            return False
        
        # Start the state machine
        success = self.state_machine.start(initial_state)
        
        if success:
            # Synchronize with legacy manager if in hybrid mode
            if self.config.mode == StateManagerMode.HYBRID:
                self._sync_to_legacy(initial_state)
            
            # Add to history
            if self.config.enable_state_history:
                self.state_history.append(initial_state)
            
            # Dispatch state change event
            if self.config.enable_events:
                event = StateChangeEvent(
                    previous_state=None,
                    new_state=initial_state,
                    context_data=self.context.data.copy()
                )
                self.event_bus.dispatch(event)
            
            logger.info(f"Enhanced state manager started with initial state: {initial_state}")
        
        return success
    
    def stop(self) -> None:
        """Stop the enhanced state manager."""
        current_state = self.get_current_state_id()
        
        self.state_machine.stop()
        
        # Dispatch stop event
        if self.config.enable_events and current_state:
            event = StateChangeEvent(
                previous_state=current_state,
                new_state=None,
                context_data=self.context.data.copy()
            )
            self.event_bus.dispatch(event)
        
        logger.info("Enhanced state manager stopped")
    
    def transition_to(self, state_id: str, force: bool = False, 
                     transition_data: Dict[str, Any] = None) -> bool:
        """Transition to a specific state.
        
        Args:
            state_id (str): ID of state to transition to
            force (bool): Whether to force the transition
            transition_data (Dict[str, Any], optional): Data for the transition
            
        Returns:
            bool: True if transition was successful
        """
        current_state_id = self.get_current_state_id()
        
        # Ensure target state exists
        if not self.create_state_instance(state_id):
            logger.error(f"Cannot transition - target state not found: {state_id}")
            return False
        
        # Set transition data
        if transition_data:
            self.context.transition_data.update(transition_data)
        
        # Execute transition
        success = self.state_machine.transition_to(state_id, force)
        
        if success:
            # Update performance stats
            self.performance_stats['state_changes'] += 1
            self.performance_stats['transitions_executed'] += 1
            
            # Synchronize with legacy manager if in hybrid mode
            if self.config.mode == StateManagerMode.HYBRID:
                self._sync_to_legacy(state_id)
            
            # Add to history
            if self.config.enable_state_history:
                self.state_history.append(state_id)
                if len(self.state_history) > self.config.max_history_size:
                    self.state_history.pop(0)
            
            # Dispatch transition event
            if self.config.enable_events:
                event = StateTransitionEvent(
                    from_state=current_state_id,
                    to_state=state_id,
                    transition_data=transition_data or {},
                    context_data=self.context.data.copy()
                )
                self.event_bus.dispatch(event)
            
            # Call transition callbacks
            for callback in self.transition_callbacks:
                try:
                    callback(current_state_id, state_id, self.context)
                except Exception as e:
                    logger.error(f"Error in transition callback: {e}")
            
            logger.debug(f"Transitioned: {current_state_id} -> {state_id}")
        
        return success
    
    def update(self, dt: float) -> None:
        """Update the state manager.
        
        Args:
            dt (float): Delta time since last update
        """
        if self.state_machine.is_running():
            self.state_machine.update(dt)
    
    def handle_event(self, event: Event) -> EventResult:
        """Handle an event in the state manager.
        
        Args:
            event (Event): Event to handle
            
        Returns:
            EventResult: Result of handling the event
        """
        self.performance_stats['events_processed'] += 1
        
        if self.state_machine.is_running():
            return self.state_machine.handle_event(event)
        
        return EventResult.CONTINUE
    
    def get_handled_events(self) -> List[str]:
        """Get list of event types this manager handles.
        
        Returns:
            List[str]: List of event type identifiers
        """
        return [
            "state.change_request",
            "state.transition_request",
            "game.player_turn",
            "game.enemy_turn",
            "game.player_death",
            "ui.inventory_open",
            "ui.targeting_start",
        ]
    
    @event_handler("state.change_request")
    def handle_state_change_request(self, event: Event) -> EventResult:
        """Handle state change request events.
        
        Args:
            event (Event): State change request event
            
        Returns:
            EventResult: Result of handling the event
        """
        target_state = event.data.get("target_state")
        force = event.data.get("force", False)
        transition_data = event.data.get("transition_data", {})
        
        if target_state:
            success = self.transition_to(target_state, force, transition_data)
            return EventResult.HANDLED if success else EventResult.ERROR
        
        return EventResult.CONTINUE
    
    def get_current_state_id(self) -> Optional[str]:
        """Get the current state ID.
        
        Returns:
            str: Current state ID, None if not running
        """
        current_state = self.state_machine.get_current_state()
        return current_state.state_id if current_state else None
    
    def get_current_state(self) -> Optional[State]:
        """Get the current state instance.
        
        Returns:
            State: Current state instance, None if not running
        """
        return self.state_machine.get_current_state()
    
    def get_previous_state_id(self) -> Optional[str]:
        """Get the previous state ID.
        
        Returns:
            str: Previous state ID, None if no previous state
        """
        previous_state = self.state_machine.get_previous_state()
        return previous_state.state_id if previous_state else None
    
    def get_state_history(self) -> List[str]:
        """Get the state history.
        
        Returns:
            List[str]: List of state IDs in chronological order
        """
        return self.state_history.copy()
    
    def get_context_data(self, key: str, default: Any = None) -> Any:
        """Get data from the state context.
        
        Args:
            key (str): Data key
            default (Any): Default value if key not found
            
        Returns:
            Any: Context data value or default
        """
        return self.context.get_data(key, default)
    
    def set_context_data(self, key: str, value: Any) -> None:
        """Set data in the state context.
        
        Args:
            key (str): Data key
            value (Any): Data value
        """
        self.context.set_data(key, value)
    
    def get_legacy_state(self) -> GameStates:
        """Get the corresponding legacy state.
        
        Returns:
            GameStates: Legacy state enum value
        """
        current_state_id = self.get_current_state_id()
        if current_state_id and current_state_id in self.enhanced_to_legacy_map:
            return self.enhanced_to_legacy_map[current_state_id]
        
        # Default fallback
        return GameStates.PLAYERS_TURN
    
    def set_legacy_state(self, legacy_state: GameStates) -> bool:
        """Set state based on legacy state enum.
        
        Args:
            legacy_state (GameStates): Legacy state to set
            
        Returns:
            bool: True if state was set successfully
        """
        if legacy_state in self.legacy_to_enhanced_map:
            enhanced_state_id = self.legacy_to_enhanced_map[legacy_state]
            return self.transition_to(enhanced_state_id)
        
        logger.warning(f"No enhanced state mapping for legacy state: {legacy_state}")
        return False
    
    def _sync_to_legacy(self, enhanced_state_id: str) -> None:
        """Synchronize enhanced state to legacy manager.
        
        Args:
            enhanced_state_id (str): Enhanced state ID to sync
        """
        if enhanced_state_id in self.enhanced_to_legacy_map:
            legacy_state = self.enhanced_to_legacy_map[enhanced_state_id]
            self.legacy_manager.set_game_state(legacy_state)
            logger.debug(f"Synced to legacy: {enhanced_state_id} -> {legacy_state.name}")
    
    def _sync_from_legacy(self, legacy_state: GameStates) -> None:
        """Synchronize legacy state to enhanced manager.
        
        Args:
            legacy_state (GameStates): Legacy state to sync from
        """
        if legacy_state in self.legacy_to_enhanced_map:
            enhanced_state_id = self.legacy_to_enhanced_map[legacy_state]
            self.transition_to(enhanced_state_id)
            logger.debug(f"Synced from legacy: {legacy_state.name} -> {enhanced_state_id}")
    
    def add_state_change_callback(self, callback: Callable[[str, str, StateContext], None]) -> None:
        """Add a callback for state changes.
        
        Args:
            callback (Callable): Callback function
        """
        self.state_change_callbacks.append(callback)
    
    def remove_state_change_callback(self, callback: Callable[[str, str, StateContext], None]) -> bool:
        """Remove a state change callback.
        
        Args:
            callback (Callable): Callback function to remove
            
        Returns:
            bool: True if callback was removed
        """
        if callback in self.state_change_callbacks:
            self.state_change_callbacks.remove(callback)
            return True
        return False
    
    def add_transition_callback(self, callback: Callable[[str, str, StateContext], None]) -> None:
        """Add a callback for state transitions.
        
        Args:
            callback (Callable): Callback function
        """
        self.transition_callbacks.append(callback)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics.
        
        Returns:
            Dict[str, Any]: Performance statistics
        """
        stats = self.performance_stats.copy()
        stats.update(self.state_machine.get_stats())
        
        # Add cache hit rate
        total_cache_requests = stats['cache_hits'] + stats['cache_misses']
        if total_cache_requests > 0:
            stats['cache_hit_rate'] = stats['cache_hits'] / total_cache_requests
        else:
            stats['cache_hit_rate'] = 0.0
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset performance statistics."""
        self.performance_stats = {
            'state_changes': 0,
            'transitions_executed': 0,
            'events_processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
        }
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get comprehensive state information.
        
        Returns:
            Dict[str, Any]: State information dictionary
        """
        current_state = self.get_current_state()
        
        return {
            'current_state_id': self.get_current_state_id(),
            'current_state_name': current_state.name if current_state else None,
            'previous_state_id': self.get_previous_state_id(),
            'legacy_state': self.get_legacy_state().name,
            'state_duration': current_state.get_duration() if current_state else None,
            'context_data_keys': list(self.context.data.keys()),
            'history_length': len(self.state_history),
            'registered_states': list(self.state_registry.keys()),
            'running': self.state_machine.is_running(),
            'mode': self.config.mode.name,
        }
    
    def validate_state_machine(self) -> List[str]:
        """Validate the state machine configuration.
        
        Returns:
            List[str]: List of validation errors
        """
        errors = []
        
        # Check for missing state mappings
        for legacy_state in GameStates:
            if legacy_state not in self.legacy_to_enhanced_map:
                errors.append(f"No enhanced state mapping for legacy state: {legacy_state.name}")
        
        # Check for orphaned enhanced states
        for enhanced_state_id in self.enhanced_to_legacy_map:
            if enhanced_state_id not in self.state_registry:
                errors.append(f"Enhanced state not registered: {enhanced_state_id}")
        
        # Validate state hierarchy if enabled
        if self.config.enable_hierarchical_states and self.state_hierarchy:
            hierarchy_errors = self.state_hierarchy.validate_hierarchy()
            errors.extend(hierarchy_errors)
        
        return errors
    
    def __str__(self) -> str:
        """String representation of the state manager."""
        current = self.get_current_state_id() or "None"
        return f"EnhancedStateManager(current={current}, mode={self.config.mode.name})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the state manager."""
        return (f"EnhancedStateManager(current_state='{self.get_current_state_id()}', "
                f"mode={self.config.mode.name}, states={len(self.state_registry)}, "
                f"running={self.state_machine.is_running()})")
