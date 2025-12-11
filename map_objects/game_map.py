"""Game map generation and management.

This module contains the GameMap class which handles dungeon generation,
tile management, entity placement, and map navigation. It uses BSP-style
room generation with connecting tunnels.
"""

from random import randint, random, choice

from components.ai import BasicMonster
from components.equippable import Equippable
from components.fighter import Fighter
from components.component_registry import ComponentType
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
from logger_config import get_logger

# ETP (Effective Threat Points) budgeting system
from balance.etp import (
    get_monster_etp,
    get_room_etp_budget,
    get_band_for_depth,
    check_room_budget,
    log_room_etp_summary,
    initialize_encounter_budget_engine,
    can_spawn_monster_in_room,
    get_spawn_restriction_reason,
    is_boss_monster,
    is_miniboss_monster,
)

# Loot pity system (prevents long stretches without healing, panic items, and upgrades)
from balance.pity import (
    check_and_apply_pity,
    reset_pity_state,
    get_pity_state,
    PityResult,
)
from balance.loot_tags import (
    get_loot_tags,
    get_items_by_category,
    get_items_for_band,
)
from services.spawn_service import (
    EncounterBudget,
    SpawnContext,
    SpawnService,
)

logger = get_logger(__name__)

# Initialize ETP values on module load
try:
    initialize_encounter_budget_engine()
except Exception as e:
    logger.warning(f"Failed to initialize ETP engine: {e}")


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
        
        # Track corridor connections for door placement
        self.corridor_connections = []  # List of (room_a, room_b, tunnel_type, start, end)
        
        # Track generated rooms for ETP analysis and debugging
        # Each room is a dict with 'rect' (Rect object) and 'metadata' (RoomMetadata or None)
        self.rooms = []  # List of room dicts: {'rect': Rect, 'metadata': RoomMetadata}

    def initialize_tiles(self):
        """Initialize the map with blocked wall tiles.

        Returns:
            list: 2D array of Tile objects, all initially blocked
        """
        """Function initializing the tiles in the map"""
        tiles = [[Tile(True) for y in range(self.height)] for x in range(self.width)]

        return tiles

    def get_walkable_stats(self):
        """Calculate walkable tile statistics for the map.

        Returns:
            tuple: (walkable_count, total_tiles, walkable_percent)
                - walkable_count: Number of non-blocked tiles
                - total_tiles: Total number of tiles on map
                - walkable_percent: Fraction of map that is walkable (0.0 to 1.0)
        """
        walkable_count = 0
        for x in range(self.width):
            for y in range(self.height):
                if not self.tiles[x][y].blocked:
                    walkable_count += 1

        total_tiles = self.width * self.height
        walkable_percent = walkable_count / total_tiles if total_tiles else 0.0
        return walkable_count, total_tiles, walkable_percent

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
        # CRITICAL: Clear corridor connections from previous floor
        # Without this, connections accumulate across all floors!
        self.corridor_connections = []
        
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
            for room_entry in rooms:
                other_room = room_entry['rect']
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
                    prev_room = rooms[num_rooms - 1]['rect']
                    (prev_x, prev_y) = prev_room.center()

                    # flip a coin (random number that is either 0 or 1)
                    if randint(0, 1) == 1:
                        # first move horizontally, then vertically
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                        # Track this connection for door placement
                        self.corridor_connections.append({
                            'room_a': prev_room,
                            'room_b': new_room,
                            'h_corridor': (min(prev_x, new_x), max(prev_x, new_x), prev_y),
                            'v_corridor': (prev_y, new_y, new_x)
                        })
                    else:
                        # first move vertically, then horizontally
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)
                        # Track this connection for door placement
                        self.corridor_connections.append({
                            'room_a': prev_room,
                            'room_b': new_room,
                            'v_corridor': (min(prev_y, new_y), max(prev_y, new_y), prev_x),
                            'h_corridor': (prev_x, new_x, new_y)
                        })

                # Place entities in this room
                # If this will be the last room, exclude the center (where stairs will go)
                exclude_coords = None
                if num_rooms + 1 >= max_rooms:
                    # This will be the last room - stairs will be at center
                    exclude_coords = (new_x, new_y)
                    logger.debug(f"Last room detected - excluding stairs location ({new_x}, {new_y}) from entity spawns")
                
                # Create room metadata first for pity system integration
                from config.level_template_registry import RoomMetadata
                room_metadata = RoomMetadata()  # Default: normal room
                
                self.place_entities(new_room, entities, exclude_coords=exclude_coords, room_metadata=room_metadata)
                
                # Place exploration features (chests, signposts)
                self.place_exploration_features(new_room, entities)

                # Append the new room to the list with its metadata
                rooms.append({
                    'rect': new_room,
                    'metadata': room_metadata
                })
                num_rooms += 1

        # Store rooms list for ETP analysis and debugging
        self.rooms = rooms
        
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
        
        # VICTORY CONDITION: Spawn Ruby Heart on level 25!
        if self.dungeon_level == 25:
            from config.entity_factory import get_entity_factory
            factory = get_entity_factory()
            
            # Place Ruby Heart in center of the last room (where stairs are)
            # Offset slightly so it doesn't overlap with stairs
            heart_x = center_of_last_room_x + 1
            heart_y = center_of_last_room_y
            
            ruby_heart = factory.create_unique_item('ruby_heart', heart_x, heart_y)
            if ruby_heart:
                entities.append(ruby_heart)
                # Logger already imported at module level (line 28)
                logger.info(f"=== RUBY HEART SPAWNED at ({heart_x}, {heart_y}) ===")
            
            # PHASE 5: Create secret room with Crimson Ritual Codex
            # Hidden room accessed via secret door (becomes visible after heart pickup)
            self._create_secret_ritual_room(rooms, entities)
        
        # PHASE 3: Spawn Ghost Guide on levels 5, 10, 15, 20
        if self.dungeon_level in [5, 10, 15, 20]:
            self._spawn_ghost_guide(rooms, entities)
        
        # Apply special rooms from level templates (Tier 2)
        self.place_special_rooms(rooms, entities)
        
        # Apply guaranteed spawns from level templates (if configured)
        self.place_guaranteed_spawns(rooms, entities)
        
        # Designate some rooms as treasure vaults (Phase 1: Simple Vaults)
        self.designate_vaults(rooms, entities)
        
        # Place secret rooms adjacent to corridors (Tier 2)
        self.place_secret_rooms(rooms, entities)
        
        # Place doors in corridors based on door_rules (Tier 2)
        self.place_corridor_doors(entities)
        
        # Place traps based on trap_rules (Tier 2)
        self.place_traps(rooms, entities)
        
        # Place secret doors between rooms (15% chance per level)
        self.place_secret_doors_between_rooms(rooms)
        
        # VALIDATION: Ensure locked doors have keys available
        self._validate_and_guarantee_locked_door_keys(entities, rooms)
        
        # VALIDATION: Ensure secret doors are only on wall tiles
        self._validate_secret_door_placement(entities)

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
    
    def place_secret_rooms(self, rooms, entities):
        """Place secret rooms adjacent to existing corridors.
        
        Secret rooms are carved from solid walls adjacent to existing corridors or dead ends.
        They are connected via secret doors and marked with hint tiles outside.
        
        Called after all base rooms and corridors are generated but before other features.
        
        Args:
            rooms (list): List of existing Rect rooms
            entities (list): List to add entities (hints, etc.) to
        """
        # Get level template registry
        template_registry = get_level_template_registry()
        level_override = template_registry.get_level_override(self.dungeon_level)
        
        # Get secret_rooms configuration
        secret_rooms_config = None
        if level_override and level_override.secret_rooms:
            secret_rooms_config = level_override.secret_rooms
        
        if not secret_rooms_config or secret_rooms_config.target_per_floor <= 0:
            logger.debug("No secret rooms configured for this level, skipping secret room placement")
            return
        
        created_count = 0
        for attempt in range(secret_rooms_config.target_per_floor * 3):  # Allow failed attempts
            if created_count >= secret_rooms_config.target_per_floor:
                break
            
            if self._try_create_secret_room(rooms, entities, secret_rooms_config):
                created_count += 1
        
        logger.info(f"Created {created_count}/{secret_rooms_config.target_per_floor} secret rooms on level {self.dungeon_level}")
    
    def _try_create_secret_room(self, rooms, entities, config):
        """Attempt to create a single secret room.
        
        Args:
            rooms (list): List of existing rooms
            entities (list): Entity list for hints
            config (SecretRooms): Configuration for secret rooms
            
        Returns:
            bool: True if successfully created, False otherwise
        """
        from random import randint, choice, random
        
        # Find valid position adjacent to a corridor or dead end
        # Try multiple times to find suitable location
        for _ in range(20):
            # Pick a random edge tile that's solid and adjacent to a corridor
            x = randint(1, self.width - 2)
            y = randint(1, self.height - 2)
            
            # Check if this is solid (wall)
            if not self.tiles[x][y].blocked:
                continue
            
            # Check if adjacent to at least one corridor/room
            adjacent_to_corridor = False
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if not self.tiles[nx][ny].blocked:
                        adjacent_to_corridor = True
                        break
            
            if not adjacent_to_corridor:
                continue
            
            # Try to carve secret room from this position
            room_size = randint(config.min_room_size, config.min_room_size + 3)
            
            # Find space to carve (try in all directions)
            carve_x, carve_y = None, None
            for dx in [-1, 1]:
                test_x = x + (dx * (room_size + 1))
                if 1 <= test_x < self.width - room_size:
                    # Check if this area is all solid
                    all_solid = True
                    for cx in range(test_x, test_x + room_size):
                        for cy in range(y - room_size // 2, y + room_size // 2):
                            if 0 <= cx < self.width and 0 <= cy < self.height:
                                if not self.tiles[cx][cy].blocked:
                                    all_solid = False
                                    break
                        if not all_solid:
                            break
                    
                    if all_solid:
                        carve_x, carve_y = test_x, y - room_size // 2
                        break
            
            if carve_x is None:
                continue
            
            # Carve the secret room
            secret_room = Rect(carve_x, carve_y, room_size, room_size)
            self.create_room(secret_room)
            
            # Create secret door at the wall
            secret_door_x, secret_door_y = x, y
            
            # Create secret door entity with default door_rules.secret behavior
            door_entity = self._create_secret_door_at(secret_door_x, secret_door_y, entities)
            if door_entity:
                entities.append(door_entity)
                logger.debug(f"Created secret door at ({secret_door_x}, {secret_door_y})")
            
            # Place hint tile marker outside the wall
            hint_tile_x, hint_tile_y = x - (1 if carve_x < x else -1), y
            if 0 <= hint_tile_x < self.width and 0 <= hint_tile_y < self.height:
                # Store hint information on the tile for rendering
                hint_tile = self.tiles[hint_tile_x][hint_tile_y]
                if not hasattr(hint_tile, 'hint_marker'):
                    hint_tile.hint_marker = config.discovery.ambient_hint
                    hint_tile.hint_discoverable = config.discovery.search_action
                    logger.debug(f"Placed hint marker '{config.discovery.ambient_hint}' at ({hint_tile_x}, {hint_tile_y})")
            
            return True
        
        return False
    
    def _create_secret_door_at(self, x, y, entities):
        """Create a secret door entity at the specified position.
        
        Args:
            x, y: Position for the secret door
            entities: List to check for collisions
            
        Returns:
            Door entity or None
        """
        from components.door import Door
        from config.entity_factory import get_entity_factory
        
        # Don't place if occupied
        if any(e.x == x and e.y == y for e in entities):
            return None
        
        factory = get_entity_factory()
        door_entity = factory.create_door("wooden_door", x, y)
        
        if not door_entity:
            return None
        
        # Create Door component and mark as secret
        door_component = Door()
        door_entity.door = door_component
        door_component.owner = door_entity
        
        # Mark as secret with standard discovery settings
        door_component.is_secret = True
        door_component.is_discovered = False
        door_component.search_dc = 12
        
        # Secret doors render as walls
        door_entity.char = '#'
        door_entity.color = (127, 127, 127)  # Wall-like gray
        
        return door_entity

    def place_corridor_doors(self, entities):
        """Place doors in corridors based on level template door_rules.
        
        This method is called after all corridors are created to place doors
        at corridor entrance points where they meet rooms.
        
        FIXED VERSION: Now places exactly ONE door per corridor connection at the
        junction point where the corridor meets room_a. No more scattered doors!
        
        Args:
            entities (list): List to add door entities to
        """
        # Get level template registry
        template_registry = get_level_template_registry()
        level_override = template_registry.get_level_override(self.dungeon_level)
        
        # Get door rules (level scope or per-connection defaults)
        door_rules = None
        if level_override and level_override.door_rules:
            door_rules = level_override.door_rules
        
        if not door_rules or door_rules.spawn_ratio <= 0:
            logger.debug("No door rules configured for this level, skipping door placement")
            return
        
        # VERIFICATION MARKER: This proves the new code is running
        print(f"╔═══════════════════════════════════════════════════════╗")
        print(f"║ DOOR PLACEMENT v2.0 - LEVEL {self.dungeon_level:3d}                    ║")
        print(f"║ Corridor connections: {len(self.corridor_connections):2d}                         ║")
        print(f"╚═══════════════════════════════════════════════════════╝")
        logger.info(f"[DOOR PLACEMENT v2.0] Placing doors for {len(self.corridor_connections)} corridor connections on level {self.dungeon_level}")
        
        # Place doors at corridor connections
        doors_placed = 0
        for connection in self.corridor_connections:
            before_count = len(entities)
            self._place_door_for_connection(connection, door_rules, entities)
            if len(entities) > before_count:
                doors_placed += 1
        
        print(f"║ Doors actually placed: {doors_placed:2d}                            ║")
        print(f"╚═══════════════════════════════════════════════════════╝")
    
    def _place_door_for_connection(self, connection: dict, door_rules, entities):
        """Place a door for a single corridor connection.
        
        Doors are placed ONLY at junction tiles where a corridor meets a room.
        A junction tile is where the corridor is adjacent to a room's perimeter.
        
        CONSTRAINT: Doors are only placed on 1-tile-wide corridors. Wider corridors
        are skipped to avoid placing ineffective single doors that don't block passage.
        
        Args:
            connection: Dictionary with 'room_a', 'room_b', corridor info
            door_rules: DoorRules configuration for this level
            entities: List to add door entity to
        """
        from random import random
        
        # Check spawn probability
        if random() > door_rules.spawn_ratio:
            return
        
        # Get the two rooms connected by this corridor
        room_a = connection['room_a']
        room_b = connection['room_b']
        
        door_pos = None
        corridor_direction = None  # 'horizontal' or 'vertical'
        
        # Process horizontal corridor if available
        # Place door at the junction closest to room_a (only ONE per connection)
        if 'h_corridor' in connection and not door_pos:
            h_x_min, h_x_max, h_y = connection['h_corridor']
            # NOTE: h_x_min might be > h_x_max if corridor goes right-to-left!
            # Always normalize to get true min/max
            h_x_actual_min = min(h_x_min, h_x_max)
            h_x_actual_max = max(h_x_min, h_x_max)
            
            # For horizontal corridor, find the junction point at room_a
            # Try room_a's right edge (x2) first
            if h_x_actual_min <= room_a.x2 <= h_x_actual_max:
                candidate = (room_a.x2, h_y)
                if self._is_valid_door_position(candidate[0], candidate[1]):
                    door_pos = candidate
                    corridor_direction = 'horizontal'
            # If not found, try room_a's left edge (x1)
            elif h_x_actual_min <= room_a.x1 <= h_x_actual_max:
                candidate = (room_a.x1, h_y)
                if self._is_valid_door_position(candidate[0], candidate[1]):
                    door_pos = candidate
                    corridor_direction = 'horizontal'
        
        # Process vertical corridor if available (and we haven't found a position yet)
        if 'v_corridor' in connection and not door_pos:
            v_y_min, v_y_max, v_x = connection['v_corridor']
            # NOTE: v_y_min might be > v_y_max if corridor goes bottom-to-top!
            # Always normalize to get true min/max
            v_y_actual_min = min(v_y_min, v_y_max)
            v_y_actual_max = max(v_y_min, v_y_max)
            
            # For vertical corridor, find the junction point at room_a
            # Try room_a's bottom edge (y2) first
            if v_y_actual_min <= room_a.y2 <= v_y_actual_max:
                candidate = (v_x, room_a.y2)
                if self._is_valid_door_position(candidate[0], candidate[1]):
                    door_pos = candidate
                    corridor_direction = 'vertical'
            # If not found, try room_a's top edge (y1)
            elif v_y_actual_min <= room_a.y1 <= v_y_actual_max:
                candidate = (v_x, room_a.y1)
                if self._is_valid_door_position(candidate[0], candidate[1]):
                    door_pos = candidate
                    corridor_direction = 'vertical'
        
        # Place the door if we found a valid position
        if not door_pos:
            logger.debug("No valid door junction position found for corridor connection")
            return
        
        # Check corridor width - only place doors on 1-tile-wide corridors
        corridor_width = self._get_corridor_width_at(door_pos[0], door_pos[1], corridor_direction)
        if corridor_width > 1:
            logger.debug(
                f"[DEBUG] Skipping door placement at ({door_pos[0]}, {door_pos[1]}) "
                f"because corridor width is {corridor_width} > 1"
            )
            return
        
        # Create door entity
        door_entity = self._create_door_entity(door_pos[0], door_pos[1], door_rules, entities)
        if door_entity:
            entities.append(door_entity)
            logger.debug(f"Placed door '{door_entity.name}' at ({door_pos[0]}, {door_pos[1]})")
    
    def _is_valid_door_position(self, x: int, y: int) -> bool:
        """Check if a position is valid for door placement.
        
        A valid door position must be:
        - Within map bounds
        - On a non-blocked (walkable) floor tile
        
        Args:
            x (int): X coordinate to check
            y (int): Y coordinate to check
            
        Returns:
            bool: True if position is valid for door placement, False otherwise
        """
        # Check bounds
        if not self.is_in_bounds(x, y):
            return False
        
        # Check if tile is walkable (not blocked)
        if self.tiles[x][y].blocked:
            return False
        
        return True
    
    def _get_corridor_width_at(self, x: int, y: int, direction: str) -> int:
        """Determine the width of a corridor at a given position.
        
        For a horizontal corridor (running left-right), width is the number of
        contiguous walkable floor tiles above/below the corridor at this x.
        For a vertical corridor (running up-down), width is the number of
        contiguous walkable floor tiles to the left/right at this y.
        
        Args:
            x (int): X coordinate of the corridor tile
            y (int): Y coordinate of the corridor tile
            direction (str): 'horizontal' or 'vertical' - the corridor orientation
            
        Returns:
            int: Number of walkable tiles perpendicular to the corridor direction.
                 Returns 1 for a typical 1-tile-wide corridor, 2+ for wider corridors.
        """
        if direction == 'horizontal':
            # For horizontal corridor, check tiles above and below (y-1, y+1)
            # Count contiguous walkable tiles at the same y across different x values
            width = 1  # The corridor tile itself
            
            # Check above (y - 1)
            if self.is_in_bounds(x, y - 1) and not self.tiles[x][y - 1].blocked:
                width += 1
            
            # Check below (y + 1)
            if self.is_in_bounds(x, y + 1) and not self.tiles[x][y + 1].blocked:
                width += 1
            
            return width
        
        elif direction == 'vertical':
            # For vertical corridor, check tiles left and right (x-1, x+1)
            # Count contiguous walkable tiles at the same x across different y values
            width = 1  # The corridor tile itself
            
            # Check left (x - 1)
            if self.is_in_bounds(x - 1, y) and not self.tiles[x - 1][y].blocked:
                width += 1
            
            # Check right (x + 1)
            if self.is_in_bounds(x + 1, y) and not self.tiles[x + 1][y].blocked:
                width += 1
            
            return width
        
        else:
            # Default to width 1 if direction is unknown
            logger.warning(f"Unknown corridor direction: {direction}")
            return 1
    
    def _create_door_entity(self, x: int, y: int, door_rules, entities):
        """Create a door entity at the specified position.
        
        Doors are placed at corridor connections based on door_rules configuration.
        The door style (e.g., 'wooden_door', 'iron_door') must be a valid entity ID
        from entities.yaml. Invalid door styles should be caught at level load time
        by the level template registry validator.
        
        Args:
            x, y: Position for the door
            door_rules: DoorRules configuration
            entities: List of existing entities (to check for collisions)
            
        Returns:
            Door entity, or None if creation failed
        """
        from random import random
        from components.door import Door
        from config.entity_factory import get_entity_factory
        
        # SAFETY: Ensure position is within bounds before creating entity
        if not self.is_in_bounds(x, y):
            logger.error(
                f"Cannot create door at ({x}, {y}): position is out of bounds "
                f"(map: {self.width}x{self.height})"
            )
            return None
        
        # Don't place if already occupied
        if any(e.x == x and e.y == y for e in entities):
            return None
        
        # Select door style using weighted random
        door_style = door_rules.get_random_style()
        
        # Create door entity
        factory = get_entity_factory()
        door_entity = factory.create_door(door_style, x, y)
        
        if not door_entity:
            # Note: Invalid door_style should have been caught at configuration load time.
            # If this warning appears, check that door_rules.styles[*].type matches a valid
            # door entity ID (e.g., 'wooden_door', 'iron_door', 'stone_door', etc.)
            logger.warning(
                f"Failed to create door with entity ID '{door_style}' at ({x}, {y}). "
                f"Verify that this door type is defined in entities.yaml 'map_features' section."
            )
            return None
        
        # Get or create Door component
        door_component = door_entity.get_component_optional(ComponentType.DOOR)
        if not door_component:
            door_component = Door()
            door_entity.door = door_component
            door_entity.components.add(ComponentType.DOOR, door_component)
            door_component.owner = door_entity
        
        # Apply locked state
        if door_rules.locked and random() < door_rules.locked.chance:
            door_component.is_locked = True
            door_component.key_tag = door_rules.locked.key_tag
            logger.debug(f"Door at ({x}, {y}) locked with key tag '{door_component.key_tag}'")
        
        # Apply secret state
        if door_rules.secret and random() < door_rules.secret.chance:
            door_component.is_secret = True
            door_component.is_discovered = False
            door_component.search_dc = door_rules.secret.search_dc
            # Secret doors appear as walls
            door_entity.char = '#'
            door_entity.color = (127, 127, 127)  # Wall-like gray
            logger.debug(f"Door at ({x}, {y}) is secret with DC {door_component.search_dc}")
        
        return door_entity
    
    def place_traps(self, rooms, entities):
        """Place traps in rooms based on level template trap_rules.
        
        Traps are placed at configurable density within rooms, respecting
        room type whitelists. Trap types are selected from configured trap_table
        with weighted random selection.
        
        Args:
            rooms (list): List of Rect room objects
            entities (list): List to add trap entities to
        """
        from components.trap import Trap
        from config.entity_factory import get_entity_factory
        
        # Get level template registry
        template_registry = get_level_template_registry()
        level_override = template_registry.get_level_override(self.dungeon_level)
        
        # Get trap rules (level scope takes precedence)
        trap_rules = None
        if level_override and level_override.trap_rules:
            trap_rules = level_override.trap_rules
        
        if not trap_rules or trap_rules.density <= 0:
            logger.debug("No trap rules configured for this level, skipping trap placement")
            return
        
        factory = get_entity_factory()
        
        # Place traps in each room
        for room_entry in rooms:
            room = room_entry['rect']
            self._place_traps_in_room(room, trap_rules, entities, factory, level_override)
    
    def _place_traps_in_room(self, room, trap_rules, entities, factory, level_override):
        """Place traps in a single room based on trap_rules.
        
        Args:
            room (Rect): Room to place traps in
            trap_rules: TrapRules configuration (level scope)
            entities (list): List to add trap entities to
            factory: EntityFactory for creating trap entities
            level_override: Level override config (for special room trap_rules)
        """
        from random import random
        
        # Check room type whitelist (for now, accept all rooms)
        # Future: special_room types could have room_type set and filter by whitelist
        
        # Iterate through room tiles and place traps based on density
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                # Check density probability for this tile
                if random() > trap_rules.density:
                    continue
                
                # Don't place trap if tile is occupied
                if any(e.x == x and e.y == y for e in entities):
                    continue
                
                # Don't place trap on blocked tiles
                if self.tiles[x][y].blocked:
                    continue
                
                # Select trap type using weighted random selection
                trap_type = trap_rules.get_random_trap()
                if not trap_type:
                    continue
                
                # Create trap entity
                trap_entity = factory.create_trap(trap_type, x, y)
                if trap_entity:
                    # Apply trap_rules detection settings to the trap component
                    if trap_entity.components.has(ComponentType.TRAP):
                        trap = trap_entity.components.get(ComponentType.TRAP)
                        trap.detectable = trap_rules.detection.detectable
                        trap.passive_detect_chance = trap_rules.detection.passive_chance
                        trap.reveal_tags = trap_rules.detection.reveal_on
                    
                    entities.append(trap_entity)
                    logger.debug(f"Placed {trap_type} at ({x}, {y})")

    def place_entities(self, room, entities, exclude_coords=None, encounter_budget=None, room_metadata=None):
        """Place monsters and items in a room based on dungeon level.

        Uses probability tables that scale with dungeon level to determine
        what entities to spawn and where to place them. Spawn rates can be
        modified by testing configuration or level template overrides (Tier 2).
        
        ETP Budgeting: If encounter_budget is specified (or from level template),
        monster spawning will respect the ETP budget, stopping when max is reached.
        
        Pity System: After items are spawned, checks pity counters and may spawn
        additional healing, panic, weapon, or armor items to prevent bad luck streaks.
        Only triggers in normal rooms (not boss/treasure/etc.).

        Args:
            room (Rect): Room to place entities in
            entities (list): List to add new entities to
            exclude_coords (tuple or list of tuples, optional): Coordinates (x, y) to avoid 
                when placing entities. Used to prevent items spawning on stairs.
            encounter_budget (EncounterBudget, optional): ETP budget for this room.
                If None, uses default band budget from ETP config.
            room_metadata (RoomMetadata, optional): Room role and flags for pity system.
                If None, assumes a normal room.
        """
        # Normalize exclude_coords to a list of tuples
        if exclude_coords is None:
            exclude_coords = []
        elif isinstance(exclude_coords, tuple):
            exclude_coords = [exclude_coords]
        config = get_testing_config()
        
        spawn_service = SpawnService(self.dungeon_level)
        
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
        
        # ─────────────────────────────────────────────────────────────────────
        # BAND-BASED DENSITY SCALING: Reduce loot flood in B1-B2
        # ─────────────────────────────────────────────────────────────────────
        band_str = get_band_for_depth(self.dungeon_level)
        band_num = int(band_str[1:]) if band_str.startswith("B") else 1
        max_items_per_room = spawn_service.scale_max_items_per_room(max_items_per_room, band_num)
        
        # Get ETP budget for this room
        # Priority: explicit encounter_budget param > level override > default band budget
        etp_min, etp_max = get_room_etp_budget(self.dungeon_level)
        allow_spike = False
        
        if encounter_budget is not None:
            etp_min = encounter_budget.etp_min
            etp_max = encounter_budget.etp_max
            allow_spike = encounter_budget.allow_spike
        elif level_override and level_override.encounter_budget is not None:
            etp_min = level_override.encounter_budget.etp_min
            etp_max = level_override.encounter_budget.etp_max
            allow_spike = level_override.encounter_budget.allow_spike
        
        # Build spawn context and plan
        from config.testing_config import is_testing_mode
        item_spawn_config = config.get_item_spawn_chances(self.dungeon_level)
        
        spawn_context = SpawnContext(
            depth=self.dungeon_level,
            band_id=band_str,
            band_num=band_num,
            max_monsters=max_monsters_per_room,
            max_items=max_items_per_room,
            encounter_budget=EncounterBudget(
                etp_min=etp_min,
                etp_max=etp_max,
                allow_spike=allow_spike,
            ),
            testing_mode=is_testing_mode(),
            no_monsters=config.no_monsters,
            item_spawn_config=item_spawn_config,
        )
        
        spawn_plan = spawn_service.generate_room_plan(
            spawn_context,
            randint_fn=randint,
            choice_fn=random_choice_from_dict,
        )
        
        # ETP budgeting: Track total ETP as we spawn monsters
        room_total_etp = 0.0
        spawned_monsters = []  # Track (type, etp) for logging
        room_id = f"room_{room.x1}_{room.y1}"
        HEAVY_MONSTER_TYPES = {"troll", "large_slime"}
        
        # Track heavy monster presence for B1 constraint (still enforced)
        spawned_heavy_monster = False
        
        for _ in range(spawn_plan.num_monsters):
            # Check if we've hit ETP budget
            if room_total_etp >= etp_max:
                logger.debug(
                    f"Room {room_id}: ETP budget reached ({room_total_etp:.1f}/{etp_max}), "
                    f"stopping monster spawns ({len(spawned_monsters)}/{spawn_plan.num_monsters} placed)"
                )
                break
            
            # B1 CONSTRAINT: If we've already spawned a heavy monster, skip further spawns
            if band_str == "B1" and spawned_heavy_monster:
                logger.debug(
                    f"Room {room_id}: B1 constraint - already has heavy monster, "
                    f"skipping additional spawn"
                )
                break
            
            # Choose a random location in the room
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            
            if not any(
                [entity for entity in entities if entity.x == x and entity.y == y]
            ):
                monster_choice = spawn_service.pick_monster(
                    spawn_plan.monster_chances,
                    choice_fn=random_choice_from_dict,
                )
                if not monster_choice:
                    continue
                
                is_heavy = monster_choice in HEAVY_MONSTER_TYPES
                
                # B1 CONSTRAINT: If trying to spawn a heavy and room already has monsters, skip
                if band_str == "B1" and is_heavy and len(spawned_monsters) > 0:
                    logger.debug(
                        f"Room {room_id}: B1 constraint - skipping {monster_choice} "
                        f"(room already has monsters)"
                    )
                    continue
                
                monster_etp = get_monster_etp(monster_choice, self.dungeon_level)
                
                # Check if this monster would exceed budget (unless allow_spike)
                if not allow_spike and (room_total_etp + monster_etp) > etp_max:
                    logger.debug(
                        f"Room {room_id}: Skipping {monster_choice} "
                        f"(ETP {monster_etp:.1f} would exceed budget "
                        f"{room_total_etp:.1f}+{monster_etp:.1f} > {etp_max})"
                    )
                    continue
                
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
                    
                    # Track ETP
                    room_total_etp += monster_etp
                    spawned_monsters.append((monster_choice, monster_etp))
                    
                    # Track heavy monsters for B1 constraint
                    if is_heavy:
                        spawned_heavy_monster = True
        
        # Debug log in the requested format: [DEBUG] Room X @ depth Y (band Z): ETP=N, monsters=[type:count, ...]
        
        # Count monsters by type for clean logging
        from collections import Counter
        monster_type_counts = Counter(m_type for m_type, _ in spawned_monsters)
        monster_summary = ", ".join(f"{t}:{c}" for t, c in sorted(monster_type_counts.items()))
        
        # Determine ETP status
        etp_status = "OK"
        if room_total_etp < etp_min:
            etp_status = "UNDER"
        elif room_total_etp > etp_max:
            etp_status = "OVER"
        
        logger.debug(
            f"[ETP] Room {room_id} @ depth {self.dungeon_level} (band {band_str}): "
            f"ETP={room_total_etp:.1f} [{etp_status}], budget=[{etp_min}-{etp_max}], "
            f"monsters=[{monster_summary if monster_summary else 'empty'}]"
        )
        
        # Log room ETP summary (existing detailed format)
        log_room_etp_summary(
            room_id=room_id,
            depth=self.dungeon_level,
            monster_list=spawned_monsters,
            total_etp=room_total_etp,
            budget_min=etp_min,
            budget_max=etp_max
        )
        
        # Track items spawned in this room for pity system
        spawned_item_ids = []
        
        for _ in range(spawn_plan.num_items):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)

            # SAFETY: Check tile is walkable, no entity already there, and not on excluded coords (stairs)
            if (not self.is_blocked(x, y) and 
                not any([entity for entity in entities if entity.x == x and entity.y == y]) and
                (x, y) not in exclude_coords):
                item_choice = spawn_service.pick_item(
                    spawn_plan.item_chances,
                    choice_fn=random_choice_from_dict,
                )
                if not item_choice:
                    continue
                
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
                
                # Track item for pity system
                spawned_item_ids.append(item_choice)
        
        # ─────────────────────────────────────────────────────────────────────
        # PITY SYSTEM: Ensure critical items don't go too long without dropping
        # Supports healing, panic, weapon upgrades, and armor upgrades.
        # Only triggers in normal rooms; at most one pity item per room.
        # ─────────────────────────────────────────────────────────────────────
        
        # Get room metadata for pity decisions
        from config.level_template_registry import RoomMetadata
        if room_metadata is None:
            room_metadata = RoomMetadata()  # Default: normal room
        
        # Build spawn helper functions for each pity category
        def spawn_pity_item_in_room(item_id: str, pity_type: str) -> bool:
            """Helper to spawn a pity item in a valid position in the room.
            
            Args:
                item_id: Item ID to spawn
                pity_type: Type of pity for logging
                
            Returns:
                True if item was successfully spawned
            """
            entity_factory = get_entity_factory()
            
            for _ in range(10):  # Try up to 10 times
                x = randint(room.x1 + 1, room.x2 - 1)
                y = randint(room.y1 + 1, room.y2 - 1)
                
                if (not self.is_blocked(x, y) and
                    not any([e for e in entities if e.x == x and e.y == y]) and
                    (x, y) not in exclude_coords):
                    
                    # Try different creation methods based on item type
                    pity_item = entity_factory.create_spell_item(item_id, x, y)
                    if not pity_item:
                        pity_item = entity_factory.create_weapon(item_id, x, y)
                    if not pity_item:
                        pity_item = entity_factory.create_armor(item_id, x, y)
                    if not pity_item:
                        pity_item = entity_factory.create_ring(item_id, x, y)
                    
                    if pity_item:
                        entities.append(pity_item)
                        invalidate_entity_cache(f"entity_added_pity_{pity_type}")
                        spawned_item_ids.append(item_id)
                        logger.debug(
                            f"[PITY] Spawned {item_id} at ({x}, {y}) in room {room_id} ({pity_type} pity)"
                        )
                        return True
            
            logger.warning(
                f"[PITY] Failed to spawn pity {pity_type} item in room {room_id} - no valid position"
            )
            return False
        
        def get_valid_pity_item_for_category(category: str) -> str:
            """Get a valid item ID for pity spawning from a category.
            
            Selects items that are available in the current band.
            
            Args:
                category: Item category (e.g., "healing", "panic")
                
            Returns:
                Item ID to spawn, or fallback if none available
            """
            from random import choice
            
            # Get all items in this category
            category_items = get_items_by_category(category)
            
            # Filter to items available in this band
            band_items = get_items_for_band(band_num)
            valid_items = [item for item in category_items if item in band_items]
            
            if valid_items:
                return choice(valid_items)
            elif category_items:
                # Fall back to any item in category if band filtering is too strict
                return choice(category_items)
            else:
                # Ultimate fallbacks by category
                fallbacks = {
                    "healing": "healing_potion",
                    "panic": "teleport_scroll",
                    "upgrade_weapon": "enhance_weapon_scroll",
                    "upgrade_armor": "enhance_armor_scroll",
                }
                return fallbacks.get(category, "healing_potion")
        
        def spawn_healing_item() -> bool:
            item_id = get_valid_pity_item_for_category("healing")
            return spawn_pity_item_in_room(item_id, "healing")
        
        def spawn_panic_item() -> bool:
            item_id = get_valid_pity_item_for_category("panic")
            return spawn_pity_item_in_room(item_id, "panic")
        
        def spawn_weapon_upgrade() -> bool:
            item_id = get_valid_pity_item_for_category("upgrade_weapon")
            return spawn_pity_item_in_room(item_id, "weapon_upgrade")
        
        def spawn_armor_upgrade() -> bool:
            item_id = get_valid_pity_item_for_category("upgrade_armor")
            return spawn_pity_item_in_room(item_id, "armor_upgrade")
        
        # Call unified pity check
        pity_result = check_and_apply_pity(
            depth=self.dungeon_level,
            band=band_num,
            room_role=room_metadata.role,
            room_etp_exempt=room_metadata.etp_exempt,
            spawned_item_ids=spawned_item_ids,
            spawn_healing_item_fn=spawn_healing_item,
            spawn_panic_item_fn=spawn_panic_item,
            spawn_upgrade_weapon_fn=spawn_weapon_upgrade,
            spawn_upgrade_armor_fn=spawn_armor_upgrade,
            room_id=room_id,
        )

    def place_exploration_features(self, room, entities):
        """Place exploration features (chests, signposts, murals, secret doors) in a room.
        
        Spawns exploration content based on dungeon level and probability tables:
        - Chests: 30% chance per room (quality scales with depth)
        - Signposts: 20% chance per room (random messages)
        - Murals: 15% chance per room (environmental lore)
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
        
        # MURALS - 15% chance per room (Phase 4 environmental lore)
        if random() < 0.15:
            # Random position in room (not at edges)
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            
            mural = entity_factory.create_mural(x, y, depth=self.dungeon_level)
            if mural:
                entities.append(mural)
                logger.debug(f"Placed mural at ({x}, {y}) in room (depth {self.dungeon_level})")
    
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
        
        # Need at least 2 rooms to place secret doors
        if len(rooms) < 2:
            return
        
        # Generate 1-3 secret doors (but not more than rooms - 1)
        num_doors = randint(1, min(3, len(rooms) - 1))
        
        for _ in range(num_doors):
            
            # Pick two adjacent rooms to connect
            room_entry_a = choice(rooms)
            room_entry_b = choice([r for r in rooms if r != room_entry_a])
            
            # Extract rects from room entries
            room_a = room_entry_a['rect'] if isinstance(room_entry_a, dict) else room_entry_a
            room_b = room_entry_b['rect'] if isinstance(room_entry_b, dict) else room_entry_b
            
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
        
        Vault rooms are marked with role="treasure" and allow_spike=True in metadata.
        
        Args:
            rooms (list): List of room dicts with 'rect' and 'metadata' keys
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
        vault_room_entries = sample(eligible_rooms, num_vaults)
        
        # Load vault theme registry
        from config.vault_theme_registry import get_vault_theme_registry
        theme_registry = get_vault_theme_registry()
        
        # Import RoomMetadata for vault designation
        from config.level_template_registry import RoomMetadata
        
        # Create each vault with a theme
        for room_entry in vault_room_entries:
            vault_room = room_entry['rect']
            vault_room.is_vault = True
            
            # Update room metadata to mark as treasure/spike room
            room_entry['metadata'] = RoomMetadata(
                role="treasure",
                allow_spike=True,  # Vaults can exceed normal ETP budgets
                etp_exempt=False   # But still track their ETP
            )
            
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
                
                if monster and monster.get_component_optional(ComponentType.FIGHTER):
                    # Apply elite bonuses from theme
                    monster.fighter.base_max_hp = int(monster.fighter.base_max_hp * hp_multiplier)
                    monster.fighter.hp = monster.fighter.max_hp  # Heal to new max
                    monster.get_component_optional(ComponentType.FIGHTER).base_power += power_bonus
                    monster.get_component_optional(ComponentType.FIGHTER).base_defense += defense_bonus
                    
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
    
    # ========================================================================
    # SAFE TILE ACCESS METHODS
    # These methods provide bounds-checked access to tiles, preventing
    # IndexError crashes when accessing tiles with invalid coordinates.
    # Always use these methods instead of direct tiles[x][y] access!
    # ========================================================================
    
    def is_in_bounds(self, x: int, y: int) -> bool:
        """Check if coordinates are within map bounds.
        
        Args:
            x (int): X coordinate to check
            y (int): Y coordinate to check
        
        Returns:
            bool: True if coordinates are valid, False otherwise
        """
        return 0 <= x < self.width and 0 <= y < self.height
    
    def get_tile(self, x: int, y: int):
        """Safely get tile at coordinates.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
        
        Returns:
            Tile or None: Tile object if coordinates are valid, None otherwise
        """
        if not self.is_in_bounds(x, y):
            return None
        return self.tiles[x][y]
    
    def is_blocked(self, x, y):
        """Check if a tile is blocked for movement.
        
        SAFETY: Treats out-of-bounds coordinates as blocked.

        Args:
            x (int): X coordinate to check
            y (int): Y coordinate to check

        Returns:
            bool: True if the tile is blocked or out of bounds, False otherwise
        """
        tile = self.get_tile(x, y)
        if tile is None:
            return True  # Out of bounds = blocked
        return tile.blocked
    
    def is_explored(self, x: int, y: int) -> bool:
        """Check if a tile has been explored by the player.
        
        SAFETY: Out-of-bounds coordinates return False.
        
        Args:
            x (int): X coordinate to check
            y (int): Y coordinate to check
        
        Returns:
            bool: True if tile is explored, False if unexplored or out of bounds
        """
        tile = self.get_tile(x, y)
        if tile is None:
            return False  # Out of bounds = not explored
        return tile.explored
    
    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a tile is walkable (not blocked).
        
        SAFETY: Out-of-bounds coordinates return False.
        
        Args:
            x (int): X coordinate to check
            y (int): Y coordinate to check
        
        Returns:
            bool: True if tile is walkable, False if blocked or out of bounds
        """
        return not self.is_blocked(x, y)
    
    def get_tile_property(self, x: int, y: int, property_name: str, default=None):
        """Safely get a property from a tile.
        
        SAFETY: Returns default value if out of bounds or property doesn't exist.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            property_name (str): Name of the property to get (e.g. 'blocked', 'explored')
            default: Value to return if tile is out of bounds or property doesn't exist
        
        Returns:
            Property value or default
        """
        tile = self.get_tile(x, y)
        if tile is None:
            return default
        return getattr(tile, property_name, default)

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

        player.get_component_optional(ComponentType.FIGHTER).heal(player.get_component_optional(ComponentType.FIGHTER).max_hp // 2)

        message_log.add_message(
            MB.custom(
                "You take a moment to rest, and recover your strength.", (159, 63, 255)
            )
        )
        
        # Phase 2: Entity dialogue - Entity gets more anxious as player descends
        self._trigger_entity_dialogue(message_log)
        
        # Phase 1.5b: Wire telemetry floor tracking for new floor
        from services.telemetry_service import get_telemetry_service
        telemetry_service = get_telemetry_service()
        if telemetry_service.enabled:
            telemetry_service.start_floor(self.dungeon_level)
            self._populate_floor_telemetry(telemetry_service, entities)
            logger.info(f"Telemetry started for floor {self.dungeon_level}")

        return entities
    
    def _trigger_entity_dialogue(self, message_log):
        """Trigger Entity dialogue based on current dungeon level.
        
        The Entity (ancient dragon bound in human form) speaks to the player
        as they descend, growing progressively more anxious and desperate.
        
        Phase 2 implementation - depth-based dialogue from entity_dialogue.yaml.
        
        Args:
            message_log (MessageLog): Game message log
        """
        from config.entity_dialogue_loader import get_entity_dialogue_loader
        
        # Get dialogue for current level
        dialogue_loader = get_entity_dialogue_loader()
        dialogue = dialogue_loader.get_dialogue_for_level(self.dungeon_level)
        
        if dialogue and dialogue_loader.should_show_in_log():
            # Add Entity's message to the log
            # Color based on dialogue config (purple → violet → red as anxiety increases)
            import libtcodpy as libtcod
            color_map = {
                'light_purple': libtcod.light_purple,
                'purple': libtcod.purple,
                'violet': libtcod.violet,
                'red': libtcod.red,
                'light_red': libtcod.light_red,
            }
            color = color_map.get(dialogue.color, libtcod.light_purple)
            
            message_log.add_message(MB.custom(dialogue.message, color))
            logger.info(f"Entity dialogue triggered at level {self.dungeon_level}")
    
    def _populate_floor_telemetry(self, telemetry_service, entities):
        """Populate telemetry floor stats after map generation.
        
        Computes and records floor-level metrics including:
        - ETP sum (total monster difficulty)
        - Room count (approximated from corridor connections)
        - Monster count
        - Item count (excluding player inventory)
        - Door count
        - Trap count
        - Secret count
        
        Args:
            telemetry_service: TelemetryService instance
            entities: List of all entities on the floor
        """
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
        room_count = len(self.corridor_connections) + 1
        
        # Set telemetry data
        telemetry_service.set_floor_etp(etp_sum=etp_sum)
        telemetry_service.set_room_counts(
            rooms=room_count,
            monsters=monster_count,
            items=item_count
        )
        
        logger.info(
            f"Floor {self.dungeon_level} telemetry: "
            f"ETP={etp_sum}, Rooms≈{room_count}, Monsters={monster_count}, "
            f"Items={item_count}, Doors={door_count}, Traps={trap_count}, Secrets={secret_count}"
        )
    
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
        
        # DEBUG: Tier 1 - Respect no_monsters flag for guaranteed spawns too
        config = get_testing_config()
        skip_monsters = config.no_monsters
        
        # Place guaranteed monsters
        for spawn in level_override.guaranteed_monsters:
            # Skip monster spawns if no_monsters flag is active
            if skip_monsters:
                logger.debug(f"Skipping guaranteed monster spawn: {spawn.entity_type} (no_monsters flag)")
                continue
            
            # Check if this is a boss/miniboss that requires a special room
            is_restricted = is_boss_monster(spawn.entity_type) or is_miniboss_monster(spawn.entity_type)
            
            if is_restricted:
                # Find a room with appropriate role for this monster
                target_room = self._find_room_for_restricted_monster(
                    spawn.entity_type, rooms
                )
                if target_room is None:
                    # No suitable room found - skip spawn with warning
                    restriction_reason = get_spawn_restriction_reason(spawn.entity_type, "normal")
                    logger.warning(
                        f"Skipping guaranteed spawn of {spawn.entity_type}: {restriction_reason}. "
                        f"Add a special room with appropriate role to spawn this monster."
                    )
                    failed_count += 1
                    continue
                
                # Spawn in the target room
                spawn_count = spawn.get_random_count()
                for i in range(spawn_count):
                    room_rect = target_room['rect'] if isinstance(target_room, dict) else target_room
                    x, y = self._find_random_position_in_room(room_rect, entities)
                    if x is None:
                        logger.warning(
                            f"Could not find position in boss room for {spawn.entity_type}, "
                            f"spawned {i}/{spawn_count}"
                        )
                        failed_count += 1
                        break
                    
                    monster = entity_factory.create_monster(spawn.entity_type, x, y)
                    if monster:
                        from components.monster_equipment import spawn_equipment_on_monster
                        spawn_equipment_on_monster(monster, self.dungeon_level)
                        entities.append(monster)
                        invalidate_entity_cache("guaranteed_spawn_monster")
                        spawned_count += 1
                        logger.info(f"Spawned {spawn.entity_type} in boss/miniboss room")
                    else:
                        logger.warning(f"Failed to create monster: {spawn.entity_type}")
                        failed_count += 1
            else:
                # Normal monster - spawn with ETP budget awareness
                spawn_count = spawn.get_random_count()
                for i in range(spawn_count):
                    # Use ETP-aware room selection for normal monsters
                    room_entry, x, y = self._find_room_with_etp_budget(
                        rooms, entities, spawn.entity_type
                    )
                    
                    if x is None:
                        # No room with budget available - log and skip
                        monster_etp = get_monster_etp(spawn.entity_type, self.dungeon_level)
                        etp_min, etp_max = get_room_etp_budget(self.dungeon_level)
                        logger.debug(
                            f"Skipping guaranteed spawn of {spawn.entity_type} "
                            f"(ETP {monster_etp:.1f}): no room with available budget "
                            f"[0-{etp_max}] found, spawned {i}/{spawn_count}"
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
                        
                        # Log the ETP-aware placement
                        monster_etp = get_monster_etp(spawn.entity_type, self.dungeon_level)
                        logger.debug(
                            f"Guaranteed spawn: {spawn.entity_type} (ETP {monster_etp:.1f}) "
                            f"placed in room with budget"
                        )
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
                # Check unique items first (rare, specific names like "amulet_of_yendor")
                item = entity_factory.create_unique_item(spawn.entity_type, x, y)
                if not item:
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
            # Pick a random room entry
            room_entry = rooms[randint(0, len(rooms) - 1)]
            
            # Extract rect from room entry (handle both old and new format)
            room = room_entry['rect'] if isinstance(room_entry, dict) else room_entry
            
            # Pick a random position in that room
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            
            # Check if position is unoccupied
            if not any(entity.x == x and entity.y == y for entity in entities):
                return (x, y)
                
        # Could not find a position after max_attempts
        return (None, None)
    
    def _get_room_current_etp(self, room, entities):
        """Calculate the current ETP of monsters in a room.
        
        Args:
            room: Rect object for the room
            entities: List of all entities on the map
            
        Returns:
            float: Total ETP of monsters currently in the room
        """
        total_etp = 0.0
        for entity in entities:
            # Skip non-monsters
            if not hasattr(entity, 'ai') or entity.ai is None:
                continue
            if getattr(entity, 'name', '').lower() == 'player':
                continue
            
            # Check if entity is in this room
            if room.x1 <= entity.x <= room.x2 and room.y1 <= entity.y <= room.y2:
                # Get monster type from name (handle Elite variants)
                monster_name = getattr(entity, 'name', 'unknown')
                monster_type = monster_name.lower().replace(' (elite)', '')
                total_etp += get_monster_etp(monster_type, self.dungeon_level)
        
        return total_etp
    
    def _find_room_with_etp_budget(self, rooms, entities, monster_type, max_attempts=20):
        """Find a room where a monster can be placed without exceeding ETP budget.
        
        Only considers normal rooms (not special, spike, or exempt).
        For special/spike/exempt rooms, returns None to indicate the monster
        should be placed elsewhere.
        
        Args:
            rooms: List of room entries (dicts with 'rect' and 'metadata')
            entities: List of all entities on the map
            monster_type: Monster type to place
            max_attempts: Maximum number of rooms to try
            
        Returns:
            tuple: (room_entry, x, y) if found, (None, None, None) otherwise
        """
        from config.level_template_registry import RoomMetadata
        
        monster_etp = get_monster_etp(monster_type, self.dungeon_level)
        etp_min, etp_max = get_room_etp_budget(self.dungeon_level)
        
        # Get level override for custom budget if exists
        template_registry = get_level_template_registry()
        level_override = template_registry.get_level_override(self.dungeon_level)
        if level_override and level_override.encounter_budget:
            etp_max = level_override.encounter_budget.etp_max
        
        # Shuffle room order for randomness
        from random import shuffle
        room_indices = list(range(len(rooms)))
        shuffle(room_indices)
        
        for attempt, room_idx in enumerate(room_indices):
            if attempt >= max_attempts:
                break
            
            room_entry = rooms[room_idx]
            room = room_entry['rect'] if isinstance(room_entry, dict) else room_entry
            metadata = room_entry.get('metadata', RoomMetadata()) if isinstance(room_entry, dict) else RoomMetadata()
            
            # Check if this is a normal room that should respect ETP budget
            is_special = metadata.is_special() if hasattr(metadata, 'is_special') else False
            allow_spike = getattr(metadata, 'allow_spike', False)
            etp_exempt = getattr(metadata, 'etp_exempt', False)
            
            # For special/spike/exempt rooms, allow placement without budget check
            if is_special or allow_spike or etp_exempt:
                # Find a position in this room
                x, y = self._find_random_position_in_room(room, entities)
                if x is not None:
                    return (room_entry, x, y)
                continue
            
            # For normal rooms, check ETP budget
            current_etp = self._get_room_current_etp(room, entities)
            if current_etp + monster_etp <= etp_max:
                # This room can accommodate the monster
                x, y = self._find_random_position_in_room(room, entities)
                if x is not None:
                    return (room_entry, x, y)
        
        return (None, None, None)
    
    def _find_room_for_restricted_monster(self, monster_type, rooms):
        """Find a room with appropriate role for boss/miniboss monster.
        
        Args:
            monster_type: Monster type identifier
            rooms: List of room entries (dicts with 'rect' and 'metadata')
            
        Returns:
            Room entry (dict) with appropriate role, or None if not found
        """
        from config.level_template_registry import RoomMetadata
        
        for room_entry in rooms:
            if isinstance(room_entry, dict) and 'metadata' in room_entry:
                metadata = room_entry.get('metadata')
                if metadata:
                    role = metadata.role if hasattr(metadata, 'role') else 'normal'
                else:
                    role = 'normal'
            else:
                role = 'normal'
            
            if can_spawn_monster_in_room(monster_type, role):
                return room_entry
        
        return None
    
    def _find_random_position_in_room(self, room, entities, max_attempts=20):
        """Find a random unoccupied position within a specific room.
        
        Args:
            room: Rect object for the room
            entities: List of existing entities to avoid
            max_attempts: Maximum number of random placement attempts
            
        Returns:
            tuple: (x, y) coordinates, or (None, None) if no position found
        """
        for attempt in range(max_attempts):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            
            # Check if position is unoccupied
            if not any(entity.x == x and entity.y == y for entity in entities):
                return (x, y)
        
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
            rooms (list): All available room dicts (with 'rect' and 'metadata' keys)
            special_room (SpecialRoom): Special room configuration
            used_rooms (set): Set of room entry IDs already used
            
        Returns:
            list: Selected room entries (may be empty)
        """
        # Filter out already-used rooms
        available_rooms = [r for r in rooms if id(r) not in used_rooms]
        
        if not available_rooms:
            return []
            
        # Filter by minimum size requirement
        if special_room.min_room_size is not None:
            available_rooms = [
                r for r in available_rooms 
                if self._get_room_size(r['rect']) >= special_room.min_room_size
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
            available_rooms.sort(key=lambda r: self._get_room_size(r['rect']), reverse=True)
        elif special_room.placement == "smallest":
            # Sort by size ascending and take the count smallest
            available_rooms.sort(key=lambda r: self._get_room_size(r['rect']))
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
            room (Rect): Room rect to measure
            
        Returns:
            int: Area of the room (width * height)
        """
        width = room.x2 - room.x1
        height = room.y2 - room.y1
        return width * height
    
    def _populate_special_room(self, room_entry, special_room, entities):
        """Populate a special room with guaranteed spawns.
        
        Args:
            room_entry (dict): Room entry with 'rect' and 'metadata' keys
            special_room (SpecialRoom): Special room configuration
            entities (list): List to add new entities to
        """
        room = room_entry['rect']
        
        # Update room metadata from special room config
        if special_room.metadata:
            room_entry['metadata'] = special_room.metadata
        
        # Get room role for spawn filtering
        room_role = "normal"
        metadata = room_entry.get('metadata')
        if metadata and hasattr(metadata, 'role'):
            room_role = metadata.role
        
        logger.info(
            f"Populating '{special_room.room_type}' (role: {room_role}) at "
            f"({room.center()[0]}, {room.center()[1]})"
        )
        
        entity_factory = get_entity_factory()
        spawned_count = 0
        failed_count = 0
        
        # Place guaranteed monsters
        for spawn in special_room.guaranteed_monsters:
            # Check if this monster can spawn in this room based on role
            if not can_spawn_monster_in_room(spawn.entity_type, room_role):
                restriction_reason = get_spawn_restriction_reason(spawn.entity_type, room_role)
                logger.warning(
                    f"Skipping spawn of {spawn.entity_type} in special room: {restriction_reason}"
                )
                failed_count += 1
                continue
            
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
    
    def _create_secret_ritual_room(self, rooms, entities):
        """Create a hidden room with Corrupted Ritualists and Crimson Ritual Codex (Phase 5).
        
        This secret room is only accessible after picking up the Ruby Heart.
        Contains 2-3 Corrupted Ritualists and the Crimson Ritual Codex.
        
        Args:
            rooms: List of room rectangles
            entities: List of entities to add enemies and item to
        """
        if not rooms or len(rooms) < 2:
            logger.warning("Not enough rooms for secret ritual room on Level 25")
            return
        
        # Pick a room that's not the last room (where Ruby Heart/stairs are)
        # Prefer a room further from the start
        if len(rooms) > 3:
            secret_room_entry = rooms[randint(len(rooms) // 2, len(rooms) - 2)]
        else:
            secret_room_entry = rooms[0]
        
        # Extract rect from room entry
        secret_room = secret_room_entry['rect'] if isinstance(secret_room_entry, dict) else secret_room_entry
        
        # Create a small hidden room attached to this room
        # Try to place it off to the side
        room_center_x = (secret_room.x1 + secret_room.x2) // 2
        room_center_y = (secret_room.y1 + secret_room.y2) // 2
        
        # Create a 7x7 secret room to the right of the chosen room
        secret_x = secret_room.x2 + 2  # 2 tiles away for secret door
        secret_y = room_center_y - 3   # Centered vertically
        secret_w = 7
        secret_h = 7
        
        # Make sure it fits in the map
        if secret_x + secret_w >= self.width - 1 or secret_y + secret_h >= self.height - 1:
            # Try left side instead
            secret_x = max(1, secret_room.x1 - secret_w - 2)
            if secret_x < 1:
                logger.warning("Cannot place secret room on Level 25")
                return
        
        # Create the secret room (Rect already imported at module level)
        ritual_room = Rect(secret_x, secret_y, secret_w, secret_h)
        self.create_room(ritual_room)
        
        # Create a secret door connecting to the main room
        # Find a good connection point
        if secret_x > secret_room.x2:
            # Secret room is to the right
            door_x = secret_room.x2 + 1
            door_y = room_center_y
        else:
            # Secret room is to the left
            door_x = secret_room.x1 - 1
            door_y = room_center_y
        
        # Create a tunnel with a secret door
        self.create_h_tunnel(secret_room.x2, secret_x, door_y)
        
        # Mark one tile as a secret door (will be revealed when Ruby Heart is picked up)
        # Secret doors are just normal floor tiles that look like walls
        if hasattr(self, 'secret_doors'):
            self.secret_doors.append((door_x, door_y))
        else:
            self.secret_doors = [(door_x, door_y)]
        
        logger.info(f"=== SECRET RITUAL ROOM CREATED at ({secret_x}, {secret_y}) ===")
        
        # Spawn 2-3 Corrupted Ritualists in the secret room
        from config.entity_factory import get_entity_factory
        factory = get_entity_factory()
        
        num_ritualists = randint(2, 3)
        ritual_center_x = secret_x + secret_w // 2
        ritual_center_y = secret_y + secret_h // 2
        
        for i in range(num_ritualists):
            # Spawn ritualists around the room
            offset_x = randint(-2, 2)
            offset_y = randint(-2, 2)
            ritualist_x = ritual_center_x + offset_x
            ritualist_y = ritual_center_y + offset_y
            
            # Make sure spawn point is valid
            if (secret_x < ritualist_x < secret_x + secret_w and
                secret_y < ritualist_y < secret_y + secret_h):
                ritualist = factory.create_monster('corrupted_ritualist', ritualist_x, ritualist_y)
                if ritualist:
                    entities.append(ritualist)
                    logger.info(f"Spawned Corrupted Ritualist at ({ritualist_x}, {ritualist_y})")
        
        # Spawn Crimson Ritual Codex in the center
        codex_x = ritual_center_x
        codex_y = ritual_center_y
        
        codex = factory.create_unique_item('crimson_ritual_codex', codex_x, codex_y)
        if codex:
            entities.append(codex)
            logger.info(f"=== CRIMSON RITUAL CODEX SPAWNED at ({codex_x}, {codex_y}) ===")
            print(f">>> SECRET ROOM: Crimson Ritual Codex created with name '{codex.name}'")
        else:
            logger.error("=== FAILED TO CREATE CRIMSON RITUAL CODEX ===")
            print(">>> SECRET ROOM: Failed to create Crimson Ritual Codex")
    
    def _spawn_ghost_guide(self, rooms, entities):
        """Spawn the Ghost Guide NPC in a camp room (Phase 3).
        
        The Guide appears at levels 5, 10, 15, 20 to provide warnings
        and reveal the Entity's backstory.
        
        Args:
            rooms: List of room rectangles
            entities: List of entities to add Guide to
        """
        if not rooms:
            logger.warning(f"No rooms available for Guide spawn on level {self.dungeon_level}")
            return
        
        # First, try to create or use a camp room
        # Check if we have any camp rooms marked
        camp_rooms = getattr(self, 'camp_rooms', [])
        
        if not camp_rooms:
            # No camp room exists, create one by converting a random room
            # Pick a room that's not the first (player spawn) or last (stairs)
            if len(rooms) > 2:
                camp_room_entry = rooms[randint(1, len(rooms) - 2)]
            else:
                camp_room_entry = rooms[0]  # Fallback to first room
            
            # Extract rect from room entry
            camp_room = camp_room_entry['rect'] if isinstance(camp_room_entry, dict) else camp_room_entry
            
            logger.info(f"Converting room at ({camp_room.x1}, {camp_room.y1}) to camp for Guide")
            
            # Clear monsters from this room to make it safe
            entities_to_remove = [
                e for e in entities
                if (hasattr(e, 'ai') and e.get_component_optional(ComponentType.AI) and 
                    camp_room.x1 < e.x < camp_room.x2 and 
                    camp_room.y1 < e.y < camp_room.y2)
            ]
            for entity in entities_to_remove:
                entities.remove(entity)
                logger.debug(f"Removed {entity.name} from camp room")
        else:
            # Use existing camp room
            camp_room = camp_rooms[0]
        
        # Find a good position for the Guide (center-ish)
        guide_x = (camp_room.x1 + camp_room.x2) // 2
        guide_y = (camp_room.y1 + camp_room.y2) // 2
        
        # Make sure position isn't occupied
        if any(entity.x == guide_x and entity.y == guide_y for entity in entities):
            # Try to find nearby free spot
            guide_x, guide_y = self._find_random_position_in_room(camp_room, entities)
            if guide_x is None:
                logger.warning(f"Could not find free position for Guide on level {self.dungeon_level}")
                return
        
        # Spawn the Ghost Guide!
        from config.entity_factory import get_entity_factory
        factory = get_entity_factory()
        
        guide = factory.create_unique_npc('ghost_guide', guide_x, guide_y, self.dungeon_level)
        if guide:
            entities.append(guide)
            logger.info(f"=== GHOST GUIDE SPAWNED at ({guide_x}, {guide_y}) on level {self.dungeon_level} ===")
        else:
            logger.error(f"Failed to create Ghost Guide on level {self.dungeon_level}")
    
    def _validate_and_guarantee_locked_door_keys(self, entities, rooms):
        """Validate that every locked door has a reachable key on the same floor.
        
        If a locked door exists but no matching key is found:
        1. Try to spawn a fallback key on the level
        2. As a last resort, unlock the door
        
        Args:
            entities (list): List of entities on the map
            rooms (list): List of room Rect objects
        """
        from components.component_registry import ComponentType
        from components.door import Door
        from config.entity_factory import get_entity_factory
        
        # Find all locked doors and their key requirements
        locked_doors = {}  # key_tag -> [door_entities]
        for entity in entities:
            if entity.components.has(ComponentType.DOOR):
                door_comp = entity.components.get(ComponentType.DOOR)
                if door_comp.is_locked and door_comp.key_tag:
                    if door_comp.key_tag not in locked_doors:
                        locked_doors[door_comp.key_tag] = []
                    locked_doors[door_comp.key_tag].append(entity)
        
        if not locked_doors:
            return  # No locked doors, nothing to validate
        
        # Check each key_tag for available keys
        for key_tag, door_entities in locked_doors.items():
            # Count available keys for this key_tag
            available_keys = 0
            for entity in entities:
                if hasattr(entity, 'key_type'):
                    # Match by key_type attribute
                    if entity.key_type in key_tag or key_tag.replace('_key', '') == entity.key_type:
                        available_keys += 1
                elif hasattr(entity, 'entity_id') and entity.entity_id == key_tag:
                    available_keys += 1
                elif hasattr(entity, 'name'):
                    item_name = entity.name.lower().replace(' ', '_')
                    if item_name == key_tag or item_name.replace(' ', '_') == key_tag:
                        available_keys += 1
            
            # If no keys found, spawn fallback key
            if available_keys == 0:
                logger.debug(f"No keys found for locked doors requiring '{key_tag}' on level {self.dungeon_level}")
                
                # Try to spawn fallback key
                door_entity = door_entities[0]  # Pick first locked door location
                spawn_pos = self._find_random_unoccupied_position(rooms, entities)
                
                if spawn_pos[0] is not None:
                    x, y = spawn_pos
                    factory = get_entity_factory()
                    
                    # Create key matching the key_tag
                    key = factory.create_spell_item(key_tag, x, y)
                    if key:
                        entities.append(key)
                        logger.info(f"[VALIDATION] Spawned fallback key '{key_tag}' at ({x}, {y}) on level {self.dungeon_level}")
                    else:
                        # Fallback: try to unlock the door
                        logger.warning(
                            f"Failed to spawn key '{key_tag}' on level {self.dungeon_level}, "
                            f"unlocking {len(door_entities)} locked door(s) as last resort"
                        )
                        for door_ent in door_entities:
                            door_ent.components.get(ComponentType.DOOR).unlock()
                else:
                    # No space to spawn key - unlock doors
                    logger.warning(
                        f"No space to spawn fallback key '{key_tag}' on level {self.dungeon_level}, "
                        f"unlocking {len(door_entities)} locked door(s) as last resort"
                    )
                    for door_ent in door_entities:
                        door_ent.components.get(ComponentType.DOOR).unlock()
    
    def _validate_secret_door_placement(self, entities):
        """Validate that secret doors are only placed on wall tiles.
        
        Secret doors placed on walkable tiles are converted to normal doors.
        This prevents the issue of "secret doors" in the middle of corridors
        that were already walkable.
        
        Args:
            entities (list): List of entities on the map
        """
        from components.component_registry import ComponentType
        
        secret_doors_invalid = []
        
        for entity in entities:
            if entity.components.has(ComponentType.DOOR):
                door_comp = entity.components.get(ComponentType.DOOR)
                if door_comp.is_secret:
                    # Check if the tile is currently walkable
                    x, y = entity.x, entity.y
                    if not self.is_in_bounds(x, y):
                        logger.warning(f"Secret door at ({x}, {y}) is out of bounds!")
                        secret_doors_invalid.append(entity)
                        continue
                    
                    tile = self.tiles[x][y]
                    if not tile.blocked:
                        # Tile is walkable - this is invalid for a secret door
                        logger.warning(
                            f"Secret door at ({x}, {y}) is on a walkable floor tile, "
                            f"converting to normal door"
                        )
                        # Convert to normal (non-secret) door
                        door_comp.is_secret = False
                        door_comp.is_discovered = True
                        secret_doors_invalid.append(entity)
                    else:
                        # Verify it has at least one adjacent walkable tile
                        has_adjacent_walkable = False
                        for dx in [-1, 0, 1]:
                            for dy in [-1, 0, 1]:
                                if dx == 0 and dy == 0:
                                    continue
                                adj_x, adj_y = x + dx, y + dy
                                if self.is_in_bounds(adj_x, adj_y):
                                    if not self.tiles[adj_x][adj_y].blocked:
                                        has_adjacent_walkable = True
                                        break
                            if has_adjacent_walkable:
                                break
                        
                        if not has_adjacent_walkable:
                            logger.warning(
                                f"Secret door at ({x}, {y}) has no adjacent walkable tiles, "
                                f"removing it"
                            )
                            secret_doors_invalid.append(entity)
        
        # Remove invalid secret doors
        for entity in secret_doors_invalid:
            if entity in entities:
                entities.remove(entity)
                logger.debug(f"Removed invalid secret door from level {self.dungeon_level}")
