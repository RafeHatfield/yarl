# Phase 19: Necromancer Implementation

**Date:** 2026-01-01  
**Branch:** feature/phase19-necromancer-raise-and-corpse-seeking-ai  
**Status:** ✅ COMPLETE

---

## Overview

This document summarizes the implementation of the Necromancer enemy with corpse-focused gameplay: raise dead on cooldown, corpse-seeking movement with safety constraints, and hang-back AI behavior.

---

## Implementation Summary

### 1. Necromancer Entity (`config/entities.yaml`)

**Stats:**
- HP: 28 (moderate, support role)
- Power: 1 (very weak melee)
- Damage: 2-4 (avoid direct combat)
- Strength: 8, Dexterity: 14, Constitution: 12
- Faction: CULTIST
- ETP: 44 (controller with summons)

**Abilities:**
- `raise_dead_enabled: true`
- `raise_dead_range: 5`
- `raise_dead_cooldown_turns: 4`
- `danger_radius_from_player: 2`
- `preferred_distance_min: 4`
- `preferred_distance_max: 7`

### 2. NecromancerAI (`components/ai/necromancer_ai.py`)

**Turn Priority:**

1. **Raise Dead (if off cooldown):**
   - Find nearest raisable corpse within range 5
   - Check `CorpseComponent.can_be_raised() == True`
   - Deterministic selection: nearest first, tie-break by (y, x)
   - Cast `raise_dead` with `raiser_faction=CULTIST`
   - On success: set 4-turn cooldown
   - Metrics: `necro_raise_attempts`, `necro_raise_successes`

2. **Corpse Seeking (if corpses out of range):**
   - Find nearest raisable corpse anywhere
   - Compute step toward corpse
   - **Safety Check:** Never approach within 2 tiles of player
   - Try primary step, then alternatives (x-only, y-only)
   - If all steps violate safety: block move
   - Metrics: `necro_corpse_seek_moves`, `necro_unsafe_move_blocks`

3. **Hang-Back/Retreat:**
   - If too close to player (<=2): try to retreat
   - Maintain preferred distance 4-7 when possible
   - Fallback to basic AI (attack/wait) if boxed in

**Key Methods:**
- `_try_raise_dead()`: Raise logic with cooldown
- `_try_corpse_seeking_movement()`: Seek distant corpses safely
- `_try_safe_corpse_approach()`: Move toward corpse respecting danger radius
- `_find_best_raisable_corpse()`: Deterministic corpse selection
- `_is_safe_move()`: Safety constraint check

**Determinism:**
- No RNG in corpse selection or movement
- Tie-breaking by (y, x) coordinates
- Cooldown prevents spam
- Safety radius hard constraint

### 3. Scenario (`config/levels/scenario_monster_necromancer_identity.yaml`)

**Layout:**
- 21x15 arena
- 1 Necromancer (position 17, 7)
- 4 Skeletons (positions 13,5 and 13,9) - will leave bone piles + corpses
- 4 Orcs (positions 9,6 and 9,8) - corpse sources
- Player starts at (2, 7)

**Items:**
- Shortbow + 20 arrows (ranged combat)
- Longsword (melee upgrade)
- 10 healing potions (extended combat)

**Purpose:**
- Test corpse seeking: enemies at multiple distances (9-17 tiles)
- Validate safety radius: necromancer must avoid player while seeking
- Observe multiple raise cycles: 4-turn cooldown allows multiple raises
- Verify corpse persistence: zombies remain on map after raise

**Expected Metrics (30 runs):**
- `necro_raise_successes`: >= 20
- `necro_corpse_seek_moves`: >= 10
- Player deaths: <= 15

### 4. Metrics Integration

**RunMetrics (per-run):**
- `necro_raise_attempts: int`
- `necro_raise_successes: int`
- `necro_corpse_seek_moves: int`
- `necro_unsafe_move_blocks: int`

**AggregatedMetrics (multi-run):**
- `total_necro_raise_attempts: int`
- `total_necro_raise_successes: int`
- `total_necro_corpse_seek_moves: int`
- `total_necro_unsafe_move_blocks: int`

**Collection:**
- NecromancerAI increments metrics via `get_active_metrics_collector().increment()`
- Scenario harness aggregates across all runs
- Balance suite includes necromancer scenario (FULL mode)

### 5. Enforcement Test (`tests/integration/test_necromancer_identity_scenario_metrics.py`)

**Marked:** `@pytest.mark.slow`

**Test 1: Metrics Thresholds**
- Runs 30 scenarios
- Asserts: raise_successes >= 20
- Asserts: corpse_seek_moves >= 10
- Asserts: player_deaths <= 15
- Asserts: attempts >= successes (sanity)

**Test 2: Corpse Persistence Invariant**
- Validates design-level invariant
- Raised corpses remain on map (transformed to zombies)
- CorpseComponent marked consumed=True
- Enables future corpse explosion mechanics

---

## Design Decisions

### Corpse Persistence (Critical)

**Implementation:**
- Raise dead spell transforms corpse entity in-place
- Adds `Fighter` and `AI` components to corpse
- Sets `corpse.faction = raiser_faction` (friendly to necromancer)
- Marks `CorpseComponent.consumed = True`
- **Does NOT remove corpse from entities list**

**Rationale:**
- Supports future corpse explosion (target consumed corpses)
- Enables corpse decay mechanics (tooltip shows "spent remains")
- Avoids needing separate "spent corpse" entity type
- Simpler than remove-and-replace pattern

### Safety Radius (Balance)

**Why 2 tiles?**
- Necromancer has weak stats (3-5 damage, 28 HP)
- Should avoid melee combat
- 2-tile radius allows tactical positioning
- Doesn't prevent necromancer from being threatened

**Alternative Considered:**
- Larger radius (3-4) would make necromancer too safe
- Smaller radius (1) would cause frequent melee deaths

### Cooldown Tuning (4 turns)

**Why 4 turns?**
- Short enough for multiple raises per fight
- Long enough to prevent instant army spam
- Allows player to kill corpse sources before raises
- Balanced with 5-tile range (limited targeting)

**Tuning Lever:**
- Increase cooldown (6-8 turns) if necromancer too oppressive
- Decrease cooldown (2-3 turns) if raises feel rare
- Adjust in `entities.yaml` without code changes

---

## Metrics Baseline

**From 30-run scenario (expected):**

| Metric | Threshold | Interpretation |
|--------|-----------|----------------|
| Raise attempts | ~30-40 | Necromancer finds corpses most runs |
| Raise successes | >= 20 | Most raises succeed |
| Corpse seek moves | >= 10 | Demonstrates seeking behavior |
| Unsafe blocks | ~5-15 | Safety radius enforced |
| Player deaths | <= 15 | Moderate threat level |

**If metrics diverge:**
- Raise successes < 20: Corpse detection bug or scenario positioning issue
- Corpse seek moves < 10: Corpses always in range (scenario too dense)
- Player deaths > 15: Necromancer + zombies overtuned

---

## API Usage Example (Future: Corpse Explosion)

```python
# Find consumed corpses for explosion targeting
from components.component_registry import ComponentType

def find_consumed_corpses(entities, max_range):
    """Find consumed corpses for explosion spell."""
    corpses = []
    for entity in entities:
        corpse_comp = entity.get_component_optional(ComponentType.CORPSE)
        if corpse_comp and corpse_comp.consumed:
            # This corpse was raised - can be targeted for explosion
            corpses.append(entity)
    return corpses
```

This works because raised corpses remain on map (as zombies) with consumed=True.

---

## Testing

**Unit Tests:**
- `tests/unit/test_necromancer_creation.py` (2 tests)
  - Necromancer entity creation with all attributes
  - NecromancerAI initialization

**Integration Tests:**
- `tests/integration/test_necromancer_identity_scenario_metrics.py` (2 tests, slow)
  - 30-run scenario metrics validation
  - Corpse persistence invariant check

**Regression:**
- All fast tests pass: 3286 tests
- Necromancer added to balance suite (FULL mode)

---

## Files Changed

**Core Implementation:**
1. `components/corpse.py` - CorpseComponent (Phase 19 Part 1)
2. `components/component_registry.py` - CORPSE enum
3. `death_functions.py` - Attach CorpseComponent on death
4. `spells/spell_executor.py` - Use CorpseComponent, add raiser_faction
5. `services/damage_service.py` - Add death features to entities
6. `engine/systems/ai_system.py` - Add death features to entities
7. `engine/systems/environment_system.py` - Add death features to entities
8. `game_actions.py` - Add death features to entities

**Necromancer Implementation:**
9. `components/ai/necromancer_ai.py` - NecromancerAI class
10. `config/entities.yaml` - Necromancer monster definition
11. `config/entity_registry.py` - MonsterDefinition necromancer fields
12. `config/factories/monster_factory.py` - NecromancerAI registration + attribute copying

**Metrics & Testing:**
13. `services/scenario_harness.py` - Necromancer metrics fields + aggregation
14. `config/levels/scenario_monster_necromancer_identity.yaml` - Identity scenario
15. `tools/balance_suite.py` - Add necromancer scenario to FULL suite
16. `tests/test_corpse_safety.py` - Corpse safety tests (10 tests)
17. `tests/test_death_nonboss.py` - Fix for ComponentRegistry requirement
18. `tests/unit/test_necromancer_creation.py` - Necromancer creation tests (2 tests)
19. `tests/integration/test_necromancer_identity_scenario_metrics.py` - Metrics enforcement (2 tests, slow)

**Documentation:**
20. `docs/INVESTIGATIONS/PHASE19_CORPSE_SAFETY_IMPLEMENTATION.md` - Corpse safety audit
21. `docs/INVESTIGATIONS/PHASE19_NECROMANCER_IMPLEMENTATION.md` - This document
22. `docs/PHASE_19_MONSTER_IDENTITY_AND_ABILITIES.md` - Added necromancer section

**Total:** 22 files

---

## Known Limitations

1. **No corpse decay:** Corpses persist indefinitely (future feature)
2. **Simple pathfinding:** Necromancer uses greedy step toward corpse (no A*)
3. **No LOS check:** Necromancer can seek corpses through walls (acceptable - maintains distance anyway)
4. **No ally coordination:** Necromancer doesn't account for zombie positions when raising

**None are blockers** - all can be added later if needed.

---

## Next Steps (Out of Scope)

1. **Corpse Explosion Spell:**
   - AoE spell targeting consumed corpses
   - Uses corpse persistence invariant
   - Adds tactical corpse denial gameplay

2. **Corpse Decay:**
   - Corpses become non-raisable after N turns
   - Visual indicators (color fade)
   - Uses `death_turn` in CorpseComponent

3. **Necromancer Variants:**
   - Bone Necromancer: Can raise bone piles as skeleton zombies
   - Blood Necromancer: Sacrifices HP to raise without cooldown
   - Lich: High-tier necromancer with multiple summons

---

**END OF DOCUMENT**

