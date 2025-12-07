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
from components.player_pathfinding import PlayerPathfinding
from components.speed_bonus_tracker import SpeedBonusTracker
from components.statistics import Statistics
from config.game_constants import get_constants as get_new_constants, get_combat_config, get_inventory_config
from config.entity_registry import load_entity_config
from config.entity_factory import get_entity_factory
from config.identification_manager import reset_identification_manager
from config.item_appearances import reset_appearance_generator
from config.level_template_registry import get_level_template_registry
from config.testing_config import get_testing_config
from entity import Entity
from equipment_slots import EquipmentSlots
from game_messages import MessageLog
from game_states import GameStates
from map_objects.game_map import GameMap
from render_functions import RenderOrder
from spells.spell_catalog import register_all_spells
from logger_config import get_logger
from instrumentation.run_metrics import initialize_run_metrics_recorder

logger = get_logger(__name__)


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
    
    # Initialize mural manager for unique message selection per floor
    from services.mural_manager import get_mural_manager
    mural_mgr = get_mural_manager()
    mural_mgr.set_current_floor(1)  # Start on floor 1
    
    # Register all spells in the spell registry
    register_all_spells()
    
    # Initialize appearance generator for item identification system
    appearance_gen = reset_appearance_generator()
    
    # Reset the identification manager (tracks which item types are identified)
    reset_identification_manager()
    
    # Reset the pity system (ensures healing drops don't go too long without appearing)
    from balance.pity import reset_pity_state
    reset_pity_state()
    
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
            # Phase 7: Tar potion (speed debuff)
            'tar_potion',
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
    
    # Add SpeedBonusTracker for combat speed system (Phase 1)
    # Default: 25% speed bonus = bonus attack after 4 consecutive attacks
    speed_bonus_component = SpeedBonusTracker(speed_bonus_ratio=0.25)
    player.speed_bonus_tracker = speed_bonus_component
    speed_bonus_component.owner = player
    player.components.add(ComponentType.SPEED_BONUS_TRACKER, speed_bonus_component)
    
    entities = [player]

    # Create starting equipment using EntityFactory
    dagger = entity_factory.create_weapon("dagger", 0, 0)
    player.require_component(ComponentType.INVENTORY).add_item(dagger)
    player.get_component_optional(ComponentType.EQUIPMENT).toggle_equip(dagger)
    
    # Add starting leather armor for better survivability
    leather_armor = entity_factory.create_armor("leather_armor", 0, 0)
    player.require_component(ComponentType.INVENTORY).add_item(leather_armor)
    player.get_component_optional(ComponentType.EQUIPMENT).toggle_equip(leather_armor)
    
    # Add starting healing potion for early game survivability (Option 6 balance)
    starting_potion = entity_factory.create_spell_item("healing_potion", 0, 0)
    player.require_component(ComponentType.INVENTORY).add_item(starting_potion)
    
    # PLAYTEST: Add Wand of Portals for testing portal system mechanics
    wand_of_portals = entity_factory.create_wand_of_portals(0, 0)
    if wand_of_portals:
        player.require_component(ComponentType.INVENTORY).add_item(wand_of_portals)
    
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
    config = get_testing_config()
    if config.start_level > 1:
        entities = _skip_to_level(player, entities, game_map, message_log, config.start_level, constants)

    # Tier 1 - Reveal entire map if requested (MUST be after level skip!)
    if config.reveal_map:
        # Mark all tiles as explored (will be rendered as visible)
        for x in range(game_map.width):
            for y in range(game_map.height):
                game_map.tiles[x][y].explored = True
    
    # Initialize run metrics recorder (Phase 1.5: Run Metrics)
    # Detect bot mode from constants (set by engine.py CLI parsing)
    bot_enabled = constants.get("input_config", {}).get("bot_enabled", False)
    run_mode = "bot" if bot_enabled else "human"
    
    # Get soak config if available (bot-soak mode with limits)
    soak_config = constants.get("soak_config", {})
    start_floor = soak_config.get("start_floor", 1)
    max_turns = soak_config.get("max_turns")
    max_floors = soak_config.get("max_floors")
    run_seed = soak_config.get("seed")  # RNG seed for deterministic runs
    
    initialize_run_metrics_recorder(
        mode=run_mode, 
        seed=run_seed,
        start_floor=start_floor,
        max_turns=max_turns,
        max_floors=max_floors
    )
    logger.info(f"Run metrics recorder initialized: mode={run_mode}, start_floor={start_floor}, seed={run_seed}")
    
    # Phase 1.5b: Wire telemetry floor tracking for initial floor
    from services.telemetry_service import get_telemetry_service
    telemetry_service = get_telemetry_service()
    if telemetry_service.enabled:
        telemetry_service.start_floor(game_map.dungeon_level)
        _populate_floor_telemetry(telemetry_service, game_map, entities)
        logger.info(f"Telemetry started for floor {game_map.dungeon_level}")

    return player, entities, game_map, message_log, game_state


def _populate_floor_telemetry(telemetry_service, game_map, entities):
    """Populate telemetry floor stats after map generation.
    
    Computes and records floor-level metrics including:
    - ETP sum (total monster difficulty)
    - Room count (approximated from map connectivity)
    - Monster count
    - Item count (excluding player inventory)
    - Door count
    - Trap count
    - Secret count
    
    Args:
        telemetry_service: TelemetryService instance
        game_map: GameMap with generated floor
        entities: List of all entities on the floor
    """
    from components.component_registry import ComponentType
    
    # Count entities by type
    monster_count = 0
    item_count = 0
    door_count = 0
    trap_count = 0
    secret_count = 0
    etp_sum = 0
    
    for entity in entities:
        # Skip player
        if entity.name == "Player":
            continue
        
        # Count monsters and sum ETP
        fighter = entity.get_component_optional(ComponentType.FIGHTER)
        ai = entity.get_component_optional(ComponentType.AI)
        if fighter and ai:
            monster_count += 1
            # ETP estimation: simple heuristic based on HP and power
            # (Real ETP might be tracked elsewhere, but this is reasonable)
            etp_sum += fighter.max_hp + (fighter.power * 2)
        
        # Count items (items have Item component)
        item_comp = entity.get_component_optional(ComponentType.ITEM)
        if item_comp:
            item_count += 1
        
        # Count doors
        door_comp = entity.get_component_optional(ComponentType.DOOR)
        if door_comp:
            door_count += 1
            # Count secret doors as secrets
            if door_comp.is_secret:
                secret_count += 1
        
        # Count traps
        trap_comp = entity.get_component_optional(ComponentType.TRAP)
        if trap_comp:
            trap_count += 1
    
    # Estimate room count from corridor connections (rough approximation)
    # Each corridor connects 2 rooms, so room_count ≈ connection_count + 1
    # But this is imperfect; we'll use a simple heuristic
    room_count = len(getattr(game_map, 'corridor_connections', [])) + 1
    
    # Set telemetry data
    telemetry_service.set_floor_etp(etp_sum=etp_sum)
    telemetry_service.set_room_counts(
        rooms=room_count,
        monsters=monster_count,
        items=item_count
    )
    
    logger.info(
        f"Floor {game_map.dungeon_level} telemetry: "
        f"ETP={etp_sum}, Rooms≈{room_count}, Monsters={monster_count}, "
        f"Items={item_count}, Doors={door_count}, Traps={trap_count}, Secrets={secret_count}"
    )


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
        
    Returns:
        list: Updated entities list for the target level
    """
    logger.info(f"⏭️  DEBUG: Skipping to level {target_level}...")
    print(f"⏭️  Descending to level {target_level}...")
    
    # Descend through levels, capturing the entities list each time
    for i in range(target_level - 1):
        maybe_new_entities = game_map.next_floor(player, message_log, constants)
        if isinstance(maybe_new_entities, list):
            entities = maybe_new_entities
        elif maybe_new_entities is not None:
            logger.debug(
                "   Ignoring next_floor return value of type %s; keeping existing entities",
                type(maybe_new_entities).__name__,
            )
        # Update mural manager for each floor
        from services.mural_manager import get_mural_manager
        mural_mgr = get_mural_manager()
        mural_mgr.set_current_floor(game_map.dungeon_level)
        logger.debug(f"   Descended to level {game_map.dungeon_level}")
    
    # Grant level-appropriate gear
    _grant_level_appropriate_gear(player, entities, target_level)
    
    # Boost player level to survive at this depth
    target_player_level = min(target_level // 2, 10)  # Half dungeon level, max 10
    player.level.current_level = target_player_level
    player.fighter.base_max_hp = 30 + (target_player_level * 10)
    player.fighter.hp = player.fighter.max_hp  # max_hp property calculates from base + bonuses
    
    logger.info(f"✅ Started at dungeon level {game_map.dungeon_level}")
    logger.info(f"   Player level: {player.level.current_level}")
    logger.info(f"   HP: {player.get_component_optional(ComponentType.FIGHTER).hp}/{player.get_component_optional(ComponentType.FIGHTER).max_hp}")
    
    print(f"✅ Ready! You are on dungeon level {game_map.dungeon_level}")
    print(f"   Player Level: {player.level.current_level} | HP: {player.get_component_optional(ComponentType.FIGHTER).hp}/{player.get_component_optional(ComponentType.FIGHTER).max_hp}")
    
    return entities


def _grant_level_appropriate_gear(player, entities, dungeon_level):
    """Grant gear appropriate for testing at a specific dungeon depth.
    
    Args:
        player: Player entity
        entities: List of all entities  
        dungeon_level: Current dungeon level
    """
    entity_factory = get_entity_factory()
    
    # Track entities created for gear (we'll remove them from world entities)
    created_gear = []
    
    # Always give healing potions (5 base + 1 per 5 levels)
    num_potions = 5 + (dungeon_level // 5)
    for i in range(num_potions):
        potion = entity_factory.create_spell_item('healing_potion', 0, 0)
        if potion:
            created_gear.append(potion)
            if player.require_component(ComponentType.INVENTORY):
                player.require_component(ComponentType.INVENTORY).add_item(potion)
    logger.info(f"   Granted {num_potions} healing potions")
    
    # Give weapon for deeper levels
    if dungeon_level >= 5:
        sword = entity_factory.create_weapon('sword', 0, 0)
        if sword:
            created_gear.append(sword)
            if player.get_component_optional(ComponentType.EQUIPMENT):
                # Unequip starting dagger first
                if player.get_component_optional(ComponentType.EQUIPMENT).main_hand:
                    player.require_component(ComponentType.INVENTORY).add_item(player.get_component_optional(ComponentType.EQUIPMENT).main_hand)
                    player.get_component_optional(ComponentType.EQUIPMENT).toggle_equip(player.get_component_optional(ComponentType.EQUIPMENT).main_hand)
                player.get_component_optional(ComponentType.EQUIPMENT).toggle_equip(sword)
                logger.info("   Granted sword (replacing dagger)")
    
    # Give armor for deeper levels
    if dungeon_level >= 10:
        chain_mail = entity_factory.create_armor('chain_mail', 0, 0)
        if chain_mail:
            created_gear.append(chain_mail)
            if player.get_component_optional(ComponentType.EQUIPMENT):
                # Unequip starting leather armor
                if player.get_component_optional(ComponentType.EQUIPMENT).chest:
                    player.require_component(ComponentType.INVENTORY).add_item(player.get_component_optional(ComponentType.EQUIPMENT).chest)
                    player.get_component_optional(ComponentType.EQUIPMENT).toggle_equip(player.get_component_optional(ComponentType.EQUIPMENT).chest)
                player.get_component_optional(ComponentType.EQUIPMENT).toggle_equip(chain_mail)
                logger.info("   Granted chain mail (replacing leather armor)")
    
    # Give utility scrolls for deep levels
    if dungeon_level >= 15:
        for i in range(3):
            scroll = entity_factory.create_spell_item('teleport_scroll', 0, 0)
            if scroll:
                created_gear.append(scroll)
                if player.require_component(ComponentType.INVENTORY):
                    player.require_component(ComponentType.INVENTORY).add_item(scroll)
        logger.info("   Granted 3 teleport scrolls")
    
    # Remove created gear from world entities list (they should only be in inventory/equipment)
    # Items created at (0, 0) shouldn't appear on the map
    for gear in created_gear:
        if gear in entities:
            entities.remove(gear)
            logger.debug(f"   Removed {gear.name} from world entities (now in inventory/equipment)")
    
    # Also validate all entities have valid coordinates within map bounds
    from config.game_constants import GameConstants
    game_constants = GameConstants()
    map_width = game_constants.gameplay.DEFAULT_MAP_WIDTH
    map_height = game_constants.gameplay.DEFAULT_MAP_HEIGHT
    
    invalid_entities = [e for e in entities if e.x < 0 or e.x >= map_width or e.y < 0 or e.y >= map_height]
    if invalid_entities:
        logger.warning(f"   ⚠️  Found {len(invalid_entities)} entities with invalid coordinates:")
        for entity in invalid_entities:
            has_item = hasattr(entity, 'item') and entity.get_component_optional(ComponentType.ITEM)
            has_fighter = hasattr(entity, 'fighter') and entity.get_component_optional(ComponentType.FIGHTER)
            entity_type = "item" if has_item else "monster" if has_fighter else "other"
            logger.warning(f"      {entity.name} ({entity_type}) at ({entity.x}, {entity.y}) - removing from world")
            print(f"   ⚠️  DEBUG: Removed invalid entity: {entity.name} at ({entity.x}, {entity.y})")
            if entity in entities:
                entities.remove(entity)
    else:
        logger.debug(f"   ✅ All {len(entities)} entities have valid coordinates")
    
    # Recalculate HP after equipment changes (max_hp is a property, recalculates automatically)
    player.fighter.hp = player.fighter.max_hp
