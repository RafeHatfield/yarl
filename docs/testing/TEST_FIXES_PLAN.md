# Test Fixes Plan

## Summary
144 failing tests out of 2154 total (93.3% pass rate)

## Root Causes

### 1. Mock Component Access Pattern Changed
**Issue:** Code now uses `entity.get_component_optional(ComponentType.X)` but tests mock `entity.components.get()`

**Fix Pattern:**
```python
# Before
self.monster.components.get = Mock(return_value=self.monster.equipment)

# After - add BOTH
self.monster.components.get = Mock(return_value=self.monster.equipment)
self.monster.get_component_optional = Mock(return_value=self.monster.equipment)
```

### 2. Mock Inventory Items Not Iterable
**Issue:** `inventory.items = Mock()` causes `TypeError: 'Mock' object is not iterable`

**Fix Pattern:**
```python
# Before
self.monster.inventory.items = Mock()

# After
self.monster.inventory.items = []  # or [item1, item2]
```

### 3. Loot Generation System Added
**Issue:** New loot quality system generates bonus items, breaking test assertions about exact item counts

**Fix Pattern:**
```python
# Add to test
@patch('components.loot.get_loot_generator')
def test_something(self, mock_get_loot_gen):
    mock_loot_gen = Mock()
    mock_loot_gen.should_monster_drop_loot.return_value = False
    mock_get_loot_gen.return_value = mock_loot_gen
```

## Affected Test Modules

- `test_monster_equipment_system.py` (8 failures) - IN PROGRESS
- `test_pathfinding_turn_transitions.py` (4 failures)
- `test_player_migration.py` (6 failures)  
- `test_room_generators.py` (2 failures)
- `test_save_load_basic.py` (4 failures)
- `test_slime_splitting.py` (2 failures)
- `test_variable_damage.py` (3 failures)
- `test_variable_defense_combat.py` (10 failures)
- `test_variable_monster_damage.py` (4 failures)

## Strategy

1. ✅ Fix `test_monster_equipment_system.py` completely
2. Create helper functions for common mock setups  
3. Batch-fix remaining modules
4. Commit and run full suite
5. Address any remaining edge cases

## Progress

- [x] Identified root causes
- [ ] Fix monster_equipment tests (6/8 done)
- [ ] Fix pathfinding tests
- [ ] Fix player_migration tests  
- [ ] Fix save_load tests
- [ ] Fix combat tests
- [ ] Verify all passing

