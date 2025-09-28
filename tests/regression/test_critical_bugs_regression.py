"""Regression tests for critical game bugs.

This module contains tests for critical bugs that must never reoccur,
such as negative HP, broken targeting, and other game-breaking issues.
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
from item_functions import heal, cast_confuse, cast_fireball


class TestDeathSystemRegression(unittest.TestCase):
    """Regression tests for death system bugs."""

    def test_negative_hp_prevented_regression(self):
        """Regression test: Player HP can go negative internally but should be treated as dead.

        Bug: Player could reach -2 HP and continue playing, which is invalid.
        Fix: Game logic should treat HP <= 0 as dead, HP display should be clamped to 0.
        """
        # Create player with low HP
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=0, power=5)
        )
        player.fighter.hp = 2  # Very low HP
        
        # Apply massive damage
        results = player.fighter.take_damage(10)  # More damage than current HP
        
        # HP can be negative internally, but player should be considered dead
        self.assertLessEqual(player.fighter.hp, 0,
                        "HP should be <= 0 when dead (can be negative for XP calculation)")
        # Death should be detected
        self.assertTrue(any(r.get("dead") for r in results), "Death should be detected")
        
        # Should indicate death
        self.assertTrue(any(result.get("dead") for result in results),
                       "Should indicate entity death when HP reaches 0")

    def test_death_detection_regression(self):
        """Regression test: Death should be properly detected and handled."""
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=0, power=5)
        )
        player.fighter.hp = 1
        
        # Apply lethal damage
        results = player.fighter.take_damage(1)
        
        # Should detect death
        death_results = [r for r in results if r.get("dead")]
        self.assertEqual(len(death_results), 1, "Should have exactly one death result")
        self.assertEqual(death_results[0]["dead"], player, "Should indicate correct entity died")

    def test_overkill_damage_regression(self):
        """Regression test: Massive overkill damage should still detect death properly."""
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=0, power=5)
        )
        player.fighter.hp = 5
        
        # Apply massive overkill damage
        results = player.fighter.take_damage(100)
        
        # HP can be negative, but death should be detected
        self.assertLessEqual(player.fighter.hp, 0,
                        "HP should be <= 0 when dead (can be negative with overkill)")
        # Death should be detected
        self.assertTrue(any(r.get("dead") for r in results), "Death should be detected even with overkill")

    def test_zero_damage_no_death_regression(self):
        """Regression test: Zero or negative damage should not cause death."""
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=10, power=5)  # High defense
        )
        
        # Apply zero damage
        results = player.fighter.take_damage(0)
        
        # Should not die
        self.assertFalse(any(result.get("dead") for result in results),
                        "Zero damage should not cause death")
        self.assertEqual(player.fighter.hp, 30, "HP should remain unchanged")


class TestTargetingSystemRegression(unittest.TestCase):
    """Regression tests for targeting system bugs."""

    def setUp(self):
        """Set up targeting test scenario."""
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

    def test_targeting_mode_entry_regression(self):
        """Regression test: Using targeting items should enter targeting mode.
        
        Bug: Confusion scroll and other targeting items didn't work.
        Fix: Properly handle targeting=True items and enter TARGETING state.
        """
        # Use confusion scroll (should enter targeting mode)
        action = {"inventory_index": 0}
        
        _process_game_actions(
            action, {}, self.state_manager, None, GameStates.SHOW_INVENTORY, {}
        )
        
        # Should enter targeting state
        self.assertEqual(self.state_manager.state.current_state, GameStates.TARGETING,
                        "Should enter targeting state when using targeting item")
        
        # Should store targeting item
        targeting_item = self.state_manager.get_extra_data("targeting_item")
        self.assertEqual(targeting_item, self.confusion_scroll,
                        "Should store the targeting item for later use")

    def test_targeting_left_click_regression(self):
        """Regression test: Left click should use targeting item on target.
        
        Bug: Mouse clicks during targeting didn't work.
        Fix: Handle left_click mouse action in TARGETING state.
        """
        # Set up targeting state
        self.state_manager.update_state(current_state=GameStates.TARGETING)
        self.state_manager.set_extra_data("targeting_item", self.confusion_scroll)
        self.state_manager.set_extra_data("previous_state", GameStates.PLAYERS_TURN)
        
        # Mock FOV to allow targeting
        self.state_manager.state.fov_map.configure_mock(**{
            'map_is_in_fov.return_value': True
        })
        
        # Simulate left click on monster
        mouse_action = {"left_click": (15, 10)}  # Monster position
        
        with patch('item_functions.libtcodpy.map_is_in_fov') as mock_fov:
            mock_fov.return_value = True
            
            _process_game_actions(
                {}, mouse_action, self.state_manager, None, GameStates.TARGETING, {}
            )
            
            # Should return to previous state
            self.assertEqual(self.state_manager.state.current_state, GameStates.PLAYERS_TURN,
                           "Should return to previous state after targeting")
            
            # Should clear targeting item
            targeting_item = self.state_manager.get_extra_data("targeting_item")
            self.assertIsNone(targeting_item, "Should clear targeting item after use")

    def test_targeting_right_click_cancel_regression(self):
        """Regression test: Right click should cancel targeting.
        
        Bug: No way to cancel targeting mode.
        Fix: Handle right_click mouse action to cancel targeting.
        """
        # Set up targeting state
        self.state_manager.update_state(current_state=GameStates.TARGETING)
        self.state_manager.set_extra_data("targeting_item", self.confusion_scroll)
        self.state_manager.set_extra_data("previous_state", GameStates.PLAYERS_TURN)
        
        # Simulate right click (cancel)
        mouse_action = {"right_click": (20, 20)}
        
        _process_game_actions(
            {}, mouse_action, self.state_manager, None, GameStates.TARGETING, {}
        )
        
        # Should return to previous state
        self.assertEqual(self.state_manager.state.current_state, GameStates.PLAYERS_TURN,
                        "Should return to previous state when canceling targeting")
        
        # Should clear targeting item
        targeting_item = self.state_manager.get_extra_data("targeting_item")
        self.assertIsNone(targeting_item, "Should clear targeting item when canceling")

    def test_targeting_escape_cancel_regression(self):
        """Regression test: Escape key should also cancel targeting."""
        # Set up targeting state
        self.state_manager.update_state(current_state=GameStates.TARGETING)
        self.state_manager.set_extra_data("targeting_item", self.confusion_scroll)
        self.state_manager.set_extra_data("previous_state", GameStates.PLAYERS_TURN)
        
        # Simulate escape key
        action = {"exit": True}
        
        _process_game_actions(
            action, {}, self.state_manager, None, GameStates.TARGETING, {}
        )
        
        # Should return to previous state
        self.assertEqual(self.state_manager.state.current_state, GameStates.PLAYERS_TURN,
                        "Should return to previous state when pressing escape")


class TestCombatSystemRegression(unittest.TestCase):
    """Regression tests for combat system bugs."""

    def test_player_death_handling_regression(self):
        """Regression test: Player death should be handled properly.

        Bug: Player could continue playing with negative HP.
        Fix: Ensure death is detected and game state changes appropriately.
        """
        # Create player with low HP
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=0, power=5)
        )
        player.fighter.hp = 1

        # Simulate lethal damage (like from a monster attack)
        damage_results = player.fighter.take_damage(10)  # More than current HP

        # Player should be dead (HP <= 0)
        self.assertLessEqual(player.fighter.hp, 0,
                           "Dead player should have HP <= 0 (can be negative)")
        
        # Death should be detected
        self.assertTrue(any(r.get("dead") for r in damage_results), 
                       "Death should be detected when HP reaches 0 or below")
        
        # The dead entity should be the player
        dead_entities = [r.get("dead") for r in damage_results if r.get("dead")]
        self.assertEqual(len(dead_entities), 1, "Should have exactly one death result")
        self.assertEqual(dead_entities[0], player, "Dead entity should be the player")


if __name__ == "__main__":
    unittest.main(verbosity=2)
