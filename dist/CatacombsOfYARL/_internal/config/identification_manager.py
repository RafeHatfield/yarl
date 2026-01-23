"""Global Item Identification Manager.

This module manages which item TYPES have been identified in the current game.
Unlike per-instance identification, this tracks at the type level: when you identify
one healing potion, ALL healing potions become identified.

This is the traditional roguelike behavior:
- Identify one "cyan potion" → discover it's a "healing potion"
- All future "cyan potions" are now known to be "healing potions"
- Next game, "cyan potion" might be something different (randomized per-game)
"""

from typing import Set, Dict, Any
import logging

logger = logging.getLogger(__name__)


class IdentificationManager:
    """Manages global identification state for item types.
    
    This class tracks which item types (e.g., "healing_potion", "fireball_scroll")
    have been identified in the current game session. When one instance of an item
    type is identified, all instances of that type become identified.
    
    Also tracks which types are DECIDED to be unidentified for consistency.
    
    Attributes:
        _identified_types: Set of item type names that have been identified
        _unidentified_types: Set of item type names that are decided to be unidentified
    """
    
    def __init__(self):
        """Initialize an empty identification registry."""
        self._identified_types: Set[str] = set()
        self._unidentified_types: Set[str] = set()
    
    def is_identified(self, item_type: str) -> bool:
        """Check if an item type has been identified.
        
        Args:
            item_type: Internal item type name (e.g., "healing_potion")
        
        Returns:
            bool: True if this type has been identified, False otherwise
        """
        return item_type in self._identified_types
    
    def is_unidentified(self, item_type: str) -> bool:
        """Check if an item type has been decided to be unidentified.
        
        Args:
            item_type: Internal item type name (e.g., "healing_potion")
        
        Returns:
            bool: True if this type is decided to be unidentified, False otherwise
        """
        return item_type in self._unidentified_types
    
    def has_decision(self, item_type: str) -> bool:
        """Check if an identification decision has been made for this type.
        
        Args:
            item_type: Internal item type name
        
        Returns:
            bool: True if a decision (identified or unidentified) has been made
        """
        return item_type in self._identified_types or item_type in self._unidentified_types
    
    def identify_type(self, item_type: str) -> bool:
        """Mark an item type as identified.
        
        Args:
            item_type: Internal item type name to identify
        
        Returns:
            bool: True if this was newly identified, False if already identified
        """
        if item_type in self._identified_types:
            return False  # Already identified
        
        # Remove from unidentified if it was there
        self._unidentified_types.discard(item_type)
        
        self._identified_types.add(item_type)
        logger.info(f"Item type identified: {item_type}")
        return True  # Newly identified
    
    def mark_unidentified(self, item_type: str) -> None:
        """Mark an item type as decided to be unidentified.
        
        This is used during pre-identification to record that a type
        rolled "unidentified", so future items of this type are also unidentified.
        
        Args:
            item_type: Internal item type name to mark as unidentified
        """
        if item_type not in self._identified_types:
            self._unidentified_types.add(item_type)
            logger.info(f"Item type marked as unidentified: {item_type}")
    
    def get_identified_types(self) -> Set[str]:
        """Get a copy of all identified item types.
        
        Returns:
            Set of identified item type names
        """
        return self._identified_types.copy()
    
    def set_identified_types(self, identified_types: Set[str]) -> None:
        """Set the identified types (for loading saves).
        
        Args:
            identified_types: Set of item type names to mark as identified
        """
        self._identified_types = set(identified_types)
        logger.info(f"Loaded {len(identified_types)} identified types from save")
    
    def reset(self) -> None:
        """Clear all identified and unidentified types (for new game)."""
        self._identified_types.clear()
        self._unidentified_types.clear()
        logger.info("Identification registry reset")
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for saving.
        
        Returns:
            Dictionary containing identification state
        """
        return {
            "identified_types": list(self._identified_types),
            "unidentified_types": list(self._unidentified_types)
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Deserialize from loaded save.
        
        Args:
            data: Dictionary containing identification state
        """
        identified_list = data.get("identified_types", [])
        self._identified_types = set(identified_list)
        
        unidentified_list = data.get("unidentified_types", [])
        self._unidentified_types = set(unidentified_list)
        
        logger.info(f"Loaded {len(self._identified_types)} identified types, "
                   f"{len(self._unidentified_types)} unidentified types")


# Global singleton instance
_identification_manager: IdentificationManager = None


def get_identification_manager() -> IdentificationManager:
    """Get the global identification manager singleton.
    
    Returns:
        The global IdentificationManager instance
    """
    global _identification_manager
    if _identification_manager is None:
        _identification_manager = IdentificationManager()
    return _identification_manager


def reset_identification_manager() -> IdentificationManager:
    """Reset the global identification manager (for new game).
    
    Returns:
        The newly reset IdentificationManager instance
    """
    global _identification_manager
    _identification_manager = IdentificationManager()
    return _identification_manager

