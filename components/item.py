from typing import Optional, Callable, Any, Dict

from components.component_registry import ComponentType


class Item:
    """Component that makes an entity usable as an item.

    This component defines how an entity behaves when used from inventory.
    It can have use functions (for consumables), targeting behavior (for spells),
    and additional parameters for the use function.

    Attributes:
        use_function (callable): Function to call when item is used
        targeting (bool): Whether this item requires targeting
        targeting_message (Message): Message to show during targeting
        function_kwargs (dict): Additional arguments for the use function
        owner (Entity): The entity that owns this component
        identified (bool): Whether the item has been identified
        appearance (Optional[str]): Unidentified name (e.g., "cyan potion", "KIRJE XIXAXA scroll")
        item_category (str): Category for identification ("scroll", "potion", "ring", "wand", "other")
        stackable (bool): Whether this item can stack with identical items
        quantity (int): Number of items in this stack
    """

    def __init__(
        self, 
        use_function: Optional[Callable] = None, 
        targeting: bool = False, 
        targeting_message: Optional[Any] = None,
        identified: bool = True,
        appearance: Optional[str] = None,
        item_category: str = "other",
        stackable: bool = True,
        quantity: int = 1,
        **kwargs: Any
    ) -> None:
        """Initialize an Item component.

        Args:
            use_function (Optional[Callable], optional): Function to call when used
            targeting (bool, optional): Whether item requires targeting. Defaults to False.
            targeting_message (Optional[Any], optional): Message for targeting mode (Message type)
            identified (bool, optional): Whether item starts identified. Defaults to True.
            appearance (Optional[str], optional): Unidentified display name. Defaults to None.
            item_category (str, optional): Category for identification. Defaults to "other".
            stackable (bool, optional): Whether item can stack. Defaults to True.
            quantity (int, optional): Number of items in stack. Defaults to 1.
            **kwargs: Additional arguments passed to the use function
        
        Returns:
            None
        """
        self.use_function: Optional[Callable] = use_function
        self.targeting: bool = targeting
        self.targeting_message: Optional[Any] = targeting_message  # Message type
        self.function_kwargs: Dict[str, Any] = kwargs
        self.owner: Optional[Any] = None  # Entity, Will be set when component is registered
        
        # Item identification system
        self.identified: bool = identified
        self.appearance: Optional[str] = appearance
        self.item_category: str = item_category
        
        # Item stacking system
        self.stackable: bool = stackable
        self.quantity: int = max(1, quantity)  # Ensure quantity is at least 1
    
    def get_display_name(self, compact: bool = False, show_quantity: bool = True) -> str:
        """Get the display name for this item.
        
        Returns the appearance if unidentified, otherwise returns the owner's name.
        Includes quantity prefix if stacked (e.g., "5x Healing Potion").
        
        Args:
            compact: If True, returns a shorter version of the name for UI space constraints
            show_quantity: If True, includes quantity prefix for stacked items
        
        Returns:
            str: The name to display to the player
        """
        # Get base name
        base_name = ""
        if not self.identified and self.appearance:
            base_name = self.appearance
        elif self.owner:
            # Check if owner has get_display_name for compact wand names
            if compact and hasattr(self.owner, 'get_display_name'):
                base_name = self.owner.get_display_name(compact=True)
            else:
                base_name = self.owner.name
        else:
            base_name = "Unknown Item"
        
        # Add quantity prefix if stacked
        if show_quantity and self.stackable and self.quantity > 1:
            return f"{self.quantity}x {base_name}"
        
        return base_name
    
    def identify(self, entities=None) -> bool:
        """Identify this item and register its type globally.
        
        When one instance of an item type is identified, ALL instances of that
        type should become identified. This method registers the type globally
        and updates all other items of the same type.
        
        Args:
            entities: Optional list of all game entities to update
        
        Returns:
            bool: True if item was previously unidentified, False if already identified
        """
        was_unidentified = not self.identified
        self.identified = True
        
        # Register this item type globally if we have owner information
        if was_unidentified and self.owner:
            from config.identification_manager import get_identification_manager
            id_manager = get_identification_manager()
            # Get the item type from the owner's name (e.g., "healing_potion")
            item_type = self.owner.name.lower().replace(' ', '_')
            id_manager.identify_type(item_type)
            
            # Update all other items of the same type
            if entities:
                for entity in entities:
                    if hasattr(entity, 'item') and entity.get_component_optional(ComponentType.ITEM) and entity != self.owner:
                        # Check if this item is the same type
                        other_item_type = entity.name.lower().replace(' ', '_')
                        if other_item_type == item_type:
                            entity.item.identified = True
        
        return was_unidentified
