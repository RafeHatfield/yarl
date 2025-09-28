"""State-related events for integration with the event system.

This module defines events that are dispatched during state machine
operations, enabling loose coupling and reactive programming patterns.
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum, auto

from events import Event, EventContext, EventPriority, GameEvent, GameEventType


class StateEventType(Enum):
    """Types of state-related events."""
    
    # State lifecycle events
    STATE_ENTER = "state.enter"
    STATE_EXIT = "state.exit"
    STATE_UPDATE = "state.update"
    
    # State transition events
    STATE_CHANGE = "state.change"
    STATE_TRANSITION = "state.transition"
    STATE_TRANSITION_BLOCKED = "state.transition_blocked"
    
    # State machine events
    STATE_MACHINE_START = "state_machine.start"
    STATE_MACHINE_STOP = "state_machine.stop"
    STATE_MACHINE_ERROR = "state_machine.error"
    
    # Hierarchical state events
    CHILD_STATE_ENTER = "child_state.enter"
    CHILD_STATE_EXIT = "child_state.exit"
    CHILD_STATE_CHANGE = "child_state.change"
    
    # State request events
    STATE_CHANGE_REQUEST = "state.change_request"
    STATE_TRANSITION_REQUEST = "state.transition_request"
    
    # State validation events
    STATE_VALIDATION_ERROR = "state.validation_error"
    STATE_GUARD_FAILED = "state.guard_failed"


class StateEvent(Event):
    """Base class for state-related events."""
    
    def __init__(self, event_type: StateEventType, state_id: str = None,
                 data: Dict[str, Any] = None, context: Optional[EventContext] = None):
        """Initialize state event.
        
        Args:
            event_type (StateEventType): Type of state event
            state_id (str, optional): ID of the state involved
            data (Dict[str, Any], optional): Event data
            context (EventContext, optional): Event context
        """
        super().__init__(context)
        self._event_type = event_type
        self.state_id = state_id
        self.data = data or {}
    
    @property
    def event_type(self) -> str:
        """Get the event type identifier."""
        return self._event_type.value
    
    @property
    def state_event_type(self) -> StateEventType:
        """Get the state event type enum."""
        return self._event_type
    
    def validate(self) -> list[str]:
        """Validate the event data."""
        errors = []
        
        if not isinstance(self.data, dict):
            errors.append("Event data must be a dictionary")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation."""
        return {
            'event_type': self._event_type.value,
            'state_id': self.state_id,
            'data': self.data,
            'context': {
                'source': self.context.source,
                'target': self.context.target,
                'timestamp': self.context.timestamp,
                'priority': self.context.priority.value,
                'metadata': self.context.metadata,
                'trace_id': self.context.trace_id,
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateEvent':
        """Create event from dictionary representation."""
        context_data = data.get('context', {})
        context = EventContext(
            source=context_data.get('source'),
            target=context_data.get('target'),
            timestamp=context_data.get('timestamp'),
            priority=EventPriority(context_data.get('priority', EventPriority.NORMAL.value)),
            metadata=context_data.get('metadata', {}),
            trace_id=context_data.get('trace_id')
        )
        
        event_type = StateEventType(data['event_type'])
        
        return cls(
            event_type=event_type,
            state_id=data.get('state_id'),
            data=data.get('data', {}),
            context=context
        )


@dataclass
class StateChangeEvent(StateEvent):
    """Event dispatched when a state change occurs."""
    
    def __init__(self, previous_state: str = None, new_state: str = None,
                 context_data: Dict[str, Any] = None, 
                 event_context: Optional[EventContext] = None):
        """Initialize state change event.
        
        Args:
            previous_state (str, optional): ID of previous state
            new_state (str, optional): ID of new state
            context_data (Dict[str, Any], optional): State context data
            event_context (EventContext, optional): Event context
        """
        data = {
            'previous_state': previous_state,
            'new_state': new_state,
            'context_data': context_data or {},
            'timestamp': event_context.timestamp if event_context else None,
        }
        
        super().__init__(StateEventType.STATE_CHANGE, new_state, data, event_context)
        
        self.previous_state = previous_state
        self.new_state = new_state
        self.context_data = context_data or {}


@dataclass
class StateTransitionEvent(StateEvent):
    """Event dispatched when a state transition occurs."""
    
    def __init__(self, from_state: str = None, to_state: str = None,
                 transition_data: Dict[str, Any] = None,
                 context_data: Dict[str, Any] = None,
                 event_context: Optional[EventContext] = None):
        """Initialize state transition event.
        
        Args:
            from_state (str, optional): ID of state being transitioned from
            to_state (str, optional): ID of state being transitioned to
            transition_data (Dict[str, Any], optional): Transition-specific data
            context_data (Dict[str, Any], optional): State context data
            event_context (EventContext, optional): Event context
        """
        data = {
            'from_state': from_state,
            'to_state': to_state,
            'transition_data': transition_data or {},
            'context_data': context_data or {},
        }
        
        super().__init__(StateEventType.STATE_TRANSITION, to_state, data, event_context)
        
        self.from_state = from_state
        self.to_state = to_state
        self.transition_data = transition_data or {}
        self.context_data = context_data or {}


@dataclass
class StateLifecycleEvent(StateEvent):
    """Event dispatched during state lifecycle operations."""
    
    def __init__(self, lifecycle_type: StateEventType, state_id: str,
                 state_data: Dict[str, Any] = None,
                 duration: float = None,
                 event_context: Optional[EventContext] = None):
        """Initialize state lifecycle event.
        
        Args:
            lifecycle_type (StateEventType): Type of lifecycle event
            state_id (str): ID of the state
            state_data (Dict[str, Any], optional): State-specific data
            duration (float, optional): Duration of state operation
            event_context (EventContext, optional): Event context
        """
        data = {
            'state_data': state_data or {},
            'duration': duration,
        }
        
        super().__init__(lifecycle_type, state_id, data, event_context)
        
        self.state_data = state_data or {}
        self.duration = duration


@dataclass
class StateRequestEvent(StateEvent):
    """Event for requesting state changes or transitions."""
    
    def __init__(self, request_type: StateEventType, target_state: str,
                 force: bool = False, transition_data: Dict[str, Any] = None,
                 requester: str = None, event_context: Optional[EventContext] = None):
        """Initialize state request event.
        
        Args:
            request_type (StateEventType): Type of request
            target_state (str): ID of target state
            force (bool): Whether to force the transition
            transition_data (Dict[str, Any], optional): Data for the transition
            requester (str, optional): ID of the requesting component
            event_context (EventContext, optional): Event context
        """
        data = {
            'target_state': target_state,
            'force': force,
            'transition_data': transition_data or {},
            'requester': requester,
        }
        
        super().__init__(request_type, target_state, data, event_context)
        
        self.target_state = target_state
        self.force = force
        self.transition_data = transition_data or {}
        self.requester = requester


@dataclass
class StateErrorEvent(StateEvent):
    """Event dispatched when state-related errors occur."""
    
    def __init__(self, error_type: StateEventType, state_id: str = None,
                 error_message: str = "", error_details: Dict[str, Any] = None,
                 exception: Exception = None, event_context: Optional[EventContext] = None):
        """Initialize state error event.
        
        Args:
            error_type (StateEventType): Type of error
            state_id (str, optional): ID of state where error occurred
            error_message (str): Error message
            error_details (Dict[str, Any], optional): Additional error details
            exception (Exception, optional): Original exception
            event_context (EventContext, optional): Event context
        """
        data = {
            'error_message': error_message,
            'error_details': error_details or {},
            'exception_type': type(exception).__name__ if exception else None,
            'exception_message': str(exception) if exception else None,
        }
        
        super().__init__(error_type, state_id, data, event_context)
        
        self.error_message = error_message
        self.error_details = error_details or {}
        self.exception = exception


@dataclass
class HierarchicalStateEvent(StateEvent):
    """Event for hierarchical state operations."""
    
    def __init__(self, event_type: StateEventType, parent_state_id: str,
                 child_state_id: str, hierarchy_data: Dict[str, Any] = None,
                 event_context: Optional[EventContext] = None):
        """Initialize hierarchical state event.
        
        Args:
            event_type (StateEventType): Type of hierarchical event
            parent_state_id (str): ID of parent state
            child_state_id (str): ID of child state
            hierarchy_data (Dict[str, Any], optional): Hierarchy-specific data
            event_context (EventContext, optional): Event context
        """
        data = {
            'parent_state_id': parent_state_id,
            'child_state_id': child_state_id,
            'hierarchy_data': hierarchy_data or {},
        }
        
        super().__init__(event_type, child_state_id, data, event_context)
        
        self.parent_state_id = parent_state_id
        self.child_state_id = child_state_id
        self.hierarchy_data = hierarchy_data or {}


# Convenience functions for creating state events

def create_state_change_event(previous_state: str = None, new_state: str = None,
                             context_data: Dict[str, Any] = None,
                             source: str = None, priority: EventPriority = EventPriority.NORMAL) -> StateChangeEvent:
    """Create a state change event.
    
    Args:
        previous_state (str, optional): Previous state ID
        new_state (str, optional): New state ID
        context_data (Dict[str, Any], optional): State context data
        source (str, optional): Event source
        priority (EventPriority): Event priority
        
    Returns:
        StateChangeEvent: Created state change event
    """
    event_context = EventContext(source=source, priority=priority)
    return StateChangeEvent(previous_state, new_state, context_data, event_context)


def create_state_transition_event(from_state: str = None, to_state: str = None,
                                 transition_data: Dict[str, Any] = None,
                                 source: str = None, priority: EventPriority = EventPriority.NORMAL) -> StateTransitionEvent:
    """Create a state transition event.
    
    Args:
        from_state (str, optional): From state ID
        to_state (str, optional): To state ID
        transition_data (Dict[str, Any], optional): Transition data
        source (str, optional): Event source
        priority (EventPriority): Event priority
        
    Returns:
        StateTransitionEvent: Created state transition event
    """
    event_context = EventContext(source=source, priority=priority)
    return StateTransitionEvent(from_state, to_state, transition_data, {}, event_context)


def create_state_request_event(target_state: str, force: bool = False,
                              transition_data: Dict[str, Any] = None,
                              requester: str = None, priority: EventPriority = EventPriority.NORMAL) -> StateRequestEvent:
    """Create a state request event.
    
    Args:
        target_state (str): Target state ID
        force (bool): Whether to force the transition
        transition_data (Dict[str, Any], optional): Transition data
        requester (str, optional): Requesting component ID
        priority (EventPriority): Event priority
        
    Returns:
        StateRequestEvent: Created state request event
    """
    event_context = EventContext(source=requester, priority=priority)
    return StateRequestEvent(
        StateEventType.STATE_CHANGE_REQUEST, target_state, force, 
        transition_data, requester, event_context
    )


def create_state_lifecycle_event(lifecycle_type: StateEventType, state_id: str,
                                state_data: Dict[str, Any] = None, duration: float = None,
                                source: str = None, priority: EventPriority = EventPriority.NORMAL) -> StateLifecycleEvent:
    """Create a state lifecycle event.
    
    Args:
        lifecycle_type (StateEventType): Type of lifecycle event
        state_id (str): State ID
        state_data (Dict[str, Any], optional): State data
        duration (float, optional): Duration of operation
        source (str, optional): Event source
        priority (EventPriority): Event priority
        
    Returns:
        StateLifecycleEvent: Created state lifecycle event
    """
    event_context = EventContext(source=source, priority=priority)
    return StateLifecycleEvent(lifecycle_type, state_id, state_data, duration, event_context)


def create_state_error_event(error_message: str, state_id: str = None,
                            error_details: Dict[str, Any] = None, exception: Exception = None,
                            source: str = None, priority: EventPriority = EventPriority.HIGH) -> StateErrorEvent:
    """Create a state error event.
    
    Args:
        error_message (str): Error message
        state_id (str, optional): State ID where error occurred
        error_details (Dict[str, Any], optional): Additional error details
        exception (Exception, optional): Original exception
        source (str, optional): Event source
        priority (EventPriority): Event priority
        
    Returns:
        StateErrorEvent: Created state error event
    """
    event_context = EventContext(source=source, priority=priority)
    return StateErrorEvent(
        StateEventType.STATE_MACHINE_ERROR, state_id, error_message,
        error_details, exception, event_context
    )


def create_hierarchical_state_event(event_type: StateEventType, parent_state_id: str,
                                   child_state_id: str, hierarchy_data: Dict[str, Any] = None,
                                   source: str = None, priority: EventPriority = EventPriority.NORMAL) -> HierarchicalStateEvent:
    """Create a hierarchical state event.
    
    Args:
        event_type (StateEventType): Type of hierarchical event
        parent_state_id (str): Parent state ID
        child_state_id (str): Child state ID
        hierarchy_data (Dict[str, Any], optional): Hierarchy data
        source (str, optional): Event source
        priority (EventPriority): Event priority
        
    Returns:
        HierarchicalStateEvent: Created hierarchical state event
    """
    event_context = EventContext(source=source, priority=priority)
    return HierarchicalStateEvent(
        event_type, parent_state_id, child_state_id, hierarchy_data, event_context
    )
