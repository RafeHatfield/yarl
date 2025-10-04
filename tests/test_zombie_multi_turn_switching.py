"""Integration test for zombie target switching over multiple turns.

This test simulates actual gameplay with a zombie, player, and orc all adjacent,
and runs through multiple turns to verify the zombie switches targets.
"""

import unittest
from unittest.mock import Mock, patch
from components.ai import MindlessZombieAI
from components.fighter import Fighter
from components.faction import Faction
from entity import Entity


class TestZombieMultiTurnSwitching(unittest.TestCase):
    """Integration test for zombie behavior over multiple turns."""
    
    def setUp(self):
        """Set up a realistic combat scenario."""
        # Create zombie at (10, 10)
        self.zombie = Entity(10, 10, 'Z', (0, 255, 0), 'Zombie', blocks=True)
        self.zombie.fighter = Fighter(hp=30, defense=0, power=5, strength=10, dexterity=10)
        self.zombie.fighter.owner = self.zombie
        self.zombie.ai = MindlessZombieAI()
        self.zombie.ai.owner = self.zombie
        self.zombie.faction = Faction.NEUTRAL
        
        # Create player adjacent at (11, 10)
        self.player = Entity(11, 10, '@', (255, 255, 255), 'Player', blocks=True)
        self.player.fighter = Fighter(hp=100, defense=10, power=5, strength=14, dexterity=14)
        self.player.fighter.owner = self.player
        self.player.faction = Faction.PLAYER
        
        # Create orc adjacent at (10, 11)
        self.orc = Entity(10, 11, 'o', (0, 255, 0), 'Orc', blocks=True)
        self.orc.fighter = Fighter(hp=20, defense=2, power=4, strength=12, dexterity=10)
        self.orc.fighter.owner = self.orc
        self.orc.faction = Faction.NEUTRAL  # Regular monsters are NEUTRAL
        
        self.game_map = Mock()
        self.fov_map = Mock()
        self.entities = [self.zombie, self.player, self.orc]
    
    def test_zombie_finds_adjacent_targets(self):
        """Test that _find_adjacent_targets correctly identifies adjacent entities."""
        adjacent = self.zombie.ai._find_adjacent_targets(self.entities)
        
        # Should find both player and orc (both adjacent)
        self.assertEqual(len(adjacent), 2, "Should find 2 adjacent targets")
        self.assertIn(self.player, adjacent)
        self.assertIn(self.orc, adjacent)
    
    def test_zombie_switches_target_over_multiple_turns(self):
        """Test that zombie DOES switch targets over multiple turns.
        
        This is the real bug scenario: zombie, player, and orc all adjacent.
        Over ~20 turns with 50% switch chance, we should see SOME switches.
        """
        # Start with zombie locked onto player
        self.zombie.ai.current_target = self.player
        
        switches = 0
        current_target = self.player
        
        # Run 20 turns with real randomness
        for turn in range(20):
            # Mock the attack to avoid actual damage
            with patch.object(self.zombie.fighter, 'attack_d20', return_value=[]):
                self.zombie.ai.take_turn(
                    target=None,
                    fov_map=self.fov_map,
                    game_map=self.game_map,
                    entities=self.entities
                )
            
            # Check if target switched
            if self.zombie.ai.current_target != current_target:
                switches += 1
                current_target = self.zombie.ai.current_target
        
        # With 50% chance per turn, we expect ~10 switches in 20 turns
        # But let's be conservative and just check for ANY switches
        self.assertGreater(switches, 0, 
                          f"Zombie should switch targets at least once in 20 turns (got {switches} switches)")
        
        # With 50% chance, getting 0 switches in 20 turns is extremely unlikely (~0.0001%)
        # If this fails, there's a bug in the switching logic
    
    def test_zombie_switching_with_controlled_randomness(self):
        """Test switching with controlled random values."""
        # Start with zombie locked onto player
        self.zombie.ai.current_target = self.player
        
        # Turn 1: Force switch (random = 0.3 < 0.5)
        with patch('random.random', return_value=0.3):
            with patch('random.choice', return_value=self.orc):
                with patch.object(self.zombie.fighter, 'attack_d20', return_value=[]):
                    self.zombie.ai.take_turn(None, self.fov_map, self.game_map, self.entities)
        
        self.assertEqual(self.zombie.ai.current_target, self.orc,
                        "Should switch to orc when random() < 0.5")
        
        # Turn 2: Force NO switch (random = 0.7 >= 0.5)
        with patch('random.random', return_value=0.7):
            with patch.object(self.zombie.fighter, 'attack_d20', return_value=[]):
                self.zombie.ai.take_turn(None, self.fov_map, self.game_map, self.entities)
        
        self.assertEqual(self.zombie.ai.current_target, self.orc,
                        "Should stay on orc when random() >= 0.5")
        
        # Turn 3: Force switch back to player
        with patch('random.random', return_value=0.2):
            with patch('random.choice', return_value=self.player):
                with patch.object(self.zombie.fighter, 'attack_d20', return_value=[]):
                    self.zombie.ai.take_turn(None, self.fov_map, self.game_map, self.entities)
        
        self.assertEqual(self.zombie.ai.current_target, self.player,
                        "Should switch back to player")
    
    def test_zombie_only_switches_when_multiple_adjacent(self):
        """Test that zombie only considers switching when there are other targets."""
        # Move orc far away, only player adjacent
        self.orc.x, self.orc.y = 20, 20
        entities = [self.zombie, self.player, self.orc]
        
        self.zombie.ai.current_target = self.player
        
        # Even with 50% switch chance, should NOT switch (no other adjacent)
        switches = 0
        for _ in range(10):
            old_target = self.zombie.ai.current_target
            with patch.object(self.zombie.fighter, 'attack_d20', return_value=[]):
                self.zombie.ai.take_turn(None, self.fov_map, self.game_map, entities)
            if self.zombie.ai.current_target != old_target:
                switches += 1
        
        self.assertEqual(switches, 0, 
                        "Zombie should NOT switch when only one target is adjacent")


if __name__ == '__main__':
    unittest.main()

