"""Cross-platform color representation and utilities.

This module provides a unified color system that works across different
rendering backends, with automatic conversion between color formats
and support for common color operations.
"""

from typing import Union, Tuple, NamedTuple
import colorsys


class Color(NamedTuple):
    """Immutable color representation with RGB values.
    
    This class provides a consistent color interface across all rendering
    backends, with automatic conversion to backend-specific formats and
    support for common color operations.
    
    Attributes:
        r (int): Red component (0-255)
        g (int): Green component (0-255)  
        b (int): Blue component (0-255)
    """
    r: int
    g: int
    b: int
    
    @classmethod
    def create(cls, r: int, g: int, b: int) -> 'Color':
        """Create a new Color with clamped RGB values.
        
        Args:
            r (int): Red component (0-255)
            g (int): Green component (0-255)
            b (int): Blue component (0-255)
        """
        return cls(max(0, min(255, int(r))),
                  max(0, min(255, int(g))),
                  max(0, min(255, int(b))))
    
    @classmethod
    def from_tuple(cls, rgb: Tuple[int, int, int]) -> 'Color':
        """Create Color from RGB tuple.
        
        Args:
            rgb (Tuple[int, int, int]): RGB values
            
        Returns:
            Color: New color instance
        """
        return cls(rgb[0], rgb[1], rgb[2])
    
    @classmethod
    def from_hex(cls, hex_color: str) -> 'Color':
        """Create Color from hex string.
        
        Args:
            hex_color (str): Hex color string (e.g., "#FF0000" or "FF0000")
            
        Returns:
            Color: New color instance
        """
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            raise ValueError(f"Invalid hex color: {hex_color}")
        
        return cls(
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16)
        )
    
    @classmethod
    def from_hsv(cls, h: float, s: float, v: float) -> 'Color':
        """Create Color from HSV values.
        
        Args:
            h (float): Hue (0.0-1.0)
            s (float): Saturation (0.0-1.0)
            v (float): Value (0.0-1.0)
            
        Returns:
            Color: New color instance
        """
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return cls(int(r * 255), int(g * 255), int(b * 255))
    
    def to_tuple(self) -> Tuple[int, int, int]:
        """Convert to RGB tuple.
        
        Returns:
            Tuple[int, int, int]: RGB values
        """
        return (self.r, self.g, self.b)
    
    def to_hex(self) -> str:
        """Convert to hex string.
        
        Returns:
            str: Hex color string (e.g., "#FF0000")
        """
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"
    
    def to_hsv(self) -> Tuple[float, float, float]:
        """Convert to HSV values.
        
        Returns:
            Tuple[float, float, float]: HSV values (0.0-1.0)
        """
        return colorsys.rgb_to_hsv(self.r / 255.0, self.g / 255.0, self.b / 255.0)
    
    def lerp(self, other: 'Color', t: float) -> 'Color':
        """Linear interpolation between colors.
        
        Args:
            other (Color): Target color
            t (float): Interpolation factor (0.0-1.0)
            
        Returns:
            Color: Interpolated color
        """
        t = max(0.0, min(1.0, t))
        return Color(
            int(self.r + (other.r - self.r) * t),
            int(self.g + (other.g - self.g) * t),
            int(self.b + (other.b - self.b) * t)
        )
    
    def darken(self, factor: float) -> 'Color':
        """Create a darker version of this color.
        
        Args:
            factor (float): Darkening factor (0.0-1.0)
            
        Returns:
            Color: Darkened color
        """
        factor = max(0.0, min(1.0, 1.0 - factor))
        return Color(
            int(self.r * factor),
            int(self.g * factor),
            int(self.b * factor)
        )
    
    def lighten(self, factor: float) -> 'Color':
        """Create a lighter version of this color.
        
        Args:
            factor (float): Lightening factor (0.0-1.0)
            
        Returns:
            Color: Lightened color
        """
        factor = max(0.0, min(1.0, factor))
        return Color(
            int(self.r + (255 - self.r) * factor),
            int(self.g + (255 - self.g) * factor),
            int(self.b + (255 - self.b) * factor)
        )


# Common color constants
class Colors:
    """Common color constants for convenience."""
    
    BLACK = Color(0, 0, 0)
    WHITE = Color(255, 255, 255)
    RED = Color(255, 0, 0)
    GREEN = Color(0, 255, 0)
    BLUE = Color(0, 0, 255)
    YELLOW = Color(255, 255, 0)
    CYAN = Color(0, 255, 255)
    MAGENTA = Color(255, 0, 255)
    
    # Game-specific colors (matching current libtcod colors)
    DARK_WALL = Color(0, 0, 100)
    DARK_GROUND = Color(50, 50, 150)
    LIGHT_WALL = Color(130, 110, 50)
    LIGHT_GROUND = Color(200, 180, 50)
    
    # UI colors
    LIGHT_RED = Color(255, 114, 114)
    LIGHT_GREEN = Color(63, 255, 63)  # Matches the old libtcod.light_green
    LIGHT_BLUE = Color(114, 159, 255)
    DARK_RED = Color(191, 0, 0)
    DARK_GREEN = Color(0, 127, 0)
    DARK_BLUE = Color(0, 0, 127)
    
    # Text colors
    TEXT_DISABLED = Color(128, 128, 128)

# Define dependent colors after the class
Colors.TEXT_DEFAULT = Colors.WHITE
Colors.TEXT_HIGHLIGHT = Colors.YELLOW
Colors.TEXT_ERROR = Colors.LIGHT_RED
Colors.TEXT_SUCCESS = Colors.LIGHT_GREEN
