"""Centralized sidebar layout calculations.

This module provides a single source of truth for sidebar Y-coordinate calculations,
ensuring that rendering, click detection, and tooltips all stay synchronized.
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class SidebarLayoutPositions:
    """Y-coordinate positions for all sidebar sections.
    
    All positions are calculated dynamically based on actual item counts,
    preventing off-by-one errors when the sidebar layout changes.
    """
    # Section start positions
    title_y: int
    separator_y: int
    hotkeys_header_y: int
    hotkeys_start_y: int
    equipment_header_y: int
    equipment_start_y: int
    inventory_header_y: int
    inventory_start_y: int
    
    # Section sizes (for validation)
    hotkey_count: int
    equipment_slot_count: int


def calculate_sidebar_layout(hotkey_count: int = 7, equipment_slot_count: int = 7) -> SidebarLayoutPositions:
    """Calculate Y-coordinate positions for all sidebar sections.
    
    This is the single source of truth for sidebar layout calculations.
    All other modules (sidebar.py, sidebar_interaction.py, tooltip.py) should
    use this function to get consistent Y positions.
    
    Args:
        hotkey_count: Number of hotkey lines to render (default: 7)
        equipment_slot_count: Number of equipment slots (default: 7)
        
    Returns:
        SidebarLayoutPositions with all calculated Y coordinates
    """
    y = 2  # Starting Y position
    
    # Title section
    title_y = y
    y += 1  # Title line
    y += 1  # Spacing after title
    
    # Separator
    separator_y = y
    y += 1  # Separator line
    y += 1  # Spacing after separator
    
    # Hotkeys section
    hotkeys_header_y = y
    y += 1  # "HOTKEYS" header
    hotkeys_start_y = y
    y += hotkey_count  # All hotkey lines
    y += 1  # Spacing after hotkeys
    
    # Equipment section
    equipment_header_y = y
    y += 1  # "EQUIPMENT" header
    equipment_start_y = y
    y += equipment_slot_count  # All equipment slots
    y += 1  # Spacing after equipment
    
    # Inventory section
    inventory_header_y = y
    y += 1  # "INVENTORY (N/20)" header
    inventory_start_y = y
    # (inventory items extend downward from here based on item count)
    
    return SidebarLayoutPositions(
        title_y=title_y,
        separator_y=separator_y,
        hotkeys_header_y=hotkeys_header_y,
        hotkeys_start_y=hotkeys_start_y,
        equipment_header_y=equipment_header_y,
        equipment_start_y=equipment_start_y,
        inventory_header_y=inventory_header_y,
        inventory_start_y=inventory_start_y,
        hotkey_count=hotkey_count,
        equipment_slot_count=equipment_slot_count,
    )


def get_hotkey_list() -> List[Tuple[str, bool]]:
    """Get the canonical list of hotkeys displayed in the sidebar.
    
    Returns:
        List of (hotkey_text, is_context_aware) tuples
        is_context_aware=True means the action depends on game state
    """
    return [
        ("C - Character", False),
        ("I - Inventory", False),
        ("O - Auto-Explore", False),
        ("G - Get/Drop", True),   # Context-aware
        ("S - Search", False),
        ("Z - Wait", False),
        ("Enter - Stairs", True),  # Context-aware
    ]


def get_equipment_slot_list() -> List[str]:
    """Get the canonical list of equipment slots displayed in the sidebar.
    
    Returns:
        List of equipment slot names in display order
    """
    return [
        "main_hand",
        "off_hand",
        "head",
        "chest",
        "feet",
        "left_ring",
        "right_ring",
    ]

