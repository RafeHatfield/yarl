"""UI component system for scalable interface management.

This package provides a comprehensive UI component system that works with
the rendering abstraction layer to create reusable, composable interface
elements. The system is designed to work with both console and future GUI
backends while maintaining consistent behavior and appearance.

Key Components:
- Component: Base class for all UI elements
- Layout: Layout managers for positioning components
- Button: Interactive button component
- Panel: Container component for grouping elements
- Menu: Menu component with selectable options
- Dialog: Modal dialog component
- Theme: Styling and appearance management
"""

from .component import Component, ComponentState
from .layout import Layout, GridLayout, FlowLayout, AbsoluteLayout
from .button import Button
from .panel import Panel
from .menu import Menu, MenuItem
from .dialog import Dialog, DialogType, DialogResult
from .theme import Theme, DefaultTheme, DarkTheme, LightTheme, GameTheme
from .events import UIEvent, UIEventType

__all__ = [
    'Component',
    'ComponentState', 
    'Layout',
    'GridLayout',
    'FlowLayout',
    'AbsoluteLayout',
    'Button',
    'Panel',
    'Menu',
    'MenuItem',
    'Dialog',
    'DialogType',
    'DialogResult',
    'Theme',
    'DefaultTheme',
    'DarkTheme',
    'LightTheme',
    'GameTheme',
    'UIEvent',
    'UIEventType',
]
