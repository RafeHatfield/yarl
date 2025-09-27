"""Stairs component for level transitions.

This module defines the Stairs component which marks entities
as stairs that can transport the player to different dungeon levels.
"""


class Stairs:
    """Component marking an entity as stairs to another floor.

    Attributes:
        floor (int): The floor number these stairs lead to
    """

    def __init__(self, floor):
        """Initialize Stairs component.

        Args:
            floor (int): The floor number these stairs lead to
        """
        self.floor = floor
