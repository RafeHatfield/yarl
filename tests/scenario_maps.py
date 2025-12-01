"""Scenario-based test maps for deterministic bot testing.

STATUS: TODO - Placeholder for future implementation

This module will provide deterministic test maps that can be used for:
1. Focused bot behavior testing (combat, loot, exploration)
2. Regression testing for specific scenarios
3. Performance benchmarking with controlled complexity

DESIGN GOALS:
- Maps are defined programmatically, not loaded from files
- Each scenario has a specific test purpose
- Maps are small and fast to run
- Results are deterministic given the same seed

FUTURE SCENARIOS:

1. COMBAT_CORRIDOR
   - Long corridor with single enemy
   - Test: Bot engages and defeats enemy
   - Expected: Bot kills enemy, no stuck detection

2. LOOT_ROOM
   - Small room with multiple item types
   - Test: Bot picks up and equips items
   - Expected: Bot equips weapon/armor, collects potions

3. MULTI_ROOM_EXPLORE
   - 3-4 connected rooms with doors
   - Test: Bot explores all rooms
   - Expected: Full exploration, no oscillation

4. STAIRS_DESCENT
   - Simple map with obvious stairs path
   - Test: Bot finds and uses stairs
   - Expected: Bot descends when floor complete

5. TRAPPED_CORRIDOR
   - Corridor with traps
   - Test: Bot navigates around/through traps
   - Expected: Bot reaches destination (may take damage)

INTEGRATION WITH SOAK HARNESS:

The soak harness will accept a `--scenario` flag that:
1. Replaces normal mapgen with scenario map
2. Uses scenario-specific success criteria
3. Reports pass/fail per scenario

Example usage:
    python engine.py --bot --scenario COMBAT_CORRIDOR --seed 42
    python engine.py --bot-soak --runs 10 --scenario LOOT_ROOM

"""

from typing import Optional, Dict, Any, List, Tuple


# Placeholder: Scenario type definitions
class TestScenario:
    """Base class for test scenarios.
    
    TODO: Implement this class with:
    - name: str - Unique scenario identifier
    - description: str - What the scenario tests
    - generate_map() - Create the deterministic map
    - check_success() - Verify scenario passed
    """
    pass


def generate_test_map_combat_corridor(seed: int = 0) -> Optional[Any]:
    """Generate a simple combat corridor test map.
    
    TODO: Implement this function to create:
    - 30x5 corridor
    - Player at one end
    - Single orc at the other end
    - No items, no traps
    
    Args:
        seed: RNG seed for any randomization (layout should be fixed)
        
    Returns:
        GameMap instance (None until implemented)
    """
    # TODO: Implement scenario map generation
    # This requires:
    # 1. Creating a GameMap without full mapgen
    # 2. Manually placing tiles, entities
    # 3. Setting up FOV properly
    return None


def generate_test_map_loot_room(seed: int = 0) -> Optional[Any]:
    """Generate a loot collection test map.
    
    TODO: Implement this function to create:
    - 10x10 room
    - Player in center
    - Various items scattered around
    - No monsters
    
    Args:
        seed: RNG seed for item variety
        
    Returns:
        GameMap instance (None until implemented)
    """
    # TODO: Implement scenario map generation
    return None


def list_available_scenarios() -> List[str]:
    """List all available test scenarios.
    
    Returns:
        List of scenario names
    """
    return [
        "COMBAT_CORRIDOR",
        "LOOT_ROOM", 
        "MULTI_ROOM_EXPLORE",
        "STAIRS_DESCENT",
        "TRAPPED_CORRIDOR",
    ]


def get_scenario(name: str) -> Optional[TestScenario]:
    """Get a scenario by name.
    
    Args:
        name: Scenario name (case-insensitive)
        
    Returns:
        TestScenario instance, or None if not found/not implemented
    """
    # TODO: Return actual scenario instances
    return None

