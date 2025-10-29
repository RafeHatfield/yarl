"""Regression test for the specific zombie bug where player can act after death.

This test ensures that the timing issue between AI system death detection
and action processing is resolved.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from engine_integration import _process_game_actions
from engine.systems.ai_system import AISystem
from engine.game_state_manager import GameStateManager
from game_states import GameStates
from game_messages import MessageLog
from entity import Entity
from components.fighter import Fighter
from components.ai import BasicMonster


class TestZombieBugRegression(unittest.TestCase):
    """Test the specific zombie bug where player acts after death."""

    def setUp(self):
        """Set up the zombie bug test scenario."""
        from systems.turn_controller import reset_turn_controller
        from services import pickup_service as pickup_service_module
        from services import movement_service as movement_service_module
        reset_turn_controller()
        pickup_service_module._pickup_service = None
        movement_service_module._movement_service = None
        self.state_manager = GameStateManager()
        self.message_log = MessageLog(x=0, width=80, height=5)
        
        # Create nearly dead player
        self.player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=0, power=5)
        )
        self.player.fighter.hp = 1  # About to die
        
        # Create monster that will kill player
        self.monster = Entity(
            x=11, y=10, char='o', color=(63, 127, 63), name='Orc',
            fighter=Fighter(hp=10, defense=0, power=10),  # Will kill player
            ai=BasicMonster(),
            blocks=True
        )
        
        # Set up initial game state
        mock_game_map = Mock()
        mock_game_map.is_blocked.return_value = False  # Allow movement/attacks
        
        self.state_manager.update_state(
            player=self.player,
            entities=[self.player, self.monster],
            game_map=mock_game_map,
            message_log=self.message_log,
            current_state=GameStates.PLAYERS_TURN,
            fov_map=Mock(),
        )

    def test_no_zombie_actions_after_ai_death_regression(self):
        """Regression test: Player cannot act after AI system kills them.
        
        This is the specific zombie bug where:
        1. Player presses attack
        2. AI system runs and kills player
        3. Player's attack action still gets processed (zombie behavior)
        
        The fix ensures actions are processed BEFORE AI system runs.
        """
        # Create AI system
        ai_system = AISystem(priority=50)
        mock_engine = Mock()
        mock_engine.state_manager = self.state_manager
        ai_system.initialize(mock_engine)
        
        # Simulate the problematic sequence:
        # 1. Player is about to attack monster (move action)
        player_action = {"move": (1, 0)}  # Attack monster
        
        # 2. Process player action first (this should work)
        with patch('entity.get_blocking_entities_at_location') as mock_get_blocking:
            mock_get_blocking.return_value = self.monster
            
            # Player attacks monster
            _process_game_actions(
                player_action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, {}
            )
            
            # Player should still be alive at this point
            self.assertGreater(self.player.fighter.hp, 0, "Player should be alive after their attack")
            
            # State should transition to ENEMY_TURN
            self.assertEqual(self.state_manager.state.current_state, GameStates.ENEMY_TURN,
                           "Should be enemy turn after player action")
        
        # 3. Now AI system runs and kills player
        with patch('components.ai.libtcodpy.map_is_in_fov') as mock_fov:
            with patch('random.randint', return_value=20):  # Guarantee critical hit
                mock_fov.return_value = True
                
                # AI system processes monster turn (monster kills player)
                ai_system.update(0.016)
                
                # Player should now be dead (HP can be negative for XP calculation)
                self.assertLessEqual(self.player.fighter.hp, 0, "Player should be dead after monster attack")
                self.assertEqual(self.state_manager.state.current_state, GameStates.PLAYER_DEAD,
                               "Should be in death state after AI kills player")
        
        # 4. Try to process another player action (should be blocked)
        zombie_action = {"move": (0, 1)}  # Try to move after death
        original_x, original_y = self.player.x, self.player.y
        
        _process_game_actions(
            zombie_action, {}, self.state_manager, None, GameStates.PLAYER_DEAD, {}
        )
        
        # Player should not have moved
        self.assertEqual(self.player.x, original_x, "Dead player should not move")
        self.assertEqual(self.player.y, original_y, "Dead player should not move")
        
        # State should still be PLAYER_DEAD
        self.assertEqual(self.state_manager.state.current_state, GameStates.PLAYER_DEAD,
                        "Should remain in death state")

    def test_ai_system_respects_death_state_regression(self):
        """Regression test: AI system doesn't run when player is dead."""
        # Set player to dead state
        self.player.fighter.hp = 0
        self.state_manager.set_game_state(GameStates.PLAYER_DEAD)
        
        # Create AI system
        ai_system = AISystem(priority=50)
        mock_engine = Mock()
        mock_engine.state_manager = self.state_manager
        ai_system.initialize(mock_engine)
        
        # Store original monster HP
        original_monster_hp = self.monster.fighter.hp
        
        # Try to run AI system (should be blocked)
        ai_system.update(0.016)
        
        # Monster should not have acted (HP unchanged)
        self.assertEqual(self.monster.fighter.hp, original_monster_hp,
                        "Monster should not act when player is dead")
        
        # State should remain PLAYER_DEAD
        self.assertEqual(self.state_manager.state.current_state, GameStates.PLAYER_DEAD,
                        "Should remain in death state")

    def test_death_state_prevents_turn_transition_regression(self):
        """Regression test: Death state prevents switching back to player turn."""
        # Set up enemy turn with dead player
        self.player.fighter.hp = 0
        self.state_manager.set_game_state(GameStates.ENEMY_TURN)
        
        # Create AI system
        ai_system = AISystem(priority=50)
        mock_engine = Mock()
        mock_engine.state_manager = self.state_manager
        ai_system.initialize(mock_engine)
        
        # Manually set player to dead during "AI processing"
        self.state_manager.set_game_state(GameStates.PLAYER_DEAD)
        
        # AI system should not switch back to player turn
        ai_system.update(0.016)
        
        # Should remain in death state, not switch to player turn
        self.assertEqual(self.state_manager.state.current_state, GameStates.PLAYER_DEAD,
                        "Should not switch to player turn when player is dead")


if __name__ == "__main__":
    unittest.main(verbosity=2)
