"""Mural message manager for unique per-floor mural text assignment.

This module manages the selection and tracking of mural messages across different
dungeon floors to ensure diversity and prevent repetition of the same message on
a single floor.

Features:
- Track used mural messages per floor
- Ensure unique message selection within a floor
- Allow repeats only after all messages in pool are exhausted
- Reset tracking on floor transitions
"""

from typing import Dict, List, Optional, Set, Tuple
from logger_config import get_logger
from config.murals_registry import MuralsRegistry

logger = get_logger(__name__)


class MuralManager:
    """Manages mural message selection and uniqueness per floor.
    
    Tracks which mural messages have been used on each floor to ensure
    players see variety when exploring. Once a floor's message pool is
    exhausted, messages can repeat on subsequent playthroughs.
    """
    
    def __init__(self):
        """Initialize mural manager."""
        self.used_messages_per_floor: Dict[int, Set[str]] = {}
        self.mural_registry = MuralsRegistry()
        self.current_floor = 1
        
    def set_current_floor(self, floor_number: int) -> None:
        """Update current floor and initialize tracking if needed.
        
        Args:
            floor_number: The current dungeon floor
        """
        self.current_floor = floor_number
        if floor_number not in self.used_messages_per_floor:
            self.used_messages_per_floor[floor_number] = set()
    
    def get_unique_mural(self, depth: int) -> Tuple[Optional[str], Optional[str]]:
        """Get a unique mural message for this floor.
        
        Selects a mural that hasn't been used yet on this floor. If all
        available murals have been used, resets the pool and allows repeats.
        
        Args:
            depth: Current dungeon level
            
        Returns:
            Tuple of (mural_text, mural_id) or (None, None) if no mural found
        """
        # Ensure floor tracking is initialized
        if self.current_floor not in self.used_messages_per_floor:
            self.used_messages_per_floor[self.current_floor] = set()
        
        # Get all murals available for this depth
        available_murals = self.mural_registry.get_all_murals_for_depth(depth)
        
        if not available_murals:
            logger.warning(f"No murals available for depth {depth}")
            return (None, None)
        
        # Filter out already-used messages on this floor
        unused_murals = [
            mural for mural in available_murals 
            if mural[1] not in self.used_messages_per_floor[self.current_floor]
        ]
        
        # If all have been used, reset the pool
        if not unused_murals:
            logger.debug(f"All murals used on floor {self.current_floor}, resetting pool")
            self.used_messages_per_floor[self.current_floor].clear()
            unused_murals = available_murals
        
        # Select random unused mural
        import random
        selected_mural = random.choice(unused_murals)
        
        # Mark as used
        self.used_messages_per_floor[self.current_floor].add(selected_mural[1])
        
        logger.debug(f"Selected unique mural {selected_mural[1]} for floor {self.current_floor}")
        return (selected_mural[0], selected_mural[1])
    
    def reset_floor_state(self, floor_number: int) -> None:
        """Clear tracking for a specific floor.
        
        Useful when generating a new floor or clearing history.
        
        Args:
            floor_number: The floor to reset
        """
        if floor_number in self.used_messages_per_floor:
            self.used_messages_per_floor[floor_number].clear()
            logger.debug(f"Reset mural message pool for floor {floor_number}")
    
    def reset_all(self) -> None:
        """Reset all floor tracking."""
        self.used_messages_per_floor.clear()
        logger.debug("Reset all mural message tracking")


# Global instance
_instance: Optional[MuralManager] = None


def get_mural_manager() -> MuralManager:
    """Get or create the singleton mural manager instance.
    
    Returns:
        The global MuralManager instance
    """
    global _instance
    if _instance is None:
        _instance = MuralManager()
    return _instance

