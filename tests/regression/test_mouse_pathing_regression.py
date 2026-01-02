"""Regression test for mouse pathing "Cannot reach that location" bug.

This test verifies that the pathfinding cost map is correctly constructed
for tcod.path.AStar, which expects non-zero values for walkable tiles
and zero for blocked tiles.

Bug: All mouse clicks showed "Cannot reach that location" because the
cost map was incorrectly inverted (0 for walkable, 1 for blocked).

Fix: Use fov.walkable.astype("int8") directly, not inverted.
"""

import unittest
from components.player_pathfinding import PlayerPathfinding
from entity import Entity
from map_objects.game_map import GameMap


class TestMousePathingRegression(unittest.TestCase):
    """Test that mouse pathing works correctly after the cost map fix."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.game_map = GameMap(width=30, height=30, dungeon_level=1)
        
        # Create a simple open area
        for x in range(30):
            for y in range(30):
                self.game_map.tiles[x][y].explored = True
                self.game_map.tiles[x][y].blocked = False
                self.game_map.tiles[x][y].block_sight = False
        
        # Create player with pathfinding component
        self.player = Entity(5, 5, '@', (255, 255, 255), 'Player', blocks=True)
        pathfinding = PlayerPathfinding()
        self.player.pathfinding = pathfinding
        pathfinding.owner = self.player
        
        self.entities = [self.player]
    
    def test_can_pathfind_to_adjacent_tile(self):
        """Test that pathfinding works for adjacent tiles."""
        # This should always work - adjacent tile
        success = self.player.pathfinding.set_destination(
            6, 6, self.game_map, self.entities, fov_map=None
        )
        
        self.assertTrue(success, "Should be able to pathfind to adjacent tile")
        self.assertGreater(len(self.player.pathfinding.current_path), 0)
    
    def test_can_pathfind_to_nearby_tile(self):
        """Test that pathfinding works for nearby tiles (regression test)."""
        # This was failing with "Cannot reach that location" due to inverted cost map
        success = self.player.pathfinding.set_destination(
            10, 10, self.game_map, self.entities, fov_map=None
        )
        
        self.assertTrue(success, "Should be able to pathfind to nearby tile")
        self.assertGreater(len(self.player.pathfinding.current_path), 0)
        
        # Verify the path makes sense
        path = self.player.pathfinding.current_path
        self.assertEqual(path[-1], (10, 10), "Path should end at destination")
    
    def test_can_pathfind_around_obstacles(self):
        """Test that pathfinding can route around walls."""
        # Create a wall between player and destination
        for y in range(10):
            self.game_map.tiles[8][y].blocked = True
            self.game_map.tiles[8][y].explored = True
        
        # Try to pathfind to other side of wall
        success = self.player.pathfinding.set_destination(
            12, 5, self.game_map, self.entities, fov_map=None
        )
        
        self.assertTrue(success, "Should find path around obstacle")
        
        # Verify path doesn't go through the wall
        path = self.player.pathfinding.current_path
        for x, y in path:
            self.assertFalse(
                self.game_map.tiles[x][y].blocked,
                f"Path should not go through blocked tile at ({x}, {y})"
            )
    
    def test_cannot_pathfind_to_blocked_destination(self):
        """Test that pathfinding correctly rejects blocked destinations."""
        # Mark destination as blocked
        self.game_map.tiles[10][10].blocked = True
        
        success = self.player.pathfinding.set_destination(
            10, 10, self.game_map, self.entities, fov_map=None
        )
        
        self.assertFalse(success, "Should not pathfind to blocked tile")
    
    def test_cost_map_construction(self):
        """Test that the cost map is correctly constructed for tcod.path.AStar."""
        import tcod
        import warnings
        
        # Create a small test map
        test_map = GameMap(width=10, height=10, dungeon_level=1)
        for x in range(10):
            for y in range(10):
                test_map.tiles[x][y].explored = True
                test_map.tiles[x][y].blocked = False
                test_map.tiles[x][y].block_sight = False
        
        # Add a wall
        test_map.tiles[5][5].blocked = True
        
        # Build the FOV map the same way the pathfinding code does
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            fov = tcod.map.Map(test_map.width, test_map.height)
        
        for y in range(test_map.height):
            for x in range(test_map.width):
                fov.transparent[y, x] = not test_map.tiles[x][y].block_sight
                fov.walkable[y, x] = not test_map.tiles[x][y].blocked
        
        # Create cost map the same way the fix does
        cost = fov.walkable.astype("int8")
        
        # Verify: walkable tiles should have non-zero cost (1)
        # blocked tiles should have zero cost
        self.assertEqual(cost[0, 0], 1, "Walkable tile should have cost 1")
        self.assertEqual(cost[5, 5], 0, "Blocked tile should have cost 0")
        
        # Verify pathfinding works with this cost map
        astar = tcod.path.AStar(cost, diagonal=1.41)
        path = astar.get_path(0, 0, 9, 9)
        
        self.assertGreater(len(path), 0, "Should find path with correct cost map")


if __name__ == '__main__':
    unittest.main()



