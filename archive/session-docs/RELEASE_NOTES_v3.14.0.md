# Release Notes - Version 3.14.0

**Release Date:** October 18, 2025  
**Branch:** `feature/themed-vaults` → `main`  
**Theme:** Themed Vaults & UI Architecture Improvements

---

## 🎯 Overview

This release completes **Phase 2 of the Exploration & Discovery feature set**, introducing **Themed Vaults** with keys, locked doors, and unique loot/monster configurations. It also includes a major **UI architecture refactoring** that eliminates a class of recurring bugs in sidebar interactions.

---

## ✨ New Features

### 🔑 Key System
- **4 Key Types:** Bronze, Silver, Gold, Dragon Scale
- **Consumable Unlocking:** Keys are consumed when used to unlock chests or doors
- **Visual Distinction:** Each key type has unique coloring
- **Integration:** Works with locked chests and locked doors

### 🚪 Locked Doors
- **4 Door Types:** Bronze Door, Silver Door, Gold Door, Crimson Door
- **Key-Based Unlocking:** Each door requires a specific key type
- **Interactive:** Click on doors to unlock them (if you have the key)
- **Permanent Removal:** Unlocked doors are removed and tiles become passable

### 🏛️ Themed Vaults (5 Types)
Vaults now have distinct themes that affect their appearance, monsters, and loot:

1. **Ancient Library** (Levels 1-4)
   - Bronze walls
   - Wizard enemies (casters)
   - Scroll-heavy loot
   - Requires: Bronze Key

2. **Armory** (Levels 2-6)
   - Steel-gray walls
   - Warrior enemies (melee specialists)
   - Weapon/armor loot
   - Requires: Silver Key

3. **Treasure Vault** (Levels 4-8)
   - Golden walls
   - Rogue enemies (fast/evasive)
   - Gold, gems, rings
   - Requires: Gold Key

4. **Sacred Shrine** (Levels 5-9)
   - Silver-white walls
   - Cleric enemies (healers)
   - Potions, holy items
   - Requires: Gold Key

5. **Dragon's Hoard** (Levels 7+)
   - Crimson walls
   - Dragon enemies (elite)
   - Legendary loot
   - Requires: Dragon Scale

**Themed Features:**
- **Custom Wall Colors:** Each vault type has distinct visual appearance
- **Themed Monster Tables:** Encounter enemies appropriate to the vault type
- **Elite Scaling:** Vault monsters have boosted HP, power, and defense
- **Quality Loot:** Guaranteed high-quality chests and bonus items
- **Depth-Aware Spawning:** Vaults appear at appropriate dungeon levels

### 🗺️ Signpost Vault Hints
- **13 New Vault-Themed Messages:** Cryptic hints about vault locations and required keys
- **Depth Filtering:** Messages appear at appropriate dungeon levels
- **Lore Integration:** Hints tie into vault themes and lore

---

## 🛠️ Technical Improvements

### 🎨 Centralized Sidebar Layout System
**Problem Solved:** Eliminated recurring off-by-one bugs in sidebar interactions (tooltips, clicks, rendering).

**New Architecture:**
- **`ui/sidebar_layout.py`:** Single source of truth for Y-coordinate calculations
- **`calculate_sidebar_layout()`:** Dynamic position calculator based on actual counts
- **`get_hotkey_list()`:** Canonical hotkey definitions
- **`get_equipment_slot_list()`:** Canonical equipment slot order
- **`SidebarLayoutPositions`:** Type-safe dataclass for all Y positions

**Benefits:**
- ✅ Adding/removing hotkeys: Update one list, all modules sync automatically
- ✅ Adding/removing equipment slots: Same - one change propagates everywhere
- ✅ No more manual Y-offset calculations scattered across 3 files
- ✅ Compiler/runtime catches misalignment issues
- ✅ Self-documenting layout structure

**Modules Updated:**
- `ui/sidebar.py` - Rendering
- `ui/sidebar_interaction.py` - Click detection
- `ui/tooltip.py` - Hover tooltips

### ✅ Comprehensive Test Suite
**New Test File:** `tests/test_sidebar_layout.py`

**20 Tests Across 5 Categories:**
1. **Layout Calculations** (6 tests) - Validates positioning logic
2. **Hotkey List** (4 tests) - Ensures hotkey data integrity
3. **Equipment Slot List** (4 tests) - Validates equipment slot data
4. **Layout Consistency** (3 tests) - Tests dynamic resizing behavior
5. **Regression Prevention** (3 tests) - Prevents specific known bugs

**All 20 tests pass ✅**

---

## 🐛 Bug Fixes

### Critical Fixes
1. **Keys Defined in Wrong YAML Section**
   - **Issue:** Keys were in `wands:` section, causing "Unknown wand spell ''" warnings
   - **Fix:** Moved keys to `spells:` section where they belong
   - **Impact:** 7 warnings eliminated

2. **Trapped Chest Crash (UnboundLocalError: 'MB')**
   - **Issue:** MessageBuilder imported locally, went out of scope for trap code
   - **Fix:** Removed redundant local imports, use global import
   - **Impact:** Trapped chests now work correctly

3. **Sidebar Inventory Click Detection Off-by-One**
   - **Issue:** Y-coordinate calculation counted 8 hotkeys, but only 7 existed
   - **Fix:** Updated calculation to use actual hotkey count (7)
   - **Impact:** All inventory items now clickable

4. **Leftover Variable Reference in Sidebar Rendering**
   - **Issue:** `y += 1` reference from pre-refactoring code
   - **Fix:** Calculate hint_y based on layout positions
   - **Impact:** Game starts without crashes

### Minor Fixes
5. **Monster Equipment Config Access Error**
   - **Issue:** Attempting to access `constants.monster_equipment` as dict
   - **Fix:** Use `get_monster_equipment_config()` helper function
   - **Impact:** Monster AI no longer crashes

6. **Non-Existent Wand Reference in Testing Config**
   - **Issue:** `wand_of_magic_missile` doesn't exist in entities.yaml
   - **Fix:** Changed to `wand_of_teleportation`
   - **Impact:** Testing mode works without warnings

---

## 📊 Changes Summary

### Files Added (6)
- `components/locked_door.py` - Locked door component
- `config/vault_themes.yaml` - Themed vault configurations
- `config/vault_theme_registry.py` - Vault theme management
- `docs/planning/THEMED_VAULTS_PHASE2_PLAN.md` - Phase 2 documentation
- `tests/test_sidebar_layout.py` - Sidebar layout tests
- `ui/sidebar_layout.py` - Centralized layout calculator

### Files Modified (13)
- `components/ai.py` - Fixed monster equipment config access
- `components/component_registry.py` - Added LOCKED_DOOR type
- `components/map_feature.py` - Added DOOR type
- `config/entities.yaml` - Added keys, locked doors, vault hints
- `config/entity_factory.py` - Added key item handling
- `config/level_templates_testing.yaml` - Added keys, fixed wand reference
- `config/signpost_messages.yaml` - Added 13 vault-themed hints
- `map_objects/game_map.py` - Integrated themed vaults
- `mouse_movement.py` - Added locked door/chest key handling
- `ui/sidebar.py` - Uses centralized layout
- `ui/sidebar_interaction.py` - Uses centralized layout
- `ui/tooltip.py` - Uses centralized layout

### Code Statistics
- **Lines Added:** ~5,089
- **Lines Removed:** ~4,491
- **Net Change:** +598 lines
- **Tests Added:** 20 (all passing)
- **Bugs Fixed:** 6

---

## 🧪 Testing

### Manual Testing Completed
- ✅ Keys spawn and can be picked up
- ✅ Locked chests require correct key
- ✅ Locked doors unlock with correct key
- ✅ Themed vaults spawn with correct visuals
- ✅ Elite monsters have appropriate scaling
- ✅ Vault loot is higher quality
- ✅ Signpost hints appear at correct depths
- ✅ Trapped chests deal damage correctly
- ✅ Sidebar clicks work for all items
- ✅ Tooltips align correctly
- ✅ Equipment equipping/unequipping works

### Automated Testing
- **20/20 sidebar layout tests pass**
- **All existing tests continue to pass**

---

## 🎮 Gameplay Impact

### Player Experience
- **Exploration Depth:** Vaults now feel unique and memorable
- **Risk/Reward:** Finding keys creates treasure hunt gameplay
- **Visual Feedback:** Themed walls make vaults instantly recognizable
- **Challenge Scaling:** Elite monsters provide appropriate difficulty

### Balance Notes
- **Key Rarity:** Keys are rare drops, creating scarcity
- **Vault Difficulty:** Elite monsters are 2x tougher (HP, power, defense)
- **Loot Quality:** Vaults guarantee 2-4 chests with high-quality loot
- **Depth Progression:** Vault types scale with dungeon depth

---

## 📝 Known Issues

### Non-Critical
- **Locked Chests:** Currently no way to unlock without key (by design for now)
- **Mimic System:** Placeholder messages exist, but mimics not yet implemented
- **Poison Traps:** Placeholder messages exist, but poison status effect not yet implemented
- **Monster Spawn Traps:** Placeholder messages exist, but monster spawning not yet implemented

---

## 🗺️ Roadmap Update

### Completed
- ✅ **Phase 1:** Simple Vaults (v3.13.0)
- ✅ **Phase 2:** Themed Vaults (v3.14.0) ← **YOU ARE HERE**

### Next Up
- 🔜 **Phase 3:** Advanced Vault Features (Mini-bosses, vault-specific loot tables)
- 🔜 **Slice 5:** Complete secret door visual effects and discovery feedback
- 🔜 **Mimic System:** Implement chest mimics
- 🔜 **Trap System:** Complete poison and monster spawn traps

---

## 🙏 Acknowledgments

Special thanks to playtesting which uncovered:
- Keys in wrong YAML section causing wand warnings
- Trapped chest crash bug
- Sidebar click detection issues
- Variable reference bugs in sidebar rendering

These bugs were all caught and fixed before release! 🎯

---

## 📦 Installation & Upgrade

```bash
# Pull latest changes
git pull origin main

# Activate virtual environment
source ~/.virtualenvs/rlike/bin/activate

# Install any new dependencies (none in this release)
pip install -r requirements.txt

# Run the game
python engine.py
```

---

## 🎉 Conclusion

Version 3.14.0 delivers a major step forward in **dungeon exploration depth** with themed vaults that provide unique, memorable encounters. The **centralized sidebar layout system** represents a significant **technical improvement** that will prevent a class of bugs from recurring and make future UI changes much easier.

**Happy exploring!** 🗝️🏛️

---

*For detailed technical documentation, see:*
- `docs/planning/THEMED_VAULTS_PHASE2_PLAN.md`
- `ui/sidebar_layout.py` (source code documentation)

