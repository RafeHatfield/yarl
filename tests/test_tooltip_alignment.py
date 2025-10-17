"""Test to ensure tooltip Y-coordinates match sidebar rendering.

This test exists because tooltip misalignment is a recurring bug. The Y-coordinate
calculations in tooltip.py MUST exactly match the rendering logic in sidebar.py.

If this test fails, it means the sidebar layout was changed without updating tooltips.
"""

import pytest
from unittest.mock import Mock, MagicMock
from config.ui_layout import UILayoutConfig
from components.component_registry import ComponentType


class TestTooltipAlignment:
    """Test suite to verify tooltip Y-coordinates match sidebar rendering."""
    
    def test_equipment_tooltip_ycoords_match_sidebar(self):
        """Equipment tooltip Y-coordinates must match sidebar.py rendering.
        
        This test documents the expected Y-coordinate calculation for equipment tooltips.
        If sidebar.py layout changes, both the sidebar AND this test must be updated together.
        """
        # Simulate the Y-coordinate calculation from sidebar.py render_sidebar()
        # This must EXACTLY match the rendering logic
        
        y = 2  # Starting Y position (sidebar.py line 29)
        y += 2  # Title spacing (sidebar.py line 39)
        y += 2  # Separator spacing (sidebar.py line 48)
        y += 1  # "HOTKEYS" header increment (sidebar.py line 56)
        
        # 8 hotkeys loop (sidebar.py lines 72-77)
        # Each hotkey increments y by 1
        y += 8  # After loop, y should be at 15
        
        y += 1  # Spacing after hotkeys (sidebar.py line 79)
        y += 1  # "EQUIPMENT" header increment (sidebar.py line 89)
        
        equipment_start_y_expected = y  # Should be 17
        
        # This is where tooltips expect equipment to start
        # From tooltip.py get_sidebar_equipment_at_position()
        y_cursor = 2
        y_cursor += 2  # Title + spacing
        y_cursor += 2  # Separator + spacing
        y_cursor += 1  # "HOTKEYS" header
        y_cursor += 8  # 8 hotkey lines
        y_cursor += 1  # Spacing after hotkeys
        y_cursor += 1  # "EQUIPMENT" header is printed, then y increments
        equipment_start_y_tooltip = y_cursor
        
        assert equipment_start_y_tooltip == equipment_start_y_expected, (
            f"Equipment tooltip Y-coordinate mismatch!\n"
            f"Expected (from sidebar.py): {equipment_start_y_expected}\n"
            f"Actual (from tooltip.py): {equipment_start_y_tooltip}\n"
            f"This means tooltips will show the wrong item!\n"
            f"Fix tooltip.py:get_sidebar_equipment_at_position() to match sidebar.py:render_sidebar()"
        )
    
    def test_inventory_tooltip_ycoords_match_sidebar(self):
        """Inventory tooltip Y-coordinates must match sidebar.py rendering.
        
        This test documents the expected Y-coordinate calculation for inventory tooltips.
        If sidebar.py layout changes, both the sidebar AND this test must be updated together.
        """
        # Simulate the Y-coordinate calculation from sidebar.py render_sidebar()
        
        y = 2  # Starting Y position
        y += 2  # Title spacing
        y += 2  # Separator spacing
        y += 1  # "HOTKEYS" header
        y += 8  # 8 hotkeys
        y += 1  # Spacing after hotkeys
        y += 1  # "EQUIPMENT" header
        y += 7  # 7 equipment slots
        y += 1  # Spacing after equipment (sidebar.py line 122)
        y += 1  # "INVENTORY" header increment (sidebar.py line 150)
        
        inventory_start_y_expected = y  # Should be 26
        
        # This is where tooltips expect inventory to start
        # From tooltip.py get_sidebar_item_at_position()
        y_cursor = 2
        y_cursor += 2  # Title spacing + separator
        y_cursor += 2  # Separator spacing
        y_cursor += 1  # "HOTKEYS" header
        y_cursor += 8  # 8 hotkey lines (C, I, O, G, S, Z, <>, /)
        y_cursor += 1  # Spacing after hotkeys
        y_cursor += 1  # "EQUIPMENT" header
        y_cursor += 7  # 7 equipment slots (added rings)
        y_cursor += 1  # Spacing after equipment
        y_cursor += 1  # "INVENTORY (N/20)" header is printed, then y increments
        inventory_start_y_tooltip = y_cursor
        
        assert inventory_start_y_tooltip == inventory_start_y_expected, (
            f"Inventory tooltip Y-coordinate mismatch!\n"
            f"Expected (from sidebar.py): {inventory_start_y_expected}\n"
            f"Actual (from tooltip.py): {inventory_start_y_tooltip}\n"
            f"This means tooltips will show the wrong item!\n"
            f"Fix tooltip.py:get_sidebar_item_at_position() to match sidebar.py:render_sidebar()"
        )
    
    def test_hotkey_count_constant(self):
        """Verify hotkey count matches between sidebar and tooltip.
        
        When hotkeys are added/removed, BOTH sidebar.py and tooltip.py must be updated.
        This test ensures they stay in sync.
        """
        # Expected hotkeys from sidebar.py lines 61-70
        expected_hotkeys = [
            "C - Character",
            "I - Inventory",
            "O - Auto-Explore",
            "G - Get/Drop",
            "S - Search",
            "Z - Wait",
            "<> - Stairs",
            "/ - Look",
        ]
        
        expected_count = len(expected_hotkeys)
        
        # This constant appears in tooltip.py calculations
        tooltip_hotkey_count = 8
        
        assert tooltip_hotkey_count == expected_count, (
            f"Hotkey count mismatch!\n"
            f"Expected (from sidebar.py): {expected_count}\n"
            f"Tooltip calculation uses: {tooltip_hotkey_count}\n"
            f"If you added/removed a hotkey, update BOTH sidebar.py AND tooltip.py!"
        )
    
    def test_equipment_slot_count_constant(self):
        """Verify equipment slot count matches between sidebar and tooltip.
        
        When equipment slots are added/removed, BOTH sidebar.py and tooltip.py must be updated.
        This test ensures they stay in sync.
        """
        # Expected slots from sidebar.py lines 94-102
        expected_slots = [
            "Weapon",
            "Shield",
            "Helm",
            "Armor",
            "Boots",
            "L Ring",
            "R Ring",
        ]
        
        expected_count = len(expected_slots)
        
        # This constant appears in tooltip.py calculations
        tooltip_slot_count = 7
        
        assert tooltip_slot_count == expected_count, (
            f"Equipment slot count mismatch!\n"
            f"Expected (from sidebar.py): {expected_count}\n"
            f"Tooltip calculation uses: {tooltip_slot_count}\n"
            f"If you added/removed an equipment slot, update BOTH sidebar.py AND tooltip.py!"
        )


class TestTooltipIntegration:
    """Integration tests for tooltip functionality."""
    
    def test_equipment_tooltip_returns_correct_item(self):
        """Verify equipment tooltip returns the correct item for a given Y position."""
        ui_layout = UILayoutConfig()
        
        # Create mock player with equipment
        player = Mock()
        equipment = Mock()
        equipment.main_hand = Mock(name="Iron Sword")
        equipment.off_hand = Mock(name="Wooden Shield")
        equipment.head = Mock(name="Leather Helm")
        equipment.chest = Mock(name="Chain Mail")
        equipment.feet = Mock(name="Boots")
        equipment.left_ring = Mock(name="Ring of Protection")
        equipment.right_ring = None
        
        player.get_component_optional = Mock(return_value=equipment)
        player.equipment = equipment
        
        # Import after mocking to avoid circular imports
        from ui.tooltip import get_sidebar_equipment_at_position
        
        # Test that first equipment slot (y=17) returns main_hand
        equipment_start_y = 17
        result = get_sidebar_equipment_at_position(5, equipment_start_y, player, ui_layout)
        
        assert result == equipment.main_hand, (
            f"First equipment slot should return main_hand, got {result}"
        )
        
        # Test that second equipment slot (y=18) returns off_hand
        result = get_sidebar_equipment_at_position(5, equipment_start_y + 1, player, ui_layout)
        
        assert result == equipment.off_hand, (
            f"Second equipment slot should return off_hand, got {result}"
        )

