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
    """

    def __init__(
        self, use_function: Optional[Callable] = None, targeting: bool = False, 
        targeting_message: Optional[Any] = None, **kwargs: Any
    ) -> None:
        """Initialize an Item component.

        Args:
            use_function (Optional[Callable], optional): Function to call when used
            targeting (bool, optional): Whether item requires targeting. Defaults to False.
            targeting_message (Optional[Any], optional): Message for targeting mode (Message type)
            **kwargs: Additional arguments passed to the use function
        
        Returns:
            None
        """
        self.use_function: Optional[Callable] = use_function
        self.targeting: bool = targeting
        self.targeting_message: Optional[Any] = targeting_message  # Message type
        self.function_kwargs: Dict[str, Any] = kwargs
        self.owner: Optional[Any] = None  # Entity, Will be set when component is registered
