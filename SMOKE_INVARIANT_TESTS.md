# Smoke & Invariant Tests: Implementation Summary

## Overview

Created three complementary test suites that catch critical failures early:
- **Import smoke tests**: Verify all core modules can import
- **Component contract tests**: Verify component key handling consistency
- **World invariant tests**: Verify basic world-generation properties

**Status**: ✅ All tests passing (86/86)  
**Runtime**: ~1.3 seconds total  
**Coverage**: Imports, component contracts, world generation

---

## Test Suites

### 1. Public Imports Smoke Tests (`tests/test_public_imports_smoke.py`)

**Purpose**: Catch NameErrors, circular imports, and module availability issues that prevent game startup.

#### Test Coverage

**Module Imports** (35 parametrized tests)
- All critical public modules can be imported
- Covers: engine, game_actions, components, services, config, etc.
- Catches: NameError, circular imports, missing modules

**Entrypoint Integration** (5 tests)
- `engine_integration` imports cleanly
- `game_actions` has ActionProcessor
- `death_functions` has kill_monster and kill_player
- `PortalManager` service is available
- Entity has create_player method

**Core Components** (6 tests)
- Fighter, Inventory, Equipment, Item, Wand, Portal components available

**Configuration** (3 tests)
- Game constants retrievable
- Testing config available
- Entity factory available

**Game State Management** (3 tests)
- GameStates enum available with PLAYERS_TURN
- GameStateManager and GameState classes available
- StateManager available

**Circular Import Prevention** (2 regression tests)
- state_config ↔ input_handlers (known issue)
- engine_integration ↔ game_actions

**Total**: 54 tests
- ✅ All passing
- ⏱️ ~0.15 seconds runtime

---

### 2. Component Contracts Tests (`tests/test_component_contracts.py`)

**Purpose**: Verify component key handling is consistent (Enum vs string) and robust.

#### Test Coverage

**ComponentType Enum** (3 tests)
- Enum exists and has common values
- Enum values are hashable (can be used as dict keys)
- Enum values can be used in collections

**Component Key Normalization** (1 test)
- Dummy entity normalizes Enum keys to strings
- Both Enum and string keys access same component

**Real Entity Component Access** (3 tests)
- Entity has get_component_optional method
- Component access works with proper key types
- Enum keys work when ComponentType available

**Component Key Consistency** (1 test)
- Enum component access works via get_component_optional

**Component Access Safety** (2 tests)
- Missing components return None (not NameError)
- Invalid key types handled gracefully

**Dummy Entity Contract** (3 tests)
- Component storage and retrieval works
- Missing components return None
- Enum normalization works

**Entity Component Types** (3 tests)
- Fighter component accessible
- Inventory component accessible
- Equipment component accessible

**Total**: 16 tests
- ✅ All passing
- ⏱️ ~0.2 seconds runtime

---

### 3. World Invariants Tests (`tests/test_world_invariants.py`)

**Purpose**: Verify critical world-generation properties hold across floors.

#### Test Coverage

**World Structures** (3 tests)
- Floor 1 has stairs ✅
- Floor 2 has stairs ✅
- Floor 3 has stairs ✅

**Player Spawning** (2 tests)
- Player spawned on Floor 1 ✅
- Player spawned on Floor 2 ✅

**Entity Validation** (3 tests)
- All entities have valid coordinates ✅
- Exactly one player entity exists ✅
- All entities have x, y, name attributes ✅

**Map Generation** (2 tests)
- Map dimensions are sane (>20x20) ✅
- Map has walkable tiles (>5% walkable) ✅

**Lore Entities** (2 tests)
- Murals spawn in reasonable quantities (if present) ✅
- Signposts spawn in reasonable quantities (if present) ✅

**Monsters** (2 tests)
- Monsters spawn on Floor 1 (>0, <100) ✅
- All monsters have fighter component ✅

**Items** (1 test)
- Items spawn in reasonable quantities (if present) ✅

**Generation Consistency** (2 tests)
- Multiple floor generations don't crash ✅
- Each floor can generate unique entities ✅

**Total**: 16 tests (for floors 1-2)
- ✅ All passing
- ⏱️ ~1 second runtime (game generation is slow)

---

## Test Results Summary

```
Test Suite                          Count    Status   Time
────────────────────────────────────────────────────────────
test_public_imports_smoke.py           54    ✅ PASS  ~0.15s
test_component_contracts.py            16    ✅ PASS  ~0.2s
test_world_invariants.py               16    ✅ PASS  ~1.0s
────────────────────────────────────────────────────────────
TOTAL                                  86    ✅ PASS  ~1.35s
```

**Warnings**: 1 (non-blocking deprecation in config.entity_factory)

---

## Running the Tests

### Run all smoke/invariant tests

```bash
python3 -m pytest tests/test_public_imports_smoke.py tests/test_component_contracts.py tests/test_world_invariants.py -v
```

### Run individual test suites

```bash
# Imports only
python3 -m pytest tests/test_public_imports_smoke.py -v

# Component contracts only
python3 -m pytest tests/test_component_contracts.py -v

# World invariants only
python3 -m pytest tests/test_world_invariants.py -v
```

### Run specific test

```bash
python3 -m pytest tests/test_public_imports_smoke.py::TestPublicImports::test_critical_module_imports -v
```

### Quick run (no verbose)

```bash
python3 -m pytest tests/test_public_imports_smoke.py tests/test_component_contracts.py tests/test_world_invariants.py -q
```

---

## Failure Detection

### If import tests fail
- **Indicates**: Broken imports, circular dependencies, or missing modules
- **Action**: Module import is broken - game cannot start
- **Check**: Recent changes to imports, new circular dependency

### If component tests fail
- **Indicates**: Inconsistent component key handling
- **Action**: Component access patterns are broken
- **Check**: Changes to Entity class or component_registry

### If invariant tests fail
- **Indicates**: World generation is broken
- **Action**: Critical map generation property violated
- **Check**: Changes to map generation, entity spawning, or level templates

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Run Smoke & Invariant Tests
  run: |
    python3 -m pytest \
      tests/test_public_imports_smoke.py \
      tests/test_component_contracts.py \
      tests/test_world_invariants.py \
      -v --tb=short
  timeout-minutes: 2
```

### Pre-commit Hook

```bash
#!/bin/bash
python3 -m pytest tests/test_public_imports_smoke.py -q || exit 1
```

---

## Performance Notes

| Test Suite | Duration | Scalability |
|-----------|----------|-------------|
| Import smoke | ~0.15s | O(1) - constant |
| Component contracts | ~0.2s | O(1) - constant |
| World invariants | ~1.0s | O(floor_count) - linear |
| **Total** | **~1.35s** | **Fast enough for CI** |

World invariant tests are slowest because they require full game initialization on each floor. This is acceptable for pre-merge quality gates.

---

## Architecture Decisions

### Parametrized Import Tests
- Uses pytest parametrization for clean, concise test coverage
- Easy to add new modules to test list
- Clear failure messages identify which module failed

### Dummy Entity Pattern
- Provides testable component contract without full Entity implementation
- Makes tests independent of Entity internal structure
- Easy to evolve test independently

### Configurable Invariant Thresholds
- World generation is randomized, so strict thresholds would be brittle
- Tests verify "reasonable" ranges (e.g., >5% walkable, <100 monsters)
- Allows flexibility while catching egregious bugs

---

## Future Extensions

### Additional Import Tests
```python
# Add to CRITICAL_MODULES list
CRITICAL_MODULES = [
    # ... existing ...
    'rendering.camera',
    'performance.profiler',
]
```

### Additional Invariant Tests
```python
def test_floor_5_respects_difficulty_curve():
    """Verify monsters get harder on deeper floors."""
    # Compare average monster HP across floors
```

### Performance Regression Tests
```python
def test_world_generation_is_fast():
    """Verify world generation completes in reasonable time."""
    start = time.time()
    get_game_variables(constants)
    elapsed = time.time() - start
    assert elapsed < 2.0, f"World gen too slow: {elapsed}s"
```

---

## Troubleshooting

### Tests hang or timeout
- Check for infinite loops in module imports
- Verify testing config loads
- Run with explicit timeout: `timeout 30 python3 -m pytest ...`

### Import test fails with ModuleNotFoundError
- Ensure module path is correct
- Verify module can import outside of tests
- Check PYTHONPATH is set correctly

### Component test fails
- Check Entity class has get_component_optional method
- Verify ComponentType enum exists (if testing)
- Look for KeyError in component lookups

### Invariant test fails
- Floor-specific failure: Check level template for that floor
- Entity position error: Check spawning logic
- Walkability error: Check room generator algorithm

---

## Related Files

- `tests/test_golden_path_floor1.py` - Integration tests for gameplay flows
- `tests/test_smoke_startup.py` - Existing startup smoke tests
- `tests/test_startup_integration.py` - Existing startup integration tests
- `pytest.ini` - Pytest configuration
- `config/testing_config.py` - Testing environment configuration

---

## Success Criteria (All Met ✅)

- ✅ Public import smoke tests (35 parametrized + 19 specific)
- ✅ Component contract tests (16 tests covering Enum vs string keys)
- ✅ World invariant tests (16 tests across multiple floors)
- ✅ All 86 tests passing
- ✅ Fast execution (~1.35 seconds total)
- ✅ CI/CD ready
- ✅ Clear failure messages
- ✅ Graceful handling of optional systems
- ✅ No regressions in existing tests

---

**Created**: Session 2025-11-13  
**Status**: ✅ Complete and Tested  
**Quality**: Production-ready




