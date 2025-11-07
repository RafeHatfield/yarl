"""
Tests for victory portal spawning logic.

Ensures portal spawns in valid adjacent locations and doesn't regress
due to tile access syntax errors.
"""

import pytest
from unittest.mock import Mock, MagicMock
from victory_manager import VictoryManager
from entity import Entity


class TestPortalSpawnLocation:
    """Tests for _find_adjacent_open_tile method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.victory_mgr = VictoryManager()
        
        # Create mock player
        self.player = Mock(spec=Entity)
        self.player.x = 5
        self.player.y = 5
        
        # Create mock game map
        self.game_map = Mock()
        self.game_map.width = 80
        self.game_map.height = 45
        
        # Create mock tiles (2D array of tile objects)
        self.game_map.tiles = []
        for x in range(80):
            column = []
            for y in range(45):
                tile = Mock()
                tile.blocked = False  # Default: all tiles walkable
                column.append(tile)
            self.game_map.tiles.append(column)
        
        # Empty entities list
        self.entities = []
    
    def test_portal_spawns_right_when_open(self):
        """Portal should spawn to the right (first priority) when tile is open."""
        result_x, result_y = self.victory_mgr._find_adjacent_open_tile(
            self.player, self.game_map, self.entities
        )
        
        # Right is first priority: (x+1, y)
        assert result_x == 6
        assert result_y == 5
    
    def test_portal_spawns_down_when_right_blocked(self):
        """Portal should spawn down (second priority) when right is blocked."""
        # Block tile to the right
        self.game_map.tiles[6][5].blocked = True
        
        result_x, result_y = self.victory_mgr._find_adjacent_open_tile(
            self.player, self.game_map, self.entities
        )
        
        # Down is second priority: (x, y+1)
        assert result_x == 5
        assert result_y == 6
    
    def test_portal_spawns_left_when_right_and_down_blocked(self):
        """Portal should spawn left (third priority) when right and down blocked."""
        # Block right and down
        self.game_map.tiles[6][5].blocked = True
        self.game_map.tiles[5][6].blocked = True
        
        result_x, result_y = self.victory_mgr._find_adjacent_open_tile(
            self.player, self.game_map, self.entities
        )
        
        # Left is third priority: (x-1, y)
        assert result_x == 4
        assert result_y == 5
    
    def test_portal_spawns_up_when_cardinals_blocked(self):
        """Portal should spawn up (fourth priority) when all cardinals blocked."""
        # Block right, down, left
        self.game_map.tiles[6][5].blocked = True  # Right
        self.game_map.tiles[5][6].blocked = True  # Down
        self.game_map.tiles[4][5].blocked = True  # Left
        
        result_x, result_y = self.victory_mgr._find_adjacent_open_tile(
            self.player, self.game_map, self.entities
        )
        
        # Up is fourth priority: (x, y-1)
        assert result_x == 5
        assert result_y == 4
    
    def test_portal_spawns_diagonal_when_all_cardinals_blocked(self):
        """Portal should spawn diagonally when all cardinal directions blocked."""
        # Block all cardinal directions
        self.game_map.tiles[6][5].blocked = True   # Right
        self.game_map.tiles[5][6].blocked = True   # Down
        self.game_map.tiles[4][5].blocked = True   # Left
        self.game_map.tiles[5][4].blocked = True   # Up
        
        result_x, result_y = self.victory_mgr._find_adjacent_open_tile(
            self.player, self.game_map, self.entities
        )
        
        # First diagonal is down-right: (x+1, y+1)
        assert result_x == 6
        assert result_y == 6
    
    def test_portal_avoids_entity_blocking(self):
        """Portal should avoid tiles with blocking entities."""
        # Create blocking entity to the right
        blocking_entity = Mock(spec=Entity)
        blocking_entity.blocks = True
        blocking_entity.x = 6
        blocking_entity.y = 5
        self.entities = [blocking_entity]
        
        result_x, result_y = self.victory_mgr._find_adjacent_open_tile(
            self.player, self.game_map, self.entities
        )
        
        # Should skip right (has entity) and use down
        assert result_x == 5
        assert result_y == 6
    
    def test_portal_ignores_non_blocking_entity(self):
        """Portal can spawn on tiles with non-blocking entities (items)."""
        # Create non-blocking entity (item) to the right
        item_entity = Mock(spec=Entity)
        item_entity.blocks = False
        item_entity.x = 6
        item_entity.y = 5
        self.entities = [item_entity]
        
        result_x, result_y = self.victory_mgr._find_adjacent_open_tile(
            self.player, self.game_map, self.entities
        )
        
        # Should still spawn right (item doesn't block)
        assert result_x == 6
        assert result_y == 5
    
    def test_portal_falls_back_to_player_location(self):
        """Portal falls back to player location when all adjacent tiles blocked."""
        # Block ALL adjacent tiles
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Skip player's tile
                x = self.player.x + dx
                y = self.player.y + dy
                self.game_map.tiles[x][y].blocked = True
        
        result_x, result_y = self.victory_mgr._find_adjacent_open_tile(
            self.player, self.game_map, self.entities
        )
        
        # Should fall back to player's location
        assert result_x == self.player.x
        assert result_y == self.player.y
    
    def test_portal_respects_map_bounds_right_edge(self):
        """Portal should not spawn outside map bounds on right edge."""
        # Place player at right edge
        self.player.x = 79  # Last column
        self.player.y = 20
        
        result_x, result_y = self.victory_mgr._find_adjacent_open_tile(
            self.player, self.game_map, self.entities
        )
        
        # Should not be x=80 (out of bounds)
        assert 0 <= result_x < self.game_map.width
        assert 0 <= result_y < self.game_map.height
        # Should spawn down (second priority, since right is out of bounds)
        assert result_x == 79
        assert result_y == 21
    
    def test_portal_respects_map_bounds_bottom_edge(self):
        """Portal should not spawn outside map bounds on bottom edge."""
        # Place player at bottom edge
        self.player.x = 40
        self.player.y = 44  # Last row
        
        result_x, result_y = self.victory_mgr._find_adjacent_open_tile(
            self.player, self.game_map, self.entities
        )
        
        # Should not be y=45 (out of bounds)
        assert 0 <= result_x < self.game_map.width
        assert 0 <= result_y < self.game_map.height
        # Should spawn right (first priority that's in bounds)
        assert result_x == 41
        assert result_y == 44
    
    def test_portal_respects_map_bounds_top_left_corner(self):
        """Portal should handle top-left corner correctly."""
        # Place player at top-left corner
        self.player.x = 0
        self.player.y = 0
        
        result_x, result_y = self.victory_mgr._find_adjacent_open_tile(
            self.player, self.game_map, self.entities
        )
        
        # Should stay in bounds
        assert 0 <= result_x < self.game_map.width
        assert 0 <= result_y < self.game_map.height
        # Should spawn right (first valid direction)
        assert result_x == 1
        assert result_y == 0
    
    def test_tile_access_uses_attribute_not_dict(self):
        """Regression test: Ensure we use tile.blocked, not tile['blocked']."""
        # This test ensures the bug fix stays fixed
        # If someone reverts to tile['blocked'], this will fail
        
        # The tiles are Mock objects with .blocked attribute
        # Attempting tile['blocked'] would raise TypeError
        
        result_x, result_y = self.victory_mgr._find_adjacent_open_tile(
            self.player, self.game_map, self.entities
        )
        
        # If this doesn't raise TypeError, we're using attribute access correctly
        assert isinstance(result_x, int)
        assert isinstance(result_y, int)
    
    def test_portal_spawn_with_multiple_entities(self):
        """Portal should correctly handle multiple blocking entities."""
        # Create multiple blocking entities
        entity1 = Mock(spec=Entity)
        entity1.blocks = True
        entity1.x = 6
        entity1.y = 5  # Right
        
        entity2 = Mock(spec=Entity)
        entity2.blocks = True
        entity2.x = 5
        entity2.y = 6  # Down
        
        self.entities = [entity1, entity2]
        
        result_x, result_y = self.victory_mgr._find_adjacent_open_tile(
            self.player, self.game_map, self.entities
        )
        
        # Should skip right and down, spawn left
        assert result_x == 4
        assert result_y == 5


class TestPortalSpawnIntegration:
    """Integration tests for full portal spawning flow."""
    
    def test_handle_amulet_pickup_spawns_portal_adjacent(self):
        """End-to-end test: Amulet pickup spawns portal in adjacent tile."""
        # This is more of a smoke test to ensure integration works
        # Detailed logic is tested above
        
        victory_mgr = VictoryManager()
        
        # Create minimal mocks
        player = Mock(spec=Entity)
        player.x = 10
        player.y = 10
        player.victory = None
        player.inventory = Mock()
        player.inventory.items = []
        
        entities = []
        
        game_map = Mock()
        game_map.width = 80
        game_map.height = 45
        # Create minimal tile grid
        game_map.tiles = []
        for x in range(80):
            column = []
            for y in range(45):
                tile = Mock()
                tile.blocked = False
                column.append(tile)
            game_map.tiles.append(column)
        
        message_log = Mock()
        message_log.add_message = Mock()
        
        # Mock entity factory
        mock_portal = Mock(spec=Entity)
        mock_portal.x = 11  # Will be set by factory
        mock_portal.y = 10
        victory_mgr.entity_factory = Mock()
        victory_mgr.entity_factory.create_unique_item = Mock(return_value=mock_portal)
        
        # Execute
        result = victory_mgr.handle_amulet_pickup(player, entities, game_map, message_log)
        
        # Verify
        assert result is True
        assert victory_mgr.entity_factory.create_unique_item.called
        # Portal should be created at adjacent location (not player's exact location)
        call_args = victory_mgr.entity_factory.create_unique_item.call_args
        portal_x = call_args[0][1]
        portal_y = call_args[0][2]
        
        # Portal should be adjacent to player
        dx = abs(portal_x - player.x)
        dy = abs(portal_y - player.y)
        assert (dx == 1 and dy == 0) or (dx == 0 and dy == 1) or (dx == 1 and dy == 1)

