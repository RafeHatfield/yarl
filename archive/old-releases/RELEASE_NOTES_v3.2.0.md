# Release Notes - v3.2.0: The Entity Awakens

**Release Date:** October 3, 2025

## 🎭 Overview

Version 3.2.0 brings **personality** to Yarl! The mysterious Entity that binds your soul now speaks, mocking your failures and dismissing your efforts with sardonic wit. This release combines balance improvements, comprehensive statistics tracking, a stunning death screen, and the first narrative implementation of the bound soul story.

---

## ✨ Major Features

### 🗣️ **The Entity Dialogue System** (NEW!)
The Entity that owns your soul now speaks on every death!

- **40+ unique quotes** with context-aware selection
- **Sarcastically condescending personality**:
  - "Oh. You're back. How... unsurprising."
  - "A goblin? Really? How embarrassingly mortal of you."
  - "At least you aimed high before failing spectacularly."
- **Smart context detection**:
  - Quick deaths → Different mockery
  - Deep runs → Grudging acknowledgment
  - Weak enemies → Maximum condescension
  - Strong performance → Sarcastic "praise"
- **Word-wrapped display** above statistics
- **First narrative implementation** of the bound soul story (see `docs/STORY_CONCEPTS.md`)

### 📊 Player Statistics System
Comprehensive tracking throughout each run:
- **Combat stats**: Kills by monster type, accuracy, damage dealt/taken, critical hits
- **Exploration stats**: Deepest level, rooms explored, turns taken
- **Items & Resources**: Healing received, items used, gold collected
- **Beautiful death screen** displaying all statistics
- **Quick restart** functionality (Press 'R' on death screen)

### ⚖️ Balance Improvements
Early game is now more forgiving:
- **Level 1 adjustments**:
  - Max 1 monster in first two rooms (was 2-3)
  - Guaranteed 2x healing potions + 1x invisibility scroll
  - Healing potion spawn rate: 60% (was 35%)
  - Player starts with 1 healing potion
- **Loot fine-tuning** (v3.1.1):
  - Healing potions: 55% L1 / 28% other (reduced from 60% / 35%)
  - Utility scrolls increased for variety:
    - Confusion: 12% (was 10%)
    - Invisibility: 18% at L3 (was 15% at L4)
    - Enhancement scrolls: 12% (was 10%)

---

## 📜 Legal & Licensing

### **GPL-3.0 License** (NEW!)
Changed from MIT to GPL-3.0 for better protection:
- ✅ Still open source and portfolio-visible
- ✅ Others can use, modify, and learn from the code
- ✅ **BUT** derivative works must also be open-sourced (copyleft)
- ✅ Prevents closed-source commercial exploitation
- ✅ Reserves option for future commercial dual-licensing

**Copyright © 2024-2025 Rafe Hatfield**

---

## 🐛 Bug Fixes

### Critical Fixes
- **FIX**: Healing potions now work correctly (parameter name: `amount` vs `heal_amount`)
- **FIX**: Player starts at full HP (62/62 with CON modifier, not 60/62)
- **FIX**: Fixed crash when pressing inventory keys with too few items
- **FIX**: Death screen properly renders and displays (was drawing but not blitting)
- **FIX**: 10-frame input delay prevents accidental death screen dismissal

### Equipment & Combat Fixes
- **FIX**: Equipment bonuses handle `None` values gracefully
- **FIX**: Fighter component safely handles missing stat components
- **FIX**: Inventory displays equipped items with "(equipped)" label
- **FIX**: Item names display without underscores ("Leather Armor" not "Leather_Armor")

### Technical Improvements
- **FIX**: Replaced deprecated `libtcodpy.map_is_in_fov()` with compatibility wrapper
- **FIX**: Improved error logging with full tracebacks
- **FIX**: Defensive checks prevent `NoneType` comparison crashes

---

## 🎨 UI/UX Improvements

### Death Screen with Entity Personality
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              YOU DIED
        ============

  "Again already? I've barely had time
     to prepare the next vessel."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    === RUN STATISTICS ===
    
    COMBAT
      Monsters Killed: 8
      ...
```

- Color-coded statistics sections
- Clear instructions for restart (R) or exit (ESC)
- Kill breakdown for top 5 monster types
- Accuracy percentage display
- 10-frame input delay prevents accidents

### Inventory & Display
- Equipped items marked with "(equipped)"
- Item names properly formatted (spaces, not underscores)
- Better error messages for invalid selections

### Mouse Movement
- FOV-aware pathfinding limits:
  - 40 tiles when destination is visible
  - 25 tiles when destination is hidden
- Can click across long visible hallways without errors

---

## 🏗️ Architecture Improvements

### New Modules
- **`entity_dialogue.py`**: Contextual quote system with 40+ Entity quotes
- **`components/statistics.py`**: Comprehensive player performance tracking
- **`death_screen.py`**: Death screen rendering with stats and Entity dialogue
- **`docs/STORY_CONCEPTS.md`**: Complete narrative framework for bound soul story

### Configuration Management
- **REFACTOR**: Separated testing config from normal game config
- **NEW**: `ItemSpawnConfig` dataclass for centralized spawn rates
- **NEW**: `PathfindingConfig` with FOV-aware path length limits
- **IMPROVED**: Level-specific overrides in `level_templates.yaml`
- **NEW**: `BALANCE_NOTES.md` documenting balance decisions

### Code Quality
- **NEW**: 40 new automated tests (all passing)
  - 11 tests for Entity dialogue system
  - 16 tests for statistics component
  - 13 tests for healing/initialization fixes
- **IMPROVED**: Defensive programming prevents configuration errors
- **IMPROVED**: Better separation of concerns in config files

---

## 📁 Files Changed

### New Files (7)
- `entity_dialogue.py` - Entity personality and quote system
- `components/statistics.py` - Performance tracking
- `death_screen.py` - Death screen with stats display
- `docs/STORY_CONCEPTS.md` - Narrative framework (40+ pages)
- `BALANCE_NOTES.md` - Balance decision documentation
- `tests/test_entity_dialogue.py` - Dialogue system tests (11 tests)
- `tests/test_statistics_component.py` - Statistics tests (16 tests)
- `tests/test_healing_and_init_fixes.py` - Integration tests (13 tests)

### Modified Files (18)
- `LICENSE` - Changed to GPL-3.0
- `README.md` - Updated license badge and section
- `config/entities.yaml` - Healing potion spawn rates
- `config/level_templates.yaml` - Level 1 overrides
- `config/game_constants.py` - Item spawn config, pathfinding limits
- `config/testing_config.py` - Delegated to game_constants
- `config/entity_factory.py` - Fixed healing potion parameter
- `loader_functions/initialize_new_game.py` - Player initialization
- `components/fighter.py` - Statistics integration, None-safety
- `components/equipment.py` - None-safe bonus calculations
- `game_actions.py` - Statistics tracking, defensive checks
- `input_handlers.py` - Death screen key handling
- `engine/systems/input_system.py` - Death frame counter
- `render_functions.py` - Death screen integration
- `menus.py` - Equipped item labels, name formatting
- `components/player_pathfinding.py` - FOV-aware limits
- `entity.py` - Display name formatting fix
- `ROADMAP.md` - Updated with v3.1.0 and v3.2.0 features

---

## 🧪 Testing

### Comprehensive Test Coverage
- ✅ **40 new tests**, all passing (total: 1502 tests)
- ✅ Entity dialogue system (11 tests)
  - Context-aware quote selection
  - All quote pools accessible
  - Personality tone validation
- ✅ Statistics tracking (16 tests)
  - Recording, serialization, summaries
  - Integration with game components
- ✅ Bug fixes validation (13 tests)
  - Healing potion parameter fix
  - Player initialization (full HP, items)
  - Equipment None-safety

### Test Execution
```bash
pytest tests/test_entity_dialogue.py -v         # 11 passed
pytest tests/test_statistics_component.py -v    # 16 passed
pytest tests/test_healing_and_init_fixes.py -v  # 13 passed
```

---

## 📖 Story & Narrative

### The Bound Soul Framework
Complete narrative concept documented in `docs/STORY_CONCEPTS.md`:

**Core Story**: A powerful Entity owns your soul and forces you to delve into a dungeon repeatedly. Each death returns you to them, where they place your soul into a new body and send you back down. Eventually, one body becomes strong enough to challenge the Entity for freedom.

**Entity Personality**:
- Sarcastically overbearing
- Overconfident in their supremacy
- Extremely condescending
- Dismissive but not cruel

**Tone**: Epic fantasy that doesn't take itself too seriously - stakes are real but the Entity's arrogance adds levity.

**Implementation**: Entity dialogue on death screen is the first narrative element. More to come!

---

## 🎯 Playtesting Results

**Balance Improvements:**
- ✅ Early game no longer brutally difficult
- ✅ Players have resources to survive first 2 rooms
- ✅ Progression feels fair and challenging
- ✅ Healing potions no longer flood inventory by floor 3

**Personality:**
- ✅ Death screen now entertaining instead of frustrating
- ✅ Entity's mockery makes players want to prove them wrong
- ✅ Unique voice in the roguelike space

---

## 🚀 Upgrade Notes

### For Players
1. **Entity dialogue**: Enjoy the sarcasm on death screen!
2. **Quick restart**: Press 'R' to immediately start a new game
3. **Better balance**: Level 1 is more forgiving with guaranteed items
4. **Statistics**: Review your performance after each death

### For Developers
1. **GPL-3.0 License**: Project now uses copyleft license
2. All save files remain compatible
3. Configuration changes in `game_constants.py` and `level_templates.yaml`
4. New `Statistics` component automatically added to player entities
5. Death screen uses `libtcodpy` API (compatible with codebase)

---

## 🔮 What's Next

### Upcoming Features
- **More Entity dialogue** - Additional contexts and special moments
- **Deeper story integration** - Environmental storytelling
- **Boss encounters** - Challenge the Entity?
- **Difficulty selection** - Player choice at game start
- **Player profiles** - Track stats across sessions

### Roadmap
See `ROADMAP.md` for full development plans and `docs/STORY_CONCEPTS.md` for narrative direction.

---

## 📊 Release Statistics

- **Commits**: 7 since v3.0.0
- **Lines Changed**: ~2,500+
- **New Test Cases**: 40
- **New Features**: 3 major (Entity dialogue, Statistics, Balance)
- **Bugs Fixed**: 10 critical, 8 minor
- **New Files**: 7
- **Modified Files**: 18
- **Documentation Pages**: 45+ (story concepts)

---

## 🙏 Acknowledgments

Special thanks to:
- The playtesting feedback that identified balance issues
- The roguelike community for inspiration
- Everyone who encouraged the narrative direction

---

## 🎮 Try It Now!

```bash
# Install dependencies
pip install -r requirements.txt

# Run the game
python engine.py

# Die and meet the Entity! 🐉
```

---

**The Entity awaits your failure.** 🎭✨

**Full Changelog**: https://github.com/rafehatfield/rlike/compare/v3.0.0...v3.2.0

