# Player Death Finalization Fix

## Bug Description

**Issue:** Player can reach HP == 0 and remain alive and able to act in scenario tests.

**Observed Behavior:**
- UI shows HP: 0/56
- Death message appears in log
- Gameplay continues (player can still move/act)

## Root Cause Analysis

### Death Pathways Investigated

1. **Combat damage** (`Fighter.attack_d20` → `take_damage` → `_handle_entity_death`)
   - ✅ Properly finalizes death
   - Sets `GameStates.PLAYER_DEAD`
   - Prevents further player actions

2. **Damage service** (`apply_damage` → `_handle_damage_death` → `finalize_player_death`)
   - ✅ Properly finalizes death when `state_manager` is provided
   - Routes to `engine_integration.finalize_player_death()`
   - Sets `GameStates.PLAYER_DEAD`

3. **DOT effects** (poison, burning via `damage_service.apply_damage`)
   - ✅ Properly finalizes death IF `state_manager` is passed
   - ❌ **BUG:** Clamps damage to non-lethal (leaves player at 1 HP) when `state_manager=None`

4. **Scenario harness** (`services/scenario_harness.py`)
   - ❌ **BUG:** Passed `state_manager=None` to status effects (line 919)
   - This caused DOT damage to be clamped instead of killing the player

### Critical Code Path

In `components/status_effects.py`, `PoisonEffect.process_turn_start()`:

```python
if state_manager:
    # Route through damage_service for proper death finalization
    damage_results = apply_damage(
        state_manager=state_manager,
        target_entity=self.owner,
        amount=damage_this_tick,
        cause="poison_dot",
        ...
    )
else:
    # FALLBACK: state_manager not available
    # CLAMP TO NON-LETHAL to prevent death without finalization
    if current_hp - damage_this_tick <= 0:
        clamped_damage = max(0, current_hp - 1)  # Leave at 1 HP
        logger.error("⚠️ POISON_LETHAL_CLAMP: ...")
```

The same pattern exists in `BurningEffect` and other DOT effects.

## Fix Implementation

### Changes Made

**File:** `services/scenario_harness.py`

1. **Create StateManager for harness** (line ~1038):
   ```python
   # Create a minimal StateManager for death finalization
   from state_management.state_config import StateManager
   state_manager = StateManager()
   state_manager.state = game_state
   ```

2. **Pass state_manager to enemy turn processing** (line ~1060):
   ```python
   _process_enemy_turn(game_state, metrics, state_manager=state_manager)
   ```

3. **Update `_process_enemy_turn` signature** (line ~838):
   ```python
   def _process_enemy_turn(game_state: Any, metrics: RunMetrics, state_manager=None) -> None:
   ```

4. **Pass state_manager to status effect processing** (line ~896):
   ```python
   _process_player_status_effects_harness(game_state, state_manager=state_manager)
   ```

5. **Update `_process_player_status_effects_harness` signature** (line ~902):
   ```python
   def _process_player_status_effects_harness(game_state: Any, state_manager=None) -> None:
   ```

6. **Use state_manager in status effect processing** (line ~917):
   ```python
   status_results = player.status_effects.process_turn_start(
       entities=game_state.entities,
       state_manager=state_manager  # CRITICAL: Enables proper death finalization
   )
   ```

### Why This Works

1. **DOT effects now have state_manager**: They can call `damage_service.apply_damage()` which properly finalizes death
2. **Death finalization is centralized**: `damage_service` → `_finalize_player_damage_death` → `engine_integration.finalize_player_death`
3. **Game state is set correctly**: `GameStates.PLAYER_DEAD` is set, preventing further player actions
4. **No more "undead limbo"**: Player cannot survive at 0 HP or be clamped to 1 HP from lethal DOT damage

## Testing

### Tests Run

1. **Unit tests**: `pytest -m "not slow"` - ✅ PASS
2. **Scenario harness tests**: `tests/unit/test_scenario_harness_basic.py` - ✅ PASS (28/28)
3. **Poison scenario**: `tests/integration/test_cave_spider_poison_identity_scenario_metrics.py` - ✅ PASS (2/2)
4. **Balance suite**: `make balance-suite-fast` - ✅ PASS (38/38 scenarios)

### Verification

- DOT effects can now properly kill the player in scenario tests
- Player death is finalized exactly once
- Game state transitions to `PLAYER_DEAD`
- Player cannot take actions after death (movement blocked by `StateManager.allows_movement()`)
- No regressions in existing scenarios

## Design Principles Maintained

1. **Single source of truth**: `damage_service.apply_damage()` is the canonical way to apply non-combat damage
2. **Death finalization contract**: All damage sources must route through proper death finalization
3. **State management**: `GameStates.PLAYER_DEAD` prevents further player actions
4. **Determinism**: No changes to game logic or balance
5. **Minimal changes**: Only added state_manager to scenario harness, no changes to core game loop

## Related Code

- `services/damage_service.py`: Canonical damage application with death finalization
- `engine_integration.py`: `finalize_player_death()` sets game state and handles metrics
- `components/status_effects.py`: DOT effects route through damage_service when state_manager available
- `state_management/state_config.py`: `GameStates.PLAYER_DEAD` configuration
- `game_actions.py`: `_handle_entity_death()` for combat deaths

## Future Considerations

- Main game loop already passes state_manager correctly (no changes needed)
- Any future test harnesses should also provide state_manager to status effects
- The "lethal clamp" fallback in DOT effects serves as a safety net for unit tests
- Consider adding explicit tests for player death finalization in various scenarios
