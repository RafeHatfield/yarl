from typing import Optional, Callable, Any, Dict


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
    """

    def __init__(
        self, 
        use_function: Optional[Callable] = None, 
        targeting: bool = False, 
        targeting_message: Optional[Any] = None,
        identified: bool = True,
        appearance: Optional[str] = None,
        item_category: str = "other",
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
    
    def get_display_name(self, compact: bool = False) -> str:
        """Get the display name for this item.
        
        Returns the appearance if unidentified, otherwise returns the owner's name.
        The compact parameter can be used for abbreviated names (e.g., wands).
        
        Args:
            compact: If True, returns a shorter version of the name for UI space constraints
        
        Returns:
            str: The name to display to the player
        """
        if not self.identified and self.appearance:
            return self.appearance
        
        if self.owner:
            # Check if owner has get_display_name for compact wand names
            if compact and hasattr(self.owner, 'get_display_name'):
                return self.owner.get_display_name(compact=True)
            return self.owner.name
        
        return "Unknown Item"
    
    def identify(self) -> bool:
        """Identify this item.
        
        Returns:
            bool: True if item was previously unidentified, False if already identified
        """
        was_unidentified = not self.identified
        self.identified = True
        return was_unidentified
