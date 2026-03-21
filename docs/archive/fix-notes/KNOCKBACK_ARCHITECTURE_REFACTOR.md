# Knockback Architecture Refactor - Canonical Execution Path

## Problem

Initial implementation used "split service pattern" where Fighter returned knockback data and callers (game_actions.py, scenario_harness.py) executed it. This was architecturally incorrect:

- ❌ Knockback execution in harness-side postprocessor (not production combat path)
- ❌ Dual execution points (game_actions + scenario_harness)
- ❌ Combat consequence handled outside combat system

## Solution

**Canonical execution in Fighter.attack_d20()** - Knockback executes immediately after successful hit, inside the combat system.

### Design

Add optional `game_map` and `entities` parameters to `Fighter.attack_d20()`:
```python
def attack_d20(self, target, is_surprise: bool = False, game_map=None, entities=None):
```

**Execution point**: Inside hit branch, after damage/effects applied
- Same location as poison/burning/slow weapon effects
- Executes if `game_map` and `entities` provided
- Gracefully skips if not provided (backward compat for tests)

**Callers pass game_map/entities**:
- `game_actions.py`: Has `self.state_manager.state.game_map/entities`
- `scenario_harness.py`: Has `game_state.game_map/entities`
- `mouse_movement.py`: Has `game_map/entities` parameters

## Refactor Diff

### 1. Fighter.attack_d20() Signature

**Before:**
```python
def attack_d20(self, target, is_surprise: bool = False):
```

**After:**
```python
def attack_d20(self, target, is_surprise: bool = False, game_map=None, entities=None):
```

### 2. Fighter Knockback Method

**Before (split pattern):**
```python
def _check_weapon_knockback_trigger(self, target):
    # ... check weapon flag ...
    return {"attacker": self.owner, "defender": target}  # Return data
```

**After (direct execution):**
```python
def _apply_weapon_knockback_on_hit(self, target, game_map, entities):
    # ... check weapon flag ...
    from services.knockback_service import apply_knockback
    knockback_results = apply_knockback(attacker, defender, game_map, entities)
    return knockback_results  # Return results, not data
```

### 3. Fighter Hit Branch

**Before:**
```python
knockback_data = self._check_weapon_knockback_trigger(target)
if knockback_data:
    results.append({"knockback": knockback_data})  # Return for caller
```

**After:**
```python
if game_map and entities:
    knockback_results = self._apply_weapon_knockback_on_hit(target, game_map, entities)
    results.extend(knockback_results)  # Execute directly
```

### 4. Callers Updated

**game_actions.py:**
```python
# Before
attack_results = attacker_fighter.attack_d20(target, is_surprise=is_surprise_attack)

# After
attack_results = attacker_fighter.attack_d20(
    target, 
    is_surprise=is_surprise_attack,
    game_map=self.state_manager.state.game_map,
    entities=self.state_manager.state.entities
)
```

**scenario_harness.py (2 call sites):**
```python
# Before
attack_results = player_fighter.attack_d20(target, is_surprise=is_surprise)

# After
attack_results = player_fighter.attack_d20(
    target, 
    is_surprise=is_surprise,
    game_map=game_state.game_map,
    entities=game_state.entities
)
```

**mouse_movement.py:**
```python
# Before
def _handle_enemy_click(player, target, results):
    attack_results = player.fighter.attack_d20(target)

# After
def _handle_enemy_click(player, target, results, game_map, entities):
    attack_results = player.fighter.attack_d20(target, game_map=game_map, entities=entities)
```

### 5. Removed Postprocessing

**game_actions.py - REMOVED:**
```python
# Handle weapon knockback (weapon knockback pattern)
knockback_data = result.get("knockback")
if knockback_data:
    # Execute knockback with game_map/entities
    ...
```

**scenario_harness.py - REMOVED:**
```python
# Handle knockback (weapon knockback pattern)
knockback_data = result.get("knockback")
if knockback_data:
    # Execute knockback with game_map/entities
    ...
```

## Canonical Execution Path

```
Player/Monster Attack
    ↓
Fighter.attack_d20(target, game_map=..., entities=...)
    ↓
[Hit branch]
    ↓
Apply damage
    ↓
Apply poison/burning/slow (monster abilities)
    ↓
Apply weapon poison (player weapon)
    ↓
Apply weapon knockback (player + monster weapon)  ← CANONICAL EXECUTION
    ↓
knockback_service.apply_knockback()
    ↓
Metrics incremented (single source of truth)
    ↓
Return results to caller
```

**Single execution point**: `Fighter.attack_d20()` line ~1258
**Single metrics source**: `knockback_service.apply_knockback()`
**Works for**: Real gameplay, scenario harness, bot mode, mouse clicks

## Files Modified

1. `components/fighter.py` - Added game_map/entities params, execute knockback directly
2. `game_actions.py` - Pass game_map/entities, removed postprocessing
3. `services/scenario_harness.py` - Pass game_map/entities, removed postprocessing
4. `mouse_movement.py` - Pass game_map/entities through _handle_enemy_click

## Test Results

```bash
# Slow integration test
pytest -m slow tests/integration/test_knockback_weapon_identity_scenario_metrics.py
# Result: 1 passed ✅ (0.69s)

# Fast gate
pytest -m "not slow"
# Result: 3422 passed ✅ (2:16)
```

## Metrics Validation

```
knockback_applications: 298  (✓ >= 50)
knockback_tiles_moved: 559   (✓ >= 100)
knockback_blocked_events: 20 (✓ >= 10)
stagger_applications: 20     (✓ >= 10)
```

## Architectural Correctness

✅ **Knockback executes in production combat path** (Fighter.attack_d20)
✅ **Single execution point** (no dual paths)
✅ **Identical behavior** (real gameplay = scenario harness = bot mode)
✅ **Backward compatible** (game_map/entities optional, graceful degradation)
✅ **Single metrics source** (knockback_service only)

## Why This is Canonical

1. **Execution in Fighter**: Combat consequences belong in the combat component
2. **Same layer as other effects**: Poison/burning/slow execute here
3. **Single code path**: All callers go through same Fighter.attack_d20()
4. **Optional parameters**: Doesn't break existing tests, graceful degradation
5. **No postprocessing**: Knockback happens immediately, not as deferred execution

---

**Architecture corrected. Ready for baselining.** 🎯

