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

## Future Abilities (Planned)

### Orc Chieftain: Rally Cry (Phase 19.2)

**Status:** Not Started

**Identity:** Leadership and tactical coordination  
**Decision:** Focus fire the chieftain, or deal with buffed orcs?

**Mechanic Ideas:**
- Once per combat: buff nearby orcs (+1 accuracy for 3 turns)
- Triggered when chieftain HP < 50%
- Limited-use ability (not always-on)

---

### Wraith: Life Drain (Phase 19.3)

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

