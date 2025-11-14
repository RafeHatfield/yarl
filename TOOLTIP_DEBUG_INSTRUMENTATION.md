# Tooltip Debug Instrumentation Guide

## Overview

This document describes the comprehensive debug instrumentation added to the tooltip rendering pipeline to diagnose tooltip flicker issues frame-by-frame.

## Changes Made

### 1. New Debug Flags Module: `ui/debug_flags.py`

A new module with three toggleable debug switches:

```python
ENABLE_TOOLTIP_DEBUG = True        # Enable all tooltip debug logging
TOOLTIP_IGNORE_FOV = False         # Experiment: bypass FOV checks when gathering entities
TOOLTIP_DISABLE_EFFECTS = False    # Experiment: skip visual effects during rendering
```

**Location:** `ui/debug_flags.py`

### 2. Frame Counter Access: `io_layer/console_renderer.py`

**Status:** Already exists and working correctly.

- `ConsoleRenderer._frame_counter` increments each frame
- Global `_LAST_FRAME_COUNTER` is set at line 99
- `get_last_frame_counter()` returns the current frame ID
- All tooltip logging uses frame ID for per-frame correlation

**Optional Enhancement:**
- Line 167: Added guard to skip effect playback when `TOOLTIP_DISABLE_EFFECTS=True`

### 3. Viewport Tooltip Instrumentation: `render_functions.py`

**Location:** Lines 318-389 (render tooltips section in `render_all()`)

Added logging at these points:

1. **TOOLTIP_VIEWPORT_START** — When viewport coordinates are computed
   - Frame ID, mouse position, world position

2. **TOOLTIP_VIEWPORT_ENTITIES** — After entity gathering
   - Frame ID, entity count, entity names
   - Will show if entity list flaps (empty/non-empty on consecutive frames)

3. **TOOLTIP_DRAW_CALL** — Before rendering tooltip
   - Frame ID, tooltip type ("single" or "multi")
   - If this is missing on some frames, tooltip rendering was skipped

4. **FOV bypass logic** — Lines 362-363
   - Respects `TOOLTIP_IGNORE_FOV` flag: passes `None` as `fov_map` when enabled
   - Allows testing if FOV flapping causes tooltip instability

### 4. Entity Gathering Instrumentation: `ui/tooltip.py` - `get_all_entities_at_position()`

**Location:** Lines 100-196

Added detailed logging:

1. **TOOLTIP_FOV_CHECK** — FOV status at position
   - Frame ID, world position, FOV visibility
   - Three variants: TOOLTIP_IGNORE_FOV enabled, fov_map present, no fov_map
   - Shows if FOV status flaps

2. **TOOLTIP_ENTITY_CLASSIFIED** — Each entity encountered at position
   - Frame ID, position, entity name, category (corpse/living_monster/item_or_feature)
   - Shows if entity classification is unstable

3. **TOOLTIP_ENTITIES_FINAL** — Final entity list
   - Frame ID, position, count, entity names
   - Shows final stable or flapping entity list

### 5. Single-Entity Tooltip Instrumentation: `ui/tooltip.py` - `render_tooltip()`

**Location:** Lines 543-573

Added logging:

1. **TOOLTIP_SINGLE_CONTENT** — Tooltip text content
   - Frame ID, mouse position, entity name, tooltip lines
   - Shows if tooltip text content changes

2. **TOOLTIP_SINGLE_GEOM** — Final tooltip geometry after clamping
   - Frame ID, x, y, width, height
   - Shows if tooltip position/size flaps

### 6. Multi-Entity Tooltip Instrumentation: `ui/tooltip.py` - `render_multi_entity_tooltip()`

**Location:** Lines 640-750

Added logging:

1. **TOOLTIP_MULTI_ENTITY** — Initial entity list
   - Frame ID, mouse position, count, entity names

2. **TOOLTIP_MULTI_CONTENT** — Tooltip text content
   - Frame ID, tooltip lines array
   - Shows if content changes

3. **TOOLTIP_MULTI_GEOM** — Final tooltip geometry after clamping
   - Frame ID, x, y, width, height
   - Shows if geometry flaps

## How to Use

### Step 1: Enable Debug Logging

Modify `logger_config.py` to set DEBUG level:

```python
# In logger_config.py setup_logging():
app_logger.setLevel(logging.DEBUG)  # Change from logging.WARNING
```

Or temporarily in your test script:

```python
import logging
logging.getLogger('rlike').setLevel(logging.DEBUG)
```

### Step 2: Reproduce Flicker

1. **First orc death** (baseline — typically stable)
   - Kill an orc, hover corpse+loot tile
   - Check logs for frame trace

2. **Second orc death** (flicker appears)
   - Kill another orc
   - Hover corpse+loot tile while flicker is visible
   - Capture 50-100 frames of logs

3. **After exploring more** (worse flicker)
   - Explore 4-5 rooms
   - Hover any potion on ground
   - Capture logs

### Step 3: Analyze Logs

Look for these patterns:

#### Pattern A: Entity List Flaps
```
TOOLTIP_ENTITIES_FINAL: frame=100 pos=(x,y) count=2 names=['Orc Corpse', 'Longsword']
TOOLTIP_ENTITIES_FINAL: frame=101 pos=(x,y) count=0 names=[]  # <-- FLAP!
TOOLTIP_ENTITIES_FINAL: frame=102 pos=(x,y) count=2 names=['Orc Corpse', 'Longsword']
```
**Indicates:** FOV or coordinate mapping is unstable.

#### Pattern B: Tooltip Content Changes
```
TOOLTIP_SINGLE_CONTENT: frame=100 lines=['Orc Corpse']
TOOLTIP_SINGLE_CONTENT: frame=101 lines=['Longsword']  # <-- FLIP!
TOOLTIP_SINGLE_CONTENT: frame=102 lines=['Orc Corpse']
```
**Indicates:** Entity ordering is unstable or entity classification is flapping.

#### Pattern C: Tooltip Geometry Flaps
```
TOOLTIP_SINGLE_GEOM: frame=100 x=50 y=20 w=15 h=3
TOOLTIP_SINGLE_GEOM: frame=101 x=50 y=20 w=15 h=3
TOOLTIP_SINGLE_GEOM: frame=102 x=49 y=19 w=16 h=4  # <-- FLAP!
```
**Indicates:** Tooltip layout calculation is unstable.

#### Pattern D: DRAW_CALL Missing on Some Frames
```
TOOLTIP_DRAW_CALL: frame=100 kind=single
TOOLTIP_DRAW_CALL: frame=101 kind=single
# frame=102 missing TOOLTIP_DRAW_CALL  <-- TOOLTIP NOT DRAWN THIS FRAME!
TOOLTIP_DRAW_CALL: frame=103 kind=single
```
**Indicates:** Tooltip is being rendered on some frames but omitted on others.

### Step 4: Isolate Root Cause

#### To test if FOV is the problem:

```python
# In ui/debug_flags.py
TOOLTIP_IGNORE_FOV = True  # Ignore FOV visibility
```

If flicker **disappears** with FOV disabled, the issue is FOV instability.
If flicker **persists**, move to next test.

#### To test if effects are interfering:

```python
# In ui/debug_flags.py
TOOLTIP_DISABLE_EFFECTS = True  # Skip visual effects
```

If flicker **disappears** with effects disabled, effects are interfering with tooltip stability.
If flicker **persists**, move to next test.

#### To see all events:

```python
# In ui/debug_flags.py
ENABLE_TOOLTIP_DEBUG = True  # Full logging
```

## Log Output Location

Logs are written to:
- `logs/rlike.log` — Complete debug trace (rotated at 10 MB)
- `logs/rlike_errors.log` — Error-level only (rotated at 5 MB)

### Log Format

All tooltip logs follow this format:
```
TOOLTIP_XXX: frame=NNN [additional fields...]
```

Examples:
```
TOOLTIP_VIEWPORT_START: frame=100 mouse=(50,20) world=(30,15)
TOOLTIP_FOV_CHECK: frame=100 pos=(30,15) in_fov=True fov_map_present=True
TOOLTIP_ENTITY_CLASSIFIED: frame=100 pos=(30,15) name=Orc Corpse category=corpse
TOOLTIP_ENTITIES_FINAL: frame=100 pos=(30,15) count=1 names=['Orc Corpse']
TOOLTIP_SINGLE_CONTENT: frame=100 mouse=(50,20) entity=Orc Corpse lines=['Orc Corpse']
TOOLTIP_SINGLE_GEOM: frame=100 x=52 y=21 w=15 h=3
```

## Interpreting Results

### Expected Behavior (No Flicker)

For a stable tooltip on a single tile:
- TOOLTIP_VIEWPORT_COORDS: same world position each frame (mouse stationary)
- TOOLTIP_ENTITIES_FINAL: same entity names and order each frame
- TOOLTIP_SINGLE_CONTENT or TOOLTIP_MULTI_CONTENT: identical lines each frame
- TOOLTIP_*_GEOM: same x/y/w/h each frame
- TOOLTIP_DRAW_CALL: appears every frame (tooltip is rendered)

### Flicker Pattern A: Coordinate Mapping Unstable
```
Symptoms: Entity count alternates (2 → 0 → 2 → 0)
Cause: FOV or coordinate mapping returning different results each frame
Fix: Check fov_functions.map_is_in_fov() or screen_to_world() coordinate translation
```

### Flicker Pattern B: Entity Ordering Unstable
```
Symptoms: Entity order or classification flaps
Cause: Non-deterministic entity iteration or classification logic
Fix: Ensure entity sorting is stable (check _sort_key in get_all_entities_at_position)
```

### Flicker Pattern C: Tooltip Geometry Unstable
```
Symptoms: x/y/w/h change while mouse/entities are stable
Cause: Tooltip sizing logic or screen boundary clamping is non-deterministic
Fix: Check tooltip width/height calculation or boundary adjustment logic
```

### Flicker Pattern D: Tooltip Omitted on Some Frames
```
Symptoms: TOOLTIP_DRAW_CALL missing on alternating frames
Cause: Condition for entering tooltip rendering section is flapping
Fix: Check ui_layout.is_in_viewport() or entities_at_position evaluation
```

## Disabling Instrumentation

To disable debug logging (reset to production):

```python
# In ui/debug_flags.py
ENABLE_TOOLTIP_DEBUG = False       # Disable logging
TOOLTIP_IGNORE_FOV = False         # Restore normal FOV behavior
TOOLTIP_DISABLE_EFFECTS = False    # Restore normal effects
```

The logging overhead is minimal when `ENABLE_TOOLTIP_DEBUG=False` due to the guard:
```python
if ENABLE_TOOLTIP_DEBUG and logger.isEnabledFor(logging.DEBUG):
    logger.debug(...)
```

## Next Steps (After Diagnosis)

Once you've identified the flicker pattern:

1. **FOV flapping** → Check FOV computation and entity visibility
2. **Entity ordering flaps** → Review entity classification and sorting
3. **Geometry flapping** → Review tooltip sizing and boundary logic
4. **Missing draws** → Check conditional logic for tooltip rendering

Document findings in a separate issue/ticket with:
- Flicker pattern observed
- Log excerpt (10-20 frames showing the flap)
- Reproduction steps
- Which debug flags helped isolate the issue


