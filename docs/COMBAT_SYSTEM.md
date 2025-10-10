# ⚔️ Combat System Documentation

**Date:** January 2025  
**Status:** ✅ Production Ready  
**Version:** v3.0.0+ (D20 Combat System)

---

## 📋 Overview

The game uses a **D&D-inspired D20 combat system** with ability scores, armor class, attack rolls, and critical hits/fumbles. This replaced the original deterministic damage system to add excitement and tactical depth.

### Key Features

- **D20 Attack Rolls** - Roll 1d20 + modifiers vs target AC
- **Ability Scores** - STR, DEX, CON affect combat (8-18 range)
- **Armor Class (AC)** - Dynamic defense based on armor and dexterity
- **Critical Hits** - Natural 20 = double damage
- **Fumbles** - Natural 1 = auto-miss
- **Weapon Dice** - Weapons use dice notation (1d4, 2d6, etc.)
- **Armor Types** - Light/Medium/Heavy with DEX caps

---

## 🎲 Combat Flow

### Attack Sequence

```
1. Attacker rolls d20
2. Add DEX modifier + weapon to-hit bonus
3. Compare to target's Armor Class (AC)
4. Natural 20 → Critical Hit (double damage)
5. Natural 1 → Fumble (auto-miss)
6. Otherwise → Hit if attack roll >= AC
7. On hit: Roll weapon damage + STR modifier
8. Apply damage to target HP
```

### Visual Feedback

- **Hit:** Target flashes red
- **Critical Hit:** Target flashes yellow/gold
- **Fumble:** Miss animation (only on critical fails)
- **Regular Miss:** No animation (faster gameplay)

---

## 📊 Ability Scores & Modifiers

### The Three Stats

**Strength (STR)** - Affects melee damage
- Added to all weapon damage rolls
- Range: 8-18 (10 is average)

**Dexterity (DEX)** - Affects to-hit and AC
- Added to attack rolls (accuracy)
- Added to Armor Class (defense)
- Can be capped by heavy armor

**Constitution (CON)** - Affects HP
- Added to maximum hit points
- Range: 8-18 (10 is average)

### Stat Modifier Formula

```python
modifier = (stat - 10) // 2
```

**Modifier Table:**
```
Stat   | Modifier
-------|----------
8-9    | -1
10-11  |  0
12-13  | +1
14-15  | +2
16-17  | +3
18     | +4
```

**Examples:**
- STR 10 → 0 modifier (no bonus/penalty)
- STR 16 → +3 modifier (strong!)
- DEX 8 → -1 modifier (clumsy)
- DEX 18 → +4 modifier (very agile)

---

## 🛡️ Armor Class (AC)

### AC Calculation

```
AC = 10 + DEX modifier (capped) + armor AC bonus
```

### Components

**Base AC:** 10 (unarmored)

**DEX Modifier:** Your dexterity bonus
- Can be capped by armor type
- Light armor: No cap (full DEX)
- Medium armor: Cap at +2
- Heavy armor: Cap at 0 (no DEX!)

**Armor AC Bonus:** From equipped armor
- Light armor: +1 to +3
- Medium armor: +3 to +5
- Heavy armor: +5 to +8
- Shields: +2 to +4 (off-hand slot)

### Armor Types & DEX Caps

| Armor Type | DEX Cap | AC Bonus | Examples |
|------------|---------|----------|----------|
| **Light** | None (full DEX) | +1 to +3 | Leather, Studded Leather |
| **Medium** | +2 maximum | +3 to +5 | Chain Shirt, Scale Mail |
| **Heavy** | 0 (no DEX!) | +5 to +8 | Plate Mail, Full Plate |
| **Shield** | N/A | +2 to +4 | Wooden Shield, Tower Shield |

### AC Examples

**High DEX Character (DEX 18 = +4):**
```
Unarmored:         10 + 4 (full DEX) = 14 AC
+ Leather Armor:   10 + 4 (full DEX) + 2 = 16 AC
+ Chain Mail:      10 + 2 (capped!) + 4 = 16 AC
+ Plate Mail:      10 + 0 (capped!) + 6 = 16 AC
```

**Low DEX Character (DEX 8 = -1):**
```
Unarmored:         10 - 1 = 9 AC
+ Leather Armor:   10 - 1 + 2 = 11 AC
+ Chain Mail:      10 - 1 + 4 = 13 AC
+ Plate Mail:      10 + 0 (no DEX) + 6 = 16 AC  ← Best choice!
```

**Key Insight:** High DEX characters favor light armor, low DEX characters favor heavy armor.

---

## ⚔️ Attack Rolls

### Attack Roll Calculation

```
Attack Roll = d20 + DEX modifier + weapon to-hit bonus
```

### To-Hit Bonus

Some weapons provide accuracy bonuses:
- **Finesse weapons:** +1 to-hit (Dagger, Rapier, Shortsword)
- **Unwieldy weapons:** -1 to-hit (Greataxe)
- **Standard weapons:** 0 to-hit (Most weapons)

### Hit Determination

```python
if d20_roll == 20:
    # Natural 20 - Critical Hit (always hits, double damage)
elif d20_roll == 1:
    # Natural 1 - Fumble (always misses)
elif attack_roll >= target_ac:
    # Normal hit
else:
    # Miss
```

### Attack Examples

**Attacker:** DEX 14 (+2), wielding Rapier (+1 to-hit)  
**Target:** AC 15

```
Roll d20 + 2 (DEX) + 1 (weapon) = d20 + 3

Roll 1:  Total 4  → Miss (4 < 15)
Roll 12: Total 15 → Hit! (15 >= 15)
Roll 20: Total 23 → Critical Hit! (natural 20)
Roll 1:  Total 4  → Fumble! (natural 1, always miss)
```

### Hit Chance Display

The game shows estimated hit chance to players:
```
"You attack the Orc (65% to hit) - HIT for 8 damage!"
"You attack the Orc (35% to hit) - MISS!"
```

**Calculation:**
```python
min_roll_needed = target_ac - (dex_mod + weapon_bonus)
hit_chance = max(5%, min(95%, (21 - min_roll_needed) * 5%))
```

---

## 💥 Damage Calculation

### Damage Roll

```
Damage = Weapon Dice + STR modifier
```

### Weapon Damage Dice

All weapons use dice notation:

| Weapon | Damage | Properties |
|--------|--------|------------|
| **Dagger** | 1d4 | Finesse (+1 to-hit) |
| **Club** | 1d6 | Simple |
| **Shortsword** | 1d6 | Finesse (+1 to-hit) |
| **Mace** | 1d6 | Simple |
| **Longsword** | 1d8 | Versatile |
| **Rapier** | 1d8 | Finesse (+1 to-hit) |
| **Spear** | 1d8 | Reach (2 tiles) |
| **Battleaxe** | 1d10 | Heavy |
| **Warhammer** | 1d10 | Heavy |
| **Greataxe** | 1d12 | Two-handed, Unwieldy (-1 to-hit) |
| **Greatsword** | 2d6 | Two-handed |

**Why 2d6 vs 1d12?**
- 2d6: Average 7, more consistent (bell curve)
- 1d12: Average 6.5, more swingy (flat distribution)
- Greatsword is more reliable than Greataxe

### Damage Examples

**Attacker:** STR 16 (+3), wielding Longsword (1d8)

```
Roll 1d8 + 3 (STR)

Roll 1: 1 + 3 = 4 damage
Roll 4: 4 + 3 = 7 damage
Roll 8: 8 + 3 = 11 damage
```

**Minimum 1 Damage:** Even with negative STR, minimum damage is 1.

---

## 🎯 Critical Hits & Fumbles

### Critical Hits (Natural 20)

- **Always hits** (ignores AC)
- **Double ALL damage** (weapon + STR modifier)
- **Visual:** Yellow/gold flash
- **Message:** "CRITICAL HIT! You strike the Orc for 16 damage!"

**Example:**
```
Normal hit:  1d8 + 3 = 7 damage
Critical:    (1d8 + 3) × 2 = 14 damage
```

### Fumbles (Natural 1)

- **Always misses** (ignores attack roll)
- **Visual:** Miss animation
- **Message:** "FUMBLE! You attack the Orc - complete miss!"
- **Future:** May add consequences (drop weapon, fall prone)

---

## 🏃 Combat Actions

### Standard Actions

**Attack (Melee):**
- Default combat action
- Uses equipped weapon (or fists if unarmed)
- Follows D20 attack rules above

**Attack (Ranged):**
- Uses bow/crossbow (reach 2-10 tiles)
- Same D20 rules
- Stops at max range and fires automatically

**Move:**
- Move up to speed (no limit currently)
- Diagonal movement costs 1.41 (√2)
- Can move and attack in same turn

**Use Item:**
- Healing potions, scrolls, wands
- Some items require targeting
- Takes your action

---

## 🎲 Dice System

### Dice Notation

The game uses standard D&D dice notation:

**Format:** `NdS+M`
- N = Number of dice
- S = Die size (4, 6, 8, 10, 12, 20)
- M = Fixed modifier (optional)

**Examples:**
```
1d4      → Roll 1 four-sided die
2d6      → Roll 2 six-sided dice, sum them
1d8+2    → Roll 1 eight-sided die, add 2
3d6-1    → Roll 3 six-sided dice, subtract 1
```

### Implementation

```python
from dice import roll_dice

damage = roll_dice("2d6")    # Returns 2-12
healing = roll_dice("1d8+2") # Returns 3-10
```

**Dice Rolling Code:**
```python
def roll_dice(dice_str):
    # Parse "2d6+3" → (2, 6, 3)
    num_dice, die_size, modifier = parse_dice(dice_str)
    
    # Roll each die and sum
    total = sum(random.randint(1, die_size) for _ in range(num_dice))
    
    return total + modifier
```

---

## 🔧 Code Examples

### Performing an Attack

```python
# In game_actions.py or similar
from components.component_registry import ComponentType

attacker = player  # Entity with Fighter component
target = orc       # Entity with Fighter component

# Get Fighter components
attacker_fighter = attacker.require_component(ComponentType.FIGHTER)
target_fighter = target.require_component(ComponentType.FIGHTER)

# Perform D20 attack
results = attacker_fighter.attack_d20(target)

# Process results (messages, death, XP, etc.)
for result in results:
    if 'message' in result:
        game.message_log.add_message(result['message'])
    if 'dead' in result:
        handle_death(result['dead'], result.get('xp', 0))
```

### Calculating AC

```python
# AC is a property on Fighter
fighter = entity.require_component(ComponentType.FIGHTER)

ac = fighter.armor_class  # Auto-calculated from gear
print(f"{entity.name} has {ac} AC")
```

### Checking Hit Chance

```python
# Calculate before attacking
dex_mod = attacker.fighter.dexterity_mod
weapon_bonus = 0  # Get from equipped weapon
target_ac = target.fighter.armor_class

min_roll = target_ac - (dex_mod + weapon_bonus)
hit_chance = max(5, min(95, (21 - min_roll) * 5))
print(f"You have a {hit_chance}% chance to hit")
```

---

## 📊 Balance Considerations

### Early Game (Levels 1-3)

**Player Stats:**
- HP: 30-40 (with CON bonus)
- AC: 12-15 (light armor, decent DEX)
- Attack: d20+2 to +4
- Damage: 1d6+1 to 1d8+2

**Typical Monsters:**
- Rat: AC 10, HP 5, Damage 1d4
- Orc: AC 13, HP 15, Damage 1d6+1
- Troll: AC 15, HP 30, Damage 1d8+2

### Mid Game (Levels 4-7)

**Player Stats:**
- HP: 50-70
- AC: 15-18 (medium/heavy armor)
- Attack: d20+4 to +6
- Damage: 1d10+2 to 2d6+3

### Late Game (Levels 8+)

**Player Stats:**
- HP: 80-120
- AC: 18-22 (heavy armor + shield)
- Attack: d20+6 to +8
- Damage: 1d12+4 to 2d6+5

---

## 🐛 Common Issues & Solutions

### "Attack always hits/misses"

**Problem:** Attack roll not comparing to AC properly  
**Solution:** Check that `attack_roll >= target_ac` (not `>`)

### "Critical hits doing normal damage"

**Problem:** Damage not being doubled  
**Solution:** Check that `damage = damage * 2` happens for natural 20

### "DEX not affecting AC"

**Problem:** Armor DEX cap not applied correctly  
**Solution:** Check `most_restrictive_dex_cap` logic in `armor_class` property

### "Negative damage crashes game"

**Problem:** Negative STR mod can make damage < 0  
**Solution:** Always use `damage = max(1, damage)` for minimum 1 damage

---

## 🔮 Future Enhancements

### Planned Features

- **Fumble Consequences:** Drop weapon, fall prone, provoke attacks
- **Advantage/Disadvantage:** Roll 2d20, take highest/lowest
- **Flanking Bonus:** +2 to-hit when ally opposite target
- **Backstab:** Extra damage when attacking from behind
- **Weapon Properties:** Reach, finesse, two-handed effects
- **Special Attacks:** Power attack (penalty to-hit, bonus damage)
- **Defensive Fighting:** Bonus AC, penalty to-hit
- **Dual Wielding:** Two weapons, extra attack with off-hand

### Possible Tweaks

- **Crit Range Expansion:** 19-20 crits for certain weapons
- **Exploding Dice:** Max roll = roll again and add
- **Armor Degradation:** Armor loses AC over time
- **Weapon Breakage:** Fumbles can damage weapons

---

## 📚 Related Files

### Core Combat Files
- `components/fighter.py` - Main combat implementation
- `dice.py` - Dice rolling utilities
- `game_actions.py` - Action processing
- `combat_debug.log` - Combat logging (testing mode)

### Configuration Files
- `config/entities.yaml` - Monster/weapon stats
- `config/game_constants.yaml` - Combat constants
- `equipment_slots.py` - Equipment slot definitions

### Documentation
- `BALANCE_NOTES.md` - Game balance philosophy
- `docs/POWER_SYSTEM_DESIGN.md` - Character progression
- `docs/MONSTER_LOOT_DESIGN.md` - Enemy equipment

---

## 🎓 Quick Reference

### Combat Formulas

```
Attack Roll = d20 + DEX mod + weapon bonus
Target AC = 10 + DEX mod (capped) + armor AC

Hit if: attack_roll >= target_ac
    OR: d20_roll == 20 (crit)
Miss if: d20_roll == 1 (fumble)

Damage = weapon_dice + STR mod (min 1)
Critical = damage × 2
```

### Stat Ranges

```
Ability Scores: 8-18 (10 = average)
Modifiers: -1 to +4
AC Range: 10-25
Attack Bonus: +0 to +8
Damage: 1-20+ per hit
```

---

**Last Updated:** January 2025  
**Maintainer:** Development Team  
**Status:** Production Ready ✅

