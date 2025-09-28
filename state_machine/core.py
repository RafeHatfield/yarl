"""Core state machine components and interfaces.

This module defines the fundamental state machine classes and interfaces
that form the foundation of the enhanced state management system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Set, Type, Union
from enum import Enum, auto
from dataclasses import dataclass, field
import time
import logging
from collections import defaultdict

from events import EventBus, get_event_bus, Event, EventResult


logger = logging.getLogger(__name__)


class StateResult(Enum):
    """Results of state operations."""
    
    CONTINUE = auto()       # Continue in current state
    TRANSITION = auto()     # Transition to another state
    PUSH = auto()          # Push new state onto stack
    POP = auto()           # Pop current state from stack
    ERROR = auto()         # Error occurred during operation


@dataclass
class StateContext:
    """Context information for state operations."""
    
    # Core data
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Timing information
    state_start_time: float = field(default_factory=time.time)
    last_update_time: float = field(default_factory=time.time)
    
    # State stack for hierarchical states
    state_stack: List[str] = field(default_factory=list)
    
    # Event integration
    event_bus: Optional[EventBus] = None
    
    # Transition information
    transition_data: Dict[str, Any] = field(default_factory=dict)
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get data from context.
        
        Args:
            key (str): Data key
            default (Any): Default value if key not found
            
        Returns:
            Any: Data value or default
        """
        return self.data.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """Set data in context.
        
        Args:
            key (str): Data key
            value (Any): Data value
        """
        self.data[key] = value
    
    def has_data(self, key: str) -> bool:
        """Check if data key exists.
        
        Args:
            key (str): Data key to check
            
        Returns:
            bool: True if key exists
        """
        return key in self.data
    
    def get_elapsed_time(self) -> float:
        """Get time elapsed since state started.
        
        Returns:
            float: Elapsed time in seconds
        """
        return time.time() - self.state_start_time
    
    def get_delta_time(self) -> float:
        """Get time since last update.
        
        Returns:
            float: Delta time in seconds
        """
        current_time = time.time()
        delta = current_time - self.last_update_time
        self.last_update_time = current_time
        return delta


class State(ABC):
    """Abstract base class for all states.
    
    States represent discrete modes of operation with their own logic
    for handling input, updating game state, and rendering.
    """
    
    def __init__(self, state_id: str, name: str = None):
        """Initialize the state.
        
        Args:
            state_id (str): Unique identifier for this state
            name (str, optional): Human-readable name for this state
        """
        self.state_id = state_id
        self.name = name or state_id
        self.active = False
        self.paused = False
        
        # State lifecycle tracking
        self.enter_time: Optional[float] = None
        self.exit_time: Optional[float] = None
        
        # Event integration
        self.event_bus: Optional[EventBus] = None
        
        # State metadata
        self.metadata: Dict[str, Any] = {}
    
    @abstractmethod
    def enter(self, context: StateContext) -> StateResult:
        """Called when entering this state.
        
        Args:
            context (StateContext): State context
            
        Returns:
            StateResult: Result of entering the state
        """
        pass
    
    @abstractmethod
    def exit(self, context: StateContext) -> StateResult:
        """Called when exiting this state.
        
        Args:
            context (StateContext): State context
            
        Returns:
            StateResult: Result of exiting the state
        """
        pass
    
    @abstractmethod
    def update(self, context: StateContext, dt: float) -> StateResult:
        """Update the state.
        
        Args:
            context (StateContext): State context
            dt (float): Delta time since last update
            
        Returns:
            StateResult: Result of the update
        """
        pass
    
    def handle_event(self, event: Event, context: StateContext) -> StateResult:
        """Handle an event in this state.
        
        Args:
            event (Event): Event to handle
            context (StateContext): State context
            
        Returns:
            StateResult: Result of handling the event
        """
        # Default implementation - states can override this
        return StateResult.CONTINUE
    
    def pause(self) -> None:
        """Pause this state."""
        self.paused = True
    
    def resume(self) -> None:
        """Resume this state."""
        self.paused = False
    
    def is_active(self) -> bool:
        """Check if state is active.
        
        Returns:
            bool: True if state is active
        """
        return self.active and not self.paused
    
    def get_duration(self) -> Optional[float]:
        """Get how long this state has been active.
        
        Returns:
            float: Duration in seconds, None if not active
        """
        if self.enter_time is None:
            return None
        
        end_time = self.exit_time or time.time()
        return end_time - self.enter_time
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata for this state.
        
        Args:
            key (str): Metadata key
            value (Any): Metadata value
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata for this state.
        
        Args:
            key (str): Metadata key
            default (Any): Default value if key not found
            
        Returns:
            Any: Metadata value or default
        """
        return self.metadata.get(key, default)
    
    def __str__(self) -> str:
        """String representation of the state."""
        return f"{self.__class__.__name__}(id={self.state_id}, active={self.active})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the state."""
        return (f"{self.__class__.__name__}(state_id='{self.state_id}', "
                f"name='{self.name}', active={self.active}, paused={self.paused})")


class TransitionGuard(ABC):
    """Abstract base class for transition guards.
    
    Guards determine whether a transition should be allowed to occur.
    """
    
    @abstractmethod
    def can_transition(self, from_state: State, to_state: State, 
                      context: StateContext) -> bool:
        """Check if transition is allowed.
        
        Args:
            from_state (State): State being transitioned from
            to_state (State): State being transitioned to
            context (StateContext): State context
            
        Returns:
            bool: True if transition is allowed
        """
        pass


class TransitionAction(ABC):
    """Abstract base class for transition actions.
    
    Actions are executed when a transition occurs.
    """
    
    @abstractmethod
    def execute(self, from_state: State, to_state: State, 
               context: StateContext) -> None:
        """Execute the transition action.
        
        Args:
            from_state (State): State being transitioned from
            to_state (State): State being transitioned to
            context (StateContext): State context
        """
        pass


@dataclass
class StateTransition:
    """Represents a transition between states."""
    
    from_state_id: str
    to_state_id: str
    trigger: Optional[str] = None
    guards: List[TransitionGuard] = field(default_factory=list)
    actions: List[TransitionAction] = field(default_factory=list)
    priority: int = 0
    
    def can_execute(self, from_state: State, to_state: State, 
                   context: StateContext) -> bool:
        """Check if this transition can be executed.
        
        Args:
            from_state (State): State being transitioned from
            to_state (State): State being transitioned to
            context (StateContext): State context
            
        Returns:
            bool: True if transition can be executed
        """
        for guard in self.guards:
            if not guard.can_transition(from_state, to_state, context):
                return False
        return True
    
    def execute(self, from_state: State, to_state: State, 
               context: StateContext) -> None:
        """Execute this transition.
        
        Args:
            from_state (State): State being transitioned from
            to_state (State): State being transitioned to
            context (StateContext): State context
        """
        for action in self.actions:
            action.execute(from_state, to_state, context)


class StateMachineError(Exception):
    """Exception raised by state machine operations."""
    
    def __init__(self, message: str, state_id: str = None, 
                 transition: StateTransition = None):
        """Initialize state machine error.
        
        Args:
            message (str): Error message
            state_id (str, optional): ID of state that caused error
            transition (StateTransition, optional): Transition that caused error
        """
        super().__init__(message)
        self.state_id = state_id
        self.transition = transition


class StateMachine:
    """Core state machine implementation.
    
    Manages states, transitions, and the overall state machine lifecycle.
    """
    
    def __init__(self, machine_id: str, event_bus: EventBus = None):
        """Initialize the state machine.
        
        Args:
            machine_id (str): Unique identifier for this state machine
            event_bus (EventBus, optional): Event bus for integration
        """
        self.machine_id = machine_id
        self.event_bus = event_bus or get_event_bus()
        
        # State management
        self.states: Dict[str, State] = {}
        self.current_state: Optional[State] = None
        self.previous_state: Optional[State] = None
        
        # Transition management
        self.transitions: List[StateTransition] = []
        self.transition_map: Dict[str, List[StateTransition]] = defaultdict(list)
        
        # State machine state
        self.running = False
        self.context = StateContext(event_bus=self.event_bus)
        
        # Statistics
        self.stats = {
            'transitions_executed': 0,
            'states_entered': 0,
            'total_runtime': 0.0,
            'state_durations': defaultdict(float),
        }
        
        # Lifecycle callbacks
        self.on_state_enter: Optional[Callable[[State, StateContext], None]] = None
        self.on_state_exit: Optional[Callable[[State, StateContext], None]] = None
        self.on_transition: Optional[Callable[[StateTransition, StateContext], None]] = None
    
    def add_state(self, state: State) -> None:
        """Add a state to the state machine.
        
        Args:
            state (State): State to add
        """
        if state.state_id in self.states:
            raise StateMachineError(f"State {state.state_id} already exists")
        
        self.states[state.state_id] = state
        state.event_bus = self.event_bus
        logger.debug(f"Added state: {state.state_id}")
    
    def remove_state(self, state_id: str) -> bool:
        """Remove a state from the state machine.
        
        Args:
            state_id (str): ID of state to remove
            
        Returns:
            bool: True if state was removed
        """
        if state_id not in self.states:
            return False
        
        # Can't remove current state
        if self.current_state and self.current_state.state_id == state_id:
            raise StateMachineError(f"Cannot remove current state: {state_id}")
        
        # Remove transitions involving this state
        self.transitions = [
            t for t in self.transitions 
            if t.from_state_id != state_id and t.to_state_id != state_id
        ]
        self._rebuild_transition_map()
        
        del self.states[state_id]
        logger.debug(f"Removed state: {state_id}")
        return True
    
    def add_transition(self, transition: StateTransition) -> None:
        """Add a transition to the state machine.
        
        Args:
            transition (StateTransition): Transition to add
        """
        # Validate states exist
        if transition.from_state_id not in self.states:
            raise StateMachineError(f"From state not found: {transition.from_state_id}")
        if transition.to_state_id not in self.states:
            raise StateMachineError(f"To state not found: {transition.to_state_id}")
        
        self.transitions.append(transition)
        self.transition_map[transition.from_state_id].append(transition)
        
        # Sort transitions by priority (higher priority first)
        self.transition_map[transition.from_state_id].sort(
            key=lambda t: t.priority, reverse=True
        )
        
        logger.debug(f"Added transition: {transition.from_state_id} -> {transition.to_state_id}")
    
    def _rebuild_transition_map(self) -> None:
        """Rebuild the transition map after modifications."""
        self.transition_map.clear()
        for transition in self.transitions:
            self.transition_map[transition.from_state_id].append(transition)
            
        # Sort by priority
        for transitions in self.transition_map.values():
            transitions.sort(key=lambda t: t.priority, reverse=True)
    
    def start(self, initial_state_id: str) -> bool:
        """Start the state machine.
        
        Args:
            initial_state_id (str): ID of initial state
            
        Returns:
            bool: True if started successfully
        """
        if self.running:
            logger.warning("State machine is already running")
            return False
        
        if initial_state_id not in self.states:
            raise StateMachineError(f"Initial state not found: {initial_state_id}")
        
        self.running = True
        self.context = StateContext(event_bus=self.event_bus)
        
        # Enter initial state
        initial_state = self.states[initial_state_id]
        result = self._enter_state(initial_state)
        
        if result == StateResult.ERROR:
            self.running = False
            return False
        
        logger.info(f"State machine {self.machine_id} started with initial state: {initial_state_id}")
        return True
    
    def stop(self) -> None:
        """Stop the state machine."""
        if not self.running:
            return
        
        # Exit current state
        if self.current_state:
            self._exit_state(self.current_state)
        
        self.running = False
        self.current_state = None
        self.previous_state = None
        
        logger.info(f"State machine {self.machine_id} stopped")
    
    def update(self, dt: float) -> None:
        """Update the state machine.
        
        Args:
            dt (float): Delta time since last update
        """
        if not self.running or not self.current_state:
            return
        
        try:
            # Update current state
            result = self.current_state.update(self.context, dt)
            
            # Handle state result
            if result == StateResult.TRANSITION:
                # Check for available transitions
                self._check_transitions()
            elif result == StateResult.ERROR:
                logger.error(f"Error in state {self.current_state.state_id}")
                # Could implement error recovery here
            
        except Exception as e:
            logger.error(f"Error updating state machine: {e}")
    
    def handle_event(self, event: Event) -> EventResult:
        """Handle an event in the state machine.
        
        Args:
            event (Event): Event to handle
            
        Returns:
            EventResult: Result of handling the event
        """
        if not self.running or not self.current_state:
            return EventResult.CONTINUE
        
        try:
            # Let current state handle the event
            result = self.current_state.handle_event(event, self.context)
            
            # Check for transitions after event handling
            if result == StateResult.TRANSITION:
                self._check_transitions()
            
            return EventResult.HANDLED
            
        except Exception as e:
            logger.error(f"Error handling event in state machine: {e}")
            return EventResult.ERROR
    
    def transition_to(self, state_id: str, force: bool = False) -> bool:
        """Manually trigger a transition to a specific state.
        
        Args:
            state_id (str): ID of state to transition to
            force (bool): Whether to force the transition
            
        Returns:
            bool: True if transition was successful
        """
        if not self.running:
            logger.warning("Cannot transition - state machine not running")
            return False
        
        if state_id not in self.states:
            raise StateMachineError(f"Target state not found: {state_id}")
        
        target_state = self.states[state_id]
        
        transition_to_use = None
        
        if not force and self.current_state:
            # Check if transition is allowed and find the transition to use
            valid_transitions = self.transition_map.get(self.current_state.state_id, [])
            for t in valid_transitions:
                if (t.to_state_id == state_id and 
                    t.can_execute(self.current_state, target_state, self.context)):
                    transition_to_use = t
                    break
            
            if not transition_to_use:
                logger.warning(f"Transition not allowed: {self.current_state.state_id} -> {state_id}")
                return False
        
        return self._execute_transition(target_state, transition_to_use)
    
    def _check_transitions(self) -> None:
        """Check for and execute valid transitions."""
        if not self.current_state:
            return
        
        valid_transitions = self.transition_map.get(self.current_state.state_id, [])
        
        for transition in valid_transitions:
            target_state = self.states[transition.to_state_id]
            
            if transition.can_execute(self.current_state, target_state, self.context):
                self._execute_transition(target_state, transition)
                break
    
    def _execute_transition(self, target_state: State, 
                          transition: StateTransition = None) -> bool:
        """Execute a transition to the target state.
        
        Args:
            target_state (State): State to transition to
            transition (StateTransition, optional): Transition being executed
            
        Returns:
            bool: True if transition was successful
        """
        try:
            old_state = self.current_state
            
            # Exit current state
            if old_state:
                exit_result = self._exit_state(old_state)
                if exit_result == StateResult.ERROR:
                    logger.error(f"Error exiting state {old_state.state_id}")
                    return False
            
            # Execute transition actions
            if transition and old_state:
                transition.execute(old_state, target_state, self.context)
                if self.on_transition:
                    self.on_transition(transition, self.context)
            
            # Enter new state
            enter_result = self._enter_state(target_state)
            if enter_result == StateResult.ERROR:
                logger.error(f"Error entering state {target_state.state_id}")
                return False
            
            # Update statistics
            self.stats['transitions_executed'] += 1
            
            logger.debug(f"Transitioned: {old_state.state_id if old_state else 'None'} -> {target_state.state_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error executing transition: {e}")
            return False
    
    def _enter_state(self, state: State) -> StateResult:
        """Enter a state.
        
        Args:
            state (State): State to enter
            
        Returns:
            StateResult: Result of entering the state
        """
        try:
            self.previous_state = self.current_state
            self.current_state = state
            
            state.active = True
            state.enter_time = time.time()
            
            result = state.enter(self.context)
            
            if self.on_state_enter:
                self.on_state_enter(state, self.context)
            
            self.stats['states_entered'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Error entering state {state.state_id}: {e}")
            return StateResult.ERROR
    
    def _exit_state(self, state: State) -> StateResult:
        """Exit a state.
        
        Args:
            state (State): State to exit
            
        Returns:
            StateResult: Result of exiting the state
        """
        try:
            result = state.exit(self.context)
            
            state.active = False
            state.exit_time = time.time()
            
            # Update duration statistics
            duration = state.get_duration()
            if duration is not None:
                self.stats['state_durations'][state.state_id] += duration
            
            if self.on_state_exit:
                self.on_state_exit(state, self.context)
            
            return result
            
        except Exception as e:
            logger.error(f"Error exiting state {state.state_id}: {e}")
            return StateResult.ERROR
    
    def get_current_state(self) -> Optional[State]:
        """Get the current state.
        
        Returns:
            State: Current state, None if not running
        """
        return self.current_state
    
    def get_previous_state(self) -> Optional[State]:
        """Get the previous state.
        
        Returns:
            State: Previous state, None if no previous state
        """
        return self.previous_state
    
    def get_state(self, state_id: str) -> Optional[State]:
        """Get a state by ID.
        
        Args:
            state_id (str): State ID
            
        Returns:
            State: State if found, None otherwise
        """
        return self.states.get(state_id)
    
    def get_all_states(self) -> Dict[str, State]:
        """Get all states.
        
        Returns:
            Dict[str, State]: Dictionary of all states
        """
        return self.states.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get state machine statistics.
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        stats = self.stats.copy()
        stats['current_state'] = self.current_state.state_id if self.current_state else None
        stats['total_states'] = len(self.states)
        stats['total_transitions'] = len(self.transitions)
        stats['running'] = self.running
        return stats
    
    def is_running(self) -> bool:
        """Check if state machine is running.
        
        Returns:
            bool: True if running
        """
        return self.running
    
    def __str__(self) -> str:
        """String representation of the state machine."""
        current = self.current_state.state_id if self.current_state else "None"
        return f"StateMachine(id={self.machine_id}, current={current}, running={self.running})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the state machine."""
        return (f"StateMachine(machine_id='{self.machine_id}', "
                f"states={len(self.states)}, transitions={len(self.transitions)}, "
                f"current_state='{self.current_state.state_id if self.current_state else None}', "
                f"running={self.running})")
