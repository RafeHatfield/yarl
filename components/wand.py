"""Wand component for multi-charge magic items.

Wands are reusable magic items that have charges. Each use consumes one charge.
When a matching scroll is picked up, it automatically recharges the wand by 1.
Unlike scrolls, wands can have unlimited charges (no maximum).
"""


class Wand:
    """Component for wand items with charge tracking.
    
    Wands are multi-use versions of scrolls. They have charges that are consumed
    on use and can be recharged by picking up matching scrolls.
    
    Attributes:
        spell_type (str): The type of spell this wand casts (e.g., "fireball")
        charges (int): Current number of charges
        owner (Entity): The entity that owns this component
    """
    
    def __init__(self, spell_type: str, charges: int = 1):
        """Initialize a Wand component.
        
        Args:
            spell_type (str): The spell this wand casts (matches scroll name)
            charges (int, optional): Starting charges. Defaults to 1.
        """
        self.spell_type = spell_type
        self.charges = charges
        self.owner = None
    
    def use_charge(self) -> bool:
        """Consume one charge from the wand.
        
        Returns:
            bool: True if charge was consumed, False if wand is empty
        """
        if self.charges > 0:
            self.charges -= 1
            return True
        return False
    
    def add_charge(self, amount: int = 1) -> None:
        """Add charges to the wand.
        
        Args:
            amount (int, optional): Number of charges to add. Defaults to 1.
        """
        self.charges += amount
    
    def is_empty(self) -> bool:
        """Check if the wand has any charges left.
        
        Returns:
            bool: True if wand has no charges
        """
        return self.charges <= 0
    
    def get_display_name(self) -> str:
        """Get the display name with charge count.
        
        Returns:
            str: Wand name with charge count, e.g., "Wand of Fireball (5)"
        """
        if self.owner and hasattr(self.owner, 'name'):
            base_name = self.owner.name
            return f"{base_name} ({self.charges})"
        return f"Wand ({self.charges})"

