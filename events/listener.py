"""Event listener system for handling events.

This module provides the event listener interface and decorators for
creating event handlers that can respond to specific types of events.
"""

from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Any, Union, Type
from functools import wraps
import inspect
import logging

from .core import Event, EventResult, EventPriority
from .exceptions import EventListenerError


logger = logging.getLogger(__name__)


class EventListener(ABC):
    """Abstract base class for event listeners.
    
    Event listeners are components that can receive and process events.
    They can be registered with the event bus to receive notifications
    when specific types of events are dispatched.
    """
    
    def __init__(self, listener_id: str = None):
        """Initialize the event listener.
        
        Args:
            listener_id (str, optional): Unique identifier for this listener
        """
        self.listener_id = listener_id or f"{self.__class__.__name__}_{id(self)}"
        self.enabled = True
        self.priority = EventPriority.NORMAL
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # Auto-discover event handlers
        self._discover_handlers()
    
    @abstractmethod
    def get_handled_events(self) -> List[str]:
        """Get list of event types this listener handles.
        
        Returns:
            List[str]: List of event type identifiers
        """
        pass
    
    def handle_event(self, event: Event) -> EventResult:
        """Handle an incoming event.
        
        Args:
            event (Event): Event to handle
            
        Returns:
            EventResult: Result of event processing
        """
        if not self.enabled:
            return EventResult.CONTINUE
        
        try:
            # Find handlers for this event type
            handlers = self.event_handlers.get(event.event_type, [])
            
            if not handlers:
                # Try generic handler
                if hasattr(self, 'on_event'):
                    return self.on_event(event)
                return EventResult.CONTINUE
            
            # Execute handlers in order
            result = EventResult.CONTINUE
            for handler in handlers:
                try:
                    handler_result = handler(event)
                    
                    # Update result based on handler response
                    if handler_result in (EventResult.CONSUMED, EventResult.CANCELLED, EventResult.ERROR):
                        result = handler_result
                        break
                    elif handler_result == EventResult.HANDLED:
                        result = EventResult.HANDLED
                    
                except Exception as e:
                    logger.error(f"Error in event handler {handler.__name__}: {e}")
                    event.set_error(e)
                    result = EventResult.ERROR
                    break
            
            # Mark that this listener processed the event
            event.add_processor(self.listener_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in event listener {self.listener_id}: {e}")
            event.set_error(e)
            return EventResult.ERROR
    
    def enable(self) -> None:
        """Enable this event listener."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable this event listener."""
        self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if this listener is enabled.
        
        Returns:
            bool: True if listener is enabled
        """
        return self.enabled
    
    def set_priority(self, priority: EventPriority) -> None:
        """Set the priority of this listener.
        
        Args:
            priority (EventPriority): New priority level
        """
        self.priority = priority
    
    def get_priority(self) -> EventPriority:
        """Get the priority of this listener.
        
        Returns:
            EventPriority: Current priority level
        """
        return self.priority
    
    def add_handler(self, event_type: str, handler: Callable[[Event], EventResult]) -> None:
        """Add a handler for a specific event type.
        
        Args:
            event_type (str): Event type to handle
            handler (Callable): Handler function
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        if handler not in self.event_handlers[event_type]:
            self.event_handlers[event_type].append(handler)
    
    def remove_handler(self, event_type: str, handler: Callable[[Event], EventResult]) -> bool:
        """Remove a handler for a specific event type.
        
        Args:
            event_type (str): Event type
            handler (Callable): Handler function to remove
            
        Returns:
            bool: True if handler was removed
        """
        if event_type in self.event_handlers:
            if handler in self.event_handlers[event_type]:
                self.event_handlers[event_type].remove(handler)
                return True
        return False
    
    def _discover_handlers(self) -> None:
        """Discover event handlers using decorators and naming conventions."""
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            # Check for event_handler decorator
            if hasattr(method, '_event_types'):
                for event_type in method._event_types:
                    self.add_handler(event_type, method)
            
            # Check for naming convention (on_<event_type>)
            elif name.startswith('on_') and name != 'on_event':
                event_type = name[3:]  # Remove 'on_' prefix
                self.add_handler(event_type, method)
    
    def get_handler_info(self) -> Dict[str, List[str]]:
        """Get information about registered handlers.
        
        Returns:
            Dict[str, List[str]]: Mapping of event types to handler names
        """
        info = {}
        for event_type, handlers in self.event_handlers.items():
            info[event_type] = [handler.__name__ for handler in handlers]
        return info
    
    def __str__(self) -> str:
        """String representation of the listener."""
        return f"{self.__class__.__name__}(id={self.listener_id}, enabled={self.enabled})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the listener."""
        return (f"{self.__class__.__name__}(listener_id='{self.listener_id}', "
                f"enabled={self.enabled}, priority={self.priority.name}, "
                f"handlers={len(self.event_handlers)})")


class EventHandler:
    """Decorator for marking methods as event handlers."""
    
    def __init__(self, *event_types: str, priority: EventPriority = EventPriority.NORMAL):
        """Initialize event handler decorator.
        
        Args:
            *event_types (str): Event types this handler processes
            priority (EventPriority): Handler priority
        """
        self.event_types = event_types
        self.priority = priority
    
    def __call__(self, func: Callable) -> Callable:
        """Apply the decorator to a function.
        
        Args:
            func (Callable): Function to decorate
            
        Returns:
            Callable: Decorated function
        """
        # Store event types on the function
        func._event_types = self.event_types
        func._event_priority = self.priority
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Copy attributes to wrapper
        wrapper._event_types = self.event_types
        wrapper._event_priority = self.priority
        
        return wrapper


def event_handler(*event_types: str, priority: EventPriority = EventPriority.NORMAL):
    """Decorator for marking methods as event handlers.
    
    Args:
        *event_types (str): Event types this handler processes
        priority (EventPriority): Handler priority
        
    Returns:
        EventHandler: Event handler decorator
    """
    return EventHandler(*event_types, priority=priority)


class SimpleEventListener(EventListener):
    """Simple event listener implementation for basic use cases."""
    
    def __init__(self, listener_id: str = None, handled_events: List[str] = None):
        """Initialize simple event listener.
        
        Args:
            listener_id (str, optional): Listener identifier
            handled_events (List[str], optional): List of handled event types
        """
        self._handled_events = handled_events or []
        super().__init__(listener_id)
    
    def get_handled_events(self) -> List[str]:
        """Get list of event types this listener handles."""
        return self._handled_events
    
    def on_event(self, event: Event) -> EventResult:
        """Default event handler.
        
        Args:
            event (Event): Event to handle
            
        Returns:
            EventResult: Processing result
        """
        logger.debug(f"Listener {self.listener_id} received event: {event.event_type}")
        return EventResult.CONTINUE


class CallableEventListener(EventListener):
    """Event listener that wraps a callable function."""
    
    def __init__(self, event_types: List[str], handler: Callable[[Event], EventResult],
                 listener_id: str = None, priority: EventPriority = EventPriority.NORMAL):
        """Initialize callable event listener.
        
        Args:
            event_types (List[str]): Event types to handle
            handler (Callable): Handler function
            listener_id (str, optional): Listener identifier
            priority (EventPriority): Listener priority
        """
        self._handled_events = event_types
        self._handler = handler
        super().__init__(listener_id)
        self.priority = priority
        
        # Register handler for all event types
        for event_type in event_types:
            self.add_handler(event_type, self._handler)
    
    def get_handled_events(self) -> List[str]:
        """Get list of event types this listener handles."""
        return self._handled_events


class EventListenerRegistry:
    """Registry for managing event listeners."""
    
    def __init__(self):
        """Initialize the listener registry."""
        self.listeners: Dict[str, EventListener] = {}
        self.listeners_by_event: Dict[str, List[EventListener]] = {}
    
    def register(self, listener: EventListener) -> None:
        """Register an event listener.
        
        Args:
            listener (EventListener): Listener to register
        """
        if listener.listener_id in self.listeners:
            raise EventListenerError(
                listener.listener_id, 
                operation="register"
            )
        
        self.listeners[listener.listener_id] = listener
        
        # Register for specific event types
        for event_type in listener.get_handled_events():
            if event_type not in self.listeners_by_event:
                self.listeners_by_event[event_type] = []
            
            self.listeners_by_event[event_type].append(listener)
        
        logger.debug(f"Registered event listener: {listener.listener_id}")
    
    def unregister(self, listener_id: str) -> bool:
        """Unregister an event listener.
        
        Args:
            listener_id (str): ID of listener to unregister
            
        Returns:
            bool: True if listener was unregistered
        """
        if listener_id not in self.listeners:
            return False
        
        listener = self.listeners[listener_id]
        
        # Remove from event type mappings
        for event_type in listener.get_handled_events():
            if event_type in self.listeners_by_event:
                if listener in self.listeners_by_event[event_type]:
                    self.listeners_by_event[event_type].remove(listener)
                
                # Clean up empty lists
                if not self.listeners_by_event[event_type]:
                    del self.listeners_by_event[event_type]
        
        del self.listeners[listener_id]
        logger.debug(f"Unregistered event listener: {listener_id}")
        return True
    
    def get_listeners(self, event_type: str) -> List[EventListener]:
        """Get listeners for a specific event type.
        
        Args:
            event_type (str): Event type
            
        Returns:
            List[EventListener]: List of listeners for the event type
        """
        listeners = self.listeners_by_event.get(event_type, [])
        
        # Filter enabled listeners and sort by priority
        enabled_listeners = [l for l in listeners if l.is_enabled()]
        enabled_listeners.sort(key=lambda l: l.get_priority().value, reverse=True)
        
        return enabled_listeners
    
    def get_all_listeners(self) -> List[EventListener]:
        """Get all registered listeners.
        
        Returns:
            List[EventListener]: List of all listeners
        """
        return list(self.listeners.values())
    
    def get_listener(self, listener_id: str) -> Optional[EventListener]:
        """Get a specific listener by ID.
        
        Args:
            listener_id (str): Listener ID
            
        Returns:
            EventListener: Listener if found, None otherwise
        """
        return self.listeners.get(listener_id)
    
    def clear(self) -> None:
        """Clear all registered listeners."""
        self.listeners.clear()
        self.listeners_by_event.clear()
        logger.debug("Cleared all event listeners")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics.
        
        Returns:
            Dict[str, Any]: Registry statistics
        """
        enabled_count = sum(1 for l in self.listeners.values() if l.is_enabled())
        
        return {
            'total_listeners': len(self.listeners),
            'enabled_listeners': enabled_count,
            'disabled_listeners': len(self.listeners) - enabled_count,
            'event_types_covered': len(self.listeners_by_event),
            'listeners_by_event': {
                event_type: len(listeners) 
                for event_type, listeners in self.listeners_by_event.items()
            }
        }
