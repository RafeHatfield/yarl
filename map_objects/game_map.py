"""Game map generation and management.

This module contains the GameMap class which handles dungeon generation,
tile management, entity placement, and map navigation. It uses BSP-style
room generation with connecting tunnels.
"""

from random import randint, random, choice
import logging

from components.ai import BasicMonster
from components.equippable import Equippable
from components.fighter import Fighter
from config.entity_factory import get_entity_factory
from config.level_template_registry import get_level_template_registry
from entity import Entity
from entity_sorting_cache import invalidate_entity_cache
from equipment_slots import EquipmentSlots
from game_messages import Message
from message_builder import MessageBuilder as MB
from map_objects.rectangle import Rect
from map_objects.tile import Tile
from random_utils import from_dungeon_level, random_choice_from_dict
from render_functions import RenderOrder
from stairs import Stairs
from config.testing_config import get_testing_config

logger = logging.getLogger(__name__)


class GameMap:
    """Manages the game map including tiles, rooms, and entity placement.

    Handles dungeon generation using rectangular rooms connected by tunnels,
    entity spawning based on dungeon level, map navigation, and persistent
    ground hazards from area-of-effect spells.

    Attributes:
        width (int): Map width in tiles
        height (int): Map height in tiles
        tiles (list): 2D array of Tile objects
        dungeon_level (int): Current dungeon level for scaling difficulty
        hazard_manager (GroundHazardManager): Manages persistent ground hazards
    """

    def __init__(self, width, height, dungeon_level=1):
        """Initialize a new GameMap.

        Args:
            width (int): Width of the map in tiles
            height (int): Height of the map in tiles
            dungeon_level (int, optional): Dungeon level for difficulty scaling. Defaults to 1.
        """
        self.width = width
        self.height = height
        self.tiles = self.initialize_tiles()
        self.dungeon_level = dungeon_level
        
        # Initialize ground hazard manager for persistent spell effects
        from components.ground_hazard import GroundHazardManager
        self.hazard_manager = GroundHazardManager()
        
        # Initialize secret door manager for hidden passages
        from map_objects.secret_door import SecretDoorManager
        self.secret_door_manager = SecretDoorManager()

    def initialize_tiles(self):
        """Initialize the map with blocked wall tiles.

        Returns:
            list: 2D array of Tile objects, all initially blocked
        """
        """Function initializing the tiles in the map"""
        tiles = [[Tile(True) for y in range(self.height)] for x in range(self.width)]

        return tiles

    def make_map(
        self,
        max_rooms,
        room_min_size,
        room_max_size,
        map_width,
        map_height,
        player,
        entities,
    ):
        """Generate a new dungeon map with rooms and tunnels.

        Uses BSP-style generation to create rectangular rooms connected
        by horizontal and vertical tunnels. Places the player in the first
        room and stairs in the last room.
        
        Level parameters can be overridden via level templates (Tier 2).

        Args:
            max_rooms (int): Maximum number of rooms to generate
            room_min_size (int): Minimum room dimension
            room_max_size (int): Maximum room dimension
            map_width (int): Map width in tiles
            map_height (int): Map height in tiles
            player (Entity): Player entity to place
            entities (list): List to populate with generated entities
        """
        # Check for level template overrides (Tier 2)
        template_registry = get_level_template_registry()
        level_override = template_registry.get_level_override(self.dungeon_level)
        
        # Apply level parameter overrides if configured
        if level_override and level_override.has_parameters():
            params = level_override.parameters
            if params.max_rooms is not None:
                max_rooms = params.max_rooms
                logger.info(f"Level {self.dungeon_level}: Overriding max_rooms = {max_rooms}")
            if params.min_room_size is not None:
                room_min_size = params.min_room_size
                logger.info(f"Level {self.dungeon_level}: Overriding min_room_size = {room_min_size}")
            if params.max_room_size is not None:
                room_max_size = params.max_room_size
                logger.info(f"Level {self.dungeon_level}: Overriding max_room_size = {room_max_size}")
        
        rooms = []
        num_rooms = 0

        # find centre of the last room we create, we will place stairs here
        center_of_last_room_x = None
        center_of_last_room_y = None

        for r in range(max_rooms):
            # random width and height
            w = randint(room_min_size, room_max_size)
            h = randint(room_min_size, room_max_size)
            # random position without going out of the boundaries of the map
            x = randint(0, map_width - w - 1)
            y = randint(0, map_height - h - 1)

            # "Rect" class makes rectangles easier to work with
            new_room = Rect(x, y, w, h)

            # run through the other rooms and see if they intersect with this one
            for other_room in rooms:
                if new_room.intersect(other_room):
                    break
            else:
                # this means there are no intersections, so this room is valid

                # "paint" it to the map's tiles
                self.create_room(new_room)

                # center coordinates of new room, will be useful later
                (new_x, new_y) = new_room.center()

                center_of_last_room_x = new_x
                center_of_last_room_y = new_y

                if num_rooms == 0:
                    # this is the first room, where the player starts at
                    # Ensure we place player in a walkable tile (safety check)
                    player.x = new_x
                    player.y = new_y
                    
                    # Verify the spawn tile is walkable (should always be true, but safety check)
                    if self.tiles[player.x][player.y].blocked:
                        logger.error(f"Player spawn at ({player.x}, {player.y}) is blocked! Finding safe spawn...")
                        # Find nearest walkable tile in first room
                        for dx in range(-2, 3):
                            for dy in range(-2, 3):
                                check_x, check_y = player.x + dx, player.y + dy
                                if (0 <= check_x < self.width and 0 <= check_y < self.height and
                                    not self.tiles[check_x][check_y].blocked):
                                    player.x = check_x
                                    player.y = check_y
                                    logger.info(f"Moved player to safe spawn at ({player.x}, {player.y})")
                                    break
                            else:
                                continue
                            break
                else:
                    # all rooms after the first:
                    # connect it to the previous room with a tunnel

                    # center coordinates of previous room
                    (prev_x, prev_y) = rooms[num_rooms - 1].center()

                    # flip a coin (random number that is either 0 or 1)
                    if randint(0, 1) == 1:
                        # first move horizontally, then vertically
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        # first move vertically, then horizontally
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)

                self.place_entities(new_room, entities)
                
                # Place exploration features (chests, signposts)
                self.place_exploration_features(new_room, entities)

                # finally, append the new room to the list
                rooms.append(new_room)
                num_rooms += 1

        stairs_component = Stairs(self.dungeon_level + 1)
        down_stairs = Entity(
            center_of_last_room_x,
            center_of_last_room_y,
            ">",
            (255, 255, 255),
            "Stairs",
            render_order=RenderOrder.STAIRS,
            stairs=stairs_component,
        )
        entities.append(down_stairs)
        
        # VICTORY CONDITION: Spawn Amulet of Yendor on level 25!
        if self.dungeon_level == 25:
            from config.entity_factory import get_entity_factory
            factory = get_entity_factory()
            
            # Place amulet in center of the last room (where stairs are)
            # Offset slightly so it doesn't overlap with stairs
            amulet_x = center_of_last_room_x + 1
            amulet_y = center_of_last_room_y
            
            amulet = factory.create_unique_item('amulet_of_yendor', amulet_x, amulet_y)
            if amulet:
                entities.append(amulet)
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"=== AMULET OF YENDOR SPAWNED at ({amulet_x}, {amulet_y}) ===")
        
        # Apply special rooms from level templates (Tier 2)
        self.place_special_rooms(rooms, entities)
        
        # Apply guaranteed spawns from level templates (if configured)
        self.place_guaranteed_spawns(rooms, entities)
        
        # Designate some rooms as treasure vaults (Phase 1: Simple Vaults)
        self.designate_vaults(rooms, entities)
        
        # Place secret doors between rooms (15% chance per level)
        self.place_secret_doors_between_rooms(rooms)

    def create_room(self, room):
        """Create a room by making tiles passable.

        Args:
            room (Rect): Rectangle defining the room boundaries
        """
        """Function to make a room on the map"""
        # go through the tiles in the rectangle and make them passable
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False

    def create_h_tunnel(self, x1, x2, y):
        """Create a horizontal tunnel between two x coordinates.

        Args:
            x1 (int): Starting x coordinate
            x2 (int): Ending x coordinate
            y (int): Y coordinate of the tunnel
        """
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def create_v_tunnel(self, y1, y2, x):
        """Create a vertical tunnel between two y coordinates.

        Args:
            y1 (int): Starting y coordinate
            y2 (int): Ending y coordinate
            x (int): X coordinate of the tunnel
        """
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def place_entities(self, room, entities):
        """Place monsters and items in a room based on dungeon level.

        Uses probability tables that scale with dungeon level to determine
        what entities to spawn and where to place them. Spawn rates can be
        modified by testing configuration or level template overrides (Tier 2).

        Args:
            room (Rect): Room to place entities in
            entities (list): List to add new entities to
        """
        config = get_testing_config()
        
        # Get spawn limits from configuration
        max_monsters_per_room = from_dungeon_level(
            config.get_max_monsters_per_room(self.dungeon_level), self.dungeon_level
        )
        max_items_per_room = from_dungeon_level(
            config.get_max_items_per_room(self.dungeon_level), self.dungeon_level
        )
        
        # Apply level parameter overrides if configured (Tier 2)
        template_registry = get_level_template_registry()
        level_override = template_registry.get_level_override(self.dungeon_level)
        
        if level_override and level_override.has_parameters():
            params = level_override.parameters
            if params.max_monsters_per_room is not None:
                max_monsters_per_room = params.max_monsters_per_room
            if params.max_items_per_room is not None:
                max_items_per_room = params.max_items_per_room
        
        # Get a random number of monsters and items
        number_of_monsters = randint(0, max_monsters_per_room)
        number_of_items = randint(0, max_items_per_room)

        monster_chances = {
            "orc": 80,
            "troll": from_dungeon_level(
                [[15, 3], [30, 5], [60, 7]], self.dungeon_level
            ),
        }
        
        # Add slimes for testing or higher levels
        from config.testing_config import is_testing_mode
        if is_testing_mode():
            # In testing mode, slimes appear early for testing
            monster_chances["slime"] = 40  # 40% chance on level 1
            monster_chances["large_slime"] = from_dungeon_level(
                [[10, 1], [20, 3]], self.dungeon_level  # Small chance from level 1
            )
        else:
            # In normal mode, slimes appear later
            monster_chances["slime"] = from_dungeon_level(
                [[20, 2], [40, 4], [60, 6]], self.dungeon_level
            )
            monster_chances["large_slime"] = from_dungeon_level(
                [[5, 3], [15, 5], [25, 7]], self.dungeon_level
            )

        # Get item spawn chances from configuration (normal or testing mode)
        item_spawn_config = config.get_item_spawn_chances(self.dungeon_level)
        item_chances = {}
        
        for item_name, chance_config in item_spawn_config.items():
            if isinstance(chance_config, int):
                # Simple percentage chance
                item_chances[item_name] = chance_config
            else:
                # Dungeon level-based progression
                item_chances[item_name] = from_dungeon_level(chance_config, self.dungeon_level)

        for i in range(number_of_monsters):
            # Choose a random location in the room
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)

            if not any(
                [entity for entity in entities if entity.x == x and entity.y == y]
            ):
                monster_choice = random_choice_from_dict(monster_chances)
                
                # Create monster using EntityFactory
                entity_factory = get_entity_factory()
                monster = entity_factory.create_monster(monster_choice, x, y)
                
                if monster:
                    # Try to spawn equipment on the monster
                    from components.monster_equipment import spawn_equipment_on_monster
                    equipment_list = spawn_equipment_on_monster(monster, self.dungeon_level)
                    
                    entities.append(monster)
                    # Invalidate entity sorting cache when new entities are added
                    invalidate_entity_cache("entity_added_monster")

        for i in range(number_of_items):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)

            if not any(
                [entity for entity in entities if entity.x == x and entity.y == y]
            ):
                item_choice = random_choice_from_dict(item_chances)
                
                # Get entity factory for equipment creation
                entity_factory = get_entity_factory()
                
                # Create all items using EntityFactory for consistent identification
                if item_choice == "healing_potion":
                    item = entity_factory.create_spell_item("healing_potion", x, y)
                elif item_choice == "sword":
                    item = entity_factory.create_weapon("sword", x, y)
                elif item_choice == "shield":
                    item = entity_factory.create_armor("shield", x, y)
                elif item_choice == "fireball_scroll":
                    item = entity_factory.create_spell_item("fireball_scroll", x, y)
                elif item_choice == "confusion_scroll":
                    item = entity_factory.create_spell_item("confusion_scroll", x, y)
                elif item_choice == "enhance_weapon_scroll":
                    item = entity_factory.create_spell_item("enhance_weapon_scroll", x, y)
                elif item_choice == "enhance_armor_scroll":
                    item = entity_factory.create_spell_item("enhance_armor_scroll", x, y)
                elif item_choice == "invisibility_scroll":
                    item = entity_factory.create_spell_item("invisibility_scroll", x, y)
                # Wands
                elif item_choice == "wand_of_fireball":
                    item = entity_factory.create_wand("wand_of_fireball", x, y, self.dungeon_level)
                elif item_choice == "wand_of_lightning":
                    item = entity_factory.create_wand("wand_of_lightning", x, y, self.dungeon_level)
                elif item_choice == "wand_of_confusion":
                    item = entity_factory.create_wand("wand_of_confusion", x, y, self.dungeon_level)
                elif item_choice == "wand_of_teleportation":
                    item = entity_factory.create_wand("wand_of_teleportation", x, y, self.dungeon_level)
                elif item_choice == "wand_of_dragon_farts":
                    item = entity_factory.create_wand("wand_of_dragon_farts", x, y, self.dungeon_level)
                elif item_choice == "wand_of_yo_mama":
                    item = entity_factory.create_wand("wand_of_yo_mama", x, y, self.dungeon_level)
                elif item_choice == "yo_mama_scroll":
                    item = entity_factory.create_spell_item("yo_mama_scroll", x, y)
                elif item_choice == "slow_scroll":
                    item = entity_factory.create_spell_item("slow_scroll", x, y)
                elif item_choice == "glue_scroll":
                    item = entity_factory.create_spell_item("glue_scroll", x, y)
                elif item_choice == "rage_scroll":
                    item = entity_factory.create_spell_item("rage_scroll", x, y)
                elif item_choice == "wand_of_slow":
                    item = entity_factory.create_wand("wand_of_slow", x, y, self.dungeon_level)
                elif item_choice == "wand_of_glue":
                    item = entity_factory.create_wand("wand_of_glue", x, y, self.dungeon_level)
                elif item_choice == "wand_of_rage":
                    item = entity_factory.create_wand("wand_of_rage", x, y, self.dungeon_level)
                else:
                    # Smart fallback: try different creation methods until one works
                    # This handles any items added to spawn tables without explicit elif blocks
                    item = entity_factory.create_weapon(item_choice, x, y)
                    if not item:
                        item = entity_factory.create_armor(item_choice, x, y)
                    if not item:
                        # Try as ring
                        item = entity_factory.create_ring(item_choice, x, y)
                    if not item:
                        # Try as spell item (potions, scrolls)
                        item = entity_factory.create_spell_item(item_choice, x, y)
                    if not item:
                        # Try as wand
                        item = entity_factory.create_wand(item_choice, x, y, self.dungeon_level)
                    
                    # Final fallback if everything fails
                    if not item:
                        logger.warning(f"Failed to create item: {item_choice}, falling back to healing potion")
                        item = entity_factory.create_spell_item("healing_potion", x, y)

                entities.append(item)
                # Invalidate entity sorting cache when new entities are added
                invalidate_entity_cache("entity_added_item")

    def place_exploration_features(self, room, entities):
        """Place exploration features (chests, signposts, secret doors) in a room.
        
        Spawns exploration content based on dungeon level and probability tables:
        - Chests: 30% chance per room (quality scales with depth)
        - Signposts: 20% chance per room (random messages)
        - Secret doors: 15% chance per level (placed between rooms)
        
        Args:
            room (Rect): Room to place features in
            entities (list): List to add new feature entities to
        """
        from random import random, choice
        entity_factory = get_entity_factory()
        
        # CHESTS - 30% chance per room
        if random() < 0.30:
            # Determine chest quality based on dungeon level
            if self.dungeon_level >= 8:
                chest_type = choice(['golden_chest', 'chest', 'trapped_chest'])
            elif self.dungeon_level >= 5:
                chest_type = choice(['chest', 'trapped_chest', 'chest'])
            else:
                chest_type = 'chest'
            
            # Random position in room (not at edges)
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            
            chest = entity_factory.create_chest(chest_type, x, y)
            if chest:
                entities.append(chest)
                logger.debug(f"Placed {chest_type} at ({x}, {y}) in room")
        
        # SIGNPOSTS - 20% chance per room
        if random() < 0.20:
            # Random signpost type
            sign_type = choice(['signpost', 'warning_sign', 'humor_sign', 'hint_sign'])
            
            # Random position in room (not at edges)
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            
            signpost = entity_factory.create_signpost(sign_type, x, y, depth=self.dungeon_level)
            if signpost:
                entities.append(signpost)
                logger.debug(f"Placed {sign_type} at ({x}, {y}) in room (depth {self.dungeon_level})")
    
    def place_secret_doors_between_rooms(self, rooms):
        """Place secret doors between some rooms.
        
        15% chance per level to generate 1-3 secret doors connecting rooms.
        Secret doors appear as walls until revealed by player proximity or search.
        
        Args:
            rooms (list): List of Rect rooms in the dungeon
        """
        from random import random, randint, choice
        from map_objects.secret_door import SecretDoor
        
        # 15% chance to have secret doors on this level
        if random() > 0.15:
            return
        
        # Generate 1-3 secret doors
        num_doors = randint(1, min(3, len(rooms) - 1))
        
        for _ in range(num_doors):
            if len(rooms) < 2:
                break
            
            # Pick two adjacent rooms to connect
            room_a = choice(rooms)
            room_b = choice([r for r in rooms if r != room_a])
            
            # Find a wall position between them
            # Check if rooms are adjacent and have valid overlap
            x, y = None, None
            
            if room_a.x2 == room_b.x1 - 1:
                # Rooms are horizontally adjacent (A is west of B)
                y_min = max(room_a.y1, room_b.y1) + 1
                y_max = min(room_a.y2, room_b.y2) - 1
                if y_min <= y_max:  # Valid overlap
                    x = room_a.x2
                    y = randint(y_min, y_max)
            elif room_b.x2 == room_a.x1 - 1:
                # Rooms are horizontally adjacent (B is west of A)
                y_min = max(room_a.y1, room_b.y1) + 1
                y_max = min(room_a.y2, room_b.y2) - 1
                if y_min <= y_max:  # Valid overlap
                    x = room_b.x2
                    y = randint(y_min, y_max)
            elif room_a.y2 == room_b.y1 - 1:
                # Rooms are vertically adjacent (A is north of B)
                x_min = max(room_a.x1, room_b.x1) + 1
                x_max = min(room_a.x2, room_b.x2) - 1
                if x_min <= x_max:  # Valid overlap
                    x = randint(x_min, x_max)
                    y = room_a.y2
            elif room_b.y2 == room_a.y1 - 1:
                # Rooms are vertically adjacent (B is north of A)
                x_min = max(room_a.x1, room_b.x1) + 1
                x_max = min(room_a.x2, room_b.x2) - 1
                if x_min <= x_max:  # Valid overlap
                    x = randint(x_min, x_max)
                    y = room_b.y2
            
            # Skip if rooms not adjacent or no valid overlap
            if x is None or y is None:
                continue
            
            # Create secret door at this position
            door = SecretDoor(x, y, connected_rooms=(id(room_a), id(room_b)))
            self.secret_door_manager.add_door(door)
            logger.debug(f"Placed secret door at ({x}, {y}) between rooms")
    
    def designate_vaults(self, rooms, entities):
        """Designate some rooms as treasure vaults with elite monsters and guaranteed loot.
        
        Phase 1: Simple Treasure Rooms
        - Spawn on depths 4+ (10% chance at depth 4-6, 15% at depth 7-9, 20% at depth 10+)
        - Elite monsters: 2x HP, +2 damage, +1 AC, spawn from depth+2
        - Guaranteed 2-3 chests with rare/legendary loot
        - Visual distinction (golden walls)
        
        Can be overridden via level templates using 'vault_count' parameter:
            parameters:
              vault_count: 2  # Force exactly 2 vaults on this level
        
        Args:
            rooms (list): List of Rect objects representing rooms
            entities (list): List of entities on the map
        """
        if len(rooms) < 3:
            return  # Need at least 3 rooms (player start, stairs, vault)
        
        # Check for level template override first
        from config.level_template_registry import get_level_template_registry
        template_registry = get_level_template_registry()
        level_override = template_registry.get_level_override(self.dungeon_level)
        
        vault_count_override = None
        if level_override and level_override.has_parameters():
            vault_count_override = level_override.parameters.vault_count
        
        # If template specifies vault count, use it (ignores depth restrictions)
        if vault_count_override is not None:
            num_vaults = max(0, min(vault_count_override, len(rooms) - 2))  # Cap at available rooms
            if num_vaults > 0:
                logger.info(
                    f"Level {self.dungeon_level}: Creating {num_vaults} vaults (from template override)"
                )
            else:
                return
        else:
            # No template override - use random chance based on depth/mode
            from config.testing_config import is_testing_mode
            testing_mode = is_testing_mode()
            
            # In normal mode, no vaults on early floors
            if not testing_mode and self.dungeon_level < 4:
                return  # No vaults on early floors (except in testing)
            
            # Calculate vault chance based on depth
            # In testing mode, increase chances dramatically for easier testing
            if testing_mode:
                if self.dungeon_level <= 2:
                    vault_chance = 0.80  # 80% on level 1-2 for testing
                else:
                    vault_chance = 0.50  # 50% on other levels in testing
            else:
                # Normal mode spawn rates
                if self.dungeon_level <= 6:
                    vault_chance = 0.10
                elif self.dungeon_level <= 9:
                    vault_chance = 0.15
                else:
                    vault_chance = 0.20
            
            # Roll for vault
            if random() > vault_chance:
                logger.debug(f"Level {self.dungeon_level}: No vault (rolled > {vault_chance})")
                return
            
            # Random generation: create 1 vault
            num_vaults = 1
        
        # Pick room(s) that's not first (player) or last (stairs)
        eligible_rooms = rooms[1:-1]
        if not eligible_rooms:
            return
        
        # Ensure we don't try to create more vaults than eligible rooms
        num_vaults = min(num_vaults, len(eligible_rooms))
        
        # Randomly select vault rooms
        from random import sample
        vault_rooms = sample(eligible_rooms, num_vaults)
        
        # Load vault theme registry
        from config.vault_theme_registry import get_vault_theme_registry
        theme_registry = get_vault_theme_registry()
        
        # Create each vault with a theme
        for vault_room in vault_rooms:
            vault_room.is_vault = True
            
            # Select a theme for this vault based on depth and spawn chances
            vault_theme = self._select_vault_theme(theme_registry, self.dungeon_level)
            theme_name = vault_theme.get('name', 'Treasure Room')
            
            logger.info(
                f"Level {self.dungeon_level}: Designated {theme_name} at room center {vault_room.center()}"
            )
            
            # Apply visual distinction (themed walls)
            self._apply_vault_visuals(vault_room, vault_theme)
            
            # Spawn elite monsters (themed)
            self._spawn_vault_monsters(vault_room, entities, vault_theme)
            
            # Spawn guaranteed loot (themed chests + bonus items)
            self._spawn_vault_loot(vault_room, entities, vault_theme)
    
    def _select_vault_theme(self, theme_registry, depth):
        """Select a vault theme based on depth and spawn chances.
        
        Args:
            theme_registry: VaultThemeRegistry instance
            depth: Current dungeon level
            
        Returns:
            Theme configuration dictionary
        """
        # Get available themes for this depth
        available_themes = theme_registry.get_available_themes(depth)
        
        if not available_themes:
            # No themes available, use default
            return theme_registry.get_default_theme()
        
        # Build weighted selection based on spawn chances
        theme_weights = []
        for theme_id in available_themes:
            spawn_chance = theme_registry.get_spawn_chance(theme_id, depth)
            theme_weights.append((theme_id, spawn_chance))
        
        # Weighted random selection
        total_weight = sum(weight for _, weight in theme_weights)
        if total_weight <= 0:
            return theme_registry.get_default_theme()
        
        roll = random() * total_weight
        cumulative = 0
        
        for theme_id, weight in theme_weights:
            cumulative += weight
            if roll <= cumulative:
                theme = theme_registry.get_theme(theme_id)
                if theme:
                    return theme
        
        # Fallback to default
        return theme_registry.get_default_theme()
    
    def _apply_vault_visuals(self, room, vault_theme=None):
        """Apply visual distinction to vault room walls using theme colors.
        
        Args:
            room (Rect): The vault room to modify
            vault_theme (dict): Theme configuration with wall_color
        """
        # Get wall color from theme, or use default golden tint
        if vault_theme and 'wall_color' in vault_theme:
            wall_color = tuple(vault_theme['wall_color'])
        else:
            wall_color = (200, 150, 50)  # Default golden tint
        
        # Color the walls of the vault room
        for x in range(room.x1, room.x2 + 1):
            for y in range(room.y1, room.y2 + 1):
                # Only color walls, not floor tiles
                if self.tiles[x][y].blocked:
                    self.tiles[x][y].light = wall_color
                    self.tiles[x][y].dark = tuple(c // 2 for c in wall_color)
    
    def _spawn_vault_monsters(self, room, entities, vault_theme=None):
        """Spawn elite monsters in vault room using theme configuration.
        
        Uses theme's monster table and elite scaling modifiers.
        
        Args:
            room (Rect): The vault room
            entities (list): List of entities on the map
            vault_theme (dict): Theme configuration with monsters and elite_scaling
        """
        from config.entity_factory import get_entity_factory
        from random_utils import random_choice_from_dict
        
        entity_factory = get_entity_factory()
        
        # Get monster configuration from theme, or use defaults
        if vault_theme and 'monsters' in vault_theme:
            monster_chances = vault_theme['monsters']
        else:
            # Default monster chances
            monster_chances = {"orc": 80, "troll": 20}
        
        # Get elite scaling from theme, or use defaults
        if vault_theme and 'elite_scaling' in vault_theme:
            elite_scaling = vault_theme['elite_scaling']
            hp_multiplier = elite_scaling.get('hp_multiplier', 2.0)
            power_bonus = elite_scaling.get('power_bonus', 2)
            defense_bonus = elite_scaling.get('defense_bonus', 1)
        else:
            # Default elite scaling
            hp_multiplier = 2.0
            power_bonus = 2
            defense_bonus = 1
        
        # Calculate monster count (2-6 monsters)
        elite_monster_count = randint(2, 6)
        
        theme_name = vault_theme.get('name', 'vault') if vault_theme else 'vault'
        logger.debug(
            f"Spawning {elite_monster_count} elite monsters in {theme_name} "
            f"({hp_multiplier}x HP, +{power_bonus} power, +{defense_bonus} defense)"
        )
        
        # Calculate vault depth for equipment
        vault_depth = self.dungeon_level + 2
        
        for _ in range(elite_monster_count):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            
            # Check if tile is free
            if not any([e for e in entities if e.x == x and e.y == y]):
                # Select monster type from theme's monster table
                monster_choice = random_choice_from_dict(monster_chances)
                monster = entity_factory.create_monster(monster_choice, x, y)
                
                if monster and monster.fighter:
                    # Apply elite bonuses from theme
                    monster.fighter.base_max_hp = int(monster.fighter.base_max_hp * hp_multiplier)
                    monster.fighter.hp = monster.fighter.max_hp  # Heal to new max
                    monster.fighter.base_power += power_bonus
                    monster.fighter.base_defense += defense_bonus
                    
                    # Visual indication: append (Elite) to name
                    monster.name = f"{monster.name} (Elite)"
                    
                    # Spawn equipment on elite monster
                    from components.monster_equipment import spawn_equipment_on_monster
                    spawn_equipment_on_monster(monster, vault_depth)
                    
                    entities.append(monster)
                    invalidate_entity_cache("entity_added_vault_monster")
                    logger.debug(f"Spawned elite {monster.name} at ({x}, {y})")
    
    def _spawn_vault_loot(self, room, entities, vault_theme=None):
        """Spawn guaranteed loot in vault room using theme configuration.
        
        Uses theme's chest count, quality, and bonus items configuration.
        
        Args:
            room (Rect): The vault room
            entities (list): List of entities on the map
            vault_theme (dict): Theme configuration with chest_count, chest_quality, bonus_items
        """
        from config.entity_factory import get_entity_factory
        entity_factory = get_entity_factory()
        
        # Get chest count from theme
        if vault_theme and 'chest_count' in vault_theme:
            chest_config = vault_theme['chest_count']
            num_chests = randint(chest_config.get('min', 2), chest_config.get('max', 3))
        else:
            num_chests = randint(2, 3)
        
        # Build weighted quality table from theme
        quality_weights = []
        if vault_theme and 'chest_quality' in vault_theme:
            for quality_entry in vault_theme['chest_quality']:
                quality_weights.append((quality_entry['quality'], quality_entry['weight']))
        else:
            # Default quality distribution
            quality_weights = [('rare', 70), ('legendary', 30)]
        
        theme_name = vault_theme.get('name', 'vault') if vault_theme else 'vault'
        logger.debug(f"Spawning {num_chests} chests in {theme_name}")
        
        # Spawn chests
        for _ in range(num_chests):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            
            # Check if tile is free
            if not any([e for e in entities if e.x == x and e.y == y]):
                # Select quality using weighted random
                total_weight = sum(weight for _, weight in quality_weights)
                roll = random() * total_weight
                cumulative = 0
                quality = 'rare'  # Default
                
                for q, weight in quality_weights:
                    cumulative += weight
                    if roll <= cumulative:
                        quality = q
                        break
                
                # Choose chest type based on quality
                if quality == 'legendary':
                    chest_type = 'golden_chest'
                elif quality == 'rare':
                    chest_type = choice(['golden_chest', 'chest'])
                else:
                    chest_type = 'chest'
                
                chest = entity_factory.create_chest(chest_type, x, y, loot_quality=quality)
                if chest:
                    entities.append(chest)
                    logger.debug(f"Spawned {chest_type} ({quality}) at ({x}, {y})")
        
        # Spawn bonus items on floor
        if vault_theme and 'bonus_items' in vault_theme:
            bonus_config = vault_theme['bonus_items']
            num_items = randint(bonus_config.get('min', 1), bonus_config.get('max', 2))
        else:
            num_items = randint(1, 2)
        
        for _ in range(num_items):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            
            # Check if tile is free
            if not any([e for e in entities if e.x == x and e.y == y]):
                # Use a simple selection of useful items for vault loot
                item_choices = ['healing_potion', 'lightning_scroll', 'fireball_scroll', 
                               'speed_potion', 'teleport_scroll', 'identify_scroll']
                item_type = choice(item_choices)
                
                # Try to create the item
                item = entity_factory.create_spell_item(item_type, x, y)
                if item:
                    entities.append(item)
                    logger.debug(f"Spawned bonus item {item.name} at ({x}, {y})")
    
    def is_blocked(self, x, y):
        """Check if a tile is blocked for movement.

        Args:
            x (int): X coordinate to check
            y (int): Y coordinate to check

        Returns:
            bool: True if the tile is blocked, False otherwise
        """
        """Function to determine if a tile is blocked"""
        if self.tiles[x][y].blocked:
            return True

        return False

    def next_floor(self, player, message_log, constants):
        """Generate the next dungeon floor.

        Increases dungeon level, heals the player, and generates a new map.

        Args:
            player (Entity): Player entity
            message_log (MessageLog): Game message log
            constants (dict): Game configuration constants

        Returns:
            list: New entities list for the floor
        """
        self.dungeon_level += 1
        entities = [player]

        # Check for level template overrides that might change map dimensions
        template_registry = get_level_template_registry()
        level_override = template_registry.get_level_override(self.dungeon_level)
        
        # Get map dimensions (with potential overrides)
        map_width = constants["map_width"]
        map_height = constants["map_height"]
        
        if level_override and level_override.has_parameters():
            params = level_override.parameters
            if params.map_width is not None:
                map_width = params.map_width
                logger.info(f"Level {self.dungeon_level}: Overriding map_width = {map_width}")
            if params.map_height is not None:
                map_height = params.map_height
                logger.info(f"Level {self.dungeon_level}: Overriding map_height = {map_height}")
        
        # Update map dimensions before reinitializing tiles
        self.width = map_width
        self.height = map_height
        
        self.tiles = self.initialize_tiles()
        self.make_map(
            constants["max_rooms"],
            constants["room_min_size"],
            constants["room_max_size"],
            map_width,
            map_height,
            player,
            entities,
        )

        player.fighter.heal(player.fighter.max_hp // 2)

        message_log.add_message(
            MB.custom(
                "You take a moment to rest, and recover your strength.", (159, 63, 255)
            )
        )

        return entities
    
    def place_guaranteed_spawns(self, rooms, entities):
        """Place guaranteed spawns from level templates.
        
        Checks if the current dungeon level has guaranteed spawns configured
        in the level template registry. If so, places those entities according
        to the configured mode ('additional' or 'replace').
        
        Args:
            rooms (list): List of Rect objects representing rooms
            entities (list): List to add new entities to
        """
        if not rooms:
            logger.warning("No rooms available for guaranteed spawns")
            return
            
        # Get level template registry
        template_registry = get_level_template_registry()
        level_override = template_registry.get_level_override(self.dungeon_level)
        
        if not level_override:
            # No override configured for this level
            return
            
        logger.info(
            f"Applying guaranteed spawns for level {self.dungeon_level} "
            f"(mode: {level_override.mode})"
        )
        
        # If mode is 'replace', clear existing entities (except player and stairs)
        if level_override.mode == 'replace':
            original_count = len(entities)
            # Keep only player and stairs
            entities[:] = [
                e for e in entities 
                if e.name == 'Player' or (hasattr(e, 'stairs') and e.stairs)
            ]
            removed_count = original_count - len(entities)
            logger.info(f"Replaced {removed_count} random spawns with guaranteed spawns")
            
        entity_factory = get_entity_factory()
        spawned_count = 0
        failed_count = 0
        
        # Place guaranteed monsters
        for spawn in level_override.guaranteed_monsters:
            spawn_count = spawn.get_random_count()
            for i in range(spawn_count):
                x, y = self._find_random_unoccupied_position(rooms, entities)
                if x is None:
                    logger.warning(
                        f"Could not find unoccupied position for {spawn.entity_type}, "
                        f"spawned {i}/{spawn_count}"
                    )
                    failed_count += 1
                    break
                    
                monster = entity_factory.create_monster(spawn.entity_type, x, y)
                if monster:
                    # Try to spawn equipment on the monster
                    from components.monster_equipment import spawn_equipment_on_monster
                    spawn_equipment_on_monster(monster, self.dungeon_level)
                    
                    entities.append(monster)
                    invalidate_entity_cache("guaranteed_spawn_monster")
                    spawned_count += 1
                else:
                    logger.warning(f"Failed to create monster: {spawn.entity_type}")
                    failed_count += 1
                    
        # Place guaranteed items (spells/potions)
        for spawn in level_override.guaranteed_items:
            spawn_count = spawn.get_random_count()
            for i in range(spawn_count):
                x, y = self._find_random_unoccupied_position(rooms, entities)
                if x is None:
                    logger.warning(
                        f"Could not find unoccupied position for {spawn.entity_type}, "
                        f"spawned {i}/{spawn_count}"
                    )
                    failed_count += 1
                    break
                    
                # Try to create item using smart fallback (supports all item types)
                item = entity_factory.create_weapon(spawn.entity_type, x, y)
                if not item:
                    item = entity_factory.create_armor(spawn.entity_type, x, y)
                if not item:
                    item = entity_factory.create_ring(spawn.entity_type, x, y)
                if not item:
                    item = entity_factory.create_spell_item(spawn.entity_type, x, y)
                if not item:
                    item = entity_factory.create_wand(spawn.entity_type, x, y, self.dungeon_level)
                
                if item:
                    entities.append(item)
                    invalidate_entity_cache("guaranteed_spawn_item")
                    spawned_count += 1
                else:
                    logger.warning(f"Failed to create guaranteed item: {spawn.entity_type} (not found in any category)")
                    failed_count += 1
                    
        # Place guaranteed equipment (weapons/armor)
        for spawn in level_override.guaranteed_equipment:
            spawn_count = spawn.get_random_count()
            for i in range(spawn_count):
                x, y = self._find_random_unoccupied_position(rooms, entities)
                if x is None:
                    logger.warning(
                        f"Could not find unoccupied position for {spawn.entity_type}, "
                        f"spawned {i}/{spawn_count}"
                    )
                    failed_count += 1
                    break
                    
                # Try to create equipment (try weapon first, then armor)
                equipment = entity_factory.create_weapon(spawn.entity_type, x, y)
                if not equipment:
                    equipment = entity_factory.create_armor(spawn.entity_type, x, y)
                    
                if equipment:
                    entities.append(equipment)
                    invalidate_entity_cache("guaranteed_spawn_equipment")
                    spawned_count += 1
                else:
                    logger.warning(f"Failed to create equipment: {spawn.entity_type}")
                    failed_count += 1
        
        # Place guaranteed map_features (chests, signposts, etc.)
        for spawn in level_override.guaranteed_map_features:
            spawn_count = spawn.get_random_count()
            for i in range(spawn_count):
                x, y = self._find_random_unoccupied_position(rooms, entities)
                if x is None:
                    logger.warning(
                        f"Could not find unoccupied position for {spawn.entity_type}, "
                        f"spawned {i}/{spawn_count}"
                    )
                    failed_count += 1
                    break
                
                # Try to create chest or signpost based on type
                # Check if it's a chest type or signpost type
                if 'chest' in spawn.entity_type.lower():
                    map_feature = entity_factory.create_chest(spawn.entity_type, x, y)
                else:
                    # Assume it's a signpost
                    map_feature = entity_factory.create_signpost(spawn.entity_type, x, y, depth=self.dungeon_level)
                
                if map_feature:
                    entities.append(map_feature)
                    invalidate_entity_cache("guaranteed_spawn_map_feature")
                    spawned_count += 1
                else:
                    logger.warning(f"Failed to create map feature: {spawn.entity_type}")
                    failed_count += 1
                    
        logger.info(
            f"Guaranteed spawns complete: {spawned_count} placed, {failed_count} failed"
        )
        
    def _find_random_unoccupied_position(self, rooms, entities, max_attempts=50):
        """Find a random unoccupied position in the given rooms.
        
        Args:
            rooms (list): List of Rect objects to search
            entities (list): List of existing entities to avoid
            max_attempts (int): Maximum number of random placement attempts
            
        Returns:
            tuple: (x, y) coordinates, or (None, None) if no position found
        """
        for attempt in range(max_attempts):
            # Pick a random room
            room = rooms[randint(0, len(rooms) - 1)]
            
            # Pick a random position in that room
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            
            # Check if position is unoccupied
            if not any(entity.x == x and entity.y == y for entity in entities):
                return (x, y)
                
        # Could not find a position after max_attempts
        return (None, None)
    
    def place_special_rooms(self, rooms, entities):
        """Place special themed rooms with guaranteed spawns (Tier 2).
        
        Selects rooms based on placement strategy and populates them with
        configured entities.
        
        Args:
            rooms (list): List of Rect objects representing generated rooms
            entities (list): List to add new entities to
        """
        if not rooms:
            logger.warning("No rooms available for special rooms")
            return
            
        # Get level template registry
        template_registry = get_level_template_registry()
        level_override = template_registry.get_level_override(self.dungeon_level)
        
        if not level_override or not level_override.has_special_rooms():
            # No special rooms configured for this level
            return
            
        logger.info(
            f"Placing {len(level_override.special_rooms)} special room type(s) "
            f"for level {self.dungeon_level}"
        )
        
        # Track which rooms have been used for special rooms
        used_rooms = set()
        
        for special_room in level_override.special_rooms:
            # Select rooms for this special room type
            selected_rooms = self._select_rooms_for_special_type(
                rooms, special_room, used_rooms
            )
            
            if not selected_rooms:
                logger.warning(
                    f"Could not find suitable rooms for special room type "
                    f"'{special_room.room_type}'"
                )
                continue
                
            # Populate each selected room with guaranteed spawns
            for room in selected_rooms:
                self._populate_special_room(room, special_room, entities)
                used_rooms.add(id(room))  # Mark room as used
                
            logger.info(
                f"Created {len(selected_rooms)} '{special_room.room_type}' room(s)"
            )
    
    def _select_rooms_for_special_type(self, rooms, special_room, used_rooms):
        """Select rooms for a special room type based on placement strategy.
        
        Args:
            rooms (list): All available rooms
            special_room (SpecialRoom): Special room configuration
            used_rooms (set): Set of room IDs already used
            
        Returns:
            list: Selected rooms (may be empty)
        """
        # Filter out already-used rooms
        available_rooms = [r for r in rooms if id(r) not in used_rooms]
        
        if not available_rooms:
            return []
            
        # Filter by minimum size requirement
        if special_room.min_room_size is not None:
            available_rooms = [
                r for r in available_rooms 
                if self._get_room_size(r) >= special_room.min_room_size
            ]
            
        if not available_rooms:
            logger.warning(
                f"No rooms meet min_room_size={special_room.min_room_size} "
                f"for '{special_room.room_type}'"
            )
            return []
            
        # Apply placement strategy
        if special_room.placement == "largest":
            # Sort by size descending and take the count largest
            available_rooms.sort(key=self._get_room_size, reverse=True)
        elif special_room.placement == "smallest":
            # Sort by size ascending and take the count smallest
            available_rooms.sort(key=self._get_room_size)
        elif special_room.placement == "random":
            # Shuffle for random selection
            from random import shuffle
            shuffle(available_rooms)
        else:
            logger.warning(
                f"Unknown placement strategy '{special_room.placement}', "
                f"using random"
            )
            from random import shuffle
            shuffle(available_rooms)
            
        # Return up to 'count' rooms
        return available_rooms[:special_room.count]
    
    def _get_room_size(self, room):
        """Get the size (area) of a room.
        
        Args:
            room (Rect): Room to measure
            
        Returns:
            int: Area of the room (width * height)
        """
        width = room.x2 - room.x1
        height = room.y2 - room.y1
        return width * height
    
    def _populate_special_room(self, room, special_room, entities):
        """Populate a special room with guaranteed spawns.
        
        Args:
            room (Rect): Room to populate
            special_room (SpecialRoom): Special room configuration
            entities (list): List to add new entities to
        """
        logger.info(
            f"Populating '{special_room.room_type}' at "
            f"({room.center()[0]}, {room.center()[1]})"
        )
        
        entity_factory = get_entity_factory()
        spawned_count = 0
        failed_count = 0
        
        # Place guaranteed monsters
        for spawn in special_room.guaranteed_monsters:
            spawn_count = spawn.get_random_count()
            for i in range(spawn_count):
                # Find position within THIS specific room
                x, y = self._find_random_position_in_room(room, entities)
                if x is None:
                    logger.warning(
                        f"Could not find position in special room for "
                        f"{spawn.entity_type}, spawned {i}/{spawn_count}"
                    )
                    failed_count += 1
                    break
                    
                monster = entity_factory.create_monster(spawn.entity_type, x, y)
                if monster:
                    from components.monster_equipment import spawn_equipment_on_monster
                    spawn_equipment_on_monster(monster, self.dungeon_level)
                    entities.append(monster)
                    invalidate_entity_cache("special_room_monster")
                    spawned_count += 1
                else:
                    logger.warning(f"Failed to create monster: {spawn.entity_type}")
                    failed_count += 1
                    
        # Place guaranteed items
        for spawn in special_room.guaranteed_items:
            spawn_count = spawn.get_random_count()
            for i in range(spawn_count):
                x, y = self._find_random_position_in_room(room, entities)
                if x is None:
                    logger.warning(
                        f"Could not find position in special room for "
                        f"{spawn.entity_type}, spawned {i}/{spawn_count}"
                    )
                    failed_count += 1
                    break
                    
                # Try to create item using smart fallback (supports all item types)
                item = entity_factory.create_weapon(spawn.entity_type, x, y)
                if not item:
                    item = entity_factory.create_armor(spawn.entity_type, x, y)
                if not item:
                    item = entity_factory.create_ring(spawn.entity_type, x, y)
                if not item:
                    item = entity_factory.create_spell_item(spawn.entity_type, x, y)
                if not item:
                    item = entity_factory.create_wand(spawn.entity_type, x, y, self.dungeon_level)
                
                if item:
                    entities.append(item)
                    invalidate_entity_cache("special_room_item")
                    spawned_count += 1
                else:
                    logger.warning(f"Failed to create special room item: {spawn.entity_type} (not found in any category)")
                    failed_count += 1
                    
        # Place guaranteed equipment
        for spawn in special_room.guaranteed_equipment:
            spawn_count = spawn.get_random_count()
            for i in range(spawn_count):
                x, y = self._find_random_position_in_room(room, entities)
                if x is None:
                    logger.warning(
                        f"Could not find position in special room for "
                        f"{spawn.entity_type}, spawned {i}/{spawn_count}"
                    )
                    failed_count += 1
                    break
                    
                equipment = entity_factory.create_weapon(spawn.entity_type, x, y)
                if not equipment:
                    equipment = entity_factory.create_armor(spawn.entity_type, x, y)
                    
                if equipment:
                    entities.append(equipment)
                    invalidate_entity_cache("special_room_equipment")
                    spawned_count += 1
                else:
                    logger.warning(f"Failed to create equipment: {spawn.entity_type}")
                    failed_count += 1
                    
        logger.info(
            f"Special room '{special_room.room_type}': "
            f"{spawned_count} entities placed, {failed_count} failed"
        )
    
    def _find_random_position_in_room(self, room, entities, max_attempts=50):
        """Find a random unoccupied position within a specific room.
        
        Args:
            room (Rect): Room to search within
            entities (list): Existing entities to avoid
            max_attempts (int): Maximum placement attempts
            
        Returns:
            tuple: (x, y) coordinates, or (None, None) if no position found
        """
        for attempt in range(max_attempts):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            
            # Check if position is unoccupied
            if not any(entity.x == x and entity.y == y for entity in entities):
                return (x, y)
                
        # Could not find a position after max_attempts
        return (None, None)
