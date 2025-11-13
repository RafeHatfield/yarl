"""Input/Output abstraction layer for the game.

This module provides abstractions for rendering and input handling,
allowing the game to be decoupled from specific rendering backends
(e.g., terminal/ASCII, sprites) and input sources (e.g., keyboard, bot).
"""

from .interfaces import Renderer, InputSource

__all__ = ["Renderer", "InputSource"]

