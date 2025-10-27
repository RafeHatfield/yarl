# Release Notes - v3.12.0: The Polish Update

**Release Date:** October 18, 2025  
**Tag:** v3.12.0  
**Status:** ✅ STABLE  
**Depth Score:** 49.5/64 (77%) - Up from 38/64 (59%) in v3.9.0

---

## 🎉 Major Highlights

This release represents **3 major versions** worth of features, stability improvements, and quality of life enhancements:

- ✨ **Complete Ring System** - 15 unique rings with passive effects
- 🛡️ **Resistance System** - Elemental damage types and resistances
- ⏱️ **Turn Economy** - All actions now have tactical weight
- 🔍 **Identify Scroll** - Temporary identification powers
- 💍 **Ring Bug Fixes** - 3 critical ring bugs resolved
- 🎨 **UI Improvements** - Clickable menus and wider sidebar
- 📚 **Documentation Cleanup** - 50+ docs organized

**Overall Progress:** +18% depth score improvement (+11.5 points)

---

## ✨ v3.12.0 - Ring Polish & QoL (October 17-18, 2025)

### 🐛 Critical Ring Bug Fixes

**Ring of Regeneration Not Healing**
- **Issue:** Ring checked for non-existent `turn_count` attribute
- **Fix:** Integrated with TurnManager to pass turn number through status effect system
- **Result:** Now heals +1 HP every 5 turns with visual feedback
- **Files:** `components/ring.py`, `components/status_effects.py`, `game_actions.py`

**Auto-Identification Crash**
- **Issue:** Used non-existent `MB.discovery()` method
- **Fix:** Changed to `MB.success()` for green success messages
- **Result:** Equipping unidentified items now properly identifies them
- **Files:** `components/equipment.py`

**Ring Unequipping Wrong Slot**
- **Issue:** Unequipping right ring would unequip left ring, then duplicate ring on both fingers
- **Fix:** Check if ring is already equipped BEFORE checking for available slots
- **Result:** Rings now correctly unequip from their actual slot
- **Files:** `components/equipment.py`

### 🎨 Quality of Life Improvements

**Clickable Main Menu**
- Main menu options are now clickable with mouse
- Keyboard shortcuts (a, b, c) still work
- Better accessibility and modern UX
- **Files:** `input_handlers.py`, `engine.py`

**Wider Sidebar**
- Increased sidebar width from 20 to 24 tiles (20% wider)
- Reduces text truncation for item names
- Better readability for equipment and inventory
- Screen width: 100 → 104 tiles
- **Files:** `config/ui_layout.py`

### 📚 Documentation Cleanup

**Organized 50+ Documentation Files**
- Root directory: 57 → 7 active docs
- Created structured `docs/` hierarchy:
  - `archive/bug-fixes/` - 8 bug fix docs
  - `archive/completed-features/` - 13 feature completions
  - `archive/sessions/` - 9 session summaries
  - `archive/releases/` - Version release notes
  - `testing/` - 12 testing docs
  - `guides/` - 2 playtesting guides
  - `reference/` - 3 game content references
  - `planning/` - 4 design docs
- Created `docs/README.md` as documentation index

**Active Docs (Kept in Root)**
- DEPTH_SCORE_TRACKING.md
- NEXT_FEATURES_REAL.md
- PLAYER_PAIN_POINTS.md
- PROJECT_STATS.md
- README.md
- ROADMAP.md
- TRADITIONAL_ROGUELIKE_FEATURES.md

---

## 💍 v3.11.1 - Ring System (October 16, 2025)

### 15 Unique Ring Types Across 2 Equipment Slots

**Defensive Rings (3)**
- Ring of Protection - +2 AC
- Ring of Regeneration - Heal 1 HP/5 turns
- Ring of Resistance - +10% all resistances

**Offensive Rings (3)**
- Ring of Strength - +2 STR
- Ring of Dexterity - +2 DEX
- Ring of Might - +1d4 damage to all attacks

**Utility Rings (4)**
- Ring of Teleportation - 20% chance to teleport when hit
- Ring of Invisibility - Start each level invisible for 5 turns
- Ring of Searching - Reveal traps/secrets within 3 tiles
- Ring of Free Action - Immune to paralysis and slow

**Magic Rings (3)**
- Ring of Wizardry - +1 to all spell effects
- Ring of Clarity - Immune to confusion
- Ring of Speed - +10% movement speed

**Special Rings (2)**
- Ring of Constitution - +2 CON (+20 max HP)
- Ring of Luck - +5% crit chance, better loot

### Ring System Features
- ✅ 2 equipment slots (left and right hand)
- ✅ Passive effects (always active while worn)
- ✅ Auto-identify on equip
- ✅ Unidentified ring appearances (copper, silver, gold, etc.)
- ✅ Turn-based effects (Regeneration)
- ✅ Combat triggers (Teleportation on hit)
- ✅ Status immunities (Free Action, Clarity)
- ✅ Stat bonuses (STR, DEX, CON)
- ✅ Combat bonuses (AC, damage, crit chance)

### Implementation Details
- **Component:** `components/ring.py` with `RingEffect` enum
- **Equipment:** `components/equipment.py` - 2 ring slots
- **Integration:** Bonuses integrated with Fighter, AI, and combat systems
- **Configuration:** 15 rings defined in `config/entities.yaml`
- **Tests:** Comprehensive test coverage for all ring mechanics

**Depth Score Impact:** +2 (Build Diversity 5 → 7)

---

## 🛡️ v3.11.0 - Resistance System (October 16, 2025)

### Elemental Damage Types & Resistances

**6 Damage Types:**
- Fire
- Cold
- Poison
- Lightning
- Acid
- Physical

**Resistance System:**
- Equipment can provide resistances (0-100%)
- Monsters can have innate resistances
- Damage reduction calculated: `final_damage = base_damage * (1 - resistance%)`
- Boss monsters have thematic resistances:
  - Dragon Lord: Fire immunity
  - Demon King: Poison immunity

### Implementation
- **Fighter Component:** `take_damage()` now accepts `damage_type` parameter
- **Damage Calculation:** Automatic resistance checks and damage reduction
- **Configuration:** Resistances defined in `entities.yaml`
- **Spell Integration:** All spells now specify damage types
- **Logging:** Comprehensive resistance logging for debugging

**Example:**
```
Dragon Lord hit by Fireball (50 fire damage):
→ 100% fire resistance
→ Final damage: 0 (immune!)

Player with Ring of Resistance (+10%) hit by Dragon Breath (40 fire damage):
→ 10% fire resistance
→ Final damage: 36 (reduced by 4)
```

**Depth Score Impact:** +1.5 (Build Diversity +0.5, Combat System +1)

---

## ⏱️ v3.11.0 - Turn Economy (October 15, 2025)

### Every Action Matters

**Actions That Cost 1 Turn:**
- ✅ Picking up items (`'g'` key)
- ✅ Using items (potions, scrolls, wands)
- ✅ Dropping items (`'d'` key)
- ✅ Equipping/unequipping equipment
- ✅ Completing targeting (selecting spell targets)
- ✅ Throwing items
- ✅ Using stairs
- ✅ Waiting (`'.'` key)

**Actions That Are FREE:**
- Opening inventory to look (`'i'` key)
- Examining items
- Reading item descriptions
- Entering targeting mode (turn consumed on target selection)
- Failed actions (no item to pick up, etc.)

### Design Philosophy
**Traditional Roguelike Turn Economy:**
- Movement = 1 turn
- Combat = 1 turn
- Item actions = 1 turn
- Menu navigation = FREE

This makes resource management tactical - you can't safely reorganize inventory mid-combat!

**Depth Score Impact:** +2 (Resource Management +2)

---

## 🔍 v3.11.0 - Identify Scroll (October 15, 2025)

### Temporary Identification Powers

**How It Works:**
1. Read Scroll of Identify
2. Gain "Identify Mode" status effect (10 turns)
3. Can identify 1 item per turn automatically
4. Effect shows remaining turns: "🔍 Identify Mode: 8 turns"

**Identification Sources:**
- Scroll of Identify (10 turns, 1 item/turn)
- Auto-identify on equip (immediate)
- Shops (future feature)

**Integration:**
- Status effect: `IdentifyModeEffect` in `components/status_effects.py`
- Spell: Registered in `spell_catalog.py`
- Turn-based processing with counter reset

**Depth Score Impact:** +0.5 (Resource Management)

---

## 📜 v3.10.0 - Final Scrolls (October 14, 2025)

### Fear Scroll
- Area-of-effect fear spell
- Enemies flee in terror for 5 turns
- Creates tactical breathing room
- AI modification: monsters actively flee from player

### Detect Monster Scroll
- Reveals all monsters on the floor
- 20-turn detection effect
- See through walls and fog of war
- Perfect for planning your approach

**Total Scrolls:** 22 types (8 → 22 expansion complete!)

**Depth Score Impact:** +0.5 (Discovery)

---

## 🔧 Technical Improvements

### Architecture
- **Component System:** Enhanced `Ring` component with passive effects
- **Status Effects:** Extended with `IdentifyModeEffect`, `FearEffect`, `DetectMonsterEffect`
- **Turn Management:** Integrated turn number throughout status effect system
- **Damage System:** Enhanced with elemental damage types and resistance calculations

### Testing
- **Ring System Tests:** Comprehensive coverage for all ring mechanics
- **Turn Economy Tests:** 14 tests verifying turn consumption
- **Resistance Tests:** Configuration pipeline and damage calculation tests
- **Bug Fix Tests:** Regression tests for all 3 ring bugs

### Configuration
- **Data-Driven:** All rings, resistances, and items defined in YAML
- **Entity Factory:** Enhanced to handle ring creation and resistance parsing
- **Validation:** Automatic validation of entity configurations

### UI/UX
- **Sidebar:** Wider (24 tiles) for better readability
- **Main Menu:** Mouse clickable
- **Auto-Identify:** Visual feedback on equip
- **Messages:** Consistent MessageBuilder usage

---

## 📊 Statistics

### Codebase
- **Total Files:** 322 Python files
- **Total Lines:** 113,539 lines of code
- **Test Coverage:** 51,043 lines (45% test coverage!)
- **Documentation:** 76 markdown files (organized!)

### Content
- **15** Ring types
- **22** Scroll types
- **11** Potion types
- **9** Wand types
- **50+** Monster types
- **30+** Spell types
- **6** Damage/resistance types

### Game Depth
- **Discovery:** 6/10 (+1 from v3.9.0)
- **Resource Management:** 7/10 (+2 from v3.9.0)
- **Build Diversity:** 8/10 (+3 from v3.9.0)
- **Emergent Gameplay:** 7/10 (+0 from v3.9.0)
- **Memorable Moments:** 6/10 (+0 from v3.9.0)
- **Combat System:** 8.5/10 (+1.5 from v3.9.0)
- **Progression:** 7/10 (+0 from v3.9.0)

**Overall:** 49.5/64 (77%) - Up from 38/64 (59%)

---

## 🐛 Known Issues

### Resolved in This Release
- ✅ Ring of Regeneration not healing
- ✅ Auto-identification crash
- ✅ Ring unequipping wrong slot
- ✅ Sidebar text truncation
- ✅ Main menu not clickable

### Still Outstanding
- None currently tracked for v3.12.0

---

## 🔄 Migration Notes

### For Players
- **Wider Screen:** Game window is now 104 tiles wide (was 100)
- **Ring System:** 2 new equipment slots to manage
- **Turn Economy:** Inventory management now costs turns
- **Clickable UI:** Main menu now supports mouse clicks

### For Developers
- **Turn Number:** Status effects now receive `turn_number` parameter
- **Damage Types:** All damage-dealing code should specify `damage_type`
- **Resistances:** Fighter component now has `resistances` dict
- **Ring Component:** New component type for ring items

---

## 📝 Upgrade Instructions

### From v3.9.0
1. **Backup your save:** Save files are compatible
2. **Update code:** Pull latest from main branch
3. **Install dependencies:** `pip install -r requirements.txt` (no changes)
4. **Run tests:** `python -m pytest tests/` (all should pass)
5. **Play!** Start game with `python3 engine.py`

### Configuration
- No configuration changes required
- Rings automatically spawn based on dungeon level
- Resistance system automatically active

---

## 🎯 What's Next?

### v3.13.0 - Exploration & Discovery (Planned)
- 🗺️ **Vaults** - Special treasure rooms with challenges
- 🚪 **Secret Doors** - Hidden passages to discover
- 📦 **Chests** - Lootable containers (trapped? locked?)
- 🪧 **Signposts** - Flavor text and world-building

**Expected Impact:** +2 depth score (Discovery 6 → 8)

### Future Roadmap
- Victory Condition (Amulet of Yendor)
- Blessed/Cursed Items
- Unique Artifacts
- Classes/Backgrounds
- More coming...

---

## 🙏 Acknowledgments

This release represents significant progress toward making Catacombs of Yarl one of the best traditional roguelikes. The game now has:
- Professional-grade test coverage (45%)
- Comprehensive documentation (76 docs)
- Rich content (100+ items, 50+ monsters, 30+ spells)
- Modern architecture (ECS, event-driven)
- Classic roguelike depth (77% depth score)

Thank you for playing and testing! 🎉

---

## 📚 Documentation

- **Depth Tracking:** `DEPTH_SCORE_TRACKING.md`
- **Next Features:** `NEXT_FEATURES_REAL.md`
- **Design Guidelines:** `PLAYER_PAIN_POINTS.md`
- **Project Stats:** `PROJECT_STATS.md`
- **Feature Archive:** `docs/archive/completed-features/`
- **Bug Fixes:** `docs/archive/bug-fixes/`
- **Testing Guides:** `docs/testing/`
- **All Docs:** `docs/README.md`

---

**Download:** Coming soon  
**Source:** [GitHub Repository]  
**Discord:** [Community Server]  
**Bug Reports:** [Issue Tracker]

---

*"In the depths of Yarl, every ring tells a story..."* 💍✨

