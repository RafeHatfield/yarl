"""Integration tests for player death during actual gameplay scenarios."""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from engine.systems.ai_system import AISystem
from engine.game_state_manager import GameStateManager
from game_states import GameStates
from entity import Entity
from components.fighter import Fighter
from components.ai import BasicMonster


class TestPlayerDeathDuringEnemyTurn(unittest.TestCase):
    """Test player death during enemy AI turns."""

    def setUp(self):
        """Set up AI death testing scenario."""
        # Create AI system
        self.ai_system = AISystem(priority=50)
        
        # Create mock engine
        self.mock_engine = Mock()
        self.state_manager = GameStateManager()
        self.mock_engine.state_manager = self.state_manager
        
        # Initialize AI system
        self.ai_system.initialize(self.mock_engine)
        
        # Create nearly dead player
        self.player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=0, power=5)
        )
        self.player.fighter.hp = 1  # About to die
        
        # Create monster next to player
        self.monster = Entity(
            x=11, y=10, char='o', color=(63, 127, 63), name='Orc',
            fighter=Fighter(hp=10, defense=0, power=5),  # Will kill player
            ai=BasicMonster(),
            blocks=True
        )
        
        # Set up game state for enemy turn
        self.state_manager.update_state(
            player=self.player,
            entities=[self.player, self.monster],
            game_map=Mock(),
            message_log=Mock(),
            current_state=GameStates.ENEMY_TURN,
            fov_map=Mock(),
        )

    def test_ai_system_handles_player_death(self):
        """Test that AI system properly handles killing the player."""
        # Mock FOV to allow monster to see player
        with patch('components.ai.libtcodpy.map_is_in_fov') as mock_fov:
            with patch('random.randint', return_value=20):  # Guarantee critical hit
                mock_fov.return_value = True
                
                # Run AI system update (monster should attack player)
                self.ai_system.update(0.016)
                
                # Player should be dead (HP <= 0)
                self.assertLessEqual(self.player.fighter.hp, 0,
                               "Player should have HP <= 0 after monster attack")
                
                # Verify AI system detected player death and changed game state
                self.assertEqual(self.state_manager.state.current_state, GameStates.PLAYER_DEAD,
                               "AI system should change game state to PLAYER_DEAD when player dies")


class TestDeathDetectionIntegration(unittest.TestCase):
    """Test death detection across all systems."""

    def test_combat_death_detection(self):
        """Test that combat properly detects and handles death."""
        # Create player and monster
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=0, power=10)
        )
        
        monster = Entity(
            x=11, y=10, char='o', color=(63, 127, 63), name='Orc',
            fighter=Fighter(hp=1, defense=0, power=5),  # Will die in one hit
            blocks=True
        )
        
        # Player attacks monster
        attack_results = player.fighter.attack(monster)
        
        # Should detect monster death
        death_results = [r for r in attack_results if r.get("dead")]
        self.assertEqual(len(death_results), 1, "Should detect monster death")
        self.assertEqual(death_results[0]["dead"], monster, "Should identify correct dead entity")
        
        # Monster should have HP <= 0 (can be negative for XP calculation)
        self.assertLessEqual(monster.fighter.hp, 0, "Dead monster should have HP <= 0")

    def test_massive_damage_death_detection(self):
        """Test death detection with massive overkill damage."""
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=1, defense=0, power=1)
        )
        
        # Apply massive damage
        results = player.fighter.take_damage(100)
        
        # Should detect death
        self.assertTrue(any(r.get("dead") for r in results), "Should detect death")
        self.assertLessEqual(player.fighter.hp, 0, "HP should be <= 0 when dead")


if __name__ == "__main__":
    unittest.main(verbosity=2)
