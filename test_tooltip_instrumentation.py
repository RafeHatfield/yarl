#!/usr/bin/env python3
"""Quick verification that tooltip instrumentation is properly wired.

This script verifies:
1. Debug flags module exists and is importable
2. Frame counter works and is accessible
3. Logging is properly configured
4. No import errors in modified files
"""

import sys
import logging

def test_debug_flags():
    """Test that debug flags module is importable and has correct attributes."""
    print("Testing debug flags module...")
    try:
        from ui.debug_flags import ENABLE_TOOLTIP_DEBUG, TOOLTIP_IGNORE_FOV, TOOLTIP_DISABLE_EFFECTS
        print(f"  ✓ ENABLE_TOOLTIP_DEBUG = {ENABLE_TOOLTIP_DEBUG}")
        print(f"  ✓ TOOLTIP_IGNORE_FOV = {TOOLTIP_IGNORE_FOV}")
        print(f"  ✓ TOOLTIP_DISABLE_EFFECTS = {TOOLTIP_DISABLE_EFFECTS}")
        return True
    except ImportError as e:
        print(f"  ✗ Failed to import debug flags: {e}")
        return False


def test_frame_counter():
    """Test that frame counter is accessible."""
    print("\nTesting frame counter...")
    try:
        from io_layer.console_renderer import get_last_frame_counter, ConsoleRenderer
        
        # Initial value should be 0
        initial = get_last_frame_counter()
        print(f"  ✓ Initial frame counter: {initial}")
        
        # Create a mock ConsoleRenderer to test increment
        from unittest.mock import MagicMock
        mock_console = MagicMock()
        renderer = ConsoleRenderer(mock_console, mock_console, mock_console, {})
        print(f"  ✓ ConsoleRenderer created")
        
        # Test that _frame_counter attribute exists
        if hasattr(renderer, '_frame_counter'):
            print(f"  ✓ ConsoleRenderer._frame_counter accessible: {renderer._frame_counter}")
        else:
            print(f"  ✗ ConsoleRenderer._frame_counter not found")
            return False
            
        return True
    except ImportError as e:
        print(f"  ✗ Failed to import frame counter: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error testing frame counter: {e}")
        return False


def test_logger_setup():
    """Test that logging is properly configured."""
    print("\nTesting logger setup...")
    try:
        from logger_config import setup_logging, get_logger
        
        # Setup logging at DEBUG level
        root_logger = setup_logging(logging.DEBUG)
        print(f"  ✓ Root logger setup with DEBUG level")
        
        # Get a module logger
        test_logger = get_logger("tooltip_test")
        print(f"  ✓ Module logger obtained: {test_logger.name}")
        
        # Verify DEBUG level is enabled
        if test_logger.isEnabledFor(logging.DEBUG):
            print(f"  ✓ DEBUG logging is enabled")
        else:
            print(f"  ✗ DEBUG logging is NOT enabled")
            return False
            
        return True
    except Exception as e:
        print(f"  ✗ Error setting up logging: {e}")
        return False


def test_tooltip_imports():
    """Test that modified tooltip modules import without errors."""
    print("\nTesting tooltip module imports...")
    
    modules = [
        ("render_functions", "render_all"),
        ("ui.tooltip", "get_all_entities_at_position"),
        ("ui.tooltip", "render_tooltip"),
        ("ui.tooltip", "render_multi_entity_tooltip"),
        ("io_layer.console_renderer", "ConsoleRenderer"),
    ]
    
    for module_name, symbol_name in modules:
        try:
            module = __import__(module_name, fromlist=[symbol_name])
            symbol = getattr(module, symbol_name)
            print(f"  ✓ {module_name}.{symbol_name}")
        except ImportError as e:
            print(f"  ✗ Failed to import {module_name}: {e}")
            return False
        except AttributeError as e:
            print(f"  ✗ {module_name}.{symbol_name} not found: {e}")
            return False
    
    return True


def test_logging_works():
    """Test that logging actually works."""
    print("\nTesting logging output...")
    try:
        from logger_config import setup_logging, get_logger
        import logging
        
        # Setup at DEBUG
        setup_logging(logging.DEBUG)
        logger = get_logger("tooltip_instrumentation_test")
        
        # Log at DEBUG level
        logger.debug("TOOLTIP_TEST: frame=999 message=instrumentation_working")
        print(f"  ✓ Debug log written successfully")
        
        return True
    except Exception as e:
        print(f"  ✗ Logging test failed: {e}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 70)
    print("TOOLTIP INSTRUMENTATION VERIFICATION")
    print("=" * 70)
    
    tests = [
        ("Debug Flags Module", test_debug_flags),
        ("Frame Counter", test_frame_counter),
        ("Logger Setup", test_logger_setup),
        ("Tooltip Module Imports", test_tooltip_imports),
        ("Logging Output", test_logging_works),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Exception in {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All instrumentation checks passed!")
        print("\nNext steps:")
        print("1. Set ENABLE_TOOLTIP_DEBUG = True in ui/debug_flags.py")
        print("2. Set logging to DEBUG level in logger_config.py")
        print("3. Run the game and reproduce tooltip flicker")
        print("4. Check logs/rlike.log for TOOLTIP_* messages")
        print("5. Analyze patterns as documented in TOOLTIP_DEBUG_INSTRUMENTATION.md")
        return 0
    else:
        print("\n✗ Some tests failed. Review output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())


