# 🚀 Next Session: Phase 4 Environmental Lore - Minimal Context Request

**Copy this entire section to start a new session with the agent.**

---

## ✨ **Session Brief (All You Need)**

**Project:** Yarl (Traditional Roguelike in Python)  
**Current Status:** ✅ Phases 1-5 of Victory Condition complete (6 endings, all tested)  
**Next Work:** **Phase 4 Environmental Lore** (2-3 weeks)  
**Goal:** Add atmospheric story lore through signposts, murals, and easter eggs

---

## 🎯 **What We're Implementing**

### Phase 4: Environmental Lore (Next 2-3 weeks)

**What:** Player discovers Zhyraxion & Entity's backstory through environmental clues

**Three Components:**

1. **Signpost Lore** (Low effort)
   - Integrate ending-specific content into existing signpost system
   - Hints about true name, ritual, endings
   - Messages vary by dungeon level

2. **Murals & Inscriptions** (Medium effort)
   - Examinable wall decorations with backstory
   - Visual depictions of Entity's power/curse
   - Clues for observant players

3. **Easter Eggs** (Low effort)
   - Special interactions for deep lore
   - Rewards for exploration
   - Secret connections between phases

**Files to Create/Modify:**
- `config/signpost_messages.yaml` - Add ending-specific content
- `config/murals_inscriptions.yaml` - NEW file for mural content
- `map_objects/game_map.py` - Add mural entity generation

**Test Files to Add:**
- `tests/test_phase4_environmental_lore.py` - Signpost/mural integration tests

---

## 📚 **Quick Reference**

**For complete strategy, read:** `SESSION_HANDOFF_NEXT.md` (10 min)  
**For technical details, read:** `VICTORY_CONDITION_PHASES.md` → Phase 4 section  
**For quick setup, read:** `SESSION_HANDOFF_TEMPLATE.md` (quick facts section)

---

## ✅ **Handoff Context Already Prepared**

All strategic decisions made. Just execute Phase 4:

- ✅ Project direction: Path A (Story Arc Completion)
- ✅ Vision: "The moddable story-rich portal roguelike"
- ✅ Phases 1-5: Complete and verified (2432 tests passing)
- ✅ Next phases: Phase 4 → Phase 7 → Portal System
- ✅ Timeline: 8-12 weeks to beta-ready "exceptional" state

---

## 🏃 **Get Started (5 Steps)**

1. **Read docs** (10 min):
   - `SESSION_HANDOFF_NEXT.md` for strategy
   - `VICTORY_CONDITION_PHASES.md` for Phase 4 tech specs

2. **Create branch**:
   ```bash
   git checkout -b feature/phase4-environmental-lore
   ```

3. **Implement**:
   - Add signpost lore entries to `config/signpost_messages.yaml`
   - Create `config/murals_inscriptions.yaml`
   - Modify `map_objects/game_map.py` for mural generation
   - Write tests in `tests/test_phase4_environmental_lore.py`

4. **Test**:
   ```bash
   make test
   # Should pass all 2432+ tests
   ```

5. **Commit**:
   ```bash
   git commit -m "Add Phase 4: Environmental Lore

   - Integrate ending-specific signpost messages
   - Create murals & inscriptions with backstory
   - Add easter eggs for deep exploration
   - 100% test coverage maintained"
   ```

---

## 💡 **Key Context (If Needed)**

**Story Arc Completed:**
- Phase 1: Amulet → Portal → Victory system
- Phase 2: Entity dialogue progression (Curious→Enraged)
- Phase 3: Guide NPC reveals true name
- Phase 5: Six distinct endings with cutscenes

**What Phases 4-7 Add:**
- Phase 4: Lore atmosphere (you are here)
- Phase 7: Assassin urgency mechanics
- Portal: Legendary tactical gameplay feature

**Architecture:**
- ECS entity system
- YAML-driven configuration
- State machine for game states
- 2432 passing tests (production quality)

---

## 🚨 **No New Context Needed**

Agent should **NOT** ask for:
- What's been done (documented in SESSION_HANDOFF_NEXT.md)
- Architecture details (documented in SESSION_HANDOFF_TEMPLATE.md)
- Phase specifications (documented in VICTORY_CONDITION_PHASES.md)
- Test procedures (documented in PHASE5_TESTING_PLAN.md)

Agent **SHOULD** ask for:
- Specific content for signpost/mural messages (lore writing)
- Design decisions on easter egg mechanics
- Questions about implementation details

---

## ✨ **Success Criteria**

Phase 4 is complete when:
- ✅ Signpost lore content integrated (10+ new messages)
- ✅ Mural/inscription system implemented
- ✅ Easter eggs added (3+ special interactions)
- ✅ All tests passing (2432+)
- ✅ No regressions in existing systems
- ✅ Committed with descriptive message

---

**Ready to code!** 🎮

All planning done. Just execute Phase 4.

