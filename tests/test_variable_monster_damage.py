"""Tests for monster variable damage system.

This module tests the implementation of variable damage for monsters,
including Fighter component updates, EntityFactory integration, 
combat message formatting, and debug logging capabilities.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import logging
import io

from components.fighter import Fighter
from config.entity_factory import EntityFactory
from config.entity_registry import EntityRegistry, EntityStats, MonsterDefinition
from entity import Entity
from components.component_registry import ComponentType


class TestMonsterVariableDamage(unittest.TestCase):
    """Test monster variable damage functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock player
        self.player = Mock()
        self.player.name = "player"
        self.player.fighter = Fighter(hp=100, defense=1, power=2)
        self.player.fighter.owner = self.player
        self.player.fighter.take_damage = Mock(return_value=[{"dead": False}])  # Mock take_damage method
        self.player.equipment = Mock()
        self.player.equipment.power_bonus = 0
        self.player.equipment.defense_bonus = 0
        self.player.equipment.main_hand = None
        self.player.equipment.off_hand = None
        self.player.equipment.left_ring = None
        self.player.equipment.right_ring = None
        # Mock get_component_optional to return None for BOSS (not a boss)
        self.player.get_component_optional = Mock(return_value=None)
        # Mock status_effects to prevent arithmetic errors
        status_effects_mock = Mock()
        status_effects_mock.get_effect = Mock(return_value=None)
        self.player.status_effects = status_effects_mock

    def test_fighter_init_with_damage_range(self):
        """Test Fighter initialization with damage_min/damage_max."""
        fighter = Fighter(hp=20, defense=0, power=3, xp=35, damage_min=1, damage_max=3)
        
        self.assertEqual(fighter.hp, 20)
        self.assertEqual(fighter.base_defense, 0)
        self.assertEqual(fighter.base_power, 3)
        self.assertEqual(fighter.xp, 35)
        self.assertEqual(fighter.damage_min, 1)
        self.assertEqual(fighter.damage_max, 3)

    def test_fighter_init_without_damage_range(self):
        """Test Fighter initialization without damage range (defaults to 0)."""
        fighter = Fighter(hp=20, defense=0, power=3)
        
        self.assertEqual(fighter.damage_min, 0)
        self.assertEqual(fighter.damage_max, 0)

    def test_get_monster_variable_damage_with_range(self):
        """Test _get_monster_variable_damage with valid damage range."""
        fighter = Fighter(hp=20, defense=0, power=3, damage_min=2, damage_max=5)
        
        # Test multiple rolls to ensure they're within range
        for _ in range(10):
            damage = fighter._get_monster_variable_damage()
            self.assertGreaterEqual(damage, 2)
            self.assertLessEqual(damage, 5)

    def test_get_monster_variable_damage_without_range(self):
        """Test _get_monster_variable_damage with no damage range returns 0."""
        fighter = Fighter(hp=20, defense=0, power=3)
        
        damage = fighter._get_monster_variable_damage()
        self.assertEqual(damage, 0)

    def test_get_monster_variable_damage_with_zero_range(self):
        """Test _get_monster_variable_damage with zero values returns 0."""
        fighter = Fighter(hp=20, defense=0, power=3, damage_min=0, damage_max=0)
        
        damage = fighter._get_monster_variable_damage()
        self.assertEqual(damage, 0)

    @patch('random.randint')
    def test_monster_attack_with_variable_damage(self, mock_randint):
        """Test monster attack using variable damage."""
        # Set up monster with variable damage
        monster = Mock()
        monster.name = "orc"
        monster.fighter = Fighter(hp=20, defense=0, power=3, damage_min=1, damage_max=3)
        monster.fighter.owner = monster
        monster.equipment = Mock()
        monster.equipment.power_bonus = 0
        monster.equipment.main_hand = None
        monster.equipment.left_ring = None
        monster.equipment.right_ring = None
        # Mock get_component_optional to return None for BOSS (not a boss)
        monster.get_component_optional = Mock(return_value=None)
        # Mock status_effects to prevent arithmetic errors
        status_effects_mock = Mock()
        status_effects_mock.get_effect = Mock(return_value=None)
        monster.status_effects = status_effects_mock
        monster.equipment.main_hand = None  # Prevent reach check from returning Mock
        
        # Mock variable damage roll
        mock_randint.return_value = 2  # Roll 2 from 1-3 range
        
        # Mock target (player with no armor)
        self.player.equipment.off_hand = None
        
        # Perform attack
        results = monster.fighter.attack(self.player)
        
        # Verify attack calculation: 3 power + 2 variable = 5 total
        # Player defense: 1, so final damage = 5 - 1 = 4
        self.assertGreaterEqual(len(results), 1)  # At least combat message
        
        # Check combat message
        message_result = next(r for r in results if 'message' in r)
        self.assertIn("orc attacks player for 4 damage (5 attack (3 power + 2 natural) - 1 defense)", 
                     message_result['message'].text.lower())

    @patch('random.randint')
    def test_player_attack_still_uses_weapon_damage(self, mock_randint):
        """Test that player attacks still use weapon damage, not monster damage."""
        # Set up player with equipment
        self.player.equipment.main_hand = Mock()
        self.player.equipment.main_hand.equippable = Mock()
        self.player.equipment.main_hand.equippable.roll_damage.return_value = 2
        self.player.equipment.main_hand.item = None  # Prevent reach check from returning Mock
        
        # Player fighter should not have monster damage
        self.assertEqual(self.player.fighter.damage_min, 0)
        self.assertEqual(self.player.fighter.damage_max, 0)
        
        # Create target monster
        target = Mock()
        target.name = "orc"
        target.fighter = Fighter(hp=20, defense=0, power=3)
        target.fighter.owner = target
        target.fighter.take_damage = Mock(return_value=[{"dead": False}])
        target.equipment = Mock()
        target.equipment.power_bonus = 0
        target.equipment.defense_bonus = 0
        target.equipment.main_hand = None
        target.equipment.off_hand = None
        
        # Perform attack
        results = self.player.fighter.attack(target)
        
        # Verify weapon damage was used
        message_result = next(r for r in results if 'message' in r)
        self.assertIn("(2 power + 2 weapon)", message_result['message'].text)
        self.assertNotIn("natural", message_result['message'].text.lower())

    @patch('random.randint')
    def test_combat_message_formatting(self, mock_randint):
        """Test combat message formatting for monster attacks."""
        monster = Mock()
        monster.name = "troll"
        monster.fighter = Fighter(hp=30, defense=2, power=6, damage_min=2, damage_max=6)
        monster.fighter.owner = monster
        monster.equipment = Mock()
        monster.equipment.power_bonus = 0
        monster.equipment.main_hand = None
        monster.equipment.left_ring = None
        monster.equipment.right_ring = None
        # Mock get_component_optional to return None for BOSS (not a boss)
        monster.get_component_optional = Mock(return_value=None)
        # Mock status_effects to prevent arithmetic errors
        status_effects_mock = Mock()
        status_effects_mock.get_effect = Mock(return_value=None)
        monster.status_effects = status_effects_mock
        monster.equipment.main_hand = None  # Prevent reach check from returning Mock
        
        mock_randint.return_value = 4  # Roll 4 from 2-6 range
        
        # Attack player
        results = monster.fighter.attack(self.player)
        
        message_result = next(r for r in results if 'message' in r)
        expected_text = "Troll attacks player for 9 damage (10 attack (6 power + 4 natural) - 1 defense)."
        self.assertEqual(message_result['message'].text, expected_text)

    @patch('components.fighter.is_testing_mode')
    @patch('random.randint')
    def test_debug_logging_with_monster_damage(self, mock_randint, mock_testing_mode):
        """Test debug logging shows monster damage ranges correctly."""
        mock_testing_mode.return_value = True
        mock_randint.return_value = 3
        
        # Create monster with damage range
        monster = Mock()
        monster.name = "orc"
        monster.fighter = Fighter(hp=20, defense=0, power=3, damage_min=1, damage_max=3)
        monster.fighter.owner = monster
        monster.equipment = Mock()
        monster.equipment.power_bonus = 0
        monster.equipment.main_hand = None
        monster.equipment.left_ring = None
        monster.equipment.right_ring = None
        # Mock get_component_optional to return None for BOSS (not a boss)
        monster.get_component_optional = Mock(return_value=None)
        # Mock status_effects to prevent arithmetic errors
        status_effects_mock = Mock()
        status_effects_mock.get_effect = Mock(return_value=None)
        monster.status_effects = status_effects_mock
        monster.equipment.main_hand = None  # Prevent reach check from returning Mock
        
        # Capture debug log output
        with patch('components.fighter.combat_logger') as mock_logger:
            results = monster.fighter.attack(self.player)
            
            # Verify debug logging was called
            mock_logger.debug.assert_called_once()
            debug_message = mock_logger.debug.call_args[0][0]
            
            # Check debug message format includes monster damage range
            self.assertIn("Orc [power:3+0] (1-3 dmg)", debug_message)
            self.assertIn("3 power + 3 rolled", debug_message)


class TestEntityFactoryIntegration(unittest.TestCase):
    """Test EntityFactory integration with monster variable damage."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test entity registry with monster definitions
        self.registry = EntityRegistry()
        
        # Add test monster with variable damage
        orc_stats = EntityStats(hp=20, power=3, defense=0, xp=35, damage_min=1, damage_max=3)
        orc_def = MonsterDefinition(
            name="Test_Orc",
            stats=orc_stats,
            char="o",
            color=(63, 127, 63),
            ai_type="basic"
        )
        self.registry.monsters["orc"] = orc_def
        
        # Add test monster without variable damage  
        troll_stats = EntityStats(hp=30, power=8, defense=2, xp=100)
        troll_def = MonsterDefinition(
            name="Test_Troll",
            stats=troll_stats,
            char="T", 
            color=(0, 127, 0),
            ai_type="basic"
        )
        self.registry.monsters["troll"] = troll_def
        
        self.factory = EntityFactory(self.registry)

    def test_create_monster_with_variable_damage(self):
        """Test creating monster with variable damage via EntityFactory."""
        monster = self.factory.create_monster("orc", 5, 5)
        
        self.assertIsNotNone(monster)
        self.assertEqual(monster.name, "Test_Orc")
        self.assertEqual(monster.fighter.base_power, 3)
        self.assertEqual(monster.fighter.damage_min, 1)
        self.assertEqual(monster.fighter.damage_max, 3)

    def test_create_monster_without_variable_damage(self):
        """Test creating monster without variable damage uses defaults."""
        monster = self.factory.create_monster("troll", 10, 10)
        
        self.assertIsNotNone(monster)
        self.assertEqual(monster.name, "Test_Troll")
        self.assertEqual(monster.fighter.base_power, 8)
        self.assertEqual(monster.fighter.damage_min, 0)  # Default value
        self.assertEqual(monster.fighter.damage_max, 0)  # Default value

    @patch('random.randint')
    def test_created_monster_can_attack_with_variable_damage(self, mock_randint):
        """Test that factory-created monsters can use variable damage in combat."""
        mock_randint.return_value = 2
        
        # Create monster and target
        monster = self.factory.create_monster("orc", 5, 5)
        
        target = Mock()
        target.name = "player"
        target.fighter = Fighter(hp=100, defense=1, power=2)
        target.fighter.owner = target
        target.fighter.take_damage = Mock(return_value=[{"dead": False}])
        target.equipment = Mock()
        target.equipment.power_bonus = 0
        target.equipment.defense_bonus = 0
        target.equipment.main_hand = None
        target.equipment.off_hand = None
        
        # Perform attack
        results = monster.fighter.attack(target)
        
        # Verify variable damage was applied
        message_result = next(r for r in results if 'message' in r)
        self.assertIn("(3 power + 2 natural)", message_result['message'].text)


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing systems."""

    def test_existing_fighter_creation_still_works(self):
        """Test that existing Fighter creation without damage params still works."""
        # Old-style Fighter creation (should still work)
        fighter = Fighter(hp=20, defense=0, power=4, xp=35)
        
        self.assertEqual(fighter.hp, 20)
        self.assertEqual(fighter.base_power, 4)
        self.assertEqual(fighter.damage_min, 0)
        self.assertEqual(fighter.damage_max, 0)

    def test_weapon_damage_still_works_for_players(self):
        """Test that weapon damage system still works for players."""
        player = Mock()
        player.name = "player"
        player.fighter = Fighter(hp=100, defense=1, power=2)  # No monster damage
        player.fighter.owner = player
        
        # Set up weapon
        player.equipment = Mock()
        player.equipment.main_hand = Mock()
        player.equipment.main_hand.equippable = Mock()
        player.equipment.main_hand.equippable.roll_damage.return_value = 3
        player.equipment.defense_bonus = 0
        
        # Test that weapon damage is calculated
        weapon_damage = player.fighter._get_weapon_damage()
        monster_damage = player.fighter._get_monster_variable_damage()
        
        self.assertEqual(weapon_damage, 3)
        self.assertEqual(monster_damage, 0)

    def test_combat_system_handles_mixed_damage_types(self):
        """Test combat between player (weapon damage) and monster (natural damage)."""
        # Player with weapon
        player = Mock()
        player.name = "player"
        player.fighter = Fighter(hp=100, defense=1, power=2)
        player.fighter.owner = player
        player.fighter.take_damage = Mock(return_value=[{"dead": False}])
        # Mock get_component_optional to return None for BOSS (not a boss)
        player.get_component_optional = Mock(return_value=None)
        player.equipment = Mock()
        player.equipment.power_bonus = 0  # Add this line
        player.equipment.main_hand = Mock()
        player.equipment.main_hand.equippable = Mock()
        player.equipment.main_hand.equippable.roll_damage.return_value = 2
        player.equipment.defense_bonus = 0
        player.equipment.off_hand = None
        player.equipment.left_ring = None
        player.equipment.right_ring = None
        # Mock status_effects to prevent arithmetic errors
        status_effects_mock = Mock()
        status_effects_mock.get_effect = Mock(return_value=None)
        player.status_effects = status_effects_mock
        player.equipment.main_hand.item = None  # Prevent reach check from returning Mock
        
        # Monster with natural damage
        monster = Mock()
        monster.name = "orc"
        monster.fighter = Fighter(hp=20, defense=0, power=3, damage_min=1, damage_max=3)
        monster.fighter.owner = monster
        monster.fighter.take_damage = Mock(return_value=[{"dead": False}])
        # Mock get_component_optional to return None for BOSS (not a boss)
        monster.get_component_optional = Mock(return_value=None)
        monster.equipment = Mock()
        monster.equipment.power_bonus = 0  # Add this line
        monster.equipment.defense_bonus = 0
        monster.equipment.main_hand = None
        monster.equipment.off_hand = None
        monster.equipment.left_ring = None
        monster.equipment.right_ring = None
        # Mock status_effects to prevent arithmetic errors
        status_effects_mock = Mock()
        status_effects_mock.get_effect = Mock(return_value=None)
        monster.status_effects = status_effects_mock
        
        # Both should be able to attack using their respective damage systems
        with patch('random.randint', return_value=2):
            player_results = player.fighter.attack(monster)
            monster_results = monster.fighter.attack(player)
        
        # Verify both attacks worked
        self.assertGreater(len(player_results), 0)
        self.assertGreater(len(monster_results), 0)
        
        # Verify message formats
        player_msg = next(r for r in player_results if 'message' in r)['message'].text
        monster_msg = next(r for r in monster_results if 'message' in r)['message'].text
        
        self.assertIn("weapon", player_msg)
        self.assertIn("natural", monster_msg)


if __name__ == '__main__':
    unittest.main()
