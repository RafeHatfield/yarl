"""Regression test for interactable pathfinding bug fix.

Bug: Right-clicking an interactable (chest, sign, mural) when out of range
caused the player to always path to the NW (northwest) tile, regardless of
which adjacent tile was actually closest.

Root cause: _find_adjacent_walkable_tile() returned the FIRST valid tile
(iterating in fixed order starting with NW), instead of choosing the BEST
tile based on path distance from player.

Fix: Modified _find_adjacent_walkable_tile() to:
1. Find ALL valid adjacent tiles
2. Choose the one with shortest Manhattan distance from player
3. Use stable tie-breaker (reading order) for determinism

This test ensures the bug never returns.
"""

import pytest
from components.component_registry import ComponentType
from entity import Entity
from map_objects.game_map import GameMap
from render_functions import RenderOrder
from systems.interaction_system import PathfindingHelper


class TestAdjacentTileSelection:
    """Test that _find_adjacent_walkable_tile chooses the best tile."""
    
    def test_open_chest_from_distance_defers_state_check(self):
        """Test that clicking an already-open chest from distance defers the state check.
        
        Bug: Previously, clicking an open chest would check can_interact() at click
        time and immediately return \"already empty\" without pathfinding.
        
        Correct behavior: Distance check happens FIRST. If not adjacent, should
        attempt to pathfind regardless of chest state. The \"already empty\" message
        should only appear ON ARRIVAL when the player is adjacent.
        """
        from components.chest import Chest, ChestState
        from systems.interaction_system import ChestInteractionStrategy
        
        game_map = GameMap(10, 10)
        game_map.initialize_tiles()
        
        for x in range(10):
            for y in range(10):
                game_map.tiles[x][y].blocked = False
                game_map.tiles[x][y].block_sight = False
        
        # Player at (8, 3) - 2 tiles away (not adjacent)
        player = Entity(8, 3, '@', (255, 255, 255), 'Player', blocks=True,
                       render_order=RenderOrder.ACTOR)
        
        # OPEN chest at (8, 5)
        chest_entity = Entity(8, 5, '&', (139, 69, 19), 'Wooden Chest', blocks=True,
                             render_order=RenderOrder.ITEM)
        chest_entity.tags.add('openable')
        chest_entity.chest = Chest(state=ChestState.OPEN, loot=[], loot_quality='common')
        chest_entity.chest.owner = chest_entity
        
        # Verify chest is NOT adjacent
        distance = player.distance_to(chest_entity)
        assert distance > 1, f"Player should not be adjacent, distance={distance}"
        
        # Verify chest cannot be interacted with (it's already open)
        assert chest_entity.chest.can_interact() is False, "Chest should be already open"
        
        # Call can_interact - should return True even for open chests
        strategy = ChestInteractionStrategy()
        assert strategy.can_interact(chest_entity, player) is True, \
            "can_interact() should return True for chests regardless of state"
    
    def test_find_adjacent_tile_from_west_chooses_west_not_nw(self):
        """Test that adjacent tile selection chooses closest tile from west.
        
        Setup:
        - Player at (1, 5) - west side
        - Target at (8, 5) - east side, same row
        - Expected: Choose (7, 5) - directly west of target (closest)
        - Bug behavior: Would choose (7, 4) - NW of target (first in iteration)
        """
        # Create a 10x10 map
        game_map = GameMap(10, 10)
        game_map.initialize_tiles()
        
        # Make all tiles walkable
        for x in range(10):
            for y in range(10):
                game_map.tiles[x][y].blocked = False
                game_map.tiles[x][y].block_sight = False
        
        # Create player at (1, 5)
        player = Entity(1, 5, '@', (255, 255, 255), 'Player', blocks=True,
                       render_order=RenderOrder.ACTOR)
        
        # Create target at (8, 5) - directly east
        target = Entity(8, 5, 'T', (255, 255, 255), 'Target', blocks=True,
                       render_order=RenderOrder.ITEM)
        
        entities = [player, target]
        
        # Test the helper directly
        helper = PathfindingHelper()
        adjacent_tile = helper._find_adjacent_walkable_tile(
            target.x, target.y, player, game_map, entities
        )
        
        # Should choose (7, 5) - west of target, NOT (7, 4) - NW
        assert adjacent_tile is not None, "Should find an adjacent tile"
        assert adjacent_tile == (7, 5), f"Should choose (7,5) west tile, got {adjacent_tile}"
    
    def test_find_adjacent_tile_from_south_chooses_south_not_nw(self):
        """Test that approaching from south chooses south tile, not NW.
        
        Setup:
        - Player at (5, 8) - south of target
        - Target at (5, 5) - north of player, same column
        - Expected: Choose (5, 6) - directly south of target (closest)
        - Bug behavior: Would choose (4, 4) - NW of target (first in iteration)
        """
        game_map = GameMap(10, 10)
        game_map.initialize_tiles()
        
        for x in range(10):
            for y in range(10):
                game_map.tiles[x][y].blocked = False
                game_map.tiles[x][y].block_sight = False
        
        # Player at (5, 8) - south
        player = Entity(5, 8, '@', (255, 255, 255), 'Player', blocks=True,
                       render_order=RenderOrder.ACTOR)
        
        # Target at (5, 5) - north
        target = Entity(5, 5, 'T', (255, 255, 255), 'Target', blocks=True,
                       render_order=RenderOrder.ITEM)
        
        entities = [player, target]
        
        helper = PathfindingHelper()
        adjacent_tile = helper._find_adjacent_walkable_tile(
            target.x, target.y, player, game_map, entities
        )
        
        # Should choose (5, 6) - south of target, NOT NW
        assert adjacent_tile is not None
        assert adjacent_tile == (5, 6), f"Should choose (5,6) south tile, got {adjacent_tile}"
    
    def test_find_adjacent_tile_from_east_chooses_east_not_nw(self):
        """Test that approaching from east chooses east tile, not NW."""
        game_map = GameMap(10, 10)
        game_map.initialize_tiles()
        
        for x in range(10):
            for y in range(10):
                game_map.tiles[x][y].blocked = False
                game_map.tiles[x][y].block_sight = False
        
        # Player at (8, 5) - east
        player = Entity(8, 5, '@', (255, 255, 255), 'Player', blocks=True,
                       render_order=RenderOrder.ACTOR)
        
        # Target at (5, 5) - west
        target = Entity(5, 5, 'T', (255, 255, 255), 'Target', blocks=True,
                       render_order=RenderOrder.ITEM)
        
        entities = [player, target]
        
        helper = PathfindingHelper()
        adjacent_tile = helper._find_adjacent_walkable_tile(
            target.x, target.y, player, game_map, entities
        )
        
        # Should choose (6, 5) - east of target, NOT NW
        assert adjacent_tile is not None
        assert adjacent_tile == (6, 5), f"Should choose (6,5) east tile, got {adjacent_tile}"
    
    def test_find_adjacent_tile_from_north_chooses_north_not_nw(self):
        """Test that approaching from north chooses north tile, not NW."""
        game_map = GameMap(10, 10)
        game_map.initialize_tiles()
        
        for x in range(10):
            for y in range(10):
                game_map.tiles[x][y].blocked = False
                game_map.tiles[x][y].block_sight = False
        
        # Player at (5, 2) - north
        player = Entity(5, 2, '@', (255, 255, 255), 'Player', blocks=True,
                       render_order=RenderOrder.ACTOR)
        
        # Target at (5, 5) - south
        target = Entity(5, 5, 'T', (255, 255, 255), 'Target', blocks=True,
                       render_order=RenderOrder.ITEM)
        
        entities = [player, target]
        
        helper = PathfindingHelper()
        adjacent_tile = helper._find_adjacent_walkable_tile(
            target.x, target.y, player, game_map, entities
        )
        
        # Should choose (5, 4) - north of target, NOT NW
        assert adjacent_tile is not None
        assert adjacent_tile == (5, 4), f"Should choose (5,4) north tile, got {adjacent_tile}"
    
    def test_find_adjacent_tile_with_blocked_tiles_chooses_best_available(self):
        """Test that if closest tile is blocked, next best is chosen."""
        game_map = GameMap(10, 10)
        game_map.initialize_tiles()
        
        for x in range(10):
            for y in range(10):
                game_map.tiles[x][y].blocked = False
                game_map.tiles[x][y].block_sight = False
        
        # Player at (1, 5) - west
        player = Entity(1, 5, '@', (255, 255, 255), 'Player', blocks=True,
                       render_order=RenderOrder.ACTOR)
        
        # Target at (5, 5)
        target = Entity(5, 5, 'T', (255, 255, 255), 'Target', blocks=True,
                       render_order=RenderOrder.ITEM)
        
        # Block the west tile (4, 5) with a wall
        game_map.tiles[4][5].blocked = True
        
        entities = [player, target]
        
        helper = PathfindingHelper()
        adjacent_tile = helper._find_adjacent_walkable_tile(
            target.x, target.y, player, game_map, entities
        )
        
        # Should find a valid adjacent tile (not the blocked west tile)
        assert adjacent_tile is not None, "Should find an unblocked adjacent tile"
        assert adjacent_tile != (4, 5), "Should not choose blocked tile"
        
        # Should be adjacent to target (Manhattan distance 1 or diagonal distance 1)
        # Diagonal tiles have Manhattan distance 2 but are still adjacent
        dx = abs(adjacent_tile[0] - 5)
        dy = abs(adjacent_tile[1] - 5)
        assert dx <= 1 and dy <= 1, f"Should be adjacent (max 1 tile away in each axis), got dx={dx}, dy={dy}"
        assert not (dx == 0 and dy == 0), "Should not be on target itself"
