"""Resolution-independent drawing surface abstraction.

This module provides the Surface class and related utilities for
resolution-independent rendering operations. Surfaces abstract away
the underlying rendering implementation and provide a consistent
drawing interface across different backends.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Any, Union
from dataclasses import dataclass
from .color import Color


@dataclass
class Rect:
    """Rectangle representation for drawing operations.
    
    Attributes:
        x (int): X coordinate
        y (int): Y coordinate
        width (int): Rectangle width
        height (int): Rectangle height
    """
    x: int
    y: int
    width: int
    height: int
    
    @property
    def left(self) -> int:
        """Left edge X coordinate."""
        return self.x
    
    @property
    def right(self) -> int:
        """Right edge X coordinate."""
        return self.x + self.width
    
    @property
    def top(self) -> int:
        """Top edge Y coordinate."""
        return self.y
    
    @property
    def bottom(self) -> int:
        """Bottom edge Y coordinate."""
        return self.y + self.height
    
    @property
    def center(self) -> Tuple[int, int]:
        """Center point coordinates."""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def contains(self, x: int, y: int) -> bool:
        """Check if point is inside rectangle.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            
        Returns:
            bool: True if point is inside rectangle
        """
        return (self.x <= x < self.x + self.width and 
                self.y <= y < self.y + self.height)
    
    def intersects(self, other: 'Rect') -> bool:
        """Check if this rectangle intersects with another.
        
        Args:
            other (Rect): Other rectangle
            
        Returns:
            bool: True if rectangles intersect
        """
        return not (self.right <= other.left or 
                   other.right <= self.left or
                   self.bottom <= other.top or 
                   other.bottom <= self.top)


class Surface(ABC):
    """Abstract drawing surface for resolution-independent rendering.
    
    This class provides a consistent interface for drawing operations
    that can be implemented by different rendering backends. It abstracts
    away the underlying rendering technology while providing all the
    drawing primitives needed by the game.
    
    Key Features:
    - Resolution-independent coordinate system
    - Efficient batch drawing operations
    - Clipping and viewport support
    - Backend-agnostic drawing primitives
    """
    
    def __init__(self, width: int, height: int):
        """Initialize the surface.
        
        Args:
            width (int): Surface width in logical units
            height (int): Surface height in logical units
        """
        self.width = width
        self.height = height
        self._clip_rect: Optional[Rect] = None
    
    @property
    def size(self) -> Tuple[int, int]:
        """Get surface dimensions.
        
        Returns:
            Tuple[int, int]: Width and height
        """
        return (self.width, self.height)
    
    @property
    def rect(self) -> Rect:
        """Get surface rectangle.
        
        Returns:
            Rect: Rectangle covering entire surface
        """
        return Rect(0, 0, self.width, self.height)
    
    def set_clip_rect(self, rect: Optional[Rect]) -> None:
        """Set clipping rectangle for drawing operations.
        
        Args:
            rect (Rect, optional): Clipping rectangle, None to disable
        """
        self._clip_rect = rect
    
    def get_clip_rect(self) -> Optional[Rect]:
        """Get current clipping rectangle.
        
        Returns:
            Rect: Current clipping rectangle, None if disabled
        """
        return self._clip_rect
    
    def _is_clipped(self, x: int, y: int) -> bool:
        """Check if coordinates are clipped.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            
        Returns:
            bool: True if coordinates are clipped
        """
        if self._clip_rect is None:
            return False
        return not self._clip_rect.contains(x, y)
    
    # Drawing primitives
    @abstractmethod
    def clear(self, color: Optional[Color] = None) -> None:
        """Clear the surface.
        
        Args:
            color (Color, optional): Clear color, defaults to black
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def get_char(self, x: int, y: int) -> str:
        """Get character at position.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            
        Returns:
            str: Character at position
        """
        pass
    
    @abstractmethod
    def set_bg_color(self, x: int, y: int, color: Color) -> None:
        """Set background color at position.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            color (Color): Background color
        """
        pass
    
    @abstractmethod
    def set_fg_color(self, x: int, y: int, color: Color) -> None:
        """Set foreground color at position.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            color (Color): Foreground color
        """
        pass
    
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
        for i, char in enumerate(text):
            if x + i >= self.width:
                break
            self.set_char(x + i, y, char, fg_color, bg_color)
    
    def fill_rect(self, rect: Rect, char: str = ' ',
                  fg_color: Optional[Color] = None,
                  bg_color: Optional[Color] = None) -> None:
        """Fill rectangle with character and colors.
        
        Args:
            rect (Rect): Rectangle to fill
            char (str): Character to fill with
            fg_color (Color, optional): Foreground color
            bg_color (Color, optional): Background color
        """
        for y in range(rect.y, rect.y + rect.height):
            for x in range(rect.x, rect.x + rect.width):
                if (0 <= x < self.width and 0 <= y < self.height and
                    not self._is_clipped(x, y)):
                    self.set_char(x, y, char, fg_color, bg_color)
    
    def draw_border(self, rect: Rect, 
                   fg_color: Optional[Color] = None,
                   bg_color: Optional[Color] = None,
                   border_chars: Optional[str] = None) -> None:
        """Draw border around rectangle.
        
        Args:
            rect (Rect): Rectangle to border
            fg_color (Color, optional): Foreground color
            bg_color (Color, optional): Background color
            border_chars (str, optional): Border characters (8 chars: ┌─┐│┘─└│)
        """
        if border_chars is None:
            border_chars = "┌─┐│┘─└│"  # Default box drawing characters
        
        if len(border_chars) != 8:
            border_chars = "+-+|+-+|"  # Fallback ASCII characters
        
        # Top border
        self.set_char(rect.x, rect.y, border_chars[0], fg_color, bg_color)
        for x in range(rect.x + 1, rect.x + rect.width - 1):
            self.set_char(x, rect.y, border_chars[1], fg_color, bg_color)
        self.set_char(rect.x + rect.width - 1, rect.y, border_chars[2], fg_color, bg_color)
        
        # Side borders
        for y in range(rect.y + 1, rect.y + rect.height - 1):
            self.set_char(rect.x, y, border_chars[7], fg_color, bg_color)
            self.set_char(rect.x + rect.width - 1, y, border_chars[3], fg_color, bg_color)
        
        # Bottom border
        self.set_char(rect.x, rect.y + rect.height - 1, border_chars[6], fg_color, bg_color)
        for x in range(rect.x + 1, rect.x + rect.width - 1):
            self.set_char(x, rect.y + rect.height - 1, border_chars[5], fg_color, bg_color)
        self.set_char(rect.x + rect.width - 1, rect.y + rect.height - 1, border_chars[4], fg_color, bg_color)
    
    @abstractmethod
    def blit(self, source: 'Surface', dest_x: int, dest_y: int,
             source_rect: Optional[Rect] = None,
             alpha: float = 1.0) -> None:
        """Copy from another surface.
        
        Args:
            source (Surface): Source surface
            dest_x (int): Destination X coordinate
            dest_y (int): Destination Y coordinate
            source_rect (Rect, optional): Source rectangle, None for entire surface
            alpha (float): Alpha blending factor (0.0-1.0)
        """
        pass
