"""Tile rendering optimization system.

This module provides optimized tile rendering with caching and dirty rectangle
tracking to significantly improve rendering performance while maintaining
backward compatibility with the existing rendering system.
"""

from typing import Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum, auto
import tcod.libtcodpy as libtcod

from fov_functions import map_is_in_fov


class TileRenderState(Enum):
    """Enumeration of possible tile rendering states."""
    UNEXPLORED = auto()
    EXPLORED_WALL = auto()
    EXPLORED_FLOOR = auto()
    VISIBLE_WALL = auto()
    VISIBLE_FLOOR = auto()


@dataclass
class TileCache:
    """Cache entry for a single tile's rendering state."""
    render_state: TileRenderState
    last_fov_frame: int
    needs_redraw: bool = True
    
    def __post_init__(self):
        """Ensure needs_redraw is properly initialized."""
        if not hasattr(self, 'needs_redraw'):
            self.needs_redraw = True


class OptimizedTileRenderer:
    """Optimized tile renderer with caching and dirty rectangle tracking.
    
    This class provides significant performance improvements for tile rendering
    by caching tile states and only redrawing tiles that have actually changed.
    It maintains full backward compatibility with the existing render_all() function.
    
    Key optimizations:
    - Tile state caching to avoid redundant FOV and tile checks
    - Dirty rectangle tracking to minimize console operations
    - Batch rendering for better performance
    - Smart FOV change detection
    
    Attributes:
        tile_cache (Dict): Cache of tile rendering states
        dirty_tiles (Set): Set of tiles that need redrawing
        last_fov_frame (int): Frame counter for FOV change detection
        frame_counter (int): Current frame number
        map_width (int): Width of the cached map
        map_height (int): Height of the cached map
        optimization_stats (Dict): Performance statistics
    """
    
    def __init__(self):
        """Initialize the optimized tile renderer."""
        self.tile_cache: Dict[Tuple[int, int], TileCache] = {}
        self.dirty_tiles: Set[Tuple[int, int]] = set()
        self.last_fov_frame = -1
        self.frame_counter = 0
        self.map_width = 0
        self.map_height = 0
        self.first_render = True  # Force full redraw on first render
        
        # Performance statistics
        self.optimization_stats = {
            'total_frames': 0,
            'tiles_cached': 0,
            'tiles_redrawn': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'fov_changes': 0,
            'full_redraws': 0,
        }
    
    def render_tiles_optimized(
        self,
        con,
        game_map,
        fov_map,
        colors: Dict[str, Any],
        force_full_redraw: bool = False,
        camera=None
    ) -> None:
        """Render map tiles with optimization caching and camera support.
        
        This is a drop-in replacement for the tile rendering portion of render_all()
        that provides significant performance improvements through caching.
        
        Args:
            con: Console to render to
            game_map: Game map containing tile data
            fov_map: Field of view map for visibility checks
            colors: Color configuration dictionary
            force_full_redraw: Whether to force redrawing all tiles
            camera: Camera for viewport scrolling (optional, defaults to no offset)
        """
        self.frame_counter += 1
        self.optimization_stats['total_frames'] += 1
        
        # Check if map dimensions changed (need full cache rebuild)
        if (game_map.width != self.map_width or 
            game_map.height != self.map_height):
            self._rebuild_cache(game_map.width, game_map.height)
            force_full_redraw = True
        
        # Detect FOV changes
        fov_changed = self._detect_fov_change(fov_map)
        if fov_changed:
            self.optimization_stats['fov_changes'] += 1
            force_full_redraw = True
        
        # Force full redraw on first render or when explicitly requested
        if force_full_redraw or self.first_render:
            self.optimization_stats['full_redraws'] += 1
            self._render_all_tiles(con, game_map, fov_map, colors, camera)
            self.first_render = False  # Clear first render flag
        else:
            self._render_dirty_tiles(con, game_map, fov_map, colors, camera)
        
        # Clear dirty tiles after rendering
        self.dirty_tiles.clear()
    
    def _rebuild_cache(self, width: int, height: int) -> None:
        """Rebuild the tile cache for a new map size.
        
        Args:
            width: New map width
            height: New map height
        """
        self.tile_cache.clear()
        self.dirty_tiles.clear()
        self.map_width = width
        self.map_height = height
        
        # Mark all tiles as needing redraw
        for y in range(height):
            for x in range(width):
                self.dirty_tiles.add((x, y))
    
    def _detect_fov_change(self, fov_map) -> bool:
        """Detect if the FOV has changed since last frame.
        
        Args:
            fov_map: Current FOV map
            
        Returns:
            bool: True if FOV has changed
        """
        # Simple heuristic: assume FOV changed if we don't have a cached frame
        # In a more sophisticated implementation, we could hash the FOV data
        current_frame = self.frame_counter
        if current_frame != self.last_fov_frame + 1:
            self.last_fov_frame = current_frame
            return True
        
        self.last_fov_frame = current_frame
        return False
    
    def _render_all_tiles(
        self,
        con,
        game_map,
        fov_map,
        colors: Dict[str, Any],
        camera=None
    ) -> None:
        """Render all tiles and update cache.
        
        Args:
            con: Console to render to
            game_map: Game map containing tile data
            fov_map: Field of view map for visibility checks
            colors: Color configuration dictionary
            camera: Camera for viewport scrolling (optional)
        """
        # Determine which tiles to render based on camera viewport
        if camera:
            # Only render tiles visible in viewport
            start_x, start_y, end_x, end_y = camera.get_viewport_bounds()
            # Clamp to map boundaries
            start_x = max(0, start_x)
            start_y = max(0, start_y)
            end_x = min(game_map.width, end_x)
            end_y = min(game_map.height, end_y)
        else:
            # No camera, render entire map
            start_x, start_y = 0, 0
            end_x, end_y = game_map.width, game_map.height
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                self._render_tile(con, x, y, game_map, fov_map, colors, update_cache=True, camera=camera)
    
    def _render_dirty_tiles(
        self,
        con,
        game_map,
        fov_map,
        colors: Dict[str, Any],
        camera=None
    ) -> None:
        """Render only tiles marked as dirty.
        
        Args:
            con: Console to render to
            game_map: Game map containing tile data
            fov_map: Field of view map for visibility checks
            colors: Color configuration dictionary
            camera: Camera for viewport scrolling (optional)
        """
        for x, y in self.dirty_tiles:
            if 0 <= x < game_map.width and 0 <= y < game_map.height:
                # Skip tiles outside viewport if camera is active
                if camera and not camera.is_in_viewport(x, y):
                    continue
                self._render_tile(con, x, y, game_map, fov_map, colors, update_cache=True, camera=camera)
        
        self.optimization_stats['tiles_redrawn'] += len(self.dirty_tiles)
    
    def _render_tile(
        self,
        con,
        x: int,
        y: int,
        game_map,
        fov_map,
        colors: Dict[str, Any],
        update_cache: bool = True,
        camera=None
    ) -> None:
        """Render a single tile and optionally update cache.
        
        Args:
            con: Console to render to
            x: Tile X coordinate (world space)
            y: Tile Y coordinate (world space)
            game_map: Game map containing tile data
            fov_map: Field of view map for visibility checks
            colors: Color configuration dictionary
            update_cache: Whether to update the tile cache
            camera: Camera for viewport scrolling (optional)
        """
        # Translate world coordinates to viewport coordinates using camera
        if camera:
            # Check if tile is in viewport
            if not camera.is_in_viewport(x, y):
                return  # Tile is outside viewport, don't render
            
            # Translate to viewport coordinates
            viewport_x, viewport_y = camera.world_to_viewport(x, y)
        else:
            # No camera, use world coordinates directly (backward compatibility)
            viewport_x, viewport_y = x, y
        
        # Get current tile state
        visible = map_is_in_fov(fov_map, x, y)
        wall = game_map.tiles[x][y].block_sight
        explored = game_map.tiles[x][y].explored
        
        # Check if reveal_map is enabled (treat explored tiles as visible)
        from config.testing_config import get_testing_config
        config = get_testing_config()
        
        # DEBUG: Log first render to verify reveal_map config
        if not hasattr(self, '_logged_reveal_map'):
            self._logged_reveal_map = True
            print(f">>> REVEAL_MAP RENDERER: config.reveal_map = {config.reveal_map}")
        
        if config.reveal_map and explored:
            visible = True
        
        # Determine render state
        if visible:
            render_state = TileRenderState.VISIBLE_WALL if wall else TileRenderState.VISIBLE_FLOOR
            # Mark as explored when visible
            game_map.tiles[x][y].explored = True
        elif explored:
            render_state = TileRenderState.EXPLORED_WALL if wall else TileRenderState.EXPLORED_FLOOR
        else:
            render_state = TileRenderState.UNEXPLORED
        
        # Check cache for optimization
        cache_key = (x, y)
        cached_tile = self.tile_cache.get(cache_key)
        
        if cached_tile and cached_tile.render_state == render_state and not cached_tile.needs_redraw:
            self.optimization_stats['cache_hits'] += 1
            return  # No need to redraw
        
        self.optimization_stats['cache_misses'] += 1
        
        # Render the tile at viewport coordinates
        if render_state == TileRenderState.VISIBLE_WALL:
            libtcod.console_set_char_background(
                con, viewport_x, viewport_y, colors.get("light_wall"), libtcod.BKGND_SET
            )
        elif render_state == TileRenderState.VISIBLE_FLOOR:
            libtcod.console_set_char_background(
                con, viewport_x, viewport_y, colors.get("light_ground"), libtcod.BKGND_SET
            )
        elif render_state == TileRenderState.EXPLORED_WALL:
            libtcod.console_set_char_background(
                con, viewport_x, viewport_y, colors.get("dark_wall"), libtcod.BKGND_SET
            )
        elif render_state == TileRenderState.EXPLORED_FLOOR:
            libtcod.console_set_char_background(
                con, viewport_x, viewport_y, colors.get("dark_ground"), libtcod.BKGND_SET
            )
        # UNEXPLORED tiles are not rendered (remain black/default)
        
        # Render ground hazard overlay if present
        visible = render_state in (TileRenderState.VISIBLE_WALL, TileRenderState.VISIBLE_FLOOR)
        from render_functions import _render_hazard_at_tile
        _render_hazard_at_tile(con, game_map, x, y, viewport_x, viewport_y, visible, colors)
        
        # Update cache
        if update_cache:
            self.tile_cache[cache_key] = TileCache(
                render_state=render_state,
                last_fov_frame=self.frame_counter,
                needs_redraw=False
            )
            self.optimization_stats['tiles_cached'] += 1
    
    def mark_tile_dirty(self, x: int, y: int) -> None:
        """Mark a specific tile as needing redraw.
        
        Args:
            x: Tile X coordinate
            y: Tile Y coordinate
        """
        self.dirty_tiles.add((x, y))
        cache_key = (x, y)
        if cache_key in self.tile_cache:
            self.tile_cache[cache_key].needs_redraw = True
    
    def mark_area_dirty(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Mark a rectangular area as needing redraw.
        
        Args:
            x1: Left boundary
            y1: Top boundary
            x2: Right boundary
            y2: Bottom boundary
        """
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for x in range(min(x1, x2), max(x1, x2) + 1):
                self.mark_tile_dirty(x, y)
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get performance optimization statistics.
        
        Returns:
            Dict containing performance metrics
        """
        stats = self.optimization_stats.copy()
        if stats['total_frames'] > 0:
            stats['cache_hit_rate'] = stats['cache_hits'] / (stats['cache_hits'] + stats['cache_misses'])
            stats['avg_tiles_per_frame'] = stats['tiles_redrawn'] / stats['total_frames']
        else:
            stats['cache_hit_rate'] = 0.0
            stats['avg_tiles_per_frame'] = 0.0
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset performance statistics."""
        for key in self.optimization_stats:
            self.optimization_stats[key] = 0


# Global instance for backward compatibility
_global_tile_renderer = OptimizedTileRenderer()


def render_tiles_optimized(con, game_map, fov_map, colors, force_full_redraw=False, camera=None):
    """Global function for optimized tile rendering with camera support.
    
    This provides a simple interface for the optimized tile renderer that can
    be used as a drop-in replacement for the tile rendering portion of render_all().
    
    Args:
        con: Console to render to
        game_map: Game map containing tile data
        fov_map: Field of view map for visibility checks
        colors: Color configuration dictionary
        force_full_redraw: Whether to force redrawing all tiles
        camera: Camera for viewport scrolling (optional, defaults to no offset)
    """
    _global_tile_renderer.render_tiles_optimized(
        con, game_map, fov_map, colors, force_full_redraw, camera
    )


def get_tile_optimization_stats():
    """Get tile rendering optimization statistics.
    
    Returns:
        Dict containing performance metrics
    """
    return _global_tile_renderer.get_optimization_stats()


def reset_tile_optimization_stats():
    """Reset tile rendering optimization statistics."""
    _global_tile_renderer.reset_stats()


def reset_tile_renderer():
    """Reset the global tile renderer to initial state.
    
    This is useful for testing to ensure a clean state between tests.
    """
    global _global_tile_renderer
    _global_tile_renderer = OptimizedTileRenderer()


def mark_tile_dirty(x, y):
    """Mark a specific tile as needing redraw.
    
    Args:
        x: Tile X coordinate
        y: Tile Y coordinate
    """
    _global_tile_renderer.mark_tile_dirty(x, y)


def mark_area_dirty(x1, y1, x2, y2):
    """Mark a rectangular area as needing redraw.
    
    Args:
        x1: Left boundary
        y1: Top boundary
        x2: Right boundary
        y2: Bottom boundary
    """
    _global_tile_renderer.mark_area_dirty(x1, y1, x2, y2)
