"""Tests for the universal base damage system.

This module tests the new unified damage system where all entities have
base damage (fists/natural attacks) and weapons override rather than add to base damage.
"""

import unittest
from unittest.mock import Mock, patch
from components.fighter import Fighter
from components.equipment import Equipment
from components.equippable import Equippable
from equipment_slots import EquipmentSlots
from components.component_registry import ComponentType


class TestBaseDamageSystem(unittest.TestCase):
    """Test the universal base damage system for all entities."""

    def setUp(self):
        """Set up test fixtures."""
        # Create player with fist damage
        self.player = Mock()
        self.player.name = "player"
        self.player.fighter = Fighter(hp=100, defense=1, power=2, damage_min=1, damage_max=2)
        self.player.fighter.owner = self.player
        # Mock get_component_optional to return None for BOSS (not a boss)
        self.player.get_component_optional = Mock(return_value=None)
        
        # Create monster with natural attacks
        self.orc = Mock()
        self.orc.name = "orc"
        self.orc.fighter = Fighter(hp=20, defense=0, power=3, damage_min=1, damage_max=3)
        self.orc.fighter.owner = self.orc
        # Mock get_component_optional to return None for BOSS (not a boss)
        self.orc.get_component_optional = Mock(return_value=None)
        
        # Mock status_effects for both entities
        self.player.status_effects = Mock()
        self.player.status_effects.get_effect = Mock(return_value=None)
        
        self.orc.status_effects = Mock()
        self.orc.status_effects.get_effect = Mock(return_value=None)
        
        # Mock equipment for both entities
        self.player.equipment = Mock()
        self.player.equipment.power_bonus = 0
        self.player.equipment.defense_bonus = 0
        self.player.equipment.main_hand = None
        self.player.equipment.off_hand = None
        
        self.orc.equipment = Mock()
        self.orc.equipment.power_bonus = 0
        self.orc.equipment.defense_bonus = 0
        self.orc.equipment.main_hand = None
        self.orc.equipment.off_hand = None
        
        # Mock take_damage for both entities
        self.player.fighter.take_damage = Mock(return_value=[{"dead": False}])
        self.orc.fighter.take_damage = Mock(return_value=[{"dead": False}])

    @patch('random.randint')
    def test_player_unarmed_attack_uses_fist_damage(self, mock_randint):
        """Test that unarmed players use fist damage (1-2)."""
        mock_randint.return_value = 2  # Max fist damage
        
        # Player attacks orc without weapon
        results = self.player.fighter.attack(self.orc)
        
        # Expected: 2 power + 2 fist damage = 4 total
        # Orc defense: 0, so 4 damage dealt
        self.orc.fighter.take_damage.assert_called_once_with(4)
        
        # Check combat message
        message_result = next(r for r in results if 'message' in r)
        message_text = message_result['message'].text
        self.assertIn("4 damage", message_text)
        self.assertIn("(2 power + 2 natural)", message_text)

    @patch('random.randint')
    def test_monster_attack_uses_natural_damage(self, mock_randint):
        """Test that monsters use their natural attack damage."""
        mock_randint.return_value = 3  # Max natural damage for orc
        
        # Orc attacks player
        results = self.orc.fighter.attack(self.player)
        
        # Expected: 3 power + 3 natural damage = 6 total
        # Player defense: 1, so 5 damage dealt
        self.player.fighter.take_damage.assert_called_once_with(5)
        
        # Check combat message
        message_result = next(r for r in results if 'message' in r)
        message_text = message_result['message'].text
        self.assertIn("5 damage", message_text)
        self.assertIn("(3 power + 3 natural)", message_text)

    @patch('random.randint')
    def test_weapon_overrides_base_damage(self, mock_randint):
        """Test that equipped weapons override base damage."""
        # Create weapon
        weapon = Mock()
        weapon.equippable = Mock()
        weapon.equippable.roll_damage.return_value = 4
        weapon.equippable.power_bonus = 0
        
        # Equip weapon on player
        self.player.equipment.main_hand = weapon
        
        # Player attacks orc with weapon
        results = self.player.fighter.attack(self.orc)
        
        # Expected: 2 power + 4 weapon damage = 6 total
        # Orc defense: 0, so 6 damage dealt
        # Note: fist damage should NOT be used when weapon is equipped
        self.orc.fighter.take_damage.assert_called_once_with(6)
        
        # Check combat message uses weapon, not natural
        message_result = next(r for r in results if 'message' in r)
        message_text = message_result['message'].text
        self.assertIn("6 damage", message_text)
        self.assertIn("(2 power + 4 weapon)", message_text)
        self.assertNotIn("natural", message_text)

    @patch('random.randint')
    def test_zero_weapon_damage_falls_back_to_base(self, mock_randint):
        """Test that zero weapon damage falls back to base damage."""
        mock_randint.return_value = 1  # Min fist damage
        
        # Create weapon that does zero damage
        weapon = Mock()
        weapon.equippable = Mock()
        weapon.equippable.roll_damage.return_value = 0
        weapon.equippable.power_bonus = 2  # Still provides power bonus
        
        # Equip weapon on player
        self.player.equipment.main_hand = weapon
        self.player.equipment.power_bonus = 2  # Equipment provides power bonus
        
        # Player attacks orc
        results = self.player.fighter.attack(self.orc)
        
        # Expected: (2 base power + 2 power bonus) + 1 fist damage = 5 total
        # Orc defense: 0, so 5 damage dealt
        self.orc.fighter.take_damage.assert_called_once_with(5)
        
        # Check combat message uses natural damage when weapon does 0
        message_result = next(r for r in results if 'message' in r)
        message_text = message_result['message'].text
        self.assertIn("5 damage", message_text)
        self.assertIn("(4 power + 1 natural)", message_text)

    def test_base_damage_defaults_to_0_0(self):
        """Test that entities without specified damage get 0-0 base damage (backward compatibility)."""
        # Create entity without damage range specified
        entity = Mock()
        entity.name = "test"
        entity.fighter = Fighter(hp=10, defense=0, power=1)  # Uses defaults
        entity.fighter.owner = entity
        
        # Check defaults (backward compatibility)
        self.assertEqual(entity.fighter.damage_min, 0)
        self.assertEqual(entity.fighter.damage_max, 0)
        
        # Test damage roll returns 0 when no range configured
        base_damage = entity.fighter._get_base_variable_damage()
        self.assertEqual(base_damage, 0)

    @patch('random.randint')
    def test_legacy_monster_damage_method_compatibility(self, mock_randint):
        """Test that legacy _get_monster_variable_damage still works."""
        mock_randint.return_value = 2
        
        # Test legacy method redirects to new method
        damage = self.orc.fighter._get_monster_variable_damage()
        base_damage = self.orc.fighter._get_base_variable_damage()
        
        self.assertEqual(damage, base_damage)
        self.assertEqual(damage, 2)

    def test_fighter_initialization_with_damage_range(self):
        """Test Fighter initialization with damage range parameters."""
        fighter = Fighter(hp=50, defense=2, power=5, damage_min=2, damage_max=4)
        
        self.assertEqual(fighter.damage_min, 2)
        self.assertEqual(fighter.damage_max, 4)
        
        # Test damage is within range
        for _ in range(10):  # Test multiple rolls
            damage = fighter._get_base_variable_damage()
            self.assertGreaterEqual(damage, 2)
            self.assertLessEqual(damage, 4)


if __name__ == '__main__':
    unittest.main()
