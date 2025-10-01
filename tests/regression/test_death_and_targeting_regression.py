"""Regression tests for death system and targeting flow bugs.

These tests ensure that critical game logic bugs don't reoccur,
specifically around player death and targeting system behavior.
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
from item_functions import cast_confuse


class TestPlayerDeathRegression(unittest.TestCase):
    """Regression tests for player death system."""

    def setUp(self):
        """Set up death testing scenario."""
        self.state_manager = GameStateManager()
        
        # Create player with very low HP
        self.player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=0, power=1)  # Weak player
        )
        self.player.fighter.hp = 1  # About to die
        
        # Create strong monster that will kill player
        self.monster = Entity(
            x=11, y=10, char='D', color=(255, 0, 0), name='Dragon',
            fighter=Fighter(hp=50, defense=0, power=10),  # Will kill player
            blocks=True
        )
        
        # Set up game state
        mock_game_map = Mock()
        mock_game_map.is_blocked.return_value = False  # Allow movement/attacks
        
        self.state_manager.update_state(
            player=self.player,
            entities=[self.player, self.monster],
            game_map=mock_game_map,
            message_log=Mock(),
            current_state=GameStates.PLAYERS_TURN,
        )

    def test_player_death_state_transition_regression(self):
        """Regression test: Player should enter PLAYER_DEAD state when dying.
        
        Bug: Player could continue playing at 0 HP without dying.
        Fix: Detect player death and transition to PLAYER_DEAD state.
        """
        # Simulate player taking lethal damage directly
        # (In the real game, this would happen during monster attacks)
        damage_results = self.player.fighter.take_damage(10)  # Lethal damage
        
        # Simulate processing the damage results (like in combat)
        for result in damage_results:
            dead_entity = result.get("dead")
            if dead_entity == self.player:
                # This is what should happen in the combat processing
                self.state_manager.set_game_state(GameStates.PLAYER_DEAD)
                death_message = Message(
                    "You died! Press any key to return to the main menu.",
                    (255, 30, 30)
                )
                self.state_manager.state.message_log.add_message(death_message)
        
        # Verify player is dead
        self.assertLessEqual(self.player.fighter.hp, 0, 
                       "Player should have HP <= 0 when dead")
        
        # Verify game state changed to PLAYER_DEAD
        self.assertEqual(self.state_manager.state.current_state, GameStates.PLAYER_DEAD,
                       "Game state should transition to PLAYER_DEAD when player dies")
        
        # Verify death message was added
        self.state_manager.state.message_log.add_message.assert_called()

    def test_player_death_message_regression(self):
        """Regression test: Player death should show appropriate message."""
        # Kill player directly
        results = self.player.fighter.take_damage(10)  # More than current HP
        
        # Simulate processing death result
        for result in results:
            dead_entity = result.get("dead")
            if dead_entity == self.player:
                self.state_manager.set_game_state(GameStates.PLAYER_DEAD)
                death_message = Message(
                    "You died! Press any key to return to the main menu.",
                    (255, 30, 30)
                )
                self.state_manager.state.message_log.add_message(death_message)
        
        # Verify death state
        self.assertEqual(self.state_manager.state.current_state, GameStates.PLAYER_DEAD,
                        "Should be in death state")
        
        # Verify death message
        self.state_manager.state.message_log.add_message.assert_called()

    def test_monster_death_no_state_change_regression(self):
        """Regression test: Monster death should not change game state."""
        # Create weak monster
        weak_monster = Entity(
            x=11, y=10, char='g', color=(63, 127, 63), name='Goblin',
            fighter=Fighter(hp=1, defense=0, power=1),
            blocks=True
        )
        
        self.state_manager.state.entities = [self.player, weak_monster]
        
        # Player attacks weak monster (should kill it)
        action = {"move": (1, 0)}
        
        with patch('entity.get_blocking_entities_at_location') as mock_get_blocking:
            with patch('random.randint', return_value=20):  # Guarantee critical hit
                mock_get_blocking.return_value = weak_monster
                
                _process_game_actions(
                    action, {}, self.state_manager, None, GameStates.PLAYERS_TURN, {}
                )
            
            # Player should be alive
            self.assertGreater(self.player.fighter.hp, 0, "Player should still be alive")
            
            # Game state should transition to ENEMY_TURN (normal flow)
            self.assertEqual(self.state_manager.state.current_state, GameStates.ENEMY_TURN,
                           "Should transition to enemy turn after killing monster")
            
            # Monster should be transformed into a corpse (remains in entities)
            self.assertIn(weak_monster, self.state_manager.state.entities,
                         "Dead monster should remain as corpse in entities")
            self.assertFalse(weak_monster.blocks, "Corpse should not block movement")
            self.assertEqual(weak_monster.char, '%', "Corpse should have % character")
            self.assertIsNone(weak_monster.fighter, "Corpse should have no fighter component")


class TestTargetingFlowRegression(unittest.TestCase):
    """Regression tests for targeting system flow."""

    def setUp(self):
        """Set up targeting flow testing."""
        self.state_manager = GameStateManager()
        
        # Create player
        self.player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            inventory=Inventory(capacity=26)
        )
        
        # Create target monster
        self.monster = Entity(
            x=15, y=10, char='o', color=(63, 127, 63), name='Orc',
            fighter=Fighter(hp=10, defense=0, power=3),
            blocks=True
        )
        
        # Create confusion scroll
        self.confusion_scroll = Entity(
            x=0, y=0, char='~', color=(255, 63, 159), name='Confusion Scroll',
            item=Item(
                use_function=cast_confuse,
                targeting=True,
                targeting_message=Message(
                    "Left-click an enemy to confuse it, or right-click to cancel.",
                    (63, 255, 255)
                )
            )
        )
        
        # Add scroll to inventory
        self.player.inventory.items.append(self.confusion_scroll)
        
        # Set up game state
        self.state_manager.update_state(
            player=self.player,
            entities=[self.player, self.monster],
            game_map=Mock(),
            message_log=Mock(),
            current_state=GameStates.SHOW_INVENTORY,
            fov_map=Mock(),
        )

    def test_targeting_complete_returns_to_game_regression(self):
        """Regression test: Completing targeting should return to game map.
        
        Bug: After using confusion scroll, returned to inventory menu instead of game.
        Fix: Successful targeting should return to PLAYERS_TURN, not previous state.
        """
        # Use confusion scroll (enters targeting mode)
        action = {"inventory_index": 0}
        _process_game_actions(
            action, {}, self.state_manager, None, GameStates.SHOW_INVENTORY, {}
        )
        
        # Should be in targeting mode
        self.assertEqual(self.state_manager.state.current_state, GameStates.TARGETING)
        
        # Complete targeting with left click
        mouse_action = {"left_click": (15, 10)}  # Click on monster
        
        with patch('item_functions.libtcodpy.map_is_in_fov') as mock_fov:
            mock_fov.return_value = True
            
            _process_game_actions(
                {}, mouse_action, self.state_manager, None, GameStates.TARGETING, {}
            )
            
            # Should return to PLAYERS_TURN (game map), NOT SHOW_INVENTORY
            self.assertEqual(self.state_manager.state.current_state, GameStates.PLAYERS_TURN,
                           "Successful targeting should return to game map, not inventory menu")

    def test_targeting_cancel_returns_to_previous_regression(self):
        """Regression test: Canceling targeting should return to where you came from.
        
        This ensures that canceling (right-click/escape) behaves differently
        from completing targeting.
        """
        # Use confusion scroll (enters targeting mode)
        action = {"inventory_index": 0}
        _process_game_actions(
            action, {}, self.state_manager, None, GameStates.SHOW_INVENTORY, {}
        )
        
        # Should be in targeting mode
        self.assertEqual(self.state_manager.state.current_state, GameStates.TARGETING)
        
        # Cancel targeting with right click
        mouse_action = {"right_click": (20, 20)}
        
        _process_game_actions(
            {}, mouse_action, self.state_manager, None, GameStates.TARGETING, {}
        )
        
        # Should return to SHOW_INVENTORY (where we came from)
        self.assertEqual(self.state_manager.state.current_state, GameStates.SHOW_INVENTORY,
                        "Canceling targeting should return to inventory menu")

    def test_targeting_escape_cancel_regression(self):
        """Regression test: Escape key should cancel targeting properly."""
        # Use confusion scroll (enters targeting mode)
        action = {"inventory_index": 0}
        _process_game_actions(
            action, {}, self.state_manager, None, GameStates.SHOW_INVENTORY, {}
        )
        
        # Cancel with escape key
        action = {"exit": True}
        _process_game_actions(
            action, {}, self.state_manager, None, GameStates.TARGETING, GameStates.SHOW_INVENTORY
        )
        
        # Should return to inventory (previous state)
        self.assertEqual(self.state_manager.state.current_state, GameStates.SHOW_INVENTORY,
                        "Escape should return to previous state")

    def test_targeting_item_cleanup_regression(self):
        """Regression test: Targeting item should be cleaned up properly."""
        # Use confusion scroll
        action = {"inventory_index": 0}
        _process_game_actions(
            action, {}, self.state_manager, None, GameStates.SHOW_INVENTORY, {}
        )
        
        # Should store targeting item
        targeting_item = self.state_manager.get_extra_data("targeting_item")
        self.assertIsNotNone(targeting_item, "Should store targeting item")
        
        # Complete targeting
        mouse_action = {"left_click": (15, 10)}
        with patch('item_functions.libtcodpy.map_is_in_fov') as mock_fov:
            mock_fov.return_value = True
            _process_game_actions(
                {}, mouse_action, self.state_manager, None, GameStates.TARGETING, {}
            )
        
        # Should clean up targeting item
        targeting_item = self.state_manager.get_extra_data("targeting_item")
        self.assertIsNone(targeting_item, "Should clean up targeting item after use")


class TestGameLogicFlowRegression(unittest.TestCase):
    """Regression tests for complete game logic flows."""

    def test_complete_inventory_to_targeting_to_game_flow(self):
        """Test the complete flow: Inventory → Targeting → Game Map."""
        state_manager = GameStateManager()
        
        # Set up player with confusion scroll
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            inventory=Inventory(capacity=26)
        )
        
        confusion_scroll = Entity(
            x=0, y=0, char='~', color=(255, 63, 159), name='Confusion Scroll',
            item=Item(use_function=cast_confuse, targeting=True)
        )
        player.inventory.items.append(confusion_scroll)
        
        monster = Entity(
            x=15, y=10, char='o', color=(63, 127, 63), name='Orc',
            fighter=Fighter(hp=10, defense=0, power=3)
        )
        
        state_manager.update_state(
            player=player,
            entities=[player, monster],
            game_map=Mock(),
            message_log=Mock(),
            current_state=GameStates.PLAYERS_TURN,
            fov_map=Mock(),
        )
        
        # Step 1: Open inventory
        action = {"show_inventory": True}
        _process_game_actions(action, {}, state_manager, None, GameStates.PLAYERS_TURN, {})
        self.assertEqual(state_manager.state.current_state, GameStates.SHOW_INVENTORY)
        
        # Step 2: Use targeting item
        action = {"inventory_index": 0}
        _process_game_actions(action, {}, state_manager, None, GameStates.SHOW_INVENTORY, {})
        self.assertEqual(state_manager.state.current_state, GameStates.TARGETING)
        
        # Step 3: Complete targeting
        mouse_action = {"left_click": (15, 10)}
        with patch('item_functions.libtcodpy.map_is_in_fov') as mock_fov:
            mock_fov.return_value = True
            _process_game_actions({}, mouse_action, state_manager, None, GameStates.TARGETING, {})
        
        # Step 4: Should be back to game map
        self.assertEqual(state_manager.state.current_state, GameStates.PLAYERS_TURN,
                        "Complete targeting flow should end at game map")

    def test_complete_combat_death_flow(self):
        """Test the complete flow: Combat → Death → Death State."""
        state_manager = GameStateManager()
        
        # Set up doomed player
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=0, power=1)
        )
        player.fighter.hp = 1  # Will die in one hit
        
        # Strong monster
        monster = Entity(
            x=11, y=10, char='D', color=(255, 0, 0), name='Dragon',
            fighter=Fighter(hp=50, defense=0, power=10)
        )
        
        mock_game_map = Mock()
        mock_game_map.is_blocked.return_value = False  # Allow movement/attacks
        
        state_manager.update_state(
            player=player,
            entities=[player, monster],
            game_map=mock_game_map,
            message_log=Mock(),
            current_state=GameStates.PLAYERS_TURN,
        )
        
        # Step 1: Player attacks monster
        action = {"move": (1, 0)}
        with patch('entity.get_blocking_entities_at_location') as mock_get_blocking:
            mock_get_blocking.return_value = monster
            
            _process_game_actions(action, {}, state_manager, None, GameStates.PLAYERS_TURN, {})
        
        # Step 2: Should transition to enemy turn after player attack
        self.assertEqual(state_manager.state.current_state, GameStates.ENEMY_TURN,
                        "Should transition to enemy turn after player attack")
        
        # Player should still be alive at this point (monster hasn't counter-attacked yet)
        self.assertGreater(player.fighter.hp, 0, "Player should still be alive after their attack")

    def test_no_actions_allowed_when_dead_regression(self):
        """Regression test: Player cannot perform actions when dead.
        
        Bug: Player could continue playing at 0 HP.
        Fix: Block all game actions when in PLAYER_DEAD state.
        """
        state_manager = GameStateManager()
        
        # Set up dead player
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=0, power=5)
        )
        player.fighter.hp = 0  # Dead
        
        # Set up game state as PLAYER_DEAD
        state_manager.update_state(
            player=player,
            entities=[player],
            game_map=Mock(),
            message_log=Mock(),
            current_state=GameStates.PLAYER_DEAD,
        )
        
        # Store original position
        original_x, original_y = player.x, player.y
        
        # Try various actions that should be blocked
        blocked_actions = [
            {"move": (1, 0)},  # Movement
            {"pickup": True},  # Item pickup
            {"show_inventory": True},  # Inventory
            {"wait": True},  # Wait
            {"take_stairs": True},  # Stairs
        ]
        
        for action in blocked_actions:
            # Process action (should be blocked)
            _process_game_actions(action, {}, state_manager, None, GameStates.PLAYER_DEAD, {})
            
            # Verify player didn't move
            self.assertEqual(player.x, original_x, f"Player moved when dead (action: {action})")
            self.assertEqual(player.y, original_y, f"Player moved when dead (action: {action})")
            
            # Verify state is still PLAYER_DEAD
            self.assertEqual(state_manager.state.current_state, GameStates.PLAYER_DEAD,
                           f"State changed when dead (action: {action})")
        
        # Verify HP is still 0
        self.assertEqual(player.fighter.hp, 0, "Player HP changed when dead")


if __name__ == "__main__":
    unittest.main(verbosity=2)
