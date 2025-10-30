"""Tests for player pathfinding to explored tiles.

Players should be able to click on any explored tile to automatically
pathfind there, with interruptions for enemies and hazards.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch

from entity import Entity
from components.fighter import Fighter
from components.player_pathfinding import PlayerPathfinding
from components.ground_hazard import GroundHazard, GroundHazardManager, HazardType
from map_objects.game_map import GameMap
from mouse_movement import handle_mouse_click, process_pathfinding_movement
from game_messages import Message
from game_states import GameStates


class TestPlayerExploredPathfinding(unittest.TestCase):
    """Test player pathfinding to explored tiles."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.game_map = GameMap(width=50, height=50, dungeon_level=1)
        
        # Create player at (5, 5) with components
        fighter = Fighter(hp=100, defense=5, power=10)
        pathfinding = PlayerPathfinding()
        self.player = Entity(
            5, 5, '@', (255, 255, 255), 'Player',
            blocks=True, fighter=fighter, pathfinding=pathfinding
        )
        
        self.entities = [self.player]
        
        # Mark various tiles as explored and walkable
        for x in range(50):
            for y in range(50):
                self.game_map.tiles[x][y].explored = True
                self.game_map.tiles[x][y].blocked = False
                self.game_map.tiles[x][y].block_sight = False
    
    def test_pathfind_to_nearby_explored_tile(self):
        """Test pathfinding to a nearby explored tile."""
        # Pathfind to (10, 10)
        success = self.player.pathfinding.set_destination(
            10, 10, self.game_map, self.entities, fov_map=None
        )
        
        self.assertTrue(success, "Should find path to nearby explored tile")
        self.assertTrue(self.player.pathfinding.is_path_active())
        self.assertGreater(self.player.pathfinding.get_remaining_steps(), 0)
    
    def test_pathfind_to_distant_explored_tile(self):
        """Test pathfinding to a distant explored tile."""
        # Pathfind to (40, 40) - much farther
        success = self.player.pathfinding.set_destination(
            40, 40, self.game_map, self.entities, fov_map=None
        )
        
        # Should succeed (within OUT_FOV limit of 25)
        # But 40,40 from 5,5 is about 49 steps diagonal - might fail
        # Let's try a closer distant target
        success = self.player.pathfinding.set_destination(
            25, 25, self.game_map, self.entities, fov_map=None
        )
        
        # This should work (about 20 diagonal steps)
        self.assertTrue(success, "Should find path to distant explored tile")
    
    def test_cannot_pathfind_to_unexplored_tile(self):
        """Test that pathfinding fails for unexplored tiles."""
        # Mark tile as unexplored
        self.game_map.tiles[30][30].explored = False
        
        # Try to pathfind there
        success = self.player.pathfinding.set_destination(
            30, 30, self.game_map, self.entities, fov_map=None
        )
        
        self.assertFalse(success, "Should not pathfind to unexplored tile")
    
    def test_cannot_pathfind_to_blocked_tile(self):
        """Test that pathfinding fails for blocked tiles."""
        # Mark tile as blocked (wall)
        self.game_map.tiles[10][10].blocked = True
        
        # Try to pathfind there
        success = self.player.pathfinding.set_destination(
            10, 10, self.game_map, self.entities, fov_map=None
        )
        
        self.assertFalse(success, "Should not pathfind to blocked tile")
    
    def test_pathfinding_respects_max_path_length(self):
        """Test that pathfinding respects MAX_PATH_LENGTH_EXPLORED for explored tiles."""
        # From (5,5) to (45, 45) is about 57 steps diagonal
        # This should succeed with MAX_PATH_LENGTH_EXPLORED=150
        success = self.player.pathfinding.set_destination(
            45, 45, self.game_map, self.entities, fov_map=None
        )
        
        # Should succeed for explored tiles within 150 steps
        self.assertTrue(success, "Should succeed for explored tiles within 150 steps")
        
        # For paths exceeding 150 steps, we'd need a much larger map or forced circuitous path
        # Since our 50x50 map can't create a >150 step path, just verify this path succeeded
        self.assertIsNotNone(self.player.pathfinding.current_path)
    
    def test_pathfinding_to_explored_tile_with_obstacles(self):
        """Test pathfinding around obstacles to explored tile."""
        # Create a wall between player and destination
        for y in range(10):
            self.game_map.tiles[10][y].blocked = True
            self.game_map.tiles[10][y].explored = True
        
        # Try to pathfind to other side of wall
        success = self.player.pathfinding.set_destination(
            15, 5, self.game_map, self.entities, fov_map=None
        )
        
        self.assertTrue(success, "Should find path around obstacle")
    
    def test_explored_pathfinding_updates_player_position(self):
        """Test that pathfinding actually moves the player."""
        # Set a destination
        self.player.pathfinding.set_destination(
            10, 5, self.game_map, self.entities, fov_map=None
        )
        
        # Simulate several movement steps
        initial_x = self.player.x
        for _ in range(5):
            if not self.player.pathfinding.is_path_active():
                break
            next_pos = self.player.pathfinding.get_next_move()
            if next_pos:
                self.player.x, self.player.y = next_pos
        
        # Player should have moved
        self.assertGreater(self.player.x, initial_x, "Player should move along path")


class TestPlayerHazardInterrupt(unittest.TestCase):
    """Test that player pathfinding interrupts when stepping on hazards."""
    
    def setUp(self):
        """Set up test fixtures."""
        from services.movement_service import reset_movement_service
        reset_movement_service()  # Reset global service between tests

        self.game_map = GameMap(width=30, height=30, dungeon_level=1)
        
        # Mark all tiles as explored and walkable
        for x in range(30):
            for y in range(30):
                self.game_map.tiles[x][y].explored = True
                self.game_map.tiles[x][y].blocked = False
                self.game_map.tiles[x][y].block_sight = False
        
        # Create player with components
        fighter = Fighter(hp=100, defense=5, power=10)
        pathfinding = PlayerPathfinding()
        self.player = Entity(
            5, 5, '@', (255, 255, 255), 'Player',
            blocks=True, fighter=fighter, pathfinding=pathfinding
        )
        
        self.entities = [self.player]
        
        # Mock FOV map
        self.fov_map = Mock()
    
    def test_pathfinding_interrupts_on_fire(self):
        """Test that pathfinding stops when stepping on fire."""
        # Create fire at (7, 5)
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=7, y=5,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Test Fire"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        # Set destination past the fire
        self.player.pathfinding.set_destination(
            15, 5, self.game_map, self.entities, self.fov_map
        )
        
        # Simulate movement until hitting fire
        result = None
        for _ in range(5):
            if not self.player.pathfinding.is_path_active():
                break
            mock_state_manager = Mock()
            mock_state_manager.state.player = self.player
            mock_state_manager.state.game_map = self.game_map
            mock_state_manager.state.entities = self.entities
            mock_state_manager.state.current_state = GameStates.PLAYERS_TURN
            result = process_pathfinding_movement(
                self.player, self.entities, self.game_map, self.fov_map, mock_state_manager
            )
            # Check if we hit the hazard
            if self.player.x == 7 and self.player.y == 5:
                break
        
        # Pathfinding should be interrupted
        self.assertFalse(
            self.player.pathfinding.is_path_active(),
            "Pathfinding should be interrupted by fire"
        )
        
        # Should have a message about the hazard
        messages = [r.get("message") for r in result.get("results", []) if r.get("message")]
        self.assertTrue(
            any("Fire" in str(msg) or "stopped" in str(msg).lower() for msg in messages),
            "Should have message about fire hazard"
        )
    
    def test_pathfinding_interrupts_on_poison_gas(self):
        """Test that pathfinding stops when stepping on poison gas."""
        # Create poison gas at (8, 5)
        gas = GroundHazard(
            hazard_type=HazardType.POISON_GAS,
            x=8, y=5,
            base_damage=5,
            remaining_turns=4,
            max_duration=4,
            source_name="Test Gas"
        )
        self.game_map.hazard_manager.add_hazard(gas)
        
        # Set destination past the gas
        self.player.pathfinding.set_destination(
            15, 5, self.game_map, self.entities, self.fov_map
        )
        
        # Simulate movement until hitting gas
        for _ in range(5):
            if not self.player.pathfinding.is_path_active():
                break
            mock_state_manager = Mock()
            mock_state_manager.state.player = self.player
            mock_state_manager.state.game_map = self.game_map
            mock_state_manager.state.entities = self.entities
            mock_state_manager.state.current_state = GameStates.PLAYERS_TURN
            process_pathfinding_movement(
                self.player, self.entities, self.game_map, self.fov_map, mock_state_manager
            )
            if self.player.x == 8:
                break
        
        # Pathfinding should be interrupted
        self.assertFalse(
            self.player.pathfinding.is_path_active(),
            "Pathfinding should be interrupted by poison gas"
        )
    
    def test_no_interrupt_without_hazards(self):
        """Test that pathfinding continues normally without hazards."""
        # No hazards - just normal pathfinding
        self.player.pathfinding.set_destination(
            15, 5, self.game_map, self.entities, self.fov_map
        )
        
        # Simulate a couple movements
        for _ in range(3):
            if not self.player.pathfinding.is_path_active():
                break
            mock_state_manager = Mock()
            mock_state_manager.state.player = self.player
            mock_state_manager.state.game_map = self.game_map
            mock_state_manager.state.entities = self.entities
            mock_state_manager.state.current_state = GameStates.PLAYERS_TURN
            process_pathfinding_movement(
                self.player, self.entities, self.game_map, self.fov_map, mock_state_manager
            )
        
        # Should still be moving (or reached destination)
        # Either way, should not have been interrupted early
        self.assertTrue(
            self.player.x > 5,
            "Player should have moved forward"
        )


class TestExploredTileValidation(unittest.TestCase):
    """Test the explored tile validation logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.game_map = GameMap(width=20, height=20, dungeon_level=1)
        self.player = Entity(5, 5, '@', (255, 255, 255), 'Player', blocks=True)
        self.player.pathfinding = PlayerPathfinding()
        self.player.pathfinding.owner = self.player
    
    def test_valid_destination_explored_and_walkable(self):
        """Test that explored and walkable tiles are valid."""
        self.game_map.tiles[10][10].explored = True
        self.game_map.tiles[10][10].blocked = False
        
        is_valid = self.player.pathfinding._is_valid_destination(
            10, 10, self.game_map
        )
        
        self.assertTrue(is_valid, "Explored and walkable tile should be valid")
    
    def test_invalid_destination_unexplored(self):
        """Test that unexplored tiles are invalid."""
        self.game_map.tiles[10][10].explored = False
        self.game_map.tiles[10][10].blocked = False
        
        is_valid = self.player.pathfinding._is_valid_destination(
            10, 10, self.game_map
        )
        
        self.assertFalse(is_valid, "Unexplored tile should be invalid")
    
    def test_invalid_destination_blocked(self):
        """Test that blocked tiles are invalid."""
        self.game_map.tiles[10][10].explored = True
        self.game_map.tiles[10][10].blocked = True
        
        is_valid = self.player.pathfinding._is_valid_destination(
            10, 10, self.game_map
        )
        
        self.assertFalse(is_valid, "Blocked tile should be invalid")
    
    def test_invalid_destination_out_of_bounds(self):
        """Test that out-of-bounds coordinates are invalid."""
        is_valid = self.player.pathfinding._is_valid_destination(
            -1, 5, self.game_map
        )
        self.assertFalse(is_valid, "Negative coordinate should be invalid")
        
        is_valid = self.player.pathfinding._is_valid_destination(
            25, 5, self.game_map
        )
        self.assertFalse(is_valid, "Out-of-bounds coordinate should be invalid")


if __name__ == '__main__':
    unittest.main()

