"""Test map generation with testing templates.

Regression test for bug where logger was undefined in make_map
when using testing templates.
"""

import pytest
import os
from map_objects.game_map import GameMap
from entity import Entity
from components.fighter import Fighter
from game_messages import MessageLog


def test_map_generation_level1_testing_template():
    """Test that level 1 map generates correctly with testing template.
    
    This is a regression test for UnboundLocalError where logger
    was used before being defined in make_map().
    
    Bug scenario:
    - Testing mode enabled (level template overrides)
    - Generate level 1
    - make_map() uses logger before it's imported
    - UnboundLocalError raised
    """
    # Enable testing mode
    os.environ['YARL_TESTING_MODE'] = '1'
    
    try:
        # Create a simple player entity for map generation
        player = Entity(
            0, 0, '@', (255, 255, 255), 'Player',
            blocks=True,
            fighter=Fighter(hp=100, defense=2, power=5)
        )
        
        entities = [player]
        
        # Create game map
        game_map = GameMap(80, 60, dungeon_level=1)
        
        # This should NOT raise UnboundLocalError
        # Bug was: logger used at line 114 before being defined
        game_map.make_map(
            max_rooms=10,
            room_min_size=6,
            room_max_size=10,
            map_width=80,
            map_height=60,
            player=player,
            entities=entities
        )
        
        # If we get here, map generation succeeded
        assert len(entities) > 1  # Should have spawned items/monsters
        assert game_map.dungeon_level == 1
        
    finally:
        # Clean up environment
        if 'YARL_TESTING_MODE' in os.environ:
            del os.environ['YARL_TESTING_MODE']


def test_map_generation_level25_amulet_spawn():
    """Test that level 25 map generates with amulet.
    
    Regression test that amulet spawn logic doesn't break
    logger import.
    """
    # Create a simple player entity
    player = Entity(
        0, 0, '@', (255, 255, 255), 'Player',
        blocks=True,
        fighter=Fighter(hp=100, defense=2, power=5)
    )
    
    entities = [player]
    
    # Create level 25 map
    game_map = GameMap(80, 60, dungeon_level=25)
    
    # This should spawn amulet and NOT raise logger errors
    game_map.make_map(
        max_rooms=10,
        room_min_size=6,
        room_max_size=10,
        map_width=80,
        map_height=60,
        player=player,
        entities=entities
    )
    
    # Check amulet was spawned
    amulet_found = False
    for entity in entities:
        if hasattr(entity, 'triggers_victory') and entity.triggers_victory:
            amulet_found = True
            break
    
    assert amulet_found, "Amulet of Yendor should spawn on level 25"
    assert game_map.dungeon_level == 25


def test_map_generation_normal_levels():
    """Test that normal level generation still works.
    
    Ensures fix doesn't break non-testing, non-level-25 generation.
    """
    player = Entity(
        0, 0, '@', (255, 255, 255), 'Player',
        blocks=True,
        fighter=Fighter(hp=100, defense=2, power=5)
    )
    
    entities = [player]
    
    # Test a few random levels
    for level in [5, 10, 15]:
        game_map = GameMap(80, 60, dungeon_level=level)
        
        game_map.make_map(
            max_rooms=10,
            room_min_size=6,
            room_max_size=10,
            map_width=80,
            map_height=60,
            player=player,
            entities=entities.copy()
        )
        
        assert game_map.dungeon_level == level

