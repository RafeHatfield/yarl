"""Game map generation and management.

This module contains the GameMap class which handles dungeon generation,
tile management, entity placement, and map navigation. It uses BSP-style
room generation with connecting tunnels.
"""

from random import randint

from components.ai import BasicMonster
from components.equippable import Equippable
from components.fighter import Fighter
from components.item import Item
from config.entity_factory import get_entity_factory
from entity import Entity
from entity_sorting_cache import invalidate_entity_cache
from equipment_slots import EquipmentSlots
from game_messages import Message
from item_functions import cast_confuse, cast_fireball, cast_lightning, heal, enhance_weapon, enhance_armor
from map_objects.rectangle import Rect
from map_objects.tile import Tile
from random_utils import from_dungeon_level, random_choice_from_dict
from render_functions import RenderOrder
from stairs import Stairs
from config.testing_config import get_testing_config


class GameMap:
    """Manages the game map including tiles, rooms, and entity placement.

    Handles dungeon generation using rectangular rooms connected by tunnels,
    entity spawning based on dungeon level, and map navigation.

    Attributes:
        width (int): Map width in tiles
        height (int): Map height in tiles
        tiles (list): 2D array of Tile objects
        dungeon_level (int): Current dungeon level for scaling difficulty
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

        Args:
            max_rooms (int): Maximum number of rooms to generate
            room_min_size (int): Minimum room dimension
            room_max_size (int): Maximum room dimension
            map_width (int): Map width in tiles
            map_height (int): Map height in tiles
            player (Entity): Player entity to place
            entities (list): List to populate with generated entities
        """
        # Create two rooms for demonstration purposes
        # room1 = Rect(20, 15, 10, 15)
        # room2 = Rect(35, 15, 10, 15)

        # self.create_room(room1)
        # self.create_room(room2)

        # self.create_h_tunnel(25, 40, 23)
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
                    player.x = new_x
                    player.y = new_y
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
        modified by testing configuration.

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
        
        # Get a random number of monsters and items
        number_of_monsters = randint(0, max_monsters_per_room)
        number_of_items = randint(0, max_items_per_room)

        monster_chances = {
            "orc": 80,
            "troll": from_dungeon_level(
                [[15, 3], [30, 5], [60, 7]], self.dungeon_level
            ),
        }

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
                
                # base stats for items
                if item_choice == "healing_potion":
                    item_component = Item(use_function=heal, amount=40)
                    item = Entity(
                        x,
                        y,
                        "!",
                        (127, 0, 255),
                        "Healing Potion",
                        render_order=RenderOrder.ITEM,
                        item=item_component,
                    )
                elif item_choice == "sword":
                    item = entity_factory.create_weapon("sword", x, y)
                elif item_choice == "shield":
                    item = entity_factory.create_armor("shield", x, y)
                elif item_choice == "fireball_scroll":
                    item_component = Item(
                        use_function=cast_fireball,
                        targeting=True,
                        targeting_message=Message(
                            "Left-click a target tile for the fireball, or right-click to cancel.",
                            (63, 255, 255),
                        ),
                        damage=25,
                        radius=3,
                    )
                    item = Entity(
                        x,
                        y,
                        "#",
                        (255, 0, 0),
                        "Fireball Scroll",
                        render_order=RenderOrder.ITEM,
                        item=item_component,
                    )
                elif item_choice == "confusion_scroll":
                    item_component = Item(
                        use_function=cast_confuse,
                        targeting=True,
                        targeting_message=Message(
                            "Left-click an enemy to confuse it, or right-click to cancel.",
                            (63, 255, 255),
                        ),
                    )
                    item = Entity(
                        x,
                        y,
                        "#",
                        (255, 63, 159),
                        "Confusion Scroll",
                        render_order=RenderOrder.ITEM,
                        item=item_component,
                    )
                elif item_choice == "enhance_weapon_scroll":
                    item_component = Item(
                        use_function=enhance_weapon, min_bonus=1, max_bonus=2
                    )
                    item = Entity(
                        x,
                        y,
                        "#",
                        (255, 127, 0),
                        "Weapon Enhancement Scroll",
                        render_order=RenderOrder.ITEM,
                        item=item_component,
                    )
                elif item_choice == "enhance_armor_scroll":
                    item_component = Item(
                        use_function=enhance_armor, min_bonus=1, max_bonus=1
                    )
                    item = Entity(
                        x,
                        y,
                        "#",
                        (127, 127, 255),
                        "Armor Enhancement Scroll",
                        render_order=RenderOrder.ITEM,
                        item=item_component,
                    )
                else:
                    item_component = Item(
                        use_function=cast_lightning, damage=40, maximum_range=5
                    )
                    item = Entity(
                        x,
                        y,
                        "#",
                        (255, 255, 0),
                        "Lightning Scroll",
                        render_order=RenderOrder.ITEM,
                        item=item_component,
                    )

                entities.append(item)
                # Invalidate entity sorting cache when new entities are added
                invalidate_entity_cache("entity_added_item")

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

        self.tiles = self.initialize_tiles()
        self.make_map(
            constants["max_rooms"],
            constants["room_min_size"],
            constants["room_max_size"],
            constants["map_width"],
            constants["map_height"],
            player,
            entities,
        )

        player.fighter.heal(player.fighter.max_hp // 2)

        message_log.add_message(
            Message(
                "You take a moment to rest, and recover your strength.", (159, 63, 255)
            )
        )

        return entities
