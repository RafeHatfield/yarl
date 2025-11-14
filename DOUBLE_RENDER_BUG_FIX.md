# Double-Rendering Bug Fix - Complete Analysis

## 🐛 The Bug

**Symptoms:**
- Single entities (e.g., orcs) appeared twice on screen as duplicate glyphs
- Two identical green 'o' characters visible right next to each other
- When the entity died, the "double" visual disappeared
- Only affected moving entities

**Root Cause:**
The viewport console was only being cleared when `fov_recompute=True`, which happens infrequently (typically only on major state changes like floor transitions). On regular frames, old entity glyphs persisted on the console buffer while new entity positions were being drawn, creating visual duplicates.

## 🔍 Investigation Process

### Architecture Overview
The rendering pipeline consists of:
1. **Main loop** (engine_integration.py): Calls `renderer.render()` each frame
2. **ConsoleRenderer** (io_layer/console_renderer.py): Wraps `render_all()` function
3. **render_all()** (render_functions.py): Renders map tiles, then entities
4. **draw_entity()**: Draws individual entity glyphs to console
5. **RenderSystem** (engine/systems/render_system.py): Has `skip_drawing=True` when ConsoleRenderer is active

### Key Finding
In `io_layer/console_renderer.py:103-114`, the console clearing logic was:

```python
# OLD CODE (BUGGY)
if fov_recompute:
    try:
        libtcod.console_clear(self.viewport_console)
        # ... clear other consoles ...
    except (TypeError, AttributeError):
        pass
```

This meant the viewport console accumulated stale data unless `fov_recompute` was True.

## ✅ The Fix

**Location:** `io_layer/console_renderer.py` lines 103-116

**Change:** Remove the `if fov_recompute:` condition and ALWAYS clear the viewport console at the start of each frame.

```python
# NEW CODE (FIXED)
# CRITICAL: Clear working consoles EVERY FRAME, not just on FOV recompute!
# Entities may move between frames, and old glyphs must be cleared from the 
# console before new ones are drawn. Failing to do this causes "double entity" 
# visual artifacts where old entity positions persist onscreen.
#
# This is the fix for the double-render bug where orcs appeared twice.
try:
    libtcod.console_clear(self.viewport_console)
    libtcod.console_clear(self.status_console)
    if self.sidebar_console:
        libtcod.console_clear(self.sidebar_console)
except (TypeError, AttributeError):
    # Mock consoles in tests will fail - that's OK, we just skip clearing
    pass
```

**Rationale:**
- Consoles are off-screen buffers that accumulate drawing commands
- Each frame must start with a clean slate to prevent visual artifacts
- The FOV recompute flag is independent of entity movement - an orc might move without triggering FOV recalculation
- This is a standard rendering practice: clear → draw → flush

## 📊 Testing Results

### Tests Passing
- ✅ All 14 IO abstraction tests (`tests/test_io_abstractions.py`)
- ✅ All 6 golden path tests (`tests/test_golden_path_floor1.py`)
- ✅ 2308+ total tests in the suite (no regressions)

### Rendering Pipeline Verification
- ✅ ConsoleRenderer instantiation works
- ✅ console_renderer.render() executes without errors
- ✅ Console clearing is called every frame
- ✅ Entities render exactly once per frame

## 🏗️ Architecture Notes

### Why This Approach is Correct
1. **Follows standard rendering practice:** Clear → Draw → Flush
2. **Respects the abstraction layer:** ConsoleRenderer is the canonical drawing authority
3. **RenderSystem `skip_drawing=True`:** Prevents double-rendering from systems
4. **No performance concern:** Clearing a console is fast (~O(n) where n = console area, typically 40x30)

### Related Code Ownership
- **ConsoleRenderer**: Owns all rendering to screen. Handles console setup, clearing, and flushing.
- **render_all()**: Coordinates rendering of tiles, entities, and UI
- **draw_entity()**: Draws individual entity glyphs (called by render_all for each entity)
- **RenderSystem**: Stays for FOV calculation; skips drawing when ConsoleRenderer is active

## 🔒 Guard Rails for the Future

To prevent similar bugs:
1. **Added documentation** in ConsoleRenderer explaining why clear must happen every frame
2. **Console clearing is now unconditional** - independent of other state flags
3. **Architecture is clear:** One rendering path (ConsoleRenderer) owns all drawing

## 📝 Files Changed

| File | Change | Lines |
|------|--------|-------|
| `io_layer/console_renderer.py` | Removed `if fov_recompute:` condition from console clearing | 103-116 |
| `render_functions.py` | Removed temporary debug logging | (cleanup) |

## ✨ Verification Checklist

- [x] Bug reproduced and understood
- [x] Root cause identified
- [x] Single-point fix implemented
- [x] No double-rendering on entity movement
- [x] All tests passing (no regressions)
- [x] Architecture remains clean
- [x] Documentation updated

---

**Status:** ✅ FIXED and VERIFIED  
**Date:** November 14, 2025  
**Confidence:** Very High (root cause identified, simple fix, comprehensive testing)



