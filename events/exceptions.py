"""Event system exceptions.

This module defines all exceptions used by the event system,
providing clear error handling and debugging information for
event-related operations.
"""


class EventError(Exception):
    """Base exception for all event-related errors."""
    
    def __init__(self, message: str, event_type: str = None, context: str = None):
        """Initialize event error.
        
        Args:
            message (str): Error message
            event_type (str, optional): Type of event that caused the error
            context (str, optional): Additional context information
        """
        super().__init__(message)
        self.event_type = event_type
        self.context = context
        self.message = message
    
    def __str__(self) -> str:
        """String representation of the error."""
        parts = [self.message]
        if self.event_type:
            parts.append(f"Event: {self.event_type}")
        if self.context:
            parts.append(f"Context: {self.context}")
        return " | ".join(parts)


class EventDispatchError(EventError):
    """Exception raised when event dispatching fails."""
    
    def __init__(self, event_type: str, listener_count: int = 0, cause: Exception = None):
        """Initialize event dispatch error.
        
        Args:
            event_type (str): Type of event that failed to dispatch
            listener_count (int): Number of listeners that were notified
            cause (Exception, optional): Underlying exception
        """
        message = f"Event dispatch failed: {event_type}"
        if listener_count > 0:
            message += f" (notified {listener_count} listeners)"
        if cause:
            message += f" ({type(cause).__name__}: {cause})"
        
        super().__init__(message, event_type)
        self.listener_count = listener_count
        self.cause = cause


class EventListenerError(EventError):
    """Exception raised when event listener operations fail."""
    
    def __init__(self, listener_name: str, event_type: str = None, operation: str = None):
        """Initialize event listener error.
        
        Args:
            listener_name (str): Name or identifier of the listener
            event_type (str, optional): Type of event being processed
            operation (str, optional): Operation that failed
        """
        message = f"Event listener error: {listener_name}"
        if operation:
            message += f" ({operation})"
        
        super().__init__(message, event_type)
        self.listener_name = listener_name
        self.operation = operation


class EventRegistrationError(EventError):
    """Exception raised when event registration fails."""
    
    def __init__(self, event_type: str, listener_id: str = None, reason: str = None):
        """Initialize event registration error.
        
        Args:
            event_type (str): Type of event being registered
            listener_id (str, optional): ID of listener being registered
            reason (str, optional): Reason for registration failure
        """
        message = f"Event registration failed: {event_type}"
        if listener_id:
            message += f" (listener: {listener_id})"
        if reason:
            message += f" - {reason}"
        
        super().__init__(message, event_type)
        self.listener_id = listener_id
        self.reason = reason


class EventValidationError(EventError):
    """Exception raised when event validation fails."""
    
    def __init__(self, event_type: str, validation_errors: list = None):
        """Initialize event validation error.
        
        Args:
            event_type (str): Type of event that failed validation
            validation_errors (list, optional): List of validation error messages
        """
        message = f"Event validation failed: {event_type}"
        if validation_errors:
            message += f" (errors: {', '.join(validation_errors)})"
        
        super().__init__(message, event_type)
        self.validation_errors = validation_errors or []


class EventTimeoutError(EventError):
    """Exception raised when event processing times out."""
    
    def __init__(self, event_type: str, timeout: float, elapsed: float = None):
        """Initialize event timeout error.
        
        Args:
            event_type (str): Type of event that timed out
            timeout (float): Timeout value in seconds
            elapsed (float, optional): Actual elapsed time
        """
        message = f"Event processing timeout: {event_type} (timeout: {timeout}s"
        if elapsed is not None:
            message += f", elapsed: {elapsed:.2f}s"
        message += ")"
        
        super().__init__(message, event_type)
        self.timeout = timeout
        self.elapsed = elapsed


class EventCancellationError(EventError):
    """Exception raised when event is cancelled during processing."""
    
    def __init__(self, event_type: str, cancelled_by: str = None, reason: str = None):
        """Initialize event cancellation error.
        
        Args:
            event_type (str): Type of event that was cancelled
            cancelled_by (str, optional): Component that cancelled the event
            reason (str, optional): Reason for cancellation
        """
        message = f"Event cancelled: {event_type}"
        if cancelled_by:
            message += f" (by: {cancelled_by})"
        if reason:
            message += f" - {reason}"
        
        super().__init__(message, event_type)
        self.cancelled_by = cancelled_by
        self.reason = reason
