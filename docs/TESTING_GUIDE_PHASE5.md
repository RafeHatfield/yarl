```# Phase 5 Testing Guide - How to Stop the "Going in Circles" Problem

**Created:** October 29, 2025  
**Problem:** Portal keeps breaking, testing takes forever, changes break previous fixes  
**Solution:** Automated testing + proper development workflow  

---

## The Core Problems

### 1. Python Code Caching
**Symptom:** "I changed the code but the game still has the old behavior"  
**Cause:** Python caches bytecode in `__pycache__/` directories  
**Result:** Game runs OLD code even after you edit files

### 2. Manual Testing is Slow
**Symptom:** "Testing takes a few minutes to set up every time"  
**Cause:** Must play through to Level 25, kill enemies, pick up items  
**Result:** Testing becomes painful, bugs slip through

### 3. No Regression Protection
**Symptom:** "We fix something, then break something else"  
**Cause:** No automated tests to catch when changes break working features  
**Result:** Whack-a-mole bug fixing

---

## The Solution: 3-Tier Testing Strategy

###  Tier 1: ALWAYS Clear Cache Before Testing

**NEVER start the game with `python3 engine.py` directly!**

**Instead use:**
```bash
make clean-run
```

This clears Python cache THEN starts the game with fresh code.

**Or manually:**
```bash
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null
find . -name '*.pyc' -delete 2>/dev/null
python3 engine.py
```

### Tier 2: Quick Validation (5 seconds)

**Before manual testing**, run automated validation:

```bash
python3 test_phase5_quick.py
```

This tests the **actual services code** without needing to play the game.

**Output if working:**
```
✅ ALL TESTS PASSED - Phase 5 core functionality is working!
```

**Output if broken:**
```
❌ FAIL: Portal entry not detected
  Player final position: (11, 10)
  Portal position: (11, 10)
```

**This catches issues in 5 seconds instead of 5 minutes!**

### Tier 3: Pre-Commit Hook (Automatic)

A git hook now runs critical tests **automatically before every commit**.

If tests fail, **commit is blocked** until you fix them.

```bash
git commit -m "Fix portal"
🧪 Running Phase 5 critical path tests...
❌ CRITICAL TESTS FAILED - commit blocked!
```

**To bypass** (not recommended):
```bash
git commit --no-verify -m "WIP: debugging"
```

---

## Development Workflow

### OLD Workflow (Slow, Fragile)

```
1. Make code change
2. Start game: python3 engine.py
3. Play to Level 25 (2-3 minutes)
4. Kill ritualists
5. Pick up items
6. Test portal
7. ❌ Portal broken
8. Repeat from step 1
```

**Time per cycle:** 5-10 minutes  
**Frustration:** High  
**Bugs caught:** Late (after full playthrough)

### NEW Workflow (Fast, Robust)

```
1. Make code change
2. Run: python3 test_phase5_quick.py (5 seconds)
3. ✅ Tests pass? Great!
   ❌ Tests fail? Fix now (you know exactly what's broken)
4. Optional: make clean-run (for full game test)
5. git commit (pre-commit hook runs tests automatically)
```

**Time per cycle:** 5-30 seconds  
**Frustration:** Low  
**Bugs caught:** Early (before even running game)

---

## Quick Reference Commands

```bash
# Development
make clean         # Clear Python cache
make run           # Start game with fresh code
make clean-run     # Clear cache + start game (RECOMMENDED)

# Testing
python3 test_phase5_quick.py          # Quick validation (5 sec)
python3 run_critical_tests.py         # Comprehensive tests
pytest tests/test_phase5_critical_paths.py -v  # If you have pytest

# Git
git commit         # Automatically runs tests
git commit --no-verify  # Skip tests (use sparingly)
```

---

## What Tests Cover

### Critical Path Tests

1. **Pickup Ruby Heart → Portal Spawns**
   - Tests: PickupService.execute_pickup()
   - Validates: triggers_victory detection, portal spawning, state transition

2. **Step on Portal → Confrontation Triggers**
   - Tests: MovementService.execute_movement()
   - Validates: portal entry detection, position check, confrontation flag

3. **Full Flow: Pickup → Move → Trigger**
   - Tests: Complete integration
   - Validates: End-to-end functionality

4. **Negative Test: Portal Without Ruby Heart**
   - Tests: Portal shouldn't work without prerequisite
   - Validates: State checking logic

---

## Common Issues & Solutions

### Issue 1: "Portal not working after code change"

**Diagnosis:**
```bash
# Check if services are being called
grep "MovementService\|PickupService" debug.log | tail -20
```

**If no logs:** Game running old code  
**Solution:** `make clean-run`

### Issue 2: "Tests pass but game still broken"

**Cause:** Services work, but integration doesn't  
**Solution:** Check that handlers are calling services correctly

```python
# Search for old direct implementations
grep -r "player.move" game_actions.py
grep -r "inventory.add_item" game_actions.py

# Should NOT find direct implementations in handlers
# Should ONLY find service calls
```

### Issue 3: "Commit blocked by tests"

**Good!** Tests caught a regression.

**Next steps:**
1. Read the test failure message
2. Fix the issue
3. Run `python3 test_phase5_quick.py` to verify
4. Try commit again

---

## Future Improvements

### Add More Critical Tests

When adding new Phase 5 features, add to `test_phase5_critical_paths.py`:

```python
def test_CRITICAL_your_new_feature(self, minimal_game_state):
    """CRITICAL: Your feature description."""
    # Test code here
    assert expected_behavior, "Failure message"
```

### Add Integration Tests

For boss fights, endings, etc.:

```python
def test_boss_fight_ending_1a():
    """Test complete boss fight flow for ending 1a."""
    # Simulate entire boss fight
    # Verify ending screen shows
```

### Add Performance Tests

Ensure services don't slow down the game:

```python
def test_movement_service_performance():
    """Ensure MovementService completes in <1ms."""
    # Benchmark execute_movement()
```

---

## Why This Solves "Going in Circles"

### Before (Circular Hell)

```
Make change → Test manually (5 min) → Portal broken →  
Make fix → Test manually (5 min) → Boss broken →
Make fix → Test manually (5 min) → Portal broken again →
INFINITE LOOP 😫
```

### After (Linear Progress)

```
Make change → Quick test (5 sec) → ✅ Pass →
Make change → Quick test (5 sec) → ❌ Fail (see exactly what's broken) → Fix immediately →
Quick test (5 sec) → ✅ Pass → Commit →
DONE ✅
```

---

## Preventing Specific Phase 5 Bugs

### Duplicate Logic Bug (SOLVED)
**Was:** Portal check in 2 places (keyboard + mouse)  
**Now:** Portal check in 1 place (MovementService)  
**Prevention:** Services enforce single source of truth

### Code Cache Bug (SOLVED)
**Was:** Game runs old code after changes  
**Now:** `make clean-run` always clears cache  
**Prevention:** Makefile automates cache clearing

### Method Name Bug (create_monster vs create_unique_item)
**Was:** Caught late in manual testing  
**Now:** Integration tests check actual entity creation  
**Prevention:** Tests verify correct factory methods called

### State Transition Bug
**Was:** State not transitioning correctly  
**Now:** Tests verify state after each step  
**Prevention:** Explicit state assertions in tests

---

## TL;DR - Stop Going in Circles

1. **Always use:** `make clean-run` (not `python3 engine.py`)
2. **Before testing:** `python3 test_phase5_quick.py`
3. **Before committing:** Tests run automatically
4. **When stuck:** Check `debug.log` for service calls

**Time saved:** 5-10 minutes per test cycle  
**Bugs prevented:** All duplication bugs, most integration bugs  
**Frustration:** 📉📉📉

---

## Current Test (Right Now!)

```bash
# 1. Clear cache
make clean

# 2. Start game
python3 engine.py

# 3. Look for this in console:
>>> PickupService: ...
>>> MovementService: ...

# If you see these, refactor is working!
# If you see old messages (>>> PATHFINDING:), cache issue persists
```

---

**The cycle is broken.** No more going in circles. 🎯

