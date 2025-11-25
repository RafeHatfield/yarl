"""Portal Placer Component - Wand of Portals Logic.

This module handles the Wand of Portals mechanics:
- Creating entrance and exit portals
- Managing the placement sequence
- Validating portal locations
- Recycling portals (creating new pair)

The wand has infinite uses with a simple cycle:
1. Click entrance location
2. Click exit location
3. Use wand again → portals disappear, wand ready for new placement
"""

import logging
from typing import TYPE_CHECKING, Dict, Any, Optional

from components.wand import Wand

if TYPE_CHECKING:
    from entity import Entity

logger = logging.getLogger(__name__)


class PortalPlacer(Wand):
    """Manages portal creation and lifecycle for Wand of Portals.
    
    The wand operates on a simple cycle:
    - Create entrance portal (consumes 1 charge)
    - Create exit portal (pair now active)
    - Both active until wand is used again
    - Using wand again: old portals disappear, charge refunded
    
    Attributes:
        active_entrance: Current entrance portal component (if deployed)
        active_exit: Current exit portal component (if deployed)
        active_entrance_entity: Entity owning entrance portal
        active_exit_entity: Entity owning exit portal
        targeting_stage: 0=idle, 1=placing_entrance, 2=placing_exit
    """
    
    def __init__(self):
        """Initialize portal wand with exactly 1 charge (always).
        
        The wand operates as a binary state machine:
        - State A: No portals active → wand is "ready" (1 charge)
        - State B: Portal pair active → wand is "occupied" (still 1 charge)
        
        The charge never changes. It's always 1.
        """
        super().__init__(
            spell_type="portal",
            charges=1  # ALWAYS 1 - never more, never less
        )
        
        self.active_entrance: Optional['Portal'] = None
        self.active_exit: Optional['Portal'] = None
        self.active_entrance_entity: Optional['Entity'] = None
        self.active_exit_entity: Optional['Entity'] = None
        self.targeting_stage = 0  # 0=idle, 1=placing_entrance, 2=placing_exit
    
    def start_targeting(self) -> Dict[str, Any]:
        """Begin portal placement sequence.
        
        If portals already exist, starts fresh cycle (recycles old portals).
        
        Returns:
            Result dict with status
        """
        # Recycle old portals if they exist
        if self.active_entrance or self.active_exit:
            self.recycle_portals()
        
        self.targeting_stage = 1
        
        return {
            'status': 'targeting_started',
            'stage': 1,
            'message': 'Click to place ENTRANCE portal (ESC to cancel)'
        }
    
    def place_entrance(
        self, 
        x: int, 
        y: int, 
        dungeon: 'GameMap'
    ) -> Dict[str, Any]:
        """Place entrance portal at specified location.
        
        Args:
            x: X coordinate
            y: Y coordinate
            dungeon: Current dungeon map
            
        Returns:
            Result dict with success status and portal
        """
        if not self._is_valid_placement(x, y, dungeon):
            return {
                'success': False,
                'message': 'Cannot place portal there'
            }
        
        # Remove old portals if recycling
        if self.active_entrance:
            self.active_entrance.is_deployed = False
            self.active_entrance.owner = None
            self.active_entrance = None
        
        if self.active_exit:
            self.active_exit.is_deployed = False
            self.active_exit.owner = None
            self.active_exit = None
        
        # Create entrance portal
        from components.portal import Portal
        entrance = Portal('entrance')
        entrance.x = x
        entrance.y = y
        entrance.is_deployed = True
        entrance.owner = None  # Will be set when placed in dungeon
        
        self.active_entrance = entrance
        self.targeting_stage = 2
        
        logger.debug(f"Entrance portal placed at ({x}, {y})")
        
        return {
            'success': True,
            'portal': entrance,
            'stage': 2,
            'message': 'Entrance portal placed. Click to place EXIT portal'
        }
    
    def place_exit(
        self,
        x: int,
        y: int,
        dungeon: 'GameMap'
    ) -> Dict[str, Any]:
        """Place exit portal and complete the cycle.
        
        Args:
            x: X coordinate
            y: Y coordinate
            dungeon: Current dungeon map
            
        Returns:
            Result dict with success status and both portals
        """
        if not self._is_valid_placement(x, y, dungeon):
            return {
                'success': False,
                'message': 'Cannot place portal there'
            }
        
        if not self.active_entrance:
            return {
                'success': False,
                'message': 'No entrance portal active (error)'
            }
        
        # Create exit portal
        from components.portal import Portal
        exit_portal = Portal('exit', linked_portal=self.active_entrance)
        exit_portal.x = x
        exit_portal.y = y
        exit_portal.is_deployed = True
        exit_portal.owner = None
        
        # Link both portals bidirectionally
        self.active_entrance.linked_portal = exit_portal
        
        self.active_exit = exit_portal
        self.targeting_stage = 0
        
        logger.debug(f"Exit portal placed at ({x}, {y}), portal pair complete")
        
        return {
            'success': True,
            'entrance': self.active_entrance,
            'exit': exit_portal,
            'stage': 0,
            'message': 'Portals active! Use wand again to recycle.'
        }
    
    def recycle_portals(self) -> Dict[str, Any]:
        """Remove current portals and reset for new cycle.
        
        DEPRECATED: Use cancel_active_portals() instead for proper entity cleanup.
        
        This method only marks components as not deployed without removing entities.
        Kept for backward compatibility with tests.
        
        Returns:
            Result dict with recycle status
        """
        if self.active_entrance:
            self.active_entrance.is_deployed = False
            self.active_entrance.owner = None
            self.active_entrance = None
        
        if self.active_exit:
            self.active_exit.is_deployed = False
            self.active_exit.owner = None
            self.active_exit = None
        
        self.active_entrance_entity = None
        self.active_exit_entity = None
        self.targeting_stage = 0
        
        logger.debug("Portals recycled (deprecated), wand ready for new placement")
        
        return {
            'recycled': True,
            'message': 'Portals recycled. Wand ready for new placement.'
        }
    
    def has_active_portals(self) -> bool:
        """Check if wand has active portals deployed.
        
        Returns:
            True if both entrance and exit entities exist and are deployed
        """
        return (
            self.active_entrance_entity is not None and
            self.active_entrance is not None and
            self.active_entrance.is_deployed and
            self.active_exit_entity is not None and
            self.active_exit is not None and
            self.active_exit.is_deployed
        )
    
    def cancel_active_portals(self, entities_list: list) -> Dict[str, Any]:
        """Cancel active portals and reset wand to ready state.
        
        This method:
        - Removes portal entities from the game world
        - Resets internal tracking
        - Charge stays at 1 (always)
        
        Args:
            entities_list: The game's entities list
            
        Returns:
            Dict with 'success' bool and 'message' str
        """
        if not self.has_active_portals():
            return {
                'success': False,
                'message': 'No active portals to cancel'
            }
        
        from services.portal_manager import get_portal_manager
        
        portal_manager = get_portal_manager()
        result = portal_manager.deactivate_portal_pair(
            self.active_entrance_entity,
            self.active_exit_entity,
            entities_list
        )
        
        if result.get('success'):
            # Clear internal tracking
            self.active_entrance = None
            self.active_exit = None
            self.active_entrance_entity = None
            self.active_exit_entity = None
            self.targeting_stage = 0
            
            # Ensure charge stays at 1 (invariant)
            self.charges = 1
            logger.info("Portal wand reset to ready state (charge = 1)")
            
            return {
                'success': True,
                'message': result.get('message', 'Portals canceled. Wand ready.')
            }
        else:
            return {
                'success': False,
                'message': result.get('message', 'Failed to cancel portals')
            }
    
    def _is_valid_placement(
        self,
        x: int,
        y: int,
        dungeon: 'GameMap'
    ) -> bool:
        """Validate portal placement location.
        
        Checks:
        - Within dungeon bounds
        - Not on wall tile
        - Not on water/lava
        - Not occupied by entity (optional)
        
        Args:
            x: X coordinate
            y: Y coordinate
            dungeon: Current dungeon map
            
        Returns:
            True if placement is valid, False otherwise
        """
        # Check bounds
        if x < 0 or x >= dungeon.width or y < 0 or y >= dungeon.height:
            logger.debug(f"Portal placement out of bounds: ({x}, {y})")
            return False
        
        tile = dungeon.tiles[x][y]
        
        # Can't place on walls
        if tile.blocked:
            logger.debug(f"Portal placement on wall at ({x}, {y})")
            return False
        
        # Can't place on water, lava (specific tile types)
        if hasattr(tile, 'tile_type'):
            if tile.tile_type in ['water', 'lava']:
                logger.debug(f"Portal placement on {tile.tile_type} at ({x}, {y})")
                return False
        
        logger.debug(f"Portal placement valid at ({x}, {y})")
        return True
    
    def __repr__(self):
        return (
            f"PortalPlacer(stage={self.targeting_stage}, "
            f"entrance={self.active_entrance is not None}, "
            f"exit={self.active_exit is not None})"
        )

