"""Field of view calculation functions.

This module handles field of view (FOV) computations using tcod's
built-in FOV algorithms. Manages visibility calculations for lighting
and line-of-sight mechanics.
"""

import tcod as libtcod


def initialize_fov(game_map):
    """Initialize a field of view map from a game map.

    Creates a tcod FOV map with tile properties copied from the game map.

    Args:
        game_map (GameMap): The game map to create FOV data from

    Returns:
        FOV map: tcod FOV map object for visibility calculations
    """
    fov_map = libtcod.map_new(game_map.width, game_map.height)

    for y in range(game_map.height):
        for x in range(game_map.width):
            libtcod.map_set_properties(
                fov_map,
                x,
                y,
                not game_map.tiles[x][y].block_sight,
                not game_map.tiles[x][y].blocked,
            )

    return fov_map


def recompute_fov(fov_map, x, y, radius, light_walls=True, algorithm=0):
    """Recompute field of view from a specific position.

    Args:
        fov_map: tcod FOV map object
        x (int): X coordinate of the viewer
        y (int): Y coordinate of the viewer
        radius (int): Maximum sight radius
        light_walls (bool, optional): Whether walls are lit. Defaults to True.
        algorithm (int, optional): FOV algorithm to use. Defaults to 0.
    """
    libtcod.map_compute_fov(fov_map, x, y, radius, light_walls, algorithm)
