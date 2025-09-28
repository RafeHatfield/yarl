"""Libtcod rendering backend implementation.

This module provides the LibtcodBackend class that implements the
RenderBackend interface using the libtcod library. This maintains
full backward compatibility with the existing console-based rendering
while providing the abstraction needed for future GUI backends.
"""

from typing import Dict, Any, Optional, Tuple
import warnings
import tcod as libtcod
import tcod.libtcodpy as libtcodpy

from .backend import RenderBackend
from .surface import Surface, Rect
from .color import Color


class LibtcodSurface(Surface):
    """Libtcod implementation of the Surface interface.
    
    This class wraps libtcod console operations to provide the
    Surface interface, enabling resolution-independent drawing
    operations while maintaining full compatibility with existing
    libtcod-based code.
    """
    
    def __init__(self, width: int, height: int, console=None):
        """Initialize the libtcod surface.
        
        Args:
            width (int): Surface width
            height (int): Surface height
            console: Existing libtcod console, or None to create new
        """
        super().__init__(width, height)
        
        if console is None:
            self._console = libtcod.console_new(width, height)
        else:
            self._console = console
        
        self._default_fg = Color(255, 255, 255)
        self._default_bg = Color(0, 0, 0)
    
    @property
    def console(self):
        """Get the underlying libtcod console."""
        return self._console
    
    def clear(self, color: Optional[Color] = None) -> None:
        """Clear the surface.
        
        Args:
            color (Color, optional): Clear color, defaults to black
        """
        if color is None:
            color = Color(0, 0, 0)
        
        libtcod.console_set_default_background(self._console, color.to_tuple())
        libtcod.console_clear(self._console)
    
    def set_char(self, x: int, y: int, char: str,
                 fg_color: Optional[Color] = None,
                 bg_color: Optional[Color] = None) -> None:
        """Set character at position.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            char (str): Character to draw
            fg_color (Color, optional): Foreground color
            bg_color (Color, optional): Background color
        """
        if (x < 0 or x >= self.width or y < 0 or y >= self.height or
            self._is_clipped(x, y)):
            return
        
        if fg_color is not None:
            libtcod.console_set_char_foreground(self._console, x, y, fg_color.to_tuple())
        
        if bg_color is not None:
            libtcod.console_set_char_background(self._console, x, y, bg_color.to_tuple())
        
        if char:
            libtcod.console_set_char(self._console, x, y, ord(char[0]))
    
    def get_char(self, x: int, y: int) -> str:
        """Get character at position.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            
        Returns:
            str: Character at position
        """
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return ' '
        
        char_code = libtcod.console_get_char(self._console, x, y)
        return chr(char_code) if char_code > 0 else ' '
    
    def set_bg_color(self, x: int, y: int, color: Color) -> None:
        """Set background color at position.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            color (Color): Background color
        """
        if (x < 0 or x >= self.width or y < 0 or y >= self.height or
            self._is_clipped(x, y)):
            return
        
        libtcod.console_set_char_background(self._console, x, y, color.to_tuple())
    
    def set_fg_color(self, x: int, y: int, color: Color) -> None:
        """Set foreground color at position.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            color (Color): Foreground color
        """
        if (x < 0 or x >= self.width or y < 0 or y >= self.height or
            self._is_clipped(x, y)):
            return
        
        libtcod.console_set_char_foreground(self._console, x, y, color.to_tuple())
    
    def print_string(self, x: int, y: int, text: str,
                    fg_color: Optional[Color] = None,
                    bg_color: Optional[Color] = None) -> None:
        """Print string at position.
        
        Args:
            x (int): Starting X coordinate
            y (int): Y coordinate
            text (str): Text to print
            fg_color (Color, optional): Foreground color
            bg_color (Color, optional): Background color
        """
        if fg_color is not None:
            libtcod.console_set_default_foreground(self._console, fg_color.to_tuple())
        
        if bg_color is not None:
            libtcod.console_set_default_background(self._console, bg_color.to_tuple())
        
        libtcod.console_print_ex(
            self._console, x, y, libtcod.BKGND_SET, libtcod.LEFT, text
        )
    
    def blit(self, source: 'LibtcodSurface', dest_x: int, dest_y: int,
             source_rect: Optional[Rect] = None,
             alpha: float = 1.0) -> None:
        """Copy from another surface.
        
        Args:
            source (LibtcodSurface): Source surface
            dest_x (int): Destination X coordinate
            dest_y (int): Destination Y coordinate
            source_rect (Rect, optional): Source rectangle, None for entire surface
            alpha (float): Alpha blending factor (0.0-1.0)
        """
        if source_rect is None:
            source_rect = Rect(0, 0, source.width, source.height)
        
        libtcod.console_blit(
            source.console,
            source_rect.x, source_rect.y,
            source_rect.width, source_rect.height,
            self._console,
            dest_x, dest_y,
            alpha, alpha
        )


class LibtcodBackend(RenderBackend):
    """Libtcod implementation of the RenderBackend interface.
    
    This backend provides console-based rendering using the libtcod
    library, maintaining full backward compatibility with existing
    code while providing the abstraction layer needed for future
    GUI implementations.
    
    Features:
    - Full libtcod console compatibility
    - Custom font support
    - Image loading and display
    - Keyboard and mouse input
    - Performance optimizations
    """
    
    def __init__(self, width: int, height: int, title: str = "Game"):
        """Initialize the libtcod backend.
        
        Args:
            width (int): Screen width in characters
            height (int): Screen height in characters
            title (str): Window title
        """
        super().__init__(width, height, title)
        self._main_surface: Optional[LibtcodSurface] = None
        self._surfaces: Dict[str, LibtcodSurface] = {}
        self._font_loaded = False
        
        # Performance tracking
        self._frame_count = 0
        self._render_stats = {
            'frames_rendered': 0,
            'surfaces_created': 0,
            'blits_performed': 0,
        }
    
    def initialize(self) -> bool:
        """Initialize the libtcod rendering system.
        
        Returns:
            bool: True if initialization succeeded
        """
        try:
            # Initialize the root console
            libtcod.console_init_root(
                self.width, self.height, self.title, False
            )
            
            # Create main surface
            self._main_surface = LibtcodSurface(
                self.width, self.height, console=0  # Root console
            )
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Failed to initialize libtcod backend: {e}")
            return False
    
    def shutdown(self) -> None:
        """Clean up and shutdown the rendering system."""
        self._surfaces.clear()
        self._main_surface = None
        self._initialized = False
    
    def create_surface(self, width: int, height: int) -> LibtcodSurface:
        """Create a new drawing surface.
        
        Args:
            width (int): Surface width
            height (int): Surface height
            
        Returns:
            LibtcodSurface: New drawing surface
        """
        surface = LibtcodSurface(width, height)
        self._render_stats['surfaces_created'] += 1
        return surface
    
    def get_main_surface(self) -> LibtcodSurface:
        """Get the main rendering surface.
        
        Returns:
            LibtcodSurface: Main drawing surface
        """
        if self._main_surface is None:
            raise RuntimeError("Backend not initialized")
        return self._main_surface
    
    def present(self) -> None:
        """Present the current frame to the display."""
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore", 
                    category=DeprecationWarning,
                    message="This function is not supported if contexts are being used"
                )
                libtcod.console_flush()
            
            self._frame_count += 1
            self._render_stats['frames_rendered'] += 1
            
        except RuntimeError:
            # Handle case where no console context exists (e.g., during testing)
            pass
    
    def clear(self, color: Optional[Color] = None) -> None:
        """Clear the main surface.
        
        Args:
            color (Color, optional): Clear color. Defaults to black.
        """
        if self._main_surface:
            self._main_surface.clear(color)
    
    def is_window_closed(self) -> bool:
        """Check if the window should be closed.
        
        Returns:
            bool: True if window should close
        """
        return libtcod.console_is_window_closed()
    
    def set_font(self, font_path: str, flags: int = 0) -> bool:
        """Set the rendering font.
        
        Args:
            font_path (str): Path to font file
            flags (int): Font loading flags
            
        Returns:
            bool: True if font loaded successfully
        """
        try:
            # Default flags for libtcod font loading
            if flags == 0:
                flags = libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD
            
            libtcod.console_set_custom_font(font_path, flags)
            self._font_loaded = True
            return True
            
        except Exception as e:
            print(f"Failed to load font {font_path}: {e}")
            return False
    
    def load_image(self, image_path: str) -> Any:
        """Load an image for rendering.
        
        Args:
            image_path (str): Path to image file
            
        Returns:
            Any: Libtcod image object
        """
        try:
            return libtcod.image_load(image_path)
        except Exception as e:
            print(f"Failed to load image {image_path}: {e}")
            return None
    
    def get_key_input(self) -> Dict[str, Any]:
        """Get current keyboard input state.
        
        Returns:
            Dict[str, Any]: Key input information
        """
        key = libtcod.Key()
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS, key, None)
        
        return {
            'key': key,
            'vk': key.vk,
            'c': key.c,
            'pressed': key.pressed,
            'lalt': key.lalt,
            'lctrl': key.lctrl,
            'ralt': key.ralt,
            'rctrl': key.rctrl,
            'shift': key.shift,
        }
    
    def get_mouse_input(self) -> Dict[str, Any]:
        """Get current mouse input state.
        
        Returns:
            Dict[str, Any]: Mouse input information
        """
        mouse = libtcod.Mouse()
        libtcod.sys_check_for_event(libtcod.EVENT_MOUSE, None, mouse)
        
        return {
            'mouse': mouse,
            'x': mouse.x,
            'y': mouse.y,
            'dx': mouse.dx,
            'dy': mouse.dy,
            'cx': mouse.cx,
            'cy': mouse.cy,
            'dcx': mouse.dcx,
            'dcy': mouse.dcy,
            'lbutton': mouse.lbutton,
            'rbutton': mouse.rbutton,
            'mbutton': mouse.mbutton,
            'lbutton_pressed': mouse.lbutton_pressed,
            'rbutton_pressed': mouse.rbutton_pressed,
            'mbutton_pressed': mouse.mbutton_pressed,
            'wheel_up': mouse.wheel_up,
            'wheel_down': mouse.wheel_down,
        }
    
    def get_render_stats(self) -> Dict[str, Any]:
        """Get rendering performance statistics.
        
        Returns:
            Dict[str, Any]: Performance metrics
        """
        stats = super().get_render_stats()
        stats.update(self._render_stats)
        stats.update({
            'frame_count': self._frame_count,
            'font_loaded': self._font_loaded,
            'active_surfaces': len(self._surfaces),
        })
        return stats
    
    def supports_feature(self, feature: str) -> bool:
        """Check if backend supports a specific feature.
        
        Args:
            feature (str): Feature name to check
            
        Returns:
            bool: True if feature is supported
        """
        supported_features = {
            'console_rendering',
            'custom_fonts',
            'image_loading',
            'keyboard_input',
            'mouse_input',
            'color_blending',
            'surface_blitting',
        }
        return feature in supported_features
