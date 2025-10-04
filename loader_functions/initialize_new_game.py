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
from components.statistics import Statistics
from config.game_constants import get_constants as get_new_constants, get_combat_config, get_inventory_config
from config.entity_registry import load_entity_config
from config.entity_factory import get_entity_factory
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
    
    # Override map size for testing mode (larger map to demonstrate camera scrolling)
    from config.testing_config import get_testing_map_size
    map_width, map_height = get_testing_map_size()
    constants["map_width"] = map_width
    constants["map_height"] = map_height
    
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
    # Load entity configuration from YAML files
    load_entity_config()
    
    # Get configuration objects for cleaner code
    combat_config = get_combat_config()
    inventory_config = get_inventory_config()
    
    # Get player stats from configuration
    entity_factory = get_entity_factory()
    player_stats = entity_factory.get_player_stats()
    
    # Create player components using configuration
    fighter_component = Fighter(
        hp=player_stats.hp,
        defense=player_stats.defense,
        power=player_stats.power,
        damage_min=getattr(player_stats, 'damage_min', 0),
        damage_max=getattr(player_stats, 'damage_max', 0),
        strength=getattr(player_stats, 'strength', 14),
        dexterity=getattr(player_stats, 'dexterity', 12),
        constitution=getattr(player_stats, 'constitution', 14)
    )
    inventory_component = Inventory(inventory_config.DEFAULT_INVENTORY_CAPACITY)
    level_component = Level(
        level_up_base=combat_config.DEFAULT_LEVEL_UP_BASE,
        level_up_factor=combat_config.DEFAULT_LEVEL_UP_FACTOR
    )
    equipment_component = Equipment()
    statistics_component = Statistics()

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
    
    # Add pathfinding and statistics components manually
    player.pathfinding = pathfinding_component
    pathfinding_component.owner = player
    player.statistics = statistics_component
    statistics_component.owner = player
    entities = [player]

    # Create starting equipment using EntityFactory
    dagger = entity_factory.create_weapon("dagger", 0, 0)
    player.inventory.add_item(dagger)
    player.equipment.toggle_equip(dagger)
    
    # Add starting leather armor for better survivability
    leather_armor = entity_factory.create_armor("leather_armor", 0, 0)
    player.inventory.add_item(leather_armor)
    player.equipment.toggle_equip(leather_armor)
    
    # Add starting healing potion for early game survivability (Option 6 balance)
    starting_potion = entity_factory.create_spell_item("healing_potion", 0, 0)
    player.inventory.add_item(starting_potion)
    
    # Set player HP to max_hp after all equipment and components are initialized
    # (max_hp includes CON modifier and equipment bonuses)
    player.fighter.hp = player.fighter.max_hp

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
