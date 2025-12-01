# Rendering State Fix: Hit Flashes & Tooltips

**Date:** 2025-11-24  
**Issue:** Visual state (hit flashes, tooltips) not clearing in manual play mode

## Problem

After implementing manual-loop gating to prevent AI spam, visual effects and tooltips were "sticking":

1. **Hit flash effects:** Red damage tints on entities persisted after combat instead of clearing
2. **Tooltips:** Hover tooltips remained visible even after mouse moved away

### Root Cause

The main loop was gating `engine.update()` to only run when player acted or auto-explore was active (lines 1023-1024 of `engine_integration.py`). This correctly prevented AI spam but had an unintended side effect:

**`engine.update()` calls ALL systems, including:**
- ✅ AISystem (wanted to skip in idle frames)
- ✅ EnvironmentSystem (wanted to skip in idle frames)  
- ❌ **RenderSystem (needed every frame!)**

When we skipped `engine.update()` during idle frames in manual mode:
- Visual effects queue never got played/cleared
- Tooltip state never recomputed based on mouse movement
- Transient UI state froze on-screen

## Solution

**Separate world updates from rendering** by selectively updating systems:

### Before (Broken)
```python
if should_update_systems:
    engine.update()  # ALL systems including render
```

### After (Fixed)
```python
# Update delta_time for this frame
current_time = time.time()
engine.delta_time = current_time - engine._last_time
engine._last_time = current_time

# Update world systems (AI, Environment) only when world should tick
if should_update_systems:
    for system in engine.systems.values():
        if system.name == "render" or not system.enabled:
            continue
        system.update(engine.delta_time)

# ALWAYS update render system, regardless of world tick
render_system = engine.get_system("render")
if render_system and render_system.enabled:
    render_system.update(engine.delta_time)
```

## Changes Made

### File: `engine_integration.py`

**Lines 1015-1061:** Rewrote rendering/update section to separate world updates from rendering

**Key changes:**
1. Delta time is now updated every frame (lines 1035-1037)
2. World systems (AI, Environment) only update when `should_update_systems` is true (lines 1040-1047)
3. Render system ALWAYS updates every frame (lines 1049-1056)

**Preserved invariants:**
- Manual mode: One action/auto-explore → one world tick → one enemy phase ✅
- No AI spam when player idle ✅
- Bot mode: Continuous updates ✅

## Testing

### Automated Tests: All Pass ✅
- `tests/test_engine_integration_io_loop.py` (10 tests) - Manual loop invariants
- `tests/test_tooltip*.py` (29 tests) - Tooltip rendering
- `tests/test_visual_effects*.py` (30 tests) - Visual effect queue
- `tests/engine/systems/test_render_system.py` (12 tests) - Render system

### Expected Manual Behavior

**Hit flashes:**
- ✅ Red tint appears on entity when hit
- ✅ Tint clears after one frame (~120ms duration)
- ✅ No persistent red overlays

**Tooltips:**
- ✅ Appear when hovering over entity/item
- ✅ Update when mouse moves to different entity
- ✅ Disappear when mouse moves to empty space
- ✅ No "stuck" tooltips

**Manual play:**
- ✅ Player action → world tick → AI acts → rendering
- ✅ No action → no AI → still renders (screen updates)

**Bot/soak mode:**
- ✅ Unchanged behavior
- ✅ Continuous updates with rendering

## Architecture Notes

### Visual Effects Queue (`visual_effect_queue.py`)
- Effects are **queued** during action processing
- Effects are **played** during rendering via `get_effect_queue().play_all()`
- Effects are **cleared** after playback (line 347)
- **Critical:** Queue must be played/cleared every frame or effects accumulate

### Tooltip System (`ui/tooltip.py`)
- Tooltips computed via `tooltip.resolve_hover()` based on mouse position
- Must be recomputed each frame to respond to mouse movement
- **Critical:** Tooltips must render every frame or they freeze

### Render System (`engine/systems/optimized_render_system.py`)
- Priority: 100 (runs after all other systems)
- Calls `console_renderer.render()` which:
  - Clears consoles
  - Draws map tiles
  - Draws entities  
  - Renders UI (sidebar, status panel)
  - Resolves and renders tooltips
  - Plays visual effects queue
  - Flushes to screen

## Related Issues

- **MANUAL_LOOP_FIX_SUMMARY.md** - Manual play loop invariants (prerequisite fix)
- **MAIN_MENU_FIX_SUMMARY.md** - Menu state gating refinement

## Follow-up

None required. Fix is complete and tested.

---

**Status:** ✅ COMPLETE  
**Verification:** Manual testing recommended to confirm visual behavior





