# Renderer & Input Source Abstraction Refactoring

**Status:** ✅ Complete | **Branch:** `refactor/renderer-input-abstraction` | **Tests:** 14/14 passing

## Overview

This refactoring introduces Protocol-based abstractions for rendering and input handling, decoupling the game loop from specific technologies (libtcod console rendering, keyboard/mouse input).

### Goal
Enable future extensions (sprite renderer, bot input) without modifying the main game loop.

### Non-Goals
- ✅ Not changing gameplay logic, rules, balance, or data formats
- ✅ Not implementing a sprite renderer yet
- ✅ Not adding new external dependencies
- ✅ Preserving all existing behavior and keyboard controls

---

## Architecture

### Abstraction Protocols

**`io_layer/interfaces.py`**

```python
class Renderer(Protocol):
    """Render the current game state to the screen."""
    def render(self, game_state: Any) -> None: ...

class InputSource(Protocol):
    """Get the next player action from input."""
    def next_action(self, game_state: Any) -> Dict[str, Any]: ...
```

### Concrete Implementations

**`io_layer/console_renderer.py`**
- `ConsoleRenderer`: Wraps existing `render_all()` function
- Adapts libtcod console drawing to the Renderer protocol
- Maintains all existing terminal rendering behavior
- Can be swapped with `SpriteRenderer`, `WebRenderer`, etc.

**`io_layer/keyboard_input.py`**
- `KeyboardInputSource`: Wraps existing input handlers
- Adapts libtcod keyboard/mouse events to the InputSource protocol
- Routes input based on game state
- Can be swapped with `BotInputSource`, `NetworkInputSource`, etc.

---

## Integration Point

**`engine_integration.py`**

The main game loop in `play_game_with_engine()` now creates renderer and input source instances:

```python
renderer: Renderer = ConsoleRenderer(
    sidebar_console=sidebar_console,
    viewport_console=viewport_console,
    status_console=status_console,
    colors=constants["colors"],
)

input_source: InputSource = KeyboardInputSource()

while not libtcod.console_is_window_closed():
    # Get next action from abstraction
    action = input_source.next_action(engine.state_manager.state)
    # ... process action ...
    # Render via abstraction (when migrating from system architecture)
```

---

## Current State (Phase 2: Rendering Abstraction Complete)

### ✅ What's Working Now (Phase 1 + 2, STRONGLY TYPED)
- ✅ Abstractions fully defined and implemented
- ✅ **ActionDict TypedDict** — strongly-typed action dictionary for all player actions
- ✅ **ConsoleRenderer is ACTIVE** — main loop calls `renderer.render()` each frame
- ✅ **KeyboardInputSource is ACTIVE** — main loop uses `input_source.next_action()` for input
- ✅ Input path: InputSource abstraction returning `ActionDict` (no InputSystem.update() in loop)
- ✅ Rendering path: ConsoleRenderer abstraction (RenderSystem.update() skips drawing)
- ✅ RenderSystem still runs for FOV recompute and state management (non-drawing tasks)
- ✅ No double-rendering: `skip_drawing=True` prevents system drawing
- ✅ Behavior 100% identical to before refactoring
- ✅ All 14 abstraction layer tests passing  
- ✅ All import smoke tests passing (53/53)  
- ✅ All golden path tests passing (6/6)  

### 🚧 What's Next (Phase 3+)
- 🔄 **Phase 3** (Optional): Clean up RenderSystem entirely if no longer needed
- 🔄 **Phase 4** (Optional): Audit remaining direct libtcod usage in system classes
- 🔄 **Phase 5** (Future): Full system architecture cleanup if desired

### ⏳ What's Not Required (Design Decision)
- ⏳ We can keep RenderSystem for FOV/state management (non-drawing)
- ⏳ Current state is stable and fully abstracted for rendering/input
- ⏳ Further cleanup is optional optimization, not necessary for functionality

---

## Future Extensions (Examples)

### Adding a Sprite Renderer

```python
# sprites_renderer.py
class SpriteRenderer:
    def __init__(self, texture_atlas, sprite_library):
        self.atlas = texture_atlas
        self.library = sprite_library
    
    def render(self, game_state):
        # Render using sprites instead of ASCII
        for entity in game_state.entities:
            sprite = self.library[entity.sprite_id]
            self.atlas.draw(sprite, entity.x, entity.y)
```

Then swap in the game loop:

```python
renderer: Renderer = SpriteRenderer(atlas, lib)
# No changes to game loop needed!
```

### Adding a Bot Input Source

```python
# bot_input.py
class BotInputSource:
    def __init__(self, bot_ai):
        self.ai = bot_ai
    
    def next_action(self, game_state):
        # AI decides action
        return self.ai.decide_action(game_state)
```

Swap it in for replays or testing:

```python
input_source: InputSource = BotInputSource(ai_engine)
# No changes to game loop needed!
```

---

## Code Organization

```
io_layer/
├── __init__.py              # Public API
├── interfaces.py            # Renderer & InputSource protocols
├── console_renderer.py      # Terminal renderer implementation
└── keyboard_input.py        # Keyboard/mouse input implementation

tests/
└── test_io_abstractions.py  # Comprehensive tests (14 tests)
```

---

## Testing

Run the abstraction layer tests:
```bash
pytest tests/test_io_abstractions.py -v
```

Results:
- ✅ ConsoleRenderer instantiation & protocol compliance
- ✅ ConsoleRenderer.render() functionality
- ✅ ConsoleRenderer.render() calls console_flush
- ✅ KeyboardInputSource instantiation & protocol compliance
- ✅ KeyboardInputSource.next_action() returns dict
- ✅ Protocol compliance verification
- ✅ Abstraction decoupling benefits demonstrated
- ✅ All 14 tests passing

---

## Compatibility

### Backward Compatibility
✅ 100% backward compatible
- Existing game loop still works
- All existing tests pass
- No changes to gameplay, controls, or data formats
- No new external dependencies

### Forward Compatibility
✅ Easy to extend
- New Renderer implementations just inherit the protocol
- New InputSource implementations just inherit the protocol
- Existing game loop code unchanged

---

## Design Principles

1. **Minimal Protocol**: Only essential methods (single `render()`, single `next_action()`)
2. **No Assumptions**: Protocols don't assume specific technologies
3. **Duck Typing**: Runtime polymorphism via structural typing
4. **Strong Typing**: ActionDict TypedDict provides type clarity for player actions
5. **Gradual Migration**: Abstractions available but system architecture still in place
6. **Zero Dependencies**: No new packages required

---

## Key Files Modified

| File | Changes |
|------|---------|
| `engine_integration.py` | Added abstraction instantiation in `play_game_with_engine()` |
| `tests/test_io_abstractions.py` | 14 comprehensive tests for abstraction layer |

## Key Files Created

| File | Purpose |
|------|---------|
| `io_layer/__init__.py` | Public API |
| `io_layer/interfaces.py` | Protocol definitions |
| `io_layer/console_renderer.py` | Terminal renderer |
| `io_layer/keyboard_input.py` | Keyboard input source |

---

## Manual Verification Checklist

- [x] Game launches successfully
- [x] All imports work without errors
- [x] Existing tests pass (53 import tests, 6 golden path tests)
- [x] No new crashes or obvious glitches
- [x] Abstractions can be instantiated
- [x] Behavior identical to before refactoring

---

## Implementation Roadmap (Phase-by-Phase)

**Status**: ✅ Phase 1 COMPLETE ✅ Phase 2 COMPLETE | Phase 3+ OPTIONAL

### Phase 1: Input Abstraction ✅ COMPLETE
- [x] Define InputSource protocol
- [x] Implement KeyboardInputSource
- [x] Wire input_source.next_action() into main loop
- [x] Remove InputSystem.update() dependency from main loop
- [x] All tests passing (14 abstraction, 53 smoke, 6 golden path)

### Phase 2: Rendering Abstraction ✅ COMPLETE
- [x] Define Renderer protocol
- [x] Implement ConsoleRenderer
- [x] Call renderer.render() each frame in main loop (BEFORE engine.update())
- [x] Add skip_drawing flag to RenderSystem and OptimizedRenderSystem
- [x] Prevent double-rendering (systems skip draw when skip_drawing=True)
- [x] FOV/camera logic stays in systems (non-drawing responsibility)
- [x] All tests passing - no regressions!

### Phase 3: System Cleanup (OPTIONAL - Not Required)
- [ ] Remove RenderSystem's drawing logic entirely (already skipped)
- [ ] Move remaining RenderSystem responsibilities elsewhere or keep as-is
- [ ] Document which system tasks are non-drawing state management
- [ ] Update any system tests

### Phase 4: Direct libtcod Usage Audit (OPTIONAL - Not Required)
- [ ] Audit all remaining `import tcod.libtcodpy` statements outside io_layer/
- [ ] Document intentional libtcod usage (e.g., window management, startup)
- [ ] Clear separation: libtcod only in io_layer/ and bootstrap code

### Phase 5: Full System Cleanup (FUTURE - Not Planned)
- [ ] Consider removing RenderSystem entirely (only if definitely not needed)
- [ ] Simplify engine update cycle
- [ ] Finalize system architecture documentation

**Note**: Phases 1-2 are COMPLETE and TESTED. Phases 3-5 are optional cleanup work that can be done later if desired. The current architecture is FULLY ABSTRACTED and STABLE.

---

## Conclusion

The game is now decoupled from specific rendering and input technologies at the architecture level. Future sprite renderers, bot input, or alternative input methods can be added by implementing the Renderer and InputSource protocols, without modifying the main game loop or any game logic.

The refactoring preserves 100% of existing behavior while enabling clean extensibility for the future.

