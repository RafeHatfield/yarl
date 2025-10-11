# Boss Fights Implementation Plan

**Feature:** Boss Encounters with Unique Mechanics  
**Branch:** `feature/boss-fights`  
**Target Version:** v3.9.0  
**Estimated Time:** 2-3 days (8 slices)

---

## 🎯 Goals

1. Add 2-3 boss monster types with unique abilities
2. Integrate with existing BossRoomGenerator
3. Guarantee legendary loot drops from bosses
4. Boss-specific dialogue and personality
5. Test harness in level_templates_testing.yaml

---

## 📋 Implementation Slices

### Slice 1: Boss Monster Definitions (30 mins) ✅ TESTABLE
**Branch Checkpoint:** `slice-1-boss-definitions`

**What:**
- Add boss entries to `config/entities.yaml`
- Dragon Lord: High HP, high power, fire-themed
- Demon King: High HP, medium power, curse-themed
- Mark as boss with `is_boss: true` flag

**Testable:**
- Boss monsters can be spawned
- Boss stats are significantly higher than normal monsters
- Boss flag is set correctly

**Files:**
- `config/entities.yaml` (add 2 boss entries)

**Acceptance Criteria:**
- [ ] Dragon Lord defined with ~100 HP, 10-15 power
- [ ] Demon King defined with ~80 HP, 8-12 power
- [ ] Both marked with `is_boss: true`
- [ ] Can instantiate via entity factory
- [ ] Smoke tests pass

---

### Slice 2: Test Level Configuration (15 mins) ✅ TESTABLE
**Branch Checkpoint:** `slice-2-test-level`

**What:**
- Modify `config/level_templates_testing.yaml`
- Add guaranteed boss spawn on level 5
- Add boss room template

**Testable:**
- Load test config
- Generate level 5
- Boss spawns in boss room

**Files:**
- `config/level_templates_testing.yaml`

**Acceptance Criteria:**
- [ ] Level 5 configured with boss spawn
- [ ] Boss room is large (12x12+)
- [ ] Boss spawns correctly in test mode
- [ ] Can playtest to level 5

---

### Slice 3: Boss Component (45 mins) ✅ TESTABLE
**Branch Checkpoint:** `slice-3-boss-component`

**What:**
- Create `components/boss.py`
- `Boss` component with:
  - `is_boss: bool`
  - `boss_name: str`
  - `phase: int` (for multi-phase bosses)
  - `enrage_threshold: float` (HP% to enrage)
  - `dialogue: Dict[str, List[str]]`

**Testable:**
- Component can be added to entities
- Component serializes/deserializes
- Boss detection works in combat

**Files:**
- `components/boss.py` (new, ~100 lines)
- `components/__init__.py` (add Boss import)
- `tests/test_boss_component.py` (new, ~80 lines)

**Acceptance Criteria:**
- [ ] Boss component created with all fields
- [ ] Can attach to entities
- [ ] 5+ unit tests passing
- [ ] Integration with entity factory

---

### Slice 4: Boss Loot Integration (30 mins) ✅ TESTABLE
**Branch Checkpoint:** `slice-4-boss-loot`

**What:**
- Modify `components/monster_equipment.py`
- Add boss loot logic: guaranteed legendary + 2-3 items
- Check for Boss component in `drop_monster_loot()`

**Testable:**
- Kill boss monster
- Verify legendary drop
- Verify multiple items

**Files:**
- `components/monster_equipment.py` (modify)
- `tests/test_loot_system.py` (add boss loot tests)

**Acceptance Criteria:**
- [ ] Bosses drop 100% legendary weapon or armor
- [ ] Bosses drop 2-3 total items
- [ ] Normal monsters still use normal loot system
- [ ] 3+ tests for boss loot

---

### Slice 5: Boss Dialogue System (45 mins) ✅ TESTABLE
**Branch Checkpoint:** `slice-5-boss-dialogue`

**What:**
- Create `boss_dialogue.py`
- Dialogue triggers:
  - On boss spawn (introduction)
  - When boss takes damage (taunts)
  - When boss below 50% HP (enrage)
  - When boss below 25% HP (desperate)
  - On boss death (final words)

**Testable:**
- Trigger each dialogue state
- Verify messages appear
- Verify timing is correct

**Files:**
- `boss_dialogue.py` (new, ~150 lines)
- `tests/test_boss_dialogue.py` (new, ~60 lines)

**Acceptance Criteria:**
- [ ] 5 dialogue states implemented
- [ ] Dragon Lord has 3+ lines per state
- [ ] Demon King has 3+ lines per state
- [ ] Messages use MessageBuilder
- [ ] 4+ tests passing

---

### Slice 6: Boss AI Behavior (60 mins) ✅ TESTABLE
**Branch Checkpoint:** `slice-6-boss-ai`

**What:**
- Create `BossAI` class in `components/ai.py`
- Inherits from BasicMonster
- Special behaviors:
  - Area attacks (hit player + adjacent tiles)
  - Summon minions at 50% HP
  - Enrage mode (increased damage)
  - Never confused/affected by most status effects

**Testable:**
- Boss AI makes decisions
- Area attacks work
- Enrage triggers correctly
- Status effect resistance

**Files:**
- `components/ai.py` (add BossAI class)
- `tests/test_boss_ai.py` (new, ~100 lines)

**Acceptance Criteria:**
- [ ] BossAI class implemented
- [ ] Area attack logic works
- [ ] Enrage mode increases damage by 50%
- [ ] 6+ tests covering boss behaviors

---

### Slice 7: Boss Special Abilities (60 mins) ✅ TESTABLE
**Branch Checkpoint:** `slice-7-boss-abilities`

**What:**
- Add boss-specific spells/abilities
- Dragon Lord:
  - Fire Breath (cone attack, 3-tile range)
  - Wing Buffet (knockback player)
  - Summon Fire Elementals (at 50% HP)
- Demon King:
  - Curse (reduce player damage)
  - Life Drain (heal self, damage player)
  - Teleport (tactical repositioning)

**Testable:**
- Each ability can be triggered
- Abilities have correct effects
- Cooldowns work properly

**Files:**
- `boss_abilities.py` (new, ~200 lines)
- `tests/test_boss_abilities.py` (new, ~120 lines)

**Acceptance Criteria:**
- [ ] 6 boss abilities implemented
- [ ] Each ability has proper damage/effects
- [ ] Abilities integrate with combat system
- [ ] 8+ tests covering all abilities

---

### Slice 8: Integration & Polish (60 mins) ✅ TESTABLE
**Branch Checkpoint:** `slice-8-integration`

**What:**
- Integrate all pieces:
  - Boss spawns in boss rooms
  - Boss dialogue triggers at right times
  - Boss AI uses special abilities
  - Boss drops legendary loot
- Add boss victory tracking to statistics
- Polish messages and feedback

**Testable:**
- Full playthrough to boss
- Kill boss
- Verify all systems work together

**Files:**
- `components/statistics.py` (add boss_kills tracking)
- `death_screen.py` (show boss kills)
- Integration testing

**Acceptance Criteria:**
- [ ] Full boss encounter works end-to-end
- [ ] Boss dialogue flows naturally
- [ ] Legendary loot drops correctly
- [ ] Statistics track boss victories
- [ ] All smoke tests pass
- [ ] 2+ integration tests

---

## 📊 Success Metrics

**Code Quality:**
- [ ] All slices tested individually
- [ ] 30+ new tests, all passing
- [ ] No regressions in existing tests
- [ ] Type hints on all new code

**Gameplay:**
- [ ] 2 unique boss types
- [ ] Each boss has 3+ unique abilities
- [ ] Boss difficulty significantly higher than normal
- [ ] Guaranteed legendary loot is exciting

**Polish:**
- [ ] Boss dialogue is personality-rich
- [ ] Combat feedback is clear
- [ ] Victory feels earned
- [ ] Stats tracking works

---

## 🔍 Testing Strategy

### Unit Tests (per slice)
- Test each component in isolation
- Mock dependencies
- Fast execution (<1 second per test file)

### Integration Tests (Slice 8)
- Spawn boss → trigger dialogue → combat → death → loot
- Verify multi-system interactions
- Test edge cases (boss dies to hazard, etc.)

### Playtest Checklist
- [ ] Reach level 5 in test mode
- [ ] Boss spawns in large room
- [ ] Boss uses special abilities
- [ ] Dialogue appears at right times
- [ ] Kill boss, get legendary loot
- [ ] Stats show boss kill

---

## 📁 File Summary

**New Files (7):**
1. `components/boss.py` (~100 lines)
2. `boss_dialogue.py` (~150 lines)
3. `boss_abilities.py` (~200 lines)
4. `tests/test_boss_component.py` (~80 lines)
5. `tests/test_boss_dialogue.py` (~60 lines)
6. `tests/test_boss_ai.py` (~100 lines)
7. `tests/test_boss_abilities.py` (~120 lines)

**Modified Files (5):**
1. `config/entities.yaml` (add 2 bosses)
2. `config/level_templates_testing.yaml` (add boss level)
3. `components/ai.py` (add BossAI class)
4. `components/monster_equipment.py` (boss loot logic)
5. `components/statistics.py` (track boss kills)

**Total New Code:** ~800 lines + tests

---

## ⚠️ Risks & Mitigations

**Risk 1: Boss too easy/hard**
- **Mitigation:** Test at multiple player levels, adjust HP/damage

**Risk 2: Special abilities break combat system**
- **Mitigation:** Test each ability in isolation first, gradual integration

**Risk 3: Boss AI gets stuck/broken**
- **Mitigation:** Inherit from proven BasicMonster AI, only override specific behaviors

**Risk 4: Performance with boss abilities**
- **Mitigation:** Profile area attacks, ensure <100ms execution

---

## 🚀 Deployment Plan

1. **Merge to main** after Slice 8 complete
2. **Tag as v3.9.0**
3. **Create release notes** highlighting boss fights
4. **Update ROADMAP.md** marking boss fights complete
5. **Optional:** Create boss fight showcase video

---

## 📝 Next Steps After Completion

**Immediate Follow-Ups:**
- Add 1-2 more boss types (easy now!)
- Boss-specific loot tables (themed drops)
- Multi-phase boss encounters (phase 2 transformation)

**Future Enhancements:**
- Boss arenas with environmental hazards
- Boss minion waves
- Boss achievement system
- Legendary boss items (unique one-per-game drops)

---

**Status:** Ready to begin!  
**First Slice:** Boss Monster Definitions  
**Estimated Completion:** Slice 1 by end of current session

