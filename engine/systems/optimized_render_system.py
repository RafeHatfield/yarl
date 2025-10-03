"""Optimized rendering system with performance enhancements.

This module extends the base RenderSystem with performance optimizations
including dirty rectangle rendering, render culling, and efficient FOV handling.
"""

from typing import Dict, Any, Optional, Set
import tcod.libtcodpy as libtcod
import logging

from .render_system import RenderSystem
from render_functions import render_all, clear_all, draw_entity, clear_entity
from fov_functions import recompute_fov

logger = logging.getLogger(__name__)


class OptimizedRenderSystem(RenderSystem):
    """Optimized rendering system with performance enhancements.

    Extends the base RenderSystem with optimizations that maintain clean code:
    - Dirty rectangle rendering to minimize redraws
    - Render culling to skip invisible entities
    - FOV caching to avoid redundant calculations
    - Spatial awareness for efficient rendering

    These optimizations can provide significant performance improvements
    while maintaining the same clean interface as the base RenderSystem.

    Attributes:
        use_optimizations (bool): Whether to use performance optimizations
        last_rendered_entities (Set): Entities rendered in the last frame
        render_cache (Dict): Cache for rendering data
    """

    def __init__(
        self,
        console,
        panel,
        screen_width: int,
        screen_height: int,
        colors: Dict[str, Any],
        priority: int = 100,
        use_optimizations: bool = True,
        sidebar_console=None,
    ):
        """Initialize the OptimizedRenderSystem.

        Args:
            console: Main game console for rendering (viewport)
            panel: UI panel console (status panel)
            screen_width (int): Width of the screen
            screen_height (int): Height of the screen
            colors (Dict[str, Any]): Color configuration dictionary
            priority (int, optional): System update priority. Defaults to 100.
            use_optimizations (bool, optional): Whether to use optimizations. Defaults to True.
            sidebar_console: Left sidebar console (optional)
        """
        super().__init__(console, panel, screen_width, screen_height, colors, priority, sidebar_console)

        # Optimization settings
        self.use_optimizations = use_optimizations

        # Render tracking
        self.last_rendered_entities: Set[Any] = set()
        self.render_cache: Dict[str, Any] = {}

        # Performance counters
        self.optimization_stats = {
            "frames_optimized": 0,
            "entities_skipped": 0,
            "dirty_renders": 0,
            "full_renders": 0,
        }

    def update(self, dt: float) -> None:
        """Update the optimized rendering system for one frame.

        Uses performance optimizations when available, falls back to
        standard rendering otherwise.

        Args:
            dt (float): Delta time since last update in seconds
        """
        if not self.enabled:
            return

        # Get game state
        game_state = self._get_game_state()
        if not game_state:
            return
        
        # Update FOV map if it changed (e.g., new level)
        new_fov_map = game_state.get("fov_map")
        if new_fov_map and new_fov_map != self.fov_map:
            self.fov_map = new_fov_map

        # Extract game state data
        entities = game_state.get("entities", [])
        player = game_state.get("player")
        game_map = game_state.get("game_map")
        message_log = game_state.get("message_log")
        current_game_state = game_state.get("current_state")
        mouse = game_state.get("mouse")

        if not all([player, game_map, message_log]):
            return

        # Get the authoritative fov_recompute flag from game state
        game_state_fov_recompute = game_state.get("fov_recompute", False)
        
        
        # Update our internal flag from game state
        self.fov_recompute = game_state_fov_recompute
        
        # Use the game state flag for rendering (this is the authoritative source)
        original_fov_recompute = game_state_fov_recompute
        
        # Use optimized rendering if available and enabled
        if self.use_optimizations and self._has_performance_data(game_state):
            self._optimized_render(
                game_state,
                entities,
                player,
                game_map,
                message_log,
                current_game_state,
                mouse,
                original_fov_recompute,
            )
        else:
            # Fall back to standard rendering
            self._standard_render(
                game_state,
                entities,
                player,
                game_map,
                message_log,
                current_game_state,
                mouse,
                original_fov_recompute,
            )

        # Present the frame
        console_flush_succeeded = False
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=DeprecationWarning, 
                                      message="This function is not supported if contexts are being used")
                libtcod.console_flush()
            console_flush_succeeded = True
        except RuntimeError:
            # Handle case where no console context exists (e.g., during testing)
            pass

        # Reset the game state fov_recompute flag after rendering
        # This prevents unnecessary redraws on subsequent frames
        # Only reset if we actually rendered successfully (not during mocked tests)
        if (self.engine and hasattr(self.engine, 'state_manager') and 
            original_fov_recompute and console_flush_succeeded):
            self.engine.state_manager.state.fov_recompute = False

        # Update render tracking
        self.last_rendered_entities = set(entities)

    def _has_performance_data(self, game_state: Dict[str, Any]) -> bool:
        """Check if performance optimization data is available.

        Args:
            game_state (Dict): Current game state

        Returns:
            bool: True if performance data is available
        """
        return (
            "visible_entities" in game_state
            and "dirty_rectangles" in game_state
            and "full_redraw_needed" in game_state
        )

    def _optimized_render(
        self,
        game_state: Dict[str, Any],
        entities,
        player,
        game_map,
        message_log,
        current_game_state,
        mouse,
        original_fov_recompute: bool,
    ) -> None:
        """Perform optimized rendering using performance data.

        Args:
            game_state (Dict): Current game state with optimization data
            entities: All entities
            player: Player entity
            game_map: Game map
            message_log: Message log
            current_game_state: Current game state
            mouse: Mouse object
        """
        visible_entities = game_state.get("visible_entities", set())
        dirty_rectangles = game_state.get("dirty_rectangles", set())
        full_redraw_needed = game_state.get("full_redraw_needed", True)

        # Handle FOV recomputation with caching
        if self.fov_map:
            performance_system = self.engine.get_system("performance")
            
            # Check if we should recompute based on position (for caching optimization)
            should_recompute_for_position = (
                not performance_system or 
                performance_system.should_recompute_fov(
                    player.x, player.y, game_state.get("fov_radius", 10)
                )
            )
            
            # Always recompute when fov_recompute=True, or when position changed
            if original_fov_recompute or should_recompute_for_position:
                recompute_fov(
                    self.fov_map,
                    player.x,
                    player.y,
                    game_state.get("fov_radius", 10),
                    game_state.get("fov_light_walls", True),
                    game_state.get("fov_algorithm", 12),
                )

                # Cache the result
                if performance_system:
                    performance_system.cache_fov_result(
                        player.x,
                        player.y,
                        game_state.get("fov_radius", 10),
                        self.fov_map,
                    )

        # Decide rendering strategy
        # Force full redraw when FOV was recomputed (map tiles need to be redrawn)
        fov_was_recomputed = original_fov_recompute
        if full_redraw_needed or not dirty_rectangles or fov_was_recomputed:
            # Full render needed
            self._render_full_optimized(
                entities,
                visible_entities,
                player,
                game_map,
                message_log,
                current_game_state,
                mouse,
                original_fov_recompute,
            )
            self.optimization_stats["full_renders"] += 1
        else:
            # Dirty rectangle rendering
            self._render_dirty_rectangles(
                dirty_rectangles,
                entities,
                visible_entities,
                player,
                game_map,
                message_log,
                current_game_state,
                mouse,
            )
            self.optimization_stats["dirty_renders"] += 1

        self.fov_recompute = False
        self.optimization_stats["frames_optimized"] += 1

        # DON'T reset the game state's fov_recompute flag here
        # Let the game logic control when to reset it

        # Clear entities (only visible ones for optimization)
        self._clear_visible_entities(visible_entities)

        # Clear dirty rectangles
        performance_system = self.engine.get_system("performance")
        if performance_system:
            performance_system.clear_dirty_rectangles()

    def _standard_render(
        self,
        game_state: Dict[str, Any],
        entities,
        player,
        game_map,
        message_log,
        current_game_state,
        mouse,
        original_fov_recompute: bool,
    ) -> None:
        """Perform standard rendering (fallback when optimizations unavailable).

        Args:
            game_state (Dict): Current game state
            entities: All entities
            player: Player entity
            game_map: Game map
            message_log: Message log
            current_game_state: Current game state
            mouse: Mouse object
        """
        # Standard FOV recomputation
        if self.fov_recompute and self.fov_map:
            recompute_fov(
                self.fov_map,
                player.x,
                player.y,
                game_state.get("fov_radius", 10),
                game_state.get("fov_light_walls", True),
                game_state.get("fov_algorithm", 12),
            )

        # Standard rendering (use original tile rendering, not optimization)
        render_all(
            self.console,
            self.panel,
            entities,
            player,
            game_map,
            self.fov_map,
            original_fov_recompute,
            message_log,
            self.screen_width,
            self.screen_height,
            self.bar_width,
            self.panel_height,
            self.panel_y,
            mouse,
            self.colors,
            current_game_state,
            use_optimization=False,
        )

        self.fov_recompute = False

        # DON'T reset the game state's fov_recompute flag here
        # Let the game logic control when to reset it

        # Standard entity clearing
        clear_all(self.console, entities)

    def _render_full_optimized(
        self,
        entities,
        visible_entities: Set[Any],
        player,
        game_map,
        message_log,
        current_game_state,
        mouse,
        original_fov_recompute: bool,
    ) -> None:
        """Perform a full render with entity culling optimization.

        Args:
            entities: All entities
            visible_entities (Set): Set of visible entities for culling
            player: Player entity
            game_map: Game map
            message_log: Message log
            current_game_state: Current game state
            mouse: Mouse object
        """
        # Use render_all but with culled entity list
        culled_entities = [e for e in entities if e in visible_entities or e == player]

        render_all(
            self.console,
            self.panel,
            culled_entities,
            player,
            game_map,
            self.fov_map,
            original_fov_recompute,
            message_log,
            self.screen_width,
            self.screen_height,
            self.bar_width,
            self.panel_height,
            self.panel_y,
            mouse,
            self.colors,
            current_game_state,
            use_optimization=False,
        )

        # Track skipped entities
        skipped = len(entities) - len(culled_entities)
        self.optimization_stats["entities_skipped"] += skipped

        if skipped > 0 and logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Culled {skipped} invisible entities")

    def _render_dirty_rectangles(
        self,
        dirty_rectangles: Set,
        entities,
        visible_entities: Set[Any],
        player,
        game_map,
        message_log,
        current_game_state,
        mouse,
    ) -> None:
        """Render only dirty rectangular areas.

        Args:
            dirty_rectangles (Set): Set of dirty rectangle areas
            entities: All entities
            visible_entities (Set): Set of visible entities
            player: Player entity
            game_map: Game map
            message_log: Message log
            current_game_state: Current game state
            mouse: Mouse object
        """
        # For now, fall back to full render for dirty rectangles
        # This could be optimized further by implementing partial rendering
        self._render_full_optimized(
            entities,
            visible_entities,
            player,
            game_map,
            message_log,
            current_game_state,
            mouse,
        )

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Processed {len(dirty_rectangles)} dirty rectangles")

    def _clear_visible_entities(self, visible_entities: Set[Any]) -> None:
        """Clear only visible entities from the console.

        Args:
            visible_entities (Set): Set of visible entities to clear
        """
        for entity in visible_entities:
            clear_entity(self.console, entity)

    def enable_optimizations(self) -> None:
        """Enable rendering optimizations."""
        self.use_optimizations = True
        logger.info("Rendering optimizations enabled")

    def disable_optimizations(self) -> None:
        """Disable rendering optimizations (for debugging)."""
        self.use_optimizations = False
        logger.info("Rendering optimizations disabled")

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get rendering optimization statistics.

        Returns:
            Dict: Optimization statistics
        """
        return self.optimization_stats.copy()

    def reset_optimization_stats(self) -> None:
        """Reset optimization statistics."""
        self.optimization_stats = {
            "frames_optimized": 0,
            "entities_skipped": 0,
            "dirty_renders": 0,
            "full_renders": 0,
        }
        logger.info("Rendering optimization statistics reset")

    def cleanup(self) -> None:
        """Clean up optimized rendering resources."""
        super().cleanup()
        self.last_rendered_entities.clear()
        self.render_cache.clear()
        logger.info("OptimizedRenderSystem cleaned up")
