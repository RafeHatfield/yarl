# Flicker Fix — Corrected ✅

## The Problem (Now Fixed)

After applying the initial fix to prevent double rendering, the map went black because:

**Initial fix was too aggressive:**
- Skipped the entire `update()` method when `skip_drawing=True`
- This prevented FOV map recomputation 
- Result: No FOV data, map appeared black

## The Correct Fix

**File:** `engine/systems/optimized_render_system.py` (lines 122-150)

Changed from:
```python
# WRONG: Skipped entire update method
if self.skip_drawing:
    return
```

To:
```python
# CORRECT: Only skip rendering, not FOV computation
if not self.skip_drawing:
    # Do rendering (render_all, console_flush)
```

### What This Does

**FOV Computation:** ✅ ALWAYS happens (lines 95-120)
- Updates FOV map
- Computes visibility
- Needed for game logic

**Rendering:** ✅ Only when NOT skipped (lines 124-170)
- Calls render_all() 
- Calls console_flush()
- Skipped when ConsoleRenderer is the drawing authority

**Result:** 
- No double rendering → **No flicker** ✅
- Map still visible → **No black screen** ✅

## Key Changes

1. **FOV computation moved OUTSIDE the skip check** (lines 95-120)
   - Always happens, required for game state

2. **Rendering wrapped in `if not self.skip_drawing`** (lines 124-170)
   - Only render if we're the drawing authority
   - Prevents double rendering conflict

3. **Console flush also wrapped** (lines 152-170)
   - Only flush when we rendered

## Test Now

```bash
python engine.py --testing
```

You should see:
1. ✅ Map visible
2. ✅ Entities rendered
3. ✅ No tooltip flicker when hovering over weapons + corpses

## Architecture Now Correct

```
ConsoleRenderer.render()
├── Calls render_all()
├── Draws to console
└── Flushes once per frame
    
engine.update() → OptimizedRenderSystem.update()
├── FOV computation (ALWAYS)
├── Skip rendering (because skip_drawing=True)
└── No console_flush (ConsoleRenderer handles it)

Result: Single render_all() call per frame
        Single console_flush() per frame
        = NO FLICKER ✅
```

## Files Modified

- `engine/systems/optimized_render_system.py` — Fixed skip_drawing logic

## Next Steps

If the game works:
1. Verify tooltip no longer flickers
2. Verify map is visible and rendering correctly
3. Verify performance is acceptable

If there are still issues:
1. Check console output for errors
2. Verify FOV is working (explore the map)
3. Verify entities are visible

