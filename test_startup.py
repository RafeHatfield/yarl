#!/usr/bin/env python3
"""Quick game startup test script.

This script provides a fast way to test if the game can start up correctly
without running the full test suite. Useful for quick verification after
code changes.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))


def test_game_startup():
    """Test basic game startup without GUI."""
    print("🧪 Testing game startup...")
    
    try:
        # Test 1: Basic imports
        from loader_functions.initialize_new_game import get_game_variables, get_constants
        from fov_functions import initialize_fov
        print("✅ Core imports successful")
        
        # Test 2: Constants loading
        constants = get_constants()
        print("✅ Constants loaded")
        
        # Test 3: Game variables creation
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        print("✅ Game variables created")
        
        # Test 4: FOV system
        fov_map = initialize_fov(game_map)
        print("✅ FOV system initialized")
        
        # Test 5: Engine creation
        from engine_integration import create_game_engine, initialize_game_engine
        
        class MockConsole:
            pass
        
        mock_sidebar = MockConsole()
        mock_viewport = MockConsole()
        mock_status = MockConsole()
        engine = create_game_engine(constants, mock_sidebar, mock_viewport, mock_status)
        initialize_game_engine(engine, player, entities, game_map, message_log, game_state, constants)
        print("✅ Game engine initialized")
        
        print("\n🎉 Game startup test PASSED - All systems ready!")
        
    except Exception as e:
        print(f"\n❌ Game startup test FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise AssertionError(f"Game startup failed: {e}")


if __name__ == "__main__":
    try:
        test_game_startup()
        sys.exit(0)
    except Exception:
        sys.exit(1)
