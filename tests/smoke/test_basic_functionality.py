"""Smoke tests for basic game functionality.

These tests verify that core game systems work without crashing.
They're designed to run quickly and catch major regressions.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from engine_integration import create_game_engine, _process_game_actions
from engine.game_state_manager import GameStateManager
from game_states import GameStates
from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from components.item import Item


class TestBasicGameFunctionality(unittest.TestCase):
    """Smoke tests for basic game functionality."""

    def setUp(self):
        """Set up basic test fixtures."""
        self.state_manager = GameStateManager()
        
        # Create basic entities
        self.player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=2, power=5),
            inventory=Inventory(capacity=26)
        )
        
        self.monster = Entity(
            x=11, y=10, char='o', color=(63, 127, 63), name='Orc',
            fighter=Fighter(hp=10, defense=0, power=3),
            blocks=True
        )
        
        self.item = Entity(
            x=10, y=10, char='!', color=(127, 0, 127), name='Healing Potion',
            item=Item()
        )
        
        # Set up state
        self.state_manager.update_state(
            player=self.player,
            entities=[self.player, self.monster, self.item],
            game_map=Mock(),
            message_log=Mock(),
            current_state=GameStates.PLAYERS_TURN,
        )

    def test_engine_creation_smoke(self):
        """Smoke test: Engine creation doesn't crash."""
        mock_console = Mock()
        mock_panel = Mock()
        constants = {
            "screen_width": 80,
            "screen_height": 50,
            "colors": {"dark_wall": (0, 0, 100)},
        }
        
        # Should not crash
        engine = create_game_engine(constants, Mock(), Mock(), Mock())  # sidebar, viewport, status
        
        # Basic verification
        self.assertIsNotNone(engine, "Engine should be created")
        self.assertTrue(len(engine.systems) > 0, "Engine should have systems")

    def test_movement_action_smoke(self):
        """Smoke test: Movement actions don't crash."""
        action = {"move": (1, 0)}
        
        with patch('entity.get_blocking_entities_at_location') as mock_get_blocking:
            mock_get_blocking.return_value = None
            
            # Should not crash
            _process_game_actions(
                action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, {}
            )

    def test_pickup_action_smoke(self):
        """Smoke test: Pickup actions don't crash."""
        action = {"pickup": True}
        
        # Should not crash
        _process_game_actions(
            action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, {}
        )

    def test_combat_action_smoke(self):
        """Smoke test: Combat actions don't crash."""
        action = {"move": (1, 0)}  # Move into monster
        
        with patch('entity.get_blocking_entities_at_location') as mock_get_blocking:
            mock_get_blocking.return_value = self.monster
            
            # Should not crash
            _process_game_actions(
                action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, {}
            )

    def test_menu_transitions_smoke(self):
        """Smoke test: Menu transitions don't crash."""
        actions = [
            {"show_inventory": True},
            {"show_character_screen": True},
            {"drop_inventory": True},
        ]
        
        for action in actions:
            # Should not crash
            _process_game_actions(
                action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, {}
            )

    def test_exit_actions_smoke(self):
        """Smoke test: Exit actions don't crash."""
        # Test exit from various states
        states = [
            GameStates.SHOW_INVENTORY,
            GameStates.CHARACTER_SCREEN,
            GameStates.DROP_INVENTORY,
            GameStates.TARGETING,
        ]
        
        action = {"exit": True}
        
        for state in states:
            self.state_manager.update_state(current_state=state)
            
            # Should not crash
            _process_game_actions(
                action, {}, self.state_manager, None, state, GameStates.PLAYERS_TURN
            )


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""

    def test_invalid_action_handling(self):
        """Test that invalid actions don't crash the game."""
        state_manager = GameStateManager()
        
        # Test various invalid/malformed actions
        invalid_actions = [
            {"invalid_key": True},
            {"move": "invalid"},
            {"move": (999, 999)},
            None,
            {},
        ]
        
        for action in invalid_actions:
            # Should not crash
            try:
                _process_game_actions(
                    action or {}, {}, state_manager, None, GameStates.PLAYERS_TURN, {}
                )
            except Exception as e:
                self.fail(f"Action {action} caused crash: {e}")

    def test_missing_components_handling(self):
        """Test that missing components don't crash the game."""
        state_manager = GameStateManager()
        
        # Create player without fighter component
        player_no_fighter = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player'
            # No fighter or inventory components
        )
        
        state_manager.update_state(
            player=player_no_fighter,
            entities=[player_no_fighter],
            game_map=Mock(),
            message_log=Mock(),
            current_state=GameStates.PLAYERS_TURN,
        )
        
        # Test actions that require components
        actions = [
            {"move": (1, 0)},
            {"pickup": True},
        ]
        
        for action in actions:
            # Should not crash (may do nothing, but shouldn't crash)
            try:
                _process_game_actions(
                    action, {}, state_manager, None, GameStates.PLAYERS_TURN, {}
                )
            except Exception as e:
                self.fail(f"Action {action} with missing components caused crash: {e}")


if __name__ == "__main__":
    unittest.main()
