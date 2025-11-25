"""Keyboard input source implementation.

This module provides a KeyboardInputSource class that wraps the existing libtcod-based
input handling system, adapting it to the InputSource protocol. This allows the game loop
to be input-source-agnostic while maintaining all existing keyboard controls.
"""

from typing import Any, Optional
import tcod.libtcodpy as libtcod

from input_handlers import handle_keys, handle_mouse
from game_states import GameStates
from io_layer.interfaces import ActionDict


class KeyboardInputSource:
    """Input source implementation for keyboard and mouse using libtcod.

    This class wraps the existing libtcod input handling system, providing
    a clean interface to the InputSource protocol. It manages keyboard and mouse
    event acquisition and translation to game actions.

    Attributes:
        death_frame_counter: Frames since player death (used for death screen input delay)
        current_key: Last received Key object
        current_mouse: Last received Mouse object
    """

    def __init__(self):
        """Initialize the KeyboardInputSource.

        Sets up libtcod key and mouse objects for event handling.
        """
        self.current_key = libtcod.Key()
        self.current_mouse = libtcod.Mouse()
        self.death_frame_counter = None

    def record_external_event_pump(self) -> None:
        """DEPRECATED: No longer used.
        
        Previously, this flagged that events were pumped externally to prevent
        double-polling. Now we only poll events in next_action(), so this is
        no longer needed.
        
        Kept for API compatibility but does nothing.
        """
        pass  # No-op

    def next_action(self, game_state: Any) -> ActionDict:
        """Get the next player action from keyboard/mouse input.

        Acquires input events from libtcod and translates them to game actions
        based on the current game state. Handles both keyboard and mouse input,
        routing through appropriate state-specific handlers.

        Args:
            game_state: Object containing current game state. Expected to have attributes:
                        - game_state: GameStates enum value indicating current state
                        - (optional) other state-specific information

        Returns:
            An ActionDict containing the next player action, or an empty dict if no
            input is available.
        """
        # DEBUG: Log key state BEFORE processing
        import logging
        logger = logging.getLogger(__name__)
        before_vk = self.current_key.vk
        before_c = self.current_key.c
        logger.debug(f"[NEXT_ACTION START] key=({before_vk}, {before_c})")
        
        # CRITICAL: Poll events here (and ONLY here) to avoid double-polling
        # We use EVENT_KEY_PRESS (not EVENT_ANY) to only get key press events,
        # not key releases or other events that might confuse the input handling.
        libtcod.sys_check_for_event(
            libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, self.current_key, self.current_mouse
        )
        logger.debug(f"[NEXT_ACTION] Polled events, key now=({self.current_key.vk}, {self.current_key.c})")

        # Extract game state enum
        current_game_state = getattr(game_state, "game_state", GameStates.PLAYERS_TURN)

        # Combine keyboard and mouse actions
        actions = {}

        # Handle keyboard input
        if self.current_key.vk != libtcod.KEY_NONE or self.current_key.c != 0:
            logger.debug(f"[NEXT_ACTION] Processing key: vk={self.current_key.vk}, c={self.current_key.c}")
            
            # Special case: PLAYER_DEAD needs death frame counter
            if current_game_state == GameStates.PLAYER_DEAD:
                self.death_frame_counter = getattr(game_state, "death_frame_counter", 0)
                key_actions = handle_keys(
                    self.current_key, current_game_state, self.death_frame_counter
                )
            else:
                key_actions = handle_keys(self.current_key, current_game_state)

            actions.update(key_actions)
            logger.debug(f"[NEXT_ACTION] Key produced actions: {actions}")
            
            # CRITICAL FIX: Clear the key after processing to prevent double-processing
            # Without this, the same key persists across frames and causes double moves.
            # This ensures: one keypress → one processed action → one world tick.
            self.current_key.vk = libtcod.KEY_NONE
            self.current_key.c = 0
            logger.debug(f"[NEXT_ACTION] Cleared key after processing")
        else:
            logger.debug(f"[NEXT_ACTION] No key to process")

        # Handle mouse input
        if (
            self.current_mouse.lbutton_pressed
            or self.current_mouse.rbutton_pressed
            or self.current_mouse.cx != -1
            or self.current_mouse.cy != -1
        ):
            camera = getattr(game_state, "camera", None)
            mouse_actions = handle_mouse(
                self.current_mouse, camera=camera, game_state=current_game_state
            )
            actions.update(mouse_actions)

        logger.debug(f"[NEXT_ACTION END] returning actions={actions}")
        return actions

