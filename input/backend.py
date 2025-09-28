"""Input backend interface and capabilities.

This module defines the abstract interface that all input backends must
implement, along with capability detection and device management.
"""

from abc import ABC, abstractmethod
from enum import Enum, Flag, auto
from typing import List, Optional, Dict, Any, Callable, Set
from dataclasses import dataclass

from .events import InputEvent, AnyInputEvent


class InputDeviceType(Enum):
    """Types of input devices."""
    
    KEYBOARD = auto()
    MOUSE = auto()
    GAMEPAD = auto()
    TOUCH = auto()
    JOYSTICK = auto()
    STYLUS = auto()
    TRACKPAD = auto()


class InputCapabilities(Flag):
    """Input backend capabilities."""
    
    NONE = 0
    
    # Device support
    KEYBOARD = auto()
    MOUSE = auto()
    GAMEPAD = auto()
    TOUCH = auto()
    JOYSTICK = auto()
    
    # Feature support
    KEY_REPEAT = auto()
    MOUSE_CAPTURE = auto()
    MOUSE_RELATIVE = auto()
    GAMEPAD_RUMBLE = auto()
    TOUCH_MULTIPOINT = auto()
    TOUCH_PRESSURE = auto()
    
    # Advanced features
    RAW_INPUT = auto()
    DEVICE_HOTPLUG = auto()
    CUSTOM_CURSORS = auto()
    CLIPBOARD_ACCESS = auto()
    
    # Platform features
    WINDOW_EVENTS = auto()
    SYSTEM_EVENTS = auto()
    POWER_EVENTS = auto()


@dataclass
class InputDevice:
    """Represents an input device."""
    
    device_id: str
    device_type: InputDeviceType
    name: str
    connected: bool = True
    capabilities: InputCapabilities = InputCapabilities.NONE
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize device properties."""
        if self.properties is None:
            self.properties = {}


class InputBackend(ABC):
    """Abstract base class for input backends.
    
    This class defines the interface that all input backends must implement
    to provide input handling for different platforms and systems.
    """
    
    def __init__(self, name: str):
        """Initialize the input backend.
        
        Args:
            name (str): Name of the input backend
        """
        self.name = name
        self.initialized = False
        self.devices: Dict[str, InputDevice] = {}
        self.event_callbacks: List[Callable[[AnyInputEvent], None]] = []
        self.device_callbacks: List[Callable[[InputDevice, bool], None]] = []
    
    @property
    @abstractmethod
    def capabilities(self) -> InputCapabilities:
        """Get the capabilities of this input backend.
        
        Returns:
            InputCapabilities: Backend capabilities
        """
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the input backend.
        
        Returns:
            bool: True if initialization succeeded
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the input backend and cleanup resources."""
        pass
    
    @abstractmethod
    def poll_events(self) -> List[AnyInputEvent]:
        """Poll for input events.
        
        Returns:
            List[AnyInputEvent]: List of input events since last poll
        """
        pass
    
    @abstractmethod
    def get_devices(self) -> List[InputDevice]:
        """Get list of available input devices.
        
        Returns:
            List[InputDevice]: Available input devices
        """
        pass
    
    @abstractmethod
    def is_key_pressed(self, key: str) -> bool:
        """Check if a key is currently pressed.
        
        Args:
            key (str): Key identifier
            
        Returns:
            bool: True if key is pressed
        """
        pass
    
    @abstractmethod
    def is_mouse_button_pressed(self, button: str) -> bool:
        """Check if a mouse button is currently pressed.
        
        Args:
            button (str): Mouse button identifier
            
        Returns:
            bool: True if button is pressed
        """
        pass
    
    @abstractmethod
    def get_mouse_position(self) -> tuple[int, int]:
        """Get current mouse position.
        
        Returns:
            tuple[int, int]: Mouse (x, y) coordinates
        """
        pass
    
    def add_event_callback(self, callback: Callable[[AnyInputEvent], None]) -> None:
        """Add an event callback.
        
        Args:
            callback (Callable): Function to call for each input event
        """
        if callback not in self.event_callbacks:
            self.event_callbacks.append(callback)
    
    def remove_event_callback(self, callback: Callable[[AnyInputEvent], None]) -> None:
        """Remove an event callback.
        
        Args:
            callback (Callable): Callback function to remove
        """
        if callback in self.event_callbacks:
            self.event_callbacks.remove(callback)
    
    def add_device_callback(self, callback: Callable[[InputDevice, bool], None]) -> None:
        """Add a device connection callback.
        
        Args:
            callback (Callable): Function to call when devices connect/disconnect
                                 Parameters: (device, connected)
        """
        if callback not in self.device_callbacks:
            self.device_callbacks.append(callback)
    
    def remove_device_callback(self, callback: Callable[[InputDevice, bool], None]) -> None:
        """Remove a device connection callback.
        
        Args:
            callback (Callable): Callback function to remove
        """
        if callback in self.device_callbacks:
            self.device_callbacks.remove(callback)
    
    def has_capability(self, capability: InputCapabilities) -> bool:
        """Check if backend has a specific capability.
        
        Args:
            capability (InputCapabilities): Capability to check
            
        Returns:
            bool: True if backend has the capability
        """
        # Special case for NONE - check if backend has no capabilities
        if capability == InputCapabilities.NONE:
            return self.capabilities == InputCapabilities.NONE
        return bool(self.capabilities & capability)
    
    def get_device(self, device_id: str) -> Optional[InputDevice]:
        """Get a specific input device.
        
        Args:
            device_id (str): Device identifier
            
        Returns:
            InputDevice: Device if found, None otherwise
        """
        return self.devices.get(device_id)
    
    def get_devices_by_type(self, device_type: InputDeviceType) -> List[InputDevice]:
        """Get all devices of a specific type.
        
        Args:
            device_type (InputDeviceType): Type of device to find
            
        Returns:
            List[InputDevice]: Matching devices
        """
        return [device for device in self.devices.values() 
                if device.device_type == device_type and device.connected]
    
    def _notify_event_callbacks(self, event: AnyInputEvent) -> None:
        """Notify all event callbacks of a new event.
        
        Args:
            event (AnyInputEvent): Input event to broadcast
        """
        for callback in self.event_callbacks:
            try:
                callback(event)
            except Exception as e:
                # Don't let callback errors break input processing
                print(f"Input event callback error: {e}")
    
    def _notify_device_callbacks(self, device: InputDevice, connected: bool) -> None:
        """Notify all device callbacks of a device connection change.
        
        Args:
            device (InputDevice): Device that changed
            connected (bool): True if device connected, False if disconnected
        """
        for callback in self.device_callbacks:
            try:
                callback(device, connected)
            except Exception as e:
                # Don't let callback errors break device management
                print(f"Input device callback error: {e}")
    
    def _register_device(self, device: InputDevice) -> None:
        """Register a new input device.
        
        Args:
            device (InputDevice): Device to register
        """
        self.devices[device.device_id] = device
        self._notify_device_callbacks(device, True)
    
    def _unregister_device(self, device_id: str) -> None:
        """Unregister an input device.
        
        Args:
            device_id (str): ID of device to unregister
        """
        if device_id in self.devices:
            device = self.devices[device_id]
            device.connected = False
            self._notify_device_callbacks(device, False)
            del self.devices[device_id]
    
    def supports_device_type(self, device_type: InputDeviceType) -> bool:
        """Check if backend supports a device type.
        
        Args:
            device_type (InputDeviceType): Device type to check
            
        Returns:
            bool: True if device type is supported
        """
        capability_map = {
            InputDeviceType.KEYBOARD: InputCapabilities.KEYBOARD,
            InputDeviceType.MOUSE: InputCapabilities.MOUSE,
            InputDeviceType.GAMEPAD: InputCapabilities.GAMEPAD,
            InputDeviceType.TOUCH: InputCapabilities.TOUCH,
            InputDeviceType.JOYSTICK: InputCapabilities.JOYSTICK,
        }
        
        required_capability = capability_map.get(device_type)
        if required_capability:
            return self.has_capability(required_capability)
        
        return False
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about this backend.
        
        Returns:
            Dict[str, Any]: Backend information
        """
        return {
            'name': self.name,
            'initialized': self.initialized,
            'capabilities': [cap.name for cap in InputCapabilities if self.has_capability(cap)],
            'device_count': len(self.devices),
            'devices': [
                {
                    'id': device.device_id,
                    'type': device.device_type.name,
                    'name': device.name,
                    'connected': device.connected
                }
                for device in self.devices.values()
            ]
        }
    
    def __str__(self) -> str:
        """String representation of the backend."""
        return f"{self.__class__.__name__}(name='{self.name}', initialized={self.initialized})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the backend."""
        return (f"{self.__class__.__name__}(name='{self.name}', "
                f"initialized={self.initialized}, devices={len(self.devices)})")


class NullInputBackend(InputBackend):
    """Null input backend that provides no input functionality.
    
    This backend can be used as a fallback when no other backends
    are available or for testing purposes.
    """
    
    def __init__(self):
        """Initialize the null input backend."""
        super().__init__("null")
    
    @property
    def capabilities(self) -> InputCapabilities:
        """Get capabilities (none for null backend)."""
        return InputCapabilities.NONE
    
    def initialize(self) -> bool:
        """Initialize (always succeeds for null backend)."""
        self.initialized = True
        return True
    
    def shutdown(self) -> None:
        """Shutdown (no-op for null backend)."""
        self.initialized = False
    
    def poll_events(self) -> List[AnyInputEvent]:
        """Poll events (always empty for null backend)."""
        return []
    
    def get_devices(self) -> List[InputDevice]:
        """Get devices (always empty for null backend)."""
        return []
    
    def is_key_pressed(self, key: str) -> bool:
        """Check key state (always False for null backend)."""
        return False
    
    def is_mouse_button_pressed(self, button: str) -> bool:
        """Check mouse button state (always False for null backend)."""
        return False
    
    def get_mouse_position(self) -> tuple[int, int]:
        """Get mouse position (always (0, 0) for null backend)."""
        return (0, 0)
