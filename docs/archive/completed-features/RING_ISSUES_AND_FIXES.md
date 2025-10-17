# Ring Issues and Fixes

**Date:** October 17, 2025
**Reporter:** User testing
**Status:** 🔧 In Progress

---

## 🐛 Issue #1: Ring of Invisibility Does Nothing

### User Report
> "ring of Invisibility doesn't do anything; what is it meant to do anyway? being permanently invisible feels like it's a bit OP"

### Investigation

**Design Intent** (from `components/ring.py` line 39):
```python
INVISIBILITY = auto()    # Start each level invisible for 5 turns
```

**Configuration** (`config/entities.yaml` line 960-964):
```yaml
ring_of_invisibility:
  char: "="
  color: [150, 150, 200]  # Faint blue
  ring_effect: "invisibility"
  effect_strength: 5  # 5 turns invisible per level
```

### Root Cause

**The Ring of Invisibility is NOT implemented!**

The design is:
- ✅ NOT permanent invisibility (user was worried about this)
- ✅ Grants 5 turns of invisibility when you descend/ascend to a new dungeon level
- ❌ BUT: No code exists to trigger this effect

**Missing Implementation:**
1. No code in `components/ring.py` to handle `RingEffect.INVISIBILITY`
2. No code in stairs/level transition to check for Ring of Invisibility
3. The `process_turn()` method only handles REGENERATION
4. The `on_take_damage()` method only handles TELEPORTATION

---

## 🐛 Issue #2: Ring Identification Display Bug

### User Report
> "i picked up a copper ring, when i equip it, it shows that it's a ring of Mi(something), the tool tip still says copper ring, and when i take it off it says copper ring again."

### Investigation

**Expected Behavior:**
- When you equip a ring, it should automatically identify it
- Once identified, all messages should show the real name
- Tooltip should show real name
- Unequip message should show real name

**Actual Behavior:**
- Equipping shows real name briefly (in equip message?)
- Tooltip still shows "copper ring" (unidentified name)
- Unequip shows "copper ring" (unidentified name)

### Root Cause

**Equipment doesn't auto-identify when equipped!**

**File:** `components/equipment.py` method `toggle_equip()`

The method:
1. ✅ Equips the item (`setattr(self, slot_attr, equippable_entity)`)
2. ✅ Returns results with equipped/dequipped messages
3. ❌ Never calls `equippable_entity.item.identify()` to identify it

**Why This Matters:**
- In traditional roguelikes, you identify equipment by using/wearing it
- Players need to know what they're wearing
- Ring effects depend on knowing which ring you have

---

## ✅ Fix #1: Auto-Identify Equipment on Equip

### Solution

Add identification to `Equipment.toggle_equip()` when equipping an item.

**File:** `components/equipment.py`

```python
def toggle_equip(self, equippable_entity: Any) -> List[Dict[str, Any]]:
    # ... existing code ...
    
    if current_item == equippable_entity:
        # Unequip the item
        setattr(self, slot_attr, None)
        results.append({"dequipped": equippable_entity})
    else:
        # ... existing two-handed weapon logic ...
        
        # Replace or equip
        if current_item:
            results.append({"dequipped": current_item})

        setattr(self, slot_attr, equippable_entity)
        
        # ✨ NEW: Auto-identify equipment when equipped
        if hasattr(equippable_entity, 'item') and equippable_entity.item:
            was_unidentified = equippable_entity.item.identify()
            if was_unidentified:
                # Add message that item was identified
                results.append({
                    "message": f"You recognize this as {equippable_entity.name}!",
                    "identified": True
                })
        
        results.append({"equipped": equippable_entity})

    return results
```

**Why This Works:**
- ✅ Calls `item.identify()` which marks it as identified globally
- ✅ All instances of that ring type become identified
- ✅ Future messages use the real name via `get_display_name()`
- ✅ Tooltip shows real name after identification

---

## ✅ Fix #2: Implement Ring of Invisibility

### Design Decision

**NOT Permanent Invisibility** - This would be OP as the user suspected.

**Instead:** Grant 5 turns of invisibility when entering a new dungeon level.

### Implementation Options

#### Option A: Trigger on Stairs (Recommended)
When player uses stairs and has Ring of Invisibility equipped, grant invisibility.

**File:** `stairs.py` or wherever stairs are handled

```python
def use_stairs(player, stairs, game_map, ...):
    # ... existing stairs logic ...
    
    # Check if player has Ring of Invisibility equipped
    if player.equipment:
        rings = [player.equipment.left_ring, player.equipment.right_ring]
        for ring_entity in rings:
            if ring_entity and hasattr(ring_entity, 'ring'):
                if ring_entity.ring.ring_effect == RingEffect.INVISIBILITY:
                    # Grant invisibility for N turns
                    from components.status_effects import InvisibilityEffect
                    duration = ring_entity.ring.effect_strength  # Default: 5
                    
                    if not hasattr(player, 'status_effects'):
                        from components.status_effects import StatusEffectManager
                        player.status_effects = StatusEffectManager(player)
                    
                    invis_effect = InvisibilityEffect(duration=duration, owner=player)
                    results = player.status_effects.add_effect(invis_effect)
                    # Add results to message log
```

#### Option B: Trigger in Ring Component
Add a method `on_new_level()` to Ring component.

**File:** `components/ring.py`

```python
class Ring:
    def on_new_level(self, wearer) -> List[Dict[str, Any]]:
        """Handle ring effects that trigger when entering a new level.
        
        Args:
            wearer (Entity): The entity wearing this ring
            
        Returns:
            List[Dict[str, Any]]: List of result dictionaries
        """
        results = []
        
        # Ring of Invisibility: grant invisibility at start of level
        if self.ring_effect == RingEffect.INVISIBILITY:
            from components.status_effects import InvisibilityEffect
            
            if not hasattr(wearer, 'status_effects'):
                from components.status_effects import StatusEffectManager
                wearer.status_effects = StatusEffectManager(wearer)
            
            invis_effect = InvisibilityEffect(
                duration=self.effect_strength,  # Default: 5 turns
                owner=wearer
            )
            effect_results = wearer.status_effects.add_effect(invis_effect)
            results.extend(effect_results)
        
        return results
```

Then call this from stairs logic:
```python
# When using stairs
if player.equipment:
    for ring_entity in [player.equipment.left_ring, player.equipment.right_ring]:
        if ring_entity and hasattr(ring_entity, 'ring'):
            ring_results = ring_entity.ring.on_new_level(player)
            # Add to message log
```

---

## 🎯 Recommended Implementation Order

### Phase 1: Fix Identification (High Priority)
1. ✅ Add auto-identify to `Equipment.toggle_equip()`
2. ✅ Test that equipping a ring identifies it
3. ✅ Verify tooltip shows real name after equipping
4. ✅ Verify unequip message shows real name

### Phase 2: Implement Ring of Invisibility (Medium Priority)
1. ⏭️ Add `on_new_level()` method to `Ring` component
2. ⏭️ Find stairs usage code and add ring trigger
3. ⏭️ Test that Ring of Invisibility grants 5 turns of invisibility
4. ⏭️ Verify it only triggers when descending/ascending
5. ⏭️ Verify invisibility breaks on attack

---

## 📋 Testing Checklist

### Identification Fix
- [ ] Equip unidentified ring → Shows "You recognize this as Ring of X!"
- [ ] Equip message shows real name
- [ ] Tooltip shows real name (not "copper ring")
- [ ] Unequip message shows real name
- [ ] Other rings of same type auto-identify

### Ring of Invisibility
- [ ] Equip Ring of Invisibility
- [ ] Descend stairs → Become invisible for 5 turns
- [ ] Ascend stairs → Become invisible for 5 turns
- [ ] Attack while invisible → Invisibility breaks
- [ ] Invisibility expires after 5 turns
- [ ] Unequip ring → No invisibility on new level
- [ ] Works with both left and right ring slots

---

## 🤔 Design Questions

### Q: Should ALL equipment auto-identify on equip?
**A:** Yes! This is standard in roguelikes. You learn what something is by using it.

### Q: What if Ring of Invisibility is too weak?
**A:** Can increase duration (5 → 10 turns) or frequency (every level → every floor)

### Q: Should invisibility stack if you have two Rings of Invisibility?
**A:** No - duration should NOT stack. Only apply once per level change.

---

## 📝 Status

- [x] Issue #1: Ring of Invisibility - ✅ IMPLEMENTED
- [x] Issue #2: Auto-identification - ✅ IMPLEMENTED  
- [x] Testing - ✅ COMPLETE (13 tests in test_ring_fixes.py)
- [x] Documentation - ✅ COMPLETE

**Implementation Complete!**

### Files Changed:
1. ✅ `components/equipment.py` - Added auto-identify on equip (lines 192-201)
2. ✅ `components/ring.py` - Added `on_new_level()` method (lines 223-258)
3. ✅ `game_actions.py` - Added ring trigger on stairs (lines 893-902)
4. ✅ `tests/test_ring_fixes.py` - Added 13 comprehensive tests

### What Now Works:
1. ✅ Equipping any ring automatically identifies it
2. ✅ Shows "You recognize this as Ring of X!" message
3. ✅ Ring of Invisibility grants 5 turns of invisibility when taking stairs
4. ✅ Works for both left and right ring slots
5. ✅ Multiple rings don't stack duration
6. ✅ Only triggers when ring is equipped

