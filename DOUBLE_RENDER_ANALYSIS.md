# Double Render Per Frame — Root Cause Found 🎯

## The Discovery

Your diagnostic output shows **each frame number appears TWICE**:

```
[TOOLTIP_RENDER] frame=16404 ...
[TOOLTIP_RENDER] frame=16405 ...
[TOOLTIP_RENDER] frame=16405 ...  ← SAME FRAME!
[TOOLTIP_RENDER] frame=16406 ...
[TOOLTIP_RENDER] frame=16406 ...  ← SAME FRAME!
```

This means **`render_all()` is being called twice per frame**! 

## Why This Causes Flicker

When `render_all()` is called twice:

1. **First render**: Render tooltip at position (27,46) with [Club, Orc Corpse]
2. **Console flushed** (sends to screen)
3. **Second render**: Same position, same entities (but maybe rendered slightly differently?)
4. **Console flushed again** (replaces what was on screen)
5. Result: **Visual flicker** as the two renders conflict

## New Diagnostic: Confirm Double Rendering

I've added a `[RENDER_CALL]` diagnostic. When you run the game:

```bash
python engine.py --testing 2>&1 | grep -E "\[RENDER_CALL\]|\[TOOLTIP_RENDER\]" | head -50
```

You should see something like:

```
[RENDER_CALL] frame=16404 call_count=2
[RENDER_CALL] frame=16405 call_count=2
[RENDER_CALL] frame=16406 call_count=2
```

If `call_count=2` appears, **that's the problem!**

## Where render_all() is Called

Search for all places that call `render_all()`:

```bash
grep -r "render_all(" . --include="*.py" | grep -v ".pyc" | grep -v "def render_all"
```

Likely culprits:
- `engine_integration.py` - game loop
- `engine.py` - game loop  
- `engine/systems/render_system.py` - rendering system
- Anywhere else the rendering is triggered

## The Fix

Once we confirm double rendering, we need to find and FIX:

1. **Why is render_all() being called twice?**
2. **Should it only be called once per frame?**
3. **Is there a second rendering pipeline we don't know about?**

## What To Do Now

1. Run: `python engine.py --testing 2>&1 | tee /tmp/render_debug.log`
2. Hover over corpse+weapon and let it flicker
3. Look for `[RENDER_CALL]` output
4. Send me these lines showing the call counts

---

## The Club Render Order Issue

I also noticed the Club is being classified as 'corpse' when it should be 'item'. This might be a separate issue, but the DOUBLE RENDERING is the primary culprit for the flicker.

