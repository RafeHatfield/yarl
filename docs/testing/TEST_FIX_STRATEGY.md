# Test Fix Strategy & Implementation Guide

**Created:** October 18, 2025  
**Purpose:** Systematic approach to achieve 100% passing test suite  
**Current Status:** 2,025 / 2,387 passing (84.8%), 111 failing, 248 quarantined

---

## 🎯 **Strategic Approach**

### Philosophy
- **Quality over Speed:** Fix tests properly, don't paper over issues
- **Patterns over One-offs:** Document patterns for reuse
- **Delete over Fix:** Remove obsolete tests for removed features
- **Real over Mock:** Use real components where feasible

### Priority Order
1. **Quarantined Tests** - Known issues, documented, ready for systematic review
2. **Simple Failures** - Similar patterns, bulk fixes possible
3. **Complex Failures** - Deep mocking issues, may need test restructure

---

## 📋 **Test Categories & Fix Strategies**

### Category 1: **Quarantined Tests** (248 tests) - **START HERE**

These tests are already identified, documented, and skipped. They're the best candidates for systematic fixing.

#### **Quick Wins (Est. 2-4 hours)**
Priority: ⭐⭐⭐ **HIGH** - Do these first!

1. **`test_slime_splitting.py`** (2 tests)
   - **Issue:** Slime splitting logic doesn't match tests
   - **Strategy:** Review slime implementation, update test expectations
   - **Effort:** 30-60 min
   - **Decision:** Keep & Fix

2. **Simple API updates** (~10-15 tests scattered)
   - **Pattern:** Function renamed or signature changed
   - **Strategy:** Bulk find/replace for common patterns
   - **Effort:** 1-2 hours
   - **Decision:** Keep & Fix

#### **Medium Effort (Est. 4-8 hours)**
Priority: ⭐⭐ **MEDIUM** - After quick wins

3. **`test_corpse_behavior.py`** (4 tests)
   - **Issue:** Corpse mechanics may have changed
   - **Strategy:** Review death handling, verify corpse creation
   - **Effort:** 1-2 hours
   - **Decision:** Keep & Fix (death mechanics are important)

4. **`test_armor_slots.py`** (10 tests)
   - **Issue:** AC bonuses from armor slots not applying
   - **Strategy:** Verify armor slot integration, check AC calculation
   - **Effort:** 2-3 hours
   - **Decision:** Keep & Fix (equipment is core)

5. **`test_armor_dex_caps.py`** (7 tests)
   - **Issue:** DEX cap functionality not working
   - **Strategy:** Check if DEX cap is implemented, update tests or code
   - **Effort:** 1-2 hours
   - **Decision:** Investigate first - feature may be unimplemented

6. **`test_d20_combat.py`** (2 tests)
   - **Issue:** Hit/miss mechanics don't match expectations
   - **Strategy:** Review d20 combat implementation vs test assumptions
   - **Effort:** 1 hour
   - **Decision:** Keep & Fix (core combat)

#### **High Effort (Est. 8-16 hours)**
Priority: ⭐ **LOW** - Last resort, evaluate if worth it

7. **Integration Test Suites** (~40-50 tests)
   - Files:
     - `test_save_load_basic.py` (4 tests)
     - `test_json_save_load_comprehensive.py` (6 tests)
     - `test_pathfinding_turn_transitions.py` (4 tests)
     - `test_engine_integration.py` (3 tests)
     - `test_healing_and_init_fixes.py` (4 tests)
     - `test_spell_scenario_integration.py` (6 tests)
     - `test_map_rendering_regression.py` (5 tests)
     - `test_game_startup.py` (4 tests)
     - `test_game_logic_integration.py` (? tests)
   
   - **Common Issues:**
     - AppearanceGenerator not initialized
     - Full game state setup required
     - Mock APIs out of sync with real code
     - Complex interdependencies
   
   - **Strategy Options:**
     1. **Invest in Fixtures:** Create comprehensive test fixtures
     2. **Simplify Tests:** Break into smaller, focused unit tests
     3. **Delete & Recreate:** Remove and write new simpler tests
     4. **Defer:** Mark as "needs major refactor" for future sprint
   
   - **Recommended:** Start with Option 4 (defer), revisit after quick wins
   - **Decision:** Evaluate each file individually

#### **Obsolete Tests (Est. 1-2 hours)**
Priority: ⭐⭐⭐ **HIGH** - Easy wins!

8. **Tests for Removed Features** (~10-20 tests)
   - **Strategy:** Grep for removed classes/functions, delete tests
   - **Examples:**
     - Old IdentifyModeEffect API tests (already done)
     - Removed AI behaviors
     - Deprecated item functions
   - **Effort:** 1-2 hours
   - **Decision:** **DELETE** - No value in keeping

---

### Category 2: **Current Failing Tests** (111 tests)

#### **Sub-Category 2A: Simple Mock Fixes** (~30-40 tests)
**Estimated Time:** 3-4 hours

**Common Patterns:**

1. **Missing Status Effects Mock**
   - **Symptom:** `TypeError: unsupported operand type(s) for +=: 'int' and 'Mock'`
   - **Fix Pattern:**
     ```python
     entity.status_effects = Mock()
     entity.status_effects.get_effect = Mock(return_value=None)
     ```
   - **Affected Tests:** Combat, AI, inventory tests
   - **Bulk Fix:** Can apply to many tests at once

2. **Missing Entity Constructor Args**
   - **Symptom:** `TypeError: Entity.__init__() missing 2 required positional arguments: 'color' and 'name'`
   - **Fix Pattern:**
     ```python
     # Old: Entity(0, 0, 'T', fighter=fighter)
     # New: Entity(0, 0, 'T', (255, 255, 255), 'Test Entity', fighter=fighter)
     ```
   - **Affected Tests:** Entity creation tests
   - **Bulk Fix:** Search/replace across test files

3. **Status Effect Duration Not Decrementing**
   - **Symptom:** `assert effect.duration == initial_duration - 1` fails
   - **Issue:** `process_turn_start()` may not decrement, or decrements in `process_turn_end()`
   - **Fix:** Update test to check correct method or verify implementation
   - **Affected Tests:** 1-2 tests (minor)

4. **Potion Effects Not Applying**
   - **Symptom:** `assert entity.status_effects.has_effect("speed")` fails
   - **Issue:** Mocking might interfere with real StatusEffectManager
   - **Fix:** Use real StatusEffectManager instead of Mock
   - **Affected Tests:** `test_new_potions.py` (16 tests)

#### **Sub-Category 2B: Complex Mock Issues** (~40-50 tests)
**Estimated Time:** 8-12 hours

**Characteristics:**
- Deep mock chains (mock.object.method.return_value.attribute)
- Mocks interfering with real logic
- Tests tightly coupled to implementation details

**Examples:**
- `test_base_damage_system.py` (4 failing)
- `test_combat_debug_logging.py` (4 failing)
- `test_variable_damage.py` (3 failing)
- `test_variable_defense_combat.py` (11 failing)
- Combat integration tests

**Strategies:**

1. **Replace Mocks with Real Objects**
   - **When:** Mock is interfering with logic
   - **How:** Use real Fighter, Equipment, StatusEffectManager
   - **Tradeoff:** Slower tests, but more reliable

2. **Simplify Test Scope**
   - **When:** Test is doing too much
   - **How:** Break into smaller, focused tests
   - **Tradeoff:** More tests, but easier to maintain

3. **Use Test Builders**
   - **When:** Complex object creation repeated
   - **How:** Create helper functions like `create_test_fighter()`
   - **Tradeoff:** Upfront work, but cleaner tests

**Recommendation:** Start with #1 (real objects), measure test speed impact

#### **Sub-Category 2C: Unknown Issues** (~20-30 tests)
**Estimated Time:** 4-6 hours

Tests that fail for unclear reasons. Need investigation.

**Strategy:**
1. Run test with `-vv --tb=long` for full context
2. Add debug prints to understand failure
3. Check if feature still exists or was removed
4. Decide: Fix, Simplify, or Delete

---

## 🔧 **Implementation Patterns**

### Pattern 1: **Standard Entity Test Setup**

```python
def setup_method(self):
    """Standard setup for entity-based tests."""
    # Create fighter with resistances
    fighter = Fighter(hp=100, defense=2, power=5)
    
    # Create entity with all required params
    self.entity = Entity(
        x=0, y=0,
        char='@',
        color=(255, 255, 255),
        name='Test Entity',
        fighter=fighter
    )
    
    # Add status effects (CRITICAL!)
    self.entity.status_effects = StatusEffectManager(self.entity)
    
    # Mock optional components
    self.entity.get_component_optional = Mock(return_value=None)
    
    # Add equipment if needed
    self.entity.equipment = Equipment(self.entity)
```

### Pattern 2: **Combat Test Setup**

```python
def setup_method(self):
    """Setup for combat tests."""
    # Attacker
    self.attacker = self._create_test_entity("Attacker", power=5)
    
    # Defender  
    self.defender = self._create_test_entity("Defender", defense=2)

def _create_test_entity(self, name, **fighter_kwargs):
    """Helper to create test entities."""
    fighter = Fighter(hp=100, **fighter_kwargs)
    entity = Entity(0, 0, 'T', (255, 255, 255), name, fighter=fighter)
    
    # Essential mocking
    entity.status_effects = StatusEffectManager(entity)
    entity.equipment = Equipment(entity)
    entity.get_component_optional = Mock(return_value=None)
    
    return entity
```

### Pattern 3: **Checking for Obsolete Tests**

```bash
# Find tests referencing removed code
grep -r "OldClassName" tests/
grep -r "removed_function" tests/

# Check if test file's main subject still exists
# Example: Does IdentifyModeEffect still have these methods?
grep -A 10 "class IdentifyModeEffect" components/status_effects.py
```

### Pattern 4: **Bulk Mock Addition**

```bash
# Add status_effects mock to all test setups
# Find test files missing it:
grep -L "status_effects" tests/test_*.py

# Then manually add to setUp/setup_method in each file
```

---

## 📊 **Execution Plan**

### **Session 2: Quarantine Quick Wins** (4-6 hours)
**Goal:** Clear 30-50 quarantined tests

1. **Identify Obsolete Tests** (1 hour)
   - Grep for removed features
   - Delete obsolete test files
   - **Target:** -10-20 tests

2. **Fix Simple Quarantined Tests** (2-3 hours)
   - `test_slime_splitting.py`
   - Simple API updates
   - **Target:** -10-15 tests

3. **Fix Medium Quarantined Tests** (2-3 hours)
   - `test_corpse_behavior.py`
   - `test_d20_combat.py`
   - **Target:** -6 tests

**Session 2 Target:** 2,075+ passing (87%), <80 failing, <200 quarantined

### **Session 3: Simple Mock Fixes** (4-6 hours)
**Goal:** Apply bulk fixes to failing tests

1. **Bulk Status Effects Mocking** (2 hours)
   - Add to all combat tests
   - Add to all AI tests
   - **Target:** -20-30 tests

2. **Bulk Entity Constructor Fixes** (1 hour)
   - Search/replace across test files
   - **Target:** -5-10 tests

3. **Fix Potion Tests** (1-2 hours)
   - Use real StatusEffectManager
   - **Target:** -16 tests

**Session 3 Target:** 2,125+ passing (89%), <50 failing, <200 quarantined

### **Session 4: Medium Quarantined Tests** (4-6 hours)
**Goal:** Address armor/equipment tests

1. **`test_armor_slots.py`** (2-3 hours)
2. **`test_armor_dex_caps.py`** (1-2 hours)  
3. **Review remaining quarantined** (1-2 hours)

**Session 4 Target:** 2,150+ passing (90%), <40 failing, <180 quarantined

### **Session 5: Complex Mock Fixes** (6-8 hours)
**Goal:** Tackle combat system test mocking

1. **Create test helpers** (2 hours)
   - `create_test_fighter()`
   - `create_test_combat_scenario()`

2. **Fix combat tests** (4-6 hours)
   - Base damage system
   - Variable damage/defense
   - Combat debug logging

**Session 5 Target:** 2,200+ passing (92%), <20 failing, <170 quarantined

### **Session 6: Final Push** (4-6 hours)
**Goal:** 100% passing, 0 quarantined

1. **Fix remaining failures** (2-3 hours)
2. **Review high-effort quarantined** (2-3 hours)
   - Keep valuable integration tests
   - Delete or defer rest

**Session 6 Target:** 2,387 passing (100%), 0 failing, 0 quarantined ✨

---

## 🎯 **Success Metrics**

### **Per Session**
- **Tests Fixed:** Minimum 30-50 per session
- **Pass Rate Increase:** +3-5% per session
- **Time per Test:** Average 5-10 minutes (including research)

### **Overall Goals**
- **Pass Rate:** 100% (2,387 / 2,387)
- **Run Time:** <30 seconds
- **No Quarantined Tests:** All reviewed (keep/fix/delete)
- **No Flaky Tests:** Consistent pass/fail behavior

### **Quality Gates**
- ✅ All core systems tested (turn economy, combat, resistance)
- ✅ No mock-only tests (use real objects where possible)
- ✅ Tests fail for right reasons (not mocking issues)
- ✅ Clear test names and documentation
- ✅ Fast execution (<30s total)

---

## 🔍 **Investigation Checklist**

When a test fails:

1. **Read the error carefully**
   - What's the actual error message?
   - What line is failing?
   - TypeError, AttributeError, AssertionError?

2. **Check if feature exists**
   - Is the class/function being tested still in the codebase?
   - Has it been renamed or moved?
   - Has the API changed?

3. **Check test age**
   - When was the test last modified?
   - Is it testing old behavior?
   - Has the feature evolved since?

4. **Verify test value**
   - Is this testing important functionality?
   - Is it duplicating other tests?
   - Would we notice if we deleted it?

5. **Decision matrix**
   - **Feature gone?** → DELETE test
   - **API changed?** → UPDATE test
   - **Test broken?** → FIX test
   - **Feature changed?** → REWRITE test
   - **Low value?** → DELETE test
   - **Too complex?** → DEFER or SIMPLIFY

---

## 📝 **Documentation Standards**

When fixing tests:

1. **Commit Message Format:**
   ```
   ✅ Fix: test_file_name.py - All N tests passing
   
   - Fixed issue A
   - Fixed issue B
   - Deleted obsolete test C
   
   Before: X pass, Y fail
   After: Z pass, 0 fail
   
   Impact: +N passing tests
   ```

2. **Add Comments for Non-Obvious Fixes:**
   ```python
   # CRITICAL: StatusEffectManager must be real, not Mock,
   # because drink_speed_potion() needs to call add_effect()
   self.entity.status_effects = StatusEffectManager(self.entity)
   ```

3. **Document Deletions:**
   ```python
   # DELETED: test_old_api_method()
   # Reason: IdentifyModeEffect.identifies_used_this_turn removed in v3.10.0
   # Old API replaced with automatic identification at turn start
   ```

---

## 💡 **Lessons Learned (Session 1)**

### **What Worked Well**
1. ✅ Systematic pattern identification
2. ✅ Bulk fixes for similar issues
3. ✅ Deleting obsolete tests instead of fixing
4. ✅ Documenting patterns for reuse

### **What Was Challenging**
1. ⚠️ Deep mock chains in combat tests
2. ⚠️ Tests tightly coupled to implementation
3. ⚠️ Unclear if some features still exist
4. ⚠️ Time-consuming investigation per test

### **Key Insights**
1. 💡 Many quarantined tests likely simpler than failing tests
2. 💡 Mock objects cause more problems than they solve
3. 💡 Better to use real objects in tests when possible
4. 💡 Test maintenance is ongoing - need good patterns

---

## 🚀 **Quick Reference**

### **Common Fixes**

```python
# Fix 1: Add status effects
entity.status_effects = StatusEffectManager(entity)

# Fix 2: Fix Entity constructor
Entity(x, y, char, (255, 255, 255), 'Name', **components)

# Fix 3: Mock status effects to return None
entity.status_effects = Mock()
entity.status_effects.get_effect = Mock(return_value=None)

# Fix 4: Use any() for checking consumed flag
assert any(r.get('consumed') for r in results)

# Fix 5: Handle string/enum resistance types
# Already fixed in fighter.py with normalize_resistance_type()
```

### **Commands**

```bash
# Run specific test file
pytest tests/test_file.py -v

# Run with full traceback
pytest tests/test_file.py -vv --tb=long

# Run only quarantined tests
pytest -m "skip" tests/

# Count failing tests by file
pytest --tb=no -q 2>&1 | grep "FAILED" | awk -F"::" '{print $1}' | sort | uniq -c | sort -rn

# Find tests missing status_effects
grep -L "status_effects" tests/test_*.py
```

---

**Status:** ✅ Session 2 Complete - Major Progress + Critical Bug Found  
**Next Action:** Investigate AC calculation bug, then Session 3  
**Progress:** 43 tests fixed (+30 passing, +13 partial)

---

## 🔍 **CRITICAL BUG DISCOVERED - Session 2**

### **AC Bonus Calculation Not Working**

**Issue:** `Fighter.armor_class` property not reading `Equippable.armor_class_bonus`

**Impact:** ~15 tests failing across 3 files:
- `test_d20_combat.py` (2 tests)
- `test_armor_slots.py` (6 tests)
- `test_armor_dex_caps.py` (8 tests)

**Symptoms:**
- Tests create armor with `armor_class_bonus=2`
- `fighter.armor_class` returns 11 (base 10 + DEX 1)
- **Expected:** 13 (base 10 + DEX 1 + armor 2)
- **Actual:** 11 (armor bonus not applied)

**Test Setup Pattern:**
```python
helmet = Entity(0, 0, '^', (255, 255, 255), 'Helmet')
helmet.equippable = Equippable(EquipmentSlots.HEAD, armor_class_bonus=1)
helmet.components = Mock()
helmet.components.has = Mock(return_value=False)  # Use hasattr fallback

player.equipment = Equipment(player)
player.equipment.head = helmet

# This fails:
assert player.fighter.armor_class == 12  # Expected: 10 + 1 DEX + 1 helmet
# Actual: 11 (helmet bonus not applied)
```

**Investigation Needed:**
1. Check `Fighter.armor_class` property (fighter.py:322-380)
2. Verify `_get_equipment()` returns correct Equipment
3. Check iteration over equipment slots (main_hand, off_hand, head, chest, feet)
4. Verify `item.equippable.armor_class_bonus` is accessible
5. Check if `components.has()` logic is correct

**Workarounds Attempted:**
- ✅ Equipment(owner) initialization - didn't fix
- ✅ Mock components.has(return_value=False) - didn't fix
- ❌ Real Equippable objects used - still fails

**Root Cause Hypothesis:**
The `armor_class` property iteration may not be finding equipped items, OR the `armor_class_bonus` attribute isn't being read correctly from Equippable objects.

**Priority:** 🔥 **HIGH** - Blocking 15 tests, core combat mechanic

---

**Status:** 📋 Strategy Document Complete + AC Bug Documented  
**Next Action:** **Fix AC calculation bug**, then continue Session 3  
**Expected Outcome:** +15 tests once bug fixed


