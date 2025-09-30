#!/usr/bin/env python3
"""
Regression tests for save game functionality.

This test ensures that the save game bug where subsequent saves weren't working
properly is fixed and doesn't reoccur.
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from components.fighter import Fighter
from components.inventory import Inventory
from entity import Entity
from game_messages import MessageLog
from game_states import GameStates
from loader_functions.data_loaders import save_game, load_game
from map_objects.game_map import GameMap


class TestSaveGameRegression(unittest.TestCase):
    """Test save game functionality to prevent regression."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test saves
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create test entities
        self.player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=2, power=5),
            inventory=Inventory(capacity=26)
        )
        
        self.monster = Entity(
            x=15, y=10, char='o', color=(63, 127, 63), name='Orc',
            fighter=Fighter(hp=10, defense=0, power=3), blocks=True
        )
        
        self.entities = [self.player, self.monster]
        
        # Create real objects instead of mocks for pickling
        from map_objects.tile import Tile
        self.game_map = GameMap(width=80, height=50, dungeon_level=1)
        # Initialize the map with basic tiles
        for x in range(self.game_map.width):
            for y in range(self.game_map.height):
                self.game_map.tiles[x][y] = Tile(blocked=False, block_sight=False)
        
        self.message_log = MessageLog(x=0, width=80, height=5)
        self.game_state = GameStates.PLAYERS_TURN

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        # Clean up any save files (both JSON and legacy formats)
        for file in os.listdir(self.test_dir):
            if file.startswith('savegame.'):
                os.remove(os.path.join(self.test_dir, file))
        os.rmdir(self.test_dir)

    def test_multiple_saves_work_regression(self):
        """Regression test: Multiple saves should work, not just the first one.
        
        Bug: The save_game function used shelve.open with 'n' flag, which created
        a new file each time, causing issues with subsequent saves.
        Fix: Changed to 'c' flag which creates if needed, otherwise opens existing.
        """
        # First save
        save_game(self.player, self.entities, self.game_map, self.message_log, self.game_state)
        
        # Verify save file exists (now JSON format)
        self.assertTrue(os.path.exists('savegame.json'), "Save file should exist after first save")
        
        # Load and verify
        loaded_player, loaded_entities, loaded_map, loaded_log, loaded_state = load_game()
        self.assertEqual(loaded_player.name, 'Player')
        self.assertEqual(len(loaded_entities), 2)
        self.assertEqual(loaded_state, GameStates.PLAYERS_TURN)
        
        # Modify game state
        self.player.fighter.hp = 20  # Take damage
        self.player.x = 12  # Move player
        
        # Second save (this is where the bug occurred)
        save_game(self.player, self.entities, self.game_map, self.message_log, self.game_state)
        
        # Load again and verify changes were saved
        loaded_player2, loaded_entities2, loaded_map2, loaded_log2, loaded_state2 = load_game()
        self.assertEqual(loaded_player2.fighter.hp, 20, "Player HP change should be saved")
        self.assertEqual(loaded_player2.x, 12, "Player position change should be saved")
        self.assertEqual(len(loaded_entities2), 2, "Entities should still be saved")
        
        # Third save to be extra sure
        self.player.fighter.hp = 15  # More damage
        self.monster.fighter.hp = 5   # Damage monster too
        
        save_game(self.player, self.entities, self.game_map, self.message_log, self.game_state)
        
        # Final load and verify
        loaded_player3, loaded_entities3, loaded_map3, loaded_log3, loaded_state3 = load_game()
        self.assertEqual(loaded_player3.fighter.hp, 15, "Third save should work")
        self.assertEqual(loaded_entities3[1].fighter.hp, 5, "Monster damage should be saved")

    def test_save_overwrites_correctly_regression(self):
        """Regression test: Saves should overwrite previous saves, not append."""
        # Initial save
        original_hp = self.player.fighter.hp
        save_game(self.player, self.entities, self.game_map, self.message_log, self.game_state)
        
        # Modify and save again
        self.player.fighter.hp = original_hp - 10
        save_game(self.player, self.entities, self.game_map, self.message_log, self.game_state)
        
        # Load should get the latest save, not the original
        loaded_player, _, _, _, _ = load_game()
        self.assertEqual(loaded_player.fighter.hp, original_hp - 10, 
                        "Save should overwrite, not revert to first save")
        self.assertNotEqual(loaded_player.fighter.hp, original_hp,
                           "Should not load original save data")

    def test_save_file_flag_creates_or_updates_regression(self):
        """Regression test: Verify shelve flag 'c' behavior works correctly."""
        # First save - should create file
        save_game(self.player, self.entities, self.game_map, self.message_log, self.game_state)
        self.assertTrue(os.path.exists('savegame.json'), "First save should create file")
        
        # Get file modification time
        first_mtime = os.path.getmtime('savegame.json')
        
        # Wait a bit and save again
        import time
        time.sleep(0.1)
        
        # Modify data and save
        self.player.fighter.hp = 25
        save_game(self.player, self.entities, self.game_map, self.message_log, self.game_state)
        
        # File should be updated, not recreated
        second_mtime = os.path.getmtime('savegame.json')
        self.assertGreater(second_mtime, first_mtime, "Save file should be updated, not recreated")
        
        # Verify the update worked
        loaded_player, _, _, _, _ = load_game()
        self.assertEqual(loaded_player.fighter.hp, 25, "Updated data should be saved")


if __name__ == "__main__":
    unittest.main()
