"""Comprehensive tests for stairs and level progression functionality."""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from engine_integration import _process_game_actions
from engine.game_state_manager import GameStateManager
from game_states import GameStates
from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from stairs import Stairs
from map_objects.game_map import GameMap


class TestStairsFunctionality(unittest.TestCase):
    """Test stairs and level progression."""

    def setUp(self):
        """Set up stairs testing scenario."""
        self.state_manager = GameStateManager()
        
        # Create player
        self.player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=25, defense=2, power=5),  # Slightly damaged
            inventory=Inventory(capacity=26)
        )
        
        # Create stairs
        self.stairs = Entity(
            x=10, y=10, char='>', color=(255, 255, 255), name='Stairs',
            stairs=Stairs(floor=2)
        )
        
        # Create game map
        self.game_map = GameMap(width=80, height=50, dungeon_level=1)
        
        # Create message log
        self.message_log = Mock()
        
        # Set up game state
        self.state_manager.update_state(
            player=self.player,
            entities=[self.player, self.stairs],
            game_map=self.game_map,
            message_log=self.message_log,
            current_state=GameStates.PLAYERS_TURN,
        )
        
        # Use actual constants from the new system
        from config.game_constants import get_constants
        self.constants = get_constants()

    def test_stairs_level_progression(self):
        """Test that taking stairs generates new level."""
        action = {"take_stairs": True}
        
        original_level = self.game_map.dungeon_level
        original_hp = self.player.fighter.hp
        
        # Mock the next_floor method to track if it's called
        with patch.object(self.game_map, 'next_floor') as mock_next_floor:
            mock_next_floor.return_value = [self.player]  # Return player as only entity
            
            _process_game_actions(
                action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, self.constants
            )
            
            # Verify next_floor was called
            mock_next_floor.assert_called_once_with(
                self.player, self.message_log, self.constants
            )

    def test_stairs_not_present(self):
        """Test taking stairs when not on stairs."""
        # Move stairs away from player
        self.stairs.x = 20
        self.stairs.y = 20
        
        action = {"take_stairs": True}
        
        _process_game_actions(
            action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, self.constants
        )
        
        # Verify "no stairs" message was added
        self.message_log.add_message.assert_called()
        call_args = self.message_log.add_message.call_args[0][0]
        self.assertIn("no stairs", call_args.text.lower())

    def test_stairs_fov_update(self):
        """Test that FOV is updated when taking stairs."""
        action = {"take_stairs": True}
        
        with patch.object(self.game_map, 'next_floor') as mock_next_floor:
            mock_next_floor.return_value = [self.player]
            
            with patch('fov_functions.initialize_fov') as mock_init_fov:
                mock_fov_map = Mock()
                mock_init_fov.return_value = mock_fov_map
                
                
                _process_game_actions(
                    action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, self.constants
                )
                
                # Verify FOV was reinitialized
                mock_init_fov.assert_called_once_with(self.game_map)
                
                # Verify FOV map was updated in state
                self.assertEqual(self.state_manager.state.fov_map, mock_fov_map)
                
                # Verify FOV recompute was requested
                self.assertTrue(self.state_manager.state.fov_recompute)

    def test_stairs_entity_update(self):
        """Test that entities are updated when taking stairs."""
        action = {"take_stairs": True}
        
        # Mock new entities from next floor
        new_monster = Entity(x=15, y=15, char='T', color=(255, 0, 0), name='Troll')
        new_entities = [self.player, new_monster]
        
        with patch.object(self.game_map, 'next_floor') as mock_next_floor:
            mock_next_floor.return_value = new_entities
            
            _process_game_actions(
                action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, self.constants
            )
            
            # Verify entities were updated
            self.assertEqual(self.state_manager.state.entities, new_entities)
            self.assertIn(new_monster, self.state_manager.state.entities)
            self.assertNotIn(self.stairs, self.state_manager.state.entities)  # Old stairs gone


class TestStairsIntegration(unittest.TestCase):
    """Integration tests for stairs with other systems."""

    def test_stairs_with_real_game_map(self):
        """Test stairs functionality with actual GameMap."""
        # Use new default map size (Phase 3: 120x80)
        map_width, map_height = 120, 80
        
        # Create real game map
        game_map = GameMap(width=map_width, height=map_height, dungeon_level=1)
        
        # Create player
        player = Entity(
            x=60, y=40, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=20, defense=2, power=5),
            inventory=Inventory(capacity=26)
        )
        
        # Generate initial map
        entities = [player]
        constants = {
            "max_rooms": 10,
            "room_min_size": 6,
            "room_max_size": 10,
            "map_width": map_width,
            "map_height": map_height,
        }
        
        game_map.make_map(
            constants["max_rooms"],
            constants["room_min_size"],
            constants["room_max_size"],
            constants["map_width"],
            constants["map_height"],
            player,
            entities,
        )
        
        # Find stairs (should be created by make_map)
        stairs = None
        for entity in entities:
            if hasattr(entity, 'stairs') and entity.stairs:
                stairs = entity
                break
        
        self.assertIsNotNone(stairs, "Map generation should create stairs")
        
        # Move player to stairs and damage them to test healing
        player.x = stairs.x
        player.y = stairs.y
        player.fighter.hp = 10  # Damage player to test healing
        
        # Set up state manager
        state_manager = GameStateManager()
        message_log = Mock()
        
        state_manager.update_state(
            player=player,
            entities=entities,
            game_map=game_map,
            message_log=message_log,
            current_state=GameStates.PLAYERS_TURN,
        )
        
        # Test taking stairs
        action = {"take_stairs": True}
        original_level = game_map.dungeon_level
        
        _process_game_actions(
            action, {}, state_manager, None, GameStates.PLAYERS_TURN, constants
        )
        
        # Verify level increased
        self.assertEqual(game_map.dungeon_level, original_level + 1,
                        "Dungeon level should increase")
        
        # Verify player was healed (10 + max_hp//2 = 10 + 10 = 20)
        self.assertEqual(player.fighter.hp, 20, "Player should be healed on new level")
        
        # Verify new entities were created
        new_entities = state_manager.state.entities
        self.assertGreater(len(new_entities), 1, "New level should have entities")
        self.assertIn(player, new_entities, "Player should be in new entities")


if __name__ == "__main__":
    unittest.main(verbosity=2)
