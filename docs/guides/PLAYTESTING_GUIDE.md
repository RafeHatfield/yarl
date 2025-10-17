# 🎮 Comprehensive Playtesting Guide

## How to Enable Testing Mode

Set the environment variable before running:
```bash
export YARL_TESTING_MODE=1
python engine.py
```

Or run in one line:
```bash
YARL_TESTING_MODE=1 python engine.py
```

---

## 📋 Testing Levels Overview

Each level is specifically designed to test different features. Stairs are available to move between test levels!

### **Level 1: Potion Testing** 🧪
**What to test:**
- ✅ **Buff Potions** (6 types):
  - Speed Potion → Double movement speed (50 turns)
  - Regeneration Potion → Heal 1 HP/turn (30 turns)
  - Invisibility Potion → Enemies can't see you (30 turns)
  - Levitation Potion → Avoid ground hazards (20 turns)
  - Protection Potion → +2 AC (30 turns)
  - Heroism Potion → +2 attack/damage (30 turns)

- ✅ **Debuff Potions** (3 types) - Throw at enemies!:
  - Weakness Potion → -2 attack/damage (20 turns)
  - Blindness Potion → Can't see (15 turns)
  - Paralysis Potion → Can't move (5 turns)

- ✅ **Identification System**:
  - Pick up unidentified potions (random appearance each game)
  - Use Identify scroll for 10-turn identify mode
  - Press 'i' during identify mode to identify items
  - Verify all potions of same type sync when identified

**Testing checklist:**
- [ ] Drink all 6 buff potions, verify effects
- [ ] Throw debuff potions at orcs, verify effects
- [ ] Test potion identification (pickup unidentified, use identify scroll)
- [ ] Verify item stacking (5x Healing Potion display)

---

### **Level 2: Scroll Testing** 📜
**What to test:**
- ✅ **New Utility Scrolls**:
  - Identify Scroll → 10-turn identify mode (press 'i' to identify)
  - Haste Scroll → Double speed (20 turns)
  - Blink Scroll → Teleport 3-5 tiles in random direction
  - Light Scroll → Reveal entire level map
  - Magic Mapping Scroll → Reveal walls/corridors (not items/monsters)
  - Earthquake Scroll → Damage all enemies on level

- ✅ **Enchantment Scrolls**:
  - Enhance Weapon Scroll → +1 to weapon damage permanently
  - Enhance Armor Scroll → +1 to armor AC permanently

- ✅ **Classic Scrolls** (for comparison):
  - Lightning, Fireball, Confusion, Teleport

**Testing checklist:**
- [ ] Use Identify scroll, press 'i' to identify items
- [ ] Test Haste vs Speed potion (both double speed, different durations)
- [ ] Use Blink scroll multiple times, verify random teleport
- [ ] Use Light scroll, verify entire map revealed
- [ ] Use Magic Mapping, verify only walls revealed
- [ ] Use Earthquake, verify all enemies take damage
- [ ] Enhance sword and armor, verify permanent stat boost

---

### **Level 3: Ring Testing** 💍
**What to test:**
- ✅ **All 15 Ring Types**:
  - **AC Rings**: Protection (+2 AC), Resistance (+1 AC vs elemental)
  - **Stat Rings**: Strength (+2 STR), Dexterity (+2 DEX), Constitution (+2 CON)
  - **Combat Rings**: Might (+1d4 damage), Luck (+1 to all rolls)
  - **Passive Rings**: Regeneration (1 HP/turn), Speed (+10% speed)
  - **Immunity Rings**: Free Action (paralysis), Clarity (confusion)
  - **Special Rings**: Teleportation (trigger on hit), Invisibility, Searching, Wizardry

- ✅ **Dual Ring Slots**:
  - Left Ring slot (L)
  - Right Ring slot (R)
  - Can equip 2 rings simultaneously!

- ✅ **Ring Identification**:
  - Unidentified rings show material (e.g., "Wooden Ring", "Gold Ring")
  - Use Identify scroll to reveal true nature

**Testing checklist:**
- [ ] Equip 2 rings at once (left + right slots)
- [ ] Test Ring of Protection (+2 AC visible in character screen)
- [ ] Test Ring of Regeneration (watch HP regen each turn)
- [ ] Test Ring of Might (check damage rolls increase)
- [ ] Test Ring of Free Action (drink Paralysis potion, verify immunity)
- [ ] Test Ring of Clarity (use Confusion scroll, verify immunity)
- [ ] Test Ring of Teleportation (get hit, verify teleport trigger)
- [ ] Verify ring identification system

---

### **Level 4: Wand Testing** 🪄
**What to test:**
- ✅ **Wand System**:
  - Wands have charges (e.g., "Wand of Lightning (3 charges)")
  - Each use consumes 1 charge
  - Empty wands can't be used
  - Recharge wands by using matching scroll on wand
  - Merge 2 wands of same type (charges stack!)

- ✅ **Wand Types**:
  - Wand of Lightning (single target)
  - Wand of Fireball (area of effect)
  - Wand of Confusion (debuff)
  - Wand of Magic Missile (always hits)

**Testing checklist:**
- [ ] Use wand until empty (0 charges)
- [ ] Try using empty wand (verify "fizzles" message)
- [ ] Recharge wand: use Lightning Scroll on Wand of Lightning
- [ ] Verify charges increase
- [ ] Merge 2 wands of same type (charges stack)
- [ ] Test all 4 wand types in combat

---

### **Level 5: Throwing System Testing** 🎯
**What to test:**
- ✅ **Throw Mechanics**:
  - Press 't' to throw (select item from menu)
  - Right-click enemy → instant throw menu!
  - Mouse click or keyboard to select item
  - Target with mouse or keyboard
  - Watch projectile animation!

- ✅ **Throwing Potions**:
  - Healing Potion → Heals TARGET (not you!)
  - Debuff Potions → Apply to target
  - Potions shatter on impact (consumed)

- ✅ **Throwing Weapons**:
  - Daggers, Spears → Deal damage
  - Weapon drops at landing spot
  - Throwing penalty: -2 damage (min 1)

**Testing checklist:**
- [ ] Press 't', select item, throw at orc
- [ ] Right-click orc → throw menu shortcut
- [ ] Click item in throw menu (mouse selection)
- [ ] Throw Healing Potion at wounded orc (verify it heals the orc!)
- [ ] Throw Weakness Potion at orc (verify debuff)
- [ ] Throw dagger at orc (verify damage, weapon drops)
- [ ] Verify projectile animation plays
- [ ] Throw multiple items in one combat

---

### **Level 6: Equipment & Combat Testing** ⚔️
**What to test:**
- ✅ **Weapon Variety**:
  - Dagger (1d4, reach 1)
  - Sword (1d6, reach 1)
  - Spear (1d6, **reach 2!** - attack from 2 tiles away!)
  - Greatsword (2d6, reach 1, two-handed - can't use shield)
  - Shortbow (1d6, reach 8, ranged)
  - Longbow (1d8, reach 10, ranged)
  - Crossbow (1d8, reach 8, ranged)

- ✅ **Armor Types**:
  - Leather Armor (+1 AC)
  - Chain Mail (+3 AC)
  - Plate Armor (+5 AC)
  - Shield (+1 AC)
  - Helmet, Boots (various bonuses)

- ✅ **Weapon Properties**:
  - **Reach**: Spear lets you attack from 2 tiles away!
  - **Two-Handed**: Greatsword requires both hands (no shield)
  - **Ranged**: Bows with animated arrow projectiles!

**Testing checklist:**
- [ ] Equip spear, attack orc from 2 tiles away! (diagonal counts!)
- [ ] Equip greatsword, verify can't equip shield (two-handed)
- [ ] Equip longbow, shoot from 10 tiles away
- [ ] Watch arrow animation for bow shots
- [ ] Enchant weapon (+1 damage), verify permanent boost
- [ ] Enchant armor (+1 AC), verify permanent boost
- [ ] Test all 7 weapon types in combat
- [ ] Mix melee + ranged in same fight

---

### **Level 7: Status Effects Testing** ✨
**What to test:**
- ✅ **Buff Effects** (player):
  - Speed → Double movement (50 turns)
  - Haste → Double movement (20 turns)
  - Protection → +2 AC (30 turns)
  - Heroism → +2 attack/damage (30 turns)
  - Regeneration → Heal 1 HP/turn (30 turns)
  - Invisibility → Enemies can't see (30 turns)
  - Levitation → Avoid hazards (20 turns)

- ✅ **Debuff Effects** (enemies):
  - Confusion → Random movement (10 turns)
  - Slow → Half movement (20 turns)
  - Glue → Can't move (5 turns)
  - Weakness → -2 attack/damage (20 turns)
  - Blindness → Can't see (15 turns)
  - Paralysis → Can't act (5 turns)

- ✅ **Immunities** (rings):
  - Ring of Free Action → Paralysis immunity
  - Ring of Clarity → Confusion immunity

**Testing checklist:**
- [ ] Stack multiple buffs (Speed + Protection + Heroism)
- [ ] Verify buff durations countdown in sidebar
- [ ] Cast debuff on enemy, verify behavior change
- [ ] Throw Paralysis potion at orc, verify it freezes
- [ ] Equip Ring of Free Action, drink Paralysis potion (verify immunity)
- [ ] Equip Ring of Clarity, use Confusion scroll (verify immunity)
- [ ] Test Invisibility (enemies shouldn't chase you)
- [ ] Test Regeneration (watch HP increase each turn)

---

### **Level 8: Boss Arena** 🐉👹
**What to test:**
- ✅ **Both Bosses**:
  - Dragon Lord (high HP, strong attacks)
  - Demon King (spellcaster, summons)
  - Both at once + troll guards!

- ✅ **Full Build**:
  - Best equipment (Greatsword, Plate Armor, Shield)
  - Best rings (Protection + Regeneration)
  - All consumables (20 healing potions!)
  - Wands and scrolls

- ✅ **Large Arena**:
  - 120x80 map for camera scrolling
  - Big boss room (15-20 tiles)
  - Test auto-explore ('o' key or right-click ground)

**Testing checklist:**
- [ ] Enchant your greatsword and plate armor (+1 each)
- [ ] Equip 2 best rings (Protection + Might)
- [ ] Buff up before fight (Speed + Heroism + Protection potions)
- [ ] Use wands and scrolls tactically
- [ ] Test ranged combat with longbow
- [ ] Defeat Dragon Lord
- [ ] Defeat Demon King
- [ ] Test auto-explore in large map
- [ ] Verify camera follows player correctly

---

## 🎯 Key Features to Test

### **Mouse Control** (Fully Implemented!)
- ✅ Left-click movement (pathfinding!)
- ✅ Left-click attack (click on enemy)
- ✅ Left-click pickup (click on item)
- ✅ Right-click auto-explore (click on ground)
- ✅ Right-click throw (click on enemy)
- ✅ Click inventory items (sidebar)
- ✅ Click menu items (all menus)

### **Turn Economy** (Everything Costs 1 Turn!)
- ✅ Movement (1 turn)
- ✅ Attacking (1 turn)
- ✅ Picking up items ('g' key) (1 turn)
- ✅ Using items from inventory (1 turn)
- ✅ Equipping/unequipping (1 turn)
- ✅ Dropping items (1 turn)
- ✅ Identifying items (during identify mode) (1 turn)
- ✅ Completing throw targeting (1 turn)

### **Auto-Explore** (Press 'o' or right-click ground)
- ✅ Automatically explores unexplored areas
- ✅ Picks up valuable items
- ✅ Stops when enemy spotted
- ✅ Stops when new item found
- ✅ Smart pathfinding around obstacles

### **Diagonal Combat** (FIXED!)
- ✅ Monsters attack from diagonal positions
- ✅ You can attack diagonally
- ✅ All 8 surrounding tiles are "adjacent"

---

## 🐛 Bug Testing Priorities

### **Identification System**
- [ ] Verify all potions of same type sync when identified
- [ ] Verify rings show material when unidentified
- [ ] Verify pickup merges identified items correctly
- [ ] Test Identify scroll 10-turn mode

### **Throwing System**
- [ ] Verify thrown potions affect TARGET (not thrower!)
- [ ] Verify thrown weapons deal damage
- [ ] Verify mouse clicks work in throw menu
- [ ] Verify right-click enemy brings up throw menu

### **Equipment System**
- [ ] Test spear reach (2 tiles)
- [ ] Test greatsword two-handed (no shield)
- [ ] Test bow range (8-10 tiles)
- [ ] Verify diagonal attacks work

### **Ring System**
- [ ] Equip 2 rings simultaneously
- [ ] Verify stat bonuses apply
- [ ] Test immunities (Free Action, Clarity)
- [ ] Test trigger effects (Teleportation on hit)

### **Wand System**
- [ ] Use wand until empty
- [ ] Recharge with matching scroll
- [ ] Merge 2 wands of same type
- [ ] Verify charge display

---

## 💡 Pro Testing Tips

1. **Start with Level 1** and work your way through systematically
2. **Test one feature category per session** to avoid confusion
3. **Watch for crashes** and note exact steps to reproduce
4. **Check the sidebar** for status effect durations
5. **Use character screen ('c' key)** to verify stat changes
6. **Save frequently** (though testing mode is repeatable!)
7. **Test mouse AND keyboard** for every feature
8. **Try edge cases**: empty wands, full inventory, stacking items

---

## 📝 Feedback Format

When reporting issues, please include:
- **Level number** (1-8)
- **Feature being tested** (potions, rings, throwing, etc.)
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Any error messages in console**

Example:
```
Level: 3 (Ring Testing)
Feature: Ring of Teleportation
Steps: Equipped ring, got hit by orc
Expected: Should teleport away
Actual: Stayed in place
Error: None visible
```

---

## 🎉 Have Fun!

This testing setup gives you access to EVERYTHING we've built:
- 10 new potions
- 8 new scrolls  
- 15 new rings
- Wand system
- Throwing mechanics
- Full mouse control
- And much more!

Enjoy breaking things! 🎮✨

