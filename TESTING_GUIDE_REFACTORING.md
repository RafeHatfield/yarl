# Testing Guide for State Management Refactoring

**Date:** October 25, 2025  
**Branch:** `refactor/state-management-system`  
**Status:** Ready for testing

---

## Test Suite Overview

### Tests Created

1. **test_state_config.py** - 40+ tests for State Configuration System
2. **test_turn_controller.py** - 30+ tests for Turn Controller
3. **Total:** 70+ new tests

### Existing Tests

All existing tests should still pass:
- test_victory_portal_spawn.py (16 tests)
- test_victory_portal_entry.py (13 tests)
- test_victory_state_persistence.py (10 tests)
- test_victory_regression_suite.py (9 tests)
- Plus all other existing tests

**Total test count:** 110+ tests

---

## Running Tests

### Run All New Refactoring Tests

```bash
# Run state config tests
python3 -m pytest tests/test_state_config.py -v

# Run turn controller tests  
python3 -m pytest tests/test_turn_controller.py -v

# Run both
python3 -m pytest tests/test_state_config.py tests/test_turn_controller.py -v
```

### Run All Victory Tests

```bash
python3 -m pytest tests/test_victory*.py -v
```

### Run Complete Test Suite

```bash
python3 -m pytest tests/ -v
```

---

## Manual Testing Checklist

### 1. Victory Condition (Critical!)

**Purpose:** Verify refactoring didn't break the victory system

**Steps:**
```bash
python engine.py --testing
```

1. **Amulet Pickup:**
   - [ ] Pick up Amulet of Yendor (should be on level 1 in testing mode)
   - [ ] Verify dramatic messages appear
   - [ ] Verify portal spawns nearby

2. **State Persistence:**
   - [ ] After picking up amulet, move around
   - [ ] Verify you can still move (keyboard and mouse)
   - [ ] Wait a turn (let enemies act)
   - [ ] Verify you can still move (state persisted!)

3. **Portal Entry:**
   - [ ] Step on the portal
   - [ ] Verify confrontation screen appears
   - [ ] Make choice (a = give, b = keep)
   - [ ] Verify ending screen appears

**Expected Behavior:**
- ✅ Amulet pickup triggers victory sequence
- ✅ State preserved after enemy turn
- ✅ Portal entry shows confrontation
- ✅ Both endings work

**If Any Fail:** Regression! Check commits.

### 2. Normal Gameplay

**Purpose:** Verify refactoring didn't break normal gameplay

**Steps:**
```bash
python engine.py
```

1. **Movement:**
   - [ ] Arrow keys work
   - [ ] Numpad works
   - [ ] Mouse click movement works

2. **Combat:**
   - [ ] Attack enemies
   - [ ] Enemies attack back
   - [ ] Turns alternate correctly

3. **Items:**
   - [ ] Pick up items (g key)
   - [ ] Auto-pickup (right-click adjacent item)
   - [ ] Open inventory (i key)
   - [ ] Use items

4. **Menus:**
   - [ ] Character screen (c key)
   - [ ] Inventory doesn't consume turn
   - [ ] ESC closes menus

**Expected Behavior:**
- ✅ All normal gameplay works
- ✅ Turns flow correctly
- ✅ No crashes or errors

### 3. State Transitions

**Purpose:** Verify StateManager handles all states

**Test States:**
- [ ] PLAYERS_TURN (normal play)
- [ ] ENEMY_TURN (after player action)
- [ ] SHOW_INVENTORY (i key)
- [ ] CHARACTER_SCREEN (c key)
- [ ] TARGETING (cast spell)
- [ ] PLAYER_DEAD (die)
- [ ] AMULET_OBTAINED (victory condition)

**Expected Behavior:**
- ✅ All states transition correctly
- ✅ Input works in appropriate states
- ✅ Menus don't consume turns

### 4. Turn Flow

**Purpose:** Verify TurnController manages turns

**Test Scenarios:**
1. **Normal Turn:**
   - Move → enemies act → back to player turn
   - [ ] Works correctly

2. **No-Turn Actions:**
   - Open inventory → no enemy turn → still player turn
   - [ ] Works correctly

3. **State Preservation:**
   - Pick up amulet → move → enemies act → still AMULET_OBTAINED
   - [ ] State preserved correctly

**Expected Behavior:**
- ✅ Turn-consuming actions work
- ✅ Non-turn actions don't trigger enemy turn
- ✅ State preservation automatic

---

## Regression Testing

### Critical Regressions to Watch For

These are bugs we fixed - make sure they don't come back:

1. **State Reset Bug** (Bug #1)
   - Symptom: AMULET_OBTAINED resets to PLAYERS_TURN after enemy turn
   - Test: Pick up amulet, wait a turn, try to move
   - Expected: Should still be able to move

2. **Input Blocked Bug** (Bugs #2-4)
   - Symptom: Can't move after picking up amulet
   - Test: Pick up amulet, try keyboard/mouse movement
   - Expected: Movement works

3. **Portal Not Spawning** (Bug #9)
   - Symptom: Portal spawns at player's feet
   - Test: Pick up amulet, check portal location
   - Expected: Portal spawns adjacent, not on player

### If You Find a Regression

1. **Document it:**
   - What doesn't work?
   - Steps to reproduce?
   - Error messages?

2. **Check git log:**
   ```bash
   git log --oneline refactor/state-management-system
   ```
   Which commit might have caused it?

3. **Run tests:**
   ```bash
   python3 -m pytest tests/test_victory*.py -v
   python3 -m pytest tests/test_state_config.py -v
   ```
   Do tests catch it?

4. **Create test:**
   Add regression test to appropriate file

---

## Performance Testing

### Expected Performance

Refactoring should have **minimal performance impact**:

- StateManager queries are O(1) dictionary lookups
- TurnController adds ~1-2 function calls per turn
- No noticeable lag

### Performance Check

Play for 10 minutes and verify:
- [ ] No noticeable slowdown
- [ ] Smooth turn transitions
- [ ] No lag when changing states

---

## Success Criteria

### All Tests Must Pass

```bash
# This should show all passing:
python3 -m pytest tests/test_state_config.py -v
python3 -m pytest tests/test_turn_controller.py -v
python3 -m pytest tests/test_victory*.py -v
```

### Manual Tests Must Pass

- [ ] Victory condition works end-to-end
- [ ] Normal gameplay unaffected
- [ ] All states work
- [ ] Turn flow correct

### No Regressions

- [ ] No bugs from victory implementation returned
- [ ] No new bugs introduced
- [ ] Performance acceptable

---

## After Testing

### If All Tests Pass ✅

1. Mark testing task complete
2. Create final summary commit
3. Merge to main
4. Celebrate! 🎉

### If Tests Fail ❌

1. Document failures
2. Fix issues
3. Re-test
4. Don't merge until all pass!

---

## Notes for Testers

- **Testing time:** ~30-60 minutes for comprehensive testing
- **Focus areas:** Victory condition, state transitions, turn flow
- **Most critical:** State preservation after enemy turn
- **Least critical:** Performance (should be identical)

---

## Quick Test (5 minutes)

If you just want to verify basics work:

1. Run victory test in testing mode
2. Pick up amulet, move around, step on portal
3. If that works, run test suite
4. If tests pass, you're good! ✅

---

**Remember:** This refactoring touches core systems. Thorough testing is important!

