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

### Troll: Regeneration + Acid/Fire Suppression

**Status:** ✅ COMPLETE (Phase 19.6)

**Identity:** Trolls regenerate rapidly but are vulnerable to acid and fire  
**Decision:** Do I use acid/fire damage to suppress regeneration, or rush to finish it quickly?

**Mechanics:**

**A) Natural Regeneration:**
- Trolls heal **2 HP at end of their turn** (after all actions, 3 HP for ancient trolls)
- Regeneration stops if troll is at max HP
- Regeneration is **deterministic** (no RNG)
- Only applies to monsters with `regeneration_amount` attribute

**B) Acid/Fire Suppression (Counterplay):**
- When a troll takes damage from `acid` or `fire` damage type:
  - Regeneration is suppressed until the **next turn**
  - Message: "The acid prevents the troll from regenerating!" (orange)
  - Suppression is turn-based (turn number tracked via TurnManager)
- Slimes deal acid damage via `natural_damage_type: "acid"` field
- Creates tactical decision: let slime attack troll first, then finish it off

**Tuning:**
- Basic troll: 2 HP/turn regeneration, 30 HP, defense 2
- Ancient troll: 3 HP/turn regeneration, 50 HP, defense 3
- Suppression duration: 1 turn (until next turn)
- Slimes always deal acid damage (no RNG)

**Implementation:**
- Regeneration: `engine/systems/ai_system.py` (_apply_regeneration method)
- Suppression tracking: `components/fighter.py` (take_damage method, tracks `regeneration_suppressed_until_turn`)
- Damage type plumbing: `components/fighter.py` (attack_d20 passes `weapon_damage_type` or `natural_damage_type`)
- Natural damage types: `config/factories/monster_factory.py` (stores `natural_damage_type` on entity)
- Monster definitions: `config/entities.yaml` (slime has `natural_damage_type: "acid"`)

**Metrics Tracking:**
- `troll_regen_attempts`: Total regeneration attempts
- `troll_regen_successes`: Successful regenerations
- `troll_regen_suppressed`: Regenerations suppressed by acid/fire damage
- Tracked in `engine/systems/ai_system.py` (_apply_regeneration method)

**Testing:**
- Scenario: `scenario_monster_troll_identity.yaml`
- Setup: 1 troll + 1 slime in arena with player
- Validates: regeneration occurs, acid suppression works, metrics are tracked
- Expected behavior: Slime's acid attacks suppress troll regeneration

**Scenario:**
- 1 troll (regenerates 2 HP/turn normally)
- 1 slime (deals acid damage, hostile to all)
- Player starts with longsword and 3 healing potions
- Expected behavior:
  - Without acid: Troll regenerates each turn
  - With slime acid hit: Troll regeneration suppressed for 1 turn
  - Player learns to use slime's acid tactically
- Validates: regen occurs, suppression works, metrics track

**Balance Impact:**
- Scenario runs: 30 runs, 100 turn limit
- Expected: ~20-25 kills (learning curve), <= 15 deaths
- Trolls are tough without counterplay, manageable with acid/fire
- Included in full balance suite (not fast mode)

**Teaching Moment:**
- Regeneration teaches **burst damage**: finish trolls quickly
- Suppression teaches **damage type awareness**: acid/fire are valuable vs trolls
- Slime interaction teaches **multi-enemy tactics**: use hostile slimes to your advantage

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

### Orc Shaman: Crippling Hex + Chant of Dissonance (Phase 19 Battlefield Controller)

**Status:** ✅ COMPLETE

**Identity:** Battlefield controller with deterministic debuff abilities  
**Decision:** Do I interrupt the shaman's chant with ranged attacks, or endure the movement tax?

**Mechanics:**

**Mechanic 1: Crippling Hex (Cooldown-Based Debuff)**
- Applied to player when shaman is within hex_radius (default: 6 tiles)
- Effect on player:
  - -1 to-hit penalty
  - -1 AC penalty
  - Duration: 5 turns
- Cooldown: 10 turns
- Message: "🔮 A dark hex settles over [player]!"
- Deterministic, no RNG
- Can be recast after cooldown expires

**Mechanic 2: Chant of Dissonance (Channeled Movement Tax, Interruptible)**
- Applied to player when shaman is within chant_radius (default: 5 tiles)
- Effect on player:
  - +1 energy cost per movement (movement costs 2 turns instead of 1)
  - Duration: 3 turns (while shaman channels)
- Channeling requirements:
  - Shaman must maintain channeling (sets `is_channeling=True`)
  - Shaman cannot perform other actions while channeling
  - **Interruptible:** ANY damage to shaman immediately breaks the chant
- Cooldown: 15 turns (applies even if interrupted)
- Message on start: "🎵 A dissonant chant assaults [player]'s senses!"
- Message on interrupt: "The chant is broken!"
- Message on natural expiry: "The chant affecting [player] ceases."
- Deterministic, no RNG

**Mechanic 3: Hang-back AI Heuristic**
- Shaman prefers to "hang back" at distance 4-7 from player
- Positional preference:
  - If too close (≤2), tries to retreat if possible
  - If at good distance (4-7), stays put or moves laterally
  - If too far (>7), moves closer (but prefers to cast abilities)
  - If boxed in or no retreat possible, attacks normally
- Never stalls: if forced to engage, attacks
- Encourages tactical play: reach shaman via flanking/ranged/funneling

**Implementation:**
- Status effects: `CripplingHexEffect`, `DissonantChantEffect` in `components/status_effects.py`
- AI: `OrcShamanAI` in `components/ai/orc_shaman_ai.py`
- Config: `config/entities.yaml` (orc_shaman with hex/chant fields)
- Chant interrupt: `Fighter.take_damage()` detects channeling and ends it
- Combat penalties: `Fighter.attack_d20()` applies hex to-hit penalty, `Fighter.armor_class` applies hex AC penalty
- Movement tax: `game_actions.py._handle_movement()` consumes extra turn when chant is active
- AI system: `engine/systems/ai_system.py` processes interrupt_chant result
- Scenario: `scenario_monster_orc_shaman_identity.yaml`
- Unit tests: `tests/unit/test_orc_shaman.py` (14 tests)

**Scenario:**
- 1 Orc Shaman + 3 basic orcs
- Shaman hangs back (distance 4-7) while orcs engage
- Hex triggers when player is within range (6 tiles)
- Chant triggers when player is within range (5 tiles)
- Player can interrupt chant by:
  - Using shortbow to damage shaman from distance
  - Throwing daggers at shaman
  - Flanking to reach shaman with melee
- Validates: hex application, chant application, chant interrupt, hang-back AI, cooldowns

**Balance Impact:**
- Scenario runs: 30 runs, 200 turn limit
- Expected: 4 enemies per run (1 shaman + 3 orcs)
- Hex is impactful (-1 to-hit and -1 AC) but temporary (5 turns, 10 turn cooldown)
- Chant is powerful (double movement cost) but interruptible (counterplay required)
- Encourages tactical play: prioritize shaman or endure debuffs
- Included in full balance suite (not fast mode)

**Metrics Tracking:**
- `shaman_hex_casts`: Total hex casts across all runs
- `shaman_chant_starts`: Total chant starts
- `shaman_chant_interrupts`: Chants interrupted by damage (proves counterplay)
- `shaman_chant_expiries`: Chants that completed naturally
- Tracked in `OrcShamanAI` and `engine/systems/ai_system.py`

**Expected Thresholds (30 runs):**
- `shaman_hex_casts >= 30`: At least 1 hex per run
- `shaman_chant_starts >= 15`: At least half of runs see chant
- `shaman_chant_interrupts >= 5`: Counterplay is viable and used
- `shaman_chant_expiries >= 5`: Some chants complete naturally

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

### Necromancer: Raise Dead + Corpse Seeking

**Implementation Date:** 2026-01-01

**Identity:** Corpse economy controller who raises dead on cooldown and seeks distant corpses while maintaining safe distance from player.

**Mechanics:**

1. **Raise Dead (Cooldown-Based Resurrection):**
   - Range: 5 tiles
   - Cooldown: 4 turns (short - frequent raising)
   - Effect: Transforms raisable corpse (CorpseComponent.can_be_raised() == True) into friendly zombie
   - Zombies: Faction matches necromancer (friendly to cultists), moderate stats (2x HP, 0.5x damage)
   - Deterministic: Targets nearest raisable corpse, tie-break by (y, x) position

2. **Corpse Seeking Movement:**
   - Behavior: Moves toward raisable corpses when out of range
   - Safety Constraint: Never approaches within 2 tiles of player (danger radius)
   - Pathfinding: Deterministic step toward corpse, with safety check
   - If unsafe: Try alternative steps, or block move and record metric

3. **Hang-Back AI:**
   - Preferred distance: 4-7 tiles from player
   - If too close (<=2): Retreats if possible
   - Never stalls: Attacks or waits if boxed in

**Corpse Persistence Invariant:**
- Raised corpses are NOT removed from entities list
- Corpse entity transformed in-place to zombie
- CorpseComponent marked consumed=True (supports future corpse explosion)
- Design rationale: Enables future mechanics targeting spent corpses, supports decay/tooltips

**Stats (config/entities.yaml):**
```yaml
necromancer:
  hp: 28
  power: 1 (weak melee)
  damage_min/max: 2-4 (very weak)
  faction: cultist
  ai_type: necromancer
  raise_dead_range: 5
  raise_dead_cooldown_turns: 4
  danger_radius_from_player: 2
  preferred_distance_min: 4
  preferred_distance_max: 7
```

**Scenario:** `config/levels/scenario_monster_necromancer_identity.yaml`
- 1 Necromancer + 4 skeletons + 4 orcs (corpse sources)
- Enemies positioned at various distances (9-17 tiles)
- Creates corpses at different locations to test seeking behavior
- Player starts with dagger, ranged weapon available
- Healing potions support extended combat for multiple raise cycles
- 30 runs, 250 turn limit

**Expected Metrics (30 runs):**
- `necro_raise_successes`: >= 20 (frequent raising)
- `necro_corpse_seek_moves`: >= 10 (demonstrates corpse seeking)
- `necro_unsafe_move_blocks`: >= 0 (informational, proves safety constraint)
- Player deaths: <= 15 (moderate threat)

**Enforcement Test:**
- `tests/integration/test_necromancer_identity_scenario_metrics.py`
- Marked @pytest.mark.slow
- Asserts minimum raise successes, corpse seek moves, reasonable deaths
- Validates corpse persistence invariant (design-level)

**Balance Impact:**
- ETP: 44 (controller with summons, moderate individual threat)
- No baseline changes required
- Included in full balance suite (not fast mode)
- Expected: ~30+ kills (1 necromancer + enemies per run)
- Expected player deaths: <= 15 (necromancer + zombies moderate threat)
- Necromancer weak in melee, relies on zombies for damage

**Teaching Moment:**
- Corpse economy teaches **target prioritization**: kill enemies to deny necromancer corpses
- Raise mechanic teaches **positioning**: force necromancer away from corpses
- Safety radius teaches **threat assessment**: necromancer won't suicide rush
- Zombies teach **faction awareness**: raised zombies attack player, not necromancer

---

### Lich (Arch-Necromancer): Soul Bolt + Command + Death Siphon

**Implementation Date:** 2026-01-02

**Identity:** Elite undead controller with powerful personal abilities and necromancer corpse economy.

**Mechanics:**

1. **Soul Bolt (2-turn telegraph + resolve):**
   - Turn 1 (charging): Apply ChargingSoulBoltEffect, message "channeling dark energy!"
   - Turn 2 (resolve): If player still in LOS + range, fire Soul Bolt
   - Damage: ceil(0.35 * target.max_hp) - deterministic, very high (35% max HP)
   - Range: 7 tiles
   - Cooldown: 4 turns after resolution
   - Telegraph gives player 1 turn to react (retreat, use Soul Ward scroll, etc.)

2. **Soul Ward (Counter - Scroll):**
   - Consumable: scroll_soul_ward (player starts with 2 in scenario)
   - Effect: SoulWardEffect (10 turn duration)
   - When Soul Bolt hits while ward active:
     - Reduces upfront damage by 70% (rounded up): ceil(base * 0.30)
     - Converts prevented damage to Soul Burn DOT over 3 turns
   - Example: 19 damage bolt → 6 upfront + 13 DOT (4-4-5 split)
   - Ward does NOT trivialize bolt; it reshapes it into manageable DOT

3. **Soul Burn (DOT from Ward):**
   - 3-turn deterministic DOT
   - Damage split: total_damage // 3 per turn, remainder on last tick
   - Example: 13 damage → 4-4-5 over 3 turns
   - Status effect: SoulBurnEffect

4. **Command the Dead (Passive Aura):**
   - Allied undead within radius 6 get +1 to-hit
   - Applied during attack_d20() in fighter.py
   - Faction-aware: only undead faction allies benefit
   - Deterministic, fast (no scanning every frame; computed during attack roll)

5. **Death Siphon (Passive Heal):**
   - When allied undead dies within radius 6, lich heals 2 HP
   - Capped at missing HP (no overheal)
   - Hooked into death finalization path in death_functions.py
   - Deterministic

6. **AI Behavior:**
   - Priority 1: If charging Soul Bolt, resolve it if able (LOS + range)
   - Priority 2: If Soul Bolt off cooldown + not charging, start charge
   - Priority 3: Fallback to necromancer base behavior (raise dead, corpse seeking, hang-back)
   - Inherits NecromancerBase patterns: avoid moving within 2 tiles of player, prefer distance 4-7

**Stats (config/entities.yaml):**
```yaml
lich:
  hp: 40
  power: 2
  defense: 2
  xp: 150
  damage_min/max: 3-6 (weak melee)
  faction: undead
  ai_type: lich
  soul_bolt_range: 7
  soul_bolt_damage_pct: 0.35
  soul_bolt_cooldown_turns: 4
  command_the_dead_radius: 6
  death_siphon_radius: 6
  action_enabled: true  # Can still raise dead like necromancer
  action_range: 5
  summon_monster_id: zombie
  etp_base: 131  # Elite controller
```

**Scenario:** `config/levels/scenario_monster_lich_identity.yaml`
- 1 Lich + 4 skeletons in 17x17 arena
- Lich positioned at back, skeletons guard flanks
- Player starts with dagger + equipment scattered (shortbow, longsword, arrows)
- 2 soul_ward scrolls + 4 healing potions available
- Expected behavior:
  - Soul Bolt charges and fires multiple times per run
  - Soul Ward used tactically when lich charges
  - Skeletons benefit from Command the Dead (+1 to-hit)
  - Lich heals via Death Siphon when skeletons die
- 30 runs, 300 turn limit

**Expected Metrics (30 runs):**
- `lich_soul_bolt_casts`: >= 20 (frequent casting)
- `soul_ward_blocks`: >= 15 (counterplay used)
- `lich_death_siphon_heals`: >= 60 (4 skeletons × ~15 runs)
- Player deaths: <= 15 (dangerous but counterable)

**Enforcement Test:**
- `tests/integration/test_lich_identity_scenario_metrics.py`
- Marked @pytest.mark.slow
- Asserts minimum Soul Bolt casts, Soul Ward blocks, Death Siphon heals
- Validates balance: player should win most runs with proper tactics

**Balance Impact:**
- ETP: 131 (elite controller with strong personal threat)
- No baseline changes required
- Included in full balance suite (not fast mode)
- Expected: ~40+ kills (1 lich + 4 skeletons per run)
- Expected player deaths: <= 15 (lich is dangerous but ward + tactics help)
- Soul Bolt is high-threat but telegraphed (1 turn warning)
- Soul Ward reshapes damage, doesn't eliminate it (upfront + DOT)

**Teaching Moment:**
- Soul Bolt telegraph teaches **positioning**: player learns to retreat when lich charges
- Soul Ward teaches **resource management**: use scrolls proactively when lich charges
- Command the Dead teaches **target priority**: kill lich to weaken undead allies
- Death Siphon teaches **kill order**: focus lich before clearing skeletons
- Combined: lich is a high-priority target that rewards tactical play

---

## Future Abilities (Planned)

- **Corpse Explosion:** Necromancer ability targeting consumed corpses for AoE damage (requires corpse persistence invariant)

(Phase 19 complete!)

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

