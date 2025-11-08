"""Portal Visual Effects System

Handles visual feedback for portal teleportation events:
- Flash effect when entities teleport
- Color highlights
- Message display

This creates satisfying visual feedback so players understand
what just happened in the game world.
"""

import logging
from typing import Optional, Dict, Any, Tuple
from game_messages import Message
from message_builder import MessageBuilder as MB

logger = logging.getLogger(__name__)


class PortalVisualEffect:
    """A visual effect for portal events."""
    
    def __init__(self, 
                 entity_name: str,
                 effect_type: str,  # 'teleport_out', 'teleport_in', 'flash'
                 from_pos: Optional[Tuple[int, int]] = None,
                 to_pos: Optional[Tuple[int, int]] = None,
                 color: Tuple[int, int, int] = (100, 200, 255)):
        """
        Args:
            entity_name: Name of entity being affected
            effect_type: Type of effect ('teleport_out', 'teleport_in', 'flash')
            from_pos: Starting position (x, y)
            to_pos: Ending position (x, y)
            color: RGB color tuple for the effect
        """
        self.entity_name = entity_name
        self.effect_type = effect_type
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.color = color


class PortalVFXSystem:
    """Centralized portal visual effects."""
    
    @staticmethod
    def create_teleportation_message(entity_name: str, 
                                     is_player: bool = False,
                                     is_monster: bool = False) -> Dict[str, Any]:
        """Create a visual effect message for teleportation.
        
        Args:
            entity_name: Name of entity being teleported
            is_player: True if entity is the player
            is_monster: True if entity is a monster
            
        Returns:
            Dictionary with 'message' and optional visual data
        """
        if is_player:
            # Player teleportation - dramatic, personal
            return {
                'message': MB.item_effect("✨ Reality warps around you!"),
                'effect_type': 'teleport_player',
                'intensity': 'high',
            }
        elif is_monster:
            # Monster teleportation - noticeable but not as dramatic
            return {
                'message': MB.warning(f"✨ {entity_name} shimmers and vanishes!"),
                'effect_type': 'teleport_monster',
                'intensity': 'medium',
            }
        else:
            # Generic teleportation
            return {
                'message': MB.info("✨ A shimmer in the air..."),
                'effect_type': 'teleport_generic',
                'intensity': 'low',
            }
    
    @staticmethod
    def create_portal_placement_message(portal_type: str) -> Message:
        """Create a message when portal is placed.
        
        Args:
            portal_type: 'entrance' or 'exit'
            
        Returns:
            Message to display
        """
        if portal_type == 'entrance':
            return MB.item_effect("✓ Blue portal placed (entrance)")
        elif portal_type == 'exit':
            return MB.item_effect("✓ Orange portal placed (exit)")
        else:
            return MB.item_effect("✓ Portal placed")
    
    @staticmethod
    def create_portal_activation_message(entity_name: str) -> Message:
        """Create a message when a portal is activated (stepped on).
        
        Args:
            entity_name: Name of entity stepping on portal
            
        Returns:
            Message to display
        """
        return MB.item_effect(f"✨ {entity_name} is pulled into the portal!")


class TeleportationEffect:
    """Represents a single teleportation effect with timing info."""
    
    def __init__(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int],
                 entity_name: str, intensity: str = 'medium'):
        """
        Args:
            from_pos: Starting position (x, y)
            to_pos: Ending position (x, y)
            entity_name: Name of entity teleporting
            intensity: 'low', 'medium', or 'high'
        """
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.entity_name = entity_name
        self.intensity = intensity
        self.created_at = None  # Populated by rendering system
    
    def get_flash_color(self) -> Tuple[int, int, int]:
        """Get the flash color based on intensity.
        
        Returns:
            RGB tuple for the flash effect
        """
        intensity_map = {
            'low': (100, 150, 200),      # Dim blue
            'medium': (150, 200, 255),   # Bright blue
            'high': (200, 255, 255),     # Very bright cyan
        }
        return intensity_map.get(self.intensity, (150, 200, 255))


class PortalEffectQueue:
    """Queue for managing visual effects over time."""
    
    def __init__(self):
        """Initialize the effect queue."""
        self.effects = []  # List of active effects
        self.max_effects = 10  # Prevent infinite buildup
    
    def add_teleportation(self, from_pos: Tuple[int, int], 
                         to_pos: Tuple[int, int],
                         entity_name: str,
                         intensity: str = 'medium') -> None:
        """Add a teleportation effect to the queue.
        
        Args:
            from_pos: Starting position (x, y)
            to_pos: Ending position (x, y)
            entity_name: Name of entity being teleported
            intensity: 'low', 'medium', or 'high'
        """
        if len(self.effects) >= self.max_effects:
            # Remove oldest effect
            self.effects.pop(0)
        
        effect = TeleportationEffect(from_pos, to_pos, entity_name, intensity)
        self.effects.append(effect)
        logger.debug(f"Added teleportation effect for {entity_name}: {from_pos} -> {to_pos}")
    
    def clear(self) -> None:
        """Clear all effects."""
        self.effects.clear()
    
    def get_effects_for_position(self, x: int, y: int) -> list:
        """Get all effects at a specific position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            List of effects at that position
        """
        return [e for e in self.effects if e.from_pos == (x, y) or e.to_pos == (x, y)]


# Global effect queue instance
_effect_queue = PortalEffectQueue()


def get_portal_effect_queue() -> PortalEffectQueue:
    """Get the global portal effect queue."""
    return _effect_queue

