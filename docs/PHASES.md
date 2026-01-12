# Catacombs of YARL - Development Phases

**Last Updated:** 2024-12-14

## Purpose

This document tracks the development arc of Catacombs of YARL from foundation to current state, and maps the road ahead.

**What this is:**
- Historical record of completed work
- Planning tool for future development
- Orientation guide for new contributors

**What this is not:**
- Detailed technical documentation (see individual docs/)
- Complete feature specifications
- Exhaustive change log

**How to use this:**
- Read sequentially to understand how the game evolved
- Use phase numbers as reference points in discussions
- Update as phases complete or priorities shift

---

## Completed Phases

### Phase 1-3: Foundation (Early 2024)

**Status:** COMPLETE

**What it addressed:**
- Core engine architecture and ECS implementation
- Basic turn-based gameplay loop
- Entity system with monsters, items, and player
- Initial UI rendering and input handling
- MVP playable game loop

**What it unlocked:**
- Stable foundation for iterative development
- Ability to test gameplay mechanics in isolation
- Clear separation between game logic and rendering

---

### Phase 4-5: Core Systems Stabilization

**Status:** COMPLETE

**What it addressed:**
- Turn controller refactoring for clean state management
- Input abstraction layer (keyboard/bot/future inputs)
- Message system and combat feedback
- Death screen and game over handling
- Component access patterns and type safety

**What it unlocked:**
- Reliable turn sequencing for complex interactions
- Bot testing infrastructure
- Consistent player feedback across all actions
- Foundation for automated testing

---

### Phase 6-8: World Generation

**Status:** COMPLETE

**What it addressed:**
- YAML-based level template system
- Room generation with doors, corridors, vaults
- Dungeon depth progression
- Loot distribution and item placement
- Victory condition (Amulet of Yarl)

**What it unlocked:**
- Content authoring without code changes
- Varied dungeon layouts and replayability
- Clear progression structure (descend → retrieve → ascend)
- Worldgen sanity testing harness

**Key artifact:** `worldgen_sanity.py` for regression testing

---

### Phase 9-11: Combat Mechanics Expansion

**Status:** COMPLETE

**What it addressed:**
- Surprise attack system (backstab mechanics)
- Momentum and bonus attack chains
- Critical hit system (natural 20 = 2x damage)
- Awareness states (unaware/aware/alert)
- Speed bonuses and turn economy

**What it unlocked:**
- Tactical depth beyond "hit enemy until dead"
- Positioning and flanking strategies
- Speed items as meaningful progression
- Foundation for future status effects

---

### Phase 12: Scenario Harness (Deterministic Testing)

**Status:** COMPLETE

**What it addressed:**
- Hand-authored scenario system (no worldgen RNG)
- Repeatable combat testing with fixed starting conditions
- Scenario-based metrics collection
- Bot policy integration for automated testing

**What it unlocked:**
- Ability to measure combat balance objectively
- Regression detection for combat changes
- Fast iteration on combat tuning (no full runs needed)
- Foundation for difficulty curve analysis

**Key artifact:** `ecosystem_sanity.py` scenario runner

---

### Phase 13: Combat Metrics & Feel Measurement

**Status:** COMPLETE

**What it addressed:**
- Attack rate tracking (player vs monster)
- Hit percentage measurement
- Bonus attack frequency metrics
- Combat pacing visibility

**What it unlocked:**
- Quantitative answers to "does this feel good?"
- Data-driven combat tuning
- Speed bonus effectiveness measurement
- Foundation for Phase 16 difficulty tuning

**Key metrics:** player_hit_rate, monster_hit_rate, bonus_attacks_per_run

---

### Phase 14-15: Bot Intelligence & Telemetry

**Status:** COMPLETE

**What it addressed:**
- Bot persona system (balanced, cautious, aggressive, greedy, speedrunner)
- Tactical decision-making (attack, heal, flee, explore)
- Bot soak testing (hundreds of runs)
- Telemetry and survivability reporting

**What it unlocked:**
- Automated playtesting at scale
- Survivability measurement across scenarios
- Persona-specific behavior validation
- Foundation for Phase 17 heal logic tuning

**Key tools:** `bot_soak_harness`, `bot_survivability_report.py`

---

### Phase 16: Difficulty Curve & First Tuning Pass

**Status:** COMPLETE (16A)

**What it addressed:**
- Difficulty curve visualization across depth
- First combat balance tuning (YAML-only changes)
- Target bands for death rate, hit rates, pressure
- Orc/zombie stat adjustments
- Player accuracy improvements

**What it unlocked:**
- Visual understanding of difficulty progression
- Baseline metrics for future comparison
- Confidence in YAML-based iteration
- Graphs: death rate, hit rates, pressure index vs depth

**Key outputs:** `difficulty_dashboard.md`, depth-tagged scenarios

---

### Phase 17: Bot Survivability & Heal Logic (17A-17C)

**Status:** COMPLETE

**What it addressed:**
- Heal threshold calibration (from 3-7% emergency to 25-30% proactive)
- Panic logic for multi-attacker pressure (15% threshold)
- Potion availability detection bugs
- Adaptive heal thresholds per persona
- Combat healing enablement for balanced persona

**What it unlocked:**
- Bots that survive lethal scenarios intelligently
- Survivability metrics that reflect player experience
- Persona-specific heal strategies
- Foundation for advanced AI decision-making

**Key fixes:**
- 17A: Baseline survivability framework
- 17B: Heal threshold calibration + panic logic
- 17C: Adaptive thresholds, potion availability fixes, priority tweaks

**Key metrics:** heal_hp_pct (P25/P50/P75), deaths_with_potions, panic_heals

---

### Phase 18: Gear Identity, Affixes, Damage Types (18.0-18.3)

**Status:** COMPLETE

**What it addressed:**
- Explicit weapon affix system (keen, vicious, fine, masterwork)
- Damage type semantics (slashing, piercing, bludgeoning)
- Armor resistances and vulnerabilities
- Monster faction damage modifiers (undead, armored)
- Weapon variant scenarios for balance testing
- Balance Suite orchestration tool

**What it unlocked:**
- Meaningful gear choices (not just +1/+2)
- Tactical weapon selection vs enemy types
- Comprehensive balance regression detection
- Weapon affix effectiveness measurement
- Balance Acceptance Contract for CI

**Key deliverables:**
- Affix→stat mappings (keen=crit range, vicious=+dmg, fine=+hit, masterwork=both)
- Damage type vulnerability system
- 15-scenario balance suite (3 bases × 5 weapon variants)
- `tools/balance_suite.py` orchestrator
- `docs/BALANCE_ACCEPTANCE_CONTRACT.md`
- CI integration (balance-ci.yml)

**Key metrics:** death_rate, player_hit_rate, monster_hit_rate, pressure_index, bonus_attacks_per_run

---

## Current Phase

**Post-Phase 18: Consolidation & Quality-of-Life**

Status: Phase 18 QOL work is complete. The project is stable and ready for the next major phase.

**Recently completed:**
- Balance Acceptance Contract (formal merge policy)
- CI integration for balance suite (GitHub Actions)
- Reports directory cleanup (baselines only)
- Documentation consolidation
- Balance suite baseline establishment

**Next steps:**
- Establish baseline from production scenarios
- Validate CI workflow on real PRs
- Begin Phase 19 planning (Monster Identity & Abilities)

**No new major features are in active development.**

---

## Proposed Future Phases

### Phase 19: Monster Identity & Abilities

**Status:** ✅ COMPLETE (v4.10.0)

**Intent:**
Monster-specific abilities and tactical patterns to differentiate enemy types beyond HP/damage stats.

**Implemented Features:**
- **Orc Chieftain:** Rally aura (+2 damage to nearby orcs), tactical positioning
- **Orc Shaman:** Channeled Chant of War (+2 to-hit aura), interruptible by damage
- **Necromancer Variants:**
  - Base Necromancer: Raises corpses into zombies, hang-back AI
  - Bone Necromancer: Summons bone thralls from bone piles
  - Plague Necromancer: Raises plague zombies with infection
  - Exploder Necromancer: Detonates spent corpses (Phase 20 integration)
- **Lich (Arch-Necromancer):** Soul Bolt telegraph+resolve, Soul Ward counter, Command the Dead aura, Death Siphon
- **Wraith:** Life Drain melee (heals on hit), countered by Ward Against Drain
- **Troll:** Regeneration (2 HP/turn), suppressed by acid/fire damage
- **Skeleton:** Death-spawns bone pile (targetable by Bone Necromancer)
- **Corpse Safety System:** CorpseComponent prevents infinite raise loops

**Deliverables:**
- 12 new monster variants with unique abilities
- 26-scenario balance suite (all identity kits validated)
- Deterministic ability mechanics (no RNG where avoidable)
- Faction-aware AI and aura systems

---

### Phase 20: Status Effects & Combat Depth

**Status:** ✅ COMPLETE

**Intent:**
Introduce persistent combat effects and corpse explosion mechanics to create tactical depth.

**Completed Systems:**

**Corpse Explosion Lifecycle:**
- FRESH corpses: Created on death, raisable, NOT explodable
- SPENT corpses: Created on re-death of raised entities, explodable, NOT raisable
- CONSUMED corpses: Post-explosion, inert
- Lineage tracking: Raised entities carry corpse_id for deterministic SPENT creation
- Exploder Necromancer: Targets ONLY SPENT corpses
- State machine prevents illegal double-use (raise+explode same corpse)

**Status Effects Maturity:**
- **PoisonEffect:** Damage-over-time (6 turns, 1/tick), resistance-aware, canonical DOT model
- **BurningEffect:** Fire damage-over-time, applied by fire creatures and hazards
- **SilencedEffect:** Spell denial (blocks spellcasting, scrolls, spell-tagged abilities), 3-turn duration
- **SlowedEffect:** Turn-skip movement penalty, refresh-not-stack semantics
- **EntangledEffect:** Root/vine movement blocker, turn-consuming, 3-turn duration
- **StaggeredEffect:** Micro-stun from wall-impact knockback, 1-turn skip

**Hazards Modernization:**
- Fire hazards apply BurningEffect via canonical status system
- Poison gas hazards apply PoisonEffect via canonical status system
- Environmental damage routes through status effects framework

**Knockback System:**
- Weapon-based knockback (power-delta scaled distance, cap 4 tiles)
- Wall-impact stagger (micro-stun on collision)
- Canonical movement execution, respects entangle/root
- Deterministic under scenario harness seeding

**Silence Canonicalization:**
- Scroll of Silence applies SilencedEffect
- Execution-point blocking (not AI decision logic)
- Works on both player and monsters
- Clear scope: blocks spells/scrolls/spell-tagged abilities, not potions/melee/movement

**Deliverables:**
- Complete status effect framework with duration tracking
- Corpse lifecycle state machine (FRESH/SPENT/CONSUMED)
- Weapon knockback with stagger mechanics
- Hazards integrated with status effects
- Deterministic, metriced, baselined systems

**What it unlocked:**
- Tactical depth through persistent effects
- Environmental hazards as meaningful gameplay elements
- Foundation for Phase 21 traps (status effect routing)
- Combat variety beyond raw damage numbers

---

### Phase 21: Traps & Environmental Control

**Status:** PLANNED

**Intent:**
Make dungeon layouts mechanically meaningful beyond monster placement. Introduce traps that trigger on tile entry and route effects through canonical systems.

**Trap Types:**

**Spike Trap:**
- Direct damage routed through damage_service
- Applies bleed status effect
- Common trap type

**Root Trap:**
- Applies EntangleEffect (movement blocked, turn consumed)
- Uses canonical status effect system
- Tactical positioning disruption

**Gas Trap:**
- Applies PoisonEffect (damage-over-time)
- Routes through status effects framework
- Environmental hazard integration

**Fire Trap:**
- Applies BurningEffect (fire damage-over-time)
- Uses canonical status effect system
- Synergy with fire resistance mechanics

**Teleport Trap:**
- Teleports entity to random valid tile on same dungeon level
- Deterministic under seed (no RNG surprises)
- Tactical repositioning, not death sentence

**Hole Trap (RARE):**
- Forces descent to next dungeon level
- Uses canonical level-transition logic
- Intentionally high-impact, rare occurrence
- No instant death — player survives fall

**Design Principles:**
- Traps trigger on tile entry (post-successful movement)
- Traps execute at canonical execution points, not AI/decision logic
- Effects/damage route through existing canonical systems (damage_service, status effects)
- Introduction sequence: identity scenarios → controlled arenas → worldgen integration
- Knockback synergy: knockback into traps is a valid interaction, but knockback is NOT a trap type

**Phase 21 Goals:**
- Implement six trap types with canonical effect routing
- Create identity scenarios validating each trap type
- Integrate traps into controlled arena scenarios
- Add trap placement to worldgen (YAML-driven)
- Ensure deterministic behavior under scenario harness seeding
- Maintain balance suite stability

**Dependencies:**
- Phase 20 status effects framework (complete)
- Trap component system (exists)
- Movement service integration (exists)
- Damage service routing (exists)

**Risks:**
- Worldgen complexity increases significantly
- Bot pathfinding needs trap awareness
- May require renderer updates for visual clarity
- Trap density must balance challenge without frustration

---

### Phase 22: Progression & Meta Systems

**Status:** PLANNED

**Intent:**
Layer meta-progression on top of single-run gameplay. Unlock systems, persistent upgrades, challenge modes, or run modifiers.

**Potential features:**
- Unlock system (start with limited gear/floors)
- Persistent upgrades (cross-run bonuses)
- Challenge modifiers (harder runs = better rewards?)
- Scoring system and leaderboards
- Achievement tracking

**Dependencies:**
- Save system expansion
- Unlock/progression database
- UI for meta-systems

**Risks:**
- May dilute core roguelike loop
- Balancing progression power creep
- Scope creep (meta systems can balloon)

---

### Phase 23: Content Expansion & Polish

**Status:** PLANNED

**Intent:**
Expand existing systems with more content rather than new mechanics. Focus on variety, balance, and player experience refinement.

**Potential features:**
- More monster families (demons, constructs, beasts)
- Expanded item pool (more weapons, armor, consumables)
- Additional spell schools
- Unique boss encounters
- Biome variety (different dungeon themes)
- Sound effects and music
- Particle effects and animation polish

**Dependencies:**
- All core systems stable
- Content pipeline efficient (YAML-based)
- Asset creation workflow (if adding art/sound)

**Risks:**
- Content additions may reveal balance issues
- Diminishing returns on variety without new mechanics
- Art/sound asset creation can be time-intensive

---

## Phase Management Notes

### How Phases Are Chosen

Phases are not strictly linear. The order reflects:
1. **Dependencies** (foundation before features)
2. **Risk** (validate core assumptions early)
3. **Feedback** (prioritize based on playtesting)
4. **Momentum** (capitalize on related work)

### When to Start a New Phase

Start a new phase when:
- Previous phase is stable and tested
- Clear problem statement exists
- Success criteria are definable
- Dependencies are satisfied

### When to Pause or Pivot

Pause or pivot when:
- Current approach isn't working (pivot)
- Blocking bugs emerge (pause, fix, resume)
- Playtesting reveals different priorities (pivot)
- Technical debt becomes inhibiting (consolidate)

### Phase Documentation Standards

Each phase should have:
- Problem statement (why)
- Goals (what)
- Deliverables (concrete outputs)
- Success criteria (how we know it's done)
- Key files changed (what/where)

Analysis docs (`PHASE_N_ANALYSIS.md`) live in repo root during active development, then move to `archive/` when complete.

---

## Related Documentation

- **Architecture:** `ARCHITECTURE_OVERVIEW.md`
- **Combat System:** `docs/COMBAT_SYSTEM.md`
- **Balance & Testing:** `docs/BALANCE_AND_TESTING_HARNESS.md`
- **Bot System:** `docs/BOTBRAIN_OVERVIEW.md`, `docs/BOT_PERSONAS.md`
- **Worldgen:** `docs/WORLDGEN_OVERVIEW.md`
- **Scenario Testing:** `docs/BALANCE_SUITE.md`

---

## Changelog

- **2024-12-14:** Document created (backfilled Phases 1-18, proposed 19-23)
