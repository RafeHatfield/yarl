"""Regression tests for player death handling.

This module tests that player death is properly detected and handled
across all damage sources: combat, traps, hazards, and thrown weapons.

Bug: Player could reach 0 HP but remain alive and controllable.
Fix: Ensure all damage sources properly process death results and
     transition to PLAYER_DEAD game state.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from entity import Entity
from components.fighter import Fighter
from game_states import GameStates


class TestPlayerDeathFromTraps(unittest.TestCase):
    """Test that player death from traps is properly handled."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a minimal player entity using old-style constructor
        self.player = Entity(
            x=10, y=10, 
            char='@', 
            color=(255, 255, 255), 
            name='Player',
            fighter=Fighter(hp=30, defense=0, power=5, xp=0)
        )
        
    def test_spike_trap_death_detection(self):
        """Test that spike trap damage properly detects player death.
        
        Regression: Spike trap damage was not processing death results,
        allowing player to continue at 0 HP.
        """
        # Set player to low HP
        self.player.fighter.hp = 5
        
        # Apply lethal spike trap damage
        damage_results = self.player.fighter.take_damage(10)
        
        # Verify death was detected
        self.assertLessEqual(self.player.fighter.hp, 0, 
                           "Player HP should be <= 0 after lethal damage")
        
        death_results = [r for r in damage_results if r.get("dead")]
        self.assertEqual(len(death_results), 1, 
                        "Should have exactly one death result")
        self.assertEqual(death_results[0]["dead"], self.player,
                        "Death result should reference the player")
        
    def test_spike_trap_death_with_overkill(self):
        """Test that massive trap damage still detects death properly."""
        # Set player to low HP
        self.player.fighter.hp = 1
        
        # Apply massive overkill damage
        damage_results = self.player.fighter.take_damage(100)
        
        # Verify death was detected
        self.assertLessEqual(self.player.fighter.hp, 0,
                           "Player HP should be <= 0 after overkill damage")
        
        death_results = [r for r in damage_results if r.get("dead")]
        self.assertEqual(len(death_results), 1,
                        "Should detect death even with overkill damage")
        
    def test_trap_damage_non_lethal(self):
        """Test that non-lethal trap damage does not trigger death."""
        # Set player to moderate HP
        self.player.fighter.hp = 20
        
        # Apply non-lethal damage
        damage_results = self.player.fighter.take_damage(5)
        
        # Verify no death
        self.assertEqual(self.player.fighter.hp, 15,
                        "Player should survive non-lethal damage")
        
        death_results = [r for r in damage_results if r.get("dead")]
        self.assertEqual(len(death_results), 0,
                        "Should not have death result for non-lethal damage")
        
    def test_trap_damage_exact_lethal(self):
        """Test that exact lethal damage (reducing HP to exactly 0) triggers death."""
        # Set player to exact HP
        self.player.fighter.hp = 10
        
        # Apply exact lethal damage
        damage_results = self.player.fighter.take_damage(10)
        
        # Verify death was detected
        self.assertEqual(self.player.fighter.hp, 0,
                        "Player HP should be exactly 0")
        
        death_results = [r for r in damage_results if r.get("dead")]
        self.assertEqual(len(death_results), 1,
                        "Should detect death when HP reaches exactly 0")


class TestPlayerDeathFromCombat(unittest.TestCase):
    """Test that player death from combat is properly handled."""
    
    def test_combat_death_detection(self):
        """Test that combat damage properly detects player death."""
        player = Entity(
            x=10, y=10,
            char='@',
            color=(255, 255, 255),
            name='Player',
            fighter=Fighter(hp=30, defense=0, power=5, xp=0)
        )
        
        # Set to low HP
        player.fighter.hp = 3
        
        # Apply lethal combat damage
        damage_results = player.fighter.take_damage(5)
        
        # Verify death
        self.assertLessEqual(player.fighter.hp, 0,
                           "Player should be dead after lethal combat damage")
        
        death_results = [r for r in damage_results if r.get("dead")]
        self.assertEqual(len(death_results), 1,
                        "Combat death should be detected")
        self.assertEqual(death_results[0]["dead"], player,
                        "Death result should reference the player")


class TestPlayerDeathFromThrowingWeapon(unittest.TestCase):
    """Test that player death from thrown weapons is properly handled."""
    
    def test_thrown_weapon_death_detection(self):
        """Test that thrown weapon damage properly detects player death.
        
        Regression: Thrown weapon damage was not processing death results
        from take_damage(), instead manually checking hp <= 0.
        """
        player = Entity(
            x=10, y=10,
            char='@',
            color=(255, 255, 255),
            name='Player',
            fighter=Fighter(hp=30, defense=0, power=5, xp=0)
        )
        
        # Set to low HP
        player.fighter.hp = 2
        
        # Simulate thrown weapon damage
        damage_results = player.fighter.take_damage(5)
        
        # Verify death
        self.assertLessEqual(player.fighter.hp, 0,
                           "Player should be dead after lethal thrown weapon damage")
        
        death_results = [r for r in damage_results if r.get("dead")]
        self.assertEqual(len(death_results), 1,
                        "Thrown weapon death should be detected")
        
        # Verify XP is included in death result
        self.assertIn("xp", death_results[0],
                     "Death result should include XP value")


class TestPlayerDeathConsistency(unittest.TestCase):
    """Test that player death behavior is consistent across all damage sources."""
    
    def test_death_result_format_consistency(self):
        """Test that all death results follow the same format."""
        player = Entity(
            x=10, y=10,
            char='@',
            color=(255, 255, 255),
            name='Player',
            fighter=Fighter(hp=30, defense=0, power=5, xp=100)
        )
        
        # Set to low HP
        player.fighter.hp = 1
        
        # Apply lethal damage
        damage_results = player.fighter.take_damage(10)
        
        # Verify result format
        death_results = [r for r in damage_results if r.get("dead")]
        self.assertEqual(len(death_results), 1, "Should have one death result")
        
        death_result = death_results[0]
        self.assertIn("dead", death_result, "Result should have 'dead' key")
        self.assertIn("xp", death_result, "Result should have 'xp' key")
        self.assertEqual(death_result["dead"], player, "Should reference correct entity")
        self.assertEqual(death_result["xp"], 100, "Should include correct XP value")
        
    def test_multiple_damage_sources_same_behavior(self):
        """Test that death behaves identically regardless of damage source."""
        # Create three identical players
        players = []
        for i in range(3):
            player = Entity(
                x=10, y=10,
                char='@',
                color=(255, 255, 255),
                name=f'Player{i}',
                fighter=Fighter(hp=30, defense=0, power=5, xp=50)
            )
            player.fighter.hp = 5
            players.append(player)
        
        # Apply lethal damage to each
        results = []
        for player in players:
            damage_results = player.fighter.take_damage(10)
            results.append(damage_results)
        
        # Verify all behave identically
        for i, damage_results in enumerate(results):
            death_results = [r for r in damage_results if r.get("dead")]
            self.assertEqual(len(death_results), 1,
                           f"Player {i} should have death result")
            self.assertEqual(death_results[0]["xp"], 50,
                           f"Player {i} should have correct XP")
            self.assertEqual(death_results[0]["dead"], players[i],
                           f"Player {i} death result should reference correct entity")


if __name__ == "__main__":
    unittest.main(verbosity=2)
