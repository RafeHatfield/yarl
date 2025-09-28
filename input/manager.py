"""Central input management system.

This module provides the main InputManager class that coordinates all
input functionality including backends, mapping, state management,
and event dispatching.
"""

from typing import List, Optional, Dict, Any, Callable, Union
import threading
import logging

from .backend import InputBackend, NullInputBackend, InputCapabilities
from .events import InputEvent, AnyInputEvent
from .mapping import InputMapping, InputProfile, InputAction
from .state import InputStateManager, InputSequence, InputCombo
from .libtcod_backend import LibtcodInputBackend
from .exceptions import InputError, InputBackendError, InputMappingError


logger = logging.getLogger(__name__)


class InputManager:
    """Central input management system.
    
    The InputManager coordinates all input-related operations including
    backend management, event processing, input mapping, and state tracking.
    It provides a unified interface for all input functionality.
    """
    
    def __init__(self, 
                 preferred_backend: Optional[str] = None,
                 auto_detect_backend: bool = True):
        """Initialize the input manager.
        
        Args:
            preferred_backend (str, optional): Preferred backend name
            auto_detect_backend (bool): Auto-detect best available backend
        """
        self.preferred_backend = preferred_backend
        self.auto_detect_backend = auto_detect_backend
        
        # Core components
        self.backend: InputBackend = NullInputBackend()
        self.mapping = InputMapping()
        self.state_manager = InputStateManager()
        
        # Available backends
        self.available_backends: Dict[str, type] = {
            'libtcod': LibtcodInputBackend,
            'null': NullInputBackend,
        }
        
        # Event processing
        self.action_callbacks: Dict[str, List[Callable[[str], None]]] = {}
        self.event_callbacks: List[Callable[[AnyInputEvent], None]] = []
        self.enabled = True
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize backend
        if auto_detect_backend:
            self._auto_detect_backend()
        elif preferred_backend:
            self.set_backend(preferred_backend)
    
    def set_backend(self, backend_name: str) -> bool:
        """Set the input backend.
        
        Args:
            backend_name (str): Name of backend to use
            
        Returns:
            bool: True if backend was set successfully
        """
        with self._lock:
            if backend_name not in self.available_backends:
                logger.error(f"Unknown input backend: {backend_name}")
                return False
            
            try:
                # Shutdown current backend
                if self.backend.initialized:
                    self.backend.shutdown()
                
                # Create and initialize new backend
                backend_class = self.available_backends[backend_name]
                new_backend = backend_class()
                
                if new_backend.initialize():
                    self.backend = new_backend
                    logger.info(f"Input backend set to: {backend_name}")
                    return True
                else:
                    logger.error(f"Failed to initialize backend: {backend_name}")
                    return False
                    
            except Exception as e:
                logger.error(f"Error setting backend {backend_name}: {e}")
                return False
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about the current backend.
        
        Returns:
            Dict[str, Any]: Backend information
        """
        return self.backend.get_backend_info()
    
    def get_available_backends(self) -> List[str]:
        """Get list of available backend names.
        
        Returns:
            List[str]: Available backend names
        """
        return list(self.available_backends.keys())
    
    def register_backend(self, name: str, backend_class: type) -> None:
        """Register a custom input backend.
        
        Args:
            name (str): Backend name
            backend_class (type): Backend class (must inherit from InputBackend)
        """
        if not issubclass(backend_class, InputBackend):
            raise InputError(f"Backend class must inherit from InputBackend: {backend_class}")
        
        self.available_backends[name] = backend_class
        logger.info(f"Registered input backend: {name}")
    
    def process_events(self) -> List[str]:
        """Process input events and return triggered actions.
        
        Returns:
            List[str]: List of triggered action names
        """
        if not self.enabled or not self.backend.initialized:
            return []
        
        triggered_actions = []
        
        with self._lock:
            try:
                # Poll events from backend
                events = self.backend.poll_events()
                
                for event in events:
                    # Update state manager
                    self.state_manager.process_event(event)
                    
                    # Notify event callbacks
                    for callback in self.event_callbacks:
                        try:
                            callback(event)
                        except Exception as e:
                            logger.warning(f"Event callback error: {e}")
                    
                    # Get actions for this event
                    actions = self.mapping.get_actions_for_event(event)
                    triggered_actions.extend(actions)
                
                # Update state manager for new frame
                self.state_manager.update_frame()
                
                # Notify action callbacks
                for action in triggered_actions:
                    self._notify_action_callbacks(action)
                
            except Exception as e:
                logger.error(f"Error processing input events: {e}")
        
        return triggered_actions
    
    def is_action_active(self, action: Union[InputAction, str]) -> bool:
        """Check if an action is currently active (key/button held).
        
        Args:
            action (Union[InputAction, str]): Action to check
            
        Returns:
            bool: True if action is active
        """
        action_name = action.value if isinstance(action, InputAction) else str(action)
        mapping = self.mapping.active_profile.get_mapping(action_name) if self.mapping.active_profile else None
        
        if not mapping or not mapping.enabled:
            return False
        
        # Check if any binding for this action is currently active
        for binding in mapping.bindings:
            if not binding.enabled:
                continue
            
            # Check key bindings
            if hasattr(binding, 'key') and binding.key:
                if self.state_manager.is_key_pressed(binding.key):
                    return True
            
            # Check mouse bindings
            if hasattr(binding, 'button') and binding.button:
                if self.state_manager.mouse_state.is_button_pressed(binding.button):
                    return True
            
            # Check gamepad bindings
            if hasattr(binding, 'gamepad_button') and binding.gamepad_button:
                for gamepad_state in self.state_manager.gamepad_states.values():
                    if gamepad_state.connected and gamepad_state.is_button_pressed(binding.gamepad_button):
                        return True
        
        return False
    
    def is_action_just_pressed(self, action: Union[InputAction, str]) -> bool:
        """Check if an action was just pressed this frame.
        
        Args:
            action (Union[InputAction, str]): Action to check
            
        Returns:
            bool: True if action was just pressed
        """
        action_name = action.value if isinstance(action, InputAction) else str(action)
        mapping = self.mapping.active_profile.get_mapping(action_name) if self.mapping.active_profile else None
        
        if not mapping or not mapping.enabled:
            return False
        
        # Check if any binding for this action was just pressed
        for binding in mapping.bindings:
            if not binding.enabled:
                continue
            
            # Check key bindings
            if hasattr(binding, 'key') and binding.key:
                if self.state_manager.is_key_just_pressed(binding.key):
                    return True
            
            # Check mouse bindings
            if hasattr(binding, 'button') and binding.button:
                if self.state_manager.mouse_state.is_button_just_pressed(binding.button):
                    return True
            
            # Check gamepad bindings
            if hasattr(binding, 'gamepad_button') and binding.gamepad_button:
                for gamepad_state in self.state_manager.gamepad_states.values():
                    if gamepad_state.connected and gamepad_state.is_button_just_pressed(binding.gamepad_button):
                        return True
        
        return False
    
    def get_mouse_position(self) -> tuple[int, int]:
        """Get current mouse position.
        
        Returns:
            tuple[int, int]: Mouse (x, y) coordinates
        """
        return self.state_manager.get_mouse_position()
    
    def get_mouse_delta(self) -> tuple[int, int]:
        """Get mouse movement delta for this frame.
        
        Returns:
            tuple[int, int]: Mouse movement (delta_x, delta_y)
        """
        return self.state_manager.get_mouse_delta()
    
    def add_action_callback(self, action: Union[InputAction, str], 
                           callback: Callable[[str], None]) -> None:
        """Add a callback for when an action is triggered.
        
        Args:
            action (Union[InputAction, str]): Action to listen for
            callback (Callable): Function to call when action is triggered
        """
        action_name = action.value if isinstance(action, InputAction) else str(action)
        
        if action_name not in self.action_callbacks:
            self.action_callbacks[action_name] = []
        
        if callback not in self.action_callbacks[action_name]:
            self.action_callbacks[action_name].append(callback)
    
    def remove_action_callback(self, action: Union[InputAction, str],
                              callback: Callable[[str], None]) -> None:
        """Remove an action callback.
        
        Args:
            action (Union[InputAction, str]): Action to stop listening for
            callback (Callable): Callback function to remove
        """
        action_name = action.value if isinstance(action, InputAction) else str(action)
        
        if action_name in self.action_callbacks:
            if callback in self.action_callbacks[action_name]:
                self.action_callbacks[action_name].remove(callback)
    
    def add_event_callback(self, callback: Callable[[AnyInputEvent], None]) -> None:
        """Add a callback for raw input events.
        
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
    
    def set_input_profile(self, profile_name: str) -> bool:
        """Set the active input profile.
        
        Args:
            profile_name (str): Name of profile to activate
            
        Returns:
            bool: True if profile was set
        """
        return self.mapping.set_active_profile(profile_name)
    
    def get_input_profile(self) -> Optional[InputProfile]:
        """Get the current active input profile.
        
        Returns:
            InputProfile: Active profile, or None
        """
        return self.mapping.active_profile
    
    def load_input_profile(self, filepath: str) -> bool:
        """Load an input profile from file.
        
        Args:
            filepath (str): Path to profile file
            
        Returns:
            bool: True if profile was loaded successfully
        """
        try:
            profile = InputProfile.load_from_file(filepath)
            self.mapping.add_profile(profile)
            logger.info(f"Loaded input profile: {profile.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to load input profile from {filepath}: {e}")
            return False
    
    def save_input_profile(self, profile_name: str, filepath: str) -> bool:
        """Save an input profile to file.
        
        Args:
            profile_name (str): Name of profile to save
            filepath (str): Path to save profile to
            
        Returns:
            bool: True if profile was saved successfully
        """
        try:
            profile = self.mapping.get_profile(profile_name)
            if not profile:
                logger.error(f"Profile not found: {profile_name}")
                return False
            
            profile.save_to_file(filepath)
            logger.info(f"Saved input profile: {profile_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save input profile to {filepath}: {e}")
            return False
    
    def add_input_sequence(self, sequence: InputSequence) -> None:
        """Add an input sequence to track.
        
        Args:
            sequence (InputSequence): Sequence to add
        """
        self.state_manager.add_sequence(sequence)
    
    def add_input_combo(self, combo: InputCombo) -> None:
        """Add an input combo to track.
        
        Args:
            combo (InputCombo): Combo to add
        """
        self.state_manager.add_combo(combo)
    
    def enable(self) -> None:
        """Enable input processing."""
        self.enabled = True
        logger.debug("Input processing enabled")
    
    def disable(self) -> None:
        """Disable input processing."""
        self.enabled = False
        logger.debug("Input processing disabled")
    
    def shutdown(self) -> None:
        """Shutdown the input manager and cleanup resources."""
        with self._lock:
            if self.backend.initialized:
                self.backend.shutdown()
            
            self.action_callbacks.clear()
            self.event_callbacks.clear()
            self.enabled = False
            
            logger.info("Input manager shut down")
    
    def _auto_detect_backend(self) -> None:
        """Auto-detect the best available input backend."""
        # Try backends in order of preference
        backend_priority = ['libtcod', 'null']
        
        for backend_name in backend_priority:
            if backend_name in self.available_backends:
                try:
                    backend_class = self.available_backends[backend_name]
                    test_backend = backend_class()
                    
                    if test_backend.initialize():
                        test_backend.shutdown()
                        self.set_backend(backend_name)
                        logger.info(f"Auto-detected input backend: {backend_name}")
                        return
                except Exception as e:
                    logger.debug(f"Backend {backend_name} not available: {e}")
                    continue
        
        # Fallback to null backend
        logger.warning("No suitable input backend found, using null backend")
        self.set_backend('null')
    
    def _notify_action_callbacks(self, action: str) -> None:
        """Notify callbacks for a triggered action.
        
        Args:
            action (str): Action that was triggered
        """
        callbacks = self.action_callbacks.get(action, [])
        for callback in callbacks:
            try:
                callback(action)
            except Exception as e:
                logger.warning(f"Action callback error for {action}: {e}")
    
    def get_capabilities(self) -> InputCapabilities:
        """Get capabilities of the current backend.
        
        Returns:
            InputCapabilities: Backend capabilities
        """
        return self.backend.capabilities
    
    def has_capability(self, capability: InputCapabilities) -> bool:
        """Check if current backend has a specific capability.
        
        Args:
            capability (InputCapabilities): Capability to check
            
        Returns:
            bool: True if backend has the capability
        """
        return self.backend.has_capability(capability)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current input manager status.
        
        Returns:
            Dict[str, Any]: Status information
        """
        return {
            'enabled': self.enabled,
            'backend': self.backend.name,
            'backend_initialized': self.backend.initialized,
            'active_profile': self.mapping.active_profile.name if self.mapping.active_profile else None,
            'available_backends': self.get_available_backends(),
            'capabilities': [cap.name for cap in InputCapabilities if self.has_capability(cap)],
            'action_callbacks': {action: len(callbacks) for action, callbacks in self.action_callbacks.items()},
            'event_callbacks': len(self.event_callbacks),
        }


# Global input manager instance
_global_manager: Optional[InputManager] = None


def get_input_manager() -> InputManager:
    """Get the global input manager instance.
    
    Returns:
        InputManager: Global input manager
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = InputManager()
    return _global_manager


def initialize_input_manager(**kwargs) -> InputManager:
    """Initialize the global input manager with custom settings.
    
    Args:
        **kwargs: Arguments to pass to InputManager constructor
        
    Returns:
        InputManager: Initialized input manager
    """
    global _global_manager
    _global_manager = InputManager(**kwargs)
    return _global_manager


def shutdown_input_manager() -> None:
    """Shutdown the global input manager."""
    global _global_manager
    if _global_manager:
        _global_manager.shutdown()
        _global_manager = None
