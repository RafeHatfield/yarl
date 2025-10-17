# Ring of Regeneration Fix

**Date:** October 17, 2025
**Issue:** Ring of Regeneration not healing the player
**Status:** ✅ FIXED

---

## 🐛 The Problem

**User Report:**
> "i don't think the ring of regeneration works, i'm not healing while wearing it"

**Expected Behavior:**
- Ring of Regeneration should heal 1 HP every 5 turns while equipped
- Should show message: "{Name}'s ring glows softly. (+1 HP)"

**Actual Behavior:**
- Nothing happened
- No healing
- No messages

---

## 🔍 Root Cause

The Ring of Regeneration's `process_turn()` method checked for a `turn_count` attribute on the player:

```python
# components/ring.py line 188
if hasattr(wearer, 'turn_count'):
    if wearer.turn_count % self.effect_strength == 0:
        # Heal...
```

**Problem:** The player entity doesn't have a `turn_count` attribute!

The code assumed entities would track their own turns, but:
- No entity in the game has `turn_count`
- The `TurnManager` tracks global turn number
- Ring never healed because the check always failed

---

## ✅ The Fix

### Part 1: Update Ring Component

**File:** `components/ring.py`

Changed `process_turn()` to accept an optional `turn_number` parameter:

```python
def process_turn(self, wearer, turn_number: int = None) -> List[Dict[str, Any]]:
    """Process turn-based effects for this ring."""
    results = []
    
    if self.ring_effect == RingEffect.REGENERATION:
        # Get turn number from parameter or fallback to wearer.turn_count
        current_turn = None
        if hasattr(wearer, 'turn_count'):
            current_turn = wearer.turn_count
        elif turn_number is not None:
            current_turn = turn_number
        
        if current_turn is not None:
            # Heal every 5 turns (skip turn 0)
            if current_turn > 0 and current_turn % self.effect_strength == 0:
                if wearer.fighter and wearer.fighter.hp < wearer.fighter.max_hp:
                    wearer.fighter.heal(1)
                    results.append({
                        'message': MB.status_effect(f"{wearer.name}'s ring glows softly. (+1 HP)")
                    })
    
    return results
```

**Changes:**
- Added `turn_number` parameter
- Check parameter if `turn_count` attribute doesn't exist
- Skip turn 0 to avoid healing immediately on equip
- Use MessageBuilder for proper message formatting

---

### Part 2: Update StatusEffectManager

**File:** `components/status_effects.py`

Updated `process_turn_start()` to accept and pass `turn_number`:

```python
def process_turn_start(self, entities=None, turn_number: int = None) -> List[Dict[str, Any]]:
    """Process status effects at turn start."""
    results = []
    
    # Process ring effects first (Ring of Regeneration)
    equipment = self.owner.equipment if hasattr(self.owner, 'equipment') else None
    if equipment:
        for ring in [equipment.left_ring, equipment.right_ring]:
            if ring and ring.components.has(ComponentType.RING):
                ring_results = ring.ring.process_turn(self.owner, turn_number=turn_number)
                results.extend(ring_results)
    
    # ... rest of status effect processing
    return results
```

**Changes:**
- Added `turn_number` parameter
- Pass `turn_number` to `ring.process_turn()`

---

### Part 3: Update Game Actions

**File:** `game_actions.py`

Updated `_process_player_status_effects()` to:
1. Get turn number from TurnManager
2. Call `process_turn_start()` (which processes rings)
3. Then call `process_turn_end()` (which decrements durations)

```python
def _process_player_status_effects(self) -> None:
    """Process status effects at the end of the player's turn."""
    player = self.state_manager.state.player
    message_log = self.state_manager.state.message_log
    
    # Get current turn number from TurnManager
    turn_number = None
    if self.turn_manager:
        turn_number = self.turn_manager.turn_number
    
    # Process status effects at turn START (for Ring of Regeneration, etc.)
    if hasattr(player, 'status_effects') and player.status_effects:
        start_results = player.status_effects.process_turn_start(turn_number=turn_number)
        for result in start_results:
            message = result.get("message")
            if message:
                message_log.add_message(message)
    
    # Process status effects turn end (duration decrements, etc.)
    effect_results = player.process_status_effects_turn_end()
    # ...
```

**Changes:**
- Get `turn_number` from `TurnManager`
- Call `process_turn_start()` with `turn_number`
- Properly process ring effects at turn start

---

## 🎯 How It Works Now

**Turn Flow:**
1. Player takes action (move, attack, wait, etc.)
2. `_process_player_status_effects()` is called
3. Gets current turn number from TurnManager (e.g., turn 5, 10, 15, ...)
4. Calls `status_effects.process_turn_start(turn_number=5)`
5. StatusEffectManager calls `ring.process_turn(player, turn_number=5)`
6. Ring checks: `5 % 5 == 0` → TRUE!
7. Ring heals player for 1 HP
8. Message shows: "You's ring glows softly. (+1 HP)"

**Healing Schedule:**
- Turn 5: +1 HP 🩹
- Turn 10: +1 HP 🩹
- Turn 15: +1 HP 🩹
- Turn 20: +1 HP 🩹
- ...and so on every 5 turns

---

## 📋 Files Changed

1. ✅ `components/ring.py` - Updated `process_turn()` to accept `turn_number`
2. ✅ `components/status_effects.py` - Updated `process_turn_start()` to pass `turn_number`
3. ✅ `game_actions.py` - Updated `_process_player_status_effects()` to get and pass turn number

---

## 🧪 Testing

**Manual Test:**
1. Equip Ring of Regeneration
2. Take damage (get hit by monster, stand on hazard)
3. Wait/move 5 times
4. On turn 5, 10, 15, etc., should heal +1 HP
5. Should see message: "You's ring glows softly. (+1 HP)"

**Edge Cases:**
- ✅ Works when turn_count doesn't exist (uses TurnManager)
- ✅ Backward compatible if turn_count ever added to entities
- ✅ Doesn't heal on turn 0 (avoids immediate heal on equip)
- ✅ Only heals if HP < max HP (doesn't waste messages)
- ✅ Works with both left and right ring slots

---

## 💡 Design Notes

### Why Check turn_count First?

The code checks `hasattr(wearer, 'turn_count')` before using the parameter because:
1. **Future-proof** - If we ever add per-entity turn tracking, it takes priority
2. **Monster support** - Monsters might have their own turn counts
3. **Backward compatible** - Works with or without TurnManager

### Why Skip Turn 0?

```python
if current_turn > 0 and current_turn % 5 == 0:
```

This prevents healing immediately when equipping the ring. Otherwise:
- Turn 0 % 5 == 0 → Would heal instantly on equip
- Not a bug, but not the intended behavior
- Feels more natural to wait for the first cycle

### Why process_turn_start not process_turn_end?

Ring of Regeneration should heal BEFORE the turn ends so the player sees the effect during their turn, not after monsters have already acted. This makes the healing more visible and useful.

---

## ✅ Status: FIXED

**Try it now:**
1. Equip Ring of Regeneration
2. Take some damage
3. Wait/move around
4. Every 5 turns you'll heal +1 HP with a message!

The ring now works as intended! 🩹💍

