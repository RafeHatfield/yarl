"""Core game engine class for managing systems and game state.

This module contains the main GameEngine class which coordinates all game systems,
manages the game loop, and provides a clean interface for game initialization
and execution.
"""

import time
from typing import Dict, List, Optional, Type
from collections import OrderedDict

from .system import System
from .game_state_manager import GameStateManager


class GameEngine:
    """Main game engine that coordinates all game systems.

    The GameEngine is responsible for:
    - Managing and updating all game systems
    - Coordinating the main game loop
    - Providing system registration and lifecycle management
    - Maintaining consistent frame timing

    Attributes:
        systems (OrderedDict): Registered systems ordered by priority
        running (bool): Whether the engine is currently running
        target_fps (int): Target frames per second
        delta_time (float): Time since last frame in seconds
    """

    def __init__(self, target_fps: int = 60):
        """Initialize the game engine.

        Args:
            target_fps (int, optional): Target frames per second. Defaults to 60.
        """
        self.systems: OrderedDict[str, System] = OrderedDict()
        self.running = False
        self.target_fps = target_fps
        self.delta_time = 0.0
        self._last_time = 0.0
        self._frame_time = 1.0 / target_fps if target_fps > 0 else 0.0
        self.state_manager = GameStateManager()

    def register_system(self, system: System) -> None:
        """Register a system with the engine.

        Systems are automatically sorted by priority (lower numbers first).
        The system's initialize method is called with a reference to this engine.

        Args:
            system (System): The system instance to register

        Raises:
            ValueError: If a system with the same name is already registered
        """
        if system.name in self.systems:
            raise ValueError(f"System '{system.name}' is already registered")

        # Initialize the system with engine reference
        system.initialize(self)

        # Insert system in priority order
        self.systems[system.name] = system
        self._sort_systems()

    def unregister_system(self, name: str) -> Optional[System]:
        """Unregister a system from the engine.

        The system's cleanup method is called before removal.

        Args:
            name (str): Name of the system to remove

        Returns:
            System or None: The removed system, or None if not found
        """
        if name not in self.systems:
            return None

        system = self.systems[name]
        system.cleanup()
        del self.systems[name]
        return system

    def get_system(self, name: str) -> Optional[System]:
        """Get a registered system by name.

        Args:
            name (str): Name of the system to retrieve

        Returns:
            System or None: The system instance, or None if not found
        """
        return self.systems.get(name)

    def get_systems_by_type(self, system_type: Type[System]) -> List[System]:
        """Get all registered systems of a specific type.

        Args:
            system_type (Type[System]): The system class type to search for

        Returns:
            List[System]: List of systems matching the type
        """
        return [
            system
            for system in self.systems.values()
            if isinstance(system, system_type)
        ]

    def start(self) -> None:
        """Start the game engine.

        Initializes timing and sets the running flag to True.
        """
        self.running = True
        self._last_time = time.time()

    def stop(self) -> None:
        """Stop the game engine.

        Sets the running flag to False and cleans up all systems.
        """
        self.running = False
        for system in self.systems.values():
            system.cleanup()

    def update(self) -> None:
        """Update all enabled systems for one frame.

        Calculates delta time and calls update on all enabled systems
        in priority order.
        """
        current_time = time.time()
        self.delta_time = current_time - self._last_time
        self._last_time = current_time

        # Update all enabled systems in priority order
        for system in self.systems.values():
            if system.enabled:
                system.update(self.delta_time)

    def run(self) -> None:
        """Run the main game loop.

        Starts the engine and runs the update loop until stopped.
        Maintains target FPS by sleeping between frames if necessary.
        """
        self.start()

        try:
            while self.running:
                frame_start = time.time()

                self.update()

                # Maintain target FPS
                if self._frame_time > 0:
                    frame_duration = time.time() - frame_start
                    sleep_time = self._frame_time - frame_duration
                    if sleep_time > 0:
                        time.sleep(sleep_time)

        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def _sort_systems(self) -> None:
        """Sort systems by priority (lower numbers first)."""
        self.systems = OrderedDict(
            sorted(self.systems.items(), key=lambda x: x[1].priority)
        )

    @property
    def system_count(self) -> int:
        """Get the number of registered systems."""
        return len(self.systems)

    @property
    def enabled_system_count(self) -> int:
        """Get the number of enabled systems."""
        return sum(1 for system in self.systems.values() if system.enabled)

    def get_system_info(self) -> Dict[str, Dict]:
        """Get information about all registered systems.

        Returns:
            Dict[str, Dict]: Dictionary mapping system names to their info
        """
        return {
            name: {
                "enabled": system.enabled,
                "priority": system.priority,
                "type": type(system).__name__,
            }
            for name, system in self.systems.items()
        }
