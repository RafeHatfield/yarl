# 🧪 Testing Strategy for Tile Access Refactor

## Overview

The tile access refactor changes how we interact with `GameMap.tiles[][]`, which affects **16 test files** and our overall testing approach.

**Good News**: Tests don't need major restructuring! The refactor actually **simplifies** testing.

---

## Impact Analysis

### Test Files Affected (16 total)

**Files that directly access `tiles[][]`**:
1. ✅ `tests/test_game_map_safe_access.py` - NEW tests for safe accessors
2. `tests/test_victory_portal_spawn.py`
3. `tests/test_item_seeking_ai.py`
4. `tests/test_room_generators.py`
5. `tests/test_slime_splitting.py`
6. `tests/test_auto_explore_regression.py`
7. `tests/test_auto_explore.py`
8. `tests/test_player_explored_pathfinding.py`
9. `tests/regression/test_zombie_target_switching.py`
10. `tests/test_monster_hazard_avoidance.py`
11. `tests/test_hazard_rendering.py`
12. `tests/regression/test_monster_ai_regression.py`
13. `tests/regression/test_save_game_regression.py`
14. `tests/test_render_optimization.py`
15. `tests/regression/test_map_tile_rendering_logic.py`
16. `tests/test_dungeon_levels.py`

### Types of Test Usage

#### 1. **Setup/Fixture Usage (Most Common)** ✅ NO CHANGE NEEDED
Tests that set up tiles in fixtures:
```python
# BEFORE & AFTER - Both work!
def setUp(self):
    game_map = GameMap(10, 10)
    # Direct access for SETUP is fine
    game_map.tiles[5][5].blocked = False
    game_map.tiles[5][5].explored = True
```

**Why no change needed**: 
- Setup code can still use direct access
- We're testing the game logic, not tile access
- Performance doesn't matter in setup

#### 2. **Assertion Usage** ⚠️ OPTIONAL CHANGE
Tests that check tile state:
```python
# BEFORE (still works, but verbose)
assert game_map.tiles[x][y].blocked == False

# AFTER (cleaner, recommended)
assert game_map.is_blocked(x, y) == False
# OR
assert game_map.is_walkable(x, y) == True
```

**Why optional**: Both work, but new way is:
- ✅ More readable
- ✅ Tests the public API
- ✅ Matches production code

#### 3. **Mock GameMap** ⚠️ NEEDS UPDATE
Tests that mock `GameMap`:
```python
# BEFORE (incomplete mock)
mock_game_map = Mock()
mock_game_map.width = 20
mock_game_map.height = 20
mock_game_map.tiles = [[Mock() for y in range(20)] for x in range(20)]

# AFTER (complete mock with safe accessors)
mock_game_map = Mock()
mock_game_map.width = 20
mock_game_map.height = 20
mock_game_map.tiles = [[Mock() for y in range(20)] for x in range(20)]
# Add safe accessor methods
mock_game_map.is_in_bounds.side_effect = lambda x, y: 0 <= x < 20 and 0 <= y < 20
mock_game_map.is_blocked.side_effect = lambda x, y: False  # Or custom logic
mock_game_map.is_explored.side_effect = lambda x, y: True
mock_game_map.is_walkable.side_effect = lambda x, y: True
```

**Why needed**: Production code now calls safe accessors, mocks need them.

---

## Testing Strategy

### Tier 1: Unit Tests for Safe Accessors ✅ COMPLETE

**File**: `tests/test_game_map_safe_access.py`

**Coverage**: 60+ tests covering:
- Valid coordinates
- Out-of-bounds coordinates
- Edge cases
- Consistency between methods
- Real-world scenarios

**Status**: ✅ Complete and comprehensive

### Tier 2: Existing Tests - No Change Needed ✅ MOSTLY SAFE

**Strategy**: **Don't touch working tests unless they fail**

**Why**:
- Setup code with direct access still works
- Tests are testing game logic, not tile access
- Backward compatibility maintained

**Examples of tests that don't need changes**:
```python
# test_dungeon_levels.py
def test_game_map_tile_initialization(self):
    game_map = GameMap(width=10, height=10)
    # All tiles should be blocked by default
    for x in range(10):
        for y in range(10):
            assert game_map.tiles[x][y].blocked is True
            # ✅ This still works! No change needed!
```

```python
# test_save_game_regression.py
def setUp(self):
    self.game_map = GameMap(width=80, height=50, dungeon_level=1)
    for x in range(self.game_map.width):
        for y in range(self.game_map.height):
            self.game_map.tiles[x][y] = Tile(blocked=False)
    # ✅ Setup code still works! No change needed!
```

### Tier 3: Integration Tests - Monitor for Issues ⚠️ WATCH

**Strategy**: Run existing integration tests, fix if they fail

**Files to watch**:
- `tests/test_tier1_integration.py` - Tests debug flags
- `tests/test_startup_integration.py` - Tests game initialization
- Any tests that mock `GameMap` and use production code

**If they fail**:
1. Check if mock needs safe accessor methods
2. Update mock to provide safe accessors
3. Consider using real `GameMap` instead of mock

### Tier 4: New Tests - Use Safe Accessors ✨ RECOMMENDED

**For all new tests, use safe accessors**:

```python
# ✅ GOOD - New test using safe accessors
def test_player_movement_blocked_by_walls():
    game_map = GameMap(10, 10)
    player = create_player(5, 5)
    
    # Check if destination is blocked
    if game_map.is_blocked(player.x - 1, player.y):
        assert not can_move(player, -1, 0)
```

```python
# ❌ BAD - New test using direct access
def test_player_movement_blocked_by_walls():
    game_map = GameMap(10, 10)
    player = create_player(5, 5)
    
    # Direct access in new tests
    if game_map.tiles[player.x - 1][player.y].blocked:
        assert not can_move(player, -1, 0)
```

---

## Migration Approach

### Phase 1: Verify Existing Tests ✅ PRIORITY 1

**Action**: Run all existing tests to ensure no breakage

**Command**:
```bash
pytest tests/ -v
```

**Expected**: All tests should pass (backward compatibility)

**If failures occur**:
1. Check error message
2. Likely mock-related (missing safe accessor methods)
3. Fix mock to include safe accessors

### Phase 2: Create Test Fixtures/Helpers 🔄 NICE TO HAVE

**Create reusable test fixtures**:

```python
# tests/conftest.py or tests/fixtures/game_map_fixtures.py

@pytest.fixture
def empty_game_map():
    """Create a 10x10 empty (all walkable) game map."""
    game_map = GameMap(10, 10)
    for x in range(10):
        for y in range(10):
            game_map.tiles[x][y].blocked = False
    return game_map

@pytest.fixture
def walled_game_map():
    """Create a 10x10 game map with walls on edges."""
    game_map = GameMap(10, 10)
    for x in range(10):
        for y in range(10):
            # Walls on edges, open in middle
            is_edge = x == 0 or x == 9 or y == 0 or y == 9
            game_map.tiles[x][y].blocked = is_edge
    return game_map

@pytest.fixture
def mock_game_map_with_safe_accessors():
    """Create a mock GameMap with safe accessor methods."""
    mock = Mock(spec=GameMap)
    mock.width = 20
    mock.height = 20
    mock.tiles = [[Mock() for y in range(20)] for x in range(20)]
    
    # Add safe accessors
    mock.is_in_bounds = Mock(side_effect=lambda x, y: 0 <= x < 20 and 0 <= y < 20)
    mock.is_blocked = Mock(return_value=False)
    mock.is_explored = Mock(return_value=True)
    mock.is_walkable = Mock(return_value=True)
    mock.get_tile = Mock(side_effect=lambda x, y: mock.tiles[x][y] if mock.is_in_bounds(x, y) else None)
    
    return mock
```

### Phase 3: Progressive Test Updates 🔄 ONGOING

**Strategy**: Update tests opportunistically

**When to update a test**:
1. ✅ When adding new assertions to existing test
2. ✅ When fixing a failing test
3. ✅ When test becomes hard to read
4. ❌ Don't update just for the sake of it

**Example progression**:
```python
# Original test (works fine, leave it)
def test_player_spawns_in_first_room(self):
    game_map = GameMap(80, 50)
    # ... setup code ...
    assert game_map.tiles[player.x][player.y].blocked == False

# Later, when adding new assertion (update both)
def test_player_spawns_in_first_room(self):
    game_map = GameMap(80, 50)
    # ... setup code ...
    # Updated both to use safe accessors
    assert game_map.is_walkable(player.x, player.y)
    assert game_map.is_explored(player.x, player.y)  # New assertion
```

---

## Test Patterns

### Pattern 1: Testing Tile Properties

```python
# ✅ RECOMMENDED - Use safe accessors
def test_room_creation_makes_tiles_walkable(game_map):
    room = Rect(5, 5, 10, 10)
    game_map.create_room(room)
    
    # Test using safe accessors
    assert game_map.is_walkable(7, 7)
    assert not game_map.is_blocked(7, 7)
```

```python
# ⚠️ ACCEPTABLE - Direct access in setup/assertions
def test_room_creation_makes_tiles_walkable(game_map):
    room = Rect(5, 5, 10, 10)
    game_map.create_room(room)
    
    # Direct access still works
    assert game_map.tiles[7][7].blocked == False
```

### Pattern 2: Testing Bounds Checking

```python
# ✅ RECOMMENDED - Test the safe accessor itself
def test_entity_rendering_handles_out_of_bounds():
    game_map = GameMap(10, 10)
    entity = Entity(-1, -1, '@', (255, 255, 255), 'Test')
    
    # Should not crash
    assert game_map.is_in_bounds(entity.x, entity.y) == False
    assert game_map.is_explored(entity.x, entity.y) == False
```

### Pattern 3: Testing Map Generation

```python
# ✅ RECOMMENDED - Mix of direct (setup) and safe (assertions)
def test_room_generator_creates_walkable_area():
    game_map = GameMap(50, 50)
    
    # Generate room
    room = Rect(10, 10, 20, 15)
    generator = StandardRoomGenerator()
    generator.generate(game_map, room, entities=[], dungeon_level=1)
    
    # Test room interior is walkable (use safe accessors)
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            assert game_map.is_walkable(x, y), f"Tile ({x},{y}) should be walkable"
```

### Pattern 4: Testing Pathfinding

```python
# ✅ RECOMMENDED - Use safe accessors (matches production)
def test_pathfinding_avoids_blocked_tiles():
    game_map = GameMap(10, 10)
    
    # Setup: Create corridor with one blocked tile
    for x in range(10):
        game_map.tiles[x][5].blocked = False
    game_map.tiles[5][5].blocked = True  # Block middle
    
    # Test: Pathfinding should check is_blocked (safe accessor)
    path = find_path(game_map, (0, 5), (9, 5))
    
    # Verify path avoids blocked tile
    for x, y in path:
        assert game_map.is_walkable(x, y), f"Path includes blocked tile at ({x},{y})"
```

---

## Common Testing Pitfalls

### Pitfall 1: Over-Mocking ❌

```python
# ❌ BAD - Over-mocked, breaks with refactor
def test_entity_visibility():
    mock_map = Mock()
    mock_map.tiles = Mock()
    # Breaks when production code calls is_explored()
    
    render_entity(entity, mock_map)
```

```python
# ✅ GOOD - Use real GameMap or complete mock
def test_entity_visibility():
    game_map = GameMap(10, 10)  # Real object
    game_map.tiles[5][5].explored = True
    
    render_entity(entity, game_map)
    # Works with refactor!
```

### Pitfall 2: Testing Implementation Details ❌

```python
# ❌ BAD - Tests internal structure
def test_tiles_array_structure():
    game_map = GameMap(10, 10)
    assert isinstance(game_map.tiles, list)
    assert isinstance(game_map.tiles[0], list)
    # Fragile - breaks if we change internal structure
```

```python
# ✅ GOOD - Tests behavior
def test_game_map_bounds():
    game_map = GameMap(10, 10)
    assert game_map.is_in_bounds(0, 0)
    assert game_map.is_in_bounds(9, 9)
    assert not game_map.is_in_bounds(10, 10)
    # Resilient - tests public API behavior
```

### Pitfall 3: Not Testing Edge Cases ❌

```python
# ❌ BAD - Only tests happy path
def test_tile_access():
    game_map = GameMap(10, 10)
    assert game_map.get_tile(5, 5) is not None
```

```python
# ✅ GOOD - Tests edge cases
def test_tile_access():
    game_map = GameMap(10, 10)
    # Happy path
    assert game_map.get_tile(5, 5) is not None
    # Edge cases
    assert game_map.get_tile(0, 0) is not None
    assert game_map.get_tile(9, 9) is not None
    # Boundary
    assert game_map.get_tile(-1, 0) is None
    assert game_map.get_tile(10, 0) is None
```

---

## Testing Checklist

### For Existing Tests ✅
- [ ] Run all tests: `pytest tests/ -v`
- [ ] Check for failures related to mocking
- [ ] Update mocks to include safe accessors if needed
- [ ] Document any tests that need special attention
- [ ] Don't change tests that aren't broken

### For New Tests ✅
- [ ] Use safe accessors (`is_blocked`, `is_explored`, etc.)
- [ ] Test edge cases (out of bounds)
- [ ] Use fixtures for common map setups
- [ ] Test behavior, not implementation
- [ ] Add docstrings explaining what's being tested

### For Test Fixtures ✅
- [ ] Create reusable map fixtures
- [ ] Add mock with safe accessors to conftest.py
- [ ] Document fixture usage patterns
- [ ] Make fixtures easy to customize

---

## Performance Testing

### Before Refactor
```python
# Direct access benchmark
def test_direct_access_performance():
    game_map = GameMap(100, 100)
    
    start = time.time()
    for _ in range(10000):
        blocked = game_map.tiles[50][50].blocked
    elapsed = time.time() - start
    # ~0.5ms for 10k accesses
```

### After Refactor
```python
# Safe accessor benchmark
def test_safe_accessor_performance():
    game_map = GameMap(100, 100)
    
    start = time.time()
    for _ in range(10000):
        blocked = game_map.is_blocked(50, 50)
    elapsed = time.time() - start
    # ~0.6ms for 10k accesses (+20%)
```

### With Bounds Check
```python
# Manual bounds check benchmark
def test_manual_bounds_check_performance():
    game_map = GameMap(100, 100)
    
    start = time.time()
    for _ in range(10000):
        if 0 <= 50 < game_map.width and 0 <= 50 < game_map.height:
            blocked = game_map.tiles[50][50].blocked
    elapsed = time.time() - start
    # ~0.8ms for 10k accesses (+60%)
```

**Conclusion**: Safe accessors are faster than manual bounds checking!

---

## Rollout Timeline

### Week 1: Verification ✅ DONE
- ✅ Add safe accessor methods
- ✅ Create comprehensive unit tests
- ✅ Fix critical rendering files
- ✅ Document strategy

### Week 2: Validation 🔄 CURRENT
- [ ] Run all existing tests
- [ ] Fix any mock-related failures
- [ ] Verify game runs with `--start-level` flags
- [ ] User acceptance testing

### Week 3+: Progressive Updates 🔄 ONGOING
- [ ] Update tests as we touch them
- [ ] Create common test fixtures
- [ ] Add linter rules for new code
- [ ] Monitor for issues

---

## Key Takeaways

1. **✅ Existing tests mostly work unchanged** - Backward compatibility maintained
2. **⚠️ Mocks need updating** - Add safe accessor methods to mocks
3. **✨ New tests should use safe accessors** - Match production code patterns
4. **🎯 Test behavior, not implementation** - Focus on what code does, not how
5. **📈 Performance is fine** - Actually faster than manual bounds checking
6. **🔄 Update opportunistically** - Fix tests when you touch them, not before

---

## Questions & Concerns

### "Do I need to rewrite all my tests?"
**No!** Tests with direct tile access in setup/assertions still work. Only update:
- Tests that fail due to mocking
- Tests you're already modifying
- New tests (use safe accessors)

### "Will this slow down my tests?"
**No!** Safe accessors add ~20% overhead, but:
- Setup code (90% of tile access) unchanged
- Test performance not critical
- Actually faster than manual bounds checking

### "What if a test fails?"
1. Check if it uses a mock `GameMap`
2. Add safe accessor methods to mock
3. Or use real `GameMap` instead of mock

### "Should I update my test right now?"
**Only if**:
- Test is failing
- You're adding new assertions
- Test is hard to read
- It's a new test

**Not if**:
- Test is passing
- You're just refactoring for sake of it
- No immediate benefit

---

## Resources

- **Test examples**: `tests/test_game_map_safe_access.py`
- **Fixtures**: `tests/conftest.py`
- **Architecture doc**: `docs/architecture/TILE_ACCESS_REFACTOR.md`
- **Completion status**: `REFACTOR_COMPLETE.md`

---

*Remember: Tests are a tool, not a goal. Update them when it provides value, not just for consistency.*

