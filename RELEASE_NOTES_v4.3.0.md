# Release Notes - v4.3.0

**Release Date:** 2025-11-17  
**Type:** Minor Release  
**Focus:** Bot Soak Harness Stability Fixes

---

## Overview

This release fixes two critical bugs in the bot soak harness (Phase 1.6) that prevented multi-run stability testing from completing successfully. These fixes enable reliable automated testing of game stability across multiple sequential bot runs.

---

## 🐛 Bug Fixes

### Critical: Cross-Run State Leakage Bug

**Issue:** Bot runs 2+ would hang with repeated failed movement attempts after run 1 completed successfully.

**Root Cause:** Singleton services (`MovementService`, `PickupService`, `FloorStateManager`) were not being reset between runs, causing run 2+ to use stale references from run 1's `state_manager`.

**Fix:**
- Added singleton service resets before each bot soak run
- Created `reset_pickup_service()` function (was missing)
- Added comprehensive documentation of singleton reset requirements
- Added test coverage for singleton reset behavior

**Impact:** All 10 bot soak runs now complete successfully (previously only run 1 would work)

**Files Changed:**
- `engine/soak_harness.py` - Added singleton service resets
- `services/pickup_service.py` - Added reset function
- `tests/test_bot_soak.py` - Added test coverage

**See:** `BOT_SOAK_CROSS_RUN_STATE_FIX.md`

---

### Critical: Stairs Hang Bug

**Issue:** Bot would occasionally hang at the end of run 2+ when encountering stairs during exploration.

**Root Cause:** Auto-explore would stop when stepping on stairs (to prevent accidental descent), but would immediately stop again when restarted because the bot was still on the same stairs, creating an infinite loop.

**Fix:**
- Added `known_stairs` tracking to `AutoExplore` component
- Modified `_on_stairs()` to only stop for NEW stairs (not previously discovered)
- Follows same pattern as `known_monsters` and `known_items`

**Impact:** Bot can now safely discover stairs and continue exploring without hanging

**Files Changed:**
- `components/auto_explore.py` - Added stairs tracking and smart stop logic

**See:** `BOT_SOAK_STAIRS_HANG_FIX.md`

---

## ✅ Verification

### Test Results

**Unit Tests:**
```bash
$ python3 -m pytest tests/test_bot_soak.py -v
9 passed, 1 warning in 0.06s
```

**Bot Soak (3 runs):**
```
Runs: 3
Completed: 3
Crashes: 0
```

**Bot Soak (10 runs):**
```
Runs: 10
Completed: 10
Crashes: 0
```

### Verified Behaviors

✅ Run 1 completes successfully (always worked)  
✅ Run 2+ complete successfully (was broken, now fixed)  
✅ No crashes or hangs across 10 sequential runs  
✅ Normal gameplay mode (`python3 engine.py`) unchanged  
✅ Bot mode (`python3 engine.py --bot`) unchanged  
✅ Bot soak mode (`python3 engine.py --bot-soak --runs N`) fully functional  

---

## 📊 Technical Details

### Singleton Services Reset

The following singleton services are now properly reset before each bot soak run:

| Service | Reset Function | Purpose |
|---------|---------------|---------|
| RunMetricsRecorder | `reset_run_metrics_recorder()` | Per-run statistics |
| TelemetryService | `reset_telemetry_service()` | Per-run telemetry data |
| MovementService | `reset_movement_service()` | Movement validation (primary fix) |
| PickupService | `reset_pickup_service()` | Item pickup logic |
| FloorStateManager | `reset_floor_state_manager()` | Cross-floor state |
| BotInputSource | `reset_bot_run_state()` | Bot exploration tracking |

### AutoExplore Smart Stops

Auto-explore now tracks discovered entities and only stops for NEW discoveries:

| Entity Type | Tracking | Behavior |
|-------------|----------|----------|
| Monsters | `known_monsters: Set[int]` | Only stop for new monsters |
| Items | `known_items: Set[int]` | Only stop for new items |
| Stairs | `known_stairs: Set[Tuple[int,int]]` | Only stop for new stairs ✅ NEW |
| Chests | `known_items: Set[int]` | Only stop for new chests |
| Signposts | `known_items: Set[int]` | Only stop for new signposts |

---

## 🔧 Breaking Changes

None. This is a pure bug fix release with no API or behavior changes for normal gameplay.

---

## 📝 Documentation Added

- `BOT_SOAK_CROSS_RUN_STATE_FIX.md` - Detailed analysis of singleton state leakage bug
- `BOT_SOAK_STAIRS_HANG_FIX.md` - Detailed analysis of stairs hang bug
- Updated `engine/soak_harness.py` docstring with singleton reset requirements

---

## 🎯 Use Cases Enabled

This release enables:

1. **Reliable stability testing** - Run 10+ bot games back-to-back for crash detection
2. **Performance profiling** - Collect metrics across multiple runs without manual intervention
3. **Telemetry validation** - Verify telemetry collection works across sequential games
4. **Regression testing** - Automated multi-run tests for CI/CD pipelines

---

## 🔮 Future Considerations

### Recommended Follow-ups:

1. **Audit remaining singletons** - Check if other singleton services need reset functions
2. **Consider dependency injection** - For services like MovementService, passing state_manager explicitly could prevent stale reference bugs entirely
3. **Add full integration test** - Create end-to-end bot soak test that verifies multiple runs complete (currently mocked in unit tests)

---

## 🙏 Acknowledgments

Special thanks to the thorough testing process that uncovered these subtle cross-run state issues. Both bugs only manifested in multi-run scenarios, highlighting the importance of comprehensive integration testing.

---

## 📦 Upgrade Instructions

No special upgrade steps required. Simply pull the latest code:

```bash
git checkout main
git pull origin main
```

Or use the release tag:

```bash
git checkout v4.3.0
```

---

## 🧪 Testing This Release

To verify the fixes work in your environment:

```bash
# Quick test (3 runs)
python3 engine.py --bot-soak --runs 3

# Full soak test (10 runs)
python3 engine.py --bot-soak --runs 10

# Expected output:
# Runs: 10
# Completed: 10
# Crashes: 0
```

If all runs complete successfully with 0 crashes, the fixes are working correctly.

---

## Previous Release

See v4.2.2 release notes for previous changes.

