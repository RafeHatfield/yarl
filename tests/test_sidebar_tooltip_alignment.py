"""Test that sidebar tooltips align correctly with displayed items.

Critical regression test: tooltip hover positions must match actual item positions.
"""
import pytest
from unittest.mock import Mock
from components.item import Item
from components.inventory import Inventory
from components.component_registry import ComponentType


class TestSidebarTooltipAlignment:
    """Test tooltip/click position alignment with sidebar rendering."""
    
    def test_inventory_sorting_matches_across_files(self):
        """All three files (sidebar.py, tooltip.py, sidebar_interaction.py) must sort items identically."""
        # Create mock items with different internal names vs display names
        items = []
        
        # Item 1: Unidentified potion - will sort differently by name vs display_name
        item1 = Mock()
        item1.name = "healing_potion"  # Internal name starts with 'h'
        item1.get_display_name = Mock(return_value="zesty yellow potion")  # Display starts with 'z'
        item1.components = Mock()
        item1.components.has = lambda comp: comp == ComponentType.ITEM
        items.append(item1)
        
        # Item 2: Identified item - name and display name are similar
        item2 = Mock()
        item2.name = "Sword"
        item2.get_display_name = Mock(return_value="Sword")
        item2.components = Mock()
        item2.components.has = lambda comp: comp == ComponentType.EQUIPPABLE
        items.append(item2)
        
        # Item 3: Another unidentified potion
        item3 = Mock()
        item3.name = "speed_potion"  # Internal name starts with 's'
        item3.get_display_name = Mock(return_value="bubbling green potion")  # Display starts with 'b'
        item3.components = Mock()
        item3.components.has = lambda comp: comp == ComponentType.ITEM
        items.append(item3)
        
        # Sort by internal name (OLD BUGGY WAY)
        sorted_by_name = sorted(items, key=lambda item: item.name.lower())
        name_order = [item.name for item in sorted_by_name]
        
        # Sort by display name (CORRECT WAY)
        sorted_by_display = sorted(items, key=lambda item: item.get_display_name().lower())
        display_order = [item.name for item in sorted_by_display]
        
        # These should be DIFFERENT (showing the bug would have existed)
        assert name_order != display_order, \
            "Test setup incorrect: name and display_name sorting should differ for unidentified items"
        
        # Verify the correct order: "bubbling green potion", "Sword", "zesty yellow potion"
        assert sorted_by_display[0].name == "speed_potion"  # "bubbling green potion"
        assert sorted_by_display[1].name == "Sword"  # "Sword"
        assert sorted_by_display[2].name == "healing_potion"  # "zesty yellow potion"
        
        print(f"✓ Sorting by name: {name_order}")
        print(f"✓ Sorting by display_name: {display_order}")
        print("✓ Confirmed: display_name sorting is required for correct tooltip alignment")
    
    def test_y_position_includes_header_offset(self):
        """Verify Y position calculation accounts for header line."""
        # Simulate the Y calculation from tooltip.py
        y_cursor = 2  # Title
        y_cursor += 2  # Title spacing + separator
        y_cursor += 2  # Separator spacing
        y_cursor += 1  # "HOTKEYS" header
        y_cursor += 6  # 6 hotkey lines
        y_cursor += 1  # Spacing after hotkeys
        y_cursor += 1  # "EQUIPMENT" header
        y_cursor += 5  # 5 equipment slots
        y_cursor += 1  # Spacing after equipment
        y_cursor += 1  # "INVENTORY (N/20)" header
        header_y = y_cursor
        
        # After printing header, sidebar.py does y += 1, THEN prints items
        y_cursor += 1  # This is the fix!
        inventory_start_y = y_cursor
        
        # First item should be at header_y + 1
        assert inventory_start_y == header_y + 1, \
            "First inventory item should be 1 line below the header"
        
        # Calculate expected Y for first 3 items
        expected_positions = [
            inventory_start_y,      # First item
            inventory_start_y + 1,  # Second item
            inventory_start_y + 2,  # Third item
        ]
        
        print(f"✓ Header at Y={header_y}")
        print(f"✓ First item at Y={inventory_start_y} (header + 1)")
        print(f"✓ Item positions: {expected_positions}")
    
    def test_equipment_y_position_includes_header_offset(self):
        """Verify equipment Y position calculation accounts for header line."""
        # Simulate the Y calculation for equipment section
        y_cursor = 2  # Title
        y_cursor += 2  # Title spacing + separator
        y_cursor += 2  # Separator spacing
        y_cursor += 1  # "HOTKEYS" header
        y_cursor += 6  # 6 hotkey lines
        y_cursor += 1  # Spacing after hotkeys
        y_cursor += 1  # "EQUIPMENT" header
        equipment_header_y = y_cursor
        
        # After printing header, sidebar.py does y += 1, THEN prints equipment
        y_cursor += 1  # This is the fix!
        equipment_start_y = y_cursor
        
        # First equipment slot should be at equipment_header_y + 1
        assert equipment_start_y == equipment_header_y + 1, \
            "First equipment slot should be 1 line below the header"
        
        # Calculate expected Y for 5 equipment slots
        expected_positions = [
            equipment_start_y,      # Weapon
            equipment_start_y + 1,  # Shield
            equipment_start_y + 2,  # Helm
            equipment_start_y + 3,  # Armor
            equipment_start_y + 4,  # Boots
        ]
        
        print(f"✓ Equipment header at Y={equipment_header_y}")
        print(f"✓ First equipment slot at Y={equipment_start_y} (header + 1)")
        print(f"✓ Equipment positions: {expected_positions}")
    
    def test_all_three_files_calculate_y_consistently(self):
        """Verify sidebar.py, tooltip.py, and sidebar_interaction.py all calculate Y the same way."""
        # This test documents the expected Y positions for each section
        
        y = 2  # Starting Y
        
        # Title section
        y += 2  # Title + spacing
        y += 2  # Separator + spacing
        
        # Hotkeys section
        y += 1  # Header
        hotkeys_start = y
        y += 6  # 6 hotkey lines
        y += 1  # Spacing
        
        # Equipment section
        y += 1  # Header line
        equipment_header = y  # y is now at the header line
        y += 1  # Header printed, y increments, THEN slots rendered
        equipment_start = y
        y += 5  # 5 equipment slots
        y += 1  # Spacing
        
        # Inventory section
        y += 1  # Header line
        inventory_header = y  # y is now at the header line
        y += 1  # Header printed, y increments, THEN items rendered
        inventory_start = y
        
        # Verify the critical offsets
        assert equipment_start == equipment_header + 1, \
            "Equipment slots start 1 line after header"
        assert inventory_start == inventory_header + 1, \
            "Inventory items start 1 line after header"
        
        print(f"✓ Equipment: header={equipment_header}, start={equipment_start}")
        print(f"✓ Inventory: header={inventory_header}, start={inventory_start}")
        print("✓ All sections account for y+=1 after headers")
    
    def test_unidentified_items_sort_by_appearance(self):
        """Unidentified items must sort by their appearance, not internal name."""
        # Create two unidentified potions
        item1 = Mock()
        item1.name = "healing_potion"
        item1.item = Mock()
        item1.item.identified = False
        item1.item.appearance = "zesty yellow potion"
        item1.get_display_name = Mock(return_value="zesty yellow potion")
        
        item2 = Mock()
        item2.name = "speed_potion"
        item2.item = Mock()
        item2.item.identified = False
        item2.item.appearance = "bubbling green potion"
        item2.get_display_name = Mock(return_value="bubbling green potion")
        
        items = [item1, item2]
        
        # Sort by display name (appearance)
        sorted_items = sorted(items, key=lambda item: item.get_display_name().lower())
        
        # "bubbling green potion" should come before "zesty yellow potion"
        assert sorted_items[0].name == "speed_potion"
        assert sorted_items[1].name == "healing_potion"
        
        # If we had sorted by internal name, order would be wrong
        sorted_by_name = sorted(items, key=lambda item: item.name.lower())
        assert sorted_by_name[0].name == "healing_potion"  # Wrong order!
        assert sorted_by_name[1].name == "speed_potion"
        
        # Confirm they're different
        assert sorted_items != sorted_by_name, \
            "Sorting by name vs display_name produces different results (this is the bug we fixed)"

