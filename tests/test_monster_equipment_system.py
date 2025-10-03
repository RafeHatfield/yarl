"""Tests for the monster equipment spawning and loot dropping system.

This module tests the new monster equipment system including:
- Equipment spawning on monsters based on dungeon level
- Loot dropping when monsters die
- Configuration-based spawn rates
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from components.monster_equipment import MonsterEquipmentSpawner, MonsterLootDropper
from components.monster_equipment import spawn_equipment_on_monster, drop_loot_from_monster
from components.fighter import Fighter
from components.equipment import Equipment
from components.equippable import Equippable
from equipment_slots import EquipmentSlots


class TestMonsterEquipmentSpawner(unittest.TestCase):
    """Test monster equipment spawning functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.spawner = MonsterEquipmentSpawner()
        
        # Mock monster
        self.monster = Mock()
        self.monster.name = "orc"
        self.monster.equipment = Mock()
        self.monster.equipment.toggle_equip = Mock()

    @patch('components.monster_equipment.is_testing_mode')
    @patch('random.random')
    def test_should_spawn_equipment_normal_mode(self, mock_random, mock_testing_mode):
        """Test equipment spawn chance calculation in normal mode."""
        mock_testing_mode.return_value = False
        mock_random.return_value = 0.15  # 15% roll
        
        # Level 1: 10% chance
        result = self.spawner.should_spawn_with_equipment("orc", 1)
        self.assertFalse(result)  # 15% > 10%
        
        # Level 2: 20% chance  
        result = self.spawner.should_spawn_with_equipment("orc", 2)
        self.assertTrue(result)  # 15% < 20%

    @patch('components.monster_equipment.is_testing_mode')
    @patch('random.random')
    def test_should_spawn_equipment_testing_mode(self, mock_random, mock_testing_mode):
        """Test equipment spawn chance in testing mode (flat 50%)."""
        mock_testing_mode.return_value = True
        mock_random.return_value = 0.4  # 40% roll
        
        # Any level should have 50% chance in testing mode
        result = self.spawner.should_spawn_with_equipment("orc", 1)
        self.assertTrue(result)  # 40% < 50%
        
        mock_random.return_value = 0.6  # 60% roll
        result = self.spawner.should_spawn_with_equipment("orc", 5)
        self.assertFalse(result)  # 60% > 50%

    @patch('components.monster_equipment.is_testing_mode')
    @patch('random.random')
    def test_spawn_chance_cap(self, mock_random, mock_testing_mode):
        """Test that spawn chance is capped at maximum."""
        mock_testing_mode.return_value = False
        mock_random.return_value = 0.65  # 65% roll
        
        # Very high level should be capped at 70%
        result = self.spawner.should_spawn_with_equipment("orc", 20)
        self.assertTrue(result)  # 65% < 70% (cap)

    @patch.object(MonsterEquipmentSpawner, 'should_spawn_with_equipment')
    def test_generate_equipment_no_spawn(self, mock_should_spawn):
        """Test no equipment generation when spawn check fails."""
        mock_should_spawn.return_value = False
        
        result = self.spawner.generate_equipment_for_monster(self.monster, 1)
        
        self.assertEqual(result, [])
        self.monster.equipment.toggle_equip.assert_not_called()

    @patch.object(MonsterEquipmentSpawner, 'should_spawn_with_equipment')
    @patch.object(MonsterEquipmentSpawner, '_create_weapon_for_level')
    @patch('random.random')
    def test_generate_weapon_equipment(self, mock_random, mock_create_weapon, mock_should_spawn):
        """Test weapon equipment generation."""
        mock_should_spawn.return_value = True
        mock_random.return_value = 0.5  # Within weapon spawn weight (60%)
        
        # Mock weapon creation
        mock_weapon = Mock()
        mock_weapon.name = "sword"
        mock_create_weapon.return_value = mock_weapon
        
        result = self.spawner.generate_equipment_for_monster(self.monster, 3)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], mock_weapon)
        self.monster.equipment.toggle_equip.assert_called_once_with(mock_weapon)

    @patch.object(MonsterEquipmentSpawner, 'should_spawn_with_equipment')
    @patch.object(MonsterEquipmentSpawner, '_create_armor_for_level')
    @patch('random.random')
    def test_generate_armor_equipment(self, mock_random, mock_create_armor, mock_should_spawn):
        """Test armor equipment generation."""
        mock_should_spawn.return_value = True
        mock_random.return_value = 0.8  # Outside weapon spawn weight (60%)
        
        # Mock armor creation
        mock_armor = Mock()
        mock_armor.name = "shield"
        mock_create_armor.return_value = mock_armor
        
        result = self.spawner.generate_equipment_for_monster(self.monster, 2)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], mock_armor)
        self.monster.equipment.toggle_equip.assert_called_once_with(mock_armor)

    def test_create_weapon_for_level(self):
        """Test weapon creation based on dungeon level."""
        # Mock the entity factory on the spawner instance
        mock_factory = Mock()
        mock_weapon = Mock()
        mock_factory.create_weapon.return_value = mock_weapon
        self.spawner.entity_factory = mock_factory
        
        # Level 1-2: dagger
        result = self.spawner._create_weapon_for_level(1)
        mock_factory.create_weapon.assert_called_with("dagger", 0, 0)
        self.assertEqual(result, mock_weapon)
        
        # Level 3+: shortsword (updated in v3.0.0)
        result = self.spawner._create_weapon_for_level(3)
        mock_factory.create_weapon.assert_called_with("shortsword", 0, 0)
        self.assertEqual(result, mock_weapon)

    def test_create_armor_for_level(self):
        """Test armor creation."""
        # Mock the entity factory on the spawner instance
        mock_factory = Mock()
        mock_armor = Mock()
        mock_factory.create_armor.return_value = mock_armor
        self.spawner.entity_factory = mock_factory
        
        result = self.spawner._create_armor_for_level(2)
        mock_factory.create_armor.assert_called_with("shield", 0, 0)
        self.assertEqual(result, mock_armor)


class TestMonsterLootDropper(unittest.TestCase):
    """Test monster loot dropping functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.monster = Mock()
        self.monster.name = "orc"
        self.monster.x = 5
        self.monster.y = 10

    def test_drop_loot_no_equipment(self):
        """Test loot dropping when monster has no equipment."""
        self.monster.equipment = None
        self.monster.inventory = None
        
        result = MonsterLootDropper.drop_monster_loot(self.monster, 5, 10)
        
        self.assertEqual(result, [])

    def test_drop_equipped_weapon(self):
        """Test dropping equipped weapon."""
        # Mock equipped weapon
        weapon = Mock()
        weapon.name = "sword"
        
        self.monster.equipment = Mock()
        self.monster.equipment.main_hand = weapon
        self.monster.equipment.off_hand = None
        self.monster.inventory = None
        
        result = MonsterLootDropper.drop_monster_loot(self.monster, 5, 10)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], weapon)
        self.assertEqual(weapon.x, 5)
        self.assertEqual(weapon.y, 10)

    def test_drop_equipped_armor(self):
        """Test dropping equipped armor."""
        # Mock equipped armor
        armor = Mock()
        armor.name = "shield"
        
        self.monster.equipment = Mock()
        self.monster.equipment.main_hand = None
        self.monster.equipment.off_hand = armor
        self.monster.inventory = None
        
        result = MonsterLootDropper.drop_monster_loot(self.monster, 5, 10)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], armor)
        self.assertEqual(armor.x, 5)
        self.assertEqual(armor.y, 10)

    def test_drop_inventory_items(self):
        """Test dropping items from monster inventory."""
        # Mock inventory items
        potion = Mock()
        potion.name = "healing_potion"
        scroll = Mock()
        scroll.name = "lightning_scroll"

        self.monster.equipment = None
        self.monster.inventory = Mock()
        self.monster.inventory.items = [potion, scroll]

        result = MonsterLootDropper.drop_monster_loot(self.monster, 5, 10)

        self.assertEqual(len(result), 2)
        self.assertIn(potion, result)
        self.assertIn(scroll, result)
        
        # Items should be dropped near the target location (within 1 tile)
        for item in [potion, scroll]:
            self.assertLessEqual(abs(item.x - 5), 1)
            self.assertLessEqual(abs(item.y - 10), 1)

    def test_drop_all_items(self):
        """Test dropping both equipped and inventory items."""
        # Mock equipped items
        weapon = Mock()
        weapon.name = "sword"
        armor = Mock()
        armor.name = "shield"
        
        # Mock inventory items
        potion = Mock()
        potion.name = "healing_potion"
        
        self.monster.equipment = Mock()
        self.monster.equipment.main_hand = weapon
        self.monster.equipment.off_hand = armor
        self.monster.inventory = Mock()
        self.monster.inventory.items = [potion]
        
        result = MonsterLootDropper.drop_monster_loot(self.monster, 5, 10)
        
        self.assertEqual(len(result), 3)
        self.assertIn(weapon, result)
        self.assertIn(armor, result)
        self.assertIn(potion, result)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions for monster equipment system."""

    @patch('components.monster_equipment.MonsterEquipmentSpawner')
    def test_spawn_equipment_on_monster(self, mock_spawner_class):
        """Test spawn_equipment_on_monster convenience function."""
        mock_spawner = Mock()
        mock_spawner_class.return_value = mock_spawner
        mock_spawner.generate_equipment_for_monster.return_value = ["weapon"]
        
        monster = Mock()
        result = spawn_equipment_on_monster(monster, 3)
        
        mock_spawner.generate_equipment_for_monster.assert_called_once_with(monster, 3)
        self.assertEqual(result, ["weapon"])

    @patch('components.monster_equipment.MonsterLootDropper.drop_monster_loot')
    def test_drop_loot_from_monster(self, mock_drop_loot):
        """Test drop_loot_from_monster convenience function."""
        mock_drop_loot.return_value = ["sword", "shield"]
        
        monster = Mock()
        result = drop_loot_from_monster(monster, 5, 10)
        
        mock_drop_loot.assert_called_once_with(monster, 5, 10, None)  # Updated signature includes game_map parameter
        self.assertEqual(result, ["sword", "shield"])


class TestMonsterEquipmentIntegration(unittest.TestCase):
    """Integration tests for monster equipment system."""

    def setUp(self):
        """Set up integration test fixtures."""
        # Create a real monster with equipment component
        self.monster = Mock()
        self.monster.name = "orc"
        self.monster.x = 5
        self.monster.y = 10
        
        # Mock equipment component
        self.monster.equipment = Mock()
        self.monster.equipment.main_hand = None
        self.monster.equipment.off_hand = None
        self.monster.equipment.toggle_equip = Mock()

    @patch('components.monster_equipment.get_entity_factory')
    @patch('components.monster_equipment.is_testing_mode')
    @patch('random.random')
    def test_full_equipment_spawn_flow(self, mock_random, mock_testing_mode, mock_get_factory):
        """Test complete equipment spawning flow."""
        # Setup mocks
        mock_testing_mode.return_value = True  # Testing mode for predictable results
        mock_random.side_effect = [0.3, 0.5]  # Spawn equipment, choose weapon
        
        mock_factory = Mock()
        mock_weapon = Mock()
        mock_weapon.name = "sword"
        mock_factory.create_weapon.return_value = mock_weapon
        mock_get_factory.return_value = mock_factory
        
        # Spawn equipment
        result = spawn_equipment_on_monster(self.monster, 3)
        
        # Verify equipment was created and equipped
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], mock_weapon)
        self.monster.equipment.toggle_equip.assert_called_once_with(mock_weapon)

    def test_full_loot_drop_flow(self):
        """Test complete loot dropping flow."""
        # Setup equipped items
        weapon = Mock()
        weapon.name = "sword"
        armor = Mock()
        armor.name = "shield"

        self.monster.equipment.main_hand = weapon
        self.monster.equipment.off_hand = armor
        self.monster.inventory = None

        # Drop loot
        result = drop_loot_from_monster(self.monster, 8, 12)

        # Verify items were dropped near the target location
        self.assertEqual(len(result), 2)
        self.assertIn(weapon, result)
        self.assertIn(armor, result)
        
        # Items should be dropped near the target location (within 1 tile)
        for item in [weapon, armor]:
            self.assertLessEqual(abs(item.x - 8), 1)
            self.assertLessEqual(abs(item.y - 12), 1)


if __name__ == '__main__':
    unittest.main()
