"""
Unit tests for components/inventory.py

Tests inventory management including adding, removing, and using items.
"""
import pytest
from unittest.mock import Mock, patch
from components.inventory import Inventory
from components.item import Item
from item_functions import heal, cast_fireball
from entity import Entity
from game_messages import Message
from render_functions import RenderOrder


class TestInventoryBasics:
    """Test basic inventory functionality."""
    
    def test_inventory_creation(self):
        """Test basic inventory creation."""
        # Act
        inventory = Inventory(capacity=10)
        
        # Assert
        assert inventory.capacity == 10
        assert len(inventory.items) == 0
        # Note: Inventory doesn't have owner attribute until assigned to entity

    def test_inventory_with_owner(self, player_entity):
        """Test inventory with owner assignment."""
        # Arrange
        inventory = Inventory(capacity=26)
        
        # Act
        inventory.owner = player_entity
        
        # Assert
        assert inventory.owner == player_entity

    def test_inventory_zero_capacity(self):
        """Test inventory with zero capacity."""
        # Act
        inventory = Inventory(capacity=0)
        
        # Assert
        assert inventory.capacity == 0
        assert len(inventory.items) == 0


class TestInventoryAddItem:
    """Test adding items to inventory."""
    
    def test_add_item_success(self, basic_inventory, healing_potion, mock_libtcod):
        """Test successfully adding an item to inventory."""
        # Act
        results = basic_inventory.add_item(healing_potion)
        
        # Assert
        assert len(results) == 1
        assert 'item_added' in results[0]
        assert results[0]['item_added'] == healing_potion
        assert 'message' in results[0]
        assert healing_potion in basic_inventory.items
        assert len(basic_inventory.items) == 1

    def test_add_item_inventory_full(self, healing_potion, mock_libtcod):
        """Test adding item when inventory is full."""
        # Arrange
        inventory = Inventory(capacity=1)
        existing_item = Entity(0, 0, '!', mock_libtcod.violet, 'Existing Potion', 
                              render_order=RenderOrder.ITEM, item=Item())
        inventory.items.append(existing_item)
        
        # Act
        results = inventory.add_item(healing_potion)
        
        # Assert
        assert len(results) == 1
        assert 'item_added' not in results[0]
        assert 'message' in results[0]
        assert 'full' in results[0]['message'].text.lower()
        assert healing_potion not in inventory.items
        assert len(inventory.items) == 1  # Still only the existing item

    def test_add_multiple_items(self, basic_inventory, healing_potion, fireball_scroll):
        """Test adding multiple items to inventory."""
        # Act
        results1 = basic_inventory.add_item(healing_potion)
        results2 = basic_inventory.add_item(fireball_scroll)
        
        # Assert
        assert len(basic_inventory.items) == 2
        assert healing_potion in basic_inventory.items
        assert fireball_scroll in basic_inventory.items
        assert len(results1) == 1
        assert len(results2) == 1

    def test_add_same_item_twice(self, basic_inventory, healing_potion):
        """Test adding the same item instance twice."""
        # Act
        results1 = basic_inventory.add_item(healing_potion)
        results2 = basic_inventory.add_item(healing_potion)
        
        # Assert
        # Item should only appear once in inventory
        assert basic_inventory.items.count(healing_potion) == 1
        assert len(basic_inventory.items) == 1

    def test_add_item_none(self, basic_inventory):
        """Test adding None as an item."""
        # Act & Assert
        with pytest.raises(AttributeError):
            basic_inventory.add_item(None)

    def test_add_item_to_exact_capacity(self, healing_potion, mock_libtcod):
        """Test filling inventory to exact capacity."""
        # Arrange
        inventory = Inventory(capacity=2)
        item2 = Entity(0, 0, '!', mock_libtcod.violet, 'Potion 2', 
                      render_order=RenderOrder.ITEM, item=Item())
        item3 = Entity(0, 0, '!', mock_libtcod.violet, 'Potion 3', 
                      render_order=RenderOrder.ITEM, item=Item())
        
        # Act
        results1 = inventory.add_item(healing_potion)
        results2 = inventory.add_item(item2)
        results3 = inventory.add_item(item3)  # Should fail
        
        # Assert
        assert len(inventory.items) == 2
        assert 'item_added' in results1[0]
        assert 'item_added' in results2[0]
        assert 'item_added' not in results3[0]


class TestInventoryRemoveItem:
    """Test removing items from inventory."""
    
    def test_remove_item_success(self, basic_inventory, healing_potion):
        """Test successfully removing an item from inventory."""
        # Arrange
        basic_inventory.add_item(healing_potion)
        
        # Act
        basic_inventory.remove_item(healing_potion)
        
        # Assert
        assert healing_potion not in basic_inventory.items
        assert len(basic_inventory.items) == 0

    def test_remove_item_not_in_inventory(self, basic_inventory, healing_potion):
        """Test removing an item that's not in inventory."""
        # Act & Assert - should not raise exception
        basic_inventory.remove_item(healing_potion)
        assert len(basic_inventory.items) == 0

    def test_remove_item_multiple_items(self, basic_inventory, healing_potion, fireball_scroll):
        """Test removing one item when multiple items exist."""
        # Arrange
        basic_inventory.add_item(healing_potion)
        basic_inventory.add_item(fireball_scroll)
        
        # Act
        basic_inventory.remove_item(healing_potion)
        
        # Assert
        assert healing_potion not in basic_inventory.items
        assert fireball_scroll in basic_inventory.items
        assert len(basic_inventory.items) == 1

    def test_remove_none_item(self, basic_inventory):
        """Test removing None from inventory."""
        # Act & Assert - should not raise exception
        basic_inventory.remove_item(None)
        assert len(basic_inventory.items) == 0


class TestInventoryUseItem:
    """Test using items from inventory."""
    
    def test_use_healing_potion(self, player_entity, healing_potion, mock_libtcod):
        """Test using a healing potion."""
        # Arrange
        player_entity.inventory.add_item(healing_potion)
        player_entity.fighter.hp = 10  # Injured
        
        # Act
        results = player_entity.inventory.use(healing_potion)
        
        # Assert
        assert len(results) >= 1
        # Check if healing occurred
        assert player_entity.fighter.hp > 10
        # Item should be removed after use
        assert healing_potion not in player_entity.inventory.items

    def test_use_targeting_item_without_target(self, player_entity, fireball_scroll, mock_libtcod):
        """Test using a targeting item without providing target coordinates."""
        # Arrange
        player_entity.inventory.add_item(fireball_scroll)
        
        # Act
        results = player_entity.inventory.use(fireball_scroll)
        
        # Assert
        assert len(results) == 1
        assert 'targeting' in results[0]
        assert results[0]['targeting'] == fireball_scroll
        # Item should still be in inventory (not consumed yet)
        assert fireball_scroll in player_entity.inventory.items

    def test_use_targeting_item_with_target(self, player_entity, fireball_scroll, mock_fov_map, mock_libtcod):
        """Test using a targeting item with target coordinates."""
        # Arrange
        player_entity.inventory.add_item(fireball_scroll)
        entities = [player_entity]
        
        # Act
        results = player_entity.inventory.use(
            fireball_scroll, 
            entities=entities, 
            fov_map=mock_fov_map,
            target_x=15, 
            target_y=15
        )
        
        # Assert
        assert len(results) >= 1
        # Should find a consumed result
        consumed_result = next((r for r in results if 'consumed' in r), None)
        assert consumed_result is not None
        # Item should be removed after successful use
        assert fireball_scroll not in player_entity.inventory.items

    def test_use_item_with_no_use_function(self, player_entity, mock_libtcod):
        """Test using an item with no use function."""
        # Arrange
        unusable_item = Entity(0, 0, '?', mock_libtcod.white, 'Unusable Item',
                              render_order=RenderOrder.ITEM, item=Item(use_function=None))
        player_entity.inventory.add_item(unusable_item)
        
        # Act
        results = player_entity.inventory.use(unusable_item)
        
        # Assert
        assert len(results) == 1
        assert 'message' in results[0]
        assert 'cannot be used' in results[0]['message'].text.lower()
        # Item should remain in inventory
        assert unusable_item in player_entity.inventory.items

    def test_use_item_not_in_inventory(self, player_entity, healing_potion):
        """Test using an item that's not in inventory."""
        # Act
        results = player_entity.inventory.use(healing_potion)
        
        # Assert
        # Should handle gracefully - the item component will still try to execute
        assert len(results) >= 1

    def test_use_item_function_kwargs(self, player_entity, mock_libtcod):
        """Test using an item with function kwargs."""
        # Arrange
        special_item = Entity(
            0, 0, '*', mock_libtcod.gold, 'Special Item',
            render_order=RenderOrder.ITEM,
            item=Item(use_function=heal, amount=25)  # Custom amount
        )
        player_entity.inventory.add_item(special_item)
        player_entity.fighter.hp = 1  # Very injured
        
        # Act
        results = player_entity.inventory.use(special_item)
        
        # Assert
        assert len(results) >= 1
        assert player_entity.fighter.hp == 26  # 1 + 25


class TestInventoryDropItem:
    """Test dropping items from inventory."""
    
    def test_drop_item_success(self, player_entity, healing_potion):
        """Test successfully dropping an item."""
        # Arrange
        player_entity.inventory.add_item(healing_potion)
        player_entity.x = 5
        player_entity.y = 10
        
        # Act
        results = player_entity.inventory.drop_item(healing_potion)
        
        # Assert
        assert len(results) == 1
        assert 'item_dropped' in results[0]
        assert results[0]['item_dropped'] == healing_potion
        assert 'message' in results[0]
        # Item should be removed from inventory
        assert healing_potion not in player_entity.inventory.items
        # Item should be placed at player's location
        assert healing_potion.x == 5
        assert healing_potion.y == 10

    def test_drop_item_not_in_inventory(self, player_entity, healing_potion):
        """Test dropping an item that's not in inventory."""
        # Act
        results = player_entity.inventory.drop_item(healing_potion)
        
        # Assert
        # Should handle gracefully - item will still be "dropped"
        assert len(results) == 1
        assert 'item_dropped' in results[0]

    def test_drop_multiple_items(self, player_entity, healing_potion, fireball_scroll):
        """Test dropping multiple items."""
        # Arrange
        player_entity.inventory.add_item(healing_potion)
        player_entity.inventory.add_item(fireball_scroll)
        
        # Act
        results1 = player_entity.inventory.drop_item(healing_potion)
        results2 = player_entity.inventory.drop_item(fireball_scroll)
        
        # Assert
        assert len(player_entity.inventory.items) == 0
        assert len(results1) == 1
        assert len(results2) == 1

    def test_drop_none_item(self, player_entity):
        """Test dropping None item."""
        # Act & Assert
        with pytest.raises(AttributeError):
            player_entity.inventory.drop_item(None)


class TestInventoryEdgeCases:
    """Test edge cases and error conditions for inventory."""
    
    def test_inventory_negative_capacity(self):
        """Test inventory with negative capacity."""
        # Act
        inventory = Inventory(capacity=-5)
        
        # Assert
        assert inventory.capacity == -5
        # Should behave as if full (can't add items)

    def test_inventory_massive_capacity(self):
        """Test inventory with very large capacity."""
        # Act
        inventory = Inventory(capacity=999999)
        
        # Assert
        assert inventory.capacity == 999999
        assert len(inventory.items) == 0

    def test_use_item_with_missing_owner(self, healing_potion):
        """Test using item with inventory that has no owner."""
        # Arrange
        inventory = Inventory(capacity=10)
        inventory.add_item(healing_potion)
        
        # Act & Assert
        with pytest.raises(AttributeError):
            inventory.use(healing_potion)

    def test_drop_item_with_missing_owner(self, healing_potion):
        """Test dropping item with inventory that has no owner."""
        # Arrange
        inventory = Inventory(capacity=10)
        inventory.add_item(healing_potion)
        
        # Act & Assert
        with pytest.raises(AttributeError):
            inventory.drop_item(healing_potion)

    def test_inventory_str_representation(self):
        """Test string representation of inventory."""
        # Arrange
        inventory = Inventory(capacity=10)
        
        # Act
        str_repr = str(inventory)
        
        # Assert - should not raise exception
        assert isinstance(str_repr, str)

    def test_inventory_with_duplicate_items(self, basic_inventory, mock_libtcod):
        """Test inventory behavior with multiple identical items."""
        # Arrange
        potion1 = Entity(0, 0, '!', mock_libtcod.violet, 'Healing Potion', 
                        render_order=RenderOrder.ITEM, item=Item(use_function=heal, amount=10))
        potion2 = Entity(0, 0, '!', mock_libtcod.violet, 'Healing Potion', 
                        render_order=RenderOrder.ITEM, item=Item(use_function=heal, amount=10))
        
        # Act
        basic_inventory.add_item(potion1)
        basic_inventory.add_item(potion2)
        
        # Assert
        assert len(basic_inventory.items) == 2
        assert potion1 in basic_inventory.items
        assert potion2 in basic_inventory.items
        assert potion1 != potion2  # Different instances
