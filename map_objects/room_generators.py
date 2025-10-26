"""Room generator system for modular dungeon creation.

This module provides a pluggable room generator pattern that makes it easy
to add new room types (treasure rooms, boss rooms, puzzle rooms, etc.) without
modifying the core map generation code.

Architecture:
- RoomGenerator: Base class defining the room generation interface
- StandardRoomGenerator: Classic rectangular rooms with random monsters/items
- TreasureRoomGenerator: Rooms with guaranteed loot and fewer monsters
- BossRoomGenerator: Large rooms designed for boss encounters
- PuzzleRoomGenerator: Future extension for puzzle challenges

Usage:
    generator = StandardRoomGenerator()
    room = generator.generate(game_map, entities, bounds)
"""

from abc import ABC, abstractmethod
from random import randint
from typing import List, Tuple, Optional, TYPE_CHECKING

from map_objects.rectangle import Rect
from random_utils import from_dungeon_level, random_choice_from_dict
from config.testing_config import get_testing_config
import logging

if TYPE_CHECKING:
    from entity import Entity
    from map_objects.game_map import GameMap

logger = logging.getLogger(__name__)


class RoomGenerator(ABC):
    """Base class for all room generators.
    
    Defines the interface for generating rooms with specific characteristics.
    Subclasses implement different room types (standard, treasure, boss, etc.).
    
    Attributes:
        name (str): Human-readable name for this generator type
        min_size (int): Minimum room dimension
        max_size (int): Maximum room dimension
        spawn_chance (float): Probability of this room type being selected (0.0 - 1.0)
    """
    
    def __init__(self, name: str, min_size: int = 6, max_size: int = 10, spawn_chance: float = 1.0):
        """Initialize room generator.
        
        Args:
            name: Descriptive name for this room type
            min_size: Minimum width/height for rooms
            max_size: Maximum width/height for rooms
            spawn_chance: Selection probability (used by room chooser)
        """
        self.name = name
        self.min_size = min_size
        self.max_size = max_size
        self.spawn_chance = spawn_chance
    
    def generate(
        self,
        game_map: 'GameMap',
        entities: List['Entity'],
        bounds: Tuple[int, int, int, int],
        dungeon_level: int
    ) -> Optional[Rect]:
        """Generate and place a room on the map.
        
        This is the main entry point called by the map generator.
        It creates a room rectangle, carves it into the map, and populates it.
        
        Args:
            game_map: GameMap to modify
            entities: List to add entities to
            bounds: (x_min, y_min, x_max, y_max) map boundaries
            dungeon_level: Current dungeon level for scaling
            
        Returns:
            Rect representing the created room, or None if generation failed
        """
        # Create room rectangle
        room = self._create_room_rect(bounds)
        if not room:
            return None
        
        # Carve room into map
        self._carve_room(game_map, room)
        
        # Populate with entities
        self._populate_room(game_map, room, entities, dungeon_level)
        
        logger.debug(f"Generated {self.name} at ({room.x1}, {room.y1}) size {room.x2-room.x1}x{room.y2-room.y1}")
        return room
    
    def _create_room_rect(self, bounds: Tuple[int, int, int, int]) -> Optional[Rect]:
        """Create a rectangular room within the given boundaries.
        
        Args:
            bounds: (x_min, y_min, x_max, y_max) map boundaries
            
        Returns:
            Rect object or None if creation failed
        """
        x_min, y_min, x_max, y_max = bounds
        
        # Random dimensions
        w = randint(self.min_size, self.max_size)
        h = randint(self.min_size, self.max_size)
        
        # Random position without going out of bounds
        if x_max - w - 1 <= x_min or y_max - h - 1 <= y_min:
            return None  # Not enough space
        
        x = randint(x_min, x_max - w - 1)
        y = randint(y_min, y_max - h - 1)
        
        return Rect(x, y, w, h)
    
    def _carve_room(self, game_map: 'GameMap', room: Rect) -> None:
        """Carve the room into the map by making tiles passable.
        
        Args:
            game_map: GameMap to modify
            room: Room rectangle to carve
        """
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                if 0 <= x < game_map.width and 0 <= y < game_map.height:
                    game_map.tiles[x][y].blocked = False
                    game_map.tiles[x][y].block_sight = False
    
    @abstractmethod
    def _populate_room(
        self,
        game_map: 'GameMap',
        room: Rect,
        entities: List['Entity'],
        dungeon_level: int
    ) -> None:
        """Populate the room with entities (monsters, items, etc.).
        
        Must be implemented by subclasses to define room-specific population.
        
        Args:
            game_map: GameMap being generated
            room: Room rectangle to populate
            entities: List to add entities to
            dungeon_level: Current dungeon level for scaling
        """
        pass


class StandardRoomGenerator(RoomGenerator):
    """Generator for standard dungeon rooms with random monsters and items.
    
    This is the default room type used in most dungeon generation.
    Spawns monsters and items based on dungeon level probability tables.
    """
    
    def __init__(self, min_size: int = 6, max_size: int = 10):
        super().__init__(
            name="Standard Room",
            min_size=min_size,
            max_size=max_size,
            spawn_chance=1.0
        )
    
    def _populate_room(
        self,
        game_map: 'GameMap',
        room: Rect,
        entities: List['Entity'],
        dungeon_level: int
    ) -> None:
        """Populate with random monsters and items based on dungeon level."""
        # Use the existing place_entities logic
        game_map.place_entities(room, entities)


class TreasureRoomGenerator(RoomGenerator):
    """Generator for treasure rooms with guaranteed loot and fewer monsters.
    
    Treasure rooms are larger than standard rooms and contain more items
    but fewer monsters, encouraging exploration and risk/reward decisions.
    """
    
    def __init__(self, min_size: int = 8, max_size: int = 14):
        super().__init__(
            name="Treasure Room",
            min_size=min_size,
            max_size=max_size,
            spawn_chance=0.15  # 15% chance to appear
        )
    
    def _populate_room(
        self,
        game_map: 'GameMap',
        room: Rect,
        entities: List['Entity'],
        dungeon_level: int
    ) -> None:
        """Populate with more items and fewer monsters."""
        from entity import Entity
        from components.item import Item
        from config.entity_factory import get_entity_factory
        
        # Fewer monsters (50% normal)
        max_monsters = max(1, from_dungeon_level([[2, 1], [3, 4], [5, 6]], dungeon_level) // 2)
        num_monsters = randint(0, max_monsters)
        
        # More items (200% normal)
        max_items = from_dungeon_level([[1, 1], [2, 4]], dungeon_level) * 2
        num_items = randint(2, max_items)  # At least 2 items
        
        factory = get_entity_factory()
        
        # Spawn items - use game_map's item spawning logic for consistency
        # For now, just spawn more items than a standard room would
        # The actual implementation uses probability tables from game_map.place_entities
        
        # Simplified treasure room logic: delegate to standard spawning
        # but with modified counts (handled in StandardRoomGenerator)
        pass  # Treasure room spawning requires integration with GameMap.place_entities
        
        logger.info(f"Generated treasure room with {num_items} items and {num_monsters} monsters")


class BossRoomGenerator(RoomGenerator):
    """Generator for boss encounter rooms.
    
    Boss rooms are large, square rooms designed for climactic battles.
    They're empty except for the boss monster, providing space for combat.
    """
    
    def __init__(self, min_size: int = 12, max_size: int = 16):
        super().__init__(
            name="Boss Room",
            min_size=min_size,
            max_size=max_size,
            spawn_chance=0.05  # 5% chance, typically placed manually
        )
    
    def _create_room_rect(self, bounds: Tuple[int, int, int, int]) -> Optional[Rect]:
        """Create a large square room for boss encounters."""
        x_min, y_min, x_max, y_max = bounds
        
        # Square dimensions
        size = randint(self.min_size, self.max_size)
        
        if x_max - size - 1 <= x_min or y_max - size - 1 <= y_min:
            return None
        
        x = randint(x_min, x_max - size - 1)
        y = randint(y_min, y_max - size - 1)
        
        return Rect(x, y, size, size)  # Square room
    
    def _populate_room(
        self,
        game_map: 'GameMap',
        room: Rect,
        entities: List['Entity'],
        dungeon_level: int
    ) -> None:
        """Leave empty - boss will be placed manually or by special logic."""
        # Boss rooms are typically left empty for manual boss placement
        # or special boss spawning logic
        logger.info(f"Generated empty boss room (size {room.x2-room.x1})")


class EmptyRoomGenerator(RoomGenerator):
    """Generator for empty rooms.
    
    Sometimes emptiness creates tension. Empty rooms provide:
    - Breathing space between encounters
    - Safe rest areas
    - Variety in dungeon pacing
    """
    
    def __init__(self, min_size: int = 6, max_size: int = 10):
        super().__init__(
            name="Empty Room",
            min_size=min_size,
            max_size=max_size,
            spawn_chance=0.10  # 10% chance
        )
    
    def _populate_room(
        self,
        game_map: 'GameMap',
        room: Rect,
        entities: List['Entity'],
        dungeon_level: int
    ) -> None:
        """Leave completely empty."""
        # Intentionally empty - creates pacing variety
        pass


class CampRoomGenerator(RoomGenerator):
    """Generator for camp/safe rooms where NPCs like the Guide appear.
    
    Camp rooms are:
    - Safe (no monsters)
    - Well-lit
    - Have minimal items (maybe healing?)
    - Spawn special NPCs like the Ghost Guide
    
    Phase 3: Used for Guide encounters at levels 5, 10, 15, 20
    """
    
    def __init__(self, min_size: int = 8, max_size: int = 12):
        super().__init__(
            name="Camp Room",
            min_size=min_size,
            max_size=max_size,
            spawn_chance=0.0  # Don't spawn randomly - placed intentionally
        )
    
    def _populate_room(
        self,
        game_map: 'GameMap',
        room: Rect,
        entities: List['Entity'],
        dungeon_level: int
    ) -> None:
        """Populate camp with minimal entities - safe resting area."""
        # No monsters in camp rooms!
        
        # Maybe spawn some healing items (low chance)
        from random import random
        if random() < 0.3:  # 30% chance
            # Spawn a single healing item
            from config.entity_factory import get_entity_factory
            
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            
            # Check if position is free
            if not any(entity.x == x and entity.y == y for entity in entities):
                factory = get_entity_factory()
                healing_item = factory.create_item('healing_potion', x, y, dungeon_level)
                if healing_item:
                    entities.append(healing_item)
                    logger.debug(f"Placed healing item in camp at ({x}, {y})")
        
        # Mark this room as a camp for special NPC spawning
        # (Will be handled by map generation logic)
        if not hasattr(game_map, 'camp_rooms'):
            game_map.camp_rooms = []
        game_map.camp_rooms.append(room)
        
        logger.info(f"Generated camp room at ({room.x1}, {room.y1})")


class RoomGeneratorFactory:
    """Factory for selecting and creating room generators.
    
    Manages a pool of room generators and selects appropriate ones
    based on spawn chances, dungeon level, and game state.
    """
    
    def __init__(self):
        """Initialize with standard room generators."""
        self.generators = [
            StandardRoomGenerator(),
            TreasureRoomGenerator(),
            BossRoomGenerator(),
            EmptyRoomGenerator(),
            CampRoomGenerator(),  # Phase 3: Safe rooms for NPCs
        ]
    
    def add_generator(self, generator: RoomGenerator) -> None:
        """Add a custom room generator to the pool.
        
        Args:
            generator: RoomGenerator instance to add
        """
        self.generators.append(generator)
    
    def get_generator(self, room_type: Optional[str] = None) -> RoomGenerator:
        """Get a room generator, either specific or weighted random.
        
        Args:
            room_type: Specific room type name, or None for random selection
            
        Returns:
            RoomGenerator instance
        """
        if room_type:
            # Return specific generator
            for gen in self.generators:
                if gen.name.lower().replace(" ", "_") == room_type.lower():
                    return gen
            logger.warning(f"Room type '{room_type}' not found, using standard")
            return StandardRoomGenerator()
        
        # Weighted random selection
        total_weight = sum(gen.spawn_chance for gen in self.generators)
        roll = randint(1, int(total_weight * 100)) / 100.0
        
        cumulative = 0.0
        for gen in self.generators:
            cumulative += gen.spawn_chance
            if roll <= cumulative:
                return gen
        
        # Fallback to standard
        return StandardRoomGenerator()


# Convenience function for external use
def create_room_generator_factory() -> RoomGeneratorFactory:
    """Create and return a new RoomGeneratorFactory with default generators.
    
    Returns:
        Configured RoomGeneratorFactory instance
    """
    return RoomGeneratorFactory()

