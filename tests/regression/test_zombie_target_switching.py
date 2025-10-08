"""Regression tests for zombie target switching behavior.

Ensures zombies properly switch targets with 50% chance when multiple
adjacent targets are available.
"""

import unittest
from unittest.mock import patch, Mock

from entity import Entity
from components.fighter import Fighter
from components.ai import MindlessZombieAI
from components.faction import Faction
from map_objects.game_map import GameMap


class TestZombieTargetSwitching(unittest.TestCase):
    """Test zombie target switching logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create zombie
        zombie_fighter = Fighter(hp=40, defense=0, power=3)
        zombie_ai = MindlessZombieAI()
        self.zombie = Entity(10, 10, 'Z', (0, 0, 0), 'Zombie', blocks=True,
                           fighter=zombie_fighter, ai=zombie_ai)
        self.zombie.faction = Faction.NEUTRAL
        
        # Create player
        player_fighter = Fighter(hp=30, defense=1, power=0)
        self.player = Entity(11, 10, '@', (255, 255, 255), 'Player', blocks=True,
                           fighter=player_fighter)
        self.player.faction = Faction.PLAYER
        
        # Create orc
        orc_fighter = Fighter(hp=20, defense=0, power=3)
        self.orc = Entity(10, 11, 'o', (0, 255, 0), 'Orc', blocks=True,
                        fighter=orc_fighter)
        self.orc.faction = Faction.NEUTRAL
        
        # Create map
        self.game_map = GameMap(30, 30)
        for x in range(30):
            for y in range(30):
                self.game_map.tiles[x][y].blocked = False
                self.game_map.tiles[x][y].block_sight = False
        
        self.fov_map = Mock()
        self.entities = [self.zombie, self.player, self.orc]
    
    def test_zombie_switches_target_when_other_adjacent_50_percent(self):
        """REGRESSION: Zombie should have chance to switch when other target is adjacent."""
        # Zombie at (10, 10), locked onto player at (11, 10)
        # Orc at (10, 11) - also adjacent
        self.zombie.ai.current_target = self.player
        
        # Test with random() returning 0.3 (< 0.5, should switch)
        with patch('random.random', return_value=0.3):
            with patch('random.choice', return_value=self.orc):
                with patch.object(self.zombie.fighter, 'attack_d20', return_value=[]):
                    self.zombie.ai.take_turn(self.player, self.fov_map,
                                            self.game_map, self.entities)
        
        # Should have switched to orc
        self.assertEqual(self.zombie.ai.current_target, self.orc,
                        "Zombie should switch to orc when random() < 0.5")
    
    def test_zombie_does_not_switch_when_no_other_adjacent(self):
        """REGRESSION: Zombie shouldn't switch if only one target is adjacent."""
        # Only player adjacent, orc far away
        self.orc.x, self.orc.y = 20, 20  # Far away
        self.zombie.ai.current_target = self.player
        
        with patch('random.random', return_value=0.3):  # Would trigger switch
            with patch.object(self.zombie.fighter, 'attack_d20', return_value=[]):
                self.zombie.ai.take_turn(self.player, self.fov_map,
                                        self.game_map, self.entities)
        
        # Should NOT switch (no other adjacent targets)
        self.assertEqual(self.zombie.ai.current_target, self.player,
                        "Zombie should stay locked on player when no other targets")
    
    def test_zombie_can_switch_to_any_adjacent_target(self):
        """REGRESSION: Zombie should be able to switch to any adjacent target."""
        # Create multiple adjacent targets
        orc2_fighter = Fighter(hp=20, defense=0, power=3)
        orc2 = Entity(9, 10, 'o', (0, 255, 0), 'Orc2', blocks=True,
                    fighter=orc2_fighter)
        orc2.faction = Faction.NEUTRAL
        
        entities = [self.zombie, self.player, self.orc, orc2]
        
        # Zombie at (10, 10)
        # Player at (11, 10) - adjacent
        # Orc at (10, 11) - adjacent  
        # Orc2 at (9, 10) - adjacent
        # Total: 3 adjacent targets
        
        self.zombie.ai.current_target = self.player
        
        # Force switch with random() = 0.3
        with patch('random.random', return_value=0.3):
            with patch('random.choice', return_value=self.orc):
                with patch.object(self.zombie.fighter, 'attack_d20', return_value=[]):
                    self.zombie.ai.take_turn(self.player, self.fov_map,
                                            self.game_map, entities)
        
        # Should have switched to orc or orc2
        self.assertIn(self.zombie.ai.current_target, [self.orc, orc2],
                     "Zombie should switch to one of the other adjacent targets")


if __name__ == '__main__':
    unittest.main()

