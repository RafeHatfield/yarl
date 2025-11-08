"""Portal System - Game integration for portals.

Handles:
- Portal entity detection when player moves
- Automatic teleportation through portals
- Portal creation/pickup/drop
- Monster interactions with portals
"""

import logging
from typing import Optional, Tuple, List, Dict, Any

logger = logging.getLogger(__name__)


class PortalSystem:
    """Central system for portal game mechanics."""
    
    @staticmethod
    def check_portal_collision(entity, dungeon) -> Optional[Dict[str, Any]]:
        """Check if entity is on a portal and handle teleportation.
        
        Args:
            entity: Entity to check (usually player)
            dungeon: Current dungeon
            
        Returns:
            Result dict if entity teleported, None otherwise
        """
        if not entity or not dungeon:
            return None
        
        # Find portals at entity position
        for ent in dungeon.entities:
            if ent.x == entity.x and ent.y == entity.y and ent != entity:
                if hasattr(ent, 'portal'):
                    portal = ent.portal
                    if portal.is_deployed and portal.linked_portal and portal.linked_portal.owner:
                        # Teleport through portal
                        results = portal.teleport_through(entity, dungeon)
                        if results and results[0].get('teleported'):
                            return results[0]
        
        return None
    
    @staticmethod
    def get_portal_at(x: int, y: int, dungeon) -> Optional[Any]:
        """Get portal entity at coordinates if one exists.
        
        Args:
            x: X coordinate
            y: Y coordinate
            dungeon: Current dungeon
            
        Returns:
            Portal entity or None
        """
        for entity in dungeon.entities:
            if entity.x == x and entity.y == y and hasattr(entity, 'portal'):
                if entity.portal.is_deployed:
                    return entity
        
        return None
    
    @staticmethod
    def get_all_portals(dungeon) -> List[Any]:
        """Get all active portal entities in dungeon.
        
        Args:
            dungeon: Current dungeon
            
        Returns:
            List of portal entities
        """
        return [
            e for e in dungeon.entities
            if hasattr(e, 'portal') and e.portal.is_deployed
        ]
    
    @staticmethod
    def get_wand(inventory) -> Optional[Any]:
        """Get Wand of Portals from inventory if present.
        
        Args:
            inventory: Player inventory
            
        Returns:
            Wand entity or None
        """
        if not inventory:
            return None
        
        for item in inventory.items:
            if hasattr(item, 'portal_placer'):
                return item
        
        return None
    
    @staticmethod
    def pick_up_portal(entity: Any, dungeon) -> Dict[str, Any]:
        """Pick up a deployed portal and add to inventory.
        
        Args:
            entity: Portal entity to pick up
            dungeon: Current dungeon
            
        Returns:
            Result dict with success status
        """
        if not hasattr(entity, 'portal'):
            return {'success': False, 'message': 'Not a portal'}
        
        portal = entity.portal
        
        if not portal.is_deployed:
            return {'success': False, 'message': 'Portal not deployed'}
        
        # Mark as not deployed
        portal.is_deployed = False
        portal.owner = None
        
        # Remove from dungeon if tracked there
        if entity in dungeon.entities:
            dungeon.entities.remove(entity)
        
        logger.debug(f"Portal picked up: {portal.portal_type}")
        
        return {
            'success': True,
            'message': f'{portal.portal_type.title()} Portal picked up',
            'portal_entity': entity
        }
    
    @staticmethod
    def deploy_portal(player, portal_entity, x: int, y: int, dungeon) -> Dict[str, Any]:
        """Deploy a portal from inventory at specified location.
        
        Args:
            player: Player entity
            portal_entity: Portal entity with portal component
            x: X coordinate to deploy at
            y: Y coordinate to deploy at
            dungeon: Current dungeon
            
        Returns:
            Result dict with success status
        """
        if not hasattr(portal_entity, 'portal'):
            return {'success': False, 'message': 'Not a portal'}
        
        portal = portal_entity.portal
        placer = None
        
        # Find wand to validate placement
        for item in player.inventory.items if player.inventory else []:
            if hasattr(item, 'portal_placer'):
                placer = item.portal_placer
                break
        
        if not placer:
            return {'success': False, 'message': 'No wand available'}
        
        # Validate placement
        if not placer._is_valid_placement(x, y, dungeon):
            return {'success': False, 'message': 'Cannot place portal there'}
        
        # Deploy portal
        portal_entity.x = x
        portal_entity.y = y
        portal.is_deployed = True
        portal.owner = None
        
        # Add to dungeon
        if portal_entity not in dungeon.entities:
            dungeon.entities.append(portal_entity)
        
        logger.debug(f"Portal deployed at ({x}, {y}): {portal.portal_type}")
        
        return {
            'success': True,
            'message': f'{portal.portal_type.title()} Portal deployed'
        }


# Global portal system instance
_portal_system: Optional[PortalSystem] = None


def get_portal_system() -> PortalSystem:
    """Get the global portal system instance.
    
    Returns:
        PortalSystem singleton
    """
    global _portal_system
    if _portal_system is None:
        _portal_system = PortalSystem()
    return _portal_system

