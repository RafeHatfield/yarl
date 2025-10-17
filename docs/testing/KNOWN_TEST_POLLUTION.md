# Known Test Pollution Issues

These tests PASS when run individually but FAIL in the full suite.
This indicates shared state that isn't being cleaned up between tests.

## Affected Tests (6 tests across 3 files)

### test_boss_dialogue.py
- `TestBossDamageDialogue::test_boss_low_hp_dialogue` ✅ alone, ❌ in suite

### test_loot_dropping_positions.py  
- `TestLootDropPositions::test_drop_monster_loot_no_items` ✅ alone, ❌ in suite
- `TestLootDropPositions::test_drop_monster_loot_spreads_items` ✅ alone, ❌ in suite
- (possibly others)

### test_monster_loot_dropping.py
- `TestMonsterLootDropping::test_dropped_weapon_can_be_picked_up_once` ✅ alone, ❌ in suite

## Root Causes (Likely)

1. **LootQualityGenerator singleton** - Not reset between tests
2. **EntityRegistry** - Cached entity definitions  
3. **AppearanceGenerator** - Global state for item appearances
4. **Component registries** - Not clearing between tests

## Solution

Add proper tearDown to clear singletons:
```python
def tearDown(self):
    # Clear loot generator
    from components.loot import _loot_generator
    _loot_generator = None
    
    # Clear appearance generator
    from config.item_appearances import _appearance_generator
    _appearance_generator = None
    
    # Clear entity registry cache
    from config.entity_registry import _entity_registry
    _entity_registry = None
```

Or use pytest fixtures with proper scope.

## Status
**Documented but not fixed** - These are HIGH value tests that work correctly.
The issue is test isolation, not test logic. Will fix after addressing
critical failures.

**Count:** 6 pollution tests (not counting in "failing" count for now since they pass individually)

