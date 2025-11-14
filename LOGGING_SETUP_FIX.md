# Logging Setup Fix — Tooltip Debug Logs Now Appear

## Problem
Tooltip debug logs were not appearing in `logs/rlike.log` even though `ENABLE_TOOLTIP_DEBUG = True`.

## Root Cause
The game engine (`engine.py`) was using `logging.basicConfig()` with `WARNING` level instead of calling our centralized `setup_logging()` function with `DEBUG` level.

This meant:
- The centralized logging system was never initialized
- Only `WARNING` level and above were logged
- DEBUG-level tooltip logs were being silently filtered

## Solution
Modified `engine.py` to initialize the centralized logging system at startup:

```python
# Initialize centralized logging system (DEBUG level for tooltip debugging)
from logger_config import setup_logging
setup_logging(log_level=logging.DEBUG)  # Enable DEBUG for tooltip instrumentation
```

This now runs at game startup and ensures:
- DEBUG level logging is enabled globally
- All tooltip logs go to `logs/rlike.log`
- Centralized logger is used throughout the game

## What Changed
**File:** `engine.py` (lines 36-50)

**Before:**
```python
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
```

**After:**
```python
from logger_config import setup_logging
setup_logging(log_level=logging.DEBUG)
```

## How to Verify It's Working

### Step 1: Run the Verification Script
```bash
python3 test_tooltip_instrumentation.py
```
Should show: ✅ 5/5 tests pass

### Step 2: Run the Game
```bash
python engine.py --testing
```
You should see output like:
```
📝 Centralized logging enabled: logs/rlike.log (DEBUG level for tooltip debugging)
```

### Step 3: Reproduce Tooltip Flicker
1. Kill first orc (baseline)
2. Kill second orc (flicker appears)
3. Hover corpse + loot tile

### Step 4: Check Logs Appear
```bash
tail -f logs/rlike.log | grep TOOLTIP_
```

You should now see logs like:
```
2025-11-14 12:34:56 - render_functions - DEBUG - TOOLTIP_VIEWPORT_START: frame=100 mouse=(50,20) world=(30,15)
2025-11-14 12:34:56 - ui.tooltip - DEBUG - TOOLTIP_FOV_CHECK: frame=100 pos=(30,15) in_fov=True fov_map_present=True
2025-11-14 12:34:56 - ui.tooltip - DEBUG - TOOLTIP_ENTITIES_FINAL: frame=100 pos=(30,15) count=1 names=['Orc Corpse']
2025-11-14 12:34:56 - render_functions - DEBUG - TOOLTIP_DRAW_CALL: frame=100 kind=single
2025-11-14 12:34:56 - ui.tooltip - DEBUG - TOOLTIP_SINGLE_CONTENT: frame=100 mouse=(50,20) entity=Orc Corpse lines=['Orc Corpse']
2025-11-14 12:34:56 - ui.tooltip - DEBUG - TOOLTIP_SINGLE_GEOM: frame=100 x=52 y=21 w=15 h=3
```

If you see these logs, **the instrumentation is working correctly!** 🎉

## Debugging If Logs Still Don't Appear

### Check 1: Verify Centralized Logger Was Initialized
```bash
grep "Centralized logging enabled" logs/rlike.log
```
Should show at the very top of the file.

### Check 2: Verify DEBUG Flags Are Enabled
Check `ui/debug_flags.py`:
```python
ENABLE_TOOLTIP_DEBUG = True  # Should be True
```

### Check 3: Check logs/ Directory Exists
```bash
ls -la logs/
```
Should show:
```
rlike.log          # Main log file
rlike_errors.log   # Error log file
```

### Check 4: Clear Old Logs and Try Again
```bash
rm logs/rlike.log logs/rlike_errors.log
python engine.py --testing
# Reproduce flicker...
tail logs/rlike.log | grep TOOLTIP_
```

### Check 5: Verify No Exceptions
Check if there are any errors preventing logging:
```bash
tail logs/rlike_errors.log
```

## Now You Can Debug!

With logging properly initialized, follow these steps:

1. **Reproduce flicker** while game is running
2. **Capture 20-30 frames** of logs:
   ```bash
   tail -n 500 logs/rlike.log | grep TOOLTIP_ > /tmp/flicker_logs.txt
   ```
3. **Analyze using pattern guide** in `TOOLTIP_DEBUG_QUICKREF.txt`
4. **Run isolation experiments**:
   - Try `TOOLTIP_IGNORE_FOV = True` (does flicker stop?)
   - Try `TOOLTIP_DISABLE_EFFECTS = True` (does flicker stop?)
5. **Document findings** with log excerpt

## Technical Details

The fix ensures:
- `setup_logging(log_level=logging.DEBUG)` is called at engine startup
- The centralized logger (`logger_config.py`) is used instead of basic config
- All modules that import `logging.getLogger(__name__)` will use the configured logger
- DEBUG level logs are written to `logs/rlike.log` with rotation (10 MB max)
- Errors are also written to `logs/rlike_errors.log`

## Summary

✅ **What Fixed It:**
- Modified `engine.py` to call `setup_logging(log_level=logging.DEBUG)` at startup

✅ **Result:**
- Tooltip debug logs now appear in `logs/rlike.log`
- You can see exactly when and how tooltip flicker occurs
- Frame-by-frame tracing is now possible

✅ **Next Steps:**
- Run game with `python engine.py --testing`
- Reproduce flicker
- Capture and analyze logs
- Identify root cause using pattern guide

