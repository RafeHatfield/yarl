import logging
import os
import shelve


def save_game(player, entities, game_map, message_log, game_state):
    """
    Save the current game state to a shelve database file.

    Args:
        player: The player entity
        entities: List of all entities in the game
        game_map: The current game map
        message_log: The message log
        game_state: Current game state

    Raises:
        ValueError: If required data is missing or invalid
        IOError: If file cannot be written
    """
    try:
        # Validate required parameters
        if player is None:
            raise ValueError("Player cannot be None")
        if entities is None or len(entities) == 0:
            raise ValueError("Entities list cannot be empty")
        if player not in entities:
            raise ValueError("Player must be in entities list")
        if game_map is None:
            raise ValueError("Game map cannot be None")
        if message_log is None:
            raise ValueError("Message log cannot be None")
        if game_state is None:
            raise ValueError("Game state cannot be None")

        with shelve.open("savegame.dat", "n") as data_file:
            data_file["player_index"] = entities.index(player)
            data_file["entities"] = entities
            data_file["game_map"] = game_map
            data_file["message_log"] = message_log
            data_file["game_state"] = game_state

        logging.info("Game saved successfully")

    except Exception as e:
        logging.error(f"Failed to save game: {e}")
        raise


def load_game():
    """
    Load game state from a shelve database file.

    Returns:
        tuple: (player, entities, game_map, message_log, game_state)

    Raises:
        FileNotFoundError: If save file doesn't exist
        KeyError: If save file is corrupted or missing required data
        ValueError: If loaded data is invalid
        IOError: If file cannot be read
    """
    try:
        if not os.path.isfile("savegame.dat.db"):
            raise FileNotFoundError("Save file 'savegame.dat.db' not found")

        with shelve.open("savegame.dat", "r") as data_file:
            # Validate that all required keys exist
            required_keys = [
                "player_index",
                "entities",
                "game_map",
                "message_log",
                "game_state",
            ]
            missing_keys = [key for key in required_keys if key not in data_file]
            if missing_keys:
                raise KeyError(f"Save file is missing required data: {missing_keys}")

            player_index = data_file["player_index"]
            entities = data_file["entities"]
            game_map = data_file["game_map"]
            message_log = data_file["message_log"]
            game_state = data_file["game_state"]

        # Validate loaded data
        if entities is None or len(entities) == 0:
            raise ValueError("Loaded entities list is empty")
        if player_index < 0 or player_index >= len(entities):
            raise ValueError(f"Invalid player index: {player_index}")

        player = entities[player_index]

        if player is None:
            raise ValueError("Loaded player is None")

        logging.info("Game loaded successfully")
        return player, entities, game_map, message_log, game_state

    except Exception as e:
        logging.error(f"Failed to load game: {e}")
        raise


def save_file_exists():
    """
    Check if a save file exists.

    Returns:
        bool: True if save file exists, False otherwise
    """
    return os.path.isfile("savegame.dat.db")


def delete_save_file():
    """
    Delete the save file if it exists.

    Returns:
        bool: True if file was deleted, False if file didn't exist

    Raises:
        OSError: If file exists but cannot be deleted
    """
    try:
        if save_file_exists():
            os.remove("savegame.dat.db")
            logging.info("Save file deleted successfully")
            return True
        return False
    except Exception as e:
        logging.error(f"Failed to delete save file: {e}")
        raise
