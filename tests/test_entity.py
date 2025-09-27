"""
Unit tests for entity.py

Tests Entity class functionality including movement, distance calculations, and pathfinding.
"""

import pytest
from unittest.mock import Mock, patch
import math
from entity import Entity, get_blocking_entities_at_location
from components.ai import BasicMonster, ConfusedMonster
from components.fighter import Fighter
from components.inventory import Inventory
from render_functions import RenderOrder


class TestEntityBasics:
    """Test basic Entity functionality."""

    def test_entity_creation(self, mock_libtcod):
        """Test basic entity creation."""
        # Act
        entity = Entity(5, 10, "@", mock_libtcod.white, "Test Entity")

        # Assert
        assert entity.x == 5
        assert entity.y == 10
        assert entity.char == "@"
        assert entity.color == mock_libtcod.white
        assert entity.name == "Test Entity"
        assert entity.blocks is False  # Default value
        assert entity.fighter is None
        assert entity.inventory is None
        assert entity.ai is None
        assert entity.item is None

    def test_entity_with_components(self, mock_libtcod):
        """Test entity creation with components."""
        # Arrange
        fighter = Fighter(hp=30, defense=2, power=5)
        inventory = Inventory(26)

        # Act
        entity = Entity(
            x=0,
            y=0,
            char="@",
            color=mock_libtcod.white,
            name="Player",
            blocks=True,
            render_order=RenderOrder.ACTOR,
            fighter=fighter,
            inventory=inventory,
        )

        # Assert
        assert entity.blocks is True
        assert entity.render_order == RenderOrder.ACTOR
        assert entity.fighter == fighter
        assert entity.inventory == inventory
        assert fighter.owner == entity
        assert inventory.owner == entity

    def test_entity_move(self, mock_libtcod):
        """Test entity movement."""
        # Arrange
        entity = Entity(10, 10, "@", mock_libtcod.white, "Test")

        # Act
        entity.move(3, -2)

        # Assert
        assert entity.x == 13
        assert entity.y == 8

    def test_entity_move_zero(self, mock_libtcod):
        """Test entity movement with zero displacement."""
        # Arrange
        entity = Entity(10, 10, "@", mock_libtcod.white, "Test")

        # Act
        entity.move(0, 0)

        # Assert
        assert entity.x == 10
        assert entity.y == 10

    def test_entity_move_negative(self, mock_libtcod):
        """Test entity movement with negative values."""
        # Arrange
        entity = Entity(10, 10, "@", mock_libtcod.white, "Test")

        # Act
        entity.move(-5, -3)

        # Assert
        assert entity.x == 5
        assert entity.y == 7


class TestEntityDistance:
    """Test Entity distance calculations."""

    def test_distance_to_same_position(self, mock_libtcod):
        """Test distance calculation to same position."""
        # Arrange
        entity1 = Entity(10, 10, "@", mock_libtcod.white, "Entity1")
        entity2 = Entity(10, 10, "o", mock_libtcod.red, "Entity2")

        # Act
        distance = entity1.distance_to(entity2)

        # Assert
        assert distance == 0.0

    def test_distance_to_adjacent(self, mock_libtcod):
        """Test distance calculation to adjacent entity."""
        # Arrange
        entity1 = Entity(10, 10, "@", mock_libtcod.white, "Entity1")
        entity2 = Entity(11, 10, "o", mock_libtcod.red, "Entity2")

        # Act
        distance = entity1.distance_to(entity2)

        # Assert
        assert distance == 1.0

    def test_distance_to_diagonal(self, mock_libtcod):
        """Test distance calculation to diagonal entity."""
        # Arrange
        entity1 = Entity(0, 0, "@", mock_libtcod.white, "Entity1")
        entity2 = Entity(3, 4, "o", mock_libtcod.red, "Entity2")

        # Act
        distance = entity1.distance_to(entity2)

        # Assert
        assert distance == 5.0  # 3-4-5 triangle

    def test_distance_coordinates(self, mock_libtcod):
        """Test distance calculation to specific coordinates."""
        # Arrange
        entity = Entity(0, 0, "@", mock_libtcod.white, "Entity")

        # Act
        distance = entity.distance(6, 8)

        # Assert
        assert distance == 10.0  # 6-8-10 triangle

    def test_distance_negative_coordinates(self, mock_libtcod):
        """Test distance calculation with negative coordinates."""
        # Arrange
        entity = Entity(5, 5, "@", mock_libtcod.white, "Entity")

        # Act
        distance = entity.distance(-1, 1)

        # Assert
        expected = math.sqrt(36 + 16)  # sqrt((5-(-1))^2 + (5-1)^2) = sqrt(36+16)
        assert abs(distance - expected) < 0.001


class TestEntityPathfinding:
    """Test Entity pathfinding and movement towards targets."""

    @patch("entity.libtcod")
    def test_move_towards_adjacent_target(self, mock_tcod, mock_libtcod):
        """Test moving towards an adjacent target."""
        # Arrange
        entity = Entity(10, 10, "@", mock_libtcod.white, "Entity")
        target_x, target_y = 11, 10
        mock_game_map = Mock()
        mock_game_map.is_blocked = Mock(return_value=False)  # Mock game_map.is_blocked
        entities = []

        # Act
        entity.move_towards(target_x, target_y, mock_game_map, entities)

        # Assert
        assert entity.x == 11
        assert entity.y == 10
        mock_game_map.is_blocked.assert_called()

    @patch("entity.libtcod")
    def test_move_towards_diagonal_target(self, mock_tcod, mock_libtcod):
        """Test moving towards a diagonal target."""
        # Arrange
        entity = Entity(10, 10, "@", mock_libtcod.white, "Entity")
        target_x, target_y = 15, 15
        mock_game_map = Mock()
        mock_game_map.is_blocked = Mock(return_value=False)  # Mock game_map.is_blocked
        entities = []

        # Act
        entity.move_towards(target_x, target_y, mock_game_map, entities)

        # Assert
        # Should move one step towards target
        assert entity.x in [10, 11]
        assert entity.y in [10, 11]
        # Should be closer to target
        new_distance = entity.distance(target_x, target_y)
        original_distance = math.sqrt(25 + 25)  # Distance from (10,10) to (15,15)
        assert new_distance < original_distance
        mock_game_map.is_blocked.assert_called()

    @patch("entity.libtcod")
    def test_move_towards_same_position(self, mock_tcod, mock_libtcod):
        """Test moving towards same position causes division by zero error."""
        # Arrange
        entity = Entity(10, 10, "@", mock_libtcod.white, "Entity")
        target_x, target_y = 10, 10
        mock_game_map = Mock()
        entities = []

        # Act & Assert - current implementation has division by zero bug
        with pytest.raises(ZeroDivisionError):
            entity.move_towards(target_x, target_y, mock_game_map, entities)

    @patch("entity.libtcod")
    def test_move_astar_pathfinding(self, mock_tcod, mock_libtcod):
        """Test A* pathfinding functionality."""
        # Arrange
        entity = Entity(10, 10, "@", mock_libtcod.white, "Entity")
        target = Entity(15, 15, "T", mock_libtcod.red, "Target")
        mock_game_map = Mock()
        mock_game_map.width = 80
        mock_game_map.height = 50

        # Create proper mock tiles structure
        mock_tile = Mock()
        mock_tile.block_sight = False
        mock_tile.blocked = False
        # Create a 2D array structure that game_map expects
        mock_game_map.tiles = [[mock_tile for _ in range(50)] for _ in range(80)]
        entities = []

        # Mock tcod pathfinding functions
        mock_path = Mock()
        mock_tcod.map_new.return_value = Mock()
        mock_tcod.map_set_properties.return_value = None
        mock_tcod.path_new_using_map.return_value = mock_path
        mock_tcod.path_compute.return_value = None
        mock_tcod.path_is_empty.return_value = False
        mock_tcod.path_size.return_value = 5
        mock_tcod.path_walk.return_value = (11, 11)
        mock_tcod.path_delete.return_value = None

        # Act
        entity.move_astar(target, entities, mock_game_map)

        # Assert
        assert entity.x == 11
        assert entity.y == 11
        mock_tcod.path_new_using_map.assert_called()
        mock_tcod.path_compute.assert_called()
        mock_tcod.path_walk.assert_called()
        mock_tcod.path_delete.assert_called()

    @patch("entity.libtcod")
    def test_move_astar_no_path(self, mock_tcod, mock_libtcod):
        """Test A* pathfinding when no path exists (falls back to move_towards)."""
        # Arrange
        entity = Entity(10, 10, "@", mock_libtcod.white, "Entity")
        target = Entity(15, 15, "T", mock_libtcod.red, "Target")
        mock_game_map = Mock()
        mock_game_map.width = 80
        mock_game_map.height = 50
        mock_game_map.is_blocked = Mock(return_value=False)  # Mock game_map.is_blocked

        # Create proper mock tiles structure
        mock_tile = Mock()
        mock_tile.block_sight = False
        mock_tile.blocked = False
        mock_game_map.tiles = [[mock_tile for _ in range(50)] for _ in range(80)]
        entities = []

        # Mock tcod pathfinding functions - no path available
        mock_path = Mock()
        mock_tcod.map_new.return_value = Mock()
        mock_tcod.map_set_properties.return_value = None
        mock_tcod.path_new_using_map.return_value = mock_path
        mock_tcod.path_compute.return_value = None
        mock_tcod.path_is_empty.return_value = True  # No path found
        mock_tcod.path_delete.return_value = None

        # Act
        entity.move_astar(target, entities, mock_game_map)

        # Assert
        # Should fall back to basic movement towards target
        assert entity.x in [10, 11]
        assert entity.y in [10, 11]
        mock_game_map.is_blocked.assert_called()

    @patch("entity.libtcod")
    def test_move_astar_path_too_long(self, mock_tcod, mock_libtcod):
        """Test A* pathfinding when path is too long (falls back to move_towards)."""
        # Arrange
        entity = Entity(10, 10, "@", mock_libtcod.white, "Entity")
        target = Entity(50, 50, "T", mock_libtcod.red, "Target")
        mock_game_map = Mock()
        mock_game_map.width = 80
        mock_game_map.height = 50
        mock_game_map.is_blocked = Mock(return_value=False)  # Mock game_map.is_blocked

        # Create proper mock tiles structure
        mock_tile = Mock()
        mock_tile.block_sight = False
        mock_tile.blocked = False
        mock_game_map.tiles = [[mock_tile for _ in range(50)] for _ in range(80)]
        entities = []

        # Mock tcod pathfinding functions - path too long
        mock_path = Mock()
        mock_tcod.map_new.return_value = Mock()
        mock_tcod.map_set_properties.return_value = None
        mock_tcod.path_new_using_map.return_value = mock_path
        mock_tcod.path_compute.return_value = None
        mock_tcod.path_is_empty.return_value = False
        mock_tcod.path_size.return_value = 30  # Too long (>25)
        mock_tcod.path_delete.return_value = None

        # Act
        entity.move_astar(target, entities, mock_game_map)

        # Assert
        # Should fall back to basic movement towards target
        distance_before = math.sqrt((50 - 10) ** 2 + (50 - 10) ** 2)
        distance_after = entity.distance(50, 50)
        assert distance_after < distance_before
        mock_game_map.is_blocked.assert_called()


class TestGetBlockingEntities:
    """Test get_blocking_entities_at_location function."""

    def test_get_blocking_entity_found(self, mock_libtcod):
        """Test finding a blocking entity at specific location."""
        # Arrange
        entity1 = Entity(10, 10, "@", mock_libtcod.white, "Player", blocks=False)
        entity2 = Entity(15, 15, "o", mock_libtcod.red, "Orc", blocks=True)
        entity3 = Entity(20, 20, "#", mock_libtcod.brown, "Wall", blocks=True)
        entities = [entity1, entity2, entity3]

        # Act
        blocking_entity = get_blocking_entities_at_location(entities, 15, 15)

        # Assert
        assert blocking_entity == entity2

    def test_get_blocking_entity_not_found(self, mock_libtcod):
        """Test when no blocking entity exists at location."""
        # Arrange
        entity1 = Entity(10, 10, "@", mock_libtcod.white, "Player", blocks=False)
        entity2 = Entity(15, 15, "o", mock_libtcod.red, "Orc", blocks=True)
        entities = [entity1, entity2]

        # Act
        blocking_entity = get_blocking_entities_at_location(entities, 5, 5)

        # Assert
        assert blocking_entity is None

    def test_get_blocking_entity_non_blocking_at_location(self, mock_libtcod):
        """Test when non-blocking entity exists at location."""
        # Arrange
        entity1 = Entity(10, 10, "@", mock_libtcod.white, "Player", blocks=False)
        entity2 = Entity(15, 15, "!", mock_libtcod.violet, "Potion", blocks=False)
        entities = [entity1, entity2]

        # Act
        blocking_entity = get_blocking_entities_at_location(entities, 15, 15)

        # Assert
        assert blocking_entity is None

    def test_get_blocking_entity_multiple_at_location(self, mock_libtcod):
        """Test when multiple entities exist at same location."""
        # Arrange
        entity1 = Entity(15, 15, "!", mock_libtcod.violet, "Potion", blocks=False)
        entity2 = Entity(15, 15, "o", mock_libtcod.red, "Orc", blocks=True)
        entity3 = Entity(15, 15, "#", mock_libtcod.brown, "Wall", blocks=True)
        entities = [entity1, entity2, entity3]

        # Act
        blocking_entity = get_blocking_entities_at_location(entities, 15, 15)

        # Assert
        # Should return the first blocking entity found
        assert blocking_entity in [entity2, entity3]
        assert blocking_entity.blocks is True

    def test_get_blocking_entity_empty_list(self, mock_libtcod):
        """Test with empty entities list."""
        # Arrange
        entities = []

        # Act
        blocking_entity = get_blocking_entities_at_location(entities, 10, 10)

        # Assert
        assert blocking_entity is None


class TestEntityEdgeCases:
    """Test edge cases and error conditions for Entity class."""

    def test_entity_with_extreme_coordinates(self, mock_libtcod):
        """Test entity creation with extreme coordinate values."""
        # Act & Assert - should not raise exceptions
        entity1 = Entity(-1000, -1000, "@", mock_libtcod.white, "Test")
        assert entity1.x == -1000
        assert entity1.y == -1000

        entity2 = Entity(999999, 999999, "@", mock_libtcod.white, "Test")
        assert entity2.x == 999999
        assert entity2.y == 999999

    def test_entity_distance_to_none(self, mock_libtcod):
        """Test distance calculation with None target."""
        # Arrange
        entity = Entity(10, 10, "@", mock_libtcod.white, "Test")

        # Act & Assert
        with pytest.raises(AttributeError):
            entity.distance_to(None)

    def test_entity_with_none_components(self, mock_libtcod):
        """Test entity with explicitly None components."""
        # Act
        entity = Entity(
            x=0,
            y=0,
            char="@",
            color=mock_libtcod.white,
            name="Test",
            fighter=None,
            inventory=None,
            ai=None,
            item=None,
        )

        # Assert
        assert entity.fighter is None
        assert entity.inventory is None
        assert entity.ai is None
        assert entity.item is None


class TestBasicMonsterAI:
    """Test BasicMonster AI behavior."""

    def test_basic_monster_creation(self, mock_libtcod):
        """Test basic monster AI creation."""
        # Act
        ai = BasicMonster()

        # Assert
        assert ai is not None
        # Note: BasicMonster doesn't have owner attribute until assigned

    def test_basic_monster_out_of_fov_no_action(self, mock_libtcod):
        """Test basic monster does nothing when target is out of FOV."""
        # Arrange
        ai = BasicMonster()
        monster = Entity(10, 10, "o", mock_libtcod.red, "Orc", ai=ai)
        target = Entity(20, 20, "@", mock_libtcod.white, "Player")
        mock_fov_map = Mock()
        mock_game_map = Mock()
        entities = []

        # Mock FOV check to return False (monster can't see target)
        with patch("components.ai.libtcod") as mock_tcod:
            mock_tcod.map_is_in_fov.return_value = False

            # Act
            results = ai.take_turn(target, mock_fov_map, mock_game_map, entities)

        # Assert
        assert len(results) == 0
        mock_tcod.map_is_in_fov.assert_called_once_with(mock_fov_map, 10, 10)

    @patch("entity.libtcod")
    def test_basic_monster_moves_when_far_from_target(self, mock_tcod, mock_libtcod):
        """Test basic monster moves towards target when distance >= 2."""
        # Arrange
        ai = BasicMonster()
        fighter = Fighter(hp=10, defense=0, power=3)
        monster = Entity(10, 10, "o", mock_libtcod.red, "Orc", ai=ai, fighter=fighter)
        target = Entity(15, 15, "@", mock_libtcod.white, "Player")
        mock_fov_map = Mock()
        mock_game_map = Mock()
        mock_game_map.width = 80
        mock_game_map.height = 50

        # Create proper mock tiles structure for A* pathfinding
        mock_tile = Mock()
        mock_tile.block_sight = False
        mock_tile.blocked = False
        mock_game_map.tiles = [[mock_tile for _ in range(50)] for _ in range(80)]
        entities = []

        # Mock FOV and pathfinding
        mock_tcod.map_is_in_fov.return_value = True
        mock_path = Mock()
        mock_tcod.map_new.return_value = Mock()
        mock_tcod.map_set_properties.return_value = None
        mock_tcod.path_new_using_map.return_value = mock_path
        mock_tcod.path_compute.return_value = None
        mock_tcod.path_is_empty.return_value = False
        mock_tcod.path_size.return_value = 5
        mock_tcod.path_walk.return_value = (11, 11)
        mock_tcod.path_delete.return_value = None

        # Act
        results = ai.take_turn(target, mock_fov_map, mock_game_map, entities)

        # Assert
        assert len(results) == 0  # No attack, just movement
        assert monster.x == 11  # Monster moved via A*
        assert monster.y == 11

    def test_basic_monster_attacks_when_adjacent(self, mock_libtcod):
        """Test basic monster attacks when adjacent to target."""
        # Arrange
        ai = BasicMonster()
        monster_fighter = Fighter(hp=10, defense=0, power=5)
        monster = Entity(
            10, 10, "o", mock_libtcod.red, "Orc", ai=ai, fighter=monster_fighter
        )

        target_fighter = Fighter(hp=20, defense=1, power=3)
        target = Entity(
            11, 10, "@", mock_libtcod.white, "Player", fighter=target_fighter
        )

        mock_fov_map = Mock()
        mock_game_map = Mock()
        entities = []

        # Mock FOV check
        with patch("components.ai.libtcod") as mock_tcod:
            mock_tcod.map_is_in_fov.return_value = True
            mock_tcod.white = mock_libtcod.white

            # Act
            results = ai.take_turn(target, mock_fov_map, mock_game_map, entities)

        # Assert
        assert len(results) >= 1  # Should have attack result
        assert target.fighter.hp < 20  # Target should take damage


class TestConfusedMonsterAI:
    """Test ConfusedMonster AI behavior."""

    def test_confused_monster_creation(self, mock_libtcod):
        """Test confused monster AI creation."""
        # Arrange
        previous_ai = BasicMonster()

        # Act
        confused_ai = ConfusedMonster(previous_ai, number_of_turns=5)

        # Assert
        assert confused_ai.previous_ai == previous_ai
        assert confused_ai.number_of_turns == 5

    def test_confused_monster_default_turns(self, mock_libtcod):
        """Test confused monster AI with default number of turns."""
        # Arrange
        previous_ai = BasicMonster()

        # Act
        confused_ai = ConfusedMonster(previous_ai)

        # Assert
        assert confused_ai.number_of_turns == 10

    @patch("components.ai.randint")
    @patch("entity.libtcod")
    def test_confused_monster_random_movement(
        self, mock_tcod, mock_randint, mock_libtcod
    ):
        """Test confused monster moves randomly."""
        # Arrange
        previous_ai = BasicMonster()
        confused_ai = ConfusedMonster(previous_ai, number_of_turns=3)
        monster = Entity(10, 10, "o", mock_libtcod.red, "Confused Orc", ai=confused_ai)
        target = Entity(15, 15, "@", mock_libtcod.white, "Player")
        mock_fov_map = Mock()
        mock_game_map = Mock()
        mock_game_map.is_blocked = Mock(return_value=False)
        entities = []

        # Mock random movement: randint(0, 2) returns 0, 1, 2
        # So random_x = 10 + 0 - 1 = 9, random_y = 10 + 2 - 1 = 11 (different from current)
        mock_randint.side_effect = [0, 2]  # First call returns 0, second returns 2

        # Act
        results = confused_ai.take_turn(target, mock_fov_map, mock_game_map, entities)

        # Assert
        assert len(results) == 0  # No messages during confusion
        assert confused_ai.number_of_turns == 2  # Decremented
        # Should attempt to move (mock_game_map.is_blocked would be called)
        mock_game_map.is_blocked.assert_called()

    @patch("components.ai.randint")
    def test_confused_monster_no_movement_same_position(
        self, mock_randint, mock_libtcod
    ):
        """Test confused monster doesn't move when random position equals current position."""
        # Arrange
        previous_ai = BasicMonster()
        confused_ai = ConfusedMonster(previous_ai, number_of_turns=3)
        monster = Entity(10, 10, "o", mock_libtcod.red, "Confused Orc", ai=confused_ai)
        target = Entity(15, 15, "@", mock_libtcod.white, "Player")
        mock_fov_map = Mock()
        mock_game_map = Mock()
        mock_game_map.is_blocked = Mock(return_value=False)
        entities = []

        # Mock random to return same position: randint(0, 2) - 1 = 0
        mock_randint.side_effect = [
            1,
            1,
        ]  # random_x = 10, random_y = 10 (same as current)

        # Act
        results = confused_ai.take_turn(target, mock_fov_map, mock_game_map, entities)

        # Assert
        assert len(results) == 0
        assert confused_ai.number_of_turns == 2
        # Should NOT call is_blocked since no movement attempted
        mock_game_map.is_blocked.assert_not_called()

    def test_confused_monster_recovery(self, mock_libtcod):
        """Test confused monster recovers after turns expire."""
        # Arrange
        previous_ai = BasicMonster()
        confused_ai = ConfusedMonster(previous_ai, number_of_turns=1)
        monster = Entity(10, 10, "o", mock_libtcod.red, "Confused Orc", ai=confused_ai)
        target = Entity(15, 15, "@", mock_libtcod.white, "Player")
        mock_fov_map = Mock()
        mock_game_map = Mock()
        entities = []

        # Mock the color for message
        with patch("components.ai.libtcod") as mock_tcod:
            mock_tcod.red = mock_libtcod.red

            # Act - first turn should still be confused
            results1 = confused_ai.take_turn(
                target, mock_fov_map, mock_game_map, entities
            )

            # Act - second turn should recover
            results2 = confused_ai.take_turn(
                target, mock_fov_map, mock_game_map, entities
            )

        # Assert
        assert len(results1) == 0  # No recovery message yet
        assert confused_ai.number_of_turns == 0  # Decremented to 0

        assert len(results2) == 1  # Recovery message
        assert "message" in results2[0]
        assert "no longer confused" in results2[0]["message"].text
        assert monster.ai == previous_ai  # AI restored

    def test_confused_monster_zero_turns_immediate_recovery(self, mock_libtcod):
        """Test confused monster with 0 turns recovers immediately."""
        # Arrange
        previous_ai = BasicMonster()
        confused_ai = ConfusedMonster(previous_ai, number_of_turns=0)
        monster = Entity(10, 10, "o", mock_libtcod.red, "Confused Orc", ai=confused_ai)
        target = Entity(15, 15, "@", mock_libtcod.white, "Player")
        mock_fov_map = Mock()
        mock_game_map = Mock()
        entities = []

        # Mock the color for message
        with patch("components.ai.libtcod") as mock_tcod:
            mock_tcod.red = mock_libtcod.red

            # Act
            results = confused_ai.take_turn(
                target, mock_fov_map, mock_game_map, entities
            )

        # Assert
        assert len(results) == 1  # Recovery message
        assert "message" in results[0]
        assert "no longer confused" in results[0]["message"].text
        assert monster.ai == previous_ai  # AI restored immediately
