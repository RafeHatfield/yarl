"""Tests for monster loot dropping position logic.

This module tests that items are dropped in adjacent positions to avoid
being hidden under corpses.
"""

import unittest
from unittest.mock import Mock

from components.monster_equipment import MonsterLootDropper
from components.component_registry import ComponentType


class TestLootDropPositions(unittest.TestCase):
    """Test loot dropping position logic."""

    def test_find_drop_location_no_existing_items(self):
        """Test drop location when no items exist yet."""
        x, y = MonsterLootDropper._find_drop_location(5, 5, [])
        
        # Should return the original position when no items exist
        self.assertEqual((x, y), (5, 5))

    def test_find_drop_location_with_existing_items(self):
        """Test drop location avoids existing items."""
        # Create mock items at specific positions
        item1 = Mock()
        item1.x, item1.y = 5, 5  # Center position
        
        item2 = Mock()
        item2.x, item2.y = 5, 4  # North position
        
        existing_items = [item1, item2]
        
        # Should find the next available position (East: 6, 5)
        x, y = MonsterLootDropper._find_drop_location(5, 5, existing_items)
        self.assertEqual((x, y), (6, 5))

    def test_find_drop_location_spiral_pattern(self):
        """Test that drop locations follow the spiral pattern."""
        existing_items = []
        center_x, center_y = 10, 10
        
        # Expected positions in spiral order
        expected_positions = [
            (10, 10),  # Center
            (10, 9),   # North
            (11, 10),  # East
            (10, 11),  # South
            (9, 10),   # West
            (11, 9),   # Northeast
            (11, 11),  # Southeast
            (9, 11),   # Southwest
            (9, 9),    # Northwest
        ]
        
        positions = []
        for i in range(len(expected_positions)):
            x, y = MonsterLootDropper._find_drop_location(center_x, center_y, existing_items)
            positions.append((x, y))
            
            # Add a mock item at this position for the next iteration
            mock_item = Mock()
            mock_item.x, mock_item.y = x, y
            existing_items.append(mock_item)
        
        self.assertEqual(positions, expected_positions)

    def test_drop_monster_loot_spreads_items(self):
        """Test that dropping multiple items spreads them around."""
        # Create a mock monster with inventory and equipment
        monster = Mock()
        monster.name = "Test Orc"
        
        # Mock inventory with items
        item1 = Mock()
        item1.name = "Scroll 1"
        item2 = Mock()
        item2.name = "Scroll 2"
        
        monster.inventory = Mock()
        monster.inventory.items = [item1, item2]
        
        # Mock equipment with weapon
        weapon = Mock()
        weapon.name = "Sword"
        
        monster.equipment = Mock()
        monster.equipment.main_hand = weapon
        monster.equipment.off_hand = None
        
        # Mock ComponentRegistry
        monster.components = Mock()
        def get_component(comp_type):
            if comp_type == ComponentType.EQUIPMENT:
                return monster.equipment
            elif comp_type == ComponentType.INVENTORY:
                return monster.inventory
            return None
        monster.components.get = Mock(side_effect=get_component)
        
        # Drop loot
        dropped_items = MonsterLootDropper.drop_monster_loot(monster, 5, 5)
        
        # Should have 3 items (2 inventory + 1 weapon)
        self.assertEqual(len(dropped_items), 3)
        
        # Check that items are at different positions
        positions = [(item.x, item.y) for item in dropped_items]
        unique_positions = set(positions)
        
        # Should have at least 2 unique positions (items spread out)
        self.assertGreaterEqual(len(unique_positions), 2)
        
        # All positions should be adjacent to or at the drop location
        for x, y in positions:
            distance = max(abs(x - 5), abs(y - 5))
            self.assertLessEqual(distance, 1, f"Item too far from drop location: ({x}, {y})")

    def test_drop_monster_loot_no_items(self):
        """Test dropping loot from monster with no items."""
        monster = Mock()
        monster.name = "Empty Orc"
        monster.inventory = None
        monster.equipment = None
        monster.components = Mock()
        monster.components.get = Mock(return_value=None)
        
        dropped_items = MonsterLootDropper.drop_monster_loot(monster, 5, 5)
        
        self.assertEqual(len(dropped_items), 0)

    def test_drop_monster_loot_inventory_only(self):
        """Test dropping loot from monster with only inventory items."""
        monster = Mock()
        monster.name = "Inventory Orc"
        
        item = Mock()
        item.name = "Test Item"
        
        monster.inventory = Mock()
        monster.inventory.items = [item]
        monster.equipment = None
        
        # Mock ComponentRegistry
        monster.components = Mock()
        def get_component(comp_type):
            if comp_type == ComponentType.INVENTORY:
                return monster.inventory
            return None
        monster.components.get = Mock(side_effect=get_component)
        
        dropped_items = MonsterLootDropper.drop_monster_loot(monster, 3, 3)
        
        self.assertEqual(len(dropped_items), 1)
        self.assertEqual(dropped_items[0], item)
        self.assertEqual((item.x, item.y), (3, 3))

    def test_drop_monster_loot_equipment_only(self):
        """Test dropping loot from monster with only equipped items."""
        monster = Mock()
        monster.name = "Equipped Orc"
        
        weapon = Mock()
        weapon.name = "Test Weapon"
        armor = Mock()
        armor.name = "Test Armor"
        
        monster.inventory = None
        monster.equipment = Mock()
        monster.equipment.main_hand = weapon
        monster.equipment.off_hand = armor
        
        # Mock ComponentRegistry
        monster.components = Mock()
        def get_component(comp_type):
            if comp_type == ComponentType.EQUIPMENT:
                return monster.equipment
            return None
        monster.components.get = Mock(side_effect=get_component)
        
        dropped_items = MonsterLootDropper.drop_monster_loot(monster, 7, 7)
        
        self.assertEqual(len(dropped_items), 2)
        self.assertIn(weapon, dropped_items)
        self.assertIn(armor, dropped_items)
        
        # Items should be at different positions
        positions = [(item.x, item.y) for item in dropped_items]
        unique_positions = set(positions)
        self.assertEqual(len(unique_positions), 2)


if __name__ == '__main__':
    unittest.main()
