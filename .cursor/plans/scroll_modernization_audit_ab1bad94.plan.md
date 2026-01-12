---
name: Scroll Modernization Audit
overview: "Modernize Dragon Fart and Fireball scrolls to follow Phase 20 patterns: single execution points, damage_service routing, canonical metrics, and deterministic scenario testing."
todos:
  - id: fix-cone-kwargs
    content: Fix SpellExecutor._cast_cone_spell kwargs bug (line 403 missing **kwargs)
    status: pending
  - id: create-sleep-effect
    content: Create SleepEffect status effect (or evaluate using existing ConfusedEffect with proper ticking)
    status: pending
  - id: refactor-env-hazards
    content: Refactor EnvironmentSystem to apply status effects instead of direct damage
    status: pending
  - id: dragon-fart-executor
    content: Migrate Dragon Fart to SpellExecutor and remove bespoke item_functions path
    status: pending
  - id: add-metrics-spellexec
    content: Add metrics tracking to SpellExecutor for fireball_*/dragon_fart_* counters
    status: pending
  - id: scenario-dragon-fart
    content: Create monster_scroll_dragon_fart_identity scenario with deterministic setup
    status: pending
  - id: scenario-fireball
    content: Create monster_scroll_fireball_identity scenario with deterministic setup
    status: pending
  - id: integration-tests
    content: Create integration tests enforcing metric thresholds for both scrolls
    status: pending
---

# Legacy Scroll Audit and Modernization Plan: Dragon Fart + Fireball

---

## 1. Current-State Audit

### 1.1 Dragon Fart Scroll

**Execution Path:**

- Entry: `item_functions.cast_dragon_fart()` (lines 484-587)
- NOT delegated to SpellExecutor (unlike other spells)
- SpellCatalog has `DRAGON_FART` definition but `_cast_cone_spell` in SpellExecutor has a **broken reference** (`kwargs` undefined on line 403)

**Effect Model:**

- Immediate: Applies `ConfusedMonster` AI replacement (confusion/sleep effect)
- Tile-based: Creates `GroundHazard(HazardType.POISON_GAS)` via `item_functions` directly
- Hazard properties: `base_damage=6`, `duration=5`, `source_name="Dragon Fart"`

**Known Problems:**

1. **Bespoke path**: Does NOT use SpellExecutor - bypasses silence gating
2. **Direct AI manipulation**: Line 577-579 directly replaces AI component, not a proper status effect
3. **Hazard damage NOT routed through damage_service**: `environment_system.py` lines 186 calls `entity.fighter.take_damage()` directly
4. **No metrics tracking**: No `collector.increment()` calls for applications, ticks, damage
5. **Player vs monster asymmetry**: Sleep/confusion applied via AI swap (monsters only)
6. **Death finalization inconsistency**: `_handle_hazard_death()` uses kill_monster but doesn't call damage_service

### 1.2 Fireball Scroll

**Execution Path:**

- Entry: `item_functions.cast_fireball()` (lines 92-107) - delegates to `cast_spell_by_id("fireball", ...)`
- SpellExecutor: `_cast_aoe_spell()` (lines 233-346)
- Properly silence-gated at SpellExecutor.cast() line 61

**Effect Model:**

- Immediate: AoE damage to all entities in radius
- Tile-based: Creates `GroundHazard(HazardType.FIRE)` via SpellExecutor
- Hazard properties: `base_damage=3`, `duration=3`, `source_name="Fireball"`

**Known Problems:**

1. **Damage routed through damage_service**: Correct for immediate AoE damage (lines 307-316)
2. **Hazard damage NOT routed through damage_service**: Same as Dragon Fart - environment_system bypasses damage_service
3. **No metrics tracking**: No scroll-specific metrics (tiles_created, applications, damage, kills)
4. **Player DOES take self-damage**: This is correct AoE behavior per regression test
5. **Death finalization via environment_system**: Not using canonical damage_service path

### 1.3 Hazard System Issues (Shared)

The `EnvironmentSystem._process_hazards()` ([`engine/systems/environment_system.py`](engine/systems/environment_system.py) lines 133-197):

- Calls `entity.fighter.take_damage()` directly (line 186)
- Has its own death handling `_handle_hazard_death()` (lines 199-248)
- Does NOT use `damage_service.apply_damage()` - violates Phase 20 patterns

---

## 2. Target Architecture (Modern Pattern)

### 2.1 Dragon Fart Scroll

**Proposed Effect Model: Hybrid (Immediate Status + Lingering Hazard)**

| Phase | Effect | Implementation |

|-------|--------|----------------|

| Immediate | Sleep/Stun (replaces confusion) | New `SleepEffect` status effect with proper ticking |

| Lingering | Poison gas hazard | Unchanged `GroundHazard(POISON_GAS)` |

| Hazard DOT | When entity stands on gas | Apply `PoisonEffect` status effect, NOT direct damage |

**Execution Point:**

- Migrate fully to SpellExecutor by fixing `_cast_cone_spell` (`kwargs` bug on line 403)
- Remove bespoke `item_functions.cast_dragon_fart()` after migration

**Ticking:**

- `SleepEffect.process_turn_start()` - tick duration on owner's turn
- `PoisonEffect.process_turn_start()` - tick damage on owner's turn (already modern)
- Environment system: NO damage ticking - only hazard aging

**Silence Interaction:**

- Already gated at SpellExecutor.cast() - scroll usage blocked by silence

### 2.2 Fireball Scroll

**Proposed Effect Model: Hybrid (Immediate AoE + Lingering Hazard)**

| Phase | Effect | Implementation |

|-------|--------|----------------|

| Immediate | AoE fire damage | Already via damage_service in SpellExecutor |

| Lingering | Fire hazard | Unchanged `GroundHazard(FIRE)` |

| Hazard DOT | When entity stands on fire | Apply `BurningEffect` status effect, NOT direct damage |

**Execution Point:**

- Already in SpellExecutor - no migration needed
- Add metrics tracking to `_cast_aoe_spell()`

**Ticking:**

- `BurningEffect.process_turn_start()` - tick damage on owner's turn (already modern)
- Environment system: NO damage ticking - only hazard aging + effect application

**Silence Interaction:**

- Already gated at SpellExecutor.cast()

### 2.3 Hazard Processing Refactor

**Current Problem:** Environment system applies damage directly, bypassing damage_service.

**Proposed Pattern:**

```
EnvironmentSystem._process_hazards():
  FOR each hazard:
    FOR each entity on hazard tile:
      IF entity NOT levitating:
        APPLY status effect (BurningEffect or PoisonEffect)
        DO NOT deal direct damage
  Age all hazards
```

**Status Effect Handles:**

- Damage routing through damage_service
- Death finalization
- Metrics tracking
- Resistance application

---

## 3. Metrics Design

### 3.1 Dragon Fart Metrics

| Metric | Source of Truth | Description |

|--------|-----------------|-------------|

| `dragon_fart_casts` | SpellExecutor._cast_cone_spell | Successful cast count |

| `dragon_fart_tiles_created` | SpellExecutor._cast_cone_spell | Gas hazard tiles created |

| `dragon_fart_sleep_applications` | SleepEffect.apply() | Entities put to sleep |

| `dragon_fart_poison_applications` | PoisonEffect via hazard | Poison DOT applications from gas |

| `poison_ticks_processed` | PoisonEffect.process_turn_start | Already tracked |

| `poison_damage_dealt` | PoisonEffect.process_turn_start | Already tracked |

**Aggregation in scenario_harness:**

- Sum `dragon_fart_*` counters across runs
- Reuse existing `poison_*` metrics (no new aggregation needed)

### 3.2 Fireball Metrics

| Metric | Source of Truth | Description |

|--------|-----------------|-------------|

| `fireball_casts` | SpellExecutor._cast_aoe_spell | Successful cast count |

| `fireball_tiles_created` | SpellExecutor._cast_aoe_spell | Fire hazard tiles created |

| `fireball_direct_damage` | SpellExecutor._cast_aoe_spell | Immediate AoE damage dealt |

| `burning_applications` | BurningEffect.apply() or hazard contact | Already tracked |

| `burning_ticks_processed` | BurningEffect.process_turn_start | Already tracked |

| `burning_damage_dealt` | BurningEffect.process_turn_start | Already tracked |

**Aggregation in scenario_harness:**

- Sum `fireball_*` counters across runs
- Reuse existing `burning_*` metrics (no new aggregation needed)

---

## 4. Scenarios and Tests

### 4.1 Dragon Fart Identity Scenario

**Setup:**

```yaml
scenario_id: scroll_dragon_fart_identity
map_layout: 5x5 open room
player: center (2,2), 100 HP
monsters: 2x goblin (3,3) and (4,2) - in cone direction
items: 1x Scroll of Dragon Fart in player inventory
turn_limit: 30
```

**Behavior Validation:**

1. Player uses scroll targeting (4,2)
2. Assert: Gas hazards created in cone tiles (3+ tiles)
3. Assert: Goblins receive SleepEffect (not ConfusedMonster AI)
4. Assert: Hazard aged after environment phase
5. Assert: Entity standing on gas receives PoisonEffect
6. Assert: Poison damage routed through damage_service

**Integration Test Expectations:**

- `dragon_fart_casts >= 1`
- `dragon_fart_tiles_created >= 3`
- `dragon_fart_sleep_applications >= 1`
- `poison_applications >= 1` (from hazard contact)

**Balance Suite Thresholds (30 runs):**

- Player deaths <= 5
- Sleep applications >= 20
- Poison damage >= 30

### 4.2 Fireball Identity Scenario

**Setup:**

```yaml
scenario_id: scroll_fireball_identity
map_layout: 7x7 open room
player: corner (1,1), 100 HP
monsters: 3x orc at (4,4), (5,4), (4,5) - in AoE radius
items: 1x Scroll of Fireball in player inventory
turn_limit: 30
```

**Behavior Validation:**

1. Player uses scroll targeting (4,4) with radius 3
2. Assert: Immediate damage dealt to all 3 orcs
3. Assert: Fire hazards created in radius tiles
4. Assert: Hazard aged after environment phase
5. Assert: Entity moving into fire receives BurningEffect
6. Assert: Burning damage routed through damage_service

**Integration Test Expectations:**

- `fireball_casts >= 1`
- `fireball_tiles_created >= 7` (radius 3 circle)
- `fireball_direct_damage >= 15` (3 orcs x 5+ damage)
- `burning_applications >= 1` (from hazard contact)

**Balance Suite Thresholds (30 runs):**

- Player deaths <= 3 (fireball AoE can self-damage)
- Direct damage >= 100
- Burning damage >= 30

---

## 5. Risk Assessment

### 5.1 Turn System Risk: NONE

- No TurnManager changes required
- Status effects tick via existing `process_turn_start()` infrastructure
- Hazard aging remains in ENVIRONMENT phase

### 5.2 Movement/FOV Risk: NONE

- No changes to FOV computation
- Cone/AoE tile calculation unchanged
- Levitation check already exists for hazard immunity

### 5.3 Interaction Risks

| Effect | Interaction | Risk Level | Mitigation |

|--------|-------------|------------|------------|

| Burning | PoisonEffect from Dragon Fart | LOW | Both can stack (different effect types) |

| Burning | Fire hazard re-application | LOW | BurningEffect already handles refresh |

| Poison | Sleep from Dragon Fart | LOW | Sleep prevents actions, poison still ticks |

| Silence | Scroll usage | NONE | Already gated at SpellExecutor |

| Knockback | Hazard zones | LOW | Knocked entity may land on hazard, apply effect |

### 5.4 Migration Risks

| Risk | Impact | Mitigation |

|------|--------|------------|

| Dragon Fart AI swap removal | Behavior change | New SleepEffect with identical duration |

| Hazard direct damage removal | Damage timing | Status effects tick on entity turn, not environment phase |

| SpellExecutor kwargs bug | Broken cone spells | Fix before migration |

| Existing tests | May break | Update test expectations for new metrics |

---

## Shared Patterns / Abstractions

### Hazard-to-StatusEffect Dispatcher

Create a utility in `environment_system.py`:

```python
def _apply_hazard_effect(entity, hazard, collector):
    """Convert hazard contact into status effect application."""
    if hazard.hazard_type == HazardType.FIRE:
        effect = BurningEffect(owner=entity, duration=4, damage_per_turn=hazard.get_current_damage())
    elif hazard.hazard_type == HazardType.POISON_GAS:
        effect = PoisonEffect(owner=entity, duration=3, damage_per_turn=hazard.get_current_damage())
    
    entity.status_effects.add_effect(effect)
```

This reuses existing `BurningEffect` and `PoisonEffect` patterns from Phase 20A/B.

---

## Go / No-Go Checklist

Before implementation:

- [ ] Fix SpellExecutor `_cast_cone_spell` kwargs bug (line 403)
- [ ] Create `SleepEffect` status effect class (or reuse existing pattern)
- [ ] Verify BurningEffect and PoisonEffect work with variable damage_per_turn
- [ ] Confirm scenario harness supports new metrics
- [ ] Existing fireball/dragon_fart tests pass

During implementation:

- [ ] Route all hazard damage through status effects, not direct damage
- [ ] Add metrics tracking to SpellExecutor methods
- [ ] Create identity scenarios for both scrolls
- [ ] Update environment_system to apply effects, not damage

After implementation:

- [ ] All existing spell tests pass
- [ ] New identity scenario tests pass
- [ ] Balance suite thresholds met
- [ ] No regression in hazard save/load