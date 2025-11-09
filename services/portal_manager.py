"""PortalManager Service - Centralized portal logic.

Single source of truth for all portal operations:
- Creating portals (wand, victory, etc)
- Detecting collisions
- Handling teleportation
- Managing portal pairs

This service replaces scattered portal logic across multiple files.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from components.portal import Portal
from entity import Entity

logger = logging.getLogger(__name__)


class PortalManager:
    """Centralized service for all portal-related operations."""
    
    @staticmethod
    def create_portal_entity(
        portal_type: str,
        x: int,
        y: int,
        linked_portal: Optional['Portal'] = None,
        from_yaml: bool = True
    ) -> Optional[Entity]:
        """Create a portal entity - SINGLE source of truth for all portal creation.
        
        Args:
            portal_type: 'entrance', 'exit', or 'entity_portal' (victory)
            x: X coordinate
            y: Y coordinate
            linked_portal: Optional linked Portal component (for pairs)
            from_yaml: If True, load appearance from YAML (default). If False, use defaults.
            
        Returns:
            Portal entity with all components properly set up
        """
        from config.entity_factory import get_entity_factory
        
        factory = get_entity_factory()
        
        # Map portal types to YAML entity names
        yaml_map = {
            'entrance': 'portal_entrance',
            'exit': 'portal_exit',
            'entity_portal': 'entity_portal',  # Victory portal
        }
        
        yaml_name = yaml_map.get(portal_type)
        if not yaml_name:
            logger.error(f"Unknown portal type: {portal_type}")
            return None
        
        try:
            # Load entity from YAML to get appearance and components
            entity = factory.create_unique_item(yaml_name, x, y)
            
            if not entity:
                logger.error(f"Failed to create portal entity from YAML: {yaml_name}")
                return None
            
            # Create or replace the Portal component
            # Keep portal_type as-is (entity_portal is a special victory portal type)
            portal = Portal(
                portal_type,
                linked_portal=linked_portal
            )
            portal.owner = entity
            portal.is_deployed = True
            
            # Replace any existing portal component
            entity.portal = portal
            
            # Ensure Item component exists
            if not hasattr(entity, 'item') or entity.get_component_optional(ComponentType.ITEM) is None:
                from components.item import Item
                entity.item = Item()
            
            # Register components properly
            from components.component_registry import ComponentType
            entity.components.add(ComponentType.PORTAL, portal)
            
            logger.debug(f"Created portal entity: {portal_type} at ({x}, {y})")
            return entity
        
        except Exception as e:
            logger.error(f"Error creating portal entity: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    @staticmethod
    def link_portal_pair(entrance: Optional[Portal], exit_portal: Optional[Portal]) -> bool:
        """Link two portals together.
        
        Args:
            entrance: Entrance portal component
            exit_portal: Exit portal component
            
        Returns:
            True if linking succeeded
        """
        if not entrance or not exit_portal:
            logger.error("Cannot link portals: one or both are None")
            return False
        
        try:
            entrance.linked_portal = exit_portal
            exit_portal.linked_portal = entrance
            logger.debug(f"Portals linked successfully")
            return True
        except Exception as e:
            logger.error(f"Error linking portals: {e}")
            return False
    
    @staticmethod
    def check_portal_collision(
        entity: Entity,
        entities: List[Entity]
    ) -> Optional[Dict[str, Any]]:
        """Check if entity is standing on a portal and handle teleportation.
        
        This is the ONLY place portal collision is checked. Replaces:
        - PortalSystem.check_portal_collision()
        - MovementService portal detection
        
        For monsters, checks the AI's portal_usable flag before allowing teleportation.
        
        Args:
            entity: Entity to check (usually player, but can be monsters)
            entities: List of all entities in the dungeon
            
        Returns:
            Dict with teleportation result if successful, None otherwise
        """
        if not entity or not entities:
            return None
        
        try:
            # Monsters must be allowed to use portals by their AI
            # Players can always use portals
            if hasattr(entity, 'ai') and entity.get_component_optional(ComponentType.AI):
                # Check if this monster's AI allows portal usage
                if hasattr(entity.get_component_optional(ComponentType.AI), 'portal_usable') and not entity.get_component_optional(ComponentType.AI).portal_usable:
                    logger.debug(f"Monster {entity.name} cannot use portals (portal_usable=False)")
                    return None
            
            # Check if entity is carrying the entry portal (prevents portal entry then)
            if hasattr(entity, 'inventory') and entity.require_component(ComponentType.INVENTORY):
                for item in entity.require_component(ComponentType.INVENTORY).items:
                    if hasattr(item, 'portal') and item.portal:
                        if item.portal.portal_type == 'entrance':
                            logger.debug(f"Entity {entity.name} cannot use portals (carrying entry portal)")
                            return None
            
            # Find portals at entity position
            for ent in entities:
                if (ent.x == entity.x and 
                    ent.y == entity.y and 
                    ent != entity and 
                    hasattr(ent, 'portal')):
                    
                    portal = ent.portal
                    
                    # Check if this is a functional wand portal (entrance/exit)
                    # NOT the victory portal (entity_portal)
                    if portal.portal_type in ['entrance', 'exit']:
                        if portal.is_deployed and portal.linked_portal and portal.linked_portal.owner:
                            # Perform teleportation
                            old_x, old_y = entity.x, entity.y
                            entity.x = portal.linked_portal.owner.x
                            entity.y = portal.linked_portal.owner.y
                            
                            # Invalidate entity sorting cache
                            from entity_sorting_cache import invalidate_entity_cache
                            invalidate_entity_cache("portal_teleportation")
                            
                            entity_type = "Monster" if hasattr(entity, 'ai') and entity.get_component_optional(ComponentType.AI) else "Player"
                            is_monster = entity_type == "Monster"
                            
                            logger.info(f"{entity_type} portal teleportation: ({old_x}, {old_y}) -> ({entity.x}, {entity.y})")
                            
                            # Create visual effect message
                            from services.portal_visual_effects import PortalVFXSystem, get_portal_effect_queue
                            vfx_msg = PortalVFXSystem.create_teleportation_message(
                                entity.name, 
                                is_player=not is_monster,
                                is_monster=is_monster
                            )
                            
                            # Add to visual effect queue for rendering
                            effect_queue = get_portal_effect_queue()
                            effect_queue.add_teleportation(
                                (old_x, old_y),
                                (entity.x, entity.y),
                                entity.name,
                                intensity='high' if not is_monster else 'medium'
                            )
                            
                            return {
                                'teleported': True,
                                'actor': entity,
                                'from_pos': (old_x, old_y),
                                'to_pos': (entity.x, entity.y),
                                'message': vfx_msg.get('message', f"{entity.name} steps through the portal..."),
                                'vfx': vfx_msg
                            }
            
            return None
        
        except Exception as e:
            logger.error(f"Error checking portal collision: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    @staticmethod
    def check_victory_portal_collision(
        entity: Entity,
        entities: List[Entity]
    ) -> Optional[Entity]:
        """Check if entity is standing on the victory portal (entity_portal).
        
        This is separate from wand portals - it triggers confrontation, not teleportation.
        
        Args:
            entity: Entity to check (usually player)
            entities: List of all entities in the dungeon
            
        Returns:
            Victory portal entity if player is on it, None otherwise
        """
        if not entity or not entities:
            return None
        
        try:
            for ent in entities:
                if (ent.x == entity.x and 
                    ent.y == entity.y and 
                    hasattr(ent, 'portal')):
                    
                    portal = ent.portal
                    
                    # Only check for victory portal (entity_portal)
                    # Wand portals (entrance/exit) don't trigger confrontation
                    if portal.portal_type not in ['entrance', 'exit']:
                        return ent
            
            return None
        
        except Exception as e:
            logger.error(f"Error checking victory portal collision: {e}")
            return None
    
    @staticmethod
    def recycle_portals(entrance: Optional[Portal], exit_portal: Optional[Portal]) -> None:
        """Mark portals as no longer deployed (for wand recycling).
        
        Args:
            entrance: Entrance portal to recycle
            exit_portal: Exit portal to recycle
        """
        if entrance:
            entrance.is_deployed = False
            entrance.owner = None
        
        if exit_portal:
            exit_portal.is_deployed = False
            exit_portal.owner = None


# Global portal manager instance
_portal_manager: Optional[PortalManager] = None


def get_portal_manager() -> PortalManager:
    """Get or create the global portal manager instance."""
    global _portal_manager
    if _portal_manager is None:
        _portal_manager = PortalManager()
    return _portal_manager

