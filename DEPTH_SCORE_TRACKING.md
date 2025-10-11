# Depth Score Tracking - KPI Dashboard

*Goal: Transform Yarl into one of the best traditional roguelikes by tracking progress toward legendary status.*

## Current Depth Scores (v3.9.0 - Post Boss Fights)

| Category | Current | Target | Gap | Priority Features to Close Gap |
|----------|---------|--------|-----|-------------------------------|
| **Discovery** | 2/10 | 10/10 | -8 | Item Identification, Vaults, Secret Doors, Unique Artifacts |
| **Resource Management** | 3/10 | 9/10 | -6 | Hunger System, Wand Charges, Identify Scrolls, Corpse System |
| **Build Diversity** | 5/10 | 9/10 | -4 | Rings, Amulets, Resistances, Blessed/Cursed Items |
| **Emergent Gameplay** | 4/10 | 9/10 | -5 | Throwing, Item Interactions, Polymorph, Digging |
| **Memorable Moments** | 6/10 | 10/10 | -4 | Wishes, Polymorph, Divine Intervention, Artifacts |
| **Combat System** | 8/10 | 9/10 | -1 | (Strong foundation - add fumble effects, swarm mechanics) |
| **Progression** | 7/10 | 9/10 | -2 | Victory Condition, Hall of Fame, Morgue Files, Classes |

**Overall Depth Score: 35/64 (55%)** → **Target: 64/74 (86%)**

---

## What Each Score Means

### Discovery (2/10) - "Do I feel excited to explore?"
**Current Strengths:**
- Boss encounters with guaranteed legendary loot ✅
- 4-tier loot quality system (Common → Legendary) ✅
- Manual level design with special rooms ✅

**Missing Critical Elements:**
- ❌ No item identification ("What does this blue potion do?")
- ❌ No vaults (special treasure rooms with challenges)
- ❌ No secret doors (hidden passages)
- ❌ No unique artifacts (chase items like Excalibur)
- ❌ Limited scroll/potion variety (8 scrolls, need 20+)

**To reach 10/10:**
- Add Item Identification System (+3)
- Add Vaults & Secret Doors (+2)
- Expand Scroll/Potion Variety (+2)
- Add Unique Artifacts (+1)

---

### Resource Management (3/10) - "Do resources feel precious?"
**Current Strengths:**
- Healing potions are limited ✅
- Scrolls are consumable ✅
- Equipment has weight limits ✅

**Missing Critical Elements:**
- ❌ No wand charges (reusable magic missing)
- ❌ No identify scroll economy (identification is free)
- ❌ No ring/amulet slot competition
- ❌ No blessing/cursing resources
- ❌ No anti-grinding measures (can rest forever)

**⚠️ NOTE:** Hunger system is OPTIONAL/CONTROVERSIAL (DCSS removed it in v0.26). Resource management will come from:
- **Wand Charges** - Primary reusable magic system
- **Item Identification Economy** - Identify scrolls are valuable
- **Anti-Grinding Design** - Finite monsters, no respawns
- **Blessing/Curse Economy** - Altars and removal scrolls

**To reach 9/10 (WITHOUT mandatory hunger):**
- Add Wand System with Charges (+3) - Primary resource management
- Add Item Identification Economy (+2) - Identify scrolls, shop services
- Add Anti-Grinding Design (+1) - Finite XP per floor
- Add Blessing/Curse Resources (+1) - Remove curse scrolls, altars
- Add Ring/Amulet Competition (+1) - Limited slots, hard choices
- (Optional) Hunger as difficulty toggle (+1 if chosen)

---

### Build Diversity (5/10) - "Can I create unique builds?"
**Current Strengths:**
- 12 weapon types with different properties ✅
- 5 equipment slots (weapon, shield, head, chest, feet) ✅
- 4 rarity tiers with magic bonuses ✅
- STR/DEX/CON stat system ✅
- Finesse/unwieldy weapon properties ✅

**Missing Critical Elements:**
- ❌ No rings (passive effect builds)
- ❌ No amulets (build-defining items)
- ❌ No resistances (fire/cold/poison/electric)
- ❌ No blessed/cursed items (equipment puzzle)
- ❌ No god/religion system (divine builds)
- ❌ Limited status effects (only invisibility, confusion, shield)

**To reach 9/10:**
- Add Ring System (2 slots, 15 types) (+2)
- Add Resistance System (+1)
- Add Blessed/Cursed Items (+1)
- Add Religion/God System (+2)
- Add More Status Effects (+1)
- Add Amulet System (+1)

---

### Emergent Gameplay (4/10) - "Can I create creative solutions?"
**Current Strengths:**
- Teleport scroll for positioning ✅
- Invisibility for stealth ✅
- Raise dead for allies ✅
- Dragon fart for area denial ✅
- Equipment swapping mid-combat ✅

**Missing Critical Elements:**
- ❌ No throwing system (can't throw potions at enemies)
- ❌ No item interactions (can't dip weapon in poison)
- ❌ No polymorph (can't transform into monsters)
- ❌ No digging/tunneling (can't create paths)
- ❌ No fountain/altar interactions
- ❌ Limited monster special abilities

**To reach 9/10:**
- Add Throwing System (+2) - Throw potions, tactical depth
- Add Item Interaction System (+2) - Dipping, alchemy
- Add Polymorph System (+2)
- Add Digging/Tunneling (+1)
- Add Fountain/Altar Effects (+1)
- Add Monster Special Abilities (+1)

---

### Memorable Moments (6/10) - "Will I remember this run?"
**Current Strengths:**
- Boss fights with dialogue and phases ✅
- Critical hits and fumbles ✅
- Legendary loot drops ✅
- Enrage mechanics ✅
- Raise dead zombies ✅

**Missing Critical Elements:**
- ❌ No wish system (legendary moments)
- ❌ No polymorph stories ("I became a dragon!")
- ❌ No divine intervention (god saves you)
- ❌ No unique artifacts (finding Excalibur)
- ❌ No cursed item disasters ("I can't remove this!")

**To reach 10/10:**
- Add Wish/Genie System (+2) - Players remember forever
- Add Polymorph System (+1)
- Add Religion/God System (+1) - Divine intervention
- Add Unique Artifacts (+1)
- Add Blessed/Cursed Drama (+1)

---

### Combat System (8/10) - "Does combat feel good?"
**Current Strengths:**
- D&D-style d20 attack rolls ✅
- AC system with armor types ✅
- Dice notation damage (1d4, 2d6+3) ✅
- Critical hits (20 = double damage) ✅
- Critical fumbles (1 = automatic miss) ✅
- STR/DEX/CON modifiers ✅
- Multiple AI systems ✅
- Boss fights with phases ✅
- Status effects (confusion, invisibility) ✅

**Missing Elements:**
- ❌ No fumble consequences (weapon drops, prone)
- ❌ No swarm mechanics (groups of weak enemies)
- ❌ Limited monster special abilities
- ❌ No ranged weapons

**To reach 9/10:**
- Add Fumble Consequences (+1) - Drop weapon, fall prone
- Add Swarm Mechanics (+0.5)
- Add Monster Special Abilities (+0.5) - Stealing, stat drain

---

### Progression (7/10) - "Do I feel like I'm building toward something?"
**Current Strengths:**
- XP and leveling system ✅
- Stat increases on level up ✅
- Equipment progression (4 rarity tiers) ✅
- Dungeon depth scaling ✅
- Statistics tracking ✅
- Death screen with stats ✅

**Missing Elements:**
- ❌ No victory condition (no final goal)
- ❌ No hall of fame (no permanent record)
- ❌ No player classes (no starting diversity)
- ❌ No skill trees/feats
- ❌ No morgue files (shareable run history)
- ❌ No achievements

**To reach 9/10:**
- Add Victory Condition/Ascension (+1) - Clear goal
- Add Hall of Fame (+0.5) - Persistent records
- Add Player Classes (+1)
- Add Morgue Files (+0.5)

---

## Progress Milestones

### Milestone 1: "Real Roguelike" (Target: v4.0.0 - 8 weeks)
**Goal: 45/74 (61%) - Discovery & Resource Management boosted**

Features:
- ✅ Item Identification System
- ✅ Item Stacking
- ✅ Scroll/Potion Variety (20 scrolls, 15 potions)
- ✅ Resistance System
- ✅ Throwing System

**Expected Scores:**
- Discovery: 2 → 5 (+3)
- Resource Management: 3 → 4 (+1)
- Emergent Gameplay: 4 → 6 (+2)
- Build Diversity: 5 → 6 (+1)

**Player Feedback Target:** "Now THIS feels like a real roguelike!"

---

### Milestone 2: "Deep Systems" (Target: v4.5.0 - 18 weeks)
**Goal: 55/74 (74%) - Resource Management & Build Diversity complete**

Features:
- ✅ Wand System (charges, recharging)
- ✅ Ring System (2 slots, 15 types)
- ✅ Anti-Grinding Design (finite monsters, no respawns)
- ✅ Vaults & Secret Doors
- ✅ Trap System (NO instant death)
- ⚠️ Hunger/Food System (OPTIONAL - may skip based on DCSS lessons)

**Expected Scores:**
- Discovery: 5 → 7 (+2)
- Resource Management: 4 → 8 (+4) - From wands, ID economy, rings
- Build Diversity: 6 → 8 (+2)

**Player Feedback Target:** "I have to manage everything carefully!" (without tedious hunger busywork)

---

### Milestone 3: "Meta-Progression" (Target: v5.0.0 - 32 weeks)
**Goal: 62/74 (84%) - Build Diversity maxed, Memorable Moments boosted**

Features:
- ✅ Blessed/Cursed Items
- ✅ Religion/God System
- ✅ Shop System
- ✅ Amulet System
- ✅ More Status Effects
- ✅ Victory Condition/Ascension

**Expected Scores:**
- Discovery: 7 → 8 (+1)
- Resource Management: 8 → 9 (+1)
- Build Diversity: 8 → 9 (+1)
- Memorable Moments: 6 → 8 (+2)
- Progression: 7 → 8 (+1)

**Player Feedback Target:** "Every run feels unique!"

---

### Milestone 4: "Legendary Status" (Target: v6.0.0 - 48 weeks)
**Goal: 69/74 (93%) - All categories 8+, Memorable Moments maxed**

Features:
- ✅ Item Interaction System
- ✅ Polymorph System
- ✅ Wish/Genie System
- ✅ Unique Artifacts
- ✅ Monster Special Abilities
- ✅ Player Classes

**Expected Scores:**
- Discovery: 8 → 10 (+2)
- Emergent Gameplay: 6 → 9 (+3)
- Memorable Moments: 8 → 10 (+2)
- Combat: 8 → 9 (+1)
- Progression: 8 → 9 (+1)

**Player Feedback Target:** "Remember that run when I polymorphed into a dragon and got a wish?!"

---

## Version History

### v3.9.0 (Current - October 2025)
**Overall: 35/64 (55%)**

Completed:
- Boss Fights (v3.9.0)
- Loot Quality System (v3.8.0)
- D&D Combat System (v3.0.0)
- 8 Tactical Scrolls (v2.7.0)
- Ground Hazards (v3.6.0)

Depth Scores:
- Discovery: 2/10
- Resource Management: 3/10
- Build Diversity: 5/10
- Emergent Gameplay: 4/10
- Memorable Moments: 6/10
- Combat System: 8/10
- Progression: 7/10

---

## How to Update This Document

After completing each feature, update:
1. Current depth scores
2. Overall percentage
3. Mark features as complete (✅)
4. Add to version history
5. Update milestone progress
6. Commit with message: "Update Depth Scores - [Feature Name] Complete"

---

## Next Update: Item Identification System

**Expected Impact:**
- Discovery: 2 → 5 (+3)
- Resource Management: 3 → 4 (+1)
- Build Diversity: 5 → 6 (+1)
- Overall: 35/64 → 41/64 (64%)

**Why These Changes:**
- Discovery gets major boost from "What does this do?" moments
- Resource Management improves from identify scroll economy
- Build Diversity improves from strategic identification choices (identify rings vs potions)

**Configuration:**
- **Master Toggle:** Can completely disable ID system (accessibility)
- **Difficulty Integration:** Easy=80% pre-ID, Medium=40%, Hard=5%
- **Meta-Progression:** Common items auto-ID after first win

**Validation Method:**
- Playtest 10+ runs across all difficulty levels
- Track player feedback quotes by difficulty
- Measure "identification moment" frequency
- Compare Easy mode accessibility vs Hard mode challenge
- Monitor toggle usage (how many disable ID completely?)

