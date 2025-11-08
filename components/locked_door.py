"""Locked Door Component System.

This module provides the locked door component for vault entrances and special areas.
Locked doors require specific keys to unlock and transform to passable floor when opened.

Example:
    >>> door = Entity(10, 10, '+', (255, 215, 0), 'Golden Door')
    >>> door.locked_door = LockedDoor(required_key='gold_key')
    >>> results = door.locked_door.unlock(player)
"""

from enum import Enum, auto
from typing import TYPE_CHECKING, Optional, Dict, Any, List

from components.map_feature import MapFeature, MapFeatureType

if TYPE_CHECKING:


class DoorState(Enum):
    """States a door can be in."""
    LOCKED = auto()     # Locked, requires key
    UNLOCKED = auto()   # Unlocked but still visible
    OPENED = auto()     # Fully open (becomes floor)


class LockedDoor(MapFeature):
    """Component for locked doors.
    
    Locked doors block passage until the player uses the correct key.
    Once unlocked, they can be opened to transform into passable floor tiles.
    
    Attributes:
        state: Current state of the door
        required_key: Key type needed to unlock (e.g., 'bronze_key', 'gold_key')
        door_type: Visual/thematic type of door
    """
    
    def __init__(
        self,
        required_key: str,
        state: DoorState = DoorState.LOCKED,
        door_type: Optional[str] = None
    ):
        """Initialize a locked door component.
        
        Args:
            required_key: Key type needed to unlock (matches key item names)
            state: Initial state of the door
            door_type: Optional type identifier for themed doors
        """
        super().__init__(
            feature_type=MapFeatureType.DOOR,
            discovered=True,  # Doors are visible by default
            interactable=True
        )
        
        self.required_key = required_key
        self.state = state
        self.door_type = door_type or "standard"
    
    def is_locked(self) -> bool:
        """Check if door is currently locked.
        
        Returns:
            True if door state is LOCKED
        """
        return self.state == DoorState.LOCKED
    
    def is_passable(self) -> bool:
        """Check if door allows passage.
        
        Returns:
            True if door is OPENED, False otherwise
        """
        return self.state == DoorState.OPENED
    
    def unlock(self, actor: 'Entity', has_key: bool = False) -> List[Dict[str, Any]]:
        """Attempt to unlock the door.
        
        Args:
            actor: Entity attempting to unlock the door
            has_key: Whether actor has the required key
            
        Returns:
            List of result dictionaries from unlocking attempt
        """
        results = []
        
        if not self.is_locked():
            # Door is already unlocked, just open it
            from message_builder import MessageBuilder as MB
            results.append({
                'message': MB.info("The door is already unlocked.")
            })
            return self._open_door(results)
        
        # Check if actor has the required key
        if not has_key:
            from message_builder import MessageBuilder as MB
            key_name = self.required_key.replace('_', ' ').title()
            results.append({
                'message': MB.warning(f"This door is locked. You need a {key_name}.")
            })
            return results
        
        # Unlock the door
        self.state = DoorState.UNLOCKED
        
        from message_builder import MessageBuilder as MB
        key_name = self.required_key.replace('_', ' ').title()
        results.append({
            'message': MB.success(f"You unlock the door with the {key_name}.")
        })
        
        # Automatically open the door after unlocking
        return self._open_door(results)
    
    def _open_door(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Open the door, making it passable.
        
        Args:
            results: Existing results list to append to
            
        Returns:
            Updated results list
        """
        self.state = DoorState.OPENED
        
        from message_builder import MessageBuilder as MB
        results.append({
            'door_opened': True,
            'door_entity': self.owner,
            'message': MB.info("The door swings open.")
        })
        
        return results
    
    def get_description(self) -> str:
        """Get description of the door.
        
        Returns:
            String description for tooltips
        """
        state_descriptions = {
            DoorState.LOCKED: f"Locked Door",
            DoorState.UNLOCKED: f"Unlocked Door",
            DoorState.OPENED: "Open Door"
        }
        
        desc = state_descriptions.get(self.state, "Door")
        
        # Add key requirement if locked
        if self.is_locked():
            key_name = self.required_key.replace('_', ' ').title()
            desc += f" (requires {key_name})"
        
        return desc
    
    def __repr__(self):
        return (
            f"LockedDoor(required_key={self.required_key}, "
            f"state={self.state}, door_type={self.door_type})"
        )

