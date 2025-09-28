"""Dialog UI component implementation.

This module provides the Dialog class, which creates modal dialog boxes
for user interaction. Dialogs can display messages, prompt for input,
and provide action buttons for user responses.
"""

from typing import List, Optional, Callable, Any, Dict
from enum import Enum, auto

from rendering import Surface, Color, Colors
from rendering.surface import Rect
from .component import Component, ComponentState, ComponentStyle
from .button import Button, ButtonStyle
from .panel import Panel, PanelStyle
from .layout import FlowLayout, LayoutDirection, LayoutConstraints, Alignment
from .events import UIEvent, UIEventType


class DialogType(Enum):
    """Types of dialogs."""
    MESSAGE = auto()      # Simple message display
    CONFIRMATION = auto() # Yes/No confirmation
    INPUT = auto()        # Text input dialog
    CUSTOM = auto()       # Custom dialog with user-defined content


class DialogResult(Enum):
    """Dialog result values."""
    NONE = auto()
    OK = auto()
    CANCEL = auto()
    YES = auto()
    NO = auto()
    CUSTOM = auto()


class DialogStyle(PanelStyle):
    """Extended style configuration for dialogs."""
    
    def __init__(self, **kwargs):
        # Set dialog-specific defaults
        defaults = {
            'fg_color': Colors.TEXT_DEFAULT,
            'bg_color': Color(64, 64, 64),
            'border_color': Colors.TEXT_HIGHLIGHT,
        }
        
        # Override with provided values
        for key, value in kwargs.items():
            if hasattr(PanelStyle, key):
                defaults[key] = value
        
        super().__init__(**defaults)


class Dialog(Panel):
    """Modal dialog component.
    
    The Dialog component creates modal dialog boxes that can display
    messages, prompt for user input, and provide action buttons.
    Dialogs are typically displayed over other UI content and capture
    input focus until dismissed.
    
    Features:
    - Modal behavior (blocks interaction with other components)
    - Multiple dialog types (message, confirmation, input, custom)
    - Automatic button layout and handling
    - Keyboard shortcuts (Enter, Escape)
    - Customizable styling and content
    - Result callbacks and events
    """
    
    def __init__(self, x: int = 0, y: int = 0, width: int = 40, height: int = 15,
                 title: str = "Dialog", message: str = "",
                 dialog_type: DialogType = DialogType.MESSAGE,
                 buttons: Optional[List[str]] = None,
                 visible: bool = True, enabled: bool = True,
                 style: Optional[DialogStyle] = None,
                 on_result: Optional[Callable[['Dialog', DialogResult, Any], None]] = None):
        """Initialize the dialog.
        
        Args:
            x (int): X position
            y (int): Y position
            width (int): Dialog width
            height (int): Dialog height
            title (str): Dialog title
            message (str): Dialog message text
            dialog_type (DialogType): Type of dialog
            buttons (List[str], optional): Custom button labels
            visible (bool): Whether dialog is visible
            enabled (bool): Whether dialog is enabled
            style (DialogStyle, optional): Dialog styling
            on_result (Callable, optional): Result callback
        """
        super().__init__(x, y, width, height, title, visible, enabled, 
                        style or DialogStyle(), scrollable=False)
        
        self.message = message
        self.dialog_type = dialog_type
        self.result = DialogResult.NONE
        self.result_data: Any = None
        self._on_result = on_result
        
        # Dialog state
        self.modal = True
        self.center_on_parent = True
        
        # Create content
        self._create_content(buttons)
    
    def _create_content(self, custom_buttons: Optional[List[str]] = None) -> None:
        """Create dialog content based on type.
        
        Args:
            custom_buttons (List[str], optional): Custom button labels
        """
        # Clear existing content
        self.children.clear()
        
        # Create message area if we have a message
        if self.message:
            self._create_message_area()
        
        # Create buttons based on dialog type
        if custom_buttons:
            button_labels = custom_buttons
        else:
            button_labels = self._get_default_buttons()
        
        if button_labels:
            self._create_button_area(button_labels)
        
        # Set up layout
        self.set_layout_manager(FlowLayout(LayoutDirection.VERTICAL, spacing=1, padding=1))
    
    def _create_message_area(self) -> None:
        """Create the message display area."""
        content_area = self.content_area
        message_height = max(1, min(content_area.height - 4, self._calculate_message_height()))
        
        # Create a panel for the message
        message_panel = Panel(
            0, 0, content_area.width, message_height,
            style=PanelStyle(
                fg_color=self.style.fg_color,
                bg_color=self.style.bg_color,
                border_color=None  # No border for message area
            )
        )
        
        # Add message text (we'll render it manually in render_self)
        self.add_child(message_panel)
    
    def _create_button_area(self, button_labels: List[str]) -> None:
        """Create the button area.
        
        Args:
            button_labels (List[str]): Button labels to create
        """
        content_area = self.content_area
        button_height = 3
        button_width = max(8, (content_area.width - len(button_labels) - 1) // len(button_labels))
        
        # Create button panel
        button_panel = Panel(
            0, 0, content_area.width, button_height,
            style=PanelStyle(
                fg_color=self.style.fg_color,
                bg_color=self.style.bg_color,
                border_color=None
            )
        )
        
        # Create buttons
        button_layout = FlowLayout(LayoutDirection.HORIZONTAL, spacing=1)
        button_panel.set_layout_manager(button_layout)
        
        for i, label in enumerate(button_labels):
            button = Button(
                0, 0, button_width, button_height,
                text=label,
                style=ButtonStyle(),
                on_click=lambda btn, lbl=label: self._handle_button_click(lbl)
            )
            
            # Set layout constraints for even distribution
            constraints = LayoutConstraints(
                preferred_width=button_width,
                preferred_height=button_height,
                horizontal_alignment=Alignment.CENTER
            )
            button_layout.set_constraints(button, constraints)
            
            button_panel.add_child(button)
            
            # Focus first button by default
            if i == 0:
                button.set_state(ComponentState.FOCUSED)
        
        self.add_child(button_panel)
    
    def _get_default_buttons(self) -> List[str]:
        """Get default button labels for dialog type.
        
        Returns:
            List[str]: Default button labels
        """
        if self.dialog_type == DialogType.MESSAGE:
            return ["OK"]
        elif self.dialog_type == DialogType.CONFIRMATION:
            return ["Yes", "No"]
        elif self.dialog_type == DialogType.INPUT:
            return ["OK", "Cancel"]
        else:  # CUSTOM
            return ["OK"]
    
    def _calculate_message_height(self) -> int:
        """Calculate required height for message text.
        
        Returns:
            int: Required height in lines
        """
        if not self.message:
            return 0
        
        content_area = self.content_area
        text_width = content_area.width - 2  # Account for padding
        
        # Simple word wrapping calculation
        words = self.message.split()
        lines = 1
        current_line_length = 0
        
        for word in words:
            if current_line_length + len(word) + 1 > text_width:
                lines += 1
                current_line_length = len(word)
            else:
                current_line_length += len(word) + 1
        
        return lines
    
    def _handle_button_click(self, button_label: str) -> None:
        """Handle button click events.
        
        Args:
            button_label (str): Label of clicked button
        """
        # Determine result based on button label
        label_lower = button_label.lower()
        
        if label_lower in ('ok', 'okay'):
            self.result = DialogResult.OK
        elif label_lower in ('cancel', 'close'):
            self.result = DialogResult.CANCEL
        elif label_lower in ('yes', 'y'):
            self.result = DialogResult.YES
        elif label_lower in ('no', 'n'):
            self.result = DialogResult.NO
        else:
            self.result = DialogResult.CUSTOM
            self.result_data = button_label
        
        self._close_dialog()
    
    def _close_dialog(self) -> None:
        """Close the dialog and trigger result callback."""
        # Emit close event
        close_event = UIEvent(
            UIEventType.DIALOG_CLOSED,
            source=self,
            data={'result': self.result, 'result_data': self.result_data}
        )
        self.emit_event('close', close_event)
        
        # Call result callback
        if self._on_result:
            try:
                self._on_result(self, self.result, self.result_data)
            except Exception as e:
                print(f"Error in dialog result handler: {e}")
        
        # Hide dialog
        self.visible = False
    
    def show(self) -> None:
        """Show the dialog."""
        self.visible = True
        self.result = DialogResult.NONE
        self.result_data = None
        
        # Focus first button if available
        for child in self.children:
            if isinstance(child, Panel):
                for button in child.children:
                    if isinstance(button, Button):
                        button.set_state(ComponentState.FOCUSED)
                        break
                break
        
        # Emit open event
        open_event = UIEvent(UIEventType.DIALOG_OPENED, source=self)
        self.emit_event('open', open_event)
    
    def hide(self) -> None:
        """Hide the dialog without setting a result."""
        self.visible = False
    
    def center_in_area(self, area_width: int, area_height: int) -> None:
        """Center the dialog in the given area.
        
        Args:
            area_width (int): Area width
            area_height (int): Area height
        """
        self.x = max(0, (area_width - self.width) // 2)
        self.y = max(0, (area_height - self.height) // 2)
    
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
        
        # Handle common dialog shortcuts
        if key_lower in ('enter', 'return'):
            # Activate focused button or default action
            for child in self.children:
                if isinstance(child, Panel):
                    for button in child.children:
                        if isinstance(button, Button) and button.state == ComponentState.FOCUSED:
                            button.click()
                            return True
            
            # Default to OK/Yes action
            if self.dialog_type == DialogType.CONFIRMATION:
                self.result = DialogResult.YES
            else:
                self.result = DialogResult.OK
            self._close_dialog()
            return True
        
        elif key_lower == 'escape':
            # Cancel/close dialog
            if self.dialog_type == DialogType.CONFIRMATION:
                self.result = DialogResult.NO
            else:
                self.result = DialogResult.CANCEL
            self._close_dialog()
            return True
        
        elif key_lower in ('tab', 'left', 'right'):
            # Navigate between buttons
            self._navigate_buttons(key_lower in ('tab', 'right'))
            return True
        
        # Let parent handle other keys (including button focus)
        return super().on_key_event(key, pressed)
    
    def _navigate_buttons(self, forward: bool = True) -> None:
        """Navigate between dialog buttons.
        
        Args:
            forward (bool): True to navigate forward, False for backward
        """
        buttons = []
        
        # Collect all buttons
        for child in self.children:
            if isinstance(child, Panel):
                for button in child.children:
                    if isinstance(button, Button):
                        buttons.append(button)
        
        if not buttons:
            return
        
        # Find currently focused button
        current_index = -1
        for i, button in enumerate(buttons):
            if button.state == ComponentState.FOCUSED:
                current_index = i
                break
        
        # Move focus
        if forward:
            next_index = (current_index + 1) % len(buttons)
        else:
            next_index = (current_index - 1) % len(buttons)
        
        # Update focus
        for i, button in enumerate(buttons):
            if i == next_index:
                button.set_state(ComponentState.FOCUSED)
            else:
                button.set_state(ComponentState.NORMAL)
    
    def render_self(self, surface: Surface) -> None:
        """Render the dialog.
        
        Args:
            surface (Surface): Surface to render to
        """
        # Render panel background and border
        super().render_self(surface)
        
        # Render message text if we have it
        if self.message and self.children:
            message_panel = self.children[0]  # First child should be message panel
            if isinstance(message_panel, Panel):
                self._render_message_text(surface, message_panel)
    
    def _render_message_text(self, surface: Surface, message_panel: Panel) -> None:
        """Render message text within the message panel.
        
        Args:
            surface (Surface): Surface to render to
            message_panel (Panel): Message panel component
        """
        abs_rect = message_panel.absolute_rect
        content_area = message_panel.content_area
        
        # Calculate text area
        text_x = abs_rect.x + 1
        text_y = abs_rect.y + 1
        text_width = content_area.width - 2
        text_height = content_area.height - 2
        
        # Simple word wrapping
        words = self.message.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= text_width:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Render lines
        fg_color, _ = self.get_style_colors()
        for i, line in enumerate(lines[:text_height]):
            surface.print_string(text_x, text_y + i, line, fg_color)
    
    @classmethod
    def show_message(cls, title: str, message: str, 
                    on_result: Optional[Callable[['Dialog', DialogResult, Any], None]] = None) -> 'Dialog':
        """Create and show a message dialog.
        
        Args:
            title (str): Dialog title
            message (str): Message text
            on_result (Callable, optional): Result callback
            
        Returns:
            Dialog: Created dialog instance
        """
        dialog = cls(
            title=title,
            message=message,
            dialog_type=DialogType.MESSAGE,
            on_result=on_result
        )
        dialog.show()
        return dialog
    
    @classmethod
    def show_confirmation(cls, title: str, message: str,
                         on_result: Optional[Callable[['Dialog', DialogResult, Any], None]] = None) -> 'Dialog':
        """Create and show a confirmation dialog.
        
        Args:
            title (str): Dialog title
            message (str): Message text
            on_result (Callable, optional): Result callback
            
        Returns:
            Dialog: Created dialog instance
        """
        dialog = cls(
            title=title,
            message=message,
            dialog_type=DialogType.CONFIRMATION,
            on_result=on_result
        )
        dialog.show()
        return dialog
    
    def __repr__(self) -> str:
        """String representation of dialog."""
        return (f"Dialog(title='{self.title}', type={self.dialog_type.name}, "
                f"result={self.result.name}, visible={self.visible})")
