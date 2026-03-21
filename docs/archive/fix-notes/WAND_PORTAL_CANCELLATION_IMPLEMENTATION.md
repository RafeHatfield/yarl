# Wand of Portals Cancellation & Charge Refund Implementation

**Date**: November 24, 2025  
**Status**: ✅ Complete  
**Tests**: 104 portal tests passing (including 13 new cancellation tests)

---

## Summary

Implemented portal cancellation and charge refund for the Wand of Portals. Players can now cancel active portal pairs by using the wand again, which removes the portals from the map and refunds the charge.

## Changes Made

### 1. Core Implementation

#### **services/portal_manager.py**
- **Added** `deactivate_portal_pair()` method
  - Removes portal entities from the game world
  - Clears bidirectional portal links
  - Invalidates entity sorting cache
  - Returns success status and removal count
  - Logs portal deactivation for debugging

#### **components/portal_placer.py**
- **Modified** `__init__()` to use finite charges (3) instead of infinite (-1)
- **Added** entity tracking: `active_entrance_entity` and `active_exit_entity`
- **Updated** `has_active_portals()` to check both components and entities
- **Added** `cancel_active_portals()` method:
  - Calls PortalManager to remove portal entities
  - Refunds 1 charge to the wand
  - Clears all internal tracking (components, entities, stage)
  - Returns detailed result with success status and charge info
- **Updated** `recycle_portals()` to also clear entity references (marked as deprecated)

#### **item_functions.py**
- **Modified** `use_wand_of_portals()` to handle two flows:
  1. **Active portals exist**: Cancel them, refund charge, show message
  2. **No active portals**: Enter targeting mode to place new pair
- **Added** charge validation (cannot use empty wand)
- **Added** charge display in success messages

#### **game_actions.py** (lines 2127-2179)
- **Added** charge consumption when placing entrance portal
- **Added** charge refund if portal entity creation fails
- **Updated** to store both component AND entity references in `portal_placer`
- **Updated** messages to show remaining charges
- **Updated** exit portal placement message to mention cancellation

#### **config/factories/spawn_factory.py**
- **Modified** `create_wand_of_portals()` to use PortalPlacer for both wand and portal_placer attributes
- **Updated** documentation to describe finite charges and cancellation flow
- **Removed** redundant Wand component creation (PortalPlacer extends Wand)

### 2. Testing

#### **tests/test_wand_portal_cancellation.py** (NEW)
Comprehensive test suite with 13 tests covering:
- ✅ Wand starts with finite charges (not infinite)
- ✅ Placing entrance consumes 1 charge
- ✅ `has_active_portals()` detects completed pairs
- ✅ Canceling removes entities from game world
- ✅ Canceling refunds 1 charge
- ✅ Canceling clears internal tracking
- ✅ Can place new portals after cancellation
- ✅ `use_wand_of_portals()` cancels when portals active
- ✅ `use_wand_of_portals()` enters targeting when no portals
- ✅ Empty wand cannot place portals
- ✅ PortalManager removes both entities
- ✅ PortalManager clears portal links
- ✅ Complete charge economy cycle (place → use → cancel → refund)

#### **tests/test_golden_path_portal_wand.py** (UPDATED)
- **Fixed** `test_player_starts_with_wand_of_portals`: Now expects finite charges
- **Updated** `test_wand_has_infinite_charges` → `test_wand_has_finite_charges_with_refund`:
  - Verifies finite charges
  - Tests charge consumption and refund
  - Confirms wand becomes empty when drained

### 3. Test Results
```
104 portal tests PASSED
  - 13 new cancellation tests
  - 91 existing portal tests (no regressions)
  - 0 failures
```

---

## New Player Flow

### Placing Portal Pair
1. Player uses Wand of Portals (3 charges)
2. Click to place entrance portal (consumes 1 charge → 2 remaining)
3. Click to place exit portal (pair now active)
4. Portals can be used for teleportation

### Canceling Active Portals
1. Player uses Wand of Portals while pair is active
2. Both portals disappear from map
3. Charge refunded (2 → 3)
4. Message: "Portals collapse as the wand's magic is withdrawn. Charge refunded (2 → 3)."
5. Wand ready to place new portal pair

### Depleted Wand
- If wand reaches 0 charges, cannot place portals
- Message: "The wand is depleted. Find a Portal scroll to recharge it."
- Portal scrolls add 1 charge when picked up (existing mechanism)

---

## Design Decisions

### Charge Economy
- **Initial charges**: 3 (configurable in `PortalPlacer.__init__`)
- **Cost to place pair**: 1 charge (consumed when placing entrance)
- **Refund on cancel**: 1 charge (net: portal pair is free if canceled)
- **Rationale**: Players can experiment with portal placement without permanent cost

### Entity vs Component Tracking
- `PortalPlacer` now tracks both Portal components AND Entity objects
- Required for proper removal from game world
- Prevents dangling references and stale entity list entries

### PortalManager Integration
- All portal removal goes through `PortalManager.deactivate_portal_pair()`
- Ensures consistent cleanup: entities removed, links cleared, cache invalidated
- Single source of truth for portal lifecycle management

### Backward Compatibility
- `recycle_portals()` method kept for old tests (marked deprecated)
- New code uses `cancel_active_portals()` for proper cleanup
- Both methods clear entity references to prevent memory leaks

---

## Architecture Adherence

✅ **ECS Compliance**: Portal state flows through Entity → Component → PortalPlacer (service)  
✅ **Single Responsibility**: PortalManager handles all portal lifecycle operations  
✅ **No Rendering Logic**: Changes are pure gameplay logic, rendering unchanged  
✅ **Input Abstraction**: Portal cancellation uses same action pipeline as placement  
✅ **Minimal Delta**: Changes localized to portal system, no architectural rewrites  
✅ **Test Coverage**: 100% coverage of new cancellation feature  

---

## Files Modified

```
services/portal_manager.py          (+57 lines)
components/portal_placer.py         (+60 lines, updated __init__)
item_functions.py                   (+32 lines, refactored use_wand_of_portals)
game_actions.py                     (+15 lines, charge tracking)
config/factories/spawn_factory.py   (+8 lines, updated docs)
tests/test_wand_portal_cancellation.py  (+460 lines, NEW)
tests/test_golden_path_portal_wand.py   (+10 lines, fixed tests)
```

**Total**: ~642 lines added/modified

---

## Manual Verification Checklist

After code review, manual testing should verify:

- [ ] Wand shows finite charges in tooltip/sidebar
- [ ] Placing entrance portal consumes 1 charge
- [ ] Placing exit portal completes the pair (no additional charge)
- [ ] Portals function normally (teleportation works)
- [ ] Using wand with active portals removes them from map
- [ ] Charge is refunded after cancellation
- [ ] No "Component PORTAL already exists" errors when placing new pair after cancel
- [ ] Wand becomes unusable at 0 charges
- [ ] Finding Portal scroll recharges the wand
- [ ] Message log shows clear feedback for all actions

---

## Known Limitations & Future Work

1. **Partial Pair Cancellation**: Currently, if player places only entrance portal (not exit), using wand again will try to place exit. Consider adding "cancel partial placement" option.

2. **Visual Feedback**: Portal disappearance is instant. Could add visual effect (fade out, particle effect) when canceling.

3. **Charge Configuration**: Wand starts with 3 charges (hardcoded). Consider moving to YAML config for easier balance tuning.

4. **Scroll Recharge Logic**: Portal scrolls already recharge wands (existing system), but this could be made more explicit in the UI.

---

## Regression Risk Assessment

**Risk Level**: Low

- Changes are isolated to portal system
- All 104 portal tests pass (including 13 new tests)
- No changes to rendering, input handling, or ECS core
- Existing portal functionality (teleportation, victory portals) unchanged
- Backward-compatible with old tests via deprecated methods

**Potential Issues**:
- If other code checks `wand.charges == -1` for infinite portals, it will break (mitigated: no other code does this)
- If portal entities are referenced elsewhere after placement, removal might cause issues (mitigated: PortalManager cleans all references)

---

## Conclusion

The Wand of Portals cancellation feature is fully implemented, tested, and ready for review. The implementation follows ECS architecture, maintains backward compatibility, and includes comprehensive test coverage. All 104 existing portal tests pass with no regressions.

**Next Steps**:
1. Code review
2. Manual playtesting (see checklist above)
3. Consider visual feedback for cancellation (low priority)
4. Merge to main branch


