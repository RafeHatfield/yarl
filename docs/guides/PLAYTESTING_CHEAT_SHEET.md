# 🎮 PLAYTESTING CHEAT SHEET - Complete Feature Guide

**Version:** v3.12.0  
**Last Updated:** Post-Ring System Implementation  
**Purpose:** Comprehensive guide to all features implemented since roguelike feature evaluation  

---

## 📋 TABLE OF CONTENTS

1. [Quick Reference - New Controls](#quick-reference---new-controls)
2. [Turn Economy System](#turn-economy-system)
3. [Item Identification System](#item-identification-system)
4. [Potions (11 Types)](#potions-11-types)
5. [Scrolls (14 Types)](#scrolls-14-types)
6. [Rings (15 Types)](#rings-15-types)
7. [Wands (9 Types)](#wands-9-types)
8. [Throwing System](#throwing-system)
9. [Item Stacking](#item-stacking)
10. [Auto-Explore Improvements](#auto-explore-improvements)
11. [Visual Effects](#visual-effects)
12. [Bug Fixes](#critical-bug-fixes)

---

## 🎮 QUICK REFERENCE - NEW CONTROLS

| Key | Action | Turn Cost |
|-----|--------|-----------|
| **t** | Throw item | 1 turn |
| **g** | Pick up item | **1 turn** (NEW!) |
| **i** | Open inventory | Free |
| **Use item** | From inventory | **1 turn** (NEW!) |
| **Equip/unequip** | Toggle equipment | **1 turn** (NEW!) |
| **d** | Drop item | **1 turn** (NEW!) |
| **o** | Auto-explore | 1 turn per move |
| **z** | Cast spell/use wand | 1 turn |

**💡 NEW:** All inventory actions now consume a turn! Plan carefully!

---

## ⏱️ TURN ECONOMY SYSTEM

### What Changed?
**ALL player actions now consume a turn.** This is a major gameplay change!

### Actions That Take 1 Turn:
- ✅ **Picking up items** (`g` key)
- ✅ **Using items from inventory** (drink potion, read scroll)
- ✅ **Equipping/unequipping items** (changing gear)
- ✅ **Dropping items** (`d` key)
- ✅ **Identifying items** (during Identify mode)
- ✅ **Throwing items** (`t` key)

### Actions That Are FREE:
- ✅ **Opening inventory to look** (`i` key)
- ✅ **Reading item descriptions** (hover/examine)
- ✅ **Checking character screen** (`c` key)
- ✅ **Examining entities** (mouse hover)

### Tactical Implications:
- ⚠️ **Don't chug potions mid-combat carelessly** - each takes a turn!
- ⚠️ **Gear swapping is risky** - enemies get to attack while you change equipment
- ⚠️ **Plan your inventory usage** - every action matters

---

## 🔍 ITEM IDENTIFICATION SYSTEM

### How It Works:
1. **Unidentified items** have random appearances:
   - Potions: "cloudy red potion", "sparkling blue liquid"
   - Scrolls: "scroll labeled KIRJE XIXAXA"
   - Rings: "copper ring", "jade ring", "platinum ring"
   - Wands: Appear unidentified with random materials

2. **Global Identification:**
   - Identifying **ONE** item identifies **ALL items of that type**
   - Example: Identify one "viscous brown liquid" → ALL healing potions identified

3. **Ways to Identify:**
   - **Use it** (risky! might be a debuff)
   - **Read Identify scroll** (grants 10-turn identify mode)
   - **Find identified items** (some spawn pre-identified)

### Identify Scroll (Special):
- Grants **10 turns of identification mode**
- While active, you can **identify 1 item per turn** by using it
- Shows **"[IDENTIFY MODE: X turns]"** in UI
- Perfect for safely identifying multiple items

---

## 🧪 POTIONS (11 Types)

### 🛡️ BUFF POTIONS (6 types)

| Potion | Effect | Duration | Strategy |
|--------|--------|----------|----------|
| **Healing** | Restore HP | Instant | Keep 2-3 always! |
| **Speed** | +10% movement speed | 20 turns | Chase fleeing enemies |
| **Regeneration** | Heal 1 HP/turn | 30 turns | Long fights, sustained healing |
| **Invisibility** | Enemies can't see you | 30 turns | Escape, reposition, ambush |
| **Levitation** | Float over hazards | 20 turns | Cross fire/poison/glue |
| **Protection** | +2 AC | 15 turns | Before boss fights |
| **Heroism** | +2 attack bonus | 15 turns | Offensive boost for bosses |

### ☠️ DEBUFF POTIONS (4 types)

| Potion | Effect | Duration | Use Case |
|--------|--------|----------|----------|
| **Weakness** | -2 damage penalty | 15 turns | Throw at tough enemies! |
| **Slowness** | -10% movement | 20 turns | Kite melee enemies |
| **Blindness** | Can't see (not implemented yet) | 10 turns | Disable ranged enemies |
| **Paralysis** | Can't move or act | 5 turns | Emergency disable |

### 🌟 SPECIAL POTIONS (1 type)

| Potion | Effect | Rarity |
|--------|--------|--------|
| **Experience** | Instant level up! | Very rare (1% at L8+) |

**💡 Pro Tips:**
- **Debuff potions = throwable weapons!** Use `t` key to throw at enemies
- Stack buffs before boss fights (Protection + Heroism = deadly combo)
- Regeneration is amazing for attrition battles
- Always keep 1-2 healing potions in reserve

---

## 📜 SCROLLS (14 Types)

### ⚔️ OFFENSIVE SCROLLS (4 types)

| Scroll | Effect | Range | Damage | Use Case |
|--------|--------|-------|--------|----------|
| **Lightning** | Line attack | 8 tiles | 20 dmg | Corridors, groups |
| **Fireball** | 3-tile radius AoE | 8 tiles | 25 dmg | Monster packs |
| **Earthquake** | Map-wide damage | Entire floor | 15 dmg | Emergency nuke |
| **Dragon Fart** | Confuse + damage in cone | 8 tiles | 10 dmg + confuse | Crowd control |

### 🛡️ DEFENSIVE SCROLLS (2 types)

| Scroll | Effect | Duration | Use Case |
|--------|--------|----------|----------|
| **Invisibility** | Can't be seen | 30 turns | Escape, reposition |
| **Shield** | +AC bonus | 15 turns | Before fights |

### 🎯 TACTICAL SCROLLS (4 types)

| Scroll | Effect | Use Case |
|--------|--------|----------|
| **Confusion** | Enemy wanders randomly | Disable dangerous enemies |
| **Slow** | Reduce enemy speed | Kite fast enemies |
| **Glue** | Create sticky ground trap | Zone control |
| **Rage** | Enemy attacks randomly | Turn enemies on each other |
| **Yo Mama** | Insult scroll (confuse + taunt) | Comedy + utility |

### 🚀 UTILITY SCROLLS (6 types)

| Scroll | Effect | Use Case |
|--------|--------|----------|
| **Haste** | +speed buff | 8 turns | Chase, escape, reposition |
| **Blink** | Short teleport (5 tiles) | Emergency escape |
| **Light** | Reveal current FOV permanently | Map exploration |
| **Magic Mapping** | Reveal ENTIRE floor | Instant map knowledge |
| **Identify** | 10 turns of identify mode | Safely identify items |
| **Teleportation** | Random teleport | Emergency escape |

### ⚒️ ENHANCEMENT SCROLLS (2 types)

| Scroll | Effect | Permanent? |
|--------|--------|-----------|
| **Enhance Weapon** | +1 damage to weapon | ✅ YES |
| **Enhance Armor** | +1 AC to armor | ✅ YES |

**💡 Pro Tips:**
- **Magic Mapping** is game-changing on large floors
- **Identify** is your best friend for safe item testing
- **Haste** scroll is like a Speed potion (8 turns)
- **Earthquake** hits EVERYTHING on the map (including you!)
- Stack **Enhance** scrolls for godlike gear

---

## 💍 RINGS (15 Types) - **NEW!**

### Equipment Slots:
- **2 ring slots:** Left hand, Right hand
- Can wear **2 rings simultaneously**
- Mix and match for **105 unique combinations!**

### 🛡️ DEFENSIVE RINGS (3 types)

| Ring | Effect | Spawn Level | Build |
|------|--------|-------------|-------|
| **Protection** | +2 AC | L5 (10%) | Tank build |
| **Regeneration** | Heal 1 HP every 5 turns | L3 (8%) | Sustained combat |
| **Resistance** | +10% all resistances | L8 (6%) | Late-game defense |

### ⚔️ OFFENSIVE RINGS (3 types)

| Ring | Effect | Spawn Level | Build |
|------|--------|-------------|-------|
| **Strength** | +2 STR | L5 (8%) | Melee damage |
| **Dexterity** | +2 DEX | L5 (8%) | Hit chance + AC |
| **Might** | +1d4 damage to all attacks | L7 (7%) | Pure damage |

### 🎯 UTILITY RINGS (4 types)

| Ring | Effect | Spawn Level | Use Case |
|------|--------|-------------|----------|
| **Teleportation** | 20% chance to teleport when hit | L9 (4%) | Emergency escape |
| **Invisibility** | Start each level invisible for 5 turns | L10 (4%) | Scouting/ambush |
| **Searching** | Reveal traps/secrets within 3 tiles | L4 (7%) | Trap detection |
| **Free Action** | Immune to paralysis & slow | L7 (6%) | Anti-CC |

### 🔮 MAGIC RINGS (3 types)

| Ring | Effect | Spawn Level | Build |
|------|--------|-------------|-------|
| **Wizardry** | +1 to all spell effects | L9 (5%) | Caster build |
| **Clarity** | Immune to confusion | L3 (8%) | Anti-confusion |
| **Speed** | +10% movement speed | L6 (6%) | Mobility build |

### 🌟 SPECIAL RINGS (2 types)

| Ring | Effect | Spawn Level | Build |
|------|--------|-------------|-------|
| **Constitution** | +2 CON (+20 max HP!) | L7 (8%) | HP stacking |
| **Luck** | +5% crit chance, better loot | L9 (5%) | Treasure hunter |

### 💍 Ring Combinations (Best Build Ideas):

**🛡️ TANK BUILD:**
- Ring of Protection + Ring of Constitution
- **Result:** +2 AC, +20 HP (nearly unkillable!)

**⚔️ BERSERKER BUILD:**
- Ring of Strength + Ring of Might
- **Result:** +2 STR modifier, +1d4 damage (crush everything!)

**🏃 SPEED DEMON BUILD:**
- Ring of Dexterity + Ring of Speed
- **Result:** +2 DEX (AC + hit), +10% speed (kite forever!)

**🔮 WIZARD BUILD:**
- Ring of Wizardry + Ring of Clarity
- **Result:** +1 spell power, confusion immunity (safe caster!)

**🦸 SUPERMAN BUILD:**
- Ring of Free Action + Ring of Teleportation
- **Result:** Immune to CC, 20% escape chance (unstoppable!)

**💎 TREASURE HUNTER BUILD:**
- Ring of Luck + Ring of Searching
- **Result:** Better loot, trap detection (rich and safe!)

**💡 Pro Tips:**
- Rings start **unidentified** (e.g., "copper ring", "jade ring")
- Identifying one ring identifies ALL rings of that type
- **Free Action** makes you immune to paralysis/slow (huge in late game!)
- **Clarity** makes you immune to confusion (essential for confusion-heavy floors)
- **Regeneration** heal procs EVERY 5 turns (amazing sustain!)
- **Constitution** grants +2 CON = +20 max HP (massive health boost!)

---

## 🪄 WANDS (9 Types) - Already Implemented!

### How Wands Work:
1. **Multi-charge items** - use multiple times before running out
2. **Recharge with scrolls** - pick up matching scroll to add charges
3. **Wand-to-wand merging** - picking up same wand type merges charges
4. **Charge display** - shows remaining charges in UI

### Available Wands:

| Wand | Effect | Starting Charges | Recharge Scroll |
|------|--------|------------------|-----------------|
| **Fireball** | 3-tile radius AoE | 3-7 | Fireball scroll |
| **Lightning** | Line attack | 3-7 | Lightning scroll |
| **Confusion** | Confuse target | 5-10 | Confusion scroll |
| **Teleportation** | Teleport target | 3-7 | Teleport scroll |
| **Dragon Farts** | Cone attack | 3-7 | Dragon Fart scroll |
| **Yo Mama** | Insult (confuse + taunt) | 3-7 | Yo Mama scroll |
| **Slow** | Slow target | 5-10 | Slow scroll |
| **Glue** | Sticky trap | 3-7 | Glue scroll |
| **Rage** | Enrage target | 3-7 | Rage scroll |

**💡 Pro Tips:**
- Wands are **multi-use scrolls** - much more valuable!
- Always pick up matching scrolls to recharge
- Merge duplicate wands for max charges
- Wands show **(X charges)** in UI

---

## 🎯 THROWING SYSTEM - **NEW!**

### How to Throw:
1. Press **`t`** key
2. Select item to throw from inventory
3. Target enemy with cursor
4. Watch projectile fly!

### What You Can Throw:

#### **💊 Potions:**
- **Shatter on impact** (consumed)
- **Apply effect to target**
- **Debuff potions are GREAT throwables!**
  - Throw Weakness potion at tough enemy (-2 damage)
  - Throw Slowness potion to kite melee
  - Throw Paralysis potion for emergency disable

#### **⚔️ Weapons:**
- **-2 damage penalty** when thrown
- **Weapon drops at impact location** (retrieve it!)
- Emergency option when out of ranged attacks

### 🎬 Projectile Animations:
- **Arrows/bolts** now have animated flight paths!
- **Directional characters:**
  - Horizontal: `-`
  - Vertical: `|`
  - Diagonal: `/` or `\`
- Applies to **bows, crossbows, and thrown items**

**💡 Pro Tips:**
- **Debuff potions are consumable grenades!**
- Throw Paralysis potion = instant 5-turn disable
- Throwing weapons is situational (you have to retrieve them)
- Watch the beautiful projectile animations!

---

## 📦 ITEM STACKING - Already Implemented!

### How It Works:
- **Identical items stack automatically** on pickup
- **Displays quantity:** "5x Healing Potion"
- **Saves inventory space** (more room for loot!)
- **Splits automatically** when using one

### What Stacks:
- ✅ Potions of the same type
- ✅ Scrolls of the same type
- ✅ Stackable items (marked in YAML)

### What Doesn't Stack:
- ❌ Equipment (weapons, armor)
- ❌ Rings (each is unique)
- ❌ Wands (merge charges instead)

**💡 Pro Tips:**
- Stock up on Healing potions (they stack!)
- Stacks save precious inventory slots
- Identified + unidentified items DON'T stack (different types)

---

## 🗺️ AUTO-EXPLORE IMPROVEMENTS

### Bug Fixes:
1. ✅ **Corpses no longer block** - dead enemies don't stop exploration
2. ✅ **Pathfinding crashes fixed** - no more `IndexError`
3. ✅ **Gear detection improved** - already-visible items don't stop exploration
4. ✅ **Out-of-bounds handling** - safe array indexing

### How Auto-Explore Works:
- Press **`o`** to start
- Automatically explores **unexplored tiles**
- **Stops when:**
  - Enemy spotted (living enemies only!)
  - **NEW item found** (items already in FOV don't stop it)
  - Unreachable areas
  - Player presses any key

**💡 Pro Tips:**
- Auto-explore is now **much more reliable**
- Use it liberally for fast dungeon clearing
- It ignores corpses and already-seen items now!

---

## 🎨 VISUAL EFFECTS

### Projectile Animations:
- **Arrows** fly from bow to target with directional characters
- **Bolts** fly from crossbow to target
- **Thrown items** animate along Bresenham line
- **No more instant hits** - watch projectiles travel!

### Combat Feedback:
- **Hit effects** flash on successful attacks
- **Miss effects** show when attacks fail
- **Spell effects** animate properly
- **Deferred rendering** prevents flickering

---

## 🐛 CRITICAL BUG FIXES (12 Major Fixes)

### Game-Breaking Fixes:
1. ✅ **Startup crash fixed** - `NoneType` attribute error resolved
2. ✅ **Tooltip identification leak fixed** - unidentified items no longer reveal effects
3. ✅ **Sidebar alignment fixed** - tooltips now match displayed items (off-by-one error)
4. ✅ **Inventory click fixed** - clicking items now works correctly
5. ✅ **Monster equipment drops fixed** - all armor pieces now drop
6. ✅ **Underscores in names fixed** - "Leather_Armor" → "Leather Armor"
7. ✅ **Global identification consistency** - no more mixed identified/unidentified items
8. ✅ **Auto-explore corpse bug** - corpses no longer block exploration
9. ✅ **Auto-explore pathfinding crash** - `IndexError` fixed
10. ✅ **Auto-explore gear bug** - visible items don't stop exploration
11. ✅ **Auto-explore unreachable spam** - false-positive "Cannot reach" fixed
12. ✅ **Turn economy integration** - all actions properly consume turns

---

## 🎯 PLAYTESTING PRIORITIES

### 🔥 HIGH PRIORITY:
1. **Turn Economy** - Does the 1-turn-per-action feel good?
2. **Ring Balance** - Are any rings too strong/weak?
3. **Throwing System** - Is throwing debuff potions fun?
4. **Item Identification** - Is the global ID system clear?
5. **Projectile Animations** - Do they look good?

### ⚠️ MEDIUM PRIORITY:
6. **Spawn Rates** - Do items appear at appropriate levels?
7. **Ring Combinations** - Do builds feel distinct?
8. **Wand Usage** - Is the charge system intuitive?
9. **Item Stacking** - Does it save enough inventory space?
10. **Auto-Explore** - Is it reliable now?

### 📊 LOW PRIORITY:
11. **Potion Variety** - Are all 11 potions useful?
12. **Scroll Variety** - Are all 14 scrolls balanced?
13. **Visual Effects** - Any animation issues?

---

## 🏆 BUILD DIVERSITY CHEAT SHEET

### 🛡️ TANK (Defense Focus):
- **Rings:** Protection + Constitution
- **Potions:** Protection, Regeneration
- **Scrolls:** Shield, Enhance Armor
- **Goal:** +2 AC, +20 HP, sustained healing

### ⚔️ BERSERKER (Melee Damage):
- **Rings:** Strength + Might
- **Potions:** Heroism, Speed
- **Scrolls:** Enhance Weapon, Haste
- **Goal:** Massive melee damage, fast attacks

### 🏹 ARCHER (Ranged Focus):
- **Rings:** Dexterity + Luck
- **Potions:** Speed, Invisibility
- **Scrolls:** Haste, Enhance Weapon
- **Goal:** High accuracy, kiting, crit fishing

### 🔮 WIZARD (Magic Focus):
- **Rings:** Wizardry + Clarity
- **Potions:** Regeneration (sustain)
- **Scrolls:** ALL SCROLLS (spell power boost!)
- **Goal:** +1 spell effects, confusion immunity

### 🦸 SUPERMAN (Balanced Overpowered):
- **Rings:** Free Action + Teleportation
- **Potions:** Heroism + Protection
- **Scrolls:** Magic Mapping, Enhance Everything
- **Goal:** Immune to CC, emergency escapes, god mode

### 💎 TREASURE HUNTER (Loot Focus):
- **Rings:** Luck + Searching
- **Potions:** Invisibility (stealth looting)
- **Scrolls:** Magic Mapping (find treasure)
- **Goal:** Better loot drops, trap detection, rich!

---

## 📈 DEPTH SCORE PROGRESS

### Current Scores (v3.12.0):

| Category | Score | Max | Notes |
|----------|-------|-----|-------|
| **Combat Depth** | 7 | 10 | D20 system, variable damage, status effects |
| **Discovery** | 3 | 10 | Identification system added |
| **Resource Management** | 4 | 10 | Turn economy, inventory management |
| **Emergent Gameplay** | 5 | 10 | Item interactions, throwing |
| **Build Diversity** | **7** | 10 | **+2 from Ring System!** 🎉 |
| **Roguelike Feel** | 4 | 8 | Permadeath, procgen, identification |
| **Polish** | 6 | 6 | UI, animations, bug fixes |

**Overall:** 42/64 (66%) - **Up from 40/64 (62%)!**

---

## 🎮 TESTING CHECKLIST

### Session 1: Core Systems
- [ ] Pick up items (`g`) - takes 1 turn?
- [ ] Use potion from inventory - takes 1 turn?
- [ ] Equip/unequip armor - takes 1 turn?
- [ ] Drop item (`d`) - takes 1 turn?
- [ ] Open inventory (`i`) - free action?

### Session 2: Identification
- [ ] Find unidentified potion (random appearance?)
- [ ] Use unidentified potion (risky!)
- [ ] Pick up same potion - now identified for all?
- [ ] Find Identify scroll
- [ ] Use Identify scroll - grants 10-turn mode?
- [ ] Identify multiple items during mode

### Session 3: Rings
- [ ] Find first ring (unidentified appearance?)
- [ ] Equip in left ring slot
- [ ] Find second ring
- [ ] Equip in right ring slot (both show in sidebar?)
- [ ] Test Ring of Protection (+2 AC working?)
- [ ] Test Ring of Regeneration (heal every 5 turns?)
- [ ] Test Ring of Strength (+2 STR bonus?)
- [ ] Test Ring of Might (+1d4 damage?)
- [ ] Test Ring of Free Action (immune to paralysis?)
- [ ] Test Ring of Clarity (immune to confusion?)

### Session 4: Throwing System
- [ ] Press `t` to throw
- [ ] Select potion from inventory
- [ ] Target enemy
- [ ] Watch projectile animate
- [ ] Potion shatters and applies effect?
- [ ] Throw weapon (-2 damage, drops at target?)
- [ ] Retrieve thrown weapon

### Session 5: Wands
- [ ] Find wand (shows charges?)
- [ ] Use wand multiple times
- [ ] Find matching scroll (recharges wand?)
- [ ] Find duplicate wand (merges charges?)

### Session 6: Advanced Combat
- [ ] Stack buffs before boss (Protection + Heroism?)
- [ ] Throw debuff potion at tough enemy
- [ ] Use Identify scroll to ID 10 items
- [ ] Test ring combinations (Strength + Might?)
- [ ] Watch bow/crossbow projectile animations

---

## 🚀 KNOWN LIMITATIONS / FUTURE WORK

### Not Yet Implemented:
- ❌ **Ring of Invisibility** level-start effect (needs level initialization hook)
- ❌ **Ring of Wizardry** spell enhancement (needs spell system integration)
- ❌ **Ring of Searching** trap reveal (needs trap system)
- ❌ **Ring of Luck** loot boost (needs loot system integration)
- ❌ **Blindness potion** effect (vision system needs work)

### Needs Balance Testing:
- ⚠️ **Ring spawn rates** - too common/rare?
- ⚠️ **Ring combinations** - any overpowered combos?
- ⚠️ **Turn economy** - too punishing/lenient?
- ⚠️ **Throwing potions** - too powerful?

---

## 💡 PRO TIPS FOR PLAYTESTING

1. **Try Pure Builds First:**
   - Pure tank (Protection + Constitution)
   - Pure damage (Strength + Might)
   - Pure caster (Wizardry + Clarity)

2. **Test Edge Cases:**
   - Equip 2 rings, then find a third (slot selection works?)
   - Throw potion at wall (blocks properly?)
   - Use Identify scroll, wait 10 turns (expires correctly?)
   - Pick up items during combat (enemies attack while you loot?)

3. **Abuse the Systems:**
   - Stack ALL buff potions before boss (overpowered?)
   - Throw ALL debuff potions at boss (too easy?)
   - Get Ring of Constitution early (game-breaking?)

4. **Break Things:**
   - Spam `o` auto-explore near enemies (handles correctly?)
   - Throw items at out-of-range targets (errors?)
   - Try to equip non-equippable items (handled?)

---

## 📝 FEEDBACK TEMPLATE

When playtesting, consider documenting:

### What Feels Good:
- [ ] Specific features that are fun
- [ ] Emergent gameplay moments
- [ ] Satisfying combinations

### What Feels Bad:
- [ ] Frustrating mechanics
- [ ] Unclear systems
- [ ] Balance issues

### Bugs Found:
- [ ] Reproduction steps
- [ ] Expected vs actual behavior
- [ ] Screenshots/logs if applicable

---

**Happy Playtesting, Partner! Let's find out how close we are to the world's best roguelike! 🚀🎮💍✨**

