# Turn Economy Implementation - Everything Takes Time

## Overview

**Goal:** Make ALL player actions take a turn (standard roguelike design)

**Why:** Required for Identify scroll mechanic (10 turns to identify items, 1 per turn)

**Impact:** Major gameplay improvement - adds tactical weight to every decision

---

## Current State Analysis

**Actions That Currently Take a Turn:**
- Moving
- Attacking
- Using scrolls/potions in combat
- Resting

**Actions That Currently DON'T Take a Turn (need fixing):**
- Opening inventory ('i' key)
- Picking up items ('g' key)
- Dropping items ('d' key)
- Equipping items
- Unequipping items
- Using items from inventory
- Reading item descriptions
- Examining items

---

## Required Changes

### 1. Input Handlers Need Turn Advancement

**Files to Modify:**
- `input_handlers.py` - Main input processing
- `game_actions.py` - Action processing

**Key Concept:**
Every action that returns from input handler needs to signal whether it consumes a turn.

**Current Pattern:**
```python
def handle_keys(key, game_state):
    if key == 'i':
        game_state = GameStates.SHOW_INVENTORY
        return {'inventory': True}  # No turn consumed
```

**New Pattern:**
```python
def handle_keys(key, game_state):
    if key == 'g':  # Pick up item
        # ... pick up logic ...
        return {'picked_up': True, 'turn_consumed': True}  # Turn consumed!
```

### 2. Inventory Actions Take Turns

**Actions That Need Turn Cost:**

#### Pick Up Item ('g' key)
- **Current:** Instant pickup
- **New:** Takes 1 turn
- **Reason:** Bending down, grabbing item takes time

#### Use Item from Inventory ('i' -> select)
- **Current:** Might be instant
- **New:** Takes 1 turn
- **Reason:** Finding item, using it takes time

#### Equip Item
- **Current:** Might be instant  
- **New:** Takes 1 turn
- **Reason:** Putting on armor, switching weapons takes time

#### Drop Item ('d' key)
- **Current:** Might be instant
- **New:** Takes 1 turn
- **Reason:** Rifling through pack, discarding takes time

#### Examine Item (reading description)
- **Current:** Free (pauses game)
- **New:** REMAINS FREE (just looking)
- **Reason:** Player needs to read descriptions without danger

### 3. UI Implications

**Inventory Screen:**
- Add warning text: "Using items takes a turn!"
- Show turn count in corner
- Color-code items by action type (instant vs turn-consuming)

**Ground Items:**
- When picking up, show message: "You pick up the {item}."
- Monsters get to act after pickup

**Equipment Screen:**
- Add warning: "Equipping takes a turn!"
- Show confirmation for dangerous situations

### 4. Special Cases

**Multiple Items on Same Tile:**
- **Option A:** Each pickup takes 1 turn (realistic)
- **Option B:** Pickup ALL items in 1 turn (player-friendly)
- **Recommendation:** Option A (more tactical)

**Auto-Pickup:**
- If we add auto-pickup feature, it still takes 1 turn per item
- Player can configure auto-pickup rules

**Quick-Swap (future feature):**
- Could add "Quick Swap" ability (0 turns) as character perk
- Makes equipment swapping not cost a turn
- Requires finding/unlocking the perk

### 5. Identify Scroll Integration

**How It Works:**
1. Player uses Identify scroll
2. Gets IDENTIFY_MODE status effect (10 turns)
3. Opens inventory ('i') - **NO TURN COST** (just opening)
4. Selects unidentified item - **TAKES 1 TURN** (the identification)
5. Item becomes identified
6. Can identify 1 more item next turn
7. After 10 turns, effect expires

**UI During Identify Mode:**
- Highlight unidentified items in inventory
- Show "Identify Mode: X turns remaining"
- Show "Select item to identify (costs 1 turn)"

---

## Implementation Priority

### Phase 1: Core Turn Economy (Required for Identify)
1. ✅ Update Identify scroll definition (DONE)
2. Make pickup ('g') take 1 turn
3. Make inventory use take 1 turn
4. Make equip/unequip take 1 turn
5. Make drop take 1 turn
6. Update UI warnings

### Phase 2: Identify Mode Status Effect
1. Create IdentifyModeEffect class
2. Add UI indicator for identify mode
3. Hook up item selection during identify mode
4. Track identifies per turn (1 per turn limit)
5. Update turn counter in UI

### Phase 3: Polish
1. Add confirmation dialogs for dangerous situations
2. Tutorial/help text explaining turn economy
3. Playtest and balance
4. Add accessibility options (instant mode toggle?)

---

## Code Examples

### Example 1: Pickup Takes Turn

```python
# In game_actions.py or input_handlers.py

def pickup_item(player, entities, game_map):
    """Pick up item at player's location. COSTS 1 TURN."""
    items_at_location = [e for e in entities 
                         if e.x == player.x and e.y == player.y 
                         and e.components.has(ComponentType.ITEM)]
    
    if not items_at_location:
        return {'message': "There is nothing here to pick up.", 
                'turn_consumed': False}
    
    if len(items_at_location) == 1:
        item = items_at_location[0]
        # Pick up the item
        player.inventory.add_item(item)
        entities.remove(item)
        
        return {
            'message': f"You pick up the {item.get_display_name()}.",
            'picked_up': item,
            'turn_consumed': True  # <-- KEY: Turn consumed!
        }
    else:
        # Multiple items - show selection menu
        # Selecting and picking up will cost 1 turn
        return {
            'show_pickup_menu': items_at_location,
            'turn_consumed': False  # Turn not consumed until selection
        }
```

### Example 2: Use Item Takes Turn

```python
# In inventory handling

def use_item_from_inventory(player, item, **kwargs):
    """Use an item from inventory. COSTS 1 TURN."""
    
    # Execute the item's use function
    results = item.item.use(player, **kwargs)
    
    # Add turn consumption to results
    results.append({'turn_consumed': True})  # <-- KEY: Turn consumed!
    
    # If item was consumed, remove from inventory
    if any(r.get('consumed') for r in results):
        player.inventory.remove_item(item)
    
    return results
```

### Example 3: Identify Mode Effect

```python
# In components/status_effects.py

class IdentifyModeEffect(StatusEffect):
    """Allows identifying 1 item per turn for duration."""
    
    def __init__(self, duration: int, owner: 'Entity'):
        super().__init__("identify_mode", duration, owner)
        self.identifies_used_this_turn = 0
    
    def apply(self) -> List[Dict[str, Any]]:
        results = super().apply()
        results.append({
            'message': MB.status_effect(
                f"✨ You can now identify items! ({self.duration} turns remaining)"
            )
        })
        return results
    
    def can_identify_item(self) -> bool:
        """Check if owner can identify an item this turn."""
        return self.identifies_used_this_turn < 1
    
    def use_identify(self) -> None:
        """Mark that an identify was used this turn."""
        self.identifies_used_this_turn += 1
    
    def process_turn_start(self) -> List[Dict[str, Any]]:
        """Reset identify counter each turn."""
        results = super().process_turn_start()
        self.identifies_used_this_turn = 0  # Reset for new turn
        
        if self.duration > 0:
            results.append({
                'message': MB.info(f"Identify Mode: {self.duration} turns remaining")
            })
        
        return results
    
    def remove(self) -> List[Dict[str, Any]]:
        results = super().remove()
        results.append({
            'message': MB.status_effect("Your identification powers fade.")
        })
        return results
```

---

## Testing Checklist

**Turn Economy:**
- [ ] Picking up item advances turn counter
- [ ] Monsters get to act after picking up item
- [ ] Using item from inventory advances turn
- [ ] Equipping item advances turn
- [ ] Dropping item advances turn
- [ ] Opening inventory DOESN'T advance turn (just viewing)

**Identify Mode:**
- [ ] Using identify scroll grants 10-turn buff
- [ ] Can identify 1 item per turn
- [ ] Cannot identify more than 1 item per turn
- [ ] Turn counter decrements properly
- [ ] Effect expires after 10 turns
- [ ] UI shows remaining turns
- [ ] Unidentified items are highlighted

**Edge Cases:**
- [ ] Picking up item with full inventory
- [ ] Trying to identify when already identified
- [ ] Identify mode expires mid-inventory
- [ ] Multiple items on same tile
- [ ] Picking up item while in danger

---

## Player Impact

**Before (current):**
- Inventory management is "free" - no time cost
- Can reorganize inventory while monsters wait
- Less tactical weight to inventory decisions

**After (with turn economy):**
- Every action matters - time is a resource
- Can't casually pick up everything
- Strategic decisions: "Do I have time to pick this up?"
- Identify scroll becomes meaningful (10 turns of power)
- More like traditional roguelikes (NetHack, DCSS, etc.)

---

## Difficulty Considerations

**For New Players:**
This makes the game harder! Consider:
- Tutorial explicitly explains turn economy
- Early floors are more forgiving (fewer monsters)
- Add "tutorial messages" when actions take turns

**Accessibility Option:**
Could add a game setting:
```yaml
turn_economy:
  enabled: true  # Standard roguelike mode
  # If false, inventory management is instant (easier mode)
```

---

## Timeline

**Estimated Time:** 2-3 days

**Day 1:** Core turn economy implementation
- Input handlers
- Action processing
- Turn advancement

**Day 2:** Identify mode status effect
- IdentifyModeEffect class
- UI integration
- Turn tracking

**Day 3:** Testing and polish
- Playtest extensively
- Fix edge cases
- UI improvements

---

## Decision Point

**This is a significant change!** Before proceeding, confirm:

1. **Do we implement full turn economy NOW?**
   - Pro: Required for Identify scroll, improves game design
   - Con: Bigger scope than just "add scrolls"

2. **Or do we defer it?**
   - Pro: Can finish other scroll work first
   - Con: Identify scroll won't work properly

**Recommendation:** Implement full turn economy NOW. It's the right design and makes all the new scrolls more meaningful.

---

## Next Steps

Once approved:
1. Implement turn economy core (pickup, use, equip, drop)
2. Implement IdentifyModeEffect status effect
3. Add UI indicators and warnings
4. Test extensively
5. Update documentation
6. Continue with remaining scrolls

This will make the game feel significantly more like a traditional roguelike! 🎮

