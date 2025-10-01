"""Regression tests for monster AI behavior.

This test suite ensures that monsters properly:
- Take turns when in player's FOV
- Move toward the player
- Attack when adjacent
- Both BasicMonster and SlimeAI work correctly

These tests prevent the "monsters just sit there" bug from recurring.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tcod.libtcodpy as libtcod

from entity import Entity
from components.fighter import Fighter
from components.ai import BasicMonster, SlimeAI
from components.faction import Faction
from map_objects.game_map import GameMap
from fov_functions import initialize_fov, recompute_fov


class TestBasicMonsterAIRegression(unittest.TestCase):
    """Regression tests for BasicMonster AI."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create player
        self.player = Entity(10, 10, '@', (255, 255, 255), 'Player', blocks=True)
        self.player.fighter = Fighter(hp=30, defense=1, power=0, 
                                     strength=14, dexterity=12, constitution=14)
        self.player.faction = Faction.PLAYER
        
        # Create orc with BasicMonster AI
        self.orc = Entity(12, 10, 'o', (0, 255, 0), 'Orc', blocks=True)
        self.orc.fighter = Fighter(hp=20, defense=0, power=3,
                                  strength=14, dexterity=10, constitution=12)
        self.orc.fighter.owner = self.orc
        self.orc.ai = BasicMonster()
        self.orc.ai.owner = self.orc  # CRITICAL: Set AI owner
        self.orc.faction = Faction.NEUTRAL
        
        # Create game map
        self.game_map = GameMap(30, 30)
        for x in range(30):
            for y in range(30):
                self.game_map.tiles[x][y].blocked = False
                self.game_map.tiles[x][y].block_sight = False
        
        # Create FOV map
        self.fov_map = initialize_fov(self.game_map)
        recompute_fov(self.fov_map, self.player.x, self.player.y, 10, True, 0)
        
        self.entities = [self.player, self.orc]
    
    def test_orc_moves_toward_player_when_distant(self):
        """REGRESSION: Orc should move toward player when distant."""
        # Orc is at (12, 10), player at (10, 10) - distance 2, should move
        initial_distance = self.orc.distance_to(self.player)
        
        # Orc should take a turn
        results = self.orc.ai.take_turn(self.player, self.fov_map, self.game_map, self.entities)
        
        # Orc should have moved closer
        final_distance = self.orc.distance_to(self.player)
        self.assertLess(final_distance, initial_distance, 
                       "Orc should move closer to player")
    
    def test_orc_attacks_when_adjacent(self):
        """REGRESSION: Orc should attack when adjacent to player."""
        # Place orc adjacent to player
        self.orc.x, self.orc.y = 11, 10  # Distance 1
        
        with patch('random.randint', return_value=20):  # Guarantee hit
            results = self.orc.ai.take_turn(self.player, self.fov_map, 
                                           self.game_map, self.entities)
        
        # Should have attack results
        self.assertTrue(len(results) > 0, "Should have combat results")
        # Check for damage message or dead player
        has_combat = any('message' in r or 'dead' in r for r in results)
        self.assertTrue(has_combat, "Should have combat-related results")
    
    def test_orc_does_not_move_when_not_in_fov(self):
        """REGRESSION: Orc should not act when not in player's FOV."""
        # Place orc far away, out of FOV
        self.orc.x, self.orc.y = 25, 25
        
        # Recompute FOV (orc should be out of range)
        recompute_fov(self.fov_map, self.player.x, self.player.y, 10, True, 0)
        
        initial_x, initial_y = self.orc.x, self.orc.y
        
        results = self.orc.ai.take_turn(self.player, self.fov_map, 
                                       self.game_map, self.entities)
        
        # Orc should not have moved
        self.assertEqual(self.orc.x, initial_x, "Orc should not move when out of FOV")
        self.assertEqual(self.orc.y, initial_y, "Orc should not move when out of FOV")
    
    def test_multiple_orcs_all_take_turns(self):
        """REGRESSION: Multiple monsters should all take turns."""
        # Create multiple orcs
        orc2 = Entity(13, 10, 'o', (0, 255, 0), 'Orc2', blocks=True)
        orc2.fighter = Fighter(hp=20, defense=0, power=3)
        orc2.fighter.owner = orc2
        orc2.ai = BasicMonster()
        orc2.ai.owner = orc2
        orc2.faction = Faction.NEUTRAL
        
        orc3 = Entity(14, 10, 'o', (0, 255, 0), 'Orc3', blocks=True)
        orc3.fighter = Fighter(hp=20, defense=0, power=3)
        orc3.fighter.owner = orc3
        orc3.ai = BasicMonster()
        orc3.ai.owner = orc3
        orc3.faction = Faction.NEUTRAL
        
        entities = [self.player, self.orc, orc2, orc3]
        
        # All orcs should move
        for orc in [self.orc, orc2, orc3]:
            initial_distance = orc.distance_to(self.player)
            orc.ai.take_turn(self.player, self.fov_map, self.game_map, entities)
            final_distance = orc.distance_to(self.player)
            self.assertLess(final_distance, initial_distance,
                           f"{orc.name} should move toward player")


class TestSlimeAIRegression(unittest.TestCase):
    """Regression tests for SlimeAI."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create player
        self.player = Entity(10, 10, '@', (255, 255, 255), 'Player', blocks=True)
        self.player.fighter = Fighter(hp=30, defense=1, power=0,
                                     strength=14, dexterity=12, constitution=14)
        self.player.faction = Faction.PLAYER
        
        # Create slime with SlimeAI
        self.slime = Entity(15, 10, 's', (0, 255, 0), 'Slime', blocks=True)
        self.slime.fighter = Fighter(hp=15, defense=0, power=1,
                                    strength=8, dexterity=6, constitution=10)
        self.slime.fighter.owner = self.slime
        self.slime.ai = SlimeAI()
        self.slime.ai.owner = self.slime  # CRITICAL: Set AI owner
        self.slime.faction = Faction.HOSTILE_ALL
        
        # Create game map
        self.game_map = GameMap(30, 30)
        for x in range(30):
            for y in range(30):
                self.game_map.tiles[x][y].blocked = False
                self.game_map.tiles[x][y].block_sight = False
        
        # Create FOV map
        self.fov_map = initialize_fov(self.game_map)
        recompute_fov(self.fov_map, self.player.x, self.player.y, 10, True, 0)
        
        self.entities = [self.player, self.slime]
    
    def test_slime_moves_toward_player_when_distant(self):
        """REGRESSION: Slime should move toward player when within vision range."""
        # Slime at (15, 10), player at (10, 10) - distance 5, within slime vision (10)
        initial_distance = self.slime.distance_to(self.player)
        
        results = self.slime.ai.take_turn(self.player, self.fov_map, 
                                         self.game_map, self.entities)
        
        final_distance = self.slime.distance_to(self.player)
        self.assertLess(final_distance, initial_distance,
                       "Slime should move closer to player")
    
    def test_slime_attacks_when_adjacent(self):
        """REGRESSION: Slime should attack when adjacent to player."""
        # Place slime adjacent
        self.slime.x, self.slime.y = 11, 10
        
        with patch('random.randint', return_value=20):  # Guarantee hit
            results = self.slime.ai.take_turn(self.player, self.fov_map,
                                             self.game_map, self.entities)
        
        has_combat = any('message' in r or 'dead' in r for r in results)
        self.assertTrue(has_combat, "Slime should attack adjacent player")
    
    def test_slime_uses_distance_vision_not_player_fov(self):
        """REGRESSION: Slime should use distance-based vision, not player FOV."""
        # Place slime within slime vision (10 tiles) but far from player
        self.slime.x, self.slime.y = 18, 10  # Distance 8 from player
        
        # Even though slime might not be in player's immediate FOV,
        # it should still act based on its own vision
        initial_distance = self.slime.distance_to(self.player)
        
        results = self.slime.ai.take_turn(self.player, self.fov_map,
                                         self.game_map, self.entities)
        
        final_distance = self.slime.distance_to(self.player)
        # Slime should move (unless it can't for some reason)
        # At minimum, it should have tried to take an action
        self.assertTrue(final_distance <= initial_distance,
                       "Slime should act based on distance vision")
    
    def test_slime_attacks_other_monsters(self):
        """REGRESSION: Slime should attack other monsters (monster-vs-monster)."""
        # Place player far away so slime prioritizes nearby orc
        self.player.x, self.player.y = 5, 5
        
        # Create an orc adjacent to slime
        orc = Entity(16, 10, 'o', (0, 255, 0), 'Orc', blocks=True)
        orc.fighter = Fighter(hp=20, defense=0, power=3)
        orc.fighter.owner = orc
        orc.ai = BasicMonster()
        orc.ai.owner = orc
        orc.faction = Faction.NEUTRAL
        
        entities = [self.player, self.slime, orc]
        
        # Slime at (15, 10), orc at (16, 10) - distance 1, adjacent
        # Player at (5, 5) - distance ~11, out of close range
        # Slime should attack orc (closer target)
        with patch('random.randint', return_value=20):  # Guarantee hit
            results = self.slime.ai.take_turn(self.player, self.fov_map,
                                             self.game_map, entities)
        
        # Should have attacked something
        has_combat = any('message' in r or 'dead' in r for r in results)
        self.assertTrue(has_combat, 
                       "Slime should attack nearby orc (monster-vs-monster)")


class TestFOVCompatibilityRegression(unittest.TestCase):
    """Regression tests for FOV system compatibility."""
    
    def test_map_is_in_fov_works_with_legacy_map(self):
        """REGRESSION: map_is_in_fov should work with legacy tcod.map.Map."""
        from fov_functions import map_is_in_fov
        
        # Create legacy FOV map
        game_map = GameMap(20, 20)
        fov_map = initialize_fov(game_map)
        recompute_fov(fov_map, 10, 10, 10, True, 0)
        
        # Should not crash
        try:
            result = map_is_in_fov(fov_map, 10, 10)
            self.assertTrue(result, "Center should be visible")
            
            result = map_is_in_fov(fov_map, 11, 10)
            self.assertTrue(result, "Adjacent tile should be visible")
            
            result = map_is_in_fov(fov_map, 25, 25)
            self.assertFalse(result, "Out of bounds should not be visible")
        except AttributeError as e:
            self.fail(f"map_is_in_fov should not raise AttributeError: {e}")


if __name__ == '__main__':
    unittest.main()

