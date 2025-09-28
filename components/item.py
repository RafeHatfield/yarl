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
        self, use_function=None, targeting=False, targeting_message=None, **kwargs
    ):
        """Initialize an Item component.

        Args:
            use_function (callable, optional): Function to call when used
            targeting (bool, optional): Whether item requires targeting. Defaults to False.
            targeting_message (Message, optional): Message for targeting mode
            **kwargs: Additional arguments passed to the use function
        """

        self.use_function = use_function
        self.targeting = targeting
        self.targeting_message = targeting_message
        self.function_kwargs = kwargs
        self.owner = None  # Will be set by Entity when component is registered
