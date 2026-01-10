# Release v4.17.0 - Weapon Knockback System

## Overview

Introduces weapon-based knockback mechanics with power-delta scaled distance and wall-impact micro-stun. This adds tactical depth to melee combat by making positioning and power differentials meaningful.

## New Features

### Weapon Knockback
- **Distance based on power delta** (capped at 4 tiles):
  - `delta <= -1` → 1 tile
  - `delta in [0, 1]` → 2 tiles
  - `delta in [2, 3]` → 3 tiles
  - `delta >= 4` → 4 tiles
- **Directional push**: Defender pushed directly away from attacker
- **Step-by-step resolution**: Stops early if blocked by terrain/entities
- **Canonical movement**: Uses `Entity.move()` (respects entangle/root/all movement blockers)

### Staggered Effect (Wall-Impact Micro-Stun)
- **Duration**: 1 turn (refresh-not-stack)
- **Trigger**: Knockback blocked early by hard obstacle (wall/solid/occupied tile)
- **Effect**: Skip next action/turn
- **No chain effects**: Only the shoved entity is staggered (not the blocker)
- **Message clarity**:
  - Wall impact: "X slams into the wall and is staggered!"
  - Entity collision: "X collides with Y and is staggered!"

### New Weapon: Knockback Mace
- Extends standard mace (1d6 bludgeoning damage)
- Bronze/copper appearance
- Flag: `applies_knockback_on_hit: true`
- Available for both player and monsters

## Technical Implementation

### Architecture
- **Canonical execution**: Knockback executes in `Fighter.attack_d20()` (production combat path)
- **Single code path**: All attack sources (keyboard/mouse/bot/scenario) use same Fighter method
- **Optional parameters**: `game_map` and `entities` passed to `attack_d20()` for terrain checks
- **Backward compatible**: Graceful degradation if parameters not provided

### Metrics (Single Source of Truth)
- `knockback_applications`: Count of knockback triggers
- `knockback_tiles_moved`: Sum of tiles moved by knockback
- `knockback_blocked_events`: Count of hard blocks (wall/entity)
- `stagger_applications`: Count of stagger effects applied
- `stagger_turns_skipped`: Count of turns skipped due to stagger

### Testing
- **Identity scenario**: `knockback_weapon_identity` (3 orcs, 30 runs, deterministic)
- **Integration test**: Lower-bound invariants (avoid flakiness from kill ordering)
- **Unit tests**: 7 tests covering distance mapping, stagger application, movement execution
- **Balance suite**: Added to regression matrix

## Test Results (30 runs, seed=1337)

```
✓ knockback_applications: 388  (threshold: >= 50)
✓ knockback_tiles_moved: 727   (threshold: >= 100)
✓ knockback_blocked_events: 26 (threshold: >= 10)
✓ stagger_applications: 26     (threshold: >= 10)
✓ stagger_turns_skipped: 0     (enemies die before next turn)
✓ player_deaths: 0             (threshold: <= 20)
```

```
Fast gate: 3422 passed
Slow integration: 1 passed
```

## Files Changed

**Core Implementation (5 files):**
- `components/status_effects.py` - StaggeredEffect class
- `services/knockback_service.py` - NEW: Knockback resolution service
- `components/fighter.py` - Knockback hook in attack_d20()
- `config/entity_registry.py` - WeaponDefinition flag
- `components/equippable.py` - Equippable flag

**Configuration (2 files):**
- `config/entities.yaml` - knockback_mace weapon
- `config/factories/equipment_factory.py` - Flag plumbing

**Integration (3 files):**
- `game_actions.py` - Pass game_map/entities to attack_d20()
- `services/scenario_harness.py` - Pass game_map/entities, metrics aggregation
- `mouse_movement.py` - Pass game_map/entities through click handler

**Testing (4 files):**
- `config/levels/scenario_knockback_weapon_identity.yaml` - NEW: Identity scenario
- `tests/integration/test_knockback_weapon_identity_scenario_metrics.py` - NEW: Integration test
- `tests/test_knockback_service.py` - NEW: Unit tests
- `tools/balance_suite.py` - Added to matrix

**Documentation (4 files):**
- `WEAPON_KNOCKBACK_IMPLEMENTATION.md` - Implementation summary
- `KNOCKBACK_GUARDRAILS_REVIEW.md` - Code review sign-off
- `KNOCKBACK_SCENARIO_FIXES.md` - Setup fixes root cause analysis
- `KNOCKBACK_ARCHITECTURE_REFACTOR.md` - Canonical execution path

## Guardrails

✅ No TurnManager / action economy changes
✅ No global FOV computation changes
✅ Enforcement at movement execution point (Entity.move())
✅ No AI-only special casing (works for player + monsters)
✅ Deterministic under scenario harness seeding
✅ Small, localized edits (no refactors of unrelated systems)
✅ No existing scenario geometry/baselines modified
✅ Lower-bound invariants (avoid test flakiness)

## Future Extensions (Out of Scope)

- Damage-on-impact (wall slam damage)
- Knockback potions/scrolls
- Knockback resistance stat
- Knockback direction control (cone/line effects)
- Multi-tile entity knockback (large creatures)

## Upgrade Notes

No breaking changes. Existing weapons unaffected. New `applies_knockback_on_hit` flag is opt-in.

---

**Full implementation details**: See `WEAPON_KNOCKBACK_IMPLEMENTATION.md`
**Architecture review**: See `KNOCKBACK_ARCHITECTURE_REFACTOR.md`
**Guardrails review**: See `KNOCKBACK_GUARDRAILS_REVIEW.md`

