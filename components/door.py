"""Door component for corridor connections.

This module provides the Door component that manages door state, locking, and
discovery. Doors can be:
- Open/Closed: Can be traversed when open
- Locked: Requires a key with matching tag to unlock
- Secret: Hidden appearance until discovered via search or adjacency

Doors maintain logical connectivity while controlling passage physically.
"""

from typing import Optional, TYPE_CHECKING
from logger_config import get_logger

if TYPE_CHECKING:
    from entity import Entity

logger = get_logger(__name__)


class Door:
    """Represents a door blocking a corridor connection.
    
    A door can be:
    - Closed: blocks movement, can be opened/unlocked
    - Locked: requires a key, can be unlocked if player has matching key
    - Secret: appears as a wall until discovered
    - Open: allows passage
    
    Attributes:
        owner: The Entity that owns this door
        is_closed: Whether the door is closed (blocks movement when True)
        is_locked: Whether the door is locked (cannot open without key)
        is_secret: Whether the door appears as a wall until discovered
        is_discovered: Whether the secret door has been found
        key_tag: Tag that keys must have to unlock this door
        search_dc: DC for search checks to discover (if secret)
    """
    
    def __init__(
        self,
        key_tag: str = "iron_key",
        is_locked: bool = False,
        is_secret: bool = False,
        search_dc: int = 12
    ):
        """Initialize a Door component.
        
        Args:
            key_tag: Tag required on keys to unlock (default "iron_key")
            is_locked: Whether door starts locked (default False)
            is_secret: Whether door appears as wall until discovered (default False)
            search_dc: Difficulty class for discovering secret doors (default 12)
        """
        self.owner: Optional['Entity'] = None
        self.is_closed: bool = True  # Doors start closed
        self.is_locked: bool = is_locked
        self.is_secret: bool = is_secret
        self.is_discovered: bool = not is_secret  # Secret doors start undiscovered
        self.key_tag: str = key_tag
        self.search_dc: int = search_dc
    
    def open(self) -> bool:
        """Attempt to open the door.
        
        Returns:
            True if door successfully opened, False if locked
        """
        if self.is_locked:
            return False
        
        self.is_closed = False
        if self.owner:
            logger.debug(f"Door at ({self.owner.x}, {self.owner.y}) opened")
        return True
    
    def close(self) -> None:
        """Close the door."""
        self.is_closed = True
        if self.owner:
            logger.debug(f"Door at ({self.owner.x}, {self.owner.y}) closed")
    
    def unlock(self) -> bool:
        """Unlock the door (called when player uses matching key).
        
        Returns:
            True if successfully unlocked, False if not locked
        """
        if not self.is_locked:
            return False
        
        self.is_locked = False
        if self.owner:
            logger.debug(f"Door at ({self.owner.x}, {self.owner.y}) unlocked")
        return True
    
    def discover(self) -> bool:
        """Discover a secret door (make it visible).
        
        Returns:
            True if discovered, False if not secret
        """
        if not self.is_secret:
            return False
        
        self.is_discovered = True
        if self.owner:
            logger.debug(f"Secret door at ({self.owner.x}, {self.owner.y}) discovered")
        return True
    
    def blocks_movement(self) -> bool:
        """Check if this door blocks movement.
        
        A door blocks movement if:
        - It's closed AND not yet discovered (secret), OR
        - It's closed AND locked
        
        Open doors never block movement.
        Undiscovered secret doors appear as walls.
        
        Returns:
            True if door blocks movement, False otherwise
        """
        # Open doors don't block
        if not self.is_closed:
            return False
        
        # Closed secret doors that haven't been discovered block as walls
        if self.is_secret and not self.is_discovered:
            return True
        
        # Discovered closed doors block, but can be opened/unlocked
        return True
    
    def can_lock_with_key(self, key_tag: str) -> bool:
        """Check if a key with given tag can unlock this door.
        
        Args:
            key_tag: Tag to check against door's required key_tag
            
        Returns:
            True if key matches and door is locked, False otherwise
        """
        return self.is_locked and key_tag == self.key_tag

