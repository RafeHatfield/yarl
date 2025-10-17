# Equipment Unequip Fix

**Date:** October 17, 2025
**Issue:** Can't unequip items from sidebar
**Status:** ✅ FIXED

---

## 🐛 The Problem

**User Report:**
> "i can't unequip anything; i think perhaps we've never implemented that? we used to make you open the separate inventory screen to do it, but i don't want to use that screen for anything any more. you should be able to unequip stuff by clicking on it in the left menu, in the Equipment section"

**What Was Happening:**
- Clicking on equipped items in the sidebar's EQUIPMENT section did literally nothing
- The code had a `pass` statement - it was intentionally not implemented
- Comment said: `"For now, left-click on equipment does nothing (could add "examine" later)"`
- Players had no way to unequip items without opening the inventory menu

---

## 🔍 Root Cause

**File:** `game_actions.py` lines 1190-1194

```python
elif 'equipment_slot' in action:
    # User left-clicked on equipment - could show info or do nothing for now
    logger.warning(f"SIDEBAR EQUIPMENT CLICKED: slot {action['equipment_slot']}")
    # For now, left-click on equipment does nothing (could add "examine" later)
    pass  # ← DOES NOTHING!
```

The sidebar interaction code (`ui/sidebar_interaction.py`) correctly detected equipment clicks and returned the clicked item, but `game_actions.py` didn't do anything with it.

---

## ✅ The Fix

**File:** `game_actions.py` lines 1190-1206

```python
elif 'equipment_slot' in action:
    # User left-clicked on equipment - unequip it!
    logger.warning(f"SIDEBAR EQUIPMENT CLICKED: slot {action['equipment_slot']}")
    equipment_item = action.get('equipment_item')
    if equipment_item and player.equipment:
        # Unequip the item (toggle_equip on already equipped item = unequip)
        message_log = self.state_manager.state.message_log
        equip_results = player.equipment.toggle_equip(equipment_item)
        
        for result in equip_results:
            message = result.get("message")
            if message:
                message_log.add_message(message)
        
        # Unequipping takes a turn
        self._process_player_status_effects()
        _transition_to_enemy_turn(self.state_manager, self.turn_manager)
```

**How It Works:**
1. Get the equipment item from the click action
2. Call `toggle_equip()` on it (which unequips if already equipped)
3. Display any messages (e.g., "You unequip Iron Sword")
4. Consume a turn (unequipping takes time, like in traditional roguelikes)
5. Transition to enemy turn

---

## 🎮 How to Use

**To Equip:**
1. Click on an item in your **INVENTORY** section (bottom of sidebar)
2. Item equips automatically
3. Message: "You equipped [item name]!"

**To Unequip:**
1. Click on an equipped item in the **EQUIPMENT** section (top of sidebar)
2. Item unequips and goes back to inventory
3. Message: "You unequipped [item name]"

**Works for:**
- ✅ Weapons (main hand, off hand)
- ✅ Armor (head, chest, feet)
- ✅ Rings (left ring, right ring)
- ✅ Any equippable item

---

## 🧪 Testing

Created **`tests/test_sidebar_equipment_unequip.py`** with 10 comprehensive tests:

1. ✅ Clicking equipped weapon unequips it
2. ✅ Clicking equipped armor unequips it
3. ✅ Clicking equipped ring unequips it
4. ✅ Full equip/unequip cycle works
5. ✅ Unequipping multiple items works
6. ✅ Toggle logic: equipped → unequipped
7. ✅ Toggle logic: unequipped → equipped
8. ✅ Results contain proper messages
9. ✅ Other equipment stays equipped when unequipping one item
10. ✅ Works for all equipment slots

---

## 🎯 Design Decision: Turn Cost

**Question:** Should unequipping take a turn?

**Answer:** Yes, for these reasons:
1. **Traditional roguelike behavior** - Equipment changes take time
2. **Prevents equipment-swapping exploits** - Can't swap gear mid-combat without cost
3. **Tactical consideration** - Must decide if it's worth the turn
4. **Consistency** - Equipping takes a turn, so unequipping should too

**Example:**
- Monster is about to hit you
- You have Ring of Teleportation in inventory
- You could unequip current ring and equip teleport ring
- But that's 2 turns = 2 monster attacks
- Risk/reward decision!

---

## 📋 What Changed

### Files Modified:
1. ✅ `game_actions.py` - Added unequip logic to equipment click handler
2. ✅ `tests/test_sidebar_equipment_unequip.py` - Created comprehensive test suite

### Behavior Changes:
- **Before:** Clicking equipped items in sidebar did nothing
- **After:** Clicking equipped items unequips them and consumes a turn

### No Breaking Changes:
- ✅ Inventory menu still works (if you want to use it)
- ✅ Keyboard shortcuts still work
- ✅ Equipment still auto-identifies on equip
- ✅ All existing equipment functionality preserved

---

## 💡 Future Enhancements

**Possible additions (not implemented):**
1. **Shift+Click** - Examine/show info without unequipping
2. **Ctrl+Click** - Drop equipped item directly
3. **Right-Click** - Context menu (unequip, drop, examine)
4. **Tooltip enhancement** - Show "Click to unequip" hint

**For now:** Simple left-click to toggle equip/unequip is clean and intuitive!

---

## ✅ Status: COMPLETE

- [x] Bug identified
- [x] Fix implemented
- [x] Tests written (10 tests)
- [x] Documentation complete
- [ ] Manual testing (user to verify)

**Ready to test!** Click on any equipped item in the sidebar's EQUIPMENT section and it should unequip. 💪

