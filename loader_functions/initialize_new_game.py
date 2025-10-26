"""Game initialization functions and constants.

This module handles the creation of new games, setting up initial
game state, player character, and game world configuration.
"""

from tcod import libtcodpy

from components.component_registry import ComponentType
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
    
    # Check for map size overrides from level templates (level 1)
    # This allows testing mode to set larger maps via level_templates_testing.yaml
    from config.level_template_registry import get_level_template_registry
    registry = get_level_template_registry()
    
    level_1_override = registry.get_level_override(1)
    if level_1_override and level_1_override.has_parameters():
        params = level_1_override.parameters
        if params.map_width is not None:
            constants["map_width"] = params.map_width
        if params.map_height is not None:
            constants["map_height"] = params.map_height
    
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
    
    # Register all spells in the spell registry
    from spells.spell_catalog import register_all_spells
    register_all_spells()
    
    # Initialize appearance generator for item identification system
    from config.item_appearances import reset_appearance_generator
    appearance_gen = reset_appearance_generator()
    
    # Reset the identification manager (tracks which item types are identified)
    from config.identification_manager import reset_identification_manager
    reset_identification_manager()
    
    # Register all item types that need identification
    appearance_gen.initialize({
        'scroll': [
            # Existing scrolls
            'lightning_scroll', 'fireball_scroll', 'confusion_scroll',
            'invisibility_scroll', 'teleport_scroll', 'enhance_weapon_scroll',
            'enhance_armor_scroll', 'shield_scroll', 'dragon_fart_scroll',
            'raise_dead_scroll', 'yo_mama_scroll', 'slow_scroll',
            'glue_scroll', 'rage_scroll',
            # New scrolls (v3.11.0+)
            'haste_scroll', 'blink_scroll', 'light_scroll',
            'magic_mapping_scroll', 'earthquake_scroll', 'identify_scroll'
        ],
        'potion': [
            'healing_potion',
            # New buff potions
            'speed_potion', 'regeneration_potion', 'invisibility_potion',
            'levitation_potion', 'protection_potion', 'heroism_potion',
            # New debuff potions
            'weakness_potion', 'slowness_potion', 'blindness_potion',
            'paralysis_potion',
            # Special potion
            'experience_potion'
        ],
        'ring': [
            # Defensive rings
            'ring_of_protection', 'ring_of_regeneration', 'ring_of_resistance',
            # Offensive rings
            'ring_of_strength', 'ring_of_dexterity', 'ring_of_might',
            # Utility rings
            'ring_of_teleportation', 'ring_of_invisibility', 'ring_of_searching',
            'ring_of_free_action',
            # Magic rings
            'ring_of_wizardry', 'ring_of_clarity', 'ring_of_speed',
            # Special rings
            'ring_of_constitution', 'ring_of_luck'
        ]
    })
    
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
    # IMPORTANT: Register with ComponentRegistry AND set as direct attribute
    player.pathfinding = pathfinding_component
    pathfinding_component.owner = player
    player.components.add(ComponentType.PATHFINDING, pathfinding_component)
    
    player.statistics = statistics_component
    statistics_component.owner = player
    player.components.add(ComponentType.STATISTICS, statistics_component)
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
    
    # DEBUG: Tier 1 - Skip to specific dungeon level if requested
    from config.testing_config import get_testing_config
    config = get_testing_config()
    if config.start_level > 1:
        _skip_to_level(player, entities, game_map, message_log, config.start_level, constants)

    return player, entities, game_map, message_log, game_state


def _skip_to_level(player, entities, game_map, message_log, target_level, constants):
    """Skip to a specific dungeon level for testing.
    
    Descends through levels and grants appropriate gear for the target depth.
    
    Args:
        player: Player entity
        entities: List of all entities
        game_map: Game map
        message_log: Message log
        target_level: Target dungeon level (2-25)
        constants: Game constants
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"⏭️  DEBUG: Skipping to level {target_level}...")
    print(f"⏭️  Descending to level {target_level}...")
    
    # Descend through levels
    for i in range(target_level - 1):
        game_map.next_floor(player, message_log, constants)
        logger.debug(f"   Descended to level {game_map.dungeon_level}")
    
    # Grant level-appropriate gear
    _grant_level_appropriate_gear(player, entities, target_level)
    
    # Boost player level to survive at this depth
    target_player_level = min(target_level // 2, 10)  # Half dungeon level, max 10
    player.level.current_level = target_player_level
    player.fighter.max_hp = 30 + (target_player_level * 10)
    player.fighter.hp = player.fighter.max_hp
    
    logger.info(f"✅ Started at dungeon level {game_map.dungeon_level}")
    logger.info(f"   Player level: {player.level.current_level}")
    logger.info(f"   HP: {player.fighter.hp}/{player.fighter.max_hp}")
    
    print(f"✅ Ready! You are on dungeon level {game_map.dungeon_level}")
    print(f"   Player Level: {player.level.current_level} | HP: {player.fighter.hp}/{player.fighter.max_hp}")


def _grant_level_appropriate_gear(player, entities, dungeon_level):
    """Grant gear appropriate for testing at a specific dungeon depth.
    
    Args:
        player: Player entity
        entities: List of all entities  
        dungeon_level: Current dungeon level
    """
    import logging
    logger = logging.getLogger(__name__)
    
    entity_factory = get_entity_factory()
    
    # Always give healing potions (5 base + 1 per 5 levels)
    num_potions = 5 + (dungeon_level // 5)
    for i in range(num_potions):
        potion = entity_factory.create_spell_item('healing_potion', 0, 0)
        if potion and player.inventory:
            player.inventory.add_item(potion)
    logger.info(f"   Granted {num_potions} healing potions")
    
    # Give weapon for deeper levels
    if dungeon_level >= 5:
        sword = entity_factory.create_weapon('sword', 0, 0)
        if sword and player.equipment:
            # Unequip starting dagger first
            if player.equipment.main_hand:
                player.inventory.add_item(player.equipment.main_hand)
                player.equipment.toggle_equip(player.equipment.main_hand)
            player.equipment.toggle_equip(sword)
            logger.info("   Granted sword (replacing dagger)")
    
    # Give armor for deeper levels
    if dungeon_level >= 10:
        chain_mail = entity_factory.create_armor('chain_mail', 0, 0)
        if chain_mail and player.equipment:
            # Unequip starting leather armor
            if player.equipment.chest:
                player.inventory.add_item(player.equipment.chest)
                player.equipment.toggle_equip(player.equipment.chest)
            player.equipment.toggle_equip(chain_mail)
            logger.info("   Granted chain mail (replacing leather armor)")
    
    # Give utility scrolls for deep levels
    if dungeon_level >= 15:
        for i in range(3):
            scroll = entity_factory.create_spell_item('teleport_scroll', 0, 0)
            if scroll and player.inventory:
                player.inventory.add_item(scroll)
        logger.info("   Granted 3 teleport scrolls")
    
    # Recalculate HP after equipment changes (max_hp is a property, recalculates automatically)
    player.fighter.hp = player.fighter.max_hp
