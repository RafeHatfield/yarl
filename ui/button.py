"""Button UI component implementation.

This module provides the Button class, which is a clickable UI component
that can display text and respond to user interactions. Buttons support
various states (normal, hover, pressed, disabled) and can trigger events
when clicked.
"""

from typing import Optional, Callable, Any

from rendering import Surface, Color, Colors
from .component import Component, ComponentState, ComponentStyle
from .events import UIEvent, UIEventType


class ButtonStyle(ComponentStyle):
    """Extended style configuration for buttons."""
    
    def __init__(self, **kwargs):
        # Set button-specific defaults
        defaults = {
            'fg_color': Colors.TEXT_DEFAULT,
            'bg_color': Color(64, 64, 64),
            'border_color': Colors.TEXT_DISABLED,
            'hover_fg_color': Colors.TEXT_HIGHLIGHT,
            'hover_bg_color': Color(96, 96, 96),
            'pressed_fg_color': Colors.TEXT_DEFAULT,
            'pressed_bg_color': Color(32, 32, 32),
            'disabled_fg_color': Colors.TEXT_DISABLED,
            'disabled_bg_color': Color(32, 32, 32),
        }
        
        # Override with provided values
        for key, value in kwargs.items():
            if hasattr(ComponentStyle, key):
                defaults[key] = value
        
        super().__init__(**defaults)


class Button(Component):
    """Interactive button component.
    
    The Button component provides a clickable interface element that can
    display text and respond to mouse interactions. It supports various
    visual states and can trigger events when activated.
    
    Features:
    - Text display with automatic centering
    - Visual feedback for hover and press states
    - Keyboard activation (Enter/Space)
    - Customizable styling and appearance
    - Event callbacks for click handling
    """
    
    def __init__(self, x: int = 0, y: int = 0, width: int = 10, height: int = 3,
                 text: str = "Button", visible: bool = True, enabled: bool = True,
                 style: Optional[ButtonStyle] = None,
                 on_click: Optional[Callable[['Button'], None]] = None):
        """Initialize the button.
        
        Args:
            x (int): X position
            y (int): Y position
            width (int): Button width
            height (int): Button height
            text (str): Button text
            visible (bool): Whether button is visible
            enabled (bool): Whether button is enabled
            style (ButtonStyle, optional): Button styling
            on_click (Callable, optional): Click event handler
        """
        super().__init__(x, y, width, height, visible, enabled, style or ButtonStyle())
        
        self._text = text
        self._on_click = on_click
        self._is_pressed = False
        self._mouse_over = False
        
        # Ensure minimum size for text
        if width < len(text) + 2:
            self.width = len(text) + 2
        if height < 1:
            self.height = 1
    
    @property
    def text(self) -> str:
        """Get button text."""
        return self._text
    
    @text.setter
    def text(self, value: str) -> None:
        """Set button text."""
        if self._text != value:
            self._text = value
            self.mark_dirty()
    
    def set_click_handler(self, handler: Callable[['Button'], None]) -> None:
        """Set the click event handler.
        
        Args:
            handler (Callable): Click handler function
        """
        self._on_click = handler
    
    def click(self) -> None:
        """Programmatically trigger a button click."""
        if self.enabled:
            self._trigger_click()
    
    def _trigger_click(self) -> None:
        """Internal method to trigger click events."""
        # Emit UI event
        event = UIEvent.button_clicked(self, {'text': self.text})
        self.emit_event('click', event)
        
        # Call direct handler if set
        if self._on_click:
            try:
                self._on_click(self)
            except Exception as e:
                print(f"Error in button click handler: {e}")
    
    def on_mouse_event(self, x: int, y: int, button: int, pressed: bool) -> bool:
        """Handle mouse events.
        
        Args:
            x (int): Mouse X coordinate (relative to button)
            y (int): Mouse Y coordinate (relative to button)
            button (int): Mouse button
            pressed (bool): True if pressed, False if released
            
        Returns:
            bool: True if event was handled
        """
        if not self.enabled:
            return False
        
        # Check if mouse is over button
        was_over = self._mouse_over
        self._mouse_over = self.rect.contains(x, y)
        
        # Handle mouse enter/leave
        if self._mouse_over and not was_over:
            self.set_state(ComponentState.HOVER)
            self.emit_event('mouse_enter', UIEvent(UIEventType.MOUSE_ENTER, self))
        elif not self._mouse_over and was_over:
            self.set_state(ComponentState.NORMAL)
            self.emit_event('mouse_leave', UIEvent(UIEventType.MOUSE_LEAVE, self))
        
        # Handle mouse press/release
        if self._mouse_over and button == 0:  # Left mouse button
            if pressed:
                self._is_pressed = True
                self.set_state(ComponentState.PRESSED)
                self.emit_event('mouse_down', UIEvent(UIEventType.MOUSE_DOWN, self))
            else:
                if self._is_pressed:
                    self._is_pressed = False
                    self.set_state(ComponentState.HOVER)
                    self._trigger_click()
                self.emit_event('mouse_up', UIEvent(UIEventType.MOUSE_UP, self))
            
            return True
        
        return self._mouse_over
    
    def on_key_event(self, key: str, pressed: bool) -> bool:
        """Handle keyboard events.
        
        Args:
            key (str): Key identifier
            pressed (bool): True if pressed, False if released
            
        Returns:
            bool: True if event was handled
        """
        if not self.enabled or self.state != ComponentState.FOCUSED:
            return False
        
        # Activate button with Enter or Space
        if pressed and key.lower() in ('enter', 'return', 'space'):
            self._trigger_click()
            return True
        
        return False
    
    def render_self(self, surface: Surface) -> None:
        """Render the button.
        
        Args:
            surface (Surface): Surface to render to
        """
        abs_rect = self.absolute_rect
        fg_color, bg_color = self.get_style_colors()
        
        # Fill background
        surface.fill_rect(abs_rect, ' ', fg_color, bg_color)
        
        # Draw border if specified
        if self.style.border_color:
            surface.draw_border(abs_rect, self.style.border_color, bg_color)
        
        # Draw text (centered)
        if self.text and self.width > 0 and self.height > 0:
            text_x = abs_rect.x + max(0, (abs_rect.width - len(self.text)) // 2)
            text_y = abs_rect.y + abs_rect.height // 2
            
            # Ensure text fits within button bounds
            if text_x >= abs_rect.x and text_y >= abs_rect.y:
                display_text = self.text
                max_text_width = abs_rect.width - 2  # Leave space for borders
                
                if len(display_text) > max_text_width:
                    display_text = display_text[:max_text_width-3] + "..."
                
                surface.print_string(text_x, text_y, display_text, fg_color)
    
    def on_state_changed(self, old_state: ComponentState, new_state: ComponentState) -> None:
        """Handle state changes.
        
        Args:
            old_state (ComponentState): Previous state
            new_state (ComponentState): New state
        """
        super().on_state_changed(old_state, new_state)
        
        # Reset internal state when disabled
        if new_state == ComponentState.DISABLED:
            self._is_pressed = False
            self._mouse_over = False
    
    def __repr__(self) -> str:
        """String representation of button."""
        return (f"Button(text='{self.text}', x={self.x}, y={self.y}, "
                f"w={self.width}, h={self.height}, state={self.state.name})")
