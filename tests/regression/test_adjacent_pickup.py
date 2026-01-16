"""Regression test for adjacent item pickup.

Bug: After chest interaction changes, picking up items near chests failed with
"Path is blocked by chest" because pickup required standing on the item tile.

Fix: Allow pickup from adjacency (8-neighbor), not just same tile.

This test ensures:
1. Items can be picked up from adjacent tiles
2. Chest loot can be picked up without stepping on chest tile
3. Items on same tile are prioritized over adjacent items
4. Selection is deterministic when multiple items are adjacent
"""

import pytest
from components.component_registry import ComponentType
from components.inventory import Inventory
from components.item import Item
from entity import Entity
from map_objects.game_map import GameMap
from render_functions import RenderOrder
from services.pickup_service import PickupService
from state_management.state_config import StateManager
from game_messages import MessageLog


class TestAdjacentPickup:
    """Test that items can be picked up from adjacent tiles."""
    
    @pytest.fixture
    def setup_pickup_test(self):
        """Create minimal game state for pickup testing."""
        # Create map
        game_map = GameMap(10, 10)
        game_map.initialize_tiles()
        for x in range(10):
            for y in range(10):
                game_map.tiles[x][y].blocked = False
                game_map.tiles[x][y].block_sight = False
        
        # Create player at (5, 5) with inventory
        player = Entity(5, 5, '@', (255, 255, 255), 'Player', blocks=True,
                       render_order=RenderOrder.ACTOR)
        player.inventory = Inventory(26)
        player.inventory.owner = player
        # Component auto-registered via __setattr__
        
        # Create state manager
        state_manager = StateManager()
        
        class GameState:
            def __init__(self):
                self.player = player
                self.entities = [player]
                self.game_map = game_map
                self.message_log = MessageLog(x=0, width=40, height=10)
        
        state_manager.state = GameState()
        
        return {
            'player': player,
            'game_map': game_map,
            'state_manager': state_manager,
            'entities': state_manager.state.entities
        }
    
    def test_pickup_from_same_tile(self, setup_pickup_test):
        """Test that pickup still works when standing on item (backward compatible)."""
        player = setup_pickup_test['player']
        entities = setup_pickup_test['entities']
        state_manager = setup_pickup_test['state_manager']
        
        # Create item at player's location (5, 5)
        item = Entity(5, 5, '!', (255, 0, 255), 'Potion', blocks=False,
                     render_order=RenderOrder.ITEM)
        item.item = Item(use_function=None)
        item.item.owner = item
        entities.append(item)
        
        # Execute pickup
        pickup_service = PickupService(state_manager)
        result = pickup_service.execute_pickup(source="test")
        
        # Verify pickup succeeded
        assert result.success is True, "Should pick up item on same tile"
        assert item not in entities, "Item should be removed from entities"
        assert item in player.inventory.items, "Item should be in inventory"
    
    def test_pickup_from_adjacent_orthogonal(self, setup_pickup_test):
        """Test that pickup works from orthogonal adjacent tiles (N, S, E, W)."""
        player = setup_pickup_test['player']
        entities = setup_pickup_test['entities']
        state_manager = setup_pickup_test['state_manager']
        
        # Create item at (6, 5) - east of player
        item = Entity(6, 5, '!', (255, 0, 255), 'Potion', blocks=False,
                     render_order=RenderOrder.ITEM)
        item.item = Item(use_function=None)
        item.item.owner = item
        entities.append(item)
        
        # Execute pickup
        pickup_service = PickupService(state_manager)
        result = pickup_service.execute_pickup(source="test")
        
        # Verify pickup succeeded
        assert result.success is True, "Should pick up item from adjacent tile"
        assert item not in entities, "Item should be removed from entities"
        assert item in player.inventory.items, "Item should be in inventory"
    
    def test_pickup_from_adjacent_diagonal(self, setup_pickup_test):
        """Test that pickup works from diagonal adjacent tiles."""
        player = setup_pickup_test['player']
        entities = setup_pickup_test['entities']
        state_manager = setup_pickup_test['state_manager']
        
        # Create item at (6, 6) - SE of player
        item = Entity(6, 6, '!', (255, 0, 255), 'Potion', blocks=False,
                     render_order=RenderOrder.ITEM)
        item.item = Item(use_function=None)
        item.item.owner = item
        entities.append(item)
        
        # Execute pickup
        pickup_service = PickupService(state_manager)
        result = pickup_service.execute_pickup(source="test")
        
        # Verify pickup succeeded
        assert result.success is True, "Should pick up item from diagonal adjacent tile"
        assert item not in entities, "Item should be removed from entities"
        assert item in player.inventory.items, "Item should be in inventory"
    
    def test_pickup_prioritizes_same_tile_over_adjacent(self, setup_pickup_test):
        """Test that items on same tile are picked up before adjacent items."""
        player = setup_pickup_test['player']
        entities = setup_pickup_test['entities']
        state_manager = setup_pickup_test['state_manager']
        
        # Create item on same tile
        item_on_tile = Entity(5, 5, '!', (255, 0, 255), 'Potion A', blocks=False,
                             render_order=RenderOrder.ITEM)
        item_on_tile.item = Item(use_function=None)
        item_on_tile.item.owner = item_on_tile
        entities.append(item_on_tile)
        
        # Create item adjacent
        item_adjacent = Entity(6, 5, '!', (255, 0, 255), 'Potion B', blocks=False,
                              render_order=RenderOrder.ITEM)
        item_adjacent.item = Item(use_function=None)
        item_adjacent.item.owner = item_adjacent
        entities.append(item_adjacent)
        
        # Execute pickup
        pickup_service = PickupService(state_manager)
        result = pickup_service.execute_pickup(source="test")
        
        # Verify the item on same tile was picked up, not the adjacent one
        assert result.success is True
        assert item_on_tile not in entities, "Item on same tile should be picked up"
        assert item_adjacent in entities, "Adjacent item should remain"
        assert item_on_tile in player.inventory.items
        assert item_adjacent not in player.inventory.items
    
    def test_chest_loot_pickup_from_adjacent(self, setup_pickup_test):
        """Test that chest loot can be picked up from adjacent position.
        
        This is the core regression test for the chest loot bug.
        
        Scenario:
        - Chest at (6, 5)
        - Player at (5, 5) - west of chest (adjacent)
        - Item dropped at chest location (6, 5) after opening
        - Player should be able to pick up item WITHOUT stepping on chest tile
        """
        player = setup_pickup_test['player']
        game_map = setup_pickup_test['game_map']
        entities = setup_pickup_test['entities']
        state_manager = setup_pickup_test['state_manager']
        
        # Create chest at (6, 5) - east of player
        from components.chest import Chest, ChestState
        chest_entity = Entity(6, 5, '&', (139, 69, 19), 'Wooden Chest', blocks=True,
                             render_order=RenderOrder.ITEM)
        chest_entity.tags.add('openable')
        chest_entity.chest = Chest(state=ChestState.OPEN, loot=[], loot_quality='common')
        chest_entity.chest.owner = chest_entity
        entities.append(chest_entity)
        
        # Create item at chest location (6, 5) - simulating chest loot drop
        item = Entity(6, 5, '!', (255, 0, 255), 'Healing Potion', blocks=False,
                     render_order=RenderOrder.ITEM)
        item.item = Item(use_function=None)
        item.item.owner = item
        entities.append(item)
        
        # Verify player is adjacent to item but not on same tile
        assert player.x != item.x or player.y != item.y, "Player should not be on item tile"
        assert player.chebyshev_distance_to(item) == 1, "Player should be adjacent to item"
        
        # Execute pickup
        pickup_service = PickupService(state_manager)
        result = pickup_service.execute_pickup(source="test")
        
        # Verify pickup succeeded WITHOUT needing to step on chest tile
        assert result.success is True, "Should pick up item from adjacent chest tile"
        assert item not in entities, "Item should be removed from entities"
        assert item in player.inventory.items, "Item should be in inventory"
        assert player.x == 5 and player.y == 5, "Player should not have moved"
    
    def test_pickup_deterministic_with_multiple_adjacent_items(self, setup_pickup_test):
        """Test that pickup is deterministic when multiple items are adjacent."""
        player = setup_pickup_test['player']
        entities = setup_pickup_test['entities']
        state_manager = setup_pickup_test['state_manager']
        
        # Create multiple items at different adjacent positions
        item_north = Entity(5, 4, '!', (255, 0, 255), 'Potion North', blocks=False,
                           render_order=RenderOrder.ITEM)
        item_north.item = Item(use_function=None)
        item_north.item.owner = item_north
        entities.append(item_north)
        
        item_east = Entity(6, 5, '!', (255, 0, 255), 'Potion East', blocks=False,
                          render_order=RenderOrder.ITEM)
        item_east.item = Item(use_function=None)
        item_east.item.owner = item_east
        entities.append(item_east)
        
        # Execute pickup twice with same setup
        pickup_service = PickupService(state_manager)
        
        # First pickup
        result1 = pickup_service.execute_pickup(source="test")
        assert result1.success is True
        picked_item_1 = result1.item_name
        
        # Reset for second test
        player.inventory.items.clear()
        entities.clear()
        entities.append(player)
        entities.append(item_north)
        entities.append(item_east)
        
        # Second pickup (same setup)
        result2 = pickup_service.execute_pickup(source="test")
        assert result2.success is True
        picked_item_2 = result2.item_name
        
        # Should pick up the same item both times (deterministic)
        assert picked_item_1 == picked_item_2, \
            f"Pickup should be deterministic, got {picked_item_1} then {picked_item_2}"
