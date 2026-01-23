# Tileset Readiness Report

**Date:** 2026-01-21  
**Status:** GROUNDWORK COMPLETE  
**Scope:** Audit + minimal seam establishment (no tileset rendering implemented)

---

## Executive Summary

The Catacombs of YARL codebase has a solid foundation for future tileset support. The existing `Renderer` protocol and `RenderBackend` abstraction provide clean extension points. However, **no canonical visual identity system** (`render_key`) exists—visuals are scattered across YAML configs and hardcoded in rendering functions.

This report documents the current state and the minimal changes made to establish tileset readiness without implementing actual tile rendering.

---

## 1. Current Rendering Architecture

### 1.1 Where Drawing Happens

| File | Responsibility |
|------|---------------|
| `render_functions.py` | Main orchestration: `render_all()`, `draw_entity()`, `_render_hazard_at_tile()` |
| `io_layer/console_renderer.py` | `ConsoleRenderer` class wrapping libtcod, implements `Renderer` protocol |
| `io_layer/render_optimization.py` | `OptimizedTileRenderer` for map tiles with caching |
| `rendering/backend.py` | Abstract `RenderBackend` interface |
| `rendering/libtcod_backend.py` | `LibtcodBackend` implementation |
| `rendering/surface.py` | Abstract `Surface` class for resolution-independent drawing |

### 1.2 Existing Renderer Abstraction

**YES** - A clean renderer abstraction exists:

```python
# io_layer/interfaces.py
class Renderer(Protocol):
    def render(self, game_state: Any) -> None: ...
```

The `ConsoleRenderer` in `io_layer/console_renderer.py` implements this protocol, wrapping all libtcod drawing. This is the primary integration point for a future tileset renderer.

### 1.3 How Visuals Are Chosen Today

| Entity Type | Visual Source | State Handling |
|-------------|---------------|----------------|
| **Monsters** | `config/entities.yaml` → `char`, `color` fields | None (fixed appearance) |
| **Items** | `config/entities.yaml` → `char`, `color` fields | Wands show charge count in name |
| **Hazards/Traps** | `Trap.get_visible_char()` method | Hidden→`.`, Detected→type char, Disarmed→`x` |
| **Ground Hazards** | Hardcoded in `_render_hazard_at_tile()` | Fire→`*`, Poison→`%`, fades with age |
| **Chests** | `config/entities.yaml` → `char`, `color` | OPEN state changes color to grey |
| **Stairs** | `config/entities.yaml` → `char`, `color` | None |
| **Signs/Murals** | `config/entities.yaml` → `char`, `color` | None |
| **Tiles (floors/walls)** | `TileRenderState` enum in `render_optimization.py` | Visible/Explored states, custom light/dark colors |

### 1.4 Existing render_key / sprite_id Concept

**NO** - Prior to this task, no canonical visual identity existed.

The only reference was in the future-extension example in `docs/architecture/RENDERER_INPUT_ABSTRACTION.md`:
```python
sprite = self.library[entity.sprite_id]  # Example code, not implemented
```

---

## 2. Gaps Identified (Pre-Task)

1. **No canonical `render_key`** - Entities lacked a stable visual identity string
2. **No centralized visual registry** - Char/color mappings scattered across YAML and code
3. **No tileset renderer seam** - The `Renderer` protocol existed but lacked a tile-drawing interface
4. **State-based visuals inconsistent** - Traps use a method, chests use inline logic, hazards are hardcoded

---

## 3. Changes Made (Minimal Groundwork)

### 3.1 Added `render_key` Property to Entity

**File:** `entity.py`

Added a computed property that returns a canonical visual identity:

```python
@property
def render_key(self) -> str:
    """Get the canonical render key for visual lookup."""
    # Explicit render_key takes priority
    if hasattr(self, '_render_key') and self._render_key:
        return self._render_key
    
    # Derive from component state (trap, chest, etc.)
    # ... state-aware derivation logic ...
    
    # Fallback to species_id or sanitized name
    return self.species_id
```

**Key features:**
- Explicit `_render_key` attribute takes priority (for YAML-defined keys)
- State-aware derivation for traps (e.g., `trap_spike_hidden`, `trap_spike_detected`)
- State-aware derivation for chests (e.g., `chest_closed`, `chest_open`)
- Fallback to `species_id` (which itself falls back to sanitized name)

### 3.2 Created Visual Registry

**File:** `rendering/visual_registry.py`

A centralized mapping from `render_key` to visual properties:

```python
def get_visual(render_key: str) -> VisualSpec:
    """Get visual properties for a render key."""
    return VISUAL_REGISTRY.get(render_key, DEFAULT_VISUAL)
```

**Features:**
- `VisualSpec` dataclass with `char`, `fg_color`, `bg_color`, `description`
- Registry populated from `config/entities.yaml` at module load
- Handles all entity types: monsters, items, map_features, map_traps, etc.
- State-variant keys for traps and chests
- Clean fallback to default visual (white `?`)

### 3.3 Extended Renderer Interface

**File:** `io_layer/interfaces.py`

Added `TileRenderer` protocol for future tileset support:

```python
class TileRenderer(Protocol):
    """Protocol for tile-based rendering (future tileset support)."""
    
    def draw_tile(
        self,
        x: int,
        y: int,
        render_key: str,
        fg_color: Optional[Tuple[int, int, int]] = None,
        bg_color: Optional[Tuple[int, int, int]] = None,
    ) -> None: ...
    
    def draw_text(
        self,
        x: int,
        y: int,
        text: str,
        fg_color: Optional[Tuple[int, int, int]] = None,
        bg_color: Optional[Tuple[int, int, int]] = None,
    ) -> None: ...
```

This protocol is **interface-only**—no implementation changes to the current renderer.

### 3.4 Added Lightweight Tests

**File:** `tests/test_tileset_readiness.py`

Tests verifying:
- Entity `render_key` determinism
- Trap state-based render keys
- Chest state-based render keys  
- Visual registry returns expected glyphs
- Registry handles unknown keys gracefully

---

## 4. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Game Loop                                │
│                  (engine_integration.py)                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Renderer Protocol                             │
│                  (io_layer/interfaces.py)                        │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ render(state)    │  │ TileRenderer     │ ◄── NEW (seam)      │
│  └──────────────────┘  │ draw_tile(...)   │                     │
│                        │ draw_text(...)   │                     │
│                        └──────────────────┘                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────────┐
│ ConsoleRenderer  │ │ (Future)         │ │ (Future)             │
│ (ASCII/libtcod)  │ │ SpriteRenderer   │ │ WebGLRenderer        │
└────────┬─────────┘ └──────────────────┘ └──────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Visual Registry                               │
│              (rendering/visual_registry.py)                      │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ get_visual(render_key) → {char, fg_color, bg_color}     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Entity.render_key ──► "orc" ──► {char='o', color=(63,127,63)} │
│  Entity.render_key ──► "trap_spike_detected" ──► {char='^'}    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Future Tileset Implementation Path

When ready to implement tileset rendering:

1. **Create `SpriteRenderer`** implementing `TileRenderer` protocol
2. **Extend `visual_registry.py`** to return tile indices alongside char/color
3. **Load sprite atlas** in renderer initialization
4. **Replace `draw_entity()` calls** with `draw_tile(entity.render_key, ...)`
5. **Add render mode setting** to switch between ASCII and tiles

No changes needed to:
- Game logic, combat, AI, balance
- Entity definitions (render_key is derived)
- TurnManager or determinism
- Existing ASCII rendering (remains default)

---

## 6. Files Modified

| File | Change |
|------|--------|
| `entity.py` | Added `render_key` property |
| `rendering/visual_registry.py` | **NEW** - Centralized visual mapping |
| `io_layer/interfaces.py` | Added `TileRenderer` protocol |
| `tests/test_tileset_readiness.py` | **NEW** - Lightweight tests |

---

## 7. Verification

```bash
# Run all non-slow tests
pytest -m "not slow"

# Run tileset readiness tests specifically
pytest tests/test_tileset_readiness.py -v
```

All existing tests pass. No visual changes to ASCII output.

---

## 8. Conclusion

The codebase now has the minimal groundwork for tileset support:

✅ **Canonical visual identity** - Every entity has a deterministic `render_key`  
✅ **Centralized visual mapping** - `visual_registry.get_visual()` provides char/color  
✅ **Clear renderer seam** - `TileRenderer` protocol defines the interface  
✅ **State-aware visuals** - Traps and chests have state-variant render keys  
✅ **Zero gameplay impact** - No changes to logic, balance, or determinism  
✅ **ASCII unchanged** - Current rendering identical to before  

The path to tileset rendering is now clear and requires no architectural changes—only implementation of the defined interfaces.
