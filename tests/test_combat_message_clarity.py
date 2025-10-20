"""Tests for clear combat message formatting."""


# QUARANTINED: Message format assertions need review
# See QUARANTINED_TESTS.md for details.

import pytest

# Quarantine entire file
# pytestmark = pytest.mark.skip(reason="Quarantined - Message format assertions need review. See QUARANTINED_TESTS.md")  # REMOVED Session 2
import unittest
from unittest.mock import patch
import os

from entity import Entity
from components.fighter import Fighter
from components.equippable import Equippable
from components.equipment import Equipment
from components.faction import Faction


class TestCombatMessageClarity(unittest.TestCase):
    """Test that combat messages show clear, understandable math."""
    
    def setUp(self):
        """Set up test entities."""
        # Enable testing mode for debug logging
        os.environ['YARL_TESTING_MODE'] = '1'
        
        # Create basic orc
        self.orc = Entity(0, 0, 'o', (255, 0, 0), 'Orc', blocks=True, 
                         render_order=4, fighter=Fighter(hp=10, defense=0, power=0, damage_min=4, damage_max=6),
                         faction=Faction.NEUTRAL)
        
        # Create basic player
        self.player = Entity(1, 0, '@', (255, 255, 255), 'Player', blocks=True, 
                            render_order=4, fighter=Fighter(hp=30, defense=1, power=0, damage_min=3, damage_max=5),
                            faction=Faction.PLAYER)
        
        # Create armor for player
        self.armor = Entity(0, 0, ']', (139, 69, 19), 'Leather Armor', 
                           equippable=Equippable(slot='off_hand', defense_bonus=0, defense_min=1, defense_max=3))
        
        # Equip armor on player
        self.player.equipment = Equipment()
        self.player.equipment.off_hand = self.armor
    
    def test_combat_message_math_adds_up(self):
        """Test that combat message math is clear and correct."""
        # Mock specific damage rolls for predictable results
        with patch.object(self.orc.fighter, '_get_base_variable_damage', return_value=5), \
             patch.object(self.player.fighter, '_get_armor_defense', return_value=2):
            
            results = self.orc.fighter.attack(self.player)
            
            # Find the combat message
            message_result = next(r for r in results if "message" in r)
            message_text = message_result["message"].text
            
            # Expected: 5 attack (0 power + 5 natural) - 3 defense (1 base + 2 armor) = 2 damage
            self.assertIn("for 2 damage", message_text)
            self.assertIn("5 attack (0 power + 5 natural)", message_text)
            self.assertIn("3 defense (1 base + 2 armor)", message_text)
            
            # Verify the math: 5 - 3 = 2
            self.assertEqual(self.player.fighter.hp, 30 - 2)  # Player took 2 damage
    
    def test_blocked_attack_message_math(self):
        """Test that blocked attack messages show clear math."""
        # Create a weak attacker vs strong defender
        weak_orc = Entity(0, 0, 'o', (255, 0, 0), 'Weak Orc', blocks=True, 
                         fighter=Fighter(hp=10, defense=0, power=0, damage_min=1, damage_max=2),
                         faction=Faction.NEUTRAL)
        
        strong_armor = Entity(0, 0, ']', (139, 69, 19), 'Plate Armor', 
                             equippable=Equippable(slot='off_hand', defense_bonus=0, defense_min=4, defense_max=6))
        
        armored_player = Entity(1, 0, '@', (255, 255, 255), 'Armored Player', blocks=True, 
                               fighter=Fighter(hp=30, defense=3, power=0),
                               faction=Faction.PLAYER)
        armored_player.equipment = Equipment()
        armored_player.equipment.off_hand = strong_armor
        
        # Mock damage rolls to ensure blocking
        with patch.object(weak_orc.fighter, '_get_base_variable_damage', return_value=1), \
             patch.object(armored_player.fighter, '_get_armor_defense', return_value=5):
            
            results = weak_orc.fighter.attack(armored_player)
            
            # Find the combat message
            message_result = next(r for r in results if "message" in r)
            message_text = message_result["message"].text
            
            # Expected: 1 attack (0 power + 1 natural) - 8 defense (3 base + 5 armor) = 0 damage
            self.assertIn("for 0 damage", message_text)
            self.assertIn("1 attack (0 power + 1 natural)", message_text)
            self.assertIn("8 defense (3 base + 5 armor)", message_text)
            self.assertIn("attack blocked", message_text)
            
            # Verify no damage was dealt
            self.assertEqual(armored_player.fighter.hp, 30)  # No damage taken
    
    def test_weapon_attack_message_format(self):
        """Test that weapon attacks show correct power + weapon breakdown."""
        # Create a weapon
        sword = Entity(0, 0, '/', (192, 192, 192), 'Sword', 
                      equippable=Equippable(slot='main_hand', power_bonus=2, damage_min=2, damage_max=4))
        
        # Equip weapon on orc
        self.orc.equipment = Equipment()
        self.orc.equipment.main_hand = sword
        
        # Mock specific damage rolls
        with patch.object(sword.equippable, 'roll_damage', return_value=3), \
             patch.object(self.player.fighter, '_get_armor_defense', return_value=1):
            
            results = self.orc.fighter.attack(self.player)
            
            # Find the combat message
            message_result = next(r for r in results if "message" in r)
            message_text = message_result["message"].text
            
            # Expected: 5 attack (2 power + 3 weapon) - 2 defense (1 base + 1 armor) = 3 damage
            self.assertIn("for 3 damage", message_text)
            self.assertIn("5 attack (2 power + 3 weapon)", message_text)
            self.assertIn("2 defense (1 base + 1 armor)", message_text)
    
    def test_no_variable_damage_message_format(self):
        """Test message format when no variable damage is rolled."""
        # Create entities with no variable damage capability
        simple_orc = Entity(0, 0, 'o', (255, 0, 0), 'Simple Orc', blocks=True, 
                           fighter=Fighter(hp=10, defense=0, power=3),  # Only base power
                           faction=Faction.NEUTRAL)
        
        simple_player = Entity(1, 0, '@', (255, 255, 255), 'Simple Player', blocks=True, 
                              fighter=Fighter(hp=30, defense=2, power=0),  # Only base defense
                              faction=Faction.PLAYER)
        
        # Mock zero variable damage
        with patch.object(simple_orc.fighter, '_get_base_variable_damage', return_value=0), \
             patch.object(simple_player.fighter, '_get_armor_defense', return_value=0):
            
            results = simple_orc.fighter.attack(simple_player)
            
            # Find the combat message
            message_result = next(r for r in results if "message" in r)
            message_text = message_result["message"].text
            
            # Expected: 3 attack - 2 defense = 1 damage (no breakdown details)
            self.assertIn("for 1 damage", message_text)
            self.assertIn("3 attack", message_text)
            self.assertIn("2 defense", message_text)
            # Should not have breakdown details when no variable damage
            self.assertNotIn("power +", message_text)
            self.assertNotIn("base +", message_text)


if __name__ == '__main__':
    unittest.main()
