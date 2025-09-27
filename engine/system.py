"""Base system class for the game engine.

This module defines the abstract base class that all game systems inherit from.
Systems are responsible for updating specific aspects of the game world.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class System(ABC):
    """Abstract base class for all game systems.

    Systems are responsible for updating specific aspects of the game world
    such as rendering, input handling, AI, physics, etc. Each system operates
    on entities with specific components.

    Attributes:
        name (str): Unique name identifier for this system
        enabled (bool): Whether this system is currently active
        priority (int): Update priority (lower numbers update first)
    """

    def __init__(self, name: str, priority: int = 100):
        """Initialize the system.

        Args:
            name (str): Unique name for this system
            priority (int, optional): Update priority. Defaults to 100.
        """
        self.name = name
        self.enabled = True
        self.priority = priority
        self._engine = None

    def initialize(self, engine) -> None:
        """Initialize the system with a reference to the game engine.

        Called once when the system is registered with the engine.
        Override this method to perform system-specific initialization.

        Args:
            engine: Reference to the main GameEngine instance
        """
        self._engine = engine

    @abstractmethod
    def update(self, dt: float) -> None:
        """Update the system for one frame.

        This method is called every frame and should contain the main
        logic for this system. Override this method in derived classes.

        Args:
            dt (float): Delta time since last update in seconds
        """
        pass

    def cleanup(self) -> None:
        """Clean up system resources.

        Called when the system is being shut down or removed.
        Override this method to perform cleanup operations.
        """
        pass

    def enable(self) -> None:
        """Enable this system for updates."""
        self.enabled = True

    def disable(self) -> None:
        """Disable this system from updates."""
        self.enabled = False

    @property
    def engine(self):
        """Get reference to the game engine."""
        return self._engine
