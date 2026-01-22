# Oath Implementation Notes

## Determinism Doctrine

**Rule**: All gameplay RNG MUST use Python's global `random` module, which is seeded by the scenario harness.

**Why**: This ensures scenarios are reproducible under fixed seeds (e.g., `seed_base=1337`).

**How It Works**:
1. `services/scenario_harness.py` line 1192-1194 calls `set_global_seed(run_seed)` before each run
2. `engine/rng_config.py` line 57 seeds Python's `random` module
3. All Oath proc rolls use `random.random()` (not a custom RNG)
4. Anti-regression test verifies determinism: `tests/test_oath_invariants.py::TestOathDeterminism`

**Enforcement**:
- ✅ Oath effects use `import random` then `random.random()`
- ✅ Scenario harness seeds before each run
- ✅ Tests verify same seed → same procs

**Violation Prevention**:
- DO NOT use `random.Random()` instances in gameplay code (breaks seeding)
- DO NOT use non-Python RNG (numpy, etc.) without explicit seeding
- DO run anti-regression tests after any RNG changes

---

## Movement Tracking for Oath of Chains

**Design**: Oath of Chains tracks **voluntary movement** to create positioning decisions.

### What Counts as Movement
- ✅ **Voluntary**: Walking, pathfinding, auto-explore → calls `Entity.move()` → sets `moved_last_turn = True`
- ❌ **Involuntary**: Teleports, knockback → direct x/y assignment → doesn't set flag

### Reset Semantics
- **Single canonical reset**: `Entity.process_status_effects_turn_start()` line 795
- Resets `moved_last_turn = False` at start of each entity's turn
- No ad-hoc resets scattered around codebase

### Why This Matters
- **Correct**: Teleport traps shouldn't disable Oath bonus (involuntary)
- **Predictable**: Single reset point prevents timing bugs
- **Intentional**: Tracks player's positioning *choices*, not forced displacement

### Code Locations
- Flag definition: `entity.py` line 136
- Flag set: `entity.py` line 379 (in `move()` method)
- Flag reset: `entity.py` line 795 (in `process_status_effects_turn_start()`)
- Flag check: `services/knockback_service.py` line 53 (Chains conditional)

### Teleport Implementations (verified to bypass move())
- Teleport trap: `services/movement_service.py` line 614-615
- Teleport scroll: `item_functions.py` line 395-396
- Teleport spell: `spells/spell_executor.py` line 786
- Portal: `services/portal_manager.py` line 209-210
- Portal (component): `components/portal.py` line 144-145

---

## Oath Effect Execution Order

**Critical**: Oath effects fire AFTER knockback resolution (line 1293 in `fighter.py`).

**Why**: This is a tactical feature for Embers self-burn:
- Hit lands → damage applied → knockback occurs → Oath checks adjacency
- If knockback opened space, player avoids self-burn (rewards tactical play)
- If still adjacent, player takes self-burn (risk of staying in melee)

**Order**:
1. Hit confirmation (d20 vs AC)
2. Base damage calculation
3. `take_damage()` applied
4. On-hit effects (corrosion, engulf, etc.)
5. **Weapon knockback** ← happens here
6. **Oath effects** ← adjacency check happens here
7. Combat flags

---

## Anti-Regression Invariants

### What We Test (`tests/test_oath_invariants.py`)
1. **Permanence**: Oaths never expire (duration = -1, no decrement)
2. **Player-Only**: Oath effects only apply to entities without AI component
3. **Determinism**: Same seed → identical proc counts
4. **Movement Constraint**: Chains bonus respects `moved_last_turn` flag

### When to Run
- After ANY changes to:
  - Oath status effects
  - Fighter combat logic
  - Knockback service
  - Entity movement
  - RNG seeding

### How to Run
```bash
pytest tests/test_oath_invariants.py -xvs
```

---

## Metrics Without Double-Counting

### Oath-Specific Metrics
- `oath_embers_procs`: Times Embers applied burning to enemy
- `oath_embers_self_burn_procs`: Times Embers applied burning to self
- `oath_venom_procs`: Times Venom applied/extended poison
- `oath_venom_duration_extensions`: Times duration was extended (focus-fire proof)
- `oath_chains_bonus_applied`: Times knockback bonus was active
- `oath_chains_bonus_denied`: Times bonus was denied by movement

### Relationship to Existing Metrics
- `burning_damage_dealt`: Tracks ALL burning damage (Oath + monsters + fire beetles)
- `poison_damage_dealt`: Tracks ALL poison damage (Oath + spiders)
- `knockback_tiles_moved`: Tracks ALL knockback movement
- `knockback_tiles_moved_by_player`: Tracks player-caused knockback only (NEW in 22.1)

**No Double-Counting**: Oath metrics track *application*, existing metrics track *outcome*.

---

## Future Considerations

### Phase 22.2: Ranged Doctrine
- Oaths will need enforcement in ranged attack paths
- Same execution point pattern: after damage, before cleanup
- Movement tracking already works for Chains (voluntary movement)

### UI Selection
- Currently: Oaths set via scenario YAML (`player.oath: "embers"`)
- Future: Add start-of-run selection menu (see `loader_functions/initialize_new_game.py` line 219)
- Keep scenario override for testing

### Additional Oaths
- Same pattern: permanent StatusEffect + enforcement at execution points
- Must define decision lever (not just output multiplier)
- Add anti-regression test to `test_oath_invariants.py`

---

**Last Updated**: Phase 22.1.1  
**Maintainer**: Engineering team
