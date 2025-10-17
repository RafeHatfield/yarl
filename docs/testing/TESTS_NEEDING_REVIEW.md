# Tests Needing Deeper Review

These tests have failures that are not simple mock issues. They require evaluation of whether the test expectations are outdated or if there are actual bugs in the code.

## AC Calculation Tests

### test_armor_slots.py (10 failures)
**Issue:** AC calculations don't match test expectations  
**Example:** `test_ac_with_boots` expects AC=12 (10 base + 1 DEX + 1 boots) but gets AC=11  
**Root Cause:** Either:
- AC calculation changed and tests weren't updated
- Armor slot bonuses not being applied correctly
- Test expectations were wrong from the start

**Needs:** Review of Fighter.armor_class property vs Equipment bonus calculation

### test_armor_dex_caps.py (7 failures)
**Issue:** DEX cap functionality not working as expected  
**Root Cause:** Either:
- DEX cap feature not implemented yet
- Test expectations don't match implementation
- AC calculation doesn't respect armor_type/dex_cap properties

**Needs:** Review of DEX cap implementation status

## Combat Behavior Tests

### test_d20_combat.py (2 failures)
**Issue:** Combat roll/hit mechanics don't match expectations  
**Example:** Tests expect certain hit/miss results that don't occur  
**Root Cause:** Either:
- D20 combat system changed
- Test mocking not matching actual mechanics
- RNG/determinism issues in tests

**Needs:** Review of d20 attack roll implementation

### test_slime_splitting.py (2 failures)
**Issue:** Slime splitting mechanics don't work as expected  
**Root Cause:** Either:
- Slime splitting logic changed
- Entity creation in death handler changed
- Test setup doesn't match actual game conditions

**Needs:** Review of death_functions.py slime splitting logic

## Integration/System Tests

### test_corpse_behavior.py (4 failures)
**Root Cause:** Likely related to entity death handling changes

### test_healing_and_init_fixes.py (4 failures)
**Root Cause:** Player initialization or statistics component setup

### test_combat_message_clarity.py (1 failure)
**Root Cause:** Combat message format may have changed

### test_corrosion_mechanics.py (1 failure)
**Root Cause:** Corrosion system implementation mismatch

## Recommendation

These tests should be reviewed by someone familiar with the game mechanics to determine:

1. **Are the test expectations correct?**
   - If NO: Update tests to match current implementation
   - If YES: There's a bug in the code that needs fixing

2. **Is the feature fully implemented?**
   - Some tests (like DEX caps) may be testing features not yet complete

3. **Did the mechanics change?**
   - If combat/AC/damage systems changed, tests need updating

## Files That Can Be Auto-Fixed (Mock Issues Only)

The following files likely just need boss component mocks and ComponentType imports:
- test_item_seeking_ai.py
- test_player_migration.py  
- test_loot_dropping_positions.py
- test_pathfinding_turn_transitions.py
- test_save_load_basic.py
- test_json_save_load_comprehensive.py
- test_room_generators.py
- test_item_drop_fix.py
- test_monster_loot_dropping.py
- test_entity_sorting_cache.py
- test_component_type_scoping.py
- test_boss_dialogue.py
- test_equipment_migration.py
- test_engine_integration.py
- test_map_rendering_regression.py
- test_spell_scenario_integration.py
- test_game_startup.py (smoke test)

**Total:** ~17 files likely auto-fixable

