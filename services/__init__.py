"""Game services module.

This module contains service classes that encapsulate game logic
in a way that can be called from multiple input sources (keyboard, mouse, etc.)
without duplicating code.

Services provide a single source of truth for game mechanics.
"""

from .movement_service import MovementService
from .pickup_service import PickupService

__all__ = [
    'MovementService',
    'PickupService',
]

