# Release Notes - v4.18.0

**Release Date**: January 12, 2026  
**Tag**: v4.18.0  
**Commit**: b8c1960

## Phase 21: Complete Trap Framework + Hazards Suite + Counterplay

This release introduces a comprehensive trap system with 7 trap types, an environmental hazards test suite, and trap counterplay mechanics (detection and disarm).

---

## New Features

### Trap Types (6 Floor Traps + 1 Chest Trap)

#### Floor Traps (Trigger on Tile Entry)

1. **Root Trap** (Phase 21.1)
   - Applies EntangledEffect that blocks movement for 3 turns
   - Visual: `~` (green vines)
   - Counterplay: Detect and avoid/disarm

2. **Spike Trap** (Phase 21.2)
   - Deals 7 damage + bleed effect
   - Damage routes through canonical damage_service
   - Visual: `^` (red spikes)
   - Counterplay: Detect and avoid/disarm

3. **Teleport Trap** (Phase 21.3)
   - Randomly teleports entity to valid tile on same level
   - Uses deterministic RNG (reproducible under same seed)
   - Visual: `T` (blue-violet arcane sigil)
   - Counterplay: Detect and avoid/disarm

4. **Gas Trap** (Phase 21.4)
   - Applies PoisonEffect (6 turns, 1 damage/turn)
   - DOT damage routes through status effect lifecycle
   - Visual: `G` (light green gas)
   - Counterplay: Detect and avoid/disarm

5. **Fire Trap** (Phase 21.4)
   - Applies BurningEffect (4 turns, 1 damage/turn)
   - DOT damage routes through status effect lifecycle
   - Visual: `F` (orange-red flames)
   - Counterplay: Detect and avoid/disarm

6. **Hole Trap** (Phase 21.5)
   - Causes fall to next dungeon level
   - Uses TransitionRequest mechanism for canonical level transition
   - Visual: `O` (dark gray pit)
   - Counterplay: Detect and avoid/disarm

#### Chest Traps (Trigger on Chest Open)

7. **Trapped Chest (Spike)** (Phase 21.6)
   - Chest contains spike trap payload
   - Deals 5 damage when opened (less than floor spikes)
   - Trap triggers once, chest becomes inert
   - Visual: `C` (dark brown chest)
   - Counterplay: Detect before opening (future)

### Trap Counterplay Mechanics (Phase 21.7)

#### Detection
- **Passive Detection**: Chance to notice traps in adjacent 8 tiles after movement
- **Active Search**: Press 's' to search room for hidden traps and secret doors
- **Detection Chance**: Configurable per trap type (0.08-0.15 base)
- Detected traps render with their trap glyph instead of floor tile

#### Disarm
- **Disarm Action**: Press 'x' to disarm revealed trap in adjacent tile
- **Success**: Deterministic success for thin slice (no skill roll yet)
- **Effect**: Disarmed traps become inert, render as 'x'
- **Avoidance**: Detected traps are automatically avoided when stepped on

### Environmental Hazards Suite

New test suite for environmental mechanics (separate from ecology-focused balance suite):

**Suite Runner**: `make hazards-suite` or `make hazards-suite-fast`

**9 Identity Scenarios** (all deterministic, seed_base=1337):
1. `trap_root_identity` - Root trap entangle mechanics
2. `trap_spike_identity` - Spike trap damage routing
3. `trap_teleport_identity` - Teleport trap RNG determinism
4. `trap_gas_identity` - Gas trap poison application
5. `trap_fire_identity` - Fire trap burning application
6. `trap_hole_identity` - Hole trap level transition
7. `trapped_chest_spike_identity` - Chest trap payload execution
8. `trap_detect_identity` - Passive trap detection
9. `trap_disarm_identity` - Trap disarm mechanics

**Suite Features**:
- Deterministic execution (seed_base=1337)
- Fast feedback (~30 runs per scenario)
- JSON + summary reports
- Suite doctrine: tags decide membership, list decides ordering
- Validation test ensures list stays in sync with tags

---

## Technical Implementation

### Architecture Principles

All trap mechanics follow canonical execution paths:

- **Damage**: Routes through `damage_service.apply_damage()`
- **Status Effects**: Routes through `StatusEffectManager`
- **Teleportation**: Direct x/y assignment at canonical execution point
- **Level Transitions**: `TransitionRequest` → `game_map.next_floor()`
- **Metrics**: Single source of truth via `ScenarioMetricsCollector`

### TransitionRequest Mechanism (Phase 21.5)

New lightweight mechanism for requesting level transitions:

```python
from services.transition_service import get_transition_service

# At trap trigger point:
transition_service.request_transition("next_floor", "hole_trap", entity)

# In gameplay loop (after movement):
if transition_service.has_pending_transition():
    request = transition_service.consume_transition()
    entities = game_map.next_floor(player, message_log, constants)
```

**Benefits**:
- Decouples trap trigger from transition execution
- Testable without multi-level scenario support
- Maintains single canonical transition path
- Resolved universally after any movement

### Trap Metrics

All trap actions tracked via single source of truth:

**Floor Traps**:
- `traps_triggered_total` (shared counter)
- Per-type: `trap_root_triggered`, `trap_spike_triggered`, etc.
- Damage: `trap_spike_damage_total`
- Effects: `trap_root_effects_applied`, `trap_gas_effects_applied`, etc.
- Transitions: `trap_hole_transition_requested`

**Chest Traps**:
- `chest_traps_triggered_total`
- `chest_trap_spike_triggered`
- `chest_trap_spike_damage_total`

**Counterplay**:
- `traps_detected_total`
- `trap_disarms_attempted`
- `trap_disarms_succeeded`

---

## Testing

### Test Coverage

- **Total Tests**: 3,475 passing (all fast tests)
- **New Tests**: ~60 trap-specific tests
- **Test Files**: 9 new test files
- **Scenarios**: 9 identity scenarios

### Verification

✅ All fast tests passing (`pytest -m "not slow"`)  
✅ All hazards suite scenarios passing (9/9)  
✅ All balance suite scenarios passing (38/38, no baseline changes)  
✅ All ecosystem_sanity checks passing  
✅ Deterministic under seed_base=1337  

---

## Gameplay Impact

### New Mechanics

- **Environmental Hazards**: 6 new trap types add variety and danger
- **Trap Counterplay**: Detection and disarm add tactical depth
- **Trapped Chests**: Loot containers can be dangerous
- **Level Transitions**: Hole traps create unexpected floor changes

### Balance

- Trap damage balanced against player HP pools
- Detection chances tuned per trap type (0.08-0.15)
- Disarm is deterministic success (no frustration)
- Detected traps are automatically avoided

### Controls

- **'s' key**: Search for hidden traps and secret doors (existing)
- **'x' key**: Disarm revealed trap in adjacent tile (new)

---

## Files Changed

### Created (18 files)
- 9 scenario YAML files (`config/levels/scenario_trap_*.yaml`)
- 9 test files (`tests/test_trap_*.py`, `tests/test_hazards_suite.py`)
- 1 service (`services/transition_service.py`)
- 1 tool (`tools/hazards_suite.py`)

### Modified (27 files)
- Core trap logic: `components/trap.py`, `services/movement_service.py`
- Action handling: `game_actions.py`, `input_handlers.py`
- Chest traps: `components/chest.py`
- Metrics: `services/scenario_harness.py`
- Scenario loading: `services/scenario_level_loader.py`, `services/scenario_invariants.py`
- Entity definitions: `config/entities.yaml`
- Suite infrastructure: `config/level_template_registry.py`, `Makefile`
- Various AI and spell files (minor updates)

---

## Known Design Decisions

### Detected Traps Are Avoided

When a trap is detected (revealed), the player automatically avoids it when stepping on that tile. This is an intentional design choice that makes detection valuable without requiring disarm.

**Trap Behavior**:
- Hidden trap + stepped on = triggers
- Detected trap + stepped on = avoided (message shown)
- Disarmed trap + stepped on = safe (no message)

**Rationale**: Gentler gameplay that rewards detection. Disarm is still useful for clearing paths and preventing accidental triggers during combat.

### RNG Doctrine

Teleport trap uses Python's global `random.choice()` after `set_global_seed()`, which is consistent with the project's RNG pattern. All trap mechanics are deterministic under the same seed.

---

## Future Enhancements

Potential future additions (not in this release):

- Skill-based disarm rolls (rogue/dexterity checks)
- Lockpicks and tools for disarming
- More chest trap payloads (gas, fire, teleport, hole)
- LOS/proximity triggers (alarm traps that trigger on sight)
- Trap crafting/placement by player
- Trap damage scaling by dungeon depth

---

## Compatibility

- **Save Game**: Compatible (new trap types added, no breaking changes)
- **Mods**: New trap types available for custom scenarios
- **Balance**: No changes to existing balance suite baselines

---

## Credits

**Phase 21 Development**: Complete trap framework implementation  
**Architecture**: Canonical execution paths, single-sourced metrics  
**Testing**: Comprehensive identity scenarios, hazards suite infrastructure  

---

## Upgrade Notes

No special upgrade steps required. New trap types will appear in dungeon generation automatically based on existing trap_rules configuration in level templates.

To use the hazards suite:
```bash
make hazards-suite        # Full run
make hazards-suite-fast   # Quick run
```

To test specific trap scenarios:
```bash
python3 ecosystem_sanity.py --scenario trap_spike_identity
```

---

**Full Changelog**: v4.17.0...v4.18.0
