"""Tests for the item-seeking AI system.

This module tests the item-seeking behavior for monsters, including:
- Item detection and prioritization
- Movement towards items
- Item pickup and equipping
- Integration with existing AI
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import math

from components.item_seeking_ai import ItemSeekingAI, create_item_seeking_ai
from components.ai import BasicMonster
from components.inventory import Inventory
from components.equipment import Equipment
from components.equippable import Equippable
from equipment_slots import EquipmentSlots


class TestItemSeekingAI(unittest.TestCase):
    """Test the ItemSeekingAI component."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock monster with inventory
        self.monster = Mock()
        self.monster.name = "orc"
        self.monster.x = 5
        self.monster.y = 5
        self.monster.inventory = Mock()
        self.monster.inventory.items = []
        self.monster.inventory.capacity = 5
        
        # Mock player
        self.player = Mock()
        self.player.x = 10
        self.player.y = 10
        
        # Mock game map
        self.game_map = Mock()
        self.game_map.width = 20
        self.game_map.height = 20
        
        # Mock tiles for movement validation
        mock_tile = Mock()
        mock_tile.blocked = False
        self.game_map.tiles = {}
        for x in range(20):
            self.game_map.tiles[x] = {}
            for y in range(20):
                self.game_map.tiles[x][y] = mock_tile
        
        # Create AI
        self.ai = ItemSeekingAI(self.monster, seek_distance=5)

    def test_initialization(self):
        """Test ItemSeekingAI initialization."""
        ai = ItemSeekingAI(self.monster, seek_distance=7)
        
        self.assertEqual(ai.monster, self.monster)
        self.assertEqual(ai.seek_distance, 7)
        self.assertIsNone(ai.target_item)

    def test_no_inventory_returns_none(self):
        """Test that monsters without inventory don't seek items."""
        self.monster.inventory = None
        
        result = self.ai.get_item_seeking_action(self.game_map, [], self.player)
        
        self.assertIsNone(result)

    def test_full_inventory_returns_none(self):
        """Test that monsters with full inventory don't seek items."""
        # Fill inventory to capacity
        self.monster.inventory.items = [Mock() for _ in range(5)]
        
        result = self.ai.get_item_seeking_action(self.game_map, [], self.player)
        
        self.assertIsNone(result)

    def test_no_items_returns_none(self):
        """Test behavior when no items are nearby."""
        entities = [self.monster, self.player]  # No items
        
        result = self.ai.get_item_seeking_action(self.game_map, entities, self.player)
        
        self.assertIsNone(result)

    def test_find_nearby_items(self):
        """Test finding items within seek distance."""
        # Create mock items
        close_item = Mock()
        close_item.item = Mock()  # Has item component
        close_item.x = 6
        close_item.y = 6
        close_item.owner = None  # Not being carried
        
        far_item = Mock()
        far_item.item = Mock()
        far_item.x = 15
        far_item.y = 15
        far_item.owner = None
        
        non_item = Mock()
        non_item.item = None  # Not an item
        non_item.x = 7
        non_item.y = 7
        
        entities = [self.monster, self.player, close_item, far_item, non_item]
        
        nearby_items = self.ai._find_nearby_items(entities)
        
        # Should find only the close item
        self.assertEqual(len(nearby_items), 1)
        self.assertEqual(nearby_items[0][0], close_item)
        self.assertAlmostEqual(nearby_items[0][1], math.sqrt(2), places=2)

    def test_calculate_distance(self):
        """Test distance calculation."""
        distance = self.ai._calculate_distance(0, 0, 3, 4)
        self.assertEqual(distance, 5.0)  # 3-4-5 triangle

    def test_item_closer_than_player(self):
        """Test seeking item that's closer than player."""
        # Item at (7, 7) - distance ~2.8 from monster (not adjacent)
        item = Mock()
        item.item = Mock()
        item.name = "sword"
        item.x = 7
        item.y = 7
        item.owner = None
        
        # Player at (10, 10) - distance ~7.1 from monster
        entities = [self.monster, self.player, item]
        
        result = self.ai.get_item_seeking_action(self.game_map, entities, self.player)
        
        self.assertIsNotNone(result)
        self.assertIn("move", result)
        self.assertEqual(result["move"], (1, 1))  # Move towards item

    def test_item_farther_than_player_ignored(self):
        """Test that items farther than player are ignored."""
        # Item at (15, 15) - farther than player
        item = Mock()
        item.item = Mock()
        item.name = "sword"
        item.x = 15
        item.y = 15
        item.owner = None
        
        entities = [self.monster, self.player, item]
        
        result = self.ai.get_item_seeking_action(self.game_map, entities, self.player)
        
        self.assertIsNone(result)

    def test_pickup_when_adjacent(self):
        """Test pickup action when adjacent to item."""
        # Item adjacent to monster
        item = Mock()
        item.item = Mock()
        item.name = "sword"
        item.x = 6
        item.y = 5  # Adjacent
        item.owner = None
        
        entities = [self.monster, self.player, item]
        
        result = self.ai.get_item_seeking_action(self.game_map, entities, self.player)
        
        self.assertIsNotNone(result)
        self.assertIn("pickup_item", result)
        self.assertEqual(result["pickup_item"], item)

    @patch.object(ItemSeekingAI, '_is_valid_move')
    def test_blocked_movement_tries_alternatives(self, mock_is_valid):
        """Test alternative movement when direct path is blocked."""
        # Item to the right
        item = Mock()
        item.item = Mock()
        item.name = "sword"
        item.x = 7
        item.y = 5
        item.owner = None
        
        entities = [self.monster, self.player, item]
        
        # Direct move blocked, but alternative move valid
        mock_is_valid.side_effect = [False, True]  # First move blocked, second valid
        
        result = self.ai.get_item_seeking_action(self.game_map, entities, self.player)
        
        self.assertIsNotNone(result)
        self.assertIn("move", result)

    def test_is_valid_move_checks_boundaries(self):
        """Test movement validation for map boundaries."""
        # Mock tile access
        self.game_map.tiles = {}
        
        # Test boundary checks
        self.assertFalse(self.ai._is_valid_move(-1, 5, self.game_map, []))
        self.assertFalse(self.ai._is_valid_move(5, -1, self.game_map, []))
        self.assertFalse(self.ai._is_valid_move(20, 5, self.game_map, []))
        self.assertFalse(self.ai._is_valid_move(5, 20, self.game_map, []))

    def test_is_valid_move_checks_blocking_entities(self):
        """Test movement validation for blocking entities."""
        # Mock valid tile
        mock_tile = Mock()
        mock_tile.blocked = False
        self.game_map.tiles = {6: {5: mock_tile}}
        
        # Blocking entity at target location
        blocking_entity = Mock()
        blocking_entity.x = 6
        blocking_entity.y = 5
        blocking_entity.blocks = True
        
        entities = [blocking_entity]
        
        self.assertFalse(self.ai._is_valid_move(6, 5, self.game_map, entities))


class TestItemSeekingAICreation(unittest.TestCase):
    """Test creation of ItemSeekingAI components."""

    def test_create_item_seeking_ai_success(self):
        """Test successful creation of ItemSeekingAI."""
        monster = Mock()
        monster.name = "orc"
        monster.inventory = Mock()
        
        monster_def = Mock()
        monster_def.can_seek_items = True
        monster_def.seek_distance = 7
        
        ai = create_item_seeking_ai(monster, monster_def)
        
        self.assertIsNotNone(ai)
        self.assertIsInstance(ai, ItemSeekingAI)
        self.assertEqual(ai.seek_distance, 7)

    def test_create_item_seeking_ai_cannot_seek(self):
        """Test creation when monster cannot seek items."""
        monster = Mock()
        monster_def = Mock()
        monster_def.can_seek_items = False
        
        ai = create_item_seeking_ai(monster, monster_def)
        
        self.assertIsNone(ai)

    def test_create_item_seeking_ai_no_inventory(self):
        """Test creation when monster has no inventory."""
        monster = Mock()
        monster.name = "orc"
        monster.inventory = None
        
        monster_def = Mock()
        monster_def.can_seek_items = True
        
        ai = create_item_seeking_ai(monster, monster_def)
        
        self.assertIsNone(ai)


class TestBasicMonsterIntegration(unittest.TestCase):
    """Test integration of item-seeking with BasicMonster AI."""

    def setUp(self):
        """Set up test fixtures."""
        self.monster = Mock()
        self.monster.name = "orc"
        self.monster.x = 5
        self.monster.y = 5
        self.monster.distance_to = Mock(return_value=3)
        self.monster.move_astar = Mock()
        self.monster.move = Mock()
        self.monster.fighter = Mock()
        self.monster.fighter.attack = Mock(return_value=[])
        
        # Mock item usage system to prevent interference
        self.monster.item_usage = None
        
        self.player = Mock()
        self.player.x = 8
        self.player.y = 8
        self.player.fighter = Mock()
        self.player.fighter.hp = 100
        
        self.ai = BasicMonster()
        self.ai.owner = self.monster
        
        self.fov_map = Mock()
        self.game_map = Mock()
        self.entities = [self.monster, self.player]

    @patch('components.ai.map_is_in_fov')
    def test_normal_behavior_without_item_seeking(self, mock_fov):
        """Test normal AI behavior when no item-seeking AI is present."""
        mock_fov.return_value = True
        self.monster.item_seeking_ai = None
        
        results = self.ai.take_turn(self.player, self.fov_map, self.game_map, self.entities)
        
        # Should use normal pathfinding
        self.monster.move_astar.assert_called_once()

    @patch('components.ai.map_is_in_fov')
    def test_item_seeking_overrides_combat(self, mock_fov):
        """Test that item-seeking overrides normal combat behavior."""
        mock_fov.return_value = True
        
        # Mock item-seeking AI that returns an action
        mock_item_ai = Mock()
        mock_item_ai.get_item_seeking_action.return_value = {"move": (1, 0)}
        self.monster.item_seeking_ai = mock_item_ai
        
        results = self.ai.take_turn(self.player, self.fov_map, self.game_map, self.entities)
        
        # Should move towards item, not use pathfinding to player
        self.monster.move.assert_called_once_with(1, 0)
        self.monster.move_astar.assert_not_called()

    @patch('components.ai.map_is_in_fov')
    def test_pickup_item_integration(self, mock_fov):
        """Test item pickup through AI integration."""
        mock_fov.return_value = True
        
        # Mock inventory and equipment
        self.monster.inventory = Mock()
        self.monster.inventory.items = []
        self.monster.inventory.capacity = 5
        self.monster.inventory.add_item = Mock()
        self.monster.equipment = Mock()
        self.monster.equipment.main_hand = None
        self.monster.equipment.toggle_equip = Mock()
        
        # Mock item
        item = Mock()
        item.name = "sword"
        item.equippable = Mock()
        item.equippable.slot = Mock()
        item.equippable.slot.value = "main_hand"
        
        # Mock item-seeking AI that returns pickup action
        mock_item_ai = Mock()
        mock_item_ai.get_item_seeking_action.return_value = {"pickup_item": item}
        self.monster.item_seeking_ai = mock_item_ai
        
        results = self.ai.take_turn(self.player, self.fov_map, self.game_map, self.entities)
        
        # Should pick up and equip item
        self.monster.inventory.add_item.assert_called_once_with(item)
        self.monster.equipment.toggle_equip.assert_called_once_with(item)
        
        # Should generate pickup message
        self.assertEqual(len(results), 1)
        self.assertIn("message", results[0])


if __name__ == '__main__':
    unittest.main()
