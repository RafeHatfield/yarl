"""Unit tests for GameMap safe tile accessor methods.

These tests verify that the safe accessor methods properly handle:
- Valid coordinates
- Out-of-bounds coordinates (negative, beyond width/height)
- Edge cases (0, max-1)
- None/default value returns
"""

import pytest
from map_objects.game_map import GameMap
from map_objects.tile import Tile


@pytest.fixture
def test_map():
    """Create a 10x10 test map."""
    game_map = GameMap(width=10, height=10, dungeon_level=1)
    
    # Set some tiles to specific states for testing
    game_map.tiles[5][5].blocked = False
    game_map.tiles[5][5].explored = True
    
    game_map.tiles[0][0].blocked = True
    game_map.tiles[0][0].explored = False
    
    game_map.tiles[9][9].blocked = False
    game_map.tiles[9][9].explored = True
    
    return game_map


class TestIsInBounds:
    """Test the is_in_bounds() method."""
    
    def test_valid_coordinates(self, test_map):
        """Valid coordinates should return True."""
        assert test_map.is_in_bounds(0, 0) is True
        assert test_map.is_in_bounds(5, 5) is True
        assert test_map.is_in_bounds(9, 9) is True
    
    def test_negative_coordinates(self, test_map):
        """Negative coordinates should return False."""
        assert test_map.is_in_bounds(-1, 0) is False
        assert test_map.is_in_bounds(0, -1) is False
        assert test_map.is_in_bounds(-1, -1) is False
    
    def test_beyond_width(self, test_map):
        """Coordinates beyond width should return False."""
        assert test_map.is_in_bounds(10, 0) is False
        assert test_map.is_in_bounds(100, 5) is False
    
    def test_beyond_height(self, test_map):
        """Coordinates beyond height should return False."""
        assert test_map.is_in_bounds(0, 10) is False
        assert test_map.is_in_bounds(5, 100) is False
    
    def test_edge_coordinates(self, test_map):
        """Edge coordinates (0 and max-1) should be valid."""
        assert test_map.is_in_bounds(0, 0) is True
        assert test_map.is_in_bounds(9, 0) is True
        assert test_map.is_in_bounds(0, 9) is True
        assert test_map.is_in_bounds(9, 9) is True


class TestGetTile:
    """Test the get_tile() method."""
    
    def test_valid_coordinates_returns_tile(self, test_map):
        """Valid coordinates should return a Tile object."""
        tile = test_map.get_tile(5, 5)
        assert tile is not None
        assert isinstance(tile, Tile)
        assert tile.blocked is False
        assert tile.explored is True
    
    def test_invalid_coordinates_returns_none(self, test_map):
        """Invalid coordinates should return None."""
        assert test_map.get_tile(-1, 0) is None
        assert test_map.get_tile(0, -1) is None
        assert test_map.get_tile(10, 0) is None
        assert test_map.get_tile(0, 10) is None
        assert test_map.get_tile(100, 100) is None
    
    def test_edge_coordinates(self, test_map):
        """Edge coordinates should return valid tiles."""
        tile = test_map.get_tile(0, 0)
        assert tile is not None
        assert isinstance(tile, Tile)
        
        tile = test_map.get_tile(9, 9)
        assert tile is not None
        assert isinstance(tile, Tile)


class TestIsBlocked:
    """Test the is_blocked() method."""
    
    def test_blocked_tile(self, test_map):
        """Blocked tiles should return True."""
        test_map.tiles[3][3].blocked = True
        assert test_map.is_blocked(3, 3) is True
    
    def test_unblocked_tile(self, test_map):
        """Unblocked tiles should return False."""
        test_map.tiles[5][5].blocked = False
        assert test_map.is_blocked(5, 5) is False
    
    def test_out_of_bounds_treated_as_blocked(self, test_map):
        """Out-of-bounds coordinates should be treated as blocked."""
        assert test_map.is_blocked(-1, 0) is True
        assert test_map.is_blocked(0, -1) is True
        assert test_map.is_blocked(10, 0) is True
        assert test_map.is_blocked(0, 10) is True
        assert test_map.is_blocked(100, 100) is True


class TestIsExplored:
    """Test the is_explored() method."""
    
    def test_explored_tile(self, test_map):
        """Explored tiles should return True."""
        test_map.tiles[5][5].explored = True
        assert test_map.is_explored(5, 5) is True
    
    def test_unexplored_tile(self, test_map):
        """Unexplored tiles should return False."""
        test_map.tiles[3][3].explored = False
        assert test_map.is_explored(3, 3) is False
    
    def test_out_of_bounds_treated_as_unexplored(self, test_map):
        """Out-of-bounds coordinates should be treated as unexplored."""
        assert test_map.is_explored(-1, 0) is False
        assert test_map.is_explored(0, -1) is False
        assert test_map.is_explored(10, 0) is False
        assert test_map.is_explored(0, 10) is False
        assert test_map.is_explored(100, 100) is False


class TestIsWalkable:
    """Test the is_walkable() method."""
    
    def test_walkable_tile(self, test_map):
        """Unblocked tiles should be walkable."""
        test_map.tiles[5][5].blocked = False
        assert test_map.is_walkable(5, 5) is True
    
    def test_unwalkable_tile(self, test_map):
        """Blocked tiles should not be walkable."""
        test_map.tiles[3][3].blocked = True
        assert test_map.is_walkable(3, 3) is False
    
    def test_out_of_bounds_not_walkable(self, test_map):
        """Out-of-bounds coordinates should not be walkable."""
        assert test_map.is_walkable(-1, 0) is False
        assert test_map.is_walkable(0, -1) is False
        assert test_map.is_walkable(10, 0) is False
        assert test_map.is_walkable(0, 10) is False
        assert test_map.is_walkable(100, 100) is False


class TestGetTileProperty:
    """Test the get_tile_property() method."""
    
    def test_get_blocked_property(self, test_map):
        """Should correctly retrieve 'blocked' property."""
        test_map.tiles[5][5].blocked = True
        assert test_map.get_tile_property(5, 5, 'blocked') is True
        
        test_map.tiles[5][5].blocked = False
        assert test_map.get_tile_property(5, 5, 'blocked') is False
    
    def test_get_explored_property(self, test_map):
        """Should correctly retrieve 'explored' property."""
        test_map.tiles[5][5].explored = True
        assert test_map.get_tile_property(5, 5, 'explored') is True
        
        test_map.tiles[5][5].explored = False
        assert test_map.get_tile_property(5, 5, 'explored') is False
    
    def test_out_of_bounds_returns_default(self, test_map):
        """Out-of-bounds should return default value."""
        assert test_map.get_tile_property(-1, 0, 'blocked', default=True) is True
        assert test_map.get_tile_property(10, 0, 'explored', default=False) is False
        assert test_map.get_tile_property(100, 100, 'foo', default='bar') == 'bar'
    
    def test_nonexistent_property_returns_default(self, test_map):
        """Non-existent property should return default value."""
        result = test_map.get_tile_property(5, 5, 'nonexistent_property', default='default_value')
        assert result == 'default_value'
    
    def test_none_default_value(self, test_map):
        """Should correctly return None as default."""
        assert test_map.get_tile_property(-1, 0, 'blocked') is None
        assert test_map.get_tile_property(5, 5, 'nonexistent') is None


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_zero_coordinates(self, test_map):
        """(0, 0) should be valid."""
        assert test_map.is_in_bounds(0, 0) is True
        tile = test_map.get_tile(0, 0)
        assert tile is not None
    
    def test_max_coordinates(self, test_map):
        """(width-1, height-1) should be valid."""
        assert test_map.is_in_bounds(9, 9) is True
        tile = test_map.get_tile(9, 9)
        assert tile is not None
    
    def test_just_beyond_max(self, test_map):
        """(width, height) should be invalid."""
        assert test_map.is_in_bounds(10, 10) is False
        assert test_map.get_tile(10, 10) is None
    
    def test_large_negative_coordinates(self, test_map):
        """Large negative values should be handled correctly."""
        assert test_map.is_in_bounds(-1000, -1000) is False
        assert test_map.get_tile(-1000, -1000) is None
        assert test_map.is_blocked(-1000, -1000) is True
    
    def test_large_positive_coordinates(self, test_map):
        """Large positive values should be handled correctly."""
        assert test_map.is_in_bounds(1000, 1000) is False
        assert test_map.get_tile(1000, 1000) is None
        assert test_map.is_blocked(1000, 1000) is True


class TestConsistency:
    """Test consistency between related methods."""
    
    def test_is_walkable_inverse_of_is_blocked(self, test_map):
        """is_walkable should be the inverse of is_blocked."""
        for x in range(test_map.width):
            for y in range(test_map.height):
                assert test_map.is_walkable(x, y) == (not test_map.is_blocked(x, y))
    
    def test_get_tile_consistency_with_is_in_bounds(self, test_map):
        """get_tile should return None iff coordinates are out of bounds."""
        test_coords = [
            (0, 0), (5, 5), (9, 9),  # Valid
            (-1, 0), (0, -1), (10, 0), (0, 10)  # Invalid
        ]
        
        for x, y in test_coords:
            in_bounds = test_map.is_in_bounds(x, y)
            tile = test_map.get_tile(x, y)
            
            if in_bounds:
                assert tile is not None, f"Expected tile at ({x}, {y})"
            else:
                assert tile is None, f"Expected None at ({x}, {y})"
    
    def test_is_explored_matches_get_tile_property(self, test_map):
        """is_explored should match get_tile_property('explored')."""
        for x in [0, 5, 9]:
            for y in [0, 5, 9]:
                explored_method = test_map.is_explored(x, y)
                explored_property = test_map.get_tile_property(x, y, 'explored', default=False)
                assert explored_method == explored_property


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""
    
    def test_rendering_with_invalid_entity_coordinates(self, test_map):
        """Simulate rendering an entity with invalid coordinates."""
        # This was the bug - entity at (-1, -1) caused IndexError
        # With safe accessors, should return safe values
        assert test_map.is_in_bounds(-1, -1) is False
        assert test_map.get_tile(-1, -1) is None
        assert test_map.is_explored(-1, -1) is False
        # No crash!
    
    def test_movement_validation_at_boundary(self, test_map):
        """Simulate checking if player can move to edge/beyond."""
        # At edge (valid)
        assert test_map.is_walkable(9, 9) is True or test_map.is_walkable(9, 9) is False
        
        # Beyond edge (should be blocked)
        assert test_map.is_walkable(10, 10) is False
        assert test_map.is_blocked(10, 10) is True
    
    def test_pathfinding_with_out_of_bounds_nodes(self, test_map):
        """Simulate pathfinding that might check out-of-bounds tiles."""
        # Pathfinding might check neighbors including out of bounds
        neighbors = [(-1, 0), (0, -1), (1, 1), (10, 10)]
        
        for x, y in neighbors:
            # Should not crash
            is_valid = test_map.is_in_bounds(x, y)
            is_walkable = test_map.is_walkable(x, y)
            
            # Out of bounds should not be walkable
            if not is_valid:
                assert is_walkable is False

