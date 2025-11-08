# Portal System Refactoring Plan

## Goal
Consolidate scattered portal logic into a single, centralized `PortalManager` service.

## Current State (Fragmented)
- `PortalPlacer` creates Portal components directly
- `victory_manager.py` creates portal via `create_unique_item()`
- `game_actions.py` wraps portals in Entity objects
- `PortalSystem` handles collision detection
- `MovementService` handles portal entry detection
- `entity_factory.py` has `create_portal()` method (becoming obsolete)

## New State (Unified)
- **PortalManager** handles ALL portal creation, collision, teleportation
- **PortalPlacer** becomes thin wrapper around PortalManager
- **victory_manager** uses PortalManager
- **MovementService** delegates to PortalManager
- **Single interface** for all portal operations

## Execution Steps

### Phase 1: Integration (PortalManager → Existing Code)
✅ Step 1: Create PortalManager service (`services/portal_manager.py`)

**Step 2: Update game_actions.py**
- Replace `factory.create_portal()` calls with `PortalManager.create_portal_entity()`
- Use PortalManager for linking portal pairs

**Step 3: Update movement_service.py**
- Replace `PortalSystem.check_portal_collision()` with `PortalManager.check_portal_collision()`
- Replace `_check_portal_entry()` with `PortalManager.check_victory_portal_collision()`

**Step 4: Update victory_manager.py**
- Replace `create_unique_item('entity_portal')` with `PortalManager.create_portal_entity('entity_portal')`

**Step 5: Simplify PortalPlacer**
- Remove direct Portal() creation
- Store Portal components created by PortalManager
- PortalPlacer becomes pure "placement sequencing" logic

### Phase 2: Cleanup (Obsolete Code)
**Step 6: Deprecate PortalSystem.check_portal_collision()**
- Replace with PortalManager version
- Keep old method but have it delegate to PortalManager

**Step 7: Remove entity_factory.create_portal()**
- No longer needed - PortalManager handles this

**Step 8: Clean up entity_factory.create_wand_of_portals()**
- Still creates the wand, but no longer creates portals

### Phase 3: Testing & Validation
**Step 9: Update existing tests**
- All portal tests use PortalManager

**Step 10: Add integration tests**
- Test wand portal creation → collision → teleportation
- Test victory portal creation → collision → confrontation
- Test portal linking
- Test portal recycling

## Benefits
✅ Single source of truth for portal logic  
✅ Easier to debug - all portal logic in one place  
✅ Consistent interfaces across all portal operations  
✅ Easier to add new portal types in future  
✅ Better testability - centralized logic is easier to test  
✅ Reduced coupling - other systems just call PortalManager  

## Implementation Time
- Phase 1 (Integration): ~2-3 hours
- Phase 2 (Cleanup): ~1 hour  
- Phase 3 (Testing): ~1 hour
- **Total: ~4 hours**

## Files to Modify
- `services/portal_manager.py` (NEW) ✅
- `game_actions.py` (refactor portal placement)
- `services/movement_service.py` (use PortalManager)
- `victory_manager.py` (use PortalManager)
- `components/portal_placer.py` (simplify)
- `engine/portal_system.py` (deprecate or delegate)
- `config/entity_factory.py` (remove create_portal)
- `tests/test_portal_*.py` (update to use PortalManager)

## Risk Assessment
**Low Risk** - We have working code, just refactoring internal organization
- All functionality already exists and tested
- Changes are primarily routing/delegation
- Can test each step incrementally

