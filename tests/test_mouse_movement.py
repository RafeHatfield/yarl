"""Tests for mouse movement functionality.

This module tests the click-to-move pathfinding system, including:
- Basic pathfinding component functionality
- Mouse click handling for movement and combat
- Enemy detection during movement
- Movement interruption mechanics
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest

from components.player_pathfinding import PlayerPathfinding
from mouse_movement import handle_mouse_click, process_pathfinding_movement
from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from game_messages import Message
from render_functions import RenderOrder


class TestPlayerPathfinding(unittest.TestCase):
    """Test the PlayerPathfinding component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pathfinding = PlayerPathfinding()
        
        # Create mock player entity
        self.player = Mock(spec=Entity)
        self.player.x = 5
        self.player.y = 5
        self.player.distance_to = Mock(return_value=1.0)
        self.player.distance = Mock(return_value=3.0)
        self.player.move = Mock()
        self.player.blocks = True
        
        # Set up pathfinding component
        self.pathfinding.owner = self.player
        
        # Create mock game map
        self.game_map = Mock()
        self.game_map.width = 20
        self.game_map.height = 20
        self.game_map.is_blocked = Mock(return_value=False)
        
        # Create mock entities list
        self.entities = [self.player]
    
    def test_initialization(self):
        """Test pathfinding component initialization."""
        pathfinding = PlayerPathfinding()
        
        self.assertIsNone(pathfinding.owner)
        self.assertEqual(pathfinding.current_path, [])
        self.assertIsNone(pathfinding.destination)
        self.assertEqual(pathfinding.path_index, 0)
        self.assertFalse(pathfinding.is_moving)
        self.assertFalse(pathfinding.movement_interrupted)
        self.assertEqual(pathfinding.total_moves_planned, 0)
        self.assertEqual(pathfinding.total_moves_completed, 0)
        self.assertEqual(pathfinding.interruption_count, 0)
    
    def test_invalid_destination_bounds(self):
        """Test setting destination outside map bounds."""
        # Test negative coordinates
        result = self.pathfinding.set_destination(-1, 5, self.game_map, self.entities)
        self.assertFalse(result)
        
        # Test coordinates beyond map size
        result = self.pathfinding.set_destination(25, 5, self.game_map, self.entities)
        self.assertFalse(result)
        
        result = self.pathfinding.set_destination(5, 25, self.game_map, self.entities)
        self.assertFalse(result)
    
    def test_invalid_destination_blocked(self):
        """Test setting destination on blocked tile."""
        self.game_map.is_blocked.return_value = True
        
        result = self.pathfinding.set_destination(10, 10, self.game_map, self.entities)
        self.assertFalse(result)
        self.game_map.is_blocked.assert_called_with(10, 10)
    
    def test_destination_same_as_current(self):
        """Test setting destination to current position."""
        result = self.pathfinding.set_destination(5, 5, self.game_map, self.entities)
        self.assertFalse(result)
    
    @patch('components.player_pathfinding.tcod')
    @patch('components.player_pathfinding.libtcodpy')
    def test_successful_pathfinding(self, mock_libtcodpy, mock_tcod):
        """Test successful pathfinding setup."""
        # Mock tcod map creation
        mock_fov = Mock()
        mock_tcod.map.Map.return_value = mock_fov
        mock_fov.transparent = {}
        mock_fov.walkable = {}
        
        # Mock pathfinding
        mock_path = Mock()
        mock_libtcodpy.path_new_using_map.return_value = mock_path
        mock_libtcodpy.path_compute.return_value = None
        mock_libtcodpy.path_is_empty.return_value = False
        mock_libtcodpy.path_size.return_value = 3
        
        # Mock path walking
        mock_libtcodpy.path_walk.side_effect = [(6, 5), (7, 5), (8, 5), (None, None)]
        
        # Mock game map tiles
        mock_tiles = {}
        for x in range(20):
            mock_tiles[x] = {}
            for y in range(20):
                mock_tile = Mock()
                mock_tile.block_sight = False
                mock_tile.blocked = False
                mock_tiles[x][y] = mock_tile
        self.game_map.tiles = mock_tiles
        
        result = self.pathfinding.set_destination(8, 5, self.game_map, self.entities)
        
        self.assertTrue(result)
        self.assertTrue(self.pathfinding.is_moving)
        self.assertEqual(self.pathfinding.destination, (8, 5))
        self.assertEqual(self.pathfinding.current_path, [(6, 5), (7, 5), (8, 5)])
        self.assertEqual(self.pathfinding.total_moves_planned, 3)
        
        # Verify cleanup
        mock_libtcodpy.path_delete.assert_called_with(mock_path)
    
    def test_get_next_move(self):
        """Test getting next move from path."""
        # Set up a path manually
        self.pathfinding.current_path = [(6, 5), (7, 5), (8, 5)]
        self.pathfinding.is_moving = True
        self.pathfinding.path_index = 0
        
        # Get first move
        next_move = self.pathfinding.get_next_move()
        self.assertEqual(next_move, (6, 5))
        self.assertEqual(self.pathfinding.path_index, 1)
        self.assertEqual(self.pathfinding.total_moves_completed, 1)
        self.assertTrue(self.pathfinding.is_moving)
        
        # Get second move
        next_move = self.pathfinding.get_next_move()
        self.assertEqual(next_move, (7, 5))
        self.assertEqual(self.pathfinding.path_index, 2)
        
        # Get final move
        next_move = self.pathfinding.get_next_move()
        self.assertEqual(next_move, (8, 5))
        self.assertEqual(self.pathfinding.path_index, 0)  # Reset by _complete_movement()
        self.assertFalse(self.pathfinding.is_moving)  # Should complete movement
        
        # No more moves
        next_move = self.pathfinding.get_next_move()
        self.assertIsNone(next_move)
    
    def test_interrupt_movement(self):
        """Test movement interruption."""
        # Set up active movement
        self.pathfinding.current_path = [(6, 5), (7, 5), (8, 5)]
        self.pathfinding.is_moving = True
        
        self.pathfinding.interrupt_movement("Test interruption")
        
        self.assertFalse(self.pathfinding.is_moving)
        self.assertTrue(self.pathfinding.movement_interrupted)
        self.assertEqual(self.pathfinding.interruption_count, 1)
    
    def test_cancel_movement(self):
        """Test movement cancellation."""
        # Set up active movement
        self.pathfinding.current_path = [(6, 5), (7, 5), (8, 5)]
        self.pathfinding.is_moving = True
        self.pathfinding.destination = (8, 5)
        self.pathfinding.path_index = 1
        
        self.pathfinding.cancel_movement()
        
        self.assertFalse(self.pathfinding.is_moving)
        self.assertEqual(self.pathfinding.current_path, [])
        self.assertIsNone(self.pathfinding.destination)
        self.assertEqual(self.pathfinding.path_index, 0)
        self.assertFalse(self.pathfinding.movement_interrupted)
    
    def test_movement_stats(self):
        """Test movement statistics tracking."""
        # Set up movement
        self.pathfinding.current_path = [(6, 5), (7, 5)]
        self.pathfinding.is_moving = True
        self.pathfinding.destination = (7, 5)
        self.pathfinding.path_index = 1
        self.pathfinding.total_moves_planned = 2
        self.pathfinding.total_moves_completed = 1
        self.pathfinding.interruption_count = 0
        
        stats = self.pathfinding.get_movement_stats()
        
        expected_stats = {
            'is_moving': True,
            'current_path_length': 2,
            'path_index': 1,
            'remaining_steps': 1,
            'destination': (7, 5),
            'movement_interrupted': False,
            'total_moves_planned': 2,
            'total_moves_completed': 1,
            'interruption_count': 0,
        }
        
        self.assertEqual(stats, expected_stats)


class TestMouseMovementHandling(unittest.TestCase):
    """Test mouse click handling for movement and combat."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create player entity with pathfinding
        self.player = Entity(
            x=5, y=5, char='@', color=(255, 255, 255), name='Player',
            blocks=True, render_order=RenderOrder.ACTOR
        )
        self.player.pathfinding = PlayerPathfinding()
        self.player.pathfinding.owner = self.player
        
        # Create fighter component for combat tests
        self.player.fighter = Fighter(hp=100, defense=2, power=5)
        
        # Create enemy entity
        self.enemy = Entity(
            x=10, y=10, char='o', color=(255, 0, 0), name='Orc',
            blocks=True, render_order=RenderOrder.ACTOR
        )
        self.enemy.fighter = Fighter(hp=20, defense=1, power=3)
        
        # Create game map
        self.game_map = Mock()
        self.game_map.width = 20
        self.game_map.height = 20
        self.game_map.is_blocked = Mock(return_value=False)
        
        self.entities = [self.player, self.enemy]
    
    def test_invalid_click_coordinates(self):
        """Test handling invalid click coordinates."""
        # Test negative coordinates
        result = handle_mouse_click(-1, 5, self.player, self.entities, self.game_map)
        
        self.assertIn("results", result)
        results = result["results"]
        self.assertEqual(len(results), 1)
        self.assertIn("message", results[0])
        self.assertIn("cannot move there", results[0]["message"].text.lower())
        
        # Test coordinates beyond map bounds
        result = handle_mouse_click(25, 5, self.player, self.entities, self.game_map)
        results = result["results"]
        self.assertEqual(len(results), 1)
        self.assertIn("message", results[0])
    
    @patch('mouse_movement.get_blocking_entities_at_location')
    def test_click_on_empty_space_successful_pathfinding(self, mock_get_blocking):
        """Test clicking on empty space with successful pathfinding."""
        mock_get_blocking.return_value = None
        
        # Mock successful pathfinding
        self.player.pathfinding.set_destination = Mock(return_value=True)
        
        result = handle_mouse_click(10, 8, self.player, self.entities, self.game_map)
        
        self.assertIn("results", result)
        results = result["results"]
        
        # Should have success message and pathfinding start signal
        messages = [r for r in results if "message" in r]
        pathfinding_signals = [r for r in results if "start_pathfinding" in r]
        
        self.assertEqual(len(messages), 1)
        self.assertEqual(len(pathfinding_signals), 1)
        self.assertIn("moving to", messages[0]["message"].text.lower())
        self.assertTrue(pathfinding_signals[0]["start_pathfinding"])
        
        # Verify pathfinding was called correctly
        self.player.pathfinding.set_destination.assert_called_once_with(
            10, 8, self.game_map, self.entities
        )
    
    @patch('mouse_movement.get_blocking_entities_at_location')
    def test_click_on_empty_space_no_path(self, mock_get_blocking):
        """Test clicking on empty space when no path can be found."""
        mock_get_blocking.return_value = None
        
        # Mock failed pathfinding
        self.player.pathfinding.set_destination = Mock(return_value=False)
        
        result = handle_mouse_click(15, 15, self.player, self.entities, self.game_map)
        
        results = result["results"]
        messages = [r for r in results if "message" in r]
        
        self.assertEqual(len(messages), 1)
        self.assertIn("cannot reach", messages[0]["message"].text.lower())
    
    @patch('mouse_movement.get_blocking_entities_at_location')
    def test_click_on_adjacent_enemy(self, mock_get_blocking):
        """Test clicking on adjacent enemy for attack."""
        # Position enemy adjacent to player
        self.enemy.x = 6
        self.enemy.y = 5
        mock_get_blocking.return_value = self.enemy
        
        # Mock distance calculation
        self.player.distance_to = Mock(return_value=1.0)
        
        # Mock attack
        attack_results = [{"message": Message("You hit the Orc!", (255, 255, 255))}]
        self.player.fighter.attack = Mock(return_value=attack_results)
        
        result = handle_mouse_click(6, 5, self.player, self.entities, self.game_map)
        
        results = result["results"]
        
        # Should have attack message and enemy turn signal
        messages = [r for r in results if "message" in r]
        enemy_turn_signals = [r for r in results if "enemy_turn" in r]
        
        self.assertEqual(len(messages), 1)
        self.assertEqual(len(enemy_turn_signals), 1)
        self.assertTrue(enemy_turn_signals[0]["enemy_turn"])
        
        # Verify attack was called
        self.player.fighter.attack.assert_called_once_with(self.enemy)
    
    @patch('mouse_movement.get_blocking_entities_at_location')
    def test_click_on_distant_enemy(self, mock_get_blocking):
        """Test clicking on distant enemy (should pathfind toward enemy)."""
        mock_get_blocking.return_value = self.enemy
        
        # Mock distance calculation (enemy is far away)
        self.player.distance_to = Mock(return_value=5.0)
        
        result = handle_mouse_click(10, 10, self.player, self.entities, self.game_map)
        
        results = result["results"]
        messages = [r for r in results if "message" in r]
        pathfind_signals = [r for r in results if "pathfind_to_enemy" in r]
        
        self.assertEqual(len(messages), 1)
        self.assertIn("moving toward", messages[0]["message"].text.lower())
        self.assertEqual(len(pathfind_signals), 1)
        self.assertEqual(pathfind_signals[0]["pathfind_to_enemy"], (10, 10))
    
    def test_click_without_pathfinding_component(self):
        """Test clicking when player lacks pathfinding component."""
        # Remove pathfinding component
        del self.player.pathfinding
        
        result = handle_mouse_click(10, 8, self.player, self.entities, self.game_map)
        
        results = result["results"]
        messages = [r for r in results if "message" in r]
        
        self.assertEqual(len(messages), 1)
        self.assertIn("pathfinding not available", messages[0]["message"].text.lower())
    
    @patch('mouse_movement.get_blocking_entities_at_location')
    def test_pathfind_to_enemy_integration(self, mock_get_blocking):
        """Test that clicking distant enemy creates pathfind_to_enemy signal."""
        # Position enemy far from player
        self.enemy.x = 15
        self.enemy.y = 15
        mock_get_blocking.return_value = self.enemy
        
        # Mock distance calculation (enemy is far away)
        self.player.distance_to = Mock(return_value=10.0)
        
        result = handle_mouse_click(15, 15, self.player, self.entities, self.game_map)
        
        results = result["results"]
        pathfind_signals = [r for r in results if "pathfind_to_enemy" in r]
        messages = [r for r in results if "message" in r]
        
        # Should have pathfind signal and appropriate message
        self.assertEqual(len(pathfind_signals), 1)
        self.assertEqual(pathfind_signals[0]["pathfind_to_enemy"], (15, 15))
        self.assertEqual(len(messages), 1)
        self.assertIn("moving toward", messages[0]["message"].text.lower())


class TestPathfindingMovementProcessing(unittest.TestCase):
    """Test pathfinding movement processing during gameplay."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create player with pathfinding
        self.player = Entity(
            x=5, y=5, char='@', color=(255, 255, 255), name='Player',
            blocks=True, render_order=RenderOrder.ACTOR
        )
        self.player.pathfinding = PlayerPathfinding()
        self.player.pathfinding.owner = self.player
        self.player.move = Mock()
        
        # Create enemy
        self.enemy = Entity(
            x=10, y=10, char='o', color=(255, 0, 0), name='Orc',
            blocks=True, render_order=RenderOrder.ACTOR
        )
        self.enemy.fighter = Fighter(hp=20, defense=1, power=3)
        
        # Create game map
        self.game_map = Mock()
        self.game_map.width = 20
        self.game_map.height = 20
        self.game_map.is_blocked = Mock(return_value=False)
        
        # Create FOV map
        self.fov_map = Mock()
        
        self.entities = [self.player, self.enemy]
    
    def test_no_active_pathfinding(self):
        """Test processing when no pathfinding is active."""
        result = process_pathfinding_movement(
            self.player, self.entities, self.game_map, self.fov_map
        )
        
        self.assertEqual(result["results"], [])
    
    @patch('mouse_movement._check_for_enemies_in_fov')
    @patch('mouse_movement.get_blocking_entities_at_location')
    def test_enemy_spotted_interruption(self, mock_get_blocking, mock_check_enemies):
        """Test movement interruption when enemy is spotted AFTER moving."""
        # Set up active pathfinding
        self.player.pathfinding.current_path = [(6, 5), (7, 5)]
        self.player.pathfinding.is_moving = True
        self.player.pathfinding.path_index = 0
        
        # Mock no blocking entities but enemy detection after move
        mock_get_blocking.return_value = None
        mock_check_enemies.return_value = True
        
        result = process_pathfinding_movement(
            self.player, self.entities, self.game_map, self.fov_map
        )
        
        results = result["results"]
        messages = [r for r in results if "message" in r]
        fov_signals = [r for r in results if "fov_recompute" in r]
        
        # Should have moved first, then detected enemy
        self.assertEqual(len(messages), 1)
        self.assertIn("enemy spotted", messages[0]["message"].text.lower())
        self.assertEqual(len(fov_signals), 1)  # FOV recompute should happen
        
        # Verify player moved before detection
        self.player.move.assert_called_once_with(1, 0)  # (6,5) - (5,5) = (1,0)
        
        # Movement should be interrupted
        self.assertFalse(self.player.pathfinding.is_moving)
        self.assertTrue(self.player.pathfinding.movement_interrupted)
    
    @patch('mouse_movement._check_for_enemies_in_fov')
    @patch('mouse_movement.get_blocking_entities_at_location')
    def test_successful_movement_step(self, mock_get_blocking, mock_check_enemies):
        """Test successful movement step."""
        # Set up active pathfinding
        self.player.pathfinding.current_path = [(6, 5), (7, 5)]
        self.player.pathfinding.is_moving = True
        self.player.pathfinding.path_index = 0
        
        # Mock no enemies and no blocking entities
        mock_check_enemies.return_value = False
        mock_get_blocking.return_value = None
        
        result = process_pathfinding_movement(
            self.player, self.entities, self.game_map, self.fov_map
        )
        
        results = result["results"]
        
        # Should have FOV recompute and continue pathfinding signals
        fov_signals = [r for r in results if "fov_recompute" in r]
        continue_signals = [r for r in results if "continue_pathfinding" in r]
        
        self.assertEqual(len(fov_signals), 1)
        self.assertEqual(len(continue_signals), 1)
        self.assertTrue(fov_signals[0]["fov_recompute"])
        self.assertTrue(continue_signals[0]["continue_pathfinding"])
        
        # Verify player moved
        self.player.move.assert_called_once_with(1, 0)  # (6,5) - (5,5) = (1,0)
    
    @patch('mouse_movement._check_for_enemies_in_fov')
    @patch('mouse_movement.get_blocking_entities_at_location')
    def test_path_blocked_by_entity(self, mock_get_blocking, mock_check_enemies):
        """Test movement interruption when path is blocked by entity."""
        # Set up active pathfinding
        self.player.pathfinding.current_path = [(6, 5)]
        self.player.pathfinding.is_moving = True
        self.player.pathfinding.path_index = 0
        
        # Mock no enemies but blocking entity
        mock_check_enemies.return_value = False
        blocking_entity = Mock()
        blocking_entity.name = "Wall"
        mock_get_blocking.return_value = blocking_entity
        
        result = process_pathfinding_movement(
            self.player, self.entities, self.game_map, self.fov_map
        )
        
        results = result["results"]
        messages = [r for r in results if "message" in r]
        
        self.assertEqual(len(messages), 1)
        self.assertIn("blocked by wall", messages[0]["message"].text.lower())
        self.assertFalse(self.player.pathfinding.is_moving)
    
    @patch('mouse_movement._check_for_enemies_in_fov')
    def test_path_blocked_by_terrain(self, mock_check_enemies):
        """Test movement interruption when path is blocked by terrain."""
        # Set up active pathfinding
        self.player.pathfinding.current_path = [(6, 5)]
        self.player.pathfinding.is_moving = True
        self.player.pathfinding.path_index = 0
        
        # Mock no enemies but blocked terrain
        mock_check_enemies.return_value = False
        self.game_map.is_blocked.return_value = True
        
        result = process_pathfinding_movement(
            self.player, self.entities, self.game_map, self.fov_map
        )
        
        results = result["results"]
        messages = [r for r in results if "message" in r]
        
        self.assertEqual(len(messages), 1)
        self.assertIn("path blocked", messages[0]["message"].text.lower())
        self.assertFalse(self.player.pathfinding.is_moving)
    
    @patch('mouse_movement._check_for_enemies_in_fov')
    @patch('mouse_movement.get_blocking_entities_at_location')
    def test_movement_completion(self, mock_get_blocking, mock_check_enemies):
        """Test movement completion."""
        # Set up pathfinding with final step
        self.player.pathfinding.current_path = [(6, 5)]
        self.player.pathfinding.is_moving = True
        self.player.pathfinding.path_index = 0
        
        # Mock no enemies and no blocking entities
        mock_check_enemies.return_value = False
        mock_get_blocking.return_value = None
        
        result = process_pathfinding_movement(
            self.player, self.entities, self.game_map, self.fov_map
        )
        
        results = result["results"]
        messages = [r for r in results if "message" in r]
        
        # Should have completion message
        completion_messages = [m for m in messages 
                             if "arrived" in m["message"].text.lower()]
        self.assertEqual(len(completion_messages), 1)
        
        # Pathfinding should be completed
        self.assertFalse(self.player.pathfinding.is_moving)


if __name__ == '__main__':
    unittest.main()
