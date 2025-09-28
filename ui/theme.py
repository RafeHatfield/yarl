"""Theme system for UI component styling.

This module provides a comprehensive theming system that allows for
consistent styling across all UI components. Themes define colors,
fonts, spacing, and other visual properties that can be applied
globally or to specific component types.
"""

from typing import Dict, Any, Optional, Type, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from rendering import Color, Colors
from .component import ComponentStyle
from .button import ButtonStyle
from .panel import PanelStyle
from .menu import MenuStyle
from .dialog import DialogStyle


@dataclass
class ThemeColors:
    """Color palette for a theme."""
    
    # Base colors
    primary: Color = Colors.BLUE
    secondary: Color = Colors.CYAN
    accent: Color = Colors.YELLOW
    
    # Background colors
    background: Color = Colors.BLACK
    surface: Color = Color(32, 32, 32)
    surface_variant: Color = Color(48, 48, 48)
    
    # Text colors
    text_primary: Color = Colors.WHITE
    text_secondary: Color = Colors.TEXT_DISABLED
    text_on_primary: Color = Colors.WHITE
    text_on_surface: Color = Colors.WHITE
    
    # State colors
    success: Color = Colors.LIGHT_GREEN
    warning: Color = Colors.YELLOW
    error: Color = Colors.LIGHT_RED
    info: Color = Colors.LIGHT_BLUE
    
    # Interactive colors
    hover: Color = Color(80, 80, 80)
    pressed: Color = Color(64, 64, 64)
    focused: Color = Colors.TEXT_HIGHLIGHT
    disabled: Color = Colors.TEXT_DISABLED
    
    # Border colors
    border: Color = Colors.TEXT_DISABLED
    border_focus: Color = Colors.TEXT_HIGHLIGHT


@dataclass
class ThemeSpacing:
    """Spacing values for a theme."""
    
    # Basic spacing units
    xs: int = 1
    sm: int = 2
    md: int = 4
    lg: int = 8
    xl: int = 16
    
    # Component-specific spacing
    button_padding: int = 1
    panel_padding: int = 1
    menu_item_spacing: int = 0
    dialog_padding: int = 2


@dataclass
class ThemeSizing:
    """Sizing values for a theme."""
    
    # Minimum sizes
    min_button_width: int = 8
    min_button_height: int = 1
    min_panel_width: int = 10
    min_panel_height: int = 5
    
    # Default sizes
    default_button_width: int = 12
    default_button_height: int = 3
    default_dialog_width: int = 40
    default_dialog_height: int = 15


class Theme(ABC):
    """Abstract base class for UI themes.
    
    Themes provide consistent styling across all UI components by
    defining color palettes, spacing, sizing, and component-specific
    style configurations.
    """
    
    def __init__(self, name: str):
        """Initialize the theme.
        
        Args:
            name (str): Theme name
        """
        self.name = name
        self.colors = self._create_colors()
        self.spacing = self._create_spacing()
        self.sizing = self._create_sizing()
        
        # Component style cache
        self._style_cache: Dict[Type, Any] = {}
    
    @abstractmethod
    def _create_colors(self) -> ThemeColors:
        """Create the color palette for this theme.
        
        Returns:
            ThemeColors: Theme color configuration
        """
        pass
    
    @abstractmethod
    def _create_spacing(self) -> ThemeSpacing:
        """Create the spacing configuration for this theme.
        
        Returns:
            ThemeSpacing: Theme spacing configuration
        """
        pass
    
    @abstractmethod
    def _create_sizing(self) -> ThemeSizing:
        """Create the sizing configuration for this theme.
        
        Returns:
            ThemeSizing: Theme sizing configuration
        """
        pass
    
    def get_component_style(self, component_type: Type) -> ComponentStyle:
        """Get the style configuration for a component type.
        
        Args:
            component_type (Type): Component class type
            
        Returns:
            ComponentStyle: Style configuration for the component
        """
        if component_type not in self._style_cache:
            self._style_cache[component_type] = self._create_component_style(component_type)
        
        return self._style_cache[component_type]
    
    def _create_component_style(self, component_type: Type) -> ComponentStyle:
        """Create style configuration for a specific component type.
        
        Args:
            component_type (Type): Component class type
            
        Returns:
            ComponentStyle: Style configuration
        """
        # Import here to avoid circular imports
        from .button import Button
        from .panel import Panel
        from .menu import Menu
        from .dialog import Dialog
        
        if component_type == Button or issubclass(component_type, Button):
            return self._create_button_style()
        elif component_type == Panel or issubclass(component_type, Panel):
            return self._create_panel_style()
        elif component_type == Menu or issubclass(component_type, Menu):
            return self._create_menu_style()
        elif component_type == Dialog or issubclass(component_type, Dialog):
            return self._create_dialog_style()
        else:
            return self._create_default_style()
    
    def _create_button_style(self) -> ButtonStyle:
        """Create button style configuration.
        
        Returns:
            ButtonStyle: Button style configuration
        """
        return ButtonStyle(
            fg_color=self.colors.text_on_surface,
            bg_color=self.colors.surface_variant,
            border_color=self.colors.border,
            hover_fg_color=self.colors.text_primary,
            hover_bg_color=self.colors.hover,
            pressed_fg_color=self.colors.text_primary,
            pressed_bg_color=self.colors.pressed,
            disabled_fg_color=self.colors.disabled,
            disabled_bg_color=self.colors.surface,
        )
    
    def _create_panel_style(self) -> PanelStyle:
        """Create panel style configuration.
        
        Returns:
            PanelStyle: Panel style configuration
        """
        return PanelStyle(
            fg_color=self.colors.text_primary,
            bg_color=self.colors.surface,
            border_color=self.colors.border,
        )
    
    def _create_menu_style(self) -> MenuStyle:
        """Create menu style configuration.
        
        Returns:
            MenuStyle: Menu style configuration
        """
        return MenuStyle(
            fg_color=self.colors.text_primary,
            bg_color=self.colors.surface,
            border_color=self.colors.border,
            hover_fg_color=self.colors.text_primary,
            hover_bg_color=self.colors.hover,
            disabled_fg_color=self.colors.disabled,
        )
    
    def _create_dialog_style(self) -> DialogStyle:
        """Create dialog style configuration.
        
        Returns:
            DialogStyle: Dialog style configuration
        """
        return DialogStyle(
            fg_color=self.colors.text_primary,
            bg_color=self.colors.surface_variant,
            border_color=self.colors.border_focus,
        )
    
    def _create_default_style(self) -> ComponentStyle:
        """Create default component style configuration.
        
        Returns:
            ComponentStyle: Default style configuration
        """
        return ComponentStyle(
            fg_color=self.colors.text_primary,
            bg_color=self.colors.surface,
            border_color=self.colors.border,
            hover_fg_color=self.colors.text_primary,
            hover_bg_color=self.colors.hover,
            pressed_fg_color=self.colors.text_primary,
            pressed_bg_color=self.colors.pressed,
            disabled_fg_color=self.colors.disabled,
            disabled_bg_color=self.colors.surface,
        )
    
    def clear_cache(self) -> None:
        """Clear the component style cache."""
        self._style_cache.clear()
    
    def __repr__(self) -> str:
        """String representation of theme."""
        return f"Theme(name='{self.name}')"


class DefaultTheme(Theme):
    """Default theme with standard colors and styling."""
    
    def __init__(self):
        """Initialize the default theme."""
        super().__init__("Default")
    
    def _create_colors(self) -> ThemeColors:
        """Create default color palette."""
        return ThemeColors()
    
    def _create_spacing(self) -> ThemeSpacing:
        """Create default spacing configuration."""
        return ThemeSpacing()
    
    def _create_sizing(self) -> ThemeSizing:
        """Create default sizing configuration."""
        return ThemeSizing()


class DarkTheme(Theme):
    """Dark theme with darker colors and high contrast."""
    
    def __init__(self):
        """Initialize the dark theme."""
        super().__init__("Dark")
    
    def _create_colors(self) -> ThemeColors:
        """Create dark color palette."""
        return ThemeColors(
            background=Color(16, 16, 16),
            surface=Color(24, 24, 24),
            surface_variant=Color(32, 32, 32),
            text_primary=Color(240, 240, 240),
            text_secondary=Color(160, 160, 160),
            hover=Color(48, 48, 48),
            pressed=Color(16, 16, 16),
            border=Color(64, 64, 64),
        )
    
    def _create_spacing(self) -> ThemeSpacing:
        """Create dark theme spacing configuration."""
        return ThemeSpacing()
    
    def _create_sizing(self) -> ThemeSizing:
        """Create dark theme sizing configuration."""
        return ThemeSizing()


class LightTheme(Theme):
    """Light theme with bright colors and good readability."""
    
    def __init__(self):
        """Initialize the light theme."""
        super().__init__("Light")
    
    def _create_colors(self) -> ThemeColors:
        """Create light color palette."""
        return ThemeColors(
            primary=Color(25, 118, 210),  # Blue
            secondary=Color(156, 39, 176),  # Purple
            accent=Color(255, 193, 7),  # Amber
            
            background=Color(250, 250, 250),
            surface=Color(255, 255, 255),
            surface_variant=Color(245, 245, 245),
            
            text_primary=Color(33, 33, 33),
            text_secondary=Color(117, 117, 117),
            text_on_primary=Colors.WHITE,
            text_on_surface=Color(33, 33, 33),
            
            hover=Color(240, 240, 240),
            pressed=Color(230, 230, 230),
            focused=Color(25, 118, 210),
            disabled=Color(158, 158, 158),
            
            border=Color(224, 224, 224),
            border_focus=Color(25, 118, 210),
        )
    
    def _create_spacing(self) -> ThemeSpacing:
        """Create light theme spacing configuration."""
        return ThemeSpacing()
    
    def _create_sizing(self) -> ThemeSizing:
        """Create light theme sizing configuration."""
        return ThemeSizing()


class GameTheme(Theme):
    """Game-specific theme matching the roguelike aesthetic."""
    
    def __init__(self):
        """Initialize the game theme."""
        super().__init__("Game")
    
    def _create_colors(self) -> ThemeColors:
        """Create game color palette."""
        return ThemeColors(
            primary=Colors.LIGHT_GROUND,  # Gold/yellow
            secondary=Colors.LIGHT_WALL,  # Brown
            accent=Colors.LIGHT_GREEN,
            
            background=Colors.BLACK,
            surface=Colors.DARK_GROUND,
            surface_variant=Color(60, 60, 120),
            
            text_primary=Colors.WHITE,
            text_secondary=Color(180, 180, 180),
            text_on_primary=Colors.BLACK,
            text_on_surface=Colors.WHITE,
            
            success=Colors.LIGHT_GREEN,
            warning=Colors.YELLOW,
            error=Colors.LIGHT_RED,
            info=Colors.LIGHT_BLUE,
            
            hover=Color(80, 80, 150),
            pressed=Color(40, 40, 100),
            focused=Colors.LIGHT_GROUND,
            disabled=Color(100, 100, 100),
            
            border=Color(130, 130, 130),
            border_focus=Colors.LIGHT_GROUND,
        )
    
    def _create_spacing(self) -> ThemeSpacing:
        """Create game theme spacing configuration."""
        return ThemeSpacing(
            # Tighter spacing for game UI
            button_padding=0,
            panel_padding=1,
            menu_item_spacing=0,
            dialog_padding=1,
        )
    
    def _create_sizing(self) -> ThemeSizing:
        """Create game theme sizing configuration."""
        return ThemeSizing(
            # Smaller default sizes for game UI
            default_button_width=10,
            default_button_height=1,
            default_dialog_width=35,
            default_dialog_height=12,
        )


# Global theme registry
_theme_registry: Dict[str, Theme] = {}
_current_theme: Optional[Theme] = None


def register_theme(theme: Theme) -> None:
    """Register a theme in the global registry.
    
    Args:
        theme (Theme): Theme to register
    """
    _theme_registry[theme.name] = theme


def get_theme(name: str) -> Optional[Theme]:
    """Get a theme by name.
    
    Args:
        name (str): Theme name
        
    Returns:
        Theme: Theme instance, or None if not found
    """
    return _theme_registry.get(name)


def set_current_theme(theme: Theme) -> None:
    """Set the current global theme.
    
    Args:
        theme (Theme): Theme to set as current
    """
    global _current_theme
    _current_theme = theme
    
    # Clear all theme caches
    for registered_theme in _theme_registry.values():
        registered_theme.clear_cache()


def get_current_theme() -> Theme:
    """Get the current global theme.
    
    Returns:
        Theme: Current theme (defaults to DefaultTheme if none set)
    """
    global _current_theme
    if _current_theme is None:
        _current_theme = DefaultTheme()
    return _current_theme


def list_themes() -> List[str]:
    """Get list of registered theme names.
    
    Returns:
        List[str]: List of theme names
    """
    return list(_theme_registry.keys())


# Register built-in themes
register_theme(DefaultTheme())
register_theme(DarkTheme())
register_theme(LightTheme())
register_theme(GameTheme())

# Set default theme
set_current_theme(get_theme("Default"))
