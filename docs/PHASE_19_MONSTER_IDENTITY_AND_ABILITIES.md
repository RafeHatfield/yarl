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

### Skeleton: Shield Wall (Phase 19.3)

**Status:** ✅ Complete (Phase 19.3)

**Identity:** Defensive undead warriors that form shield walls  
**Decision:** Do I break their formation or use the right weapon type?

**Mechanics:**

**A) Shield Wall:**
- Skeletons gain **+1 AC per adjacent skeleton ally** (4-way adjacency: N/S/E/W)
- **NO CAP** on shield wall bonus
- Deterministic AC calculation based on formation
- Cached per-turn for performance

**B) Damage Type Modifiers:**
- **Piercing weapons:** Skeletons take 50% damage (0.5x multiplier)
- **Bludgeoning weapons:** Skeletons take 150% damage (1.5x multiplier)
- **Slashing weapons:** Normal damage (1.0x multiplier)
- Multipliers apply before crit doubling

**C) Formation AI:**
- Skeletons try to group up when not in combat
- Prefer moves that increase adjacency to allies
- Still attack player when in range (combat priority)
- Deterministic movement selection

**D) Bone Pile:**
- Spawns on skeleton death
- Future hook for necromancer abilities
- Currently cosmetic/lore element

**Tuning:**
- Base skeleton: 20 HP, 3-5 damage, 11 AC (base)
- With 2 adjacent allies: 13 AC
- With 4 adjacent allies: 15 AC
- Piercing damage: 50% effectiveness
- Bludgeoning damage: 150% effectiveness

**Implementation:**
- Shield wall: `components/fighter.py` (armor_class property)
- Adjacency counting: `services/skeleton_service.py`
- Damage modifiers: `components/fighter.py` (attack_d20 method)
- Formation AI: `components/ai/skeleton_ai.py`
- Bone pile: `death_functions.py` (_spawn_death_feature)
- Monster definitions: `config/entities.yaml`

**Testing:**
- Scenario: `scenario_monster_skeleton_identity.yaml`
- Validates shield wall AC, damage types, formation AI, bone piles
- Unit tests: `test_skeleton_shield_wall.py` (16 tests, all passing)

**Balance Impact:**
- Scenario runs: 30 runs, 200 turn limit
- Expected: 4 skeletons per run, demonstrating all mechanics
- Included in full balance suite (not fast mode)

---

## Orc Chieftain: Rally Cry + Sonic Bellow (Phase 19.4)

**Status:** ✅ COMPLETE

**Identity:** High-priority leader enemy with deterministic, scenario-backed behavior  
**Decision:** Focus fire the chieftain to break rally, or deal with buffed orcs?

**Mechanic 1: Rallying Cry (ONE-TIME, very impactful)**
- Triggers once at start of chieftain's turn when:
  - Not yet rallied
  - >= 2 orc allies within radius 5
- Effects on nearby ORC allies:
  - +1 to-hit bonus
  - +1 damage bonus
  - Cleanses fear/morale-debuff effects
  - Issues "call to attack" directive: rallied orcs prioritize chieftain's target
- Rally persists UNTIL THE CHIEFTAIN IS DAMAGED (first time)
- When chieftain takes ANY damage (first time after rally):
  - Rally ends immediately for ALL rallied orcs
  - Buffs removed, directives cleared
  - Message: "The rally falters as the chieftain is struck!"
- Deterministic, no RNG

**Mechanic 2: Sonic Bellow (ONE-TIME desperation shout)**
- Triggers once when chieftain drops below 50% HP (first time only)
- Effect on player:
  - -1 to-hit penalty for 2 turns
- Message: "The Orc Chieftain's bellow rings in your ears!"
- Deterministic, no RNG

**Mechanic 3: Hang-back AI Heuristic**
- Chieftain prefers to "hang back" when other orcs can engage
- Positional preference:
  - If any non-chieftain orc ally can attack the player, chieftain prefers distance 2-4
  - If already at good distance, stays put or moves laterally
  - If too close (distance 1), tries to move away
  - If boxed in or no allies can engage, attacks normally
- Never stalls: if forced to engage, attacks
- Encourages tactical play: reach chieftain via flanking/ranged/funneling

**Implementation:**
- Status effects: `RallyBuffEffect`, `SonicBellowDebuffEffect` in `components/status_effects.py`
- AI: `OrcChieftainAI` in `components/ai/orc_chieftain_ai.py`
- Config: `config/entities.yaml` (orc_chieftain with rally/bellow fields)
- Rally break: `Fighter.take_damage()` detects chieftain damage and ends rally
- Combat bonuses: `Fighter.attack_d20()` applies rally buffs and bellow debuffs
- AI directive: `BasicMonster.take_turn()` respects rally_directive_target_id
- Scenario: `scenario_monster_orc_chieftain_identity.yaml`
- Unit tests: `test_orc_chieftain.py` (15 tests)

**Scenario:**
- 1 Orc Chieftain + 3 basic orcs
- Chieftain hangs back while orcs engage
- Rally triggers when chieftain has 2+ allies nearby
- Player can break rally by tagging chieftain with ranged weapon or flanking
- Bellow triggers when chieftain drops below 50% HP
- Validates: rally trigger, rally buffs, rally break-on-damage, bellow trigger, hang-back AI

**Balance Impact:**
- Scenario runs: 30 runs, 200 turn limit
- Expected: 4 enemies per run (1 chieftain + 3 orcs)
- Rally is very impactful (+to-hit +damage for all allies) but breakable
- Encourages tactical play: prioritize chieftain or deal with buffed orcs
- Included in full balance suite (not fast mode)

---

### Wraith: Life Drain + Ward Against Drain (Phase 19.5)

**Status:** ✅ COMPLETE

**Identity:** Ethereal predator that drains life force  
**Decision:** Do I use the ward scroll proactively, or save it for a crisis?

**Mechanic 1: % Life Drain**
- On successful melee hit where damage_dealt > 0:
  - `drain_amount = ceil(damage_dealt * 0.50)`  (50% of final damage)
  - `drain_amount = min(drain_amount, wraith.missing_hp)`  (capped at missing HP, no overheal)
  - Wraith heals for `drain_amount`
- Deterministic (no RNG)
- Uses **final damage dealt** (after resistances/armor)
- Message: "The wraith drains your life! (+X HP)"

**Mechanic 2: Ward Against Drain (Counter)**
- Consumable scroll: `scroll_ward_against_drain`
- Applies `WardAgainstDrainEffect` to player (10 turn duration)
- While ward is active:
  - Life drain heals are reduced to 0 (full immunity)
  - Message on drain attempt: "The ward repels the drain!"
- Ward duration ticks down each turn (standard status effect)
- Message on apply: "A pale ward surrounds you, repelling life drain!"
- Message on expire: "The ward against drain fades away."

**Tuning:**
- Life drain %: 50% of damage dealt (wraith is VERY dangerous)
- Ward duration: 10 turns (1 scroll per ~1-2 wraith encounters)
- Wraith base stats: HP=20, speed=2.0, power=3, evasion=4 (fast + hard to hit)
- No drain when damage_dealt = 0 (armor/resistance matters)

**Implementation:**
- Life drain: `Fighter._apply_life_drain_effects()` in `components/fighter.py`
- Ward effect: `WardAgainstDrainEffect` in `components/status_effects.py`
- Ward scroll: `use_ward_scroll()` in `item_functions.py`
- Config: `config/entities.yaml` (wraith with `life_drain_pct: 0.50` and `scroll_ward_against_drain`)
- Scenario: `scenario_monster_wraith_identity.yaml`
- Unit tests: `test_wraith_life_drain.py` (13 tests, all passing)

**Metrics Tracking:**
- `life_drain_attempts`: Total wraith hits that attempted drain
- `life_drain_heal_total`: Total HP healed by wraiths via drain
- `life_drain_blocked_attempts`: Drain attempts blocked by ward
- Tracked in `services/scenario_metrics.py` and aggregated in balance suite

**Scenario:**
- 2 wraiths in 13x13 arena
- Player starts with: dagger, 2 ward scrolls, 3 healing potions, longsword
- Expected behavior:
  - Without ward: Wraiths drain life and heal themselves
  - With ward active: Wraiths hit but drain is blocked (message displayed)
- Validates: drain calculation, heal capping, ward immunity, metrics tracking

**Balance Impact:**
- Scenario runs: 30 runs, 200 turn limit
- Expected: ~30+ kills (1-2 wraiths per run)
- Expected player deaths: <= 15 (wraiths are dangerous but ward helps)
- Wraiths are high-threat with speed=2.0 + drain, but deterministic and counterable
- Included in full balance suite (not fast mode)

**Teaching Moment:**
- Ward scroll teaches **preparation**: use before engaging wraiths
- Drain mechanic teaches **burst damage**: kill wraiths fast to minimize healing
- Counter availability teaches **resource management**: save wards for dangerous fights

---

## Future Abilities (Planned)

(None at this time - Phase 19 complete!)

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

