# Testing the Resistance System

**Quick Guide for Testing v3.12.0 Resistance Mechanics**

---

## 🎮 How to Test

### Quick Start (Recommended)
```bash
./test_resistance.sh
```
This script will guide you through testing and launch the game.

### Manual Start
```bash
export YARL_TESTING_MODE=1
python3 engine.py
```

---

## 💬 What You'll See

**Console Logging:**
When resistances are applied, you'll see messages in the console like:
```
🛡️ RESISTANCE: Dragon Lord is IMMUNE to fire (100% resistance) - 50 damage → 0
🛡️ RESISTANCE: Demon King resists fire (75% resistance) - 40 damage → 10
🛡️ RESISTANCE: Orc resists poison (30% resistance) - 20 damage → 14
```

**In-Game Messages:**
The game message log will also show:
```
Dragon Lord is immune to fire!
Demon King resists fire damage! (75% resistance, 40 → 10)
```

---

## 🧪 Test Scenarios

### Scenario 1: Test Dragon Fire Immunity
**Level 8 (Boss Arena) in Testing Mode**

1. Go down stairs to Level 8
2. Find the Dragon Lord (big red "D")
3. Cast Fireball scroll at the Dragon Lord
4. **Expected Result:**
   - Console: `🛡️ RESISTANCE: Dragon Lord is IMMUNE to fire (100% resistance)`
   - Message: "Dragon Lord is immune to fire!"
   - Dragon takes **0 damage**

### Scenario 2: Test Dragon Cold Resistance
1. Cast Lightning Bolt at Dragon Lord (or any non-fire spell)
2. **Expected Result:**
   - Dragon takes normal damage from lightning
   - No resistance message (Dragon has no lightning resistance)
3. If you had a cold spell:
   - Dragon would take 50% reduced damage (50% cold resistance)

### Scenario 3: Test Demon Poison Immunity
**Level 8 (Boss Arena)**

1. Find Demon King (purple "K")
2. Cast Dragon Fart scroll (poison damage) at Demon King
3. **Expected Result:**
   - Console: `🛡️ RESISTANCE: Demon King is IMMUNE to poison (100% resistance)`
   - Message: "Demon King is immune to poison!"
   - Demon takes **0 damage** from poison

### Scenario 4: Test Demon Fire Resistance
1. Cast Fireball at Demon King
2. **Expected Result:**
   - Console: `🛡️ RESISTANCE: Demon King resists fire (75% resistance) - X → Y`
   - Demon takes 25% of normal fire damage
   - Example: 40 damage → 10 damage

### Scenario 5: Test Normal Monsters (No Resistance)
**Any Level**

1. Find a normal Orc or Troll
2. Cast Fireball at them
3. **Expected Result:**
   - Console: (no resistance message, or "No resistance to fire damage")
   - Monster takes full damage
   - No resistance applied

---

## 📊 Quick Reference: Monster Resistances

| Monster | Fire | Cold | Poison | Lightning | Notes |
|---------|------|------|--------|-----------|-------|
| **Dragon Lord** | 100% (Immune) | 50% | 30% | 0% | Fire-breathing dragon |
| **Demon King** | 75% | 0% | 100% (Immune) | 50% | Creature of hell |
| **Orc** | 0% | 0% | 0% | 0% | No resistances |
| **Troll** | 0% | 0% | 0% | 0% | No resistances |
| **Slime** | 0% | 0% | 0% | 0% | No resistances yet |

---

## 🔥 Spell Damage Types

| Spell | Damage Type | Best Used Against |
|-------|-------------|-------------------|
| **Fireball** | Fire | Normal monsters, Demon King (reduced) |
| **Lightning Bolt** | Lightning | Dragon Lord, Demon King (reduced) |
| **Dragon Fart** | Poison | Normal monsters, Dragon Lord (reduced) |
| **Earthquake** | Physical | Everyone (no resistances yet) |

---

## 🎯 What to Look For

### ✅ Expected Behavior
1. **Console logging** shows exact resistance calculations
2. **In-game messages** show immunity or resistance
3. **Damage numbers** are reduced correctly:
   - 50% resistance = half damage
   - 75% resistance = quarter damage
   - 100% resistance = 0 damage (immune)
4. **Unknown damage types** (normal attacks) take full damage

### ❌ Potential Issues to Report
1. Resistance messages not showing in console
2. Damage not being reduced correctly
3. Monsters taking wrong amount of damage
4. Resistance working on wrong damage types
5. Crashes or errors when applying resistances

---

## 🧮 Damage Calculation Examples

### Example 1: Dragon Lord vs Fireball
```
Base fireball damage: 50
Dragon Lord fire resistance: 100%
Calculation: 50 × (100% - 100%) = 50 × 0% = 0
Result: 0 damage (immune)
```

### Example 2: Demon King vs Fireball
```
Base fireball damage: 40
Demon King fire resistance: 75%
Calculation: 40 × (100% - 75%) = 40 × 25% = 10
Result: 10 damage
```

### Example 3: Orc vs Fireball
```
Base fireball damage: 30
Orc fire resistance: 0%
Calculation: 30 × (100% - 0%) = 30 × 100% = 30
Result: 30 damage (full damage)
```

---

## 💡 Testing Tips

1. **Use Testing Mode** - It has all scrolls and items available on early levels
2. **Level 2** - Has all scroll types including Fireball and Lightning
3. **Level 8** - Has both boss monsters with resistances
4. **Watch the Console** - Resistance logging is very detailed
5. **Test Each Damage Type:**
   - Fire: Fireball scroll
   - Lightning: Lightning Bolt scroll
   - Poison: Dragon Fart scroll
   - Physical: Earthquake scroll (no resistances yet)

---

## 🐛 If You Find a Bug

Please note:
1. Which monster you were testing
2. Which spell/damage type you used
3. Expected vs actual damage
4. Console output (copy the resistance log lines)
5. Any error messages

---

## 🚀 Quick Test Checklist

- [ ] Dragon Lord immune to fire (Fireball = 0 damage)
- [ ] Dragon Lord resists cold (50% reduction)
- [ ] Dragon Lord resists poison (30% reduction)
- [ ] Demon King immune to poison (Dragon Fart = 0 damage)
- [ ] Demon King resists fire (75% reduction)
- [ ] Demon King resists lightning (50% reduction)
- [ ] Normal monsters take full damage from all types
- [ ] Console shows resistance calculations
- [ ] In-game messages show immunity/resistance
- [ ] Damage numbers match calculations

---

## ⚙️ Advanced: Add Custom Test Resistances

Want to test specific resistance values? You can temporarily modify `config/entities.yaml`:

```yaml
orc:
  stats:
    # ... existing stats ...
    resistances:
      fire: 50  # Add 50% fire resistance to test
      cold: 100 # Add immunity to test
```

Then restart the game to see orcs with custom resistances!

---

**Happy Testing!** 🎮

If you encounter any issues or the logging doesn't appear, let me know!

