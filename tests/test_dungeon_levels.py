"""
Unit tests for dungeon level progression and multi-level mechanics.

Tests the dungeon level system including:
- GameMap dungeon level tracking
- next_floor mechanics and level transitions
- Entity management across level changes
- Player healing and positioning
- Level-based difficulty progression
"""

import pytest
from unittest.mock import Mock, patch

from map_objects.game_map import GameMap
from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from game_messages import MessageLog
from render_functions import RenderOrder


class TestGameMapDungeonLevel:
    """Test GameMap dungeon level tracking."""

    def test_game_map_default_dungeon_level(self):
        """Test GameMap initializes with dungeon level 1."""
        game_map = GameMap(width=80, height=43)
        
        assert game_map.dungeon_level == 1
        assert game_map.width == 80
        assert game_map.height == 43

    def test_game_map_custom_dungeon_level(self):
        """Test GameMap with custom initial dungeon level."""
        game_map = GameMap(width=50, height=30, dungeon_level=5)
        
        assert game_map.dungeon_level == 5
        assert game_map.width == 50
        assert game_map.height == 30

    def test_game_map_tile_initialization(self):
        """Test that GameMap properly initializes tiles."""
        game_map = GameMap(width=10, height=10)
        
        # Should have a 2D array of tiles
        assert len(game_map.tiles) == 10
        assert len(game_map.tiles[0]) == 10
        
        # All tiles should be blocked by default
        for x in range(10):
            for y in range(10):
                assert game_map.tiles[x][y].blocked is True

    def test_game_map_reinitialize_tiles(self):
        """Test that tiles can be reinitialized."""
        game_map = GameMap(width=5, height=5)
        
        # Modify a tile
        game_map.tiles[2][2].blocked = False
        game_map.tiles[2][2].explored = True
        
        # Reinitialize
        game_map.tiles = game_map.initialize_tiles()
        
        # Should be reset to default state
        assert game_map.tiles[2][2].blocked is True
        assert game_map.tiles[2][2].explored is False


class TestNextFloorMechanics:
    """Test next_floor level transition mechanics."""

    def setup_method(self):
        """Set up common test objects."""
        # Create player with fighter and level components
        self.fighter_component = Fighter(hp=30, defense=2, power=5)
        self.inventory_component = Inventory(26)
        self.level_component = Level()
        
        self.player = Entity(
            10, 10, '@', (255, 255, 255), 'Player',
            blocks=True, render_order=RenderOrder.ACTOR,
            fighter=self.fighter_component,
            inventory=self.inventory_component,
            level=self.level_component
        )
        
        self.message_log = MessageLog(10, 50, 5)
        
        # Mock constants
        self.constants = {
            'max_rooms': 30,
            'room_min_size': 6,
            'room_max_size': 10,
            'map_width': 80,
            'map_height': 43,
            'max_monsters_per_room': 3,
            'max_items_per_room': 2
        }

    def test_next_floor_increments_dungeon_level(self):
        """Test that next_floor increments the dungeon level."""
        game_map = GameMap(width=80, height=43, dungeon_level=1)
        
        with patch.object(game_map, 'make_map') as mock_make_map:
            entities = game_map.next_floor(self.player, self.message_log, self.constants)
            
            assert game_map.dungeon_level == 2
            mock_make_map.assert_called_once()

    def test_next_floor_resets_entities_to_player_only(self):
        """Test that next_floor returns only player entity."""
        game_map = GameMap(width=80, height=43)
        
        with patch.object(game_map, 'make_map'):
            entities = game_map.next_floor(self.player, self.message_log, self.constants)
            
            assert len(entities) == 1
            assert entities[0] == self.player

    def test_next_floor_reinitializes_tiles(self):
        """Test that next_floor creates fresh tiles."""
        game_map = GameMap(width=10, height=10)
        
        # Mark some tiles as explored
        game_map.tiles[5][5].explored = True
        game_map.tiles[3][3].blocked = False
        
        with patch.object(game_map, 'make_map'):
            game_map.next_floor(self.player, self.message_log, self.constants)
            
            # Tiles should be reinitialized (all blocked, none explored)
            assert game_map.tiles[5][5].explored is False
            assert game_map.tiles[3][3].blocked is True

    def test_next_floor_calls_make_map_with_correct_parameters(self):
        """Test that next_floor calls make_map with correct parameters."""
        game_map = GameMap(width=80, height=43)
        
        with patch.object(game_map, 'make_map') as mock_make_map:
            entities = game_map.next_floor(self.player, self.message_log, self.constants)
            
            mock_make_map.assert_called_once_with(
                self.constants['max_rooms'],
                self.constants['room_min_size'], 
                self.constants['room_max_size'],
                self.constants['map_width'],
                self.constants['map_height'],
                self.player,
                entities  # Should be [player] only
            )

    def test_next_floor_heals_player(self):
        """Test that next_floor heals player for half max HP."""
        game_map = GameMap(width=80, height=43)
        
        # Damage player
        self.player.fighter.hp = 10  # Down from 30 max HP
        
        with patch.object(game_map, 'make_map'):
            game_map.next_floor(self.player, self.message_log, self.constants)
            
            # Should heal by half of max HP: 10 + (30 // 2) = 25
            assert self.player.fighter.hp == 25

    def test_next_floor_healing_doesnt_exceed_max_hp(self):
        """Test that next_floor healing doesn't exceed max HP."""
        game_map = GameMap(width=80, height=43)
        
        # Player at high HP
        self.player.fighter.hp = 25  # 5 below max of 30
        
        with patch.object(game_map, 'make_map'):
            game_map.next_floor(self.player, self.message_log, self.constants)
            
            # Should heal to max HP, not exceed it
            assert self.player.fighter.hp == 30  # Max HP

    def test_next_floor_adds_rest_message(self):
        """Test that next_floor adds appropriate rest message."""
        game_map = GameMap(width=80, height=43)
        
        with patch.object(game_map, 'make_map'):
            game_map.next_floor(self.player, self.message_log, self.constants)
            
        # Should add a rest message
        assert len(self.message_log.messages) > 0
        rest_message = self.message_log.messages[-1]
        # The actual message is "You take a moment to rest, and recover your strength."
        # Check for key words that should be in this message
        message_text = rest_message.text.lower()
        assert 'strength' in message_text or 'rest' in message_text or 'recover' in message_text

    def test_next_floor_multiple_transitions(self):
        """Test multiple floor transitions."""
        game_map = GameMap(width=80, height=43, dungeon_level=1)
        
        with patch.object(game_map, 'make_map'):
            # First transition
            game_map.next_floor(self.player, self.message_log, self.constants)
            assert game_map.dungeon_level == 2
            
            # Second transition  
            game_map.next_floor(self.player, self.message_log, self.constants)
            assert game_map.dungeon_level == 3
            
            # Third transition
            game_map.next_floor(self.player, self.message_log, self.constants)
            assert game_map.dungeon_level == 4

    def test_next_floor_preserves_player_components(self):
        """Test that next_floor preserves all player components."""
        game_map = GameMap(width=80, height=43)
        
        # Set up player state
        original_level = self.player.level.current_level
        original_xp = self.player.level.current_xp
        original_max_hp = self.player.fighter.max_hp
        original_power = self.player.fighter.power
        original_defense = self.player.fighter.defense
        original_capacity = self.player.inventory.capacity
        
        with patch.object(game_map, 'make_map'):
            entities = game_map.next_floor(self.player, self.message_log, self.constants)
            
            returned_player = entities[0]
            
            # All components should be preserved
            assert returned_player.level.current_level == original_level
            assert returned_player.level.current_xp == original_xp
            assert returned_player.fighter.max_hp == original_max_hp
            assert returned_player.fighter.power == original_power
            assert returned_player.fighter.defense == original_defense
            assert returned_player.inventory.capacity == original_capacity

    def test_next_floor_with_injured_player(self):
        """Test next_floor behavior with heavily injured player."""
        game_map = GameMap(width=80, height=43)
        
        # Player at 1 HP
        self.player.fighter.hp = 1
        
        with patch.object(game_map, 'make_map'):
            game_map.next_floor(self.player, self.message_log, self.constants)
            
            # Should heal by half max HP: 1 + 15 = 16
            assert self.player.fighter.hp == 16

    def test_next_floor_with_full_hp_player(self):
        """Test next_floor behavior with player at full HP."""
        game_map = GameMap(width=80, height=43)
        
        # Player at full HP
        assert self.player.fighter.hp == self.player.fighter.max_hp
        
        with patch.object(game_map, 'make_map'):
            game_map.next_floor(self.player, self.message_log, self.constants)
            
            # Should stay at max HP
            assert self.player.fighter.hp == self.player.fighter.max_hp

    def test_next_floor_preserves_message_log_history(self):
        """Test that next_floor doesn't clear existing message log."""
        game_map = GameMap(width=80, height=43)
        
        # Add some messages to log
        from game_messages import Message
        import tcod as libtcod
        self.message_log.add_message(Message("Test message 1", libtcod.white))
        self.message_log.add_message(Message("Test message 2", libtcod.white))
        initial_message_count = len(self.message_log.messages)
        
        with patch.object(game_map, 'make_map'):
            game_map.next_floor(self.player, self.message_log, self.constants)
            
            # Should have initial messages plus rest message
            assert len(self.message_log.messages) > initial_message_count
            
            # Original messages should still be there
            assert "Test message 1" in [msg.text for msg in self.message_log.messages]
            assert "Test message 2" in [msg.text for msg in self.message_log.messages]


class TestDungeonLevelProgression:
    """Test dungeon level progression and difficulty scaling."""

    def test_dungeon_level_progression_is_persistent(self):
        """Test that dungeon level persists across operations."""
        game_map = GameMap(width=50, height=30, dungeon_level=1)
        
        # Manually increment (simulating game progression)
        game_map.dungeon_level = 5
        
        # Level should persist
        assert game_map.dungeon_level == 5
        
        # Even after tile operations
        game_map.tiles = game_map.initialize_tiles()
        assert game_map.dungeon_level == 5

    def test_dungeon_level_can_be_high_values(self):
        """Test dungeon levels can reach high values."""
        game_map = GameMap(width=80, height=43, dungeon_level=1)
        
        # Simulate many level transitions
        with patch.object(game_map, 'make_map'):
            # Create a realistic player mock with fighter component
            player = Mock()
            player.fighter = Mock()
            player.fighter.max_hp = 30
            player.fighter.heal = Mock()
            
            message_log = Mock()
            message_log.add_message = Mock()
            
            constants = {'max_rooms': 30, 'room_min_size': 6, 'room_max_size': 10,
                        'map_width': 80, 'map_height': 43, 'max_monsters_per_room': 3,
                        'max_items_per_room': 2}
            
            for _ in range(50):
                game_map.next_floor(player, message_log, constants)
            
            assert game_map.dungeon_level == 51

    def test_dungeon_level_tracking_accuracy(self):
        """Test that dungeon level tracking is accurate across multiple transitions."""
        game_map = GameMap(width=80, height=43, dungeon_level=3)
        
        expected_levels = [4, 5, 6, 7, 8]
        
        with patch.object(game_map, 'make_map'):
            # Create a realistic player mock
            player = Mock()
            player.fighter = Mock()
            player.fighter.max_hp = 30
            player.fighter.heal = Mock()
            
            message_log = Mock()
            message_log.add_message = Mock()
            
            constants = {'max_rooms': 30, 'room_min_size': 6, 'room_max_size': 10,
                        'map_width': 80, 'map_height': 43, 'max_monsters_per_room': 3,
                        'max_items_per_room': 2}
            
            for expected_level in expected_levels:
                game_map.next_floor(player, message_log, constants)
                assert game_map.dungeon_level == expected_level


class TestDungeonLevelIntegration:
    """Test integration between dungeon levels and other systems."""

    def test_dungeon_level_with_real_player_components(self):
        """Test dungeon levels work correctly with real player components."""
        # Create a realistic player setup
        fighter = Fighter(hp=25, defense=1, power=3, xp=0)
        inventory = Inventory(26)
        level_comp = Level(current_level=2, current_xp=50)
        
        player = Entity(
            5, 5, '@', (255, 255, 255), 'Player',
            blocks=True, render_order=RenderOrder.ACTOR,
            fighter=fighter, inventory=inventory, level=level_comp
        )
        
        # Damage player
        player.fighter.hp = 10
        
        game_map = GameMap(width=40, height=30, dungeon_level=1)
        message_log = MessageLog(10, 50, 5)
        constants = {
            'max_rooms': 15, 'room_min_size': 4, 'room_max_size': 8,
            'map_width': 40, 'map_height': 30, 'max_monsters_per_room': 2,
            'max_items_per_room': 1
        }
        
        with patch.object(game_map, 'make_map'):
            entities = game_map.next_floor(player, message_log, constants)
            
            # Verify everything worked correctly
            assert game_map.dungeon_level == 2
            assert len(entities) == 1
            assert entities[0] == player
            assert player.fighter.hp > 10  # Should be healed
            assert player.level.current_level == 2  # Level preserved
            assert player.level.current_xp == 50  # XP preserved

    def test_multiple_floor_transitions_with_state_preservation(self):
        """Test multiple floor transitions preserve complex player state."""
        # Set up player with progression
        fighter = Fighter(hp=50, defense=3, power=7, xp=0)
        inventory = Inventory(26)
        level_comp = Level(current_level=5, current_xp=150)
        
        player = Entity(
            15, 20, '@', (255, 255, 255), 'Player',
            blocks=True, render_order=RenderOrder.ACTOR,
            fighter=fighter, inventory=inventory, level=level_comp
        )
        
        game_map = GameMap(width=80, height=43, dungeon_level=3)
        message_log = MessageLog(10, 50, 5)
        constants = {
            'max_rooms': 30, 'room_min_size': 6, 'room_max_size': 10,
            'map_width': 80, 'map_height': 43, 'max_monsters_per_room': 3,
            'max_items_per_room': 2
        }
        
        with patch.object(game_map, 'make_map'):
            # Go through several floors
            for expected_floor in [4, 5, 6]:
                player.fighter.hp = player.fighter.max_hp - 20  # Simulate damage
                
                entities = game_map.next_floor(player, message_log, constants)
                
                # Verify state after each transition
                assert game_map.dungeon_level == expected_floor
                assert len(entities) == 1
                assert entities[0] == player
                assert entities[0].level.current_level == 5  # Character level preserved
                assert entities[0].level.current_xp == 150  # XP preserved
                assert entities[0].fighter.power == 7  # Stats preserved
                assert entities[0].fighter.hp > player.fighter.max_hp - 20  # Healed
