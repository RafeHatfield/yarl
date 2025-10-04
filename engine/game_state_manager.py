"""Game state management for the engine.

This module provides centralized game state management that bridges
the gap between the new engine architecture and the existing game systems.
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass, field

from game_states import GameStates


@dataclass
class GameState:
    """Container for all game state data.

    This class holds all the game state information that systems need
    to access, providing a centralized and type-safe way to manage
    game data across the engine.

    Attributes:
        player: The player entity
        entities: List of all entities in the game
        game_map: The current game map
        message_log: Game message log
        current_state: Current game state (GameStates enum)
        mouse: Mouse input object
        key: Keyboard input object
        fov_map: Field of view map
        fov_recompute: Whether FOV needs recomputation
        targeting_item: Item being targeted (for spells)
        previous_game_state: Previous game state for state transitions
        constants: Game configuration constants
        extra_data: Dictionary for additional state data
    """

    # Core game objects
    player: Any = None
    entities: list = field(default_factory=list)
    game_map: Any = None
    message_log: Any = None

    # Game state management
    current_state: GameStates = GameStates.PLAYERS_TURN
    previous_game_state: GameStates = GameStates.PLAYERS_TURN

    # Input objects
    mouse: Any = None
    key: Any = None

    # Rendering state
    fov_map: Any = None
    fov_recompute: bool = True
    camera: Any = None  # Camera for viewport scrolling

    # Interaction state
    targeting_item: Any = None

    # Configuration
    constants: Dict[str, Any] = field(default_factory=dict)

    # Extensible data storage
    extra_data: Dict[str, Any] = field(default_factory=dict)


class GameStateManager:
    """Manages game state for the engine systems.

    The GameStateManager provides a centralized way to manage and access
    game state data. It acts as a bridge between the new engine architecture
    and the existing game systems.

    Attributes:
        _state (GameState): Current game state data
        _state_change_callbacks: List of callbacks for state changes
    """

    def __init__(self):
        """Initialize the GameStateManager."""
        self._state = GameState()
        self._state_change_callbacks = []

    @property
    def state(self) -> GameState:
        """Get the current game state.

        Returns:
            GameState: The current game state data
        """
        return self._state

    def update_state(self, **kwargs) -> None:
        """Update game state with new values.

        Args:
            **kwargs: Key-value pairs to update in the game state
        """
        for key, value in kwargs.items():
            if hasattr(self._state, key):
                setattr(self._state, key, value)
            else:
                # Store unknown keys in extra_data
                self._state.extra_data[key] = value

    def set_game_state(self, new_state: GameStates) -> None:
        """Set the current game state.

        Args:
            new_state (GameStates): The new game state
        """
        if new_state != self._state.current_state:
            self._state.previous_game_state = self._state.current_state
            self._state.current_state = new_state
            self._notify_state_change(new_state)

    def get_state_data(self) -> Dict[str, Any]:
        """Get game state as a dictionary for system access.

        Returns:
            Dict[str, Any]: Dictionary containing all game state data
        """
        return {
            "player": self._state.player,
            "entities": self._state.entities,
            "game_map": self._state.game_map,
            "message_log": self._state.message_log,
            "current_state": self._state.current_state,
            "previous_state": self._state.previous_game_state,
            "mouse": self._state.mouse,
            "key": self._state.key,
            "fov_map": self._state.fov_map,
            "fov_recompute": self._state.fov_recompute,
            "camera": self._state.camera,
            "targeting_item": self._state.targeting_item,
            "constants": self._state.constants,
            **self._state.extra_data,
        }

    def initialize_game(
        self, player, entities, game_map, message_log, game_state, constants
    ) -> None:
        """Initialize the game state with starting values.

        Args:
            player: The player entity
            entities: List of all entities
            game_map: The game map
            message_log: Message log
            game_state: Initial game state
            constants: Game configuration constants
        """
        self._state.player = player
        self._state.entities = entities
        self._state.game_map = game_map
        self._state.message_log = message_log
        self._state.current_state = game_state
        self._state.constants = constants

    def set_input_objects(self, key, mouse) -> None:
        """Set the current input objects.

        Args:
            key: Keyboard input object
            mouse: Mouse input object
        """
        self._state.key = key
        self._state.mouse = mouse

    def set_fov_data(self, fov_map, fov_recompute: bool = True) -> None:
        """Set field of view data.

        Args:
            fov_map: The FOV map object
            fov_recompute (bool): Whether FOV needs recomputation
        """
        self._state.fov_map = fov_map
        self._state.fov_recompute = fov_recompute

    def request_fov_recompute(self) -> None:
        """Request that FOV be recomputed on next update."""
        self._state.fov_recompute = True

    def set_targeting_item(self, item) -> None:
        """Set the item being targeted.

        Args:
            item: The item being targeted, or None to clear
        """
        self._state.targeting_item = item

    def add_state_change_callback(self, callback) -> None:
        """Add a callback for state changes.

        Args:
            callback: Function to call when state changes
        """
        self._state_change_callbacks.append(callback)

    def remove_state_change_callback(self, callback) -> None:
        """Remove a state change callback.

        Args:
            callback: Function to remove from callbacks
        """
        if callback in self._state_change_callbacks:
            self._state_change_callbacks.remove(callback)

    def _notify_state_change(self, new_state: GameStates) -> None:
        """Notify all callbacks of state change.

        Args:
            new_state (GameStates): The new game state
        """
        for callback in self._state_change_callbacks:
            try:
                callback(new_state)
            except Exception as e:
                # Log error but don't crash the game
                import logging

                logging.error(f"Error in state change callback: {e}")

    def reset(self) -> None:
        """Reset the game state to initial values."""
        self._state = GameState()

    def get_extra_data(self, key: str, default: Any = None) -> Any:
        """Get extra data by key.

        Args:
            key (str): The key to look up
            default: Default value if key not found

        Returns:
            Any: The value associated with the key, or default
        """
        return self._state.extra_data.get(key, default)

    def set_extra_data(self, key: str, value: Any) -> None:
        """Set extra data by key.

        Args:
            key (str): The key to set
            value: The value to store
        """
        self._state.extra_data[key] = value
