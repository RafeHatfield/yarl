"""Performance optimization system for the game engine.

This module provides performance optimizations that maintain clean code
while improving rendering and game loop efficiency. Includes dirty rectangle
rendering, spatial indexing, and render culling.
"""

from typing import Dict, Set, Tuple, List, Any, Optional
import logging
from collections import defaultdict

from ..system import System
from config.game_constants import get_performance_config

logger = logging.getLogger(__name__)


class PerformanceSystem(System):
    """System responsible for performance optimizations.

    The PerformanceSystem provides various optimizations including:
    - Dirty rectangle tracking for efficient rendering
    - Spatial indexing for fast entity lookups
    - Render culling to skip invisible entities
    - FOV caching to avoid redundant calculations

    These optimizations maintain clean code while significantly improving
    performance, especially with larger maps and more entities.

    Attributes:
        dirty_rectangles (Set): Areas that need rerendering
        spatial_index (Dict): Grid-based entity spatial index
        fov_cache (Dict): Cached FOV results
        render_stats (Dict): Performance statistics
        optimization_enabled (bool): Whether optimizations are active
    """

    def __init__(self, priority: int = 5):
        """Initialize the PerformanceSystem with configurable settings.

        Args:
            priority (int, optional): System update priority. Defaults to 5 (very early).
        """
        super().__init__("performance", priority)
        
        # Get performance configuration
        perf_config = get_performance_config()

        # Dirty rectangle tracking
        self.dirty_rectangles: Set[Tuple[int, int, int, int]] = set()
        self.full_redraw_needed = True

        # Spatial indexing for entities
        self.spatial_index: Dict[Tuple[int, int], List[Any]] = defaultdict(list)
        self.spatial_grid_size = perf_config.SPATIAL_GRID_SIZE

        # FOV caching
        self.fov_cache: Dict[Tuple[int, int, int], Any] = {}
        self.fov_cache_size_limit = perf_config.FOV_CACHE_SIZE
        self.last_fov_position = None
        self.last_fov_radius = None

        # Render culling
        self.visible_entities: Set[Any] = set()
        self.last_visible_check = {}

        # Performance statistics
        self.render_stats = {
            "frames_rendered": 0,
            "dirty_rectangles_used": 0,
            "entities_culled": 0,
            "fov_cache_hits": 0,
            "spatial_lookups": 0,
        }

        # Configuration
        self.optimization_enabled = True
        self.debug_mode = False

    def initialize(self, engine) -> None:
        """Initialize the performance system with engine reference.

        Args:
            engine: Reference to the main GameEngine instance
        """
        super().initialize(engine)
        logger.info("PerformanceSystem initialized")

    def update(self, dt: float) -> None:
        """Update the performance system for one frame.

        Updates spatial indices, processes dirty rectangles, and maintains
        performance optimization data structures.

        Args:
            dt (float): Delta time since last update in seconds
        """
        if not self.optimization_enabled:
            return

        if not self.engine or not hasattr(self.engine, "state_manager"):
            return

        state_manager = self.engine.state_manager
        if not state_manager:
            return

        game_state = state_manager.state

        # Update spatial index
        self._update_spatial_index(game_state.entities)

        # Update visible entities for render culling
        self._update_visible_entities(game_state)

        # Store optimization data for other systems to use
        state_manager.set_extra_data("spatial_index", self.spatial_index)
        state_manager.set_extra_data("visible_entities", self.visible_entities)
        state_manager.set_extra_data("dirty_rectangles", self.dirty_rectangles)
        state_manager.set_extra_data("full_redraw_needed", self.full_redraw_needed)

    def _update_spatial_index(self, entities: List[Any]) -> None:
        """Update the spatial index with current entity positions.

        Args:
            entities (List): All entities in the game
        """
        # Clear previous index
        self.spatial_index.clear()

        # Build new index
        for entity in entities:
            if hasattr(entity, "x") and hasattr(entity, "y"):
                grid_x = entity.x // self.spatial_grid_size
                grid_y = entity.y // self.spatial_grid_size
                self.spatial_index[(grid_x, grid_y)].append(entity)

        self.render_stats["spatial_lookups"] += 1

    def _update_visible_entities(self, game_state) -> None:
        """Update the set of visible entities for render culling.

        Args:
            game_state: Current game state
        """
        if not game_state.fov_map:
            return

        self.visible_entities.clear()

        for entity in game_state.entities:
            if hasattr(entity, "x") and hasattr(entity, "y"):
                # Check if entity is in FOV or is stairs on explored tile
                from fov_functions import map_is_in_fov

                in_fov = map_is_in_fov(game_state.fov_map, entity.x, entity.y)
                
                # Special entities visible on explored tiles (stairs, chests, signposts, murals, secret doors, portals)
                # SAFETY: Use GameMap safe accessor method instead of manual bounds check
                is_persistent_feature_on_explored = False
                if game_state.game_map:
                    is_persistent_feature_on_explored = (
                        game_state.game_map.is_explored(entity.x, entity.y)
                        and (
                            (hasattr(entity, "stairs") and entity.stairs) or
                            (hasattr(entity, "chest") and entity.chest) or
                            (hasattr(entity, "signpost") and entity.signpost) or
                            (hasattr(entity, "mural") and entity.mural) or
                            (hasattr(entity, "is_secret_door_marker") and entity.is_secret_door_marker) or
                            (hasattr(entity, "is_portal") and entity.is_portal)
                        )
                    )

                if in_fov or is_persistent_feature_on_explored:
                    self.visible_entities.add(entity)
                else:
                    self.render_stats["entities_culled"] += 1

    def mark_dirty_rectangle(self, x: int, y: int, width: int, height: int) -> None:
        """Mark a rectangular area as needing redraw.

        Args:
            x (int): Left edge of the rectangle
            y (int): Top edge of the rectangle
            width (int): Width of the rectangle
            height (int): Height of the rectangle
        """
        self.dirty_rectangles.add((x, y, width, height))
        if self.debug_mode:
            logger.debug(f"Marked dirty rectangle: ({x}, {y}, {width}, {height})")

    def mark_entity_dirty(
        self, entity: Any, old_x: int = None, old_y: int = None
    ) -> None:
        """Mark areas around an entity as needing redraw.

        Args:
            entity: The entity that moved or changed
            old_x (int, optional): Previous X position if entity moved
            old_y (int, optional): Previous Y position if entity moved
        """
        if hasattr(entity, "x") and hasattr(entity, "y"):
            # Mark current position
            self.mark_dirty_rectangle(entity.x, entity.y, 1, 1)

            # Mark old position if entity moved
            if old_x is not None and old_y is not None:
                self.mark_dirty_rectangle(old_x, old_y, 1, 1)

    def request_full_redraw(self) -> None:
        """Request a full screen redraw on the next frame."""
        self.full_redraw_needed = True
        self.dirty_rectangles.clear()
        if self.debug_mode:
            logger.debug("Full redraw requested")

    def clear_dirty_rectangles(self) -> None:
        """Clear all dirty rectangles after rendering."""
        self.dirty_rectangles.clear()
        self.full_redraw_needed = False
        self.render_stats["dirty_rectangles_used"] += len(self.dirty_rectangles)

    def get_entities_in_area(
        self, x: int, y: int, width: int, height: int
    ) -> List[Any]:
        """Get all entities within a rectangular area using spatial indexing.

        Args:
            x (int): Left edge of the area
            y (int): Top edge of the area
            width (int): Width of the area
            height (int): Height of the area

        Returns:
            List: Entities within the specified area
        """
        entities = []

        # Calculate grid bounds
        grid_x1 = x // self.spatial_grid_size
        grid_y1 = y // self.spatial_grid_size
        grid_x2 = (x + width - 1) // self.spatial_grid_size
        grid_y2 = (y + height - 1) // self.spatial_grid_size

        # Check all grid cells that intersect the area
        for gx in range(grid_x1, grid_x2 + 1):
            for gy in range(grid_y1, grid_y2 + 1):
                for entity in self.spatial_index.get((gx, gy), []):
                    # Double-check entity is actually in the area
                    if (
                        hasattr(entity, "x")
                        and hasattr(entity, "y")
                        and x <= entity.x < x + width
                        and y <= entity.y < y + height
                    ):
                        entities.append(entity)

        return entities

    def get_entities_at_position(self, x: int, y: int) -> List[Any]:
        """Get all entities at a specific position using spatial indexing.

        Args:
            x (int): X coordinate
            y (int): Y coordinate

        Returns:
            List: Entities at the specified position
        """
        return self.get_entities_in_area(x, y, 1, 1)

    def cache_fov_result(self, x: int, y: int, radius: int, fov_map: Any) -> None:
        """Cache a FOV calculation result.

        Args:
            x (int): FOV center X coordinate
            y (int): FOV center Y coordinate
            radius (int): FOV radius
            fov_map: The computed FOV map
        """
        cache_key = (x, y, radius)
        self.fov_cache[cache_key] = fov_map

        # Limit cache size to prevent memory issues
        if len(self.fov_cache) > 100:
            # Remove oldest entries (simple FIFO)
            oldest_key = next(iter(self.fov_cache))
            del self.fov_cache[oldest_key]

    def get_cached_fov(self, x: int, y: int, radius: int) -> Optional[Any]:
        """Get a cached FOV result if available.

        Args:
            x (int): FOV center X coordinate
            y (int): FOV center Y coordinate
            radius (int): FOV radius

        Returns:
            FOV map if cached, None otherwise
        """
        cache_key = (x, y, radius)
        if cache_key in self.fov_cache:
            self.render_stats["fov_cache_hits"] += 1
            return self.fov_cache[cache_key]
        return None

    def should_recompute_fov(self, x: int, y: int, radius: int) -> bool:
        """Check if FOV needs recomputation.

        Args:
            x (int): Current FOV center X coordinate
            y (int): Current FOV center Y coordinate
            radius (int): Current FOV radius

        Returns:
            bool: True if FOV should be recomputed
        """
        # Always recompute if position or radius changed
        if self.last_fov_position != (x, y) or self.last_fov_radius != radius:
            self.last_fov_position = (x, y)
            self.last_fov_radius = radius
            return True

        return False

    def enable_optimizations(self) -> None:
        """Enable performance optimizations."""
        self.optimization_enabled = True
        logger.info("Performance optimizations enabled")

    def disable_optimizations(self) -> None:
        """Disable performance optimizations (for debugging)."""
        self.optimization_enabled = False
        logger.info("Performance optimizations disabled")

    def set_debug_mode(self, enabled: bool) -> None:
        """Enable or disable debug logging.

        Args:
            enabled (bool): Whether to enable debug mode
        """
        self.debug_mode = enabled
        logger.info(f"Performance debug mode {'enabled' if enabled else 'disabled'}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics.

        Returns:
            Dict: Performance statistics
        """
        return self.render_stats.copy()

    def reset_performance_stats(self) -> None:
        """Reset performance statistics."""
        self.render_stats = {
            "frames_rendered": 0,
            "dirty_rectangles_used": 0,
            "entities_culled": 0,
            "fov_cache_hits": 0,
            "spatial_lookups": 0,
        }
        logger.info("Performance statistics reset")

    def cleanup(self) -> None:
        """Clean up performance system resources."""
        self.dirty_rectangles.clear()
        self.spatial_index.clear()
        self.fov_cache.clear()
        self.visible_entities.clear()
        logger.info("PerformanceSystem cleaned up")
