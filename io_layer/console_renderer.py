"""Console-based (terminal/ASCII) renderer implementation.

This module provides a ConsoleRenderer class that wraps the existing libtcod-based
rendering system, adapting it to the Renderer protocol. This allows the game loop
to be renderer-agnostic while maintaining all existing terminal rendering behavior.
"""

from typing import Any, Dict, Optional, Callable
import tcod.libtcodpy as libtcod

from render_functions import render_all
from config.ui_layout import get_ui_layout
from rendering.frame_models import FrameContext, FrameVisuals

# Module-level frame counter for diagnostic logging
_LAST_FRAME_COUNTER = 0


def get_last_frame_counter() -> int:
    """Get the current frame counter for debugging/logging purposes.
    
    Returns:
        int: The frame counter value from the most recent ConsoleRenderer.render() call.
    """
    return _LAST_FRAME_COUNTER


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
        self._frame_counter = 0

        # Cache console dimensions
        self.screen_width = self.ui_layout.screen_width
        self.screen_height = self.ui_layout.screen_height
        self.panel_height = self.ui_layout.status_panel_height
        self.panel_y = self.ui_layout.viewport_height

    def render(self, frame_data: Any, render_func: Optional[Callable[..., None]] = None) -> None:
        """Render the current game state to the screen via the frame pipeline.

        The orchestrator performs these steps exactly once per frame:

        1. Clear working consoles.
        2. Delegate world/UI drawing to :func:`render_functions.render_all`.
        3. Resolve and draw hover tooltips.
        4. Blit composed consoles to the root console.
        5. Play queued visual effects.
        6. Flush the root console.

        Keeping all clears and flushes centralized here guarantees the "single
        frame pipeline" invariant regardless of which modules produce draw
        commands during the frame.

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
        # Increment frame counter and expose it at module level for diagnostics
        global _LAST_FRAME_COUNTER
        self._frame_counter += 1
        _LAST_FRAME_COUNTER = self._frame_counter
        
        if isinstance(frame_data, FrameContext):
            frame_context = frame_data
        else:
            entities = getattr(frame_data, "entities", [])
            player = getattr(frame_data, "player", None)
            game_map = getattr(frame_data, "game_map", None)
            fov_map = getattr(frame_data, "fov_map", None)
            message_log = getattr(frame_data, "message_log", None)
            fov_recompute = getattr(frame_data, "fov_recompute", False)
            mouse = getattr(frame_data, "mouse", None)
            current_game_state = getattr(frame_data, "game_state", None)
            camera = getattr(frame_data, "camera", None)
            death_screen_quote = getattr(frame_data, "death_screen_quote", None)

            frame_context = FrameContext(
                entities=list(entities) if entities is not None else [],
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
                sidebar_console=self.sidebar_console,
                camera=camera,
                death_screen_quote=death_screen_quote,
                use_optimization=True,
            )

        camera = frame_context.camera

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
        render_callable = render_func or render_all

        visuals = FrameVisuals(
            viewport_console=self.viewport_console,
            status_console=self.status_console,
            sidebar_console=self.sidebar_console,
        )

        result = render_callable(frame_context, visuals)
        if isinstance(result, FrameVisuals):
            visuals = result

        from ui import tooltip

        tooltip_model = tooltip.resolve_hover(visuals.hover_probe, frame_context)
        tooltip.render(tooltip_model, self.viewport_console, self.sidebar_console)

        self._blit_to_root()

        # CRITICAL: Play visual effects BEFORE flushing to screen!
        # This ensures all effects (map, entities, UI, and visual effects) are drawn
        # onto the console BEFORE the single flush, preventing flicker and ensuring
        # effects appear as part of the same visual frame as the rest of the game.
        from visual_effect_queue import get_effect_queue
        from ui.debug_flags import TOOLTIP_DISABLE_EFFECTS
        
        if not TOOLTIP_DISABLE_EFFECTS:
            effect_queue = get_effect_queue()
            if effect_queue.has_effects():
                effect_queue.play_all(con=0, camera=camera)

        # Flush console to display (single flush per frame - canonical renderer only!)
        import warnings

        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                category=DeprecationWarning,
                message="This function is not supported if contexts are being used",
            )
            libtcod.console_flush()

    def _blit_to_root(self) -> None:
        """Copy working consoles to the root console prior to flushing."""

        ui_layout = self.ui_layout

        try:
            viewport_pos = ui_layout.viewport_position
            libtcod.console_blit(
                self.viewport_console,
                0,
                0,
                ui_layout.viewport_width,
                ui_layout.viewport_height,
                0,
                viewport_pos[0],
                viewport_pos[1],
            )

            status_pos = ui_layout.status_panel_position
            libtcod.console_blit(
                self.status_console,
                0,
                0,
                ui_layout.status_panel_width,
                ui_layout.status_panel_height,
                0,
                status_pos[0],
                status_pos[1],
            )

            if self.sidebar_console:
                sidebar_pos = ui_layout.sidebar_position
                libtcod.console_blit(
                    self.sidebar_console,
                    0,
                    0,
                    ui_layout.sidebar_width,
                    ui_layout.screen_height,
                    0,
                    sidebar_pos[0],
                    sidebar_pos[1],
                )
        except (TypeError, AttributeError):
            # Tests may provide simple mocks without full libtcod API support.
            pass

