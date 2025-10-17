"""Secret Door System for Hidden Passages.

This module provides the secret door mechanic that creates discovery moments
without tedious wall-searching. Secret doors:
- Appear as normal walls until revealed
- 75% chance to reveal when player is adjacent (passive)
- Can be revealed by room-wide search action
- Ring of Searching gives 100% reveal within 3 tiles
- Provide visual hints before discovery

Example:
    >>> door = SecretDoor(10, 12, connects=(room_a, room_b))
    >>> if door.try_reveal(player):
    ...     # Door revealed! Player discovered it.
"""

from typing import Tuple, Optional, List, Dict, Any, TYPE_CHECKING
import random

if TYPE_CHECKING:
    from entity import Entity


class SecretDoor:
    """A hidden door that connects two rooms or areas.
    
    Secret doors are a core exploration mechanic that rewards attentive players
    without requiring tedious wall-checking. They use a generous passive reveal
    chance to avoid player frustration.
    
    Attributes:
        x: X coordinate of the door
        y: Y coordinate of the door
        revealed: Whether the door has been discovered
        reveal_chance: Base chance to reveal when adjacent (default 0.75)
        connected_rooms: Tuple of room IDs this door connects
        hint_given: Whether a discovery hint has been shown
    """
    
    def __init__(
        self,
        x: int,
        y: int,
        connected_rooms: Tuple[int, int] = (0, 0),
        reveal_chance: float = 0.75
    ):
        """Initialize a secret door.
        
        Args:
            x: X coordinate
            y: Y coordinate
            connected_rooms: Tuple of (room_a_id, room_b_id)
            reveal_chance: Base passive reveal chance (0.0-1.0)
        """
        self.x = x
        self.y = y
        self.revealed = False
        self.reveal_chance = reveal_chance
        self.connected_rooms = connected_rooms
        self.hint_given = False
    
    def try_reveal(self, observer: 'Entity', distance: float = None) -> Dict[str, Any]:
        """Attempt to reveal this secret door to an observer.
        
        Uses distance-based passive reveal chance. Closer = more likely to find.
        
        Args:
            observer: The entity attempting to discover the door (usually player)
            distance: Distance to observer (calculated if not provided)
            
        Returns:
            Dictionary with reveal results and messages
        """
        if self.revealed:
            return {}  # Already revealed
        
        # Calculate distance if not provided
        if distance is None:
            dx = abs(observer.x - self.x)
            dy = abs(observer.y - self.y)
            distance = max(dx, dy)  # Chebyshev distance (grid-based)
        
        # Base reveal chance
        chance = self.reveal_chance
        
        # Distance modifier (adjacent = full chance, 2+ tiles away = reduced)
        if distance <= 1:
            pass  # Full chance
        elif distance == 2:
            chance *= 0.5  # Half chance at 2 tiles
        else:
            chance *= 0.25  # Quarter chance at 3+ tiles
        
        # Check for Ring of Searching (automatic reveal within 3 tiles)
        if hasattr(observer, 'equipment') and observer.equipment:
            from components.component_registry import ComponentType
            from components.ring import RingEffect
            
            rings = [observer.equipment.left_ring, observer.equipment.right_ring]
            for ring_entity in rings:
                if ring_entity and ring_entity.components.has(ComponentType.RING):
                    if ring_entity.ring.ring_effect == RingEffect.SEARCHING:
                        if distance <= 3:
                            chance = 1.0  # Automatic reveal with Ring of Searching
                        break
        
        # Roll for reveal
        if random.random() < chance:
            self.revealed = True
            return {
                "secret_revealed": True,
                "secret_door": self,
                "distance": distance
            }
        
        # Not revealed yet - maybe give a hint
        if not self.hint_given and distance <= 1 and random.random() < 0.5:
            self.hint_given = True
            return {
                "secret_hint": True,
                "secret_door": self
            }
        
        return {}
    
    def reveal_by_search(self) -> bool:
        """Force-reveal this door via room-wide search action.
        
        Returns:
            True if door was newly revealed, False if already revealed
        """
        if not self.revealed:
            self.revealed = True
            return True
        return False
    
    def get_hint_message(self) -> str:
        """Get a randomized hint message for this door.
        
        Returns:
            String hint message for message log
        """
        hints = [
            "You notice a draft coming from the wall...",
            "The stonework here looks slightly different...",
            "Strange scratches mark this section of wall...",
            "A faint breeze flows from cracks in the stone...",
            "The wall here sounds hollow when you move near it...",
            "Odd marks on the floor suggest this wall has been moved before...",
        ]
        
        return random.choice(hints)
    
    def get_reveal_message(self, distance: float) -> str:
        """Get a reveal message based on how the door was found.
        
        Args:
            distance: How far away the player was when revealed
            
        Returns:
            String message for message log
        """
        if distance <= 1:
            return "You discover a secret door!"
        elif distance == 2:
            return "You spot a secret passage nearby!"
        else:
            return "You notice a hidden door in the distance!"
    
    def __repr__(self):
        status = "revealed" if self.revealed else "hidden"
        return f"SecretDoor(x={self.x}, y={self.y}, {status})"


class SecretDoorManager:
    """Manager for all secret doors on a level.
    
    Handles discovery checks, search actions, and door state tracking.
    """
    
    def __init__(self):
        """Initialize an empty door manager."""
        self.doors: List[SecretDoor] = []
    
    def add_door(self, door: SecretDoor) -> None:
        """Add a secret door to the manager.
        
        Args:
            door: SecretDoor instance to track
        """
        self.doors.append(door)
    
    def check_reveals_near(self, observer: 'Entity', max_distance: int = 3) -> List[Dict[str, Any]]:
        """Check all doors for passive reveals near an observer.
        
        This should be called each time the player moves.
        
        Args:
            observer: Entity to check doors against (usually player)
            max_distance: Maximum distance to check (default 3)
            
        Returns:
            List of reveal result dictionaries
        """
        results = []
        
        for door in self.doors:
            if door.revealed:
                continue  # Skip already-revealed doors
            
            # Calculate distance
            dx = abs(observer.x - door.x)
            dy = abs(observer.y - door.y)
            distance = max(dx, dy)
            
            if distance <= max_distance:
                result = door.try_reveal(observer, distance)
                if result:
                    results.append(result)
        
        return results
    
    def search_room(self, room_bounds: Tuple[int, int, int, int]) -> List[SecretDoor]:
        """Reveal all secret doors in a room.
        
        Used for room-wide search action.
        
        Args:
            room_bounds: Tuple of (x1, y1, x2, y2) defining room bounds
            
        Returns:
            List of newly revealed doors
        """
        x1, y1, x2, y2 = room_bounds
        revealed_doors = []
        
        for door in self.doors:
            if x1 <= door.x <= x2 and y1 <= door.y <= y2:
                if door.reveal_by_search():
                    revealed_doors.append(door)
        
        return revealed_doors
    
    def get_door_at(self, x: int, y: int) -> Optional[SecretDoor]:
        """Get the secret door at a specific location.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            SecretDoor if found, None otherwise
        """
        for door in self.doors:
            if door.x == x and door.y == y:
                return door
        return None
    
    def count_hidden(self) -> int:
        """Count how many doors are still hidden.
        
        Returns:
            Number of unrevealed doors
        """
        return sum(1 for door in self.doors if not door.revealed)
    
    def count_revealed(self) -> int:
        """Count how many doors have been revealed.
        
        Returns:
            Number of revealed doors
        """
        return sum(1 for door in self.doors if door.revealed)
    
    def clear(self) -> None:
        """Remove all doors from the manager."""
        self.doors.clear()
    
    def __len__(self) -> int:
        """Return the total number of doors managed."""
        return len(self.doors)
    
    def __repr__(self):
        return f"SecretDoorManager(doors={len(self.doors)}, hidden={self.count_hidden()}, revealed={self.count_revealed()})"

