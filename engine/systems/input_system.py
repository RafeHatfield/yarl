"""Input system for handling keyboard and mouse events.

This module contains the InputSystem which processes player input and translates
it into game actions based on the current game state. It provides a clean
abstraction layer for input handling that can be extended for different
input methods or key mappings.
"""

from typing import Dict, Any, Optional, Callable
import tcod.libtcodpy as libtcod

from ..system import System
from input_handlers import (
    handle_keys,
    handle_mouse,
    handle_main_menu,
    handle_targeting_keys,
    handle_inventory_keys,
    handle_player_turn_keys,
    handle_player_dead_keys,
    handle_level_up_menu,
    handle_character_screen,
)
from game_states import GameStates


class InputSystem(System):
    """System responsible for processing input and generating actions.

    The InputSystem handles all keyboard and mouse input, routing it through
    appropriate handlers based on the current game state. It provides a
    centralized place for input processing and can be extended to support
    different input methods, key remapping, and input recording/playback.

    Attributes:
        key_handlers (Dict): Mapping of game states to key handler functions
        mouse_handlers (Dict): Mapping of game states to mouse handler functions
        action_callbacks (Dict): Callbacks for specific actions
        input_buffer (list): Buffer for input recording/playback
        recording (bool): Whether input is being recorded
    """

    def __init__(self, priority: int = 10):
        """Initialize the InputSystem.

        Args:
            priority (int, optional): System update priority. Defaults to 10 (early).
        """
        super().__init__("input", priority)

        # Handler mappings for different game states
        self.key_handlers = {
            GameStates.PLAYERS_TURN: handle_player_turn_keys,
            GameStates.PLAYER_DEAD: handle_player_dead_keys,
            GameStates.TARGETING: handle_targeting_keys,
            GameStates.SHOW_INVENTORY: handle_inventory_keys,
            GameStates.DROP_INVENTORY: handle_inventory_keys,
            GameStates.LEVEL_UP: handle_level_up_menu,
            GameStates.CHARACTER_SCREEN: handle_character_screen,
        }

        # Mouse handlers (could be state-specific in the future)
        self.mouse_handlers = {
            # For now, use the same handler for all states
            "default": handle_mouse,
        }

        # Action callbacks for extensibility
        self.action_callbacks: Dict[str, Callable] = {}

        # Input recording/playback support
        self.input_buffer = []
        self.recording = False
        self.playback_index = 0
        self.playing_back = False

        # Current input objects
        self.current_key = None
        self.current_mouse = None
        self.current_actions = {}
        self.current_mouse_actions = {}

    def initialize(self, engine) -> None:
        """Initialize the input system with engine reference.

        Args:
            engine: Reference to the main GameEngine instance
        """
        super().initialize(engine)

    def update(self, dt: float) -> None:
        """Update the input system for one frame.

        Processes current input state and generates actions based on
        the current game state.

        Args:
            dt (float): Delta time since last update in seconds
        """
        if not self.engine or not hasattr(self.engine, "state_manager"):
            return

        state_manager = self.engine.state_manager
        if not state_manager:
            return

        game_state = state_manager.state

        # Get current input objects
        self.current_key = game_state.key
        self.current_mouse = game_state.mouse

        if not self.current_key:
            return

        # Handle input playback
        if self.playing_back:
            self._process_playback()
            return

        # Process keyboard input
        self.current_actions = self._process_keyboard_input(game_state.current_state)

        # Process mouse input
        self.current_mouse_actions = self._process_mouse_input(game_state.current_state)

        # Record input if recording is enabled
        if self.recording:
            self._record_input()

        # Execute action callbacks
        self._execute_action_callbacks()

        # Store actions in state manager for other systems to use
        state_manager.set_extra_data("keyboard_actions", self.current_actions)
        state_manager.set_extra_data("mouse_actions", self.current_mouse_actions)

    def _process_keyboard_input(self, current_state: GameStates) -> Dict[str, Any]:
        """Process keyboard input for the current game state.

        Args:
            current_state (GameStates): Current game state

        Returns:
            Dict[str, Any]: Dictionary of actions generated from input
        """
        handler = self.key_handlers.get(current_state)
        if handler and self.current_key:
            return handler(self.current_key)
        return {}

    def _process_mouse_input(self, current_state: GameStates) -> Dict[str, Any]:
        """Process mouse input for the current game state.

        Args:
            current_state (GameStates): Current game state

        Returns:
            Dict[str, Any]: Dictionary of actions generated from mouse input
        """
        # For now, use default mouse handler for all states
        handler = self.mouse_handlers.get("default")
        if handler and self.current_mouse:
            return handler(self.current_mouse)
        return {}

    def _execute_action_callbacks(self) -> None:
        """Execute registered callbacks for current actions."""
        for action_name, callback in self.action_callbacks.items():
            if action_name in self.current_actions:
                try:
                    callback(self.current_actions[action_name])
                except Exception as e:
                    # Log error but don't crash the game
                    import logging

                    logging.error(f"Error in action callback for {action_name}: {e}")

    def register_action_callback(self, action_name: str, callback: Callable) -> None:
        """Register a callback for a specific action.

        Args:
            action_name (str): Name of the action to listen for
            callback (Callable): Function to call when action occurs
        """
        self.action_callbacks[action_name] = callback

    def unregister_action_callback(self, action_name: str) -> None:
        """Unregister a callback for a specific action.

        Args:
            action_name (str): Name of the action to stop listening for
        """
        if action_name in self.action_callbacks:
            del self.action_callbacks[action_name]

    def register_key_handler(self, state: GameStates, handler: Callable) -> None:
        """Register a custom key handler for a specific game state.

        Args:
            state (GameStates): Game state to handle
            handler (Callable): Function to handle key input for this state
        """
        self.key_handlers[state] = handler

    def register_mouse_handler(self, state_name: str, handler: Callable) -> None:
        """Register a custom mouse handler.

        Args:
            state_name (str): Name/identifier for this handler
            handler (Callable): Function to handle mouse input
        """
        self.mouse_handlers[state_name] = handler

    def start_recording(self) -> None:
        """Start recording input for playback."""
        self.recording = True
        self.input_buffer.clear()

    def stop_recording(self) -> None:
        """Stop recording input."""
        self.recording = False

    def start_playback(self) -> None:
        """Start playing back recorded input."""
        if self.input_buffer:
            self.playing_back = True
            self.playback_index = 0

    def stop_playback(self) -> None:
        """Stop input playback."""
        self.playing_back = False
        self.playback_index = 0

    def _record_input(self) -> None:
        """Record current input state."""
        if self.current_key:
            input_record = {
                "type": "key",
                "key_code": self.current_key.vk,
                "char": self.current_key.c,
                "actions": self.current_actions.copy(),
            }
            self.input_buffer.append(input_record)

        if self.current_mouse_actions:
            input_record = {
                "type": "mouse",
                "actions": self.current_mouse_actions.copy(),
            }
            self.input_buffer.append(input_record)

    def _process_playback(self) -> None:
        """Process input playback."""
        if self.playback_index >= len(self.input_buffer):
            self.stop_playback()
            return

        record = self.input_buffer[self.playback_index]

        if record["type"] == "key":
            self.current_actions = record["actions"]
        elif record["type"] == "mouse":
            self.current_mouse_actions = record["actions"]

        self.playback_index += 1

    def get_current_actions(self) -> Dict[str, Any]:
        """Get the current keyboard actions.

        Returns:
            Dict[str, Any]: Current keyboard actions
        """
        return self.current_actions.copy()

    def get_current_mouse_actions(self) -> Dict[str, Any]:
        """Get the current mouse actions.

        Returns:
            Dict[str, Any]: Current mouse actions
        """
        return self.current_mouse_actions.copy()

    def has_action(self, action_name: str) -> bool:
        """Check if a specific action is currently active.

        Args:
            action_name (str): Name of the action to check

        Returns:
            bool: True if the action is active
        """
        return (
            action_name in self.current_actions
            or action_name in self.current_mouse_actions
        )

    def get_action_value(self, action_name: str) -> Any:
        """Get the value of a specific action.

        Args:
            action_name (str): Name of the action to get

        Returns:
            Any: Value of the action, or None if not found
        """
        if action_name in self.current_actions:
            return self.current_actions[action_name]
        elif action_name in self.current_mouse_actions:
            return self.current_mouse_actions[action_name]
        return None

    def cleanup(self) -> None:
        """Clean up input system resources."""
        self.action_callbacks.clear()
        self.input_buffer.clear()
        self.stop_recording()
        self.stop_playback()
