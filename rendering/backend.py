"""Abstract rendering backend interface.

This module defines the RenderBackend abstract base class that all
rendering implementations must implement. This enables the game to
support multiple rendering technologies (console, GUI, web) through
a unified interface.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Any, Dict
from .surface import Surface
from .color import Color


class RenderBackend(ABC):
    """Abstract base class for rendering backends.
    
    This interface defines all the rendering operations that the game
    requires, allowing different implementations (console, GUI, web)
    to provide their own rendering logic while maintaining a consistent
    API for the game logic.
    
    Key Design Principles:
    - Resolution independence through Surface abstraction
    - Consistent color handling across backends
    - Efficient batch operations for performance
    - Clean separation between game logic and rendering
    """
    
    def __init__(self, width: int, height: int, title: str = "Game"):
        """Initialize the rendering backend.
        
        Args:
            width (int): Screen width in logical units
            height (int): Screen height in logical units  
            title (str): Window/application title
        """
        self.width = width
        self.height = height
        self.title = title
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the rendering system.
        
        Returns:
            bool: True if initialization succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Clean up and shutdown the rendering system."""
        pass
    
    @abstractmethod
    def create_surface(self, width: int, height: int) -> Surface:
        """Create a new drawing surface.
        
        Args:
            width (int): Surface width in logical units
            height (int): Surface height in logical units
            
        Returns:
            Surface: New drawing surface
        """
        pass
    
    @abstractmethod
    def get_main_surface(self) -> Surface:
        """Get the main rendering surface.
        
        Returns:
            Surface: Main drawing surface
        """
        pass
    
    @abstractmethod
    def present(self) -> None:
        """Present the current frame to the display.
        
        This should be called once per frame after all drawing
        operations are complete.
        """
        pass
    
    @abstractmethod
    def clear(self, color: Optional[Color] = None) -> None:
        """Clear the main surface.
        
        Args:
            color (Color, optional): Clear color. Defaults to black.
        """
        pass
    
    @abstractmethod
    def is_window_closed(self) -> bool:
        """Check if the window should be closed.
        
        Returns:
            bool: True if window should close, False otherwise
        """
        pass
    
    @abstractmethod
    def set_font(self, font_path: str, flags: int = 0) -> bool:
        """Set the rendering font.
        
        Args:
            font_path (str): Path to font file
            flags (int): Font loading flags
            
        Returns:
            bool: True if font loaded successfully
        """
        pass
    
    @abstractmethod
    def load_image(self, image_path: str) -> Any:
        """Load an image for rendering.
        
        Args:
            image_path (str): Path to image file
            
        Returns:
            Any: Backend-specific image object
        """
        pass
    
    # Input handling (basic support)
    @abstractmethod
    def get_key_input(self) -> Dict[str, Any]:
        """Get current keyboard input state.
        
        Returns:
            Dict[str, Any]: Key input information
        """
        pass
    
    @abstractmethod
    def get_mouse_input(self) -> Dict[str, Any]:
        """Get current mouse input state.
        
        Returns:
            Dict[str, Any]: Mouse input information
        """
        pass
    
    # Performance and debugging
    def get_render_stats(self) -> Dict[str, Any]:
        """Get rendering performance statistics.
        
        Returns:
            Dict[str, Any]: Performance metrics
        """
        return {
            'backend_type': self.__class__.__name__,
            'width': self.width,
            'height': self.height,
            'initialized': self._initialized,
        }
    
    def supports_feature(self, feature: str) -> bool:
        """Check if backend supports a specific feature.
        
        Args:
            feature (str): Feature name to check
            
        Returns:
            bool: True if feature is supported
        """
        # Default implementation - subclasses should override
        return False
