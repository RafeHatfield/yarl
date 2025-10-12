"""Test turn transitions during pathfinding movement.

This test suite ensures that enemy turns are properly triggered during
player pathfinding movement, including when movement is interrupted.
"""


# QUARANTINED: Pathfinding mocking needs refactor
# See QUARANTINED_TESTS.md for details.

import pytest

# Quarantine entire file
pytestmark = pytest.mark.skip(reason="Quarantined - Pathfinding mocking needs refactor. See QUARANTINED_TESTS.md")

import unittest
from unittest.mock import Mock, MagicMock, patch
from components.player_pathfinding import PlayerPathfinding
from components.fighter import Fighter
from entity import Entity
from game_messages import Message
import mouse_movement


class TestPathfindingTurnTransitions(unittest.TestCase):
    """Test that enemies get turns during pathfinding."""
    
    def setUp(self):
        """Set up test entities and map."""
        from components.component_registry import ComponentType
        
        # Create mock player with pathfinding
        self.player = Mock(spec=Entity)
        self.player.x = 5
        self.player.y = 5
        self.player.name = "Player"
        self.player.blocks = True
        self.player.fighter = Mock(spec=Fighter)
        self.player.equipment = Mock()
        self.player.equipment.get_equipped_in_slot.return_value = None
        
        # Create pathfinding component
        self.pathfinding = PlayerPathfinding()
        self.pathfinding.owner = self.player
        self.player.pathfinding = self.pathfinding
        
        # Mock ComponentRegistry to return pathfinding
        self.player.components = Mock()
        self.player.components.get = Mock(side_effect=lambda comp_type: 
            self.pathfinding if comp_type == ComponentType.PATHFINDING else None)
        
        # Set up a simple 3-step path
        self.pathfinding.current_path = [(6, 5), (7, 5), (8, 5)]
        self.pathfinding.path_index = 0
        self.pathfinding.is_moving = True
        self.pathfinding.destination = (8, 5)
        
        # Create mock game map
        self.game_map = Mock()
        self.game_map.width = 20
        self.game_map.height = 20
        self.game_map.is_blocked = Mock(return_value=False)
        self.game_map.hazard_manager = None
        
        # Create mock tiles
        mock_tile = Mock()
        mock_tile.explored = True
        mock_tile.blocked = False
        self.game_map.tiles = [[mock_tile for _ in range(20)] for _ in range(20)]
        
        # Create mock entities list
        self.entities = []
        
        # Create mock FOV
        self.fov_map = Mock()
        
        # Mock player move
        self.player.move = Mock()
    
    @patch('mouse_movement._check_for_close_enemies')
    @patch('mouse_movement._check_for_enemy_in_weapon_range')
    def test_normal_pathfinding_triggers_enemy_turn(self, mock_check_range, mock_check_close):
        """Test that normal pathfinding step triggers enemy turn."""
        # No enemies in range or close
        mock_check_range.return_value = None
        mock_check_close.return_value = False
        
        result = mouse_movement.process_pathfinding_movement(
            self.player, self.entities, self.game_map, self.fov_map
        )
        
        # Player should have moved
        self.player.move.assert_called_once()
        
        # Should request FOV recompute
        results = result.get("results", [])
        fov_recompute = any(r.get("fov_recompute") for r in results)
        self.assertTrue(fov_recompute, "Should request FOV recompute")
        
        # Should continue pathfinding (which triggers enemy turn)
        continue_pathfinding = any(r.get("continue_pathfinding") for r in results)
        self.assertTrue(continue_pathfinding, "Should have continue_pathfinding flag")
    
    @patch('mouse_movement._check_for_enemy_in_weapon_range')
    @patch('mouse_movement._get_weapon_reach')
    @patch('mouse_movement._check_for_close_enemies')
    def test_enemy_spotted_triggers_enemy_turn(self, mock_check_enemies, mock_weapon_reach, mock_weapon_range):
        """Test that spotting an enemy during pathfinding still gives enemies their turn."""
        # Enemy is spotted
        mock_check_enemies.return_value = True
        mock_weapon_reach.return_value = 1
        mock_weapon_range.return_value = None  # No enemy in weapon range
        
        result = mouse_movement.process_pathfinding_movement(
            self.player, self.entities, self.game_map, self.fov_map
        )
        
        # Player should have moved before enemy was spotted
        self.player.move.assert_called_once()
        
        # Movement should be interrupted
        self.assertFalse(self.pathfinding.is_path_active())
        
        # Should have enemy_turn flag
        results = result.get("results", [])
        enemy_turn = any(r.get("enemy_turn") for r in results)
        self.assertTrue(enemy_turn, "Should have enemy_turn flag when enemy spotted")
        
        # Should have message
        messages = [r.get("message") for r in results if r.get("message")]
        self.assertTrue(any("enemy spotted" in str(m).lower() for m in messages))
    
    @patch('mouse_movement._check_for_enemy_in_weapon_range')
    def test_hazard_interrupt_triggers_enemy_turn(self, mock_check_range):
        """Test that stepping on hazard still gives enemies their turn."""
        # No enemies in weapon range
        mock_check_range.return_value = None
        
        # Add a hazard at player's destination
        mock_hazard = Mock()
        mock_hazard.hazard_type = Mock()
        mock_hazard.hazard_type.name = "FIRE"
        
        mock_hazard_manager = Mock()
        mock_hazard_manager.get_hazard_at = Mock(return_value=mock_hazard)
        self.game_map.hazard_manager = mock_hazard_manager
        
        result = mouse_movement.process_pathfinding_movement(
            self.player, self.entities, self.game_map, self.fov_map
        )
        
        # Player should have moved first
        self.player.move.assert_called_once()
        
        # Movement should be interrupted
        self.assertFalse(self.pathfinding.is_path_active())
        
        # Should have enemy_turn flag
        results = result.get("results", [])
        enemy_turn = any(r.get("enemy_turn") for r in results)
        self.assertTrue(enemy_turn, "Should have enemy_turn flag when stepping on hazard")
        
        # Should have message about hazard
        messages = [r.get("message") for r in results if r.get("message")]
        self.assertTrue(any("fire" in str(m).lower() for m in messages))
    
    def test_blocked_path_no_enemy_turn(self):
        """Test that blocked path (before movement) doesn't trigger enemy turn."""
        # Block the next tile
        self.game_map.is_blocked = Mock(return_value=True)
        
        result = mouse_movement.process_pathfinding_movement(
            self.player, self.entities, self.game_map, self.fov_map
        )
        
        # Player should NOT have moved
        self.player.move.assert_not_called()
        
        # Movement should be interrupted
        self.assertFalse(self.pathfinding.is_path_active())
        
        # Should NOT have enemy_turn or continue_pathfinding flags
        results = result.get("results", [])
        enemy_turn = any(r.get("enemy_turn") for r in results)
        continue_pathfinding = any(r.get("continue_pathfinding") for r in results)
        self.assertFalse(enemy_turn, "Should NOT have enemy_turn when blocked before moving")
        self.assertFalse(continue_pathfinding, "Should NOT continue pathfinding when blocked")
    
    @unittest.skip("Auto-attack disabled per user requirement: Player should never attack unless clicking on target")
    @patch('mouse_movement._check_for_close_enemies')
    @patch('mouse_movement._check_for_enemy_in_weapon_range')
    def test_ranged_attack_triggers_enemy_turn(self, mock_check_range, mock_check_close):
        """Test that ranged auto-attack during pathfinding triggers enemy turn."""
        # Create a mock enemy in range
        mock_enemy = Mock(spec=Entity)
        mock_enemy.name = "Orc"
        mock_check_range.return_value = mock_enemy
        mock_check_close.return_value = False  # No close enemies (in weapon range for auto-attack)
        
        # Mock the attack
        self.player.fighter.attack_d20 = Mock(return_value=[
            {"message": Message("You hit the Orc!", (255, 255, 255))}
        ])
        
        result = mouse_movement.process_pathfinding_movement(
            self.player, self.entities, self.game_map, self.fov_map
        )
        
        # Player should have moved
        self.player.move.assert_called_once()
        
        # Attack should have been triggered
        self.player.fighter.attack_d20.assert_called_once_with(mock_enemy)
        
        # Movement should be interrupted
        self.assertFalse(self.pathfinding.is_path_active())
        
        # Should have enemy_turn flag
        results = result.get("results", [])
        enemy_turn = any(r.get("enemy_turn") for r in results)
        self.assertTrue(enemy_turn, "Should have enemy_turn flag after ranged attack")


class TestActionProcessorPathfindingTurns(unittest.TestCase):
    """Test that ActionProcessor correctly transitions states during pathfinding."""
    
    @patch('mouse_movement.process_pathfinding_movement')
    def test_continue_pathfinding_transitions_to_enemy_turn(self, mock_process):
        """Test that continue_pathfinding flag transitions to ENEMY_TURN."""
        from game_actions import ActionProcessor
        from state_machine.game_states import GameStates
        
        # Mock the movement result
        mock_process.return_value = {
            "results": [
                {"fov_recompute": True},
                {"continue_pathfinding": True}
            ]
        }
        
        # Create mock state manager
        mock_state_manager = Mock()
        mock_state = Mock()
        mock_state.player = Mock()
        mock_state.player.pathfinding = Mock()
        mock_state.player.pathfinding.is_path_active.return_value = True
        mock_state.entities = []
        mock_state.game_map = Mock()
        mock_state.message_log = Mock()
        mock_state.fov_map = Mock()
        mock_state.camera = None
        mock_state_manager.state = mock_state
        
        # Create action processor
        processor = ActionProcessor(mock_state_manager)
        
        # Process pathfinding turn
        processor.process_pathfinding_turn()
        
        # Should transition to ENEMY_TURN
        mock_state_manager.set_game_state.assert_called_once_with(GameStates.ENEMY_TURN)
    
    @patch('mouse_movement.process_pathfinding_movement')
    def test_enemy_turn_flag_transitions_to_enemy_turn(self, mock_process):
        """Test that enemy_turn flag (from interrupts) transitions to ENEMY_TURN."""
        from game_actions import ActionProcessor
        from state_machine.game_states import GameStates
        
        # Mock the movement result (interrupted by enemy)
        mock_process.return_value = {
            "results": [
                {"fov_recompute": True},
                {"message": Mock()},
                {"enemy_turn": True}
            ]
        }
        
        # Create mock state manager
        mock_state_manager = Mock()
        mock_state = Mock()
        mock_state.player = Mock()
        mock_state.player.pathfinding = Mock()
        mock_state.player.pathfinding.is_path_active.return_value = True  # Still active initially
        mock_state.entities = []
        mock_state.game_map = Mock()
        mock_state.message_log = Mock()
        mock_state.fov_map = Mock()
        mock_state.camera = None
        mock_state_manager.state = mock_state
        
        # Create action processor
        processor = ActionProcessor(mock_state_manager)
        
        # Process pathfinding turn
        processor.process_pathfinding_turn()
        
        # Should transition to ENEMY_TURN even though pathfinding stopped
        mock_state_manager.set_game_state.assert_called_once_with(GameStates.ENEMY_TURN)
    
    @patch('mouse_movement.process_pathfinding_movement')
    def test_blocked_path_stays_in_player_turn(self, mock_process):
        """Test that path blocked (no movement) stays in PLAYERS_TURN."""
        from game_actions import ActionProcessor
        from state_machine.game_states import GameStates
        
        # Mock the movement result (blocked before moving)
        mock_process.return_value = {
            "results": [
                {"message": Mock()}
                # No enemy_turn or continue_pathfinding flags
            ]
        }
        
        # Create mock state manager
        mock_state_manager = Mock()
        mock_state = Mock()
        mock_state.player = Mock()
        mock_state.player.pathfinding = Mock()
        mock_state.player.pathfinding.is_path_active.return_value = True  # Active initially
        mock_state.entities = []
        mock_state.game_map = Mock()
        mock_state.message_log = Mock()
        mock_state.fov_map = Mock()
        mock_state.camera = None
        mock_state_manager.state = mock_state
        
        # Create action processor
        processor = ActionProcessor(mock_state_manager)
        
        # Process pathfinding turn
        processor.process_pathfinding_turn()
        
        # Should stay in PLAYERS_TURN
        mock_state_manager.set_game_state.assert_called_once_with(GameStates.PLAYERS_TURN)


class TestAutoPickupPathfindingTurns(unittest.TestCase):
    """Test that auto-pickup pathfinding (right-click) triggers enemy turns."""
    
    @patch('mouse_movement.process_pathfinding_movement')
    def test_auto_pickup_pathfinding_triggers_enemy_turn(self, mock_process):
        """Test that right-click auto-pickup pathfinding gives enemies their turn."""
        from game_actions import ActionProcessor
        from state_machine.game_states import GameStates
        
        # Mock the movement result (continue pathfinding)
        mock_process.return_value = {
            "results": [
                {"fov_recompute": True},
                {"continue_pathfinding": True}
            ]
        }
        
        # Create mock state manager
        mock_state_manager = Mock()
        mock_state = Mock()
        mock_state.player = Mock()
        mock_state.player.pathfinding = Mock()
        mock_state.player.pathfinding.is_path_active.return_value = True
        mock_state.entities = []
        mock_state.game_map = Mock()
        mock_state.message_log = Mock()
        mock_state.fov_map = Mock()
        mock_state_manager.state = mock_state
        
        # Create action processor
        processor = ActionProcessor(mock_state_manager)
        
        # Process auto-pickup pathfinding turn
        processor._process_pathfinding_movement_action(None)
        
        # Should transition to ENEMY_TURN (monsters get their turn)
        mock_state_manager.set_game_state.assert_called_once_with(GameStates.ENEMY_TURN)
    
    @patch('mouse_movement.process_pathfinding_movement')
    def test_auto_pickup_with_enemy_interrupt_triggers_turn(self, mock_process):
        """Test that enemy interruption during auto-pickup still gives enemies their turn."""
        from game_actions import ActionProcessor
        from state_machine.game_states import GameStates
        
        # Mock the movement result (interrupted by enemy)
        mock_process.return_value = {
            "results": [
                {"fov_recompute": True},
                {"message": Mock()},
                {"enemy_turn": True}  # Movement interrupted, but player moved
            ]
        }
        
        # Create mock state manager
        mock_state_manager = Mock()
        mock_state = Mock()
        mock_state.player = Mock()
        mock_state.entities = []
        mock_state.game_map = Mock()
        mock_state.message_log = Mock()
        mock_state.fov_map = Mock()
        mock_state_manager.state = mock_state
        
        # Create action processor
        processor = ActionProcessor(mock_state_manager)
        
        # Process auto-pickup pathfinding turn
        processor._process_pathfinding_movement_action(None)
        
        # Should transition to ENEMY_TURN
        mock_state_manager.set_game_state.assert_called_once_with(GameStates.ENEMY_TURN)


if __name__ == '__main__':
    unittest.main()

