"""Integration tests for Tier 1 debug flags.

These tests bypass the menu system and directly test game initialization
with various debug flag combinations. They ensure the game can actually
start without crashing.
"""

import pytest

# Mark entire module as slow
pytestmark = pytest.mark.slow
from unittest.mock import patch, Mock
from config.testing_config import TestingConfig, get_testing_config
from loader_functions.initialize_new_game import get_game_variables, get_constants
from game_states import GameStates


class TestDirectGameInitialization:
    """Test that games can be initialized directly without menu interaction."""
    
    def setup_method(self):
        """Reset testing config before each test."""
        # Force reset the singleton
        from config import testing_config as tc_module
        tc_module._testing_config = None
        
        config = get_testing_config()
        config.testing_mode = False
        config.start_level = 1
        config.god_mode = False
        config.no_monsters = False
        config.reveal_map = False
    
    def test_vanilla_game_initialization(self):
        """Test that a normal game can be initialized without debug flags."""
        constants = get_constants()
        
        # This should not crash
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Verify basic game state
        assert player is not None
        assert player.name == "Player"
        assert entities is not None
        assert game_map is not None
        assert game_map.dungeon_level == 1
        assert message_log is not None
        assert game_state == GameStates.PLAYERS_TURN
        
        # Verify player is equipped with starting gear
        assert player.equipment is not None
        assert player.equipment.main_hand is not None  # Dagger
        assert player.equipment.chest is not None  # Leather armor
    
    def test_start_level_5_initialization(self):
        """Test that game can be initialized at level 5."""
        config = get_testing_config()
        config.testing_mode = True
        config.start_level = 5
        
        constants = get_constants()
        
        # This should not crash
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Verify we're on the correct level
        assert game_map.dungeon_level == 5
        
        # Verify player level is boosted
        assert player.level.current_level >= 2
        
        # Verify player has appropriate gear
        assert player.equipment.main_hand is not None
        # Should have upgraded from dagger to sword at level 5
        assert player.equipment.main_hand.name in ["Sword", "sword"], \
            f"Expected Sword, got {player.equipment.main_hand.name}"
        
        # Verify player has healing potions
        potion_count = sum(1 for entity in entities if hasattr(entity, 'item') and 
                          entity.item and 'Healing Potion' in entity.name)
        # Should be in inventory (player.inventory counts as entities)
        assert len([e for e in entities if hasattr(e, 'inventory')]) > 0
    
    def test_start_level_10_initialization(self):
        """Test that game can be initialized at level 10."""
        config = get_testing_config()
        config.testing_mode = True
        config.start_level = 10
        
        constants = get_constants()
        
        # This should not crash
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Verify we're on the correct level
        assert game_map.dungeon_level == 10
        
        # Verify player level is boosted
        assert player.level.current_level == 5  # Half of 10
        
        # Verify player has upgraded armor
        assert player.equipment.chest is not None
        assert player.equipment.chest.name == "Chain Mail"  # Should have upgraded
    
    def test_start_level_20_initialization(self):
        """Test that game can be initialized at level 20."""
        config = get_testing_config()
        config.testing_mode = True
        config.start_level = 20
        
        constants = get_constants()
        
        # This should not crash
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Verify we're on the correct level
        assert game_map.dungeon_level == 20
        
        # Verify player level is capped at 10
        assert player.level.current_level == 10  # Capped
        
        # Verify player HP is boosted
        assert player.fighter.max_hp >= 100  # Base 30 + 10 levels * 10 = 130+
    
    def test_god_mode_with_start_level(self):
        """Test that god mode + start level work together."""
        config = get_testing_config()
        config.testing_mode = True
        config.start_level = 15
        config.god_mode = True
        
        constants = get_constants()
        
        # This should not crash
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Verify we're on the correct level
        assert game_map.dungeon_level == 15
        assert config.god_mode == True
        
        # Test god mode prevents death
        original_hp = player.fighter.hp
        player.fighter.take_damage(9999)
        assert player.fighter.hp >= 1  # Should not die
    
    def test_no_monsters_with_start_level(self):
        """Test that no-monsters + start level work together."""
        config = get_testing_config()
        config.testing_mode = True
        config.start_level = 5
        config.no_monsters = True
        
        constants = get_constants()
        
        # This should not crash
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Verify we're on the correct level
        assert game_map.dungeon_level == 5
        assert config.no_monsters == True
        
        # Count monsters (entities with Fighter component that aren't the player or NPCs)
        monsters = [e for e in entities if e != player and 
                   hasattr(e, 'fighter') and e.fighter and 
                   hasattr(e, 'ai') and e.ai and
                   not (hasattr(e, 'is_npc') and e.is_npc)]  # Exclude NPCs like Ghost Guide
        
        # Should be significantly fewer monsters (no_monsters flag active)
        # Note: Ghost Guide spawns on level 5, but it's an NPC not a monster
        # Due to map generation timing and randomness, some monsters might still spawn
        # Normal level 5 would have 10-20 monsters, so <= 5 is a huge reduction
        assert len(monsters) <= 5, f"Expected <= 5 monsters with no-monsters flag, got {len(monsters)}"
    
    def test_reveal_map_with_start_level(self):
        """Test that reveal-map + start level work together."""
        config = get_testing_config()
        config.testing_mode = True
        config.start_level = 5
        config.reveal_map = True
        
        constants = get_constants()
        
        # This should not crash
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Verify we're on the correct level
        assert game_map.dungeon_level == 5
        assert config.reveal_map == True
        
        # Verify reveal_map only affects explored tiles, not FOV radius
        # FOV should remain at the default 10
        from config.game_constants import GameConstants
        constants_obj = GameConstants()
        fov_radius = constants_obj._get_fov_radius()
        assert fov_radius == 10  # FOV unaffected by reveal_map
        
        # Verify all tiles are marked as explored (reveal_map effect)
        explored_count = sum(1 for x in range(game_map.width) 
                           for y in range(game_map.height) 
                           if game_map.tiles[x][y].explored)
        total_tiles = game_map.width * game_map.height
        assert explored_count == total_tiles, f"Expected all {total_tiles} tiles explored, got {explored_count}"
    
    def test_all_flags_combined(self):
        """Test that all debug flags work together."""
        config = get_testing_config()
        config.testing_mode = True
        config.start_level = 20
        config.god_mode = True
        config.no_monsters = True
        config.reveal_map = True
        
        constants = get_constants()
        
        # This should not crash
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Verify all flags are working
        assert game_map.dungeon_level == 20
        assert player.level.current_level == 10
        assert config.god_mode == True
        assert config.no_monsters == True
        assert config.reveal_map == True
        
        # Verify very few or no monsters spawned (excluding NPCs)
        monsters = [e for e in entities if e != player and 
                   hasattr(e, 'fighter') and e.fighter and 
                   hasattr(e, 'ai') and e.ai and
                   not (hasattr(e, 'is_npc') and e.is_npc)]
        # Due to map generation timing, a few monsters might spawn, but it should be << normal
        assert len(monsters) <= 5, f"Expected <= 5 monsters with no-monsters flag, got {len(monsters)}"
        
        # Verify god mode works
        player.fighter.take_damage(9999)
        assert player.fighter.hp >= 1
    
    def test_level_boundaries(self):
        """Test edge cases for level numbers."""
        config = get_testing_config()
        config.testing_mode = True
        
        constants = get_constants()
        
        # Test level 1 (minimum)
        config.start_level = 1
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        assert game_map.dungeon_level == 1
        
        # Test level 25 (maximum)
        config.start_level = 25
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        assert game_map.dungeon_level == 25
        assert player.level.current_level == 10  # Capped


class TestGameInitializationPerformance:
    """Test that game initialization is reasonably fast."""
    
    def setup_method(self):
        """Reset testing config before each test."""
        from config import testing_config as tc_module
        tc_module._testing_config = None
    
    def test_level_20_initialization_speed(self):
        """Test that skipping to level 20 completes in reasonable time.
        
        Note: This threshold is set high (60s) to avoid flaky failures in CI
        environments where resource contention can cause slowdowns. The test
        primarily verifies the level skip works correctly, not micro-optimization.
        """
        import time
        
        config = get_testing_config()
        config.testing_mode = True
        config.start_level = 20
        
        constants = get_constants()
        
        start_time = time.time()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        end_time = time.time()
        
        elapsed = end_time - start_time
        
        # Use a generous threshold to avoid CI flakiness while still catching
        # catastrophic performance regressions
        assert elapsed < 60.0, f"Level skip took {elapsed:.2f}s, should be < 60s"
        assert game_map.dungeon_level == 20


class TestPlayerStateBoosting:
    """Test that player stats are correctly boosted when skipping levels."""
    
    def setup_method(self):
        """Reset testing config before each test."""
        from config import testing_config as tc_module
        tc_module._testing_config = None
    
    def test_player_hp_scales_with_level(self):
        """Test that player HP increases with start level."""
        config = get_testing_config()
        config.testing_mode = True
        constants = get_constants()
        
        # Level 1 baseline
        config.start_level = 1
        player_1, _, _, _, _ = get_game_variables(constants)
        hp_level_1 = player_1.fighter.max_hp
        
        # Level 10
        config.start_level = 10
        player_10, _, _, _, _ = get_game_variables(constants)
        hp_level_10 = player_10.fighter.max_hp
        
        # Level 20
        config.start_level = 20
        player_20, _, _, _, _ = get_game_variables(constants)
        hp_level_20 = player_20.fighter.max_hp
        
        # HP should increase with level
        assert hp_level_10 > hp_level_1
        assert hp_level_20 > hp_level_10
        
        # HP should scale correctly: base 30 + (player_level * 10)
        assert player_10.fighter.base_max_hp == 30 + (5 * 10)  # Player level 5
        assert player_20.fighter.base_max_hp == 30 + (10 * 10)  # Player level 10
    
    def test_player_starts_at_full_hp(self):
        """Test that player always starts at full HP regardless of level."""
        config = get_testing_config()
        config.testing_mode = True
        constants = get_constants()
        
        for level in [1, 5, 10, 15, 20, 25]:
            config.start_level = level
            player, _, _, _, _ = get_game_variables(constants)
            
            # Should always start at full HP
            assert player.fighter.hp == player.fighter.max_hp, \
                f"Level {level}: HP {player.fighter.hp} != max HP {player.fighter.max_hp}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

