# Camera & Viewport Scrolling - Implementation Plan

## Overview

Transform Yarl from fixed-viewport gameplay to dynamic camera scrolling, enabling massive maps and enhanced exploration.

**Current:** Fixed 80x45 viewport, 80x43 maps  
**Target:** Dynamic camera, 200x200+ maps, smooth scrolling

---

## Phase 1: Camera Foundation (Infrastructure) 🏗️

**Goal:** Build the camera system without breaking anything

**Deliverables:**
- `Camera` class to track viewport position in world space
- Viewport bounds management (prevent showing outside map)
- Coordinate translation utilities (world ↔ viewport)
- Integration with rendering system

**Value:** No visible change, but foundation is solid for everything else

**Files to Create:**
- `rendering/camera.py` - Core Camera class
- `tests/test_camera.py` - Comprehensive camera tests

**Files to Modify:**
- `rendering/backend.py` - Add camera support
- `render_functions.py` - Use camera for coordinate translation
- `config/ui_layout.py` - Add camera configuration

**Tests:**
- Camera position tracking
- Viewport bounds enforcement
- Coordinate translation accuracy
- Edge cases (small maps, player at edges)

**Acceptance Criteria:**
- [ ] All existing tests still pass
- [ ] Camera system is tested and documented
- [ ] Game runs identically (camera exists but doesn't move yet)

**Estimated Time:** 2-3 hours  
**Risk:** Low (additive only, no behavior changes)

---

## Phase 2: Camera Following (First Value!) 🎥

**Goal:** Camera tracks player movement - make it WORK!

**Deliverables:**
- Camera centers on player
- Camera updates when player moves
- Smooth camera movement (or instant snap - configurable)
- Camera stops at map edges (no black space)

**Value:** ✨ **IMMEDIATE VISIBLE IMPACT!** Player movement feels dynamic!

**Files to Modify:**
- `game_actions.py` - Update camera after player moves
- `engine/systems/render_system.py` - Render from camera position
- `render_functions.py` - Translate all rendering through camera
- `visual_effect_queue.py` - Effects use camera coordinates

**Configuration:**
- `CameraMode.CENTER` - Player always centered (default)
- `CameraMode.EDGE_FOLLOW` - Camera moves when player near edge
- Configurable "dead zone" (area player can move without camera moving)

**Tests:**
- Camera follows player movement
- Camera stops at map boundaries
- Visual effects render at correct positions
- Mouse coordinates translate correctly

**Acceptance Criteria:**
- [ ] Camera follows player smoothly
- [ ] No visual glitches or artifacts
- [ ] All mouse interactions still work
- [ ] Entity rendering is correct
- [ ] FOV updates correctly with camera

**Estimated Time:** 3-4 hours  
**Risk:** Medium (affects core rendering loop)

---

## Phase 3: Larger Maps (Unlock Potential!) 🗺️

**Goal:** Generate and support maps larger than viewport

**Deliverables:**
- Update map generation to support configurable sizes
- Generate 120x80 maps (1.5x current size) as default
- Test with various map sizes (up to 200x200)
- Verify all game systems work with large maps

**Value:** ✨ **MASSIVE DUNGEONS!** Players can explore huge spaces!

**Files to Modify:**
- `map_objects/game_map.py` - Support larger dimensions
- `loader_functions/initialize_new_game.py` - Configure map size
- `config/level_templates.yaml` - Add map size overrides
- `config/game_constants.py` - Add MAP_SIZE constants

**Configuration:**
```python
class MapConfig:
    DEFAULT_WIDTH: int = 120  # Was 80
    DEFAULT_HEIGHT: int = 80  # Was 43
    MIN_WIDTH: int = 80
    MAX_WIDTH: int = 200
    MIN_HEIGHT: int = 50
    MAX_HEIGHT: int = 200
```

**Tests:**
- Map generation at various sizes
- Pathfinding works on large maps
- Performance with large maps
- Save/load with different map sizes

**Acceptance Criteria:**
- [ ] Maps generate successfully at 120x80
- [ ] Camera scrolling reveals new areas
- [ ] Performance is acceptable (<30ms frame time)
- [ ] All game systems work correctly
- [ ] Save/load preserves map size

**Estimated Time:** 2-3 hours  
**Risk:** Medium (performance, memory, save compatibility)

---

## Phase 4: Polish & Feel (Make it Great!) ✨

**Goal:** Make camera movement feel smooth and professional

**Deliverables:**
- Smooth camera interpolation (optional)
- Camera shake for combat/effects (optional)
- Configurable camera behavior
- Visual feedback for camera boundaries

**Value:** ✨ **PROFESSIONAL FEEL!** Game feels polished and modern!

**Features:**
1. **Smooth Scrolling:**
   - Linear interpolation between positions
   - Configurable speed (instant, slow, medium, fast)
   - Option to disable for performance

2. **Camera Shake:**
   - Combat hits cause small shake
   - Explosions cause large shake
   - Configurable intensity and duration

3. **Edge Indicators:**
   - Visual hint when at map edge
   - Optional minimap showing full map
   - Fog of war visualization

4. **Camera Modes:**
   - `CENTER` - Player always centered (default)
   - `EDGE_FOLLOW` - Player can move within dead zone
   - `MANUAL` - Player controls camera separately
   - `CINEMATIC` - Pre-scripted camera movements

**Files to Modify:**
- `rendering/camera.py` - Add interpolation and shake
- `visual_effect_queue.py` - Camera shake effects
- `config/game_constants.py` - Camera configuration

**Tests:**
- Smooth interpolation math
- Camera shake doesn't break rendering
- Different camera modes work correctly

**Acceptance Criteria:**
- [ ] Camera movement is smooth (if enabled)
- [ ] Camera shake enhances combat feel
- [ ] Multiple camera modes are selectable
- [ ] Performance is still good

**Estimated Time:** 3-4 hours  
**Risk:** Low (polish only, can be disabled)

---

## Phase 5: Minimap System (Navigation!) 🧭

**Goal:** Help players navigate large maps

**Deliverables:**
- Minimap in sidebar showing explored areas
- Player position indicator
- Stairs/items marked on minimap
- Click minimap to center camera (optional)

**Value:** ✨ **NEVER GET LOST!** Players can navigate huge dungeons!

**Design:**
```
MINIMAP (in sidebar)
┌────────────────┐
│  ····          │
│  ·@··  ┌─┐     │  @ = Player
│  ····  │ │     │  · = Explored
│        └─┘     │  ┌─┐ = Rooms
│       <>       │  <> = Stairs
│                │
└────────────────┘
```

**Files to Create:**
- `ui/minimap.py` - Minimap rendering

**Files to Modify:**
- `ui/sidebar.py` - Add minimap section
- `map_objects/game_map.py` - Track explored tiles

**Features:**
- Auto-scales to sidebar width
- Shows only explored areas (fog of war)
- Highlights points of interest
- Optional: Click to move camera

**Acceptance Criteria:**
- [ ] Minimap displays in sidebar
- [ ] Accurately represents map layout
- [ ] Updates as player explores
- [ ] Doesn't impact performance

**Estimated Time:** 2-3 hours  
**Risk:** Low (UI only, non-critical feature)

---

## Phase 6: Advanced Features (Optional!) 🚀

**Goal:** Extra features for power users

**Deliverables:**
- Mouse edge-scrolling (move cursor to edge → camera pans)
- Keyboard camera controls (arrow keys to pan)
- Zoom in/out (2x, 1x, 0.5x views)
- Auto-follow mode (camera follows action)

**Value:** ✨ **POWER USER FEATURES!** Advanced camera control!

**Features:**

1. **Mouse Edge Scrolling:**
   - Cursor within 2 tiles of edge → camera pans
   - Configurable speed and dead zone
   - Can be disabled in settings

2. **Keyboard Camera:**
   - Arrow keys pan camera (when not moving player)
   - Home key to re-center on player
   - Page Up/Down to zoom

3. **Zoom Levels:**
   - 2x zoom (show more map, smaller sprites)
   - 1x zoom (default)
   - 0.5x zoom (show less, larger sprites)
   - Zoom affects FOV radius

4. **Auto-Follow Mode:**
   - Camera follows combat action
   - Pans to explosions/effects
   - Returns to player after delay

**Acceptance Criteria:**
- [ ] Mouse edge scrolling is smooth
- [ ] Keyboard controls are intuitive
- [ ] Zoom levels work correctly
- [ ] All features are configurable

**Estimated Time:** 4-6 hours  
**Risk:** Medium (lots of new interactions)

---

## Implementation Strategy

### Incremental Rollout

Each phase is:
1. **Independently valuable** (or critical foundation)
2. **Fully tested** before moving to next phase
3. **Mergeable** to main (no broken states)
4. **Documented** with clear usage

### Branch Strategy

- `feature/camera-foundation` (Phase 1)
- `feature/camera-following` (Phase 2)
- `feature/large-maps` (Phase 3)
- Merge to main after each phase ✅

### Testing Strategy

- Unit tests for all camera math
- Integration tests for rendering
- Performance tests for large maps
- Visual regression tests

### Rollback Plan

Each phase can be:
- Feature-flagged (disable if issues)
- Rolled back independently
- Fixed without blocking other work

---

## Risk Assessment

### High Risk Areas

1. **Performance** with large maps
   - Mitigation: Spatial indexing, chunk loading
   - Monitor: Frame time, memory usage

2. **Coordinate Translation** bugs
   - Mitigation: Comprehensive tests
   - Verify: Mouse clicks, visual effects, entity rendering

3. **Save Compatibility** with map sizes
   - Mitigation: Versioned save format
   - Test: Load old saves, upgrade path

### Low Risk Areas

- Camera class (isolated, well-tested)
- Minimap (UI only, optional)
- Polish features (can be disabled)

---

## Success Metrics

### Phase 1-2 (Foundation + Following)
- [ ] 0 visual regressions
- [ ] 100% test pass rate
- [ ] No performance degradation

### Phase 3 (Larger Maps)
- [ ] Maps up to 120x80 work flawlessly
- [ ] Frame time <30ms on large maps
- [ ] Memory usage <500MB

### Phase 4-6 (Polish + Advanced)
- [ ] Camera feels smooth and responsive
- [ ] Players praise exploration experience
- [ ] No bugs reported for 1 week

---

## Timeline Estimate

| Phase | Time | Cumulative |
|-------|------|------------|
| Phase 1: Foundation | 2-3 hours | 3 hours |
| Phase 2: Following | 3-4 hours | 7 hours |
| Phase 3: Large Maps | 2-3 hours | 10 hours |
| Phase 4: Polish | 3-4 hours | 14 hours |
| Phase 5: Minimap | 2-3 hours | 17 hours |
| Phase 6: Advanced | 4-6 hours | 23 hours |

**Total: ~20-25 hours of development**

**Recommended:** Do Phases 1-3 first (core value), then decide on 4-6 based on feedback.

---

## Phase 1 Next Steps

Ready to start Phase 1? Here's what we'll do:

1. Create `rendering/camera.py` with Camera class
2. Add comprehensive tests
3. Integrate with rendering system (no behavior change)
4. Verify all existing tests pass
5. Commit and merge!

**Estimated time for Phase 1: 2-3 hours**

Ready to begin? 🚀

