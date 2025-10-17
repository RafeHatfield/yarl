"""Signpost Component System.

This module provides the signpost component for environmental storytelling
and player hints. Signposts display text messages when examined and can
provide lore, warnings, humor, or hints about nearby features.

Example:
    >>> signpost = Entity(10, 10, '|', (139, 69, 19), 'Signpost')
    >>> signpost.signpost = Signpost("Beware: Dragon ahead!", sign_type='warning')
    >>> results = signpost.signpost.read(player)
"""

from typing import TYPE_CHECKING, Dict, Any, List

from components.map_feature import MapFeature, MapFeatureType

if TYPE_CHECKING:
    from entity import Entity


# Message pools for random signpost generation
LORE_MESSAGES = [
    "These catacombs were once a sacred burial ground...",
    "The Entity watches from the shadows, amused by your struggles.",
    "Long ago, these halls echoed with the chants of the faithful.",
    "The deeper you descend, the older the stones become.",
    "Many have sought the Amulet. Few have returned.",
    "The dungeon shifts and changes, but the Entity remains constant.",
    "Ancient runes mark this place as cursed ground.",
    "Treasure hunters came here seeking glory. They found only death.",
]

WARNING_MESSAGES = [
    "Beware: Dangerous creatures ahead!",
    "Warning: The path beyond is treacherous.",
    "Caution: Traps have been reported in this area.",
    "Turn back now, or face certain doom!",
    "Those who proceed beyond this point rarely return.",
    "The air grows thick with malice. Proceed with care.",
    "Strong monsters guard the treasure within.",
]

HUMOR_MESSAGES = [
    "Free treasure! (Just kidding. There's a troll.)",
    "If you can read this, you're standing too close to danger.",
    "Achievement unlocked: Reading Signs",
    "The Entity put this sign here just to mess with you.",
    "Beware of... actually, never mind. You'll find out.",
    "Welcome to the dungeon! Please die quietly.",
    "Exit: That way →  (Spoiler: There is no exit)",
    "This sign was placed by the previous adventurer. RIP.",
]

HINT_MESSAGES = [
    "Check the walls for hidden passages...",
    "Not all chests are what they seem.",
    "The key lies with the guardian nearby.",
    "Some secrets reveal themselves to the patient.",
    "Look for cracks in the stonework.",
    "Rings of power can reveal hidden truths.",
    "The vault is protected, but not impenetrable.",
]

DIRECTIONAL_MESSAGES = [
    "Stairs down this way →",
    "Treasury: North",
    "Exit: Probably not this way",
    "Boss Room: Straight ahead (Good luck!)",
    "Shops: One level down",
]


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
    def get_random_message(sign_type: str) -> str:
        """Get a random message for the specified sign type.
        
        Args:
            sign_type: Type of sign to get message for
            
        Returns:
            Random message string
        """
        import random
        
        message_pools = {
            'lore': LORE_MESSAGES,
            'warning': WARNING_MESSAGES,
            'humor': HUMOR_MESSAGES,
            'hint': HINT_MESSAGES,
            'directional': DIRECTIONAL_MESSAGES
        }
        
        pool = message_pools.get(sign_type, LORE_MESSAGES)
        return random.choice(pool)
    
    def __repr__(self):
        return (
            f"Signpost(type={self.sign_type}, "
            f"read={self.has_been_read})"
        )

