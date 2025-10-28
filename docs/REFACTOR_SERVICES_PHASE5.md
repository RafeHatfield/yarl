# Services Refactoring - Phase 5 Portal System

**Date:** October 28, 2025  
**Branch:** `feature/phase3-guide-system`  
**Problem:** Portal entry bugs recurring due to code duplication across input methods  
**Solution:** Service layer providing single source of truth for game mechanics  

---

## The Problem

Portal entry in Phase 5 (Ruby Heart → Portal → Confrontation) was implemented in multiple places:

### Code Duplication Map (BEFORE)

```
PICKUP:
├─ Keyboard 'g' press
│  └─ game_actions.py::_handle_pickup()
│     └─ [150 lines: inventory.add_item(), check triggers_victory, spawn portal]
│
└─ Mouse right-click
   └─ mouse_movement.py::process_pathfinding_movement()
      └─ [150 lines: inventory.add_item(), check triggers_victory, spawn portal]

MOVEMENT:
├─ Keyboard arrow keys
│  └─ game_actions.py::_handle_movement()
│     └─ [120 lines: move, camera, FOV, check portal entry, secret doors]
│
└─ Mouse click/pathfinding  
   └─ mouse_movement.py::process_pathfinding_movement()
      └─ [120 lines: move, camera, FOV, check portal entry, secret doors]
```

**Result:** Every feature (portal, victory triggers, camera) implemented 2-4 times. Miss one = bug.

---

## The Solution: Service Layer

### Architecture

```
INPUT LAYER (keyboard, mouse, gamepad)
         ↓
   SERVICE LAYER (single source of truth)
         ↓
     GAME STATE
```

### Service Classes

#### 1. MovementService
**Location:** `services/movement_service.py`  
**Responsibility:** ALL player movement logic

```python
class MovementService:
    def execute_movement(self, dx, dy, source="keyboard") -> MovementResult:
        """Single source of truth for movement.
        
        Handles:
        - Movement validation (walls, entities)
        - Player position update
        - Camera following
        - FOV recomputation
        - Portal entry detection (Phase 5)
        - Secret door reveals
        
        Returns: MovementResult with success status and side effects
        """
```

#### 2. PickupService
**Location:** `services/pickup_service.py`  
**Responsibility:** ALL item pickup logic

```python
class PickupService:
    def execute_pickup(self, source="keyboard") -> PickupResult:
        """Single source of truth for pickup.
        
        Handles:
        - Item-at-location detection
        - Inventory management
        - Victory triggers (Ruby Heart)
        - Portal spawning (Phase 5)
        - Quest item special logic
        
        Returns: PickupResult with success status and side effects
        """
```

---

## Refactoring Changes

### Phase 1: Service Creation + Keyboard Migration

**Files Changed:**
- `services/__init__.py` (NEW)
- `services/movement_service.py` (NEW - 200 lines)
- `services/pickup_service.py` (NEW - 150 lines)
- `game_actions.py`:
  - `_handle_movement()` → uses `MovementService` (-120 lines)
  - `_handle_pickup()` → uses `PickupService` (-95 lines)

**Result:** Keyboard input unified ✅

### Phase 2: Mouse/Pathfinding Migration  

**Files Changed:**
- `mouse_movement.py`:
  - `process_pathfinding_movement()` → uses `MovementService` (-150 lines)
  - Auto-pickup logic → uses `PickupService` (-35 lines)

**Result:** Mouse input unified ✅

---

## Code Comparison

### Movement (BEFORE - Duplicated)

```python
# game_actions.py::_handle_movement() - 120 lines
def _handle_movement(self, dx, dy):
    player.move(dx, dy)
    camera.update(player.x, player.y)
    self.state_manager.request_fov_recompute()
    
    # Portal check
    if current_state == GameStates.RUBY_HEART_OBTAINED:
        for entity in entities:
            if hasattr(entity, 'is_portal') and entity.is_portal:
                if entity.x == player.x and entity.y == player.y:
                    # Trigger confrontation
                    ...
    
    # Secret doors
    game_map.reveal_secret_doors_near(player.x, player.y)
    ...

# mouse_movement.py::process_pathfinding_movement() - 120 lines  
# ... DUPLICATE of above logic ...
```

### Movement (AFTER - Unified)

```python
# game_actions.py::_handle_movement() - 30 lines
def _handle_movement(self, dx, dy):
    movement_service = get_movement_service(self.state_manager)
    result = movement_service.execute_movement(dx, dy, source="keyboard")
    
    if result.portal_entry:
        self.state_manager.set_game_state(GameStates.CONFRONTATION)
    ...

# mouse_movement.py::process_pathfinding_movement() - 40 lines
def process_pathfinding_movement(player, entities, game_map, fov_map):
    movement_service = get_movement_service(state_manager)
    result = movement_service.execute_movement(dx, dy, source="pathfinding")
    
    if result.portal_entry:
        pathfinding.interrupt_movement("Portal")
        return {"portal_entry": True}
    ...
```

**Duplicate Logic Removed:** ~300 lines across both files

---

## Benefits

### 1. Single Source of Truth
- Portal logic: 1 place (was 2)
- Victory trigger: 1 place (was 2)
- Camera updates: 1 place (was 2)
- Movement validation: 1 place (was 2)

### 2. Impossible to Diverge
**Before:** Portal worked for keyboard but not mouse (happened 3 times!)  
**After:** Both use same code path, can't diverge

### 3. Easier Testing
**Before:** Test keyboard movement + mouse movement separately  
**After:** Test MovementService once, all input methods work

### 4. Easier Maintenance
**Before:** Add feature → remember to update 2-4 places  
**After:** Add feature → update service once, all inputs get it

### 5. Better Debugging
All movement/pickup actions log with source ("keyboard", "pathfinding"):
```
>>> MovementService: (10, 10) -> (11, 10) via keyboard, state=RUBY_HEART_OBTAINED
>>> MovementService: Checking portal entry...
>>> MovementService: PORTAL ENTRY DETECTED!
```

---

## Testing Strategy

### Single Test Run Validates All Input Methods

```python
def test_full_portal_flow_keyboard():
    # Keyboard 'g' to pick up Ruby Heart
    action_processor.process_actions({'pickup': True}, {})
    assert portal_spawned()
    
    # Keyboard arrows to move onto portal
    action_processor.process_actions({'move': (1, 0)}, {})
    assert state == GameStates.CONFRONTATION

def test_full_portal_flow_mouse():
    # Right-click to pick up Ruby Heart
    action_processor.process_actions({}, {'right_click': (10, 10)})
    assert portal_spawned()
    
    # Click to move onto portal  
    action_processor.process_actions({}, {'left_click': (11, 10)})
    assert state == GameStates.CONFRONTATION
```

Both tests use same underlying services → if one works, both work!

---

## Future Enhancements

### Additional Services to Consider

1. **CombatService** - unify melee/ranged/spell combat
2. **InteractionService** - unify NPC dialogue, chest opening, door usage
3. **ThrowingService** - unify item throwing mechanics
4. **SpellcastingService** - unify spell targeting and effects

### Pattern for New Services

```python
class XyzService:
    def __init__(self, state_manager):
        self.state_manager = state_manager
    
    def execute_xyz(self, params, source="keyboard") -> XyzResult:
        """Single source of truth for XYZ mechanic."""
        # Validate
        # Execute
        # Return result with side effects
```

---

## Migration Checklist for Future Services

- [ ] Identify duplicated logic across input methods
- [ ] Create service class in `services/`
- [ ] Define result dataclass with all side effects
- [ ] Migrate keyboard handler to use service
- [ ] Migrate mouse handler to use service
- [ ] Add comprehensive logging with `source` parameter
- [ ] Write integration tests for all input methods
- [ ] Update documentation

---

## Lessons Learned

### What Caused the Bugs

1. **Copy-Paste Programming:** Pickup logic worked for keyboard, copy-pasted to mouse, later updates only to one
2. **No Single Source of Truth:** Same logic in multiple places, easy to forget one
3. **Insufficient Integration Tests:** Unit tests passed, but keyboard ≠ mouse wasn't caught

### How Services Prevent This

1. **Impossible to Forget:** Only ONE place to update
2. **Type-Safe Results:** Services return structured results, can't forget fields
3. **Source Logging:** Always know which input method triggered action
4. **Integration-Friendly:** Test service once = test all inputs

---

## Performance Impact

**Negligible.** Services are thin wrappers with minimal overhead:
- One extra function call per action (~0.001ms)
- No additional allocations (uses same objects)
- Same number of game state operations

**Benefit outweighs cost** massively - prevents entire class of bugs.

---

## Related Documents

- `PHASE5_CURRENT_SESSION.md` - Current Phase 5 status
- `PHASE5_TESTING_PLAN.md` - Testing procedures for endings
- `tests/test_portal_entry_integration.py` - Integration tests

---

## Summary

**Problem:** Portal bugs kept recurring (3x) due to duplicated logic  
**Solution:** Service layer with single source of truth  
**Result:** ~300 lines of duplicate code removed, future bugs prevented  
**Cost:** Negligible performance overhead, significant maintenance benefit  
**Status:** ✅ Complete - ready for testing

