# Item Stacking System Design

## Goals
- Reduce inventory clutter
- Improve UX ("5x Healing Potion" instead of 5 separate entries)
- Foundation for future features (wand charges, ammo)

## Design Decisions

### What Items Stack?
**YES - Stack:**
- ✅ Potions (all types)
- ✅ Scrolls (all types)
- ❌ Equipment (weapons, armor, shields) - each is unique
- 🔮 Future: Wands (but track charges separately), Ammo (arrows, bolts)

**Rationale:** Consumables stack, equipment doesn't (each piece is unique with its own bonuses/curses)

### Display Format
**Preferred:** `"3x Healing Potion"` (NetHack style)
- Clean and compact
- Easy to parse visually
- Standard roguelike convention

**Alternatives considered:**
- `"Healing Potion (3)"` - more verbose
- `"[3] Healing Potion"` - less readable

### Max Stack Size
**Decision:** Unlimited (no arbitrary cap)
- NetHack doesn't limit stack sizes
- No gameplay reason to limit
- Simpler implementation

### Identification & Stacking
**Rule:** Only items with same ID state can stack
- Unidentified "blue potion" + Unidentified "blue potion" = Stack
- Identified "Healing Potion" + Identified "Healing Potion" = Stack
- Unidentified + Identified = Don't stack (different knowledge states)

**Rationale:** Players need to see which items are/aren't identified

### Split Stacks?
**Decision:** Not in v1 (drop entire stack or use one at a time)
- Dropping splits automatically (drops 1, rest stays in inventory)
- Using consumes 1 from stack
- Can add "split stack" feature later if needed

**Future Enhancement:** Allow player to drop/throw specific quantity

---

## Implementation Plan

### Phase 1: Core Stacking (Item Component)
```python
class Item:
    def __init__(self, ..., quantity=1):
        self.quantity = quantity  # NEW
        self.stackable = True if use_function else False  # Consumables stack
```

### Phase 2: Inventory Merging
```python
def add_item(self, item):
    # If stackable, find existing stack
    if item.stackable:
        for existing_item in self.items:
            if can_stack(existing_item, item):
                existing_item.quantity += item.quantity
                return [{"item_added": existing_item, "message": ...}]
    
    # Otherwise add as new item
    self.items.append(item)
```

### Phase 3: Usage Decrement
```python
def use(self, item, ...):
    results = item.use_function(...)
    
    if consumed:
        item.quantity -= 1
        if item.quantity <= 0:
            self.items.remove(item)
```

### Phase 4: UI Display
```python
# Sidebar
if item.quantity > 1:
    display_name = f"{item.quantity}x {item.get_display_name()}"
else:
    display_name = item.get_display_name()
```

---

## Stacking Rules (can_stack helper)

Two items can stack if ALL conditions met:
1. Both have `stackable = True`
2. Same `name` (e.g., both "healing_potion")
3. Same `identified` state
4. Same `use_function` (for safety)

**NOT checked:**
- Position (x, y) - stacking happens in inventory, not on ground
- Entity ID - we merge into one stack

---

## Edge Cases

### Picking up item when stack exists
✅ Merge into existing stack, increment quantity

### Dropping item from stack
✅ Drop 1, decrement stack quantity by 1

### Using last item in stack
✅ Use item, quantity becomes 0, remove from inventory

### Save/Load
✅ Save quantity field, load with quantity

### Ground items
❌ Don't stack on ground (v1) - only stack in inventory
🔮 Future: Could stack ground items for performance

---

## Technical Notes

### Backward Compatibility
- Default quantity=1 ensures existing saves work
- Old saves without quantity field get quantity=1 on load

### Performance
- No impact: stacking reduces inventory size
- Faster rendering: fewer items to display

### Testing Priority
1. Stack identical potions ✅
2. Don't stack different potions ✅
3. Don't stack identified + unidentified ✅
4. Use from stack decrements ✅
5. Drop from stack works ✅
6. Save/load preserves quantity ✅

---

## Benefits

### Player Experience
- ✅ Clean inventory ("5x Healing Potion" vs 5 entries)
- ✅ Easier to see what you have
- ✅ Less scrolling through inventory
- ✅ More professional feel

### Code Quality
- ✅ Foundation for wand charges (quantity = charges)
- ✅ Foundation for ammo (quantity = arrow count)
- ✅ Cleaner inventory management

---

## Future Enhancements (Post-v1)

1. **Stack Splitting** - Drop/throw specific quantity
2. **Ground Stacking** - Merge items on same tile
3. **Wand Charges** - Reuse quantity field for charges
4. **Ammo System** - Quantity = number of arrows
5. **Stack Limit** - Optional cap (e.g., 99) if balance needed

---

*Ready to implement! Starting with Item component...*

