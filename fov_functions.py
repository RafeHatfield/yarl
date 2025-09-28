"""Field of view calculation functions.

This module handles field of view (FOV) computations using tcod's
modern FOV algorithms. Manages visibility calculations for lighting
and line-of-sight mechanics.
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
