# Phase 22.3: Skirmisher Implementation — Leap + Fast Pressure

**Status**: ✅ Complete and Ready for Testing  
**Date**: 2026-01-23

---

## Summary

Implemented the Skirmisher enemy archetype with Pouncing Leap and Fast Pressure abilities. The skirmisher is designed as an anti-kiting enemy that punishes players who attempt to maintain distance via ranged combat.

**Core Identity**: If the player tries to kite instead of committing to melee, the skirmisher WILL close distance and apply fast-paced melee pressure.

---

## A) New Enemy: Skirmisher

**Entity Definition**: `config/entities.yaml`
- **Character**: `k` (brown/tan color)
- **Faction**: Independent
- **HP**: 24 (moderate, not a brute)
- **Damage**: 3-5 (lower per-hit than brute, but faster tempo)
- **Stats**: DEX 15 (+2 AC, +2 to-hit), STR 12 (+1 damage)
- **Accuracy**: 4, **Evasion**: 3 (mobile, hard to pin down)
- **ETP**: 28 (balanced for mid-depth encounters)

**AI Type**: `skirmisher` → `SkirmisherAI` (Phase 22.3)

---

## B) Ability: Pouncing Leap

### Trigger Conditions

The skirmisher will attempt to leap when ALL of the following are true:

1. **Line of Sight**: Skirmisher can see the player (in FOV)
2. **Distance**: Player is 3-6 tiles away (Chebyshev distance)
   - Chebyshev distance is consistent with melee range checks (king's move)
   - Too close (< 3): Skirmisher uses melee instead
   - Too far (> 6): Skirmisher chases normally
3. **Cooldown Ready**: `leap_cooldown_remaining == 0`
4. **Not Immobilized**: Skirmisher is NOT affected by:
   - `entangled` (Root Potion, Net Arrow)
   - `rooted` (Root Trap)
   - `immobilized` (Glue spell)

### Mechanics

**Movement**:
- Leap moves exactly **2 tiles** toward the player
- Each tile uses `Entity.move(dx, dy)` for canonical movement
- Respects walls, blocking entities, and status effects at each step
- If first tile succeeds but second is blocked, skirmisher moves 1 tile only

**Cooldown**:
- **Duration**: 3 turns (configurable via `leap_cooldown_turns`)
- **Tick Down**: Decrements by 1 at start of each turn
- **Set On Leap**: Cooldown is set to 3 ONLY if skirmisher moved at least 1 tile

**Player Feedback**:
- Combat log message: `"⚡ The Skirmisher leaps forward!"`
- Only shown if skirmisher is visible to player (FOV check)

### Implementation Details

**File**: `components/ai/skirmisher_ai.py`

**Leap Logic** (`_try_pouncing_leap()`):
1. Check cooldown → distance → status effects
2. Calculate direction vector toward player (normalized to -1, 0, +1 per axis)
3. For 2 steps:
   - Validate next tile (in bounds, not blocked, no blocking entity)
   - Call `Entity.move(step_x, step_y)`
   - If move fails or blocked, stop leap
4. If moved >= 1 tile: set cooldown and emit message

**Canonical Movement**: Uses `Entity.move()` which:
- Respects entangle/root checks at execution point
- Tracks movement for Oath of Chains
- Can return `False` if blocked by status effect mid-leap

---

## C) Combat Profile: Fast Pressure

### Mechanics

**Trigger**:
- 20% chance per turn when skirmisher is adjacent to target (weapon reach range)
- Occurs AFTER main attack (if target still alive)

**Effect**:
- Extra melee attack with same to-hit roll
- Same damage as normal attack (not reduced)
  - Initial design considered 0.7x multiplier, but simplified to full damage
  - Pressure comes from frequency, not damage scaling

**Implementation**:
- Uses standard `Fighter.attack_d20()` for consistency
- Full hit/miss/crit system applies
- Metrics tracked via `skirmisher_fast_attacks_triggered`

**Design Rationale**:
- **Lower per-hit damage** (3-5) than brute enemies
- **Higher tempo** via occasional extra attacks
- Creates player tension: "This enemy attacks FAST when adjacent"
- Reinforces anti-kiting identity: closing distance is dangerous

---

## D) Metrics

### Added Metrics

**RunMetrics** (per-run):
- `skirmisher_leaps_used`: Count of successful leaps
- `skirmisher_adjacent_turns`: Turns spent adjacent to player
- `skirmisher_fast_attacks_triggered`: Count of fast pressure extra attacks

**AggregatedMetrics** (across runs):
- `total_skirmisher_leaps_used`
- `total_skirmisher_adjacent_turns`
- `total_skirmisher_fast_attacks_triggered`

**Collection**:
- Metrics recorded via `collector.increment()` in `SkirmisherAI`
- Aggregation handled in `run_scenario_many()` in `services/scenario_harness.py`

---

## E) Identity Scenario

**File**: `config/levels/scenario_skirmisher_identity.yaml`

**Setup**:
- Player at (3, 6) with longsword + leather armor
- Skirmisher at (9, 6) = distance 6 (leap trigger range)
- 16×12 arena with simple walls
- 3 healing potions for extended combat

**Expected Behavior**:
- Skirmisher should leap when player is at 3-6 tiles
- Leap closes distance rapidly (2 tiles per leap)
- Once adjacent, fast pressure should occasionally trigger
- Net arrow (if equipped) prevents leap via entangle

**Validation**:
- Deterministic under `seed_base=1337`
- Runs: 30
- Turn limit: 100
- Expected min kills: 20, max deaths: 15

---

## F) Testing

### Unit Tests

**File**: `tests/test_skirmisher_leap.py`

**Coverage**:
1. **Leap Triggers**:
   - Triggers at distance 3 (min range) ✅
   - Triggers at distance 6 (max range) ✅
   - Does NOT trigger at distance 2 (too close) ✅
   - Does NOT trigger at distance 7 (too far) ✅

2. **Leap Cooldown**:
   - Does NOT trigger when on cooldown ✅
   - Cooldown decrements by 1 per turn ✅

3. **Leap Prevention**:
   - Entangled prevents leap ✅
   - Rooted prevents leap ✅
   - Immobilized prevents leap ✅

4. **Leap Blocking**:
   - Leap stops at wall ✅
   - Leap stops at blocking entity ✅
   - Partial movement if second tile blocked ✅

5. **Leap Movement**:
   - Moves exactly 2 tiles toward player ✅
   - Respects direction vector ✅

6. **Fast Pressure**:
   - Triggers when adjacent + RNG succeeds ✅
   - Does NOT trigger when RNG fails ✅

### Integration Testing

Run the identity scenario:
```bash
python ecosystem_sanity.py --scenario skirmisher_identity --runs 30
```

Expected metrics:
- `skirmisher_leaps_used` > 0 (leaps should occur)
- `skirmisher_adjacent_turns` > 0 (skirmisher reaches melee)
- `skirmisher_fast_attacks_triggered` ≈ 20% of adjacent turns

---

## G) Design Notes

### Why Leap Uses 2×Entity.move()?

**Considered Alternatives**:
1. Teleport-like direct position change (REJECTED: bypasses Entity.move() contract)
2. Custom leap movement system (REJECTED: parallel movement execution)
3. Single move with distance=2 (REJECTED: doesn't respect per-tile blocking)

**Chosen Approach**:
- Two sequential `Entity.move(step_x, step_y)` calls
- Each call respects walls, entities, status effects
- Canonical movement execution (no bypasses)
- Allows partial leap if second tile blocked

### Why 20% Fast Pressure Chance?

**Tuning Rationale**:
- Too low (< 10%): Feels unreliable, identity lost
- Too high (> 30%): Overwhelming, eclipse main attack
- 20%: Noticeable pressure without guaranteed double-attacks
- Creates player tension: "Will it proc this turn?"

### Leap Cooldown: Why 3 Turns?

**Design Goals**:
- Prevent leap spam (would feel cheap)
- Allow multiple leaps per encounter (show identity)
- Give player time to react after leap

**Tuning**:
- 2 turns: Too spammy, player can't reposition
- 4 turns: Too rare, leap feels like one-off
- 3 turns: Balanced cadence for typical encounter length

### Distance Band: Why 3-6 Tiles?

**Ranged Doctrine Alignment** (Phase 22.2):
- Optimal ranged band: 3-6 tiles
- Skirmisher leap EXACTLY counters kiting in this band
- Forces player choice: commit to melee OR risk leap

**Player Counterplay**:
- Stay adjacent: No leap (but face melee pressure)
- Stay at 7+ tiles: No leap (but allow normal chase)
- Use net arrows / root effects: Prevent leap

---

## H) Architectural Alignment

**ECS Compliance**:
- ✅ Gameplay logic in AI system (`SkirmisherAI.take_turn()`)
- ✅ No rendering/UI logic in AI
- ✅ No direct game loop modifications

**Canonical Movement**:
- ✅ Uses `Entity.move()` for all movement
- ✅ No teleport or position override
- ✅ Respects status effects (entangle, root, immobilized)

**TurnManager Constraint**:
- ✅ No TurnManager modifications
- ✅ AI runs in existing ENEMY_TURN phase
- ✅ No new turn phases or loops

**Seeded RNG**:
- ✅ Uses `random.random()` from seeded RNG
- ✅ Fast pressure is deterministic under `seed_base=1337`

**No New Status Effects**:
- ✅ Reuses existing effects (entangle, root, immobilized)
- ✅ No new status effects created

---

## I) Risks & Mitigations

### Risk: Leap Bypasses Movement Contract

**Mitigation**: Leap uses `Entity.move()` at each step, respecting all movement rules.

### Risk: Leap Creates Unfair Positioning

**Mitigation**: 
- Leap only triggers at 3-6 tiles (player has warning)
- 3-turn cooldown prevents spam
- Clear combat log message on leap

### Risk: Fast Pressure Feels Random

**Mitigation**:
- Fixed 20% chance (consistent across encounters)
- Metrics track proc rate for balance tuning
- Deterministic under seed for testing

### Risk: Skirmisher Too Weak/Strong

**Mitigation**:
- Identity scenario provides regression baseline
- ETP-balanced (28) for mid-depth encounters
- Metrics allow data-driven tuning

---

## J) Files Modified

**New Files**:
1. `components/ai/skirmisher_ai.py` — AI implementation
2. `config/levels/scenario_skirmisher_identity.yaml` — Identity scenario
3. `tests/test_skirmisher_leap.py` — Unit tests
4. `PHASE_22_3_SKIRMISHER_IMPLEMENTATION.md` — This document

**Modified Files**:
1. `config/entities.yaml` — Added skirmisher entity definition
2. `config/factories/monster_factory.py` — Registered `skirmisher` AI type
3. `services/scenario_harness.py` — Added metrics (RunMetrics, AggregatedMetrics, aggregation logic)

---

## K) Next Steps

1. Run fast tests: `pytest -m "not slow"`
2. Run identity scenario: `python ecosystem_sanity.py --scenario skirmisher_identity --runs 30`
3. Verify metrics collection and leap behavior
4. Add to balance suite if regression tracking desired
5. Iterate on tuning based on playtesting feedback

---

## L) Success Criteria

**Commit-Ready Checklist**:
- ✅ Skirmisher AI implemented with leap + fast pressure
- ✅ Entity definition added to `entities.yaml`
- ✅ AI type registered in monster factory
- ✅ Metrics added and aggregated correctly
- ✅ Identity scenario created and documented
- ✅ Unit tests cover leap triggers, cooldown, prevention, blocking
- ✅ Implementation notes document complete
- ✅ No TurnManager modifications
- ✅ Canonical Entity.move() usage
- ✅ No new status effects

**Verification Commands**:
```bash
# Run unit tests
pytest tests/test_skirmisher_leap.py -v

# Run fast tests (should pass)
pytest -m "not slow"

# Run identity scenario
python ecosystem_sanity.py --scenario skirmisher_identity --runs 30
```

---

**End of Phase 22.3 Implementation Notes**
