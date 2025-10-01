"""Tests for variable damage system.

This module tests the variable damage and defense system including:
- Equippable component damage/defense ranges
- Combat system integration with variable damage
- Enhancement scrolls for upgrading equipment
- Display name formatting with damage ranges
"""

import unittest
from unittest.mock import Mock, patch
import pytest

from components.equippable import Equippable
from components.fighter import Fighter
from components.equipment import Equipment
from components.inventory import Inventory
from components.item import Item
from entity import Entity
from equipment_slots import EquipmentSlots
from item_functions import enhance_weapon, enhance_armor
from game_messages import Message
from render_functions import RenderOrder


class TestEquippableVariableDamage(unittest.TestCase):
    """Test Equippable component variable damage and defense functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.weapon = Equippable(
            EquipmentSlots.MAIN_HAND, 
            power_bonus=2, 
            damage_min=2, 
            damage_max=5
        )
        
        self.armor = Equippable(
            EquipmentSlots.OFF_HAND,
            defense_bonus=1,
            defense_min=1,
            defense_max=3
        )
        
        self.no_damage_item = Equippable(
            EquipmentSlots.MAIN_HAND,
            power_bonus=1
        )
    
    def test_initialization_with_damage_range(self):
        """Test equippable initialization with damage ranges."""
        self.assertEqual(self.weapon.damage_min, 2)
        self.assertEqual(self.weapon.damage_max, 5)
        self.assertEqual(self.weapon.defense_min, 0)
        self.assertEqual(self.weapon.defense_max, 0)
    
    def test_initialization_with_defense_range(self):
        """Test equippable initialization with defense ranges."""
        self.assertEqual(self.armor.defense_min, 1)
        self.assertEqual(self.armor.defense_max, 3)
        self.assertEqual(self.armor.damage_min, 0)
        self.assertEqual(self.armor.damage_max, 0)
    
    def test_initialization_validates_ranges(self):
        """Test that initialization validates min/max ranges."""
        # Test damage_max < damage_min gets corrected
        weapon = Equippable(EquipmentSlots.MAIN_HAND, damage_min=5, damage_max=2)
        self.assertEqual(weapon.damage_min, 5)
        self.assertEqual(weapon.damage_max, 5)  # Should be corrected to min
        
        # Test defense_max < defense_min gets corrected
        armor = Equippable(EquipmentSlots.OFF_HAND, defense_min=3, defense_max=1)
        self.assertEqual(armor.defense_min, 3)
        self.assertEqual(armor.defense_max, 3)  # Should be corrected to min
    
    def test_get_damage_range_text(self):
        """Test damage range text formatting."""
        # Range display
        self.assertEqual(self.weapon.get_damage_range_text(), "(2-5 damage)")
        
        # Single value display
        single_damage = Equippable(EquipmentSlots.MAIN_HAND, damage_min=3, damage_max=3)
        self.assertEqual(single_damage.get_damage_range_text(), "(3 damage)")
        
        # No damage display
        self.assertEqual(self.no_damage_item.get_damage_range_text(), "")
    
    def test_get_defense_range_text(self):
        """Test defense range text formatting."""
        # Range display
        self.assertEqual(self.armor.get_defense_range_text(), "(1-3 defense)")
        
        # Single value display
        single_defense = Equippable(EquipmentSlots.OFF_HAND, defense_min=2, defense_max=2)
        self.assertEqual(single_defense.get_defense_range_text(), "(2 defense)")
        
        # No defense display
        self.assertEqual(self.no_damage_item.get_defense_range_text(), "")
    
    @patch('random.randint')
    def test_roll_damage(self, mock_randint):
        """Test damage rolling within range."""
        mock_randint.return_value = 4
        
        damage = self.weapon.roll_damage()
        self.assertEqual(damage, 4)
        mock_randint.assert_called_once_with(2, 5)
        
        # Test no damage item
        no_damage = self.no_damage_item.roll_damage()
        self.assertEqual(no_damage, 0)
    
    @patch('random.randint')
    def test_roll_defense(self, mock_randint):
        """Test defense rolling within range."""
        mock_randint.return_value = 2
        
        defense = self.armor.roll_defense()
        self.assertEqual(defense, 2)
        mock_randint.assert_called_once_with(1, 3)
        
        # Test no defense item
        no_defense = self.no_damage_item.roll_defense()
        self.assertEqual(no_defense, 0)
    
    def test_modify_damage_range(self):
        """Test damage range modification."""
        original_min = self.weapon.damage_min
        original_max = self.weapon.damage_max
        
        self.weapon.modify_damage_range(1, 2)
        
        self.assertEqual(self.weapon.damage_min, original_min + 1)
        self.assertEqual(self.weapon.damage_max, original_max + 2)
    
    def test_modify_damage_range_minimum_bounds(self):
        """Test damage range modification respects minimum bounds."""
        # Test negative bonus doesn't go below 1
        self.weapon.modify_damage_range(-5, -5)
        self.assertEqual(self.weapon.damage_min, 1)  # Should not go below 1
        self.assertTrue(self.weapon.damage_max >= self.weapon.damage_min)
    
    def test_modify_defense_range(self):
        """Test defense range modification."""
        original_min = self.armor.defense_min
        original_max = self.armor.defense_max
        
        self.armor.modify_defense_range(1, 1)
        
        self.assertEqual(self.armor.defense_min, original_min + 1)
        self.assertEqual(self.armor.defense_max, original_max + 1)
    
    def test_modify_non_damage_item(self):
        """Test modifying item with no damage range does nothing."""
        original_min = self.no_damage_item.damage_min
        original_max = self.no_damage_item.damage_max
        
        self.no_damage_item.modify_damage_range(5, 5)
        
        self.assertEqual(self.no_damage_item.damage_min, original_min)
        self.assertEqual(self.no_damage_item.damage_max, original_max)


class TestEntityDisplayNames(unittest.TestCase):
    """Test entity display names with damage/defense ranges."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create weapon entity
        weapon_equippable = Equippable(
            EquipmentSlots.MAIN_HAND,
            power_bonus=2,
            damage_min=2,
            damage_max=5
        )
        self.weapon_entity = Entity(
            x=0, y=0, char='/', color=(255, 255, 255), name="Sword",
            equippable=weapon_equippable
        )
        
        # Create armor entity
        armor_equippable = Equippable(
            EquipmentSlots.OFF_HAND,
            defense_bonus=1,
            defense_min=1,
            defense_max=3
        )
        self.armor_entity = Entity(
            x=0, y=0, char='[', color=(255, 255, 255), name="Shield",
            equippable=armor_equippable
        )
        
        # Create non-equippable entity
        self.potion_entity = Entity(
            x=0, y=0, char='!', color=(255, 255, 255), name="Healing Potion"
        )
    
    def test_weapon_display_name(self):
        """Test weapon display name includes damage range."""
        display_name = self.weapon_entity.get_display_name()
        self.assertEqual(display_name, "Sword (2-5 damage)")
    
    def test_armor_display_name(self):
        """Test armor display name includes defense range."""
        display_name = self.armor_entity.get_display_name()
        self.assertEqual(display_name, "Shield (1-3 defense)")
    
    def test_non_equippable_display_name(self):
        """Test non-equippable items show normal name."""
        display_name = self.potion_entity.get_display_name()
        self.assertEqual(display_name, "Healing Potion")
    
    def test_weapon_with_single_damage_value(self):
        """Test weapon with single damage value display."""
        single_damage_equippable = Equippable(
            EquipmentSlots.MAIN_HAND,
            damage_min=3,
            damage_max=3
        )
        weapon = Entity(
            x=0, y=0, char='/', color=(255, 255, 255), name="Dagger",
            equippable=single_damage_equippable
        )
        
        display_name = weapon.get_display_name()
        self.assertEqual(display_name, "Dagger (3 damage)")


class TestVariableDamageCombat(unittest.TestCase):
    """Test combat system integration with variable damage."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create attacker with weapon
        self.attacker_fighter = Fighter(hp=100, defense=1, power=5)
        self.attacker_equipment = Equipment()
        self.attacker = Mock()
        self.attacker.name = "Player"
        self.attacker.equipment = self.attacker_equipment
        self.attacker_fighter.owner = self.attacker
        
        # Create weapon with variable damage
        weapon_equippable = Equippable(
            EquipmentSlots.MAIN_HAND,
            power_bonus=2,
            damage_min=2,
            damage_max=5
        )
        self.weapon = Mock()
        self.weapon.equippable = weapon_equippable
        
        # Create target with equipment
        self.target_fighter = Fighter(hp=50, defense=2, power=3)
        self.target_equipment = Equipment()
        self.target = Mock()
        self.target.name = "Orc"
        self.target.equipment = self.target_equipment
        self.target.fighter = self.target_fighter
        self.target_fighter.owner = self.target
    
    @patch('components.equippable.Equippable.roll_damage')
    def test_attack_with_weapon_damage(self, mock_roll_damage):
        """Test attack includes variable weapon damage."""
        mock_roll_damage.return_value = 4
        
        # Equip weapon
        self.attacker_equipment.main_hand = self.weapon
        
        results = self.attacker_fighter.attack(self.target)
        
        # Base damage: (5 base power + 2 weapon power bonus) - 2 defense = 5
        # Weapon damage: 4 (mocked)
        # Total: 5 + 4 = 9
        expected_damage = 9
        expected_hp = 50 - expected_damage
        
        self.assertEqual(self.target_fighter.hp, expected_hp)
        
        # Check message includes weapon damage
        message_result = next(r for r in results if "message" in r)
        message_text = message_result["message"].text
        self.assertIn("9 damage", message_text)
        self.assertIn("(7 power + 4 weapon)", message_text)
    
    def test_attack_without_weapon(self):
        """Test attack without weapon uses no variable damage."""
        # No weapon equipped
        self.attacker_equipment.main_hand = None
        
        results = self.attacker_fighter.attack(self.target)
        
        # Base damage: 5 power - 2 defense = 3
        # No weapon damage
        expected_damage = 3
        expected_hp = 50 - expected_damage
        
        self.assertEqual(self.target_fighter.hp, expected_hp)
        
        # Check message doesn't include weapon damage
        message_result = next(r for r in results if "message" in r)
        message_text = message_result["message"].text
        self.assertIn("3 damage", message_text)
        self.assertNotIn("weapon", message_text)
    
    @patch('components.equippable.Equippable.roll_damage')
    def test_attack_with_zero_weapon_damage(self, mock_roll_damage):
        """Test attack when weapon rolls zero damage."""
        mock_roll_damage.return_value = 0
        
        # Equip weapon
        self.attacker_equipment.main_hand = self.weapon
        
        results = self.attacker_fighter.attack(self.target)
        
        # Base damage: (5 base power + 2 weapon power bonus) - 2 defense = 5
        # Weapon damage: 0
        # Total: 5 + 0 = 5
        expected_damage = 5
        expected_hp = 50 - expected_damage
        
        self.assertEqual(self.target_fighter.hp, expected_hp)
        
        # Check message doesn't show weapon bonus for zero damage
        message_result = next(r for r in results if "message" in r)
        message_text = message_result["message"].text
        self.assertIn("5 damage", message_text)
        self.assertNotIn("weapon", message_text)


class TestEnhancementScrolls(unittest.TestCase):
    """Test enhancement scroll functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create player with equipment
        self.player = Mock()
        self.player.equipment = Equipment()
        
        # Create weapon
        weapon_equippable = Equippable(
            EquipmentSlots.MAIN_HAND,
            power_bonus=2,
            damage_min=2,
            damage_max=5
        )
        self.weapon = Mock()
        self.weapon.name = "Sword"
        self.weapon.equippable = weapon_equippable
        
        # Create armor
        armor_equippable = Equippable(
            EquipmentSlots.OFF_HAND,
            defense_bonus=1,
            defense_min=1,
            defense_max=3
        )
        self.armor = Mock()
        self.armor.name = "Shield"
        self.armor.equippable = armor_equippable
    
    def test_enhance_weapon_success(self):
        """Test successful weapon enhancement."""
        # Equip weapon
        self.player.equipment.main_hand = self.weapon
        
        results = enhance_weapon(self.player, min_bonus=1, max_bonus=2)
        
        # Check weapon was enhanced
        self.assertEqual(self.weapon.equippable.damage_min, 3)  # 2 + 1
        self.assertEqual(self.weapon.equippable.damage_max, 7)  # 5 + 2
        
        # Check results
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertTrue(result["consumed"])
        self.assertIn("enhanced from (2-5) to (3-7)", result["message"].text)
    
    def test_enhance_weapon_no_weapon_equipped(self):
        """Test weapon enhancement with no weapon equipped."""
        # No weapon equipped
        self.player.equipment.main_hand = None
        
        results = enhance_weapon(self.player, min_bonus=1, max_bonus=2)
        
        # Check results
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertFalse(result["consumed"])
        self.assertIn("must have a weapon equipped", result["message"].text)
    
    def test_enhance_armor_success(self):
        """Test successful armor enhancement."""
        # Equip armor
        self.player.equipment.off_hand = self.armor
        
        results = enhance_armor(self.player, min_bonus=1, max_bonus=1)
        
        # Check armor was enhanced
        self.assertEqual(self.armor.equippable.defense_min, 2)  # 1 + 1
        self.assertEqual(self.armor.equippable.defense_max, 4)  # 3 + 1
        
        # Check results
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertTrue(result["consumed"])
        self.assertIn("enhanced from (1-3) to (2-4)", result["message"].text)
    
    def test_enhance_armor_no_armor_equipped(self):
        """Test armor enhancement with no armor equipped."""
        # No armor equipped
        self.player.equipment.off_hand = None
        
        results = enhance_armor(self.player, min_bonus=1, max_bonus=1)
        
        # Check results
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertFalse(result["consumed"])
        self.assertIn("must have armor equipped", result["message"].text)
    
    def test_enhance_weapon_no_damage_range(self):
        """Test enhancing weapon with no damage range."""
        # Create weapon without damage range
        no_damage_equippable = Equippable(
            EquipmentSlots.MAIN_HAND,
            power_bonus=2
        )
        no_damage_weapon = Mock()
        no_damage_weapon.name = "Basic Weapon"
        no_damage_weapon.equippable = no_damage_equippable
        
        self.player.equipment.main_hand = no_damage_weapon
        
        results = enhance_weapon(self.player, min_bonus=1, max_bonus=2)
        
        # Check results
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertFalse(result["consumed"])
        self.assertIn("cannot be enhanced further", result["message"].text)


class TestVariableDamageIntegration(unittest.TestCase):
    """Test integration of variable damage system with game components."""
    
    def test_weapon_creation_with_damage_range(self):
        """Test creating weapons with damage ranges."""
        equippable = Equippable(
            EquipmentSlots.MAIN_HAND,
            power_bonus=3,
            damage_min=2,
            damage_max=5
        )
        
        weapon = Entity(
            x=0, y=0, char='/', color=(0, 191, 255), name="Sword",
            equippable=equippable
        )
        
        # Test display name
        self.assertEqual(weapon.get_display_name(), "Sword (2-5 damage)")
        
        # Test damage rolling
        for _ in range(10):  # Test multiple rolls
            damage = weapon.equippable.roll_damage()
            self.assertGreaterEqual(damage, 2)
            self.assertLessEqual(damage, 5)
    
    def test_armor_creation_with_defense_range(self):
        """Test creating armor with defense ranges."""
        equippable = Equippable(
            EquipmentSlots.OFF_HAND,
            defense_bonus=1,
            defense_min=1,
            defense_max=3
        )
        
        armor = Entity(
            x=0, y=0, char='[', color=(127, 63, 0), name="Shield",
            equippable=equippable
        )
        
        # Test display name
        self.assertEqual(armor.get_display_name(), "Shield (1-3 defense)")
        
        # Test defense rolling
        for _ in range(10):  # Test multiple rolls
            defense = armor.equippable.roll_defense()
            self.assertGreaterEqual(defense, 1)
            self.assertLessEqual(defense, 3)
    
    def test_backward_compatibility(self):
        """Test that old equipment without damage ranges still works."""
        # Create old-style equippable (no damage ranges)
        old_equippable = Equippable(
            EquipmentSlots.MAIN_HAND,
            power_bonus=2
        )
        
        old_weapon = Entity(
            x=0, y=0, char='/', color=(255, 255, 255), name="Old Sword",
            equippable=old_equippable
        )
        
        # Should show normal name (no damage range)
        self.assertEqual(old_weapon.get_display_name(), "Old Sword")
        
        # Should roll zero damage
        self.assertEqual(old_weapon.equippable.roll_damage(), 0)


if __name__ == '__main__':
    unittest.main()
