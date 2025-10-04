# 📦 Yarl - Complete Items Reference Guide

**Version:** v3.4.0  
**Last Updated:** October 4, 2025

This document provides a comprehensive reference for all items implemented in Yarl, including their stats, effects, and YAML keys for testing templates.

---

## 🗡️ **WEAPONS**

### **How Weapons Work:**
- **Damage:** Roll dice + STR modifier + weapon's to-hit bonus
- **Attack Roll:** d20 + STR modifier + to-hit bonus vs target's AC
- **Critical Hit:** Natural 20 → double damage
- **Fumble:** Natural 1 → miss automatically

### **Weapon Properties:**
- **Finesse** (+1 to-hit): Easier to land hits, good for high-DEX builds
- **Unwieldy** (-1 to-hit): Harder to hit, but massive damage
- **Two-Handed**: Requires both hands, **prevents shield use**
- **Reach**: Attack from **2 tiles away** (spears)

### **Combat Mechanics:**
- **Keyboard Bump Attack**: Move into adjacent monster → attack (reach doesn't apply)
- **Mouse Click Attack**: Click on monster → attack if within reach, else pathfind
- **Auto-Attack on Approach**: When pathfinding toward an enemy, automatically attack when you get within weapon reach!
  - **Spear (Reach 2)**: Auto-attacks when you get within 2 tiles
  - **Normal Weapons**: Auto-attack when adjacent
  - **Future Ranged Weapons**: Will auto-attack at their max range
- **Two-Handed Weapons**: 
  - Equipping a two-handed weapon auto-unequips your shield
  - Equipping a shield auto-unequips your two-handed weapon

---

### **Light Weapons (1d4)**
Fast, precise strikes. Good for finesse builds.

| YAML Key | Display Name | Damage | To-Hit | Avg Dmg | Range | Reach | Properties | Char | Notes |
|----------|--------------|--------|--------|---------|-------|-------|------------|------|-------|
| `dagger` | Dagger | 1d4 | +1 | 2.5 | 1-4 | 1 | Finesse | `-` | Starting weapon, easiest to hit |

---

### **One-Handed Weapons (1d6)**
Balanced weapons for early-mid game.

| YAML Key | Display Name | Damage | To-Hit | Avg Dmg | Range | Reach | Properties | Char | Notes |
|----------|--------------|--------|--------|---------|-------|-------|------------|------|-------|
| `club` | Club | 1d6 | 0 | 3.5 | 1-6 | 1 | Bludgeoning | `)` | Common weapon |
| `shortsword` | Shortsword | 1d6 | +1 | 3.5 | 1-6 | 1 | Finesse | `/` | Piercing, easier to hit |
| `mace` | Mace | 1d6 | 0 | 3.5 | 1-6 | 1 | Bludgeoning | `)` | Good vs armor |

---

### **One-Handed Weapons (1d8)**
Better damage, versatile options.

| YAML Key | Display Name | Damage | To-Hit | Avg Dmg | Range | Reach | Properties | Char | Notes |
|----------|--------------|--------|--------|---------|-------|-------|------------|------|-------|
| `longsword` | Longsword | 1d8 | 0 | 4.5 | 1-8 | 1 | Slashing | `/` | Well-balanced, standard sword |
| `rapier` | Rapier | 1d8 | +1 | 4.5 | 1-8 | 1 | Finesse | `/` | Precision weapon, elegant |
| `spear` | Spear | 1d8 | 0 | 4.5 | 1-8 | **2** | **Reach** | `/` | **Attack from 2 tiles away!** |

---

### **Heavy Weapons (1d10)**
High damage, no finesse.

| YAML Key | Display Name | Damage | To-Hit | Avg Dmg | Range | Reach | Properties | Char | Notes |
|----------|--------------|--------|--------|---------|-------|-------|------------|------|-------|
| `battleaxe` | Battleaxe | 1d10 | 0 | 5.5 | 1-10 | 1 | Slashing | `/` | Heavy chopping weapon |
| `warhammer` | Warhammer | 1d10 | 0 | 5.5 | 1-10 | 1 | Bludgeoning | `)` | Heavy bludgeoning |

---

### **Two-Handed Weapons (1d12 / 2d6)**
Maximum damage, **prevents shield use**.

| YAML Key | Display Name | Damage | To-Hit | Avg Dmg | Range | Reach | Properties | Char | Notes |
|----------|--------------|--------|--------|---------|-------|-------|------------|------|-------|
| `greataxe` | Greataxe | 1d12 | -1 | 6.5 | 1-12 | 1 | Unwieldy, **Two-Handed** | `/` | **HIGHEST SINGLE DAMAGE**, harder to hit, no shield! |
| `greatsword` | Greatsword | 2d6 | 0 | 7.0 | 2-12 | 1 | **Two-Handed** | `/` | **MOST CONSISTENT**, best avg damage, no shield! |

---

### **Legacy Weapons**
Backward compatibility only.

| YAML Key | Display Name | Damage | To-Hit | Avg Dmg | Range | Reach | Properties | Char | Notes |
|----------|--------------|--------|--------|---------|-------|-------|------------|------|-------|
| `sword` | Sword | 1d8 | 0 | 4.5 | 1-8 | 1 | - | `/` | Same as longsword, for old saves |

---

## 🛡️ **ARMOR**

### **How Armor Works:**
- **Armor Class (AC):** Target number for enemy attacks
- **Base AC:** 10 + DEX modifier
- **Total AC:** Base AC + all armor bonuses
- **DEX Cap:** Limits how much DEX bonus applies to AC

### **Armor Types:**
- **Light Armor:** +1-3 AC, **No DEX cap** (full DEX bonus)
- **Medium Armor:** +2-5 AC, **DEX cap +2** (max +2 from DEX)
- **Heavy Armor:** +2-8 AC, **DEX cap 0** (NO DEX bonus!)
- **Shield:** +2 AC, doesn't affect DEX cap

---

### **Shields (Off-Hand Slot)**

| YAML Key | Display Name | AC Bonus | Armor Type | DEX Cap | Slot | Char | Notes |
|----------|--------------|----------|------------|---------|------|------|-------|
| `shield` | Shield | +2 | Shield | No cap | off_hand | `[` | +2 AC, doesn't block DEX bonus |

---

### **Light Armor (No DEX Cap)**
Best for high-DEX characters.

| YAML Key | Display Name | AC Bonus | Armor Type | DEX Cap | Slot | Char | Notes |
|----------|--------------|----------|------------|---------|------|------|-------|
| `leather_helmet` | Leather Helmet | +1 | Light | None | head | `^` | Basic head protection |
| `leather_armor` | Leather Armor | +2 | Light | None | chest | `[` | Starting armor, flexible |
| `studded_leather_armor` | Studded Leather Armor | +3 | Light | None | chest | `[` | Better light armor option |
| `leather_boots` | Leather Boots | +1 | Light | None | feet | `]` | Basic foot protection |

**Light Armor Strategy:** Maximize DEX for high AC + evasion builds.

---

### **Medium Armor (DEX Cap +2)**
Balanced protection for moderate DEX.

| YAML Key | Display Name | AC Bonus | Armor Type | DEX Cap | Slot | Char | Notes |
|----------|--------------|----------|------------|---------|------|------|-------|
| `chain_coif` | Chain Coif | +2 | Medium | +2 | head | `^` | Chain head protection |
| `chain_mail` | Chain Mail | +4 | Medium | +2 | chest | `[` | Solid protection |
| `scale_mail` | Scale Mail | +5 | Medium | +2 | chest | `[` | **Best medium chest armor** |
| `chain_boots` | Chain Boots | +2 | Medium | +2 | feet | `]` | Chain foot protection |

**Medium Armor Strategy:** Good for DEX 14-15 characters (max +2 bonus applies).

---

### **Heavy Armor (DEX Cap 0 - No DEX Bonus!)**
Maximum protection for STR builds.

| YAML Key | Display Name | AC Bonus | Armor Type | DEX Cap | Slot | Char | Notes |
|----------|--------------|----------|------------|---------|------|------|-------|
| `plate_helmet` | Plate Helmet | +3 | Heavy | 0 | head | `^` | Heavy head protection |
| `plate_mail` | Plate Mail | +6 | Heavy | 0 | chest | `[` | Heavy chest armor |
| `full_plate` | Full Plate | +8 | Heavy | 0 | chest | `[` | **BEST ARMOR IN GAME** |
| `plate_boots` | Plate Boots | +2 | Heavy | 0 | feet | `]` | Heavy foot protection |

**Heavy Armor Strategy:** Ignore DEX, maximize STR. Get +8 AC from armor alone!

---

### **Armor Combinations:**

**Example Builds:**

| Build | Head | Chest | Feet | Shield | Total AC Bonus | Best For |
|-------|------|-------|------|--------|----------------|----------|
| **Light Tank** | Leather Helmet | Studded Leather | Leather Boots | Shield | +7 + DEX | High DEX (16+) |
| **Medium Balance** | Chain Coif | Scale Mail | Chain Boots | Shield | +11 + 2 | Moderate DEX (14-15) |
| **Heavy Fortress** | Plate Helmet | Full Plate | Plate Boots | Shield | +15 + 0 | Low DEX, max STR |

---

## 📜 **SCROLLS & CONSUMABLES**

### **How Scrolls Work:**
- **One-time use** (consumed on activation)
- **Targeting:** Click on target tile/entity
- **Range:** Some spells have maximum range
- **Effects:** Instant or duration-based

---

### **Healing**

| YAML Key | Display Name | Effect | Targeting | Char | Color | Notes |
|----------|--------------|--------|-----------|------|-------|-------|
| `healing_potion` | Healing Potion | Heal 40 HP | Self (instant) | `!` | Purple | Instant use, no targeting |

---

### **Offensive Scrolls**

| YAML Key | Display Name | Effect | Targeting | Range | Char | Color | Notes |
|----------|--------------|--------|-----------|-------|------|-------|-------|
| `lightning_scroll` | Lightning Scroll | 40 damage | Single target | 5 tiles | `~` | Yellow | Single-target burst damage |
| `fireball_scroll` | Fireball Scroll | 25 damage | Area (radius 3) | Unlimited | `~` | Red | AOE, hits all in radius |
| `dragon_fart_scroll` | Dragon Fart Scroll | Sleep 20 turns | Cone (45°) | 8 tiles | `~` | Green | Cone attack, enemies pass out |

---

### **Utility Scrolls**

| YAML Key | Display Name | Effect | Duration | Targeting | Char | Color | Notes |
|----------|--------------|--------|----------|-----------|------|-------|-------|
| `confusion_scroll` | Confusion Scroll | Random movement | 10 turns | Single target | `~` | Pink | Enemy wanders aimlessly |
| `invisibility_scroll` | Invisibility Scroll | Invisible to most monsters | 10 turns | Self | `~` | Light Blue | Slimes still detect you! |
| `teleport_scroll` | Teleport Scroll | Teleport to location | Instant | Target tile | `~` | Light Cyan | 10% misfire chance! |
| `shield_scroll` | Shield Scroll | +4 defense | 10 turns | Self | `~` | Light Blue | Monsters: 10% backfire |
| `raise_dead_scroll` | Raise Dead Scroll | Resurrect as zombie | Until killed | Corpse (range 5) | `~` | Green | 2x HP, 0.5x damage, attacks ALL |

---

### **Enhancement Scrolls**

| YAML Key | Display Name | Effect | Targeting | Char | Color | Notes |
|----------|--------------|--------|-----------|------|-------|-------|
| `enhance_weapon_scroll` | Enhance Weapon Scroll | +1 weapon power | Weapon in inventory | `~` | Orange | Permanent upgrade |
| `enhance_armor_scroll` | Enhance Armor Scroll | +1 armor defense | Armor in inventory | `~` | Cyan | Permanent upgrade |

---

## 🎯 **ITEM SPAWN RATES**

### **Healing Potion Spawn Chances:**
- **Level 1:** 50% per room
- **Levels 2+:** 25% per room

### **Scroll Spawn Chances:**
Scrolls become available at specific dungeon levels:

| Scroll | First Appears | Spawn % | Notes |
|--------|---------------|---------|-------|
| Confusion | Level 2 | 12% | Basic crowd control |
| Lightning | Level 2 | 10% | Strong single-target |
| Fireball | Level 4 | 10% | AOE damage |
| Invisibility | Level 3 | Varies | Emergency escape |
| Enhance Weapon | Level 5 | 12% | Permanent upgrade |
| Enhance Armor | Level 6 | 12% | Permanent upgrade |
| Teleport | Level 3 | 8% | Utility movement |
| Shield | Level 3 | 10% | Defensive buff |
| Dragon Fart | Level 5 | 5% | Rare, powerful |
| Raise Dead | Level 4 | 8% | Tactical minion |

---

## 🧪 **TESTING TEMPLATE EXAMPLES**

### **How to Use in `level_templates_testing.yaml`:**

```yaml
level_overrides:
  1:
    guaranteed_spawns:
      mode: "additional"
      items:
        # Weapons
        - type: "greatsword"
          count: 1
        - type: "rapier"
          count: 1
        
        # Armor
        - type: "full_plate"
          count: 1
        - type: "shield"
          count: 1
        
        # Scrolls
        - type: "fireball_scroll"
          count: 3
        - type: "healing_potion"
          count: 5
```

### **Quick Test Loadout Examples:**

**Finesse Build Test:**
```yaml
- type: "rapier"
- type: "studded_leather_armor"
- type: "leather_helmet"
- type: "leather_boots"
```

**Tank Build Test:**
```yaml
- type: "greatsword"
- type: "full_plate"
- type: "plate_helmet"
- type: "plate_boots"
- type: "shield"
```

**Spell Caster Test:**
```yaml
- type: "dagger"
- type: "fireball_scroll"
  count: 10
- type: "lightning_scroll"
  count: 10
- type: "healing_potion"
  count: 10
```

---

## 📊 **QUICK STATS SUMMARY**

**Total Items Implemented:**
- **13 Weapons** (12 unique + 1 legacy)
- **13 Armor Pieces** (1 shield + 12 armor)
- **11 Scrolls/Consumables** (1 potion + 10 scrolls)
- **37 Total Items**

**Equipment Slots:**
- `main_hand` - Weapons (13)
- `off_hand` - Shields (1)
- `head` - Helmets (3)
- `chest` - Armor (9)
- `feet` - Boots (3)

**Spell Types:**
- Healing: 1
- Offensive: 3
- Utility: 7

---

## 🎮 **GAMEPLAY TIPS**

### **Weapon Choice:**
- **High STR?** → Greataxe/Greatsword (ignore finesse)
- **High DEX?** → Rapier (1d8+1 to-hit is amazing!)
- **Balanced?** → Longsword (reliable 1d8)
- **Starting?** → Dagger until you find better

### **Armor Strategy:**
- **DEX 16+?** → Light armor (full DEX bonus!)
- **DEX 14-15?** → Medium armor (+2 DEX cap)
- **DEX 10-13?** → Heavy armor (ignore DEX entirely)

### **Essential Scrolls:**
1. **Healing Potions** - Always carry 3+
2. **Invisibility** - Emergency escape
3. **Fireball** - Clear rooms
4. **Lightning** - Boss damage

### **Scroll Tactics:**
- **Dragon Fart:** Sleep entire groups, 20 turn duration!
- **Raise Dead:** Free tank, attacks everything (including enemies!)
- **Teleport:** 10% misfire = risky but powerful
- **Shield:** Monsters can backfire it on themselves (10% chance)

---

## 🔮 **COMING SOON**

**Weapon Properties (Planned):**
- ✅ **Two-Handed** - IMPLEMENTED! (Greataxe, Greatsword)
- ✅ **Reach** - IMPLEMENTED! (Spear = 2 tiles)
- **Attack Speed** - Multiple attacks per turn
- **Durability** - Equipment degradation
- **Ranged Weapons** - Bows, crossbows with projectiles

**Future Items:**
- Ranged weapons (bows, crossbows)
- Throwing weapons
- Rings & amulets
- More armor sets
- Set bonuses

**Architecture Ready:**
- The reach system works for any reach value (1, 2, 3, etc.)
- Future ranged weapons just need to set `reach: 10` (or whatever range)
- Auto-attack on approach will work for all ranged weapons!
- Two-handed property fully integrated with equipment system

---

**For questions or item suggestions, see `ROADMAP.md` for planned features!**

