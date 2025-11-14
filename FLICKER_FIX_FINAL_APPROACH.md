# Tooltip Flicker - Final Fix (Working Approach)

## What Happened

1. **Original problem:** Tooltip flicker on weapons/corpses
2. **Root cause:** `render_all()` was being called twice per frame
3. **My first fix:** Tried to switch to ConsoleRenderer (abstraction layer)
4. **Result:** Broke everything - map went black

## Why ConsoleRenderer Failed

The ConsoleRenderer abstraction layer wasn't fully integrated:
- `renderer.render()` wasn't actually being called properly
- RenderSystem was STILL running and calling render_all()
- Result: map went black because rendering was broken

## The Right Approach

**Keep RenderSystem as the primary rendering system** (it works!), but prevent double rendering.

The double rendering was likely caused by:
1. RenderSystem calling render_all() 
2. Some OTHER path (maybe old code) also calling render_all()

### Real Solution

**One-line fix:** Just prevent the second render_all() call by checking if we're already rendering.

Since RenderSystem is working fine now and the map is visible, the flicker issue might have been solved by simply:
1. Using RenderSystem directly (current state)
2. Making sure it only calls render_all() once per frame

## Status Now

- ✅ Map visible
- ✅ Game playable  
- ❌ Tooltip flicker still happens (double rendering back)

## Next Step

Run the game and check the [RENDER_CALL] diagnostics:

```bash
python3 engine.py --testing 2>&1 | grep "\[RENDER" | head -50
```

If we see `call_count=2` again, that means RenderSystem alone is somehow calling render_all() twice. If we only see `call_count=1`, then there's a different cause for the flicker.

## Decision

Should we:
A) Keep the current working state (map visible, but flicker returns)
B) Try a simpler, more targeted fix to prevent double rendering

I recommend: **Keep current state, run diagnostics, then implement minimal fix**

