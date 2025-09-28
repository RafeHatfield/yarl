"""Integration tests for core game logic flows.

This module contains tests that verify complete game scenarios work end-to-end,
catching integration bugs that unit tests might miss.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
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


class TestGameLogicIntegration(unittest.TestCase):
    """Integration tests for core game logic scenarios."""

    def setUp(self):
        """Set up test fixtures for game logic testing."""
        # Create state manager
        self.state_manager = GameStateManager()
        
        # Create mock player with fighter and inventory
        self.player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=2, power=5),
            inventory=Inventory(capacity=26)
        )
        
        # Create mock monster
        self.monster = Entity(
            x=11, y=10, char='o', color=(63, 127, 63), name='Orc',
            fighter=Fighter(hp=10, defense=0, power=3),
            blocks=True
        )
        
        # Create mock item
        self.item = Entity(
            x=10, y=10, char='!', color=(127, 0, 127), name='Healing Potion',
            item=Item()
        )
        
        # Create mock game map
        self.game_map = Mock()
        self.game_map.is_blocked.return_value = False
        
        # Create mock message log
        self.message_log = Mock()
        
        # Set up game state
        self.state_manager.update_state(
            player=self.player,
            entities=[self.player, self.monster, self.item],
            game_map=self.game_map,
            message_log=self.message_log,
            current_state=GameStates.PLAYERS_TURN,
        )

    def test_player_movement_integration(self):
        """Test complete player movement flow."""
        # Setup action
        action = {"move": (1, 0)}  # Move right
        
        # Mock get_blocking_entities_at_location to return None (no blocking entity)
        with patch('entity.get_blocking_entities_at_location') as mock_get_blocking:
            mock_get_blocking.return_value = None
            
            # Process action
            _process_game_actions(
                action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, {}
            )
            
            # Verify player moved
            self.assertEqual(self.player.x, 11, "Player should have moved right")
            self.assertEqual(self.player.y, 10, "Player y should remain same")
            
            # Verify game state changed to enemy turn
            self.assertEqual(self.state_manager.state.current_state, GameStates.ENEMY_TURN,
                           "Should switch to enemy turn after movement")

    def test_player_attack_integration(self):
        """Test complete player attack flow."""
        # Setup action - move into monster
        action = {"move": (1, 0)}  # Move right into monster
        
        # Mock get_blocking_entities_at_location to return the monster
        with patch('entity.get_blocking_entities_at_location') as mock_get_blocking:
            mock_get_blocking.return_value = self.monster
            
            # Process action
            _process_game_actions(
                action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, {}
            )
            
            # Verify player didn't move (blocked by monster)
            self.assertEqual(self.player.x, 10, "Player should not have moved (blocked by monster)")
            
            # Verify monster took damage
            self.assertLess(self.monster.fighter.hp, 10, "Monster should have taken damage")
            
            # Verify message log was called (attack message should be added)
            self.assertTrue(self.message_log.add_message.called, 
                          "Attack should generate a message")

    def test_item_pickup_integration(self):
        """Test complete item pickup flow."""
        # Setup action
        action = {"pickup": True}
        
        # Ensure item is at player position
        self.item.x = self.player.x
        self.item.y = self.player.y
        
        # Process action
        _process_game_actions(
            action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, {}
        )
        
        # Verify item was added to inventory
        self.assertIn(self.item, self.player.inventory.items, 
                     "Item should be in player inventory")
        
        # Verify item was removed from entities
        self.assertNotIn(self.item, self.state_manager.state.entities,
                        "Item should be removed from map entities")
        
        # Verify pickup message was added
        self.assertTrue(self.message_log.add_message.called,
                       "Pickup should generate a message")

    def test_pickup_no_item_integration(self):
        """Test pickup when no item is present."""
        # Setup action
        action = {"pickup": True}
        
        # Move item away from player
        self.item.x = 20
        self.item.y = 20
        
        # Process action
        _process_game_actions(
            action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, {}
        )
        
        # Verify no item was added to inventory
        self.assertEqual(len(self.player.inventory.items), 0,
                        "No item should be in inventory")
        
        # Verify "nothing to pick up" message was added
        self.assertTrue(self.message_log.add_message.called,
                       "Should show 'nothing to pick up' message")

    def test_monster_death_integration(self):
        """Test complete monster death flow."""
        # Setup action - move into monster
        action = {"move": (1, 0)}
        
        # Set monster to low HP so it dies in one hit
        self.monster.fighter.hp = 1
        
        # Mock get_blocking_entities_at_location to return the monster
        with patch('entity.get_blocking_entities_at_location') as mock_get_blocking:
            mock_get_blocking.return_value = self.monster
            
            # Process action
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
        self.assertTrue(self.message_log.add_message.called,
                      "Monster death should generate messages")

    def test_inventory_full_integration(self):
        """Test pickup when inventory is full."""
        # Fill up inventory
        for i in range(26):  # Default capacity
            dummy_item = Entity(x=0, y=0, char='?', color=(255, 255, 255), 
                               name=f'Item{i}', item=Item())
            self.player.inventory.items.append(dummy_item)
        
        # Setup pickup action
        action = {"pickup": True}
        
        # Ensure item is at player position
        self.item.x = self.player.x
        self.item.y = self.player.y
        
        # Process action
        _process_game_actions(
            action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, {}
        )
        
        # Verify item was NOT added to inventory
        self.assertNotIn(self.item, self.player.inventory.items,
                        "Item should not be added when inventory full")
        
        # Verify item is still on map
        self.assertIn(self.item, self.state_manager.state.entities,
                     "Item should remain on map when inventory full")
        
        # Verify "inventory full" message was added
        self.assertTrue(self.message_log.add_message.called,
                       "Should show 'inventory full' message")


class TestGameStateTransitions(unittest.TestCase):
    """Test game state transitions work correctly."""

    def setUp(self):
        """Set up test fixtures."""
        self.state_manager = GameStateManager()
        self.state_manager.update_state(current_state=GameStates.PLAYERS_TURN)

    def test_inventory_menu_transitions(self):
        """Test opening and closing inventory menu."""
        # Test opening inventory
        action = {"show_inventory": True}
        _process_game_actions(action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, {})
        
        self.assertEqual(self.state_manager.state.current_state, GameStates.SHOW_INVENTORY,
                        "Should transition to inventory state")
        
        # Test closing inventory
        action = {"exit": True}
        _process_game_actions(action, {}, self.state_manager, None, GameStates.SHOW_INVENTORY, {})
        
        self.assertEqual(self.state_manager.state.current_state, GameStates.PLAYERS_TURN,
                        "Should return to player turn state")

    def test_character_screen_transitions(self):
        """Test opening and closing character screen."""
        # Test opening character screen
        action = {"show_character_screen": True}
        _process_game_actions(action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, {})
        
        self.assertEqual(self.state_manager.state.current_state, GameStates.CHARACTER_SCREEN,
                        "Should transition to character screen state")
        
        # Test closing character screen
        action = {"exit": True}
        _process_game_actions(action, {}, self.state_manager, None, GameStates.CHARACTER_SCREEN, {})
        
        self.assertEqual(self.state_manager.state.current_state, GameStates.PLAYERS_TURN,
                        "Should return to player turn state")


if __name__ == "__main__":
    unittest.main()
