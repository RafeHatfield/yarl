"""Event dispatchers for synchronous and asynchronous event processing.

This module provides different dispatching strategies for events,
including immediate synchronous processing and asynchronous
queued processing with various scheduling options.
"""

import asyncio
import threading
import time
from typing import List, Dict, Optional, Any, Callable, Awaitable
from abc import ABC, abstractmethod
from enum import Enum, auto
import logging

from .core import Event, EventResult, EventPriority
from .listener import EventListener
from .exceptions import EventDispatchError


logger = logging.getLogger(__name__)


class DispatchStrategy(Enum):
    """Event dispatch strategies."""
    
    IMMEDIATE = auto()      # Process immediately on calling thread
    QUEUED = auto()         # Queue for later processing
    THREADED = auto()       # Process on separate thread
    ASYNC = auto()          # Process asynchronously


class EventDispatcher(ABC):
    """Abstract base class for event dispatchers."""
    
    def __init__(self, strategy: DispatchStrategy = DispatchStrategy.IMMEDIATE):
        """Initialize the dispatcher.
        
        Args:
            strategy (DispatchStrategy): Dispatch strategy to use
        """
        self.strategy = strategy
        self.enabled = True
        
        # Statistics
        self.stats = {
            'events_dispatched': 0,
            'dispatch_errors': 0,
            'total_dispatch_time': 0.0,
            'avg_dispatch_time': 0.0,
        }
    
    @abstractmethod
    def dispatch(self, event: Event, listeners: List[EventListener]) -> EventResult:
        """Dispatch an event to listeners.
        
        Args:
            event (Event): Event to dispatch
            listeners (List[EventListener]): Listeners to notify
            
        Returns:
            EventResult: Result of dispatching
        """
        pass
    
    def enable(self) -> None:
        """Enable the dispatcher."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable the dispatcher."""
        self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if dispatcher is enabled.
        
        Returns:
            bool: True if enabled
        """
        return self.enabled
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dispatcher statistics.
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """Reset dispatcher statistics."""
        self.stats = {
            'events_dispatched': 0,
            'dispatch_errors': 0,
            'total_dispatch_time': 0.0,
            'avg_dispatch_time': 0.0,
        }


class SynchronousDispatcher(EventDispatcher):
    """Synchronous event dispatcher that processes events immediately."""
    
    def __init__(self):
        """Initialize synchronous dispatcher."""
        super().__init__(DispatchStrategy.IMMEDIATE)
    
    def dispatch(self, event: Event, listeners: List[EventListener]) -> EventResult:
        """Dispatch event synchronously to all listeners.
        
        Args:
            event (Event): Event to dispatch
            listeners (List[EventListener]): Listeners to notify
            
        Returns:
            EventResult: Result of dispatching
        """
        if not self.enabled:
            return EventResult.CONTINUE
        
        start_time = time.time()
        
        try:
            result = EventResult.CONTINUE
            listeners_notified = 0
            
            for listener in listeners:
                if event.is_cancelled() or event.is_consumed():
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
                    self.stats['dispatch_errors'] += 1
                    break
            
            # Update statistics
            dispatch_time = time.time() - start_time
            self.stats['events_dispatched'] += 1
            self.stats['total_dispatch_time'] += dispatch_time
            self.stats['avg_dispatch_time'] = (
                self.stats['total_dispatch_time'] / self.stats['events_dispatched']
            )
            
            logger.debug(f"Dispatched {event.event_type} to {listeners_notified} listeners: {result.name}")
            
            return result
            
        except Exception as e:
            self.stats['dispatch_errors'] += 1
            logger.error(f"Error dispatching event {event.event_type}: {e}")
            raise EventDispatchError(event.event_type, 0, e)


class ThreadedDispatcher(EventDispatcher):
    """Threaded event dispatcher that processes events on separate threads."""
    
    def __init__(self, max_threads: int = 4):
        """Initialize threaded dispatcher.
        
        Args:
            max_threads (int): Maximum number of worker threads
        """
        super().__init__(DispatchStrategy.THREADED)
        self.max_threads = max_threads
        self.thread_pool = []
        self.active_threads = 0
        self._lock = threading.Lock()
    
    def dispatch(self, event: Event, listeners: List[EventListener]) -> EventResult:
        """Dispatch event on a separate thread.
        
        Args:
            event (Event): Event to dispatch
            listeners (List[EventListener]): Listeners to notify
            
        Returns:
            EventResult: Result of dispatching (immediate return)
        """
        if not self.enabled:
            return EventResult.CONTINUE
        
        with self._lock:
            if self.active_threads >= self.max_threads:
                logger.warning("Thread pool full, dispatching synchronously")
                sync_dispatcher = SynchronousDispatcher()
                return sync_dispatcher.dispatch(event, listeners)
            
            # Create and start thread
            thread = threading.Thread(
                target=self._dispatch_threaded,
                args=(event, listeners),
                daemon=True
            )
            thread.start()
            self.active_threads += 1
            
            return EventResult.CONTINUE
    
    def _dispatch_threaded(self, event: Event, listeners: List[EventListener]) -> None:
        """Dispatch event on thread.
        
        Args:
            event (Event): Event to dispatch
            listeners (List[EventListener]): Listeners to notify
        """
        try:
            sync_dispatcher = SynchronousDispatcher()
            sync_dispatcher.dispatch(event, listeners)
        finally:
            with self._lock:
                self.active_threads -= 1


class QueuedDispatcher(EventDispatcher):
    """Queued event dispatcher that processes events in batches."""
    
    def __init__(self, max_queue_size: int = 1000, batch_size: int = 10):
        """Initialize queued dispatcher.
        
        Args:
            max_queue_size (int): Maximum queue size
            batch_size (int): Number of events to process per batch
        """
        super().__init__(DispatchStrategy.QUEUED)
        self.max_queue_size = max_queue_size
        self.batch_size = batch_size
        self.event_queue: List[tuple[Event, List[EventListener]]] = []
        self._lock = threading.Lock()
    
    def dispatch(self, event: Event, listeners: List[EventListener]) -> EventResult:
        """Queue event for later processing.
        
        Args:
            event (Event): Event to dispatch
            listeners (List[EventListener]): Listeners to notify
            
        Returns:
            EventResult: Result of queueing
        """
        if not self.enabled:
            return EventResult.CONTINUE
        
        with self._lock:
            if len(self.event_queue) >= self.max_queue_size:
                logger.warning("Event queue full, dropping oldest event")
                self.event_queue.pop(0)
            
            self.event_queue.append((event, listeners))
            
        return EventResult.CONTINUE
    
    def process_queue(self, max_events: int = None) -> int:
        """Process queued events.
        
        Args:
            max_events (int, optional): Maximum number of events to process
            
        Returns:
            int: Number of events processed
        """
        if not self.enabled:
            return 0
        
        max_events = max_events or self.batch_size
        processed = 0
        sync_dispatcher = SynchronousDispatcher()
        
        with self._lock:
            events_to_process = self.event_queue[:max_events]
            self.event_queue = self.event_queue[max_events:]
        
        for event, listeners in events_to_process:
            try:
                sync_dispatcher.dispatch(event, listeners)
                processed += 1
            except Exception as e:
                logger.error(f"Error processing queued event: {e}")
                self.stats['dispatch_errors'] += 1
        
        return processed
    
    def get_queue_size(self) -> int:
        """Get current queue size.
        
        Returns:
            int: Number of events in queue
        """
        return len(self.event_queue)
    
    def clear_queue(self) -> int:
        """Clear the event queue.
        
        Returns:
            int: Number of events cleared
        """
        with self._lock:
            count = len(self.event_queue)
            self.event_queue.clear()
            return count


class AsyncEventDispatcher:
    """Asynchronous event dispatcher using asyncio."""
    
    def __init__(self, max_concurrent: int = 10):
        """Initialize async dispatcher.
        
        Args:
            max_concurrent (int): Maximum concurrent event processing
        """
        self.max_concurrent = max_concurrent
        self.enabled = True
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Statistics
        self.stats = {
            'events_dispatched': 0,
            'dispatch_errors': 0,
            'total_dispatch_time': 0.0,
            'concurrent_dispatches': 0,
        }
    
    async def dispatch(self, event: Event, listeners: List[EventListener]) -> EventResult:
        """Dispatch event asynchronously.
        
        Args:
            event (Event): Event to dispatch
            listeners (List[EventListener]): Listeners to notify
            
        Returns:
            EventResult: Result of dispatching
        """
        if not self.enabled:
            return EventResult.CONTINUE
        
        async with self.semaphore:
            start_time = time.time()
            
            try:
                result = EventResult.CONTINUE
                listeners_notified = 0
                
                for listener in listeners:
                    if event.is_cancelled() or event.is_consumed():
                        break
                    
                    try:
                        # Run listener in thread pool for CPU-bound work
                        loop = asyncio.get_event_loop()
                        listener_result = await loop.run_in_executor(
                            None, listener.handle_event, event
                        )
                        listeners_notified += 1
                        
                        # Update overall result
                        if listener_result in (EventResult.CONSUMED, EventResult.CANCELLED, EventResult.ERROR):
                            result = listener_result
                            break
                        elif listener_result == EventResult.HANDLED:
                            result = EventResult.HANDLED
                    
                    except Exception as e:
                        logger.error(f"Error in async listener {listener.listener_id}: {e}")
                        event.set_error(e)
                        result = EventResult.ERROR
                        self.stats['dispatch_errors'] += 1
                        break
                
                # Update statistics
                dispatch_time = time.time() - start_time
                self.stats['events_dispatched'] += 1
                self.stats['total_dispatch_time'] += dispatch_time
                
                logger.debug(f"Async dispatched {event.event_type} to {listeners_notified} listeners: {result.name}")
                
                return result
                
            except Exception as e:
                self.stats['dispatch_errors'] += 1
                logger.error(f"Error in async dispatch {event.event_type}: {e}")
                raise EventDispatchError(event.event_type, 0, e)
    
    async def dispatch_batch(self, events_and_listeners: List[tuple[Event, List[EventListener]]]) -> List[EventResult]:
        """Dispatch multiple events concurrently.
        
        Args:
            events_and_listeners (List[tuple]): List of (event, listeners) pairs
            
        Returns:
            List[EventResult]: Results of dispatching
        """
        if not self.enabled:
            return [EventResult.CONTINUE] * len(events_and_listeners)
        
        tasks = [
            self.dispatch(event, listeners)
            for event, listeners in events_and_listeners
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def enable(self) -> None:
        """Enable the async dispatcher."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable the async dispatcher."""
        self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if dispatcher is enabled.
        
        Returns:
            bool: True if enabled
        """
        return self.enabled
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dispatcher statistics.
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        stats = self.stats.copy()
        if stats['events_dispatched'] > 0:
            stats['avg_dispatch_time'] = stats['total_dispatch_time'] / stats['events_dispatched']
        else:
            stats['avg_dispatch_time'] = 0.0
        return stats
    
    def reset_stats(self) -> None:
        """Reset dispatcher statistics."""
        self.stats = {
            'events_dispatched': 0,
            'dispatch_errors': 0,
            'total_dispatch_time': 0.0,
            'concurrent_dispatches': 0,
        }


class PriorityDispatcher(EventDispatcher):
    """Priority-based event dispatcher that processes high-priority events first."""
    
    def __init__(self, respect_listener_priority: bool = True):
        """Initialize priority dispatcher.
        
        Args:
            respect_listener_priority (bool): Whether to sort listeners by priority
        """
        super().__init__(DispatchStrategy.IMMEDIATE)
        self.respect_listener_priority = respect_listener_priority
    
    def dispatch(self, event: Event, listeners: List[EventListener]) -> EventResult:
        """Dispatch event with priority ordering.
        
        Args:
            event (Event): Event to dispatch
            listeners (List[EventListener]): Listeners to notify
            
        Returns:
            EventResult: Result of dispatching
        """
        if not self.enabled:
            return EventResult.CONTINUE
        
        # Sort listeners by priority if enabled
        if self.respect_listener_priority:
            listeners = sorted(listeners, key=lambda l: l.get_priority().value, reverse=True)
        
        # Use synchronous dispatcher for actual processing
        sync_dispatcher = SynchronousDispatcher()
        return sync_dispatcher.dispatch(event, listeners)


def create_dispatcher(strategy: DispatchStrategy, **kwargs) -> EventDispatcher:
    """Create an event dispatcher based on strategy.
    
    Args:
        strategy (DispatchStrategy): Dispatch strategy
        **kwargs: Additional arguments for dispatcher
        
    Returns:
        EventDispatcher: Created dispatcher
    """
    if strategy == DispatchStrategy.IMMEDIATE:
        return SynchronousDispatcher()
    elif strategy == DispatchStrategy.QUEUED:
        return QueuedDispatcher(**kwargs)
    elif strategy == DispatchStrategy.THREADED:
        return ThreadedDispatcher(**kwargs)
    else:
        raise ValueError(f"Unsupported dispatch strategy: {strategy}")


def create_async_dispatcher(**kwargs) -> AsyncEventDispatcher:
    """Create an async event dispatcher.
    
    Args:
        **kwargs: Arguments for AsyncEventDispatcher
        
    Returns:
        AsyncEventDispatcher: Created async dispatcher
    """
    return AsyncEventDispatcher(**kwargs)
