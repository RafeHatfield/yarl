class Rect:
    """A rectangular area on the game map.

    Used for room generation and collision detection in dungeon creation.
    Stores coordinates as top-left (x1, y1) and bottom-right (x2, y2).

    Attributes:
        x1 (int): Left edge x coordinate
        y1 (int): Top edge y coordinate
        x2 (int): Right edge x coordinate
        y2 (int): Bottom edge y coordinate
    """

    def __init__(self, x, y, w, h, is_vault=False):
        """Initialize a Rectangle.

        Args:
            x (int): Left edge x coordinate
            y (int): Top edge y coordinate
            w (int): Width of the rectangle
            h (int): Height of the rectangle
            is_vault (bool): Whether this room is a treasure vault
        """
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
        self.is_vault = is_vault

    def center(self):
        """Calculate the center point of the rectangle.

        Returns:
            tuple: (center_x, center_y) coordinates of the rectangle center
        """
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)
        return (center_x, center_y)

    def intersect(self, other):
        """Check if this rectangle intersects with another rectangle.

        Args:
            other (Rect): The other rectangle to check intersection with

        Returns:
            bool: True if the rectangles intersect, False otherwise
        """
        # returns true if this rectangle intersects with another one
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )
