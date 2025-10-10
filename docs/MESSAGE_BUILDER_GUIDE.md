# 💬 MessageBuilder Guide

**Date:** January 2025  
**Status:** ✅ In Progress (Phase 1 Complete)  
**Version:** v3.8.2

---

## 📋 Overview

The MessageBuilder system provides a centralized, consistent way to create game messages. Instead of scattering `Message()` calls with hardcoded colors throughout the codebase, use MessageBuilder methods for visual consistency and easier maintenance.

### Benefits

- **Consistency:** All messages of the same type use the same color
- **Maintainability:** Change a category's color in one place
- **Readability:** `MB.combat()` is clearer than `Message(text, (255, 255, 255))`
- **Type Safety:** IDE autocomplete shows available categories
- **Documentation:** Each method documents its use case

---

## 🎨 Usage

### Basic Example

**Before (Old Way):**
```python
from game_messages import Message

results.append({
    "message": Message("You hit the Orc for 10 damage!", (255, 255, 255))
})

results.append({
    "message": Message("You pick up the Sword!", (0, 0, 255))
})

results.append({
    "message": Message("You cannot carry any more!", (255, 255, 0))
})
```

**After (MessageBuilder):**
```python
from message_builder import MessageBuilder as MB

results.append({
    "message": MB.combat("You hit the Orc for 10 damage!")
})

results.append({
    "message": MB.item_pickup("You pick up the Sword!")
})

results.append({
    "message": MB.warning("You cannot carry any more!")
})
```

---

## 📚 Available Categories

### Combat Messages

| Method | Color | Use Case |
|--------|-------|----------|
| `MB.combat()` | White | Standard combat messages |
| `MB.combat_hit()` | Light Red | Emphasized hit messages |
| `MB.combat_critical()` | Gold | Critical hits |
| `MB.combat_miss()` | Gray | Normal misses |
| `MB.combat_fumble()` | Light Gray | Fumbles (natural 1) |

**Examples:**
```python
MB.combat("You attack the Orc for 8 damage!")
MB.combat_critical("CRITICAL HIT! You strike for 24 damage!")
MB.combat_miss("You attack the Orc - MISS!")
```

### Item Messages

| Method | Color | Use Case |
|--------|-------|----------|
| `MB.item_pickup()` | Blue | Picking up items |
| `MB.item_drop()` | Yellow | Dropping items |
| `MB.item_use()` | Cyan | Using consumables |
| `MB.item_equipped()` | Light Yellow | Equipping gear |
| `MB.item_unequipped()` | Light Yellow | Unequipping gear |
| `MB.item_effect()` | Gold | Item effects (enhancement, wand charging) |
| `MB.item_charge()` | Light Blue | Wand charges |

**Examples:**
```python
MB.item_pickup("You pick up the Longsword!")
MB.item_equipped("You equip the Plate Mail!")
MB.item_effect("Your weapon glows with power! (+1 damage)")
MB.item_charge("The wand glows. (3 charges remaining)")
```

### Healing & Death

| Method | Color | Use Case |
|--------|-------|----------|
| `MB.healing()` | Light Green | Healing messages |
| `MB.death()` | Dark Red | Death messages |

**Examples:**
```python
MB.healing("You heal for 15 HP!")
MB.death("You died! Press any key to return to the main menu.")
```

### Spell Messages

| Method | Color | Use Case |
|--------|-------|----------|
| `MB.spell_cast()` | Purple | Casting spells |
| `MB.spell_effect()` | Light Blue | Spell effects |
| `MB.spell_fail()` | Gray | Spell failures |

**Examples:**
```python
MB.spell_cast("You conjure a blazing fireball!")
MB.spell_effect("The fireball explodes, dealing 18 damage!")
MB.spell_fail("There is nothing to target there.")
```

### Status & System

| Method | Color | Use Case |
|--------|-------|----------|
| `MB.status_effect()` | Cyan | Status effects applied |
| `MB.level_up()` | Bright Yellow | Level up messages |
| `MB.xp_gain()` | Gold | XP gain messages |
| `MB.system()` | White | System messages |
| `MB.success()` | Green | Success messages |
| `MB.failure()` | Red | Failure messages |
| `MB.warning()` | Yellow | Warning messages |
| `MB.info()` | Light Blue | Informational messages |

**Examples:**
```python
MB.status_effect("You are now invisible! (10 turns)")
MB.level_up("You reached level 5!")
MB.xp_gain("You gain 35 XP!")
MB.warning("Your inventory is full!")
MB.info("You entered level 2 of the dungeon.")
```

### Custom Colors

If you need a color not in the standard categories:

```python
MB.custom("Special message!", (255, 128, 64))
```

---

## 🎨 Color Scheme

The MessageBuilder uses a carefully designed color scheme:

```python
WHITE = (255, 255, 255)  # Combat, system
RED = (255, 0, 0)  # Failure
LIGHT_RED = (255, 100, 100)  # Damage dealt
DARK_RED = (255, 30, 30)  # Death
GREEN = (0, 255, 0)  # Success
LIGHT_GREEN = (100, 255, 100)  # Healing
BLUE = (0, 0, 255)  # Item pickup
LIGHT_BLUE = (200, 200, 255)  # Info, spell effects
CYAN = (0, 255, 255)  # Item use, status effects
YELLOW = (255, 255, 0)  # Warning, level up
LIGHT_YELLOW = (255, 255, 100)  # Equipment
GOLD = (255, 215, 0)  # Critical hits, item effects, XP
ORANGE = (255, 165, 0)  # (Reserved)
GRAY = (180, 180, 180)  # Miss, spell fail
LIGHT_GRAY = (200, 200, 200)  # Fumble
DARK_GRAY = (128, 128, 128)  # (Reserved)
PURPLE = (200, 100, 255)  # Spell casting
```

---

## 📈 Migration Status

### ✅ Completed Files

- `components/inventory.py` - 11 messages migrated
- `message_builder.py` - Core system created

### 🔄 In Progress

- More high-frequency files pending

### 📊 Overall Progress

- **Total Message() calls:** 198 across 35 files
- **Migrated:** ~11 (5.5%)
- **Remaining:** ~187 (94.5%)

---

## 🔧 Migration Guide

### Step 1: Import MessageBuilder

```python
from message_builder import MessageBuilder as MB
```

### Step 2: Replace Message() Calls

**Find patterns like:**
```python
Message("text", (255, 255, 255))
```

**Replace with appropriate category:**
```python
MB.combat("text")
```

### Step 3: Choose Right Category

Use this decision tree:

1. **Combat?** → `MB.combat()`, `MB.combat_critical()`, etc.
2. **Item interaction?** → `MB.item_pickup()`, `MB.item_use()`, etc.
3. **Spell?** → `MB.spell_cast()`, `MB.spell_effect()`, etc.
4. **Status/System?** → `MB.warning()`, `MB.info()`, etc.
5. **Custom?** → `MB.custom()` with specific color

### Step 4: Test

```bash
python -m pytest tests/test_inventory.py  # Or relevant test
```

---

## 🎯 Priority Files for Migration

High-impact files (most Message() calls):

1. **game_actions.py** - 23 calls (core action processing)
2. **item_functions.py** - 16 calls (item functionality)
3. ~~**components/inventory.py**~~ - 11 calls ✅ DONE
4. **components/fighter.py** - 8 calls (combat)
5. **components/ai.py** - 7 calls (monster AI)
6. **spells/spell_executor.py** - 41 calls (spell system)

---

## 🐛 Common Migration Patterns

### Pattern 1: Combat Messages

**Before:**
```python
Message(f"You hit {target.name} for {damage} damage!", (255, 255, 255))
```

**After:**
```python
MB.combat(f"You hit {target.name} for {damage} damage!")
```

### Pattern 2: Item Pickup

**Before:**
```python
Message(f"You pick up the {item.name}!", (0, 0, 255))
```

**After:**
```python
MB.item_pickup(f"You pick up the {item.name}!")
```

### Pattern 3: Warnings

**Before:**
```python
Message("You cannot do that!", (255, 255, 0))
```

**After:**
```python
MB.warning("You cannot do that!")
```

### Pattern 4: Item Effects

**Before:**
```python
Message(f"Your {item.name} glows with power!", (255, 215, 0))
```

**After:**
```python
MB.item_effect(f"Your {item.name} glows with power!")
```

---

## 📚 Testing

All MessageBuilder methods return standard `Message` objects, so they're compatible with existing code:

```python
# Test MessageBuilder
from message_builder import MessageBuilder as MB

msg = MB.combat("Test message")
assert msg.text == "Test message"
assert msg.color == (255, 255, 255)
```

---

## 🔮 Future Enhancements

### Planned Features

- **Message Categories:** Group messages by type for filtering
- **Message History:** Track message types for statistics
- **Message Templates:** f-string templates for common patterns
- **Color Themes:** Multiple color schemes (dark mode, colorblind-friendly)
- **Message Priorities:** Important messages stand out more

### Possible Additions

- **Sound Integration:** Play sounds for message categories
- **Animation Triggers:** Certain messages trigger visual effects
- **Message Filtering:** Players can filter message types
- **Localization:** Support for multiple languages

---

## 📊 Before & After Comparison

### Before (Scattered Colors)

```python
# File 1
Message("You hit!", (255, 255, 255))

# File 2
Message("You hit!", (255, 255, 255))

# File 3
Message("You hit!", (200, 200, 200))  # Oops, inconsistent!
```

### After (Centralized)

```python
# All files
MB.combat("You hit!")  # Always consistent
```

### Changing Combat Color

**Before:** Search & replace across 50+ files  
**After:** Change one line in `message_builder.py`

```python
# In MessageBuilder class
WHITE = (200, 200, 200)  # Changed from (255, 255, 255)
```

All combat messages now use the new color!

---

## 🎓 Quick Reference

```python
from message_builder import MessageBuilder as MB

# Combat
MB.combat("Normal combat")
MB.combat_critical("CRIT!")
MB.combat_miss("Miss!")

# Items
MB.item_pickup("Picked up!")
MB.item_drop("Dropped!")
MB.item_equipped("Equipped!")
MB.item_effect("Glows!")

# Healing
MB.healing("Healed!")
MB.death("Died!")

# Spells
MB.spell_cast("Casting!")
MB.spell_effect("Effect!")

# Status
MB.status_effect("Buffed!")
MB.level_up("Level up!")
MB.xp_gain("XP gained!")

# System
MB.warning("Warning!")
MB.info("Info!")
MB.system("System!")
```

---

**Last Updated:** January 2025  
**Maintainer:** Development Team  
**Status:** Phase 1 Complete (Inventory ✅), More files in progress

