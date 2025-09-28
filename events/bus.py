"""Event bus for central event routing and management.

This module provides the EventBus class that serves as the central
hub for event dispatching, listener management, and event routing
throughout the game system.
"""

from typing import List, Dict, Optional, Any, Callable, Union
import threading
import time
import logging
from collections import defaultdict, deque

from .core import Event, EventResult, EventPriority
from .listener import EventListener, EventListenerRegistry
from .exceptions import EventDispatchError, EventListenerError


logger = logging.getLogger(__name__)


class EventBus:
    """Central event bus for routing events to listeners.
    
    The EventBus manages event dispatching, listener registration,
    and provides features like event queuing, filtering, and
    performance monitoring.
    """
    
    def __init__(self, max_queue_size: int = 10000, enable_stats: bool = True):
        """Initialize the event bus.
        
        Args:
            max_queue_size (int): Maximum size of event queue
            enable_stats (bool): Enable performance statistics
        """
        self.max_queue_size = max_queue_size
        self.enable_stats = enable_stats
        
        # Core components
        self.listener_registry = EventListenerRegistry()
        
        # Event queue for deferred processing
        self.event_queue: deque[Event] = deque(maxlen=max_queue_size)
        
        # Event filters
        self.event_filters: List[Callable[[Event], bool]] = []
        
        # Statistics
        self.stats = {
            'events_dispatched': 0,
            'events_queued': 0,
            'events_filtered': 0,
            'listeners_notified': 0,
            'errors_occurred': 0,
            'total_processing_time': 0.0,
            'events_by_type': defaultdict(int),
            'results_by_type': defaultdict(int),
        }
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Event hooks
        self.pre_dispatch_hooks: List[Callable[[Event], None]] = []
        self.post_dispatch_hooks: List[Callable[[Event, EventResult], None]] = []
        
        # Configuration
        self.enabled = True
        self.max_processing_time = 1.0  # Maximum time to spend processing events per update
    
    def register_listener(self, listener: EventListener) -> None:
        """Register an event listener.
        
        Args:
            listener (EventListener): Listener to register
        """
        with self._lock:
            self.listener_registry.register(listener)
            logger.info(f"Registered event listener: {listener.listener_id}")
    
    def unregister_listener(self, listener_id: str) -> bool:
        """Unregister an event listener.
        
        Args:
            listener_id (str): ID of listener to unregister
            
        Returns:
            bool: True if listener was unregistered
        """
        with self._lock:
            success = self.listener_registry.unregister(listener_id)
            if success:
                logger.info(f"Unregistered event listener: {listener_id}")
            return success
    
    def dispatch(self, event: Event, immediate: bool = True) -> EventResult:
        """Dispatch an event to listeners.
        
        Args:
            event (Event): Event to dispatch
            immediate (bool): If True, process immediately; if False, queue for later
            
        Returns:
            EventResult: Result of event processing
        """
        if not self.enabled:
            return EventResult.CONTINUE
        
        with self._lock:
            # Validate event
            validation_errors = event.validate()
            if validation_errors:
                logger.warning(f"Event validation failed: {validation_errors}")
                return EventResult.ERROR
            
            # Apply filters
            if not self._apply_filters(event):
                if self.enable_stats:
                    self.stats['events_filtered'] += 1
                return EventResult.CONTINUE
            
            if immediate:
                return self._process_event(event)
            else:
                self._queue_event(event)
                return EventResult.CONTINUE
    
    def dispatch_async(self, event: Event) -> None:
        """Dispatch an event asynchronously (queue for later processing).
        
        Args:
            event (Event): Event to dispatch
        """
        self.dispatch(event, immediate=False)
    
    def process_queued_events(self, max_time: float = None) -> int:
        """Process queued events.
        
        Args:
            max_time (float, optional): Maximum time to spend processing
            
        Returns:
            int: Number of events processed
        """
        if not self.enabled:
            return 0
        
        max_time = max_time or self.max_processing_time
        start_time = time.time()
        processed_count = 0
        
        with self._lock:
            while self.event_queue and (time.time() - start_time) < max_time:
                event = self.event_queue.popleft()
                self._process_event(event)
                processed_count += 1
        
        return processed_count
    
    def _process_event(self, event: Event) -> EventResult:
        """Process a single event.
        
        Args:
            event (Event): Event to process
            
        Returns:
            EventResult: Result of processing
        """
        start_time = time.time()
        
        try:
            # Run pre-dispatch hooks
            for hook in self.pre_dispatch_hooks:
                try:
                    hook(event)
                except Exception as e:
                    logger.warning(f"Pre-dispatch hook error: {e}")
            
            # Get listeners for this event type
            listeners = self.listener_registry.get_listeners(event.event_type)
            
            if not listeners:
                logger.debug(f"No listeners for event type: {event.event_type}")
                return EventResult.CONTINUE
            
            # Dispatch to listeners
            result = EventResult.CONTINUE
            listeners_notified = 0
            
            for listener in listeners:
                if event.is_cancelled():
                    result = EventResult.CANCELLED
                    break
                
                if event.is_consumed():
                    result = EventResult.CONSUMED
                    break
                
                try:
                    listener_result = listener.handle_event(event)
                    listeners_notified += 1
                    
                    # Update overall result
                    if listener_result in (EventResult.CONSUMED, EventResult.CANCELLED, EventResult.ERROR):
                        result = listener_result
                        break
                    elif listener_result == EventResult.HANDLED:
                        result = EventResult.HANDLED
                
                except Exception as e:
                    logger.error(f"Error in listener {listener.listener_id}: {e}")
                    event.set_error(e)
                    result = EventResult.ERROR
                    break
            
            # Run post-dispatch hooks
            for hook in self.post_dispatch_hooks:
                try:
                    hook(event, result)
                except Exception as e:
                    logger.warning(f"Post-dispatch hook error: {e}")
            
            # Update statistics
            if self.enable_stats:
                self.stats['events_dispatched'] += 1
                self.stats['listeners_notified'] += listeners_notified
                self.stats['total_processing_time'] += time.time() - start_time
                self.stats['events_by_type'][event.event_type] += 1
                self.stats['results_by_type'][result.name] += 1
                
                if event.has_error():
                    self.stats['errors_occurred'] += 1
            
            logger.debug(f"Processed event {event.event_type}: {result.name} "
                        f"({listeners_notified} listeners notified)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing event {event.event_type}: {e}")
            if self.enable_stats:
                self.stats['errors_occurred'] += 1
            raise EventDispatchError(event.event_type, 0, e)
    
    def _queue_event(self, event: Event) -> None:
        """Queue an event for later processing.
        
        Args:
            event (Event): Event to queue
        """
        if len(self.event_queue) >= self.max_queue_size:
            logger.warning("Event queue is full, dropping oldest event")
            self.event_queue.popleft()
        
        self.event_queue.append(event)
        
        if self.enable_stats:
            self.stats['events_queued'] += 1
        
        logger.debug(f"Queued event: {event.event_type}")
    
    def _apply_filters(self, event: Event) -> bool:
        """Apply event filters to determine if event should be processed.
        
        Args:
            event (Event): Event to filter
            
        Returns:
            bool: True if event should be processed
        """
        for filter_func in self.event_filters:
            try:
                if not filter_func(event):
                    logger.debug(f"Event filtered out: {event.event_type}")
                    return False
            except Exception as e:
                logger.warning(f"Event filter error: {e}")
                # Continue processing if filter fails
        
        return True
    
    def add_filter(self, filter_func: Callable[[Event], bool]) -> None:
        """Add an event filter.
        
        Args:
            filter_func (Callable): Filter function that returns True to allow event
        """
        with self._lock:
            if filter_func not in self.event_filters:
                self.event_filters.append(filter_func)
                logger.debug("Added event filter")
    
    def remove_filter(self, filter_func: Callable[[Event], bool]) -> bool:
        """Remove an event filter.
        
        Args:
            filter_func (Callable): Filter function to remove
            
        Returns:
            bool: True if filter was removed
        """
        with self._lock:
            if filter_func in self.event_filters:
                self.event_filters.remove(filter_func)
                logger.debug("Removed event filter")
                return True
            return False
    
    def add_pre_dispatch_hook(self, hook: Callable[[Event], None]) -> None:
        """Add a pre-dispatch hook.
        
        Args:
            hook (Callable): Hook function to call before dispatching
        """
        with self._lock:
            if hook not in self.pre_dispatch_hooks:
                self.pre_dispatch_hooks.append(hook)
    
    def add_post_dispatch_hook(self, hook: Callable[[Event, EventResult], None]) -> None:
        """Add a post-dispatch hook.
        
        Args:
            hook (Callable): Hook function to call after dispatching
        """
        with self._lock:
            if hook not in self.post_dispatch_hooks:
                self.post_dispatch_hooks.append(hook)
    
    def clear_queue(self) -> int:
        """Clear the event queue.
        
        Returns:
            int: Number of events that were cleared
        """
        with self._lock:
            count = len(self.event_queue)
            self.event_queue.clear()
            logger.debug(f"Cleared {count} events from queue")
            return count
    
    def get_queue_size(self) -> int:
        """Get current queue size.
        
        Returns:
            int: Number of events in queue
        """
        return len(self.event_queue)
    
    def get_listeners(self, event_type: str = None) -> Union[List[EventListener], Dict[str, List[EventListener]]]:
        """Get listeners for a specific event type or all listeners.
        
        Args:
            event_type (str, optional): Event type to get listeners for
            
        Returns:
            Union[List[EventListener], Dict[str, List[EventListener]]]: Listeners
        """
        if event_type:
            return self.listener_registry.get_listeners(event_type)
        else:
            # Return all listeners grouped by event type
            result = {}
            for listener in self.listener_registry.get_all_listeners():
                for handled_event in listener.get_handled_events():
                    if handled_event not in result:
                        result[handled_event] = []
                    if listener not in result[handled_event]:
                        result[handled_event].append(listener)
            return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics.
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        with self._lock:
            stats = self.stats.copy()
            stats['queue_size'] = len(self.event_queue)
            stats['max_queue_size'] = self.max_queue_size
            stats['listeners_registered'] = len(self.listener_registry.listeners)
            stats['event_filters'] = len(self.event_filters)
            stats['enabled'] = self.enabled
            
            # Calculate averages
            if stats['events_dispatched'] > 0:
                stats['avg_processing_time'] = stats['total_processing_time'] / stats['events_dispatched']
                stats['avg_listeners_per_event'] = stats['listeners_notified'] / stats['events_dispatched']
            else:
                stats['avg_processing_time'] = 0.0
                stats['avg_listeners_per_event'] = 0.0
            
            return stats
    
    def reset_stats(self) -> None:
        """Reset all statistics."""
        with self._lock:
            self.stats = {
                'events_dispatched': 0,
                'events_queued': 0,
                'events_filtered': 0,
                'listeners_notified': 0,
                'errors_occurred': 0,
                'total_processing_time': 0.0,
                'events_by_type': defaultdict(int),
                'results_by_type': defaultdict(int),
            }
            logger.debug("Reset event bus statistics")
    
    def enable(self) -> None:
        """Enable the event bus."""
        self.enabled = True
        logger.info("Event bus enabled")
    
    def disable(self) -> None:
        """Disable the event bus."""
        self.enabled = False
        logger.info("Event bus disabled")
    
    def is_enabled(self) -> bool:
        """Check if event bus is enabled.
        
        Returns:
            bool: True if enabled
        """
        return self.enabled
    
    def shutdown(self) -> None:
        """Shutdown the event bus and cleanup resources."""
        with self._lock:
            self.enabled = False
            self.clear_queue()
            self.listener_registry.clear()
            self.event_filters.clear()
            self.pre_dispatch_hooks.clear()
            self.post_dispatch_hooks.clear()
            logger.info("Event bus shut down")


# Global event bus instance
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance.
    
    Returns:
        EventBus: Global event bus
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


def initialize_event_bus(**kwargs) -> EventBus:
    """Initialize the global event bus with custom settings.
    
    Args:
        **kwargs: Arguments to pass to EventBus constructor
        
    Returns:
        EventBus: Initialized event bus
    """
    global _global_event_bus
    _global_event_bus = EventBus(**kwargs)
    return _global_event_bus


def shutdown_event_bus() -> None:
    """Shutdown the global event bus."""
    global _global_event_bus
    if _global_event_bus:
        _global_event_bus.shutdown()
        _global_event_bus = None
