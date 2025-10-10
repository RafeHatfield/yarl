"""Tests for the room generator system."""

import pytest
from unittest.mock import Mock, patch

from map_objects.room_generators import (
    RoomGenerator,
    StandardRoomGenerator,
    TreasureRoomGenerator,
    BossRoomGenerator,
    EmptyRoomGenerator,
    RoomGeneratorFactory,
    create_room_generator_factory
)
from map_objects.game_map import GameMap
from map_objects.rectangle import Rect


class TestRoomGeneratorBase:
    """Tests for base RoomGenerator functionality."""
    
    def test_room_generator_initialization(self):
        """Test basic room generator creation."""
        gen = StandardRoomGenerator()
        assert gen.name == "Standard Room"
        assert gen.min_size == 6
        assert gen.max_size == 10
        assert gen.spawn_chance == 1.0
    
    def test_room_generator_custom_sizes(self):
        """Test creating generator with custom sizes."""
        gen = TreasureRoomGenerator(min_size=10, max_size=15)
        assert gen.min_size == 10
        assert gen.max_size == 15


class TestStandardRoomGenerator:
    """Tests for standard room generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.game_map = GameMap(50, 50, dungeon_level=1)
        self.entities = []
        self.bounds = (0, 0, 50, 50)
        self.generator = StandardRoomGenerator()
    
    def test_generate_standard_room(self):
        """Test generating a standard room."""
        room = self.generator.generate(
            self.game_map,
            self.entities,
            self.bounds,
            dungeon_level=1
        )
        
        assert room is not None, "Room should be generated"
        assert isinstance(room, Rect), "Should return a Rect"
        assert room.x2 > room.x1, "Room should have width"
        assert room.y2 > room.y1, "Room should have height"
    
    def test_room_carved_into_map(self):
        """Test that room tiles are made passable."""
        room = self.generator.generate(
            self.game_map,
            self.entities,
            self.bounds,
            dungeon_level=1
        )
        
        # Check center of room is passable
        center_x, center_y = room.center()
        assert not self.game_map.tiles[center_x][center_y].blocked, \
            "Room center should be passable"
        assert not self.game_map.tiles[center_x][center_y].block_sight, \
            "Room center should not block sight"
    
    def test_room_contains_entities(self):
        """Test that standard rooms spawn entities."""
        initial_count = len(self.entities)
        
        room = self.generator.generate(
            self.game_map,
            self.entities,
            self.bounds,
            dungeon_level=1
        )
        
        # Standard rooms should spawn at least some entities
        # (may be 0 due to randomness, so we test multiple rooms)
        rooms_with_entities = 0
        for _ in range(10):
            entities_before = len(self.entities)
            self.generator.generate(
                self.game_map,
                self.entities,
                self.bounds,
                dungeon_level=1
            )
            if len(self.entities) > entities_before:
                rooms_with_entities += 1
        
        assert rooms_with_entities > 0, "At least some rooms should spawn entities"


class TestTreasureRoomGenerator:
    """Tests for treasure room generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.game_map = GameMap(60, 60, dungeon_level=1)
        self.entities = []
        self.bounds = (0, 0, 60, 60)
        self.generator = TreasureRoomGenerator()
    
    def test_treasure_room_larger_than_standard(self):
        """Test that treasure rooms tend to be larger."""
        room = self.generator.generate(
            self.game_map,
            self.entities,
            self.bounds,
            dungeon_level=1
        )
        
        assert room is not None
        # Treasure rooms have min_size=8 vs standard min_size=6
        width = room.x2 - room.x1
        height = room.y2 - room.y1
        assert width >= 8 or height >= 8, "Treasure room should use larger min size"
    
    def test_treasure_room_has_more_items(self):
        """Test that treasure rooms spawn more items."""
        initial_count = len(self.entities)
        
        # Generate treasure room
        room = self.generator.generate(
            self.game_map,
            self.entities,
            self.bounds,
            dungeon_level=5  # Higher level for more spawns
        )
        
        # Count items
        from components.item import Item
        items = [e for e in self.entities if hasattr(e, 'item') and e.item]
        
        # Treasure rooms should guarantee at least 2 items
        assert len(items) >= 2, "Treasure room should have at least 2 items"


class TestBossRoomGenerator:
    """Tests for boss room generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.game_map = GameMap(60, 60, dungeon_level=1)
        self.entities = []
        self.bounds = (0, 0, 60, 60)
        self.generator = BossRoomGenerator()
    
    def test_boss_room_is_square(self):
        """Test that boss rooms are square."""
        room = self.generator.generate(
            self.game_map,
            self.entities,
            self.bounds,
            dungeon_level=1
        )
        
        assert room is not None
        width = room.x2 - room.x1
        height = room.y2 - room.y1
        assert width == height, "Boss room should be square"
    
    def test_boss_room_is_large(self):
        """Test that boss rooms are large."""
        room = self.generator.generate(
            self.game_map,
            self.entities,
            self.bounds,
            dungeon_level=1
        )
        
        size = room.x2 - room.x1
        assert size >= 12, "Boss room should be at least 12x12"
    
    def test_boss_room_empty(self):
        """Test that boss rooms don't auto-spawn entities."""
        initial_count = len(self.entities)
        
        room = self.generator.generate(
            self.game_map,
            self.entities,
            self.bounds,
            dungeon_level=1
        )
        
        # Boss rooms should be empty (boss placed manually)
        assert len(self.entities) == initial_count, \
            "Boss room should not auto-spawn entities"


class TestEmptyRoomGenerator:
    """Tests for empty room generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.game_map = GameMap(50, 50, dungeon_level=1)
        self.entities = []
        self.bounds = (0, 0, 50, 50)
        self.generator = EmptyRoomGenerator()
    
    def test_empty_room_has_no_entities(self):
        """Test that empty rooms spawn nothing."""
        initial_count = len(self.entities)
        
        room = self.generator.generate(
            self.game_map,
            self.entities,
            self.bounds,
            dungeon_level=1
        )
        
        assert len(self.entities) == initial_count, \
            "Empty room should spawn no entities"


class TestRoomGeneratorFactory:
    """Tests for room generator factory."""
    
    def test_factory_initialization(self):
        """Test factory creates with default generators."""
        factory = RoomGeneratorFactory()
        assert len(factory.generators) == 4, "Should have 4 default generators"
        
        names = [g.name for g in factory.generators]
        assert "Standard Room" in names
        assert "Treasure Room" in names
        assert "Boss Room" in names
        assert "Empty Room" in names
    
    def test_add_custom_generator(self):
        """Test adding custom generator to factory."""
        factory = RoomGeneratorFactory()
        
        # Create custom generator
        custom = StandardRoomGenerator()
        custom.name = "Custom Room"
        
        factory.add_generator(custom)
        assert len(factory.generators) == 5, "Should have 5 generators"
    
    def test_get_specific_generator(self):
        """Test retrieving specific generator by name."""
        factory = RoomGeneratorFactory()
        
        gen = factory.get_generator("treasure_room")
        assert gen.name == "Treasure Room"
        
        gen = factory.get_generator("boss_room")
        assert gen.name == "Boss Room"
    
    def test_get_random_generator(self):
        """Test weighted random generator selection."""
        factory = RoomGeneratorFactory()
        
        # Get 100 random generators and verify distribution
        generated = [factory.get_generator() for _ in range(100)]
        names = [g.name for g in generated]
        
        # Standard rooms should dominate (spawn_chance=1.0)
        assert names.count("Standard Room") > 50, \
            "Standard rooms should be most common"
        
        # Should get some variety
        unique_types = len(set(names))
        assert unique_types >= 2, "Should get at least 2 different room types"
    
    def test_factory_convenience_function(self):
        """Test convenience function for factory creation."""
        factory = create_room_generator_factory()
        assert isinstance(factory, RoomGeneratorFactory)
        assert len(factory.generators) > 0


class TestRoomGeneratorIntegration:
    """Integration tests for room generator system."""
    
    def test_generate_multiple_rooms(self):
        """Test generating multiple rooms without collisions."""
        game_map = GameMap(80, 80, dungeon_level=1)
        entities = []
        factory = RoomGeneratorFactory()
        
        rooms = []
        for _ in range(10):
            gen = factory.get_generator()
            room = gen.generate(
                game_map,
                entities,
                (0, 0, 80, 80),
                dungeon_level=1
            )
            if room:
                rooms.append(room)
        
        assert len(rooms) > 0, "Should generate at least some rooms"
        
        # Verify rooms don't overlap (except borders)
        for i, room1 in enumerate(rooms):
            for room2 in rooms[i+1:]:
                # Rooms can touch at borders but shouldn't deeply overlap
                overlap_x = min(room1.x2, room2.x2) - max(room1.x1, room2.x1)
                overlap_y = min(room1.y2, room2.y2) - max(room1.y1, room2.y1)
                
                # Small overlap (1-2 tiles) is OK for tunnels
                if overlap_x > 0 and overlap_y > 0:
                    assert overlap_x <= 3 and overlap_y <= 3, \
                        "Rooms should not deeply overlap"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

