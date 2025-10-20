"""
Simple, focused tests for save/load functionality.

Tests core save/load mechanics with minimal setup.
Focuses on behavior, not implementation details.
"""

import os
import pytest

from loader_functions.data_loaders import save_game, load_game
from loader_functions.initialize_new_game import get_game_variables, get_constants
from game_states import GameStates


class TestSaveLoadCore:
    """Test core save/load functionality with real game objects."""

    def teardown_method(self):
        """Clean up save files after tests."""
        for filename in ["savegame.json", "savegame.dat", "savegame.dat.db"]:
            if os.path.exists(filename):
                os.remove(filename)

    def test_save_load_preserves_player_stats(self):
        """Test that save/load preserves critical player data."""
        # Create real game with actual initialization
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Remember player's critical stats
        original_hp = player.fighter.hp
        original_max_hp = player.fighter.max_hp
        original_level = player.level.current_level
        original_name = player.name
        original_x = player.x
        original_y = player.y
        
        # Save and load using real files (will be cleaned up)
        save_game(player, entities, game_map, message_log, game_state)
        loaded_player, loaded_entities, loaded_map, loaded_log, loaded_state = load_game()
        
        # Verify critical player data preserved
        assert loaded_player.name == original_name
        assert loaded_player.fighter.hp == original_hp
        assert loaded_player.fighter.max_hp == original_max_hp
        assert loaded_player.level.current_level == original_level
        assert loaded_player.x == original_x
        assert loaded_player.y == original_y

    def test_load_game_file_not_found(self):
        """Test load_game raises error when no save file exists."""
        # Ensure no save files exist
        for filename in ["savegame.json", "savegame.dat", "savegame.dat.db"]:
            if os.path.exists(filename):
                os.remove(filename)
        
        with pytest.raises(FileNotFoundError, match="No save file found"):
            load_game()

    def test_save_validates_player_required(self):
        """Test save_game validates required player."""
        constants = get_constants()
        _, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        with pytest.raises(ValueError, match="Player cannot be None"):
            save_game(None, entities, game_map, message_log, game_state)

    def test_save_validates_entities_not_empty(self):
        """Test save_game validates entities list."""
        constants = get_constants()
        player, _, game_map, message_log, game_state = get_game_variables(constants)
        
        with pytest.raises(ValueError, match="Entities list cannot be empty"):
            save_game(player, [], game_map, message_log, game_state)


class TestSaveLoadIntegrity:
    """Test data integrity across save/load."""
    
    def teardown_method(self):
        """Clean up save files after tests."""
        for filename in ["savegame.json", "savegame.dat", "savegame.dat.db"]:
            if os.path.exists(filename):
                os.remove(filename)

    def test_save_load_preserves_inventory(self):
        """Test that inventory contents survive save/load."""
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Count starting inventory
        original_item_count = len(player.inventory.items)
        
        # Save and load using real files (will be cleaned up)
        save_game(player, entities, game_map, message_log, game_state)
        loaded_player, _, _, _, _ = load_game()
        
        # Verify inventory preserved
        assert len(loaded_player.inventory.items) == original_item_count

    def test_save_load_preserves_game_state(self):
        """Test that game state is preserved."""
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Game should start in PLAYERS_TURN
        assert game_state == GameStates.PLAYERS_TURN
        
        # Save and load using real files (will be cleaned up)
        save_game(player, entities, game_map, message_log, game_state)
        _, _, _, _, loaded_state = load_game()
        
        # Verify state preserved
        assert loaded_state == GameStates.PLAYERS_TURN

