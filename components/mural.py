"""Mural & Inscription Component System.

This module provides the mural/inscription component for environmental storytelling.
Murals are wall-mounted visual depictions of scenes from the dungeon's history,
providing atmospheric lore about Zhyraxion, Aurelyn, and the Crimson Order.

Mural text is loaded from config/murals_inscriptions.yaml and can be filtered
by dungeon depth for contextual story progression.

Example:
    >>> mural = Entity(10, 10, 'M', (220, 20, 60), 'Mural')
    >>> mural.mural = Mural("A golden dragon descends from the sky...")
    >>> results = mural.mural.examine(player)
"""

from typing import TYPE_CHECKING, Dict, Any, List

from components.map_feature import MapFeature, MapFeatureType

if TYPE_CHECKING:


class Mural(MapFeature):
    """Component for murals and wall inscriptions.
    
    Murals provide environmental storytelling through visual depictions
    and carved inscriptions. They reveal the tragic backstory of Zhyraxion,
    Aurelyn, and the ritual that imprisoned them.
    
    Attributes:
        text: The description of the mural scene
        mural_id: Unique identifier for this mural (for easter egg tracking)
        has_been_examined: Whether the player has examined this mural
    """
    
    def __init__(
        self,
        text: str,
        mural_id: str = ""
    ):
        """Initialize a mural component.
        
        Args:
            text: The text description of the mural scene
            mural_id: Unique identifier for tracking (optional)
        """
        super().__init__(
            feature_type=MapFeatureType.MURAL,
            discovered=True,  # Murals are visible by default
            interactable=True
        )
        
        self.text = text
        self.mural_id = mural_id
        self.has_been_examined = False
    
    def examine(self, actor: 'Entity') -> List[Dict[str, Any]]:
        """Examine the mural in detail.
        
        Args:
            actor: Entity examining the mural (usually the player)
            
        Returns:
            List of result dictionaries with the mural description
        """
        results = []
        
        if not self.can_interact():
            from message_builder import MessageBuilder as MB
            results.append({
                'message': MB.warning("You can't examine that right now.")
            })
            return results
        
        self.has_been_examined = True
        
        # Format mural message
        from message_builder import MessageBuilder as MB
        
        # Use a distinctive color for mural text (violet/magenta)
        formatted_message = MB.custom(
            f"Mural:\n{self.text}",
            (200, 100, 200)
        )
        
        results.append({
            'mural_examined': True,
            'message': formatted_message,
            'mural_id': self.mural_id
        })
        
        return results
    
    def get_description(self) -> str:
        """Get description of the mural.
        
        Returns:
            String description for tooltips
        """
        if self.has_been_examined:
            return "Mural (examined)"
        return "Mural (unexamined)"
    
    @staticmethod
    def get_random_mural(depth: int = 1) -> tuple:
        """Get a random mural for the specified depth.
        
        Murals are loaded from config/murals_inscriptions.yaml and filtered
        by dungeon depth to provide contextual storytelling.
        
        Args:
            depth: Current dungeon level (for depth-specific murals)
            
        Returns:
            Tuple of (mural_text, mural_id) or (None, None) if no mural found
        """
        from config.murals_registry import get_murals_registry
        
        registry = get_murals_registry()
        return registry.get_random_mural(depth)
    
    def __repr__(self):
        return (
            f"Mural(id={self.mural_id}, "
            f"examined={self.has_been_examined})"
        )

