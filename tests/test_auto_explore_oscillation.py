"""Tests for AutoExplore oscillation detection.

This module tests that AutoExplore properly detects and stops when
oscillating between two tiles (e.g., A ↔ B ↔ A ↔ B).

This prevents infinite loops that can occur when:
- Opportunistic loot targeting alternates between two positions
- Pathfinding produces back-and-forth movement
- Any other logic causes repeated two-tile loops
"""

import pytest
from collections import deque
from unittest.mock import Mock, MagicMock, patch
from components.auto_explore import AutoExplore
from components.component_registry import ComponentType


class TestAutoExploreOscillationDetection:
    """Test oscillation detection in AutoExplore."""
    
    def test_detects_two_tile_oscillation(self):
        """Test that A-B-A-B-A-B pattern is detected and stops AutoExplore."""
        # Setup
        auto_explore = AutoExplore()
        
        # Create mock owner (player)
        player = Mock()
        player.x = 10
        player.y = 20
        player.fighter = Mock()
        player.fighter.hp = 100
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        auto_explore.owner = player
        
        # Create mock game_map with unexplored tiles
        game_map = Mock()
        game_map.width = 50
        game_map.height = 50
        game_map.is_explored = Mock(return_value=False)
        game_map.hazard_manager = Mock()
        game_map.hazard_manager.has_hazard_at = Mock(return_value=False)
        
        # Create tiles array
        tiles = []
        for x in range(50):
            col = []
            for y in range(50):
                tile = Mock()
                tile.blocked = False
                tile.explored = False
                col.append(tile)
            tiles.append(col)
        game_map.tiles = tiles
        
        entities = []
        fov_map = Mock()
        
        # Start auto-explore
        auto_explore.start(game_map, entities, fov_map)
        
        # Simulate oscillation: position alternates between (10, 20) and (10, 21)
        # Move 1: at (10, 20)
        player.x, player.y = 10, 20
        
        with patch.object(auto_explore, '_check_stop_conditions', return_value=None):
            with patch.object(auto_explore, '_find_next_unexplored_tile', return_value=(10, 21)):
                with patch.object(auto_explore, '_calculate_path_to', return_value=[(10, 21)]):
                    action1 = auto_explore.get_next_action(game_map, entities, fov_map)
                    assert action1 is not None  # First move succeeds
        
        # Move 2: at (10, 21)
        player.x, player.y = 10, 21
        
        with patch.object(auto_explore, '_check_stop_conditions', return_value=None):
            with patch.object(auto_explore, '_find_next_unexplored_tile', return_value=(10, 20)):
                with patch.object(auto_explore, '_calculate_path_to', return_value=[(10, 20)]):
                    action2 = auto_explore.get_next_action(game_map, entities, fov_map)
                    assert action2 is not None  # Second move succeeds
        
        # Move 3: at (10, 20) - first repeat
        player.x, player.y = 10, 20
        
        with patch.object(auto_explore, '_check_stop_conditions', return_value=None):
            with patch.object(auto_explore, '_find_next_unexplored_tile', return_value=(10, 21)):
                with patch.object(auto_explore, '_calculate_path_to', return_value=[(10, 21)]):
                    action3 = auto_explore.get_next_action(game_map, entities, fov_map)
                    assert action3 is not None  # Third move succeeds
        
        # Move 4: at (10, 21) - second repeat
        player.x, player.y = 10, 21
        
        with patch.object(auto_explore, '_check_stop_conditions', return_value=None):
            with patch.object(auto_explore, '_find_next_unexplored_tile', return_value=(10, 20)):
                with patch.object(auto_explore, '_calculate_path_to', return_value=[(10, 20)]):
                    action4 = auto_explore.get_next_action(game_map, entities, fov_map)
                    assert action4 is not None  # Fourth move succeeds
        
        # Move 5: at (10, 20) - third repeat
        player.x, player.y = 10, 20
        
        with patch.object(auto_explore, '_check_stop_conditions', return_value=None):
            with patch.object(auto_explore, '_find_next_unexplored_tile', return_value=(10, 21)):
                with patch.object(auto_explore, '_calculate_path_to', return_value=[(10, 21)]):
                    action5 = auto_explore.get_next_action(game_map, entities, fov_map)
                    assert action5 is not None  # Fifth move succeeds
        
        # Move 6: at (10, 21) - should detect oscillation and STOP
        player.x, player.y = 10, 21
        
        with patch.object(auto_explore, '_check_stop_conditions', return_value=None):
            action6 = auto_explore.get_next_action(game_map, entities, fov_map)
            
            # Should return None (stopped)
            assert action6 is None
            
            # Should have stopped with oscillation message
            assert not auto_explore.is_active()
            assert auto_explore.stop_reason == "Movement blocked: oscillation detected"
    
    def test_normal_movement_not_detected_as_oscillation(self):
        """Test that normal exploration with some back-and-forth doesn't trigger false positive."""
        # Setup
        auto_explore = AutoExplore()
        
        # Create mock owner (player)
        player = Mock()
        player.x = 10
        player.y = 20
        player.fighter = Mock()
        player.fighter.hp = 100
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        auto_explore.owner = player
        
        # Create mock game_map
        game_map = Mock()
        game_map.width = 50
        game_map.height = 50
        game_map.is_explored = Mock(return_value=False)
        game_map.hazard_manager = Mock()
        game_map.hazard_manager.has_hazard_at = Mock(return_value=False)
        
        # Create tiles array
        tiles = []
        for x in range(50):
            col = []
            for y in range(50):
                tile = Mock()
                tile.blocked = False
                tile.explored = False
                col.append(tile)
            tiles.append(col)
        game_map.tiles = tiles
        
        entities = []
        fov_map = Mock()
        
        # Start auto-explore
        auto_explore.start(game_map, entities, fov_map)
        
        # Simulate normal exploration: moves to different positions
        positions = [(10, 20), (10, 21), (11, 21), (11, 20), (12, 20)]
        
        for pos in positions:
            player.x, player.y = pos
            
            with patch.object(auto_explore, '_check_stop_conditions', return_value=None):
                with patch.object(auto_explore, '_find_next_unexplored_tile', return_value=(pos[0] + 1, pos[1])):
                    with patch.object(auto_explore, '_calculate_path_to', return_value=[(pos[0] + 1, pos[1])]):
                        action = auto_explore.get_next_action(game_map, entities, fov_map)
                        
                        # Should NOT stop for normal movement
                        assert action is not None
                        assert auto_explore.is_active()
    
    def test_short_back_and_forth_not_detected(self):
        """Test that A-B-A-B (only 2 cycles) doesn't trigger oscillation."""
        # Setup
        auto_explore = AutoExplore()
        
        # Create mock owner (player)
        player = Mock()
        player.x = 10
        player.y = 20
        player.fighter = Mock()
        player.fighter.hp = 100
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        auto_explore.owner = player
        
        # Create mock game_map
        game_map = Mock()
        game_map.width = 50
        game_map.height = 50
        game_map.is_explored = Mock(return_value=False)
        game_map.hazard_manager = Mock()
        game_map.hazard_manager.has_hazard_at = Mock(return_value=False)
        
        # Create tiles array
        tiles = []
        for x in range(50):
            col = []
            for y in range(50):
                tile = Mock()
                tile.blocked = False
                tile.explored = False
                col.append(tile)
            tiles.append(col)
        game_map.tiles = tiles
        
        entities = []
        fov_map = Mock()
        
        # Start auto-explore
        auto_explore.start(game_map, entities, fov_map)
        
        # Simulate A-B-A-B (only 4 moves, not enough for detection)
        positions = [(10, 20), (10, 21), (10, 20), (10, 21)]
        
        for pos in positions:
            player.x, player.y = pos
            
            with patch.object(auto_explore, '_check_stop_conditions', return_value=None):
                with patch.object(auto_explore, '_find_next_unexplored_tile', return_value=(pos[0], pos[1] + 1 if pos[1] == 20 else pos[1] - 1)):
                    with patch.object(auto_explore, '_calculate_path_to', return_value=[(pos[0], pos[1] + 1 if pos[1] == 20 else pos[1] - 1)]):
                        action = auto_explore.get_next_action(game_map, entities, fov_map)
                        
                        # Should NOT stop - not enough repetitions
                        assert action is not None
                        assert auto_explore.is_active()
    
    def test_position_history_resets_on_start(self):
        """Test that position history is cleared when auto-explore restarts."""
        # Setup
        auto_explore = AutoExplore()
        
        # Create mock owner (player)
        player = Mock()
        player.x = 10
        player.y = 20
        player.fighter = Mock()
        player.fighter.hp = 100
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        auto_explore.owner = player
        
        # Create mock game_map
        game_map = Mock()
        game_map.width = 50
        game_map.height = 50
        game_map.is_explored = Mock(return_value=False)
        game_map.hazard_manager = Mock()
        game_map.hazard_manager.has_hazard_at = Mock(return_value=False)
        
        # Create tiles array
        tiles = []
        for x in range(50):
            col = []
            for y in range(50):
                tile = Mock()
                tile.blocked = False
                tile.explored = False
                col.append(tile)
            tiles.append(col)
        game_map.tiles = tiles
        
        entities = []
        fov_map = Mock()
        
        # Manually populate position history
        auto_explore._position_history = deque([(1, 1), (2, 2), (3, 3)], maxlen=6)
        
        # Start auto-explore
        auto_explore.start(game_map, entities, fov_map)
        
        # Position history should be cleared
        assert len(auto_explore._position_history) == 0
    
    def test_three_position_cycle_not_detected(self):
        """Test that A-B-C-A-B-C pattern doesn't trigger two-tile oscillation."""
        # Setup
        auto_explore = AutoExplore()
        
        # Create mock owner (player)
        player = Mock()
        player.x = 10
        player.y = 20
        player.fighter = Mock()
        player.fighter.hp = 100
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        auto_explore.owner = player
        
        # Create mock game_map
        game_map = Mock()
        game_map.width = 50
        game_map.height = 50
        game_map.is_explored = Mock(return_value=False)
        game_map.hazard_manager = Mock()
        game_map.hazard_manager.has_hazard_at = Mock(return_value=False)
        
        # Create tiles array
        tiles = []
        for x in range(50):
            col = []
            for y in range(50):
                tile = Mock()
                tile.blocked = False
                tile.explored = False
                col.append(tile)
            tiles.append(col)
        game_map.tiles = tiles
        
        entities = []
        fov_map = Mock()
        
        # Start auto-explore
        auto_explore.start(game_map, entities, fov_map)
        
        # Simulate A-B-C-A-B-C pattern (three-tile cycle)
        positions = [(10, 20), (10, 21), (10, 22), (10, 20), (10, 21), (10, 22)]
        
        for pos in positions:
            player.x, player.y = pos
            
            with patch.object(auto_explore, '_check_stop_conditions', return_value=None):
                with patch.object(auto_explore, '_find_next_unexplored_tile', return_value=(pos[0] + 1, pos[1])):
                    with patch.object(auto_explore, '_calculate_path_to', return_value=[(pos[0] + 1, pos[1])]):
                        action = auto_explore.get_next_action(game_map, entities, fov_map)
                        
                        # Should NOT stop - this is a three-tile cycle, not two-tile oscillation
                        assert action is not None
                        assert auto_explore.is_active()
    
    def test_oscillation_with_diagonal_movement(self):
        """Test oscillation detection with diagonal positions."""
        # Setup
        auto_explore = AutoExplore()
        
        # Create mock owner (player)
        player = Mock()
        player.x = 10
        player.y = 20
        player.fighter = Mock()
        player.fighter.hp = 100
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        auto_explore.owner = player
        
        # Create mock game_map
        game_map = Mock()
        game_map.width = 50
        game_map.height = 50
        game_map.is_explored = Mock(return_value=False)
        game_map.hazard_manager = Mock()
        game_map.hazard_manager.has_hazard_at = Mock(return_value=False)
        
        # Create tiles array
        tiles = []
        for x in range(50):
            col = []
            for y in range(50):
                tile = Mock()
                tile.blocked = False
                tile.explored = False
                col.append(tile)
            tiles.append(col)
        game_map.tiles = tiles
        
        entities = []
        fov_map = Mock()
        
        # Start auto-explore
        auto_explore.start(game_map, entities, fov_map)
        
        # Simulate oscillation between diagonal positions
        positions = [(10, 20), (11, 21), (10, 20), (11, 21), (10, 20), (11, 21)]
        
        for i, pos in enumerate(positions):
            player.x, player.y = pos
            
            with patch.object(auto_explore, '_check_stop_conditions', return_value=None):
                # Alternate targets
                target = (11, 21) if pos == (10, 20) else (10, 20)
                
                with patch.object(auto_explore, '_find_next_unexplored_tile', return_value=target):
                    with patch.object(auto_explore, '_calculate_path_to', return_value=[target]):
                        action = auto_explore.get_next_action(game_map, entities, fov_map)
                        
                        if i < 5:
                            # First 5 moves should succeed
                            assert action is not None
                        else:
                            # 6th move should detect oscillation
                            assert action is None
                            assert not auto_explore.is_active()
                            assert auto_explore.stop_reason == "Movement blocked: oscillation detected"


class TestAutoExploreOscillationIntegration:
    """Integration tests for oscillation detection with opportunistic loot."""
    
    def test_opportunistic_loot_disabled_in_manual_mode(self):
        """Test that opportunistic loot does NOT run in manual play mode (bot_mode=False)."""
        # Setup
        auto_explore = AutoExplore()
        
        # Create mock owner (player)
        player = Mock()
        player.x = 20
        player.y = 30
        player.fighter = Mock()
        player.fighter.hp = 100
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        auto_explore.owner = player
        
        # Create mock game_map
        game_map = Mock()
        game_map.width = 50
        game_map.height = 50
        game_map.is_explored = Mock(return_value=False)
        game_map.hazard_manager = Mock()
        game_map.hazard_manager.has_hazard_at = Mock(return_value=False)
        
        # Create tiles array
        tiles = []
        for x in range(50):
            col = []
            for y in range(50):
                tile = Mock()
                tile.blocked = False
                tile.explored = False
                col.append(tile)
            tiles.append(col)
        game_map.tiles = tiles
        
        entities = []
        fov_map = Mock()
        
        # Start auto-explore in MANUAL mode (bot_mode=False)
        auto_explore.start(game_map, entities, fov_map, bot_mode=False)
        
        # Verify bot_mode is False
        assert auto_explore.bot_mode is False
        
        # Mock the opportunistic loot method to verify it's NOT called
        with patch.object(auto_explore, '_find_opportunistic_loot_target') as mock_loot:
            with patch.object(auto_explore, '_check_stop_conditions', return_value=None):
                with patch.object(auto_explore, '_find_next_unexplored_tile', return_value=(25, 25)):
                    with patch.object(auto_explore, '_calculate_path_to', return_value=[(21, 30)]):
                        action = auto_explore.get_next_action(game_map, entities, fov_map)
                        
                        # Should succeed
                        assert action is not None
                        
                        # Opportunistic loot should NOT be called in manual mode
                        mock_loot.assert_not_called()
    
    def test_opportunistic_loot_enabled_in_bot_mode(self):
        """Test that opportunistic loot DOES run in bot mode (bot_mode=True)."""
        # Setup
        auto_explore = AutoExplore()
        
        # Create mock owner (player)
        player = Mock()
        player.x = 20
        player.y = 30
        player.fighter = Mock()
        player.fighter.hp = 100
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        auto_explore.owner = player
        
        # Create mock game_map
        game_map = Mock()
        game_map.width = 50
        game_map.height = 50
        game_map.is_explored = Mock(return_value=False)
        game_map.hazard_manager = Mock()
        game_map.hazard_manager.has_hazard_at = Mock(return_value=False)
        
        # Create tiles array
        tiles = []
        for x in range(50):
            col = []
            for y in range(50):
                tile = Mock()
                tile.blocked = False
                tile.explored = False
                col.append(tile)
            tiles.append(col)
        game_map.tiles = tiles
        
        entities = []
        fov_map = Mock()
        
        # Start auto-explore in BOT mode (bot_mode=True)
        auto_explore.start(game_map, entities, fov_map, bot_mode=True)
        
        # Verify bot_mode is True
        assert auto_explore.bot_mode is True
        
        # Mock the opportunistic loot method to verify it IS called
        with patch.object(auto_explore, '_find_opportunistic_loot_target', return_value=None) as mock_loot:
            with patch.object(auto_explore, '_check_stop_conditions', return_value=None):
                with patch.object(auto_explore, '_find_next_unexplored_tile', return_value=(25, 25)):
                    with patch.object(auto_explore, '_calculate_path_to', return_value=[(21, 30)]):
                        action = auto_explore.get_next_action(game_map, entities, fov_map)
                        
                        # Should succeed
                        assert action is not None
                        
                        # Opportunistic loot SHOULD be called in bot mode
                        mock_loot.assert_called_once()
    
    def test_opportunistic_loot_oscillation_scenario(self):
        """Test that oscillation is detected when opportunistic loot causes back-and-forth."""
        # This is a more realistic scenario where:
        # 1. Player at A, sees loot at B
        # 2. Moves to B (opportunistic loot)
        # 3. At B, loot is at player position (skipped), finds target back at A
        # 4. Repeats
        
        # Setup
        auto_explore = AutoExplore()
        
        # Create mock owner (player)
        player = Mock()
        player.x = 20
        player.y = 30
        player.fighter = Mock()
        player.fighter.hp = 100
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        auto_explore.owner = player
        
        # Create mock game_map
        game_map = Mock()
        game_map.width = 50
        game_map.height = 50
        game_map.is_explored = Mock(return_value=False)
        game_map.hazard_manager = Mock()
        game_map.hazard_manager.has_hazard_at = Mock(return_value=False)
        
        # Create tiles array
        tiles = []
        for x in range(50):
            col = []
            for y in range(50):
                tile = Mock()
                tile.blocked = False
                tile.explored = False
                col.append(tile)
            tiles.append(col)
        game_map.tiles = tiles
        
        entities = []
        fov_map = Mock()
        
        # Start auto-explore in BOT mode (since this tests opportunistic loot oscillation)
        auto_explore.start(game_map, entities, fov_map, bot_mode=True)
        
        # Simulate the oscillation from the bug report: (20,30) ↔ (20,31)
        oscillation_positions = [
            (20, 31), (20, 30), (20, 31), (20, 30), (20, 31), (20, 30)
        ]
        
        for i, pos in enumerate(oscillation_positions):
            player.x, player.y = pos
            
            with patch.object(auto_explore, '_check_stop_conditions', return_value=None):
                # Alternate targets based on current position
                if pos == (20, 30):
                    target = (20, 31)  # At A, target B
                else:
                    target = (20, 30)  # At B, target A
                
                with patch.object(auto_explore, '_find_opportunistic_loot_target', return_value=target):
                    with patch.object(auto_explore, '_calculate_path_to', return_value=[target]):
                        action = auto_explore.get_next_action(game_map, entities, fov_map)
                        
                        if i < 5:
                            # First 5 moves should succeed
                            assert action is not None, f"Move {i} should succeed"
                            assert auto_explore.is_active(), f"AutoExplore should be active at move {i}"
                        else:
                            # 6th move should detect oscillation
                            assert action is None, f"Move {i} should detect oscillation"
                            assert not auto_explore.is_active(), f"AutoExplore should stop at move {i}"
                            assert auto_explore.stop_reason == "Movement blocked: oscillation detected"

