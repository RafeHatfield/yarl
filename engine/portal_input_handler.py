"""Portal Input Handler - Manages portal placement and targeting.

This module handles the portal targeting sequence:
1. Player activates wand
2. Enter PORTAL_TARGETING mode
3. Click entrance location
4. Click exit location
5. Portals deployed or error message shown
"""

import logging
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger(__name__)


class PortalInputHandler:
    """Manages portal placement targeting and interaction."""
    
    def __init__(self):
        """Initialize portal input handler."""
        self.targeting_active = False
        self.targeting_stage = 0  # 0=idle, 1=entrance, 2=exit
        self.entrance_pos: Optional[Tuple[int, int]] = None
        self.exit_pos: Optional[Tuple[int, int]] = None
        self.wand = None
        self.dungeon = None
    
    def start_portal_targeting(self, wand, dungeon) -> Dict[str, Any]:
        """Start portal placement targeting mode.
        
        Args:
            wand: The Wand of Portals entity
            dungeon: Current dungeon map
            
        Returns:
            Result dict with status
        """
        if not wand or not hasattr(wand, 'portal_placer'):
            return {
                'success': False,
                'message': 'Invalid wand'
            }
        
        self.wand = wand
        self.dungeon = dungeon
        self.targeting_active = True
        self.targeting_stage = 0
        self.entrance_pos = None
        self.exit_pos = None
        
        # Start the wand's targeting sequence
        result = wand.portal_placer.start_targeting()
        
        return {
            'success': True,
            'message': 'Click to place ENTRANCE portal (ESC to cancel)',
            'stage': 1
        }
    
    def handle_portal_click(self, x: int, y: int) -> Dict[str, Any]:
        """Handle player click during portal targeting.
        
        Args:
            x: Click X coordinate
            y: Click Y coordinate
            
        Returns:
            Result dict with placement result
        """
        if not self.targeting_active or not self.wand or not self.dungeon:
            return {'success': False, 'message': 'Portal targeting not active'}
        
        wand = self.wand
        placer = wand.portal_placer
        
        if placer.targeting_stage == 1:
            # Placing entrance
            result = placer.place_entrance(x, y, self.dungeon)
            
            if result['success']:
                self.entrance_pos = (x, y)
                return {
                    'success': True,
                    'message': 'Entrance portal placed. Click to place EXIT portal',
                    'stage': 2
                }
            else:
                return result
        
        elif placer.targeting_stage == 2:
            # Placing exit
            result = placer.place_exit(x, y, self.dungeon)
            
            if result['success']:
                self.exit_pos = (x, y)
                self.targeting_active = False
                self.targeting_stage = 0
                return {
                    'success': True,
                    'message': 'Portals active! Use wand again to recycle.',
                    'entrance': result['entrance'],
                    'exit': result['exit']
                }
            else:
                return result
        
        return {'success': False, 'message': 'Unknown targeting stage'}
    
    def cancel_targeting(self) -> Dict[str, Any]:
        """Cancel portal targeting mode.
        
        Returns:
            Result dict with cancellation status
        """
        self.targeting_active = False
        self.targeting_stage = 0
        self.entrance_pos = None
        self.exit_pos = None
        
        return {
            'cancelled': True,
            'message': 'Portal targeting cancelled'
        }
    
    def is_targeting(self) -> bool:
        """Check if portal targeting is active.
        
        Returns:
            True if targeting mode active
        """
        return self.targeting_active
    
    def get_targeting_stage(self) -> int:
        """Get current targeting stage.
        
        Returns:
            0=idle, 1=placing entrance, 2=placing exit
        """
        return self.wand.portal_placer.targeting_stage if self.wand else 0


# Global portal input handler instance
_portal_input_handler: Optional[PortalInputHandler] = None


def get_portal_input_handler() -> PortalInputHandler:
    """Get the global portal input handler instance.
    
    Returns:
        PortalInputHandler singleton
    """
    global _portal_input_handler
    if _portal_input_handler is None:
        _portal_input_handler = PortalInputHandler()
    return _portal_input_handler

