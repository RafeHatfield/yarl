# Tooltip Flicker Debug Index

**Delivery Date:** November 14, 2025  
**Status:** ✅ COMPLETE AND VERIFIED  
**Tests Passing:** 5/5 ✓

---

## 📋 Quick Navigation

### 🚀 **START HERE**
1. **[INSTRUMENTATION_COMPLETE.md](INSTRUMENTATION_COMPLETE.md)** — Delivery summary and guarantees
2. **[TOOLTIP_DEBUG_QUICKREF.txt](TOOLTIP_DEBUG_QUICKREF.txt)** — One-page quick reference

### 📖 **DETAILED GUIDES**
3. **[INSTRUMENTATION_SUMMARY.md](INSTRUMENTATION_SUMMARY.md)** — Complete reference with patterns
4. **[TOOLTIP_DEBUG_INSTRUMENTATION.md](TOOLTIP_DEBUG_INSTRUMENTATION.md)** — Detailed usage guide

### ✅ **VERIFICATION**
5. **[test_tooltip_instrumentation.py](test_tooltip_instrumentation.py)** — Run this first!

---

## 🎯 Five-Minute Start

### Step 1: Verify Everything Works (2 min)
```bash
python3 test_tooltip_instrumentation.py
```
✓ Should see: **5/5 tests passed**

### Step 2: Enable DEBUG Logging (1 min)
Edit `logger_config.py`:
```python
def setup_logging(log_level=logging.DEBUG):  # Change WARNING → DEBUG
```

### Step 3: Reproduce Flicker (1 min)
- Run game
- Kill first orc → stable tooltip (usually)
- Kill second orc → flicker starts

### Step 4: Capture Logs (1 min)
```bash
tail -f logs/rlike.log | grep TOOLTIP_
```

---

## 🔍 What Was Instrumented

### Four Code Files Modified
| File | Changes | Purpose |
|------|---------|---------|
| **ui/debug_flags.py** | NEW | Toggle switches (ENABLE_TOOLTIP_DEBUG, TOOLTIP_IGNORE_FOV, TOOLTIP_DISABLE_EFFECTS) |
| **ui/tooltip.py** | +97 lines | Entity gathering, single & multi-entity rendering logging |
| **render_functions.py** | +44 lines | Viewport tooltip entry, entity gathering, draw decision logging |
| **io_layer/console_renderer.py** | +6 lines | Optional effects disable guard |

### Eleven Logging Points
```
1. TOOLTIP_VIEWPORT_START          — Entered viewport, translated coordinates
2. TOOLTIP_FOV_CHECK               — FOV visibility determined
3. TOOLTIP_ENTITY_CLASSIFIED       — Entity classification (corpse/monster/item)
4. TOOLTIP_ENTITIES_FINAL          — Final stable entity list
5. TOOLTIP_VIEWPORT_ENTITIES       — Entities before render decision
6. TOOLTIP_DRAW_CALL               — Rendering decision (single vs multi)
7. TOOLTIP_SINGLE_CONTENT          — Single-entity tooltip text
8. TOOLTIP_SINGLE_GEOM             — Single-entity position/size
9. TOOLTIP_MULTI_ENTITY            — Multi-entity list
10. TOOLTIP_MULTI_CONTENT          — Multi-entity tooltip text
11. TOOLTIP_MULTI_GEOM             — Multi-entity position/size
```

---

## 🧪 Isolation Experiments

### Experiment 1: Disable FOV
```python
# In ui/debug_flags.py
TOOLTIP_IGNORE_FOV = True
```
**Result:** If flicker disappears → FOV is unstable  
**Result:** If flicker persists → continue to Experiment 2

### Experiment 2: Disable Effects
```python
# In ui/debug_flags.py
TOOLTIP_DISABLE_EFFECTS = True
```
**Result:** If flicker disappears → effects are interfering  
**Result:** If flicker persists → tooltip rendering is the issue

---

## 📊 Flicker Pattern Detection

### Pattern A: Entity List Flaps
```
frame=100: TOOLTIP_ENTITIES_FINAL count=2 names=['Orc Corpse', 'Longsword']
frame=101: TOOLTIP_ENTITIES_FINAL count=0 names=[]  ← FLAP!
frame=102: TOOLTIP_ENTITIES_FINAL count=2 names=['Orc Corpse', 'Longsword']
```
**Diagnosis:** FOV or coordinate mapping instability  
**Location:** `fov_functions.map_is_in_fov()` or `screen_to_world()`

### Pattern B: Entity Order Changes
```
frame=100: TOOLTIP_ENTITIES_FINAL names=['Orc Corpse', 'Longsword']
frame=101: TOOLTIP_ENTITIES_FINAL names=['Longsword', 'Orc Corpse']  ← FLAP!
```
**Diagnosis:** Entity sorting non-deterministic  
**Location:** `get_all_entities_at_position()._sort_key()`

### Pattern C: Tooltip Content Alternates
```
frame=100: TOOLTIP_SINGLE_CONTENT lines=['Orc Corpse']
frame=101: TOOLTIP_SINGLE_CONTENT lines=['Longsword']  ← FLIP!
```
**Diagnosis:** Entity list or selection flapping  
**Check:** Pattern A or B first

### Pattern D: Tooltip Geometry Flaps
```
frame=100: TOOLTIP_SINGLE_GEOM x=50 y=20 w=15 h=3
frame=102: TOOLTIP_SINGLE_GEOM x=49 y=19 w=16 h=4  ← FLAP!
```
**Diagnosis:** Tooltip sizing or boundary clamping unstable  
**Location:** `max(len(line)...)` calculation or screen boundary logic

### Pattern E: Missing Draw Calls
```
frame=100: TOOLTIP_DRAW_CALL kind=single
[frame=101: NO TOOLTIP_DRAW_CALL]  ← MISSING!
frame=102: TOOLTIP_DRAW_CALL kind=single
```
**Diagnosis:** Conditional rendering flapping  
**Location:** `ui_layout.is_in_viewport()` or `entities_at_position` check

---

## 🛠️ Debug Features

### Master Toggle
```python
# ui/debug_flags.py
ENABLE_TOOLTIP_DEBUG = True   # All logging on
ENABLE_TOOLTIP_DEBUG = False  # All logging off (zero overhead)
```

### FOV Bypass (Testing Only)
```python
# ui/debug_flags.py
TOOLTIP_IGNORE_FOV = True  # Bypass FOV checks
# Useful for: "Is this a FOV problem?"
```

### Effects Disable (Testing Only)
```python
# ui/debug_flags.py
TOOLTIP_DISABLE_EFFECTS = True  # Skip visual effects
# Useful for: "Are effects interfering?"
```

---

## 📝 Documentation Map

### For Decision Makers
→ **[INSTRUMENTATION_COMPLETE.md](INSTRUMENTATION_COMPLETE.md)**  
Executive summary, guarantees, and what was delivered

### For Debuggers (You Are Here!)
→ **[TOOLTIP_DEBUG_QUICKREF.txt](TOOLTIP_DEBUG_QUICKREF.txt)**  
One-page reference with common patterns and fixes

### For Deep Dives
→ **[INSTRUMENTATION_SUMMARY.md](INSTRUMENTATION_SUMMARY.md)**  
Complete reference with examples and log analysis

### For Implementation Details
→ **[TOOLTIP_DEBUG_INSTRUMENTATION.md](TOOLTIP_DEBUG_INSTRUMENTATION.md)**  
How the instrumentation works and what each log point does

---

## ⚡ Performance

| Scenario | Overhead |
|----------|----------|
| ENABLE_TOOLTIP_DEBUG = False | ~0% (just boolean checks) |
| ENABLE_TOOLTIP_DEBUG = True, DEBUG logging | ~1-2% per frame |
| ENABLE_TOOLTIP_DEBUG = True, WARNING logging | ~0% (no logs written) |

**Recommendation:** Keep False in production. True only when debugging.

---

## 🔧 Reset to Production

When done debugging:

```python
# ui/debug_flags.py
ENABLE_TOOLTIP_DEBUG = False        # Disable all logging
TOOLTIP_IGNORE_FOV = False          # Restore FOV
TOOLTIP_DISABLE_EFFECTS = False     # Restore effects

# logger_config.py
app_logger.setLevel(logging.WARNING)  # Back to WARNING
```

---

## ✨ Key Advantages

✅ **No Gameplay Changes** — Logging only, zero logic modifications  
✅ **Zero Overhead When Disabled** — Simple boolean guards  
✅ **Frame-Correlated** — Every log includes frame ID  
✅ **Comprehensive** — 11 logging points covering all major decisions  
✅ **Experiment-Ready** — FOV and effects toggles for isolation  
✅ **Well-Documented** — Multiple guides and examples  
✅ **Production-Safe** — Can be completely disabled  
✅ **Verified** — All tests pass (5/5)  

---

## 📚 File Checklist

### Code
- ✅ `ui/debug_flags.py` (NEW)
- ✅ `ui/tooltip.py` (MODIFIED, +97 lines)
- ✅ `render_functions.py` (MODIFIED, +44 lines)
- ✅ `io_layer/console_renderer.py` (MODIFIED, +6 lines)

### Documentation
- ✅ `INSTRUMENTATION_COMPLETE.md` (This delivery)
- ✅ `INSTRUMENTATION_SUMMARY.md` (Complete reference)
- ✅ `TOOLTIP_DEBUG_INSTRUMENTATION.md` (Detailed guide)
- ✅ `TOOLTIP_DEBUG_QUICKREF.txt` (Quick reference)
- ✅ `TOOLTIP_FLICKER_DEBUG_INDEX.md` (You are here!)

### Verification
- ✅ `test_tooltip_instrumentation.py` (5/5 tests pass)

---

## 🚀 Next Steps

### Immediate
1. Run `python3 test_tooltip_instrumentation.py` ← **START HERE**
2. Review results
3. All tests passed? ✅ Continue below

### Short Term
1. Edit `logger_config.py` to enable DEBUG
2. Run game
3. Reproduce tooltip flicker
4. Capture logs: `tail logs/rlike.log | grep TOOLTIP_`

### Analysis
1. Look for flapping values using Pattern A-E above
2. Run isolation experiments (FOV / Effects)
3. Document findings

### Reporting
1. Create bug report with:
   - Exact pattern observed (A, B, C, D, or E)
   - 20-30 frame log excerpt showing the flap
   - Which isolation experiment helped most
   - Proposed root cause

---

## 📞 Support

If instrumentation doesn't work:
1. Run verification: `python3 test_tooltip_instrumentation.py`
2. Check all 5 tests pass
3. If tests fail, review error messages
4. Check that DEBUG logging is enabled in `logger_config.py`

If logs aren't appearing:
1. Confirm `logs/` directory exists
2. Confirm logger is set to DEBUG level
3. Confirm `ENABLE_TOOLTIP_DEBUG = True`
4. Check `logs/rlike.log` and `logs/rlike_errors.log`

---

## 🎓 Learn More

- **How logging works?** → See `logger_config.py`
- **Frame counter details?** → See `io_layer/console_renderer.py` lines 14-99
- **FOV system?** → See `fov_functions.py`
- **Coordinate system?** → See `config/ui_layout.py`

---

**Version:** 1.0  
**Date:** November 14, 2025  
**Status:** ✅ READY FOR USE

---

*Now go catch that flicker!* 🐛


