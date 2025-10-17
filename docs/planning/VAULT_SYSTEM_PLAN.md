# Vault System - Implementation Plan

**Feature:** Special treasure rooms with escalating complexity  
**Status:** 🔄 IN PROGRESS - Slice 4  
**Started:** October 18, 2025

---

## 🎯 Overview

Vaults are special rooms that provide high-risk, high-reward exploration moments. They should feel like significant discoveries that require player preparation and skill to successfully loot.

---

## 📦 Implementation Phases

### **Phase 1: Simple Treasure Rooms** ⏳ CURRENT
**Goal:** Basic special rooms with tougher monsters and guaranteed loot

**Features:**
- Special room generation (10-15% chance on deeper levels)
- Tougher monsters than normal (elite variants or higher-level spawns)
- Guaranteed good loot (multiple chests, better quality)
- Visual distinction (different wall color? special floor tile?)
- Risk/reward balance (danger level matches reward)

**Success Criteria:**
- [ ] Vaults generate in dungeons
- [ ] Monsters are noticeably tougher
- [ ] Loot is consistently better than normal rooms
- [ ] Players can identify vaults visually
- [ ] Risk feels balanced with reward

**Value:** Immediate tactical depth and reward for exploration

---

### **Phase 2: Themed Vaults** 📋 PLANNED
**Goal:** Add variety through themes and locked entrances

**Vault Themes:**
1. **Treasure Vault**
   - Focus: Gold, gems, rare items
   - Monsters: Thieves, rogues, guardians
   - Loot: Multiple golden chests, rings, jewelry

2. **Armory**
   - Focus: Weapons and armor
   - Monsters: Warrior types, weapon masters
   - Loot: Enhanced weapons, magical armor, shields

3. **Library/Scriptorium**
   - Focus: Scrolls and knowledge
   - Monsters: Scholars, wizards, librarians
   - Loot: Rare scrolls, spell books, wands

4. **Shrine/Temple**
   - Focus: Religious artifacts, healing items
   - Monsters: Priests, zealots, undead
   - Loot: Holy items, healing potions, rings of protection

5. **Dragon's Hoard**
   - Focus: Legendary loot
   - Monsters: Dragon (boss), dragonlings
   - Loot: Legendary items, massive gold

**Additional Features:**
- **Locked Doors:** Requires keys found elsewhere in the level
- **Key System:** Keys match specific vault types
- **Signpost Hints:** Signs can hint at nearby vaults
- **Visual Themes:** Each vault type has unique tiles/colors

**Value:** Variety, strategic decision-making, sense of discovery

---

### **Phase 3: Advanced Mechanics** 📋 PLANNED
**Goal:** Complex interactions and unique challenges

**Features:**
- **Traps:** Trapped vault entrances (detect or take damage)
- **Puzzles:** Simple puzzles to unlock (later phases)
- **Guardian Monsters:** Mini-bosses that guard vaults
- **Cursed Vaults:** High reward but with a curse/debuff
- **Time Pressure:** Vault collapses after X turns (later)
- **Vault Chains:** Multiple connected vault rooms
- **Secret Vaults:** Vault accessed via secret door only

**Value:** Endgame complexity, replayability, mastery

---

## 🎮 Design Principles

### Core Tenets
1. **Risk/Reward Balance:** Tougher challenge = better loot
2. **Player Choice:** Can see vault, decide if ready to engage
3. **Visual Clarity:** Vaults should be obvious, not hidden
4. **Fair Challenge:** Difficult but not unfair
5. **Rewarding Discovery:** Finding a vault should feel exciting

### Avoid These Pitfalls
- ❌ Making vaults mandatory (player should be able to skip)
- ❌ Punishing exploration (vaults shouldn't be traps)
- ❌ Tedious mechanics (no key hunt fetch quests)
- ❌ Unclear danger levels (player should know it's tough)
- ❌ Disappointing rewards (loot must match difficulty)

---

## 🔧 Technical Implementation

### Phase 1 Components

**Generation:**
- Integrate with existing room generation
- Special room type flag
- Vault spawn rate (depth-based)
- Size constraints (larger than normal rooms)

**Monster Spawning:**
- Elite variants (2x HP, +damage)
- Higher-level monsters (depth +2-3)
- More monsters per room
- Tougher monster types (mini-bosses)

**Loot Generation:**
- Guaranteed 2-3 chests
- Higher loot quality (rare/legendary)
- Better chest types (golden chests)
- Bonus items on floor

**Visual Distinction:**
- Different wall color (gold/silver tint?)
- Special floor tile pattern
- Name in tooltip: "Treasury", "Vault", etc.

---

## 📊 Balancing Guidelines

### Spawn Rates (Phase 1)
- **Depth 1-3:** 0% (too early)
- **Depth 4-6:** 10% chance per level
- **Depth 7-9:** 15% chance per level
- **Depth 10+:** 20% chance per level

### Monster Difficulty
- **Elite Modifier:** 2x HP, +2 attack, +1 defense
- **Level Offset:** Spawn depth+2 or depth+3 monsters
- **Quantity:** 150-200% of normal room spawn count

### Loot Quality
- **Chests:** 2-3 guaranteed (1 rare, 1-2 uncommon)
- **Floor Loot:** 1-2 bonus items (potions, scrolls)
- **Special:** 10% chance for legendary item

---

## 🗺️ Integration Points

### Systems to Modify
1. `map_objects/game_map.py` - Room generation
2. Monster spawning logic
3. Loot generation system
4. Tile rendering (visual distinction)
5. Auto-explore (should stop at vault entrance)

### Dependencies
- ✅ Room generation system
- ✅ Monster spawning system
- ✅ Loot generation system
- ✅ Chest system
- ⏳ Elite monster variants (need to create)
- ⏳ Visual distinction (new tile types or colors)

---

## 📝 Future Expansion Ideas

**Phase 4+:**
- Vault-specific unique monsters
- Vault lore (signposts explaining history)
- Vault achievements/tracking
- Vault boss encounters
- Multi-level vaults
- Vault themes based on dungeon lore
- Player-created vaults (late game construction)

---

## ✅ Success Metrics

**Phase 1 Goals:**
- Players discover vaults 80%+ of playthroughs (depth 4+)
- Players attempt vaults 60%+ of discoveries
- Players feel rewarded for successful vault clears
- Death rate in vaults is higher than normal rooms
- Loot quality feels proportional to difficulty

**Feedback to Gather:**
- Are vaults too easy/hard?
- Is loot rewarding enough?
- Can players identify vaults clearly?
- Do vaults feel special/exciting?
- Is spawn rate appropriate?

---

## 🎯 Current Focus: Phase 1 Implementation

**Next Steps:**
1. Create vault room generation logic
2. Define elite monster scaling system
3. Implement guaranteed loot spawning
4. Add visual distinction to vault tiles
5. Test spawn rates and balance
6. Playtest for feel and excitement

**Estimated Time:** 2-3 hours

---

## 📚 References

- User Request: "combination of simple special rooms with tougher monsters and guaranteed good loot"
- Design Goal: "high risk, higher reward" tactical depth
- Future: "themed rooms that might be locked and require finding a key"

---

**Last Updated:** October 18, 2025  
**Next Review:** After Phase 1 implementation complete

