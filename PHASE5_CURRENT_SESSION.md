# Phase 5: The Five Endings - Current Session Status

**Date:** October 27, 2025  
**Status:** Sprint 1, Task 1 Complete (Ruby Heart) → Task 2 Starting (Portal System)  
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

## 🚀 What's Next: Portal System

### Task 2: Portal System (IN PROGRESS)

The portal is the gateway to the confrontation chamber. It needs specific behavior:

**Requirements:**
1. **Spawns when Ruby Heart is picked up** - Not before
2. **Appears near the player** - On Level 25, near where the heart was
3. **Allows exploration** - Player can find secret room before entering
4. **One-way transport** - Takes player to Confrontation Chamber (no return)
5. **Visual clarity** - Should be obvious it's the "point of no return"

**Technical Details:**
- Entity already defined in `config/entities.yaml` as `entity_portal`
- Needs to be spawned dynamically when heart is picked up
- Current victory system in `victory_manager.py` handles this logic
- Portal entry triggers game state change to `GameStates.CONFRONTATION`

**Files to Review:**
- `victory_manager.py` - Current portal spawn logic (may need updates)
- `game_actions.py` - Handles pickup action
- `components/victory.py` - Victory component tracks portal state
- `config/entities.yaml` - Portal entity definition (line ~1284)

**Current Portal Definition:**
```yaml
entity_portal:
  char: "O"
  color: [255, 0, 255]  # Bright magenta
  render_order: "item"
  blocks: false
  description: "A swirling portal of otherworldly energy. Stepping through 
    will take you to face the Entity. There is no turning back."
  portal_destination: "entity_throne_room"
  is_one_way: true
```

---

## 📋 Full Task List (18 Tasks)

### Sprint 1: Foundation (Tasks 1-4)
- [x] **Task 1:** Ruby Heart entity ✅ COMPLETE
- [ ] **Task 2:** Portal system (spawns on pickup, teleports to chamber) ⬅️ **YOU ARE HERE**
- [ ] **Task 3:** Confrontation Chamber map/room
- [ ] **Task 4:** Choice menu skeleton (Keep/Give/Destroy)

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
**Last Commit:** `46b5e96` - Ruby Heart implementation  
**Status:** Clean working directory, ready for portal work

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

*Next session: Implement portal system and confrontation chamber.*

