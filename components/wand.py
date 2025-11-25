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
        
        Note: Charges = -1 means infinite charges (special case for portal wand)
        """
        # Special case: charges = -1 means infinite (don't decrement)
        if self.charges == -1:
            return True  # Infinite charges, always has charges
        
        # Normal case: finite charges
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
        
        Note: Charges = -1 means infinite charges (never empty)
        """
        # Special case: charges = -1 means infinite (never empty)
        if self.charges == -1:
            return False  # Infinite charges
        
        # Normal case: finite charges
        return self.charges <= 0
    
    def get_display_name(self, compact: bool = False) -> str:
        """Get the display name with charge count and visual indicator.
        
        Args:
            compact: If True, return abbreviated name for sidebar (e.g., "W.Fireball⚡5")
        
        Returns:
            str: Wand name with charge count and visual indicator
        """
        # Visual charge indicator based on charge level
        if self.charges == -1:
            # Special case: infinite charges (for non-portal wands that might use this)
            indicator = "∞"  # Infinity symbol
            display_charges = "∞"
        elif self.charges == 0:
            indicator = "○"  # Empty circle - no charges
            display_charges = "0"
        elif self.charges == 1:
            # Single charge wands (like Wand of Portals) show as ready/full
            indicator = "●"  # Full circle - ready to use
            display_charges = "1"
        elif self.charges <= 2:
            indicator = "◐"  # Half-filled - low charges
            display_charges = str(self.charges)
        elif self.charges <= 4:
            indicator = "◕"  # Three-quarter filled - medium charges
            display_charges = str(self.charges)
        else:
            indicator = "●"  # Full circle - high charges
            display_charges = str(self.charges)
        
        if self.owner and hasattr(self.owner, 'name'):
            base_name = self.owner.name
            
            if compact:
                # Abbreviate for sidebar: "Wand of Fireball" -> "W.Fireball"
                compact_name = base_name.replace(" of ", " ").replace("Wand ", "W.")
                return f"{compact_name}{indicator}{display_charges}"
            else:
                # Full name for tooltips/inventory: "Wand of Fireball ● 5"
                return f"{base_name} {indicator} {display_charges}"
        
        return f"Wand {indicator} {display_charges}" if not compact else f"W.{indicator}{display_charges}"

