"""
Regression tests for inventory-related bugs.

This module contains tests to prevent regression of critical inventory bugs
that were discovered and fixed during testing.
"""

import unittest
from unittest.mock import Mock, patch

from engine.game_state_manager import GameStateManager
from game_states import GameStates
from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from components.equipment import Equipment
from components.equippable import Equippable
from components.item import Item
from equipment_slots import EquipmentSlots
from item_functions import cast_lightning, cast_fireball
from map_objects.game_map import GameMap
from fov_functions import initialize_fov, recompute_fov
from engine_integration import _process_game_actions
from game_messages import Message
from components.ai import BasicMonster


class TestInventoryBugsRegression(unittest.TestCase):
    """Regression tests for inventory-related bugs."""

    def setUp(self):
        """Set up test fixtures."""
        self.state_manager = GameStateManager()
        
        # Create player with equipment and inventory
        self.player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=2, power=5),
            inventory=Inventory(capacity=26),
            equipment=Equipment()
        )
        
        # Create a monster for lightning scroll testing
        self.monster = Entity(
            x=12, y=10, char='o', color=(63, 127, 63), name='Orc',
            fighter=Fighter(hp=10, defense=0, power=3),
            blocks=True
        )
        
        # Set up game state with real FOV map
        self.game_map = GameMap(30, 30)  # Create a real game map
        
        # Create a simple floor area for testing (clear walls around player and monster)
        for x in range(5, 25):
            for y in range(5, 25):
                self.game_map.tiles[x][y].blocked = False
                self.game_map.tiles[x][y].block_sight = False
        
        self.fov_map = initialize_fov(self.game_map)  # Create a real FOV map
        recompute_fov(self.fov_map, self.player.x, self.player.y, 10)  # Compute FOV
        
        self.state_manager.update_state(
            player=self.player,
            entities=[self.player, self.monster],
            game_map=self.game_map,
            message_log=Mock(),
            current_state=GameStates.SHOW_INVENTORY,
            fov_map=self.fov_map,
        )

    def test_lightning_scroll_fov_map_regression(self):
        """Regression test: Lightning scroll should not crash due to missing fov_map.
        
        Bug: Lightning scroll crashed with AttributeError: 'NoneType' object has no attribute 'map_c'
        Fix: Pass fov_map parameter to item use functions in engine_integration.py
        """
        # Create lightning scroll
        lightning_scroll = Entity(
            x=0, y=0, char='#', color=(255, 255, 0), name='Lightning Scroll',
            item=Item(use_function=cast_lightning, damage=20, maximum_range=5)
        )
        
        # Add to inventory
        self.player.inventory.add_item(lightning_scroll)
        
        # Mock fov_map to return True for monster visibility
        with patch('components.ai.map_is_in_fov', return_value=True):
            # Try to use the lightning scroll (inventory index 0)
            action = {"inventory_index": 0}
            
            # This should not crash anymore
            try:
                _process_game_actions(
                    action, {}, self.state_manager, None, GameStates.SHOW_INVENTORY, {}
                )
                # If we get here, the fix worked
                success = True
            except AttributeError as e:
                if "'NoneType' object has no attribute 'map_c'" in str(e):
                    success = False
                else:
                    raise  # Re-raise if it's a different error
            
            self.assertTrue(success, "Lightning scroll should not crash with AttributeError")

    def test_shield_equipping_regression(self):
        """Regression test: Shields should be equippable from inventory.
        
        Bug: Shields could be picked up but not equipped from inventory
        Fix: Process 'equip' results from inventory.use() in engine_integration.py
        """
        # Create shield
        shield = Entity(
            x=0, y=0, char=')', color=(139, 69, 19), name='Shield',
            equippable=Equippable(EquipmentSlots.OFF_HAND, defense_bonus=1)
        )
        
        # Add to inventory
        self.player.inventory.add_item(shield)
        
        # Verify shield is not equipped initially
        self.assertIsNone(self.player.equipment.off_hand, "Shield should not be equipped initially")
        
        # Try to equip the shield (inventory index 0)
        action = {"inventory_index": 0}
        
        _process_game_actions(
            action, {}, self.state_manager, None, GameStates.SHOW_INVENTORY, {}
        )
        
        # Check that shield is now equipped
        self.assertEqual(self.player.equipment.off_hand, shield, "Shield should be equipped in off hand")
        
        # Check that equipment message was added
        self.state_manager.state.message_log.add_message.assert_called()
        
        # Verify the message content contains "equip"
        call_args = self.state_manager.state.message_log.add_message.call_args
        message_text = call_args[0][0].text.lower()
        self.assertIn("equip", message_text, "Should show equipment message")
        self.assertIn("shield", message_text, "Message should mention the shield")

    def test_sword_equipping_regression(self):
        """Regression test: Swords should also be equippable from inventory."""
        # Create sword
        sword = Entity(
            x=0, y=0, char='/', color=(192, 192, 192), name='Sword',
            equippable=Equippable(EquipmentSlots.MAIN_HAND, power_bonus=3)
        )
        
        # Add to inventory
        self.player.inventory.add_item(sword)
        
        # Verify sword is not equipped initially
        self.assertIsNone(self.player.equipment.main_hand, "Sword should not be equipped initially")
        
        # Try to equip the sword (inventory index 0)
        action = {"inventory_index": 0}
        
        _process_game_actions(
            action, {}, self.state_manager, None, GameStates.SHOW_INVENTORY, {}
        )
        
        # Check that sword is now equipped
        self.assertEqual(self.player.equipment.main_hand, sword, "Sword should be equipped in main hand")
        
        # Check that equipment message was added
        self.state_manager.state.message_log.add_message.assert_called()

    def test_item_use_with_all_parameters_regression(self):
        """Regression test: Item functions should receive all necessary parameters.
        
        This test ensures that when items are used from inventory, they receive
        all the parameters they need (entities, fov_map, etc.).
        """
        # Create a healing potion (doesn't need fov_map but should still work)
        from item_functions import heal
        healing_potion = Entity(
            x=0, y=0, char='!', color=(127, 0, 127), name='Healing Potion',
            item=Item(use_function=heal, amount=4)
        )
        
        # Damage the player so healing will work
        self.player.fighter.hp = 20  # Down from 30
        
        # Add to inventory
        self.player.inventory.add_item(healing_potion)
        
        # Use the healing potion
        action = {"inventory_index": 0}
        
        _process_game_actions(
            action, {}, self.state_manager, None, GameStates.SHOW_INVENTORY, {}
        )
        
        # Player should be healed
        self.assertGreater(self.player.fighter.hp, 20, "Player should be healed")
        
        # Potion should be consumed (removed from inventory)
        self.assertEqual(len(self.player.inventory.items), 0, "Healing potion should be consumed")

    def test_fireball_death_processing_regression(self):
        """Regression test: Fireball should properly kill monsters and create corpses.
        
        Bug: Fireball would damage monsters and show death messages, but monsters wouldn't
        actually die - they'd lose HP but keep moving and attacking until hit again.
        Fix: Process death results from targeting item use in engine_integration.py
        """
        # Create a weak monster that will die from fireball
        monster = Entity(
            x=15, y=10, char='o', color=(63, 127, 63), name='Orc',
            fighter=Fighter(hp=5, defense=0, power=3),  # Low HP, will die from fireball
            ai=BasicMonster(),
            blocks=True
        )
        
        # Create fireball scroll
        fireball_scroll = Entity(
            x=0, y=0, char='~', color=(255, 127, 0), name='Fireball Scroll',
            item=Item(
                use_function=cast_fireball, 
                targeting=True,
                targeting_message=Message("Click a target for the fireball.", (63, 255, 255)),
                damage=20,  # More than enough to kill the orc
                radius=3
            )
        )
        
        # Add monster to entities and fireball to inventory
        self.state_manager.state.entities.append(monster)
        self.player.inventory.add_item(fireball_scroll)
        
        # Set up targeting state
        self.state_manager.set_game_state(GameStates.TARGETING)
        self.state_manager.set_extra_data("targeting_item", fireball_scroll)
        self.state_manager.set_extra_data("previous_state", GameStates.SHOW_INVENTORY)
        
        # Verify monster is alive initially
        self.assertEqual(monster.fighter.hp, 5, "Monster should start alive")
        self.assertTrue(monster.blocks, "Monster should block initially")
        self.assertEqual(monster.char, 'o', "Monster should have orc character")
        self.assertIsNotNone(monster.fighter, "Monster should have fighter component")
        self.assertIsNotNone(monster.ai, "Monster should have AI component")
        
        # Mock FOV to allow targeting
        with patch('components.ai.map_is_in_fov', return_value=True):
            # Simulate left-clicking on the monster's position (fireball targeting)
            mouse_action = {"left_click": (monster.x, monster.y)}
            
            _process_game_actions(
                {}, mouse_action, self.state_manager, None, GameStates.TARGETING, {}
            )
        
        # Verify monster was killed and transformed to corpse
        self.assertFalse(monster.blocks, "Monster should not block after death")
        self.assertEqual(monster.char, '%', "Monster should become corpse character")
        self.assertEqual(monster.color, (127, 0, 0), "Monster should have corpse color")
        self.assertIsNone(monster.fighter, "Monster should lose fighter component")
        self.assertIsNone(monster.ai, "Monster should lose AI component")
        self.assertTrue(monster.name.startswith("remains of"), "Monster should have corpse name")
        
        # Verify messages were added
        self.state_manager.state.message_log.add_message.assert_called()
        
        # Verify game state returned to player turn
        self.assertEqual(self.state_manager.state.current_state, GameStates.PLAYERS_TURN, 
                        "Should return to player turn after targeting")

    def test_lightning_scroll_death_processing_regression(self):
        """Regression test: Lightning scroll should properly kill monsters and create corpses.
        
        Bug: Lightning scroll would damage monsters and show death messages, but monsters wouldn't
        actually die - they'd lose HP but keep moving and attacking until hit again.
        Fix: Process death results from inventory item use in engine_integration.py
        """
        # Create a weak monster that will die from lightning
        monster = Entity(
            x=11, y=10, char='o', color=(63, 127, 63), name='Orc',
            fighter=Fighter(hp=5, defense=0, power=3),  # Low HP, will die from lightning
            ai=BasicMonster(),
            blocks=True
        )
        
        # Create lightning scroll
        lightning_scroll = Entity(
            x=0, y=0, char='~', color=(255, 255, 0), name='Lightning Scroll',
            item=Item(use_function=cast_lightning, damage=20, maximum_range=5)  # More than enough to kill
        )
        
        # Add monster to entities and lightning scroll to inventory
        self.state_manager.state.entities.append(monster)
        self.player.inventory.add_item(lightning_scroll)
        
        # Position player close to monster for lightning to target it
        self.player.x, self.player.y = 10, 10  # Adjacent to monster
        
        # Verify monster is alive initially
        self.assertEqual(monster.fighter.hp, 5, "Monster should start alive")
        self.assertTrue(monster.blocks, "Monster should block initially")
        self.assertEqual(monster.char, 'o', "Monster should have orc character")
        self.assertIsNotNone(monster.fighter, "Monster should have fighter component")
        self.assertIsNotNone(monster.ai, "Monster should have AI component")
        
        # Mock FOV to allow lightning to see the monster
        with patch('components.ai.map_is_in_fov', return_value=True):
            # Use lightning scroll from inventory (index 0)
            action = {"inventory_index": 0}
            
            _process_game_actions(
                action, {}, self.state_manager, None, GameStates.SHOW_INVENTORY, {}
            )
        
        # Verify monster was killed and transformed to corpse
        self.assertFalse(monster.blocks, "Monster should not block after death")
        self.assertEqual(monster.char, '%', "Monster should become corpse character")
        self.assertEqual(monster.color, (127, 0, 0), "Monster should have corpse color")
        self.assertIsNone(monster.fighter, "Monster should lose fighter component")
        self.assertIsNone(monster.ai, "Monster should lose AI component")
        self.assertTrue(monster.name.startswith("remains of"), "Monster should have corpse name")
        
        # Verify messages were added (lightning message + death message)
        self.state_manager.state.message_log.add_message.assert_called()
        
        # Verify game state returned to player turn (lightning doesn't use targeting)
        self.assertEqual(self.state_manager.state.current_state, GameStates.PLAYERS_TURN, 
                        "Should return to player turn after using lightning scroll")


if __name__ == "__main__":
    unittest.main()
