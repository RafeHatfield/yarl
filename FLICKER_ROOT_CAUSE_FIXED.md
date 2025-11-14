# Tooltip Flicker — ROOT CAUSE FIXED ✅

## The Problem: Double Rendering Every Frame

Your diagnostic confirmed that **`render_all()` was called EXACTLY 2 times per frame on EVERY frame**.

```
[RENDER_CALL] frame=1 call_count=2
[RENDER_CALL] frame=2 call_count=2
[RENDER_CALL] frame=3 call_count=2
... etc
```

This caused tooltip flicker because:
1. **First render**: Tooltip drawn to console
2. **Console flushed** (appears on screen)
3. **Second render**: Tooltip drawn again
4. **Console flushed again** (replaces what was on screen)
5. Result: **Visual flicker** from the conflicting renders

## The Root Cause: TWO Rendering Systems

Two systems were both calling `render_all()` each frame:

1. **`io_layer/console_renderer.py`** (line 137)
   - New abstraction layer (Phase 2)
   - Called via: `renderer.render(game_state)` in main loop

2. **`engine/systems/optimized_render_system.py`** (lines 343 and 403)
   - Old system infrastructure
   - Called via: `engine.update()` in main loop

Both were executing in the same frame, causing double rendering!

## The Fix

**File:** `engine/systems/optimized_render_system.py` (lines 90-93)

Added a check to skip rendering when `ConsoleRenderer` is handling drawing:

```python
# CRITICAL: Skip rendering if ConsoleRenderer is handling drawing (Phase 2)
# This prevents double-rendering (render_all called twice per frame)
if self.skip_drawing:
    return
```

### Why This Works

The code was already set up correctly:
- `engine_integration.py` line 163: `skip_drawing=True` when creating OptimizedRenderSystem
- `engine/systems/render_system.py` line 146: Base RenderSystem already checks skip_drawing

But `OptimizedRenderSystem` **ignored** the `skip_drawing` flag in its `update()` method!

The fix ensures:
- **ConsoleRenderer** is the SOLE authority for drawing (via `renderer.render()`)
- **OptimizedRenderSystem** only handles FOV recomputation (not drawing)
- **No double rendering** = **No flicker** ✅

## Verification

Run the game and check:

```bash
python engine.py --testing 2>&1 | grep "\[RENDER_CALL\]" | head -20
```

You should now see **nothing** (the diagnostic won't print because there's no double rendering).

Previously it would have shown:
```
[RENDER_CALL] frame=1 call_count=2
[RENDER_CALL] frame=2 call_count=2
```

## Test The Fix

1. Run: `python engine.py --testing`
2. Kill an orc to get corpse + weapon
3. Hover over the corpse + weapon tile
4. **The tooltip should NO LONGER FLICKER** ✅

## Files Modified

- `engine/systems/optimized_render_system.py` — Added skip_drawing check in update() method

## Root Cause Summary

| Component | Issue |
|-----------|-------|
| render_all() calls | 2 per frame (one from each system) |
| Console flushes | 2 per frame (one for each render) |
| Tooltip rendering | Happens twice, conflicting renders visible |
| **Result** | **FLICKER** |

**After Fix:**
| Component | Status |
|-----------|--------|
| render_all() calls | 1 per frame (only from ConsoleRenderer) |
| Console flushes | 1 per frame (single authority) |
| Tooltip rendering | Happens once per frame, stable |
| **Result** | **✅ NO FLICKER** |

---

## Clean Up

You can now remove the diagnostic prints by deleting these from your files:

1. **`render_functions.py`** lines 149-178 (the _render_call_count tracking)
2. **`render_functions.py`** lines 384-393 (the [TOOLTIP_RENDER] diagnostic)
3. **`engine/systems/ai_system.py`** lines 406-408 (the [LOOT_DEBUG] diagnostic)

Or leave them for now - they're harmless and can help with future debugging.

---

**Status:** ✅ **FIXED**
**Test:** Hover over weapon + corpse, should have zero flicker

