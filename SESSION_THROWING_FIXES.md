# Throwing System & Auto-Explore Fixes - Complete Session Summary

## 🎯 Session Goals
1. Fix throwing system (import errors, selection issues)
2. Implement right-click auto-explore feature
3. Show item stack quantities in sidebar

---

## 🐛 Bugs Fixed

### **1. Input System Missing Throw Handlers** ✅
**Problem:** Keyboard selection (a, b, c) not working in throw menu  
**Root Cause:** `InputSystem` missing handlers for `THROW_SELECT_ITEM` and `THROW_TARGETING` states  
**Fix:** Added both states to `key_handlers` dict in `engine/systems/input_system.py`  
**Result:** Keyboard selection now works in throw menus!

### **2. tcod.line Import Error (Round 1)** ✅
**Problem:** `ModuleNotFoundError: No module named 'tcod.line'`  
**Root Cause:** Incorrect import `import tcod.line`  
**Attempted Fix:** Changed to `from tcod.line import bresenham`  
**Result:** Still failed - `tcod.line` is not a module!

### **3. tcod.line Import Error (Round 2)** ✅
**Problem:** `AttributeError: 'function' object has no attribute 'bresenham'`  
**Root Cause:** `tcod.line` is a deprecated function, not a module!  
**Final Fix:** Use modern `from tcod.los import bresenham` API  
**Changes:**
- Import: `from tcod.los import bresenham`
- Usage: `bresenham((x1, y1), (x2, y2))` (takes tuples, not separate args)
- Returns: NumPy array of shape (length, 2)
- Convert: `[(int(x), int(y)) for x, y in line_array]`

**Files Fixed:** `throwing.py`, `components/fighter.py`  
**Result:** Throwing now works without import errors!

### **4. Item Stack Count Missing** ✅
**Problem:** Stacked items (e.g., "5x Healing Potion") showing as "Healing Potion" in sidebar  
**Root Cause:** Sidebar using entity's `get_display_name()` instead of item component's  
**Fix:** Use `item.item.get_display_name(show_quantity=True)` in `ui/sidebar.py`  
**Result:** Sidebar now shows "5x Healing Potion"!

### **5. AutoExplore Initialization Error** ✅
**Problem:** `AutoExplore.__init__() takes 1 positional argument but 2 were given`  
**Root Cause:** `AutoExplore()` doesn't accept owner in `__init__`  
**Fix:** Changed `AutoExplore(player)` to `AutoExplore()` + `auto_explore.owner = player`  
**Result:** AutoExplore component initializes correctly!

### **6. ComponentRegistry Method Name** ✅
**Problem:** `'ComponentRegistry' object has no attribute 'register'`  
**Root Cause:** Used wrong method name `register()` instead of `add()`  
**Fix:** Changed `player.components.register()` to `player.components.add()`  
**Result:** Components register correctly!

---

## ⭐ New Features Implemented

### **Right-Click Auto-Explore** 🗺️
**What:** Right-click on empty ground to start/stop auto-explore  
**Why:** Makes exploration fully mouse-controllable (no keyboard needed!)  
**Implementation:** `game_actions.py` - `_handle_right_click()` detects empty ground  
**UX Enhancements:**
- Shows adventure quote when starting (cyan text)
- Shows "Auto-exploring... (any key to cancel)" message
- Right-click again to cancel
- Any key also cancels

**Context-Aware Right-Click Logic:**
1. **Enemy present?** → Open throw menu (auto-target)
2. **Item present?** → Pathfind and pick up
3. **Empty ground?** → Start auto-explore ⭐ NEW!

### **Right-Click Throw Shortcut** 🎯
**What:** Right-click on enemy opens throw menu pre-targeted to that enemy  
**Why:** Faster combat - no manual targeting needed!  
**Implementation:** `game_actions.py` - stores target in `state_manager.set_extra_data("throw_target")`  
**Result:** Right-click enemy → Press 'a' → Auto-throw! Super fast! ⚡

---

## 📊 Complete Mouse Control Achieved!

| Action | Mouse Control | Status |
|--------|--------------|---------|
| Movement | Left-click | ✅ |
| Attack | Left-click enemy | ✅ |
| Pick up items | Right-click item | ✅ |
| Throw items | Right-click enemy | ✅ |
| Auto-explore | Right-click ground | ✅ **NEW!** |
| Use spells | Left-click when targeting | ✅ |
| Inventory | Click items in sidebar | ✅ |
| Equipment | Click items in sidebar | ✅ |

**Only keyboard-required:**
- Menu selection (a, b, c) - standard roguelike interface!
- Opening menus (i, d, c) - but sidebar has buttons too

---

## 🔧 Technical Details

### **tcod API Versions**
**Old (deprecated):**
```python
import tcod.line  # ❌ Not a module!
tcod.line.bresenham(x1, y1, x2, y2)  # ❌ Wrong signature
```

**New (modern):**
```python
from tcod.los import bresenham  # ✅ Correct import
line_array = bresenham((x1, y1), (x2, y2))  # ✅ Takes tuples
line = [(int(x), int(y)) for x, y in line_array]  # ✅ Convert numpy→list
```

### **Component Registration Pattern**
**Correct:**
```python
component = ComponentClass()
component.owner = entity
entity.components.add(ComponentType.COMPONENT, component)
```

**Incorrect:**
```python
component = ComponentClass(entity)  # ❌ Most don't take owner in __init__
entity.components.register(...)  # ❌ No register method!
```

---

## 🎮 User Experience Improvements

### **Accessibility Wins:**
- ✅ One-handed play (mouse only)
- ✅ Laptop trackpad friendly
- ✅ Relaxed gameplay (lean back with mouse)
- ✅ Switch between mouse/keyboard freely

### **Workflow Examples:**

**Pure Mouse Exploration:**
1. Right-click ground → Auto-explore starts
2. Monster found → Left-click to attack
3. Loot appears → Right-click to pick up
4. Right-click ground → Continue exploring!

**Combat with Throwing:**
1. Spot dangerous enemy
2. Right-click enemy → Throw menu opens (pre-targeted!)
3. Press 'a' for paralysis potion
4. Enemy frozen for 5 turns!
5. Walk up and finish them off

---

## 📁 Files Modified

1. **engine/systems/input_system.py** - Added throw state handlers
2. **throwing.py** - Fixed bresenham import and usage
3. **components/fighter.py** - Fixed bresenham import for bow animations
4. **ui/sidebar.py** - Show item stack quantities
5. **game_actions.py** - Implemented right-click auto-explore
6. **RIGHT_CLICK_FEATURES.md** - Comprehensive mouse control guide

---

## ✅ Testing Checklist

- [x] Press 't' to open throw menu
- [x] Select item with keyboard (a-z keys)
- [x] Target enemy with mouse click
- [x] Item throws with projectile animation
- [x] Right-click enemy opens throw menu
- [x] Select item, auto-throws at enemy
- [x] Stacked items show quantity (e.g., "5x Healing Potion")
- [x] No import errors when throwing
- [x] Right-click ground starts auto-explore
- [x] Adventure quote displays
- [x] Right-click again cancels auto-explore
- [ ] Menu mouse clicks (NOT IMPLEMENTED - use keyboard)

---

## 🚀 Result

**The game is now fully playable with just the mouse!** 🎉

All core gameplay actions can be performed with mouse clicks:
- Combat ✅
- Movement ✅
- Looting ✅
- Throwing ✅
- Exploration ✅

Only menu selection requires keyboard (standard roguelike UX).

This is a **major accessibility and usability win**! 🏆
