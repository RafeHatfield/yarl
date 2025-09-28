"""Layout management system for UI components.

This module provides various layout managers that automatically position
and size UI components according to different strategies. Layout managers
enable responsive and flexible UI designs that work across different
screen sizes and component configurations.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from rendering.surface import Rect
from .component import Component


class LayoutDirection(Enum):
    """Layout direction enumeration."""
    HORIZONTAL = auto()
    VERTICAL = auto()


class Alignment(Enum):
    """Alignment enumeration."""
    START = auto()      # Left/Top
    CENTER = auto()     # Center
    END = auto()        # Right/Bottom
    STRETCH = auto()    # Fill available space


@dataclass
class LayoutConstraints:
    """Layout constraints for component positioning and sizing."""
    min_width: Optional[int] = None
    max_width: Optional[int] = None
    min_height: Optional[int] = None
    max_height: Optional[int] = None
    preferred_width: Optional[int] = None
    preferred_height: Optional[int] = None
    
    # Margins
    margin_left: int = 0
    margin_right: int = 0
    margin_top: int = 0
    margin_bottom: int = 0
    
    # Alignment
    horizontal_alignment: Alignment = Alignment.START
    vertical_alignment: Alignment = Alignment.START
    
    # Flexibility (for flow layouts)
    flex_grow: float = 0.0  # How much to grow
    flex_shrink: float = 1.0  # How much to shrink
    
    @property
    def margin_width(self) -> int:
        """Total horizontal margin."""
        return self.margin_left + self.margin_right
    
    @property
    def margin_height(self) -> int:
        """Total vertical margin."""
        return self.margin_top + self.margin_bottom
    
    def clamp_width(self, width: int) -> int:
        """Clamp width to constraints.
        
        Args:
            width (int): Desired width
            
        Returns:
            int: Clamped width
        """
        if self.min_width is not None:
            width = max(width, self.min_width)
        if self.max_width is not None:
            width = min(width, self.max_width)
        return width
    
    def clamp_height(self, height: int) -> int:
        """Clamp height to constraints.
        
        Args:
            height (int): Desired height
            
        Returns:
            int: Clamped height
        """
        if self.min_height is not None:
            height = max(height, self.min_height)
        if self.max_height is not None:
            height = min(height, self.max_height)
        return height


class Layout(ABC):
    """Abstract base class for layout managers.
    
    Layout managers are responsible for positioning and sizing child
    components within a container according to specific rules and
    strategies.
    """
    
    def __init__(self, padding: int = 0):
        """Initialize the layout manager.
        
        Args:
            padding (int): Padding around the layout area
        """
        self.padding = padding
        self.component_constraints: Dict[Component, LayoutConstraints] = {}
    
    def set_constraints(self, component: Component, constraints: LayoutConstraints) -> None:
        """Set layout constraints for a component.
        
        Args:
            component (Component): Component to constrain
            constraints (LayoutConstraints): Layout constraints
        """
        self.component_constraints[component] = constraints
    
    def get_constraints(self, component: Component) -> LayoutConstraints:
        """Get layout constraints for a component.
        
        Args:
            component (Component): Component to get constraints for
            
        Returns:
            LayoutConstraints: Component constraints (default if not set)
        """
        return self.component_constraints.get(component, LayoutConstraints())
    
    @abstractmethod
    def layout(self, container: Component) -> None:
        """Layout all child components within the container.
        
        Args:
            container (Component): Container component
        """
        pass
    
    def get_layout_area(self, container: Component) -> Rect:
        """Get the available layout area within the container.
        
        Args:
            container (Component): Container component
            
        Returns:
            Rect: Available layout area
        """
        return Rect(
            self.padding,
            self.padding,
            max(0, container.width - 2 * self.padding),
            max(0, container.height - 2 * self.padding)
        )


class AbsoluteLayout(Layout):
    """Absolute positioning layout manager.
    
    This layout manager positions components at their exact specified
    coordinates without any automatic positioning. It's useful for
    precise control over component placement.
    """
    
    def layout(self, container: Component) -> None:
        """Layout components using absolute positioning.
        
        Args:
            container (Component): Container component
        """
        # Absolute layout doesn't change component positions
        # Components are positioned exactly where they're placed
        layout_area = self.get_layout_area(container)
        
        for child in container.children:
            constraints = self.get_constraints(child)
            
            # Apply size constraints if specified
            if constraints.preferred_width is not None:
                child.width = constraints.clamp_width(constraints.preferred_width)
            if constraints.preferred_height is not None:
                child.height = constraints.clamp_height(constraints.preferred_height)
            
            # Ensure child stays within layout area if needed
            child.x = max(layout_area.x, min(child.x, layout_area.x + layout_area.width - child.width))
            child.y = max(layout_area.y, min(child.y, layout_area.y + layout_area.height - child.height))


class FlowLayout(Layout):
    """Flow layout manager for sequential component arrangement.
    
    This layout manager arranges components in a flowing manner,
    either horizontally or vertically, with automatic wrapping
    when space runs out.
    """
    
    def __init__(self, direction: LayoutDirection = LayoutDirection.HORIZONTAL,
                 spacing: int = 1, wrap: bool = True, padding: int = 0):
        """Initialize the flow layout.
        
        Args:
            direction (LayoutDirection): Primary layout direction
            spacing (int): Spacing between components
            wrap (bool): Whether to wrap to next line/column
            padding (int): Padding around layout area
        """
        super().__init__(padding)
        self.direction = direction
        self.spacing = spacing
        self.wrap = wrap
    
    def layout(self, container: Component) -> None:
        """Layout components in a flowing arrangement.
        
        Args:
            container (Component): Container component
        """
        if not container.children:
            return
        
        layout_area = self.get_layout_area(container)
        
        if self.direction == LayoutDirection.HORIZONTAL:
            self._layout_horizontal(container.children, layout_area)
        else:
            self._layout_vertical(container.children, layout_area)
    
    def _layout_horizontal(self, children: List[Component], area: Rect) -> None:
        """Layout components horizontally.
        
        Args:
            children (List[Component]): Child components
            area (Rect): Available layout area
        """
        current_x = area.x
        current_y = area.y
        row_height = 0
        
        for child in children:
            constraints = self.get_constraints(child)
            
            # Apply preferred size if specified
            if constraints.preferred_width is not None:
                child.width = constraints.clamp_width(constraints.preferred_width)
            if constraints.preferred_height is not None:
                child.height = constraints.clamp_height(constraints.preferred_height)
            
            # Check if we need to wrap
            if (self.wrap and current_x + child.width > area.x + area.width and 
                current_x > area.x):
                current_x = area.x
                current_y += row_height + self.spacing
                row_height = 0
            
            # Position the child
            child.x = current_x + constraints.margin_left
            child.y = current_y + constraints.margin_top
            
            # Update position for next child
            current_x += child.width + constraints.margin_width + self.spacing
            row_height = max(row_height, child.height + constraints.margin_height)
    
    def _layout_vertical(self, children: List[Component], area: Rect) -> None:
        """Layout components vertically.
        
        Args:
            children (List[Component]): Child components
            area (Rect): Available layout area
        """
        current_x = area.x
        current_y = area.y
        column_width = 0
        
        for child in children:
            constraints = self.get_constraints(child)
            
            # Apply preferred size if specified
            if constraints.preferred_width is not None:
                child.width = constraints.clamp_width(constraints.preferred_width)
            if constraints.preferred_height is not None:
                child.height = constraints.clamp_height(constraints.preferred_height)
            
            # Check if we need to wrap
            if (self.wrap and current_y + child.height > area.y + area.height and 
                current_y > area.y):
                current_y = area.y
                current_x += column_width + self.spacing
                column_width = 0
            
            # Position the child
            child.x = current_x + constraints.margin_left
            child.y = current_y + constraints.margin_top
            
            # Update position for next child
            current_y += child.height + constraints.margin_height + self.spacing
            column_width = max(column_width, child.width + constraints.margin_width)


class GridLayout(Layout):
    """Grid layout manager for tabular component arrangement.
    
    This layout manager arranges components in a grid with specified
    rows and columns, providing precise control over component
    placement and sizing.
    """
    
    def __init__(self, rows: int, columns: int, spacing: int = 1, padding: int = 0):
        """Initialize the grid layout.
        
        Args:
            rows (int): Number of rows in the grid
            columns (int): Number of columns in the grid
            spacing (int): Spacing between grid cells
            padding (int): Padding around layout area
        """
        super().__init__(padding)
        self.rows = rows
        self.columns = columns
        self.spacing = spacing
        self.grid_assignments: Dict[Component, Tuple[int, int]] = {}
    
    def set_grid_position(self, component: Component, row: int, column: int) -> None:
        """Set the grid position for a component.
        
        Args:
            component (Component): Component to position
            row (int): Grid row (0-based)
            column (int): Grid column (0-based)
        """
        if 0 <= row < self.rows and 0 <= column < self.columns:
            self.grid_assignments[component] = (row, column)
    
    def layout(self, container: Component) -> None:
        """Layout components in a grid arrangement.
        
        Args:
            container (Component): Container component
        """
        if not container.children:
            return
        
        layout_area = self.get_layout_area(container)
        
        # Calculate cell dimensions
        total_spacing_width = (self.columns - 1) * self.spacing
        total_spacing_height = (self.rows - 1) * self.spacing
        
        cell_width = (layout_area.width - total_spacing_width) // self.columns
        cell_height = (layout_area.height - total_spacing_height) // self.rows
        
        # Auto-assign components to grid positions if not explicitly set
        auto_row, auto_col = 0, 0
        
        for child in container.children:
            # Get or assign grid position
            if child in self.grid_assignments:
                row, col = self.grid_assignments[child]
            else:
                row, col = auto_row, auto_col
                auto_col += 1
                if auto_col >= self.columns:
                    auto_col = 0
                    auto_row += 1
                if auto_row >= self.rows:
                    break  # No more space in grid
            
            # Calculate cell position
            cell_x = layout_area.x + col * (cell_width + self.spacing)
            cell_y = layout_area.y + row * (cell_height + self.spacing)
            
            constraints = self.get_constraints(child)
            
            # Size the component
            if constraints.preferred_width is not None:
                child.width = constraints.clamp_width(constraints.preferred_width)
            else:
                child.width = constraints.clamp_width(cell_width - constraints.margin_width)
            
            if constraints.preferred_height is not None:
                child.height = constraints.clamp_height(constraints.preferred_height)
            else:
                child.height = constraints.clamp_height(cell_height - constraints.margin_height)
            
            # Position the component within the cell based on alignment
            if constraints.horizontal_alignment == Alignment.CENTER:
                child.x = cell_x + (cell_width - child.width) // 2
            elif constraints.horizontal_alignment == Alignment.END:
                child.x = cell_x + cell_width - child.width - constraints.margin_right
            else:  # START or STRETCH
                child.x = cell_x + constraints.margin_left
            
            if constraints.vertical_alignment == Alignment.CENTER:
                child.y = cell_y + (cell_height - child.height) // 2
            elif constraints.vertical_alignment == Alignment.END:
                child.y = cell_y + cell_height - child.height - constraints.margin_bottom
            else:  # START or STRETCH
                child.y = cell_y + constraints.margin_top
