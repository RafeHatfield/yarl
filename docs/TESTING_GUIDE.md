# 🧪 YARL Testing & Debug Guide

**Complete reference for all testing features and debug tools**

Last Updated: October 27, 2025

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Testing Mode](#testing-mode)
3. [Tier 1: Command-Line Flags](#tier-1-command-line-flags)
4. [Tier 2: Wizard Mode](#tier-2-wizard-mode)
5. [Testing Best Practices](#testing-best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Basic Testing
```bash
# Enable testing mode (more items, better loot)
python engine.py --testing

# Start at level 5 for quick testing
python engine.py --testing --start-level 5

# God mode (can't die)
python engine.py --testing --god-mode

# Peaceful mode (no monsters)
python engine.py --testing --no-monsters

# Full visibility (no fog of war)
python engine.py --testing --reveal-map
```

### Advanced Testing (Wizard Mode)
```bash
# Enable in-game debug menu
python engine.py --testing --wizard

# In-game, press F12 to open wizard menu
# Use H/G/R/X/L/N commands
```

### Combined Testing
```bash
# Ultimate testing setup
python engine.py --testing --wizard --god-mode --reveal-map --start-level 5
```

---

## Testing Mode

### Overview
Testing mode (`--testing` or `YARL_TESTING_MODE=1`) enhances the game for faster iteration:

### What It Does
- **More Items**: 2-3x items per room vs normal
- **Better Loot**: Higher tier items spawn earlier
- **Combat Logging**: Detailed combat breakdowns
- **Monster Actions**: Logged to console
- **Level Templates**: Guaranteed spawns for specific levels

### Activation

**Command Line:**
```bash
python engine.py --testing
```

**Environment Variable:**
```bash
export YARL_TESTING_MODE=1
python engine.py
```

**In Code:**
```python
from config.testing_config import set_testing_mode, is_testing_mode

set_testing_mode(True)
if is_testing_mode():
    # Testing-specific code
```

---

## Tier 1: Command-Line Flags

**Quick debug flags for rapid testing - require restart to change**

### --start-level N

**Start game at specific dungeon level**

```bash
python engine.py --testing --start-level 15
```

**What it does:**
- Skips main menu
- Descends to target level
- Grants level-appropriate gear:
  - **Potions**: 5 + (level / 5) healing potions
  - **Weapon**: Sword at level 5+
  - **Armor**: Chain mail at level 10+
  - **Scrolls**: 3 teleport scrolls at level 15+
- Boosts player level: min(dungeon_level / 2, 10)
- Sets HP to match boosted level

**Use cases:**
- Test deep dungeon mechanics
- Test Ghost Guide at level 5/10/15/20
- Test victory sequence (level 25)
- Skip early game grind

**Range:** 1-25

---

### --god-mode

**Player cannot die (HP never goes below 1)**

```bash
python engine.py --testing --god-mode
```

**What it does:**
- Intercepts damage in `Fighter.take_damage()`
- If damage would kill player (HP < 1):
  - Sets damage to `current_hp - 1`
  - Shows: "🛡️ GOD MODE: Fatal damage prevented!"
- Player can still take damage (just not die)

**Use cases:**
- Test dangerous encounters
- Explore without fear
- Test victory/endgame without dying
- Focus on mechanics, not survival

**Toggle:** Can be toggled in Wizard Mode (G key)

---

### --no-monsters

**Disable monster spawning (peaceful mode)**

```bash
python engine.py --testing --no-monsters
```

**What it does:**
- Sets `number_of_monsters = 0` in `place_entities()`
- No monsters spawn on any level
- NPCs still spawn (Ghost Guide, etc.)

**Use cases:**
- Test story/dialogue without combat
- Test UI/navigation
- Test map generation
- Test item mechanics without danger

**Known Issues:**
- ⚠️ Currently not working (bug logged)
- See: TODO #bug-no-monsters-not-working

---

### --reveal-map

**Full visibility, no fog of war**

```bash
python engine.py --testing --reveal-map
```

**What it does:**
- Sets FOV radius to 999 in `game_constants.py`
- All tiles visible regardless of distance
- No fog of war
- Entire level revealed on entry

**Use cases:**
- Test map generation
- See full dungeon layout
- Find bugs in room placement
- Debug pathfinding issues

---

### Combining Flags

**Multiple flags work together:**

```bash
# Test Ghost Guide safely at level 5
python engine.py --testing --start-level 5 --god-mode --reveal-map

# Peaceful exploration with full visibility
python engine.py --testing --no-monsters --reveal-map

# Ultimate testing mode
python engine.py --testing --wizard --god-mode --reveal-map --start-level 10
```

---

## Tier 2: Wizard Mode

**In-game debug menu for interactive testing - no restart needed!**

### Activation

```bash
python engine.py --testing --wizard
```

**Output:**
```
🧪 TESTING MODE ENABLED
🧙 WIZARD MODE ENABLED: Press @ or F12 to open debug menu
```

### Opening the Menu

**In-game, press:**
- `F12` (recommended - most reliable)
- `@` (Shift+2) (may not work on all keyboards)

**Note:** May need to press F12 twice due to key-repeat handling

### Menu Options

```
╔════════════════════════════════════╗
║         🧙 WIZARD MODE             ║
╠════════════════════════════════════╣
║ H - Heal to Full HP                ║
║ L - Teleport to Level...           ║
║ R - Reveal Entire Map              ║
║ G - Toggle God Mode [OFF]          ║
║ X - Gain XP...                     ║
║ -----------------------------------║
║ N - Spawn NPC...                   ║
║ M - Spawn Monster...               ║
║ I - Spawn Item...                  ║
║ -----------------------------------║
║ K - Unlock Knowledge...            ║
║ -----------------------------------║
║ ESC - Close Menu                   ║
╚════════════════════════════════════╝
```

---

### Wizard Commands

#### H - Heal to Full HP ✅

**Instant full heal**

```
Press H in wizard menu
```

**What it does:**
- Sets `player.fighter.hp = player.fighter.max_hp`
- Shows: "🧙 WIZARD: Healed to full HP"

**Use cases:**
- Recover after combat testing
- Quick heal instead of using potions
- Continue testing without dying

---

#### G - Toggle God Mode ✅

**Enable/disable god mode on the fly**

```
Press G in wizard menu
```

**What it does:**
- Toggles `config.god_mode` flag
- Shows: "🧙 WIZARD: God Mode ENABLED/DISABLED"
- Same as `--god-mode` flag but toggleable

**Use cases:**
- Turn on for dangerous test
- Turn off for real combat test
- Toggle mid-game without restart

---

#### R - Reveal Entire Map ✅

**Show entire current level**

```
Press R in wizard menu
```

**What it does:**
- Sets all tiles on current level to `explored = True`
- Reveals entire map instantly
- Shows: "🧙 WIZARD: Revealed entire map"

**Use cases:**
- See full level layout
- Find stairs quickly
- Locate items/monsters
- Debug map generation

**Note:** Only affects current level, not permanent like `--reveal-map` flag

---

#### X - Gain XP ✅

**Instant experience points**

```
Press X in wizard menu
```

**What it does:**
- Grants 100 XP via `player.level.add_xp(100)`
- May trigger level-up if enough XP
- Shows: "🧙 WIZARD: Gained 100 XP"

**Use cases:**
- Quick level-ups for testing
- Test high-level character builds
- Skip grinding

**Amount:** Currently fixed at 100 XP (can be modified in code)

---

#### L - Teleport to Level ✅

**Jump to any dungeon level**

```
Press L in wizard menu
Type level number (1-25)
Press Enter to confirm, ESC to cancel
```

**What it does:**
- Prompts for target level: "🧙 WIZARD: Enter target level (1-25, ESC to cancel):"
- Type digits (up to 3)
- Press Enter to teleport
- Descends through levels using `game_map.next_floor()`
- Heals player after teleport
- Shows: "🧙 WIZARD: Arrived at dungeon level X"

**Use cases:**
- Test specific levels instantly
- Jump to Ghost Guide spawn levels (5, 10, 15, 20)
- Test victory sequence (level 25)
- Skip grinding mid-game

**Limitations:**
- Cannot teleport backwards (only forward)
- Cannot teleport to current level

**Example:**
```
Press L
Type "15"
Press Enter
→ Teleports to level 15
```

---

#### N - Spawn NPC ✅

**Spawn Ghost Guide near player**

```
Press N in wizard menu
```

**What it does:**
- Spawns Ghost Guide at nearest empty tile
- Searches within 3 tiles of player
- Uses `entity_factory.create_unique_npc('ghost_guide', x, y)`
- Adds to entities list
- Shows: "🧙 WIZARD: Spawned Ghostly Guide at (x, y)"

**Use cases:**
- **Test Ghost Guide dialogue** without descending to level 5
- Test NPC interactions
- Test dialogue system
- Spawn multiple guides for testing

**Note:** Currently only spawns Ghost Guide. Future: submenu for other NPCs.

**Example Workflow:**
```
1. Press N (spawn Ghost Guide)
2. Press T (talk to guide)
3. Test dialogue options
4. Press N again to spawn another for different level dialogue
```

---

#### M - Spawn Monster 🚧

**Status:** Not yet implemented

**Planned:**
- Spawn any monster type near player
- Submenu for monster selection
- Useful for combat testing

---

#### I - Spawn Item 🚧

**Status:** Not yet implemented

**Planned:**
- Spawn any item type at player location
- Submenu for item selection
- Useful for testing specific items

---

#### K - Unlock Knowledge 🚧

**Status:** Not yet implemented

**Planned:**
- Unlock victory knowledge flags
- Test endgame without playing through
- Example: `entity_true_name_zhyraxion`

---

### Wizard Mode Messages

All wizard commands show **purple messages** to distinguish from game events:

```
Color: (138, 43, 226)  # Purple
Prefix: "🧙 WIZARD: "
```

Examples:
- 🧙 WIZARD: Healed to full HP
- 🧙 WIZARD: God Mode ENABLED
- 🧙 WIZARD: Teleporting to level 15...
- 🧙 WIZARD: Spawned Ghostly Guide at (42, 23)

---

## Testing Best Practices

### Rapid Iteration Workflow

**Scenario: Testing Ghost Guide Dialogue**

```bash
# 1. Start with wizard mode
python engine.py --testing --wizard --god-mode

# 2. In-game:
Press F12           # Open wizard menu
Press L             # Teleport
Type "5"            # To level 5
Press Enter

Press F12           # Open menu again
Press N             # Spawn Ghost Guide

# 3. Test dialogue
Press T             # Talk to guide
Test dialogue tree

# 4. Want different level dialogue?
Press F12
Press L
Type "10"
Press Enter

Press F12
Press N             # Spawn guide for level 10 dialogue
Press T             # Test level 10 responses
```

**Time:** < 1 minute vs 10+ minutes of actual gameplay!

---

### Testing Scenarios

#### Early Game Testing
```bash
python engine.py --testing --wizard --reveal-map
# Start at level 1, reveal map, heal when needed
```

#### Mid Game Testing
```bash
python engine.py --testing --wizard --start-level 10 --god-mode
# Jump to level 10, can't die, full control
```

#### Endgame Testing
```bash
python engine.py --testing --wizard --start-level 25 --god-mode --reveal-map
# Ultimate testing mode for victory sequence
```

#### Combat Testing
```bash
python engine.py --testing --wizard --start-level 15
# Use H to heal between fights
# Use G to toggle god mode for risky tests
```

#### Story Testing
```bash
python engine.py --testing --wizard --no-monsters --reveal-map
# Peaceful exploration
# Focus on dialogue and story
```

---

## Testing Configuration

### Config Files

**`config/testing_config.py`** - Testing configuration

```python
class TestingConfig:
    def __init__(self, testing_mode: bool = False):
        self.testing_mode = testing_mode
        
        # Tier 1 flags
        self.start_level = 1
        self.god_mode = False
        self.no_monsters = False
        self.reveal_map = False
        
        # Tier 2 flags
        self.wizard_mode = False
```

**Usage:**
```python
from config.testing_config import get_testing_config

config = get_testing_config()
if config.wizard_mode:
    # Wizard-specific code
if config.god_mode:
    # God mode logic
```

---

### Debug Logging

**All debug output goes to `debug.log`**

```bash
# View debug log
tail -f debug.log

# Search for specific events
grep "WIZARD" debug.log
grep "turn_controller" debug.log
grep "ERROR" debug.log
```

**Log levels:**
- Console: WARNING and above
- File: DEBUG and above

---

## Troubleshooting

### Issue: Wizard menu not opening

**Symptoms:** Pressing F12 or @ does nothing

**Solutions:**
1. Ensure `--wizard` flag is used:
   ```bash
   python engine.py --testing --wizard
   ```

2. Check startup message:
   ```
   🧙 WIZARD MODE ENABLED: Press @ or F12 to open debug menu
   ```

3. Try pressing F12 twice (key-repeat issue)

4. Check you're in `PLAYERS_TURN` state (not in menu/dialogue)

---

### Issue: Teleport not working

**Symptoms:** Menu opens but L doesn't teleport

**Solutions:**
1. Ensure you type a valid number (1-25)
2. Press Enter after typing number
3. Cannot teleport backwards (only forward)
4. Check message log for error messages

---

### Issue: Spawn NPC fails

**Symptoms:** "No empty spot near player!"

**Solutions:**
1. Move to open area (not surrounded by walls)
2. Move away from other entities
3. Try again in different location
4. Check map with R (reveal map) first

---

### Issue: God mode not working

**Symptoms:** Still taking fatal damage

**Solutions:**
1. Check god mode is enabled:
   - `--god-mode` flag at startup
   - OR press G in wizard menu
   
2. Look for message: "🛡️ GOD MODE: Fatal damage prevented!"

3. Verify in code:
   ```python
   from config.testing_config import get_testing_config
   print(get_testing_config().god_mode)  # Should be True
   ```

---

### Issue: --no-monsters still spawning monsters

**Status:** Known bug (logged)

**Workaround:** Use wizard mode to skip combat:
```bash
python engine.py --testing --wizard --god-mode --reveal-map
# Heal with H, reveal with R, ignore monsters
```

---

## Related Documentation

- **`docs/development/DEBUG_MODE_PROPOSAL.md`** - Original debug mode proposal (4 tiers)
- **`docs/development/TIER2_WIZARD_MODE_PLAN.md`** - Wizard mode implementation plan
- **`TIER1_BUGS_FOUND.md`** - Bugs found during Tier 1 implementation
- **`TIER1_SUMMARY.md`** - Tier 1 completion summary
- **`REFACTOR_COMPLETE.md`** - Tile access refactor (enables safe spawning)

---

## Future Enhancements

### Tier 3: Save States (Planned)
- Quick save/load for testing
- Multiple save slots
- Save before risky actions

### Tier 4: Automated Testing (Planned)
- Record/replay gameplay
- Automated playthroughs
- Performance profiling

### Wizard Mode Additions
- M - Spawn Monster (any type)
- I - Spawn Item (any type)
- K - Unlock Knowledge (for victory testing)
- T - Teleport to Cursor (instant teleport)
- Ctrl+K - Kill All Monsters (clear level)

---

## Quick Reference Card

```
╔════════════════════════════════════════════════════════╗
║           YARL TESTING QUICK REFERENCE                 ║
╠════════════════════════════════════════════════════════╣
║ COMMAND LINE FLAGS (Tier 1 - requires restart)        ║
║   --testing             Testing mode (more items)      ║
║   --start-level N       Start at level N (1-25)        ║
║   --god-mode            Can't die (HP >= 1)            ║
║   --no-monsters         No monsters spawn               ║
║   --reveal-map          Full visibility, no FOW        ║
║   --wizard              Enable wizard mode              ║
╠════════════════════════════════════════════════════════╣
║ WIZARD MODE (Tier 2 - in-game, no restart)            ║
║   F12 or @              Open wizard menu                ║
║   H                     Heal to full HP                 ║
║   G                     Toggle god mode                 ║
║   R                     Reveal current map              ║
║   X                     Gain 100 XP                     ║
║   L                     Teleport to level (1-25)        ║
║   N                     Spawn Ghost Guide               ║
║   ESC                   Close menu                      ║
╠════════════════════════════════════════════════════════╣
║ BEST COMBOS                                            ║
║   Testing Ghost Guide:                                 ║
║   --testing --wizard --god-mode                        ║
║   → F12, L, "5", Enter, F12, N, T                      ║
║                                                        ║
║   Deep Dungeon Testing:                                ║
║   --testing --wizard --start-level 15 --reveal-map     ║
║                                                        ║
║   Story Testing:                                       ║
║   --testing --wizard --no-monsters --reveal-map        ║
╚════════════════════════════════════════════════════════╝
```

---

**Last Updated:** October 27, 2025  
**Version:** Tier 2 Complete (Tier 3 & 4 planned)  
**Status:** ✅ Fully functional and tested

