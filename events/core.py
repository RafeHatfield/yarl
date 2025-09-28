"""Core event system classes and interfaces.

This module defines the fundamental event classes, priorities, and
context information that form the foundation of the event system.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, Optional, Union, Type
from dataclasses import dataclass, field
import time
import uuid


class EventPriority(Enum):
    """Event priority levels for processing order."""
    
    LOWEST = 0
    LOW = 10
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100
    CRITICAL = 200


class EventResult(Enum):
    """Results of event processing."""
    
    CONTINUE = auto()    # Continue processing other listeners
    HANDLED = auto()     # Event was handled, continue processing
    CONSUMED = auto()    # Event was consumed, stop processing
    CANCELLED = auto()   # Event was cancelled, stop processing
    ERROR = auto()       # Error occurred during processing


@dataclass
class EventContext:
    """Context information for event processing."""
    
    source: Optional[str] = None           # Source component/system
    target: Optional[str] = None           # Target component/system  
    timestamp: float = field(default_factory=time.time)
    priority: EventPriority = EventPriority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the event context.
        
        Args:
            key (str): Metadata key
            value (Any): Metadata value
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata from the event context.
        
        Args:
            key (str): Metadata key
            default (Any): Default value if key not found
            
        Returns:
            Any: Metadata value or default
        """
        return self.metadata.get(key, default)
    
    def has_metadata(self, key: str) -> bool:
        """Check if metadata key exists.
        
        Args:
            key (str): Metadata key to check
            
        Returns:
            bool: True if key exists
        """
        return key in self.metadata


class Event(ABC):
    """Abstract base class for all events.
    
    This class provides the common interface and functionality that all
    events must implement, including context management, cancellation,
    and result handling.
    """
    
    def __init__(self, context: Optional[EventContext] = None):
        """Initialize the event.
        
        Args:
            context (EventContext, optional): Event context
        """
        self.context = context or EventContext()
        self.cancelled = False
        self.result = EventResult.CONTINUE
        self.processed_by: list[str] = []
        self.error: Optional[Exception] = None
    
    @property
    @abstractmethod
    def event_type(self) -> str:
        """Get the event type identifier.
        
        Returns:
            str: Event type identifier
        """
        pass
    
    @property
    def timestamp(self) -> float:
        """Get event timestamp.
        
        Returns:
            float: Event timestamp
        """
        return self.context.timestamp
    
    @property
    def priority(self) -> EventPriority:
        """Get event priority.
        
        Returns:
            EventPriority: Event priority
        """
        return self.context.priority
    
    @property
    def source(self) -> Optional[str]:
        """Get event source.
        
        Returns:
            str: Event source identifier
        """
        return self.context.source
    
    @property
    def target(self) -> Optional[str]:
        """Get event target.
        
        Returns:
            str: Event target identifier
        """
        return self.context.target
    
    @property
    def trace_id(self) -> str:
        """Get event trace ID for debugging.
        
        Returns:
            str: Unique trace identifier
        """
        return self.context.trace_id
    
    def cancel(self, reason: str = None) -> None:
        """Cancel the event.
        
        Args:
            reason (str, optional): Reason for cancellation
        """
        self.cancelled = True
        self.result = EventResult.CANCELLED
        if reason:
            self.context.add_metadata("cancellation_reason", reason)
    
    def is_cancelled(self) -> bool:
        """Check if event is cancelled.
        
        Returns:
            bool: True if event is cancelled
        """
        return self.cancelled
    
    def consume(self) -> None:
        """Mark event as consumed (stops further processing).
        """
        self.result = EventResult.CONSUMED
    
    def is_consumed(self) -> bool:
        """Check if event is consumed.
        
        Returns:
            bool: True if event is consumed
        """
        return self.result == EventResult.CONSUMED
    
    def mark_handled(self) -> None:
        """Mark event as handled (continues processing).
        """
        self.result = EventResult.HANDLED
    
    def is_handled(self) -> bool:
        """Check if event was handled.
        
        Returns:
            bool: True if event was handled
        """
        return self.result in (EventResult.HANDLED, EventResult.CONSUMED)
    
    def set_error(self, error: Exception) -> None:
        """Set an error for this event.
        
        Args:
            error (Exception): Error that occurred
        """
        self.error = error
        self.result = EventResult.ERROR
    
    def has_error(self) -> bool:
        """Check if event has an error.
        
        Returns:
            bool: True if event has an error
        """
        return self.error is not None
    
    def add_processor(self, processor_id: str) -> None:
        """Add a processor to the list of components that processed this event.
        
        Args:
            processor_id (str): ID of the processor
        """
        if processor_id not in self.processed_by:
            self.processed_by.append(processor_id)
    
    def was_processed_by(self, processor_id: str) -> bool:
        """Check if event was processed by a specific processor.
        
        Args:
            processor_id (str): Processor ID to check
            
        Returns:
            bool: True if processed by the given processor
        """
        return processor_id in self.processed_by
    
    def get_processing_chain(self) -> list[str]:
        """Get the chain of processors that handled this event.
        
        Returns:
            list[str]: List of processor IDs in order
        """
        return self.processed_by.copy()
    
    @abstractmethod
    def validate(self) -> list[str]:
        """Validate the event data.
        
        Returns:
            list[str]: List of validation errors (empty if valid)
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation.
        
        Returns:
            Dict[str, Any]: Event data as dictionary
        """
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary representation.
        
        Args:
            data (Dict[str, Any]): Event data dictionary
            
        Returns:
            Event: Created event instance
        """
        pass
    
    def clone(self) -> 'Event':
        """Create a copy of this event.
        
        Returns:
            Event: Cloned event
        """
        # Create new event from dictionary representation
        data = self.to_dict()
        cloned = self.__class__.from_dict(data)
        
        # Generate new trace ID for cloned event
        cloned.context.trace_id = str(uuid.uuid4())
        
        # Copy runtime state
        cloned.cancelled = self.cancelled
        cloned.result = self.result
        cloned.processed_by = self.processed_by.copy()
        cloned.error = self.error
        
        return cloned
    
    def __str__(self) -> str:
        """String representation of the event."""
        return f"{self.event_type}(source={self.source}, target={self.target}, trace_id={self.trace_id[:8]})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the event."""
        return (f"{self.__class__.__name__}(event_type='{self.event_type}', "
                f"source='{self.source}', target='{self.target}', "
                f"priority={self.priority.name}, cancelled={self.cancelled}, "
                f"result={self.result.name})")


class SimpleEvent(Event):
    """Simple event implementation for basic use cases."""
    
    def __init__(self, event_type: str, data: Dict[str, Any] = None, 
                 context: Optional[EventContext] = None):
        """Initialize simple event.
        
        Args:
            event_type (str): Event type identifier
            data (Dict[str, Any], optional): Event data
            context (EventContext, optional): Event context
        """
        super().__init__(context)
        self._event_type = event_type
        self.data = data or {}
    
    @property
    def event_type(self) -> str:
        """Get the event type identifier."""
        return self._event_type
    
    def validate(self) -> list[str]:
        """Validate the event data."""
        errors = []
        
        if not self._event_type:
            errors.append("Event type cannot be empty")
        
        if not isinstance(self.data, dict):
            errors.append("Event data must be a dictionary")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation."""
        return {
            'event_type': self._event_type,
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
    def from_dict(cls, data: Dict[str, Any]) -> 'SimpleEvent':
        """Create event from dictionary representation."""
        context_data = data.get('context', {})
        context = EventContext(
            source=context_data.get('source'),
            target=context_data.get('target'),
            timestamp=context_data.get('timestamp', time.time()),
            priority=EventPriority(context_data.get('priority', EventPriority.NORMAL.value)),
            metadata=context_data.get('metadata', {}),
            trace_id=context_data.get('trace_id', str(uuid.uuid4()))
        )
        
        return cls(
            event_type=data['event_type'],
            data=data.get('data', {}),
            context=context
        )


def create_event(event_type: str, data: Dict[str, Any] = None,
                source: str = None, target: str = None,
                priority: EventPriority = EventPriority.NORMAL) -> SimpleEvent:
    """Create a simple event with the given parameters.
    
    Args:
        event_type (str): Event type identifier
        data (Dict[str, Any], optional): Event data
        source (str, optional): Event source
        target (str, optional): Event target
        priority (EventPriority): Event priority
        
    Returns:
        SimpleEvent: Created event
    """
    context = EventContext(
        source=source,
        target=target,
        priority=priority
    )
    
    return SimpleEvent(event_type, data, context)
