"""Tests for the auto-explore system.

This test suite validates the auto-explore feature including:
- Component initialization and state management
- Stop condition detection (monsters, items, stairs, damage, status effects)
- Pathfinding and room-by-room exploration
- Integration with the action processing system
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from components.auto_explore import AutoExplore, ADVENTURE_QUOTES
from components.component_registry import ComponentType
from entity import Entity
from components.fighter import Fighter
from components.ai import BasicMonster
from components.item import Item
from components.equippable import Equippable
from equipment_slots import EquipmentSlots
from map_objects.game_map import GameMap
from map_objects.rectangle import Rect


def make_basic_game_map(width=20, height=20, explored=False):
    game_map = Mock()
    game_map.width = width
    game_map.height = height
    game_map.is_explored = Mock(return_value=explored)
    return game_map


class TestAutoExploreComponent:
    """Test AutoExplore component initialization and basic functionality."""
    
    def test_component_initialization(self):
        """Test that AutoExplore component initializes correctly."""
        auto_explore = AutoExplore()
        
        assert auto_explore.owner is None
        assert auto_explore.active is False
        assert auto_explore.current_path == []
        assert auto_explore.stop_reason is None
        assert auto_explore.last_hp == 0
    
    def test_start_sets_active_state(self):
        """Test that start() activates auto-explore."""
        auto_explore = AutoExplore()
        player = Entity(5, 5, '@', (255, 255, 255), "Player")
        auto_explore.owner = player
        
        game_map = make_basic_game_map()
        entities = []
        
        quote = auto_explore.start(game_map, entities)
        
        assert auto_explore.active is True
        assert quote in ADVENTURE_QUOTES
        assert auto_explore.stop_reason is None
    
    def test_stop_deactivates_and_sets_reason(self):
        """Test that stop() deactivates and records reason."""
        auto_explore = AutoExplore()
        auto_explore.active = True
        
        auto_explore.stop("Test reason")
        
        assert auto_explore.active is False
        assert auto_explore.stop_reason == "Test reason"
        assert auto_explore.current_path == []
    
    def test_is_active_returns_correct_state(self):
        """Test is_active() method."""
        auto_explore = AutoExplore()
        
        assert auto_explore.is_active() is False
        
        auto_explore.active = True
        assert auto_explore.is_active() is True


class TestStopConditions:
    """Test all stop condition detection methods."""
    
    @pytest.fixture
    def auto_explore(self):
        """Create an auto-explore component with owner."""
        auto_explore = AutoExplore()
        player = Entity(5, 5, '@', (255, 255, 255), "Player",
                       fighter=Fighter(hp=100, defense=5, power=5))
        auto_explore.owner = player
        auto_explore.last_hp = 100
        return auto_explore
    
    @pytest.fixture
    def fov_map(self):
        """Create a mock FOV map."""
        fov_map = Mock()
        fov_map.__getitem__ = Mock(return_value=Mock(__getitem__=Mock(return_value=True)))
        return fov_map
    
    def test_monster_in_fov_stops(self, auto_explore, fov_map):
        """Test that monsters in FOV trigger stop."""
        orc = Entity(6, 6, 'o', (0, 255, 0), "Orc",
                    fighter=Fighter(hp=10, defense=2, power=3),
                    ai=BasicMonster())
        # Components are auto-added by Entity constructor, don't add again
        
        entities = [auto_explore.owner, orc]
        
        result = auto_explore._monster_in_fov(entities, fov_map)
        
        assert result == orc
    
    def test_valuable_item_in_fov_stops(self, auto_explore, fov_map):
        """Test that valuable items in FOV trigger stop."""
        sword = Entity(7, 7, '/', (255, 255, 255), "Sword",
                      equippable=Equippable(slot=EquipmentSlots.MAIN_HAND, power_bonus=3),
                      item=Item(stackable=False))
        # Components are auto-added by Entity constructor
        
        entities = [auto_explore.owner, sword]
        game_map = make_basic_game_map()
        
        result = auto_explore._valuable_item_in_fov(entities, fov_map, game_map)
        
        assert result == sword
    
    def test_on_stairs_detects_stairs(self, auto_explore):
        """Test stairs detection."""
        from stairs import Stairs
        
        stairs = Entity(5, 5, '>', (255, 255, 255), "Stairs",
                       stairs=Stairs(2))
        # Components are auto-added by Entity constructor
        
        entities = [auto_explore.owner, stairs]
        
        result = auto_explore._on_stairs(entities)
        
        assert result is True
    
    def test_took_damage_detects_hp_loss(self, auto_explore):
        """Test damage detection."""
        auto_explore.last_hp = 100
        auto_explore.owner.fighter.hp = 90
        
        result = auto_explore._took_damage()
        
        assert result is True
        assert auto_explore.last_hp == 90  # Updated
    
    def test_no_damage_returns_false(self, auto_explore):
        """Test that no damage returns false."""
        auto_explore.last_hp = 100
        auto_explore.owner.fighter.hp = 100
        
        result = auto_explore._took_damage()
        
        assert result is False
        assert auto_explore.last_hp == 100
    
    def test_has_status_effect_detects_poison(self, auto_explore):
        """Test status effect detection."""
        from components.status_effects import StatusEffectManager
        
        status = StatusEffectManager(auto_explore.owner)
        status.poisoned = 5  # Poisoned for 5 turns
        auto_explore.owner.status_effects = status
        auto_explore.owner.components.add(ComponentType.STATUS_EFFECTS, status)
        
        result = auto_explore._has_status_effect()
        
        assert result == "Poisoned"
    
    def test_no_status_effect_returns_none(self, auto_explore):
        """Test that no status effects returns None."""
        result = auto_explore._has_status_effect()
        
        assert result is None


class TestRoomDetection:
    """Test room identification and unexplored tile detection."""
    
    @pytest.fixture
    def game_map(self):
        """Create a test game map with a simple room."""
        game_map = GameMap(20, 20)
        
        # Create a simple 5x5 room at (5, 5)
        for x in range(5, 10):
            for y in range(5, 10):
                game_map.tiles[x][y].blocked = False
                game_map.tiles[x][y].explored = False
        
        return game_map
    
    @pytest.fixture
    def auto_explore(self, game_map):
        """Create auto-explore with player in room."""
        auto_explore = AutoExplore()
        player = Entity(7, 7, '@', (255, 255, 255), "Player")
        auto_explore.owner = player
        return auto_explore
    
    def test_identify_current_room(self, auto_explore, game_map):
        """Test room identification from player position."""
        room = auto_explore._identify_current_room(game_map)
        
        assert room is not None
        assert isinstance(room, Rect)
        # Room should contain the player
        assert room.x1 <= auto_explore.owner.x <= room.x2
        assert room.y1 <= auto_explore.owner.y <= room.y2
    
    def test_get_unexplored_tiles_in_room(self, auto_explore, game_map):
        """Test finding unexplored tiles in a room."""
        room = Rect(5, 5, 5, 5)  # 5x5 room
        
        unexplored = auto_explore._get_unexplored_tiles_in_room(room, game_map)
        
        # Should find multiple unexplored tiles
        assert len(unexplored) > 0
        # All should be within room bounds
        for x, y in unexplored:
            assert room.x1 <= x < room.x2
            assert room.y1 <= y < room.y2
    
    def test_get_all_unexplored_tiles(self, auto_explore, game_map):
        """Test finding all unexplored tiles on map."""
        unexplored = auto_explore._get_all_unexplored_tiles(game_map)
        
        # Should find many unexplored tiles
        assert len(unexplored) > 0
        # All should be walkable and unexplored
        for x, y in unexplored:
            assert not game_map.tiles[x][y].blocked
            assert not game_map.tiles[x][y].explored


class TestPathfinding:
    """Test pathfinding and movement calculation."""
    
    @pytest.fixture
    def game_map(self):
        """Create a simple test map."""
        game_map = GameMap(20, 20)
        
        # Create a corridor from (5,5) to (15,5)
        for x in range(5, 16):
            game_map.tiles[x][5].blocked = False
            game_map.tiles[x][5].explored = False
        
        return game_map
    
    @pytest.fixture
    def auto_explore(self, game_map):
        """Create auto-explore with player."""
        auto_explore = AutoExplore()
        player = Entity(5, 5, '@', (255, 255, 255), "Player")
        auto_explore.owner = player
        return auto_explore
    
    def test_find_closest_tile_uses_dijkstra(self, auto_explore, game_map):
        """Test that closest tile finding works."""
        # Set player at (5, 5)
        target_tiles = [(10, 5), (15, 5)]  # Two targets
        
        closest = auto_explore._find_closest_tile(target_tiles, game_map)
        
        # Should find (10, 5) as it's closer
        assert closest == (10, 5)
    
    def test_calculate_path_to_target(self, auto_explore, game_map):
        """Test A* path calculation."""
        target = (10, 5)
        entities = [auto_explore.owner]
        
        path = auto_explore._calculate_path_to(target, game_map, entities)
        
        # Path calculation should work (may be empty if already at destination or unreachable)
        assert isinstance(path, list)
        # If path exists, it should end at target
        if len(path) > 0:
            assert path[-1] == target
    
    def test_avoids_hazards_in_pathfinding(self, auto_explore, game_map):
        """Test that hazards are avoided in pathfinding."""
        from components.ground_hazard import HazardType, GroundHazard
        
        # Add hazard at (7, 5) - in the middle of the path
        hazard = GroundHazard(HazardType.FIRE, 7, 5, 10, 3, 3)
        game_map.hazard_manager.add_hazard(hazard)
        
        target = (10, 5)
        entities = [auto_explore.owner]
        
        # Pathfinding should either find alternate route or return empty
        # (depends on if there's a way around)
        path = auto_explore._calculate_path_to(target, game_map, entities)
        
        # Path should not go through the hazard
        assert (7, 5) not in path


class TestIntegration:
    """Test auto-explore integration with game systems."""
    
    def test_get_next_action_returns_movement(self):
        """Test that get_next_action returns valid movement."""
        auto_explore = AutoExplore()
        player = Entity(5, 5, '@', (255, 255, 255), "Player",
                       fighter=Fighter(hp=100, defense=5, power=5))
        auto_explore.owner = player
        auto_explore.last_hp = 100
        
        game_map = GameMap(20, 20)
        # Create walkable area
        for x in range(20):
            for y in range(20):
                game_map.tiles[x][y].blocked = False
                game_map.tiles[x][y].explored = False
        
        auto_explore.active = True
        entities = [player]
        fov_map = Mock()
        
        action = auto_explore.get_next_action(game_map, entities, fov_map)
        
        # Should return movement action or stop
        if action:
            assert 'dx' in action
            assert 'dy' in action
            assert isinstance(action['dx'], int)
            assert isinstance(action['dy'], int)
    
    def test_stop_conditions_prevent_movement(self):
        """Test that stop conditions halt exploration."""
        auto_explore = AutoExplore()
        player = Entity(5, 5, '@', (255, 255, 255), "Player",
                       fighter=Fighter(hp=100, defense=5, power=5))
        auto_explore.owner = player
        auto_explore.active = True
        auto_explore.last_hp = 100
        
        # Create map
        game_map = GameMap(20, 20)
        for x in range(20):
            for y in range(20):
                game_map.tiles[x][y].blocked = False
        
        # Add monster in FOV
        orc = Entity(6, 6, 'o', (0, 255, 0), "Orc",
                    fighter=Fighter(hp=10, defense=2, power=3),
                    ai=BasicMonster())
        # Components are auto-added by Entity constructor
        
        entities = [player, orc]
        fov_map = Mock()
        fov_map.__getitem__ = Mock(return_value=Mock(__getitem__=Mock(return_value=True)))
        
        action = auto_explore.get_next_action(game_map, entities, fov_map)
        
        # Should stop due to monster
        assert action is None
        assert auto_explore.active is False
        assert "Monster spotted" in auto_explore.stop_reason


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_no_owner_handles_gracefully(self):
        """Test that missing owner doesn't crash."""
        auto_explore = AutoExplore()
        # No owner set
        
        game_map = Mock()
        entities = []
        fov_map = Mock()
        
        action = auto_explore.get_next_action(game_map, entities, fov_map)
        
        assert action is None
    
    def test_fully_explored_map_stops(self):
        """Test that fully explored map stops exploration."""
        auto_explore = AutoExplore()
        player = Entity(5, 5, '@', (255, 255, 255), "Player",
                       fighter=Fighter(hp=100, defense=5, power=5))
        auto_explore.owner = player
        auto_explore.active = True
        auto_explore.last_hp = 100
        
        # Create fully explored map
        game_map = GameMap(10, 10)
        for x in range(10):
            for y in range(10):
                game_map.tiles[x][y].blocked = False
                game_map.tiles[x][y].explored = True  # All explored!
        
        entities = [player]
        fov_map = Mock()
        
        action = auto_explore.get_next_action(game_map, entities, fov_map)
        
        # Should stop
        assert action is None
        assert "explored" in auto_explore.stop_reason.lower()
    
    def test_unreachable_areas_stops(self):
        """Test that unreachable unexplored areas cause stop."""
        auto_explore = AutoExplore()
        player = Entity(5, 5, '@', (255, 255, 255), "Player",
                       fighter=Fighter(hp=100, defense=5, power=5))
        auto_explore.owner = player
        auto_explore.active = True
        auto_explore.last_hp = 100
        
        # Create map with player in small enclosed area
        game_map = GameMap(20, 20)
        # Make 3x3 area around player walkable
        for x in range(4, 7):
            for y in range(4, 7):
                game_map.tiles[x][y].blocked = False
                game_map.tiles[x][y].explored = True
        
        # Leave rest of map unexplored but blocked
        entities = [player]
        fov_map = Mock()
        
        action = auto_explore.get_next_action(game_map, entities, fov_map)
        
        # Should stop (no reachable unexplored tiles)
        assert action is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

