import logging
import os
import json
from datetime import datetime
from typing import Any, Dict, List, Tuple

# Import game objects for type checking and reconstruction
from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from components.equipment import Equipment
from components.ai import BasicMonster, ConfusedMonster
from components.item import Item
from components.equippable import Equippable
from components.level import Level
from map_objects.game_map import GameMap
from map_objects.tile import Tile
from game_messages import MessageLog, Message
from game_states import GameStates
from equipment_slots import EquipmentSlots


def save_game(player, entities, game_map, message_log, game_state):
    """
    Save the current game state to a JSON file.

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

        # Serialize game data to JSON-compatible format
        save_data = {
            "version": "2.0",  # JSON save format version
            "timestamp": datetime.now().isoformat(),
            "player_index": entities.index(player),
            "entities": [_serialize_entity(entity) for entity in entities],
            "game_map": _serialize_game_map(game_map),
            "message_log": _serialize_message_log(message_log),
            "game_state": game_state.name if hasattr(game_state, 'name') else str(game_state)
        }
        
        # Write to JSON file
        with open("savegame.json", "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        logging.info("Game saved successfully")

    except Exception as e:
        logging.error(f"Failed to save game: {e}")
        raise


def load_game():
    """
    Load game state from a JSON file, with fallback to legacy shelve format.

    Returns:
        tuple: (player, entities, game_map, message_log, game_state)

    Raises:
        FileNotFoundError: If save file doesn't exist
        KeyError: If save file is corrupted or missing required data
        ValueError: If loaded data is invalid
        IOError: If file cannot be read
    """
    try:
        # Try JSON format first
        if os.path.isfile("savegame.json"):
            return _load_json_save()
        # Fallback to legacy shelve format
        elif os.path.isfile("savegame.dat.db"):
            return _load_legacy_save()
        else:
            raise FileNotFoundError("No save file found (savegame.json or savegame.dat.db)")

    except Exception as e:
        logging.error(f"Failed to load game: {e}")
        raise


def _load_json_save():
    """Load game from JSON format."""
    with open("savegame.json", "r", encoding="utf-8") as f:
        save_data = json.load(f)
    
    # Validate required keys
    required_keys = ["player_index", "entities", "game_map", "message_log", "game_state"]
    missing_keys = [key for key in required_keys if key not in save_data]
    if missing_keys:
        raise KeyError(f"Save file is missing required data: {missing_keys}")
    
    # Deserialize data
    entities = [_deserialize_entity(entity_data) for entity_data in save_data["entities"]]
    game_map = _deserialize_game_map(save_data["game_map"])
    message_log = _deserialize_message_log(save_data["message_log"])
    
    # Convert game state string back to enum
    game_state_str = save_data["game_state"]
    try:
        game_state = GameStates[game_state_str] if isinstance(game_state_str, str) else game_state_str
    except KeyError:
        logging.warning(f"Unknown game state '{game_state_str}', defaulting to PLAYERS_TURN")
        game_state = GameStates.PLAYERS_TURN
    
    # Validate and get player
    player_index = save_data["player_index"]
    if entities is None or len(entities) == 0:
        raise ValueError("Loaded entities list is empty")
    if player_index < 0 or player_index >= len(entities):
        raise ValueError(f"Invalid player index: {player_index}")
    
    player = entities[player_index]
    if player is None:
        raise ValueError("Loaded player is None")
    
    logging.info("Game loaded successfully from JSON format")
    return player, entities, game_map, message_log, game_state


def _load_legacy_save():
    """Load game from legacy shelve format."""
    import shelve
    
    with shelve.open("savegame.dat", "r") as data_file:
        # Validate that all required keys exist
        required_keys = ["player_index", "entities", "game_map", "message_log", "game_state"]
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

    logging.info("Game loaded successfully from legacy shelve format")
    return player, entities, game_map, message_log, game_state


def save_file_exists():
    """
    Check if a save file exists (JSON or legacy format).

    Returns:
        bool: True if save file exists, False otherwise
    """
    return os.path.isfile("savegame.json") or os.path.isfile("savegame.dat.db")


def delete_save_file():
    """
    Delete the save file if it exists (JSON or legacy format).

    Returns:
        bool: True if file was deleted, False if file didn't exist

    Raises:
        OSError: If file exists but cannot be deleted
    """
    try:
        deleted = False
        if os.path.isfile("savegame.json"):
            os.remove("savegame.json")
            deleted = True
        if os.path.isfile("savegame.dat.db"):
            os.remove("savegame.dat.db")
            deleted = True
        
        if deleted:
            logging.info("Save file(s) deleted successfully")
        return deleted
    except Exception as e:
        logging.error(f"Failed to delete save file: {e}")
        raise


# ============================================================================
# JSON Serialization Functions
# ============================================================================

def _serialize_entity(entity: Entity) -> Dict[str, Any]:
    """Serialize an entity to JSON-compatible format."""
    data = {
        "x": entity.x,
        "y": entity.y,
        "char": entity.char,
        "color": list(entity.color),  # Convert tuple to list for JSON
        "name": entity.name,
        "blocks": entity.blocks,
        "render_order": entity.render_order.name if hasattr(entity.render_order, 'name') else str(entity.render_order)
    }
    
    # Serialize components
    if entity.fighter:
        data["fighter"] = _serialize_fighter(entity.fighter)
    if entity.ai:
        data["ai"] = _serialize_ai(entity.ai)
    if entity.item:
        data["item"] = _serialize_item(entity.item)
    if entity.inventory:
        data["inventory"] = _serialize_inventory(entity.inventory)
    if entity.stairs:
        data["stairs"] = {"floor": entity.stairs.floor}
    if entity.level:
        data["level"] = _serialize_level(entity.level)
    if entity.equipment:
        data["equipment"] = _serialize_equipment(entity.equipment)
    
    return data


def _serialize_fighter(fighter: Fighter) -> Dict[str, Any]:
    """Serialize a Fighter component."""
    return {
        "base_max_hp": fighter.base_max_hp,
        "hp": fighter.hp,
        "base_defense": fighter.base_defense,
        "base_power": fighter.base_power,
        "xp": fighter.xp
    }


def _serialize_ai(ai) -> Dict[str, Any]:
    """Serialize an AI component."""
    if isinstance(ai, BasicMonster):
        return {"type": "BasicMonster"}
    elif isinstance(ai, ConfusedMonster):
        return {
            "type": "ConfusedMonster",
            "previous_ai": _serialize_ai(ai.previous_ai) if ai.previous_ai else None,
            "number_of_turns": ai.number_of_turns
        }
    else:
        return {"type": "Unknown", "class": ai.__class__.__name__}


def _serialize_item(item: Item) -> Dict[str, Any]:
    """Serialize an Item component."""
    return {
        "use_function": item.use_function.__name__ if item.use_function else None,
        "targeting": item.targeting,
        "targeting_message": item.targeting_message,
        "function_kwargs": item.function_kwargs or {}
    }


def _serialize_inventory(inventory: Inventory) -> Dict[str, Any]:
    """Serialize an Inventory component."""
    return {
        "capacity": inventory.capacity,
        "items": [_serialize_entity(item) for item in inventory.items]
    }


def _serialize_level(level: Level) -> Dict[str, Any]:
    """Serialize a Level component."""
    return {
        "current_level": level.current_level,
        "current_xp": level.current_xp,
        "level_up_base": level.level_up_base,
        "level_up_factor": level.level_up_factor
    }


def _serialize_equipment(equipment: Equipment) -> Dict[str, Any]:
    """Serialize an Equipment component."""
    return {
        "main_hand": _serialize_entity(equipment.main_hand) if equipment.main_hand else None,
        "off_hand": _serialize_entity(equipment.off_hand) if equipment.off_hand else None
    }


def _serialize_game_map(game_map: GameMap) -> Dict[str, Any]:
    """Serialize a GameMap."""
    return {
        "width": game_map.width,
        "height": game_map.height,
        "dungeon_level": game_map.dungeon_level,
        "tiles": [[_serialize_tile(game_map.tiles[x][y]) for y in range(game_map.height)] 
                  for x in range(game_map.width)]
    }


def _serialize_tile(tile: Tile) -> Dict[str, Any]:
    """Serialize a Tile."""
    return {
        "blocked": tile.blocked,
        "block_sight": tile.block_sight,
        "explored": tile.explored
    }


def _serialize_message_log(message_log: MessageLog) -> Dict[str, Any]:
    """Serialize a MessageLog."""
    return {
        "messages": [{"text": msg.text, "color": list(msg.color)} for msg in message_log.messages],
        "x": message_log.x,
        "width": message_log.width,
        "height": message_log.height
    }


# ============================================================================
# JSON Deserialization Functions
# ============================================================================

def _deserialize_entity(data: Dict[str, Any]) -> Entity:
    """Deserialize an entity from JSON data."""
    from render_functions import RenderOrder
    
    # Create base entity
    entity = Entity(
        x=data["x"],
        y=data["y"],
        char=data["char"],
        color=tuple(data["color"]),  # Convert list back to tuple
        name=data["name"],
        blocks=data["blocks"]
    )
    
    # Set render order
    render_order_str = data.get("render_order", "CORPSE")
    try:
        entity.render_order = RenderOrder[render_order_str] if isinstance(render_order_str, str) else render_order_str
    except KeyError:
        entity.render_order = RenderOrder.CORPSE
    
    # Deserialize components
    if "fighter" in data:
        entity.fighter = _deserialize_fighter(data["fighter"])
    if "ai" in data:
        entity.ai = _deserialize_ai(data["ai"])
    if "item" in data:
        entity.item = _deserialize_item(data["item"])
    if "inventory" in data:
        entity.inventory = _deserialize_inventory(data["inventory"])
    if "stairs" in data:
        from stairs import Stairs
        entity.stairs = Stairs(data["stairs"]["floor"])
    if "level" in data:
        entity.level = _deserialize_level(data["level"])
    if "equipment" in data:
        entity.equipment = _deserialize_equipment(data["equipment"])
    
    return entity


def _deserialize_fighter(data: Dict[str, Any]) -> Fighter:
    """Deserialize a Fighter component."""
    fighter = Fighter(
        hp=data["base_max_hp"],  # Constructor expects max HP
        defense=data["base_defense"],
        power=data["base_power"],
        xp=data.get("xp", 0)
    )
    # Set current HP separately
    fighter.hp = data["hp"]
    return fighter


def _deserialize_ai(data: Dict[str, Any]):
    """Deserialize an AI component."""
    ai_type = data["type"]
    if ai_type == "BasicMonster":
        return BasicMonster()
    elif ai_type == "ConfusedMonster":
        previous_ai = _deserialize_ai(data["previous_ai"]) if data["previous_ai"] else None
        confused = ConfusedMonster(previous_ai, data["number_of_turns"])
        return confused
    else:
        # Fallback to BasicMonster for unknown AI types
        logging.warning(f"Unknown AI type '{ai_type}', using BasicMonster")
        return BasicMonster()


def _deserialize_item(data: Dict[str, Any]) -> Item:
    """Deserialize an Item component."""
    # Import item functions dynamically
    use_function = None
    if data["use_function"]:
        try:
            import item_functions
            use_function = getattr(item_functions, data["use_function"])
        except AttributeError:
            logging.warning(f"Unknown item function '{data['use_function']}'")
    
    return Item(
        use_function=use_function,
        targeting=data.get("targeting", False),
        targeting_message=data.get("targeting_message"),
        **data.get("function_kwargs", {})
    )


def _deserialize_inventory(data: Dict[str, Any]) -> Inventory:
    """Deserialize an Inventory component."""
    inventory = Inventory(capacity=data["capacity"])
    for item_data in data["items"]:
        item = _deserialize_entity(item_data)
        inventory.items.append(item)
    return inventory


def _deserialize_level(data: Dict[str, Any]) -> Level:
    """Deserialize a Level component."""
    return Level(
        current_level=data["current_level"],
        current_xp=data["current_xp"],
        level_up_base=data["level_up_base"],
        level_up_factor=data["level_up_factor"]
    )


def _deserialize_equipment(data: Dict[str, Any]) -> Equipment:
    """Deserialize an Equipment component."""
    equipment = Equipment()
    if data["main_hand"]:
        equipment.main_hand = _deserialize_entity(data["main_hand"])
    if data["off_hand"]:
        equipment.off_hand = _deserialize_entity(data["off_hand"])
    return equipment


def _deserialize_game_map(data: Dict[str, Any]) -> GameMap:
    """Deserialize a GameMap."""
    game_map = GameMap(
        width=data["width"],
        height=data["height"],
        dungeon_level=data["dungeon_level"]
    )
    
    # Deserialize tiles
    for x in range(game_map.width):
        for y in range(game_map.height):
            tile_data = data["tiles"][x][y]
            game_map.tiles[x][y] = _deserialize_tile(tile_data)
    
    return game_map


def _deserialize_tile(data: Dict[str, Any]) -> Tile:
    """Deserialize a Tile."""
    tile = Tile(blocked=data["blocked"], block_sight=data.get("block_sight", data["blocked"]))
    tile.explored = data.get("explored", False)
    return tile


def _deserialize_message_log(data: Dict[str, Any]) -> MessageLog:
    """Deserialize a MessageLog."""
    message_log = MessageLog(x=data["x"], width=data["width"], height=data["height"])
    for msg_data in data["messages"]:
        message = Message(msg_data["text"], tuple(msg_data["color"]))
        message_log.messages.append(message)
    return message_log
