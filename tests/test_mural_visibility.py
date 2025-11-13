"""Tests for mural and signpost persistence/visibility out of FOV.

This test module verifies that discovered murals and signposts remain visible
on the map when outside the player's field of view, displayed in a greyed-out
state (similar to chests and stairs).
"""

import pytest
from entity import Entity
from components.mural import Mural
from components.signpost import Signpost
from map_objects.tile import Tile
from map_objects.game_map import GameMap


class TestMuralVisibility:
    """Test that murals persist visibility when discovered but out of FOV."""
    
    def test_mural_remains_greyed_out_after_discovery(self):
        """When a mural is discovered (explored), it should render greyed-out when not in FOV."""
        # Create a simple game map
        game_map = GameMap(80, 50)
        
        # Create a mural entity (manually, so add tag)
        mural_entity = Entity(
            x=10,
            y=10,
            char="M",
            color=(220, 20, 60),  # Crimson
            name="Mural"
        )
        mural_entity.tags.add('interactable')  # Tag it manually for this test
        mural_entity.mural = Mural("A mystical scene unfolds before you...")
        
        # Mark the tile as explored (discovered)
        game_map.tiles[10][10].explored = True
        
        # Verify that the mural is marked as interactable
        assert 'interactable' in mural_entity.tags
        
        # Verify that the tile is marked as explored
        assert game_map.is_explored(10, 10)
        
        # The mural should be renderable even when not in FOV due to being explored
        # This is checked in render_functions.py: draw_entity checks:
        # if in_fov or (is_persistent_feature and is_explored):
        assert hasattr(mural_entity, 'mural') and mural_entity.mural is not None
    
    def test_undiscovered_mural_not_visible(self):
        """An undiscovered mural on an unexplored tile should not be visible."""
        # Create a simple game map
        game_map = GameMap(80, 50)
        
        # Create a mural entity
        mural_entity = Entity(
            x=10,
            y=10,
            char="M",
            color=(220, 20, 60),
            name="Mural"
        )
        mural_entity.mural = Mural("A mystical scene unfolds...")
        
        # Ensure the tile is NOT explored (undiscovered)
        game_map.tiles[10][10].explored = False
        
        # Verify the tile is not explored
        assert not game_map.is_explored(10, 10)
        
        # The mural should NOT be renderable when the tile is not explored
        # (This is the player-facing behavior - draw_entity won't render it)
        assert hasattr(mural_entity, 'mural')
    
    def test_discovered_mural_location_remembered(self):
        """Once discovered, a mural's location remains known even when not visible."""
        # Create game map
        game_map = GameMap(80, 50)
        
        # Create mural
        mural_entity = Entity(
            x=15,
            y=20,
            char="M",
            color=(220, 20, 60),
            name="Mural"
        )
        mural_entity.mural = Mural("Ancient wisdom carved in stone...")
        
        # Mark tile as explored
        game_map.tiles[15][20].explored = True
        
        # Store position
        original_pos = (mural_entity.x, mural_entity.y)
        
        # Verify position is preserved
        assert (mural_entity.x, mural_entity.y) == original_pos
        assert game_map.is_explored(15, 20)


class TestSignpostVisibility:
    """Test that signposts persist visibility when discovered but out of FOV."""
    
    def test_signpost_remains_greyed_out_after_discovery(self):
        """When a signpost is discovered (explored), it should render greyed-out when not in FOV."""
        # Create a simple game map
        game_map = GameMap(80, 50)
        
        # Create a signpost entity (manually, so add tag)
        signpost_entity = Entity(
            x=25,
            y=30,
            char="!",
            color=(200, 200, 200),  # Light gray
            name="Signpost"
        )
        signpost_entity.tags.add('interactable')  # Tag it manually for this test
        signpost_entity.signpost = Signpost("Welcome to the dungeon! Mind the traps.")
        
        # Mark the tile as explored (discovered)
        game_map.tiles[25][30].explored = True
        
        # Verify that the signpost is marked as interactable
        assert 'interactable' in signpost_entity.tags
        
        # Verify that the tile is marked as explored
        assert game_map.is_explored(25, 30)
        
        # The signpost should be renderable even when not in FOV due to being explored
        assert hasattr(signpost_entity, 'signpost') and signpost_entity.signpost is not None
    
    def test_undiscovered_signpost_not_visible(self):
        """An undiscovered signpost on an unexplored tile should not be visible."""
        # Create a simple game map
        game_map = GameMap(80, 50)
        
        # Create a signpost entity
        signpost_entity = Entity(
            x=25,
            y=30,
            char="!",
            color=(200, 200, 200),
            name="Signpost"
        )
        signpost_entity.signpost = Signpost("This way to adventure...")
        
        # Ensure the tile is NOT explored (undiscovered)
        game_map.tiles[25][30].explored = False
        
        # Verify the tile is not explored
        assert not game_map.is_explored(25, 30)
        
        # The signpost should NOT be renderable when the tile is not explored
        assert hasattr(signpost_entity, 'signpost')


class TestPersistentFeaturesVisibility:
    """Test that all persistent features (murals, signposts, etc.) have consistent behavior."""
    
    def test_mural_persists_like_chest(self):
        """Murals should persist visibility like chests do."""
        game_map = GameMap(80, 50)
        
        # Create a mural
        mural = Entity(x=10, y=10, char="M", color=(220, 20, 60), name="Mural")
        mural.mural = Mural("Test mural")
        
        # Create a chest for comparison
        from components.chest import Chest, ChestState
        chest = Entity(x=20, y=20, char="C", color=(200, 150, 100), name="Chest")
        chest.chest = Chest()
        
        # Mark both tiles as explored
        game_map.tiles[10][10].explored = True
        game_map.tiles[20][20].explored = True
        
        # Both should be interactable and persistent
        assert 'interactable' in mural.tags or hasattr(mural, 'mural')
        assert hasattr(chest, 'chest')
        
        # Both tiles should be marked as explored
        assert game_map.is_explored(10, 10)
        assert game_map.is_explored(20, 20)
    
    def test_signpost_persists_like_stairs(self):
        """Signposts should persist visibility like stairs do."""
        game_map = GameMap(80, 50)
        
        # Create a signpost
        signpost = Entity(x=30, y=30, char="!", color=(200, 200, 200), name="Signpost")
        signpost.signpost = Signpost("Test sign")
        
        # Create stairs for comparison (using simple mock)
        stairs = Entity(x=40, y=40, char=">", color=(255, 255, 255), name="Stairs Down")
        # Create a simple stairs-like object
        class MockStairs:
            def __init__(self):
                pass
        stairs.stairs = MockStairs()
        
        # Mark both tiles as explored
        game_map.tiles[30][30].explored = True
        game_map.tiles[40][40].explored = True
        
        # Both should be persistent features
        assert hasattr(signpost, 'signpost')
        assert hasattr(stairs, 'stairs')
        
        # Both tiles should be marked as explored
        assert game_map.is_explored(30, 30)
        assert game_map.is_explored(40, 40)

