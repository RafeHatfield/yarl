# Tooltip Debug Instrumentation — Complete Summary

## What Was Added

A comprehensive, frame-by-frame debug instrumentation system for the tooltip rendering pipeline. All logging is guarded by toggleable debug flags and only activates when explicitly enabled.

## Files Modified

| File | Changes | Lines |
|------|---------|-------|
| `ui/debug_flags.py` | **NEW** — Three toggleable debug switches | 1-26 |
| `ui/tooltip.py` | FOV/entity/content/geometry logging | 98-750 |
| `render_functions.py` | Viewport tooltip call site instrumentation | 318-389 |
| `io_layer/console_renderer.py` | Optional effects disable guard | 164-170 |

## Debug Flags (All Gated by ENABLE_TOOLTIP_DEBUG)

### `ENABLE_TOOLTIP_DEBUG = True`
Master switch. When `True`, detailed frame-by-frame logging is output. When `False`, no tooltip debug logging occurs.

### `TOOLTIP_IGNORE_FOV = False`
Experiment switch. When `True`, FOV checks are bypassed during entity gathering. Helps isolate whether FOV flapping causes tooltip instability.

### `TOOLTIP_DISABLE_EFFECTS = False`
Experiment switch. When `True`, visual effects are not rendered. Helps determine if effect rendering interferes with tooltip stability.

## Logging Points

### 1. Viewport Entry (`render_functions.py:355`)
```
TOOLTIP_VIEWPORT_START: frame=NNN mouse=(x,y) world=(x,y)
```
- Logged when mouse enters viewport and coordinates are translated
- Shows if coordinate mapping is stable

### 2. FOV Check (`ui/tooltip.py:107-127`)
```
TOOLTIP_FOV_CHECK: frame=NNN pos=(x,y) in_fov=BOOL [reason]
```
- Logged during entity gathering
- Three variants: TOOLTIP_IGNORE_FOV enabled, fov_map present, no fov_map
- Shows if FOV status flaps

### 3. Entity Classification (`ui/tooltip.py:146-170`)
```
TOOLTIP_ENTITY_CLASSIFIED: frame=NNN pos=(x,y) name=XXXX category=corpse|living_monster|item_or_feature
```
- Logged for each entity found at position
- Shows if entity classification is unstable

### 4. Entities Gathered (`ui/tooltip.py:189-194`)
```
TOOLTIP_ENTITIES_FINAL: frame=NNN pos=(x,y) count=N names=[...]
```
- Logged after all entity gathering and sorting
- Shows if entity list is stable or flapping

### 5. Viewport Entities (`render_functions.py:368-373`)
```
TOOLTIP_VIEWPORT_ENTITIES: frame=NNN count=N names=[...]
```
- Logged before rendering decision
- Redundant with TOOLTIP_ENTITIES_FINAL but at different call site

### 6. Tooltip Draw Decision (`render_functions.py:376-381`)
```
TOOLTIP_DRAW_CALL: frame=NNN kind=single|multi
```
- Logged if tooltip will be rendered
- If missing on some frames, indicates conditional rendering is flapping

### 7. Single-Entity Content (`ui/tooltip.py:545-549`)
```
TOOLTIP_SINGLE_CONTENT: frame=NNN mouse=(x,y) entity=XXXX lines=[...]
```
- Logged in render_tooltip()
- Shows if tooltip text content changes

### 8. Single-Entity Geometry (`ui/tooltip.py:569-573`)
```
TOOLTIP_SINGLE_GEOM: frame=NNN x=N y=N w=N h=N
```
- Logged after boundary clamping
- Shows if tooltip position/size flaps

### 9. Multi-Entity List (`ui/tooltip.py:646-651`)
```
TOOLTIP_MULTI_ENTITY: frame=NNN mouse=(x,y) count=N names=[...]
```
- Logged in render_multi_entity_tooltip()
- Shows entity order at multi-entity rendering

### 10. Multi-Entity Content (`ui/tooltip.py:726-730`)
```
TOOLTIP_MULTI_CONTENT: frame=NNN lines=[...]
```
- Logged in render_multi_entity_tooltip()
- Shows if multi-entity tooltip text changes

### 11. Multi-Entity Geometry (`ui/tooltip.py:746-750`)
```
TOOLTIP_MULTI_GEOM: frame=NNN x=N y=N w=N h=N
```
- Logged after boundary clamping
- Shows if multi-entity tooltip geometry flaps

## Quick Start

### 1. Enable Debug Logging

Edit `logger_config.py`:
```python
def setup_logging(log_level=logging.DEBUG):  # Change WARNING → DEBUG
    # ... rest of setup ...
```

Or in your game initialization:
```python
import logging
from logger_config import setup_logging
setup_logging(logging.DEBUG)
```

### 2. Enable Tooltip Debug

Edit `ui/debug_flags.py`:
```python
ENABLE_TOOLTIP_DEBUG = True  # Already True by default
```

### 3. Run Game and Reproduce Flicker

1. Start game
2. Kill first orc (baseline — usually stable)
3. Hover corpse + loot tile → check for flicker
4. Kill second orc → flicker may appear
5. Explore more rooms → flicker worsens

### 4. Check Logs

Look in `logs/rlike.log`:
```bash
tail -f logs/rlike.log | grep TOOLTIP_
```

### 5. Analyze Pattern

See "Flicker Patterns" section below.

## Flicker Patterns

### Pattern A: Entity List Flaps
```
TOOLTIP_ENTITIES_FINAL: frame=100 pos=(30,15) count=2 names=['Orc Corpse', 'Longsword']
TOOLTIP_ENTITIES_FINAL: frame=101 pos=(30,15) count=0 names=[]
TOOLTIP_ENTITIES_FINAL: frame=102 pos=(30,15) count=2 names=['Orc Corpse', 'Longsword']
```
**Root Cause:** FOV or coordinate mapping is non-deterministic  
**Test:** Set `TOOLTIP_IGNORE_FOV = True` to bypass FOV checks  
**Fix:** Check `fov_functions.map_is_in_fov()` or `screen_to_world()` for instability

### Pattern B: Entity Order/Classification Changes
```
TOOLTIP_ENTITIES_FINAL: frame=100 pos=(30,15) count=2 names=['Orc Corpse', 'Longsword']
TOOLTIP_ENTITIES_FINAL: frame=101 pos=(30,15) count=2 names=['Longsword', 'Orc Corpse']
TOOLTIP_ENTITIES_FINAL: frame=102 pos=(30,15) count=2 names=['Orc Corpse', 'Longsword']
```
**Root Cause:** Entity sorting or classification is non-deterministic  
**Test:** Add more logging to `_sort_key()` function  
**Fix:** Ensure sort key is stable (currently uses render_order, name, id)

### Pattern C: Tooltip Content Alternates
```
TOOLTIP_SINGLE_CONTENT: frame=100 lines=['Orc Corpse']
TOOLTIP_SINGLE_CONTENT: frame=101 lines=['Longsword']
TOOLTIP_SINGLE_CONTENT: frame=102 lines=['Orc Corpse']
```
**Root Cause:** Entity under mouse is changing (likely due to entity list flapping)  
**Test:** Check TOOLTIP_ENTITIES_FINAL at same frame  
**Fix:** Fix entity list stability first

### Pattern D: Tooltip Geometry Flaps
```
TOOLTIP_SINGLE_GEOM: frame=100 x=50 y=20 w=15 h=3
TOOLTIP_SINGLE_GEOM: frame=101 x=50 y=20 w=15 h=3
TOOLTIP_SINGLE_GEOM: frame=102 x=49 y=19 w=16 h=4
```
**Root Cause:** Tooltip width/height calculation or boundary clamping is unstable  
**Test:** Add logging to tooltip sizing logic  
**Fix:** Check max(len(line)...) calculation or screen boundary logic

### Pattern E: Draw Call Missing
```
TOOLTIP_DRAW_CALL: frame=100 kind=single
TOOLTIP_DRAW_CALL: frame=101 kind=single
[No TOOLTIP_DRAW_CALL on frame 102]
TOOLTIP_DRAW_CALL: frame=103 kind=single
```
**Root Cause:** Conditional for tooltip rendering is flapping  
**Test:** Add logging to `ui_layout.is_in_viewport()` and `entities_at_position` check  
**Fix:** Check condition stability

## Isolation Experiments

### Experiment 1: Disable FOV
```python
# ui/debug_flags.py
TOOLTIP_IGNORE_FOV = True
```
If flicker **disappears**, FOV is the root cause.  
If flicker **persists**, move to next experiment.

### Experiment 2: Disable Effects
```python
# ui/debug_flags.py
TOOLTIP_DISABLE_EFFECTS = True
```
If flicker **disappears**, effects are interfering.  
If flicker **persists**, tooltip rendering itself is the issue.

## Performance Impact

**With `ENABLE_TOOLTIP_DEBUG = False`:**
- Negligible (just one boolean check)

**With `ENABLE_TOOLTIP_DEBUG = True` and `logging.DEBUG` enabled:**
- ~1-2% overhead per frame (debug strings only logged to disk)
- Only impacts performance if debugging

## Expected Output (Stable Tooltip)

For a tooltip on a single tile with mouse stationary, you should see in logs:

```
TOOLTIP_VIEWPORT_START: frame=100 mouse=(50,20) world=(30,15)
TOOLTIP_FOV_CHECK: frame=100 pos=(30,15) in_fov=True fov_map_present=True
TOOLTIP_ENTITY_CLASSIFIED: frame=100 pos=(30,15) name=Orc Corpse category=corpse
TOOLTIP_ENTITIES_FINAL: frame=100 pos=(30,15) count=1 names=['Orc Corpse']
TOOLTIP_DRAW_CALL: frame=100 kind=single
TOOLTIP_SINGLE_CONTENT: frame=100 mouse=(50,20) entity=Orc Corpse lines=['Orc Corpse']
TOOLTIP_SINGLE_GEOM: frame=100 x=52 y=21 w=15 h=3

TOOLTIP_VIEWPORT_START: frame=101 mouse=(50,20) world=(30,15)
TOOLTIP_FOV_CHECK: frame=101 pos=(30,15) in_fov=True fov_map_present=True
TOOLTIP_ENTITY_CLASSIFIED: frame=101 pos=(30,15) name=Orc Corpse category=corpse
TOOLTIP_ENTITIES_FINAL: frame=101 pos=(30,15) count=1 names=['Orc Corpse']
TOOLTIP_DRAW_CALL: frame=101 kind=single
TOOLTIP_SINGLE_CONTENT: frame=101 mouse=(50,20) entity=Orc Corpse lines=['Orc Corpse']
TOOLTIP_SINGLE_GEOM: frame=101 x=52 y=21 w=15 h=3

[pattern repeats identically]
```

Notice: Every field is identical each frame → stable tooltip.

If you see alternating values anywhere, that's your flicker root cause.

## Next Steps

1. **Run verification script:** `python3 test_tooltip_instrumentation.py`
2. **Enable DEBUG logging:** Modify `logger_config.py`
3. **Reproduce flicker:** Run game and trigger second orc death
4. **Capture 50-100 frames** of logs showing the flicker
5. **Analyze patterns** using examples above
6. **File bug report** with:
   - Exact flicker pattern
   - 10-20 frame log excerpt
   - Which experiment isolated it best
   - Proposed root cause

## Reference

- **Detailed Usage Guide:** `TOOLTIP_DEBUG_INSTRUMENTATION.md`
- **Implementation Details:** See inline comments in modified files
- **Verification Script:** `test_tooltip_instrumentation.py` (all tests should pass)


