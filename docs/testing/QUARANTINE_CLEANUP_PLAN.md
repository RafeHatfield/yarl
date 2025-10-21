# Quarantine Cleanup Plan

**Goal:** Review all 64 skipped tests and either fix, delete, or document why they remain skipped.

**Status:** Starting with 64 skipped tests (0 failing, 2,214 passing)

---

## 📊 Current Quarantine Breakdown

### **Tier 1: Entire Files Quarantined (44 tests)**

#### 🔴 **HIGH VALUE - Complex Integration (Need Rewrite)**

1. **`test_engine_integration.py`** (12 tests)
   - **Why Skipped:** Engine architecture changed, mocking out of sync
   - **Value:** HIGH - Tests core engine initialization and game loop
   - **Decision:** REWRITE - These are critical integration tests
   - **Estimated Effort:** 4-6 hours (complex)
   - **Priority:** LOW (functionality works in-game)

2. **`integration/test_game_logic_integration.py`** (8 tests)
   - **Why Skipped:** Integration test needs proper setup
   - **Value:** HIGH - Tests player movement, combat, inventory
   - **Decision:** FIX or REWRITE - Valuable end-to-end tests
   - **Estimated Effort:** 2-3 hours
   - **Priority:** MEDIUM (core gameplay verification)

3. **`integration/test_spell_scenario_integration.py`** (8 tests)
   - **Why Skipped:** Spell integration needs refactor
   - **Value:** MEDIUM-HIGH - Tests spell targeting and effects
   - **Decision:** FIX or REWRITE - Tests important mechanics
   - **Estimated Effort:** 2-3 hours
   - **Priority:** MEDIUM (spells work in-game)

#### 🟡 **MEDIUM VALUE - Behavioral Tests (Brittle)**

4. **`comprehensive/test_action_validation.py`** (9 tests)
   - **Why Skipped:** Complex action validation integration
   - **Value:** MEDIUM - Tests action handling robustness
   - **Decision:** EVALUATE - May be testing implementation details
   - **Estimated Effort:** 2-3 hours
   - **Priority:** LOW (actions work in-game)

5. **`test_item_drop_fix.py`** (7 tests)
   - **Why Skipped:** Tests check exact item drop counts, loot system refactored
   - **Value:** LOW-MEDIUM - Tests specific bug fix from past
   - **Decision:** **DELETE** - Regression test for fixed bug, loot system changed
   - **Estimated Effort:** 0 (delete)
   - **Priority:** HIGH (quick win)

### **Tier 2: Individual Tests Skipped (20 tests)**

#### 🟢 **QUICK WINS - Simple Fixes**

6. **`test_entity_factory.py`** (1 test)
   - **Test:** `test_create_spell_item_not_found`
   - **Why Skipped:** Factory error handling changed
   - **Decision:** **DELETE** - Testing error case that changed
   - **Effort:** 0 (delete)

7. **`test_ring_equipping.py`** (1 test)
   - **Test:** `test_ring_can_be_equipped`
   - **Why Skipped:** Message format changed
   - **Decision:** **FIX** - Update assertion (5 min fix)
   - **Effort:** 5 minutes

8. **`test_corrosion_mechanics.py`** (1 test)
   - **Test:** `test_slime_has_corrosion_ability`
   - **Why Skipped:** Slime definition may have changed
   - **Decision:** **FIX or DELETE** - Check if feature still exists
   - **Effort:** 10 minutes

9. **`regression/test_critical_bugs_regression.py`** (1 test)
   - **Test:** `test_targeting_left_click_regression`
   - **Why Skipped:** Turn economy changed (expected behavior changed)
   - **Decision:** **DELETE** - Regression test for old behavior
   - **Effort:** 0 (delete)

#### 🔵 **COMPLEX FIXES - Integration/Mocking Issues**

10. **`test_throwing_system.py`** (2 tests)
    - **Why Skipped:** Complex mock setup doesn't match implementation
    - **Decision:** **LEAVE SKIPPED** - 8/10 tests passing is good enough
    - **Effort:** N/A

11. **`test_monster_equipment_system.py`** (5 tests)
    - **Why Skipped:** Loot system refactored, tests check exact counts
    - **Decision:** **DELETE** - Brittle tests checking implementation details
    - **Effort:** 0 (delete)

12. **`test_room_generators.py`** (3 tests)
    - **Why Skipped:** EntityFactory setup issues
    - **Decision:** **FIX** - Valuable room generation tests
    - **Effort:** 30 minutes (fixture setup)

13. **`test_monster_item_usage.py`** (1 test)
    - **Why Skipped:** Mock doesn't trigger AI path
    - **Decision:** **LEAVE SKIPPED** - 22/23 tests passing
    - **Effort:** N/A

14. **`test_item_seeking_ai.py`** (1 test)
    - **Why Skipped:** Mock doesn't execute pickup logic
    - **Decision:** **LEAVE SKIPPED** - 50/51 tests passing
    - **Effort:** N/A

15. **`integration/test_ai_integration.py`** (1 test)
    - **Why Skipped:** Mock attack doesn't kill monster
    - **Decision:** **LEAVE SKIPPED** - 7/8 tests passing
    - **Effort:** N/A

16. **`test_monster_migration.py`** (1 test)
    - **Why Skipped:** Hardcoded mock values outdated
    - **Decision:** **LEAVE SKIPPED** - 22/23 tests passing
    - **Effort:** N/A

17. **`test_wand_targeting_regression.py`** (1 test)
    - **Why Skipped:** GameStateManager API refactored
    - **Decision:** **DELETE** - Regression test for old API
    - **Effort:** 0 (delete)

18. **`test_entity_sorting_cache.py`** (1 test)
    - **Why Skipped:** Integration test with complex mocking
    - **Decision:** **LEAVE SKIPPED** - 14/15 tests passing
    - **Effort:** N/A

---

## 🎯 Recommended Action Plan

### **Phase 1: Quick Wins (DELETE brittle tests) - 30 minutes**

**Goal:** Remove low-value, brittle tests that are testing old behavior or implementation details.

**Delete:** (14 tests)
- [ ] `test_item_drop_fix.py` (7 tests) - Brittle, exact count checks
- [ ] `test_monster_equipment_system.py` (5 tests) - Brittle, exact count checks
- [ ] `test_entity_factory.py` (1 test) - Testing obsolete error case
- [ ] `regression/test_critical_bugs_regression.py` (1 test) - Old behavior regression

**Result:** 64 → 50 skipped tests

### **Phase 2: Simple Fixes - 1 hour**

**Goal:** Fix tests with simple assertion updates or setup fixes.

**Fix:** (5 tests)
- [ ] `test_ring_equipping.py` (1 test) - Update assertion
- [ ] `test_corrosion_mechanics.py` (1 test) - Check/fix feature
- [ ] `test_room_generators.py` (3 tests) - Add EntityFactory fixture

**Result:** 50 → 45 skipped tests

### **Phase 3: Evaluate Large Files - 2 hours**

**Goal:** Decide fate of large quarantined files.

**Evaluate:**
- [ ] `comprehensive/test_action_validation.py` (9 tests)
  - Run tests to see current state
  - Delete if testing implementation details
  - Fix if testing valuable behavior

**Result:** 45 → 36-45 skipped tests (depends on evaluation)

### **Phase 4: Document & Leave (OPTIONAL)**

**Goal:** Explicitly document that remaining tests are intentionally skipped.

**Files to Leave Skipped:** (27-36 tests)
- `test_engine_integration.py` (12 tests) - Complex, low priority
- `integration/test_game_logic_integration.py` (8 tests) - For future work
- `integration/test_spell_scenario_integration.py` (8 tests) - For future work
- Various 1-test skips (9 tests) - Already 90%+ passing in their files

**Update `QUARANTINED_TESTS.md`** with:
- Accurate list of skipped tests
- Reasons for each
- Decision on whether to fix later or leave permanently

**Result:** Final count documented and justified

---

## 📈 Success Metrics

### **Minimum Success:**
- Delete 14 brittle tests
- Fix 5 simple tests
- Document remaining skipped tests
- **Result:** ~45 skipped tests (all justified and documented)

### **Stretch Goal:**
- Complete Phase 3 evaluation
- Fix or delete `test_action_validation.py`
- Rewrite 1-2 integration test files
- **Result:** <40 skipped tests

---

## 🚀 Implementation Order

1. **TODAY: Phase 1** (30 min) - Delete brittle tests
2. **TODAY: Phase 2** (1 hour) - Simple fixes
3. **TODAY: Phase 3** (2 hours) - Evaluation
4. **OPTIONAL: Phase 4** (1 hour) - Documentation

**Total Estimated Time:** 4-5 hours for complete cleanup

---

## 💡 Key Decision Criteria

### **DELETE if:**
- ✅ Testing old behavior that changed
- ✅ Brittle (checking exact counts, message formats)
- ✅ Low value (regression test for one-off bug)
- ✅ Redundant with other tests

### **FIX if:**
- ✅ High value (tests core functionality)
- ✅ Simple fix (<30 min)
- ✅ Unique coverage (not tested elsewhere)

### **LEAVE SKIPPED if:**
- ✅ File already has 90%+ tests passing
- ✅ Complex integration needing full rewrite
- ✅ Low priority (functionality works in-game)
- ✅ Would take >2 hours to fix

---

## 📝 Notes

- **Philosophy:** Focus on test suite health, not % passing
- **Priority:** Delete brittle > Fix valuable > Document remaining
- **Value:** Tests should prevent regressions, not slow development
- **Coverage:** Core gameplay is already well-tested (2,214 passing tests)

---

**Next Step:** Start Phase 1 - Delete brittle tests!

