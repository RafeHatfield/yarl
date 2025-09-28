class Level:
    """Component that manages character level and experience progression.

    This component tracks experience points, current level, and handles
    level-up calculations with configurable XP requirements.

    Attributes:
        current_level (int): Current character level
        current_xp (int): Current experience points
        level_up_base (int): Base XP required for first level up
        level_up_factor (int): Additional XP per level for scaling
        owner (Entity): The entity that owns this component
    """

    def __init__(
        self, current_level=1, current_xp=0, level_up_base=200, level_up_factor=150
    ):
        """Initialize a Level component.

        Args:
            current_level (int, optional): Starting level. Defaults to 1.
            current_xp (int, optional): Starting XP. Defaults to 0.
            level_up_base (int, optional): Base XP for level 2. Defaults to 200.
            level_up_factor (int, optional): XP scaling per level. Defaults to 150.
        """
        self.current_level = current_level
        self.current_xp = current_xp
        self.level_up_base = level_up_base
        self.level_up_factor = level_up_factor
        self.owner = None  # Will be set by Entity when component is registered

    @property
    def experience_to_next_level(self):
        """Calculate XP required for the next level.

        Returns:
            int: Experience points needed to reach the next level
        """
        return self.level_up_base + self.current_level * self.level_up_factor

    def add_xp(self, xp):
        """Add experience points and check for level up.

        Adds XP to the current total and automatically levels up
        if enough XP has been gained.

        Args:
            xp (int): Experience points to add

        Returns:
            bool: True if a level up occurred, False otherwise
        """
        self.current_xp += xp

        if self.current_xp > self.experience_to_next_level:
            self.current_xp -= self.experience_to_next_level
            self.current_level += 1

            return True
        else:
            return False
