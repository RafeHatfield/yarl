"""Tests for the d20-based combat system.

This test suite ensures that:
- d20 attack rolls work correctly
- AC (Armor Class) is calculated properly
- Critical hits (natural 20) double damage
- Fumbles (natural 1) always miss
- Hit percentages are displayed correctly
- STR modifier applies to damage
- DEX modifier applies to to-hit
- Combat logging works in testing mode
"""


# QUARANTINED: D20 combat mechanics need review
# See QUARANTINED_TESTS.md for details.

import pytest

# Quarantine entire file
# pytestmark = pytest.mark.skip(reason="Quarantined - D20 combat mechanics need review. See QUARANTINED_TESTS.md")  # REMOVED Session 2

import unittest
from unittest.mock import patch, MagicMock, Mock
from components.fighter import Fighter
from entity import Entity
from components.equipment import Equipment
from components.equippable import Equippable
from components.component_registry import ComponentType


class TestArmorClass(unittest.TestCase):
    """Test AC (Armor Class) calculation."""
    
    def test_base_ac_no_equipment(self):
        """Test base AC = 10 + DEX mod with no equipment."""
        fighter = Fighter(hp=30, defense=0, power=0, dexterity=12)  # +1 DEX mod
        entity = Entity(0, 0, '@', (255, 255, 255), 'Test', blocks=True)
        entity.fighter = fighter
        fighter.owner = entity
        
        self.assertEqual(fighter.armor_class, 11)  # 10 + 1 DEX
    
    def test_ac_with_high_dex(self):
        """Test AC with high DEX."""
        fighter = Fighter(hp=30, defense=0, power=0, dexterity=18)  # +4 DEX mod
        entity = Entity(0, 0, '@', (255, 255, 255), 'Test', blocks=True)
        entity.fighter = fighter
        fighter.owner = entity
        
        self.assertEqual(fighter.armor_class, 14)  # 10 + 4 DEX
    
    def test_ac_with_low_dex(self):
        """Test AC with low DEX."""
        fighter = Fighter(hp=30, defense=0, power=0, dexterity=8)  # -1 DEX mod
        entity = Entity(0, 0, '@', (255, 255, 255), 'Test', blocks=True)
        entity.fighter = fighter
        fighter.owner = entity
        
        self.assertEqual(fighter.armor_class, 9)  # 10 - 1 DEX
    
    def test_ac_with_armor_bonus(self):
        """Test AC with armor providing AC bonus."""
        fighter = Fighter(hp=30, defense=0, power=0, dexterity=12)  # +1 DEX mod
        entity = Entity(0, 0, '@', (255, 255, 255), 'Test', blocks=True)
        entity.fighter = fighter
        fighter.owner = entity
        
        # Add equipment component (needs owner)
        equipment = Equipment(entity)
        entity.equipment = equipment
        
        # Create armor with AC bonus
        armor = Entity(0, 0, '[', (100, 100, 100), 'Shield', blocks=False)
        armor_equippable = MagicMock()
        armor_equippable.armor_class_bonus = 2
        armor.equippable = armor_equippable
        # Mock components for proper integration
        armor.components = Mock()
        armor.components.has = Mock(return_value=False)  # Use direct attribute access
        
        # Equip armor
        equipment.off_hand = armor
        
        self.assertEqual(fighter.armor_class, 13)  # 10 + 1 DEX + 2 armor


class TestD20AttackRoll(unittest.TestCase):
    """Test d20 attack roll mechanics."""
    
    def setUp(self):
        """Set up test entities."""
        # Create attacker (DEX 14 = +2 mod, STR 14 = +2 mod)
        self.attacker = Entity(0, 0, 'A', (255, 255, 255), 'Attacker', blocks=True)
        self.attacker.fighter = Fighter(
            hp=30, defense=0, power=0,
            strength=14, dexterity=14, constitution=10,
            damage_min=1, damage_max=4
        )
        self.attacker.fighter.owner = self.attacker
        self.attacker.equipment = Equipment()
        
        # Create target (DEX 10 = 0 mod, AC = 10)
        self.target = Entity(1, 0, 'T', (255, 0, 0), 'Target', blocks=True)
        self.target.fighter = Fighter(
            hp=30, defense=0, power=0,
            strength=10, dexterity=10, constitution=10
        )
        self.target.fighter.owner = self.target
        self.target.equipment = Equipment()
    
    @patch('random.randint')
    def test_attack_hits_on_sufficient_roll(self, mock_randint):
        """Test that attack hits when roll + modifiers >= target AC."""
        # Roll 8 + 2 (DEX) = 10, target AC = 10, should HIT
        mock_randint.return_value = 8
        
        results = self.attacker.fighter.attack_d20(self.target)
        
        # Should have at least one message
        self.assertTrue(len(results) > 0)
        # Message should indicate HIT
        message = results[0].get('message')
        self.assertIsNotNone(message)
        self.assertIn('HIT', message.text)
    
    @patch('random.randint')
    def test_attack_misses_on_low_roll(self, mock_randint):
        """Test that attack misses when roll + modifiers < target AC."""
        # Roll 5 + 2 (DEX) = 7, target AC = 10, should MISS
        mock_randint.return_value = 5
        
        results = self.attacker.fighter.attack_d20(self.target)
        
        # Should have a message
        self.assertTrue(len(results) > 0)
        # Message should indicate MISS
        message = results[0].get('message')
        self.assertIsNotNone(message)
        self.assertIn('MISS', message.text)
    
    @patch('random.randint')
    def test_critical_hit_on_natural_20(self, mock_randint):
        """Test that natural 20 always hits and doubles damage."""
        # Natural 20
        mock_randint.side_effect = [20, 2]  # d20 roll = 20, damage roll = 2
        
        initial_hp = self.target.fighter.hp
        results = self.attacker.fighter.attack_d20(self.target)
        
        # Should have messages
        self.assertTrue(len(results) > 0)
        # Message should indicate CRITICAL HIT
        message = results[0].get('message')
        self.assertIsNotNone(message)
        self.assertIn('CRITICAL', message.text.upper())
        
        # Damage should be doubled: (2 base + 2 STR) * 2 = 8
        damage_dealt = initial_hp - self.target.fighter.hp
        self.assertEqual(damage_dealt, 8)
    
    @patch('random.randint')
    def test_fumble_on_natural_1(self, mock_randint):
        """Test that natural 1 always misses (fumble)."""
        # Natural 1
        mock_randint.return_value = 1
        
        initial_hp = self.target.fighter.hp
        results = self.attacker.fighter.attack_d20(self.target)
        
        # Should have a message
        self.assertTrue(len(results) > 0)
        # Message should indicate FUMBLE or miss
        message = results[0].get('message')
        self.assertIsNotNone(message)
        self.assertTrue('FUMBLE' in message.text or 'miss' in message.text.lower())
        
        # No damage should be dealt
        self.assertEqual(self.target.fighter.hp, initial_hp)
    
    @patch('random.randint')
    def test_str_modifier_applies_to_damage(self, mock_randint):
        """Test that STR modifier is added to damage."""
        # Roll to hit: 15 (will hit AC 10)
        # Damage roll: 3
        # Expected damage: 3 (base) + 2 (STR) = 5
        mock_randint.side_effect = [15, 3]
        
        initial_hp = self.target.fighter.hp
        results = self.attacker.fighter.attack_d20(self.target)
        
        damage_dealt = initial_hp - self.target.fighter.hp
        self.assertEqual(damage_dealt, 5)
    
    @patch('random.randint')
    def test_dex_modifier_applies_to_hit(self, mock_randint):
        """Test that DEX modifier is added to attack roll."""
        # Attacker has DEX 14 (+2 mod)
        # Roll 8 + 2 = 10, should hit AC 10
        mock_randint.side_effect = [8, 2]  # Attack roll, damage roll
        
        results = self.attacker.fighter.attack_d20(self.target)
        
        # Should hit
        message = results[0].get('message')
        self.assertIn('HIT', message.text)


class TestCombatMessages(unittest.TestCase):
    """Test combat message formatting."""
    
    def setUp(self):
        """Set up test entities."""
        self.attacker = Entity(0, 0, 'A', (255, 255, 255), 'Hero', blocks=True)
        self.attacker.fighter = Fighter(
            hp=30, defense=0, power=0,
            strength=14, dexterity=14, constitution=10,
            damage_min=1, damage_max=4
        )
        self.attacker.fighter.owner = self.attacker
        self.attacker.equipment = Equipment()
        
        self.target = Entity(1, 0, 'T', (255, 0, 0), 'Goblin', blocks=True)
        self.target.fighter = Fighter(
            hp=30, defense=0, power=0,
            strength=10, dexterity=10, constitution=10
        )
        self.target.fighter.owner = self.target
        self.target.equipment = Equipment()
    
    @patch('random.randint')
    def test_hit_message_shows_percentage(self, mock_randint):
        """Test that hit messages show hit percentage."""
        mock_randint.side_effect = [15, 2]  # Hit roll, damage roll
        
        results = self.attacker.fighter.attack_d20(self.target)
        
        message = results[0].get('message')
        # Message should contain percentage (e.g., "65% to hit")
        self.assertTrue('%' in message.text)
    
    @patch('random.randint')
    def test_miss_message_shows_percentage(self, mock_randint):
        """Test that miss messages show hit percentage."""
        mock_randint.return_value = 2  # Miss
        
        results = self.attacker.fighter.attack_d20(self.target)
        
        message = results[0].get('message')
        # Message should contain percentage and MISS
        self.assertTrue('%' in message.text)
        self.assertIn('MISS', message.text)
    
    @patch('random.randint')
    def test_critical_message_format(self, mock_randint):
        """Test critical hit message formatting."""
        mock_randint.side_effect = [20, 2]  # Crit, damage
        
        results = self.attacker.fighter.attack_d20(self.target)
        
        message = results[0].get('message')
        # Critical message should be gold color and contain CRITICAL
        self.assertIn('CRITICAL', message.text.upper())
        self.assertEqual(message.color, (255, 215, 0))  # Gold
    
    @patch('random.randint')
    def test_fumble_message_format(self, mock_randint):
        """Test fumble message formatting."""
        mock_randint.return_value = 1  # Fumble
        
        results = self.attacker.fighter.attack_d20(self.target)
        
        message = results[0].get('message')
        # Fumble message should contain FUMBLE or miss
        self.assertTrue('FUMBLE' in message.text or 'miss' in message.text.lower())


class TestWeaponBonuses(unittest.TestCase):
    """Test weapon to-hit and damage bonuses."""
    
    def setUp(self):
        """Set up test entities with weapons."""
        self.attacker = Entity(0, 0, 'A', (255, 255, 255), 'Fighter', blocks=True)
        self.attacker.fighter = Fighter(
            hp=30, defense=0, power=0,
            strength=14, dexterity=12, constitution=10,
            damage_min=1, damage_max=2
        )
        self.attacker.fighter.owner = self.attacker
        self.attacker.equipment = Equipment()
        
        self.target = Entity(1, 0, 'T', (255, 0, 0), 'Orc', blocks=True)
        self.target.fighter = Fighter(
            hp=30, defense=0, power=0,
            strength=10, dexterity=10, constitution=10
        )
        self.target.fighter.owner = self.target
        self.target.equipment = Equipment()
    
    @patch('random.randint')
    def test_weapon_to_hit_bonus_applies(self, mock_randint):
        """Test that weapon to-hit bonus is added to attack roll."""
        # Create weapon with +1 to-hit
        weapon = Entity(0, 0, '/', (200, 200, 200), 'Sword', blocks=False)
        weapon_equippable = MagicMock()
        weapon_equippable.to_hit_bonus = 1
        weapon_equippable.damage_min = 2
        weapon_equippable.damage_max = 5
        weapon_equippable.roll_damage = MagicMock(return_value=3)
        weapon.equippable = weapon_equippable
        
        self.attacker.equipment.main_hand = weapon
        
        # Roll 7 + 1 (DEX) + 1 (weapon) = 9, target AC = 10, should MISS
        # Roll 8 + 1 (DEX) + 1 (weapon) = 10, target AC = 10, should HIT
        mock_randint.return_value = 8
        
        results = self.attacker.fighter.attack_d20(self.target)
        
        # Should hit thanks to weapon bonus
        message = results[0].get('message')
        self.assertIn('HIT', message.text)


class TestMinimumDamage(unittest.TestCase):
    """Test that attacks always deal at least 1 damage on hit."""
    
    def setUp(self):
        """Set up entities where damage might be <= 0."""
        # Attacker with negative STR modifier
        self.attacker = Entity(0, 0, 'A', (255, 255, 255), 'Weakling', blocks=True)
        self.attacker.fighter = Fighter(
            hp=30, defense=0, power=0,
            strength=6, dexterity=14, constitution=10,  # STR 6 = -2 mod
            damage_min=1, damage_max=1  # Roll 1 - 2 STR = -1
        )
        self.attacker.fighter.owner = self.attacker
        self.attacker.equipment = Equipment()
        
        self.target = Entity(1, 0, 'T', (255, 0, 0), 'Target', blocks=True)
        self.target.fighter = Fighter(
            hp=30, defense=0, power=0,
            strength=10, dexterity=10, constitution=10
        )
        self.target.fighter.owner = self.target
        self.target.equipment = Equipment()
    
    @patch('random.randint')
    def test_minimum_1_damage_on_hit(self, mock_randint):
        """Test that attacks deal at least 1 damage even with negative modifiers."""
        # Hit roll, damage roll of 1
        # 1 (roll) + (-2 STR) = -1, should be clamped to 1
        mock_randint.side_effect = [15, 1]
        
        initial_hp = self.target.fighter.hp
        results = self.attacker.fighter.attack_d20(self.target)
        
        damage_dealt = initial_hp - self.target.fighter.hp
        self.assertEqual(damage_dealt, 1)  # Minimum damage


if __name__ == '__main__':
    unittest.main()

