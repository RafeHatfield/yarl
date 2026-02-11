# Rendering Migration Plan: ASCII -> Tileset + Mobile

**Status:** Future work. Revisit when gameplay is 90%+ complete.
**Created:** 2026-02-10
**Context:** Analysis of current tcod coupling and roadmap for tileset rendering + iOS mobile port.

---

## Executive Summary

The codebase has well-designed rendering abstractions (`RenderBackend`, `Surface`, `InputBackend`, `TileRenderer` protocol) but the actual rendering pipeline largely bypasses them, with ~20 files making direct `libtcod.console_*` calls. The migration path is clear but should wait until gameplay is substantially complete. The current font-based renderer is simple, fast, and not holding back development.

---

## Target Rendering System

**Tileset:** Grid-locked tile atlas (e.g., [Kenney 1-Bit Pack](https://kenney.nl/assets/1-bit-pack) — 1,078 tiles, 16x16px, CC0 license).

The 1-bit monochrome style maps directly to the current rendering model:
- Current: `VisualSpec.char='o'` + `fg_color=(63,127,63)` draws a green ASCII "o"
- Future: `render_key="orc"` resolves to tile atlas coordinate, tinted with same fg/bg colors
- The existing `render_key` -> `VisualSpec` mapping in `visual_registry.py` is the right lookup mechanism; a tileset backend resolves render_keys to atlas coordinates instead of ASCII characters.

This is **not** a free-form sprite system. Tiles are grid-aligned, fixed-size, one per cell — a direct upgrade from ASCII with the same data model.

---

## Current tcod Usage Analysis

tcod usage falls into three distinct categories:

### Category 1: Algorithm Usage (KEEP — no changes needed)

These use tcod for pure computation, not rendering. They work headlessly and don't need to change:

| File | Usage |
|------|-------|
| `fov_functions.py` | `tcod.map` for FOV computation |
| `components/player_pathfinding.py` | Pathfinding |
| `components/auto_explore.py` | Pathfinding |
| `components/ai/boss_ai.py` | `tcod.path` |
| `components/fighter.py` | `tcod.los.bresenham` |
| `throwing.py` | `tcod.los.bresenham` |
| `io_layer/bot_brain.py` | Bot pathfinding |

### Category 2: Backend Implementations (CLEAN SWAP targets)

These are properly behind the abstract interfaces — replace, don't refactor:

| File | Abstraction |
|------|------------|
| `rendering/libtcod_backend.py` | Implements `RenderBackend` ABC |
| `input/libtcod_backend.py` | Implements `InputBackend` ABC |

### Category 3: Direct libtcod Rendering Calls (LEAKAGE — needs refactoring)

These files call `libtcod.console_*` directly, bypassing the `Surface`/`RenderBackend` abstractions. This is the bulk of the migration work:

| File | What it does |
|------|-------------|
| `render_functions.py` | Main render pipeline — `console_blit`, `console_rect`, `console_print_ex` throughout |
| `engine.py` | Console init, font loading, window setup |
| `io_layer/console_renderer.py` | Clear, blit, flush via raw libtcod |
| `io_layer/effect_renderer.py` | Visual effects via `console_put_char` |
| `io_layer/sidebar_renderer.py` | Full sidebar drawn with direct libtcod |
| `io_layer/tooltip_renderer.py` | Tooltips via direct libtcod |
| `io_layer/render_optimization.py` | Optimized tile rendering via libtcod |
| `io_layer/menu_renderer.py` | All menus via direct libtcod |
| `io_layer/wizard_menu_renderer.py` | Wizard menu |
| `io_layer/death_screen_renderer.py` | Death screen |
| `io_layer/victory_screen_renderer.py` | Victory screen |
| `io_layer/npc_dialogue_renderer.py` | NPC dialogue |
| `io_layer/hall_of_fame_renderer.py` | Hall of fame |
| `io_layer/confrontation_choice_renderer.py` | Confrontation UI |
| `io_layer/grief_rage_cutscene_renderer.py` | Cutscenes |
| `io_layer/fool_freedom_cutscene_renderer.py` | Cutscenes |
| `io_layer/keyboard_input.py` | Keyboard input |
| `input_handlers.py` | Input handling |
| `engine_integration.py` | Game loop integration |
| `engine/soak_harness.py` | Soak test harness |
| `engine/systems/render_system.py` | Render system |
| `rendering/compatibility.py` | Compatibility layer |
| `loader_functions/initialize_new_game.py` | Game initialization |
| `map_objects/game_map.py` | One libtcod import (line ~2031) |

---

## Existing Abstractions (Already Built)

These are well-designed and ready to use when the time comes:

| Abstraction | File | Purpose |
|------------|------|---------|
| `RenderBackend` ABC | `rendering/backend.py` | Backend lifecycle, surface creation, present/clear |
| `Surface` ABC | `rendering/surface.py` | `set_char`, `print_string`, `blit`, `clear`, `fill_rect`, `draw_border` |
| `LibtcodSurface(Surface)` | `rendering/libtcod_backend.py` | Current tcod implementation of Surface |
| `Color` | `rendering/color.py` | Backend-agnostic color type |
| `Rect` | `rendering/surface.py` | Rectangle for drawing ops |
| `InputBackend` ABC | `input/backend.py` | Event polling, device management, capabilities |
| `InputCapabilities` flags | `input/backend.py` | Includes `TOUCH`, `TOUCH_MULTIPOINT`, `TOUCH_PRESSURE` |
| `NullInputBackend` | `input/backend.py` | Fallback/testing backend |
| `TileRenderer` protocol | `io_layer/interfaces.py` | `draw_tile(x, y, render_key, fg, bg)`, `draw_text`, `clear`, `present` |
| `Renderer` protocol | `io_layer/interfaces.py` | `render(game_state)` |
| `InputSource` protocol | `io_layer/interfaces.py` | `next_action(game_state) -> ActionDict` |
| `VisualSpec` | `rendering/visual_registry.py` | `char`, `fg_color`, `bg_color`, `description` — maps render_keys to visuals |
| `FrameContext` / `FrameVisuals` | `rendering/frame_models.py` | Pure dataclass frame data, no tcod imports |

---

## Migration Roadmap

### Phase A: Route All Rendering Through Surface

**Goal:** Every `libtcod.console_*` call in Category 3 goes through the `Surface` abstraction instead.

**Approach:**
- Replace raw console handle passing with `Surface` objects
- Each io_layer renderer calls `surface.set_char()`, `surface.print_string()`, etc. instead of `libtcod.console_set_char()`, `libtcod.console_print_ex()`, etc.
- The `LibtcodSurface` implementation handles the actual tcod calls — game behaves identically
- Can be done incrementally, one file at a time
- Start with small self-contained files (e.g., `effect_renderer.py`, `sidebar_renderer.py`) before tackling `render_functions.py`

**Regression risk:** Moderate. Touching ~20 files, but each change is mechanical (swap direct call for Surface method). Test each file individually.

**The current rendering continues to work throughout** — `LibtcodSurface` is the backing implementation; we're just routing through it properly.

### Phase B: Build pygame-ce Tileset Backend

**Goal:** New `PygameSurface(Surface)` and `PygameBackend(RenderBackend)` with tile atlas rendering.

**What this implements:**
- `PygameSurface.set_char(x, y, char, fg, bg)` — looks up render_key in tile atlas, blits tinted tile
- `PygameBackend.initialize()` — creates pygame window, loads tile atlas
- `PygameBackend.present()` — `pygame.display.flip()`
- Tile atlas loading and coordinate mapping (render_key -> atlas x,y)
- Backend selection via config/CLI flag: `--renderer=tcod` (default) vs `--renderer=pygame`

**Dependencies:** Phase A must be complete. Also requires choosing and committing to a tile atlas (Kenney 1-bit or similar) and defining the render_key -> tile coordinate mapping.

**Desktop tileset and mobile compatibility come from the same work** — pygame-ce uses SDL2 under the hood, which is more portable than tcod's console system.

### Phase C: Mobile Backend

**Goal:** iOS-compatible rendering backend.

**Options (evaluate when ready):**
1. **Web frontend** (most practical first pass) — Python game engine serves state via WebSocket, HTML5 Canvas renders tiles. Package with Capacitor for iOS. Turn-based nature means latency is a non-issue.
2. **Kivy** — Python-native, compiles to iOS via python-for-ios. OpenGL canvas for tile rendering. Smaller ecosystem, potentially finicky.
3. **Native Swift frontend** — Best iOS experience, most work. Python core as "game server", SwiftUI renders tiles.

**The key point:** All three options consume the same `Surface` / `TileRenderer` API from Phase A. The game engine doesn't change.

---

## Timing Recommendation

**Do not start this work until gameplay is substantially complete (~90%+ features).**

### Reasoning:

1. **Current renderer isn't a bottleneck.** The font-based system is simple, fast, and works. It's not holding back gameplay development.

2. **Phase A is pure infrastructure.** It ships zero gameplay, zero features, zero content. It just changes how existing working code calls the same library.

3. **Regression risk vs. benefit.** Touching ~20 rendering files introduces bugs for no user-visible benefit right now.

4. **The abstractions don't rot.** `RenderBackend`, `Surface`, `TileRenderer`, `VisualSpec` — they'll be there when needed. Nothing about the current codebase makes this harder to do later.

5. **Art direction should be settled first.** The tile atlas choice, color palette, animation approach — these decisions should drive the renderer, not the other way around.

### Convention for new code (effective now):

- When writing new io_layer renderers or UI screens, keep them as clean as possible
- Minimize raw `libtcod.console_*` calls where natural
- Pass data rather than console handles where it doesn't add complexity
- Don't refactor working code just for abstraction purity

---

## Quick Reference: What Changes vs. What Doesn't

### Changes (rendering swap):
- `rendering/libtcod_backend.py` -> new `rendering/pygame_backend.py`
- `input/libtcod_backend.py` -> new `input/pygame_backend.py` (or touch backend)
- All Category 3 files refactored to use Surface
- `visual_registry.py` extended with tile atlas coordinate mapping
- `engine.py` backend selection logic

### Does NOT change:
- ECS architecture
- Combat systems, AI, balance
- YAML-driven content / entity definitions
- Game state machine, event system
- FOV, pathfinding, line-of-sight (Category 1 tcod usage)
- Camera system
- Bot/autoplay harness
- All game logic
- `FrameContext` / `FrameVisuals` data models
- `VisualSpec` render_key system (extended, not replaced)
