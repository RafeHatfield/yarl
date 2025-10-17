# Resistance System - Example Test Output

**What you'll actually see when testing resistances**

---

## 📺 Console Output Example

When you start the game, you'll immediately see:

```
============================================================
🛡️ RESISTANCE SYSTEM ACTIVE - Logging enabled
   Watch for resistance messages when damage is dealt
============================================================
```

Then, when you attack monsters with resistances:

### Example 1: Dragon Lord vs Fireball

**What you do:** Cast Fireball scroll at Dragon Lord

**Console output:**
```
🛡️ RESISTANCE: Dragon Lord is IMMUNE to fire (100% resistance) - 50 damage → 0
```

**In-game message log:**
```
Dragon Lord is immune to fire!
```

**Result:** Dragon takes **0 damage**, doesn't even flinch!

---

### Example 2: Demon King vs Fireball

**What you do:** Cast Fireball scroll at Demon King

**Console output:**
```
🛡️ RESISTANCE: Demon King resists fire (75% resistance) - 40 damage → 10
```

**In-game message log:**
```
Demon King resists fire damage! (75% resistance, 40 → 10)
```

**Result:** Demon takes only **10 damage** instead of 40!

---

### Example 3: Demon King vs Dragon Fart

**What you do:** Cast Dragon Fart scroll at Demon King

**Console output:**
```
🛡️ RESISTANCE: Demon King is IMMUNE to poison (100% resistance) - 30 damage → 0
```

**In-game message log:**
```
Demon King is immune to poison!
```

**Result:** Demon takes **0 poison damage**!

---

### Example 4: Orc vs Fireball

**What you do:** Cast Fireball at a normal Orc

**Console output:**
```
Orc: No resistance to fire damage (30 damage)
```

**In-game message log:**
```
Orc takes 30 damage!
```

**Result:** Orc takes **full damage** (30), as expected!

---

## 🎮 Complete Test Session Example

Here's what a full test session might look like:

```
$ ./test_resistance.sh

==============================================
🛡️  RESISTANCE SYSTEM TEST MODE
==============================================

This will launch the game with:
  - Resistance logging enabled (watch console)
  - Boss monsters have resistances
  ...

Press Enter to start the game...

============================================================
🛡️ RESISTANCE SYSTEM ACTIVE - Logging enabled
   Watch for resistance messages when damage is dealt
============================================================

[Game starts, you navigate to Level 8]

You see: Dragon Lord (Level 15, HP: 500/500)

[You use Fireball scroll]

🛡️ RESISTANCE: Dragon Lord is IMMUNE to fire (100% resistance) - 45 damage → 0
Dragon Lord is immune to fire!

[Dragon Lord attacks you]

The Dragon Lord breathes fire at you for 20 damage!

[You use Lightning Bolt scroll]

Dragon Lord takes 35 damage! (HP: 465/500)

[You move to the Demon King]

You see: Demon King (Level 16, HP: 600/600)

[You use Dragon Fart scroll]

🛡️ RESISTANCE: Demon King is IMMUNE to poison (100% resistance) - 30 damage → 0
Demon King is immune to poison!

[You use Fireball scroll]

🛡️ RESISTANCE: Demon King resists fire (75% resistance) - 40 damage → 10
Demon King resists fire damage! (75% resistance, 40 → 10)
Demon King takes 10 damage! (HP: 590/600)

[etc...]
```

---

## ✅ Verification Checklist

When testing, make sure you see:

1. ✅ **Startup message** appears when game loads
2. ✅ **Console logging** shows exact calculations
3. ✅ **In-game messages** match console output
4. ✅ **Damage numbers** are correct:
   - 100% resistance = 0 damage
   - 75% resistance = 25% damage
   - 50% resistance = 50% damage
   - 0% resistance = 100% damage
5. ✅ **Multiple damage types** work independently
6. ✅ **Normal monsters** still take full damage

---

## 🐛 If Something Doesn't Match

If the console says one thing but the game does another:
1. Note the exact console output
2. Note the exact in-game message
3. Note which monster and spell
4. Check the monster's HP before and after
5. Report the discrepancy

---

## 💡 Pro Tips

1. **Keep console visible** - The detailed logging is there!
2. **Test systematically** - Try each damage type on each boss
3. **Use normal monsters as control** - They should take full damage
4. **Watch the HP bars** - They show the actual damage dealt
5. **Try different floors** - Boss resistances are the same everywhere

---

## 🔍 Debug Mode (If Needed)

If you want even MORE detail, you can enable full debug logging:

```bash
export PYTHONVERBOSE=1
python3 engine.py
```

This will show:
- Damage calculations
- Resistance lookups
- Equipment checks
- Everything!

---

## 🎯 Quick Reference

| What You Cast | At Dragon Lord | At Demon King | At Normal Monster |
|---------------|----------------|---------------|-------------------|
| **Fireball** (fire) | 0 damage (immune) | 25% damage (75% resist) | Full damage |
| **Lightning** (lightning) | Full damage | 50% damage (50% resist) | Full damage |
| **Dragon Fart** (poison) | 70% damage (30% resist) | 0 damage (immune) | Full damage |
| **Any physical** | Full damage | Full damage | Full damage |

---

**Ready to test!** 🎮

Just run `./test_resistance.sh` and start casting spells!

