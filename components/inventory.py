from typing import List, Dict, Any, Optional
from game_messages import Message
from message_builder import MessageBuilder as MB
from components.component_registry import ComponentType


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

    def __init__(self, capacity: int) -> None:
        """Initialize an Inventory component.

        Args:
            capacity (int): Maximum number of items this inventory can hold
        """
        self.capacity: int = capacity
        self.items: List[Any] = []  # List of Entity objects
        self.owner: Optional[Any] = None  # Entity, Will be set when component is registered
    
    def _can_stack_with(self, item1: Any, item2: Any) -> bool:
        """Check if two items can be stacked together.
        
        Items can stack if they have:
        - Same base name
        - Same identification status
        - Same appearance (if unidentified)
        - Both are stackable
        
        Args:
            item1: First item entity
            item2: Second item entity
            
        Returns:
            bool: True if items can stack
        """
        # Must both have item components
        if not (hasattr(item1, 'item') and hasattr(item2, 'item')):
            return False
        
        item1_comp = item1.get_component_optional(ComponentType.ITEM)
        item2_comp = item2.get_component_optional(ComponentType.ITEM)
        
        # Must both be stackable
        if not (item1_comp.stackable and item2_comp.stackable):
            return False
        
        # Must have same name
        if item1.name != item2.name:
            return False
        
        # Must have same identification status
        if item1_comp.identified != item2_comp.identified:
            return False
        
        # If unidentified, must have same appearance
        if not item1_comp.identified and item1_comp.appearance != item2_comp.appearance:
            return False
        
        return True

    def add_item(self, item: Any) -> List[Dict[str, Any]]:
        """Add an item to the inventory.

        Attempts to add an item to the inventory if there's space available.
        
        Special merging behavior:
        - Wand + Wand: If picking up a wand and you have a matching wand (same spell),
          the new wand's charges are merged into the existing wand and the new wand is consumed.
        - Scroll + Wand: If picking up a scroll and you have a matching wand,
          the scroll automatically recharges the wand instead of being added.

        Args:
            item (Any): The item entity to add to inventory (Entity type)

        Returns:
            List[Dict[str, Any]]: List of result dictionaries with 'item_added' and 'message' keys
        """
        results = []

        if len(self.items) >= self.capacity:
            results.append(
                {
                    "item_added": None,
                    "message": MB.warning(
                        "You cannot carry any more, your inventory is full"
                    ),
                }
            )
        else:
            # Check for wand-to-wand merging
            # If picking up a wand, check if we already have a wand of the same type
            wand_merged = False
            pickup_wand = getattr(item, 'wand', None)
            if pickup_wand:
                # This is a wand! Look for matching wand in inventory
                for inv_item in self.items:
                    inv_wand = getattr(inv_item, 'wand', None)
                    if inv_wand and inv_wand.spell_type == pickup_wand.spell_type:
                        # Found a matching wand! Merge charges from new wand into existing wand
                        charges_gained = pickup_wand.charges
                        for _ in range(charges_gained):
                            inv_wand.add_charge()
                        wand_merged = True
                        
                        # Queue a sparkle visual effect at player's position
                        from visual_effect_queue import get_effect_queue
                        effect_queue = get_effect_queue()
                        effect_queue.queue_wand_recharge(self.owner.x, self.owner.y, self.owner)
                        
                        charge_word = "charge" if charges_gained == 1 else "charges"
                        # Get display names (respects identification)
                        item_display_name = item.get_display_name() if hasattr(item, 'get_display_name') else item.name
                        inv_item_display_name = inv_item.get_display_name() if hasattr(inv_item, 'get_display_name') else inv_item.name
                        
                        results.append({
                            "item_added": None,  # New wand was consumed, not added
                            "item_consumed": item,  # Signal that new wand should be removed from world
                            "message": MB.item_effect(
                                f"Your {item_display_name} glows brightly and vanishes! "
                                f"Your {inv_item_display_name} gains {charges_gained} {charge_word}. ({inv_wand.charges} charges)"
                            )
                        })
                        break
            
            # Check for scroll-to-wand recharge mechanic
            # If picking up a scroll, check if we have a matching wand
            scroll_recharged_wand = False
            if not wand_merged and item.get_component_optional(ComponentType.ITEM) and item.get_component_optional(ComponentType.ITEM).use_function:  # It's a usable item (likely a scroll)
                # Get the scroll's spell identifier (e.g., "fireball_scroll")
                scroll_name = item.name.lower().replace(' ', '_')
                
                # Look for matching wand in inventory
                for inv_item in self.items:
                    wand = getattr(inv_item, 'wand', None)
                    if wand and wand.spell_type == scroll_name:
                        # Found a matching wand! Recharge it with the scroll
                        wand.add_charge()
                        scroll_recharged_wand = True
                        
                        # Queue a sparkle visual effect at player's position
                        from visual_effect_queue import get_effect_queue
                        effect_queue = get_effect_queue()
                        effect_queue.queue_wand_recharge(self.owner.x, self.owner.y, self.owner)
                        
                        # Get display names (respects identification)
                        item_display_name = item.get_display_name() if hasattr(item, 'get_display_name') else item.name
                        inv_item_display_name = inv_item.get_display_name() if hasattr(inv_item, 'get_display_name') else inv_item.name
                        
                        results.append({
                            "item_added": None,  # Scroll was consumed, not added
                            "item_consumed": item,  # Signal that scroll should be removed from world
                            "message": MB.item_effect(
                                f"Your {item_display_name} glows brightly and vanishes! "
                                f"Your {inv_item_display_name} gains a charge. ({wand.charges} charges)"
                            )
                        })
                        break
            
            # If wand merged or scroll recharged a wand, don't add it to inventory
            # Otherwise, check for stacking or add normally
            if not wand_merged and not scroll_recharged_wand:
                # Check for stacking: Can we merge this with an existing item?
                stacked = False
                if item.get_component_optional(ComponentType.ITEM) and item.get_component_optional(ComponentType.ITEM).stackable:
                    for inv_item in self.items:
                        # Check if this is a stackable match
                        if (inv_item.get_component_optional(ComponentType.ITEM) and inv_item.get_component_optional(ComponentType.ITEM).stackable and
                            self._can_stack_with(item, inv_item)):
                            # Stack them! Increment quantity
                            quantity_to_add = item.get_component_optional(ComponentType.ITEM).quantity
                            inv_item.get_component_optional(ComponentType.ITEM).quantity += quantity_to_add
                            stacked = True
                            
                            # Get display name (respects identification)
                            item_display_name = item.get_display_name() if hasattr(item, 'get_display_name') else item.name
                            
                            results.append({
                                "item_added": inv_item,  # Reference to the stack we added to
                                "item_consumed": item,   # Signal to remove the picked-up item
                                "message": MB.item_pickup(
                                    "You pick up {0}x {1}! (now have {2})".format(
                                        quantity_to_add,
                                        item_display_name,
                                        inv_item.get_component_optional(ComponentType.ITEM).quantity
                                    )
                                ),
                            })
                            break
                
                # If not stacked, add as new item
                if not stacked:
                    # Get display name (respects identification for rings, potions, scrolls)
                    item_display_name = item.get_display_name() if hasattr(item, 'get_display_name') else item.name
                    
                    results.append(
                        {
                            "item_added": item,
                            "message": MB.item_pickup(
                                "You pick up the {0}!".format(item_display_name)
                            ),
                        }
                    )

                    self.items.append(item)
                
                # NEW: If we just picked up a wand, check for matching scrolls to consume
                wand = getattr(item, 'wand', None)
                if wand:
                    # This is a wand! Look for matching scrolls in inventory
                    scrolls_to_consume = []
                    for inv_item in self.items:
                        if inv_item == item:  # Skip the wand itself
                            continue
                        # Check if this is a scroll matching the wand's spell type
                        if inv_item.get_component_optional(ComponentType.ITEM) and inv_item.get_component_optional(ComponentType.ITEM).use_function:
                            scroll_name = inv_item.name.lower().replace(' ', '_')
                            if scroll_name == wand.spell_type:
                                scrolls_to_consume.append(inv_item)
                    
                    # Consume all matching scrolls
                    if scrolls_to_consume:
                        for scroll in scrolls_to_consume:
                            self.items.remove(scroll)
                            wand.add_charge()
                        
                        scroll_word = "scroll" if len(scrolls_to_consume) == 1 else "scrolls"
                        results.append({
                            "message": MB.item_effect(
                                f"Your {item.name} hungrily absorbs {len(scrolls_to_consume)} {scroll_word}! "
                                f"({wand.charges} charges)"
                            )
                        })

        return results

    def use(self, item_entity: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        """Use an item from the inventory.

        Attempts to use an item, either by calling its use function (for consumables)
        or by equipping it (for equippable items). Handles both cases appropriately.

        Args:
            item_entity (Any): The item entity to use (Entity type)
            **kwargs: Additional arguments passed to item use functions

        Returns:
            List[Dict[str, Any]]: List of result dictionaries with usage results and messages
        """
        results = []

        item_component = item_entity.get_component_optional(ComponentType.ITEM)

        if item_component.use_function is None:
            equippable_component = item_entity.equippable

            if equippable_component:
                results.append({"equip": item_entity})
            else:
                results.append(
                    {
                        "message": MB.warning(
                            "The {0} cannot be used".format(item_entity.name)
                        )
                    }
                )
        else:
            # Check if this is a wand FIRST (multi-use item)
            # Wands have special handling even if they have targeting=True
            wand_component = getattr(item_entity, 'wand', None)
            
            if wand_component:
                # Wand usage: consume charge instead of destroying item
                if wand_component.is_empty():
                    # Wand has no charges - can't use it
                    results.append({
                        "message": MB.warning(
                            f"The {item_entity.name} fizzles uselessly. It has no charges!"
                        )
                    })
                else:
                    # Cast the spell first to see if it succeeds
                    kwargs = {**item_component.function_kwargs, **kwargs}
                    # Pass the wand entity itself for items that need it (like Wand of Portals)
                    kwargs["wand_entity"] = item_entity
                    item_use_results = item_component.use_function(self.owner, **kwargs)
                    
                    # Check if spell was successfully consumed (meaning it worked)
                    spell_consumed = any(r.get("consumed") for r in item_use_results)
                    
                    if spell_consumed:
                        # Spell worked - consume a charge
                        wand_component.use_charge()
                    
                    # Don't remove the wand - it stays in inventory
                    # Pass through all messages/effects, but remove "consumed" flag (wands don't get consumed)
                    for item_use_result in item_use_results:
                        # Create a copy without the "consumed" key (wands stay in inventory)
                        filtered_result = {k: v for k, v in item_use_result.items() if k != "consumed"}
                        if filtered_result:  # Only append if there's something left (message, effects, etc.)
                            results.append(filtered_result)
                    
                    # Add a message showing remaining charges (only if spell was consumed)
                    if spell_consumed:
                        remaining_charges = wand_component.charges
                        if remaining_charges > 0:
                            results.append({
                                "message": MB.item_charge(
                                    f"The {item_entity.name} glows. ({remaining_charges} charges remaining)"
                                )
                            })
                        else:
                            results.append({
                                "message": MB.item_charge(
                                    f"The {item_entity.name} dims. (0 charges remaining)"
                                )
                            })
            elif item_component.targeting and not (
                kwargs.get("target_x") or kwargs.get("target_y")
            ):
                # Regular targeting item (not a wand) - enter targeting mode
                results.append({"targeting": item_entity})
            else:
                # Normal item usage (scrolls, potions): consume on use
                kwargs = {**item_component.function_kwargs, **kwargs}
                item_use_results = item_component.use_function(self.owner, **kwargs)
                
                # Check if item was successfully used (consumed)
                item_consumed = any(r.get("consumed") for r in item_use_results)
                
                # Identify item on successful use (before removal)
                if item_consumed and hasattr(item_component, 'identify'):
                    # Pass entities to identify so ALL items of this type get identified
                    entities = kwargs.get('entities', None)
                    was_unidentified = item_component.identify(entities=entities)
                    if was_unidentified:
                        # Add identification message
                        results.append({
                            "message": MB.item_pickup(
                                f"You now recognize this as {item_entity.name}!"
                            )
                        })

                for item_use_result in item_use_results:
                    if item_use_result.get("consumed"):
                        # METRICS: Track potion usage for soak stats
                        # Potions have char '!' (distinguish from scrolls which have '#')
                        if hasattr(item_entity, 'char') and item_entity.char == '!':
                            if self.owner and hasattr(self.owner, 'statistics') and self.owner.statistics:
                                self.owner.statistics.record_potion_used()
                        
                        # Handle stacked items: decrement quantity instead of removing
                        if item_component.stackable and item_component.quantity > 1:
                            item_component.quantity -= 1
                            # Don't remove, just decrement
                        else:
                            # Last one or not stackable - remove from inventory
                            remove_results = self.remove_item(item_entity)
                            # If removal failed, add the error to results
                            if not remove_results[0].get("item_removed"):
                                results.extend(remove_results)

                results.extend(item_use_results)

        return results

    def remove_item(self, item: Any) -> List[Dict[str, Any]]:
        """Remove an item from the inventory.

        Removes the specified item from the inventory if it exists.
        Returns appropriate success or error messages.

        Args:
            item (Any): The item entity to remove (Entity type)

        Returns:
            List[Dict[str, Any]]: List of result dictionaries with removal results and messages
        """
        results = []

        if item and item in self.items:
            self.items.remove(item)
            results.append({"item_removed": item})
        else:
            item_name = item.name if item and hasattr(item, "name") else "Unknown item"
            results.append(
                {
                    "item_removed": None,
                    "message": MB.warning(
                        "Cannot remove {0}: not in inventory".format(item_name)
                    ),
                }
            )

        return results

    def drop_item(self, item: Any, quantity: int = 1) -> List[Dict[str, Any]]:
        """Drop an item from the inventory onto the ground.

        For stacked items, drops the specified quantity (defaults to 1).
        Creates a new entity for the dropped portion.
        Automatically unequips the item if it was equipped.

        Args:
            item (Any): The item entity to drop (Entity type)
            quantity (int): How many to drop from a stack (defaults to 1)

        Returns:
            List[Dict[str, Any]]: List of result dictionaries with drop results and messages
        """
        results = []

        # Check if item is equipped and unequip it (only if dropping entire stack)
        if (
            item
            and self.owner.get_component_optional(ComponentType.EQUIPMENT)
            and (
                self.owner.get_component_optional(ComponentType.EQUIPMENT).main_hand == item
                or self.owner.get_component_optional(ComponentType.EQUIPMENT).off_hand == item
            )
        ):
            # Can only unequip if dropping the entire stack
            if not (hasattr(item, 'item') and item.get_component_optional(ComponentType.ITEM).stackable and item.get_component_optional(ComponentType.ITEM).quantity > quantity):
                self.owner.get_component_optional(ComponentType.EQUIPMENT).toggle_equip(item)
            else:
                # Can't drop part of an equipped stack
                results.append({
                    "item_dropped": None,
                    "message": MB.warning(
                        "You must unequip the {0} before dropping it".format(item.name)
                    )
                })
                return results

        # Handle stacked items
        if hasattr(item, 'item') and item.get_component_optional(ComponentType.ITEM).stackable and item.get_component_optional(ComponentType.ITEM).quantity > 1:
            drop_quantity = min(quantity, item.get_component_optional(ComponentType.ITEM).quantity)
            
            if drop_quantity < item.get_component_optional(ComponentType.ITEM).quantity:
                # Dropping part of the stack - create new entity for dropped portion
                from entity import Entity
                from copy import copy
                
                # Create a new entity with the same properties but quantity=drop_quantity
                dropped_item = Entity(
                    self.owner.x, self.owner.y,
                    item.char, item.color, item.name,
                    render_order=item.render_order
                )
                
                # Copy the item component
                dropped_item_component = copy(item.get_component_optional(ComponentType.ITEM))
                dropped_item_component.quantity = drop_quantity
                dropped_item_component.owner = dropped_item
                dropped_item.item = dropped_item_component
                dropped_item.components.add(ComponentType.ITEM, dropped_item_component)
                
                # Decrease quantity in inventory stack
                item.get_component_optional(ComponentType.ITEM).quantity -= drop_quantity
                
                quantity_word = f"{drop_quantity}x" if drop_quantity > 1 else "1"
                remaining = item.get_component_optional(ComponentType.ITEM).quantity
                results.append({
                    "item_dropped": dropped_item,
                    "message": MB.item_drop(
                        f"You dropped {quantity_word} {item.name} ({remaining} remaining)"
                    )
                })
            else:
                # Dropping entire stack - remove from inventory
                remove_results = self.remove_item(item)
                if remove_results[0].get("item_removed"):
                    item.x = self.owner.x
                    item.y = self.owner.y
                    results.append({
                        "item_dropped": item,
                        "message": MB.item_drop(
                            f"You dropped {item.get_component_optional(ComponentType.ITEM).quantity}x {item.name}"
                        )
                    })
                else:
                    results.extend(remove_results)
        else:
            # Non-stacked item - drop normally
            remove_results = self.remove_item(item)
            if remove_results[0].get("item_removed"):
                item.x = self.owner.x
                item.y = self.owner.y
                results.append({
                    "item_dropped": item,
                    "message": MB.item_drop(
                        "You dropped the {0}".format(item.name)
                    )
                })
            else:
                results.extend(remove_results)

        return results
