"""Console-based (terminal/ASCII) renderer implementation.

This module provides a ConsoleRenderer class that wraps the existing libtcod-based
rendering system, adapting it to the Renderer protocol. This allows the game loop
to be renderer-agnostic while maintaining all existing terminal rendering behavior.
"""

from typing import Any, Dict, Optional
import tcod.libtcodpy as libtcod

from render_functions import render_all
from config.ui_layout import get_ui_layout


class ConsoleRenderer:
    """Renderer implementation for terminal/ASCII display using libtcod.

    This class wraps the existing libtcod console rendering pipeline, providing
    a clean interface to the Renderer protocol. It manages all console setup,
    configuration, and drawing.

    Attributes:
        sidebar_console: Console for left sidebar (stats, equipment, etc.)
        viewport_console: Console for main game viewport (map and entities)
        status_console: Console for status panel (HP, messages)
        root_console: Root libtcod console for screen output
        colors: Color configuration dictionary
        ui_layout: UI layout configuration
        bar_width: Width of status bars
    """

    def __init__(
        self,
        sidebar_console: Any,
        viewport_console: Any,
        status_console: Any,
        colors: Dict[str, Any],
        ui_layout: Optional[Any] = None,
        bar_width: int = 20,
    ):
        """Initialize the ConsoleRenderer.

        Args:
            sidebar_console: libtcod console for left sidebar
            viewport_console: libtcod console for main viewport
            status_console: libtcod console for status panel
            colors: Color configuration dictionary
            ui_layout: UI layout configuration (uses get_ui_layout() if None)
            bar_width: Width of status bars (default 20)
        """
        self.sidebar_console = sidebar_console
        self.viewport_console = viewport_console
        self.status_console = status_console
        self.colors = colors
        self.ui_layout = ui_layout or get_ui_layout()
        self.bar_width = bar_width

        # Cache console dimensions
        self.screen_width = self.ui_layout.screen_width
        self.screen_height = self.ui_layout.screen_height
        self.panel_height = self.ui_layout.status_panel_height
        self.panel_y = self.ui_layout.viewport_height

    def render(self, game_state: Any) -> None:
        """Render the current game state to the screen.

        Delegates to the existing render_all() function, adapting the game state
        to the function's expected parameters. This maintains all existing rendering
        behavior while wrapping it in the Renderer protocol.

        Args:
            game_state: Object containing all game state needed for rendering.
                        Expected to have attributes:
                        - entities: List of entities to render
                        - player: The player entity
                        - game_map: The game map
                        - fov_map: Field of view map
                        - message_log: Game message log
                        - fov_recompute: Whether FOV needs recomputation
                        - camera: Camera for viewport scrolling (optional)
                        - death_screen_quote: Death screen quote (optional)
        """
        # Extract components from game state (adapt to existing structure)
        entities = getattr(game_state, "entities", [])
        player = getattr(game_state, "player", None)
        game_map = getattr(game_state, "game_map", None)
        fov_map = getattr(game_state, "fov_map", None)
        message_log = getattr(game_state, "message_log", None)
        fov_recompute = getattr(game_state, "fov_recompute", False)
        mouse = getattr(game_state, "mouse", None)
        current_game_state = getattr(game_state, "game_state", None)
        camera = getattr(game_state, "camera", None)
        death_screen_quote = getattr(game_state, "death_screen_quote", None)

        # Clear the ROOT console (console 0) at the start of each frame
        # This ensures no stale data from previous frames persists
        try:
            libtcod.console_clear(0)  # Clear root console
        except (TypeError, AttributeError):
            # Mock tests might not support this - that's OK
            pass

        # CRITICAL: Clear working consoles EVERY FRAME, not just on FOV recompute!
        # Entities may move between frames, and old glyphs must be cleared from the 
        # console before new ones are drawn. Failing to do this causes "double entity" 
        # visual artifacts where old entity positions persist onscreen.
        #
        # This is the fix for the double-render bug where orcs appeared twice.
        try:
            libtcod.console_clear(self.viewport_console)
            libtcod.console_clear(self.status_console)
            if self.sidebar_console:
                libtcod.console_clear(self.sidebar_console)
        except (TypeError, AttributeError):
            # Mock consoles in tests will fail - that's OK, we just skip clearing
            pass

        # Call the existing render_all function with all parameters
        render_all(
            con=self.viewport_console,
            panel=self.status_console,
            entities=entities,
            player=player,
            game_map=game_map,
            fov_map=fov_map,
            fov_recompute=fov_recompute,
            message_log=message_log,
            screen_width=self.screen_width,
            screen_height=self.screen_height,
            bar_width=self.bar_width,
            panel_height=self.panel_height,
            panel_y=self.panel_y,
            mouse=mouse,
            colors=self.colors,
            game_state=current_game_state,
            use_optimization=True,
            sidebar_console=self.sidebar_console,
            camera=camera,
            death_screen_quote=death_screen_quote,
        )

        # Flush console to display (existing behavior)
        import warnings

        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                category=DeprecationWarning,
                message="This function is not supported if contexts are being used",
            )
            libtcod.console_flush()

