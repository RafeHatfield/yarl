"""Validation tests for all implemented game actions.

This module tests that every action handler works correctly and produces
the expected results without crashing.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from engine_integration import _process_game_actions
from engine.game_state_manager import GameStateManager
from game_states import GameStates
from game_messages import Message
from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from components.item import Item
from item_functions import heal, cast_lightning


class TestActionValidation(unittest.TestCase):
    """Validate all game actions work correctly."""

    def setUp(self):
        """Set up comprehensive test scenario."""
        self.state_manager = GameStateManager()
        
        # Create player with some damage for healing tests
        self.player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=2, power=5),  # Max HP is 30
            inventory=Inventory(capacity=26)
        )
        # Damage the player so healing will work
        self.player.fighter.hp = 20  # Now at 20/30
        
        # Create healing potion
        self.healing_potion = Entity(
            x=0, y=0, char='!', color=(127, 0, 127), name='Healing Potion',
            item=Item(use_function=heal, amount=4)
        )
        
        # Add potion to inventory
        self.player.inventory.items.append(self.healing_potion)
        
        # Create monster for combat tests
        self.monster = Entity(
            x=11, y=10, char='o', color=(63, 127, 63), name='Orc',
            fighter=Fighter(hp=10, defense=0, power=3),
            blocks=True
        )
        
        # Set up game state
        self.state_manager.update_state(
            player=self.player,
            entities=[self.player, self.monster],
            game_map=Mock(),
            message_log=Mock(),
            current_state=GameStates.PLAYERS_TURN,
        )
        
        # Mock game map
        self.state_manager.state.game_map.is_blocked.return_value = False
        

    def test_wait_action_complete(self):
        """Test wait action transitions to enemy turn."""
        action = {"wait": True}
        
        _process_game_actions(
            action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, {}
        )
        
        self.assertEqual(self.state_manager.state.current_state, GameStates.ENEMY_TURN,
                        "Wait should transition to enemy turn")

    def test_inventory_usage_complete(self):
        """Test using healing potion from inventory."""
        # Switch to inventory state
        self.state_manager.update_state(current_state=GameStates.SHOW_INVENTORY)
        
        action = {"inventory_index": 0}  # Use healing potion
        original_hp = self.player.fighter.hp
        
        _process_game_actions(
            action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, {}
        )
        
        # Verify healing occurred
        self.assertGreater(self.player.fighter.hp, original_hp,
                          "Player should be healed after using potion")
        
        # Verify item was consumed (should be removed from inventory)
        self.assertEqual(len(self.player.inventory.items), 0,
                        "Healing potion should be consumed and removed from inventory")
        
        # Verify returned to player turn
        self.assertEqual(self.state_manager.state.current_state, GameStates.PLAYERS_TURN,
                        "Should return to player turn after using item")

    def test_item_dropping_complete(self):
        """Test dropping items from inventory."""
        # Add item back to inventory for dropping test
        if self.healing_potion not in self.player.inventory.items:
            self.player.inventory.items.append(self.healing_potion)
        
        # Switch to drop inventory state
        self.state_manager.update_state(current_state=GameStates.DROP_INVENTORY)
        
        action = {"inventory_index": 0}  # Drop healing potion
        
        _process_game_actions(
            action, {}, self.state_manager, None, GameStates.DROP_INVENTORY, {}
        )
        
        # Verify item was removed from inventory
        self.assertNotIn(self.healing_potion, self.player.inventory.items,
                        "Item should be removed from inventory when dropped")
        
        # Verify item was placed on map
        self.assertIn(self.healing_potion, self.state_manager.state.entities,
                     "Dropped item should be placed on map")
        
        # Verify item is at player position
        self.assertEqual(self.healing_potion.x, self.player.x,
                        "Dropped item should be at player x position")
        self.assertEqual(self.healing_potion.y, self.player.y,
                        "Dropped item should be at player y position")
        
        # Verify returned to player turn
        self.assertEqual(self.state_manager.state.current_state, GameStates.PLAYERS_TURN,
                        "Should return to player turn after dropping item")

    def test_invalid_inventory_index_handling(self):
        """Test handling of invalid inventory indices."""
        # Switch to inventory state
        self.state_manager.update_state(current_state=GameStates.SHOW_INVENTORY)
        
        invalid_indices = [-1, 999, None]
        
        for invalid_index in invalid_indices:
            with self.subTest(index=invalid_index):
                action = {"inventory_index": invalid_index}
                
                # Should not crash
                try:
                    _process_game_actions(
                        action, {}, self.state_manager, None, GameStates.SHOW_INVENTORY, {}
                    )
                except Exception as e:
                    self.fail(f"Invalid inventory index {invalid_index} caused crash: {e}")

    def test_combat_flow_complete(self):
        """Test complete combat flow with death handling."""
        # Set monster to low HP
        self.monster.fighter.hp = 1
        
        action = {"move": (1, 0)}  # Move into monster
        
        with patch('entity.get_blocking_entities_at_location') as mock_get_blocking:
            with patch('random.randint', return_value=20):  # Guarantee critical hit
                mock_get_blocking.return_value = self.monster
                
                _process_game_actions(
                    action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, {}
                )
            
            # Verify monster was transformed into a corpse (remains in entities)
            self.assertIn(self.monster, self.state_manager.state.entities,
                         "Dead monster should remain as corpse in entities")
            self.assertFalse(self.monster.blocks, "Corpse should not block movement")
            self.assertEqual(self.monster.char, '%', "Corpse should have % character")
            self.assertIsNone(self.monster.fighter, "Corpse should have no fighter component")
            
            # Verify death message was added
            self.assertTrue(self.state_manager.state.message_log.add_message.called,
                          "Death should generate a message")

    def test_state_transitions_complete(self):
        """Test all menu state transitions work correctly."""
        transitions = [
            # From PLAYERS_TURN
            (GameStates.PLAYERS_TURN, {"show_inventory": True}, GameStates.SHOW_INVENTORY),
            (GameStates.PLAYERS_TURN, {"drop_inventory": True}, GameStates.DROP_INVENTORY),
            (GameStates.PLAYERS_TURN, {"show_character_screen": True}, GameStates.CHARACTER_SCREEN),
            
            # Exit from menus back to PLAYERS_TURN
            (GameStates.SHOW_INVENTORY, {"exit": True}, GameStates.PLAYERS_TURN),
            (GameStates.DROP_INVENTORY, {"exit": True}, GameStates.PLAYERS_TURN),
            (GameStates.CHARACTER_SCREEN, {"exit": True}, GameStates.PLAYERS_TURN),
        ]
        
        for start_state, action, expected_end_state in transitions:
            with self.subTest(start=start_state, action=action, end=expected_end_state):
                # Set starting state
                self.state_manager.update_state(current_state=start_state)
                
                # Process action
                _process_game_actions(
                    action, {}, self.state_manager, None, start_state, {}
                )
                
                # Verify end state
                self.assertEqual(self.state_manager.state.current_state, expected_end_state,
                               f"Should transition from {start_state} to {expected_end_state}")


class TestActionHandlerRobustness(unittest.TestCase):
    """Test that action handlers are robust against edge cases."""

    def setUp(self):
        """Set up edge case testing."""
        self.state_manager = GameStateManager()
        
        # Create minimal player (might be missing components)
        self.player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player'
        )
        
        self.state_manager.update_state(
            player=self.player,
            entities=[self.player],
            game_map=Mock(),
            message_log=Mock(),
            current_state=GameStates.PLAYERS_TURN,
        )

    def test_actions_with_missing_components(self):
        """Test actions when player is missing components."""
        # Player has no fighter, inventory, or equipment
        actions = [
            {"move": (1, 0)},
            {"pickup": True},
            {"wait": True},
            {"show_inventory": True},
            {"take_stairs": True},
        ]
        
        for action in actions:
            with self.subTest(action=action):
                try:
                    _process_game_actions(
                        action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, {}
                    )
                except Exception as e:
                    self.fail(f"Action {action} with missing components crashed: {e}")

    def test_actions_with_empty_game_state(self):
        """Test actions with minimal game state."""
        # Create empty state manager
        empty_state_manager = GameStateManager()
        
        actions = [
            {"move": (1, 0)},
            {"pickup": True},
            {"wait": True},
        ]
        
        for action in actions:
            with self.subTest(action=action):
                try:
                    _process_game_actions(
                        action, {}, empty_state_manager, None, GameStates.PLAYERS_TURN, {}
                    )
                except Exception as e:
                    self.fail(f"Action {action} with empty state crashed: {e}")

    def test_concurrent_actions(self):
        """Test multiple actions in same input."""
        # Test action with multiple keys (should handle gracefully)
        action = {
            "move": (1, 0),
            "pickup": True,
            "show_inventory": True,
        }
        
        try:
            _process_game_actions(
                action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, {}
            )
        except Exception as e:
            self.fail(f"Multiple actions crashed: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
