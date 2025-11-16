# Bot Mode Phase 1: Auto-Exploration Implementation

**Date:** 2025-11-16  
**Status:** ✅ Complete  
**Branch:** `codex/fix-bot-mode-to-prevent-unresponsiveness`

---

## Summary

Implemented **Phase 1 bot behavior** that enables the bot to auto-explore the dungeon instead of just waiting every turn. This builds on the stable Phase 0 foundation (no hangs, AI disabled) by integrating with the existing auto-explore system.

### Key Achievement
The bot now **reuses the entire existing auto-explore infrastructure** instead of implementing its own movement logic. This ensures consistency with player auto-explore behavior and minimizes code duplication.

---

## Implementation Details

### 1. Where the Auto-Explore System Lives

**Core Component:**
- `components/auto_explore.py` - `AutoExplore` component (989 lines)
  - Uses Dijkstra pathfinding for optimal exploration paths
  - Room-by-room exploration strategy
  - Avoids ground hazards
  - Stops on threats (monsters, items, traps, damage, etc.)

**Integration Points:**
- `game_actions.py` - `ActionProcessor._handle_start_auto_explore()` (line 263)
  - Creates/activates AutoExplore component when `{'start_auto_explore': True}` action is received
- `game_actions.py` - `ActionProcessor._process_auto_explore_turn()` (line 333)
  - Called automatically each turn when auto-explore is active
  - Gets next move from `AutoExplore.get_next_action()` and executes it

**Keyboard Flow:**
1. Player presses 'o' → `input_handlers.py` line 162
2. Generates `{'start_auto_explore': True}` action
3. `ActionProcessor._handle_start_auto_explore()` initializes component
4. Each turn: `ActionProcessor._process_auto_explore_turn()` moves the player

---

### 2. Phase 1 Bot Behavior Design

**File:** `io_layer/bot_input.py`

**Strategy:**
```python
def next_action(self, game_state):
    # 1. Guard: Only act in PLAYERS_TURN
    if game_state.current_state != GameStates.PLAYERS_TURN:
        return {}
    
    # 2. Throttle actions (default: every frame)
    if counter < action_interval:
        return {}
    
    # 3. Check if auto-explore is already active
    auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
    if auto_explore and auto_explore.is_active():
        return {}  # Let ActionProcessor handle it
    
    # 4. Trigger auto-explore
    return {'start_auto_explore': True}
```

**Key Design Decisions:**
1. **Reuse existing infrastructure** - Bot emits the same `{'start_auto_explore': True}` action that keyboard players use
2. **Stateless delegation** - Once auto-explore is active, bot returns `{}` and lets `ActionProcessor._process_auto_explore_turn()` handle movement
3. **Auto-restart** - When auto-explore stops (e.g., monster found), bot re-triggers it on the next turn
4. **Defensive programming** - Handles missing player or malformed game state gracefully

**No Changes To:**
- Main game loop
- AISystem (enemies still disabled via Phase 0's `disable_enemy_ai_for_bot` flag)
- Render pipeline
- Auto-explore component itself

---

### 3. Differences from Phase 0

| Aspect | Phase 0 (Previous) | Phase 1 (Current) |
|--------|-------------------|-------------------|
| Bot action | `{'wait': True}` every turn | `{'start_auto_explore': True}` when not exploring |
| Movement | None (just waits) | Auto-explores the dungeon systematically |
| Pathfinding | N/A | Reuses `AutoExplore.get_next_action()` → `{'dx': dx, 'dy': dy}` |
| Enemy AI | Disabled (via AISystem flag) | **Still disabled** (Phase 0 constraint preserved) |
| Main loop | Unchanged | **Still unchanged** (as required) |

**Phase 0 Constraints Preserved:**
- `engine/systems/ai_system.py` still has bot-mode flag to disable enemy AI
- No changes to AISystem, TurnManager, or main game loop
- Bot input source doesn't modify enemy AI settings (documented in tests)

---

### 4. Files Modified

**Core Implementation:**
- `io_layer/bot_input.py` - 107 lines (was 93)
  - Added auto-explore triggering logic
  - Added defensive checks (hasattr for get_component_optional)
  - Preserved throttling and state guards

**Tests Added:**
- `tests/test_bot_mode_phase1_auto_explore.py` - 218 lines (NEW)
  - 14 comprehensive tests covering:
    - Auto-explore triggering when inactive
    - Empty action when auto-explore active
    - State transitions and edge cases
    - Phase 0 invariant preservation

**Tests Updated:**
- `tests/test_bot_mode_throttle.py` - Updated 6 tests
  - Changed expected actions from `{'wait': True}` → `{'start_auto_explore': True}`
  - Added mock player with `get_component_optional` method
- `tests/test_bot_mode_integration.py` - Updated 1 test
  - Same changes as above

**No Changes:**
- `engine/systems/ai_system.py` - Phase 0 enemy AI disabling preserved
- `game_actions.py` - Auto-explore handlers unchanged
- `components/auto_explore.py` - Component logic unchanged
- Main game loop - Untouched

---

### 5. Testing & Validation

**Unit Tests:**
```bash
$ pytest tests/test_bot_mode_phase1_auto_explore.py -v
# ✅ 14/14 tests passed

$ pytest tests/test_bot_mode*.py -v
# ✅ 55/55 tests passed (including all existing bot mode tests)

$ pytest tests/test_auto_explore.py -v
# ✅ 20/20 tests passed (auto-explore system still works correctly)
```

**Test Coverage:**
- ✅ Bot triggers auto-explore when not active
- ✅ Bot returns empty when auto-explore active
- ✅ Bot re-triggers auto-explore after it stops
- ✅ Action interval throttling works correctly
- ✅ State guards prevent actions in non-PLAYERS_TURN states
- ✅ Defensive handling of missing player/components
- ✅ Phase 0 invariants preserved (enemy AI still disabled)

**Manual Validation:**
```bash
$ python3 engine.py --bot
# ✅ Game starts without hanging
# ✅ Bot mode flag detected
# ✅ No crashes or errors
```

**Smoke Test Results:**
- No hangs or infinite loops
- No linter errors
- All existing bot mode tests updated and passing
- Auto-explore system tests unchanged and passing

---

### 6. How the Bot Now Behaves

**Turn-by-Turn Flow:**

```
Turn 1: [PLAYERS_TURN]
  → BotInputSource.next_action(game_state)
  → Check: auto-explore active? No
  → Return: {'start_auto_explore': True}
  → ActionProcessor._handle_start_auto_explore()
  → AutoExplore component created and started

Turn 2-N: [PLAYERS_TURN]
  → BotInputSource.next_action(game_state)
  → Check: auto-explore active? Yes
  → Return: {}
  → ActionProcessor._process_auto_explore_turn()
  → AutoExplore.get_next_action() → {'dx': 1, 'dy': 0}
  → Player moves east

Turn N+1: [PLAYERS_TURN]
  → AutoExplore.get_next_action() → None (stopped: "Monster spotted")
  → BotInputSource.next_action(game_state)
  → Check: auto-explore active? No (just stopped)
  → Return: {'start_auto_explore': True}
  → Auto-explore restarts (cycle continues)
```

**Stop Conditions (from AutoExplore):**
- Monster in FOV
- Valuable item found
- Chest discovered
- Secret door revealed
- Standing on stairs
- Took damage
- Has status effect
- All areas explored

When auto-explore stops, the bot **immediately re-triggers it** on the next turn (Phase 1 behavior). This creates a simple "explore until complete" bot.

---

### 7. Integration with Existing Systems

**Auto-Explore System:**
- ✅ Bot reuses `ActionProcessor._handle_start_auto_explore()`
- ✅ Bot reuses `ActionProcessor._process_auto_explore_turn()`
- ✅ Bot reuses `AutoExplore.get_next_action()` pathfinding
- ✅ Same stop conditions as keyboard auto-explore
- ✅ Same movement behavior (one tile per turn)

**Turn Management:**
- ✅ Bot only acts in PLAYERS_TURN (Phase 0 constraint)
- ✅ Empty `{}` actions are ignored by ActionProcessor
- ✅ No changes to turn transitions or state machine

**Enemy AI:**
- ✅ Phase 0's `disable_enemy_ai_for_bot` flag still active
- ✅ Enemies do NOT act in bot mode (as required)
- ✅ Bot doesn't touch AISystem or enemy logic

**Rendering:**
- ✅ ConsoleRenderer remains unchanged
- ✅ No changes to render pipeline or FOV updates
- ✅ Bot triggers same movement → FOV → render flow as player

---

### 8. Architecture Compliance

**Project Rules Compliance:**

✅ **ECS Boundaries:** Bot only emits action dicts; doesn't touch entities, components, or systems directly

✅ **Rendering Layer:** No changes to renderers (they remain read-only consumers)

✅ **Input Abstraction:** Bot correctly implements InputSource protocol

✅ **Main Loop:** No changes to the main game loop (as explicitly required)

✅ **Small Changes:** Only modified 3 files (bot_input.py, 2 test files updated)

✅ **Reuse Existing Patterns:** Fully reuses auto-explore system instead of creating new movement logic

✅ **Phase 0 Preservation:** Enemy AI still disabled; no changes to AISystem

**RLIKE Rules Followed:**
- Recon → Plan → Execute → Verify → Report workflow
- Small, focused, minimal changes
- Preserved existing auto-explore architecture
- No architectural drift or new patterns introduced
- Comprehensive testing (55 tests passing)

---

### 9. Known Limitations & Future Work

**Current Limitations (by design):**
- Enemies do not act (Phase 0 constraint, will be lifted in later phases)
- Bot always re-triggers auto-explore when it stops (no combat/item logic yet)
- No inventory management or item usage (future phases)
- No level transitions yet (future phases)

**Future Phases (Not Implemented):**
- **Phase 2:** Basic combat (attack nearby enemies)
- **Phase 3:** Item pickup and usage
- **Phase 4:** Level transitions (stairs)
- **Phase 5:** Smart item prioritization and inventory management

**Technical Debt:**
- None introduced; bot cleanly integrates with existing systems

---

### 10. Diff Summary

**Changes Made:**
```diff
io_layer/bot_input.py:
  - Removed: Trivial "wait every turn" logic
  + Added: Auto-explore triggering logic
  + Added: Defensive checks for player components
  + Added: Documentation for Phase 1 behavior

tests/test_bot_mode_phase1_auto_explore.py:
  + New file: 14 comprehensive tests (218 lines)

tests/test_bot_mode_throttle.py:
  ~ Updated: 6 tests to expect {'start_auto_explore': True}
  ~ Updated: Added mock player with get_component_optional

tests/test_bot_mode_integration.py:
  ~ Updated: 1 test to expect {'start_auto_explore': True}
  ~ Updated: Added mock player setup
```

**Lines Changed:**
- `bot_input.py`: +14 lines (93 → 107)
- New test file: +218 lines
- Updated tests: ~30 lines changed

**Total Complexity:** Minimal (leverages existing auto-explore system)

---

### 11. Verification Checklist

**Implementation:**
- ✅ Bot triggers auto-explore when not active
- ✅ Bot returns empty when auto-explore is active
- ✅ Bot re-triggers auto-explore when it stops
- ✅ Throttling mechanism works correctly
- ✅ State guards prevent actions in wrong states
- ✅ Defensive error handling for missing components

**Testing:**
- ✅ All 14 new Phase 1 tests passing
- ✅ All 55 bot mode tests passing
- ✅ All 20 auto-explore tests passing
- ✅ No linter errors
- ✅ Smoke test: game starts without hanging

**Architecture:**
- ✅ No changes to main game loop
- ✅ No changes to AISystem
- ✅ No changes to render pipeline
- ✅ Reuses existing auto-explore system
- ✅ Phase 0 constraints preserved

**Documentation:**
- ✅ Code comments updated
- ✅ Test docstrings clear and comprehensive
- ✅ This summary document created

---

## Conclusion

Phase 1 bot mode is **complete and stable**. The bot now auto-explores the dungeon using the same infrastructure as keyboard auto-explore, providing a solid foundation for future combat and item management phases.

**Next Steps:**
- User can now use `python3 engine.py --bot` to watch the bot explore
- Ready for Phase 2: Basic combat behavior (future PR)

**Maintainer Notes:**
- All tests passing (55/55 bot mode tests)
- No architectural changes to core systems
- Clean integration with existing auto-explore
- Well-tested and documented

