"""Regression tests for auto-explore bugs.

This test suite covers all the auto-explore bugs we've fixed to ensure
they don't regress in the future.

Bug History:
1. Corpses stopping exploration (fixed: check hp > 0)
2. Pathfinding IndexError on valid coordinates (fixed: proper bounds checking)
3. Items on ground stopping exploration (fixed: track known_items)
4. Array transpose breaking pathfinding (fixed: keep transpose for tcod)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from components.auto_explore import AutoExplore
from components.component_registry import ComponentType
from entity import Entity
from components.fighter import Fighter
from components.ai import BasicMonster
from components.item import Item


def make_basic_game_map(width=80, height=45, explored=False):
    game_map = Mock()
    game_map.width = width
    game_map.height = height
    game_map.is_explored = Mock(return_value=explored)
    game_map.is_blocked = Mock(return_value=False)
    game_map.secret_door_manager = None
    return game_map


class TestAutoExplorePathfinding:
    """Test pathfinding core functionality."""
    
    def test_pathfinding_creates_correct_array_shape(self):
        """Verify cost array has correct shape after transpose."""
        # Create test map
        width, height = 80, 45
        game_map = Mock()
        game_map.width = width
        game_map.height = height
        game_map.tiles = [[Mock(blocked=False) for _ in range(height)] for _ in range(width)]
        game_map.hazard_manager = Mock()
        game_map.hazard_manager.has_hazard_at = Mock(return_value=False)
        
        # Create player
        player = Entity(10, 10, '@', (255, 255, 255), 'Player', blocks=True)
        
        # Create auto-explore
        auto_explore = AutoExplore()
        auto_explore.owner = player
        
        # Calculate path
        target = (15, 15)
        path = auto_explore._calculate_path_to(target, game_map, [player])
        
        # Should not crash and should find a path
        assert path is not None
        assert isinstance(path, list)
    
    def test_pathfinding_works_near_map_edges(self):
        """Ensure pathfinding doesn't crash near map boundaries."""
        # Create test map
        width, height = 80, 45
        game_map = Mock()
        game_map.width = width
        game_map.height = height
        game_map.tiles = [[Mock(blocked=False) for _ in range(height)] for _ in range(width)]
        game_map.hazard_manager = Mock()
        game_map.hazard_manager.has_hazard_at = Mock(return_value=False)
        
        # Test pathfinding from various edge positions
        edge_positions = [
            (0, 0),      # Top-left corner
            (79, 0),     # Top-right corner
            (0, 44),     # Bottom-left corner
            (79, 44),    # Bottom-right corner
            (40, 0),     # Top edge
            (40, 44),    # Bottom edge
            (0, 22),     # Left edge
            (79, 22),    # Right edge
        ]
        
        for start_x, start_y in edge_positions:
            player = Entity(start_x, start_y, '@', (255, 255, 255), 'Player', blocks=True)
            auto_explore = AutoExplore()
            auto_explore.owner = player
            
            # Try to pathfind to center
            target = (40, 22)
            path = auto_explore._calculate_path_to(target, game_map, [player])
            
            # Should not crash
            assert path is not None, f"Pathfinding failed from ({start_x}, {start_y})"
    
    def test_pathfinding_avoids_walls(self):
        """Verify pathfinding routes around blocked tiles."""
        # Create test map with wall
        width, height = 10, 10
        game_map = Mock()
        game_map.width = width
        game_map.height = height
        
        # Create tiles (all walkable except a wall at x=5, y=2-7)
        # This leaves passages at top (y=0,1) and bottom (y=8,9)
        game_map.tiles = [[Mock(blocked=False) for _ in range(height)] for _ in range(width)]
        for y in range(2, 8):  # Wall from y=2 to y=7 (not full height)
            game_map.tiles[5][y].blocked = True
        
        game_map.hazard_manager = Mock()
        game_map.hazard_manager.has_hazard_at = Mock(return_value=False)
        
        # Player on left side of wall
        player = Entity(3, 5, '@', (255, 255, 255), 'Player', blocks=True)
        auto_explore = AutoExplore()
        auto_explore.owner = player
        
        # Target on right side of wall
        target = (7, 5)
        path = auto_explore._calculate_path_to(target, game_map, [player])
        
        # Should find a path that goes around the wall (via top or bottom)
        assert path is not None
        assert len(path) > 0, "No path found around wall"
        # Path should go around the wall (not through the blocked section)
        for x, y in path:
            if x == 5:
                # If path crosses x=5, it must be at y < 2 or y >= 8
                assert y < 2 or y >= 8, f"Path went through wall at ({x}, {y})"
    
    def test_pathfinding_handles_out_of_bounds_gracefully(self):
        """Verify out-of-bounds player position doesn't crash, returns empty path."""
        # Create test map
        width, height = 80, 45
        game_map = Mock()
        game_map.width = width
        game_map.height = height
        game_map.tiles = [[Mock(blocked=False) for _ in range(height)] for _ in range(width)]
        game_map.hazard_manager = Mock()
        game_map.hazard_manager.has_hazard_at = Mock(return_value=False)
        
        # Test various out-of-bounds positions
        invalid_positions = [
            (-1, 10),      # Negative x
            (10, -1),      # Negative y
            (100, 10),     # x too large
            (10, 100),     # y too large
            (100, 100),    # Both too large
        ]
        
        for x, y in invalid_positions:
            player = Entity(x, y, '@', (255, 255, 255), 'Player', blocks=True)
            auto_explore = AutoExplore()
            auto_explore.owner = player
            
            target = (40, 22)
            path = auto_explore._calculate_path_to(target, game_map, [player])
            
            # Should return empty path, not crash
            assert path == [], f"Expected empty path for out-of-bounds position ({x}, {y})"


class TestAutoExploreStopConditions:
    """Test what stops auto-explore."""
    
    def test_corpse_does_not_stop_exploration(self):
        """Bug fix: Corpses (hp <= 0) should not stop auto-explore."""
        # Create test environment
        game_map = Mock()
        fov_map = Mock()
        
        # Create player
        player = Entity(10, 10, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Mock(hp=100)
        
        # Create dead orc (corpse)
        orc = Entity(15, 15, '%', (100, 100, 100), 'Orc Corpse', blocks=False)
        orc.fighter = Mock(hp=0)  # Dead - hp is 0
        orc.ai = BasicMonster()
        orc.components = Mock()
        orc.components.has = Mock(side_effect=lambda t: t in [ComponentType.AI, ComponentType.FIGHTER])
        orc.get_component_optional = Mock(return_value=orc.fighter)
        
        # Mock FOV to see the corpse
        with patch('fov_functions.map_is_in_fov', return_value=True):
            auto_explore = AutoExplore()
            auto_explore.owner = player
            
            # Check if corpse stops exploration
            monster = auto_explore._monster_in_fov([player, orc], fov_map)
            
            # Should NOT stop for corpse
            assert monster is None, "Auto-explore stopped for corpse (hp <= 0)"
    
    def test_living_monster_stops_exploration(self):
        """Living monsters (hp > 0) should stop auto-explore."""
        # Create test environment
        game_map = Mock()
        fov_map = Mock()
        
        # Create player
        player = Entity(10, 10, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Mock(hp=100)
        
        # Create living orc
        orc = Entity(15, 15, 'o', (0, 128, 0), 'Orc', blocks=True)
        orc.fighter = Mock(hp=10)  # Alive - hp > 0
        orc.ai = BasicMonster()
        orc.components = Mock()
        orc.components.has = Mock(side_effect=lambda t: t in [ComponentType.AI, ComponentType.FIGHTER])
        orc.get_component_optional = Mock(return_value=orc.fighter)
        
        # Mock FOV to see the orc
        with patch('fov_functions.map_is_in_fov', return_value=True):
            auto_explore = AutoExplore()
            auto_explore.owner = player
            
            # Check if living orc stops exploration
            monster = auto_explore._monster_in_fov([player, orc], fov_map)
            
            # Should stop for living monster
            assert monster == orc, "Auto-explore didn't stop for living monster"
    
    def test_known_items_do_not_stop_exploration(self):
        """Bug fix: Items visible when exploration started should not stop it."""
        # Create test environment
        game_map = make_basic_game_map()
        fov_map = Mock()
        
        # Create player
        player = Entity(10, 10, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Mock(hp=100)
        
        # Create potion
        potion = Entity(12, 12, '!', (255, 0, 255), 'Potion', blocks=False)
        potion.item = Item(use_function=Mock())
        potion.components = Mock()
        potion.components.has = Mock(side_effect=lambda t: t == ComponentType.ITEM)
        potion.components.get = Mock(return_value=potion.item)
        
        # Mock FOV
        with patch('fov_functions.map_is_in_fov', return_value=True):
            auto_explore = AutoExplore()
            auto_explore.owner = player
            
            # Start exploration with potion already visible
            auto_explore.start(game_map, [player, potion], fov_map)
            
            # Check if potion stops exploration
            item = auto_explore._valuable_item_in_fov([player, potion], fov_map, game_map)
            
            # Should NOT stop for known item
            assert item is None, "Auto-explore stopped for item that was already visible"
    
    def test_new_items_do_stop_exploration(self):
        """New items discovered during exploration should stop it."""
        # Create test environment
        game_map = make_basic_game_map()
        fov_map = Mock()
        
        # Create player
        player = Entity(10, 10, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Mock(hp=100)
        
        # Create potion (not visible at start)
        potion = Entity(12, 12, '!', (255, 0, 255), 'Potion', blocks=False)
        potion.item = Item(use_function=Mock())
        potion.components = Mock()
        potion.components.has = Mock(side_effect=lambda t: t == ComponentType.ITEM)
        potion.components.get = Mock(return_value=potion.item)
        
        auto_explore = AutoExplore()
        auto_explore.owner = player
        
        # Start exploration with no items visible
        with patch('fov_functions.map_is_in_fov', return_value=False):
            auto_explore.start(game_map, [player, potion], fov_map)
        
        # Now potion comes into view
        with patch('fov_functions.map_is_in_fov', return_value=True):
            item = auto_explore._valuable_item_in_fov([player, potion], fov_map, game_map)
            
            # Should stop for new item
            assert item == potion, "Auto-explore didn't stop for newly discovered item"
    
    def test_multiple_known_items_do_not_stop_exploration(self):
        """Multiple items visible at start should all be tracked."""
        # Create test environment
        game_map = make_basic_game_map()
        fov_map = Mock()
        
        # Create player
        player = Entity(10, 10, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Mock(hp=100)
        
        # Create multiple items
        potion1 = Entity(12, 12, '!', (255, 0, 255), 'Potion', blocks=False)
        potion1.item = Item(use_function=Mock())
        potion1.components = Mock()
        potion1.components.has = Mock(side_effect=lambda t: t == ComponentType.ITEM)
        potion1.components.get = Mock(return_value=potion1.item)
        
        potion2 = Entity(13, 13, '!', (255, 0, 255), 'Potion', blocks=False)
        potion2.item = Item(use_function=Mock())
        potion2.components = Mock()
        potion2.components.has = Mock(side_effect=lambda t: t == ComponentType.ITEM)
        potion2.components.get = Mock(return_value=potion2.item)
        
        scroll = Entity(14, 14, '?', (255, 255, 0), 'Scroll', blocks=False)
        scroll.item = Item(use_function=Mock())
        scroll.components = Mock()
        scroll.components.has = Mock(side_effect=lambda t: t == ComponentType.ITEM)
        scroll.components.get = Mock(return_value=scroll.item)
        
        entities = [player, potion1, potion2, scroll]
        
        # Mock FOV - all items visible
        with patch('fov_functions.map_is_in_fov', return_value=True):
            auto_explore = AutoExplore()
            auto_explore.owner = player
            
            # Start exploration with all items visible
            auto_explore.start(game_map, entities, fov_map)
            
            # Verify all items are tracked
            assert len(auto_explore.known_items) == 3
            
            # Check none of them stop exploration
            item = auto_explore._valuable_item_in_fov(entities, fov_map, game_map)
            assert item is None, "Auto-explore stopped for items that were already visible"


class TestAutoExploreIntegration:
    """Integration tests for auto-explore."""
    
    def test_start_and_stop(self):
        """Test basic start/stop functionality."""
        game_map = make_basic_game_map()
        fov_map = Mock()
        
        player = Entity(10, 10, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Mock(hp=100)
        
        auto_explore = AutoExplore()
        auto_explore.owner = player
        
        # Start exploration
        with patch('fov_functions.map_is_in_fov', return_value=False):
            quote = auto_explore.start(game_map, [player], fov_map)
        
        assert auto_explore.active is True
        assert isinstance(quote, str)
        assert len(quote) > 0
        
        # Stop exploration
        auto_explore.stop("Test stop")
        
        assert auto_explore.active is False
        assert auto_explore.stop_reason == "Test stop"
    
    def test_reset_known_items_on_new_exploration(self):
        """Starting new exploration should reset known items."""
        game_map = make_basic_game_map()
        fov_map = Mock()
        
        player = Entity(10, 10, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Mock(hp=100)
        
        potion = Entity(12, 12, '!', (255, 0, 255), 'Potion', blocks=False)
        potion.item = Item(use_function=Mock())
        potion.components = Mock()
        potion.components.has = Mock(side_effect=lambda t: t == ComponentType.ITEM)
        potion.components.get = Mock(return_value=potion.item)
        
        auto_explore = AutoExplore()
        auto_explore.owner = player
        
        # First exploration with potion visible
        with patch('fov_functions.map_is_in_fov', return_value=True):
            auto_explore.start(game_map, [player, potion], fov_map)
            assert len(auto_explore.known_items) == 1
        
        # Second exploration should reset
        with patch('fov_functions.map_is_in_fov', return_value=False):
            auto_explore.start(game_map, [player, potion], fov_map)
            assert len(auto_explore.known_items) == 0


def test_auto_explore_not_cancelled_by_initiating_right_click(monkeypatch):
    """Ensure the initiating right-click that starts auto-explore does not immediately cancel it."""
    from types import SimpleNamespace
    from game_states import GameStates
    from game_actions import ActionProcessor

    class DummyStateManager:
        def __init__(self, state):
            self.state = state
            self._extras = {}

        def set_extra_data(self, key, value):
            self._extras[key] = value

        def get_extra_data(self, key, default=None):
            return self._extras.get(key, default)

        def set_game_state(self, new_state):
            self.state.current_state = new_state

    auto_explore = AutoExplore()
    auto_explore.active = True
    auto_explore.stop_reason = None
    auto_explore.stop = Mock()

    class DummyPlayer:
        def __init__(self):
            self.x = 1
            self.y = 1
            self.components = Mock()
            self._components = {ComponentType.AUTO_EXPLORE: auto_explore}

        def get_component_optional(self, component):
            return self._components.get(component)

    player = DummyPlayer()
    auto_explore.owner = player

    state = SimpleNamespace(
        current_state=GameStates.PLAYERS_TURN,
        player=player,
        entities=[],
        game_map=Mock(),
        message_log=Mock(),
        fov_map=Mock(),
    )
    state_manager = DummyStateManager(state)
    # Simulate prior run state (no special flag required for guard)
    state_manager.set_extra_data("auto_explore_suppress_cancel_once", False)

    # Stub out turn controller and auto-explore stepping to avoid side effects
    monkeypatch.setattr("systems.turn_controller.initialize_turn_controller", lambda *args, **kwargs: Mock())

    action_processor = ActionProcessor(state_manager, is_bot_mode=False)
    action_processor.turn_controller = Mock()
    action_processor._process_auto_explore_turn = Mock()

    right_click_action = {"right_click": (5, 5)}
    duplicate_right_click = {"right_click": (5, 5)}

    action_processor.process_actions({}, right_click_action)
    # Duplicate event should be suppressed, not cancel
    action_processor.process_actions({}, duplicate_right_click)

    assert auto_explore.active is True
    auto_explore.stop.assert_not_called()
    action_processor._process_auto_explore_turn.assert_called()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

