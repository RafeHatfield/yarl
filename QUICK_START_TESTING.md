# 🧪 Quick Start: Testing Exploration Features

## **One-Command Test**

```bash
YARL_TESTING_MODE=1 python3 engine.py
```

That's it! You're ready to test.

---

## **What to Expect**

### **Level 1** - Exploration Basics
- 🏰 **2 guaranteed vaults** with golden walls and elite monsters
- 🎁 **Lots of chests** (normal, golden, trapped, locked)
- 📜 **Signposts everywhere** (4 types: lore, warning, humor, hint)
- 🏥 **20 healing potions** (easy survival)
- ⚔️ **Full starting gear** (sword, shield, armor, helmet, boots)
- 🔍 **Ring of Searching** (find secret doors easily)
- 👹 **Only 2 weak orcs** (safe testing, plus vault elites)

### **Level 2** - Multiple Vaults & Combat
- 🏰 **3 guaranteed vaults** with golden walls
- 👹 **Elite monsters** in vaults (2x HP, +2 damage, +1 AC)
- 🎁 **17-20 chests total** (11 guaranteed + 6-9 from vaults)
- 🏥 **30 healing potions** (survive tough fights)
- 🛡️ **Better equipment** (plate armor, greatsword)
- 💪 **Buff potions** (speed, heroism, protection)

### **Level 3+** - Random Vaults (Testing Mode)
- 🏰 **50% vault spawn rate** on levels 3+
- 👑 **Golden walls** clearly visible
- 👹 **Elite monsters** with "(Elite)" suffix
- 💰 **2-3 chests per vault** with rare/legendary loot

---

## **Quick Tests**

1. **Chests:** Click to open, items drop on ground
2. **Signposts:** Click to read message
3. **Secret Doors:** Press `S` to search, or wear Ring of Searching
4. **Auto-Explore:** Press `O`, should stop for all features
5. **Vaults:** Look for rooms with golden walls (level 3+, or 80% chance on 1-2)

---

## **Console Logs to Watch For**

```
Level 1: Designated vault at room center (25, 15)
Spawning 4 elite monsters in vault
Spawning 3 chests in vault
Placed golden_chest (rare) at (24, 14)
Entered new treasure vault at grid (2, 1)
Auto-explore stopped: Discovered treasure vault!
```

---

## **Turn Off Testing Mode**

When done:
```bash
unset YARL_TESTING_MODE
```

Or just close the terminal.

---

**Full guide:** See `TESTING_EXPLORATION_FEATURES.md`

