"""Rendering abstraction layer for multiple backend support.

This package provides a clean abstraction layer that decouples game logic
from specific rendering implementations, enabling support for multiple
rendering backends (console, GUI, web, etc.) while maintaining backward
compatibility.

Key Components:
- RenderBackend: Abstract interface for rendering operations
- Surface: Resolution-independent drawing surface
- LibtcodBackend: Console-based rendering implementation
- Color: Cross-platform color representation
"""

from .backend import RenderBackend
from .surface import Surface, Rect
from .color import Color, Colors
from .libtcod_backend import LibtcodBackend

__all__ = [
    'RenderBackend',
    'Surface', 
    'Rect',
    'Color',
    'Colors',
    'LibtcodBackend',
]
