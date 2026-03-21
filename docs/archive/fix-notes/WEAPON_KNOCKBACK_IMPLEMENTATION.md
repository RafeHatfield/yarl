# Weapon Knockback Implementation Summary

## Overview

Implemented weapon-based knockback with power-delta scaled distance (cap 4 tiles) and wall-impact micro-stun (Staggered effect). The system works for both player and monsters, uses canonical movement execution, and is fully deterministic under scenario harness seeding.

## Design

### Distance Mapping (Power Delta → Tiles)

```
delta = attacker_power - defender_power

delta <= -1     → 1 tile
delta in [0, 1] → 2 tiles
delta in [2, 3] → 3 tiles
delta >= 4      → 4 tiles (cap)
```

### Stagger Micro-Stun

- **Applied when**: Knockback blocked early by hard obstacle (wall/solid tile/occupied)
- **Duration**: 1 turn (refresh-not-stack)
- **Effect**: Skip next action/turn
- **No damage**: Wall impact does not deal damage in this phase
- **No chain effects**: Only the shoved entity is staggered (not the blocker)
- **Message clarity**:
  - Wall impact: "X slams into the wall and is staggered!"
  - Entity collision: "X collides with Y and is staggered!"

### Weapon Delivery

- **Flag**: `applies_knockback_on_hit: true` in weapon YAML
- **Trigger**: Successful melee hit (same place poison/burning weapon hooks live)
- **Scope**: Player + monsters (no faction gating)

### Movement Execution

- Uses canonical `Entity.move()` via `knockback_service._execute_move()`
- Respects entangle/root and all future movement blockers
- No direct x/y assignment bypass

## Files Changed

### Core Implementation

1. **`components/status_effects.py`**
   - Added `StaggeredEffect` class (1-turn micro-stun)
   - Metrics: `stagger_applications`, `stagger_turns_skipped`

2. **`services/knockback_service.py`** (NEW)
   - `calculate_knockback_distance()`: Power delta → distance mapping
   - `apply_knockback()`: Knockback resolution with stagger logic
   - `_can_move_to()`: Hard block check (wall/occupied)
   - `_execute_move()`: Canonical movement execution wrapper
   - Metrics: `knockback_applications`, `knockback_tiles_moved`, `knockback_blocked_events`

3. **`components/fighter.py`**
   - Added `_apply_weapon_knockback_on_hit()` hook in `attack_d20()` after successful hit
   - Calls `knockback_service.apply_knockback()` if weapon has flag

### Configuration Plumbing

4. **`config/entity_registry.py`**
   - Added `applies_knockback_on_hit: bool` field to `WeaponDefinition`
   - Piped through `_process_weapons_with_inheritance()`

5. **`components/equippable.py`**
   - Added `applies_knockback_on_hit: bool` field to `Equippable.__init__()`
   - Stored as instance attribute

6. **`config/entities.yaml`**
   - Added `knockback_mace` weapon (extends `mace`)
   - `applies_knockback_on_hit: true`
   - Bronze/copper color `[150, 100, 50]`

### Testing

7. **`config/levels/scenario_knockback_weapon_identity.yaml`** (NEW)
   - Identity scenario: 2 weak orcs, 1 strong orc, 2 trolls near walls, 1 blocker orc
   - Player starts with dagger, must pick up knockback mace
   - 15x11 arena with enclosed walls
   - 30 runs, 100 turn limit
   - Tests both wall-impact and entity-collision stagger

8. **`tests/integration/test_knockback_weapon_identity_scenario_metrics.py`** (NEW)
   - Slow integration test (30 runs, deterministic)
   - Lower-bound invariants (avoid flakiness from kill ordering):
     - `knockback_applications >= 20`
     - `knockback_tiles_moved >= 20`
     - `knockback_blocked_events >= 5`
     - `stagger_applications >= 5`
     - `stagger_turns_skipped >= 5`
     - `player_deaths <= 20` (sanity check only, generous upper bound)

9. **`tests/test_knockback_service.py`** (NEW)
   - Unit tests for distance mapping (4 tests)
   - Unit tests for stagger application (2 tests)
   - Unit test for canonical movement execution (1 test)
   - **All 7 tests pass**

10. **`tools/balance_suite.py`**
    - Added `knockback_weapon_identity` to scenario matrix (30 runs, 100 turns)

## Metrics (Single Source of Truth)

### Knockback Metrics (knockback_service.py)

- `knockback_applications`: Incremented when knockback triggers on hit
- `knockback_tiles_moved`: Sum of tiles actually moved by knockback
- `knockback_blocked_events`: Count when push blocked before full distance

### Stagger Metrics (StaggeredEffect)

- `stagger_applications`: Incremented in `StaggeredEffect.apply()`
- `stagger_turns_skipped`: Incremented in `StaggeredEffect.process_turn_start()` when skip occurs

## Architectural Compliance

✅ **No TurnManager / action economy changes**
✅ **No global FOV computation changes**
✅ **Enforcement at movement execution point** (uses canonical `Entity.move()`)
✅ **No AI-only special casing** (works for player + monsters)
✅ **Deterministic under scenario harness seeding**
✅ **Small, localized edits** (no refactors of unrelated systems)

## Tests to Run

```bash
# Fast gate (unit tests)
pytest -m "not slow"

# Slow integration test (30 runs)
pytest -m slow tests/integration/test_knockback_weapon_identity_scenario_metrics.py

# Balance suite (optional)
make balance-suite-fast
```

## Sample Metrics (Expected from 30-run sample)

Based on scenario design:
- **knockback_applications**: 30-50 (player hits with knockback mace)
- **knockback_tiles_moved**: 60-120 (varies by power delta)
- **knockback_blocked_events**: 10-20 (wall impacts)
- **stagger_applications**: 10-20 (wall-impact stuns)
- **stagger_turns_skipped**: 10-20 (turns lost to stagger)
- **player_deaths**: 3-10 (reasonable death rate)

## Future Extensions (Out of Scope)

- Damage-on-impact (wall slam damage)
- Knockback potions/scrolls
- Knockback resistance stat
- Knockback direction control (cone/line effects)
- Multi-tile entity knockback (large creatures)

## Notes

- **No existing scenario geometry modified**: All changes are additive
- **No baseline changes**: New scenario has its own baseline entry
- **Weapon flag is opt-in**: Existing weapons unaffected
- **Stagger is minimal**: 1-turn micro-stun, not a major debuff
- **Movement blockers respected**: Entangle/root prevent knockback movement
- **Hard obstacles only**: Stagger only on wall/solid/occupied, not on effect blocks

