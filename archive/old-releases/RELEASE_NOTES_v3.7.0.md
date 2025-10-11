# 🎁 Release Notes - v3.7.0: Monster Equipment & Loot

**Release Date:** October 10, 2025  
**Branch:** main  
**Previous Version:** v3.6.1

---

## 🎯 Overview

This release introduces the **Monster Equipment & Loot System**, a major gameplay enhancement that makes combat more rewarding and strategic. Monsters now spawn with equipment, and players can loot their gear upon defeat. This release also includes critical bug fixes and comprehensive error logging infrastructure.

---

## ✨ New Features

### **🗡️ Monster Equipment System**
Monsters now spawn with weapons and armor that affect their combat capabilities:

- **Weapon Spawn Rate:** 75% of orcs spawn with weapons (club, dagger, or shortsword)
- **Armor Spawn Rate:** 50% of orcs spawn with leather armor
- **Equipment Effects:** Monsters wielding weapons deal more damage; monsters wearing armor have higher AC
- **Visible Equipment:** Mouse-over tooltips show what monsters are wielding/wearing
- **Natural Progression:** Fight tougher monsters to get better gear

**Example:**
```
Orc
Wielding: Shortsword (+2 damage)
Wearing: Leather Armor (+1 AC)
```

### **📦 Enhanced Loot System**
Monsters drop all their equipment and inventory items when defeated:

- **Equipment Drops:** All equipped weapons and armor drop on death
- **Inventory Drops:** Items monsters picked up during combat also drop
- **Strategic Positioning:** Items spread around the monster's death location
- **Multi-Entity Tooltips:** Hover over a tile with multiple items to see everything

### **🔍 Comprehensive Error Logging**
New logging infrastructure to track down bugs faster:

- **errors.log:** All ERROR and CRITICAL messages logged to file (always active)
- **Clean Console:** "No actions taken" spam removed, only important actions shown
- **Testing Logs:** `monster_actions.log` and `combat_debug.log` still available in testing mode
- **Better Debugging:** Full error history with timestamps for post-playtest analysis

See `docs/LOGGING.md` for full documentation.

---

## 🐛 Bug Fixes

### **Critical: ComponentType Scoping Bug** (6 commits)
**Problem:** Local imports of `ComponentType` inside functions caused scoping issues, leading to `NameError: name 'ComponentType' is not defined`.

**Impact:** Monsters couldn't pick up items, spell usage failed, equipment system crashed.

**Files Fixed:**
- `components/ai.py`
- `components/item_seeking_ai.py`
- `item_functions.py`
- `spells/spell_executor.py`
- `config/entity_factory.py`
- `loader_functions/initialize_new_game.py`
- `components/monster_action_logger.py`

**Solution:** All `ComponentType` imports moved to module level. Added regression tests to prevent recurrence.

### **Item Duplication Bug**
**Problem:** Items dropped by dead monsters appeared multiple times on the ground, could be picked up multiple times, and would disappear when equipped.

**Root Cause:** Items weren't being removed from monster's equipment/inventory when dropped, leading to duplicate entity references.

**Fix:** Proper cleanup of equipment and inventory references when monsters die.

### **Tooltip Coordinate Mismatch**
**Problem:** Tooltips showed wrong items when hovering over sidebar inventory.

**Cause:** Y-coordinate calculations didn't account for all hotkeys (off-by-one error).

**Fix:** Corrected coordinate calculations to match sidebar rendering.

### **Monster Action Logging Spam**
**Problem:** Console flooded with "INFO: Orc at (x, y) turn complete: no actions taken" messages.

**Fix:** Changed "no actions taken" to DEBUG level (file only), important actions remain at INFO level (console + file).

---

## 📊 Technical Improvements

### **Monster Item Seeking Restored**
- Monsters now correctly seek and pick up items during combat
- Items closer than the player are prioritized
- Monsters only seek items when not in combat or taunted

### **Monster Scroll Usage Restored**
- Monsters can use scrolls from their inventory
- 75% failure rate (increased from 50%)
- Various failure effects: backfire, fizzle, wrong target

### **Enhanced Tooltips**
- Multi-entity tooltips show all items/monsters/corpses on a tile
- Living monsters prioritized over corpses
- Equipment displayed for monsters
- Clear, readable format

### **Test Coverage**
- **30 new tests** for monster equipment and loot
- **10 new tests** for enhanced tooltips
- **10 new tests** for ComponentType scoping (regression prevention)
- **1991/1992 tests passing (99.9%)**

---

## 📚 Documentation

### **New Documentation**
- **`docs/LOGGING.md`** - Complete logging system documentation
- **`docs/MONSTER_LOOT_DESIGN.md`** - Monster equipment & loot system design
- **`docs/TECH_DEBT_ANALYSIS_2025.md`** - Comprehensive technical debt analysis
- **`docs/COMPONENT_TYPE_BEST_PRACTICES.md`** - Import best practices

---

## 🎮 Gameplay Impact

### **Combat Rewards**
- **More Rewarding:** Every orc you defeat has a 75% chance of dropping a weapon
- **Strategic Choices:** Do you fight the armed orc or avoid them?
- **Natural Progression:** Better gear comes from tougher fights
- **Inventory Management:** Monsters might be carrying scrolls you can use

### **Monster Behavior**
- **Smarter Monsters:** Orcs pick up weapons during combat
- **Unpredictable:** Monsters might grab a scroll and use it (usually fails hilariously)
- **More Dangerous:** An orc with a shortsword hits harder than an unarmed one

---

## 🔧 Configuration

### **Monster Equipment Configuration**
Equipment spawn rates and pools are configured in `config/entities.yaml`:

```yaml
orc:
  equipment:
    spawn_chances:
      main_hand: 0.75  # 75% chance of weapon
      chest: 0.50      # 50% chance of armor
    equipment_pool:
      main_hand:
        - item: "club"
          weight: 40
        - item: "dagger"
          weight: 30
        - item: "shortsword"
          weight: 30
```

---

## 🚀 Upgrade Notes

### **For Players**
- No save game changes required
- Existing saves will work normally
- New monster equipment only appears in new dungeon levels

### **For Developers**
- **Error logging is always active** - check `errors.log` after playtesting
- **Monster action logging** - use `--test` flag to enable detailed logs
- **ComponentType imports** - always use module-level imports (see `docs/COMPONENT_TYPE_BEST_PRACTICES.md`)

---

## 📈 Stats

- **Commits:** 39
- **Files Changed:** 33
- **Insertions:** +43,481
- **Deletions:** -12,827
- **New Tests:** 50
- **Test Pass Rate:** 99.9% (1991/1992)

---

## 🔮 What's Next?

With the Monster Equipment & Loot system complete, the next focus is on **Technical Debt Reduction**:

- **Phase 1:** Component Access Standardization (2 weeks)
- **Phase 2:** Break Up Monolithic Files (3 weeks)
- **Phase 3:** Type Hints & Test Organization (2 weeks)

See `docs/TECH_DEBT_ANALYSIS_2025.md` for the full plan.

---

## 🙏 Acknowledgments

Special thanks to the rigorous playtesting that helped identify the ComponentType scoping bug and tooltip issues. The comprehensive error logging added in this release will make future bug hunting much easier!

---

## 🐛 Known Issues

- One skipped test in pathfinding (non-critical)
- DeprecationWarnings in tcod library (external, not our code)
- SyntaxWarning in save_load test (regex escape sequence)

---

**Enjoy looting those orcs! 🗡️**

