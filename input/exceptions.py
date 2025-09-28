"""Input system exceptions.

This module defines all exceptions used by the input system,
providing clear error handling and debugging information for
input-related operations.
"""


class InputError(Exception):
    """Base exception for all input-related errors."""
    
    def __init__(self, message: str, backend: str = None, context: str = None):
        """Initialize input error.
        
        Args:
            message (str): Error message
            backend (str, optional): Input backend that caused the error
            context (str, optional): Additional context information
        """
        super().__init__(message)
        self.backend = backend
        self.context = context
        self.message = message
    
    def __str__(self) -> str:
        """String representation of the error."""
        parts = [self.message]
        if self.backend:
            parts.append(f"Backend: {self.backend}")
        if self.context:
            parts.append(f"Context: {self.context}")
        return " | ".join(parts)


class InputBackendError(InputError):
    """Exception raised when input backend operations fail."""
    
    def __init__(self, backend: str, operation: str, cause: Exception = None):
        """Initialize input backend error.
        
        Args:
            backend (str): Name of the input backend
            operation (str): Operation that failed
            cause (Exception, optional): Underlying exception
        """
        message = f"Input backend operation failed: {operation}"
        if cause:
            message += f" ({type(cause).__name__}: {cause})"
        
        super().__init__(message, backend, operation)
        self.operation = operation
        self.cause = cause


class InputMappingError(InputError):
    """Exception raised when input mapping operations fail."""
    
    def __init__(self, mapping_name: str, action: str = None, cause: Exception = None):
        """Initialize input mapping error.
        
        Args:
            mapping_name (str): Name of the input mapping
            action (str, optional): Action that failed
            cause (Exception, optional): Underlying exception
        """
        message = f"Input mapping error: {mapping_name}"
        if action:
            message += f" (action: {action})"
        if cause:
            message += f" ({type(cause).__name__}: {cause})"
        
        super().__init__(message, context=mapping_name)
        self.mapping_name = mapping_name
        self.action = action
        self.cause = cause


class InputConfigurationError(InputError):
    """Exception raised when input configuration is invalid."""
    
    def __init__(self, config_key: str, config_value: str = None, reason: str = None):
        """Initialize input configuration error.
        
        Args:
            config_key (str): Configuration key that is invalid
            config_value (str, optional): Invalid configuration value
            reason (str, optional): Reason why configuration is invalid
        """
        message = f"Invalid input configuration: {config_key}"
        if config_value:
            message += f" = {config_value}"
        if reason:
            message += f" ({reason})"
        
        super().__init__(message, context=config_key)
        self.config_key = config_key
        self.config_value = config_value
        self.reason = reason


class InputDeviceError(InputError):
    """Exception raised when input device operations fail."""
    
    def __init__(self, device_type: str, device_id: str = None, operation: str = None):
        """Initialize input device error.
        
        Args:
            device_type (str): Type of input device (keyboard, mouse, gamepad, etc.)
            device_id (str, optional): Device identifier
            operation (str, optional): Operation that failed
        """
        message = f"Input device error: {device_type}"
        if device_id:
            message += f" (ID: {device_id})"
        if operation:
            message += f" - {operation}"
        
        super().__init__(message, context=device_type)
        self.device_type = device_type
        self.device_id = device_id
        self.operation = operation


class InputSequenceError(InputError):
    """Exception raised when input sequence operations fail."""
    
    def __init__(self, sequence_name: str, step: int = None, reason: str = None):
        """Initialize input sequence error.
        
        Args:
            sequence_name (str): Name of the input sequence
            step (int, optional): Step in sequence that failed
            reason (str, optional): Reason for failure
        """
        message = f"Input sequence error: {sequence_name}"
        if step is not None:
            message += f" (step {step})"
        if reason:
            message += f" - {reason}"
        
        super().__init__(message, context=sequence_name)
        self.sequence_name = sequence_name
        self.step = step
        self.reason = reason
