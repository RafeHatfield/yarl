# Logging System

## Overview

The game has comprehensive logging to help track down issues during development and playtesting.

## Log Files

### 1. `errors.log` (Always Active)
**Purpose:** Captures all ERROR and CRITICAL level messages from anywhere in the codebase.

**Format:**
```
2025-10-10 14:30:45 - engine.systems.ai_system - ERROR - Error processing AI turn for Orc: name 'ComponentType' is not defined
```

**When to Check:**
- After playtesting sessions
- When investigating bugs
- To find issues that might have been missed in console

**Location:** Root directory

---

### 2. `monster_actions.log` (Testing Mode Only)
**Purpose:** Detailed logging of all monster actions for debugging AI behavior.

**What's Logged:**
- **Console (INFO level):** Important actions (movement, combat, item pickup, item usage)
- **File (DEBUG level):** Everything including "no actions taken" for complete history

**Format:**
```
10:32:14 - MONSTER: Orc at (50, 22) attempts item_pickup: attempting to pick up Fireball Scroll
10:32:14 - MONSTER: Orc at (50, 22) item_pickup SUCCESS: picked up and stored Fireball Scroll
10:32:14 - MONSTER: Orc at (50, 22) turn complete: item_seeking
```

**When to Check:**
- Debugging monster AI behavior
- Investigating item seeking/usage issues
- Understanding monster combat decisions

**Location:** Root directory

---

### 3. `combat_debug.log` (Testing Mode Only)
**Purpose:** Detailed logging of combat calculations (d20 rolls, AC checks, damage).

**Format:**
```
10:32:14 - COMBAT: Orc rolled 15 + 2 (DEX) + 0 (weapon) = 17 vs AC 13 → HIT
10:32:14 - COMBAT: Orc dealt 4 damage to Player
```

**When to Check:**
- Debugging combat calculations
- Verifying dice mechanics
- Understanding why attacks hit/miss

**Location:** Root directory

---

## Console Output

The console shows:
- **WARNING level and above:** Always visible
- **INFO level (Testing Mode):** Monster actions (except "no actions taken")
- **ERROR level:** Always visible AND logged to `errors.log`

---

## Testing Mode

Enable testing mode with `--test` flag:
```bash
python engine.py --test
```

This enables:
- Monster action logging
- Combat debug logging
- Increased item spawn rates
- Additional debug output

---

## Best Practices

1. **After each playtest:** Check `errors.log` for any issues
2. **AI debugging:** Use `monster_actions.log` to trace monster behavior
3. **Combat debugging:** Use `combat_debug.log` to verify calculations
4. **Clear logs periodically:** Old logs can be deleted, they're regenerated on next run

---

## Log File Management

All log files are:
- **Append mode:** New logs are added to existing files
- **Gitignored:** Not committed to repository
- **Auto-created:** Generated on first use
- **Safe to delete:** Will be recreated on next run

