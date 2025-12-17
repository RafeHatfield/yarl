# Phase 19: Monster Identity and Abilities

**Status:** In Progress  
**Started:** 2024-12-16  
**Authority:** This document governs Phase 19 monster ability additions

---

## Purpose

Phase 19 introduces **monster-specific abilities** that:
- Express monster identity
- Create meaningful player decisions
- Preserve the existing balance envelope

**This is NOT a difficulty increase.**

---

## Design Constraints (Absolute)

### What Abilities MUST Be

- **Deterministic:** No hidden RNG that can't be tested
- **Observable:** Player can see/understand what's happening
- **Testable:** Can be exercised in scenario harness
- **Scoped:** Fits within existing turn/action economy

### What Abilities MUST NOT Be

- Raw damage multipliers ("orc deals +50% damage")
- Always-on passive buffs that bypass combat math
- Agency-removing mechanics (stun-lock, forced movement)
- Non-deterministic effects that can't be validated

---

## Implementation Principles

1. **One ability per monster type**
2. **Minimal surface area** (prefer extending existing systems)
3. **Balance validation required** (balance-suite-fast must pass)
4. **No baseline updates** unless explicitly justified

---

## Phase 19 Monster Abilities

### Troll: Regeneration

**Status:** ✅ In Progress (Phase 19.1)

**Identity:** Trolls are classically known for regeneration  
**Decision:** Do I finish this troll quickly, or deal with its healing?

**Mechanic:**
- Trolls heal **2 HP at end of their turn** (after all actions)
- Regeneration stops if troll is at max HP
- Regeneration is **deterministic** (no RNG)
- Only applies to monsters with "regenerating" tag

**Tuning:**
- Baseline: 2 HP/turn
- Max HP unchanged (30 for basic troll, 50 for ancient)
- If balance suite shows WARN/FAIL: reduce to 1 HP/turn

**Implementation:**
- Add `regeneration_amount` field to monster definitions
- Handle in `systems/combat_system.py` end-of-turn processing
- Telegraphed in combat log: "The troll regenerates 2 HP!"

**Testing:**
- Scenario: `troll_regeneration_test.yaml`
- Validates healing per turn, capped at max HP
- Ensures deterministic behavior

**Balance Impact:**
- Expected: WARN on troll-heavy scenarios (intended)
- If FAIL: reduce to 1 HP/turn or add "fire stops regeneration" mechanic

---

### Slime: Identity Kit (Phase 19.2)

**Status:** ✅ Complete (Phase 19.2)

**Identity:** Amorphous predators with corrosive, engulfing attacks  
**Decision:** Do I use metal weapons and risk corrosion? Do I stay adjacent or break contact?

**Mechanics:**

**A) Split Under Pressure (tiered):**
- Large slimes split at 35% HP into 2-3 minor slimes
- Greater slimes split at 30% HP into 2 large slimes
- Split is deterministic per seed (weighted RNG for child count)
- Split only triggers once per entity
- Replaces old split-on-death behavior

**B) Corrosive Contact:**
- 50% chance to corrode metal weapons on hit
- Reduces weapon damage_max by 1 per corrosion event
- Floor: cannot reduce below 50% of base damage
- Non-metal weapons (wood, bone, stone) are immune
- Deterministic under fixed seed

**C) Engulf:**
- Applies slow effect on slime hit
- Slow does NOT decay while player is adjacent to ANY slime
- Slow begins to decay after breaking adjacency
- Creates "break contact" decision for players

**Tuning:**
- Split thresholds: **40% (large), 35% (greater)** (Phase 19.3: tuned for observable splits)
- Corrosion chance: **Tiered by slime type** (Phase 19.2)
  - Minor/small slimes: 5%
  - Normal/large slimes: 10%
  - Greater slimes: 15%
- Corrosion floor: 50% of base damage
- Engulf: standard slow effect with adjacency-based persistence

**Implementation:**
- Split logic: `services/slime_split_service.py`
- Corrosion logic: `components/fighter.py` (attack method)
- Engulf logic: `components/status_effects.py` (EngulfedEffect)
- Monster definitions: `config/entities.yaml`

**Testing:**
- Scenario: `scenario_monster_slime_identity.yaml`
- Validates split + corrosion + engulf in deterministic runs
- Split rate: **100%+ of eligible slimes split** (exceeds 33% target)
- Split rate enforced via `test_slime_identity_scenario_split_rate.py`
- Unit tests: `test_slime_split_under_pressure.py`, `test_corrosion_mechanics.py`, `test_engulf_mechanics.py`, `test_tiered_corrosion.py`

**Balance Impact:**
- Scenario runs: 30 runs, 200 turn limit
- Typical results: ~490 kills (150 splits, 370 children), 0 deaths
- Included in full balance suite (not fast mode)

---

## Future Abilities (Planned)

### Orc Chieftain: Rally Cry (Phase 19.3)

**Status:** Not Started

**Identity:** Leadership and tactical coordination  
**Decision:** Focus fire the chieftain, or deal with buffed orcs?

**Mechanic Ideas:**
- Once per combat: buff nearby orcs (+1 accuracy for 3 turns)
- Triggered when chieftain HP < 50%
- Limited-use ability (not always-on)

---

### Wraith: Life Drain (Phase 19.4)

**Status:** Not Started

**Identity:** Ethereal predator that drains life force  
**Decision:** High-damage burst to kill before it heals?

**Mechanic Ideas:**
- On hit: heal 25% of damage dealt
- Or: drain 1 max HP from player (permanent until rest)
- Must be telegraphed and limited

---

## Balance Validation Process

For every Phase 19 ability:

1. **Before implementation:**
   - Run `make balance-suite-fast` to establish baseline
   - Note current metrics

2. **After implementation:**
   - Run `make balance-suite-fast`
   - Check verdict: PASS/WARN/FAIL

3. **Interpretation:**
   - **PASS:** Ship it
   - **WARN:** Expected for ability additions, review drift
   - **FAIL:** Stop immediately, tune down or redesign

4. **No baseline updates** without explicit justification

---

## Success Criteria

- [ ] Ability expresses monster identity clearly
- [ ] Creates meaningful player decisions
- [ ] Balance Suite does not FAIL
- [ ] Changes are small, reviewable, scoped
- [ ] Deterministic scenario tests pass

---

## Non-Goals

- Adding new monster types
- Sweeping combat system refactors
- Full test suite overhaul
- Difficulty tuning (separate from abilities)

---

## References

- Balance Contract: `docs/BALANCE_ACCEPTANCE_CONTRACT.md`
- Testing Harness: `docs/BALANCE_AND_TESTING_HARNESS.md`
- Monster Definitions: `config/entities.yaml`
- ETP System: `balance/etp.py`

