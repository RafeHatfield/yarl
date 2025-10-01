"""Tests for Large Slime splitting mechanics."""

import unittest
from unittest.mock import patch, MagicMock
import os

from entity import Entity
from components.fighter import Fighter
from components.faction import Faction
from death_functions import kill_monster, _handle_slime_splitting, _can_monster_split, _get_valid_spawn_positions
from config.entity_registry import load_entity_config
from config.entity_factory import EntityFactory


class TestSlimeSplitting(unittest.TestCase):
    """Test the slime splitting mechanics."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Enable testing mode
        os.environ['YARL_TESTING_MODE'] = '1'
        
        # Load entity config for proper slime creation
        load_entity_config()
        
        # Create a large slime with splitting ability
        self.large_slime = Entity(5, 5, 'S', (0, 200, 0), 'Large Slime', blocks=True, 
                                 render_order=4, fighter=Fighter(hp=40, defense=1, power=0),
                                 faction=Faction.HOSTILE_ALL)
        self.large_slime.special_abilities = ['corrosion', 'splitting']
        
        # Create a regular slime without splitting
        self.regular_slime = Entity(3, 3, 's', (0, 255, 0), 'Slime', blocks=True, 
                                   render_order=4, fighter=Fighter(hp=15, defense=0, power=0),
                                   faction=Faction.HOSTILE_ALL)
        self.regular_slime.special_abilities = ['corrosion']
        
        # Create a mock game map
        self.mock_game_map = MagicMock()
        self.mock_game_map.width = 20
        self.mock_game_map.height = 20
        
        # Create mock tiles - all walkable for simplicity (each tile is a separate object)
        self.mock_game_map.tiles = []
        for x in range(20):
            row = []
            for y in range(20):
                mock_tile = MagicMock()
                mock_tile.blocked = False
                row.append(mock_tile)
            self.mock_game_map.tiles.append(row)
    
    def test_can_monster_split_detection(self):
        """Test detection of monsters that can split."""
        # Large slime should be able to split
        self.assertTrue(_can_monster_split(self.large_slime))
        
        # Regular slime should not be able to split
        self.assertFalse(_can_monster_split(self.regular_slime))
        
        # Monster without special_abilities should not split
        basic_orc = Entity(1, 1, 'o', (255, 0, 0), 'Orc', blocks=True, 
                          render_order=4, fighter=Fighter(hp=10, defense=0, power=3),
                          faction=Faction.NEUTRAL)
        self.assertFalse(_can_monster_split(basic_orc))
    
    def test_get_valid_spawn_positions(self):
        """Test finding valid spawn positions around a center point."""
        # Test normal case - should find positions around center
        positions = _get_valid_spawn_positions(5, 5, self.mock_game_map, 3)
        
        self.assertGreater(len(positions), 0)
        self.assertLessEqual(len(positions), 3)
        
        # All positions should be adjacent to center (within 3 tiles)
        for x, y in positions:
            distance = max(abs(x - 5), abs(y - 5))
            self.assertLessEqual(distance, 3)
            self.assertGreater(distance, 0)  # Should not be the center itself
    
    def test_get_valid_spawn_positions_blocked_tiles(self):
        """Test spawn position finding with some blocked tiles."""
        # Block some tiles around the center
        for i in range(4, 7):
            for j in range(4, 7):
                if i != 5 or j != 5:  # Don't block center
                    self.mock_game_map.tiles[i][j].blocked = True
        
        positions = _get_valid_spawn_positions(5, 5, self.mock_game_map, 3)
        
        # Should still find some positions, just further out
        self.assertGreater(len(positions), 0)
        
        # Verify no positions are on blocked tiles
        for x, y in positions:
            self.assertFalse(self.mock_game_map.tiles[x][y].blocked)
    
    def test_get_valid_spawn_positions_no_game_map(self):
        """Test spawn position finding without a game map."""
        positions = _get_valid_spawn_positions(5, 5, None, 3)
        
        # Should fallback to center position
        self.assertEqual(positions, [(5, 5)])
    
    @patch('death_functions.random.random')
    @patch('death_functions.random.randint')
    def test_slime_splitting_success(self, mock_randint, mock_random):
        """Test successful slime splitting."""
        # Mock 40% chance (within 60% split chance)
        mock_random.return_value = 0.4
        # Mock spawning 2 slimes
        mock_randint.return_value = 2
        
        with patch('config.entity_factory.get_entity_factory') as mock_get_factory:
            mock_factory = MagicMock()
            mock_get_factory.return_value = mock_factory
            
            # Mock factory creating slimes
            mock_slime1 = MagicMock()
            mock_slime2 = MagicMock()
            mock_factory.create_monster.side_effect = [mock_slime1, mock_slime2]
            
            spawned = _handle_slime_splitting(self.large_slime, self.mock_game_map)
            
            # Should spawn 2 slimes
            self.assertEqual(len(spawned), 2)
            self.assertEqual(spawned, [mock_slime1, mock_slime2])
            
            # Should call factory to create regular slimes
            self.assertEqual(mock_factory.create_monster.call_count, 2)
            for call in mock_factory.create_monster.call_args_list:
                self.assertEqual(call[0][0], "slime")  # Should create "slime", not "large_slime"
    
    @patch('death_functions.random.random')
    def test_slime_splitting_failure_chance(self, mock_random):
        """Test slime splitting failure due to chance."""
        # Mock 70% chance (outside 60% split chance)
        mock_random.return_value = 0.7
        
        spawned = _handle_slime_splitting(self.large_slime, self.mock_game_map)
        
        # Should not spawn any slimes
        self.assertEqual(len(spawned), 0)
    
    def test_slime_splitting_non_splitter(self):
        """Test that non-splitting monsters don't split."""
        spawned = _handle_slime_splitting(self.regular_slime, self.mock_game_map)
        
        # Should not spawn any slimes
        self.assertEqual(len(spawned), 0)
    
    @patch('death_functions._handle_slime_splitting')
    def test_kill_monster_with_splitting(self, mock_splitting):
        """Test kill_monster integration with splitting."""
        # Mock splitting returning 2 slimes
        mock_slime1 = MagicMock()
        mock_slime2 = MagicMock()
        mock_splitting.return_value = [mock_slime1, mock_slime2]
        
        death_message = kill_monster(self.large_slime, self.mock_game_map, entities=None)
        
        # Should call splitting handler
        mock_splitting.assert_called_once_with(self.large_slime, self.mock_game_map, None)
        
        # Should store spawned entities on the monster
        self.assertTrue(hasattr(self.large_slime, '_spawned_entities'))
        self.assertEqual(self.large_slime._spawned_entities, [mock_slime1, mock_slime2])
        
        # Should have special splitting death message
        self.assertIn("splits into 2 smaller slimes", death_message.text)
        self.assertEqual(death_message.color, (0, 255, 0))  # Green for special event
    
    @patch('death_functions._handle_slime_splitting')
    def test_kill_monster_without_splitting(self, mock_splitting):
        """Test kill_monster when splitting doesn't occur."""
        # Mock no splitting
        mock_splitting.return_value = []
        
        death_message = kill_monster(self.large_slime, self.mock_game_map, entities=None)
        
        # Should call splitting handler
        mock_splitting.assert_called_once_with(self.large_slime, self.mock_game_map, None)
        
        # Should not store spawned entities
        self.assertFalse(hasattr(self.large_slime, '_spawned_entities'))
        
        # Should have normal death message
        self.assertIn("is dead", death_message.text)
        self.assertEqual(death_message.color, (255, 127, 0))  # Normal death color
    
    def test_kill_monster_regular_slime(self):
        """Test kill_monster with regular slime (no splitting ability)."""
        death_message = kill_monster(self.regular_slime, self.mock_game_map)
        
        # Should not have spawned entities
        self.assertFalse(hasattr(self.regular_slime, '_spawned_entities'))
        
        # Should have normal death message
        self.assertIn("is dead", death_message.text)
        self.assertEqual(death_message.color, (255, 127, 0))


class TestSlimeSplittingIntegration(unittest.TestCase):
    """Test slime splitting integration with game systems."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        os.environ['YARL_TESTING_MODE'] = '1'
        load_entity_config()
        
        self.factory = EntityFactory()
    
    def test_large_slime_has_splitting_ability(self):
        """Test that large slimes created by factory have splitting ability."""
        large_slime = self.factory.create_monster("large_slime", 5, 5)
        
        self.assertIsNotNone(large_slime)
        self.assertTrue(_can_monster_split(large_slime))
        self.assertIn('splitting', large_slime.special_abilities)
    
    def test_regular_slime_no_splitting_ability(self):
        """Test that regular slimes don't have splitting ability."""
        slime = self.factory.create_monster("slime", 5, 5)
        
        self.assertIsNotNone(slime)
        self.assertFalse(_can_monster_split(slime))
        # Regular slimes should have corrosion but not splitting
        self.assertIn('corrosion', slime.special_abilities)
        self.assertNotIn('splitting', slime.special_abilities)


if __name__ == '__main__':
    unittest.main()
