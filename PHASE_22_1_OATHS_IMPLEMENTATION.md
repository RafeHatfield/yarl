# Phase 22.1: Run Identity via Oaths - Implementation Summary

**Status**: ✅ Complete  
**Date**: 2026-01-21  
**Tests**: All 3568 fast tests passing  

---

## Overview

Implemented **Run Identity via Oaths** - a system where players choose one of three permanent gameplay modifiers at run start that bias their playstyle through small, explicit mechanical changes.

**Design Principles**:
- Oaths are permanent status effects (duration = -1, never expire)
- Enforcement happens at canonical execution points (combat/damage/movement)
- Effects are small but measurable by floor 4-6
- System is deterministic under seed_base=1337
- Metrics track Oath selection and impact without double-counting

---

## What Was Implemented

### 1. Oath Status Effects (`components/status_effects.py`)

Added three new permanent status effect classes:

#### `OathEffect` (Base Class)
- Permanent status effect (duration = -1)
- Never decrements or expires
- Override `process_turn_end()` to prevent duration decrement

#### `OathOfEmbersEffect` (Fire Identity)
- **Effect**: 33% chance to apply burning (1 dmg/turn, 3 turns) on successful melee hit
- **Enforcement**: `Fighter.attack_d20()` (canonical combat execution point)
- **Metrics**: `oath_embers_chosen`, `oath_embers_procs`

#### `OathOfVenomEffect` (Poison Identity)
- **Effect**: 25% chance to apply poison (1 dmg/turn, 4 turns) on successful melee hit
- **Enforcement**: `Fighter.attack_d20()` (canonical combat execution point)
- **Metrics**: `oath_venom_chosen`, `oath_venom_procs`

#### `OathOfChainsEffect` (Knockback Identity)
- **Effect**: +1 tile to all knockback effects
- **Enforcement**: `knockback_service.calculate_knockback_distance()` (canonical knockback point)
- **Metrics**: `oath_chains_chosen`, `knockback_tiles_moved_by_player`

---

### 2. Oath Enforcement at Execution Points

#### Fighter.attack_d20() (`components/fighter.py`)
- Added `_apply_oath_effects()` method called after damage application
- Checks attacker for Oath of Embers or Venom
- Applies burning/poison based on RNG and Oath parameters
- Only applies for player attacks (no AI component)
- Tracks `oath_embers_procs` and `oath_venom_procs` metrics

#### Knockback Service (`services/knockback_service.py`)
- Modified `calculate_knockback_distance()` to accept optional `attacker_entity`
- Checks attacker for Oath of Chains
- Adds `+1` tile to knockback distance if Oath is active
- Defensive checks to handle mocked entities in tests
- Tracks `knockback_tiles_moved_by_player` when attacker is player

---

### 3. Metrics Infrastructure

#### RunMetrics (`services/scenario_harness.py`)
Added per-run metrics:
- `oath_embers_chosen: int`
- `oath_venom_chosen: int`
- `oath_chains_chosen: int`
- `oath_embers_procs: int` - times Embers applied burning
- `oath_venom_procs: int` - times Venom applied poison
- `knockback_tiles_moved_by_player: int` - tiles moved by player-caused knockback

#### AggregatedMetrics (`services/scenario_harness.py`)
Added aggregated metrics across multiple runs:
- `total_oath_embers_chosen: int`
- `total_oath_venom_chosen: int`
- `total_oath_chains_chosen: int`
- `total_oath_embers_procs: int`
- `total_oath_venom_procs: int`
- `total_knockback_tiles_moved_by_player: int`

All metrics properly serialized in `to_dict()` methods and aggregated in scenario runs.

---

### 4. Oath Selection System

#### Scenario Level Loader (`services/scenario_level_loader.py`)
- Added `_apply_player_oath()` function
- Reads `oath` key from player config in scenario YAML
- Valid values: `"embers"`, `"venom"`, `"chains"`
- Creates and applies appropriate Oath status effect to player
- Ensures player has `STATUS_EFFECTS` component before applying

Example scenario YAML:
```yaml
player:
  oath: "embers"  # Phase 22.1: Apply Oath of Embers
  position: [3, 7]
  inventory:
    - type: "healing_potion"
      count: 2
```

#### Initialize New Game (`loader_functions/initialize_new_game.py`)
- Added comment placeholder for Oath selection
- No Oath applied by default in normal gameplay
- Future: Can add UI selection for non-scenario runs

---

### 5. Identity Scenarios

Created three deterministic test scenarios:

#### `scenario_oath_embers_identity.yaml`
- Player with Oath of Embers
- 3 orcs in arena
- 2 healing potions
- Demonstrates burning proc rate and damage contribution

#### `scenario_oath_venom_identity.yaml`
- Player with Oath of Venom
- 3 orcs in arena
- 2 healing potions
- Demonstrates poison proc rate and damage contribution

#### `scenario_oath_chains_identity.yaml`
- Player with Oath of Chains
- 3 orcs in larger arena (20x15 for knockback space)
- Mace (knockback weapon) equipped
- 2 healing potions
- Demonstrates increased knockback distance (+1 tile)

All scenarios:
- Set `depth: 5` for consistent monster stats
- Use `tactical_fighter` bot persona
- Turn limit: 150
- Expected: 2+ kills, max 1 death
- Deterministic under `seed_base=1337`

---

## Architectural Compliance

✅ **Execution Points**: Oaths enforced at canonical points (Fighter.attack_d20, knockback_service)  
✅ **Status Effect Model**: Oaths are permanent status effects with proper lifecycle  
✅ **Determinism**: All RNG uses game's random.random() seeded by scenario harness  
✅ **Metrics API**: No double counting, metrics track at source of truth  
✅ **Non-Invasive**: No changes to TurnManager, Entity.move(), or balance baselines  

---

## Testing Results

- **Fast Test Suite**: 3568 tests passing (0 failures)
- **Linter**: No errors in modified files
- **Regression**: Fixed test compatibility issue with mocked entities in knockback tests

### Test Fix Applied
- `knockback_service.py`: Added defensive type checking for `knockback_bonus`
- Ensures `isinstance(bonus, int)` before adding to distance
- Handles mocked entities gracefully in unit tests

---

## Files Modified

1. `components/status_effects.py` - Oath status effect classes
2. `components/fighter.py` - Oath enforcement in combat
3. `services/knockback_service.py` - Oath enforcement in knockback
4. `services/scenario_harness.py` - Oath metrics (RunMetrics, AggregatedMetrics)
5. `services/scenario_level_loader.py` - Oath application from scenario config
6. `loader_functions/initialize_new_game.py` - Oath selection placeholder

## Files Created

1. `config/levels/scenario_oath_embers_identity.yaml`
2. `config/levels/scenario_oath_venom_identity.yaml`
3. `config/levels/scenario_oath_chains_identity.yaml`
4. `PHASE_22_1_OATHS_IMPLEMENTATION.md` (this file)

---

## Usage Examples

### Running Oath Scenarios

```bash
# Run Oath of Embers scenario (5 runs)
python3 -m ecosystem_sanity --scenario oath_embers_identity --runs 5 --seed 1337

# Run Oath of Venom scenario (5 runs)
python3 -m ecosystem_sanity --scenario oath_venom_identity --runs 5 --seed 1337

# Run Oath of Chains scenario (5 runs)
python3 -m ecosystem_sanity --scenario oath_chains_identity --runs 5 --seed 1337
```

### Verifying Metrics

Metrics are tracked in scenario output JSON:
- `oath_embers_chosen`: Should be 1 per run with Embers Oath
- `oath_embers_procs`: Number of times burning was applied
- `burning_damage_dealt`: Total burning DOT damage (separate metric)
- `knockback_tiles_moved_by_player`: Tiles moved by player knockback

---

## Design Rationale

### Why Permanent Status Effects?
- Leverages existing status effect infrastructure
- Guarantees persistence across entire run
- Easy to check at execution points via `status_effects.get_effect()`
- No special-case code needed for "run-long" modifiers

### Why These Three Oaths?
- **Embers**: Builds on existing burning DOT system
- **Venom**: Builds on existing poison DOT system
- **Chains**: Builds on existing knockback system
- All three leverage Phase 20+ DOT/mechanics infrastructure
- Small proc chances (25-33%) are noticeable but not overwhelming
- Each biases different playstyle (damage-over-time vs positioning)

### Why Scenario-Based Selection?
- Cleaner initial implementation (no UI needed)
- Easy to test deterministically
- Can add UI selection later for normal gameplay
- Scenarios demonstrate measurable impact on gameplay

---

## Future Enhancements

### Short Term
1. Add UI selection menu at run start for normal gameplay
2. Add more Oaths (e.g., life steal, crit bonus, dodge bonus)
3. Add Oath synergy with existing items/equipment

### Long Term
1. Multi-Oath system (choose 2-3 minor Oaths)
2. Oath progression (unlock more powerful versions by floor 10+)
3. Oath-specific items/equipment
4. Oath achievements/unlocks

---

## Known Limitations

1. **No UI Selection**: Oaths only work in scenarios currently (not in normal gameplay)
2. **Fixed Parameters**: Oath effects are hardcoded (not configurable per scenario)
3. **Player Only**: Oaths only apply to player, not monsters
4. **No Stacking**: Only one Oath can be active per run

All limitations are by design for Phase 22.1 and can be addressed in future phases.

---

## Verification Checklist

- [x] Oath status effects created with proper lifecycle
- [x] Enforcement at canonical execution points (Fighter.attack_d20, knockback_service)
- [x] Metrics added to RunMetrics and AggregatedMetrics
- [x] Scenario loader supports Oath application
- [x] Three identity scenarios created and tested
- [x] All fast tests passing (3568 tests)
- [x] No linter errors
- [x] Deterministic under seed_base=1337
- [x] No changes to TurnManager, Entity.move(), or balance baselines
- [x] Documentation complete

---

**Phase 22.1 Complete** ✅
