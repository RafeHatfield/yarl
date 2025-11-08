"""Signpost Component System.

This module provides the signpost component for environmental storytelling
and player hints. Signposts display text messages when examined and can
provide lore, warnings, humor, or hints about nearby features.

Messages are loaded from config/signpost_messages.yaml and can be filtered
by dungeon depth for contextual storytelling.

Example:
    >>> signpost = Entity(10, 10, '|', (139, 69, 19), 'Signpost')
    >>> signpost.signpost = Signpost("Beware: Dragon ahead!", sign_type='warning')
    >>> results = signpost.signpost.read(player)
"""

from typing import TYPE_CHECKING, Dict, Any, List

from components.map_feature import MapFeature, MapFeatureType

if TYPE_CHECKING:


class Signpost(MapFeature):
    """Component for signposts that display messages.
    
    Signposts provide environmental storytelling, warnings, hints, and humor.
    They're readable entities that display text when examined.
    
    Attributes:
        message: The text displayed when read
        sign_type: Category of sign ('lore', 'warning', 'humor', 'hint', 'directional')
        has_been_read: Whether the player has read this sign
    """
    
    def __init__(
        self,
        message: str,
        sign_type: str = 'lore'
    ):
        """Initialize a signpost component.
        
        Args:
            message: The text to display when read
            sign_type: Category ('lore', 'warning', 'humor', 'hint', 'directional')
        """
        super().__init__(
            feature_type=MapFeatureType.SIGNPOST,
            discovered=True,  # Signposts are visible by default
            interactable=True
        )
        
        self.message = message
        self.sign_type = sign_type
        self.has_been_read = False
    
    def read(self, actor: 'Entity') -> List[Dict[str, Any]]:
        """Read the signpost message.
        
        Args:
            actor: Entity reading the sign (usually the player)
            
        Returns:
            List of result dictionaries with the message
        """
        results = []
        
        if not self.can_interact():
            from message_builder import MessageBuilder as MB
            results.append({
                'message': MB.warning("You can't read that right now.")
            })
            return results
        
        self.has_been_read = True
        
        # Format message based on sign type
        from message_builder import MessageBuilder as MB
        
        message_color = {
            'lore': MB.info,
            'warning': MB.warning,
            'humor': MB.custom,  # Will need specific color
            'hint': MB.status_effect,
            'directional': MB.system
        }
        
        message_formatter = message_color.get(self.sign_type, MB.system)
        
        if self.sign_type == 'humor':
            # Use cyan for humor
            formatted_message = MB.custom(f"Sign: {self.message}", (100, 200, 255))
        else:
            formatted_message = message_formatter(f"Sign: {self.message}")
        
        results.append({
            'signpost_read': True,
            'message': formatted_message,
            'sign_type': self.sign_type
        })
        
        return results
    
    def get_description(self) -> str:
        """Get description of the signpost.
        
        Returns:
            String description for tooltips
        """
        if self.has_been_read:
            return "Signpost (read)"
        return "Signpost (unread)"
    
    @staticmethod
    def get_random_message(sign_type: str, depth: int = 1) -> str:
        """Get a random message for the specified sign type and depth.
        
        Messages are loaded from config/signpost_messages.yaml and filtered
        by dungeon depth to provide contextual storytelling.
        
        Args:
            sign_type: Type of sign to get message for
            depth: Current dungeon level (for depth-specific messages)
            
        Returns:
            Random message string appropriate for the sign type and depth
        """
        from config.signpost_message_registry import get_signpost_message_registry
        
        registry = get_signpost_message_registry()
        return registry.get_random_message(sign_type, depth)
    
    def __repr__(self):
        return (
            f"Signpost(type={self.sign_type}, "
            f"read={self.has_been_read})"
        )

