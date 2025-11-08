"""Map Feature Component System.

This module provides the base component for interactive map features like
chests, signposts, secret doors, and vault entrances. These are entities
that exist on the map and can be interacted with by the player.

Example:
    >>> chest = Entity(10, 10, 'C', (139, 69, 19), 'Chest')
    >>> chest.map_feature = MapFeature(MapFeatureType.CHEST, interactable=True)
    >>> if chest.map_feature.can_interact():
    ...     # Player interacts with chest
"""

from enum import Enum, auto
from typing import TYPE_CHECKING, Optional, Dict, Any, List

if TYPE_CHECKING:


class MapFeatureType(Enum):
    """Types of map features that can be interacted with."""
    CHEST = auto()
    SIGNPOST = auto()
    MURAL = auto()
    PORTAL = auto()
    SECRET_DOOR = auto()
    VAULT_DOOR = auto()
    DOOR = auto()  # Generic locked door


class MapFeature:
    """Base component for interactive map features.
    
    Map features are entities on the game map that players can interact with.
    They provide discovery moments, loot, information, or access to new areas.
    
    Attributes:
        feature_type: The type of map feature (chest, signpost, etc.)
        discovered: Whether the player has discovered this feature
        interactable: Whether the player can currently interact with it
        owner: The entity that owns this component
    """
    
    def __init__(
        self,
        feature_type: MapFeatureType,
        discovered: bool = False,
        interactable: bool = True
    ):
        """Initialize a map feature component.
        
        Args:
            feature_type: The type of map feature
            discovered: Whether this feature starts discovered
            interactable: Whether this feature can be interacted with
        """
        self.feature_type = feature_type
        self.discovered = discovered
        self.interactable = interactable
        self.owner: Optional['Entity'] = None
    
    def can_interact(self) -> bool:
        """Check if this feature can be interacted with.
        
        Returns:
            True if the feature is interactable and discovered
        """
        return self.interactable and self.discovered
    
    def discover(self) -> List[Dict[str, Any]]:
        """Mark this feature as discovered.
        
        Returns:
            List of result dictionaries with discovery messages
        """
        results = []
        
        if not self.discovered:
            self.discovered = True
            results.append({
                'discovered': True,
                'feature_type': self.feature_type,
                'entity': self.owner
            })
        
        return results
    
    def interact(self, actor: 'Entity') -> List[Dict[str, Any]]:
        """Interact with this feature.
        
        Base implementation does nothing. Subclasses should override.
        
        Args:
            actor: The entity interacting with this feature
            
        Returns:
            List of result dictionaries from the interaction
        """
        results = []
        
        if not self.can_interact():
            results.append({
                'message': "You can't interact with that right now."
            })
            return results
        
        # Subclasses will override with specific behavior
        return results
    
    def get_description(self) -> str:
        """Get a description of this feature.
        
        Returns:
            String description for tooltips/examination
        """
        feature_names = {
            MapFeatureType.CHEST: "Chest",
            MapFeatureType.SIGNPOST: "Signpost",
            MapFeatureType.MURAL: "Mural",
            MapFeatureType.PORTAL: "Portal",
            MapFeatureType.SECRET_DOOR: "Secret Door",
            MapFeatureType.VAULT_DOOR: "Vault Door"
        }
        
        name = feature_names.get(self.feature_type, "Unknown Feature")
        
        if not self.discovered:
            return f"Hidden {name}"
        
        if not self.interactable:
            return f"{name} (inactive)"
        
        return name
    
    def __repr__(self):
        return (
            f"MapFeature(type={self.feature_type}, "
            f"discovered={self.discovered}, "
            f"interactable={self.interactable})"
        )

