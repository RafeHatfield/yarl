"""
Basic tests for save/load functionality.

Tests the core save/load mechanics without complex mocking.
"""

import os
import pytest
import tempfile
import shutil

from loader_functions.data_loaders import (
    save_game, load_game, save_file_exists, delete_save_file
)
from loader_functions.initialize_new_game import get_game_variables, get_constants
from game_states import GameStates


class TestBasicSaveLoad:
    """Test basic save/load functionality with real game objects."""

    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_save_file_exists_functions(self):
        """Test save_file_exists and delete_save_file functions."""
        # Initially no save file
        assert save_file_exists() is False
        assert delete_save_file() is False  # Returns False when no file to delete
        
        # Create a dummy save file
        with open('savegame.dat.db', 'w') as f:
            f.write("dummy")
        
        # Now file should exist
        assert save_file_exists() is True
        
        # Delete it
        result = delete_save_file()
        assert result is True
        assert save_file_exists() is False

    def test_load_game_file_not_found(self):
        """Test load_game when save file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Save file 'savegame.dat.db' not found"):
            load_game()

    def test_save_load_roundtrip_with_real_game_objects(self):
        """Test save/load with real game objects from initialize_new_game."""
        # Create real game objects
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        game_state = GameStates.PLAYERS_TURN
        
        # Test initial state
        original_player_hp = player.fighter.hp
        original_entities_count = len(entities)
        original_map_width = game_map.width
        
        # Save the game
        save_game(player, entities, game_map, message_log, game_state)
        
        # Verify save file was created
        assert save_file_exists() is True
        assert os.path.isfile('savegame.dat.db')
        
        # Load the game
        loaded_player, loaded_entities, loaded_game_map, loaded_message_log, loaded_game_state = load_game()
        
        # Verify data integrity
        assert loaded_player.name == player.name
        assert loaded_player.fighter.hp == original_player_hp
        assert len(loaded_entities) == original_entities_count
        assert loaded_game_map.width == original_map_width
        assert loaded_game_state == GameStates.PLAYERS_TURN

    def test_save_game_validation_errors(self):
        """Test save_game parameter validation."""
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Test with None player
        with pytest.raises(ValueError, match="Player cannot be None"):
            save_game(None, entities, game_map, message_log, game_state)
        
        # Test with empty entities
        with pytest.raises(ValueError, match="Entities list cannot be empty"):
            save_game(player, [], game_map, message_log, game_state)
        
        # Test with player not in entities
        with pytest.raises(ValueError, match="Player must be in entities list"):
            save_game(player, [entities[1]], game_map, message_log, game_state)  # Player not in list

    def test_save_game_overwrites_existing(self):
        """Test that save_game overwrites existing save files."""
        # Create initial game state
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Save first time
        save_game(player, entities, game_map, message_log, game_state)
        first_size = os.path.getsize('savegame.dat.db')
        
        # Modify player health
        original_hp = player.fighter.hp
        player.fighter.hp = 1
        
        # Save again
        save_game(player, entities, game_map, message_log, game_state)
        
        # Load and verify the change was saved
        loaded_player, _, _, _, _ = load_game()
        assert loaded_player.fighter.hp == 1
        assert loaded_player.fighter.hp != original_hp


class TestSaveLoadErrorHandling:
    """Test error handling in save/load operations."""

    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_load_game_corrupted_file(self):
        """Test load_game with corrupted save file."""
        # Create a corrupted save file
        with open('savegame.dat.db', 'wb') as f:
            f.write(b'corrupted data that is not a valid shelve file')
        
        with pytest.raises(Exception):  # Could be various types of errors
            load_game()

    def test_load_game_missing_required_keys(self):
        """Test load_game with save file missing required keys."""
        import shelve
        
        # Create save file with missing keys
        with shelve.open('savegame.dat', 'n') as data_file:
            data_file['player_index'] = 0
            # Missing other required keys like 'entities', 'game_map', etc.
        
        with pytest.raises(KeyError, match="Save file is missing required data"):
            load_game()

    def test_load_game_invalid_player_index(self):
        """Test load_game with invalid player index."""
        import shelve
        
        # Create minimal valid game state
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Create save with invalid player index
        with shelve.open('savegame.dat', 'n') as data_file:
            data_file['player_index'] = 999  # Invalid index
            data_file['entities'] = entities
            data_file['game_map'] = game_map
            data_file['message_log'] = message_log
            data_file['game_state'] = game_state
        
        with pytest.raises(ValueError, match="Invalid player index"):
            load_game()


if __name__ == "__main__":
    # Quick test if running directly
    print("Running basic save/load tests...")
    pytest.main([__file__, "-v"])
