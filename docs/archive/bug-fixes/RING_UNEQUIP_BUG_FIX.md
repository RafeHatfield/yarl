# Ring Unequipping Bug Fix

**Date:** October 17, 2025
**Issue:** Attempting to unequip rings causes incorrect behavior
**Status:** ✅ FIXED

---

## 🐛 The Problem

**User Report:**
> "there's weirdness with the rings being equipped and unequipped. trying to unequip the right ring the first time unequips the left ring, the 2nd time it puts the right ring on the left finger, so the same ring is on both fingers."

**Reproduction Steps:**
1. Equip Ring A on left finger
2. Equip Ring B on right finger
3. Click Ring B to unequip it
4. **BUG:** Ring A gets unequipped instead
5. Click Ring B again to unequip it
6. **BUG:** Ring B moves to left finger, so same ring is on both fingers

**Expected Behavior:**
- Clicking Ring B should unequip Ring B from the right finger
- Ring A should remain on the left finger unchanged

---

## 🔍 Root Cause

The issue was in `Equipment.toggle_equip()` method in `components/equipment.py`.

When handling generic `EquipmentSlots.RING` slots, the code logic was:

```python
# OLD BUGGY CODE (lines 131-139)
if slot == EquipmentSlots.RING:
    # Try left ring first, then right ring
    if self.left_ring is None:
        slot_attr = 'left_ring'
    elif self.right_ring is None:
        slot_attr = 'right_ring'
    else:
        # Both slots full, replace left ring
        slot_attr = 'left_ring'
```

**The Problem:**

This logic checks which slot is *available*, not which slot the ring is *currently in*!

**What happened:**

1. User clicks on Ring B (equipped on right finger) to unequip it
2. Sidebar passes `equipment_item=Ring B` to `toggle_equip(Ring B)`
3. Ring B's slot is `EquipmentSlots.RING` (generic)
4. Code checks: `if self.left_ring is None:` → **True!** (Ring A is there, so left_ring is NOT None)
5. Code checks: `elif self.right_ring is None:` → **False** (Ring B is there)
6. Code goes to else branch: `slot_attr = 'left_ring'`
7. Gets `current_item = self.left_ring` (Ring A)
8. Checks `if current_item == equippable_entity:` → **False!** (Ring A ≠ Ring B)
9. Goes to EQUIP branch instead of UNEQUIP branch
10. Sets `self.left_ring = Ring B` (overwrites Ring A)
11. **Result:** Wrong ring unequipped, same ring on both fingers

---

## ✅ The Fix

**File:** `components/equipment.py` (lines 131-145)

Added logic to check if the ring is *already equipped* BEFORE checking for available slots:

```python
# NEW FIXED CODE
if slot == EquipmentSlots.RING:
    # Check if this ring is already equipped in either slot
    if self.left_ring == equippable_entity:
        slot_attr = 'left_ring'
    elif self.right_ring == equippable_entity:
        slot_attr = 'right_ring'
    else:
        # Not currently equipped - find an available slot
        if self.left_ring is None:
            slot_attr = 'left_ring'
        elif self.right_ring is None:
            slot_attr = 'right_ring'
        else:
            # Both slots full, replace left ring
            slot_attr = 'left_ring'
```

**Key Change:**

The new logic has two phases:

1. **Unequip Detection:** Check if the ring is already in `left_ring` or `right_ring`
   - If found → use that slot (will trigger unequip logic)
   
2. **Equip Selection:** If not currently equipped, find an available slot
   - Prefer left_ring → then right_ring → then replace left_ring

---

## 🎯 How It Works Now

### Scenario 1: Unequipping Right Ring

**Setup:**
- Left ring: Ring A
- Right ring: Ring B

**Action:** Click Ring B to unequip

**Flow:**
1. `toggle_equip(Ring B)` called
2. Check `if self.left_ring == Ring B:` → False
3. Check `elif self.right_ring == Ring B:` → **True!**
4. `slot_attr = 'right_ring'`
5. `current_item = self.right_ring` (Ring B)
6. Check `if current_item == equippable_entity:` → **True!**
7. **UNEQUIP** branch executes
8. `self.right_ring = None`

**Result:** ✅ Ring B unequipped, Ring A unchanged

---

### Scenario 2: Equipping New Ring

**Setup:**
- Left ring: None
- Right ring: Ring B

**Action:** Equip Ring A

**Flow:**
1. `toggle_equip(Ring A)` called
2. Check `if self.left_ring == Ring A:` → False (not equipped)
3. Check `elif self.right_ring == Ring A:` → False (not equipped)
4. Falls through to "Not currently equipped" branch
5. Check `if self.left_ring is None:` → **True!**
6. `slot_attr = 'left_ring'`
7. **EQUIP** branch executes
8. `self.left_ring = Ring A`

**Result:** ✅ Ring A equipped to left finger

---

### Scenario 3: Equipping Same Ring (Should Unequip)

**Setup:**
- Left ring: Ring A
- Right ring: None

**Action:** Click Ring A again

**Flow:**
1. `toggle_equip(Ring A)` called
2. Check `if self.left_ring == Ring A:` → **True!**
3. `slot_attr = 'left_ring'`
4. `current_item = self.left_ring` (Ring A)
5. Check `if current_item == equippable_entity:` → **True!**
6. **UNEQUIP** branch executes
7. `self.left_ring = None`

**Result:** ✅ Ring A unequipped (can't have same ring on both fingers)

---

## 🧪 Testing

**Test Results:**

Created comprehensive test suite (`test_ring_unequip_fix.py`) with:

1. ✅ **Test 1:** Unequip right ring correctly
   - Verified right ring is removed
   - Verified left ring is unchanged

2. ✅ **Test 2:** Can't equip same ring to both fingers
   - Clicking equipped ring unequips it instead

3. ✅ **Test 3:** Replace left ring when both slots are full
   - Equipping 3rd ring replaces left ring (expected behavior)

**All tests passed!** ✓

---

## 📋 Files Changed

1. ✅ `components/equipment.py` - Fixed ring slot selection logic (lines 131-145)
2. ✅ `tests/test_ring_unequip_fix.py` - Comprehensive regression test suite

---

## 💡 Design Notes

### Why Check "Already Equipped" First?

The key insight is that `toggle_equip()` serves **two purposes**:

1. **Equip** a ring from inventory → need to find an available slot
2. **Unequip** an already-equipped ring → need to find which slot it's IN

The old code only handled case #1. The fix handles both by checking if the ring is already equipped FIRST.

### Why Prefer Left Ring?

Traditional roguelike convention:
- Equipment fills "top to bottom" in the interface
- Left ring is listed before right ring
- When both slots are full, replacing the left ring is more predictable

### Edge Case: Direct Slot Specification

Note that `LEFT_RING` and `RIGHT_RING` slots (specific) are also in the `slot_map`, so if the item explicitly specifies a specific ring slot (not the generic `RING`), it bypasses this logic entirely and goes directly to that slot. This is intentional for potential future features.

---

## ✅ Status: FIXED

**Try it now:**
1. Equip two rings
2. Click on either ring in the sidebar
3. The correct ring will be unequipped!
4. No more weird ring-swapping behavior!

The ring equipping/unequipping system now works correctly! 💍✨

