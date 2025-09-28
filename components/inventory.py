from game_messages import Message


class Inventory:
    """Component that manages an entity's item storage and usage.

    This component handles adding, removing, using, and dropping items.
    It enforces capacity limits and integrates with the equipment system
    for equippable items.

    Attributes:
        capacity (int): Maximum number of items that can be stored
        items (list): List of Entity objects representing stored items
        owner (Entity): The entity that owns this inventory component
    """

    def __init__(self, capacity):
        """Initialize an Inventory component.

        Args:
            capacity (int): Maximum number of items this inventory can hold
        """
        self.capacity = capacity
        self.items = []
        self.owner = None  # Will be set by Entity when component is registered

    def add_item(self, item):
        """Add an item to the inventory.

        Attempts to add an item to the inventory if there's space available.
        Returns appropriate messages for success or failure.

        Args:
            item (Entity): The item entity to add to inventory

        Returns:
            list: List of result dictionaries with 'item_added' and 'message' keys
        """
        results = []

        if len(self.items) >= self.capacity:
            results.append(
                {
                    "item_added": None,
                    "message": Message(
                        "You cannot carry any more, your inventory is full",
                        (255, 255, 0),
                    ),
                }
            )
        else:
            results.append(
                {
                    "item_added": item,
                    "message": Message(
                        "You pick up the {0}!".format(item.name), (0, 0, 255)
                    ),
                }
            )

            self.items.append(item)

        return results

    def use(self, item_entity, **kwargs):
        """Use an item from the inventory.

        Attempts to use an item, either by calling its use function (for consumables)
        or by equipping it (for equippable items). Handles both cases appropriately.

        Args:
            item_entity (Entity): The item entity to use
            **kwargs: Additional arguments passed to item use functions

        Returns:
            list: List of result dictionaries with usage results and messages
        """
        results = []

        item_component = item_entity.item

        if item_component.use_function is None:
            equippable_component = item_entity.equippable

            if equippable_component:
                results.append({"equip": item_entity})
            else:
                results.append(
                    {
                        "message": Message(
                            "The {0} cannot be used".format(item_entity.name),
                            (255, 255, 0),
                        )
                    }
                )
        else:
            if item_component.targeting and not (
                kwargs.get("target_x") or kwargs.get("target_y")
            ):
                results.append({"targeting": item_entity})
            else:
                kwargs = {**item_component.function_kwargs, **kwargs}
                item_use_results = item_component.use_function(self.owner, **kwargs)

                for item_use_result in item_use_results:
                    if item_use_result.get("consumed"):
                        remove_results = self.remove_item(item_entity)
                        # If removal failed, add the error to results
                        if not remove_results[0].get("item_removed"):
                            results.extend(remove_results)

                results.extend(item_use_results)

        return results

    def remove_item(self, item):
        """Remove an item from the inventory.

        Removes the specified item from the inventory if it exists.
        Returns appropriate success or error messages.

        Args:
            item (Entity): The item entity to remove

        Returns:
            list: List of result dictionaries with removal results and messages
        """
        """Remove item from inventory. Returns results instead of raising errors."""
        results = []

        if item and item in self.items:
            self.items.remove(item)
            results.append({"item_removed": item})
        else:
            item_name = item.name if item and hasattr(item, "name") else "Unknown item"
            results.append(
                {
                    "item_removed": None,
                    "message": Message(
                        "Cannot remove {0}: not in inventory".format(item_name),
                        (255, 255, 0),
                    ),
                }
            )

        return results

    def drop_item(self, item):
        """Drop an item from the inventory onto the ground.

        Removes an item from inventory and places it at the owner's location.
        Automatically unequips the item if it was equipped.

        Args:
            item (Entity): The item entity to drop

        Returns:
            list: List of result dictionaries with drop results and messages
        """
        """Drop item from inventory."""
        results = []

        # Check if item is equipped and unequip it
        if (
            item
            and self.owner.equipment
            and (
                self.owner.equipment.main_hand == item
                or self.owner.equipment.off_hand == item
            )
        ):
            self.owner.equipment.toggle_equip(item)

        remove_results = self.remove_item(item)
        if remove_results[0].get("item_removed"):
            # Item was successfully removed
            item.x = self.owner.x
            item.y = self.owner.y
            results.append(
                {
                    "item_dropped": item,
                    "message": Message(
                        "You dropped the {0}".format(item.name), (255, 255, 0)
                    ),
                }
            )
        else:
            # Item removal failed, pass through the error
            results.extend(remove_results)

        return results
