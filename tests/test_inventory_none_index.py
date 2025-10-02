"""Test for inventory_index None handling bug.

Regression test for the error:
'<' not supported between instances of 'int' and 'NoneType'
"""

import unittest
from unittest.mock import Mock

from game_actions import ActionProcessor
from game_states import GameStates
from components.inventory import Inventory
from components.fighter import Fighter
from components.equipment import Equipment
from entity import Entity


class TestInventoryNoneIndexBug(unittest.TestCase):
    """Test that inventory_index=None is handled gracefully."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock state manager
        self.state_manager = Mock()
        
        # Create player with inventory
        fighter = Fighter(hp=100, defense=1, power=1)
        inventory = Inventory(26)
        equipment = Equipment()
        
        self.player = Entity(0, 0, '@', (255, 255, 255), 'Player',
                            blocks=True, render_order=5,
                            fighter=fighter, inventory=inventory, equipment=equipment)
        
        # Add a test item
        test_item = Entity(0, 0, '!', (255, 0, 0), 'Test Potion')
        self.player.inventory.add_item(test_item)
        
        # Set up state manager mock
        self.state_manager.state = Mock()
        self.state_manager.state.player = self.player
        self.state_manager.state.current_state = GameStates.SHOW_INVENTORY
        self.state_manager.state.message_log = Mock()
        
        # Create action processor
        self.action_processor = ActionProcessor(self.state_manager)
    
    def test_inventory_index_none_doesnt_crash(self):
        """Test that inventory_index=None doesn't cause a crash."""
        # This should not raise an exception
        try:
            self.action_processor._handle_inventory_action(None)
        except TypeError as e:
            if "'<' not supported between instances of 'int' and 'NoneType'" in str(e):
                self.fail(f"inventory_index=None caused the comparison bug: {e}")
            else:
                raise
    
    def test_inventory_index_string_doesnt_crash(self):
        """Test that inventory_index with invalid type doesn't crash."""
        # Test with string (edge case)
        try:
            self.action_processor._handle_inventory_action("invalid")
        except (TypeError, AttributeError) as e:
            if "'<' not supported" in str(e):
                self.fail(f"Invalid inventory_index type caused comparison bug: {e}")
    
    def test_inventory_index_negative_handled_gracefully(self):
        """Test that negative inventory_index is handled gracefully."""
        # Negative index should be handled without crashing
        try:
            self.action_processor._handle_inventory_action(-1)
        except Exception as e:
            self.fail(f"Negative inventory_index caused crash: {e}")
    
    def test_inventory_index_out_of_bounds_handled(self):
        """Test that out-of-bounds inventory_index is handled gracefully."""
        # Index larger than inventory size
        try:
            self.action_processor._handle_inventory_action(999)
        except Exception as e:
            self.fail(f"Out-of-bounds inventory_index caused crash: {e}")
    
    def test_valid_inventory_index_works(self):
        """Test that valid inventory indices still work correctly."""
        # Valid index (0) should work
        try:
            self.action_processor._handle_inventory_action(0)
            # Item usage/dropping logic will be called (mocked away)
        except Exception as e:
            self.fail(f"Valid inventory_index=0 caused crash: {e}")


if __name__ == '__main__':
    unittest.main()

