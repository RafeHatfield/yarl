"""Advanced transition system for state machines.

This module provides sophisticated transition mechanisms including
conditional transitions, timed transitions, and event-triggered transitions.
"""

from typing import Any, Dict, List, Optional, Callable, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import time
import threading
import logging

from events import Event, EventBus, get_event_bus, EventListener, event_handler

from .core import State, StateContext, StateTransition, TransitionGuard, TransitionAction


logger = logging.getLogger(__name__)


class ConditionalGuard(TransitionGuard):
    """Guard that evaluates a condition function."""
    
    def __init__(self, condition: Callable[[State, State, StateContext], bool],
                 name: str = "conditional_guard"):
        """Initialize conditional guard.
        
        Args:
            condition (Callable): Function that returns True if transition is allowed
            name (str): Name for debugging purposes
        """
        self.condition = condition
        self.name = name
    
    def can_transition(self, from_state: State, to_state: State, 
                      context: StateContext) -> bool:
        """Check if transition is allowed based on condition.
        
        Args:
            from_state (State): State being transitioned from
            to_state (State): State being transitioned to
            context (StateContext): State context
            
        Returns:
            bool: True if transition is allowed
        """
        try:
            return self.condition(from_state, to_state, context)
        except Exception as e:
            logger.error(f"Error in conditional guard {self.name}: {e}")
            return False


class TimeGuard(TransitionGuard):
    """Guard that allows transition only after a minimum time has elapsed."""
    
    def __init__(self, min_time: float, name: str = "time_guard"):
        """Initialize time guard.
        
        Args:
            min_time (float): Minimum time in seconds before transition is allowed
            name (str): Name for debugging purposes
        """
        self.min_time = min_time
        self.name = name
    
    def can_transition(self, from_state: State, to_state: State, 
                      context: StateContext) -> bool:
        """Check if enough time has elapsed for transition.
        
        Args:
            from_state (State): State being transitioned from
            to_state (State): State being transitioned to
            context (StateContext): State context
            
        Returns:
            bool: True if enough time has elapsed
        """
        elapsed = context.get_elapsed_time()
        return elapsed >= self.min_time


class DataGuard(TransitionGuard):
    """Guard that checks for specific data in the context."""
    
    def __init__(self, required_data: Dict[str, Any], name: str = "data_guard"):
        """Initialize data guard.
        
        Args:
            required_data (Dict[str, Any]): Required data key-value pairs
            name (str): Name for debugging purposes
        """
        self.required_data = required_data
        self.name = name
    
    def can_transition(self, from_state: State, to_state: State, 
                      context: StateContext) -> bool:
        """Check if required data is present in context.
        
        Args:
            from_state (State): State being transitioned from
            to_state (State): State being transitioned to
            context (StateContext): State context
            
        Returns:
            bool: True if all required data is present
        """
        for key, expected_value in self.required_data.items():
            actual_value = context.get_data(key)
            if actual_value != expected_value:
                return False
        return True


class LoggingAction(TransitionAction):
    """Action that logs transition information."""
    
    def __init__(self, message: str = None, level: str = "INFO"):
        """Initialize logging action.
        
        Args:
            message (str, optional): Custom message to log
            level (str): Log level (DEBUG, INFO, WARNING, ERROR)
        """
        self.message = message
        self.level = getattr(logging, level.upper(), logging.INFO)
    
    def execute(self, from_state: State, to_state: State, 
               context: StateContext) -> None:
        """Execute the logging action.
        
        Args:
            from_state (State): State being transitioned from
            to_state (State): State being transitioned to
            context (StateContext): State context
        """
        if self.message:
            message = self.message
        else:
            message = f"Transition: {from_state.state_id} -> {to_state.state_id}"
        
        logger.log(self.level, message)


class DataAction(TransitionAction):
    """Action that sets data in the context."""
    
    def __init__(self, data_updates: Dict[str, Any]):
        """Initialize data action.
        
        Args:
            data_updates (Dict[str, Any]): Data to set in context
        """
        self.data_updates = data_updates
    
    def execute(self, from_state: State, to_state: State, 
               context: StateContext) -> None:
        """Execute the data action.
        
        Args:
            from_state (State): State being transitioned from
            to_state (State): State being transitioned to
            context (StateContext): State context
        """
        for key, value in self.data_updates.items():
            context.set_data(key, value)


class EventAction(TransitionAction):
    """Action that dispatches an event."""
    
    def __init__(self, event: Event, event_bus: EventBus = None):
        """Initialize event action.
        
        Args:
            event (Event): Event to dispatch
            event_bus (EventBus, optional): Event bus to use
        """
        self.event = event
        self.event_bus = event_bus or get_event_bus()
    
    def execute(self, from_state: State, to_state: State, 
               context: StateContext) -> None:
        """Execute the event action.
        
        Args:
            from_state (State): State being transitioned from
            to_state (State): State being transitioned to
            context (StateContext): State context
        """
        # Update event with transition information
        self.event.context.add_metadata("from_state", from_state.state_id)
        self.event.context.add_metadata("to_state", to_state.state_id)
        
        self.event_bus.dispatch(self.event)


class ConditionalTransition(StateTransition):
    """Transition that occurs when a condition is met."""
    
    def __init__(self, from_state_id: str, to_state_id: str,
                 condition: Callable[[State, State, StateContext], bool],
                 trigger: str = None, priority: int = 0):
        """Initialize conditional transition.
        
        Args:
            from_state_id (str): Source state ID
            to_state_id (str): Target state ID
            condition (Callable): Condition function
            trigger (str, optional): Trigger name
            priority (int): Transition priority
        """
        guard = ConditionalGuard(condition, f"condition_{from_state_id}_{to_state_id}")
        super().__init__(from_state_id, to_state_id, trigger, [guard], [], priority)
        self.condition = condition


class TimedTransition(StateTransition):
    """Transition that occurs after a specified time delay."""
    
    def __init__(self, from_state_id: str, to_state_id: str,
                 delay: float, trigger: str = None, priority: int = 0):
        """Initialize timed transition.
        
        Args:
            from_state_id (str): Source state ID
            to_state_id (str): Target state ID
            delay (float): Delay in seconds
            trigger (str, optional): Trigger name
            priority (int): Transition priority
        """
        guard = TimeGuard(delay, f"time_{from_state_id}_{to_state_id}")
        super().__init__(from_state_id, to_state_id, trigger, [guard], [], priority)
        self.delay = delay


class EventTriggeredTransition(StateTransition, EventListener):
    """Transition that is triggered by specific events."""
    
    def __init__(self, from_state_id: str, to_state_id: str,
                 event_types: List[str], event_bus: EventBus = None,
                 priority: int = 0):
        """Initialize event-triggered transition.
        
        Args:
            from_state_id (str): Source state ID
            to_state_id (str): Target state ID
            event_types (List[str]): List of event types that trigger this transition
            event_bus (EventBus, optional): Event bus to listen on
            priority (int): Transition priority
        """
        StateTransition.__init__(self, from_state_id, to_state_id, None, [], [], priority)
        EventListener.__init__(self, f"transition_{from_state_id}_{to_state_id}")
        
        self.event_types = event_types
        self.event_bus = event_bus or get_event_bus()
        self.triggered = False
        
        # Register as event listener
        self.event_bus.register_listener(self)
    
    def get_handled_events(self) -> List[str]:
        """Get list of event types this transition handles.
        
        Returns:
            List[str]: List of event type identifiers
        """
        return self.event_types
    
    def handle_event(self, event: Event) -> Any:
        """Handle an event that might trigger this transition.
        
        Args:
            event (Event): Event to handle
            
        Returns:
            Any: Event handling result
        """
        if event.event_type in self.event_types:
            self.triggered = True
            logger.debug(f"Event-triggered transition activated: {self.from_state_id} -> {self.to_state_id}")
        
        from events import EventResult
        return EventResult.CONTINUE
    
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
        # Check if event was triggered and base conditions are met
        return self.triggered and super().can_execute(from_state, to_state, context)
    
    def reset(self) -> None:
        """Reset the triggered state."""
        self.triggered = False


@dataclass
class TransitionBuilder:
    """Builder for creating complex transitions."""
    
    from_state_id: str
    to_state_id: str
    trigger: Optional[str] = None
    priority: int = 0
    guards: List[TransitionGuard] = field(default_factory=list)
    actions: List[TransitionAction] = field(default_factory=list)
    
    def with_trigger(self, trigger: str) -> 'TransitionBuilder':
        """Set the trigger for this transition.
        
        Args:
            trigger (str): Trigger name
            
        Returns:
            TransitionBuilder: This builder for chaining
        """
        self.trigger = trigger
        return self
    
    def with_priority(self, priority: int) -> 'TransitionBuilder':
        """Set the priority for this transition.
        
        Args:
            priority (int): Priority value
            
        Returns:
            TransitionBuilder: This builder for chaining
        """
        self.priority = priority
        return self
    
    def with_condition(self, condition: Callable[[State, State, StateContext], bool],
                      name: str = None) -> 'TransitionBuilder':
        """Add a conditional guard.
        
        Args:
            condition (Callable): Condition function
            name (str, optional): Guard name
            
        Returns:
            TransitionBuilder: This builder for chaining
        """
        guard_name = name or f"condition_{len(self.guards)}"
        self.guards.append(ConditionalGuard(condition, guard_name))
        return self
    
    def with_min_time(self, min_time: float, name: str = None) -> 'TransitionBuilder':
        """Add a time guard.
        
        Args:
            min_time (float): Minimum time in seconds
            name (str, optional): Guard name
            
        Returns:
            TransitionBuilder: This builder for chaining
        """
        guard_name = name or f"time_{len(self.guards)}"
        self.guards.append(TimeGuard(min_time, guard_name))
        return self
    
    def with_required_data(self, required_data: Dict[str, Any],
                          name: str = None) -> 'TransitionBuilder':
        """Add a data guard.
        
        Args:
            required_data (Dict[str, Any]): Required data
            name (str, optional): Guard name
            
        Returns:
            TransitionBuilder: This builder for chaining
        """
        guard_name = name or f"data_{len(self.guards)}"
        self.guards.append(DataGuard(required_data, guard_name))
        return self
    
    def with_custom_guard(self, guard: TransitionGuard) -> 'TransitionBuilder':
        """Add a custom guard.
        
        Args:
            guard (TransitionGuard): Custom guard
            
        Returns:
            TransitionBuilder: This builder for chaining
        """
        self.guards.append(guard)
        return self
    
    def with_logging(self, message: str = None, level: str = "INFO") -> 'TransitionBuilder':
        """Add a logging action.
        
        Args:
            message (str, optional): Log message
            level (str): Log level
            
        Returns:
            TransitionBuilder: This builder for chaining
        """
        self.actions.append(LoggingAction(message, level))
        return self
    
    def with_data_update(self, data_updates: Dict[str, Any]) -> 'TransitionBuilder':
        """Add a data update action.
        
        Args:
            data_updates (Dict[str, Any]): Data to update
            
        Returns:
            TransitionBuilder: This builder for chaining
        """
        self.actions.append(DataAction(data_updates))
        return self
    
    def with_event(self, event: Event, event_bus: EventBus = None) -> 'TransitionBuilder':
        """Add an event dispatch action.
        
        Args:
            event (Event): Event to dispatch
            event_bus (EventBus, optional): Event bus to use
            
        Returns:
            TransitionBuilder: This builder for chaining
        """
        self.actions.append(EventAction(event, event_bus))
        return self
    
    def with_custom_action(self, action: TransitionAction) -> 'TransitionBuilder':
        """Add a custom action.
        
        Args:
            action (TransitionAction): Custom action
            
        Returns:
            TransitionBuilder: This builder for chaining
        """
        self.actions.append(action)
        return self
    
    def build(self) -> StateTransition:
        """Build the transition.
        
        Returns:
            StateTransition: Built transition
        """
        return StateTransition(
            self.from_state_id,
            self.to_state_id,
            self.trigger,
            self.guards.copy(),
            self.actions.copy(),
            self.priority
        )


class StateTransitionBuilder:
    """Factory class for creating transitions with fluent interface."""
    
    @staticmethod
    def from_state(from_state_id: str) -> 'TransitionBuilder':
        """Start building a transition from a state.
        
        Args:
            from_state_id (str): Source state ID
            
        Returns:
            TransitionBuilder: Transition builder
        """
        # Return a partial builder that needs to_state to be set
        return _PartialTransitionBuilder(from_state_id)


class _PartialTransitionBuilder:
    """Partial transition builder that needs a target state."""
    
    def __init__(self, from_state_id: str):
        """Initialize partial builder.
        
        Args:
            from_state_id (str): Source state ID
        """
        self.from_state_id = from_state_id
    
    def to_state(self, to_state_id: str) -> TransitionBuilder:
        """Set the target state and return full builder.
        
        Args:
            to_state_id (str): Target state ID
            
        Returns:
            TransitionBuilder: Full transition builder
        """
        return TransitionBuilder(self.from_state_id, to_state_id)


# Convenience functions for creating common transitions

def create_transition(from_state_id: str, to_state_id: str,
                     trigger: str = None, priority: int = 0) -> StateTransition:
    """Create a basic transition.
    
    Args:
        from_state_id (str): Source state ID
        to_state_id (str): Target state ID
        trigger (str, optional): Trigger name
        priority (int): Priority value
        
    Returns:
        StateTransition: Created transition
    """
    return StateTransition(from_state_id, to_state_id, trigger, [], [], priority)


def create_conditional_transition(from_state_id: str, to_state_id: str,
                                 condition: Callable[[State, State, StateContext], bool],
                                 priority: int = 0) -> ConditionalTransition:
    """Create a conditional transition.
    
    Args:
        from_state_id (str): Source state ID
        to_state_id (str): Target state ID
        condition (Callable): Condition function
        priority (int): Priority value
        
    Returns:
        ConditionalTransition: Created conditional transition
    """
    return ConditionalTransition(from_state_id, to_state_id, condition, None, priority)


def create_timed_transition(from_state_id: str, to_state_id: str,
                           delay: float, priority: int = 0) -> TimedTransition:
    """Create a timed transition.
    
    Args:
        from_state_id (str): Source state ID
        to_state_id (str): Target state ID
        delay (float): Delay in seconds
        priority (int): Priority value
        
    Returns:
        TimedTransition: Created timed transition
    """
    return TimedTransition(from_state_id, to_state_id, delay, None, priority)


def create_event_triggered_transition(from_state_id: str, to_state_id: str,
                                     event_types: List[str], 
                                     priority: int = 0) -> EventTriggeredTransition:
    """Create an event-triggered transition.
    
    Args:
        from_state_id (str): Source state ID
        to_state_id (str): Target state ID
        event_types (List[str]): Event types that trigger the transition
        priority (int): Priority value
        
    Returns:
        EventTriggeredTransition: Created event-triggered transition
    """
    return EventTriggeredTransition(from_state_id, to_state_id, event_types, None, priority)


def create_player_action_transition(from_state_id: str, to_state_id: str,
                                   action_type: str = None) -> EventTriggeredTransition:
    """Create a transition triggered by player actions.
    
    Args:
        from_state_id (str): Source state ID
        to_state_id (str): Target state ID
        action_type (str, optional): Specific action type to trigger on
        
    Returns:
        EventTriggeredTransition: Created player action transition
    """
    if action_type:
        event_types = [f"player.action.{action_type}"]
    else:
        event_types = ["player.action"]
    
    return EventTriggeredTransition(from_state_id, to_state_id, event_types, None, 10)


def create_ai_completion_transition(from_state_id: str, to_state_id: str) -> EventTriggeredTransition:
    """Create a transition triggered by AI turn completion.
    
    Args:
        from_state_id (str): Source state ID
        to_state_id (str): Target state ID
        
    Returns:
        EventTriggeredTransition: Created AI completion transition
    """
    return EventTriggeredTransition(
        from_state_id, to_state_id, ["ai.turn_complete"], None, 10
    )
