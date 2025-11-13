# Golden-Path Integration Tests

## Overview

Golden-path integration tests exercise the most critical player workflows on Floor 1 and fail loudly if basic functionality breaks, even when individual unit tests still pass.

These tests are designed to be:
- **Fast**: All 6 tests complete in ~0.4 seconds
- **Focused**: Each test targets one core gameplay system
- **Meaningful**: Catches regressions in actual player workflows
- **Isolated**: Each test can run independently with full game initialization

## Test Suite

### TestGoldenPathFloor1

High-level integration tests that initialize a complete game and exercise specific systems.

#### 1. `test_basic_explore_floor1`
**Purpose**: Verify basic game initialization and player movement

**What it tests**:
- Game initializes without crashing
- Player can be placed on the map
- Player can move in multiple directions
- Map contains required structures (stairs)
- Field of view (FOV) can be computed

**Failure indicates**: Game initialization broken, movement system broken, or map generation broken

#### 2. `test_kill_basic_monster_and_loot`
**Purpose**: Verify combat and monster death flows

**What it tests**:
- Monster death functions complete without exception
- Entity list remains consistent after death
- No invalid coordinates in entity positions
- Death screen quote system (if applicable)

**Failure indicates**: Combat system broken, death handling broken, or entity management broken

#### 3. `test_use_wand_of_portals_on_floor1`
**Purpose**: Verify wand component and portal creation system

**What it tests**:
- Wand component can be created with charges
- Wand charge management works (use_charge, is_empty)
- PortalManager can create portal entities without exception
- Portal entities have valid coordinates and placement

**Failure indicates**: Wand system broken, portal creation broken, or services.portal_manager broken

#### 4. `test_discover_mural_and_signpost`
**Purpose**: Verify lore entities (murals and signposts)

**What it tests**:
- Mural and signpost entities can be found on floor 1
- Lore entities have valid coordinates
- FOV checks work on lore entities without crashing
- Player can move to see lore entities

**Failure indicates**: Lore system broken, mural manager broken, or entity spawning broken

### TestGoldenPathIntegration

Extended integration tests combining multiple systems.

#### 5. `test_multiple_moves_no_crash`
**Purpose**: Verify sustained gameplay without crashes or memory issues

**What it tests**:
- Game can handle 20+ consecutive moves
- FOV recomputes correctly after each move
- No accumulation of errors during sustained play

**Failure indicates**: Game loop broken, FOV system has memory leaks, or movement has side effects

#### 6. `test_spawn_multiple_entities_no_overlap`
**Purpose**: Verify entity spawning doesn't place multiple blocking entities on same tile

**What it tests**:
- Entity positions don't have overlapping blocking entities
- Spawning system properly checks for occupied tiles
- No corruption in spatial data structures

**Failure indicates**: Entity spawning broken, collision system broken, or map generation broken

## Running the Tests

### Run all golden-path tests via pytest

```bash
python3 -m pytest tests/test_golden_path_floor1.py -v
```

### Run specific tests via convenience runner

```bash
# Run all tests
python3 run_golden_path_tests.py

# Run by topic
python3 run_golden_path_tests.py explore      # Movement and exploration
python3 run_golden_path_tests.py combat       # Combat and monster death
python3 run_golden_path_tests.py wands        # Wand of Portals
python3 run_golden_path_tests.py lore         # Murals and signposts
python3 run_golden_path_tests.py moves        # Extended movement
python3 run_golden_path_tests.py overlap      # Entity overlap checking

# Show help
python3 run_golden_path_tests.py help
```

## Integration with CI/CD

The golden-path tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Golden Path Tests
  run: python3 run_golden_path_tests.py
  timeout-minutes: 1
```

## Architecture Notes

### Game Initialization
Tests use the same initialization path as the real game:
1. Load testing configuration via `get_testing_config()`
2. Initialize game via `get_game_variables(get_constants())`
3. This creates a full, real game state ready for testing

### Test Isolation
Each test:
1. Resets the testing configuration in `setup_method()`
2. Starts with a clean game state
3. Can run independently of other tests
4. Cleans up after itself automatically

### Fast Execution
Tests are fast because:
- Testing config uses small map sizes
- No rendering/graphics initialization
- Minimal entity spawning
- Direct function calls (no full game loop)

## Extending the Golden Path Tests

To add new golden-path tests:

1. Add a test method to `TestGoldenPathFloor1` or `TestGoldenPathIntegration`
2. Use the `setup_method()` fixture to initialize a fresh game
3. Call game functions directly (don't use game loop)
4. Assert on meaningful game state invariants
5. Keep tests fast and focused

Example:

```python
def test_staircase_descent(self):
    """Golden Path: Player descends staircase to next floor."""
    constants = get_constants()
    player, entities, game_map, message_log, game_state = get_game_variables(constants)
    
    # Find a staircase
    stairs = [e for e in entities if hasattr(e, 'stairs') and e.stairs]
    assert len(stairs) > 0, "Must have stairs"
    
    # Move player to staircase
    stair = stairs[0]
    player.x = stair.x
    player.y = stair.y
    
    # Verify player can interact with it
    assert player.x == stair.x and player.y == stair.y, "Player on stairs"
```

## Troubleshooting Test Failures

### Test fails during setup
- Check that testing configuration loads correctly
- Verify all imports work
- Run `python3 -c "from config.testing_config import get_testing_config; print(get_testing_config())"` to verify testing mode

### Test fails during game initialization
- Check `get_game_variables()` output
- Verify YAML config files are loaded
- Check for entity factory errors
- Look for missing components

### Test fails during FOV computation
- Verify `fov_functions.py` can create FOV map
- Check game map dimensions
- Ensure transparency array is correct

### Test fails with entity errors
- Check entity coordinate validity
- Verify entity component access patterns
- Look for KeyError in component lookups

## Regression Detection

These tests are most effective when:
1. Run on every pull request
2. Run before merging to main branch
3. Run in CI/CD pipeline
4. Results tracked over time

If any golden-path test fails:
- **Do not merge** the change
- Investigate root cause immediately
- The test is detecting a fundamental gameplay break
- Likely affects many players/workflows

## Performance Notes

| Metric | Value |
|--------|-------|
| Total Runtime | ~0.4 seconds |
| Per-Test Average | ~0.07 seconds |
| Fastest Test | `test_use_wand_of_portals_on_floor1` (0.05s) |
| Slowest Test | `test_basic_explore_floor1` (0.15s) |
| Total Pytest Overhead | ~0.1 seconds |

Tests run sequentially. With proper test isolation, they could theoretically run in parallel but are fast enough serially.

## Related Documentation

- [Test Startup Integration](test_startup_integration.py) - Other startup tests
- [Portal System Tests](integration/portals/) - Detailed portal system tests
- [Combat Tests](integration/combat/) - Detailed combat tests
- [Config Constants](../config/game_constants.py) - Game configuration


