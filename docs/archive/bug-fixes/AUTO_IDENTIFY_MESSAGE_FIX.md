# Auto-Identify Message Fix

**Date:** October 17, 2025
**Issue:** AttributeError when equipping items - `MessageBuilder` has no attribute `discovery`
**Status:** ✅ FIXED

---

## 🐛 The Problem

**User Report:**
```
ERROR: Error processing mouse action sidebar_click: 
type object 'MessageBuilder' has no attribute 'discovery'

File "/Users/rafehatfield/development/rlike/components/equipment.py", line 199, in toggle_equip
    "message": MB.discovery(f"You recognize this as {equippable_entity.name}!"),
               ^^^^^^^^^^^^
AttributeError: type object 'MessageBuilder' has no attribute 'discovery'
```

**Expected Behavior:**
- When equipping unidentified items, should auto-identify and show message
- Message should say: "You recognize this as [item name]!"

**Actual Behavior:**
- Game crashed with AttributeError
- Used non-existent `MB.discovery()` method

---

## 🔍 Root Cause

In the auto-identification feature I added to `equipment.py`, I incorrectly used:

```python
MB.discovery(f"You recognize this as {equippable_entity.name}!")
```

But `MessageBuilder` doesn't have a `discovery()` method!

**Available MessageBuilder methods:**
- `combat()` - white
- `success()` - green ✓
- `failure()` - red
- `warning()` - yellow
- `info()` - light blue
- `item_effect()` - gold
- `status_effect()` - cyan
- ... and many more

---

## ✅ The Fix

Changed `MB.discovery()` to `MB.success()`:

```python
# components/equipment.py line 199
"message": MB.success(f"You recognize this as {equippable_entity.name}!")
```

**Why `success()`?**
- Green color indicates positive discovery
- Appropriate for "you learned something" moments
- Used elsewhere for successful actions

---

## 📋 Files Changed

1. ✅ `components/equipment.py` - Changed `MB.discovery()` to `MB.success()`

---

## ✅ Status: FIXED

The auto-identification feature now works correctly! When you equip an unidentified item, you'll see:

**"You recognize this as Ring of Might!"** (in green)

Try equipping rings or other unidentified items now - they'll auto-identify properly! 💍✨

