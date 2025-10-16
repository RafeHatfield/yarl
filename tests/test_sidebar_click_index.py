"""Tests for sidebar click index calculation.

This test ensures that clicking on an item in the sidebar correctly identifies
the item being clicked on, especially for the drop action.

Regression test for bug where clicking to drop would drop the item ABOVE the
one clicked on.
"""

import pytest
from unittest.mock import Mock, MagicMock
from entity import Entity
from components.inventory import Inventory
from components.equipment import Equipment
from components.fighter import Fighter
from components.component_registry import ComponentType
from ui.sidebar_interaction import handle_sidebar_click
from config.ui_layout import UILayoutConfig


def create_test_player_with_items(item_names):
    """Create a player with a list of items in inventory.
    
    Args:
        item_names: List of item names to add to inventory
        
    Returns:
        Player entity with items
    """
    # Create player with inventory
    fighter = Fighter(hp=30, defense=2, power=5)
    inventory = Inventory(25)  # Default capacity
    equipment = Equipment()
    
    player = Entity(
        x=0, y=0, char='@', color=(255, 255, 255), name='Player',
        blocks=True, fighter=fighter, inventory=inventory, equipment=equipment
    )
    
    # Add items to inventory
    for i, item_name in enumerate(item_names):
        from components.item import Item
        item_entity = Entity(
            x=0, y=0, char='!', color=(255, 0, 0), name=item_name,
            item=Item()
        )
        item_entity.item.owner = item_entity
        player.inventory.items.append(item_entity)
    
    return player


def test_sidebar_click_first_inventory_item():
    """Test clicking on the first item in inventory."""
    player = create_test_player_with_items(['Apple', 'Banana', 'Cherry'])
    ui_layout = UILayoutConfig()
    
    # Calculate where the first inventory item should be:
    # Y positions (matching sidebar.py):
    # 2: Title
    # 4: Separator
    # 6: HOTKEYS header
    # 7-13: 7 hotkey lines (C, I, O, G, Z, <>, /)
    # 14: Spacing
    # 15: EQUIPMENT header
    # 16-22: 7 equipment slots
    # 23: Spacing
    # 24: INVENTORY header
    # 25: First inventory item
    
    first_item_y = 25
    click_x = 5  # Within sidebar padding
    
    result = handle_sidebar_click(click_x, first_item_y, player, ui_layout)
    
    assert result is not None, "Should detect click on first item"
    assert result['inventory_index'] == 0, "Should return index 0 for first item (Apple)"


def test_sidebar_click_second_inventory_item():
    """Test clicking on the second item in inventory."""
    player = create_test_player_with_items(['Apple', 'Banana', 'Cherry'])
    ui_layout = UILayoutConfig()
    
    second_item_y = 26  # First item at 25, second at 26
    click_x = 5
    
    result = handle_sidebar_click(click_x, second_item_y, player, ui_layout)
    
    assert result is not None, "Should detect click on second item"
    assert result['inventory_index'] == 1, "Should return index 1 for second item (Banana)"


def test_sidebar_click_third_inventory_item():
    """Test clicking on the third item in inventory."""
    player = create_test_player_with_items(['Apple', 'Banana', 'Cherry'])
    ui_layout = UILayoutConfig()
    
    third_item_y = 27  # First item at 25, third at 27
    click_x = 5
    
    result = handle_sidebar_click(click_x, third_item_y, player, ui_layout)
    
    assert result is not None, "Should detect click on third item"
    assert result['inventory_index'] == 2, "Should return index 2 for third item (Cherry)"


def test_sidebar_click_respects_alphabetical_sorting():
    """Test that clicking respects alphabetical sorting of inventory."""
    # Items added in this order, but will be sorted: Apple, Cherry, Zebra
    player = create_test_player_with_items(['Zebra', 'Apple', 'Cherry'])
    ui_layout = UILayoutConfig()
    
    first_item_y = 25
    second_item_y = 26
    third_item_y = 27
    click_x = 5
    
    # First displayed item should be "Apple" (index 1 in original list, index 0 in sorted)
    result = handle_sidebar_click(click_x, first_item_y, player, ui_layout)
    assert result is not None
    # The result should give us the index into the sorted list
    assert result['inventory_index'] == 0, "First displayed item is Apple"
    
    # Second displayed item should be "Cherry"
    result = handle_sidebar_click(click_x, second_item_y, player, ui_layout)
    assert result is not None
    assert result['inventory_index'] == 1, "Second displayed item is Cherry"
    
    # Third displayed item should be "Zebra"
    result = handle_sidebar_click(click_x, third_item_y, player, ui_layout)
    assert result is not None
    assert result['inventory_index'] == 2, "Third displayed item is Zebra"


def test_sidebar_click_excludes_equipped_items():
    """Test that equipped items are not included in inventory click detection."""
    player = create_test_player_with_items(['Apple', 'Banana', 'Sword'])
    ui_layout = UILayoutConfig()
    
    # Equip the sword
    sword = player.inventory.items[2]
    from components.equippable import Equippable
    from equipment_slots import EquipmentSlots
    sword.equippable = Equippable(slot=EquipmentSlots.MAIN_HAND)
    player.equipment.main_hand = sword
    
    # Now only Apple and Banana should be clickable in inventory
    # First item (Apple) at y=25
    first_item_y = 25
    click_x = 5
    
    result = handle_sidebar_click(click_x, first_item_y, player, ui_layout)
    assert result is not None
    assert result['inventory_index'] == 0, "First unequipped item is Apple"
    
    # Second item (Banana) at y=26
    second_item_y = 26
    result = handle_sidebar_click(click_x, second_item_y, player, ui_layout)
    assert result is not None
    assert result['inventory_index'] == 1, "Second unequipped item is Banana"
    
    # Third position (y=27) should have no item since Sword is equipped
    third_item_y = 27
    result = handle_sidebar_click(click_x, third_item_y, player, ui_layout)
    assert result is None, "No third item since Sword is equipped"

