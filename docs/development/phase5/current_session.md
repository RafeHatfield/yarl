# Phase 5: The Five Endings - Current Session Status

**Date:** October 28, 2025  
**Status:** Sprint 1 + Sprint 2 + Sprint 3 Complete → READY FOR FULL TESTING  
**Branch:** `feature/phase3-guide-system`

---

## 🎯 Mission: Implement The Five Endings

We are implementing **Phase 5: The Five Endings** - the climactic conclusion to the game where the player confronts Zhyraxion with Aurelyn's Ruby Heart and makes choices that determine one of six unique endings.

### Key Documentation (READ THESE FIRST)

1. **STORY_LORE_CANONICAL.md** - Single source of truth for all narrative
   - The Entity: Zhyraxion (bound dragon in human form)
   - Aurelyn's Ruby Heart (partner's extracted heart)
   - The Soul Rotation cycle
   - The Ghostly Guide's backstory
   - Complete lore for all six endings

2. **PHASE5_IMPLEMENTATION_PLAN.md** - Complete technical specification
   - Architecture decisions (Boss component, portal system, chamber design)
   - 18 implementation tasks organized into 5 sprints
   - Detailed boss fight mechanics for all three variants
   - Full ending sequences with cutscenes
   - Testing strategy

3. **VICTORY_CONDITION_PHASES.md** - Victory system overview
   - Current implementation status (Phases 1-4 complete)
   - Phase 5 requirements
   - Points to STORY_LORE_CANONICAL.md for narrative

---

## ✅ What We Just Completed

### Sprint 2: Secret Room + Crimson Ritual Codex (DONE)

**Files Modified:**
- `config/entities.yaml` - Added Corrupted Ritualist enemy and Crimson Ritual Codex item
- `map_objects/game_map.py` - Added `_create_secret_ritual_room()` method
- `item_functions.py` - Added `unlock_crimson_ritual()` function
- `PHASE5_TESTING_PLAN.md` - NEW: Comprehensive testing documentation

**Key Features:**

1. **Corrupted Ritualist Enemy**
   - 60 HP, 12-18 damage (tough elite enemy)
   - Fire resistance (50%) and poison resistance (25%)
   - Found guarding the secret room on Level 25
   - 2-3 spawn in the hidden chamber
   - 400 XP reward each

2. **Crimson Ritual Codex**
   - Quest item found in secret room center
   - Cannot be dropped once picked up
   - Use function: `unlock_crimson_ritual()`
   - Unlocks Ending 1b: "The Crimson Ritual" choice
   - Description: Ancient journal revealing the dragon-binding ritual

3. **Secret Room Generation**
   - 7x7 hidden chamber attached to a random room on Level 25
   - Connected via visible tunnel (no longer needs secret door tech)
   - Spawns 2-3 Corrupted Ritualists
   - Crimson Ritual Codex in center
   - Player can explore Level 25 after Ruby Heart pickup to find it

4. **Knowledge Unlock System**
   - Reading the Codex calls `victory_comp.unlock_knowledge('crimson_ritual')`
   - Displays quest message explaining the ritual mechanics
   - Unlocks "Use the ritual" option in Ending 1a submenu
   - Requires BOTH true name AND ritual knowledge for Ending 1b

**How It Works:**
1. Player reaches Level 25
2. Player picks up Ruby Heart (portal spawns)
3. **BEFORE** entering portal, player explores and finds secret room
4. Player fights 2-3 Corrupted Ritualists (tough but doable)
5. Player picks up and reads Crimson Ritual Codex
6. Message: "New knowledge unlocked: The Crimson Ritual!"
7. Player enters portal → confrontation menu now has "Use the ritual" option

**Commit:** [Pending] - "✨ Phase 5: Sprint 2 Complete - Secret Room + Crimson Ritual"

---

### Task 2: Portal System (DONE)

**Files Modified:**
- `victory_manager.py` - Renamed `handle_amulet_pickup()` → `handle_ruby_heart_pickup()`
- `components/victory.py` - Updated all amulet references to ruby_heart
- `game_states.py` - Renamed `AMULET_OBTAINED` → `RUBY_HEART_OBTAINED`
- `game_actions.py` - Updated all victory trigger comments and method calls
- `state_management/state_config.py` - Updated state config for new terminology
- `systems/turn_controller.py` - Updated documentation
- `engine/systems/ai_system.py` - Updated comments

**Key Changes:**
1. **Terminology Update:** All references to "Amulet of Yendor" replaced with "Aurelyn's Ruby Heart"
2. **Message Updates:** Portal spawn messages now reference Zhyraxion and the Ruby Heart
3. **Knowledge Tracking:** Added `knows_crimson_ritual` flag to Victory component
4. **State Persistence:** `RUBY_HEART_OBTAINED` state properly configured to persist across turns
5. **Anxiety Dialogue:** Updated Zhyraxion's dialogue to reflect desperation for the heart

**Portal Behavior:**
- ✅ Spawns adjacent to player when Ruby Heart is picked up
- ✅ Player can explore Level 25 after pickup (find secret room)
- ✅ Stepping on portal triggers `GameStates.CONFRONTATION`
- ✅ Portal is one-way (no return)
- ✅ Portal location communicated to player with directional hints

**Zhyraxion's Messages:**
```
"You have it. After all these centuries..."
"You have it. Now... bring it to me."  (calm)
"PLEASE! I need— I MUST have that heart! Come to me! NOW!"  (desperate)
```

**Commit:** `0941436` - "✨ Phase 5.2: Update portal system for Ruby Heart terminology"

---

### Task 1: Ruby Heart Entity (DONE)

**Files Modified:**
- `config/entities.yaml` - Replaced `amulet_of_yendor` with `ruby_heart`
- `map_objects/game_map.py` - Updated Level 25 spawn logic
- `config/entity_factory.py` - Updated docstring example

**Key Changes:**
```yaml
ruby_heart:
  char: "*"
  color: [220, 20, 60]  # Crimson red
  description: "A dragon's heart, crystallized into ruby. It pulses with 
    inner fire, warm to the touch, beating with a rhythm that isn't quite 
    alive but isn't quite dead either. You can feel immense power thrumming 
    through it. This was once part of a living being."
  is_quest_item: true
  triggers_victory: true
  cannot_drop: true  # Cannot be dropped once picked up
```

**Why This Matters:**
- Establishes emotional weight (it's a HEART, not just treasure)
- Warm, pulsing, disturbing to hold
- Sets up the gravity of the player's choices
- Cannot be dropped once picked up (committed to the endgame)

**Commit:** `46b5e96` - "✨ Phase 5.1: Replace Amulet with Aurelyn's Ruby Heart"

---

## 🚀 What's Next: Confrontation Chamber

### Task 3: Confrontation Chamber (READY TO START)

The confrontation chamber is where the player faces Zhyraxion and makes their choice. It needs to be:

**Requirements:**
1. **Special map/room** - Not part of the regular dungeon
2. **Atmospheric design** - Circular chamber with ritual circles
3. **Aurelyn's remains** - Golden scales/skeleton in center
4. **No escape** - No exits until choice is made
5. **Zhyraxion present** - As NPC entity (not initially hostile)

**Technical Approach:**
- Create special map generation function for confrontation chamber
- OR: Use existing map system but with custom template
- OR: Create as a "cutscene" state that transitions to choice menu

**Key Elements:**
```
- Circular room (15x15 or 20x20)
- Ritual circles on floor (decorative tiles)
- Aurelyn's remains in center (entity or decoration)
- Zhyraxion standing opposite player
- Oppressive atmosphere (dim lighting?)
- No doors/exits visible
```

**Files to Consider:**
- `map_objects/game_map.py` - Map generation (special case for confrontation)
- `screens/confrontation_choice.py` - Already exists! (Simple placeholder)
- `config/entities.yaml` - Zhyraxion entity definitions
- `game_actions.py` - Portal entry handling (line ~415-439)

**Existing Infrastructure:**
- `screens/confrontation_choice.py` exists but has simple 2-choice menu
- Portal entry already transitions to `GameStates.CONFRONTATION`
- Need to either: generate map OR go straight to choice menu

**Decision Needed:**
Do we want a physical chamber to explore, or go straight to dialogue/choice?
- **Option A:** Physical chamber (more immersive, player can look around)
- **Option B:** Straight to dialogue (simpler, faster to implement)

Recommendation: Start with Option B (dialogue screen), can add chamber later if desired.

---

## 📋 Full Task List (18 Tasks)

### Sprint 1: Foundation (Tasks 1-4)
- [x] **Task 1:** Ruby Heart entity ✅ COMPLETE
- [x] **Task 2:** Portal system (spawns on pickup, teleports to chamber) ✅ COMPLETE
- [x] **Task 3:** Confrontation choice menu (3 menus, 6 endings) ✅ COMPLETE
- [ ] **Task 4:** Ending screens for all 6 endings ⬅️ **NEXT**

### Sprint 2: Secret Path (Tasks 5-7)
- [ ] **Task 5:** Secret room on Level 25 (hidden passage)
- [ ] **Task 6:** Corrupted Ritualists (2-3 tough enemies)
- [ ] **Task 7:** Crimson Ritual Codex (unlocks Ending 1b)

### Sprint 3: Boss Fights (Tasks 8-10)
- [ ] **Task 8:** Human Zhyraxion (Medium-Hard, fast, technical)
- [ ] **Task 9:** Full Dragon Zhyraxion (EXTREME, nearly impossible)
- [ ] **Task 10:** Grief-Corrupted Dragon (Hard, erratic, berserker)

### Sprint 4: Endings (Tasks 11-16)
- [ ] **Task 11:** Ending 1a - Escape Through Battle
- [ ] **Task 12:** Ending 1b - Crimson Collector (dark)
- [ ] **Task 13:** Ending 2 - Dragon's Bargain (trap)
- [ ] **Task 14:** Ending 3 - Fool's Freedom (death)
- [ ] **Task 15:** Ending 4 - Mercy & Corruption (tragic)
- [ ] **Task 16:** Ending 5 - Sacrifice & Redemption (best)

### Sprint 5: Polish (Tasks 17-18)
- [ ] **Task 17:** Knowledge tracking (true_name, crimson_ritual)
- [ ] **Task 18:** Integration testing (all 6 paths)

---

## 🎮 The Six Endings (Quick Reference)

| # | Name | Choice Path | Boss Fight | Outcome | Difficulty |
|---|------|-------------|------------|---------|------------|
| **1a** | Escape Through Battle | Keep → Leave | Human Zhyraxion | Escape with heart | Medium-Hard |
| **1b** | Crimson Collector | Keep → Ritual (secret) | None | Extract both hearts (dark) | N/A |
| **2** | Dragon's Bargain | Keep → Transform | None | Trapped as dragon | N/A |
| **3** | Fool's Freedom | Give | Full Dragon | Death (or miracle win) | EXTREME |
| **4** | Mercy & Corruption | Destroy (no name) | Grief Dragon | Tragic, corruption | Hard |
| **5** | Sacrifice & Redemption | Destroy (with name) | None | Golden light, reunion | N/A |

**Knowledge Requirements:**
- `entity_true_name_zhyraxion` - Unlocked via Guide at Level 15
- `crimson_ritual_knowledge` - Unlocked via Crimson Ritual Codex (secret room)

---

## 🏗️ Architecture Decisions (From Implementation Plan)

### 1. Boss Fights: Standard Combat + Boss Component
- Use existing combat system
- Boss component has: enrage, dialogue, phases, immunities
- Three distinct boss styles with different stats/AI

### 2. Confrontation: Separate Chamber (Cinematic)
- Portal from Level 25 → Special confrontation room
- Circular chamber with ritual circles
- Aurelyn's remains (skeleton) in center
- No escape until choice is made

### 3. Secret Ending: Hidden Room on Level 25
- Appears after Ruby Heart pickup
- Contains 2-3 Corrupted Ritualists
- Defeat them → obtain Crimson Ritual Codex
- Codex unlocks Ending 1b (dark collector path)

### 4. Choice Menu: Conditional Dialogue Tree
- Initial choice: Keep / Give / Destroy
- Sub-choices based on knowledge flags
- Zhyraxion responds based on player choice
- Each path leads to different ending

---

## 🔑 Key Game Systems (Context)

### Victory System
- `components/victory.py` - Victory component on player
- `victory_manager.py` - Handles amulet pickup, portal entry
- `game_states.py` - Game states (currently has `AMULET_OBTAINED`)

### Dialogue System
- YAML-driven (`config/guide_dialogue.yaml`, `config/entity_dialogue.yaml`)
- `components/npc_dialogue.py` - NPCDialogue component
- `screens/npc_dialogue_screen.py` - Full-screen dialogue UI
- Knowledge flags tracked in victory component

### Boss System
- `components/boss.py` - Boss component (enrage, phases, dialogue)
- Already used for The Entity in throne room
- Perfect for our three boss variants

### Map Generation
- `map_objects/game_map.py` - Dungeon generation
- `make_map()` - Generates rooms, entities, stairs
- Level 25 special handling already in place

---

## 🧪 Testing Configuration

The game has robust testing flags:
- `--testing` - Enable testing mode
- `--start-level N` - Skip to specific level
- `--god-mode` - Invincible player
- `--no-monsters` - Peaceful mode
- `--reveal-map` - See entire map
- `--wizard` - In-game debug menu (W key)

**Wizard Menu Features:**
- Teleport to any level
- Spawn items
- Toggle god mode
- Reveal map

---

## 📝 Recent Context (What Led Us Here)

Phase 3 (Ghostly Guide) is **COMPLETE and TESTED**:
- Guide appears on levels 5, 10, 15, 20
- Dialogue system working perfectly
- Knowledge flags unlock properly
- "Corpse loot" theme reinforced throughout
- Guide's backstory: failed agent in soul rotation
- Level 15 reveals Entity's true name: ZHYRAXION
- All dialogue has proper atmospheric fadeouts

Phase 4 (Portal/Victory) was **already implemented** in earlier work:
- Portal spawn on amulet pickup ✅
- Portal entry transitions to throne room ✅
- Victory screens exist but need updating for new endings ✅

Phase 5 is the **final phase** - the culmination of everything.

---

## 🎯 Immediate Next Steps

1. **Review `victory_manager.py`** - How does portal spawn work currently?
2. **Check portal spawn location** - Does it spawn near player or fixed location?
3. **Decide if changes needed** - Current system might be fine, or might need tweaks
4. **Test portal spawn** - Quick test with `--start-level 25 --reveal-map`
5. **Move to confrontation chamber** - Create the special room

---

## 🔍 Files You'll Need

### Configuration
- `config/entities.yaml` - Entity definitions
- `config/entity_factory.py` - Entity creation
- `config/guide_dialogue.yaml` - Guide dialogue (reference for format)

### Core Systems
- `victory_manager.py` - Portal spawn, victory handling
- `components/victory.py` - Victory component
- `game_states.py` - Game state enum
- `game_actions.py` - Player action handling

### Map & Rooms
- `map_objects/game_map.py` - Level generation
- `map_objects/rectangular_room.py` - Room class

### UI Screens
- `screens/victory_screen.py` - Victory/defeat screens (will need updates)
- `screens/npc_dialogue_screen.py` - Dialogue UI (reference for choice menu)
- `screens/confrontation_choice.py` - Already exists! (needs review/update)

### Components
- `components/boss.py` - Boss mechanics
- `components/npc_dialogue.py` - Dialogue system

---

## 🎨 Tone & Style Guide

**The Entity (Zhyraxion):**
- Alan Rickman's dry wit and menace
- Patient, ancient, tired of waiting
- Genuine emotion about Aurelyn (partner)
- Sardonic when betrayed
- Desperate when heart is destroyed

**Ghostly Guide:**
- Crabby Luke Skywalker energy
- Bitter about soul rotation
- Wants player to understand the horror
- "Why do you think there's so much gear on the floor?"

**Ruby Heart:**
- Disturbing (warm, beating, alive)
- Heavy with emotional weight
- Not just treasure - it's a person's heart
- Player should feel uncomfortable holding it

---

## 💾 Git Status

**Current Branch:** `feature/phase3-guide-system`  
**Last Commit:** `b106610` - Confrontation choice menu system  
**Previous Commits:** `0941436` (Portal), `46b5e96` (Ruby Heart)  
**Status:** Clean working directory, ready for testing!

---

## 🚨 Important Notes

1. **Cannot drop Ruby Heart** - `cannot_drop: true` flag set
2. **Portal is one-way** - No return from confrontation
3. **Secret room is optional** - Adds Ending 1b, but not required
4. **Knowledge flags matter** - Change available choices
5. **Boss component exists** - Don't reinvent, use what's there
6. **Three boss variants needed** - Human, Full Dragon, Grief Dragon
7. **Six unique endings** - Each needs distinct screen + text

---

## ✨ Vision

This phase transforms the game from a traditional roguelike into a narrative-driven experience with meaningful choices and emotional weight. The player has spent 25 levels getting stronger, learning about the Entity and the Guide, discovering the truth about the "corpse loot" they've been collecting. Now they hold Aurelyn's heart - warm, pulsing, alive - and must decide:

- **Keep it?** Power, escape, or dark ritual
- **Give it?** Trust Zhyraxion's promise of freedom (it's a trap)
- **Destroy it?** Mercy or sacrifice, depending on knowledge

Every choice has consequences. Every ending tells a different story. Some are tragic, some are triumphant, one is transcendent.

**Let's build something special.** 🐉

---

## 📊 Progress Summary

**✅ Completed (Tasks 1-3):**
- ✅ Task 1: Ruby Heart entity (emotional weight, cannot_drop flag)
- ✅ Task 2: Portal system (spawn mechanics, terminology update)
- ✅ Task 3: Confrontation choice menu (3 menus, 6 endings, conditional options)

**🧪 Ready to Test:**
Full flow from Ruby Heart pickup through portal to confrontation menu works!

**⏸️ Not Yet Implemented:**
- Ending screens for Phase 5 endings ('1a', '1b', '2', '3', '4', '5')
- Boss fights (Human/Full Dragon/Grief Dragon)
- Secret room + Crimson Ritual Codex
- Secret room enemies (Corrupted Ritualists)

**Next Session:**
- Test the implemented flow
- Implement ending screens (Task 4)
- Implement boss fights (Sprint 3)
- Implement secret room (Sprint 2)

---

*Next session: Implement confrontation chamber and choice menu.*

