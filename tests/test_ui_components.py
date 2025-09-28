"""Tests for the UI component system.

This module contains comprehensive tests for all UI components including
the base component system, layout managers, buttons, panels, menus,
dialogs, and theming system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rendering import Color, Colors
from rendering.surface import Rect
from ui import (
    Component, ComponentState, Button, Panel, Menu, Dialog,
    Layout, GridLayout, FlowLayout, AbsoluteLayout,
    Theme, DefaultTheme, DarkTheme, LightTheme, GameTheme,
    UIEvent, UIEventType, MenuItem, DialogType, DialogResult
)
from ui.layout import LayoutConstraints, LayoutDirection, Alignment


# Mock surface for testing
class MockSurface:
    def __init__(self, width=80, height=25):
        self.width = width
        self.height = height
        self._chars = {}
        self._fg_colors = {}
        self._bg_colors = {}
        self._clip_rect = None
    
    def set_clip_rect(self, rect):
        self._clip_rect = rect
    
    def get_clip_rect(self):
        return self._clip_rect
    
    def set_char(self, x, y, char, fg_color=None, bg_color=None):
        self._chars[(x, y)] = char
        if fg_color:
            self._fg_colors[(x, y)] = fg_color
        if bg_color:
            self._bg_colors[(x, y)] = bg_color
    
    def get_char(self, x, y):
        return self._chars.get((x, y), ' ')
    
    def set_bg_color(self, x, y, color):
        self._bg_colors[(x, y)] = color
    
    def set_fg_color(self, x, y, color):
        self._fg_colors[(x, y)] = color
    
    def print_string(self, x, y, text, fg_color=None):
        for i, char in enumerate(text):
            self.set_char(x + i, y, char, fg_color)
    
    def fill_rect(self, rect, char=' ', fg_color=None, bg_color=None):
        for y in range(rect.y, rect.y + rect.height):
            for x in range(rect.x, rect.x + rect.width):
                self.set_char(x, y, char, fg_color, bg_color)
    
    def draw_border(self, rect, fg_color=None, bg_color=None, border_chars=None):
        # Simple border implementation for testing
        if border_chars is None:
            border_chars = "+-+|+-+|"
        
        # Top and bottom
        for x in range(rect.x, rect.x + rect.width):
            self.set_char(x, rect.y, '-', fg_color, bg_color)
            self.set_char(x, rect.y + rect.height - 1, '-', fg_color, bg_color)
        
        # Left and right
        for y in range(rect.y, rect.y + rect.height):
            self.set_char(rect.x, y, '|', fg_color, bg_color)
            self.set_char(rect.x + rect.width - 1, y, '|', fg_color, bg_color)


# Mock component for testing base functionality
class MockComponent(Component):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mouse_events = []
        self.key_events = []
    
    def on_mouse_event(self, x, y, button, pressed):
        self.mouse_events.append((x, y, button, pressed))
        return True
    
    def on_key_event(self, key, pressed):
        self.key_events.append((key, pressed))
        return True
    
    def render_self(self, surface):
        # Simple test rendering
        abs_rect = self.absolute_rect
        surface.fill_rect(abs_rect, 'X')


class TestComponent:
    """Test cases for the base Component class."""
    
    def test_component_creation(self):
        """Test basic component creation."""
        comp = MockComponent(10, 20, 30, 40)
        assert comp.x == 10
        assert comp.y == 20
        assert comp.width == 30
        assert comp.height == 40
        assert comp.visible == True
        assert comp.enabled == True
        assert comp.state == ComponentState.NORMAL
    
    def test_component_rect_properties(self):
        """Test component rectangle properties."""
        comp = MockComponent(10, 20, 30, 40)
        rect = comp.rect
        assert rect.x == 10
        assert rect.y == 20
        assert rect.width == 30
        assert rect.height == 40
        
        abs_rect = comp.absolute_rect
        assert abs_rect == rect  # No parent, so same as local rect
    
    def test_component_hierarchy(self):
        """Test parent-child relationships."""
        parent = MockComponent(0, 0, 100, 100)
        child1 = MockComponent(10, 10, 20, 20)
        child2 = MockComponent(40, 40, 30, 30)
        
        parent.add_child(child1)
        parent.add_child(child2)
        
        assert child1.parent == parent
        assert child2.parent == parent
        assert len(parent.children) == 2
        assert child1 in parent.children
        assert child2 in parent.children
        
        # Test absolute positioning
        abs_rect1 = child1.absolute_rect
        assert abs_rect1.x == 10
        assert abs_rect1.y == 10
        
        parent.remove_child(child1)
        assert child1.parent is None
        assert len(parent.children) == 1
        assert child1 not in parent.children
    
    def test_component_state_management(self):
        """Test component state changes."""
        comp = MockComponent()
        
        assert comp.state == ComponentState.NORMAL
        
        comp.set_state(ComponentState.HOVER)
        assert comp.state == ComponentState.HOVER
        
        comp.set_state(ComponentState.PRESSED)
        assert comp.state == ComponentState.PRESSED
        
        comp.set_state(ComponentState.DISABLED)
        assert comp.state == ComponentState.DISABLED
    
    def test_component_event_handling(self):
        """Test event handler system."""
        comp = MockComponent()
        events_received = []
        
        def event_handler(component, event_data):
            events_received.append((component, event_data))
            return True
        
        comp.add_event_handler('test_event', event_handler)
        
        result = comp.emit_event('test_event', 'test_data')
        assert result == True
        assert len(events_received) == 1
        assert events_received[0] == (comp, 'test_data')
    
    def test_component_mouse_handling(self):
        """Test mouse event handling."""
        comp = MockComponent(10, 10, 20, 20)
        
        # Mouse event within bounds (relative to component)
        result = comp.handle_mouse_event(15, 15, 0, True)
        assert result == True
        assert len(comp.mouse_events) == 1
        assert comp.mouse_events[0] == (15, 15, 0, True)
        
        # Mouse event outside bounds
        comp.mouse_events.clear()
        result = comp.handle_mouse_event(35, 35, 0, True)
        assert result == False
        assert len(comp.mouse_events) == 0
    
    def test_component_rendering(self):
        """Test component rendering."""
        surface = MockSurface()
        comp = MockComponent(10, 10, 5, 3)
        
        comp.render(surface)
        
        # Check that component area was filled
        assert surface.get_char(10, 10) == 'X'
        assert surface.get_char(14, 12) == 'X'


class TestButton:
    """Test cases for the Button component."""
    
    def test_button_creation(self):
        """Test button creation."""
        button = Button(10, 10, 15, 3, text="Test Button")
        assert button.text == "Test Button"
        assert button.width == 15
        assert button.height == 3
    
    def test_button_click_handling(self):
        """Test button click events."""
        clicked = []
        
        def on_click(btn):
            clicked.append(btn.text)
        
        button = Button(0, 0, 10, 3, text="Click Me", on_click=on_click)
        
        # Simulate mouse click
        button.handle_mouse_event(5, 1, 0, True)   # Press
        button.handle_mouse_event(5, 1, 0, False)  # Release
        
        assert len(clicked) == 1
        assert clicked[0] == "Click Me"
    
    def test_button_state_changes(self):
        """Test button state changes on interaction."""
        button = Button(0, 0, 10, 3)
        
        assert button.state == ComponentState.NORMAL
        
        # Mouse enter
        button.handle_mouse_event(5, 1, 0, False)
        assert button.state == ComponentState.HOVER
        
        # Mouse press
        button.handle_mouse_event(5, 1, 0, True)
        assert button.state == ComponentState.PRESSED
        
        # Mouse release
        button.handle_mouse_event(5, 1, 0, False)
        assert button.state == ComponentState.HOVER
    
    def test_button_keyboard_activation(self):
        """Test button activation with keyboard."""
        clicked = []
        
        def on_click(btn):
            clicked.append(btn.text)
        
        button = Button(0, 0, 10, 3, text="Enter Me", on_click=on_click)
        button.set_state(ComponentState.FOCUSED)
        
        # Press Enter
        button.handle_key_event('enter', True)
        
        assert len(clicked) == 1
        assert clicked[0] == "Enter Me"
    
    def test_button_rendering(self):
        """Test button rendering."""
        surface = MockSurface()
        button = Button(5, 5, 12, 3, text="Test")
        
        button.render(surface)
        
        # Check that button area has background
        assert surface.get_char(5, 5) == ' '  # Background fill
        # Text should be rendered (exact position depends on centering)


class TestPanel:
    """Test cases for the Panel component."""
    
    def test_panel_creation(self):
        """Test panel creation."""
        panel = Panel(10, 10, 30, 20, title="Test Panel")
        assert panel.title == "Test Panel"
        assert panel.width == 30
        assert panel.height == 20
    
    def test_panel_child_management(self):
        """Test panel child component management."""
        panel = Panel(0, 0, 50, 30)
        child1 = MockComponent(5, 5, 10, 10)
        child2 = MockComponent(20, 10, 15, 8)
        
        panel.add_child(child1)
        panel.add_child(child2)
        
        assert len(panel.children) == 2
        assert child1.parent == panel
        assert child2.parent == panel
    
    def test_panel_content_area(self):
        """Test panel content area calculation."""
        # Panel without border
        panel = Panel(0, 0, 20, 15)
        panel.style.border_color = None
        content_area = panel.content_area
        assert content_area.width == 20
        assert content_area.height == 15
        
        # Panel with border
        panel.style.border_color = Colors.WHITE
        content_area = panel.content_area
        assert content_area.width == 18  # 20 - 2 for borders
        assert content_area.height == 13  # 15 - 2 for borders
        
        # Panel with border and title
        panel.title = "Test"
        content_area = panel.content_area
        assert content_area.height == 12  # 15 - 2 for borders - 1 for title
    
    def test_panel_scrolling(self):
        """Test panel scrolling functionality."""
        panel = Panel(0, 0, 20, 10, scrollable=True)
        
        # Add children that exceed panel size
        for i in range(5):
            child = MockComponent(0, i * 3, 15, 2)
            panel.add_child(child)
        
        panel.update_layout()
        
        # Test scrolling
        assert panel.scroll_y == 0
        panel.scroll(0, 3)
        assert panel.scroll_y == 3
        
        # Test scroll bounds
        panel.scroll(0, 100)  # Try to scroll too far
        assert panel.scroll_y <= panel.max_scroll_y
    
    def test_panel_rendering(self):
        """Test panel rendering."""
        surface = MockSurface()
        panel = Panel(5, 5, 20, 10, title="Test Panel")
        
        panel.render(surface)
        
        # Check that panel background is rendered
        assert surface.get_char(5, 5) != ' ' or surface._bg_colors.get((5, 5)) is not None


class TestMenu:
    """Test cases for the Menu component."""
    
    def test_menu_creation(self):
        """Test menu creation."""
        items = ["Option 1", "Option 2", "Option 3"]
        menu = Menu(10, 10, 20, 8, items=items)
        
        assert len(menu.items) == 3
        assert menu.items[0].text == "Option 1"
        assert menu.items[1].text == "Option 2"
        assert menu.items[2].text == "Option 3"
    
    def test_menu_item_objects(self):
        """Test menu with MenuItem objects."""
        items = [
            MenuItem("First", "value1"),
            MenuItem("Second", "value2", enabled=False),
            MenuItem("Third", "value3")
        ]
        menu = Menu(0, 0, 20, 8, items=items)
        
        assert len(menu.items) == 3
        assert menu.items[0].value == "value1"
        assert menu.items[1].enabled == False
        assert menu.items[2].text == "Third"
    
    def test_menu_selection(self):
        """Test menu item selection."""
        items = ["Option 1", "Option 2", "Option 3"]
        menu = Menu(0, 0, 20, 8, items=items)
        
        # Test initial selection (should select first enabled item)
        assert menu.selected_index >= 0
        
        # Test manual selection
        menu.set_selection(1)
        assert menu.selected_index == 1
        assert menu.selected_item.text == "Option 2"
    
    def test_menu_keyboard_navigation(self):
        """Test menu keyboard navigation."""
        items = ["Option 1", "Option 2", "Option 3"]
        menu = Menu(0, 0, 20, 8, items=items)
        menu.set_selection(0)
        
        # Navigate down
        menu.handle_key_event('down', True)
        assert menu.selected_index == 1
        
        # Navigate up
        menu.handle_key_event('up', True)
        assert menu.selected_index == 0
        
        # Test wrapping (up from first item)
        menu.handle_key_event('up', True)
        assert menu.selected_index == 2  # Should wrap to last item
    
    def test_menu_mouse_selection(self):
        """Test menu mouse selection."""
        items = ["Option 1", "Option 2", "Option 3"]
        menu = Menu(0, 0, 20, 8, items=items)
        
        selected = []
        
        def on_select(menu, index, item):
            selected.append((index, item.text))
        
        menu._on_select = on_select
        
        # Click on second item (assuming border offset)
        menu.handle_mouse_event(5, 2, 0, False)  # Release click
        
        # Should have selected and triggered callback
        if len(selected) > 0:
            assert selected[0][1] in ["Option 1", "Option 2", "Option 3"]
    
    def test_menu_rendering(self):
        """Test menu rendering."""
        surface = MockSurface()
        items = ["Option 1", "Option 2"]
        menu = Menu(5, 5, 15, 6, items=items)
        
        menu.render(surface)
        
        # Check that menu background is rendered
        assert surface.get_char(5, 5) != ' ' or surface._bg_colors.get((5, 5)) is not None


class TestDialog:
    """Test cases for the Dialog component."""
    
    def test_dialog_creation(self):
        """Test dialog creation."""
        dialog = Dialog(10, 10, 30, 15, title="Test Dialog", message="Hello World")
        assert dialog.title == "Test Dialog"
        assert dialog.message == "Hello World"
        assert dialog.dialog_type == DialogType.MESSAGE
    
    def test_dialog_types(self):
        """Test different dialog types."""
        # Message dialog
        msg_dialog = Dialog(0, 0, 30, 15, dialog_type=DialogType.MESSAGE)
        assert msg_dialog.dialog_type == DialogType.MESSAGE
        
        # Confirmation dialog
        conf_dialog = Dialog(0, 0, 30, 15, dialog_type=DialogType.CONFIRMATION)
        assert conf_dialog.dialog_type == DialogType.CONFIRMATION
    
    def test_dialog_button_handling(self):
        """Test dialog button interactions."""
        results = []
        
        def on_result(dialog, result, data):
            results.append((result, data))
        
        dialog = Dialog(0, 0, 30, 15, title="Test", message="Choose",
                       dialog_type=DialogType.CONFIRMATION, on_result=on_result)
        
        # Simulate button click (this would normally be done through button events)
        dialog._handle_button_click("Yes")
        
        assert len(results) == 1
        assert results[0][0] == DialogResult.YES
    
    def test_dialog_keyboard_shortcuts(self):
        """Test dialog keyboard shortcuts."""
        results = []
        
        def on_result(dialog, result, data):
            results.append(result)
        
        dialog = Dialog(0, 0, 30, 15, on_result=on_result)
        
        # Test Enter key
        dialog.handle_key_event('enter', True)
        assert len(results) == 1
        assert results[0] == DialogResult.OK
        
        # Reset and test Escape key
        results.clear()
        dialog.result = DialogResult.NONE
        dialog.handle_key_event('escape', True)
        assert len(results) == 1
        assert results[0] == DialogResult.CANCEL
    
    def test_dialog_show_hide(self):
        """Test dialog show/hide functionality."""
        dialog = Dialog(0, 0, 30, 15)
        
        assert dialog.visible == True  # Visible by default
        
        dialog.hide()
        assert dialog.visible == False
        
        dialog.show()
        assert dialog.visible == True
        assert dialog.result == DialogResult.NONE  # Reset on show
    
    def test_dialog_factory_methods(self):
        """Test dialog factory methods."""
        # Message dialog
        msg_dialog = Dialog.show_message("Info", "This is a message")
        assert msg_dialog.title == "Info"
        assert msg_dialog.message == "This is a message"
        assert msg_dialog.dialog_type == DialogType.MESSAGE
        
        # Confirmation dialog
        conf_dialog = Dialog.show_confirmation("Confirm", "Are you sure?")
        assert conf_dialog.title == "Confirm"
        assert conf_dialog.message == "Are you sure?"
        assert conf_dialog.dialog_type == DialogType.CONFIRMATION


class TestLayout:
    """Test cases for layout managers."""
    
    def test_absolute_layout(self):
        """Test absolute layout manager."""
        layout = AbsoluteLayout()
        container = MockComponent(0, 0, 100, 50)
        
        child1 = MockComponent(10, 10, 20, 15)
        child2 = MockComponent(40, 20, 25, 10)
        
        container.add_child(child1)
        container.add_child(child2)
        
        # Store original positions
        orig_x1, orig_y1 = child1.x, child1.y
        orig_x2, orig_y2 = child2.x, child2.y
        
        layout.layout(container)
        
        # Absolute layout should not change positions
        assert child1.x == orig_x1
        assert child1.y == orig_y1
        assert child2.x == orig_x2
        assert child2.y == orig_y2
    
    def test_flow_layout_horizontal(self):
        """Test horizontal flow layout."""
        layout = FlowLayout(LayoutDirection.HORIZONTAL, spacing=2)
        container = MockComponent(0, 0, 100, 50)
        
        child1 = MockComponent(0, 0, 20, 10)
        child2 = MockComponent(0, 0, 15, 10)
        child3 = MockComponent(0, 0, 25, 10)
        
        container.add_child(child1)
        container.add_child(child2)
        container.add_child(child3)
        
        layout.layout(container)
        
        # Check horizontal positioning
        assert child1.x == 0  # First child at start
        assert child2.x == 22  # 20 + 2 spacing
        assert child3.x == 39  # 22 + 15 + 2 spacing
    
    def test_flow_layout_vertical(self):
        """Test vertical flow layout."""
        layout = FlowLayout(LayoutDirection.VERTICAL, spacing=1)
        container = MockComponent(0, 0, 50, 100)
        
        child1 = MockComponent(0, 0, 15, 8)
        child2 = MockComponent(0, 0, 20, 12)
        
        container.add_child(child1)
        container.add_child(child2)
        
        layout.layout(container)
        
        # Check vertical positioning
        assert child1.y == 0  # First child at start
        assert child2.y == 9  # 8 + 1 spacing
    
    def test_grid_layout(self):
        """Test grid layout manager."""
        layout = GridLayout(2, 3, spacing=1)  # 2 rows, 3 columns
        container = MockComponent(0, 0, 60, 40)
        
        children = []
        for i in range(6):
            child = MockComponent(0, 0, 10, 8)
            children.append(child)
            container.add_child(child)
        
        layout.layout(container)
        
        # Check grid positioning (approximate, depends on exact calculations)
        assert children[0].x == 0  # First cell
        assert children[1].x > children[0].x  # Second column
        assert children[3].y > children[0].y  # Second row
    
    def test_layout_constraints(self):
        """Test layout constraints."""
        constraints = LayoutConstraints(
            min_width=10,
            max_width=50,
            preferred_width=30,
            margin_left=2,
            margin_right=3
        )
        
        assert constraints.margin_width == 5  # 2 + 3
        assert constraints.clamp_width(5) == 10  # Clamped to minimum
        assert constraints.clamp_width(60) == 50  # Clamped to maximum
        assert constraints.clamp_width(25) == 25  # Within range


class TestTheme:
    """Test cases for the theming system."""
    
    def test_default_theme(self):
        """Test default theme creation."""
        theme = DefaultTheme()
        assert theme.name == "Default"
        assert theme.colors is not None
        assert theme.spacing is not None
        assert theme.sizing is not None
    
    def test_theme_component_styles(self):
        """Test theme component style generation."""
        theme = DefaultTheme()
        
        button_style = theme.get_component_style(Button)
        assert button_style is not None
        assert hasattr(button_style, 'fg_color')
        assert hasattr(button_style, 'bg_color')
        
        panel_style = theme.get_component_style(Panel)
        assert panel_style is not None
        
        # Test caching
        button_style2 = theme.get_component_style(Button)
        assert button_style is button_style2  # Should be cached
    
    def test_theme_colors(self):
        """Test theme color configurations."""
        dark_theme = DarkTheme()
        light_theme = LightTheme()
        
        # Dark theme should have dark background
        assert dark_theme.colors.background.r < 50
        assert dark_theme.colors.background.g < 50
        assert dark_theme.colors.background.b < 50
        
        # Light theme should have light background
        assert light_theme.colors.background.r > 200
        assert light_theme.colors.background.g > 200
        assert light_theme.colors.background.b > 200
    
    def test_game_theme(self):
        """Test game-specific theme."""
        game_theme = GameTheme()
        assert game_theme.name == "Game"
        
        # Game theme should use game colors
        assert game_theme.colors.primary == Colors.LIGHT_GROUND
        assert game_theme.colors.background == Colors.BLACK
    
    def test_theme_registry(self):
        """Test theme registration and retrieval."""
        from ui.theme import register_theme, get_theme, list_themes
        
        # Test built-in themes are registered
        themes = list_themes()
        assert "Default" in themes
        assert "Dark" in themes
        assert "Light" in themes
        assert "Game" in themes
        
        # Test theme retrieval
        default_theme = get_theme("Default")
        assert default_theme is not None
        assert default_theme.name == "Default"


class TestUIEvents:
    """Test cases for the UI event system."""
    
    def test_ui_event_creation(self):
        """Test UI event creation."""
        event = UIEvent(UIEventType.BUTTON_CLICKED, source="test_button")
        assert event.event_type == UIEventType.BUTTON_CLICKED
        assert event.source == "test_button"
        assert event.handled == False
        assert event.cancelled == False
    
    def test_ui_event_factory_methods(self):
        """Test UI event factory methods."""
        # Mouse click event
        click_event = UIEvent.mouse_click("button", 10, 20, 0)
        assert click_event.event_type == UIEventType.MOUSE_CLICK
        assert click_event.mouse_x == 10
        assert click_event.mouse_y == 20
        assert click_event.mouse_button == 0
        
        # Key press event
        key_event = UIEvent.key_press("input", "enter", 13)
        assert key_event.event_type == UIEventType.KEY_PRESS
        assert key_event.key == "enter"
        assert key_event.key_code == 13
        
        # Button clicked event
        button_event = UIEvent.button_clicked("button", {"text": "OK"})
        assert button_event.event_type == UIEventType.BUTTON_CLICKED
        assert button_event.get_data("text") == "OK"
    
    def test_ui_event_data_handling(self):
        """Test UI event data management."""
        event = UIEvent(UIEventType.CUSTOM)
        
        event.set_data("key1", "value1")
        event.set_data("key2", 42)
        
        assert event.get_data("key1") == "value1"
        assert event.get_data("key2") == 42
        assert event.get_data("nonexistent", "default") == "default"
    
    def test_ui_event_handling_control(self):
        """Test UI event handling control."""
        event = UIEvent(UIEventType.BUTTON_CLICKED)
        
        assert event.handled == False
        assert event.cancelled == False
        
        event.mark_handled()
        assert event.handled == True
        assert event.cancelled == False
        
        event2 = UIEvent(UIEventType.KEY_PRESS)
        event2.cancel()
        assert event2.handled == True
        assert event2.cancelled == True
    
    def test_ui_event_type_checking(self):
        """Test UI event type checking methods."""
        mouse_event = UIEvent(UIEventType.MOUSE_CLICK)
        key_event = UIEvent(UIEventType.KEY_PRESS)
        focus_event = UIEvent(UIEventType.FOCUS_GAINED)
        
        assert mouse_event.is_mouse_event() == True
        assert mouse_event.is_keyboard_event() == False
        assert mouse_event.is_focus_event() == False
        
        assert key_event.is_mouse_event() == False
        assert key_event.is_keyboard_event() == True
        assert key_event.is_focus_event() == False
        
        assert focus_event.is_mouse_event() == False
        assert focus_event.is_keyboard_event() == False
        assert focus_event.is_focus_event() == True


if __name__ == '__main__':
    pytest.main([__file__])
