"""Tests for sidebar inventory single-click activation fix.

This test suite verifies that clicking on an inventory item in the sidebar
during normal gameplay (PLAYERS_TURN) activates the item on the first click,
without requiring a "priming" click.

Bug Context:
- Previously, clicking sidebar inventory items required TWO clicks
- First click seemed to do nothing
- Second click performed the action
- This was especially noticeable after inventory re-sorts or on first click

Root Cause:
- _handle_sidebar_click was calling _handle_inventory_action
- _handle_inventory_action only worked for menu states (SHOW_INVENTORY, etc.)
- During PLAYERS_TURN, it would just return without doing anything

Fix:
- _handle_sidebar_click now directly calls _use_inventory_item during PLAYERS_TURN
- Still uses _handle_inventory_action for menu states (backward compatible)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from components.equipment import Equipment
from components.item import Item
from game_states import GameStates
from game_actions import ActionProcessor
from engine.game_state_manager import GameStateManager
from engine.turn_manager import TurnManager
from item_functions import heal
from game_messages import MessageLog


def create_test_player():
    """Create a test player entity."""
    fighter = Fighter(hp=20, defense=2, power=5)  # Damaged for testing healing
    inventory = Inventory(capacity=26)
    equipment = Equipment()
    
    player = Entity(
        x=10, y=10,
        char='@',
        color=(255, 255, 255),
        name="Test Player",
        blocks=True,
        fighter=fighter,
        inventory=inventory,
        equipment=equipment
    )
    
    return player


def create_healing_potion(name="Healing Potion"):
    """Create a healing potion item."""
    item = Item(use_function=heal, amount=4)
    
    potion = Entity(
        x=0, y=0,
        char='!',
        color=(127, 0, 255),
        name=name,
        item=item
    )
    
    return potion


def create_mock_state_manager(player, current_state=GameStates.PLAYERS_TURN):
    """Create a mock state manager for testing."""
    state_manager = GameStateManager()
    message_log = MessageLog(x=0, width=80, height=10)
    
    state_manager.update_state(
        player=player,
        entities=[player],
        game_map=Mock(),
        message_log=message_log,
        fov_map=Mock(),
        current_state=current_state
    )
    
    return state_manager


class TestSidebarSingleClickDuringPlayersTurn:
    """Test that sidebar clicks work on first click during PLAYERS_TURN."""
    
    def test_first_sidebar_click_uses_item_immediately(self):
        """First click on a sidebar inventory item should use it immediately."""
        # Setup
        player = create_test_player()
        player.fighter.hp = 10  # Damage player so healing works
        
        potion = create_healing_potion("Healing Potion")
        player.inventory.add_item(potion)
        
        state_manager = create_mock_state_manager(player, GameStates.PLAYERS_TURN)
        turn_manager = TurnManager(state_manager)
        action_processor = ActionProcessor(state_manager, turn_manager)
        
        # Get the inventory index of the potion (should be 0)
        sorted_items = sorted(player.inventory.items, key=lambda i: i.get_display_name().lower())
        potion_index = sorted_items.index(potion)
        
        original_hp = player.fighter.hp
        
        # Simulate sidebar click by calling _handle_sidebar_click with action
        # This mimics what handle_sidebar_click returns
        with patch('ui.sidebar_interaction.handle_sidebar_click') as mock_handle:
            mock_handle.return_value = {
                'inventory_index': potion_index,
                'source': 'sidebar_click'
            }
            
            # Act: Click on the potion in sidebar
            action_processor._handle_sidebar_click((50, 20))  # Arbitrary screen coords
        
        # Assert: Potion should be used on first click
        assert player.fighter.hp > original_hp, "HP should increase from healing potion"
        assert potion not in player.inventory.items, "Potion should be consumed"
    
    def test_sidebar_click_after_inventory_resort(self):
        """After inventory re-sort, first click should still work."""
        # Setup
        player = create_test_player()
        player.fighter.hp = 10
        
        # Add multiple potions with different names (will be sorted alphabetically)
        potion_a = create_healing_potion("Antidote Potion")
        potion_b = create_healing_potion("Healing Potion")
        potion_z = create_healing_potion("Zephyr Potion")
        
        # Add in non-alphabetical order
        player.inventory.add_item(potion_z)
        player.inventory.add_item(potion_a)
        player.inventory.add_item(potion_b)
        
        state_manager = create_mock_state_manager(player, GameStates.PLAYERS_TURN)
        turn_manager = TurnManager(state_manager)
        action_processor = ActionProcessor(state_manager, turn_manager)
        
        # Get sorted inventory (sidebar displays items alphabetically)
        sorted_items = sorted(player.inventory.items, key=lambda i: i.get_display_name().lower())
        
        # Click on the SECOND item in the sorted list (Healing Potion)
        target_item = sorted_items[1]  # Should be "Healing Potion" (alphabetically between A and Z)
        assert target_item.name == "Healing Potion", f"Expected Healing Potion, got {target_item.name}"
        
        original_hp = player.fighter.hp
        
        # Simulate clicking the second item
        with patch('ui.sidebar_interaction.handle_sidebar_click') as mock_handle:
            mock_handle.return_value = {
                'inventory_index': 1,  # Index into FULL sorted inventory
                'source': 'sidebar_click'
            }
            
            action_processor._handle_sidebar_click((50, 21))
        
        # Assert: Correct item was used
        assert player.fighter.hp > original_hp, "HP should increase"
        assert target_item not in player.inventory.items, "Healing Potion should be consumed"
        assert potion_a in player.inventory.items, "Antidote should still be in inventory"
        assert potion_z in player.inventory.items, "Zephyr should still be in inventory"
    
    def test_multiple_sidebar_clicks_work_consecutively(self):
        """Multiple sidebar clicks should each work on first try."""
        # Setup
        player = create_test_player()
        player.fighter.hp = 5  # Very low HP
        
        potion1 = create_healing_potion("Potion A")
        potion2 = create_healing_potion("Potion B")
        potion3 = create_healing_potion("Potion C")
        
        player.inventory.add_item(potion1)
        player.inventory.add_item(potion2)
        player.inventory.add_item(potion3)
        
        state_manager = create_mock_state_manager(player, GameStates.PLAYERS_TURN)
        turn_manager = TurnManager(state_manager)
        action_processor = ActionProcessor(state_manager, turn_manager)
        
        original_hp = player.fighter.hp
        
        # First click
        with patch('ui.sidebar_interaction.handle_sidebar_click') as mock_handle:
            mock_handle.return_value = {'inventory_index': 0, 'source': 'sidebar_click'}
            action_processor._handle_sidebar_click((50, 20))
        
        hp_after_first = player.fighter.hp
        assert hp_after_first > original_hp, "First click should work"
        assert len(player.inventory.items) == 2, "Should have 2 potions left"
        
        # Second click (on new index 0, which is now potion2)
        state_manager.set_game_state(GameStates.PLAYERS_TURN)  # Reset to players turn
        with patch('ui.sidebar_interaction.handle_sidebar_click') as mock_handle:
            mock_handle.return_value = {'inventory_index': 0, 'source': 'sidebar_click'}
            action_processor._handle_sidebar_click((50, 20))
        
        hp_after_second = player.fighter.hp
        assert hp_after_second > hp_after_first, "Second click should also work immediately"
        assert len(player.inventory.items) == 1, "Should have 1 potion left"
    
    def test_sidebar_click_on_empty_slot_safe(self):
        """Clicking on invalid inventory index should not crash."""
        # Setup
        player = create_test_player()
        player.inventory.add_item(create_healing_potion("Only Potion"))
        
        state_manager = create_mock_state_manager(player, GameStates.PLAYERS_TURN)
        turn_manager = TurnManager(state_manager)
        action_processor = ActionProcessor(state_manager, turn_manager)
        
        # Try to click on index 5 (out of range)
        with patch('ui.sidebar_interaction.handle_sidebar_click') as mock_handle:
            mock_handle.return_value = {'inventory_index': 5, 'source': 'sidebar_click'}
            
            # Should not crash
            action_processor._handle_sidebar_click((50, 25))
        
        # Item should still be in inventory
        assert len(player.inventory.items) == 1


class TestSidebarClickBackwardCompatibility:
    """Test that sidebar clicks still work in menu states (backward compatibility)."""
    
    def test_sidebar_click_in_show_inventory_state(self):
        """Sidebar clicks should still work when in SHOW_INVENTORY state."""
        # This tests backward compatibility - when in menu states,
        # we should still use _handle_inventory_action
        
        player = create_test_player()
        player.fighter.hp = 10
        potion = create_healing_potion("Test Potion")
        player.inventory.add_item(potion)
        
        # Start in SHOW_INVENTORY state (full-screen inventory menu)
        state_manager = create_mock_state_manager(player, GameStates.SHOW_INVENTORY)
        turn_manager = TurnManager(state_manager)
        action_processor = ActionProcessor(state_manager, turn_manager)
        
        original_hp = player.fighter.hp
        
        with patch('ui.sidebar_interaction.handle_sidebar_click') as mock_handle:
            mock_handle.return_value = {'inventory_index': 0, 'source': 'sidebar_click'}
            action_processor._handle_sidebar_click((50, 20))
        
        # Should still work via _handle_inventory_action path
        assert player.fighter.hp > original_hp, "Should use item in SHOW_INVENTORY state"
    
    def test_sidebar_click_in_drop_inventory_state(self):
        """Sidebar clicks should drop items when in DROP_INVENTORY state."""
        player = create_test_player()
        potion = create_healing_potion("Drop This")
        player.inventory.add_item(potion)
        
        state_manager = create_mock_state_manager(player, GameStates.DROP_INVENTORY)
        turn_manager = TurnManager(state_manager)
        action_processor = ActionProcessor(state_manager, turn_manager)
        
        with patch('ui.sidebar_interaction.handle_sidebar_click') as mock_handle:
            mock_handle.return_value = {'inventory_index': 0, 'source': 'sidebar_click'}
            action_processor._handle_sidebar_click((50, 20))
        
        # Should drop the item (remove from inventory, add to entities)
        assert potion not in player.inventory.items, "Should drop item"
        assert potion in state_manager.state.entities, "Should be placed on map"


class TestSidebarClickIndexMapping:
    """Test that inventory index mapping is correct between display and storage."""
    
    def test_index_mapping_with_multiple_items_of_different_names(self):
        """Test that clicking the correct item in a sorted list uses that specific item."""
        player = create_test_player()
        player.fighter.hp = 5
        
        # Create potions with different names that will sort differently
        potion_a = create_healing_potion("Apple Potion")
        potion_b = create_healing_potion("Berry Potion")  
        potion_z = create_healing_potion("Zephyr Potion")
        
        # Add in random order
        player.inventory.add_item(potion_z)
        player.inventory.add_item(potion_a)
        player.inventory.add_item(potion_b)
        
        state_manager = create_mock_state_manager(player, GameStates.PLAYERS_TURN)
        turn_manager = TurnManager(state_manager)
        action_processor = ActionProcessor(state_manager, turn_manager)
        
        # Get sorted inventory (Apple, Berry, Zephyr)
        full_sorted = sorted(player.inventory.items, key=lambda i: i.get_display_name().lower())
        assert full_sorted[0].name == "Apple Potion"
        assert full_sorted[1].name == "Berry Potion"
        assert full_sorted[2].name == "Zephyr Potion"
        
        # Click on Berry (index 1)
        with patch('ui.sidebar_interaction.handle_sidebar_click') as mock_handle:
            mock_handle.return_value = {'inventory_index': 1, 'source': 'sidebar_click'}
            action_processor._handle_sidebar_click((50, 20))
        
        # Berry should be consumed, others should remain
        assert potion_b not in player.inventory.items, "Berry Potion should be consumed"
        assert potion_a in player.inventory.items, "Apple Potion should remain"
        assert potion_z in player.inventory.items, "Zephyr Potion should remain"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

