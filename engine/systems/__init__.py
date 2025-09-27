"""Game systems module.

This module contains concrete implementations of game systems
that inherit from the base System class.
"""

from .render_system import RenderSystem
from .input_system import InputSystem

__all__ = ["RenderSystem", "InputSystem"]
