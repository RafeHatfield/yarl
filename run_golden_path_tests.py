#!/usr/bin/env python3
"""Run golden-path integration tests for critical gameplay flows.

These are high-level integration tests that exercise basic player workflows
and fail loudly if fundamental gameplay mechanics break, even when unit tests
still pass.

The golden-path tests are designed to be fast (sub-second) and catch
regressions that would prevent a player from:
- Starting a new game
- Moving around the map
- Engaging in combat
- Using special items (wands)
- Discovering lore entities (murals, signposts)

Usage:
    python3 run_golden_path_tests.py          # Run all golden-path tests
    python3 run_golden_path_tests.py explore   # Run specific test group
"""

import sys
import subprocess
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_pytest_tests(test_path=None, verbose=True):
    """Run pytest for golden-path tests.
    
    Args:
        test_path: Specific test path to run (e.g., 'tests/test_golden_path_floor1.py::test_basic_explore_floor1')
        verbose: If True, use verbose output mode
        
    Returns:
        int: Exit code from pytest
    """
    cmd = [sys.executable, '-m', 'pytest']
    
    if test_path:
        cmd.append(test_path)
    else:
        # Run all golden-path tests
        cmd.append('tests/test_golden_path_floor1.py')
    
    if verbose:
        cmd.extend(['-v', '--tb=short'])
    else:
        cmd.append('-q')
    
    # Add color output
    cmd.append('--color=yes')
    
    return subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__))).returncode


def main():
    """Main entry point."""
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  GOLDEN-PATH INTEGRATION TESTS".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    # Parse arguments
    test_filter = None
    if len(sys.argv) > 1:
        test_filter = sys.argv[1]
    
    # Map filter names to test patterns
    filters = {
        'explore': 'TestGoldenPathFloor1::test_basic_explore_floor1',
        'combat': 'TestGoldenPathFloor1::test_kill_basic_monster_and_loot',
        'wands': 'TestGoldenPathFloor1::test_use_wand_of_portals_on_floor1',
        'lore': 'TestGoldenPathFloor1::test_discover_mural_and_signpost',
        'moves': 'TestGoldenPathIntegration::test_multiple_moves_no_crash',
        'overlap': 'TestGoldenPathIntegration::test_spawn_multiple_entities_no_overlap',
    }
    
    if test_filter and test_filter in filters:
        # Run specific test group
        test_pattern = f"tests/test_golden_path_floor1.py::{filters[test_filter]}"
        print(f"\n🎯 Running: {filters[test_filter]}")
        return run_pytest_tests(test_pattern, verbose=True)
    elif test_filter and test_filter in ['help', '-h', '--help']:
        print("\n✨ Available test groups:")
        for name, pattern in filters.items():
            print(f"  python3 run_golden_path_tests.py {name:12} # {pattern}")
        print(f"  python3 run_golden_path_tests.py             # Run all tests")
        return 0
    elif test_filter:
        print(f"\n❌ Unknown filter: {test_filter}")
        print("   Run with 'help' for available options")
        return 1
    
    # Run all tests
    print("\n🎮 Running all golden-path Floor 1 tests...\n")
    exit_code = run_pytest_tests(verbose=True)
    
    if exit_code == 0:
        print("\n" + "="*80)
        print("✅ ALL GOLDEN-PATH TESTS PASSED")
        print("   Basic gameplay flows are working correctly!")
        print("="*80 + "\n")
    else:
        print("\n" + "="*80)
        print("❌ GOLDEN-PATH TESTS FAILED")
        print("   Critical gameplay flows are broken!")
        print("="*80 + "\n")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())

