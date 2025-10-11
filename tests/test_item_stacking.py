"""Tests for the item stacking system.

This test suite validates all aspects of the item stacking feature:
- Item component quantity and stackable fields
- Display name formatting with quantities
- Automatic stacking on pickup
- Quantity handling during use
- Quantity handling during drop
"""

import pytest
from unittest.mock import Mock

from entity import Entity
from components.item import Item
from components.inventory import Inventory
from components.component_registry import ComponentType
from item_functions import heal


class TestItemComponentStacking:
    """Test Item component stacking functionality."""
    
    def test_item_defaults_to_stackable(self):
        """Items should be stackable by default."""
        item_comp = Item()
        assert item_comp.stackable is True
        assert item_comp.quantity == 1
    
    def test_item_can_be_non_stackable(self):
        """Items can be created as non-stackable (e.g., equipment)."""
        item_comp = Item(stackable=False)
        assert item_comp.stackable is False
        assert item_comp.quantity == 1
    
    def test_item_quantity_minimum_enforced(self):
        """Item quantity should never be less than 1."""
        item_comp = Item(quantity=0)
        assert item_comp.quantity == 1
        
        item_comp2 = Item(quantity=-5)
        assert item_comp2.quantity == 1
    
    def test_item_quantity_can_be_set(self):
        """Item quantity can be set to any value >= 1."""
        item_comp = Item(quantity=5)
        assert item_comp.quantity == 5
        
        item_comp2 = Item(quantity=100)
        assert item_comp2.quantity == 100


class TestDisplayNames:
    """Test display name formatting with quantities."""
    
    def test_single_item_no_quantity_prefix(self):
        """Single items should not show quantity prefix."""
        entity = Entity(0, 0, '!', (255, 0, 0), "Healing Potion", 
                       item=Item(quantity=1, stackable=True))
        assert entity.item.get_display_name() == "Healing Potion"
    
    def test_stacked_items_show_quantity(self):
        """Stacked items should show quantity prefix."""
        entity = Entity(0, 0, '!', (255, 0, 0), "Healing Potion", 
                       item=Item(quantity=5, stackable=True))
        assert entity.item.get_display_name() == "5x Healing Potion"
    
    def test_non_stackable_no_quantity(self):
        """Non-stackable items should not show quantity prefix."""
        entity = Entity(0, 0, '/', (255, 255, 255), "Long Sword", 
                       item=Item(quantity=1, stackable=False))
        assert entity.item.get_display_name() == "Long Sword"
    
    def test_unidentified_stack_shows_quantity(self):
        """Unidentified stacks should show quantity with appearance."""
        entity = Entity(0, 0, '!', (255, 0, 0), "Healing Potion", 
                       item=Item(quantity=3, stackable=True, identified=False, 
                                appearance="cyan potion"))
        assert entity.item.get_display_name() == "3x cyan potion"
    
    def test_show_quantity_parameter_can_disable(self):
        """show_quantity parameter can disable quantity display."""
        entity = Entity(0, 0, '!', (255, 0, 0), "Healing Potion", 
                       item=Item(quantity=5, stackable=True))
        assert entity.item.get_display_name(show_quantity=False) == "Healing Potion"


class TestStackingOnPickup:
    """Test automatic stacking when items are picked up."""
    
    @pytest.fixture
    def player(self):
        """Create a test player with inventory."""
        player = Entity(0, 0, '@', (255, 255, 255), "Player")
        inventory = Inventory(capacity=10)
        inventory.owner = player
        player.inventory = inventory
        player.components.add(ComponentType.INVENTORY, inventory)
        return player
    
    @pytest.fixture
    def healing_potion(self):
        """Create a healing potion entity."""
        return Entity(5, 5, '!', (255, 0, 0), "Healing Potion",
                     item=Item(use_function=heal, stackable=True, quantity=1, amount=40))
    
    def test_first_item_added_normally(self, player, healing_potion):
        """First item should be added to inventory normally."""
        results = player.inventory.add_item(healing_potion)
        
        assert len(player.inventory.items) == 1
        assert player.inventory.items[0] == healing_potion
        assert healing_potion.item.quantity == 1
    
    def test_identical_items_stack(self, player):
        """Identical items should stack together."""
        potion1 = Entity(5, 5, '!', (255, 0, 0), "Healing Potion",
                        item=Item(use_function=heal, stackable=True, quantity=1))
        potion2 = Entity(6, 6, '!', (255, 0, 0), "Healing Potion",
                        item=Item(use_function=heal, stackable=True, quantity=1))
        
        player.inventory.add_item(potion1)
        results = player.inventory.add_item(potion2)
        
        # Should only have 1 stack in inventory
        assert len(player.inventory.items) == 1
        # Stack should have quantity 2
        assert player.inventory.items[0].item.quantity == 2
        # Should return item_consumed for the picked-up potion
        assert results[0].get("item_consumed") == potion2
    
    def test_different_items_dont_stack(self, player):
        """Different items should not stack together."""
        potion = Entity(5, 5, '!', (255, 0, 0), "Healing Potion",
                       item=Item(stackable=True, quantity=1))
        scroll = Entity(6, 6, '#', (255, 255, 0), "Fireball Scroll",
                       item=Item(stackable=True, quantity=1))
        
        player.inventory.add_item(potion)
        player.inventory.add_item(scroll)
        
        # Should have 2 separate items
        assert len(player.inventory.items) == 2
    
    def test_different_identification_status_dont_stack(self, player):
        """Items with different identification status should not stack."""
        potion1 = Entity(5, 5, '!', (255, 0, 0), "Healing Potion",
                        item=Item(stackable=True, identified=True, quantity=1))
        potion2 = Entity(6, 6, '!', (255, 0, 0), "Healing Potion",
                        item=Item(stackable=True, identified=False, 
                                 appearance="cyan potion", quantity=1))
        
        player.inventory.add_item(potion1)
        player.inventory.add_item(potion2)
        
        # Should have 2 separate stacks
        assert len(player.inventory.items) == 2
    
    def test_different_appearance_dont_stack(self, player):
        """Unidentified items with different appearances should not stack."""
        potion1 = Entity(5, 5, '!', (255, 0, 0), "Healing Potion",
                        item=Item(stackable=True, identified=False, 
                                 appearance="cyan potion", quantity=1))
        potion2 = Entity(6, 6, '!', (255, 0, 0), "Healing Potion",
                        item=Item(stackable=True, identified=False, 
                                 appearance="red potion", quantity=1))
        
        player.inventory.add_item(potion1)
        player.inventory.add_item(potion2)
        
        # Should have 2 separate stacks
        assert len(player.inventory.items) == 2
    
    def test_stacking_multiple_quantities(self, player):
        """Stacking should work with items that have quantity > 1."""
        potion1 = Entity(5, 5, '!', (255, 0, 0), "Healing Potion",
                        item=Item(stackable=True, quantity=3))
        potion2 = Entity(6, 6, '!', (255, 0, 0), "Healing Potion",
                        item=Item(stackable=True, quantity=2))
        
        player.inventory.add_item(potion1)
        player.inventory.add_item(potion2)
        
        # Should have 1 stack with quantity 5
        assert len(player.inventory.items) == 1
        assert player.inventory.items[0].item.quantity == 5


class TestStackedItemUsage:
    """Test using items from stacks."""
    
    @pytest.fixture
    def player(self):
        """Create a test player with inventory."""
        player = Entity(0, 0, '@', (255, 255, 255), "Player")
        inventory = Inventory(capacity=10)
        inventory.owner = player
        player.inventory = inventory
        player.components.add(ComponentType.INVENTORY, inventory)
        return player
    
    def test_using_from_stack_decrements_quantity(self, player):
        """Using an item from a stack should decrement quantity."""
        # Create a mock item that will be consumed
        mock_use_function = Mock(return_value=[{"consumed": True}])
        potion = Entity(5, 5, '!', (255, 0, 0), "Healing Potion",
                       item=Item(use_function=mock_use_function, stackable=True, quantity=3))
        
        player.inventory.add_item(potion)
        player.inventory.use(potion)
        
        # Should still have the item in inventory
        assert potion in player.inventory.items
        # But quantity should be decremented
        assert potion.item.quantity == 2
    
    def test_using_last_item_removes_from_inventory(self, player):
        """Using the last item in a stack should remove it from inventory."""
        mock_use_function = Mock(return_value=[{"consumed": True}])
        potion = Entity(5, 5, '!', (255, 0, 0), "Healing Potion",
                       item=Item(use_function=mock_use_function, stackable=True, quantity=1))
        
        player.inventory.add_item(potion)
        player.inventory.use(potion)
        
        # Should be removed from inventory
        assert potion not in player.inventory.items


class TestStackedItemDrop:
    """Test dropping items from stacks."""
    
    @pytest.fixture
    def player(self):
        """Create a test player with inventory and no equipment component."""
        player = Entity(0, 0, '@', (255, 255, 255), "Player")
        inventory = Inventory(capacity=10)
        inventory.owner = player
        player.inventory = inventory
        player.components.add(ComponentType.INVENTORY, inventory)
        player.equipment = None  # No equipment to simplify tests
        return player
    
    def test_drop_one_from_stack(self, player):
        """Dropping one item from a stack should create a new entity."""
        potion = Entity(5, 5, '!', (255, 0, 0), "Healing Potion",
                       item=Item(stackable=True, quantity=5))
        
        player.inventory.add_item(potion)
        results = player.inventory.drop_item(potion, quantity=1)
        
        # Should still have the stack in inventory
        assert potion in player.inventory.items
        # But with decremented quantity
        assert potion.item.quantity == 4
        # Should return a new dropped item
        dropped = results[0].get("item_dropped")
        assert dropped is not None
        assert dropped != potion  # Different entity
        assert dropped.item.quantity == 1
    
    def test_drop_entire_stack(self, player):
        """Dropping entire stack should remove from inventory."""
        potion = Entity(5, 5, '!', (255, 0, 0), "Healing Potion",
                       item=Item(stackable=True, quantity=5))
        
        player.inventory.add_item(potion)
        results = player.inventory.drop_item(potion, quantity=5)
        
        # Should be removed from inventory
        assert potion not in player.inventory.items
        # Should return the same item
        dropped = results[0].get("item_dropped")
        assert dropped == potion
        assert dropped.item.quantity == 5
    
    def test_drop_default_quantity_is_one(self, player):
        """Drop should default to quantity=1."""
        potion = Entity(5, 5, '!', (255, 0, 0), "Healing Potion",
                       item=Item(stackable=True, quantity=5))
        
        player.inventory.add_item(potion)
        results = player.inventory.drop_item(potion)  # No quantity specified
        
        # Should still have 4 in inventory
        assert potion.item.quantity == 4
        # Should drop 1
        dropped = results[0].get("item_dropped")
        assert dropped.item.quantity == 1


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_non_stackable_items_behave_normally(self):
        """Non-stackable items should work as before."""
        sword = Entity(5, 5, '/', (255, 255, 255), "Long Sword",
                      item=Item(stackable=False, quantity=1))
        
        # Should not show quantity in name
        assert sword.item.get_display_name() == "Long Sword"
        # Quantity should still be 1
        assert sword.item.quantity == 1
    
    def test_equipment_is_not_stackable(self):
        """Equipment items should typically be non-stackable."""
        # This is more of a convention test - equipment created elsewhere
        # should have stackable=False by default
        from components.equippable import Equippable
        from equipment_slots import EquipmentSlots
        
        sword = Entity(5, 5, '/', (255, 255, 255), "Long Sword",
                      equippable=Equippable(slot=EquipmentSlots.MAIN_HAND, power_bonus=3),
                      item=Item(stackable=False))
        
        assert sword.item.stackable is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

