"""Compatibility layer for gradual migration to rendering abstraction.

This module provides compatibility functions and classes that allow
existing code to work with the new rendering abstraction while
maintaining backward compatibility. This enables incremental migration
without breaking existing functionality.
"""

from typing import Optional, Dict, Any, Tuple
import tcod as libtcod
import tcod.libtcodpy as libtcodpy

from .backend import RenderBackend
from .libtcod_backend import LibtcodBackend, LibtcodSurface
from .color import Color, Colors
from .surface import Surface


# Global backend instance for compatibility
_global_backend: Optional[RenderBackend] = None


def initialize_rendering_backend(width: int, height: int, title: str = "Game",
                               font_path: Optional[str] = None) -> RenderBackend:
    """Initialize the global rendering backend.
    
    This function sets up the rendering system and creates a global
    backend instance that can be used by compatibility functions.
    
    Args:
        width (int): Screen width
        height (int): Screen height
        title (str): Window title
        font_path (str, optional): Path to font file
        
    Returns:
        RenderBackend: Initialized backend instance
    """
    global _global_backend
    
    # For now, always use libtcod backend
    _global_backend = LibtcodBackend(width, height, title)
    
    # Set font if provided
    if font_path:
        _global_backend.set_font(font_path)
    
    # Initialize the backend
    if not _global_backend.initialize():
        raise RuntimeError("Failed to initialize rendering backend")
    
    return _global_backend


def get_rendering_backend() -> Optional[RenderBackend]:
    """Get the global rendering backend.
    
    Returns:
        RenderBackend: Global backend instance, None if not initialized
    """
    return _global_backend


def shutdown_rendering_backend() -> None:
    """Shutdown the global rendering backend."""
    global _global_backend
    if _global_backend:
        _global_backend.shutdown()
        _global_backend = None


# Compatibility functions for existing libtcod code
def create_console(width: int, height: int) -> LibtcodSurface:
    """Create a new console surface.
    
    This function provides backward compatibility with libtcod.console_new()
    while using the new Surface abstraction.
    
    Args:
        width (int): Console width
        height (int): Console height
        
    Returns:
        LibtcodSurface: New console surface
    """
    if _global_backend is None:
        raise RuntimeError("Rendering backend not initialized")
    
    return _global_backend.create_surface(width, height)


def get_main_console() -> LibtcodSurface:
    """Get the main console surface.
    
    Returns:
        LibtcodSurface: Main console surface
    """
    if _global_backend is None:
        raise RuntimeError("Rendering backend not initialized")
    
    return _global_backend.get_main_surface()


def console_flush() -> None:
    """Present the current frame (compatibility function).
    
    This replaces libtcod.console_flush() calls with the abstracted
    present() method.
    """
    if _global_backend:
        _global_backend.present()


def console_is_window_closed() -> bool:
    """Check if window should close (compatibility function).
    
    Returns:
        bool: True if window should close
    """
    if _global_backend is None:
        return True
    
    return _global_backend.is_window_closed()


# Color conversion utilities
def convert_libtcod_color(color) -> Color:
    """Convert libtcod color to Color object.
    
    Args:
        color: Libtcod color (tuple or libtcod.Color)
        
    Returns:
        Color: Converted color
    """
    if isinstance(color, tuple):
        return Color(color[0], color[1], color[2])
    elif hasattr(color, 'r') and hasattr(color, 'g') and hasattr(color, 'b'):
        return Color(color.r, color.g, color.b)
    else:
        # Fallback to white
        return Colors.WHITE


def get_legacy_color_mapping() -> Dict[str, Color]:
    """Get mapping of legacy color names to Color objects.
    
    This provides backward compatibility with hardcoded color references
    in the existing codebase.
    
    Returns:
        Dict[str, Color]: Color name to Color object mapping
    """
    return {
        # Basic colors
        'black': Colors.BLACK,
        'white': Colors.WHITE,
        'red': Colors.RED,
        'green': Colors.GREEN,
        'blue': Colors.BLUE,
        'yellow': Colors.YELLOW,
        'cyan': Colors.CYAN,
        'magenta': Colors.MAGENTA,
        
        # Game-specific colors
        'dark_wall': Colors.DARK_WALL,
        'dark_ground': Colors.DARK_GROUND,
        'light_wall': Colors.LIGHT_WALL,
        'light_ground': Colors.LIGHT_GROUND,
        
        # UI colors
        'light_red': Colors.LIGHT_RED,
        'light_green': Colors.LIGHT_GREEN,
        'light_blue': Colors.LIGHT_BLUE,
        'dark_red': Colors.DARK_RED,
        'dark_green': Colors.DARK_GREEN,
        'dark_blue': Colors.DARK_BLUE,
    }


class RenderingMigrationHelper:
    """Helper class for migrating existing rendering code.
    
    This class provides utilities and wrapper functions to help
    migrate existing libtcod-based rendering code to use the new
    abstraction layer without breaking functionality.
    """
    
    def __init__(self, backend: RenderBackend):
        """Initialize the migration helper.
        
        Args:
            backend (RenderBackend): Rendering backend to use
        """
        self.backend = backend
        self.color_mapping = get_legacy_color_mapping()
    
    def wrap_console(self, console) -> LibtcodSurface:
        """Wrap an existing libtcod console in a Surface.
        
        Args:
            console: Existing libtcod console
            
        Returns:
            LibtcodSurface: Wrapped surface
        """
        if isinstance(self.backend, LibtcodBackend):
            # Get console dimensions
            width = libtcod.console_get_width(console)
            height = libtcod.console_get_height(console)
            return LibtcodSurface(width, height, console)
        else:
            raise NotImplementedError("Console wrapping only supported for LibtcodBackend")
    
    def convert_render_call(self, function_name: str, *args, **kwargs) -> Any:
        """Convert legacy rendering function calls to abstracted equivalents.
        
        Args:
            function_name (str): Name of legacy function
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Any: Result of converted function call
        """
        # This could be expanded to handle more complex conversions
        conversion_map = {
            'console_flush': lambda: self.backend.present(),
            'console_is_window_closed': lambda: self.backend.is_window_closed(),
            'console_clear': lambda con: self.wrap_console(con).clear(),
        }
        
        if function_name in conversion_map:
            return conversion_map[function_name](*args, **kwargs)
        else:
            raise NotImplementedError(f"Conversion for {function_name} not implemented")
    
    def get_performance_info(self) -> Dict[str, Any]:
        """Get performance information for migration analysis.
        
        Returns:
            Dict[str, Any]: Performance metrics and migration status
        """
        return {
            'backend_type': type(self.backend).__name__,
            'backend_stats': self.backend.get_render_stats(),
            'migration_status': 'in_progress',
            'compatibility_mode': True,
        }
