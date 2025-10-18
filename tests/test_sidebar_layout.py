"""Tests for centralized sidebar layout calculations.

These tests ensure that:
1. Layout calculations are consistent and correct
2. Adding/removing hotkeys updates all positions correctly
3. Adding/removing equipment slots updates all positions correctly
4. All three modules (rendering, interaction, tooltips) stay in sync
"""

import pytest
from ui.sidebar_layout import (
    calculate_sidebar_layout,
    get_hotkey_list,
    get_equipment_slot_list,
    SidebarLayoutPositions
)


class TestSidebarLayoutCalculations:
    """Test the centralized layout calculation function."""
    
    def test_calculate_sidebar_layout_returns_correct_type(self):
        """Layout calculator should return a SidebarLayoutPositions object."""
        layout = calculate_sidebar_layout()
        assert isinstance(layout, SidebarLayoutPositions)
    
    def test_layout_positions_are_sequential(self):
        """All Y positions should be in ascending order (no overlaps)."""
        layout = calculate_sidebar_layout(hotkey_count=7, equipment_slot_count=7)
        
        # Check that positions are in order
        assert layout.title_y < layout.separator_y
        assert layout.separator_y < layout.hotkeys_header_y
        assert layout.hotkeys_header_y < layout.hotkeys_start_y
        assert layout.hotkeys_start_y < layout.equipment_header_y
        assert layout.equipment_header_y < layout.equipment_start_y
        assert layout.equipment_start_y < layout.inventory_header_y
        assert layout.inventory_header_y < layout.inventory_start_y
    
    def test_hotkey_section_size_matches_count(self):
        """Hotkey section should have correct spacing based on count."""
        layout_7 = calculate_sidebar_layout(hotkey_count=7, equipment_slot_count=7)
        layout_5 = calculate_sidebar_layout(hotkey_count=5, equipment_slot_count=7)
        
        # With 2 fewer hotkeys, equipment section should start 2 lines earlier
        assert layout_5.equipment_header_y == layout_7.equipment_header_y - 2
        assert layout_5.equipment_start_y == layout_7.equipment_start_y - 2
        assert layout_5.inventory_header_y == layout_7.inventory_header_y - 2
        assert layout_5.inventory_start_y == layout_7.inventory_start_y - 2
    
    def test_equipment_section_size_matches_count(self):
        """Equipment section should have correct spacing based on count."""
        layout_7 = calculate_sidebar_layout(hotkey_count=7, equipment_slot_count=7)
        layout_5 = calculate_sidebar_layout(hotkey_count=7, equipment_slot_count=5)
        
        # With 2 fewer equipment slots, inventory section should start 2 lines earlier
        assert layout_5.inventory_header_y == layout_7.inventory_header_y - 2
        assert layout_5.inventory_start_y == layout_7.inventory_start_y - 2
        
        # Hotkey positions should be unchanged
        assert layout_5.hotkeys_start_y == layout_7.hotkeys_start_y
        assert layout_5.equipment_header_y == layout_7.equipment_header_y
    
    def test_layout_stores_counts_correctly(self):
        """Layout should store the hotkey and equipment counts."""
        layout = calculate_sidebar_layout(hotkey_count=10, equipment_slot_count=5)
        
        assert layout.hotkey_count == 10
        assert layout.equipment_slot_count == 5
    
    def test_default_layout_uses_current_game_values(self):
        """Default layout should match current game configuration."""
        hotkeys = get_hotkey_list()
        slots = get_equipment_slot_list()
        layout = calculate_sidebar_layout()
        
        # Should match the default parameter values (7 hotkeys, 7 equipment slots)
        assert layout.hotkey_count == 7
        assert layout.equipment_slot_count == 7


class TestHotkeyList:
    """Test the canonical hotkey list."""
    
    def test_get_hotkey_list_returns_list(self):
        """Should return a list of tuples."""
        hotkeys = get_hotkey_list()
        assert isinstance(hotkeys, list)
        assert len(hotkeys) > 0
        
        for hotkey_text, is_context_aware in hotkeys:
            assert isinstance(hotkey_text, str)
            assert isinstance(is_context_aware, bool)
    
    def test_get_hotkey_list_has_correct_count(self):
        """Should return 7 hotkeys (current game configuration)."""
        hotkeys = get_hotkey_list()
        assert len(hotkeys) == 7
    
    def test_get_hotkey_list_contains_expected_hotkeys(self):
        """Should contain all expected hotkeys in order."""
        hotkeys = get_hotkey_list()
        hotkey_texts = [text for text, _ in hotkeys]
        
        expected = [
            "C - Character",
            "I - Inventory",
            "O - Auto-Explore",
            "G - Get/Drop",
            "S - Search",
            "Z - Wait",
            "Enter - Stairs",
        ]
        
        assert hotkey_texts == expected
    
    def test_context_aware_flags_are_correct(self):
        """Context-aware hotkeys should be marked correctly."""
        hotkeys = get_hotkey_list()
        hotkey_dict = {text: is_context_aware for text, is_context_aware in hotkeys}
        
        # Get/Drop and Stairs are context-aware
        assert hotkey_dict["G - Get/Drop"] is True
        assert hotkey_dict["Enter - Stairs"] is True
        
        # All others are not context-aware
        assert hotkey_dict["C - Character"] is False
        assert hotkey_dict["I - Inventory"] is False
        assert hotkey_dict["O - Auto-Explore"] is False
        assert hotkey_dict["S - Search"] is False
        assert hotkey_dict["Z - Wait"] is False


class TestEquipmentSlotList:
    """Test the canonical equipment slot list."""
    
    def test_get_equipment_slot_list_returns_list(self):
        """Should return a list of slot names."""
        slots = get_equipment_slot_list()
        assert isinstance(slots, list)
        assert len(slots) > 0
        
        for slot_name in slots:
            assert isinstance(slot_name, str)
    
    def test_get_equipment_slot_list_has_correct_count(self):
        """Should return 7 equipment slots (current game configuration)."""
        slots = get_equipment_slot_list()
        assert len(slots) == 7
    
    def test_get_equipment_slot_list_contains_expected_slots(self):
        """Should contain all expected equipment slots in order."""
        slots = get_equipment_slot_list()
        
        expected = [
            "main_hand",
            "off_hand",
            "head",
            "chest",
            "feet",
            "left_ring",
            "right_ring",
        ]
        
        assert slots == expected
    
    def test_equipment_slot_names_are_valid_attributes(self):
        """All slot names should be valid equipment component attributes."""
        from components.equipment import Equipment
        from entity import Entity
        
        # Create a test entity with equipment
        test_entity = Entity(0, 0, '@', (255, 255, 255), "Test", blocks=True)
        test_equipment = Equipment()
        
        slots = get_equipment_slot_list()
        
        # All slot names should be valid attributes on Equipment
        for slot_name in slots:
            assert hasattr(test_equipment, slot_name), \
                f"Equipment component missing attribute: {slot_name}"


class TestLayoutConsistency:
    """Test that layout calculations remain consistent across changes."""
    
    def test_adding_hotkey_shifts_all_below_sections(self):
        """Adding a hotkey should shift equipment and inventory down by 1."""
        layout_before = calculate_sidebar_layout(hotkey_count=7, equipment_slot_count=7)
        layout_after = calculate_sidebar_layout(hotkey_count=8, equipment_slot_count=7)
        
        # Equipment section should shift down by 1
        assert layout_after.equipment_header_y == layout_before.equipment_header_y + 1
        assert layout_after.equipment_start_y == layout_before.equipment_start_y + 1
        
        # Inventory section should also shift down by 1
        assert layout_after.inventory_header_y == layout_before.inventory_header_y + 1
        assert layout_after.inventory_start_y == layout_before.inventory_start_y + 1
        
        # Hotkey section should not change its start position
        assert layout_after.hotkeys_start_y == layout_before.hotkeys_start_y
    
    def test_adding_equipment_slot_shifts_inventory_only(self):
        """Adding an equipment slot should only shift inventory down by 1."""
        layout_before = calculate_sidebar_layout(hotkey_count=7, equipment_slot_count=7)
        layout_after = calculate_sidebar_layout(hotkey_count=7, equipment_slot_count=8)
        
        # Inventory section should shift down by 1
        assert layout_after.inventory_header_y == layout_before.inventory_header_y + 1
        assert layout_after.inventory_start_y == layout_before.inventory_start_y + 1
        
        # Hotkey and equipment sections should not change their start positions
        assert layout_after.hotkeys_start_y == layout_before.hotkeys_start_y
        assert layout_after.equipment_start_y == layout_before.equipment_start_y
    
    def test_removing_hotkey_shifts_all_below_sections_up(self):
        """Removing a hotkey should shift equipment and inventory up by 1."""
        layout_before = calculate_sidebar_layout(hotkey_count=7, equipment_slot_count=7)
        layout_after = calculate_sidebar_layout(hotkey_count=6, equipment_slot_count=7)
        
        # Equipment section should shift up by 1
        assert layout_after.equipment_header_y == layout_before.equipment_header_y - 1
        assert layout_after.equipment_start_y == layout_before.equipment_start_y - 1
        
        # Inventory section should also shift up by 1
        assert layout_after.inventory_header_y == layout_before.inventory_header_y - 1
        assert layout_after.inventory_start_y == layout_before.inventory_start_y - 1


class TestRegressionPrevention:
    """Tests to prevent specific bugs we've encountered."""
    
    def test_hotkey_count_matches_actual_hotkey_list(self):
        """Default hotkey count should match the actual hotkey list length.
        
        This prevents the bug where we had 7 hotkeys but were calculating for 8.
        """
        hotkeys = get_hotkey_list()
        layout = calculate_sidebar_layout()
        
        assert layout.hotkey_count == len(hotkeys), \
            f"Layout hotkey_count ({layout.hotkey_count}) doesn't match actual hotkey list length ({len(hotkeys)})"
    
    def test_equipment_slot_count_matches_actual_slot_list(self):
        """Default equipment slot count should match the actual slot list length."""
        slots = get_equipment_slot_list()
        layout = calculate_sidebar_layout()
        
        assert layout.equipment_slot_count == len(slots), \
            f"Layout equipment_slot_count ({layout.equipment_slot_count}) doesn't match actual slot list length ({len(slots)})"
    
    def test_no_overlapping_sections(self):
        """Ensure no sections overlap (minimum 1 line spacing).
        
        This prevents bugs where clickable areas overlap.
        """
        layout = calculate_sidebar_layout()
        
        # Hotkeys end at: hotkeys_start_y + hotkey_count
        hotkeys_end = layout.hotkeys_start_y + layout.hotkey_count
        
        # Equipment header must be at least 1 line after hotkeys end
        assert layout.equipment_header_y >= hotkeys_end + 1
        
        # Equipment slots end at: equipment_start_y + equipment_slot_count
        equipment_end = layout.equipment_start_y + layout.equipment_slot_count
        
        # Inventory header must be at least 1 line after equipment ends
        assert layout.inventory_header_y >= equipment_end + 1

