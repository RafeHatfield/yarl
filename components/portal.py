"""Portal Component System.

This module provides the portal component for the Wand of Portals system.
Portals are dimensional gateways that teleport entities between two linked points.

They can be:
- Deployed on the map (blue entrance, orange exit)
- Carried in inventory as items
- Walked through (automatic teleportation)
- Picked up with right-click

Example:
    >>> portal = Portal('entrance')
    >>> portal.teleport_through(player, dungeon)
"""

from typing import TYPE_CHECKING, Dict, Any, List, Optional, Tuple

from components.map_feature import MapFeature, MapFeatureType

if TYPE_CHECKING:
    from entity import Entity


class Portal(MapFeature):
    """A dimensional gateway that teleports entities between two points.
    
    Portals exist as physical map objects that can be:
    - Stepped on (automatic teleportation)
    - Picked up with right-click (become inventory items)
    - Redeployed from inventory
    
    Each portal is part of a pair (entrance/exit, bidirectional).
    
    Attributes:
        portal_type: 'entrance' (blue) or 'exit' (orange)
        linked_portal: The paired portal (if any)
        is_deployed: Whether portal is on map or in inventory
        owner: Entity carrying this portal (if in inventory)
    """
    
    def __init__(
        self,
        portal_type: str,
        linked_portal: Optional['Portal'] = None
    ):
        """Initialize a portal component.
        
        Args:
            portal_type: 'entrance' (blue) or 'exit' (orange)
            linked_portal: The paired portal this connects to (optional)
        """
        super().__init__(
            feature_type=MapFeatureType.PORTAL,
            discovered=True,  # Portals always visible
            interactable=True
        )
        
        self.portal_type = portal_type
        self.linked_portal = linked_portal
        self.is_deployed = True  # False when in inventory
        self.owner: Optional['Entity'] = None  # Entity carrying this portal
    
    def get_portal_pair(self) -> Tuple[Optional['Portal'], Optional['Portal']]:
        """Get both entrance and exit portals as tuple (entrance, exit).
        
        Returns:
            Tuple of (entrance_portal, exit_portal)
        """
        if self.portal_type == 'entrance':
            return (self, self.linked_portal)
        else:
            return (self.linked_portal, self)
    
    def is_valid_to_enter(self, actor: 'Entity') -> bool:
        """Check if entity can enter this portal.
        
        Cannot enter entrance portal if carrying the paired exit portal
        (prevents walking into a portal you're holding the exit to).
        
        Args:
            actor: Entity attempting to enter
            
        Returns:
            True if entity can enter, False otherwise
        """
        if self.portal_type == 'exit':
            # Exit portals always usable
            return True
        
        # Entrance blocked if carrying exit portal
        if actor.inventory:
            for item in actor.inventory.items:
                if hasattr(item, 'portal'):
                    portal_component = item.portal
                    if portal_component.portal_type == 'exit':
                        # Check if it's the paired exit portal
                        if portal_component.linked_portal == self:
                            return False
        
        return True
    
    def teleport_through(self, actor: 'Entity', dungeon) -> List[Dict[str, Any]]:
        """Teleport actor through this portal to the exit.
        
        Updates actor position and FOV after teleportation.
        
        Args:
            actor: Entity being teleported
            dungeon: Current dungeon map
            
        Returns:
            List of result dictionaries with teleportation info
        """
        results = []
        
        if not self.is_valid_to_enter(actor):
            from message_builder import MessageBuilder as MB
            results.append({
                'message': MB.warning("You can't enter that portal right now.")
            })
            return results
        
        if not self.linked_portal or not self.linked_portal.is_deployed:
            from message_builder import MessageBuilder as MB
            results.append({
                'message': MB.warning("The portal flickers and dies before you reach it.")
            })
            return results
        
        # Store old position
        old_x, old_y = actor.x, actor.y
        
        # Teleport
        actor.x = self.linked_portal.x
        actor.y = self.linked_portal.y
        
        # Invalidate entity sorting cache
        from entity_sorting_cache import invalidate_entity_cache
        invalidate_entity_cache("portal_teleportation")
        
        results.append({
            'teleported': True,
            'actor': actor,
            'from_pos': (old_x, old_y),
            'to_pos': (actor.x, actor.y),
            'message': "You step through the portal..."
        })
        
        return results
    
    def get_description(self) -> str:
        """Get description of the portal.
        
        Returns:
            String description for tooltips
        """
        if self.portal_type == 'entrance':
            return "Portal Entrance (Blue)"
        else:
            return "Portal Exit (Orange)"
    
    def __repr__(self):
        linked_str = f"→{self.linked_portal.portal_type[0]}" if self.linked_portal else "→?"
        return (
            f"Portal({self.portal_type[0]}{linked_str}, "
            f"deployed={self.is_deployed})"
        )

