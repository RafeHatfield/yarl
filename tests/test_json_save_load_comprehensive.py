"""
Comprehensive tests for JSON save/load system.

Tests edge cases, serialization/deserialization, and legacy compatibility.
"""

import json
import os
import pytest
import tempfile
import shutil
from unittest.mock import patch, mock_open

from loader_functions.data_loaders import (
    save_game, load_game, save_file_exists, delete_save_file,
    _serialize_entity, _deserialize_entity,
    _serialize_game_map, _deserialize_game_map,
    _serialize_message_log, _deserialize_message_log,
    _load_json_save, _load_legacy_save
)
from loader_functions.initialize_new_game import get_game_variables, get_constants
from game_states import GameStates
from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from components.ai import BasicMonster, ConfusedMonster
from components.item import Item
from components.level import Level
from components.equipment import Equipment
from map_objects.game_map import GameMap
from map_objects.tile import Tile
from game_messages import MessageLog, Message


class TestJSONSaveLoadComprehensive:
    """Comprehensive tests for JSON save/load system."""

    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_json_save_format_structure(self):
        """Test that JSON save has correct structure and metadata."""
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Save game
        save_game(player, entities, game_map, message_log, game_state)
        
        # Load and verify JSON structure
        with open("savegame.json", "r") as f:
            save_data = json.load(f)
        
        # Check required fields
        assert "version" in save_data
        assert "timestamp" in save_data
        assert "player_index" in save_data
        assert "entities" in save_data
        assert "game_map" in save_data
        assert "message_log" in save_data
        assert "game_state" in save_data
        
        # Check version format
        assert save_data["version"] == "2.0"
        
        # Check timestamp format (ISO format)
        from datetime import datetime
        datetime.fromisoformat(save_data["timestamp"])  # Should not raise
        
        # Check entities structure
        assert isinstance(save_data["entities"], list)
        assert len(save_data["entities"]) > 0
        
        # Check game map structure
        game_map_data = save_data["game_map"]
        assert "width" in game_map_data
        assert "height" in game_map_data
        assert "dungeon_level" in game_map_data
        assert "tiles" in game_map_data

    def test_entity_serialization_deserialization(self):
        """Test entity serialization and deserialization."""
        # Create test entity with various components
        entity = Entity(
            x=10, y=15, char='@', color=(255, 255, 255), name='Test Player',
            fighter=Fighter(hp=100, defense=5, power=10, xp=50),
            inventory=Inventory(capacity=26),
            ai=BasicMonster(),
            level=Level(current_level=5, current_xp=1000)
        )
        
        # Add equipment
        entity.equipment = Equipment()
        
        # Serialize
        serialized = _serialize_entity(entity)
        
        # Check serialized structure
        assert serialized["x"] == 10
        assert serialized["y"] == 15
        assert serialized["char"] == '@'
        assert serialized["color"] == [255, 255, 255]  # Tuple -> List
        assert serialized["name"] == 'Test Player'
        assert "fighter" in serialized
        assert "inventory" in serialized
        assert "ai" in serialized
        assert "level" in serialized
        assert "equipment" in serialized
        
        # Deserialize
        deserialized = _deserialize_entity(serialized)
        
        # Check deserialized entity
        assert deserialized.x == entity.x
        assert deserialized.y == entity.y
        assert deserialized.char == entity.char
        assert deserialized.color == entity.color
        assert deserialized.name == entity.name
        assert deserialized.fighter is not None
        assert deserialized.inventory is not None
        assert deserialized.ai is not None
        assert deserialized.level is not None
        assert deserialized.equipment is not None

    def test_confused_monster_ai_serialization(self):
        """Test serialization of confused monster AI."""
        # Create confused monster
        basic_ai = BasicMonster()
        confused_ai = ConfusedMonster(basic_ai, 5)
        
        entity = Entity(
            x=5, y=5, char='o', color=(127, 127, 127), name='Confused Orc',
            ai=confused_ai
        )
        
        # Serialize and deserialize
        serialized = _serialize_entity(entity)
        deserialized = _deserialize_entity(serialized)
        
        # Check AI was preserved
        assert isinstance(deserialized.ai, ConfusedMonster)
        assert deserialized.ai.number_of_turns == 5
        assert isinstance(deserialized.ai.previous_ai, BasicMonster)

    def test_item_with_function_serialization(self):
        """Test serialization of items with use functions."""
        from item_functions import heal
        
        # Create item with function
        item_entity = Entity(
            x=0, y=0, char='!', color=(255, 0, 255), name='Healing Potion',
            item=Item(use_function=heal, amount=40)
        )
        
        # Serialize and deserialize
        serialized = _serialize_entity(item_entity)
        deserialized = _deserialize_entity(serialized)
        
        # Check item function was preserved
        assert deserialized.item is not None
        assert deserialized.item.use_function is not None
        assert deserialized.item.use_function.__name__ == 'heal'

    def test_game_map_serialization(self):
        """Test game map serialization and deserialization."""
        # Create test game map
        game_map = GameMap(width=10, height=8, dungeon_level=3)
        
        # Set some tiles as explored
        game_map.tiles[0][0].explored = True
        game_map.tiles[1][1].explored = True
        
        # Serialize and deserialize
        serialized = _serialize_game_map(game_map)
        deserialized = _deserialize_game_map(serialized)
        
        # Check map properties
        assert deserialized.width == game_map.width
        assert deserialized.height == game_map.height
        assert deserialized.dungeon_level == game_map.dungeon_level
        
        # Check tile properties
        assert deserialized.tiles[0][0].explored == True
        assert deserialized.tiles[1][1].explored == True
        assert deserialized.tiles[2][2].explored == False

    def test_message_log_serialization(self):
        """Test message log serialization and deserialization."""
        # Create message log with messages
        message_log = MessageLog(x=0, width=80, height=5)
        message_log.add_message(Message("Test message 1", (255, 255, 255)))
        message_log.add_message(Message("Test message 2", (255, 0, 0)))
        
        # Serialize and deserialize
        serialized = _serialize_message_log(message_log)
        deserialized = _deserialize_message_log(serialized)
        
        # Check message log properties
        assert deserialized.x == message_log.x
        assert deserialized.width == message_log.width
        assert deserialized.height == message_log.height
        assert len(deserialized.messages) == 2
        assert deserialized.messages[0].text == "Test message 1"
        assert deserialized.messages[1].text == "Test message 2"
        assert deserialized.messages[0].color == (255, 255, 255)
        assert deserialized.messages[1].color == (255, 0, 0)

    def test_legacy_save_compatibility(self):
        """Test that legacy shelve saves can still be loaded."""
        import shelve
        
        # Create a legacy save file
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Create legacy shelve save
        with shelve.open("savegame.dat", "c") as data_file:
            data_file["player_index"] = entities.index(player)
            data_file["entities"] = entities
            data_file["game_map"] = game_map
            data_file["message_log"] = message_log
            data_file["game_state"] = game_state
        
        # Should be able to load legacy save
        loaded_player, loaded_entities, loaded_map, loaded_log, loaded_state = load_game()
        
        # Verify data integrity
        assert loaded_player.name == player.name
        assert len(loaded_entities) == len(entities)
        assert loaded_map.width == game_map.width
        assert loaded_state == game_state

    def test_save_file_priority(self):
        """Test that JSON saves take priority over legacy saves."""
        import shelve
        
        # Create both JSON and legacy saves
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Create legacy save with different player name
        player.name = "Legacy Player"
        with shelve.open("savegame.dat", "c") as data_file:
            data_file["player_index"] = entities.index(player)
            data_file["entities"] = entities
            data_file["game_map"] = game_map
            data_file["message_log"] = message_log
            data_file["game_state"] = game_state
        
        # Create JSON save with different player name
        player.name = "JSON Player"
        save_game(player, entities, game_map, message_log, game_state)
        
        # Load should prefer JSON
        loaded_player, _, _, _, _ = load_game()
        assert loaded_player.name == "JSON Player"

    def test_unknown_game_state_handling(self):
        """Test handling of unknown game states in JSON."""
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Save game normally
        save_game(player, entities, game_map, message_log, game_state)
        
        # Modify JSON to have unknown game state
        with open("savegame.json", "r") as f:
            save_data = json.load(f)
        
        save_data["game_state"] = "UNKNOWN_STATE"
        
        with open("savegame.json", "w") as f:
            json.dump(save_data, f)
        
        # Should load with default state
        _, _, _, _, loaded_state = load_game()
        assert loaded_state == GameStates.PLAYERS_TURN

    def test_file_cleanup_functions(self):
        """Test save file cleanup and detection functions."""
        # Initially no saves
        assert save_file_exists() == False
        assert delete_save_file() == False
        
        # Create JSON save
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        save_game(player, entities, game_map, message_log, game_state)
        
        assert save_file_exists() == True
        assert os.path.exists("savegame.json")
        
        # Delete should work
        assert delete_save_file() == True
        assert save_file_exists() == False
        assert not os.path.exists("savegame.json")
        
        # Create legacy save
        import shelve
        with shelve.open("savegame.dat", "c") as data_file:
            data_file["test"] = "data"
        
        assert save_file_exists() == True
        assert os.path.exists("savegame.dat.db")
        
        # Delete should work for legacy too
        assert delete_save_file() == True
        assert save_file_exists() == False
        assert not os.path.exists("savegame.dat.db")

    def test_json_save_error_handling(self):
        """Test error handling in JSON save operations."""
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Test with permission error (mock)
        with patch("builtins.open", mock_open()) as mock_file:
            mock_file.side_effect = PermissionError("Permission denied")
            
            with pytest.raises(PermissionError):
                save_game(player, entities, game_map, message_log, game_state)

    def test_json_load_error_handling(self):
        """Test error handling in JSON load operations."""
        # Test with invalid JSON
        with open("savegame.json", "w") as f:
            f.write("invalid json content")
        
        with pytest.raises(json.JSONDecodeError):
            _load_json_save()
        
        # Test with permission error (mock)
        with patch("builtins.open", mock_open()) as mock_file:
            mock_file.side_effect = PermissionError("Permission denied")
            
            with pytest.raises(PermissionError):
                _load_json_save()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
