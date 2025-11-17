# Bot Soak Libtcod Initialization Fix

## Problem

Running `python3 engine.py --bot-soak` crashed every single run with:

```
RuntimeError: libtcod 2.2.1 libtcod/src/libtcod/console_etc.c:101
Console must not be NULL or root console must exist.
```

The crash occurred in `ConsoleRenderer.render()` when calling `libtcod.console_flush()`.

## Root Cause

Bot-soak mode bypassed libtcod initialization entirely:

1. **Normal mode** (`python3 engine.py`):
   - `main()` calls `libtcod.console_set_custom_font()` and `libtcod.console_init_root()`
   - Creates the root console BEFORE entering the game loop
   - `ConsoleRenderer.render()` → `console_flush()` works ✅

2. **Bot-soak mode** (`python3 engine.py --bot-soak`) BEFORE FIX:
   - `main()` detected `--bot-soak` flag early (line 167)
   - Immediately jumped to `run_bot_soak()` and returned
   - **NEVER called `console_init_root()`** ❌
   - `run_bot_soak()` created consoles with `console_new()` but no root console
   - `ConsoleRenderer.render()` → `console_flush()` crashed (no root console)

## Solution

**Approach:** Visible Soak (initialize libtcod properly for bot-soak mode)

### Changes Made

1. **`engine/soak_harness.py`**:
   - Added `import tcod.libtcodpy as libtcod` at module level
   - Created `_initialize_libtcod_for_soak()` function that:
     - Calls `console_set_custom_font()` with the font file
     - Calls `console_init_root()` to create the root console
     - Matches the initialization done in `engine.py main()`
   - Modified `run_bot_soak()` to call `_initialize_libtcod_for_soak()` ONCE at session start
   - Added comprehensive lifecycle documentation in module docstring

2. **`engine.py`**:
   - Added LIBTCOD LIFECYCLE documentation to module docstring
   - Explains initialization flow for all three modes:
     - Normal mode
     - Single bot mode
     - Bot soak mode

3. **`engine_integration.py`**:
   - Added LIBTCOD LIFECYCLE ASSUMPTIONS documentation
   - Clarifies that `play_game_with_engine()` expects root console to exist
   - Documents caller responsibilities

4. **`io_layer/console_renderer.py`**:
   - Added comment before `console_flush()` explaining root console requirement
   - Documents that caller must initialize libtcod before creating ConsoleRenderer

5. **`tests/test_bot_soak.py`**:
   - Added `test_run_bot_soak_initializes_libtcod_root_console()` test
   - Verifies that `console_set_custom_font()` and `console_init_root()` are called ONCE
   - Updated existing tests to mock libtcod initialization functions

## Libtcod Lifecycle Summary

### Normal Mode
1. `main()` → `console_set_custom_font()`
2. `main()` → `console_init_root()` ✅ ROOT CONSOLE CREATED
3. `main()` → `console_new()` for sidebar/viewport/status
4. `main()` → `play_game_with_engine()` → `ConsoleRenderer.render()` → `console_flush()` ✅

### Single Bot Mode
- IDENTICAL to normal mode (just uses `BotInputSource` instead of `KeyboardInputSource`)

### Bot Soak Mode (AFTER FIX)
1. `main()` → `run_bot_soak()`
2. `run_bot_soak()` → `_initialize_libtcod_for_soak()`:
   - `console_set_custom_font()`
   - `console_init_root()` ✅ ROOT CONSOLE CREATED
3. For each of N runs:
   - `console_new()` for sidebar/viewport/status (per-run consoles)
   - `play_game_with_engine()` → `ConsoleRenderer.render()` → `console_flush()` ✅
4. Root console persists until process exit

## Testing

All tests pass:
```bash
pytest tests/test_bot_soak.py -v
# 8 passed
```

Key test: `test_run_bot_soak_initializes_libtcod_root_console` verifies:
- `console_set_custom_font()` called once
- `console_init_root()` called once
- Runs complete without crashes

## Verification Checklist

Before considering the fix complete, verify:

- [x] Unit tests pass (`pytest tests/test_bot_soak.py`)
- [ ] `python3 engine.py` - normal game works, no regression
- [ ] `python3 engine.py --bot` - single bot run works
- [ ] `python3 engine.py --bot-soak` - runs 10 games without libtcod crashes
- [ ] Bot-soak session summary shows `Crashes: 0` (not 10)

## Design Decisions

### Why Visible Soak (not Headless)?

We chose to initialize libtcod for bot-soak rather than creating a headless mode because:

1. **Simpler**: Single initialization function, no new abstractions
2. **Safer**: Reuses existing, tested code paths
3. **Observable**: Can watch bot-soak runs if needed (debugging, demos)
4. **Consistent**: All three modes use the same rendering pipeline
5. **Minimal change**: Only added ~40 lines vs. a full headless renderer abstraction

Headless mode would require:
- New renderer implementation (or render bypass logic)
- New code paths to test and maintain
- Risk of divergence between visible and headless behavior
- More complex conditional logic in engine/render systems

### Why Initialize Once Per Session (not Per Run)?

Libtcod root console creation is a heavyweight operation that:
- Opens a window
- Initializes graphics context
- Loads fonts

Creating/destroying it per run would:
- Add significant overhead (window flicker, context setup)
- Risk resource leaks
- Complicate shutdown logic

Single initialization matches normal mode behavior and is stable.

## Related Files

- `engine.py` - Normal mode entry point
- `engine/soak_harness.py` - Bot soak orchestration (FIX HERE)
- `engine_integration.py` - Game loop that assumes libtcod exists
- `io_layer/console_renderer.py` - Calls `console_flush()` (needs root console)
- `tests/test_bot_soak.py` - Verification tests

## Future Work

If truly headless bot-soak is desired in the future:
1. Create `HeadlessRenderer` implementing `Renderer` protocol
2. Make `HeadlessRenderer.render()` a no-op (or log-only)
3. Add `--headless` flag to select `HeadlessRenderer` vs `ConsoleRenderer`
4. Ensure all systems handle headless mode gracefully

This would allow running bot-soak on headless CI servers or for high-speed telemetry collection.

