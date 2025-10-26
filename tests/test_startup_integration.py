"""Integration test that actually runs game initialization.

This test catches bugs that happen immediately on startup.
It runs the actual game initialization code path.
"""

import pytest
from unittest.mock import patch
from config.testing_config import get_testing_config, set_testing_mode
from loader_functions.initialize_new_game import get_game_variables, get_constants


class TestActualStartup:
    """Test actual game startup scenarios that were failing."""
    
    def setup_method(self):
        """Reset testing config before each test."""
        from config import testing_config as tc_module
        tc_module._testing_config = None
        
        # Enable testing mode
        set_testing_mode(True)
    
    def test_start_level_5_no_crash(self):
        """Test that starting at level 5 doesn't crash.
        
        This test caught bugs #5-9:
        - Bug #5: Items in walls at (0,0)
        - Bug #6: IndexError from invalid coordinates
        - Bug #7: Menu still showing (not tested here)
        - Bug #8: Secret doors crash with < 2 rooms
        - Bug #9: AttributeError on game_constants.map.width
        """
        config = get_testing_config()
        config.start_level = 5
        
        # This should NOT crash
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Basic validation
        assert player is not None
        assert game_map.dungeon_level == 5
        assert len(entities) > 0
        
        # Check no items at (0, 0) in the world
        items_at_origin = [e for e in entities if e.x == 0 and e.y == 0 and hasattr(e, 'item')]
        assert len(items_at_origin) == 0, f"Found {len(items_at_origin)} items at (0,0): {[i.name for i in items_at_origin]}"
        
        # Check all entities have valid coordinates
        map_width = constants['map_width']
        map_height = constants['map_height']
        invalid_entities = [e for e in entities if e.x < 0 or e.x >= map_width or e.y < 0 or e.y >= map_height]
        assert len(invalid_entities) == 0, f"Found {len(invalid_entities)} entities with invalid coords: {[(e.name, e.x, e.y) for e in invalid_entities]}"
    
    def test_start_level_1_no_crash(self):
        """Test that starting at level 1 still works."""
        config = get_testing_config()
        config.start_level = 1
        
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        assert player is not None
        assert game_map.dungeon_level == 1
    
    def test_start_level_20_no_crash(self):
        """Test that starting at level 20 works."""
        config = get_testing_config()
        config.start_level = 20
        
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        assert player is not None
        assert game_map.dungeon_level == 20
        assert player.level.current_level == 10  # Capped
    
    def test_start_level_multiple_times(self):
        """Test starting at level 5 multiple times (catches RNG bugs).
        
        Run 5 times to catch:
        - Secret door bugs (sometimes only 1 room)
        - Random item/monster placement bugs
        - Edge cases in map generation
        """
        config = get_testing_config()
        config.start_level = 5
        constants = get_constants()
        
        for i in range(5):
            # Each iteration should succeed
            player, entities, game_map, message_log, game_state = get_game_variables(constants)
            assert game_map.dungeon_level == 5, f"Run {i+1}: Wrong dungeon level"
            
            # No items at origin
            items_at_origin = [e for e in entities if e.x == 0 and e.y == 0 and hasattr(e, 'item')]
            assert len(items_at_origin) == 0, f"Run {i+1}: Found items at (0,0)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

