#!/usr/bin/env python3
"""Demonstration of the new rendering abstraction layer.

This script shows how the new rendering abstraction works and demonstrates
its key features including backend abstraction, surface operations, color
handling, and compatibility with existing code.
"""

import sys
import os

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rendering import RenderBackend, LibtcodBackend, Surface, Color, Colors
from rendering.surface import Rect
from rendering.compatibility import (
    initialize_rendering_backend, get_rendering_backend,
    convert_libtcod_color, get_legacy_color_mapping
)


def demo_color_system():
    """Demonstrate the Color system features."""
    print("🎨 Color System Demo")
    print("=" * 50)
    
    # Basic color creation
    red = Color(255, 0, 0)
    print(f"Red color: {red} -> {red.to_hex()}")
    
    # Color from hex
    blue = Color.from_hex("#0000FF")
    print(f"Blue from hex: {blue} -> {blue.to_tuple()}")
    
    # Color interpolation
    purple = red.lerp(blue, 0.5)
    print(f"Red + Blue interpolation: {purple} -> {purple.to_hex()}")
    
    # Color manipulation
    dark_red = red.darken(0.3)
    light_red = red.lighten(0.3)
    print(f"Dark red: {dark_red.to_hex()}, Light red: {light_red.to_hex()}")
    
    # Predefined colors
    print(f"Predefined colors: Black={Colors.BLACK.to_hex()}, White={Colors.WHITE.to_hex()}")
    print()


def demo_surface_operations():
    """Demonstrate Surface operations."""
    print("🖼️  Surface Operations Demo")
    print("=" * 50)
    
    # Create a mock surface for demonstration
    from tests.test_rendering_abstraction import MockSurface
    surface = MockSurface(20, 10)
    
    # Basic character operations
    surface.set_char(5, 5, '@', Colors.YELLOW, Colors.DARK_GROUND)
    print(f"Character at (5,5): '{surface.get_char(5, 5)}'")
    
    # String printing
    surface.print_string(2, 2, "Hello World!", Colors.WHITE)
    print("String printed at (2,2): 'Hello World!'")
    
    # Rectangle filling
    rect = Rect(10, 3, 5, 3)
    surface.fill_rect(rect, '#', Colors.RED, Colors.BLACK)
    print(f"Filled rectangle: {rect.width}x{rect.height} at ({rect.x},{rect.y})")
    
    # Clipping demonstration
    clip_rect = Rect(0, 0, 10, 5)
    surface.set_clip_rect(clip_rect)
    print(f"Clipping enabled: {surface.get_clip_rect()}")
    
    # Test clipping
    surface.set_char(15, 7, 'X')  # Should be clipped
    surface.set_char(5, 3, 'O')   # Should not be clipped
    print(f"Character at (15,7) after clipping: '{surface.get_char(15, 7)}' (should be empty)")
    print(f"Character at (5,3) after clipping: '{surface.get_char(5, 3)}' (should be 'O')")
    print()


def demo_backend_abstraction():
    """Demonstrate backend abstraction."""
    print("🔧 Backend Abstraction Demo")
    print("=" * 50)
    
    # Create backend without initializing (for demo purposes)
    backend = LibtcodBackend(80, 25, "Demo Game")
    
    print(f"Backend type: {type(backend).__name__}")
    print(f"Dimensions: {backend.width}x{backend.height}")
    print(f"Title: {backend.title}")
    print(f"Initialized: {backend._initialized}")
    
    # Check feature support
    features = ['console_rendering', 'custom_fonts', 'image_loading', 'nonexistent_feature']
    for feature in features:
        supported = backend.supports_feature(feature)
        print(f"Feature '{feature}': {'✅ Supported' if supported else '❌ Not supported'}")
    
    # Get performance stats
    stats = backend.get_render_stats()
    print(f"Performance stats: {stats}")
    print()


def demo_compatibility_layer():
    """Demonstrate compatibility layer features."""
    print("🔄 Compatibility Layer Demo")
    print("=" * 50)
    
    # Color conversion
    libtcod_color = (255, 128, 64)  # Simulate libtcod color tuple
    converted = convert_libtcod_color(libtcod_color)
    print(f"Converted libtcod color {libtcod_color} -> {converted}")
    
    # Legacy color mapping
    color_mapping = get_legacy_color_mapping()
    print(f"Legacy colors available: {list(color_mapping.keys())[:5]}... ({len(color_mapping)} total)")
    print(f"Legacy 'red' color: {color_mapping['red']}")
    
    # Backend management (without actual initialization)
    print("Backend management functions available:")
    print("- initialize_rendering_backend()")
    print("- get_rendering_backend()")
    print("- shutdown_rendering_backend()")
    print()


def demo_rect_operations():
    """Demonstrate Rect utility operations."""
    print("📐 Rectangle Operations Demo")
    print("=" * 50)
    
    rect1 = Rect(10, 10, 20, 15)
    rect2 = Rect(20, 15, 15, 10)
    rect3 = Rect(50, 50, 10, 10)
    
    print(f"Rect1: {rect1.width}x{rect1.height} at ({rect1.x},{rect1.y})")
    print(f"  Properties: left={rect1.left}, right={rect1.right}, top={rect1.top}, bottom={rect1.bottom}")
    print(f"  Center: {rect1.center}")
    
    # Point containment
    test_points = [(15, 15), (5, 5), (25, 20)]
    for point in test_points:
        contained = rect1.contains(point[0], point[1])
        print(f"  Point {point}: {'✅ Inside' if contained else '❌ Outside'}")
    
    # Rectangle intersection
    print(f"Rect1 intersects Rect2: {'✅ Yes' if rect1.intersects(rect2) else '❌ No'}")
    print(f"Rect1 intersects Rect3: {'✅ Yes' if rect1.intersects(rect3) else '❌ No'}")
    print()


def main():
    """Run all demonstrations."""
    print("🚀 Rendering Abstraction Layer Demonstration")
    print("=" * 60)
    print("This demo shows the key features of the new rendering abstraction")
    print("that enables future GUI support while maintaining libtcod compatibility.")
    print()
    
    try:
        demo_color_system()
        demo_surface_operations()
        demo_backend_abstraction()
        demo_compatibility_layer()
        demo_rect_operations()
        
        print("✅ All demonstrations completed successfully!")
        print()
        print("🎯 Key Benefits:")
        print("- ✅ Full backward compatibility with existing libtcod code")
        print("- ✅ Clean abstraction enabling future GUI implementations")
        print("- ✅ Resolution-independent drawing operations")
        print("- ✅ Cross-platform color handling and conversion")
        print("- ✅ Comprehensive testing and error handling")
        print("- ✅ Performance monitoring and feature detection")
        print()
        print("🔮 Future Possibilities:")
        print("- 🎨 Pygame/SDL backend for sprite-based graphics")
        print("- 🖥️  Modern OpenGL backend for hardware acceleration")
        print("- 🌐 Web backend for browser-based gameplay")
        print("- 📱 Mobile backends for touch interfaces")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
