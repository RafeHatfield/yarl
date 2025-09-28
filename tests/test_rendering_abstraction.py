"""Tests for the rendering abstraction layer.

This module contains comprehensive tests for the new rendering abstraction
system, including backend interfaces, surface operations, color handling,
and compatibility layers.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rendering import RenderBackend, Surface, Color, Colors, LibtcodBackend
from rendering.surface import Rect
from rendering.compatibility import (
    initialize_rendering_backend, get_rendering_backend, 
    shutdown_rendering_backend, convert_libtcod_color,
    get_legacy_color_mapping, RenderingMigrationHelper
)


class TestColor:
    """Test cases for the Color class."""
    
    def test_color_creation(self):
        """Test basic color creation."""
        color = Color(255, 128, 64)
        assert color.r == 255
        assert color.g == 128
        assert color.b == 64
    
    def test_color_clamping(self):
        """Test that color values are clamped to valid range."""
        color = Color.create(-10, 300, 128)
        assert color.r == 0
        assert color.g == 255
        assert color.b == 128
    
    def test_color_from_tuple(self):
        """Test creating color from RGB tuple."""
        color = Color.from_tuple((255, 0, 128))
        assert color.r == 255
        assert color.g == 0
        assert color.b == 128
    
    def test_color_from_hex(self):
        """Test creating color from hex string."""
        color = Color.from_hex("#FF0080")
        assert color.r == 255
        assert color.g == 0
        assert color.b == 128
        
        # Test without # prefix
        color2 = Color.from_hex("FF0080")
        assert color2 == color
    
    def test_color_from_hex_invalid(self):
        """Test error handling for invalid hex strings."""
        with pytest.raises(ValueError):
            Color.from_hex("invalid")
    
    def test_color_to_tuple(self):
        """Test converting color to tuple."""
        color = Color(255, 128, 64)
        assert color.to_tuple() == (255, 128, 64)
    
    def test_color_to_hex(self):
        """Test converting color to hex string."""
        color = Color(255, 128, 64)
        assert color.to_hex() == "#FF8040"
    
    def test_color_lerp(self):
        """Test color interpolation."""
        red = Color(255, 0, 0)
        blue = Color(0, 0, 255)
        
        # Midpoint should be purple
        purple = red.lerp(blue, 0.5)
        assert purple.r == 127 or purple.r == 128  # Allow for rounding
        assert purple.g == 0
        assert purple.b == 127 or purple.b == 128
    
    def test_color_darken(self):
        """Test color darkening."""
        color = Color(200, 200, 200)
        darker = color.darken(0.5)
        assert darker.r == 100
        assert darker.g == 100
        assert darker.b == 100
    
    def test_color_lighten(self):
        """Test color lightening."""
        color = Color(100, 100, 100)
        lighter = color.lighten(0.5)
        assert lighter.r == 177 or lighter.r == 178  # Allow for rounding
        assert lighter.g == 177 or lighter.g == 178
        assert lighter.b == 177 or lighter.b == 178
    
    def test_color_constants(self):
        """Test predefined color constants."""
        assert Colors.BLACK == Color(0, 0, 0)
        assert Colors.WHITE == Color(255, 255, 255)
        assert Colors.RED == Color(255, 0, 0)
        assert Colors.LIGHT_GREEN == Color(63, 255, 63)


class TestRect:
    """Test cases for the Rect class."""
    
    def test_rect_creation(self):
        """Test basic rectangle creation."""
        rect = Rect(10, 20, 30, 40)
        assert rect.x == 10
        assert rect.y == 20
        assert rect.width == 30
        assert rect.height == 40
    
    def test_rect_properties(self):
        """Test rectangle property calculations."""
        rect = Rect(10, 20, 30, 40)
        assert rect.left == 10
        assert rect.right == 40
        assert rect.top == 20
        assert rect.bottom == 60
        assert rect.center == (25, 40)
    
    def test_rect_contains(self):
        """Test point containment checking."""
        rect = Rect(10, 20, 30, 40)
        assert rect.contains(15, 25) == True
        assert rect.contains(5, 25) == False
        assert rect.contains(15, 15) == False
        assert rect.contains(45, 25) == False
        assert rect.contains(15, 65) == False
    
    def test_rect_intersects(self):
        """Test rectangle intersection checking."""
        rect1 = Rect(10, 10, 20, 20)
        rect2 = Rect(20, 20, 20, 20)  # Overlapping
        rect3 = Rect(40, 40, 20, 20)  # Non-overlapping
        
        assert rect1.intersects(rect2) == True
        assert rect1.intersects(rect3) == False


class MockSurface(Surface):
    """Mock surface implementation for testing."""
    
    def __init__(self, width: int, height: int):
        super().__init__(width, height)
        self._chars = {}
        self._fg_colors = {}
        self._bg_colors = {}
    
    def clear(self, color=None):
        self._chars.clear()
        self._fg_colors.clear()
        self._bg_colors.clear()
    
    def set_char(self, x, y, char, fg_color=None, bg_color=None):
        if not self._is_clipped(x, y):
            self._chars[(x, y)] = char
            if fg_color:
                self._fg_colors[(x, y)] = fg_color
            if bg_color:
                self._bg_colors[(x, y)] = bg_color
    
    def get_char(self, x, y):
        return self._chars.get((x, y), ' ')
    
    def set_bg_color(self, x, y, color):
        if not self._is_clipped(x, y):
            self._bg_colors[(x, y)] = color
    
    def set_fg_color(self, x, y, color):
        if not self._is_clipped(x, y):
            self._fg_colors[(x, y)] = color
    
    def blit(self, source, dest_x, dest_y, source_rect=None, alpha=1.0):
        pass  # Mock implementation


class TestSurface:
    """Test cases for the Surface class."""
    
    def test_surface_creation(self):
        """Test basic surface creation."""
        surface = MockSurface(80, 25)
        assert surface.width == 80
        assert surface.height == 25
        assert surface.size == (80, 25)
    
    def test_surface_rect(self):
        """Test surface rectangle property."""
        surface = MockSurface(80, 25)
        rect = surface.rect
        assert rect.x == 0
        assert rect.y == 0
        assert rect.width == 80
        assert rect.height == 25
    
    def test_surface_clipping(self):
        """Test surface clipping functionality."""
        surface = MockSurface(80, 25)
        
        # No clipping initially
        assert surface.get_clip_rect() is None
        assert surface._is_clipped(10, 10) == False
        
        # Set clipping rectangle
        clip_rect = Rect(5, 5, 10, 10)
        surface.set_clip_rect(clip_rect)
        assert surface.get_clip_rect() == clip_rect
        assert surface._is_clipped(10, 10) == False  # Inside clip
        assert surface._is_clipped(20, 20) == True   # Outside clip
    
    def test_surface_char_operations(self):
        """Test character setting and getting."""
        surface = MockSurface(80, 25)
        
        surface.set_char(10, 10, 'X', Colors.RED, Colors.BLUE)
        assert surface.get_char(10, 10) == 'X'
        assert surface._fg_colors.get((10, 10)) == Colors.RED
        assert surface._bg_colors.get((10, 10)) == Colors.BLUE
    
    def test_surface_print_string(self):
        """Test string printing."""
        surface = MockSurface(80, 25)
        
        surface.print_string(10, 10, "Hello", Colors.WHITE)
        assert surface.get_char(10, 10) == 'H'
        assert surface.get_char(11, 10) == 'e'
        assert surface.get_char(12, 10) == 'l'
        assert surface.get_char(13, 10) == 'l'
        assert surface.get_char(14, 10) == 'o'
    
    def test_surface_fill_rect(self):
        """Test rectangle filling."""
        surface = MockSurface(80, 25)
        
        rect = Rect(10, 10, 5, 3)
        surface.fill_rect(rect, 'X', Colors.RED, Colors.BLUE)
        
        # Check that rectangle is filled
        for y in range(10, 13):
            for x in range(10, 15):
                assert surface.get_char(x, y) == 'X'
                assert surface._fg_colors.get((x, y)) == Colors.RED
                assert surface._bg_colors.get((x, y)) == Colors.BLUE


class MockBackend(RenderBackend):
    """Mock backend implementation for testing."""
    
    def __init__(self, width: int, height: int, title: str = "Test"):
        super().__init__(width, height, title)
        self.initialized = False
        self.main_surface = None
    
    def initialize(self):
        self.initialized = True
        self.main_surface = MockSurface(self.width, self.height)
        self._initialized = True
        return True
    
    def shutdown(self):
        self.initialized = False
        self.main_surface = None
        self._initialized = False
    
    def create_surface(self, width, height):
        return MockSurface(width, height)
    
    def get_main_surface(self):
        return self.main_surface
    
    def present(self):
        pass
    
    def clear(self, color=None):
        if self.main_surface:
            self.main_surface.clear(color)
    
    def is_window_closed(self):
        return False
    
    def set_font(self, font_path, flags=0):
        return True
    
    def load_image(self, image_path):
        return "mock_image"
    
    def get_key_input(self):
        return {'key': None}
    
    def get_mouse_input(self):
        return {'mouse': None}


class TestRenderBackend:
    """Test cases for the RenderBackend interface."""
    
    def test_backend_creation(self):
        """Test backend creation and properties."""
        backend = MockBackend(80, 25, "Test Game")
        assert backend.width == 80
        assert backend.height == 25
        assert backend.title == "Test Game"
        assert backend._initialized == False
    
    def test_backend_initialization(self):
        """Test backend initialization."""
        backend = MockBackend(80, 25)
        assert backend.initialize() == True
        assert backend._initialized == True
        assert backend.main_surface is not None
    
    def test_backend_surface_creation(self):
        """Test surface creation."""
        backend = MockBackend(80, 25)
        backend.initialize()
        
        surface = backend.create_surface(40, 20)
        assert surface.width == 40
        assert surface.height == 20
    
    def test_backend_stats(self):
        """Test performance statistics."""
        backend = MockBackend(80, 25)
        stats = backend.get_render_stats()
        
        assert 'backend_type' in stats
        assert 'width' in stats
        assert 'height' in stats
        assert stats['width'] == 80
        assert stats['height'] == 25


@patch('rendering.libtcod_backend.libtcod')
class TestLibtcodBackend:
    """Test cases for the LibtcodBackend implementation."""
    
    def test_libtcod_backend_creation(self, mock_libtcod):
        """Test libtcod backend creation."""
        backend = LibtcodBackend(80, 25, "Test Game")
        assert backend.width == 80
        assert backend.height == 25
        assert backend.title == "Test Game"
    
    def test_libtcod_backend_initialization(self, mock_libtcod):
        """Test libtcod backend initialization."""
        backend = LibtcodBackend(80, 25)
        
        # Mock successful initialization
        mock_libtcod.console_init_root.return_value = None
        
        result = backend.initialize()
        assert result == True
        assert backend._initialized == True
        
        # Verify libtcod calls
        mock_libtcod.console_init_root.assert_called_once_with(80, 25, "Game", False)
    
    def test_libtcod_backend_features(self, mock_libtcod):
        """Test feature support checking."""
        backend = LibtcodBackend(80, 25)
        
        assert backend.supports_feature('console_rendering') == True
        assert backend.supports_feature('custom_fonts') == True
        assert backend.supports_feature('nonexistent_feature') == False


class TestCompatibilityLayer:
    """Test cases for the compatibility layer."""
    
    def test_color_conversion(self):
        """Test libtcod color conversion."""
        # Test tuple conversion
        color = convert_libtcod_color((255, 128, 64))
        assert color == Color(255, 128, 64)
        
        # Test object with r,g,b attributes
        mock_color = Mock()
        mock_color.r = 255
        mock_color.g = 128
        mock_color.b = 64
        
        color = convert_libtcod_color(mock_color)
        assert color == Color(255, 128, 64)
    
    def test_legacy_color_mapping(self):
        """Test legacy color name mapping."""
        mapping = get_legacy_color_mapping()
        
        assert 'black' in mapping
        assert 'white' in mapping
        assert 'red' in mapping
        assert mapping['black'] == Colors.BLACK
        assert mapping['white'] == Colors.WHITE
        assert mapping['red'] == Colors.RED
    
    @patch('rendering.compatibility.LibtcodBackend')
    def test_backend_initialization(self, mock_backend_class):
        """Test global backend initialization."""
        mock_backend = Mock()
        mock_backend.initialize.return_value = True
        mock_backend_class.return_value = mock_backend
        
        backend = initialize_rendering_backend(80, 25, "Test")
        
        assert backend == mock_backend
        assert get_rendering_backend() == mock_backend
        mock_backend.initialize.assert_called_once()
        
        # Test shutdown
        shutdown_rendering_backend()
        assert get_rendering_backend() is None
        mock_backend.shutdown.assert_called_once()
    
    def test_migration_helper(self):
        """Test rendering migration helper."""
        backend = MockBackend(80, 25)
        backend.initialize()
        
        helper = RenderingMigrationHelper(backend)
        
        # Test performance info
        info = helper.get_performance_info()
        assert 'backend_type' in info
        assert 'migration_status' in info
        assert info['compatibility_mode'] == True


if __name__ == '__main__':
    pytest.main([__file__])
