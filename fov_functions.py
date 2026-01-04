"""Field of view calculation functions.

This module handles field of view (FOV) computations using tcod's
modern FOV algorithms. Manages visibility calculations for lighting
and line-of-sight mechanics.

═══════════════════════════════════════════════════════════════════════════════
MODULE CONTRACT: Field of View & Visibility
───────────────────────────────────────────────────────────────────────────────

OWNERSHIP:
  - FOV computation (via tcod)
  - Visibility checks for rendered entities
  - FOV map creation and updates

KEY CONTRACTS:
  - FOV computed via recompute_fov(fov_map, x, y, radius, ...)
  - Visibility checked via fov_map.is_in_fov(x, y)
  - Do NOT reimplement FOV logic in other modules
  - ModernFOVMap provides backward-compatible wrapper around tcod

WHEN CHANGING BEHAVIOR:
  - Update tests/test_golden_path_floor1.py::test_basic_explore_floor1
  - Ensure FOV computation still works after changes
  - Verify visibility checks pass (must see own tile)
  - No reimplementation of FOV elsewhere

SEE ALSO:
  - render_functions.py - FOV rendering (uses this module)
  - fov_functions.ModernFOVMap - FOV map implementation
  - Tests: tests/test_golden_path_floor1.py (FOV verification)
═══════════════════════════════════════════════════════════════════════════════
"""

import numpy as np
import tcod.map


class ModernFOVMap:
    """Compatibility wrapper for modern tcod FOV using numpy arrays.
    
    This class provides a backward-compatible interface that mimics the old
    tcod.map.Map API while using the modern numpy-based FOV calculations.
    """
    
    def __init__(self, transparency_array):
        """Initialize with a transparency array.
        
        Args:
            transparency_array (np.ndarray): 2D boolean array where True = transparent
        """
        self.transparency = transparency_array
        self.visibility = None
        
    def compute_fov(self, x, y, radius, light_walls=True, algorithm=12):
        """Compute FOV and store the result internally.
        
        Args:
            x (int): X coordinate of the viewer
            y (int): Y coordinate of the viewer
            radius (int): Maximum sight radius
            light_walls (bool): Whether walls are lit
            algorithm (int): FOV algorithm to use
        """
        self.visibility = tcod.map.compute_fov(
            self.transparency,
            pov=(x, y),
            radius=radius,
            light_walls=light_walls,
            algorithm=algorithm
        )
        
    def is_in_fov(self, x, y):
        """Check if a position is visible (compatibility method).
        
        Args:
            x (int): X coordinate to check
            y (int): Y coordinate to check
            
        Returns:
            bool: True if position is visible
        """
        if self.visibility is None:
            return False
        return is_visible(self.visibility, x, y)


def initialize_fov(game_map):
    """Initialize a FOV map from a game map for FOV calculations.

    Creates a modern FOV map using numpy arrays with backward compatibility.

    Args:
        game_map (GameMap): The game map to create FOV data from

    Returns:
        ModernFOVMap: FOV map object compatible with old tcod.map.Map interface
    """
    # Create transparency array (True = transparent, False = blocks sight)
    # Use (width, height) to match game_map.tiles[x][y] coordinate system
    transparency = np.zeros((game_map.width, game_map.height), dtype=bool, order="F")
    
    for y in range(game_map.height):
        for x in range(game_map.width):
            transparency[x, y] = not game_map.tiles[x][y].block_sight

    return ModernFOVMap(transparency)


def recompute_fov(fov_map, x, y, radius, light_walls=True, algorithm=12):
    """Recompute field of view from a specific position.

    Args:
        fov_map (ModernFOVMap): FOV map object to update
        x (int): X coordinate of the viewer
        y (int): Y coordinate of the viewer  
        radius (int): Maximum sight radius
        light_walls (bool, optional): Whether walls are lit. Defaults to True.
        algorithm (int, optional): FOV algorithm to use. Defaults to 12 (FOV_RESTRICTIVE).
    """
    fov_map.compute_fov(x, y, radius, light_walls, algorithm)


def is_visible(fov_array, x, y):
    """Check if a position is visible in the field of view.
    
    Args:
        fov_array (np.ndarray): 2D boolean array from recompute_fov()
        x (int): X coordinate to check
        y (int): Y coordinate to check
        
    Returns:
        bool: True if position is visible, False otherwise
    """
    if fov_array is None:
        return False
    
    # Check bounds - fov_array is (width, height) to match game coordinate system
    if x < 0 or x >= fov_array.shape[0] or y < 0 or y >= fov_array.shape[1]:
        return False
        
    return bool(fov_array[x, y])


# Compatibility function for libtcod.map_is_in_fov()
def map_is_in_fov(fov_map, x, y):
    """Compatibility function replacing libtcod.map_is_in_fov().
    
    Args:
        fov_map (ModernFOVMap): FOV map object
        x (int): X coordinate to check
        y (int): Y coordinate to check
        
    Returns:
        bool: True if position is visible, False otherwise
    """
    if hasattr(fov_map, 'is_in_fov'):
        return fov_map.is_in_fov(x, y)
    else:
        # Fallback for numpy arrays
        return is_visible(fov_map, x, y)


def has_line_of_sight(game_map, x1: int, y1: int, x2: int, y2: int) -> bool:
    """Check if there's an unobstructed line of sight between two points.
    
    Uses Bresenham ray tracing to check if any tile along the line blocks sight.
    This is a pure geometry check that does NOT require a pre-computed FOV map.
    
    Use this for on-demand LOS checks (e.g., Lich Soul Bolt) when:
    - fov_map is None (headless/scenario mode)
    - You need point-to-point visibility without caching
    
    Args:
        game_map: GameMap with tiles that have block_sight attribute
        x1 (int): X coordinate of origin
        y1 (int): Y coordinate of origin
        x2 (int): X coordinate of target
        y2 (int): Y coordinate of target
        
    Returns:
        bool: True if line of sight is clear, False if blocked
    """
    from tcod.los import bresenham
    
    # Same tile is always visible
    if x1 == x2 and y1 == y2:
        return True
    
    # Get ray path using Bresenham's line algorithm
    path_array = bresenham((x1, y1), (x2, y2))
    
    # Check each tile along the path (excluding start and end points)
    # We skip the first tile (origin) and last tile (target) - we only care about obstructions
    for i in range(1, len(path_array) - 1):
        px, py = int(path_array[i][0]), int(path_array[i][1])
        
        # Bounds check
        if px < 0 or px >= game_map.width or py < 0 or py >= game_map.height:
            return False  # Out of bounds blocks sight
        
        # Check if tile blocks sight
        if game_map.tiles[px][py].block_sight:
            return False
    
    return True
