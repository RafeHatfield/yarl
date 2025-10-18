"""Contains the class for handling tiles on the map"""


class Tile:
    """
    A tile on a map. It may or may not be blocked, and may or may not block sight.
    
    Attributes:
        blocked: Whether the tile blocks movement
        block_sight: Whether the tile blocks line of sight
        explored: Whether the player has seen this tile
        light: Custom color when visible (None = use default)
        dark: Custom color when explored but not visible (None = use default)
    """

    def __init__(self, blocked, block_sight=None, light=None, dark=None):
        self.blocked = blocked

        # By default, if a tile is blocked, it also blocks sight
        if block_sight is None:
            block_sight = blocked

        self.block_sight = block_sight
        self.explored = False
        
        # Custom colors for special tiles (e.g. vault walls)
        self.light = light  # Color when visible
        self.dark = dark    # Color when explored but not visible
