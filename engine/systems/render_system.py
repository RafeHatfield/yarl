"""Rendering system for the game engine.

This module contains the RenderSystem which handles all rendering operations
including entity drawing, UI panels, and screen management. It abstracts
the rendering backend to allow for future sprite support.
"""

from typing import List, Dict, Any, Optional
import tcod.libtcodpy as libtcod

from ..system import System
from render_functions import render_all, clear_all, draw_entity, clear_entity
from fov_functions import recompute_fov


class RenderSystem(System):
    """System responsible for rendering the game world and UI.

    The RenderSystem manages all rendering operations including:
    - Drawing the game map and entities
    - Rendering UI panels and menus
    - Managing field of view calculations
    - Coordinating screen updates

    Attributes:
        console: Main game console for rendering
        panel: UI panel console
        fov_map: Field of view map for visibility calculations
        fov_recompute (bool): Whether FOV needs recalculation
        screen_width (int): Width of the screen
        screen_height (int): Height of the screen
        colors (dict): Color configuration dictionary
    """

    def __init__(
        self,
        console,
        panel,
        screen_width: int,
        screen_height: int,
        colors: Dict[str, Any],
        priority: int = 100,
    ):
        """Initialize the RenderSystem.

        Args:
            console: Main game console for rendering
            panel: UI panel console for UI elements
            screen_width (int): Width of the screen in characters
            screen_height (int): Height of the screen in characters
            colors (Dict[str, Any]): Color configuration dictionary
            priority (int, optional): System update priority. Defaults to 100.
        """
        super().__init__("render", priority)
        self.console = console
        self.panel = panel
        self.fov_map = None
        self.fov_recompute = True
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.colors = colors

        # UI layout configuration
        self.bar_width = 20
        self.panel_height = 7
        self.panel_y = screen_height - self.panel_height

    def initialize(self, engine) -> None:
        """Initialize the render system with engine reference.

        Args:
            engine: Reference to the main GameEngine instance
        """
        super().initialize(engine)

    def update(self, dt: float) -> None:
        """Update the rendering system for one frame.

        Performs all rendering operations including FOV calculation,
        entity drawing, UI rendering, and screen presentation.

        Args:
            dt (float): Delta time since last update in seconds
        """
        # Get game state from engine (we'll need to implement this)
        game_state = self._get_game_state()
        if not game_state:
            return

        entities = game_state.get("entities", [])
        player = game_state.get("player")
        game_map = game_state.get("game_map")
        message_log = game_state.get("message_log")
        current_game_state = game_state.get("current_state")
        mouse = game_state.get("mouse")

        if not all([player, game_map, message_log]):
            return

        # Recompute FOV if needed
        if self.fov_recompute and self.fov_map:
            recompute_fov(
                self.fov_map,
                player.x,
                player.y,
                game_state.get("fov_radius", 10),
                game_state.get("fov_light_walls", True),
                game_state.get("fov_algorithm", 0),
            )

        # Render everything
        render_all(
            self.console,
            self.panel,
            entities,
            player,
            game_map,
            self.fov_map,
            self.fov_recompute,
            message_log,
            self.screen_width,
            self.screen_height,
            self.bar_width,
            self.panel_height,
            self.panel_y,
            mouse,
            self.colors,
            current_game_state,
        )

        self.fov_recompute = False

        # Present the frame
        libtcod.console_flush()

        # Clear entities for next frame
        clear_all(self.console, entities)

    def set_fov_map(self, fov_map) -> None:
        """Set the field of view map.

        Args:
            fov_map: The FOV map object for visibility calculations
        """
        self.fov_map = fov_map
        self.fov_recompute = True

    def request_fov_recompute(self) -> None:
        """Request that FOV be recomputed on next update."""
        self.fov_recompute = True

    def draw_entity(self, entity) -> None:
        """Draw a single entity on the console.

        Args:
            entity: The entity to draw
        """
        if self.fov_map:
            draw_entity(
                self.console,
                entity,
                self.fov_map,
                self._get_game_state().get("game_map"),
            )

    def clear_entity(self, entity) -> None:
        """Clear a single entity from the console.

        Args:
            entity: The entity to clear
        """
        clear_entity(self.console, entity)

    def _get_game_state(self) -> Optional[Dict[str, Any]]:
        """Get current game state from the engine.

        This is a temporary method until we implement proper
        game state management in the engine.

        Returns:
            Dict[str, Any] or None: Current game state data
        """
        # TODO: Implement proper game state management
        # For now, return None to indicate no state available
        return None

    def cleanup(self) -> None:
        """Clean up rendering resources."""
        # Clean up any rendering resources if needed
        pass
