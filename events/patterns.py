"""Advanced event patterns for complex event handling.

This module provides sophisticated event patterns like chains,
conditional events, delayed events, and recurring events that
enable complex game behaviors and interactions.
"""

import time
import threading
from typing import List, Dict, Optional, Any, Callable, Union
from abc import ABC, abstractmethod
from enum import Enum, auto
import logging

from .core import Event, EventResult, EventPriority, EventContext
from .bus import EventBus, get_event_bus
from .exceptions import EventError


logger = logging.getLogger(__name__)


class PatternState(Enum):
    """States for event patterns."""
    
    PENDING = auto()        # Pattern is waiting to execute
    ACTIVE = auto()         # Pattern is currently executing
    COMPLETED = auto()      # Pattern has completed successfully
    CANCELLED = auto()      # Pattern was cancelled
    FAILED = auto()         # Pattern failed due to error


class EventPattern(ABC):
    """Abstract base class for event patterns."""
    
    def __init__(self, pattern_id: str = None, event_bus: EventBus = None):
        """Initialize event pattern.
        
        Args:
            pattern_id (str, optional): Unique identifier for pattern
            event_bus (EventBus, optional): Event bus to use
        """
        self.pattern_id = pattern_id or f"{self.__class__.__name__}_{id(self)}"
        self.event_bus = event_bus or get_event_bus()
        self.state = PatternState.PENDING
        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.error: Optional[Exception] = None
        
        # Pattern metadata
        self.metadata: Dict[str, Any] = {}
        
        # Callbacks
        self.on_start: Optional[Callable[['EventPattern'], None]] = None
        self.on_complete: Optional[Callable[['EventPattern'], None]] = None
        self.on_cancel: Optional[Callable[['EventPattern'], None]] = None
        self.on_error: Optional[Callable[['EventPattern', Exception], None]] = None
    
    @abstractmethod
    def execute(self) -> bool:
        """Execute the event pattern.
        
        Returns:
            bool: True if pattern started successfully
        """
        pass
    
    @abstractmethod
    def cancel(self) -> bool:
        """Cancel the event pattern.
        
        Returns:
            bool: True if pattern was cancelled
        """
        pass
    
    def start(self) -> bool:
        """Start the event pattern.
        
        Returns:
            bool: True if pattern started successfully
        """
        if self.state != PatternState.PENDING:
            return False
        
        try:
            self.state = PatternState.ACTIVE
            self.started_at = time.time()
            
            if self.on_start:
                self.on_start(self)
            
            return self.execute()
            
        except Exception as e:
            self.error = e
            self.state = PatternState.FAILED
            if self.on_error:
                self.on_error(self, e)
            logger.error(f"Error starting pattern {self.pattern_id}: {e}")
            return False
    
    def complete(self) -> None:
        """Mark pattern as completed."""
        if self.state == PatternState.ACTIVE:
            self.state = PatternState.COMPLETED
            self.completed_at = time.time()
            
            if self.on_complete:
                self.on_complete(self)
            
            logger.debug(f"Pattern {self.pattern_id} completed")
    
    def fail(self, error: Exception) -> None:
        """Mark pattern as failed.
        
        Args:
            error (Exception): Error that caused failure
        """
        self.error = error
        self.state = PatternState.FAILED
        self.completed_at = time.time()
        
        if self.on_error:
            self.on_error(self, error)
        
        logger.error(f"Pattern {self.pattern_id} failed: {error}")
    
    def is_active(self) -> bool:
        """Check if pattern is active.
        
        Returns:
            bool: True if pattern is active
        """
        return self.state == PatternState.ACTIVE
    
    def is_completed(self) -> bool:
        """Check if pattern is completed.
        
        Returns:
            bool: True if pattern is completed
        """
        return self.state in (PatternState.COMPLETED, PatternState.CANCELLED, PatternState.FAILED)
    
    def get_duration(self) -> Optional[float]:
        """Get pattern execution duration.
        
        Returns:
            float: Duration in seconds, None if not completed
        """
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the pattern.
        
        Args:
            key (str): Metadata key
            value (Any): Metadata value
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata from the pattern.
        
        Args:
            key (str): Metadata key
            default (Any): Default value if key not found
            
        Returns:
            Any: Metadata value or default
        """
        return self.metadata.get(key, default)


class EventChain(EventPattern):
    """Chain of events that execute in sequence."""
    
    def __init__(self, events: List[Event], pattern_id: str = None,
                 event_bus: EventBus = None, stop_on_error: bool = True):
        """Initialize event chain.
        
        Args:
            events (List[Event]): Events to execute in sequence
            pattern_id (str, optional): Pattern identifier
            event_bus (EventBus, optional): Event bus to use
            stop_on_error (bool): Whether to stop chain on first error
        """
        super().__init__(pattern_id, event_bus)
        self.events = events.copy()
        self.stop_on_error = stop_on_error
        self.current_index = 0
        self.results: List[EventResult] = []
    
    def execute(self) -> bool:
        """Execute the event chain."""
        if not self.events:
            self.complete()
            return True
        
        self._execute_next_event()
        return True
    
    def _execute_next_event(self) -> None:
        """Execute the next event in the chain."""
        if self.current_index >= len(self.events):
            self.complete()
            return
        
        event = self.events[self.current_index]
        
        try:
            result = self.event_bus.dispatch(event)
            self.results.append(result)
            
            # Check if we should continue
            if result == EventResult.ERROR and self.stop_on_error:
                self.fail(EventError(f"Event chain stopped due to error in event {self.current_index}"))
                return
            
            self.current_index += 1
            
            # Continue with next event
            if self.current_index < len(self.events):
                self._execute_next_event()
            else:
                self.complete()
                
        except Exception as e:
            self.fail(e)
    
    def cancel(self) -> bool:
        """Cancel the event chain."""
        if self.state == PatternState.ACTIVE:
            self.state = PatternState.CANCELLED
            self.completed_at = time.time()
            
            if self.on_cancel:
                self.on_cancel(self)
            
            return True
        return False
    
    def get_progress(self) -> float:
        """Get chain execution progress.
        
        Returns:
            float: Progress as percentage (0.0 to 1.0)
        """
        if not self.events:
            return 1.0
        return self.current_index / len(self.events)


class ConditionalEvent(EventPattern):
    """Event that executes only if a condition is met."""
    
    def __init__(self, event: Event, condition: Callable[[], bool],
                 pattern_id: str = None, event_bus: EventBus = None,
                 check_interval: float = 0.1, timeout: float = None):
        """Initialize conditional event.
        
        Args:
            event (Event): Event to execute conditionally
            condition (Callable): Function that returns True when event should execute
            pattern_id (str, optional): Pattern identifier
            event_bus (EventBus, optional): Event bus to use
            check_interval (float): How often to check condition (seconds)
            timeout (float, optional): Maximum time to wait for condition
        """
        super().__init__(pattern_id, event_bus)
        self.event = event
        self.condition = condition
        self.check_interval = check_interval
        self.timeout = timeout
        self.timer: Optional[threading.Timer] = None
        self.timeout_timer: Optional[threading.Timer] = None
    
    def execute(self) -> bool:
        """Execute the conditional event."""
        self._check_condition()
        
        # Set timeout if specified
        if self.timeout:
            self.timeout_timer = threading.Timer(self.timeout, self._on_timeout)
            self.timeout_timer.start()
        
        return True
    
    def _check_condition(self) -> None:
        """Check if condition is met."""
        if self.state != PatternState.ACTIVE:
            return
        
        try:
            if self.condition():
                # Condition met, execute event
                result = self.event_bus.dispatch(self.event)
                self.add_metadata('event_result', result)
                self.complete()
                
                # Cancel timeout timer
                if self.timeout_timer:
                    self.timeout_timer.cancel()
            else:
                # Condition not met, schedule next check
                self.timer = threading.Timer(self.check_interval, self._check_condition)
                self.timer.start()
                
        except Exception as e:
            self.fail(e)
    
    def _on_timeout(self) -> None:
        """Handle timeout."""
        if self.state == PatternState.ACTIVE:
            self.state = PatternState.CANCELLED
            self.completed_at = time.time()
            self.add_metadata('timeout', True)
            
            if self.timer:
                self.timer.cancel()
            
            if self.on_cancel:
                self.on_cancel(self)
            
            logger.debug(f"Conditional event {self.pattern_id} timed out")
    
    def cancel(self) -> bool:
        """Cancel the conditional event."""
        if self.state == PatternState.ACTIVE:
            self.state = PatternState.CANCELLED
            self.completed_at = time.time()
            
            if self.timer:
                self.timer.cancel()
            if self.timeout_timer:
                self.timeout_timer.cancel()
            
            if self.on_cancel:
                self.on_cancel(self)
            
            return True
        return False


class DelayedEvent(EventPattern):
    """Event that executes after a specified delay."""
    
    def __init__(self, event: Event, delay: float, pattern_id: str = None,
                 event_bus: EventBus = None):
        """Initialize delayed event.
        
        Args:
            event (Event): Event to execute after delay
            delay (float): Delay in seconds
            pattern_id (str, optional): Pattern identifier
            event_bus (EventBus, optional): Event bus to use
        """
        super().__init__(pattern_id, event_bus)
        self.event = event
        self.delay = delay
        self.timer: Optional[threading.Timer] = None
    
    def execute(self) -> bool:
        """Execute the delayed event."""
        self.timer = threading.Timer(self.delay, self._execute_event)
        self.timer.start()
        return True
    
    def _execute_event(self) -> None:
        """Execute the delayed event."""
        if self.state == PatternState.ACTIVE:
            try:
                result = self.event_bus.dispatch(self.event)
                self.add_metadata('event_result', result)
                self.complete()
            except Exception as e:
                self.fail(e)
    
    def cancel(self) -> bool:
        """Cancel the delayed event."""
        if self.state == PatternState.ACTIVE and self.timer:
            self.timer.cancel()
            self.state = PatternState.CANCELLED
            self.completed_at = time.time()
            
            if self.on_cancel:
                self.on_cancel(self)
            
            return True
        return False


class RecurringEvent(EventPattern):
    """Event that executes repeatedly at specified intervals."""
    
    def __init__(self, event: Event, interval: float, max_occurrences: int = None,
                 pattern_id: str = None, event_bus: EventBus = None):
        """Initialize recurring event.
        
        Args:
            event (Event): Event to execute repeatedly
            interval (float): Interval between executions (seconds)
            max_occurrences (int, optional): Maximum number of executions
            pattern_id (str, optional): Pattern identifier
            event_bus (EventBus, optional): Event bus to use
        """
        super().__init__(pattern_id, event_bus)
        self.event = event
        self.interval = interval
        self.max_occurrences = max_occurrences
        self.occurrence_count = 0
        self.timer: Optional[threading.Timer] = None
    
    def execute(self) -> bool:
        """Execute the recurring event."""
        self._execute_occurrence()
        return True
    
    def _execute_occurrence(self) -> None:
        """Execute one occurrence of the event."""
        if self.state != PatternState.ACTIVE:
            return
        
        try:
            # Execute the event
            result = self.event_bus.dispatch(self.event.clone())
            self.occurrence_count += 1
            
            # Check if we should continue
            if self.max_occurrences and self.occurrence_count >= self.max_occurrences:
                self.add_metadata('total_occurrences', self.occurrence_count)
                self.complete()
            else:
                # Schedule next occurrence
                self.timer = threading.Timer(self.interval, self._execute_occurrence)
                self.timer.start()
                
        except Exception as e:
            self.fail(e)
    
    def cancel(self) -> bool:
        """Cancel the recurring event."""
        if self.state == PatternState.ACTIVE:
            if self.timer:
                self.timer.cancel()
            
            self.state = PatternState.CANCELLED
            self.completed_at = time.time()
            self.add_metadata('total_occurrences', self.occurrence_count)
            
            if self.on_cancel:
                self.on_cancel(self)
            
            return True
        return False
    
    def get_occurrence_count(self) -> int:
        """Get number of occurrences executed.
        
        Returns:
            int: Number of occurrences
        """
        return self.occurrence_count


class EventSequence(EventPattern):
    """Sequence of event patterns that execute in order."""
    
    def __init__(self, patterns: List[EventPattern], pattern_id: str = None,
                 event_bus: EventBus = None, stop_on_error: bool = True):
        """Initialize event sequence.
        
        Args:
            patterns (List[EventPattern]): Patterns to execute in sequence
            pattern_id (str, optional): Pattern identifier
            event_bus (EventBus, optional): Event bus to use
            stop_on_error (bool): Whether to stop sequence on first error
        """
        super().__init__(pattern_id, event_bus)
        self.patterns = patterns.copy()
        self.stop_on_error = stop_on_error
        self.current_index = 0
        
        # Set up pattern callbacks
        for pattern in self.patterns:
            pattern.on_complete = self._on_pattern_complete
            pattern.on_error = self._on_pattern_error
    
    def execute(self) -> bool:
        """Execute the event sequence."""
        if not self.patterns:
            self.complete()
            return True
        
        self._start_current_pattern()
        return True
    
    def _start_current_pattern(self) -> None:
        """Start the current pattern in the sequence."""
        if self.current_index >= len(self.patterns):
            self.complete()
            return
        
        pattern = self.patterns[self.current_index]
        if not pattern.start():
            if self.stop_on_error:
                self.fail(EventError(f"Failed to start pattern {self.current_index}"))
            else:
                self.current_index += 1
                self._start_current_pattern()
    
    def _on_pattern_complete(self, pattern: EventPattern) -> None:
        """Handle pattern completion."""
        if self.state == PatternState.ACTIVE:
            self.current_index += 1
            self._start_current_pattern()
    
    def _on_pattern_error(self, pattern: EventPattern, error: Exception) -> None:
        """Handle pattern error."""
        if self.state == PatternState.ACTIVE:
            if self.stop_on_error:
                self.fail(error)
            else:
                self.current_index += 1
                self._start_current_pattern()
    
    def cancel(self) -> bool:
        """Cancel the event sequence."""
        if self.state == PatternState.ACTIVE:
            # Cancel current pattern
            if self.current_index < len(self.patterns):
                self.patterns[self.current_index].cancel()
            
            self.state = PatternState.CANCELLED
            self.completed_at = time.time()
            
            if self.on_cancel:
                self.on_cancel(self)
            
            return True
        return False


class EventGroup(EventPattern):
    """Group of event patterns that execute concurrently."""
    
    def __init__(self, patterns: List[EventPattern], pattern_id: str = None,
                 event_bus: EventBus = None, wait_for_all: bool = True):
        """Initialize event group.
        
        Args:
            patterns (List[EventPattern]): Patterns to execute concurrently
            pattern_id (str, optional): Pattern identifier
            event_bus (EventBus, optional): Event bus to use
            wait_for_all (bool): Whether to wait for all patterns to complete
        """
        super().__init__(pattern_id, event_bus)
        self.patterns = patterns.copy()
        self.wait_for_all = wait_for_all
        self.completed_patterns = 0
        self.failed_patterns = 0
        
        # Set up pattern callbacks
        for pattern in self.patterns:
            pattern.on_complete = self._on_pattern_complete
            pattern.on_error = self._on_pattern_error
            pattern.on_cancel = self._on_pattern_cancel
    
    def execute(self) -> bool:
        """Execute the event group."""
        if not self.patterns:
            self.complete()
            return True
        
        # Start all patterns
        for pattern in self.patterns:
            pattern.start()
        
        return True
    
    def _on_pattern_complete(self, pattern: EventPattern) -> None:
        """Handle pattern completion."""
        if self.state == PatternState.ACTIVE:
            self.completed_patterns += 1
            self._check_completion()
    
    def _on_pattern_error(self, pattern: EventPattern, error: Exception) -> None:
        """Handle pattern error."""
        if self.state == PatternState.ACTIVE:
            self.failed_patterns += 1
            if not self.wait_for_all:
                self.fail(error)
            else:
                self._check_completion()
    
    def _on_pattern_cancel(self, pattern: EventPattern) -> None:
        """Handle pattern cancellation."""
        if self.state == PatternState.ACTIVE:
            self.completed_patterns += 1
            self._check_completion()
    
    def _check_completion(self) -> None:
        """Check if group is complete."""
        total_finished = self.completed_patterns + self.failed_patterns
        
        if self.wait_for_all:
            if total_finished >= len(self.patterns):
                if self.failed_patterns > 0:
                    self.fail(EventError(f"Event group had {self.failed_patterns} failed patterns"))
                else:
                    self.complete()
        else:
            if self.completed_patterns > 0:
                self.complete()
    
    def cancel(self) -> bool:
        """Cancel the event group."""
        if self.state == PatternState.ACTIVE:
            # Cancel all active patterns
            for pattern in self.patterns:
                if pattern.is_active():
                    pattern.cancel()
            
            self.state = PatternState.CANCELLED
            self.completed_at = time.time()
            
            if self.on_cancel:
                self.on_cancel(self)
            
            return True
        return False


# Convenience functions for creating patterns

def create_event_chain(events: List[Event], **kwargs) -> EventChain:
    """Create an event chain.
    
    Args:
        events (List[Event]): Events to chain
        **kwargs: Additional arguments
        
    Returns:
        EventChain: Created event chain
    """
    return EventChain(events, **kwargs)


def create_delayed_event(event: Event, delay: float, **kwargs) -> DelayedEvent:
    """Create a delayed event.
    
    Args:
        event (Event): Event to delay
        delay (float): Delay in seconds
        **kwargs: Additional arguments
        
    Returns:
        DelayedEvent: Created delayed event
    """
    return DelayedEvent(event, delay, **kwargs)


def create_recurring_event(event: Event, interval: float, **kwargs) -> RecurringEvent:
    """Create a recurring event.
    
    Args:
        event (Event): Event to repeat
        interval (float): Interval in seconds
        **kwargs: Additional arguments
        
    Returns:
        RecurringEvent: Created recurring event
    """
    return RecurringEvent(event, interval, **kwargs)


def create_conditional_event(event: Event, condition: Callable[[], bool], **kwargs) -> ConditionalEvent:
    """Create a conditional event.
    
    Args:
        event (Event): Event to execute conditionally
        condition (Callable): Condition function
        **kwargs: Additional arguments
        
    Returns:
        ConditionalEvent: Created conditional event
    """
    return ConditionalEvent(event, condition, **kwargs)
