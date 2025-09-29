"""Game initialization functions and constants.

This module handles the creation of new games, setting up initial
game state, player character, and game world configuration.
"""

from tcod import libtcodpy

from components.equipment import Equipment
from components.equippable import Equippable
from components.fighter import Fighter
from components.inventory import Inventory
from components.item import Item
from components.level import Level
from config.game_constants import get_constants as get_new_constants, get_combat_config, get_inventory_config
from entity import Entity
from equipment_slots import EquipmentSlots
from game_messages import MessageLog
from game_states import GameStates
from map_objects.game_map import GameMap
from render_functions import RenderOrder


def get_constants():
    """Get game configuration constants.

    Returns:
        dict: Dictionary containing all game configuration values including
              screen dimensions, UI layout, colors, and game parameters
    """
    # Use the new centralized constants system
    constants = get_new_constants()
    
    # Add legacy-specific values that aren't in the new system yet
    constants.update({
        "window_title": "Yarl (Catacombs of Yarl)",  # Updated title
        "message_x": constants["bar_width"] + 2,
        "message_width": constants["screen_width"] - constants["bar_width"] - 2,
        "message_height": constants["panel_height"] - 1,
    })
    
    # Convert colors to libtcod format for backward compatibility
    libtcod_colors = {}
    for color_name, rgb in constants["colors"].items():
        if isinstance(rgb, tuple) and len(rgb) == 3:
            libtcod_colors[color_name] = libtcodpy.Color(rgb[0], rgb[1], rgb[2])
        else:
            libtcod_colors[color_name] = rgb  # Already in correct format
    
    constants["colors"] = libtcod_colors
    
    return constants


def get_game_variables(constants):
    """Initialize all game variables for a new game.

    Creates the player character, game world, entities, and initial game state.

    Args:
        constants (dict): Game configuration constants from get_constants()

    Returns:
        tuple: (player, entities, game_map, message_log, game_state) for new game
    """
    # Get configuration objects for cleaner code
    combat_config = get_combat_config()
    inventory_config = get_inventory_config()
    
    # Create player components using constants
    fighter_component = Fighter(
        hp=100,  # Player starts with more HP than default
        defense=combat_config.DEFAULT_DEFENSE + 1,  # Slightly better than default
        power=combat_config.DEFAULT_POWER + 1  # Slightly better than default
    )
    inventory_component = Inventory(inventory_config.DEFAULT_INVENTORY_CAPACITY)
    level_component = Level(
        level_up_base=combat_config.DEFAULT_LEVEL_UP_BASE,
        level_up_factor=combat_config.DEFAULT_LEVEL_UP_FACTOR
    )
    equipment_component = Equipment()
    equippable_component = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=2)

    # Create pathfinding component for mouse movement
    from components.player_pathfinding import PlayerPathfinding
    pathfinding_component = PlayerPathfinding()
    
    # Use the new Entity.create_player method for cleaner code
    player = Entity.create_player(
        x=0, y=0,
        fighter=fighter_component,
        inventory=inventory_component,
        level=level_component,
        equipment=equipment_component
    )
    
    # Add pathfinding component manually since create_player doesn't support it yet
    player.pathfinding = pathfinding_component
    pathfinding_component.owner = player
    entities = [player]

    # Create starting dagger using the new Entity.create_item method
    dagger_equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=2,
                                  damage_min=1, damage_max=3)
    dagger = Entity.create_item(
        x=0, y=0, char="-", color=(0, 191, 255), name="Dagger",
        item_component=Item(), equippable=dagger_equippable
    )
    player.inventory.add_item(dagger)
    player.equipment.toggle_equip(dagger)

    game_map = GameMap(constants["map_width"], constants["map_height"])
    game_map.make_map(
        constants["max_rooms"],
        constants["room_min_size"],
        constants["room_max_size"],
        constants["map_width"],
        constants["map_height"],
        player,
        entities,
    )

    message_log = MessageLog(
        constants["message_x"], constants["message_width"], constants["message_height"]
    )

    game_state = GameStates.PLAYERS_TURN

    return player, entities, game_map, message_log, game_state
