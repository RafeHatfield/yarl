# 📍 Current Status & Priority List

*Last Updated: October 14, 2025 - After Test Cleanup*

## ✅ Recently Completed (October 2025)

### 1. **Boss Fights** ✅ (v3.9.0)
- Epic boss encounters with dialogue
- Dragon Lord and Demon King
- Enrage system, status immunities
- Legendary loot drops
- 28 boss-specific tests

### 2. **Item Identification System** ✅ (v3.9.1)
- **DUAL TOGGLE** system (master + difficulty integration)
- Scrolls appear as "scroll labeled XYZZY"
- Potions appear as "murky violet potion"
- Configurable pre-identification by difficulty
- **EXACTLY** as designed in PLAYER_PAIN_POINTS.md

### 3. **Item Stacking** ✅ (v3.9.1)
- Stackable items (potions, scrolls)
- Automatic merging on pickup
- Quantity display
- Partial/full drop support

### 4. **Auto-Explore** ✅ (v3.9.2)
- One-button dungeon exploration
- Stops on monsters, items, stairs, damage
- Room-by-room pathfinding
- Hazard avoidance

### 5. **Test Suite Cleanup** ✅ (v3.9.2)
- 100% passing tests (1,859 active)
- 267 tests quarantined (documented)
- 0 failing tests
- Build status: GREEN

---

## 🎯 Phase 1: Core Roguelike Identity - **IN PROGRESS**

**Goal:** Transform into a true roguelike with THE defining mechanics

### ✅ Completed (3/5)
1. ✅ **Item Identification System** - THE roguelike mechanic (DONE!)
2. ✅ **Item Stacking** - QoL improvement (DONE!)
3. ⏭️ **Scroll/Potion Variety** - Expand content **(NEXT UP!)**

### 🎯 Remaining (2/5)
4. ⏳ **Resistance System** - Build diversity foundation
5. ⏳ **Throwing System** - Tactical depth, emergent gameplay

---

## 🚀 **NEXT PRIORITY: Scroll/Potion Variety**

**Status:** Ready to start
**Time Estimate:** 1-2 weeks
**Depth Score Impact:** Discovery 2→5 (+3 points)

### Why This Is Next
- **Completes the identification loop** - We built the system, now fill it with content
- **Quick content wins** - Mostly YAML configuration + simple functions
- **High player impact** - More items = more discovery = more fun
- **Natural progression** - Finish Phase 1 before moving to Phase 2

### Current State
- **Scrolls:** ~8 types (fireball, lightning, confusion, healing, etc.)
- **Potions:** ~5 types (healing, strength, etc.)

### Target State
- **Scrolls:** 20+ types
- **Potions:** 15+ types

### New Scrolls to Add (12 more)
Based on beloved roguelike scrolls:

**Utility:**
1. **Magic Mapping** - Reveals entire floor layout
2. **Teleportation** - Random teleport (escape or risk)
3. **Identify** - Identify one unknown item
4. **Remove Curse** - Uncurse one item
5. **Enchant Weapon** - +1 to weapon
6. **Enchant Armor** - +1 to armor
7. **Recharging** - Restore wand charges

**Tactical:**
8. **Create Monster** - Summon random monster (risky!)
9. **Taming** - Make one monster friendly
10. **Amnesia** - Confuses all nearby monsters
11. **Fear** - Monsters flee from you
12. **Summon Ally** - Friendly creature for 20 turns

### New Potions to Add (10 more)
Based on beloved roguelike potions:

**Buffs:**
1. **Speed** - Double move speed for 20 turns
2. **Invisibility** - Enemies can't see you for 30 turns
3. **Levitation** - Float over traps/water for 40 turns
4. **Protection** - +4 AC for 50 turns
5. **Heroism** - +3 to hit, +3 damage for 30 turns

**Debuffs (risky!):**
6. **Weakness** - -2 to damage for 30 turns
7. **Slowness** - Half speed for 20 turns
8. **Blindness** - Can't see for 15 turns
9. **Paralysis** - Can't move for 3-5 turns

**Special:**
10. **Experience** - Gain 1 level instantly

### Implementation Plan

**Slice 1: New Scroll Effects** (2-3 days)
- Add spell functions to `spells/` directory
- Magic Mapping, Teleport, Identify, Remove Curse
- Register in spell registry
- Basic tests

**Slice 2: New Potion Effects** (2-3 days)
- Add effect functions to `item_functions.py`
- Speed, Invisibility, Levitation, Protection
- Integration with status effect system
- Basic tests

**Slice 3: Entity Registry Updates** (1 day)
- Add all new items to `config/entities.yaml`
- Generate random appearances
- Configure identification settings
- Loot table integration

**Slice 4: Balance & Testing** (2-3 days)
- Playtest each item
- Balance durations and effects
- Add comprehensive tests
- Integration tests

**Total:** 8-10 days (1.5-2 weeks)

---

## 📊 Depth Score Progress

### Before Scroll/Potion Variety
| Category | Current | Target | Gap |
|----------|---------|--------|-----|
| Discovery | 2/10 | 10/10 | -8 |
| Resource Management | 3/10 | 9/10 | -6 |
| Build Diversity | 5/10 | 9/10 | -4 |
| Emergent Gameplay | 4/10 | 9/10 | -5 |

**Overall: 35/64 (55%)**

### After Scroll/Potion Variety
| Category | Current | Target | Gap |
|----------|---------|--------|-----|
| Discovery | **5/10** | 10/10 | **-5** |
| Emergent Gameplay | **5/10** | 9/10 | **-4** |

**Overall: 41/64 (64%)**

---

## 🔮 What Comes After (Phase 1 Completion)

After Scroll/Potion Variety, we'll finish Phase 1:

### Priority #4: Resistance System (2 weeks)
- Fire/Cold/Lightning/Poison resistances
- Build diversity (tank vs balanced vs glass cannon)
- Foundation for ring system

### Priority #5: Throwing System (1 week)
- Throw potions at enemies
- Tactical depth
- Emergent gameplay

**Then:** Phase 2 - Resource Management & Build Depth

---

## 🎮 Player Impact

**What players will experience after Scroll/Potion Variety:**

### Discovery
- "I found a scroll labeled PRATYAVAYAH - what does it do?"
- "This shimmering cyan potion might be invisibility!"
- "I have to decide: use this unknown scroll now or save it?"

### Strategic Depth
- Identify scrolls become valuable resources
- Risky potion drinking has bigger payoff potential
- More tools for different situations

### Replay Value
- Different items each run (randomized appearances)
- New strategies to discover
- "This run I'll try a scroll-heavy build"

---

## ✨ Design Philosophy (From PLAYER_PAIN_POINTS.md)

We're implementing with these principles:

### ✅ DO THIS
1. **Player Agency** - Dual toggle system for ID
2. **Clear Feedback** - Tooltips explain effects
3. **Fair Deaths** - No instant death potions
4. **Respect Time** - No tedious busywork
5. **Interesting Choices** - Every item creates decisions

### ❌ DON'T DO THIS
1. **Instant Death** - No "potion of death"
2. **Wiki Required** - All effects explained
3. **Punish Experimentation** - Debuff potions are survivable
4. **Tedious Busywork** - Keep it fun

---

## 🚦 Decision Point

**Do you want to:**

**A) Start Scroll/Potion Variety** (my strong recommendation)
- Natural next step
- High impact
- Quick wins
- Completes Phase 1 foundation

**B) Jump to Resistance System**
- Build diversity first
- Sets up ring system
- Different direction

**C) Implement Throwing System**
- Tactical depth
- Emergent gameplay
- Fun to implement

**D) Something else entirely?**

---

**My Recommendation: A** - Let's finish what we started with identification!

