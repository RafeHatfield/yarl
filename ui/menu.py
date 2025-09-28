"""Menu UI component implementation.

This module provides the Menu class, which displays a list of selectable
options and handles navigation and selection. Menus support keyboard
navigation, mouse interaction, and customizable styling.
"""

from typing import List, Optional, Callable, Any, Union
from dataclasses import dataclass

from rendering import Surface, Color, Colors
from rendering.surface import Rect
from .component import Component, ComponentState, ComponentStyle
from .events import UIEvent, UIEventType


@dataclass
class MenuItem:
    """Represents a single menu item.
    
    Attributes:
        text (str): Display text for the item
        value (Any): Associated value/data for the item
        enabled (bool): Whether the item can be selected
        separator (bool): Whether this is a separator line
    """
    text: str
    value: Any = None
    enabled: bool = True
    separator: bool = False
    
    def __post_init__(self):
        """Initialize default values."""
        if self.value is None:
            self.value = self.text


class MenuStyle(ComponentStyle):
    """Extended style configuration for menus."""
    
    def __init__(self, **kwargs):
        # Set menu-specific defaults
        defaults = {
            'fg_color': Colors.TEXT_DEFAULT,
            'bg_color': Color(48, 48, 48),
            'border_color': Colors.TEXT_DISABLED,
            'hover_fg_color': Colors.TEXT_HIGHLIGHT,
            'hover_bg_color': Color(80, 80, 80),
            'disabled_fg_color': Colors.TEXT_DISABLED,
        }
        
        # Override with provided values
        for key, value in kwargs.items():
            if hasattr(ComponentStyle, key):
                defaults[key] = value
        
        super().__init__(**defaults)


class Menu(Component):
    """Selectable menu component.
    
    The Menu component displays a list of options that users can navigate
    through and select using keyboard or mouse input. It supports various
    interaction patterns and styling options.
    
    Features:
    - Keyboard navigation (arrow keys, Enter, Escape)
    - Mouse selection and hovering
    - Disabled items and separators
    - Customizable item display
    - Selection callbacks and events
    - Automatic sizing based on content
    """
    
    def __init__(self, x: int = 0, y: int = 0, width: int = 20, height: int = 10,
                 items: Optional[List[Union[str, MenuItem]]] = None,
                 visible: bool = True, enabled: bool = True,
                 style: Optional[MenuStyle] = None,
                 on_select: Optional[Callable[['Menu', int, MenuItem], None]] = None):
        """Initialize the menu.
        
        Args:
            x (int): X position
            y (int): Y position
            width (int): Menu width
            height (int): Menu height
            items (List[Union[str, MenuItem]], optional): Menu items
            visible (bool): Whether menu is visible
            enabled (bool): Whether menu is enabled
            style (MenuStyle, optional): Menu styling
            on_select (Callable, optional): Selection event handler
        """
        super().__init__(x, y, width, height, visible, enabled, style or MenuStyle())
        
        self.items: List[MenuItem] = []
        self.selected_index = -1
        self.scroll_offset = 0
        self._on_select = on_select
        
        # Set items if provided
        if items:
            self.set_items(items)
        
        # Calculate initial size
        self._update_size()
    
    @property
    def selected_item(self) -> Optional[MenuItem]:
        """Get the currently selected menu item.
        
        Returns:
            MenuItem: Selected item, or None if no selection
        """
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None
    
    @property
    def visible_item_count(self) -> int:
        """Get the number of items that can be displayed at once.
        
        Returns:
            int: Number of visible items
        """
        border_height = 2 if self.style.border_color else 0
        return max(1, self.height - border_height)
    
    def set_items(self, items: List[Union[str, MenuItem]]) -> None:
        """Set the menu items.
        
        Args:
            items (List[Union[str, MenuItem]]): List of items (strings or MenuItem objects)
        """
        self.items = []
        for item in items:
            if isinstance(item, str):
                self.items.append(MenuItem(item))
            else:
                self.items.append(item)
        
        # Reset selection
        self.selected_index = -1
        self.scroll_offset = 0
        
        # Find first selectable item
        self._find_next_selectable(0)
        
        self._update_size()
        self.mark_dirty()
    
    def add_item(self, item: Union[str, MenuItem]) -> None:
        """Add a single item to the menu.
        
        Args:
            item (Union[str, MenuItem]): Item to add
        """
        if isinstance(item, str):
            self.items.append(MenuItem(item))
        else:
            self.items.append(item)
        
        self._update_size()
        self.mark_dirty()
    
    def add_separator(self) -> None:
        """Add a separator line to the menu."""
        self.items.append(MenuItem("─" * (self.width - 2), separator=True, enabled=False))
        self.mark_dirty()
    
    def remove_item(self, index: int) -> None:
        """Remove an item by index.
        
        Args:
            index (int): Index of item to remove
        """
        if 0 <= index < len(self.items):
            self.items.pop(index)
            
            # Adjust selection
            if self.selected_index >= index:
                self.selected_index -= 1
            
            # Ensure valid selection
            if self.selected_index >= len(self.items):
                self.selected_index = len(self.items) - 1
            
            self._update_size()
            self.mark_dirty()
    
    def clear_items(self) -> None:
        """Remove all items from the menu."""
        self.items.clear()
        self.selected_index = -1
        self.scroll_offset = 0
        self._update_size()
        self.mark_dirty()
    
    def set_selection(self, index: int) -> None:
        """Set the selected item by index.
        
        Args:
            index (int): Index to select (-1 for no selection)
        """
        if index == -1:
            self.selected_index = -1
        elif 0 <= index < len(self.items) and self.items[index].enabled:
            self.selected_index = index
            self._ensure_visible(index)
        
        self.mark_dirty()
    
    def select_item(self, item: MenuItem) -> None:
        """Select an item by reference.
        
        Args:
            item (MenuItem): Item to select
        """
        try:
            index = self.items.index(item)
            self.set_selection(index)
        except ValueError:
            pass  # Item not found
    
    def _update_size(self) -> None:
        """Update menu size based on content."""
        if not self.items:
            return
        
        # Calculate required width
        max_text_width = max(len(item.text) for item in self.items)
        border_width = 2 if self.style.border_color else 0
        required_width = max_text_width + border_width
        
        if required_width > self.width:
            self.width = required_width
        
        # Height is typically set by the caller, but we could auto-size here too
    
    def _find_next_selectable(self, start_index: int, direction: int = 1) -> bool:
        """Find the next selectable item.
        
        Args:
            start_index (int): Starting index
            direction (int): Search direction (1 for forward, -1 for backward)
            
        Returns:
            bool: True if a selectable item was found
        """
        if not self.items:
            return False
        
        index = start_index
        for _ in range(len(self.items)):
            if 0 <= index < len(self.items):
                item = self.items[index]
                if item.enabled and not item.separator:
                    self.selected_index = index
                    self._ensure_visible(index)
                    return True
            
            index = (index + direction) % len(self.items)
        
        return False
    
    def _ensure_visible(self, index: int) -> None:
        """Ensure the specified item is visible by adjusting scroll offset.
        
        Args:
            index (int): Item index to make visible
        """
        visible_count = self.visible_item_count
        
        if index < self.scroll_offset:
            self.scroll_offset = index
        elif index >= self.scroll_offset + visible_count:
            self.scroll_offset = index - visible_count + 1
        
        # Clamp scroll offset
        max_scroll = max(0, len(self.items) - visible_count)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
    
    def _trigger_selection(self) -> None:
        """Trigger selection event for current item."""
        if self.selected_item and self.selected_item.enabled:
            # Emit UI event
            event = UIEvent.menu_item_selected(
                self, self.selected_index, self.selected_item
            )
            self.emit_event('select', event)
            
            # Call direct handler if set
            if self._on_select:
                try:
                    self._on_select(self, self.selected_index, self.selected_item)
                except Exception as e:
                    print(f"Error in menu selection handler: {e}")
    
    def on_mouse_event(self, x: int, y: int, button: int, pressed: bool) -> bool:
        """Handle mouse events.
        
        Args:
            x (int): Mouse X coordinate (relative to menu)
            y (int): Mouse Y coordinate (relative to menu)
            button (int): Mouse button
            pressed (bool): True if pressed, False if released
            
        Returns:
            bool: True if event was handled
        """
        if not self.enabled:
            return False
        
        # Calculate item under mouse
        border_offset = 1 if self.style.border_color else 0
        item_y = y - border_offset
        
        if item_y >= 0 and item_y < self.visible_item_count:
            item_index = self.scroll_offset + item_y
            
            if 0 <= item_index < len(self.items):
                item = self.items[item_index]
                
                if not pressed:  # Mouse release
                    if button == 0 and item.enabled and not item.separator:
                        self.set_selection(item_index)
                        self._trigger_selection()
                        return True
                else:  # Mouse press
                    if item.enabled and not item.separator:
                        self.set_selection(item_index)
                        return True
        
        return True  # Menu consumes all mouse events within its bounds
    
    def on_key_event(self, key: str, pressed: bool) -> bool:
        """Handle keyboard events.
        
        Args:
            key (str): Key identifier
            pressed (bool): True if pressed, False if released
            
        Returns:
            bool: True if event was handled
        """
        if not self.enabled or not pressed:
            return False
        
        key_lower = key.lower()
        
        # Navigation keys
        if key_lower in ('up', 'w'):
            if self.selected_index > 0:
                self._find_next_selectable(self.selected_index - 1, -1)
            else:
                # Wrap to last item
                self._find_next_selectable(len(self.items) - 1, -1)
            self.mark_dirty()
            return True
        
        elif key_lower in ('down', 's'):
            if self.selected_index < len(self.items) - 1:
                self._find_next_selectable(self.selected_index + 1, 1)
            else:
                # Wrap to first item
                self._find_next_selectable(0, 1)
            self.mark_dirty()
            return True
        
        elif key_lower in ('enter', 'return', 'space'):
            self._trigger_selection()
            return True
        
        elif key_lower == 'escape':
            # Clear selection and emit cancel event
            self.selected_index = -1
            self.emit_event('cancel', UIEvent(UIEventType.MENU_CLOSED, self))
            return True
        
        # Letter navigation (select first item starting with letter)
        elif len(key) == 1 and key.isalpha():
            key_upper = key.upper()
            start_index = (self.selected_index + 1) % len(self.items)
            
            for i in range(len(self.items)):
                index = (start_index + i) % len(self.items)
                item = self.items[index]
                
                if (item.enabled and not item.separator and 
                    item.text and item.text[0].upper() == key_upper):
                    self.set_selection(index)
                    self.mark_dirty()
                    return True
        
        return False
    
    def render_self(self, surface: Surface) -> None:
        """Render the menu.
        
        Args:
            surface (Surface): Surface to render to
        """
        abs_rect = self.absolute_rect
        fg_color, bg_color = self.get_style_colors()
        
        # Fill background
        surface.fill_rect(abs_rect, ' ', fg_color, bg_color)
        
        # Draw border if specified
        border_offset = 0
        if self.style.border_color:
            surface.draw_border(abs_rect, self.style.border_color, bg_color)
            border_offset = 1
        
        # Draw items
        visible_count = self.visible_item_count
        for i in range(visible_count):
            item_index = self.scroll_offset + i
            
            if item_index >= len(self.items):
                break
            
            item = self.items[item_index]
            item_y = abs_rect.y + border_offset + i
            item_x = abs_rect.x + border_offset
            
            # Determine colors for this item
            if item_index == self.selected_index and item.enabled:
                item_fg = self.style.hover_fg_color or fg_color
                item_bg = self.style.hover_bg_color or bg_color
            elif not item.enabled:
                item_fg = self.style.disabled_fg_color
                item_bg = bg_color
            else:
                item_fg = fg_color
                item_bg = bg_color
            
            # Draw item background
            item_width = abs_rect.width - 2 * border_offset
            surface.fill_rect(
                Rect(item_x, item_y, item_width, 1),
                ' ', item_fg, item_bg
            )
            
            # Draw item text
            if item.text:
                display_text = item.text
                max_width = item_width
                
                if len(display_text) > max_width:
                    display_text = display_text[:max_width-3] + "..."
                
                surface.print_string(item_x, item_y, display_text, item_fg)
        
        # Draw scroll indicators if needed
        if self.scroll_offset > 0:
            # Up arrow
            surface.set_char(abs_rect.right - 1, abs_rect.y + border_offset, '▲', fg_color)
        
        if self.scroll_offset + visible_count < len(self.items):
            # Down arrow
            surface.set_char(abs_rect.right - 1, abs_rect.bottom - 1 - border_offset, '▼', fg_color)
    
    def __repr__(self) -> str:
        """String representation of menu."""
        return (f"Menu(x={self.x}, y={self.y}, w={self.width}, h={self.height}, "
                f"items={len(self.items)}, selected={self.selected_index})")
